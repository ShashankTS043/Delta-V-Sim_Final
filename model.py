from mesa import Model
# from mesa.time import RandomActivation  <-- DELETE THIS LINE
from agent import F1Agent # Import the agent you just defined

class DeltaVModel(Model):
    """The main model running the Delta-V simulation."""
    
    def __init__(self, num_agents):
        super().__init__()
        self.num_agents = num_agents
        # self.schedule = RandomActivation(self)  <-- DELETE THIS LINE
        
        # Create agents
        for i in range(self.num_agents):
            # The agent is automatically added to the model
            # when its __init__ is called.
            a = F1Agent(i, self)
            # self.schedule.add(a)  <-- DELETE THIS LINE

    def step(self):
        """Execute one time step of the simulation."""
        
        # This is the NEW way to run all agent steps in a random order
        self.agents.shuffle_do("step")
        
        # This is where we will also process SimPy events
        # and collect data for the leaderboard