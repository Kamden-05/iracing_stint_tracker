import threading
from typing import Optional
from queue import Queue, Empty
import logging
from requests import HTTPError
from src.api.tasks import APITask, TaskType
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

    def _process_session(self, session: Session):
        if not isinstance(session, Session):
            logger.warning(
                "Invalid payload type: expected %s, got %s",
                Session.__name__,
                type(session).__name__,
            )
            return

        logger.info("Posting new session")
        try:
            self.client.post_session(session.to_json())
        except HTTPError as e:
            logger.error("HTTP error: %s", e)

    def _process_stint_create(self, stint: Stint):
        if not isinstance(stint, Stint):
            logger.warning(
                "Invalid payload type: expected %s, got %s",
                stint.__name__,
                type(stint).__name__,
            )
            return

        session_id = stint.session_id

        logger.info("Creating new stint for session %s", session_id)
        latest_stint = self.client.get_latest_stint(session_id=session_id)
        stint.number = (latest_stint["number"] + 1) if latest_stint else 1

        response = self.client.post_stint(stint.to_post_json())

        if response and "id" in response:
            stint.id = response["id"]
            self.context.stint_id = stint.id

        logger.info(
            "Created new stint %s for session %s with ID %s",
            stint.number,
            session_id,
            stint.id,
        )

    def _process_stint_update(self, task_data: dict):
        stint_id = task_data.get("stint_id")
        if not stint_id:
            logger.warning("Cannot update stint without ID")
            return

        stint: Optional[Stint] = task_data["stint_obj"]
        if not stint:
            logger.warning("No stint object provided in task_data")
            return

        logger.info("Updating stint %s", stint_id)
        response = self.client.patch_stint(stint.to_patch_json())
        if response is None:
            logger.warning("Failed to update stint %s", stint_id)
        else:
            logger.info("Stint %s updated successfully", stint_id)

    def _process_lap(self, lap_data: dict):
        lap_number = lap_data.get("lap_number")
        stint_id = lap_data.get("stint_id")

        logger.info(
            "Posting lap %s for stint %s",
            lap_number,
            stint_id,
        )

        response = self.client.post_lap(lap_data)

        if response is None:
            logger.warning("Failed to post lap %s for stint %s", lap_number, stint_id)
        else:
            logger.info("Lap %s posted successfully for stint %s", lap_number, stint_id)

    def _process_pitstop_create(self, task_data: dict):
        stint_id = task_data.get("stint_id")
        pitstop: Optional[PitStop] = task_data.get("pitstop_obj")

        if not pitstop:
            logger.warning("No pitstop object provided in task_data")
            return

        logger.info("Creating pitstop for stint %s", stint_id)
        response = self.client.post_pitstop(pitstop.to_post_dict())

        if response and "id" in response:
            pitstop.pitstop_id = response["id"]
            logger.info("Pitstop posted successfully for stint %s", stint_id)
        else:
            logger.warning("Failed to post pitstop for stint %s", stint_id)

    def _process_pitstop_update(self, task_data: dict):
        pitstop_id = task_data.get("pitstop_id")
        if not pitstop_id:
            logger.warning("Cannot update pitstop without ID")
            return

        pitstop: Optional[PitStop] = task_data["pitstop_obj"]
        if not pitstop:
            logger.warning("No pitstop object provided in task_data")
            return

        logger.info("Updating pitstop %s", pitstop_id)
        response = self.client.patch_pitstop(pitstop.to_patch_json())
        if response is None:
            logger.warning("Failed to update pitstop %s", pitstop_id)
        else:
            logger.info("Pitstop %s updated succesfully", pitstop_id)
