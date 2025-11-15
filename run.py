import sys
import json
import time
import os  # <-- NEW: Import os
from model import DeltaVModel

# --- SPEED CONTROL ---
# 1.0 = Real-time
# 2.0 = 2x real-time speed
# 4.0 = 4x real-time speed
SPEED_MULTIPLIER = 50.0
# --- END SPEED CONTROL ---

COMMAND_FILE = "commands.json"  # <-- NEW: Define command file

# --- NEW: Function to safely read the pause command ---
def get_pause_state():
    """
    Safely reads the command file to check the pause state.
    Defaults to False if file not found or error.
    """
    try:
        if os.path.exists(COMMAND_FILE):
            with open(COMMAND_FILE, 'r') as f:
                data = json.load(f)
            # Return the value of "pause_active", default to False if key doesn't exist
            return data.get("pause_active", False)
    except Exception as e:
        # On any error (e.g., file being written, JSON error), just default to not paused
        return False
    # Default to not paused
    return False
# --- END NEW FUNCTION ---

# --- Config loading (unchanged) ---
CONFIG_FILE = "starting_grid.json"
if len(sys.argv) > 1:
    CONFIG_FILE = sys.argv[1]

try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    race_laps = config['simulation_params']['race_laps']
    time_step = config['simulation_params']['time_step']
    MAX_TIME_SECONDS = race_laps * 92 
    print(f"--- DEBUG: RUNNING SIMULATION FOR {MAX_TIME_SECONDS} SECONDS ({race_laps} laps) ---")
except Exception as e:
    print(f"Error loading config file {CONFIG_FILE}: {e}")
    sys.exit(1)

print(f"--- Starting Delta-V Simulation (Grid: {CONFIG_FILE}, Laps: {race_laps}) ---")

# --- Model setup (unchanged) ---
model = DeltaVModel(
    config_file_path=CONFIG_FILE, 
    seed=123,
    live_snapshot_mode=True # <-- Tell the model to write snapshots
)

# --- REAL-TIME MASTER LOOP (UPDATED WITH PAUSE LOGIC) ---

sleep_duration = time_step / SPEED_MULTIPLIER

while model.running and (model.env.now < MAX_TIME_SECONDS):
    try:
        # --- NEW: PAUSE CHECK ---
        # Before every step, check if the dashboard has requested a pause.
        while get_pause_state():
            # We are paused. Sleep for a bit and check again.
            # Do not advance the simulation.
            time.sleep(0.5) 
            # This print will overwrite itself, looking like a "blinking" status
            print("...sim paused...", end="\r") 
        # --- END PAUSE CHECK ---

        # If we are here, we are not paused. Run one step.
        model.env.run(until=model.env.now + time_step)
        
        # Sleep for the *adjusted* duration
        time.sleep(sleep_duration)
        
    except KeyboardInterrupt:
        print("\n--- Simulation interrupted by user ---")
        model.running = False
        break

# --- END UPDATED LOOP ---

print("\n--- Simulation Complete ---")