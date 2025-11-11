import random
import json
import simpy
from mesa import Model
from agent import F1Agent
from track_graph import build_bahrain_track

class DeltaVModel(Model):
    """
    The main model running the Delta-V simulation.
    (Day 4 "Pro-Tuned": 50/50 Power, Capped Regen, 57-Lap Physics)
    """

    def __init__(self, config_file_path, seed=None):
        # --- Start of Manual Initialization ---
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        self.random = random.Random(self.seed)
        self.running = True
        self.space = None
        
        # --- SimPy Environment Setup ---
        self.env = simpy.Environment()
        self.vsc_active = False
        # --- End of Manual Initialization ---

        # --- Load Master Starting Grid Config ---
        with open(config_file_path, 'r') as f:
            self.config = json.load(f)
        
        sim_params = self.config['simulation_params']
        starting_grid = self.config['grid']
        
        self.num_agents = len(starting_grid)
        self.time_step = sim_params['time_step']
        self.race_laps = sim_params['race_laps']
        
        # --- Build the Environment ---
        self.track = build_bahrain_track()
        self.track_length = sum(data['length'] for u, v, data in self.track.edges(data=True))
        
        # --- Create Agents from Starting Grid ---
        self.f1_agents = []
        strategy_cache = {}

        for driver_data in starting_grid:
            strategy_file = driver_data['strategy_file']
            
            if strategy_file not in strategy_cache:
                with open(strategy_file, 'r') as f:
                    strategy_cache[strategy_file] = json.load(f)["strategy"]
            
            strategy_config = strategy_cache[strategy_file]

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
        self.env.process(self.race_master_events())

    def run_simulation_steps(self):
        """
        The main 'main loop' that calls agent.step() on every tick.
        """
        try:
            while True:
                self.random.shuffle(self.f1_agents)

                for agent in self.f1_agents:
                    agent.step()
                
                data = self.get_simulation_data()
                with open("data.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                yield self.env.timeout(self.time_step)
        except simpy.Interrupt:
            print("Simulation interrupted.")

    def race_master_events(self):
        """
        The 'Race Master' process that injects global events.
        (FIXED with infinite loop and realistic timing)
        """
        while True:
            # Wait for 300-600 seconds (5-10 mins)
            wait_time = self.random.uniform(300, 600)
            yield self.env.timeout(wait_time)
            
            # Deploy the VSC
            print(f"--- VSC DEPLOYED at t={self.env.now:.1f}s ---")
            self.vsc_active = True
            
            # Hold VSC for 15-30 seconds
            vsc_duration = self.random.uniform(15, 30)
            yield self.env.timeout(vsc_duration)
            
            # End the VSC
            print(f"--- VSC ENDING at t={self.env.now:.1f}s ---")
            self.vsc_active = False

    def get_simulation_data(self):
        """
        Builds a dictionary of the current simulation state
        to match the data.json.sample contract.
        """
        
        race_status = {
            "timestamp": f"0:00:{self.env.now:.1f}",
            "current_lap": 1, 
            "total_laps": self.race_laps,
            "safety_car": "VSC" if self.vsc_active else "NONE"
        }

        agent_list = []
        sorted_agents = sorted(self.f1_agents,
                                key=lambda x: x.total_distance_traveled,
                                reverse=True)
        
        for i, agent in enumerate(sorted_agents):
            node_pos = self.track.nodes[agent.position[0]]['pos']
            
            agent_data = {
                "id": agent.unique_id,
                "team": agent.team,
                "rank": i + 1,
                "position": [node_pos[0], node_pos[1]],
                "status": agent.status,
                "lap_data": {
                    "current_lap": agent.laps_completed + 1,
                    "last_lap_time": "0:00.000", 
                    "fastest_lap_time": "0:00.000"
                },
                "vehicle_state": {
                    "battery_soc": round(agent.battery_soc, 2),
                    "fuel_remaining_mj": round(agent.fuel_energy_remaining, 2),
                    "aero_mode": agent.aero_mode,
                    "mom_available": agent.mom_available,
                    "tyre_life": round(agent.tyre_life_remaining, 2),
                    
                    # --- NEW ADDITIONS ---
                    "tyre_compound": agent.tyre_compound,
                    "mom_active": agent.mom_active,
                    "on_cliff": agent.on_cliff
                }
            }
            agent_list.append(agent_data)

        final_data = {
            "race_status": race_status,
            "agents": agent_list
        }
        return final_data