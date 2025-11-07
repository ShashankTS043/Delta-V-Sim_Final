import subprocess
import sys
import json
from collections import defaultdict
import time
import statistics
import os
import random # <-- NEW

# --- CONFIGURATION ---
STARTING_GRID_FILE = "starting_grid.json"
NUM_RACES = 20 # Run 20 different random simulations of this grid
# ---------------------

def run_simulation_set(config_file, num_races):
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
            race_data = json.loads(result.stdout.strip())
            winner = race_data[0]
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
        print(f"  Race {i+1}/{num_races} complete (Seed: {race_seed}). Winner: {winner_name} (Time: {duration:.2f}s)")
        
    return win_counts, all_race_results

def analyze_results(title, all_results, num_races):
    print(f"\n--- {title.upper()} ANALYSIS ({num_races} races) ---")
    
    if not all_results:
        print("  No results to analyze.")
        return

    # 1. Win Tally
    win_counts = defaultdict(int)
    for race in all_results:
        winner = race[0] 
        winner_name = f"{winner['driver']} ({winner['team']})"
        win_counts[winner_name] += 1
        
    print("\n  1. WIN TALLY (Top 5):")
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)
    for driver_team, wins in sorted_wins[:5]: 
        percentage = (wins / num_races) * 100
        print(f"    > {driver_team}: {wins} wins ({percentage:.1f}%)")

    # 2. Performance Analysis
    haas_results = {"Ocon": [], "Bearman": []}
    all_final_soc = []
    all_final_tyre = []
    
    for race in all_results:
        for driver in race:
            if driver["driver"] == "Ocon":
                haas_results["Ocon"].append(driver["final_tyre_life"])
            if driver["driver"] == "Bearman":
                haas_results["Bearman"].append(driver["final_tyre_life"])
            all_final_soc.append(driver['final_soc_pct'])
            all_final_tyre.append(driver['final_tyre_life'])
            
    avg_soc = statistics.mean(all_final_soc)
    avg_tyre = statistics.mean(all_final_tyre)
    
    # NEW: Specific Haas analysis
    avg_ocon_tyre = statistics.mean(haas_results["Ocon"])
    avg_bearman_tyre = statistics.mean(haas_results["Bearman"])

    print("\n  2. PERFORMANCE METRICS (Grid-wide):")
    print(f"    > Avg. Final Battery: {avg_soc:.2f}%")
    print(f"    > Avg. Final Tyre Life: {avg_tyre:.2f}%")
    
    print("\n  3. HAAS STRATEGY ANALYSIS:")
    print(f"    > Ocon (Aggressive) Avg. Tyre Life: {avg_ocon_tyre:.2f}%")
    print(f"    > Bearman (Conservative) Avg. Tyre Life: {avg_bearman_tyre:.2f}%")


if __name__ == "__main__":
    if not os.path.exists(STARTING_GRID_FILE):
        print(f"Error: Config file not found: {STARTING_GRID_FILE}")
        sys.exit(1)
        
    print("--- Starting Strategic Monte Carlo Analyzer ---")
    
    wins, results = run_simulation_set(STARTING_GRID_FILE, NUM_RACES)
    analyze_results(f"Strategy Analysis: {STARTING_GRID_FILE}", results, NUM_RACES)
    
    print("\n--- Strategic Analysis Complete ---")