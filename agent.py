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
            
            # --- NEW 2026 ENERGY/AERO VALUES ---
            "c_1_power": 0.000001,      # Base power cost constant (tuned)
            "c_2_z_mode_drag": 0.0001,  # HIGH drag for Z-Mode (corners)
            "c_2_x_mode_drag": 0.00003  # LOW drag for X-Mode (straights)
        }

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        self.make_decision()  # 1. Decide on velocity and aero mode
        self.update_physics() # 2. Move the agent and consume energy
        self.perceive()       # 3. See the new state

    def perceive(self):
        """Agent gathers information from the environment."""
        current_node = self.position[0]
        if current_node == 0 and self.position[1] < 0.01 and self.velocity > 0:
            print(f"--- AGENT {self.unique_id} COMPLETED A LAP! ---")
        
    def make_decision(self):
        """Agent's "brain" decides velocity and aero mode."""

        # --- ENERGY CHECK (Guard Clause) ---
        # If we are out of energy, stop all decision-making.
        if self.status == "OUT_OF_ENERGY":
            self.velocity = 0
            self.aero_mode = "Z-MODE" # Default to high-grip
            return
        # --- END OF CHECK ---
        
        # 1. Get current track segment data
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors:
            self.velocity = 0
            return
            
        next_node = successors[0]
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        track_type = edge_data['type']
        x_mode_allowed = edge_data['x_mode_allowed']

        # --- 2. ACTIVE AERO (X-MODE) LOGIC ---
        # If X-Mode is allowed (on a straight)...
        if x_mode_allowed:
            self.aero_mode = "X-MODE"
            self.velocity = self.strategy['top_speed']
        else: # We are in a corner
            self.aero_mode = "Z-MODE"
            self.velocity = self.strategy['corner_speed']
        
    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        
        # --- ZOMBIE CAR CHECK ---
        # If we start the step with 0 velocity, don't move.
        if self.velocity == 0:
            return

        # 1. Get current position details
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

        # 2. Calculate distance to move
        distance_to_move = self.velocity * self.model.time_step
        
        if edge_length == 0:
            progress_to_add = 1.0
        else:
            progress_to_add = distance_to_move / edge_length
        
        # 3. Update position
        progress_on_edge += progress_to_add
        
        if progress_on_edge >= 1.0:
            leftover_progress_fraction = progress_on_edge - 1.0
            self.position = (next_node, leftover_progress_fraction)
        else:
            self.position = (current_node, progress_on_edge)

        # 4. ADVANCED 2026 ENERGY COST MODEL
        
        # Get constants from our strategy
        C1_POWER = self.strategy['c_1_power']
        
        # Get the correct drag constant based on our current Aero Mode
        if self.aero_mode == "X-MODE":
            C2_AERO_DRAG = self.strategy['c_2_x_mode_drag']
        else: # Z-MODE
            C2_AERO_DRAG = self.strategy['c_2_z_mode_drag']

        # Calculate Energy Cost using the formula: E = C1*v^2 + C2*Drag
        power_cost = C1_POWER * (self.velocity * self.velocity)
        drag_cost = C2_AERO_DRAG
        
        energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step
        
        # 5. Apply the cost and check if we ran out
        if self.battery_soc > energy_cost_per_step:
            self.battery_soc -= energy_cost_per_step
        else:
            # Out of energy!
            self.battery_soc = 0
            self.velocity = 0 # Stop the car
            self.status = "OUT_OF_ENERGY"