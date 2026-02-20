from queue import Queue
from typing import Any
from src.fsm.states import States
from src.context.race_context import RaceContext
from src.api.tasks import APITask, TaskType, PayloadType
from src.exporters.excel_exporter import ExcelExporter


class BaseManager:
    required_fields: dict[str, str] = {}

    def __init__(self, context: RaceContext, queue: Queue, excel: ExcelExporter):
        self.context = context
        self.queue = queue
        self.excel = excel

        for attr in self.required_fields.values():
            setattr(self, attr, None)

    def handle_event(self, event: str, telem: dict[str, Any], ctx: dict[str, Any]):
        pass

    def on_tick(self, telem: dict[str, Any], state: States):
        for telem_key, attr_name in self.required_fields.items():
            setattr(self, attr_name, telem[telem_key])

    def _send_data(self, task: TaskType, payload: PayloadType):
        self.queue.put(APITask(type=task, payload=payload))

        if task is TaskType.SESSION:
            self.excel.create_workbook(payload)
            print("workbook created")
        elif task in [TaskType.STINT_CREATE, TaskType.PITSTOP_CREATE, TaskType.Lap]:
            self.excel.update_sheet(payload, append=True)
            print("appended to sheet")
        else:
            self.excel.update_sheet(payload, append=False)
