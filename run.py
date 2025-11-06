import sys
import json
from model import DeltaVModel

# --- NEW: Run with a config file ---
# Default to our template, but allow a command-line argument
CONFIG_FILE = "config_aggressive.json"
if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]

# We get max time from the config file now
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        race_laps = config['simulation_params']['race_laps']
        # ~95s per lap in our current model
        MAX_TIME_SECONDS = race_laps * 95 
except Exception as e:
    print(f"Error loading config file {CONFIG_FILE}: {e}")
    sys.exit(1)


print(f"--- Starting Delta-V Simulation (Config: {CONFIG_FILE}, Laps: {race_laps}) ---")

# 1. Create the Model
#    We now pass the config file path to the model
model = DeltaVModel(config_file_path=CONFIG_FILE)

# 2. Agent customization is GONE from here, it's all in the JSON!

# 3. Run the SimPy environment
model.env.run(until=MAX_TIME_SECONDS)

print("\n--- Simulation Complete ---")