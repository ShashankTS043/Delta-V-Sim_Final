from mesa import Agent

class F1Agent(Agent):
    """
    An agent representing a single 2026 F1 car.
    It contains all logic for physics, decision-making (AI), and perception.
    """
    
    def __init__(self, unique_id, model, strategy_config):
        # --- Manually set the 2 required properties ---
        self.unique_id = unique_id
        self.model = model
        
        # --- Core Physics State ---
        self.position = (0, 0.0) # (current_node, progress_on_edge_as_fraction)
        self.velocity = 0.0     # in m/s
        self.status = "RACING"
        
        # --- Race State ---
        self.laps_completed = 0
        self.total_distance_traveled = 0.0 # Used for ranking
        
        # --- 2026 Power Unit (Engine) State ---
        self.battery_soc = 1.0
        
        # --- 2026 Active Aero State ---
        self.aero_mode = "Z-MODE"
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False # Can it be used this lap?
        self.mom_active = False    # Is it being used *this step*?
        
        # --- Agent Strategy (The "Brain") ---
        # The strategy is now passed in from the config file
        self.strategy = strategy_config

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        self.perceive()       # 1. See the environment and check for MOM
        self.make_decision()  # 2. Decide on velocity, aero, and MOM use
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
            
            # Handle lap crossover (e.g., other is 1 lap ahead)
            if gap < -self.model.track_length / 2:
                gap += self.model.track_length
            
            if 0 < gap < min_gap:
                min_gap = gap
                agent_in_front = other

        # --- 2. Check for MOM activation ---
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors: return
        
        edge_data = self.model.track.get_edge_data(current_node, successors[0])
        is_detection_point = edge_data.get('mom_detection', False)

        if is_detection_point and agent_in_front and (min_gap < self.strategy["mom_detection_gap"]):
            if not self.mom_available: 
                print(f"--- AGENT {self.unique_id} GOT MOM! (Gap: {min_gap:.1f}m) ---")
            self.mom_available = True
        
    def make_decision(self):
        """Agent's "brain" decides velocity and aero mode."""

        # --- 1. CHECK GUARD CLAUSES ---
        if self.status == "OUT_OF_ENERGY":
            self.velocity = 0
            self.aero_mode = "Z-MODE"
            self.mom_active = False
            return
            
        if self.model.vsc_active:
            self.velocity = self.strategy['vsc_speed']
            self.aero_mode = "Z-MODE" 
            self.mom_active = False 
            return
        
        # --- 2. Get current track segment data ---
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors:
            self.velocity = 0
            self.mom_active = False
            return
            
        next_node = successors[0]
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        
        # --- 3. DYNAMIC PHYSICS & AERO LOGIC ---
        
        track_radius = edge_data.get('radius') # Get the corner radius
        
        if track_radius is None:
            # This is a STRAIGHT
            self.aero_mode = "X-MODE" 
            base_velocity = self.strategy['top_speed']
        
        else:
            # This is a CORNER
            self.aero_mode = "Z-MODE"
            
            # --- NEW DYNAMIC CORNERING ---
            # Physics: v = sqrt(Grip / Radius)
            # Our formula: v = sqrt(grip_factor / radius)
            # This ensures (low radius = low speed), (high radius = high speed)
            grip = self.strategy['grip_factor']
            
            # Prevent division by zero if radius is 0
            if track_radius <= 0:
                base_velocity = 0
            else:
                base_velocity = (grip * track_radius) ** 0.5 # ** 0.5 is sqrt()
            
            # Cap the corner speed by the car's absolute top speed
            if base_velocity > self.strategy['top_speed']:
                base_velocity = self.strategy['top_speed']
                
        # --- 4. MANUAL OVERRIDE (MOM) LOGIC ---
        self.mom_active = False 
        
        use_mom_chance = self.model.random.random() 
        x_mode_allowed = edge_data.get('x_mode_allowed', False)
        
        # MOM is only allowed on designated X-Mode straights
        if self.mom_available and x_mode_allowed and (use_mom_chance < self.strategy['mom_aggressiveness']):
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
            if next_node == 0:
                self.laps_completed += 1
                self.mom_available = False 
                print(f"--- AGENT {self.unique_id} COMPLETED LAP {self.laps_completed}! ---")
        else:
            self.position = (current_node, progress_on_edge)

        # --- 5. ADVANCED 2026 ENERGY COST MODEL ---
        # --- 5. ADVANCED 2026 ENERGY/REGEN MODEL ---
        
        # Get constants from our strategy
        C1_POWER = self.strategy['c_1_power']
        REGEN_EFFICIENCY = self.strategy['c_regen_efficiency']

        # --- A. ENERGY DRAIN (On a straight, in X-Mode) ---
        if self.aero_mode == "X-MODE":
            C2_AERO_DRAG = self.strategy['c_2_x_mode_drag']
            
            # E = C1*v^2 + C2*Drag
            power_cost = C1_POWER * (self.velocity * self.velocity)
            drag_cost = C2_AERO_DRAG
            energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step

            # Add MOM cost if active
            if self.mom_active:
                energy_cost_per_step += self.strategy['mom_energy_cost']

            # Apply the cost
            if self.battery_soc > energy_cost_per_step:
                self.battery_soc -= energy_cost_per_step
            else:
                self.battery_soc = 0
                self.velocity = 0
                self.status = "OUT_OF_ENERGY"
        
        # --- B. ENERGY REGENERATION (In a corner, in Z-Mode) ---
        else: # We are in "Z-MODE" (braking for a corner)
            # Regen is proportional to braking (approximated by corner speed)
            energy_gained = (self.velocity / 50.0) * REGEN_EFFICIENCY * self.model.time_step
            
            if self.battery_soc < 1.0: # Can't charge over 100%
                self.battery_soc += energy_gained
                if self.battery_soc > 1.0:
                    self.battery_soc = 1.0
            
            # --- C. Z-MODE (CORNER) ENERGY DRAIN ---
            # It still costs energy to move through a corner, just less
            # We'll use the Z-Mode drag constant
            C2_AERO_DRAG = self.strategy['c_2_z_mode_drag']
            power_cost = C1_POWER * (self.velocity * self.velocity)
            drag_cost = C2_AERO_DRAG
            
            energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step
            
            if self.battery_soc > energy_cost_per_step:
                self.battery_soc -= energy_cost_per_step
            else:
                self.battery_soc = 0
                self.velocity = 0
                self.status = "OUT_OF_ENERGY"