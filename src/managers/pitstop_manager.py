from queue import Queue
from src.managers.base_manager import BaseManager
from src.context.race_context import RaceContext
from src.models.pitstop import PitStop
from src.api.task_types import get_task_dict, TaskType


class PitstopManager(BaseManager):
    required_fields = {
        "SessionTime": "session_time",
        "PitRepairLeft": "repair_time",
        "PitOptRepairLeft": "repair_opt_time",
        "dpFuelAddKg": "fuel_add_amt",
        "FuelLevel": "fuel_level",
        "FuelLevelPct": "fuel_level_pct",
        "dpRFTireChange": "right_front",
        "dpLFTireChange": "left_front",
        "dpRRTireChange": "right_rear",
        "dpLRTireChange": "left_rear",
        "FastRepairUsed": "fast_repair_used",
    }
    
    def handle_event(self, event, telem, ctx):
        if event == "enter_pit_box":
            self._start_pitstop()
        elif event == "exit_pit_box":
            self._end_pitstop()

    def send_pitstop_data(self):
        pass

    def _start_pitstop(self):
        pass

    def _end_pitstop(self):
        pass