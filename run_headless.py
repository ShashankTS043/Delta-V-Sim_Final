import sys
import os
import json
from model import DeltaVModel

def run_single_race(config_file_path, seed): # <-- NEW: accept seed
    """
    Runs one full, silent simulation from a config file.
    Returns a JSON string of the final race results.
    """
    with open(config_file_path, 'r') as f:
        config = json.load(f)
    
    race_laps = config['simulation_params']['race_laps']
    RACE_TIME_SECONDS = race_laps * 95
    
    # Pass the seed to the model
    model = DeltaVModel(config_file_path=config_file_path, seed=seed)
    model.env.run(until=RACE_TIME_SECONDS)
    
    final_results = []
    for agent in model.f1_agents:
        agent_data = {
            "driver": agent.unique_id,
            "team": agent.team,
            "laps_completed": agent.laps_completed,
            "total_distance": agent.total_distance_traveled,
            "final_soc_pct": round(agent.battery_soc * 100, 2),
            "final_tyre_life": round(agent.tyre_life_remaining * 100, 2), # <-- NEW
            "status": agent.status
        }
        final_results.append(agent_data)
        
    sorted_results = sorted(final_results, 
                           key=lambda x: x["total_distance"], 
                           reverse=True)
    
    return json.dumps(sorted_results)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Error: No config file specified.\n")
        sys.exit(1)
        
    config_file = sys.argv[1]
    
    # NEW: Get a random seed from the Monte Carlo script
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    results_json = run_single_race(config_file_path=config_file, seed=seed)
    
    sys.stdout = original_stdout
    print(results_json)