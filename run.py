from model import DeltaVModel

# --- Simulation Parameters ---
NUM_AGENTS = 2
MAX_STEPS = 1000

print("--- Starting Delta-V Simulation (Bahrain Circuit) ---")

# 1. Create the Model
model = DeltaVModel(num_agents=NUM_AGENTS)

# --- Customize agents using our NEW 'f1_agents' list ---
model.f1_agents[0].unique_id = "Ocon"
model.f1_agents[0].strategy['top_speed'] = 85.0  # m/s

model.f1_agents[1].unique_id = "Bearman"
model.f1_agents[1].strategy['top_speed'] = 83.0  # m/s (slightly slower)


# 2. Run the Simulation
for i in range(MAX_STEPS):
    print(f"\n--- Step {i} ---")
    model.step()
    
    # --- Print agent states using our NEW 'f1_agents' list ---
    for agent in model.f1_agents:
        print(f"  > Agent {agent.unique_id}: \
Node {agent.position[0]}, \
Progress: {agent.position[1]*100:.1f}%, \
V: {agent.velocity} m/s, \
SOC: {agent.battery_soc*100:.2f}%")

print("\n--- Simulation Complete ---")