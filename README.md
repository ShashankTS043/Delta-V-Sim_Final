Delta-V Sim: The 2026 F1 "Reason Engine"
[TrackShift Innovation Challenge 2025]

Delta-V Sim is a professional-grade, stochastic race simulator built in Python to model the complex strategic landscape of the 2026 Formula 1 regulations.

It's not just a visualizer; it's a powerful "Reason Engine" designed to analyze the deep, counter-intuitive trade-offs between Tyre Wear, Fuel Burn, and Battery Deployment.

This platform is built on a "Universal AI" architecture, allowing it to run two distinct, high-level simulation modes:

A 22-Car Stochastic Race (Pro+): A full-grid simulation to test how a randomized energy strategy (e.g., mom_aggressiveness: 0.9) performs against 20 unique AI opponents, random VSCs, and random driver errors.

A 2-Car "Dyno Test" (Pro++): A 1v1 "dyno" to compare two specific, deterministic, segment-by-segment "Energy Maps" (e.g., "Deploy on all straights" vs. "Tactical Save").

1. The Problem: The 2026 "Energy Reset"
The 2026 F1 regulations are the biggest strategic shift in decades. Winning will no longer be about the fastest car, but the smartest strategy.

New 50/50 Power Unit: A 350kW MGU-K (battery) and a 4600 MJ (110kg) fuel tank (ICE) force a constant, complex trade-off between the two power sources.

Advanced MOM Physics: The new "push-to-pass" system is not a simple button. It's a complex regulation:

Standard: Electrical power tapers off after 290 kph.

MOM Active: A driver can choose to push to 337 kph, but at the cost of 0.5 MJ of extra battery energy.

2. Our Solution: A "Reason Engine"
Delta-V Sim is a platform that lets a team like MoneyGram Haas F1 run thousands of 57-lap race simulations to find the optimal strategy before the first race.

Our "Reason Engine" (monte_carlo.py) can answer deep strategic questions:

Pro+ (22-Car): "In a full, chaotic race, is an 'Energy Burn' (high-MOM) or 'Energy Save' (low-MOM) strategy statistically faster and more reliable?"

Pro++ (2-Car): "Is it faster to deploy MOM on all straights, or to save it for the long straights? What is the exact fuel cost and lap time trade-off of these two 'Energy Maps'?"

3. Core Features
"Universal Agent" AI: The core of the simulation. A single agent.py "brain" that automatically detects its strategy type.

If mom_aggressiveness is found: It runs in "Pro+" mode, using random chance to deploy MOM.

If energy_deployment_map is found: It runs in "Pro++" mode, executing a perfect, deterministic energy plan from its strategy file.

Full 50/50 Power Unit: A realistic physics model where agents must manage both the fuel_energy_remaining (ICE) and the regenerating battery_soc (MGU-K). Energy costs are tuned so that fuel is a critical, race-deciding resource.

Advanced 2026 MOM Physics: Implements the real 2026 "push-to-pass" regulation. Standard cars are capped at 290 kph, but activating MOM grants 0.5 MJ of extra battery energy and raises the speed limit to 337 kph.

Realistic 57-Lap Race Model:

Tyre Wear: A 3-compound (S/M/H) tyre model tuned so that a 0-stop strategy is impossible.

Pit Stop AI: Agents' "brains" (perceive()) correctly monitor tyre wear and pit window openings to execute multi-stop strategies.

Chequered Flag: The simulation ends exactly when the winner completes Lap 57.

Stochastic World Engine:

"Strategy Noise": All 20 "field" cars have their physics (top speed, grip) randomized to ensure no two races are identical.

Random VSCs: The "Race Master" (model.py) deploys random Virtual Safety Cars.

Driver Error: Every agent has a tiny, random chance on each step to make a mistake and crash.

4. Core Architecture
Simulation Core (Mesa): We use Mesa to give each F1Agent an autonomous "brain" to perceive its environment and make decisions.

Environment & Track (NetworkX): The racetrack is a networkx directed graph of 15 turns (Bahrain) with a full, multi-segment pit lane.

Data & Analytics (JSON/Python): The "Reason Engine" (monte_carlo.py) runs headless simulations, gathers JSON reports, and performs a final statistical analysis.

Visualization (Pygame & Matplotlib): A decoupled frontend reads the live data.json to show the 2D race and data leaderboards.

5. How to Run
This project uses Python 3.12+ and a virtual environment.

1. Local Setup
Bash

# Clone the repository
git clone https://github.com/ShashankTS043/Delta-V-Sim.git
cd Delta-V-Sim

# Create and activate the virtual environment
# On macOS
python3 -m venv venv
source venv/bin/activate
# On Windows
# python -m venv venv
# .\venv\Scripts\activate

# Install all required libraries
pip install -r requirements.txt
2. Run the Live 22-Car Simulation (Visual Mode)
This runs the full 22-car race (using starting_grid.json) and outputs the live data.json file for your frontend visualizer.

Bash

python3 run.py
3. Run the "Reason Engine" (Headless Analysis)
This is the main analysis tool. It runs 20 full, headless 57-lap races and prints a final strategic summary.

To run the 22-car "Pro+" simulation (Random MOM):

Bash

# This is the default
python3 monte_carlo.py

# You can also specify the grid file
python3 monte_carlo.py starting_grid.json
To run the 2-car "Pro++" Dyno Test (Energy Maps):

Bash

python3 monte_carlo.py two_car_grid.json
6. Our Team
Shashank T S

Shreekesh S

Arjun H Athreya
