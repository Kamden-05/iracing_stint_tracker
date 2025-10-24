import logging
import os
import sys
import threading
import time
from queue import Empty, Queue
from src.api_client import APIClient
from src.session_manager import SessionManager, SessionStatus
from src.utils import get_task_dict
from gui.app_gui import StintTrackerGUI

import json

logger = logging.getLogger(__name__)


def manage_race(manager: SessionManager, name: str, q: Queue, stop_event):
    finished = False

    try:
        while not stop_event.is_set() and not finished:
            manager.check_iracing()

            if not manager.is_connected:
                time.sleep(1)
                continue

            if manager.session_id is None:
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


def get_config_path(filename="settings.json"):
    # Folder where the .exe is located
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle
        base_path = os.path.dirname(sys.executable)
    else:
        # Running as normal Python script
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


def load_data(config_path):
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"url": "", "username": ""}  # defaults
    except json.JSONDecodeError:
        return {"url": "", "username": ""}  # defaults


def main():

    config_path = get_config_path()
    config = load_data(config_path)

    api_url = config.get("url", "")
    user_name = config.get("username", "")

    print(api_url, user_name)

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
