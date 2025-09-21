from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from src.utils import format_time


@dataclass
class Stint:
    driver: str
    laps: List[float]
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int
    start_tires_used: int

    in_lap: Optional[float] = None
    out_lap: Optional[float] = None
    laps_completed: Optional[int] = None
    end_time: Optional[float] = None
    end_position: Optional[int] = None
    end_incidents: Optional[int] = None
    end_fuel: Optional[float] = None
    fuel_add_amount: Optional[float] = None
    end_tires_used: Optional[int] = None
    incidents: Optional[int] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    service_time: Optional[float] = None
    end_fast_repairs: Optional[int] = None

    def get_stint_length(self) -> float:
        return self.end_time - self.start_time

    def get_average_lap(self) -> float:
        return sum(self.laps) / len(self.laps) if self.laps else 0.0

    def get_fastest_lap(self) -> float:
        return min(self.laps) if self.laps else 0.0
