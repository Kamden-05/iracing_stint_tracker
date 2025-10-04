import pandas as pd
import time
from src.session_manager import SessionManager
from src.sheets import Sheets
from dotenv import load_dotenv
import os
import re

def main():
    load_dotenv()
    sheets = Sheets(
        service_account_file=os.getenv("service_account_file"),
        sheet_id="1y24KbjufqwZ5NB4ka7r9D8ddXdq-Vg2ZYPkmRb33k1k",
    )
    manager = SessionManager()
    stint_count = 0
    finished = False
    try:
         while True:
             if not manager.is_connected:
                 manager.connect()

             if manager.is_connected:
                 while manager.is_connected:
                     session_type = manager.get_session_type()
                     if session_type == "Race":
                         manager.process_race()
                         if len(manager.stints) > stint_count:
                            sheets.append_row(range_name='Raw',value_input_option='RAW', values=[list(manager.stints[stint_count].to_dict().values())])
                            sheets.append_row(range_name='Laps',value_input_option='RAW', values=[[lap] for lap in manager.stints[stint_count].laps])
                            stint_count += 1 
                     if manager.ended:
                         manager.disconnect()
                         finished = True
                     time.sleep(1 / 60)

             if finished:
                 break
    except KeyboardInterrupt:
         if manager:
             manager.disconnect()

    df = pd.DataFrame([stint.to_dict() for stint in manager.stints])
    df.to_csv(r"C:\Users\kmdnw\iracing_stint_tracker\races\output.csv", index=False)
    # sheets.append_row(
    #     range_name="Race", value_input_option="RAW", values=df.values.tolist()
    # )


def get_sheet_id(url: str) -> str:
    return None

if __name__ == "__main__":
    main()
