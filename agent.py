from mesa import Agent

class F1Agent(Agent):
    """
    An agent representing a single 2026 F1 car.
    (Day 4 "Pro-Tuned": 50/50 Power, Capped Regen, 57-Lap Physics)
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
        
        # --- NEW: 2026 50/50 Power Unit State ---
        self.battery_capacity_mj = strategy_config['battery_capacity_mj']
        self.battery_soc = 1.0 
        self.fuel_energy_remaining = strategy_config['fuel_tank_mj']
        self.energy_recovered_this_lap_mj = 0.0 
        
        # --- 2026 Active Aero State ---
        self.aero_mode = "Z-MODE"
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False
        self.mom_active = False 
        
        # --- Tyre State (Day 2 Feature) ---
        self.tyre_compound = "medium" 
        self.tyre_life_remaining = 1.0 
        self.tyre_grip_modifier = 1.0 
        self.on_cliff = False 
        
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
            if other.unique_id == self.unique_id: continue
            
            gap = other.total_distance_traveled - self.total_distance_traveled
            
            if gap < -self.model.track_length / 2: gap += self.model.track_length
            
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
        
        # --- NO PIT LOGIC IN THIS VERSION ---

    def make_decision(self):
        """Agent's "brain" decides velocity and aero mode."""

        if self.status == "OUT_OF_ENERGY" or self.status == "CRASHED":
            self.velocity = 0
            self.aero_mode = "Z-MODE"
            self.mom_active = False
            return
        
        if self.model.vsc_active:
            self.velocity = self.strategy['vsc_speed']
            self.aero_mode = "Z-MODE"
            self.mom_active = False
            return
        
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors:
            self.velocity = 0
            self.mom_active = False
            self.status = "FINISHED"
            return
        
        next_node = successors[0]
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        
        track_radius = edge_data.get('radius') 
        
        if track_radius is None:
            self.aero_mode = "X-MODE"
            base_velocity = self.strategy['top_speed']
            
        else:
            self.aero_mode = "Z-MODE"
            grip = self.strategy['grip_factor'] * self.tyre_grip_modifier
            
            if track_radius <= 0: base_velocity = 0
            else: base_velocity = (grip * track_radius) ** 0.5
            
            if base_velocity > self.strategy['top_speed']:
                base_velocity = self.strategy['top_speed']
        
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

        # --- 2. Calculate distance and update totals ---
        distance_to_move = self.velocity * self.model.time_step
        self.total_distance_traveled += distance_to_move
        
        progress_to_add = (distance_to_move / edge_length) if edge_length > 0 else 1.0
        
        # --- 3. Update position & Check for Laps ---
        progress_on_edge += progress_to_add
        
        if progress_on_edge >= 1.0:
            leftover_progress_fraction = progress_on_edge - 1.0
            
            is_finish = edge_data.get('is_finish_line', False)
            if is_finish:
                self.laps_completed += 1
                self.mom_available = False
                self.energy_recovered_this_lap_mj = 0.0 # <-- RESET REGEN COUNTER
                print(f"--- AGENT {self.unique_id} COMPLETED LAP {self.laps_completed}! ---")

            self.position = (next_node, leftover_progress_fraction)
        else:
            self.position = (current_node, progress_on_edge)

        # --- 4. 50/50 POWER UNIT & ENERGY MODEL ---
        
        # --- A. Calculate Total Energy Cost for this step ---
        C1_POWER = self.strategy['c_1_power']
        if self.aero_mode == "X-MODE":
            C2_AERO_DRAG = self.strategy['c_2_x_mode_drag']
        else: # Z-MODE
            C2_AERO_DRAG = self.strategy['c_2_z_mode_drag']
        
        power_cost = C1_POWER * (self.velocity * self.velocity)
        drag_cost = C2_AERO_DRAG
        total_energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step
        
        if self.mom_active:
            total_energy_cost_per_step += self.strategy['mom_energy_cost']
        
        # --- B. Pay the cost with 50/50 Power ---
        battery_power_limit_mj = self.strategy['battery_power_limit_mj_per_step']
        battery_drain = min(total_energy_cost_per_step, battery_power_limit_mj)
        
        soc_drain = battery_drain / self.battery_capacity_mj 
        
        if self.battery_soc > soc_drain:
             self.battery_soc -= soc_drain
             energy_cost_remaining = total_energy_cost_per_step - battery_drain
        else:
             energy_paid_by_battery = self.battery_soc * self.battery_capacity_mj
             self.battery_soc = 0
             energy_cost_remaining = total_energy_cost_per_step - energy_paid_by_battery
             
        ice_power_limit_mj = self.strategy['ice_power_limit_mj_per_step']
        fuel_drain = min(energy_cost_remaining, ice_power_limit_mj)
        
        if self.fuel_energy_remaining > fuel_drain:
            self.fuel_energy_remaining -= fuel_drain
        else:
            self.fuel_energy_remaining = 0
            self.status = "OUT_OF_ENERGY"
            self.velocity = 0

        # --- C. REGENERATION (In a corner) ---
        if self.aero_mode == "Z-MODE":
            # 1. Calculate potential energy gain (v^2 model)
            regen_factor = self.strategy['c_regen_factor']
            energy_gained = regen_factor * (self.velocity * self.velocity) * self.model.time_step
            
            # 2. Check against the 8.5 MJ per-lap cap
            max_regen_limit = self.strategy['max_regen_per_lap_mj']
            if self.energy_recovered_this_lap_mj + energy_gained > max_regen_limit:
                energy_gained = max_regen_limit - self.energy_recovered_this_lap_mj
            
            # 3. Add the (capped) energy to our trackers
            if self.battery_soc < 1.0 and energy_gained > 0:
                soc_gain = energy_gained / self.battery_capacity_mj
                
                if self.battery_soc + soc_gain > 1.0:
                    self.battery_soc = 1.0
                else:
                    self.battery_soc += soc_gain
                
                self.energy_recovered_this_lap_mj += energy_gained

        # --- 5. TYRE WEAR MODEL (Re-enabled) ---
        if self.status == "RACING":
            if self.tyre_compound == "soft":
                wear_rate = self.strategy['tyre_wear_rate_soft']
            elif self.tyre_compound == "hard":
                wear_rate = self.strategy['tyre_wear_rate_hard']
            else: # Default to medium
                wear_rate = self.strategy['tyre_wear_rate_medium']
            
            tyre_wear = wear_rate * self.model.time_step
            
            if self.aero_mode == "Z-MODE":
                tyre_wear *= 1.5
            if self.mom_active:
                tyre_wear *= 2.0
            
            if self.tyre_life_remaining > 0:
                self.tyre_life_remaining -= tyre_wear
            
            if not self.on_cliff and (self.tyre_life_remaining <= self.strategy['tyre_grip_cliff_percent']):
                self.on_cliff = True
                self.tyre_grip_modifier = self.strategy['tyre_cliff_grip_modifier']
                print(f"--- AGENT {self.unique_id} TYRES FELL OFF A CLIFF! GRIP REDUCED. ---")

            if self.tyre_life_remaining <= 0:
                self.tyre_life_remaining = 0
                self.status = "CRASHED"
                self.velocity = 0