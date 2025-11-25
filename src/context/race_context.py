from dataclasses import dataclass, fields
from typing import Optional


@dataclass
class RaceContext:
    session_id: Optional[int] = None
    car_id: Optional[int] = None
    stint_id: Optional[int] = None
    user_name: Optional[str] = None

    def reset(self):
        for field in fields(self):
            if field.name != "user_name":
                continue
            setattr(self, field.name, None)
