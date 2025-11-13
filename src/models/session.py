from dataclasses import dataclass, asdict
import datetime

@dataclass
class Session:
    id: int
    track: str
    car_class: str
    car: str
    race_duration: int
    session_date: datetime.date

    def to_dict(self):
        return asdict(self)