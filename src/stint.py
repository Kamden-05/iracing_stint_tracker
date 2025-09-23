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
    avg_lap: Optional[float] = None
    laps_completed: Optional[int] = None
    end_position: Optional[int] = None

    """Pit Values:"""

    end_fuel: Optional[float] = None
    refuel_amount: Optional[float] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    service_time: Optional[float] = None
    service_start_time: Optional[float] = None
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
        print(f"Stint Length: {self.stint_length}")
        print(f"End Position: {self.end_position}")
        print(f"Incidents in Stint: {self.incidents}")
        print(f"Out Lap: {self.out_lap}")
        print(f"In Lap: {self.in_lap}")
        print(f"Average Lap: {self.avg_lap}")
        print(f"Laps Completed: {self.laps_completed}")
        print(f"{'-'*40}")
        print(f"End Fuel: {self.end_fuel}")
        print(f"Refuel Amount: {self.refuel_amount}")
        print(f"Required Repair Time: {self.required_repair_time}")
        print(f"Optional Repair Time: {self.optional_repair_time}")
        print(f"Service Start Time: {self.service_start_time}")
        print(f"Service Time: {self.service_time}")
        print(f"Tire Change: {self.tire_change}")
        print(f"Repairs: {self.repairs}")
        print(f"{'='*40}\n")
