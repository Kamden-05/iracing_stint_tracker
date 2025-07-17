from dataclasses import dataclass
from typing import List
from datetime import datetime
from utils import format_time


@dataclass
class Stint:
    driver: str
    start_time: float
    laps: List[float]
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int

    laps_completed: int = -1
    end_time: float = -1.0
    end_position: int = -1
    end_fuel: float = -1.0
    incidents: int = -1
    service_time: float = -1.0
    tire_replacement: bool = None
    end_fast_repairs: int = -1
    refuel_amount: float = -1.0

    def get_stint_length(self, current_time: float) -> float:
        return current_time - self.start_time

    def get_average_lap(self) -> float:
        return sum(self.laps) / len(self.laps) if self.laps else 0.0

    def get_fastest_lap(self) -> float:
        return min(self.laps) if self.laps else 0.0

    def repairing(self) -> bool:
        if self.end_fast_repairs is not None and self.start_fast_repairs is not None:
            return self.end_fast_repairs < self.start_fast_repairs
        else:
            return self.service_time > 0

    def to_dict(self) -> dict:
        return {
            "Local Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": self.driver,
            "Stint Start": format_time(self.start_time),
            "Stint Length": format_time(self.get_stint_length(self.end_time)),
            "Laps": self.laps_completed,
            "Average Lap": format_time(self.get_average_lap()),
            "Fastest Lap": format_time(self.get_fastest_lap()),
            "Out Lap": format_time(self.laps[0]) if self.laps else None,
            "In Lap": format_time(self.laps[-1]) if self.laps else None,
            "Start Fuel Qty.": round(self.start_fuel, 2),
            "End Fuel Qty.": round(self.end_fuel, 2),
            "Refuel Qty.": round(self.refuel_amount, 2),
            "Tires": "True" if self.tire_replacement == 1.0 else "False",
            "Repairs": ("True" if self.repairing() else "False"),
            "Service Time": format_time(self.service_time),
            "Incidents": self.incidents - self.start_incidents,
            "Start Position": self.start_position,
            "End Position": self.end_position,
        }
