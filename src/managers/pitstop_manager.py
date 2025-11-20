from queue import Queue
from typing import Optional
from src.managers.base_manager import BaseManager
from src.context.race_context import RaceContext
from src.models.pitstop import PitStop
from src.api.task_types import get_task_dict, TaskType


class PitstopManager(BaseManager):
    required_fields = {
        "SessionTime": "session_time",
        "PitRepairLeft": "repair_time",
        "PitOptRepairLeft": "repair_opt_time",
        "dpFuelAddKg": "fuel_add_amt",
        "FuelLevel": "fuel_level",
        "FuelLevelPct": "fuel_level_pct",
        "dpFuelFill": "fuel_fill",
        "dpRFTireChange": "right_front",
        "dpLFTireChange": "left_front",
        "dpRRTireChange": "right_rear",
        "dpLRTireChange": "left_rear",
        "FastRepairUsed": "fast_repair_used",
    }

    session_time: Optional[float]
    repair_time: Optional[float]
    repair_opt_time: Optional[float]
    fuel_add_amt: Optional[float]
    fuel_level: Optional[float]
    fuel_level_pct: Optional[float]
    fuel_fill: Optional[bool]
    right_front: Optional[bool]
    left_front: Optional[bool]
    right_rear: Optional[bool]
    left_rear: Optional[bool]
    fast_repair_used: Optional[bool]

    def __init__(self, context: RaceContext, queue: Queue):
        super().__init__(context, queue)
        self.current_pitstop: Optional[PitStop] = None
    
    def handle_event(self, event, telem, ctx):
        if event == "enter_pit_road":
            self._handle_enter_pit_road()
        elif event == "exit_pit_road":
            self._handle_exit_pit_road()
        elif event == "enter_pit_box":
            self._start_service()
        elif event == "exit_pit_box":
            self._end_service()

    def send_pitstop_data(self):
        pass

    def _handle_enter_pit_road(self):
        self.current_pitstop = PitStop(
            stint_id=self.context.stint_id,
            road_enter_time=self.session_time,
        )
    
    def _handle_exit_pit_road(self):
        self.current_pitstop.road_exit_time = self.session_time

    def _start_service(self):
        self.current_pitstop.service_start_time = self.session_time
        self.current_pitstop.required_repair_time = self.repair_time
        self.current_pitstop.optional_repair_time = self.repair_opt_time
        self.current_pitstop.refuel_amount = self._get_refuel_amount()
        self.current_pitstop.left_front = self.left_front
        self.current_pitstop.right_front = self.right_front
        self.current_pitstop.left_rear = self.left_rear
        self.current_pitstop.right_rear = self.right_rear

    def _end_service(self):
        pass
        