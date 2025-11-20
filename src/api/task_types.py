from enum import Enum
from typing import Any


class TaskType(str, Enum):
    SESSION = "Session"
    STINT_CREATE = "StintCreate"
    STINT_UPDATE = "StintUpdate"
    LAP = "Lap"
    PITSTOP = "PitStop"


def get_task_dict(task_type: TaskType, data: Any) -> dict[str, Any]:
    return {
        "type": task_type.value,
        "data": data,
    }
