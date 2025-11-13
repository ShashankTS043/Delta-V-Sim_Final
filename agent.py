from mesa import Agent
import statistics

class F1Agent(Agent):
    """
    An agent representing a single 2026 F1 car.
    (Elite+ Day 6: Includes Pit AI, Stats Logging, and Driver Error)
    """

    def __init__(self, unique_id, model, strategy_config):
        # --- Manually set the 2 required properties ---
        self.unique_id = unique_id
        self.model = model
        
        # --- Core Physics State ---
        self.position = ("n_t15_apex", 0.0) 
        self.velocity = 0.0 
        self.status = "RACING" # RACING, PITTING, OUT_OF_ENERGY, CRASHED, FINISHED
        
        # --- Race State ---
        self.laps_completed = 0
        self.total_distance_traveled = 0.0
        
        # --- 2026 50/50 Power Unit State ---
        self.battery_capacity_mj = strategy_config['battery_capacity_mj']
        self.battery_soc = 1.0 
        self.fuel_energy_remaining = strategy_config['fuel_tank_mj']
        self.energy_recovered_this_lap_mj = 0.0 
        
        # --- 2026 Active Aero State ---
        self.aero_mode = "Z-MODE"
        
        # --- 2026 Manual Override Mode (MOM) State ---
        self.mom_available = False
        self.mom_active = False 
        
        # --- Tyre State ---
        self.tyre_compound = "medium" 
        self.tyre_life_remaining = 1.0 
        self.tyre_grip_modifier = 1.0 
        self.on_cliff = False 
        
        # --- Pit Stop State ---
        self.wants_to_pit = False
        self.time_in_pit_stall = 0.0
        
        # --- Stats Logging ---
        self.pit_stops_made = 0
        self.time_on_softs_s = 0.0
        self.time_on_mediums_s = 0.0
        self.time_on_hards_s = 0.0
        self.mom_uses_count = 0
        
        # --- Race Time Logging ---
        self.total_race_time_s = 0.0
        self.lap_times = []
        
        # --- Agent Strategy (The "Brain") ---
        self.strategy = strategy_config

    def step(self):
        """The agent's main logic loop, called by the model each tick."""
        self.perceive() 
        self.make_decision()
        self.update_physics() 

    def perceive(self):
        """Agent gathers information and makes high-level strategy decisions (like pitting)."""
        
        # Stop perceiving if race is over
        if self.status == "FINISHED": return

        # --- 1. Find the car directly in front (for MOM) ---
        agent_in_front = None
        min_gap = float('inf')

        for other in self.model.f1_agents:
            if other.unique_id == self.unique_id: continue
            
            gap = other.total_distance_traveled - self.total_distance_traveled
            
            if gap < -self.model.track_length / 2: gap += self.model.track_length
            
            if 0 < gap < min_gap:
                min_gap = gap
                agent_in_front = other

        # --- 2. Check for MOM activation & Pit Decision---
        current_node = self.position[0]
        
        # Find the *next* node on the default track path
        next_node = self.get_next_node_from_successors(force_track=True)
        
        if not next_node: return
        
        # Get the data for the edge we are CURRENTLY on
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        
        if not edge_data: return

        # --- Check for MOM ---
        is_detection_point = edge_data.get('mom_detection', False)
        if is_detection_point and agent_in_front and (min_gap < self.strategy["mom_detection_gap"]):
            if not self.mom_available: 
                print(f"--- AGENT {self.unique_id} GOT MOM! (Gap: {min_gap:.1f}m) ---")
            self.mom_available = True
        
        # --- Check for Pit Decision ---
        is_pit_decision_point = edge_data.get('is_pit_entry_decision', False)
        
        if is_pit_decision_point:
            # Check strategy: Are we allowed to pit? (e.g. Lap 1 + 1 >= Lap 2)
            can_pit = (self.laps_completed + 1 >= self.strategy['pit_window_open_lap'])
            
            # Check tyre state: Do we NEED to pit?
            should_pit = (self.tyre_life_remaining < self.strategy['pit_tyre_cliff_threshold'])
            
            if can_pit and should_pit and self.status == "RACING":
                self.wants_to_pit = True
                print(f"--- AGENT {self.unique_id} DECIDES TO PIT! (Tyre: {self.tyre_life_remaining*100:.0f}%) ---")
            else:
                self.wants_to_pit = False

    def get_next_node_from_successors(self, force_track=False):
        """Helper function to find the next node, handling pit/track splits."""
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        
        if not successors:
            return None

        # If we are forced to stay on track (or not pitting), find the non-pit edge
        if force_track or (not self.wants_to_pit and current_node == "n_t15_apex"):
             for succ in successors:
                if not self.model.track.get_edge_data(current_node, succ).get('is_pit_lane', False):
                    return succ
        
        # If we want to pit and are at the decision node
        elif self.wants_to_pit and current_node == "n_t15_apex":
            for succ in successors:
                if self.model.track.get_edge_data(current_node, succ).get('is_pit_lane', False):
                    return succ # Return "n_pit_entry"
        
        # Otherwise (already in pit lane or on a normal part of the track), just return the only path
        # This will also handle the case where force_track=True and we're not on the decision node
        if force_track and successors:
            for succ in successors:
                if not self.model.track.get_edge_data(current_node, succ).get('is_pit_lane', False):
                    return succ
            
        return successors[0] if successors else None


    def make_decision(self):
        """Agent's "brain" decides velocity, aero, and path (track vs. pits)."""

        # --- 1. CHECK GUARD CLAUSES ---
        if self.status in ["OUT_OF_ENERGY", "CRASHED", "FINISHED"]:
            self.velocity = 0
            self.aero_mode = "Z-MODE"
            self.mom_active = False
            return
        
        if self.model.vsc_active:
            self.velocity = self.strategy['vsc_speed']
            self.aero_mode = "Z-MODE"
            self.mom_active = False
            return
                
        # --- Day 6 Stochastic Realism (Driver Error) ---
        error_chance = self.model.random.random()
        if error_chance < self.strategy.get("driver_error_rate", 0.00001):
            if self.status == "RACING": 
                print(f"--- AGENT {self.unique_id} HAS CRASHED! (Driver Error) ---")
                self.status = "CRASHED"
                self.velocity = 0
                self.mom_active = False
                return
            
        # --- 2. Get current track/pit segment data ---
        current_node = self.position[0]
        next_node = self.get_next_node_from_successors()
        
        if current_node == "n_pit_stall":
            self.velocity = 0 
            self.mom_active = False
            self.aero_mode = "Z-MODE"
            return 
        
        if next_node is None:
            self.velocity = 0
            self.mom_active = False
            self.status = "FINISHED"
            return
        
        if self.wants_to_pit and current_node == "n_t15_apex":
            self.status = "PITTING"

        # --- 3. GET EDGE DATA FOR OUR CHOSEN PATH ---
        edge_data = self.model.track.get_edge_data(current_node, next_node)
        
        # --- 4. DYNAMIC PHYSICS & AERO LOGIC ---
        track_radius = edge_data.get('radius') 
        
        if edge_data.get('is_pit_lane', False):
            base_velocity = self.strategy['vsc_speed']
            self.aero_mode = "Z-MODE"
        
        elif track_radius is None:
            self.aero_mode = "X-MODE"
            base_velocity = self.strategy['top_speed']
            
        else:
            self.aero_mode = "Z-MODE"
            grip = self.strategy['grip_factor'] * self.tyre_grip_modifier
            
            if track_radius <= 0: base_velocity = 0
            else: base_velocity = (grip * track_radius) ** 0.5
            
            if base_velocity > self.strategy['top_speed']:
                base_velocity = self.strategy['top_speed']
        
        # --- 5. MANUAL OVERRIDE (MOM) LOGIC ---
        self.mom_active = False
        use_mom_chance = self.model.random.random() 
        x_mode_allowed = edge_data.get('x_mode_allowed', False)
        
        if self.mom_available and x_mode_allowed and (not edge_data.get('is_pit_lane', False)) and (use_mom_chance < self.strategy['mom_aggressiveness']):
            self.velocity = base_velocity + self.strategy['mom_boost']
            self.mom_active = True
            self.mom_uses_count += 1 
        else:
            self.velocity = base_velocity


    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        
        # --- PIT STOP SERVICE LOGIC ---
        if self.status == "PITTING" and self.position[0] == "n_pit_stall" and self.velocity == 0:
            self.time_in_pit_stall += self.model.time_step
            if self.time_in_pit_stall >= self.strategy['pit_time_loss_seconds']:
                print(f"--- AGENT {self.unique_id} PIT STOP COMPLETE! ---")
                self.tyre_compound = "medium" if self.tyre_compound == "soft" else "hard"
                self.tyre_life_remaining = 1.0
                self.on_cliff = False
                self.tyre_grip_modifier = 1.0
                self.pit_stops_made += 1 
                self.time_in_pit_stall = 0.0
                self.wants_to_pit = False
                self.status = "RACING" 
                self.position = ("n_pit_exit", 0.0)
            self.total_race_time_s += self.model.time_step
            return
        
        
        if self.velocity == 0:
            if self.status in ["RACING", "CRASHED", "OUT_OF_ENERGY"]:
                self.total_race_time_s += self.model.time_step
            return

        # --- 1. Get position details & calculate movement ---
        current_node = self.position[0]
        progress_on_edge = self.position[1] 
        next_node = self.get_next_node_from_successors()
        if next_node is None:
            self.status = "FINISHED"
            self.velocity = 0
            return
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
                current_lap_time = self.total_race_time_s - sum(self.lap_times)
                self.lap_times.append(current_lap_time) 
                self.laps_completed += 1
                self.mom_available = False
                self.energy_recovered_this_lap_mj = 0.0
                print(f"--- AGENT {self.unique_id} COMPLETED LAP {self.laps_completed}! (Time: {current_lap_time:.2f}s) ---")
                
                if self.laps_completed >= self.model.race_laps and not self.model.race_over:
                    print(f"--- AGENT {self.unique_id} WINS THE RACE! (First to {self.laps_completed} laps) ---")
                    self.model.race_over = True 
                    self.status = "FINISHED"
                    
            self.position = (next_node, leftover_progress_fraction)
        else:
            self.position = (current_node, progress_on_edge)

        # --- 4. 50/50 POWER UNIT & ENERGY MODEL ---
        
        C1_POWER = float(self.strategy['c_1_power'])
        if self.aero_mode == "X-MODE":
            C2_AERO_DRAG = float(self.strategy['c_2_x_mode_drag'])
        else: # Z-MODE
            C2_AERO_DRAG = float(self.strategy['c_2_z_mode_drag'])
        
        power_cost = C1_POWER * (self.velocity * self.velocity)
        drag_cost = C2_AERO_DRAG
        total_energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step
        
        if self.mom_active:
            total_energy_cost_per_step += self.strategy['mom_energy_cost']
        
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

        if self.aero_mode == "Z-MODE":
            regen_factor = self.strategy.get('c_regen_factor', 1e-07)
            energy_gained = regen_factor * (self.velocity * self.velocity) * self.model.time_step
            max_regen_limit = self.strategy['max_regen_per_lap_mj']
            if self.energy_recovered_this_lap_mj + energy_gained > max_regen_limit:
                energy_gained = max_regen_limit - self.energy_recovered_this_lap_mj
            if self.battery_soc < 1.0 and energy_gained > 0:
                soc_gain = energy_gained / self.battery_capacity_mj
                self.battery_soc = min(1.0, self.battery_soc + soc_gain)
                self.energy_recovered_this_lap_mj += energy_gained

        # --- 5. TYRE WEAR MODEL ---
        if self.status == "RACING":
            if self.tyre_compound == "soft":
                self.time_on_softs_s += self.model.time_step 
                wear_rate = self.strategy['tyre_wear_rate_soft']
            elif self.tyre_compound == "hard":
                self.time_on_hards_s += self.model.time_step 
                wear_rate = self.strategy['tyre_wear_rate_hard']
            else: # Default to medium
                self.time_on_mediums_s += self.model.time_step 
                wear_rate = self.strategy['tyre_wear_rate_medium']
            
            tyre_wear = wear_rate * self.model.time_step
            if self.aero_mode == "Z-MODE": tyre_wear *= 1.5
            if self.mom_active: tyre_wear *= 2.0
            self.tyre_life_remaining -= tyre_wear
            
            if not self.on_cliff and (self.tyre_life_remaining <= self.strategy['tyre_grip_cliff_percent']):
                self.on_cliff = True
                self.tyre_grip_modifier = self.strategy['tyre_cliff_grip_modifier']
                print(f"--- AGENT {self.unique_id} TYRES FELL OFF A CLIFF! GRIP REDUCED. ---")

            if self.tyre_life_remaining <= 0:
                self.tyre_life_remaining = 0
                self.status = "CRASHED"
                self.velocity = 0
            
        # --- 6. Log Total Time ---
        if self.status != "FINISHED":
            self.total_race_time_s += self.model.time_step