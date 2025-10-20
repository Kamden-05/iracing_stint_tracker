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
        self.session = requests.Session()

    def get_latest_stint(self, session_id: int):
        r = requests.get(f"{self.base_url}/sessions/{session_id}/stints/latest")
        print(r.text)

    def post_session(self, session_info: dict):
        payload = json.dumps(session_info)
        r = requests.post(f"{self.base_url}/sessions/", data=payload)
        print(r.text)

    def post_stint(self, session_id: int, stint_json: dict[str, Any]):
        r = requests.post(
            f"{self.base_url}/sessions/{session_id}/stints/", data=stint_json
        )
        print(r.text)

    def put_stint(self, session_id: int, stint_json: dict[str, Any]):
        r = requests.put(f"{self.base_url}/{session_id}/stints/", data=stint_json)
        print(r.text)

    def post_lap(self, stint_id: int, lap: Lap):
        lap = Lap(stint_id=10, time=60.5, number=1)
        payload = json.dumps(lap.to_dict())
        r = requests.post(f"{self.base_url}/stints/{stint_id}/laps/", data=payload)
        print(r.text)

    def close(self):
        self.session.close()


url = "http://127.0.0.1:8000"
id = 0

client = APIClient(base_url=url)

client.get_latest_stint(session_id=id)
