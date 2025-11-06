from model import DeltaVModel

MAX_TIME_SECONDS = 100 # Run for 100 seconds
NUM_AGENTS = 2

print(f"--- Starting Delta-V Simulation (SimPy, {MAX_TIME_SECONDS}s) ---")

# 1. Create the Model
#    (This automatically creates the SimPy env and starts the processes)
model = DeltaVModel(num_agents=NUM_AGENTS)

# 2. Customize agents for an overtake test
model.f1_agents[0].unique_id = "Ocon"
model.f1_agents[0].strategy['top_speed'] = 83.0  # m/s (The car in front)

model.f1_agents[1].unique_id = "Bearman"
model.f1_agents[1].strategy['top_speed'] = 84.0  # m/s (The chasing car)

# 3. Run the SimPy environment
model.env.run(until=MAX_TIME_SECONDS)

print("\n--- Simulation Complete ---")