import pandas as pd
import time
from src.session_manager import SessionManager, SessionStatus, manage_race
from src.api_client import APIClient, process_api_queue
import threading
from queue import Queue, Empty

def main():
    q = Queue()
    manager = SessionManager()
    manager_thread = threading.Thread(
        target=manage_race, daemon=True, args=(manager, q)
    )
    manager_thread.start()
    while True:
        try:
           #TODO: send data to server as we get laps/stints  
            if not manager_thread.is_alive():
                break
        except Empty:
            continue
        except KeyboardInterrupt:
            if manager:
                manager.disconnect()
            break

    df = pd.DataFrame([stint.model_dump(exclude={'laps'}) for stint in manager.stints])
    df.to_csv(r"C:\Users\kmdnw\Projects\iRacing\iracing_stint_tracker\races\output.csv", index=False)

if __name__ == "__main__":
    main()
