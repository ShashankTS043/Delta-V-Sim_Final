from mesa import Agent

class F1Agent(Agent):
    """An agent representing a single F1 car."""
    
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        
        # --- Core Physics State ---
        self.position = (0, 0) # (x, y) coordinates or (node_id, progress_on_edge)
        self.velocity = 0.0     # in m/s
        self.status = "RACING"  # e.g., RACING, PITTING, FINISHED
        
        # --- 2026 Power Unit (Engine) State ---
        # 50/50 Power Unit & Energy Management
        self.battery_soc = 1.0  # State of Charge (1.0 = 100%)
        self.fuel_energy_remaining = 100.0 # in MJ (Megajoules)
        
        # --- 2026 Active Aero State ---
        # 'Z-Mode' (high-downforce) or 'X-Mode' (low-drag)
        self.aero_mode = "Z-MODE" 
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False # Becomes True if < 1s behind at detection
        self.mom_energy_boost = 0.0 # e.g., gets 0.5 MJ when activated
        
        # --- Agent Strategy (The "Brain") ---
        # This will be configured for each agent (e.g., Ocon vs. Bearman)
        self.strategy = {
            "x_mode_aggressiveness": 0.8, # 0.0 to 1.0
            "mom_deployment": "EARLY_BOOST", # vs. "LATE_DEFEND"
            "battery_target_soc": 0.2
        }

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        self.perceive()
        self.make_decision()
        self.update_physics()
        print(f"Agent {self.unique_id} is at {self.position} with {self.battery_soc*100}% battery.")

    def perceive(self):
        """Agent gathers information from the environment."""
        # This is where we'll check gap to car in front, track mode, etc.
        pass

    def make_decision(self):
        """Agent's "brain" decides what to do based on its strategy."""
        # e.g., "IF in X-Mode-Zone AND strategy.aggressiveness > 0.5 -> SET self.aero_mode = 'X-MODE'"
        # e.g., "IF self.mom_available AND strategy.deployment == 'EARLY_BOOST' -> USE MOM"
        pass

    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        # e.g., self.position += self.velocity * model.time_step
        # e.g., self.battery_soc -= energy_cost_of_this_step
        pass