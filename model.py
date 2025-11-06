import random
import json
import simpy  # <-- NEW IMPORT
from mesa import Model
from agent import F1Agent
from track_graph import build_bahrain_track

class DeltaVModel(Model):
    """The main model running the Delta-V simulation."""
    
    def __init__(self, num_agents):
        # --- Start of Manual Initialization ---
        self.seed = 12345
        self.random = random.Random(self.seed)
        self.running = True
        self.space = None 
        # self.step_count = 0  <-- We no longer need this
        # --- End of Manual Initialization ---
        
        # --- NEW SimPy Environment ---
        self.env = simpy.Environment()
        self.vsc_active = False # Global VSC flag
        
        self.num_agents = num_agents
        self.time_step = 0.1  # Simulate 10 times per second (100ms)
        
        # --- Build the Environment ---
        self.track = build_bahrain_track()
        self.track_length = sum(data['length'] for u, v, data in self.track.edges(data=True))
        
        # --- Create Agents ---
        self.f1_agents = []
        for i in range(self.num_agents):
            a = F1Agent(i, self)
            self.f1_agents.append(a)
            
        # --- NEW: Start SimPy Processes ---
        # These start automatically when the model is created
        self.env.process(self.run_simulation_steps())
        self.env.process(self.race_master_events())

    def run_simulation_steps(self):
        """This is the new 'main loop' that calls model.step()"""
        try:
            while True:
                # Shuffle the list of agents
                self.random.shuffle(self.f1_agents)
                
                # Manually call step() on each agent in our list
                for agent in self.f1_agents:
                    agent.step()
                    
                # --- DATA PIPELINE ---
                data = self.get_simulation_data()
                with open("data.json", "w") as f:
                    json.dump(data, f, indent=2)
                
                # Wait for the next tick
                yield self.env.timeout(self.time_step)
        except simpy.Interrupt:
            print("Simulation interrupted.")

    def race_master_events(self):
        """This is the 'Race Master' that injects global events."""
        
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
        """
        
        race_status = {
            # --- NEW: Use SimPy's clock ---
            "timestamp": f"0:00:{self.env.now:.1f}",
            "current_lap": 1, 
            "total_laps": 57,
            "safety_car": "VSC" if self.vsc_active else "NONE" # <-- NEW
        }
        
        agent_list = []
        
        sorted_agents = sorted(self.f1_agents, 
                               key=lambda x: x.total_distance_traveled, 
                               reverse=True)
        
        for i, agent in enumerate(sorted_agents):
            
            node_pos = self.track.nodes[agent.position[0]]['pos']
            
            agent_data = {
                "id": agent.unique_id,
                "team": "Haas", 
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