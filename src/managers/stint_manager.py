from typing import Optional
from queue import Queue
from src.managers.base_manager import BaseManager
from src.models.stint import Stint
from src.context.race_context import RaceContext
from src.api.tasks import TaskType
from src.exporters.excel_exporter import ExcelExporter


class StintManager(BaseManager):
    required_fields = {
        "DriverInfo": "driver_info",
        "SessionTime": "session_time",
        "PlayerCarClassPosition": "position",
        "PlayerCarMyIncidentCount": "incidents",
        "FuelLevel": "fuel_level",
        "LapCompleted": "lap_completed",
    }

    driver_info: Optional[dict]
    session_time: Optional[float]
    position: Optional[int]
    incidents: Optional[int]
    fuel_level: Optional[float]
    lap_completed: Optional[int]

    def __init__(self, context: RaceContext, queue: Queue, excel: ExcelExporter):
        super().__init__(context, queue, excel)
        self.current_stint = None
        self.last_lap_completed = 0

    def on_tick(self, telem, state):
        super().on_tick(telem, state)

        self._check_for_new_lap()

    def _check_for_new_lap(self):
        if not self.current_stint or self.lap_completed is None:
            return

        if self.lap_completed > self.last_lap_completed:
            self._update_stint()
            self.last_lap_completed = self.lap_completed

    def _post_stint_data(self):
        self._send_data(TaskType.STINT_CREATE, self.current_stint)

    def _patch_stint_data(self):
        self._send_data(TaskType.STINT_UPDATE, self.current_stint)

    def handle_event(self, event_name: str):
        if event_name == "session_start":
            self._handle_session_start()
        elif event_name == "enter_pit_box":
            self._handle_enter_pit_box()
        elif event_name == "exit_pit_box":
            self._start_stint()
        elif event_name == "finish_session":
            self._end_stint()

    def _handle_session_start(self):
        self._start_stint()

    def _handle_enter_pit_box(self):
        self._end_stint()

    def _start_stint(self):
        if self.current_stint:
            return

        self.current_stint = Stint(
            session_id=self.context.session_id,
            driver_name=self.context.user_name,
            start_time=self.session_time,
            start_position=self.position,
            start_incidents=self.incidents,
            start_fuel=self.fuel_level,
        )

        self.last_lap_completed = self.lap_completed or 0
        self._post_stint_data()

        print("stint started")

    def _update_stint(self):
        if self.current_stint:
            self.current_stint.end_time = self.session_time
            self.current_stint.end_position = self.position
            self.current_stint.end_incidents = self.incidents
            self.current_stint.end_fuel = self.fuel_level

            self._patch_stint_data()
            print("stint updated")

    def _end_stint(self):
        if not self.current_stint:
            return

        self._update_stint()
        self.current_stint = None
        print("stint ended")
