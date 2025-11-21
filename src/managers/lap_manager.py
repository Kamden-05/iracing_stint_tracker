from typing import Optional
from src.managers.base_manager import BaseManager
from src.models.lap import Lap
from src.api.tasks import TaskType


class LapManager(BaseManager):
    required_fields = {
        "SessionTime": "session_time",
        "LapCompleted": "lap_completed",
        "LapLastLapTime": "last_lap_time",
        "Lap": "current_lap",
    }

    session_time: Optional[float]
    lap_completed: Optional[int]
    last_lap_time: Optional[float]
    current_lap: Optional[int]

    def __init__(self, context, queue):
        super().__init__(context, queue)
        self.last_lap_completed = 0
        self.lap_start_time = None

    def on_tick(self, telem: dict[str, any], state):
        super().on_tick(telem, state)

        self._check_for_new_lap()

    def _check_for_new_lap(self):
        if self.current_lap == 1 and self.lap_completed == 0 and not self.lap_start_time:
            self.lap_start_time = self.session_time

        if self.lap_completed == 0:
            return

        if self.lap_completed > self.last_lap_completed:

            if self.last_lap_time and self.last_lap_time > 0.0:
                lap_time = self.last_lap_time
            else:
                lap_time = self.session_time - self.lap_start_time

            self._post_lap_info(lap_time)
            self.last_lap_completed = self.lap_completed
            self.lap_start_time = self.session_time

    def _post_lap_info(self, lap_time: float):
        data = Lap(
            stint_id=self.context.stint_id,
            number=self.lap_completed,
            time=lap_time,
        ).to_dict()

        self._send_data(TaskType.LAP, data)
