import irsdk


class IracingInterface:
    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.ir_connected = False

    def check_connection(self):
        if self.ir_connected and not (self.ir.is_initialized and self.ir.is_connected):
            self.ir_connected = False

            self.ir.shutdown()
            print("irsdk disconnected")
        elif (
            not self.ir_connected
            and self.ir.startup()
            and self.ir.is_initialized
            and self.ir.is_connected
        ):
            self.ir_connected = True
            print("irsdk connected")

        return self.ir_connected

    def is_connected(self):
        return self.ir_connected

    # TODO: change to check for session type instead of specifically race type
    def get_session_type(self) -> str:
        return self.ir["SessionInfo"]["Sessions"][self.ir["SessionNum"]]["SessionType"]

    def get_player_car_idx(self) -> int:
        return self.ir["PlayerCarIdx"]

    def get_driver_name(self) -> str:
        car_idx = self.get_player_car_idx()
        return self.ir["DriverInfo"]["Drivers"][car_idx]["UserName"]

    def get_lap(self) -> int:
        return self.ir["Lap"]

    def get_completed_laps(self) -> int:
        return self.ir["LapCompleted"]

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
