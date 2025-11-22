import threading
from typing import Optional, Any
from queue import Queue, Empty
import logging
from requests import HTTPError
from src.api.tasks import APITask, TaskType, PayloadType
from src.api.api_client import APIClient
from src.models import Session, Stint, PitStop, Lap
from src.context.race_context import RaceContext

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class APIWorker(threading.Thread):
    def __init__(
        self,
        context: RaceContext,
        client: APIClient,
        queue: Queue,
        stop_event: threading.Event,
    ):
        super().__init__(daemon=True)
        self.context = context
        self.client = client
        self.queue = queue
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            try:
                task = self.queue.get(timeout=1)
                if task is None:
                    break
                self.process_task(task)
                self.queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.exception("Error processing task: %s", e)

    def process_task(self, task: APITask):
        task_type = task.type
        payload = task.payload

        handlers = {
            TaskType.SESSION.value: self._process_session,
            TaskType.STINT_CREATE.value: self._process_stint_create,
            TaskType.STINT_UPDATE.value: self._process_stint_update,
            TaskType.LAP.value: self._process_lap,
            TaskType.PITSTOP_CREATE.value: self._process_pitstop_create,
            TaskType.PITSTOP_UPDATE.value: self._process_pitstop_update,
        }

        handler = handlers.get(task_type)
        if handler:
            handler(payload)
        else:
            logger.warning("Unknown task type: %s", task_type)

    def _is_valid_payload_type(self, payload: Any, expected_type: type):
        if not isinstance(payload, expected_type):
            logger.warning(
                "Invalid payload type: expected %s, got %s",
                expected_type.__name__,
                type(payload).__name__,
            )
            return False

        return True

    def _process_session(self, session: Session):
        if not self._is_valid_payload_type(session, Session):
            return

        logger.info("Posting new session")
        try:
            self.client.post_session(session)
        except HTTPError as e:
            logger.error("HTTP error: %s", e)

    def _process_stint_create(self, stint: Stint):
        if not self._is_valid_payload_type(stint, Stint):
            return

        session_id = stint.session_id

        logger.info("Creating new stint for session %s", session_id)
        latest_stint = self.client.get_latest_stint(session_id)
        stint.number = (latest_stint["number"] + 1) if latest_stint else 1

        response = self.client.post_stint(stint)

        if response and "id" in response:
            stint.id = response["id"]
            self.context.stint_id = stint.id

        logger.info(
            "Created new stint %s for session %s with ID %s",
            stint.number,
            session_id,
            stint.id,
        )

    def _process_stint_update(self, stint: Stint):
        if not self._is_valid_payload_type(stint, Stint):
            return

        response = self.client.patch_stint(stint)

        if response is None:
            logger.warning("Failed to update stint")
        else:
            logger.info("Stint updated successfully")

    def _process_lap(self, lap: Lap):
        if not self._is_valid_payload_type(lap, Lap):
            return
        
        lap_number = lap.number
        stint_id = lap.stint_id

        logger.info(
            "Posting lap %s for stint %s",
            lap_number,
            stint_id,
        )

        response = self.client.post_lap(lap)

        if response is None:
            logger.warning("Failed to post lap %s for stint %s", lap_number, stint_id)
        else:
            logger.info("Lap %s posted successfully for stint %s", lap_number, stint_id)

    def _process_pitstop_create(self, pitstop: PitStop):
        if not self._is_valid_payload_type(pitstop, PitStop):
            return
        
        stint_id = pitstop.stint_id

        logger.info("Creating pitstop for stint %s", stint_id)
        response = self.client.post_pitstop(pitstop)

        if response and "id" in response:
            pitstop.pitstop_id = response["id"]
            logger.info("Pitstop posted successfully for stint %s", stint_id)
        else:
            logger.warning("Failed to post pitstop for stint %s", stint_id)

    def _process_pitstop_update(self, pitstop: PitStop):
        if not self._is_valid_payload_type(pitstop, PitStop):
            return
        
        logger.info("Updating pitstop %s", pitstop.id)
        response = self.client.patch_pitstop(pitstop)
        if response is None:
            logger.warning("Failed to update pitstop %s", pitstop.id)
        else:
            logger.info("Pitstop %s updated succesfully", pitstop.id)
