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
        self.position = ("n_t15_apex", 0.0) 
        self.velocity = 0.0     
        self.status = "RACING"
        
        # --- Race State ---
        self.laps_completed = 0
        self.total_distance_traveled = 0.0 
        
        # --- 2026 Power Unit (Engine) State ---
        self.battery_soc = 1.0
        
        # --- 2026 Active Aero State ---
        self.aero_mode = "Z-MODE"
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False 
        self.mom_active = False    
        
        # --- NEW: Tyre State ---
        self.tyre_compound = "medium" # Default, will be set by config
        self.tyre_life_remaining = 1.0  # 1.0 = 100%
        self.tyre_grip_modifier = 1.0   # 1.0 = 100% grip
        self.on_cliff = False           # Has tyre grip "fallen off a cliff"?
        
        # --- Agent Strategy (The "Brain") ---
        self.strategy = strategy_config

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        self.perceive()       
        self.make_decision()  
        self.update_physics() 

    def perceive(self):
        """Agent gathers information from the environment (MOM detection)."""
        
        agent_in_front = None
        min_gap = float('inf')

        for other in self.model.f1_agents:
            if other.unique_id == self.unique_id:
                continue
            
            gap = other.total_distance_traveled - self.total_distance_traveled
            
            if gap < -self.model.track_length / 2:
                gap += self.model.track_length
            
            if 0 < gap < min_gap:
                min_gap = gap
                agent_in_front = other

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
        if self.status == "OUT_OF_ENERGY" or self.status == "CRASHED": # NEW
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
        track_radius = edge_data.get('radius') 
        
        if track_radius is None:
            # This is a STRAIGHT
            self.aero_mode = "X-MODE" 
            base_velocity = self.strategy['top_speed']
        
        else:
            # This is a CORNER
            self.aero_mode = "Z-MODE"
            
            # --- DYNAMIC CORNERING ---
            # NEW: Grip is now affected by tyre wear
            grip = self.strategy['grip_factor'] * self.tyre_grip_modifier
            
            if track_radius <= 0:
                base_velocity = 0
            else:
                base_velocity = (grip * track_radius) ** 0.5 
            
            if base_velocity > self.strategy['top_speed']:
                base_velocity = self.strategy['top_speed']
                
        # --- 4. MANUAL OVERRIDE (MOM) LOGIC ---
        self.mom_active = False 
        use_mom_chance = self.model.random.random() 
        x_mode_allowed = edge_data.get('x_mode_allowed', False)
        
        if self.mom_available and x_mode_allowed and (use_mom_chance < self.strategy['mom_aggressiveness']):
            self.velocity = base_velocity + self.strategy['mom_boost']
            self.mom_active = True
        else:
            self.velocity = base_velocity
        
    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        
        if self.velocity == 0:
            return

        # --- 1. Get position details & calculate movement ---
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
        self.total_distance_traveled += distance_to_move
        
        progress_to_add = (distance_to_move / edge_length) if edge_length > 0 else 1.0
        
        # --- 2. Update position & Check for Laps ---
        progress_on_edge += progress_to_add
        
        if progress_on_edge >= 1.0:
            leftover_progress_fraction = progress_on_edge - 1.0
            
            is_finish = edge_data.get('is_finish_line', False)
            if is_finish:
                self.laps_completed += 1
                self.mom_available = False 
                print(f"--- AGENT {self.unique_id} COMPLETED LAP {self.laps_completed}! ---")

            self.position = (next_node, leftover_progress_fraction)
        else:
            self.position = (current_node, progress_on_edge)

        # --- 3. ADVANCED 2026 ENERGY/REGEN MODEL ---
        C1_POWER = self.strategy['c_1_power']
        REGEN_EFFICIENCY = self.strategy['c_regen_efficiency']

        if self.aero_mode == "X-MODE":
            # --- A. ENERGY DRAIN (On a straight) ---
            C2_AERO_DRAG = self.strategy['c_2_x_mode_drag']
            power_cost = C1_POWER * (self.velocity * self.velocity)
            drag_cost = C2_AERO_DRAG
            energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step

            if self.mom_active:
                energy_cost_per_step += self.strategy['mom_energy_cost']

            if self.battery_soc > energy_cost_per_step:
                self.battery_soc -= energy_cost_per_step
            else:
                self.battery_soc = 0
                self.velocity = 0
                self.status = "OUT_OF_ENERGY"
        else: 
            # --- B. ENERGY REGENERATION (In a corner) ---
            energy_gained = (self.velocity / 50.0) * REGEN_EFFICIENCY * self.model.time_step
            
            if self.battery_soc < 1.0: 
                self.battery_soc += energy_gained
                if self.battery_soc > 1.0: self.battery_soc = 1.0
            
            # --- C. Z-MODE (CORNER) ENERGY DRAIN ---
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

        # --- 4. NEW: TYRE WEAR MODEL ---
        
        # Find the correct wear rate for our compound
        if self.tyre_compound == "soft":
            wear_rate = self.strategy['tyre_wear_rate_soft']
        elif self.tyre_compound == "hard":
            wear_rate = self.strategy['tyre_wear_rate_hard']
        else: # Default to medium
            wear_rate = self.strategy['tyre_wear_rate_medium']
            
        # Base wear
        tyre_wear = wear_rate * self.model.time_step
        
        # Extra wear for cornering (Z-Mode) and MOM
        if self.aero_mode == "Z-MODE":
            tyre_wear *= 1.5 # 50% extra wear in corners
        if self.mom_active:
            tyre_wear *= 2.0 # 100% extra wear when using MOM boost
            
        # Apply the wear
        if self.tyre_life_remaining > 0:
            self.tyre_life_remaining -= tyre_wear
        
        # Check for "grip cliff"
        if not self.on_cliff and (self.tyre_life_remaining <= self.strategy['tyre_grip_cliff_percent']):
            self.on_cliff = True
            self.tyre_grip_modifier = self.strategy['tyre_cliff_grip_modifier']
            print(f"--- AGENT {self.unique_id} TYRES FELL OFF A CLIFF! GRIP REDUCED. ---")

        # If tyres are completely gone, you're done
        if self.tyre_life_remaining <= 0:
            self.tyre_life_remaining = 0
            self.status = "CRASHED" # Simplified, could be "PUNCTURE"
            self.velocity = 0