from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from src.utils import format_time


@dataclass
class Stint:
    """Stint Start Values:"""

    driver: str
    laps: List[float]
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int

    """Stint End Values:"""
    stint_length: Optional[float] = None
    incidents: Optional[int] = None
    in_lap: Optional[float] = None
    out_lap: Optional[float] = None
    laps_completed: Optional[int] = None
    end_position: Optional[int] = None

    """Pit Values:"""

    end_fuel: Optional[float] = None
    refuel_amount: Optional[float] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    service_time: Optional[float] = None
    tire_change: Optional[bool] = False
    repairs: Optional[bool] = False
