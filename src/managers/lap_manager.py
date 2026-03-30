from typing import Optional
import logging
from src.managers.base_manager import BaseManager
from src.models import Lap
from src.api import TaskType

logger = logging.getLogger(__name__)


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

    def __init__(self, context, queue, excel):
        super().__init__(context, queue, excel)
        self.last_lap_completed = 0
        self.lap_start_time = None
        self.event_handlers = {}

    def on_tick(self, telem: dict[str, any]):
        super().on_tick(telem)

        self._check_for_new_lap()

    def _check_for_new_lap(self):

        if self.lap_completed == 0:
            # pre-first-lap initialization
            if self.current_lap == 1 and not self.lap_start_time:
                self.lap_start_time = self.session_time

            return

        if self.lap_completed > self.last_lap_completed:

            if self.last_lap_time and self.last_lap_time > 0.0:
                lap_time = self.last_lap_time
            elif self.lap_start_time is not None:
                lap_time = self.session_time - self.lap_start_time
            else:
                logger.warning(
                    "Skipping lap: lap_completed=%s session_time=%s",
                    self.lap_completed,
                    self.session_time,
                )

            self._post_lap_info(lap_time)
            self.last_lap_completed = self.lap_completed
            self.lap_start_time = self.session_time

    def _post_lap_info(self, lap_time: float):
        lap = Lap(
            stint_id=self.context.stint_id,
            number=self.lap_completed,
            time=lap_time,
        )

        self._send_data(TaskType.LAP, lap)
