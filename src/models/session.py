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

    def to_dict(self) -> dict:
        data = asdict(self)

        if isinstance(data.get("session_date"), datetime.date):
            data["session_date"] = data["session_date"].isoformat()

        return data
