import requests
import json
from .stint import Stint, Lap

base_url = "http://127.0.0.1:8000"

def post_session(url: str, session_info: dict):
    payload = json.dumps(session_info)
    r = requests.post(f'{url}/sessions/', data=payload)
    print(r.text)


def post_stint(url: str, session_id: int, stint: Stint):
    payload = stint.model_dump(
        include={'stint_number','driver_name','start_time'}
    )

def put_stint(url: str, session_id: int, stint: Stint):
    pass

def post_lap(url: str, stint_id: int, lap: Lap):
    pass


post_session(base_url, {})