import requests
import logging

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(
        self,
        base_url: str='http://127.0.0.1:8000',
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
        print(r.text)
        return r.json()

    """Stint Methods"""

    def get_latest_stint(self, session_id: int):
        r = self.s.get(f"{self.base_url}/sessions/{session_id}/stints/latest")
        print(r.text)
        if r.status_code == 204:
            return None
        else: 
            return r.json()

    def post_stint(self, stint_data: dict):
        session_id = stint_data["session_id"]
        r = self.s.post(
            f"{self.base_url}/sessions/{session_id}/stints/", json=stint_data
        )
        
        print(r.text)
        return r.json()

    def put_stint(self, stint_data: dict):
        session_id = stint_data["session_id"]
        r = self.s.put(f"{self.base_url}/{session_id}/stints/", json=stint_data)

        print(r.text)
        return r.json()

    """Lap Methods"""

    def post_lap(self, lap_data: dict):
        stint_id = lap_data["stint_id"]
        r = self.s.post(
            f"{self.base_url}/stints/{stint_id}/laps/", json=lap_data
        )
        print(r.text)
        return r.json()


