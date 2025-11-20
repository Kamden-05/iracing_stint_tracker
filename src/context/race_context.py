from dataclasses import dataclass
from typing import Optional


@dataclass
class RaceContext:
    session_id: Optional[int]
    car_id: Optional[int]
    stint_id: Optional[int]
    pitstop_id: Optional[int]
    stint_number: Optional[int]
    user_name: Optional[str]
