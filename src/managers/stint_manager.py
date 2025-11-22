from typing import Optional
from queue import Queue
from src.managers.base_manager import BaseManager
from src.models.stint import Stint
from src.context.race_context import RaceContext
from src.api.tasks import TaskType


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

    def __init__(self, context: RaceContext, queue: Queue):
        super().__init__(context, queue)
        self.current_stint = None
        self.last_lap_completed = 0
        self.pending_stint_end = False

    def on_tick(self, telem, state):
        super().on_tick(telem, state)

        self._check_for_new_lap()

    def _check_for_new_lap(self):
        if not self.pending_stint_end:
            if self.lap_completed is None:
                return
            
            if self.lap_completed > self.last_lap_completed:
                self._update_stint()
                self.last_lap_completed = self.lap_completed

    def handle_event(self, event, telem, ctx):
        if event == "exit_pit_road":
            self._handle_exit_pit_road()
        elif event == "enter_pit_road":
            self._handle_enter_pit_road()
        elif event == "session_start":
            self._handle_session_start()
        elif event == "enter_pit_box":
            self._handle_enter_pit_box()


    def _handle_session_start(self):
        self._start_stint()

    def _handle_enter_pit_road(self):
        self._update_stint()
        self.pending_stint_end = True

    def _handle_exit_pit_road(self):
        if self.pending_stint_end:
            self.pending_stint_end = False
        else:
            self._start_stint()

    def _handle_enter_pit_box(self):
        self._end_stint()
        self.pending_stint_end = False

    def _start_stint(self):
        self.current_stint = Stint(
            session_id=self.context.session_id,
            driver_name=self.context.user_name,
            start_time=self.session_time,
            start_position=self.position,
            start_incidents=self.incidents,
            start_fuel=self.fuel_level,
        )

        self._send_data(TaskType.STINT_CREATE, self.current_stint)
    
    def _update_stint(self):
        if self.current_stint and not self.current_stint.is_complete:
            self.current_stint.end_time = self.session_time
            self.current_stint.end_position = self.position
            self.current_stint.end_incidents = self.incidents
            self.current_stint.end_fuel = self.fuel_level

            self._send_data(TaskType.STINT_UPDATE, self.current_stint)

    def _end_stint(self):
        self.current_stint.is_complete = True
        self._send_data(TaskType.STINT_UPDATE, self.current_stint)

        self.current_stint = None
