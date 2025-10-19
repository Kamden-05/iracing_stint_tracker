from typing import List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field, computed_field


@dataclass
class Lap:
    stint_id: int
    lap_time: float
    lap_number: int


class Stint(BaseModel):
    """Stint Start Values:"""

    session_id: int
    stint_id: int
    number: int
    driver_name: str
    start_time: float
    start_position: int
    start_incidents: int
    start_fuel: float
    start_fast_repairs: int
    laps: List[Lap] = Field(default_factory=list)

    """Stint End Values:"""
    end_incidents: int = -1
    end_fast_repairs: int = -1
    end_position: Optional[int] = None
    length: Optional[float] = None
    final: bool = False

    def model_post_init(self, __context):
        self.end_incidents = self.start_incidents
        self.end_fast_repairs = self.start_fast_repairs

    """Pit Values:"""
    end_fuel: Optional[float] = None
    refuel_amount: Optional[float] = None
    required_repair_time: Optional[float] = None
    optional_repair_time: Optional[float] = None
    pit_service_duration: Optional[float] = None
    pit_service_start_time: Optional[float] = None
    tire_change: Optional[bool] = None

    @computed_field
    def avg_lap(self) -> Optional[float]:
        return (
            (sum(lap.time for lap in self.laps) / len(self.laps)) if self.laps else None
        )

    @computed_field
    def fastest_lap(self) -> Optional[float]:
        return (min(lap.time for lap in self.laps)) if self.laps else None

    @computed_field
    def laps_completed(self) -> int:
        return len(self.laps)

    @computed_field
    def in_lap(self) -> Optional[float]:
        if self.laps and not self.final:
            return self.laps[-1].time
        return None

    @computed_field
    def out_lap(self) -> Optional[float]:
        if self.laps:
            return self.laps[0].time
        return None

    @computed_field
    def repairs(self) -> Optional[bool]:
        if self.end_fast_repairs - self.start_fast_repairs > 0:
            return True
        elif self.optional_repair_time is None and self.required_repair_time is None:
            return None
        else:
            return (
                (self.optional_repair_time or 0.0) + (self.required_repair_time or 0.0)
            ) > 0.0

    @computed_field
    def incidents(self) -> int:
        return self.end_incidents - self.start_incidents

    def record_pit(
        self,
        required_repair_time: float,
        optional_repair_time: float,
        end_fuel: float,
        refuel_amount: float,
        tires: bool,
        session_time: float,
    ) -> None:
        self.required_repair_time = required_repair_time
        self.optional_repair_time = optional_repair_time
        self.end_fuel = end_fuel
        self.refuel_amount = refuel_amount
        self.tire_change = tires
        self.pit_service_start_time = session_time

    def record_lap(self, time: float, lap_number: int) -> None:
        lap = Lap(stint_id=self.stint_id, lap_time=time, lap_number=lap_number)
        self.laps.append(lap)

    def end_stint(
        self,
        session_time: float,
        position: float,
        incidents: int,
        fast_repairs: int,
        end_fuel: float,
        final: bool,
    ) -> None:
        self.final = final
        self.length = session_time - self.start_time
        self.end_position = position
        self.end_incidents = incidents
        self.end_fast_repairs = fast_repairs

        if self.final:
            self.end_fuel = end_fuel
        else:
            self.pit_service_duration = session_time - self.pit_service_start_time
    
    def post_json(self) -> dict:
        return self.model_dump(
            include={
                'session_id',
                'number',
                'driver_name',
                'start_time',
                'start_position',
                'start_fuel',
            }
        )
    
    def put_json(self) -> dict:
        return self.model_dump(
            include={
                'end_position',
                'end_fuel',
                'refuel_amount',
                'tire_change',
                'repairs',
                'pit_service_duration',
                'incidents',
                'length',
            }
        )
