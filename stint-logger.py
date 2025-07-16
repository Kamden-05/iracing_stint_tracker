from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime
import time
import irsdk
import pandas as pd


def format_time(seconds: float) -> str:
    h, m = divmod(int(seconds), 3600)
    m, s = divmod(m, 60)
    ms = seconds % 1
    s_with_ms = s + ms
    return f"{h}:{m:02}:{s_with_ms:06.3f}" if h > 0 else f"{m:02}:{s_with_ms:06.3f}"


@dataclass
class Stint:
    driver: str
    start_time: float
    laps: List[float]
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int

    def stint_length(self, current_time: float) -> float:
        return current_time - self.start_time

    def average_lap(self) -> float:
        return sum(self.laps) / len(self.laps) if self.laps else 0.0

    def fastest_lap(self) -> float:
        return min(self.laps) if self.laps else 0.0

    def refuel_amount(self, prev_start_fuel: float, end_fuel: float) -> float:
        return prev_start_fuel - end_fuel

    def repairs(self, end_fast_repairs: int, service_time: float) -> bool:
        if end_fast_repairs is not None and self.start_fast_repairs is not None:
            return end_fast_repairs < self.start_fast_repairs
        else:
            return service_time > 0

    def to_dict(
        self,
        end_time: float,
        end_fuel: float,
        end_position: int,
        incidents: int,
        service_time: float,
        tire_replacement: bool,
        end_fast_repairs: int,
    ) -> dict:
        return {
            "Local Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": self.driver,
            "Stint Start": format_time(self.start_time),
            "Stint Length": format_time(self.stint_length(end_time)),
            "Laps": len(self.laps),
            "Average Lap": format_time(self.average_lap()),
            "Fastest Lap": format_time(self.fastest_lap()),
            "Out Lap": format_time(self.laps[0]) if self.laps else None,
            "In Lap": format_time(self.laps[-1]) if self.laps else None,
            "Start Fuel Qty.": f"{self.start_fuel:.2f}",
            "End Fuel Qty.": f"{end_fuel:.2f}",
            "Refuel Qty.": 0,
            "Tires": "True" if tire_replacement == 1.0 else "False",
            "Repairs": str(self.repairs(end_fast_repairs, service_time)),
            "Service Time": format_time(service_time),
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

    def get_player_car_idx(self) -> int:
        return self.ir["PlayerCarIdx"]

    def get_driver_name(self) -> str:
        car_idx = self.get_player_car_idx()
        return self.ir["DriverInfo"]["Drivers"][car_idx]["UserName"]

    def get_lap(self) -> int:
        return self.ir["Lap"]

    def get_last_lap_time(self) -> float:
        return self.ir["LapLastLapTime"]

    def get_session_time(self):  # TODO: check if session time is int or float
        return self.ir["SessionTime"]

    def get_player_position(self) -> int:
        return self.ir["PlayerCarPosition"]

    def get_team_incidents(self) -> int:
        return self.ir["PlayerCarTeamIncidentCount"]

    def get_fuel_level(self) -> float:
        return self.ir["FuelLevel"]

    def get_tire_replacement(self) -> bool:
        return (
            self.ir["dpLFTireChange"]
            or self.ir["dpRFTireChange"]
            or self.ir["dpLRTireChange"]
            or self.ir["dpRRTireChange"]
        )

    def get_fast_repairs(self) -> int:
        return self.ir["PlayerCarFastRepairsUsed"]

    def get_pitstop_active(self) -> bool:
        return self.ir["PitstopActive"]

    def get_service_time(self) -> float:
        return self.ir["PitOptRepairLeft"] + self.ir["PitRepairLeft"]

    def get_session_flags(self) -> str:
        return self.ir["SessionFlags"]


# TODO: only calculate inital position under green flag, not race session

# TODO: separate processing methods for practice/quali/race

# TODO: if we join the middle of a session, dont start collecting data until the next stint starts for consistency


def process_race(ir_interface: IracingInterface):
    pass


def process_practice():
    pass


def process_quali():
    pass


def main():
    ir_interface = IracingInterface()
    out_file_name = "stints"
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

                position = ir_interface.get_player_position()
                if position > 0:

                    out_file_name = str(ir_interface.ir["SessionUniqueID"])

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
                            start_fast_repairs=ir_interface.get_fast_repairs(),
                        )

                        if len(stints) > 0:
                            stints[-1]["Refuel Qty."] = max(
                                0,
                                f"{current_stint.start_fuel - stints[-1]["End Fuel Qty."]:.2f}",
                            )
                            print(
                                f'prev stint refuel updated to {stints[-1]["Refuel Qty."]}'
                            )

                        print("new stint started")

                    if (
                        current_stint
                        and current_lap > 1
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
                        tire_replacement = ir_interface.get_tire_replacement()
                        end_fast_repairs = ir_interface.get_fast_repairs()

                        stint_data = current_stint.to_dict(
                            end_time,
                            end_fuel,
                            end_pos,
                            incidents,
                            service_time,
                            tire_replacement,
                            end_fast_repairs,
                        )
                        stints.append(stint_data)

                        print(stints)
                        current_stint = None

                    last_pitstop_active = pitstop_active
                else:
                    print("waiting for race start")
            time.sleep(1)

    except KeyboardInterrupt:
        # TODO: log the current stint on exit
        print("Exiting")

    # Export DataFrame
    out_path = "./races/" + out_file_name + ".csv"
    df = pd.DataFrame(stints)
    df.to_csv(out_path, index=False)
    print(f"Stints saved to {out_path}")


if __name__ == "__main__":
    main()
