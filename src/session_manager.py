from src.stint import Stint
from src.utils import format_time
from typing import List
import irsdk
import logging


class SessionManager:

    def __init__(self, ir=None):
        self.ir = ir or irsdk.IRSDK()
        self.is_connected: bool = False
        self.stints: List[Stint] = []
        self.prev_pit_active: bool = False
        self.current_stint: Stint = None
        self.end_stint = False
        self.prev_lap = 0
        self.prev_recorded_lap = 0
        self.race_started = False
        self.race_ended = False
        self.final_lap = -999
        self.lap_start_time = 0.0
        self.pending_lap_time = 0.0

    def connect(self) -> bool:
        if not self.is_connected and not self.race_ended:
            self.is_connected = self.ir.startup()
            if self.is_connected:
                print("Connected to iRacing")
        return self.is_connected

    def disconnect(self) -> None:
        if self.is_connected:
            if self.current_stint:
                self.current_stint.end_stint()
                self.stints.append(self.current_stint)

            self.ir.shutdown()
            self.is_connected = False
            logging.info("Disconnected from iRacing")

    def check_race_status(self) -> None:

        # TODO: set race started to True when we start/end a pitstop
        session_state = self.ir["SessionState"]
        if (
            not self.race_started
            and session_state == irsdk.SessionState.racing
            and self.ir["PlayerCarClassPosition"] > 0
        ):
            self.race_started = True
            self.race_ended = False

        flags = self.ir["SessionFlags"]
        if flags & irsdk.Flags.checkered:
            if self.final_lap == -999:
                self.final_lap = self.ir["Lap"]
            elif self.final_lap == self.prev_recorded_lap:
                self.race_ended = True
                self.disconnect()

    def process_race(self) -> None:
        self.ir.freeze_var_buffer_latest()
        self.check_race_status()
        if self.race_started and not self.race_ended:
            pit_active = self.ir["PitstopActive"]
            time = self.ir["SessionTime"]
            position = self.ir["PlayerCarClassPosition"]
            incidents = self.ir["PlayerCarMyIncidentCount"]
            fuel = self.ir["FuelLevel"]
            fast_repairs = self.ir["FastRepairUsed"]

            if not pit_active and self.current_stint is None:

                car_id = self.ir["PlayerCarIdx"]
                driver = self.ir["DriverInfo"]["Drivers"][car_id]["UserName"]

                self.current_stint = Stint(
                    stint_id=len(self.stints) + 1,
                    driver=driver,
                    start_time=time,
                    start_position=position,
                    start_incidents=incidents,
                    start_fuel=fuel,
                    start_fast_repairs=fast_repairs,
                )

            elif pit_active and not self.prev_pit_active:

                required_repair = self.ir["PitRepairLeft"]
                optional_repair = self.ir["PitOptRepairLeft"]
                fuel_add = self.ir["dpFuelAddKg"]
                max_fuel = fuel / self.ir["FuelLevelPct"]
                refuel = min(fuel_add, max_fuel - fuel)

                self.current_stint.record_pit(
                    required_repair_time=required_repair,
                    optional_repair_time=optional_repair,
                    end_fuel=fuel,
                    reufel_amount=refuel,
                    tires=self._check_tires(),
                    session_time=time,
                )

            elif not pit_active and self.prev_pit_active:
                self.end_stint = True

            if self.current_stint:

                lap = self.ir["Lap"]
                lap_completed = self.ir["LapCompleted"]
                lap_dist_pct = self.ir["LapDistPct"]

                if lap > self.prev_lap:
                    self.pending_lap_time = self.ir["SessionTime"] - self.lap_start_time
                    self.lap_start_time = self.ir["SessionTime"]
                    self.prev_lap = lap

                if self.prev_recorded_lap != lap_completed and lap_dist_pct > 0.075:

                    lap_time = self.ir["LapLastLapTime"]

                    if lap_time == -1.0:
                        lap_time = self.pending_lap_time

                    if lap_time != 0.0:
                        print(f"Lap {self.ir['LapCompleted']}: {format_time(lap_time)}")
                        self.current_stint.laps.append(lap_time)

                    self.prev_recorded_lap = lap_completed

                if self.end_stint:

                    self.current_stint.end_stint(
                        time=time,
                        position=position,
                        incidents=incidents,
                        fast_repairs=fast_repairs,
                    )
                    self.stints.append(self.current_stint)
                    self.current_stint = None
                    self.end_stint = False

            self.prev_pit_active = pit_active

    def _check_tires(self) -> bool:
        return (
            self.ir["dpLFTireChange"]
            or self.ir["dpRFTireChange"]
            or self.ir["dpLRTireChange"]
            or self.ir["dpRRTireChange"]
        )
