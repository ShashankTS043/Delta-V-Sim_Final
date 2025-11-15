import random
import json
import simpy
import copy
import os
import glob
import time
from datetime import datetime
from mesa import Model
from agent import F1Agent
from track_graph import build_bahrain_track

# --- (write_simulation_data function is unchanged) ---
def write_simulation_data(data, folder=".", prefix="data_snapshot_", keep_last=12):
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fname = f"{prefix}{ts}.json"
    temp_path = os.path.join(folder, f"{fname}.tmp")
    final_path = os.path.join(folder, fname)
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.rename(temp_path, final_path)
    except Exception as e:
        print(f"Error writing snapshot file {final_path}: {e}")
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except Exception: pass
        return None
    try:
        pattern = os.path.join(folder, f"{prefix}*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        for old in files[keep_last:]:
            try:
                os.remove(old)
            except Exception:
                pass
    except Exception:
        pass
    return final_path
# --- (End of function) ---


class DeltaVModel(Model):
    def __init__(self, config_file_path, seed=None, live_snapshot_mode=False):
        self.env = simpy.Environment()
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        self.random = random.Random(self.seed)
        self.running = True
        self.space = None
        self.live_snapshot_mode = live_snapshot_mode
        self.vsc_active = False
        self.step_count = 0
        self.race_over = False
        
        # --- Weather State ---
        self.weather_state = "DRY"
        
        with open(config_file_path, 'r') as f:
            self.config = json.load(f)
        sim_params = self.config['simulation_params']
        starting_grid = self.config['grid']
        self.num_agents = len(starting_grid)
        self.time_step = sim_params['time_step']
        self.race_laps = self.config['simulation_params']['race_laps']
        self.track = build_bahrain_track()
        self.track_length = sum(data['length'] for u, v, data in self.track.edges(data=True))
        self.f1_agents = []
        strategy_cache = {}
        for driver_data in starting_grid:
            strategy_file = driver_data['strategy_file']
            if strategy_file not in strategy_cache:
                with open(strategy_file, 'r') as f:
                    strategy_cache[strategy_file] = json.load(f) 
            strategy_config = copy.deepcopy(strategy_cache[strategy_file]["strategy"])
            
            # --- START FINAL RANDOMNESS (for car-to-car variability) ---
            plank_noise = self.random.uniform(0.97, 1.03) # +/- 3%
            g_noise = self.random.uniform(0.98, 1.02) # +/- 2%
            
            strategy_config["plank_wear_factor"] = plank_noise
            strategy_config["g_factor"] = g_noise
            # --- END FINAL RANDOMNESS ---

            if "haas" not in strategy_file:
                speed_noise = self.random.uniform(0.99, 1.01)
                strategy_config["standard_top_speed_kph"] *= speed_noise
                grip_noise = self.random.uniform(0.95, 1.05)
                strategy_config["grip_factor"] *= grip_noise
                if "mom_aggressiveness" in strategy_config:
                    mom_noise = self.random.uniform(0.95, 1.05)
                    strategy_config["mom_aggressiveness"] *= mom_noise
            a = F1Agent(
                unique_id=driver_data['driver'], 
                model=self, 
                strategy_config=strategy_config
            )
            a.team = driver_data['team']
            a.tyre_compound = driver_data['tyre']
            start_pos_meters = driver_data['pos'] * 10.0
            start_node_edge = self.track.get_edge_data("n_t15_apex", "n_t1_brake")
            start_progress = -(start_pos_meters / start_node_edge['length'])
            a.position = ("n_t15_apex", start_progress)
            a.total_distance_traveled = start_progress * start_node_edge['length']
            self.f1_agents.append(a)
            
        # --- Start SimPy Processes ---
        self.env.process(self.run_simulation_steps())
        
        # --- REMOVED RANDOMNESS: Random VSC is disabled. ---
        # The dashboard is now the sole source of race control.
        # self.env.process(self.race_master_events()) 
        # --- END REMOVED RANDOMNESS ---
        
        self.env.process(self.weather_system())

    def run_simulation_steps(self):
        try:
            while True:
                self.random.shuffle(self.f1_agents)
                for agent in self.f1_agents:
                    agent.step()
                
                data = self.get_simulation_data()
                
                if self.live_snapshot_mode:
                    write_simulation_data(data)
                
                self.step_count += 1
                
                if self.race_over:
                    print("--- CHEQUERED FLAG: Race has ended. ---")
                    self.running = False
                    
                    # --- NEW: Dump all historical telemetry ---
                    num_records = self.dump_full_telemetry()
                    print(f"--- TELEMETRY DUMPED: {num_records} records saved to telemetry_history.json ---")
                    # --- END NEW ---
                    
                    break
                        
                yield self.env.timeout(self.time_step)
        except simpy.Interrupt:
            self.running = False
            print("Simulation interrupted.")

    def race_master_events(self):
        """
        This process is now inactive in this deterministic version.
        """
        pass

    def weather_system(self):
        """
        Implements a continuous weather cycle: (Dry Wait) -> (Rain for 10 Laps) -> (Dry Wait)
        """
        RAIN_DURATION_SECONDS = 900.0 # Approx 10 laps (90s/lap)

        while not self.race_over:
            # 1. DRY PHASE: Wait for a random period (10-20 min of sim time)
            if self.weather_state == "DRY":
                time_to_rain_check = self.random.uniform(600, 1200) 
                yield self.env.timeout(time_to_rain_check)

                if self.race_over: return
                
                # Check for rain chance (50% chance of the dry period ending)
                if self.random.random() < 0.5: 
                     self.weather_state = "WET"
                     print(f"\n--- WEATHER: IT'S STARTING TO RAIN! (t={self.env.now:.1f}s) ---\n")
            
            # 2. WET PHASE: Rain is falling, wait for the duration
            elif self.weather_state == "WET":
                print(f"--- RAIN: Expecting track to dry in {RAIN_DURATION_SECONDS/60:.0f} minutes. ---")
                
                # Wait for the fixed 10-lap duration
                yield self.env.timeout(RAIN_DURATION_SECONDS)

                if self.race_over: return
                
                # Track dries up
                self.weather_state = "DRY"
                print(f"\n--- WEATHER: THE TRACK IS DRYING UP! (t={self.env.now:.1f}s) ---\n")

    # --- NEW: Telemetry Dump Function ---
    def dump_full_telemetry(self):
        """
        Compiles the telemetry_history from all agents into a single JSON file.
        Used for CSV export after the race.
        """
        all_telemetry = []
        for agent in self.f1_agents:
            # Add the history for each agent
            all_telemetry.extend(agent.telemetry_history)
        
        # Sort by simulation time
        all_telemetry.sort(key=lambda x: x['sim_time'])

        # Write the data to a file that the dashboard can access
        with open("telemetry_history.json", "w") as f:
            json.dump(all_telemetry, f, indent=2)

        return len(all_telemetry)
    # --- END NEW ---

    def get_simulation_data(self):
        """
        Builds a dictionary of the current simulation state
        """
        
        def format_lap_time(s):
            if s <= 0: return "0:00.000"
            minutes = int(s // 60)
            seconds = int(s % 60)
            milliseconds = int((s * 1000) % 1000)
            return f"{minutes}:{seconds:02d}.{milliseconds:03d}"
        
        sorted_agents = sorted(self.f1_agents,
                                key=lambda x: x.total_distance_traveled,
                                reverse=True)
        
        leader_lap = 1
        if sorted_agents:
            leader = sorted_agents[0]
            leader_lap = leader.laps_completed + 1
            if leader_lap > self.race_laps:
                leader_lap = self.race_laps

        race_status = {
            "timestamp": format_lap_time(self.env.now),
            "current_lap": leader_lap,
            "total_laps": self.race_laps,
            "safety_car": "VSC" if self.vsc_active else "NONE",
            "weather": self.weather_state
        }

        agent_list = []
        for i, agent in enumerate(sorted_agents):
            
            # --- Position Interpolation (Unchanged) ---
            start_node_name = agent.position[0]
            progress_on_edge = agent.position[1]
            end_node_name = agent.get_next_node_from_successors()
            start_pos = self.track.nodes[start_node_name]['pos']
            end_pos = None
            if end_node_name and end_node_name in self.track.nodes:
                end_pos = self.track.nodes[end_node_name]['pos']
            else:
                end_pos = start_pos
            interp_x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress_on_edge
            interp_y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress_on_edge
            interpolated_position = [interp_x, interp_y]

            last_lap_s = agent.lap_times[-1] if agent.lap_times else 0.0
            fastest_lap_s = min(agent.lap_times) if agent.lap_times else 0.0
            
            # --- START NOISE CALCULATION ---
            energy_noise_factor = self.random.uniform(0.98, 1.02)
            tyre_noise_factor = self.random.uniform(0.99, 1.01)
            temp_noise_absolute = self.random.uniform(-1.0, 1.0)
            
            # 1. SOC (0.0 to 1.0)
            noisy_soc = agent.battery_soc * energy_noise_factor
            noisy_soc = max(0.0, min(1.0, noisy_soc))
            
            # 2. Fuel (MJ)
            noisy_fuel = agent.fuel_energy_remaining * energy_noise_factor
            noisy_fuel = max(0.0, noisy_fuel)
            
            # 3. Tyre Life (0.0 to 1.0)
            noisy_tyre_life = agent.tyre_life_remaining * tyre_noise_factor
            noisy_tyre_life = max(0.0, min(1.0, noisy_tyre_life))
            
            # 4. Tyre Temp (C)
            noisy_tyre_temp = agent.tyre_temp + temp_noise_absolute
            
            # --- END NOISE CALCULATION ---
            
            agent_data = {
                "id": agent.unique_id,
                "team": agent.team,
                "rank": i + 1,
                "position": interpolated_position,
                "status": agent.status,
                "lap_data": {
                    "current_lap": agent.laps_completed + 1,
                    "last_lap_time": format_lap_time(last_lap_s),
                    "fastest_lap_time": format_lap_time(fastest_lap_s)
                },
                "vehicle_state": {
                    "battery_soc": round(noisy_soc, 2),
                    "fuel_remaining_mj": round(noisy_fuel, 2),
                    "aero_mode": agent.aero_mode,
                    "mom_available": agent.mom_available,
                    "tyre_life": round(noisy_tyre_life, 2),
                    "tyre_compound": agent.tyre_compound,
                    "tyre_temp": round(noisy_tyre_temp, 1),
                    "mom_active": agent.mom_active,
                    "on_cliff": agent.on_cliff,
                    "pit_stops_made": agent.pit_stops_made
                }
            }
            agent_list.append(agent_data)

        final_data = {
            "race_status": race_status,
            "agents": agent_list
        }
        return final_data