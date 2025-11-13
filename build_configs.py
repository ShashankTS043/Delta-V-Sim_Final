import json
import copy
import os

print("Building config files...")

# 1. Load the building blocks
try:
    with open('roster_2026.json', 'r') as f:
        roster_data = json.load(f)

    with open('strategy_default.json', 'r') as f:
        default_strategy_data = json.load(f)
except FileNotFoundError as e:
    print(f"Error: Missing base file {e.filename}. Cannot build configs.")
    exit()

# 2. Define our simulation parameters
sim_params = {
    "simulation_params": {
        "race_laps": 15,
        "time_step": 0.1
    }
}

# 3. Build: config_aggressive.json
aggressive_config = copy.deepcopy(sim_params)
aggressive_config["driver_roster"] = []

for driver in roster_data["driver_roster"]:
    new_driver = copy.deepcopy(driver)
    
    strategy = copy.deepcopy(default_strategy_data["strategy"])
    strategy["top_speed"] = 85.0
    strategy["mom_aggressiveness"] = 0.9
    strategy["c_1_power"] = 0.0000012
    strategy["grip_factor"] = 22.0
    strategy["tyre_wear_rate_soft"] = 0.003
    strategy["tyre_wear_rate_medium"] = 0.002
    strategy["tyre_wear_rate_hard"] = 0.001
    strategy["pit_window_open_lap"] = 2
    
    new_driver["strategy"] = strategy
    aggressive_config["driver_roster"].append(new_driver)

with open('config_aggressive.json', 'w') as f:
    json.dump(aggressive_config, f, indent=2)
print("Successfully built config_aggressive.json")

# 4. Build: config_conservative.json
conservative_config = copy.deepcopy(sim_params)
conservative_config["driver_roster"] = []

for driver in roster_data["driver_roster"]:
    new_driver = copy.deepcopy(driver)
    
    strategy = copy.deepcopy(default_strategy_data["strategy"])
    strategy["top_speed"] = 82.0
    strategy["mom_aggressiveness"] = 0.25
    strategy["c_1_power"] = 0.0000008
    strategy["grip_factor"] = 21.0
    strategy["tyre_wear_rate_soft"] = 0.0015
    strategy["tyre_wear_rate_medium"] = 0.0008
    strategy["tyre_wear_rate_hard"] = 0.0004
    strategy["pit_window_open_lap"] = 7
    
    new_driver["strategy"] = strategy
    conservative_config["driver_roster"].append(new_driver)

with open('config_conservative.json', 'w') as f:
    json.dump(conservative_config, f, indent=2)
print("Successfully built config_conservative.json")

# 5. Build our Haas vs. Field strategies
print("Building Haas vs. Field strategy files...")
try:
    # Create Haas Aggressive
    haas_agg_strat = copy.deepcopy(default_strategy_data["strategy"])
    haas_agg_strat["top_speed"] = 85.0
    haas_agg_strat["grip_factor"] = 22.0
    haas_agg_strat["c_1_power"] = 0.0000012
    haas_agg_strat["tyre_wear_rate_soft"] = 0.003 # Tuned from 
    haas_agg_strat["tyre_wear_rate_medium"] = 0.002
    haas_agg_strat["tyre_wear_rate_hard"] = 0.001
    haas_agg_strat["mom_aggressiveness"] = 0.9
    haas_agg_strat["pit_window_open_lap"] = 2 # Tuned from 
    with open('strategy_haas_aggressive.json', 'w') as f:
        json.dump({"strategy": haas_agg_strat}, f, indent=2)

    # Create Haas Conservative
    haas_con_strat = copy.deepcopy(default_strategy_data["strategy"])
    haas_con_strat["top_speed"] = 82.0
    haas_con_strat["grip_factor"] = 21.0
    haas_con_strat["c_1_power"] = 0.0000008
    haas_con_strat["tyre_wear_rate_soft"] = 0.0015 # Tuned from 
    haas_con_strat["tyre_wear_rate_medium"] = 0.0008
    haas_con_strat["tyre_wear_rate_hard"] = 0.0004
    haas_con_strat["mom_aggressiveness"] = 0.3
    with open('strategy_haas_conservative.json', 'w') as f:
        json.dump({"strategy": haas_con_strat}, f, indent=2)

    # Create Field Baseline
    field_base_strat = copy.deepcopy(default_strategy_data["strategy"])
    field_base_strat["tyre_wear_rate_soft"] = 0.002 # Tuned from 
    field_base_strat["tyre_wear_rate_medium"] = 0.001
    field_base_strat["tyre_wear_rate_hard"] = 0.0005
    with open('strategy_field_baseline.json', 'w') as f:
        json.dump({"strategy": field_base_strat}, f, indent=2)
    
    print("Successfully built Haas and Field strategy files.")
except Exception as e:
    print(f"Error building Haas/Field strategies: {e}")


print("\nConfig generation complete.")