from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime
import time
import irsdk
import pandas as pd


@dataclass
class Stint:
    driver: str
    start_time: float
    laps: List[float]
    start_position: int
    start_incidents: int
    start_fuel: float

    def stint_length(self, current_time: float) -> float:
        return current_time - self.start_time

    def average_lap(self) -> float:
        return sum(self.laps) / len(self.laps) if self.laps else 0.0

    def fastest_lap(self) -> float:
        return min(self.laps) if self.laps else 0.0

    def refuel_amount(self, prev_start_fuel: float, end_fuel: float) -> float:
        return prev_start_fuel - end_fuel

    def to_dict(
        self,
        end_time: float,
        end_fuel: float,
        end_position: int,
        incidents: int,
        service_time: float,
    ) -> dict:
        return {
            "Local Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": self.driver,
            "Stint Start": self.start_time,
            "Stint Length": self.stint_length(end_time),
            "Laps": len(self.laps),
            "Average Lap": self.average_lap(),
            "Fastest Lap": self.fastest_lap(),
            "Out Lap": self.laps[0] if self.laps else None,
            "In Lap": self.laps[-1] if self.laps else None,
            "Start Fuel Qty.": self.start_fuel,
            "End Fuel Qty.": end_fuel,
            "Refuel Qty.": 0,
            "Tires": False,  # TODO: check if tires were taken at pit stop
            "Repairs": False,  # TODO: check if repairs were needed for pitstop
            "Service Time": service_time,
            "Incidents": incidents - self.start_incidents,
            "Start Position": self.start_position,
            "End Position": end_position,
        }


class IracingInterface:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.ir_connected = False

    def connect(self):
        if (
            not self.ir_connected
            and self.ir.startup()
            and self.ir.is_initialized
            and self.ir.is_connected
        ):
            self.ir_connected = True
            print("Connected to iRacing")

    def disconnect(self):
        if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.ir_connected = False
            self.ir.shutdown()
            print("Disconnected from iRacing")

    def is_connected(self):
        return self.ir_connected

    def is_race_session(self):
        return (
            self.ir["SessionInfo"]["Sessions"][self.ir["SessionNum"]]["SessionType"]
            == "Race"
        )

    def get_player_car_idx(self):
        return self.ir["PlayerCarIdx"]

    def get_driver_name(self):
        car_idx = self.get_player_car_idx()
        return self.ir["DriverInfo"]["Drivers"][car_idx]["UserName"]

    def get_lap(self):
        return self.ir["Lap"]

    def get_last_lap_time(self):
        return self.ir["LapLastLapTime"]

    def get_session_time(self):
        return self.ir["SessionTime"]

    def get_player_position(self):
        return self.ir["PlayerCarPosition"]

    def get_team_incidents(self):
        return self.ir["PlayerCarTeamIncidentCount"]

    def get_fuel_level(self):
        return self.ir["FuelLevel"]

    def get_pitstop_active(self):
        return self.ir["PitstopActive"]

    def get_service_time(self):
        return self.ir["PitOptRepairLeft"] + self.ir["PitRepairLeft"]


def main():
    ir_interface = IracingInterface()
    out_file_name = "stints.csv"
    stints = []
    current_stint = None
    last_pitstop_active = False
    last_recorded_lap = -1

    try:
        print("initializing")
        while True:
            ir_interface.connect()
            if not ir_interface.is_connected():
                ir_interface.disconnect()
                time.sleep(1)
                continue

            if ir_interface.is_race_session():

                out_file_name = ir_interface.ir["SessionUniqueID"]

                current_lap = ir_interface.get_lap()
                pitstop_active = ir_interface.get_pitstop_active()

                if current_stint is None and not pitstop_active:
                    current_stint = Stint(
                        driver=ir_interface.get_driver_name(),
                        start_time=ir_interface.get_session_time(),
                        laps=[],
                        start_position=ir_interface.get_player_position(),
                        start_incidents=ir_interface.get_team_incidents(),
                        start_fuel=ir_interface.get_fuel_level(),
                    )

                    if len(stints) >= 2:
                        stints[-2]["Refuel Qty."] = max(
                            0, current_stint.start_fuel - stints[-2]["End Fuel Qty."]
                        )
                        print(
                            f'prev stint refuel updated to {stints[-2]["Refuel Qty."]}'
                        )

                if (
                    current_stint
                    and current_lap > 0
                    and current_lap > last_recorded_lap
                ):
                    lap_time = ir_interface.get_last_lap_time()
                    current_stint.laps.append(lap_time)
                    last_recorded_lap = current_lap

                if (
                    pitstop_active
                    and not last_pitstop_active
                    and current_stint is not None
                ):
                    # Pit started, record stint
                    end_time = ir_interface.get_session_time()
                    end_fuel = ir_interface.get_fuel_level()
                    end_pos = ir_interface.get_player_position()
                    incidents = ir_interface.get_team_incidents()
                    service_time = ir_interface.get_service_time()

                    stint_data = current_stint.to_dict(
                        end_time, end_fuel, end_pos, incidents, service_time
                    )
                    stints.append(stint_data)
                    print(stints)
                    current_stint = None

                last_pitstop_active = pitstop_active
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting")

    # Export DataFrame
    out_path = "./races/" + out_file_name + "csv"
    df = pd.DataFrame(stints)
    df.to_csv(out_path, index=False)
    print(f"Stints saved to {out_path}")


if __name__ == "__main__":
    main()
