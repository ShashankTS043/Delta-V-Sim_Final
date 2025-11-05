from mesa import Agent

class F1Agent(Agent):
    """An agent representing a single 2026 F1 car."""
    
    def __init__(self, unique_id, model):
        # --- Start of Fix ---
        # DO NOT call super() or Agent.__init__(). This is the source of the bug.
        # We will manually set the 2 required properties.
        self.unique_id = unique_id
        self.model = model
        # --- End of Fix ---
        
        # --- Core Physics State ---
        self.position = (0, 0.0) # Start at Node 0, 0% complete
        self.velocity = 0.0     # in m/s
        self.status = "RACING"
        
        # --- 2026 Power Unit (Engine) State ---
        self.battery_soc = 1.0
        self.fuel_energy_remaining = 100.0
        
        # --- 2026 Active Aero State ---
        self.aero_mode = "Z-MODE"
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False
        
        # --- Agent Strategy (The "Brain") ---
        self.strategy = {
            "top_speed": 85.0, # m/s (approx 306 kph)
            "corner_speed": 40.0, # m/s (approx 144 kph)
        }

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        self.make_decision()  # 1. Decide on velocity
        self.update_physics() # 2. Move the agent
        self.perceive()       # 3. See the new state

    def perceive(self):
        """Agent gathers information from the environment."""
        current_node = self.position[0]
        if current_node == 0 and self.position[1] < 0.01 and self.velocity > 0:
            print(f"--- AGENT {self.unique_id} COMPLETED A LAP! ---")
        
    def make_decision(self):
        """Agent's "brain" decides what to do."""
        current_node = self.position[0]
        
        successors = list(self.model.track.successors(current_node))
        if not successors:
            self.velocity = 0
            return
            
        next_node = successors[0]
        
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        track_type = edge_data['type']

        if track_type == "STRAIGHT":
            self.velocity = self.strategy['top_speed']
        else: # track_type == "CORNER"
            self.velocity = self.strategy['corner_speed']
        
    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        current_node = self.position[0]
        progress_on_edge = self.position[1] 

        successors = list(self.model.track.successors(current_node))
        if not successors:
            self.status = "FINISHED"
            self.velocity = 0
            return 

        next_node = successors[0]
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        edge_length = edge_data['length'] 

        distance_to_move = self.velocity * self.model.time_step
        
        if edge_length == 0:
            progress_to_add = 1.0
        else:
            progress_to_add = distance_to_move / edge_length
        
        progress_on_edge += progress_to_add
        
        if progress_on_edge >= 1.0:
            leftover_progress_fraction = progress_on_edge - 1.0
            self.position = (next_node, leftover_progress_fraction)
        else:
            self.position = (current_node, progress_on_edge)

        if self.velocity > 0:
            cost = (self.velocity / 10000.0) 
            self.battery_soc -= cost