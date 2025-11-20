from typing import Optional
from dataclasses import dataclass, field
from src.models.lap import Lap

@dataclass
class Stint:

    # required
    session_id: int
    driver_name: str
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float

    # meta data
    number: Optional[int] = None
    id: Optional[int] = None
    laps: list[Lap] = field(default_factory=list)
    is_complete: bool = False

    # end of stint values
    end_time: Optional[float] = None
    end_position: Optional[int] = None
    end_incidents: Optional[float] = None
    end_fuel: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        if self.end_time is None:
            return None

        end = self.end_time

        if end < self.start_time:
            end += 86400

        return end - self.start_time

    @property
    def incidents(self) -> Optional[int]:
        if self.end_incidents is None:
            return None
        return self.end_incidents - self.start_incidents

    @property
    def fuel_used(self) -> Optional[float]:
        if self.end_fuel is None:
            return None
        return self.end_fuel - self.start_fuel

    def post_dict(self) -> dict:
        """
        Dictionary for creating a new stint in the backend
        """
        return {
            "session_id": self.session_id,
            "number": self.number,
            "driver_name": self.driver_name,
            "start_time": self.start_time,
            "start_position": self.start_position,
            "start_incidents": self.start_incidents,
            "start_fuel": self.start_fuel,
        }

    def patch_dict(self) -> dict:
        """
        Dictionary for updating an existing stint in the backend
        """
        return {
            "is_complete": self.is_complete,
            "end_time": self.end_time,
            "end_position": self.end_position,
            "end_incidents": self.end_incidents,
            "end_fuel": self.end_fuel,
        }
