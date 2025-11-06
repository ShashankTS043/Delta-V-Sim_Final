import random
import json
import simpy
from mesa import Model
from agent import F1Agent
from track_graph import build_bahrain_track

class DeltaVModel(Model):
    """
    The main model running the Delta-V simulation.
    This class holds the SimPy environment, the track, and the list of agents.
    """
    
    def __init__(self, config_file_path):
        # --- Start of Manual Initialization ---
        self.seed = 12345
        self.random = random.Random(self.seed)
        self.running = True
        self.space = None 
        self.step_count = 0 
        # --- End of Manual Initialization ---
        
        # --- Load Configuration ---
        with open(config_file_path, 'r') as f:
            self.config = json.load(f)
            
        sim_params = self.config['simulation_params']
        driver_roster = self.config['driver_roster']
        
        # --- SimPy Environment Setup ---
        self.env = simpy.Environment() 
        self.vsc_active = False 
        
        self.num_agents = len(driver_roster)
        self.time_step = sim_params['time_step']
        
        # --- Build the Environment ---
        self.track = build_bahrain_track()
        self.track_length = sum(data['length'] for u, v, data in self.track.edges(data=True))
        
        # --- Create Agents from Roster ---
        self.f1_agents = []
        for driver_config in driver_roster:
            # Pass the agent its specific strategy config
            a = F1Agent(
                unique_id=driver_config['unique_id'], 
                model=self, 
                strategy_config=driver_config['strategy']
            )
            a.team = driver_config.get('team', 'Independent') # Optional: Add team name
            self.f1_agents.append(a)
            
        # --- Start SimPy Processes ---
        self.env.process(self.run_simulation_steps())
        self.env.process(self.race_master_events())

    def run_simulation_steps(self):
        """
        This is the new 'main loop' that calls agent.step() on every tick.
        It's a SimPy process that yields (pauses) for time_step seconds.
        """
        try:
            while True:
                # Shuffle agent activation order for fairness
                self.random.shuffle(self.f1_agents)
                
                # Manually call step() on each agent in our list
                for agent in self.f1_agents:
                    agent.step()
                    
                # --- DATA PIPELINE ---
                # Write the current state to data.json for the visualizer
                data = self.get_simulation_data()
                with open("data.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                self.step_count += 1
                
                # Tell SimPy to pause this function and resume in 0.1s
                yield self.env.timeout(self.time_step)
        except simpy.Interrupt:
            print("Simulation interrupted.")

    def race_master_events(self):
        """
        This is the 'Race Master' process that injects global events.
        It runs in parallel with run_simulation_steps.
        """
        
        # Wait for 30 seconds of race time
        yield self.env.timeout(30)
        
        # Deploy the VSC
        print(f"--- VSC DEPLOYED at t={self.env.now:.1f}s ---")
        self.vsc_active = True
        
        # Hold VSC for 20 seconds
        yield self.env.timeout(20)
        
        # End the VSC
        print(f"--- VSC ENDING at t={self.env.now:.1f}s ---")
        self.vsc_active = False

    def get_simulation_data(self):
        """
        Builds a dictionary of the current simulation state
        to match the data.json.sample contract.
        This is the "API" for our visualizer.
        """
        
        race_status = {
            "timestamp": f"0:00:{self.env.now:.1f}", # Use SimPy's master clock
            "current_lap": 1, 
            "total_laps": 57,
            "safety_car": "VSC" if self.vsc_active else "NONE" # Report VSC status
        }
        
        agent_list = []
        
        # Sort agents by total distance traveled to get a live ranking
        sorted_agents = sorted(self.f1_agents, 
                               key=lambda x: x.total_distance_traveled, 
                               reverse=True)
        
        for i, agent in enumerate(sorted_agents):
            
            # Get the (x, y) coordinate from the agent's current node
            node_pos = self.track.nodes[agent.position[0]]['pos']
            
            agent_data = {
                "id": agent.unique_id,
                "team": "Haas", 
                "rank": i + 1,   # Rank is now based on the sort
                "position": [node_pos[0], node_pos[1]], # Real (x,y) data
                "status": agent.status,
                "lap_data": {
                    "current_lap": agent.laps_completed + 1, # Real lap count
                    "last_lap_time": "0:00.000", 
                    "fastest_lap_time": "0:00.000"
                },
                "vehicle_state": {
                    "battery_soc": round(agent.battery_soc, 2),
                    "aero_mode": agent.aero_mode,
                    "mom_available": agent.mom_available
                }
            }
            agent_list.append(agent_data)

        final_data = {
            "race_status": race_status,
            "agents": agent_list
        }
        
        return final_data