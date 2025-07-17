import time
from iracing_interface import IracingInterface
import pandas as pd
from session_manager import SessionManager


# TODO: only calculate inital position under green flag, not race session

# TODO: separate processing methods for practice/quali/race

# TODO: if we join the middle of a session, dont start collecting data until the next stint starts for consistency


def main():
    ir_interface = IracingInterface()
    manager = SessionManager(ir_interface)

    try:
        print("initializing")
        while True:
            if not ir_interface.check_connection():
                time.sleep(1)
                continue

            # check if race data is ready to be recorded
            if (
                ir_interface.get_session_type() == "Race"
                and ir_interface.get_player_position() > 0
            ):
                manager.process_race()
            else:
                print("Waiting for race start")
            time.sleep(1)

    except KeyboardInterrupt:
        # TODO: log the current stint on exit
        print("Exiting")

    # Export DataFrame
    out_path = "./races/stints.csv"
    df = pd.DataFrame(manager.export_stints())
    df.to_csv(out_path, index=False)
    print(f"Stints saved to {out_path}")


if __name__ == "__main__":
    main()
