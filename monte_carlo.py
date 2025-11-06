import subprocess
import sys
from collections import defaultdict

NUM_RACES = 20  # Let's start with 20. You can set this to 1000 later.

print(f"--- Starting Monte Carlo Simulation ({NUM_RACES} races) ---")

win_counts = defaultdict(int)

for i in range(NUM_RACES):
    # Print progress
    print(f"Running race {i+1} of {NUM_RACES}...")

    # This runs `python3 run_headless.py` as a separate process
    # and captures its output.
    result = subprocess.run(
        [sys.executable, "run_headless.py"], 
        capture_output=True, 
        text=True
    )

    # The output of the script is just the winner's name
    winner = result.stdout.strip()

    if winner:
        win_counts[winner] += 1
    else:
        print(f"Race {i+1} failed or had no winner.")

print("\n--- Monte Carlo Simulation Complete ---")
print("WIN TALLY:")
for driver, wins in win_counts.items():
    percentage = (wins / NUM_RACES) * 100
    print(f"  > {driver}: {wins} wins ({percentage:.1f}%)")