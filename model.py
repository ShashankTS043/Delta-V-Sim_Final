import random
import json
from mesa import Model
# We removed the broken BaseScheduler import
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
        self.step_count = 0 # Our simple step counter
        # --- End of Manual Initialization ---
        
        self.num_agents = num_agents
        self.time_step = 0.1  # Simulate 10 times per second (100ms)
        
        # --- Build the Environment ---
        self.track = build_bahrain_track()
        
        # --- NEW: Calculate total track length ---
        self.track_length = sum(data['length'] for u, v, data in self.track.edges(data=True))
        
        # --- Create Agents in our OWN list ---
        self.f1_agents = []
        for i in range(self.num_agents):
            a = F1Agent(i, self)
            self.f1_agents.append(a)

    def step(self):
        """Execute one time step of the simulation."""
        
        # Shuffle the list of agents
        self.random.shuffle(self.f1_agents)
        
        # Manually call step() on each agent in our list
        for agent in self.f1_agents:
            agent.step()
            
        # --- NEW DATA PIPELINE ---
        data = self.get_simulation_data()
        with open("data.json", "w") as f:
            json.dump(data, f, indent=2)
            
        self.step_count += 1

    def get_simulation_data(self):
        """
        Builds a dictionary of the current simulation state
        to match the data.json.sample contract.
        """
        
        race_status = {
            "timestamp": f"0:00:{self.time_step * self.step_count:.1f}",
            "current_lap": 1, # (This is still a placeholder, agent lap is now real)
            "total_laps": 57,
            "safety_car": "NONE"
        }
        
        agent_list = []
        
        # --- NEW: Sort by total distance traveled ---
        # This is now our "true" ranking
        sorted_agents = sorted(self.f1_agents, 
                               key=lambda x: x.total_distance_traveled, 
                               reverse=True)
        
        for i, agent in enumerate(sorted_agents):
            
            node_pos = self.track.nodes[agent.position[0]]['pos']
            
            agent_data = {
                "id": agent.unique_id,
                "team": "Haas", 
                "rank": i + 1,   # Rank is now real
                "position": [node_pos[0], node_pos[1]],
                "status": agent.status,
                "lap_data": {
                    "current_lap": agent.laps_completed + 1, # This is now real
                    "last_lap_time": "0:00.000", 
                    "fastest_lap_time": "0:00.000"
                },
                "vehicle_state": {
                    "battery_soc": round(agent.battery_soc, 2),
                    "aero_mode": agent.aero_mode,
                    "mom_available": agent.mom_available # This is now real
                }
            }
            agent_list.append(agent_data)

        final_data = {
            "race_status": race_status,
            "agents": agent_list
        }
        
        return final_data