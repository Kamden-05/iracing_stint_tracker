import requests
from queue import Queue, Empty
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(
        self,
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.s.close()

    """Session Methods"""

    def post_session(self, session_data: dict):
        r = self.s.post(f"{self.base_url}/sessions/", json=session_data)
        return r.json()

    """Stint Methods"""

    def get_latest_stint(self, session_id: int):
        r = self.s.get(f"{self.base_url}/sessions/{session_id}/stints/latest")
        if r.status_code == 204:
            return None
        else: 
            return r.json()

    def post_stint(self, stint_data: dict):
        session_id = stint_data["session_id"]
        r = self.s.post(
            f"{self.base_url}/sessions/{session_id}/stints/", json=stint_data
        )
        
        return r.json()

    def put_stint(self, stint_data: dict):
        session_id = stint_data["session_id"]
        r = self.s.put(f"{self.base_url}/{session_id}/stints/", json=stint_data)
        return r.json()

    """Lap Methods"""

    def post_lap(self, lap_data: dict):
        stint_id = lap_data["stint_id"]
        r = self.s.post(
            f"{self.base_url}/stints/{stint_id}/laps/", json=lap_data.to_dict()
        )
        return r.json()


def process_api_queue(client: APIClient, q: Queue):

    while True:
        try:
            task = q.get(timeout=1)

            if task is None:
                break

            task_type = task["type"]
            action = task["action"]
            data = task["data"]

            match task_type:
                case "Session":
                    if action == "create":
                        client.post_session(session_data=data)
                case "Stint":
                    if action == "create":
                        client.post_stint(stint_data=data)
                    elif action == "update":
                        client.put_stint(stint_data=data)
                case "Lap":
                    if action == "create":
                        client.post_lap(lap_data=data)
                case _:
                    raise ValueError(f'Ivalid task type: {task_type}')

        except Empty:
            continue
        except Exception as e:
            logger.exception(f'Error processing taskL {e}')