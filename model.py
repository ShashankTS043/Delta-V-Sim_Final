import random
from mesa import Model
# from mesa.agent import AgentSet  <-- WE NO LONGER NEED THIS
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