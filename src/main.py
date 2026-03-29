import time
import os
import logging
import sys
from dotenv import load_dotenv
from src.engine import AppEngine

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("stint_tracker.log"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


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
