import logging
import os
import threading
import time
from queue import Empty, Queue
from dotenv import load_dotenv
from src.utils.api import APIClient
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


def process_api_queue(client: APIClient, q: Queue):

    while True:
        try:
            task = q.get(timeout=1)

            if task is None:
                break

            task_type = task["type"]
            data = task["data"]

            match task_type:
                case "Session":
                    print("Session case")
                    client.post_session(session_data=data)
                case "Stint":
                    print("stint case")
                    stint = data["stint"]
                    session_id = data["session_id"]
                    response = client.get_latest_stint(session_id=session_id)
                    if response:
                        stint.number = response["number"] + 1
                    else:
                        stint.number = 1

                    response = client.post_stint(stint_data=stint.post_dict())
                    current_stint_id = response["id"]

                    for lap in stint.laps:
                        lap.stint_id = current_stint_id
                        response = client.post_lap(lap_data=lap.to_dict())
                case _:
                    raise ValueError(f"Ivalid task type: {task_type}")

        except Empty:
            continue
        except Exception as e:
            logger.exception(f"Error processing taskL {e}")

def main():
    load_dotenv()

    api_url = os.getenv("TEST_URL")
    user_name = "Kam Wilson"

    q = Queue()
    stop_event = threading.Event()

    client = APIClient(base_url=api_url)
    api_thread = threading.Thread(target=process_api_queue, args=(client, q))
    api_thread.start()

    manager = SessionManager()
    manager_thread = threading.Thread(
        target=manage_race, args=(manager, user_name, q, stop_event)
    )
    manager_thread.start()

    gui_user_name= user_name.split()[0]

    gui = StintTrackerGUI(
        client=client, manager=manager, stop_event=stop_event, driver_name=gui_user_name
    )
    gui.run()

    stop_event.set()
    manager_thread.join()
    api_thread.join()


if __name__ == "__main__":
    main()
