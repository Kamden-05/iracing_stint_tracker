import time
import os
from dotenv import load_dotenv
from src.engine import AppEngine


def main():
    load_dotenv()
    api_url = os.getenv("TEST_URL")
    user_name = "Kam Wilson"

    engine = AppEngine(user_name=user_name, api_base_url=api_url)

    engine.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()


if __name__ == "__main__":
    main()
