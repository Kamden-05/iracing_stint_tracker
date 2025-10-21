import threading
import time
from queue import Empty, Queue

import pandas as pd

from src.api_client import APIClient, process_api_queue
from src.session_manager import SessionManager, SessionStatus, manage_race
from src.utils import get_task_dict


def manage_race(manager: SessionManager, q: Queue, stop_event):
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

                        if completed_stint:
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
    q = Queue()
    manager = SessionManager()
    client = APIClient()
    stop_event = threading.Event()

    manager_thread = threading.Thread(target=manage_race, args=(manager, q, stop_event))
    api_thread = threading.Thread(target=process_api_queue, args=(client, q))

    api_thread.start()
    manager_thread.start()

    while True:
        try:
            if not manager_thread.is_alive():
                break
        except Empty:
            continue
        except KeyboardInterrupt:
            stop_event.set()
            break

            # TODO: append stints to df or csv one at a time since manager no longer keeps track of a list
    # df = pd.DataFrame([stint.model_dump(exclude={"laps"}) for stint in manager.stints])
    # df.to_csv(
    #     r"C:\Users\kmdnw\Projects\iRacing\iracing_stint_tracker\races\output.csv",
    #     index=False,
    # )


if __name__ == "__main__":
    main()
