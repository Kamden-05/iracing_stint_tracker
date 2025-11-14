import logging
import os
import threading
import time
from queue import Empty, Queue
from dotenv import load_dotenv
from src.utils.api_client import APIClient
from src.session_manager import SessionManager, SessionStatus
from src.utils.utils import get_task_dict
from src.gui.app_gui import StintTrackerGUI

logger = logging.getLogger(__name__)

def manage_race(manager: SessionManager, name: str, q: Queue, stop_event):
    finished = False

    try:
        while not stop_event.is_set() and not finished:
            manager.check_iracing()

            if not manager.is_connected:
                time.sleep(1)
                continue

            if manager.session_id is None or manager.session_id != manager.get_ir_session_id():
                manager.init_session()
                session_task = get_task_dict(
                    task_type="Session", data=manager.get_session_info()
                )
                q.put(session_task)

            session_type = manager.get_session_type()

            if session_type == "Race":
                completed_stint = manager.process_race()

                if completed_stint and completed_stint.driver_name == name:
                    stint_task = get_task_dict(
                        task_type="Stint",
                        data={
                            "stint": completed_stint,
                            "session_id": manager.session_id,
                        },
                    )
                    q.put(stint_task)

            if manager.status == SessionStatus.FINISHED:
                finished = True
                manager.disconnect()

            time.sleep(1 / 60)
    finally:
        manager.disconnect()
        q.put(None)

def main():
    pass


if __name__ == "__main__":
    main()
