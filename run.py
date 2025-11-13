import sys
import json
from model import DeltaVModel

# --- NEW: Run with a STARTING GRID file ---
CONFIG_FILE = "starting_grid.json"
if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]

# Get max time from the config file
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    race_laps = config['simulation_params']['race_laps']
    
    # Run for 100 seconds per lap (a safe buffer)
    MAX_TIME_SECONDS = race_laps * 100 
    
    print(f"--- DEBUG: RUNNING SIMULATION FOR {MAX_TIME_SECONDS} SECONDS ({race_laps} laps) ---")

except Exception as e:
    print(f"Error loading config file {CONFIG_FILE}: {e}")
    sys.exit(1)

print(f"--- Starting Delta-V Simulation (Grid: {CONFIG_FILE}, Laps: {race_laps}) ---")

model = DeltaVModel(config_file_path=CONFIG_FILE, seed=123) # Use a fixed seed for testing
model.env.run(until=MAX_TIME_SECONDS)

print("\n--- Simulation Complete ---")