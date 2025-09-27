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
    stint_length: Optional[float] = -1.0
    incidents: Optional[int] = -1
    in_lap: Optional[float] = -1.0
    out_lap: Optional[float] = -1.0
    avg_lap: Optional[float] = -1.0
    laps_completed: Optional[int] = -1
    end_position: Optional[int] = -1

    """Pit Values:"""

    end_fuel: Optional[float] = -1.0
    refuel_amount: Optional[float] = 0.0
    required_repair_time: Optional[float] = 0.0
    optional_repair_time: Optional[float] = 0.0
    pit_service_time: Optional[float] = 0.0
    pit_service_start_time: Optional[float] = 0.0
    tire_change: Optional[bool] = False
    repairs: Optional[bool] = False

    def display(self):
        """Print all values in the stint for easy review."""
        print(f"{'='*40}")
        print(f"Driver: {self.driver}")
        print(f"Start Time: {self.start_time}")
        print(f"Start Position: {self.start_position}")
        print(f"Start Incidents: {self.start_incidents}")
        print(f"Start Fuel: {self.start_fuel}")
        print(f"Start Fast Repairs: {self.start_fast_repairs}")
        print(f"Laps: {self.laps}")
        print(f"{'-'*40}")
        print(f"Stint Length: {format_time(self.stint_length)}")
        print(f"End Position: {self.end_position}")
        print(f"Incidents in Stint: {self.incidents}")
        print(f"Out Lap: {format_time(self.out_lap)}")
        print(f"In Lap: {format_time(self.in_lap)}")
        print(f"Average Lap: {format_time(self.avg_lap)}")
        print(f"Laps Completed: {self.laps_completed}")
        print(f"{'-'*40}")
        print(f"End Fuel: {self.end_fuel}")
        print(f"Refuel Amount: {self.refuel_amount}")
        print(f"Required Repair Time: {format_time(self.required_repair_time)}")
        print(f"Optional Repair Time: {format_time(self.optional_repair_time)}")
        print(f"Service Start Time: {format_time(self.pit_service_start_time)}")
        print(f"Service Time: {format_time(self.pit_service_time)}")
        print(f"Tire Change: {self.tire_change}")
        print(f"Repairs: {self.repairs}")
        print(f"{'='*40}\n")
