import sys
import os
import json
import statistics
from model import DeltaVModel

def run_single_race(config_file_path, seed): 
    """
    Runs one full, silent simulation from a config file.
    Returns a JSON string of the final race results.
    """
    
    with open(config_file_path, 'r') as f:
        config = json.load(f)
    
    race_laps = config['simulation_params']['race_laps']
    RACE_TIME_SECONDS = race_laps * 92 # ~100s per lap (safe buffer)
    
    # Pass the seed to the model
    model = DeltaVModel(config_file_path=config_file_path, seed=seed)
    model.env.run(until=RACE_TIME_SECONDS)
    
    # --- Collate Full Race Report ---
    final_results = []
    for agent in model.f1_agents:
        agent_data = {
            "driver": agent.unique_id,
            "team": agent.team,
            "laps_completed": agent.laps_completed,
            "total_race_time_s": round(agent.total_race_time_s, 2),
            "avg_lap_time_s": round(statistics.mean(agent.lap_times[1:]) if len(agent.lap_times) > 1 else 0, 2),
            "status": agent.status,
            "final_soc_pct": round(agent.battery_soc * 100, 2),
            "final_fuel_mj": round(agent.fuel_energy_remaining, 2),
            "final_tyre_life_pct": round(agent.tyre_life_remaining * 100, 2), 
            "final_tyre_compound": agent.tyre_compound,
            
            # --- Day 5 Stats ---
            "pit_stops_made": agent.pit_stops_made,
            "mom_uses": agent.mom_uses_count,
            "time_on_softs_s": round(agent.time_on_softs_s, 1),
            "time_on_mediums_s": round(agent.time_on_mediums_s, 1),
            "time_on_hards_s": round(agent.time_on_hards_s, 1)
        }
        final_results.append(agent_data)
    
    # Sort by status (RACING/FINISHED first), then laps, then time
    sorted_results = sorted(final_results, 
                            key=lambda x: (
                                0 if x["status"] in ["RACING", "FINISHED"] else 1, # Group DNFs at bottom
                                -x["laps_completed"], 
                                x["total_race_time_s"]
                            ))
    
    # Add final rank
    for i, res in enumerate(sorted_results):
        res["final_rank"] = i + 1
            
    return json.dumps(sorted_results)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.stderr.write("Error: No config file specified.\n")
        sys.exit(1)
    
    config_file = sys.argv[1]
    
    # Get a random seed from the Monte Carlo script (or None if not provided)
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    
    results_json = run_single_race(config_file_path=config_file, seed=seed)
    
    sys.stdout = original_stdout
    # Print ONLY the final JSON results
    print(results_json)