import time
import irsdk
import pandas as pd
from stint import Stint


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


def update_prev_refuel(prev_stint: Stint, current_stint: Stint) -> Stint:
    prev_stint["Refuel Qty."] = max(
        0,
        round(
            current_stint.start_fuel - prev_stint["End Fuel Qty."],
            2,
        ),
    )

    return prev_stint


def record_stint(stint: Stint, ir_interface: IracingInterface) -> dict:
    end_time = ir_interface.get_session_time()
    end_fuel = ir_interface.get_fuel_level()
    end_pos = ir_interface.get_player_position()
    incidents = ir_interface.get_team_incidents()
    service_time = ir_interface.get_service_time()
    tire_replacement = ir_interface.get_tire_replacement()
    end_fast_repairs = ir_interface.get_fast_repairs()

    stint_data = stint.to_dict(
        end_time,
        end_fuel,
        end_pos,
        incidents,
        service_time,
        tire_replacement,
        end_fast_repairs,
    )

    return stint_data


def process_race(ir_interface: IracingInterface):
    pass


def process_practice():
    pass


def process_quali():
    pass


# TODO: only calculate inital position under green flag, not race session

# TODO: separate processing methods for practice/quali/race

# TODO: if we join the middle of a session, dont start collecting data until the next stint starts for consistency


def main():
    ir_interface = IracingInterface()
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

            # check if race data is ready to be recorded
            if (
                ir_interface.is_race_session()
                and ir_interface.get_player_position() > 0
            ):

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
                        stints[-1] = update_prev_refuel(stints[-1], current_stint)

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
                    stints.append(record_stint(current_stint, ir_interface))
                    current_stint = None
                    print("Stint recorded")

                last_pitstop_active = pitstop_active
            else:
                print("Waiting for race start")
            time.sleep(1)

    except KeyboardInterrupt:
        # TODO: log the current stint on exit
        print("Exiting")

    # Export DataFrame
    out_path = "./races/stints.csv"
    df = pd.DataFrame(stints)
    df.to_csv(out_path, index=False)
    print(f"Stints saved to {out_path}")


if __name__ == "__main__":
    main()
