from mesa import Agent

class F1Agent(Agent):
    """An agent representing a single 2026 F1 car."""
    
    def __init__(self, unique_id, model):
        # --- Manually set the 2 required properties ---
        self.unique_id = unique_id
        self.model = model
        
        # --- Core Physics State ---
        self.position = (0, 0.0) # (current_node, progress_on_edge_as_fraction)
        self.velocity = 0.0     # in m/s
        self.status = "RACING"
        
        # --- NEW Race State ---
        self.laps_completed = 0
        self.total_distance_traveled = 0.0
        
        # --- 2026 Power Unit (Engine) State ---
        self.battery_soc = 1.0
        self.fuel_energy_remaining = 100.0
        
        # --- 2026 Active Aero State ---
        self.aero_mode = "Z-MODE"
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False # Can it be used this lap?
        self.mom_active = False    # Is it being used *this step*?
        
        # --- Agent Strategy (The "Brain") ---
        self.strategy = {
            "top_speed": 85.0, # m/s (approx 306 kph)
            "corner_speed": 40.0, # m/s (approx 144 kph)
            
            "c_1_power": 0.000001,    # Tuned to be much lower
            "c_2_z_mode_drag": 0.0001, # Also tuned lower
            "c_2_x_mode_drag": 0.00003, # Also tuned lower
            
            # --- NEW MOM Strategy ---
            "mom_aggressiveness": 0.75, # 0.0 (never use) to 1.0 (always use)
            "mom_boost": 5.0,           # 5 m/s extra speed
            "mom_energy_cost": 0.0005,  # Extra cost per step
            "mom_detection_gap": 80.0   # 80 meters (roughly 1s at 80m/s)
        }

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        # --- NEW STEP ORDER ---
        self.perceive()       # 1. See the environment
        self.make_decision()  # 2. Decide on velocity and aero
        self.update_physics() # 3. Move the agent and consume energy

    def perceive(self):
        """Agent gathers information from the environment (MOM detection)."""
        
        # --- 1. Find the car directly in front ---
        agent_in_front = None
        min_gap = float('inf')

        for other in self.model.f1_agents:
            if other.unique_id == self.unique_id:
                continue
            
            gap = other.total_distance_traveled - self.total_distance_traveled
            
            # Handle lap crossover (other is 1 lap ahead)
            if gap < -self.model.track_length / 2:
                gap += self.model.track_length
            
            # If they are in front of us (positive gap) and it's the smallest gap so far
            if 0 < gap < min_gap:
                min_gap = gap
                agent_in_front = other

        # --- 2. Check for MOM activation ---
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors: return
        
        edge_data = self.model.track.get_edge_data(current_node, successors[0])
        is_detection_point = edge_data.get('mom_detection', False)

        # If we are on a detection straight, we have a car in front, and the gap is close
        if is_detection_point and agent_in_front and (min_gap < self.strategy["mom_detection_gap"]):
            if not self.mom_available: # Only print on the first time
                print(f"--- AGENT {self.unique_id} GOT MOM! (Gap: {min_gap:.1f}m) ---")
            self.mom_available = True
        
    def make_decision(self):
        """Agent's "brain" decides velocity and aero mode."""

        # --- 1. ENERGY CHECK (Guard Clause) ---
        if self.status == "OUT_OF_ENERGY":
            self.velocity = 0
            self.aero_mode = "Z-MODE"
            return
        
        # --- 2. Get current track segment data ---
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors:
            self.velocity = 0
            return
            
        next_node = successors[0]
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        track_type = edge_data['type']
        x_mode_allowed = edge_data['x_mode_allowed']

        # --- 3. ACTIVE AERO (X-MODE) LOGIC ---
        if x_mode_allowed:
            self.aero_mode = "X-MODE"
            base_velocity = self.strategy['top_speed']
        else: # We are in a corner
            self.aero_mode = "Z-MODE"
            base_velocity = self.strategy['corner_speed']

        # --- 4. MANUAL OVERRIDE (MOM) LOGIC ---
        self.mom_active = False # Reset
        
        # Use MOM if it's available, we're on a straight, and we are "aggressive"
        # We use model.random for a reproducible random choice
        use_mom_chance = self.model.random.random() 
        
        if self.mom_available and track_type == "STRAIGHT" and (use_mom_chance < self.strategy['mom_aggressiveness']):
            self.velocity = base_velocity + self.strategy['mom_boost']
            self.mom_active = True
        else:
            self.velocity = base_velocity
        
    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        
        # --- ZOMBIE CAR CHECK ---
        if self.velocity == 0:
            return

        # --- 1. Get current position details ---
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

        # --- 2. Calculate distance and update totals ---
        distance_to_move = self.velocity * self.model.time_step
        self.total_distance_traveled += distance_to_move
        
        if edge_length == 0:
            progress_to_add = 1.0
        else:
            progress_to_add = distance_to_move / edge_length
        
        # --- 3. Update position ---
        progress_on_edge += progress_to_add
        
        if progress_on_edge >= 1.0:
            leftover_progress_fraction = progress_on_edge - 1.0
            self.position = (next_node, leftover_progress_fraction)
            
            # --- 4. LAP COMPLETION LOGIC ---
            # If we just moved to Node 0, we completed a lap
            if next_node == 0:
                self.laps_completed += 1
                self.mom_available = False # Reset MOM for the new lap
                print(f"--- AGENT {self.unique_id} COMPLETED LAP {self.laps_completed}! ---")
        else:
            self.position = (current_node, progress_on_edge)

        # --- 5. ADVANCED 2026 ENERGY COST MODEL ---
        C1_POWER = self.strategy['c_1_power']
        
        if self.aero_mode == "X-MODE":
            C2_AERO_DRAG = self.strategy['c_2_x_mode_drag']
        else: # Z-MODE
            C2_AERO_DRAG = self.strategy['c_2_z_mode_drag']

        power_cost = C1_POWER * (self.velocity * self.velocity)
        drag_cost = C2_AERO_DRAG
        
        energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step
        
        # --- 6. ADD MOM COST ---
        if self.mom_active:
            energy_cost_per_step += self.strategy['mom_energy_cost']
        
        # --- 7. Apply the cost and check if we ran out ---
        if self.battery_soc > energy_cost_per_step:
            self.battery_soc -= energy_cost_per_step
        else:
            self.battery_soc = 0
            self.velocity = 0
            self.status = "OUT_OF_ENERGY"