#!python3
import irsdk
import time
from datetime import datetime
import pandas as pd

# Column Headers for dataframes
column_names = ["Local Time", "Driver", "Stint Start", "Stint Length", "Laps", "Average Lap", "Fastest Lap", "Out Lap", "In Lap", "Start Fuel Qty.", "End Fuel Qty.", "Refuel Qty.", "Tires", "Repairs", "Service Time", "Incidents", "Start Position", "End Position"]

# this is our State class, with some helpful variables
class State:
    ir_connected = False
    last_car_setup_tick = -1

# here we check if we are connected to iracing
# so we can retrieve some data
def check_iracing():
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        state.ir_connected = False
        # don't forget to reset your State variables
        state.last_car_setup_tick = -1
        # we are shutting down ir library (clearing all internal variables)
        ir.shutdown()
        print('irsdk disconnected')
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True
        print('irsdk connected')

def record_stint(laps, start_pos, start_time, start_incidents, start_fuel):
    local_time = datetime.now().strftime('%H:%M:%S')
    stint_length = ir["SessionTimeOfDay"] - start_time
    num_laps = len(laps)
    avg_lap = sum(laps) / len(laps)
    fast_lap = max(laps)
    out_lap = laps[0]
    in_lap = laps[-1]
    end_fuel = ir["FuelLevel"]
    fuel_add_amount = ir["dpFuelAddKg"] - end_fuel
    refuel = fuel_add_amount if fuel_add_amount > 0 else 0
    service_time = ir["PitOptRepairLeft"] + ir["PitRepairLeft"]
    incidents = ir["PlayerCarTeamIncidentCount"] - start_incidents
    end_pos = ir["PlayerCarPosition"]

    d = {
        "Local Time": local_time,
        "Driver": "Kam", 
        "Stint Start": start_time, 
        "Stint Length": stint_length, 
        "Laps": num_laps, 
        "Average Lap": avg_lap, 
        "Fastest Lap": fast_lap, 
        "Out Lap": out_lap, 
        "In Lap": in_lap, 
        "Start Fuel Qty.": start_fuel, 
        "End Fuel Qty.": end_fuel, 
        "Refuel Qty.": refuel, 
        "Tires": False, 
        "Repairs": False, 
        "Service Time": service_time, 
        "Incidents": incidents, 
        "Start Position": start_pos, 
        "End Position": end_pos
    }

    df = pd.DataFrame([d])

    return df

if __name__ == '__main__':
    
    ir = irsdk.IRSDK()
    state = State()

    last_pit_check = False
    pit_check = False

    prev_lap = 0
    start_lap = 0
    stint_laps = []
    stint_start_time = 0
    start_pos = 0
    start_incidents = 0
    start_fuel = 0
    last_name = None


    
    stints = pd.DataFrame(columns=column_names)

    try:
        # infinite loop
        while True:
            # check if we are connected to iracing
            check_iracing()
            # if we are, then process data
            if state.ir_connected:
                
                driver_id = ir['PlayerCarIdx']
                session_info = ir._get_session_info

                # update stint laps when a new lap is started
                if prev_lap < ir["Lap"]:
                    stint_laps.append(ir["LapLastLapTime"])
                    prev_lap = ir["Lap"]

                # if we have started a pit stop, update the stint log
                pit_check = ir['PitstopActive']    
                if pit_check is True and last_pit_check is False:
                    # log a stint
                    stints = pd.concat([stints, record_stint(stint_laps, start_pos, start_time, start_incidents, start_fuel)])
                    print(stint_laps)
                    print(stints)
                    stint_laps = []
                    start_lap = ["Lap"]

                # record the start data of the next stint
                elif pit_check is False and last_pit_check is True:
                    # record the start data of next stint
                    start_time = ir["SessionTimeOfDay"]
                    start_pos = ir["PlayerCarPosition"] # TRACKS RACE POSITION NOT CLASS POSITION
                    start_incidents = ir["PlayerCarTeamIncidentCount"]
                    start_fuel = ir["FuelLevel"]

                last_pit_check = pit_check
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            time.sleep(1)
    except KeyboardInterrupt:
        # press ctrl+c to exit
        pass
#