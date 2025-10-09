import pandas as pd
import time
from src.session_manager import SessionManager, SessionStatus
from src.sheets import Sheets
from dotenv import load_dotenv
import os
import re
import threading
from queue import Queue, Empty


def get_sheet_id(url: str) -> str:
    match = re.search(r"d/([^/]+)/edit", url)
    print(match.group())
    if match:
        return match.group(1)
    return ""

def manage_race(manager: SessionManager, q: Queue):
    finished = False
    last_sent = 0
    current_stint_id = 0

    while not finished:
        if not manager.is_connected:
            manager.connect()

        if manager.is_connected:
            while manager.is_connected:
                session_type = manager.get_session_type()
                if session_type == "Race":
                    manager.process_race(stint_id=current_stint_id)
                    if manager.prev_pit_active and current_stint_id == manager.current_stint.stint_id:
                        current_stint_id += 1
                    if len(manager.stints) > last_sent:
                        q.put(manager.stints[last_sent])
                        last_sent += 1
                if manager.status == SessionStatus.FINISHED:
                    manager.disconnect()
                    finished = True
                time.sleep(1 / 60)

    print('Race Finished')

def main():
    load_dotenv()
    sheets = Sheets(
        service_account_file=os.getenv("service_account_file"),
        sheet_id="1y24KbjufqwZ5NB4ka7r9D8ddXdq-Vg2ZYPkmRb33k1k",
    )
    q = Queue()
    manager = SessionManager()
    manager_thread = threading.Thread(
        target=manage_race, daemon=True, args=(manager, q)
    )
    manager_thread.start()
    while True:
        try:
            stint = q.get(timeout=1)
            stint_data = [list(stint.model_dump(exclude={'laps'}).values())]
            laps = [[lap] for lap in stint.laps]
            sheets.append_row(
                range_name="Raw",
                value_input_option="RAW",
                values=stint_data,
            )
            sheets.append_row(
                range_name="Laps",
                value_input_option="RAW",
                values=laps
            )
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
