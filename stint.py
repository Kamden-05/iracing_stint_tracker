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

    def get_stint_length(self, current_time: float) -> float:
        return current_time - self.start_time

    def get_average_lap(self) -> float:
        return sum(self.laps) / len(self.laps) if self.laps else 0.0

    def get_fastest_lap(self) -> float:
        return min(self.laps) if self.laps else 0.0

    def get_refuel_amount(self, prev_start_fuel: float, end_fuel: float) -> float:
        return prev_start_fuel - end_fuel

    def repairing(self, end_fast_repairs: int, service_time: float) -> bool:
        if end_fast_repairs is not None and self.start_fast_repairs is not None:
            return end_fast_repairs < self.start_fast_repairs
        else:
            return service_time > 0

    def to_dict(
        self,
        end_time: float,
        end_fuel: float,
        end_position: int,
        incidents: int,
        service_time: float,
        tire_replacement: bool,
        end_fast_repairs: int,
    ) -> dict:
        return {
            "Local Time": datetime.now().strftime("%H:%M:%S"),
            "Driver": self.driver,
            "Stint Start": format_time(self.start_time),
            "Stint Length": format_time(self.get_stint_length(end_time)),
            "Laps": len(self.laps),
            "Average Lap": format_time(self.get_average_lap()),
            "Fastest Lap": format_time(self.get_fastest_lap()),
            "Out Lap": format_time(self.laps[0]) if self.laps else None,
            "In Lap": format_time(self.laps[-1]) if self.laps else None,
            "Start Fuel Qty.": round(self.start_fuel, 2),
            "End Fuel Qty.": round(end_fuel, 2),
            "Refuel Qty.": 0,
            "Tires": "True" if tire_replacement == 1.0 else "False",
            "Repairs": (
                "True" if self.repairing(end_fast_repairs, service_time) else "False"
            ),
            "Service Time": format_time(service_time),
            "Incidents": incidents - self.start_incidents,
            "Start Position": self.start_position,
            "End Position": end_position,
        }
