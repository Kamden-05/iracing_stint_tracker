from typing import Optional
from queue import Queue
import logging
from src.managers.base_manager import BaseManager
from src.models import Stint
from src.context import RaceContext
from src.api import TaskType
from src.exporters import ExcelExporter

logger = logging.getLogger(__name__)


class StintManager(BaseManager):
    required_fields = {
        "DriverInfo": "driver_info",
        "SessionTime": "session_time",
        "PlayerCarIdx": "player_car_id",
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

    def __init__(
        self, context: RaceContext, queue: Queue, excel: Optional[ExcelExporter]
    ):
        super().__init__(context, queue, excel)
        self.current_stint = None
        self.last_lap_completed = 0

        self.event_handlers = {
            "session_start": self._on_session_start,
            "enter_pit_box": self._on_enter_pit_box,
            "exit_pit_box": self._on_exit_pit_box,
            "session_finish": self._on_session_finish,
        }

    def on_tick(self, telem):
        super().on_tick(telem)

        self._check_for_new_lap()

    def _get_driver_name(self) -> str:
        car_id = self.player_car_id
        drivers = self.driver_info["Drivers"]

        driver = next(
            (d for d in drivers if d["CarIdx"] == car_id and not d["IsSpectator"]),
            None,
        )

        if driver is None:
            logger.warning("Driver name not found for car_id=%s", car_id)
            return ""

        return driver["UserName"]

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

    def _on_session_start(self):
        self._on_exit_pit_box()

    def _on_enter_pit_box(self):
        self._on_session_finish()

    def _on_exit_pit_box(self):
        if self.current_stint:
            return

        # TODO replace context.user_name with name from IRSDK
        self.current_stint = Stint(
            session_id=self.context.session_id,
            driver_name=self._get_driver_name(),
            start_time=self.session_time,
            start_position=self.position,
            start_incidents=self.incidents,
            start_fuel=self.fuel_level,
        )

        self.last_lap_completed = self.lap_completed or 0
        self._post_stint_data()

        logger.info("stint started")

    def _update_stint(self):
        if self.current_stint:
            self.current_stint.end_time = self.session_time
            self.current_stint.end_position = self.position
            self.current_stint.end_incidents = self.incidents
            self.current_stint.end_fuel = self.fuel_level

            self._patch_stint_data()
            logger.info("stint updated")

    def _on_session_finish(self):
        if not self.current_stint:
            return

        self._update_stint()
        self.current_stint = None
        logger.info("stint ended")
