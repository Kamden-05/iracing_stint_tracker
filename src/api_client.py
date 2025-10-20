import requests
import json
from src.stint import Lap
from typing import Any


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

    def get_latest_stint(self, session_id: int):
        r = self.s.get(f"{self.base_url}/sessions/{session_id}/stints/latest")
        print(r.text)

    def post_session(self, session_info: dict):
        payload = json.dumps(session_info)
        r = self.s.post(f"{self.base_url}/sessions/", data=payload)
        print(r.text)

    def post_stint(self, session_id: int, stint_json: dict[str, Any]):
        r = self.s.post(
            f"{self.base_url}/sessions/{session_id}/stints/", data=stint_json
        )
        print(r.text)

    def put_stint(self, session_id: int, stint_json: dict[str, Any]):
        r = self.s.put(f"{self.base_url}/{session_id}/stints/", data=stint_json)
        print(r.text)

    def post_lap(self, stint_id: int, lap: Lap):
        lap = Lap(stint_id=1, time=60.5, number=2)
        payload = json.dumps(lap.to_dict())
        r = self.s.post(f"{self.base_url}/stints/{stint_id}/laps/", data=payload)
        print(r.text)