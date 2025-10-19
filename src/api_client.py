import requests
import json
from .stint import Lap
from typing import Any

def post_session(url: str, session_info: dict):
    payload = json.dumps(session_info)
    r = requests.post(f"{url}/sessions/", data=payload)
    print(r.text)


def post_stint(url: str, session_id: int, stint_json: dict[str, Any]):
    r = requests.post(f"{url}/sessions/{session_id}/stints/", data=stint_json)
    print(r.text)


def put_stint(url: str, session_id: int, stint_json: dict[str, Any]):
    r = requests.put(f"{url}/{session_id}/stints/", data=stint_json)
    print(r.text)


def post_lap(url: str, stint_id: int, lap: Lap):
    lap = Lap(stint_id=10, time=60.5, number=1)
    payload = json.dumps(lap.to_dict())
    r = requests.post(f"{url}/stints/{stint_id}/laps/", data=payload)
    print(r.text)