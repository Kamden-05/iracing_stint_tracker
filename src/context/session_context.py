from dataclasses import dataclass
from typing import Optional

@dataclass
class SessionContext:
    session_id: Optional[int]
    car_id: Optional[int]
