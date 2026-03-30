from dataclasses import dataclass, fields
from typing import Optional


@dataclass
class RaceContext:
    session_id: Optional[int] = None
    car_id: Optional[int] = None
    stint_id: Optional[int] = None
    pitstop_id: Optional[int] = None

    def reset(self):
        for field in fields(self):
            setattr(self, field.name, None)
