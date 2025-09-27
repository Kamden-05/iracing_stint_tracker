import time
import pandas as pd
from src.session_manager import SessionManager


def main():
    manager = SessionManager()

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
                        return
                    time.sleep(1 / 60)

    except KeyboardInterrupt:
        if manager:
            manager.disconnect()


if __name__ == "__main__":
    main()
