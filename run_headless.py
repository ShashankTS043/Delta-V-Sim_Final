import sys
import os
import json
from model import DeltaVModel

def run_single_race(config_file_path):
    """
    Runs one full, silent simulation from a config file.
    Returns a JSON string of the final race results.
    """
    
    # --- Load Config ---
    with open(config_file_path, 'r') as f:
        config = json.load(f)
    
    race_laps = config['simulation_params']['race_laps']
    RACE_TIME_SECONDS = race_laps * 95 # ~95s per lap
    
    # --- Create Model ---
    model = DeltaVModel(config_file_path=config_file_path, seed=None)
    
    # --- Run Simulation ---
    model.env.run(until=RACE_TIME_SECONDS)
    
    # --- Collate Results ---
    final_results = []
    for agent in model.f1_agents:
        agent_data = {
            "driver": agent.unique_id,
            "team": agent.team,
            "laps_completed": agent.laps_completed,
            "total_distance": agent.total_distance_traveled,
            "final_soc_pct": round(agent.battery_soc * 100, 2),
            "status": agent.status
        }
        final_results.append(agent_data)
        
    # Sort by distance to find the winner
    sorted_results = sorted(final_results, 
                           key=lambda x: x["total_distance"], 
                           reverse=True)
    
    # Return the full results as a JSON string
    return json.dumps(sorted_results)

# This part lets the file be run by itself
if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        # We'll write errors to stderr so they don't corrupt the output
        sys.stderr.write("Error: No config file specified.\n")
        sys.exit(1)
        
    config_file = sys.argv[1]
    
    # Silence all print statements
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    # Run the race
    results_json = run_single_race(config_file_path=config_file)
    
    # Restore print
    sys.stdout = original_stdout
    
    # Print ONLY the final JSON results
    print(results_json)