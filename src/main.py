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
                    manager.process_race()
                    time.sleep(1 / 60)

    except KeyboardInterrupt:
        if manager:
            manager.disconnect()


if __name__ == "__main__":
    main()
