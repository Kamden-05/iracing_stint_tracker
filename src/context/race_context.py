from dataclasses import dataclass
from typing import Optional


@dataclass
class RaceContext:
    session_id: Optional[int] = None
    car_id: Optional[int] = None
    stint_id: Optional[int] = None
    user_name: Optional[str] = None
