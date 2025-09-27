from src.stint import Stint
from src.utils import format_time
from typing import List
import irsdk
import logging
import yaml


class SessionManager:

    def __init__(self, ir=None):
        self.ir = ir or irsdk.IRSDK()
        self.is_connected: bool = False
        self.stints: List[Stint] = []
        self.prev_pit_active: bool = False
        self.current_stint: Stint = None
        self.prev_lap = 0
        self.prev_recorded_lap = 0
        self.started = False
        self.ended = False
        self.final_lap = -999
        self.lap_start_time = 0.0
        self.lap_start_tick = 0
        self.pending_lap_time = 0.0
        self.pit_road_lap = -1
        self.prev_pit_road = False
        self.pit_active_lap = -1
        self.pending_stint_end = False

    def connect(self) -> bool:
        if not self.is_connected:
            self.is_connected = self.ir.startup()
            if self.is_connected:
                print("Connected to iRacing")
        return self.is_connected

    def disconnect(self) -> None:
        if self.is_connected:
            if self.current_stint:
                self._end_stint(self.current_stint, final_stint=True)
                self.stints.append(self.current_stint)
                self.current_stint = None

            self.ir.shutdown()
            self.is_connected = False
            logging.info("Disconnected from iRacing")

    def get_session_type(self) -> str:
        """
        Returns the current session type as a string: "Race", "Practice", "Qualify", "Warmup"
        """
        raw = self.ir["SessionInfo"]
        if not raw:
            return None

        # If it's a dict already, use it directly; otherwise parse YAML
        if isinstance(raw, dict):
            info = raw
        else:
            try:
                info = yaml.safe_load(raw) or {}
            except Exception:
                return None

        session_num = self.ir["SessionNum"]

        try:
            sessions = info.get("Sessions", [])
            for sess in sessions:
                if int(sess.get("SessionNum", -1)) == session_num:
                    return str(sess.get("SessionType", "Race"))
        except Exception:
            return None

        # default if we can't find it
        return "Race"

    def check_start(self) -> bool:
        if not self.started:
            return (
                self.ir["SessionState"] == irsdk.SessionState.racing
                and self.ir["PlayerCarClassPosition"] > 0
            )
        else:
            return True

    def check_end(self) -> bool:
        flags = self.ir["SessionFlags"]
        session_state = self.ir["SessionState"]
        # session_type = self.get_session_type()
        if flags & irsdk.Flags.checkered:
            if self.final_lap == -999:
                self.final_lap = self.ir["Lap"]
            elif self.final_lap <= self.prev_recorded_lap:
                return True
        return False

    def process_race(self) -> None:
        self.ir.freeze_var_buffer_latest()
        self.started = self.check_start()
        self.ended = self.check_end()

        tick = self.ir["SessionTick"]
        lap = self.ir["Lap"]
        lap_completed = self.ir["LapCompleted"]
        on_pit_road = self.ir["OnPitRoad"]
        pit_active = self.ir["PitstopActive"]
        session_time = self.ir["SessionTime"]
        position = self.ir["PlayerCarClassPosition"]
        incidents = self.ir["PlayerCarMyIncidentCount"]
        fuel = self.ir["FuelLevel"]
        fast_repairs = self.ir["FastRepairUsed"]

        # TODO: if not started and not ended: start stint at the next pit stop then started=true
        if self.started and not self.ended:

            if on_pit_road and not self.prev_pit_road:
                self.pit_road_lap = lap

            if not pit_active and self.current_stint is None:

                car_id = self.ir["PlayerCarIdx"]
                driver = self.ir["DriverInfo"]["Drivers"][car_id]["UserName"]

                self.current_stint = Stint(
                    stint_id=len(self.stints) + 1,
                    driver=driver,
                    start_time=session_time,
                    start_position=position,
                    start_incidents=incidents,
                    start_fuel=fuel,
                    start_fast_repairs=fast_repairs,
                )

            elif pit_active and not self.prev_pit_active:
                self.pit_active_lap = lap

                required_repair = self.ir["PitRepairLeft"]
                optional_repair = self.ir["PitOptRepairLeft"]
                refuel = 0.0
                if self.ir["dpFuelFill"]:
                    fuel_add = self.ir["dpFuelAddKg"]
                    max_fuel = fuel / self.ir["FuelLevelPct"]
                    refuel = min(fuel_add, max_fuel - fuel)

                self.current_stint.record_pit(
                    required_repair_time=required_repair,
                    optional_repair_time=optional_repair,
                    end_fuel=fuel,
                    reufel_amount=refuel,
                    tires=self._check_tires(),
                    session_time=session_time,
                )

            elif not pit_active and self.prev_pit_active:
                self.pending_stint_end = True

            if self.current_stint:

                # TODO: make sure lap times work if we pit before the s/f line

                if lap > self.prev_lap:
                    self.pending_lap_time = session_time - self.lap_start_time
                    self.lap_start_time = session_time
                    self.lap_start_tick = tick
                    self.prev_lap = lap

                    if self.pending_stint_end:
                        self.pit_active_lap = lap

                if (
                    self.prev_recorded_lap < lap_completed
                    and tick >= self.lap_start_tick + 120
                ):

                    lap_time = self.ir["LapLastLapTime"]

                    if lap_time == -1.0:
                        lap_time = self.pending_lap_time

                    if lap_time != 0.0:
                        print(f"Lap {lap_completed}: {format_time(lap_time)}")
                        self.current_stint.record_lap(lap_time)

                    self.prev_recorded_lap = lap_completed

                if self.pending_stint_end:
                    if (
                        self.pit_active_lap > self.pit_road_lap
                        and self.prev_recorded_lap == self.pit_road_lap
                    ):
                        self._end_stint(self.current_stint)
                        self.stints.append(self.current_stint)
                        self.current_stint = None
                        self.pending_stint_end = False

            self.prev_pit_road = on_pit_road
            self.prev_pit_active = pit_active

    def _check_tires(self) -> bool:
        return bool(
            self.ir["dpLFTireChange"]
            or self.ir["dpRFTireChange"]
            or self.ir["dpLRTireChange"]
            or self.ir["dpRRTireChange"]
        )

    def _end_stint(self, stint: Stint, final_stint=False) -> None:
        stint.end_stint(
            time=self.ir["SessionTime"],
            position=self.ir["PlayerCarClassPosition"],
            incidents=self.ir["PlayerCarMyIncidentCount"],
            fast_repairs=self.ir["FastRepairUsed"],
            end_fuel=self.ir["FuelLevel"],
            final=final_stint,
        )

    def _get_tick_data(self) -> dict:

        return {
            "pit_active": self.ir["PitstopActive"],
            "session_time": self.ir["SessionTime"],
            "position": self.ir["PlayerCarClassPosition"],
            "incidents": self.ir["PlayerCarMyIncidentCount"],
            "fuel_level": self.ir["FuelLevel"],
            "fast_repairs": self.ir["FastRepairUsed"],
            "lap": self.ir["Lap"],
            "lap_completed": self.ir["LapCompleted"],
            "lap_dist_pct": self.ir["LapDistPct"],
            "lap_time": self.ir["LapLastLapTime"],
            "required_repair": self.ir["PitRepairLeft"],
            "optional_repair": self.ir["PitOptRepairLeft"],
            "fuel_add": self.ir["dpFuelAddKg"],
        }
