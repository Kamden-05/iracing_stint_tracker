import pandas as pd
import time
from src.session_manager import SessionManager
from src.sheets import Sheets
from dotenv import load_dotenv
import os
from tests.mock_stints import test_stints


def main():
    load_dotenv()
    sheets = Sheets(
        service_account_file=os.getenv("service_account_file"),
        sheet_id="1y24KbjufqwZ5NB4ka7r9D8ddXdq-Vg2ZYPkmRb33k1k",
    )
    manager = SessionManager()
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
                     if manager.ended:
                         manager.disconnect()
                         finished = True
                     time.sleep(1 / 60)

             if finished:
                 break
    except KeyboardInterrupt:
         if manager:
             manager.disconnect()

    # df = pd.DataFrame([stint.to_dict() for stint in manager.stints])
    # print(df)
    # df.to_csv(r"C:\Users\kmdnw\iracing_stint_tracker\races\output.csv", index=False)
    df = pd.DataFrame(test_stints)
    sheets.append_row(
        range_name="Race", value_input_option="RAW", values=df.values.tolist()
    )


if __name__ == "__main__":
    main()
