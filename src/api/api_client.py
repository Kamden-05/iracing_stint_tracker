from typing import Optional
import logging
import requests
from src.models import Session, Stint, PitStop, Lap

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


class APIClient:
    """Synchronous API client for interacting with telemetry backend."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.s = requests.Session()
        self.is_connected = self.check_connection()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.s.close()

    # Core request handler
    def _request(
        self, method: str, endpoint: str, json: Optional[dict] = None
    ) -> Optional[dict]:
        """Generic HTTP request."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            r = self.s.request(method, url, json=json, timeout=5)
            # r.raise_for_status()
            if r.status_code in [409, 204]:
                return None
            logger.debug("%s %s -> %s", method, url, r.status_code)
            return r.json()
        except requests.RequestException as e:
            logger.exception("API request failed: %s %s -> %s", method, url, e)
            return None

    def get(self, endpoint: str) -> Optional[dict]:
        return self._request("GET", endpoint)

    def post(self, endpoint: str, json: dict) -> Optional[dict]:
        return self._request("POST", endpoint, json=json)

    def put(self, endpoint: str, json: dict) -> Optional[dict]:
        return self._request("PUT", endpoint, json=json)

    def patch(self, endpoint: str, json: dict) -> Optional[dict]:
        return self._request("PATCH", endpoint, json=json)

    # Domain specific methods
    def post_session(self, session: Session):
        return self.post("sessions", session.to_post_json())

    def get_latest_stint(self, session_id: int):
        return self.get(f"sessions/{session_id}/stints/latest")

    def post_stint(self, stint: Stint):
        session_id = stint.session_id
        return self.post(f"sessions/{session_id}/stints", stint.to_post_json())

    def patch_stint(self, stint: Stint):
        stint_id = stint.id
        return self.patch(f"/stints/{stint_id}", stint.to_patch_json())

    def post_pitstop(self, pitstop: PitStop):
        stint_id = pitstop.stint_id
        return self.post(f"stints/{stint_id}/pitstops", pitstop.to_post_json())

    def patch_pitstop(self, pitstop: PitStop):
        pitstop_id = pitstop.id
        return self.patch(f"pitstops/{pitstop_id}", pitstop.to_patch_json())

    def post_lap(self, lap_data: dict):
        stint_id = lap_data["stint_id"]
        return self.post(f"stints/{stint_id}/laps", lap_data)

    # Utilities
    def check_connection(self) -> bool:
        """Check if backend is reachable."""
        try:
            r = self.s.get(f"{self.base_url}/health", timeout=3)
            return r.status_code == 200
        except requests.RequestException:
            return False
