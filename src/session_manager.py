from src.stint import Stint
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
        self.last_recorded_lap = -1
        self.end_stint = False
        self.race_started = False
        self.prev_lap_time = -99999.0
        self.race_started = False
        self.race_ended = False
        self.final_lap = -1

    def connect(self) -> bool:
        if not self.is_connected and not self.race_ended:
            self.is_connected = self.ir.startup()
            if self.is_connected:
                print("Connected to iRacing")
            else:
                logging.warning("Failed to connect to iRacing")
        return self.is_connected

    def disconnect(self) -> None:
        if self.is_connected:
            if self.current_stint:
                self._end_stint(self.current_stint)
                self.stints.append(self.current_stint)
                print(f"\nStint {len(self.stints)}")
                print(self.current_stint.display())

            self.ir.shutdown()
            self.is_connected = False
            logging.info("Disconnected from iRacing")

    def check_race_status(self) -> None:
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
            if self.final_lap == -1:
                self.final_lap = self.ir["Lap"]
            elif self.final_lap == self.last_recorded_lap:
                self.race_ended = True
                self.disconnect()

    def process_race(self):
        self.ir.freeze_var_buffer_latest()
        self.check_race_status()
        if self.race_started and not self.race_ended:
            car_id = self.ir["PlayerCarIdx"]
            pit_active = self.ir["PitstopActive"]
            lap = self.ir["LapCompleted"]

            """ 
            if pit inactive and no stint, start next stint
            if pit active and last pit inactive, record the pit data
            if pit inactive and last pit active, change the flag so we know to end the stint
            """
            if not pit_active and self.current_stint is None:
                self.current_stint = self._start_stint(car_id)

            elif pit_active and not self.prev_pit_active:
                self.current_stint = self._record_pit(self.current_stint)

            elif not pit_active and self.prev_pit_active:
                self.end_stint = True

            # record laps, make sure that the in lap has only been recorded once we've pit and crossed the start/finish line
            if self.current_stint:
                lap_time = self.ir["LapLastLapTime"]

                if (
                    lap != self.last_recorded_lap
                    and lap_time != self.prev_lap_time
                    and lap_time != 0
                ):
                    print(f"Recording lap {lap}: {lap_time}")
                    self.current_stint.laps.append(lap_time)
                    self.last_recorded_lap = lap
                    self.prev_lap_time = lap_time

                if self.end_stint:
                    self.current_stint = self._end_stint(self.current_stint)
                    self.stints.append(self.current_stint)
                    print(f"\nStint {len(self.stints)}")
                    print(self.current_stint.display())
                    self.current_stint = None
                    self.end_stint = False

            self.prev_pit_active = pit_active

    def _start_stint(self, car_id: int) -> Stint:
        new_stint = Stint(
            driver=self.ir["DriverInfo"]["Drivers"][car_id]["UserName"],
            laps=[],
            start_time=self.ir["SessionTime"],
            start_position=self.ir["PlayerCarClassPosition"],
            start_incidents=self.ir["PlayerCarMyIncidentCount"],
            start_fuel=self.ir["FuelLevel"],
            start_fast_repairs=self.ir["FastRepairUsed"],
        )

        return new_stint

    def _end_stint(self, stint: Stint) -> Stint:
        stint.stint_length = self.ir["SessionTime"] - stint.start_time
        stint.end_position = self.ir["PlayerCarClassPosition"]
        stint.incidents = self.ir["PlayerCarMyIncidentCount"] - stint.start_incidents
        stint.repairs = self._check_repairs(stint)
        stint.out_lap = stint.laps[0] if stint.laps else 0.0
        if not self.race_ended:
            stint.in_lap = stint.laps[-1] if stint.laps else 0.0
        stint.avg_lap = (
            float(sum(stint.laps)) / float(len(stint.laps)) if stint.laps else 0.0
        )
        stint.laps_completed = len(stint.laps)
        stint.pit_service_time = (
            self.ir["SessionTime"] - stint.pit_service_start_time
            if stint.pit_service_start_time
            else 0.0
        )
        return stint

    def _record_pit(self, stint: Stint) -> Stint:
        stint.required_repair_time = self.ir["PitRepairLeft"]
        stint.optional_repair_time = self.ir["PitOptRepairLeft"]
        stint.end_fuel = self.ir["FuelLevel"]
        stint.refuel_amount = max(self.ir["dpFuelAddKg"] - stint.end_fuel, 0.0)

        stint.tire_change = self._check_tires()
        stint.pit_service_start_time = self.ir["SessionTime"]
        return stint

    def _check_repairs(self, stint: Stint) -> bool:
        if stint.required_repair_time + stint.optional_repair_time > 0:
            return True
        elif self.ir["FastRepairUsed"] - stint.start_fast_repairs > 0:
            return True
        else:
            return False

    def _check_tires(self) -> bool:
        return (
            self.ir["dpLFTireChange"]
            or self.ir["dpRFTireChange"]
            or self.ir["dpLRTireChange"]
            or self.ir["dpRRTireChange"]
        )
