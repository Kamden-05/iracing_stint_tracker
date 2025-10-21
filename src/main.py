import threading
from queue import Empty, Queue

import pandas as pd

from src.api_client import APIClient, process_api_queue
from src.session_manager import SessionManager, SessionStatus, manage_race


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

    df = pd.DataFrame([stint.model_dump(exclude={"laps"}) for stint in manager.stints])
    df.to_csv(
        r"C:\Users\kmdnw\Projects\iRacing\iracing_stint_tracker\races\output.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
