from dataclasses import dataclass, fields
from typing import Optional


@dataclass
class RaceContext:
    session_id: Optional[int] = None
    car_id: Optional[int] = None
    stint_id: Optional[int] = None
    user_name: Optional[str] = None

    def reset(self):
        excluded = {"user_name"}
        for field in fields(self):
            if field.name not in excluded:
                continue
            setattr(self, field.name, None)
