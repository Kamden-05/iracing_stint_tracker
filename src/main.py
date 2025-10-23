import logging
import os
import threading
import time
from queue import Empty, Queue

import pandas as pd
from dotenv import load_dotenv

from src.api_client import APIClient
from src.session_manager import SessionManager, SessionStatus
from src.utils import get_task_dict

logger = logging.getLogger(__name__)


def manage_race(manager: SessionManager, name: str, q: Queue, stop_event):
    finished = False

    try:
        while not stop_event.is_set() and not finished:
            if not manager.is_connected:
                manager.connect()

            if manager.is_connected:
                manager.init_session()
                print(manager.get_session_info())
                session_task = get_task_dict(
                    task_type="Session", data=manager.get_session_info()
                )
                q.put(session_task)

                while not stop_event.is_set() and manager.is_connected:

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
    api_url = os.getenv('TEST_URL')

    user_name = input("Enter your iRacing username: ")

    q = Queue()
    client = APIClient(base_url=api_url)
    stop_event = threading.Event()
    api_thread = threading.Thread(target=process_api_queue, args=(client, q))
    api_thread.start()
    manager_thread = None

    while not stop_event.is_set():
        try:
            if manager_thread is None or not manager_thread.is_alive():
                manager = SessionManager()
                manager_thread = threading.Thread(
                    target=manage_race, args=(manager, user_name, q, stop_event)
                )
                manager_thread.start()
            
            time.sleep(1)
        except KeyboardInterrupt:
            stop_event.set()
            manager_thread.join()
            api_thread.join()

            # TODO: append stints to df or csv one at a time since manager no longer keeps track of a list
    # df = pd.DataFrame([stint.model_dump(exclude={"laps"}) for stint in manager.stints])
    # df.to_csv(
    #     r"C:\Users\kmdnw\Projects\iRacing\iracing_stint_tracker\races\output.csv",
    #     index=False,
    # )


if __name__ == "__main__":
    main()
