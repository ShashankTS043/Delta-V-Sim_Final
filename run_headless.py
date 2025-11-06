import sys
import os  # <-- ADD THIS LINE
from model import DeltaVModel

# Run a full race (Bahrain is ~90s per lap, so 57 laps is ~5130s)
# We'll do a 3-lap race for a quick test
RACE_LAPS = 3
RACE_TIME_SECONDS = 95 * RACE_LAPS # 95s per lap

def run_single_race():
    """
    Runs one full, silent simulation and returns the winner.
    """
    model = DeltaVModel(num_agents=2)
    
    # Setup the strategies
    model.f1_agents[0].unique_id = "Ocon"
    model.f1_agents[0].strategy['top_speed'] = 83.0  # Car A

    model.f1_agents[1].unique_id = "Bearman"
    model.f1_agents[1].strategy['top_speed'] = 84.0  # Car B
    
    # Run the SimPy environment
    model.env.run(until=RACE_TIME_SECONDS)
    
    # --- Determine the winner ---
    # We sort by total distance traveled
    sorted_agents = sorted(model.f1_agents, 
                           key=lambda x: x.total_distance_traveled, 
                           reverse=True)
    
    winner = sorted_agents[0].unique_id
    return winner

# This part lets the file be run by itself
if __name__ == "__main__":
    # This will make our multiprocessing script work
    # We silence all print statements by redirecting them
    sys.stdout = open(os.devnull, 'w')
    winner_name = run_single_race()
    sys.stdout = sys.__stdout__ # Restore print
    
    # Print ONLY the winner's name
    print(winner_name)