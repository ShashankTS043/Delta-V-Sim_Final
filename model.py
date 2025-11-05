import random
import json
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
        
        # We need a step counter for the timestamp
        self.step_count = 0 # This is our new, simple counter 
        # --- End of Manual Initialization ---
        
        
        self.num_agents = num_agents
        self.time_step = 0.1  # Simulate 10 times per second (100ms)
        
        # --- Build the Environment ---
        self.track = build_bahrain_track()
        
        # --- Create Agents in our OWN list ---
        # We are using a simple Python list, not an AgentSet
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
        # 1. Get the data dictionary
        data = self.get_simulation_data()
        
        # 2. Write it to the data.json file
        with open("data.json", "w") as f:
            json.dump(data, f, indent=2)
            
        # 3. Advance the step counter
        self.step_count += 1

    def get_simulation_data(self):
        """
        Builds a dictionary of the current simulation state
        to match the data.json.sample contract.
        """
        
        # 1. Build the global race_status
        # (We'll add timestamp/lap later, for now they are placeholders)
        race_status = {
            "timestamp": f"0:00:{self.time_step * self.step_count:.1f}",
            "current_lap": 1, 
            "total_laps": 57,
            "safety_car": "NONE"
        }
        
        # 2. Build the list of agents
        agent_list = []
        
        # We need to sort agents by rank. For now, we'll sort by
        # their progress on the track (node number, then progress on edge).
        sorted_agents = sorted(self.f1_agents, 
                               key=lambda x: (x.position[0], x.position[1]), 
                               reverse=True)
        
        for i, agent in enumerate(sorted_agents):
            
            # Get the (x, y) position from the track graph node
            node_pos = self.track.nodes[agent.position[0]]['pos']
            
            agent_data = {
                "id": agent.unique_id,
                "team": "Haas", # Placeholder
                "rank": i + 1,   # Rank based on our sort
                "position": [node_pos[0], node_pos[1]], # Use the (x,y) from the node
                "status": agent.status,
                "lap_data": {
                    "current_lap": 1, # Placeholder
                    "last_lap_time": "0:00.000", # Placeholder
                    "fastest_lap_time": "0:00.000" # Placeholder
                },
                "vehicle_state": {
                    "battery_soc": round(agent.battery_soc, 2), # Clean up the number
                    "aero_mode": agent.aero_mode,
                    "mom_available": agent.mom_available
                }
            }
            agent_list.append(agent_data)

        # 3. Combine into the final dictionary
        final_data = {
            "race_status": race_status,
            "agents": agent_list
        }
        
        return final_data