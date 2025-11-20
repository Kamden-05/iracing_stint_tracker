import threading
from typing import Optional
from queue import Queue, Empty
import logging
from src.api.task_types import TaskType
from src.api.api_client import APIClient
from src.models.stint import Stint

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class APIWorker(threading.Thread):
    def __init__(self, client: APIClient, queue: Queue, stop_event: threading.Event):
        super().__init__(daemon=True)
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

    def process_task(self, task: dict):
        task_type = task["type"]
        data = task["data"]

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
            handler(data)
        else:
            logger.warning("Unknown task type: %s", task_type)

    def _process_session(self, session_data: dict):
        logger.info("Posting new session")
        self.client.post_session(session_data)

    def _process_stint_create(self, task_data: dict):
        session_id = task_data["session_id"]
        stint: Optional[Stint] = task_data["stint_obj"]

        if not stint:
            logger.warning("No stint object provided in task_data")
            return

        logger.info("Creating new stint for session %s", session_id)
        latest_stint = self.client.get_latest_stint(session_id=session_id)
        stint.number = (latest_stint["number"] + 1) if latest_stint else 1

        response = self.client.post_stint(stint.post_dict())

        if response and "id" in response:
            stint.id = response["id"]

        logger.info(
            "Created new stint %s for session %s with ID %s",
            stint.number,
            session_id,
            stint.id,
        )

    def _process_stint_update(self, stint_data: dict):
        stint_id = stint_data.get("id")
        if not stint_id:
            logger.warning("Cannot update stint without ID")
            return

        logger.info("Updating stint %s", stint_id)
        response = self.client.patch_stint(stint_data)
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

    def _process_pitstop_create(self, pit_data: dict):
        stint_id = pit_data.get("stint_id")
        logger.info("Posting pitstop for stint %s", stint_id)

        response = self.client.post_pitstop(pit_data)

        if response is None:
            logger.warning("Failed to post pitstop for stint %s", stint_id)
        else:
            logger.info("Pitstop posted successfully for stint %s", stint_id)

    def _process_pitstop_update(self, pit_data: dict):
        pitstop_id = pit_data.get("pitstop_id")
        if not pitstop_id:
            logger.warning("Cannot update pitstop without ID")

        logger.info("Updating pitstop %s", pitstop_id)
        response = self.client.patch_pitstop(pit_data)
        if response is None:
            logger.warning("Failed to update pitstop %s", pitstop_id)
        else:
            logger.info("Pitstop %s updated succesfully", pitstop_id)
