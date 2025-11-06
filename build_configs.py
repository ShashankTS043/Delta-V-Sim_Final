import json
import copy

print("Building config files...")

# --- 1. Load the building blocks ---
with open('roster_2026.json', 'r') as f:
    roster_data = json.load(f)

with open('strategy_default.json', 'r') as f:
    default_strategy_data = json.load(f)

# --- 2. Define our simulation parameters ---
sim_params = {
    "simulation_params": {
        "race_laps": 3,
        "time_step": 0.1
    }
}

# --- 3. Build: config_aggressive.json ---
aggressive_config = copy.deepcopy(sim_params)
aggressive_config["driver_roster"] = []

for driver in roster_data["driver_roster"]:
    new_driver = copy.deepcopy(driver)
    
    # Create the "Aggressive" strategy
    strategy = copy.deepcopy(default_strategy_data["strategy"])
    strategy["top_speed"] = 85.0          # Higher top speed
    strategy["mom_aggressiveness"] = 0.9  # Use MOM almost always
    strategy["c_1_power"] = 0.0000012     # Burn slightly more energy
    
    new_driver["strategy"] = strategy
    aggressive_config["driver_roster"].append(new_driver)

# Write the file
with open('config_aggressive.json', 'w') as f:
    json.dump(aggressive_config, f, indent=2)
print("Successfully built config_aggressive.json")

# --- 4. Build: config_conservative.json ---
conservative_config = copy.deepcopy(sim_params)
conservative_config["driver_roster"] = []

for driver in roster_data["driver_roster"]:
    new_driver = copy.deepcopy(driver)
    
    # Create the "Conservative" strategy
    strategy = copy.deepcopy(default_strategy_data["strategy"])
    strategy["top_speed"] = 82.0          # Lower top speed to save fuel
    strategy["mom_aggressiveness"] = 0.25 # Rarely use MOM
    strategy["c_1_power"] = 0.0000008     # Burn less energy
    
    new_driver["strategy"] = strategy
    conservative_config["driver_roster"].append(new_driver)

# Write the file
with open('config_conservative.json', 'w') as f:
    json.dump(conservative_config, f, indent=2)
print("Successfully built config_conservative.json")

print("\nConfig generation complete.")