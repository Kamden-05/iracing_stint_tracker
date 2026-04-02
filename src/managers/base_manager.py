from queue import Queue
from typing import Any, Optional
from src.context import RaceContext
from src.api import APITask, TaskType, PayloadType
from src.exporters import ExcelExporter
from src.fsm import States


class BaseManager:
    required_fields: dict[str, str] = {}

    def __init__(
        self, context: RaceContext, queue: Queue, excel: Optional[ExcelExporter]
    ):
        self.context: RaceContext = context
        self.queue: Queue = queue
        self.excel: Optional[ExcelExporter] = excel
        self.event_handlers = {}

        for attr in self.required_fields.values():
            setattr(self, attr, None)

    def handle_event(self, event_name: str):
        if event_name in self.event_handlers:
            self.event_handlers[event_name]()

    def on_tick(self, telem: dict[str, Any], state: States):
        for telem_key, attr_name in self.required_fields.items():
            setattr(self, attr_name, telem[telem_key])

    def _send_data(self, task: TaskType, payload: PayloadType):
        self.queue.put(APITask(type=task, payload=payload))

        if self.excel is not None:
            if task is TaskType.SESSION:
                self.excel.create_workbook(payload)
            elif task in [TaskType.STINT_CREATE, TaskType.PITSTOP_CREATE, TaskType.LAP]:
                self.excel.update_sheet(payload, append=True)
            else:
                self.excel.update_sheet(payload, append=False)
