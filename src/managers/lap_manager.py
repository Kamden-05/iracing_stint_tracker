from typing import Optional
from queue import Queue
import logging
from src.managers.base_manager import BaseManager
from src.models import Lap
from src.api import TaskType
from src.context import RaceContext
from src.exporters import ExcelExporter
from src.fsm import States

logger = logging.getLogger(__name__)


class LapManager(BaseManager):
    required_fields = {
        "SessionTime": "session_time",
        "LapCompleted": "lap_completed",
        "LapLastLapTime": "last_lap_time",
        "Lap": "current_lap",
        "SessionTick": "current_tick",
        "SessionNum": "session_num",
    }

    session_time: Optional[float]
    lap_completed: Optional[int]
    last_lap_time: Optional[float]
    current_lap: Optional[int]

    def __init__(
        self,
        context: RaceContext,
        queue: Queue,
        excel: Optional[ExcelExporter],
        delay_ticks: int,
    ):
        super().__init__(context, queue, excel)
        self.last_lap_completed = 0
        self.lap_start_time = None
        self.event_handlers = {}
        self.delay_ticks = delay_ticks
        self.temp_lap_time = None
        self.temp_lap_tick = None

    def on_tick(self, telem: dict[str, any], state: States):
        super().on_tick(telem, state)

        if state in [
            States.ON_TRACK,
            States.ON_PIT_ROAD,
            States.IN_PIT_BOX,
        ]:
            if self._is_new_lap_ready():
                self._record_lap()
        else:
            self.temp_lap_time = None
            self.temp_lap_tick = None
            self.lap_start_time = None

    def _is_new_lap_ready(self) -> bool:
        if self.lap_completed <= 0:
            # pre-first-lap initialization
            if self.current_lap == 1 and self.lap_start_time is None:
                self.lap_start_time = self.session_time

            return False

        if self.lap_completed > self.last_lap_completed:
            self.temp_lap_tick = self.current_tick

            if self.lap_start_time is not None:
                self.temp_lap_time = self.session_time - self.lap_start_time

            self.lap_start_time = self.session_time
            self.last_lap_completed = self.lap_completed

        if self.temp_lap_tick is not None:
            if (self.current_tick - self.temp_lap_tick) >= self.delay_ticks:
                self.temp_lap_tick = None
                return True

        return False

    def _record_lap(self):
        if self.lap_completed == 0:
            logger.info("Skipping lap 0 which had time=%s", self.last_lap_time)
            return

        if self.last_lap_time is not None and self.last_lap_time > 0.0:
            lap_time = self.last_lap_time
        elif self.temp_lap_time is not None:
            lap_time = self.temp_lap_time
        else:
            logger.warning(
                "Skipping lap: lap_completed=%s session_time=%s",
                self.lap_completed,
                self.session_time,
            )
            return

        self._post_lap_info(lap_time)
        self.temp_lap_time = None

    def _post_lap_info(self, lap_time: float):
        lap = Lap(
            stint_id=self.context.stint_id,
            number=self.lap_completed,
            time=lap_time,
        )

        logger.debug("Lap Posted: number=%s time=%s", self.lap_completed, lap_time)

        self._send_data(TaskType.LAP, lap)
