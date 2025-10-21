import requests
import json
from src.stint import Lap
from typing import Any
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

    def post_session(self, session_info: dict):
        r = self.s.post(f"{self.base_url}/sessions/", json=session_info)
        print(r.text)

    """Stint Methods"""

    def get_latest_stint(self, session_id: int):
        r = self.s.get(f"{self.base_url}/sessions/{session_id}/stints/latest")
        print(r.text)

    def post_stint(self, stint_data: dict):
        session_id = stint_data['session_id']
        r = self.s.post(
            f"{self.base_url}/sessions/{session_id}/stints/", json=stint_data
        )
        print(r.text)

    def put_stint(self, stint_data: dict):
        session_id = stint_data['session_id']
        r = self.s.put(f"{self.base_url}/{session_id}/stints/", json=stint_data)
        print(r.text)

    """Lap Methods"""

    def post_lap(self, stint_id: int, lap: Lap):
        lap = Lap(stint_id=1, time=60.5, number=2)
        r = self.s.post(f"{self.base_url}/stints/{stint_id}/laps/", json=lap.to_dict())
        print(r.text)


def process_api_queue(client: APIClient, q: Queue):

    while True:
        try:
            task = q.get(timeout=1)

            match task["type"]:
                case "Session":
                    pass
                case "Stint":
                    pass
                case "Lap":
                    pass
                case _:
                    logger.error("No valid type in task")

        except Empty:
            continue
