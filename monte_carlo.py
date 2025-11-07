import subprocess
import sys
import json
from collections import defaultdict
import time
import statistics
import os

# --- CONFIGURATION ---
CONFIG_A = "config_aggressive.json"
CONFIG_B = "config_conservative.json"
NUM_RACES_PER_CONFIG = 10 # Run 10 races for each strategy
# ---------------------

def run_simulation_set(config_file, num_races):
    """Runs a set of races for a given config file."""
    print(f"\n--- RUNNING STRATEGY: {config_file} ---")
    
    all_race_results = [] # Store full results for analysis
    win_counts = defaultdict(int)
    
    for i in range(num_races):
        start_time = time.time()
        
        # Pass the config file to the headless runner
        result = subprocess.run(
            [sys.executable, "run_headless.py", config_file], 
            capture_output=True, 
            text=True,
            encoding='utf-8' # Ensure correct encoding
        )
        
        # The output is now a JSON string
        try:
            # result.stdout will be the JSON list of all 22 drivers
            race_data = json.loads(result.stdout.strip())
            winner = race_data[0] # The winner is the first in the sorted list
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
        print(f"  Race {i+1}/{num_races} complete. Winner: {winner_name} (Time: {duration:.2f}s)")
        
    return win_counts, all_race_results

def analyze_results(title, all_results, num_races):
    """Prints a detailed analysis of a strategy."""
    print(f"\n--- {title.upper()} ANALYSIS ({num_races} races) ---")
    
    if not all_results:
        print("  No results to analyze.")
        return

    # 1. Win Tally
    win_counts = defaultdict(int)
    for race in all_results:
        winner = race[0] # Winner is the first entry
        winner_name = f"{winner['driver']} ({winner['team']})"
        win_counts[winner_name] += 1
        
    print("\n  1. WIN TALLY:")
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)
    for driver_team, wins in sorted_wins[:5]: # Print top 5 winners
        percentage = (wins / num_races) * 100
        print(f"    > {driver_team}: {wins} wins ({percentage:.1f}%)")

    # 2. Performance Analysis (Your "Richer Comparison")
    all_final_soc = []
    all_status_counts = defaultdict(int)
    
    for race in all_results:
        for driver in race:
            if driver['status'] == "OUT_OF_ENERGY":
                all_status_counts["OUT_OF_ENERGY"] += 1
            all_final_soc.append(driver['final_soc_pct'])
            
    avg_soc = statistics.mean(all_final_soc)
    dnf_count = all_status_counts["OUT_OF_ENERGY"]
    dnf_rate = (dnf_count / (num_races * len(all_results[0]))) * 100

    print("\n  2. PERFORMANCE METRICS:")
    print(f"    > Avg. Final Battery (Grid-wide): {avg_soc:.2f}%")
    print(f"    > Total 'Out of Energy' (DNFs): {dnf_count} ({dnf_rate:.1f}%)")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(CONFIG_A) or not os.path.exists(CONFIG_B):
        print(f"Error: Config files not found. Run 'python3 build_configs.py' first.")
        sys.exit(1)
        
    print("--- Starting Strategic Monte Carlo Analyzer ---")
    
    # Run the "Aggressive" config
    wins_A, results_A = run_simulation_set(CONFIG_A, NUM_RACES_PER_CONFIG)
    
    # Run the "Conservative" config
    wins_B, results_B = run_simulation_set(CONFIG_B, NUM_RACES_PER_CONFIG)
    
    # Print the final comparison
    analyze_results(f"Strategy '{CONFIG_A}'", results_A, NUM_RACES_PER_CONFIG)
    analyze_results(f"Strategy '{CONFIG_B}'", results_B, NUM_RACES_PER_CONFIG)
    
    print("\n--- Strategic Analysis Complete ---")