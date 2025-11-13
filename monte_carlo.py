import subprocess
import sys
import json
from collections import defaultdict
import time
import statistics
import os
import random

# --- CONFIGURATION ---
STARTING_GRID_FILE = "starting_grid.json"
NUM_RACES = 20 # Run 20 different random simulations of this grid
# ---------------------

def run_simulation_set(config_file, num_races):
    """Runs a set of races for a given config file."""
    print(f"\n--- RUNNING STRATEGIC ANALYSIS: {config_file} ---")
    
    all_race_results = [] 
    win_counts = defaultdict(int)
    
    for i in range(num_races):
        start_time = time.time()
        
        # NEW: Generate a unique seed for every single race
        race_seed = random.randint(0, 1000000)
        
        result = subprocess.run(
            [sys.executable, "run_headless.py", config_file, str(race_seed)], 
            capture_output=True, 
            text=True,
            encoding='utf-8'
        )
        
        try:
            # The output is now a JSON string
            race_data = json.loads(result.stdout.strip())
            winner = race_data[0] # Winner is first in the sorted list
            winner_name = f"{winner['driver']} ({winner['team']})"
            win_counts[winner_name] += 1
            all_race_results.append(race_data)
        except Exception as e:
            print(f"\nRace {i+1} FAILED. Could not parse JSON.")
            print(f"Error: {e}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}\n")
            continue
        
        duration = time.time() - start_time
        print(f" Race {i+1}/{num_races} complete (Seed: {race_seed}). Winner: {winner_name} (Time: {duration:.2f}s)")
    
    return win_counts, all_race_results

def analyze_results(title, all_results, num_races):
    """Prints a detailed analysis of a strategy."""
    print(f"\n--- {title.upper()} ANALYSIS ({num_races} races) ---")
    
    if not all_results:
        print(" No results to analyze.")
        return

    # --- 1. Win Tally ---
    win_counts = defaultdict(int)
    for race in all_results:
        if race: # Check if race data is not empty
            winner = race[0] 
            winner_name = f"{winner['driver']} ({winner['team']})"
            win_counts[winner_name] += 1
    
    print("\n 1. WIN TALLY (Top 5):")
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)
    for driver_team, wins in sorted_wins[:5]: 
        percentage = (wins / num_races) * 100
        print(f" > {driver_team}: {wins} wins ({percentage:.1f}%)")

    # --- 2. HAAS "REASON ENGINE" ANALYSIS ---
    haas_stats = {
        "Ocon": {"ranks": [], "pit_stops": [], "tyre_life": [], "status": defaultdict(int)},
        "Bearman": {"ranks": [], "pit_stops": [], "tyre_life": [], "status": defaultdict(int)}
    }
    
    for race in all_results:
        for driver in race:
            if driver["driver"] == "Ocon":
                haas_stats["Ocon"]["ranks"].append(driver["final_rank"])
                haas_stats["Ocon"]["pit_stops"].append(driver["pit_stops_made"])
                haas_stats["Ocon"]["tyre_life"].append(driver["final_tyre_life_pct"])
                haas_stats["Ocon"]["status"][driver["status"]] += 1
            elif driver["driver"] == "Bearman":
                haas_stats["Bearman"]["ranks"].append(driver["final_rank"])
                haas_stats["Bearman"]["pit_stops"].append(driver["pit_stops_made"])
                haas_stats["Bearman"]["tyre_life"].append(driver["final_tyre_life_pct"])
                haas_stats["Bearman"]["status"][driver["status"]] += 1
    
    print("\n 2. HAAS STRATEGY ANALYSIS (Avg. over 20 races):")
    
    # Ocon Analysis
    ocon_avg_rank = statistics.mean(haas_stats["Ocon"]["ranks"])
    ocon_avg_stops = statistics.mean(haas_stats["Ocon"]["pit_stops"])
    ocon_avg_tyre = statistics.mean(haas_stats["Ocon"]["tyre_life"])
    ocon_crashes = haas_stats["Ocon"]["status"]["CRASHED"] + haas_stats["Ocon"]["status"]["OUT_OF_ENERGY"]
    
    print("\n  Ocon (Aggressive / Soft Tyre Start):")
    print(f"    > Avg. Finishing Position: P{ocon_avg_rank:.1f}")
    print(f"    > Avg. Pit Stops: {ocon_avg_stops:.1f}")
    print(f"    > Avg. Final Tyre Life: {ocon_avg_tyre:.1f}%")
    print(f"    > Total DNFs (Crashes/Fuel): {ocon_crashes}")
    
    # Bearman Analysis
    bearman_avg_rank = statistics.mean(haas_stats["Bearman"]["ranks"])
    bearman_avg_stops = statistics.mean(haas_stats["Bearman"]["pit_stops"])
    bearman_avg_tyre = statistics.mean(haas_stats["Bearman"]["tyre_life"])
    bearman_crashes = haas_stats["Bearman"]["status"]["CRASHED"] + haas_stats["Bearman"]["status"]["OUT_OF_ENERGY"]
    
    print("\n  Bearman (Conservative / Hard Tyre Start):")
    print(f"    > Avg. Finishing Position: P{bearman_avg_rank:.1f}")
    print(f"    > Avg. Pit Stops: {bearman_avg_stops:.1f}")
    print(f"    > Avg. Final Tyre Life: {bearman_avg_tyre:.1f}%")
    print(f"    > Total DNFs (Crashes/Fuel): {bearman_crashes}")

if __name__ == "__main__":
    if not os.path.exists(STARTING_GRID_FILE):
        print(f"Error: Config file not found: {STARTING_GRID_FILE}")
        sys.exit(1)
    
    print("--- Starting Strategic Monte Carlo Analyzer ---")
    
    wins, results = run_simulation_set(STARTING_GRID_FILE, NUM_RACES)
    analyze_results(f"Strategy Analysis: {STARTING_GRID_FILE}", results, NUM_RACES)
    
    print("\n--- Strategic Analysis Complete ---")