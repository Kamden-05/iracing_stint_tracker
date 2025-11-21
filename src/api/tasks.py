from enum import Enum
from dataclasses import dataclass
from typing import Union
from src.models import Session, Stint, PitStop, Lap


class TaskType(str, Enum):
    SESSION = "Session"
    STINT_CREATE = "StintCreate"
    STINT_UPDATE = "StintUpdate"
    LAP = "Lap"
    PITSTOP_CREATE = "PitstopCreate"
    PITSTOP_UPDATE = "PitstopUpdate"


PayloadType = Union[Session, Stint, PitStop, Lap]


@dataclass
class APITask:
    task: TaskType
    payload: PayloadType
