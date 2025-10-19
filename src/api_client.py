import requests
from stint import Stint, Lap

base_url = "http://127.0.0.1:8000"

session_id = 0
stint_id = 68

r = requests.get(f"{base_url}/sessions/{session_id}/stints/{stint_id}")

print(r.text)

def post_stint(url: str, session_id: int, stint: Stint):
    payload = stint.model_dump(
        include={'stint_number','driver_name','start_time'}
    )

def put_stint(url: str, session_id: int, stint: Stint):
    pass

def post_lap(url: str, stint_id: int, lap: Lap):
    pass