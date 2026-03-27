from queue import Queue
from typing import Optional
from src.managers.base_manager import BaseManager
from src.context.race_context import RaceContext
from src.models.pitstop import PitStop
from src.api.tasks import TaskType
from src.exporters.excel_exporter import ExcelExporter


class PitstopManager(BaseManager):
    required_fields = {
        "SessionTime": "session_time",
        "PitRepairLeft": "required_repair_time",
        "PitOptRepairLeft": "optional_repair_time",
        "FuelLevel": "fuel_level",
        "dpRFTireChange": "right_front",
        "dpLFTireChange": "left_front",
        "dpRRTireChange": "right_rear",
        "dpLRTireChange": "left_rear",
        "FastRepairAvailable": "fast_repair_available",
    }

    session_time: Optional[float]
    required_repair_time: Optional[float]
    optional_repair_time: Optional[float]
    fast_repair_available: Optional[int]
    fuel_level: Optional[float]
    right_front: Optional[bool]
    left_front: Optional[bool]
    right_rear: Optional[bool]
    left_rear: Optional[bool]

    def __init__(self, context: RaceContext, queue: Queue, excel: ExcelExporter):
        super().__init__(context, queue, excel)
        self.current_pitstop: Optional[PitStop] = None
        self.road_enter_time: Optional[float] = None

    def handle_event(self, event_name: str):
        if event_name == "enter_pit_road":
            self._handle_enter_pit_road()
        elif event_name == "exit_pit_road":
            self._handle_exit_pit_road()
        elif event_name == "enter_pit_box":
            self._handle_enter_pit_box()
        elif event_name == "exit_pit_box":
            self._handle_exit_pit_box()
        elif event_name == "driver_swap_in":
            self._handle_driver_swap_in()
        elif event_name == "driver_swap_out":
            self._handle_driver_swap_out()

    def _reset_pit(self):
        self.current_pitstop = None
        self.road_enter_time = None

    def _post_pitstop_data(self):
        self._send_data(TaskType.PITSTOP_CREATE, self.current_pitstop)

    def _patch_pitstop_data(self):
        self._send_data(TaskType.PITSTOP_UPDATE, self.current_pitstop)

    def _handle_enter_pit_road(self):
        self.road_enter_time = self.session_time
        print(f"enter pit road: {self.road_enter_time}")

    def _handle_exit_pit_road(self):
        if self.current_pitstop is not None:
            self.current_pitstop.road_exit_time = self.session_time
            self._patch_pitstop_data()

        print(f"exit pit road: {self.current_pitstop}")
        self._reset_pit()

    def _handle_enter_pit_box(self):
        if self.road_enter_time is None:
            self.road_enter_time = self.session_time

        self.current_pitstop = PitStop(
            stint_id=self.context.stint_id,
            road_enter_time=self.road_enter_time,
            service_start_time=self.session_time,
            required_repair_time=self.required_repair_time,
            optional_repair_time=self.optional_repair_time,
            start_fast_repairs=self.fast_repair_available,
            fuel_start_amount=self.fuel_level,
            left_front=self.left_front,
            right_front=self.right_front,
            left_rear=self.left_rear,
            right_rear=self.right_rear,
        )

        self._post_pitstop_data()
        print(f"enter pit: {self.current_pitstop}")

    def _handle_exit_pit_box(self):
        if self.current_pitstop is not None:
            self.current_pitstop.service_end_time = self.session_time
            self.current_pitstop.fuel_end_amount = self.fuel_level
            self.current_pitstop.end_fast_repairs = self.fast_repair_available

        print(f"exit box: {self.current_pitstop}")

    def _handle_driver_swap_in(self):
        self.current_pitstop = PitStop(
            stint_id=self.context.stint_id,
            id=self.context.pitstop_id,
        )

    def _handle_driver_swap_out(self):
        self._reset_pit()
