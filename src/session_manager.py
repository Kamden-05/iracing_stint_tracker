from src.stint import Stint
from typing import List
import irsdk
import logging


class SessionManager:

    def __init__(self):
        self.ir = irsdk.IRSDK()
        self.is_connected: bool = False
        self.stints: List[Stint] = []
        self.stint_count: int = 0
        self.prev_pit_active: bool = False
        self.current_stint: Stint = None

    def connect(self) -> bool:
        if not self.is_connected:
            self.is_connected = self.ir.startup()
            if self.is_connected:
                print("Connected to iRacing")
            else:
                logging.warning("Failed to connect to iRacing")
        return self.is_connected

    def disconnect(self) -> None:
        if self.is_connected:
            self.ir.shutdown()
            self.is_connected = False
            logging.info("Disconnected from iRacing")

    def process_race(self):
        self.ir.freeze_var_buffer_latest()
        car_id = self.ir["PlayerCarIdx"]
        pit_active = self.ir["PitstopActive"]

        """ 
        if pit inactive and no stint, start next stint
        if pit active and last pit inactive, record the pit data
        if pit inactive and last pit active, end the stint
        """
        if not pit_active and self.current_stint is None:
            self.current_stint = self._start_stint(car_id)
        elif pit_active and not self.prev_pit_active:
            self.current_stint = self._record_pit(self.current_stint)
        elif not pit_active and self.prev_pit_active:
            self.current_stint = self._end_stint(self.current_stint)
            self.stints.append(self.current_stint)
            self.current_stint = None

        # TODO: record lap times

        self.prev_pit_active = pit_active

    def _start_stint(self, car_id: int) -> Stint:
        new_stint = Stint(
            driver=self.ir["DriverInfo"]["Drivers"][car_id]["UserName"],
            laps=[],
            start_time=self.ir["SessionTime"],
            start_position=self.ir["CarIdxClassPosition"],
            start_incidents=self.ir["PlayerCarMyIncidentCount"],
            start_fuel=self.ir["FuelLevel"],
            start_fast_repairs=self.ir["FastRepairAvailable"],
            start_tires_used=self.ir["TireSetsUsed"],
        )

        return new_stint

    def _end_stint(self, stint: Stint) -> Stint:
        stint.end_time = self.ir["CarIdxClassPosition"]
        stint.end_position = self.ir["CarIdxClassPosition"]
        stint.end_incidents = self.ir["PlayerCarMyIncidentCount"]
        stint.out_lap = stint.laps[1] if len(stint.laps) > 0 else 0
        stint.in_lap = stint.laps[-1] if len(stint.laps) > 0 else 0
        return stint

    def _record_pit(self, stint: Stint) -> Stint:
        stint.required_repair_time = self.ir["PitRepairLeft"]
        stint.optional_repair_time = self.ir["PitOptRepairLeft"]
        stint.end_fuel = self.ir["FuelLevel"]
        stint.fuel_add_amount = self.ir["dpFuelAddKg"]
        return stint
