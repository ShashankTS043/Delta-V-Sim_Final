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
        if race:
            winner = race[0] 
            winner_name = f"{winner['driver']} ({winner['team']})"
            win_counts[winner_name] += 1
    
    print("\n 1. WIN TALLY (Top 5):")
    sorted_wins = sorted(win_counts.items(), key=lambda item: item[1], reverse=True)
    for driver_team, wins in sorted_wins[:5]: 
        percentage = (wins / num_races) * 100
        print(f" > {driver_team}: {wins} wins ({percentage:.1f}%)")

    # --- 2. HAAS "ENERGY STRATEGY" REASON ENGINE ---
    haas_stats = {
        "Ocon": {"ranks": [], "race_times": [], "fuel_left": [], "mom_uses": [], "status": defaultdict(int), "positions_gained": []},
        "Bearman": {"ranks": [], "race_times": [], "fuel_left": [], "mom_uses": [], "status": defaultdict(int), "positions_gained": []}
    }
    
    # Load the grid config ONCE to get starting positions
    with open(STARTING_GRID_FILE, 'r') as f:
        grid_config = json.load(f)
    starting_positions = {entry['driver']: entry['pos'] for entry in grid_config['grid']}

    for race in all_results:
        for driver in race:
            start_pos = starting_positions.get(driver['driver'], -1)
            
            if driver["driver"] == "Ocon":
                haas_stats["Ocon"]["ranks"].append(driver["final_rank"])
                haas_stats["Ocon"]["fuel_left"].append(driver["final_fuel_mj"])
                haas_stats["Ocon"]["mom_uses"].append(driver["mom_uses"])
                haas_stats["Ocon"]["status"][driver["status"]] += 1
                if driver["status"] == "FINISHED":
                    haas_stats["Ocon"]["race_times"].append(driver["total_race_time_s"])
                    haas_stats["Ocon"]["positions_gained"].append(start_pos - driver['final_rank'])
                    
            elif driver["driver"] == "Bearman":
                haas_stats["Bearman"]["ranks"].append(driver["final_rank"])
                haas_stats["Bearman"]["fuel_left"].append(driver["final_fuel_mj"])
                haas_stats["Bearman"]["mom_uses"].append(driver["mom_uses"])
                haas_stats["Bearman"]["status"][driver["status"]] += 1
                if driver["status"] == "FINISHED":
                    haas_stats["Bearman"]["race_times"].append(driver["total_race_time_s"])
                    haas_stats["Bearman"]["positions_gained"].append(start_pos - driver['final_rank'])
    
    print("\n 2. HAAS STRATEGY ANALYSIS (Avg. over 20 races):")
    
    # Ocon Analysis
    ocon_avg_rank = statistics.mean(haas_stats["Ocon"]["ranks"])
    ocon_avg_time = statistics.mean(haas_stats["Ocon"]["race_times"]) if haas_stats["Ocon"]["race_times"] else 0
    ocon_avg_fuel = statistics.mean(haas_stats["Ocon"]["fuel_left"])
    ocon_avg_mom = statistics.mean(haas_stats["Ocon"]["mom_uses"])
    ocon_avg_pos_gained = statistics.mean(haas_stats["Ocon"]["positions_gained"]) if haas_stats["Ocon"]["positions_gained"] else 0
    ocon_dnfs = haas_stats["Ocon"]["status"]["CRASHED"] + haas_stats["Ocon"]["status"]["OUT_OF_ENERGY"]
    
    print("\n  Ocon (Energy BURN Strategy):")
    print(f"    > Avg. Finishing Position: P{ocon_avg_rank:.1f}")
    print(f"    > Avg. Positions Gained/Lost (on finish): {ocon_avg_pos_gained:+.1f}")
    print(f"    > Avg. Total Race Time (on finish): {ocon_avg_time:.1f} s")
    print(f"    > Avg. MOM Uses: {ocon_avg_mom:.1f}")
    print(f"    > Avg. Final Fuel Remaining: {ocon_avg_fuel:.1f} MJ")
    print(f"    > Total DNFs (Crashes/Fuel): {ocon_dnfs}")

    
    # Bearman Analysis
    bearman_avg_rank = statistics.mean(haas_stats["Bearman"]["ranks"])
    bearman_avg_time = statistics.mean(haas_stats["Bearman"]["race_times"]) if haas_stats["Bearman"]["race_times"] else 0
    bearman_avg_fuel = statistics.mean(haas_stats["Bearman"]["fuel_left"])
    bearman_avg_mom = statistics.mean(haas_stats["Bearman"]["mom_uses"])
    bearman_avg_pos_gained = statistics.mean(haas_stats["Bearman"]["positions_gained"]) if haas_stats["Bearman"]["positions_gained"] else 0
    bearman_dnfs = haas_stats["Bearman"]["status"]["CRASHED"] + haas_stats["Bearman"]["status"]["OUT_OF_ENERGY"]
    
    print("\n  Bearman (Energy SAVE Strategy):")
    print(f"    > Avg. Finishing Position: P{bearman_avg_rank:.1f}")
    print(f"    > Avg. Positions Gained/Lost (on finish): {bearman_avg_pos_gained:+.1f}")
    print(f"    > Avg. Total Race Time (on finish): {bearman_avg_time:.1f} s")
    print(f"    > Avg. MOM Uses: {bearman_avg_mom:.1f}")
    print(f"    > Avg. Final Fuel Remaining: {bearman_avg_fuel:.1f} MJ")
    print(f"    > Total DNFs (Crashes/Fuel): {bearman_dnfs}")

if __name__ == "__main__":
    if not os.path.exists(STARTING_GRID_FILE):
        print(f"Error: Config file not found: {STARTING_GRID_FILE}")
        sys.exit(1)
    
    print("--- Starting Strategic Monte Carlo Analyzer ---")
    
    wins, results = run_simulation_set(STARTING_GRID_FILE, NUM_RACES)
    analyze_results(f"Strategy Analysis: {STARTING_GRID_FILE}", results, NUM_RACES)
    
    print("\n--- Strategic Analysis Complete ---")