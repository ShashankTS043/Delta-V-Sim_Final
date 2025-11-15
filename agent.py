from mesa import Agent
import statistics
import numpy as np 

# --- Define tyre types ---
DRY_TYRES = ["soft", "medium", "hard"]
WET_TYRES = ["intermediate"]

class F1Agent(Agent):
    """
    An agent representing a single 2026 F1 car.
    (Pro++: "Universal Brain" - Can run random or map-based logic)
    """

    def __init__(self, unique_id, model, strategy_config):
        self.unique_id = unique_id
        self.model = model
        self.strategy = strategy_config
        
        # --- Physics ---
        self.position = ("n_t15_apex", 0.0) 
        self.velocity = 0.0 
        self.status = "RACING"
        
        # --- Race State ---
        self.laps_completed = 0
        self.total_distance_traveled = 0.0
        self.total_race_time_s = 0.0
        self.lap_times = []
        
        # --- Power Unit ---
        self.battery_capacity_mj = self.strategy['battery_capacity_mj']
        self.battery_soc = 1.0 
        self.fuel_energy_remaining = self.strategy['fuel_tank_mj']
        self.energy_recovered_this_lap_mj = 0.0 
        
        # --- Aero & MOM ---
        self.aero_mode = "Z-MODE"
        self.mom_available = False
        self.mom_active = False 
        
        # --- Tyres ---
        self.tyre_compound = "medium" 
        self.tyre_life_remaining = 1.0 
        self.tyre_grip_modifier = 1.0 
        self.on_cliff = False 
        self.tyre_temp = 95.0
        
        # --- Pit Stops ---
        self.wants_to_pit = False
        self.time_in_pit_stall = 0.0
        
        # --- Stats ---
        self.pit_stops_made = 0
        self.time_on_softs_s = 0.0
        self.time_on_mediums_s = 0.0
        self.time_on_hards_s = 0.0
        self.mom_uses_count = 0
        
        # --- FINAL TELEMETRY ---
        self.telemetry_history = []
        self.plank_wear = 0.0
        self.acceleration_g = 0.0 # <-- RESTORED
        self.plank_wear_rate_factor = self.strategy.get('plank_wear_factor', 1.0)
        self.tyre_pressure_factor = self.strategy.get('tyre_pressure_factor', 1.0)
        self.acceleration_g_factor = self.strategy.get('g_factor', 1.0) # <-- RESTORED FACTOR
        # --- END FINAL TELEMETRY ---

    def step(self):
        self.perceive() 
        self.make_decision()
        self.update_physics() 

    def perceive(self):
        """Agent gathers information and makes high-level strategy decisions."""
        if self.status == "FINISHED": return

        # 1. Find car ahead
        agent_in_front = None
        min_gap = float('inf')
        for other in self.model.f1_agents:
            if other.unique_id == self.unique_id: continue
            gap = other.total_distance_traveled - self.total_distance_traveled
            if gap < -self.model.track_length / 2: gap += self.model.track_length
            if 0 < gap < min_gap:
                min_gap = gap
                agent_in_front = other

        # 2. Check MOM Detection
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors: return
        
        main_track_edge = None
        for succ in successors:
             if not self.model.track.get_edge_data(current_node, succ).get('is_pit_lane', False):
                main_track_edge = self.model.track.get_edge_data(current_node, succ)
                break
        
        if main_track_edge:
            is_detection_point = main_track_edge.get('mom_detection', False)
            if is_detection_point and agent_in_front and (min_gap < self.strategy.get("mom_detection_gap", 10.0)):
                if not self.mom_available: 
                    print(f"--- AGENT {self.unique_id} GOT MOM! (Gap: {min_gap:.1f}m) ---")
                    # Grant the 0.5 MJ of extra energy
                    self.battery_soc += (self.strategy.get('mom_extra_energy_mj', 0.5) / self.battery_capacity_mj)
                    if self.battery_soc > 1.0: self.battery_soc = 1.0
                self.mom_available = True
        
        # 3. Check Pit Decision
        next_node_for_decision = self.get_next_node_from_successors(force_track=True)
        if not next_node_for_decision: return
        
        edge_data = self.model.track.get_edge_data(current_node, next_node_for_decision)
        if edge_data:
            is_pit_decision_point = edge_data.get('is_pit_entry_decision', False)
            if is_pit_decision_point:
                
                # Check for "emergency" reasons to pit
                PIT_CLIFF_THRESHOLD = self.strategy.get('pit_tyre_cliff_threshold', 0.10)
                
                tyre_worn_out = (self.tyre_life_remaining <= PIT_CLIFF_THRESHOLD)
                
                is_on_dry_tyres = self.tyre_compound in DRY_TYRES
                is_wet = (self.model.weather_state == "WET")
                wrong_tyre_for_conditions = (is_wet and is_on_dry_tyres) or (not is_wet and not is_on_dry_tyres)
                
                # DECISION: Pit if tyres are worn OR if you're on the wrong compound.
                should_pit = tyre_worn_out or wrong_tyre_for_conditions
                can_pit = (self.laps_completed > 0) # Can pit anytime after lap 0

                if can_pit and should_pit and self.status == "RACING":
                    self.wants_to_pit = True
                    if wrong_tyre_for_conditions:
                        print(f"--- AGENT {self.unique_id} PITS FOR WRONG TYRES! (Weather: {self.model.weather_state}) ---")
                    else:
                        print(f"--- AGENT {self.unique_id} DECIDES TO PIT! (Tyre: {self.tyre_life_remaining*100:.0f}%) ---")
                else:
                    self.wants_to_pit = False

    def get_next_node_from_successors(self, force_track=False):
        current_node = self.position[0]
        successors = list(self.model.track.successors(current_node))
        if not successors: return None
        if force_track or (not self.wants_to_pit and current_node == "n_t15_apex"):
             for succ in successors:
                if not self.model.track.get_edge_data(current_node, succ).get('is_pit_lane', False):
                    return succ
        elif self.wants_to_pit and current_node == "n_t15_apex":
            for succ in successors:
                if self.model.track.get_edge_data(current_node, succ).get('is_pit_lane', False):
                    return succ 
        
        if successors:
            return successors[0]
        return None

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
                
        # --- REMOVED RANDOMNESS: Driver Error Check Removed ---
            
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
        
        standard_top_speed_ms = self.strategy['standard_top_speed_kph'] / 3.6
        taper_speed_ms = self.strategy.get('electric_motor_taper_kph', 290.0) / 3.6
        
        if edge_data.get('is_pit_lane', False):
            base_velocity = self.strategy['vsc_speed']
            self.aero_mode = "Z-MODE"
        
        elif track_radius is None:
            self.aero_mode = "X-MODE"
            base_velocity = standard_top_speed_ms
            
        else:
            self.aero_mode = "Z-MODE"
            
            # --- Weather Grip Modifier ---
            weather_grip_modifier = 1.0
            is_wet = (self.model.weather_state == "WET")
            is_on_dry_tyres = self.tyre_compound in DRY_TYRES
            
            if is_wet and is_on_dry_tyres:
                weather_grip_modifier = self.strategy.get('grip_modifier_wet_wrong_tyre', 0.5)
            elif not is_wet and not is_on_dry_tyres:
                weather_grip_modifier = self.strategy.get('grip_modifier_dry_wrong_tyre', 0.7)
            # --- End Weather Grip ---
                
            # Combine base grip, wear grip, and weather grip
            grip = self.strategy['grip_factor'] * self.tyre_grip_modifier * weather_grip_modifier
            
            if track_radius <= 0: base_velocity = 0
            else: base_velocity = (grip * track_radius) ** 0.5
            
            if base_velocity > standard_top_speed_ms:
                base_velocity = standard_top_speed_ms
        
        # --- 5. "UNIVERSAL BRAIN" MOM LOGIC ---
        self.mom_active = False
        x_mode_allowed = edge_data.get('x_mode_allowed', False)
        should_activate_mom = False # Flag to decide

        # --- "Pro++" LOGIC (Energy Map) ---
        if "energy_deployment_map" in self.strategy:
            energy_map = self.strategy.get("energy_deployment_map", {})
            command = energy_map.get(current_node, "STANDARD")

            if command == "DEPLOY" and self.mom_available and x_mode_allowed and (not edge_data.get('is_pit_lane', False)):
                should_activate_mom = True
        
        # --- "Pro+" LOGIC (Random Aggressiveness) ---
        elif "mom_aggressiveness" in self.strategy:
            # We keep this logic, but aggression is now *deterministic*
            if self.mom_available and x_mode_allowed and (not edge_data.get('is_pit_lane', False)) and (0.5 < self.strategy['mom_aggressiveness']):
                should_activate_mom = True

        # --- EXECUTE DECISION ---
        if should_activate_mom:
            self.velocity = self.strategy['mom_boost_speed_kph'] / 3.6 # 337 kph
            self.mom_active = True
            self.mom_uses_count += 1 
        else:
            self.velocity = base_velocity
            if self.velocity > taper_speed_ms:
                self.velocity = taper_speed_ms


    def update_physics(self):
        """Agent's state (position, velocity, soc) is updated."""
        
        # --- PIT STOP SERVICE LOGIC ---
        if self.status == "PITTING" and self.position[0] == "n_pit_stall" and self.velocity == 0:
            self.time_in_pit_stall += self.model.time_step
            if self.time_in_pit_stall >= self.strategy['pit_time_loss_seconds']:
                print(f"--- AGENT {self.unique_id} PIT STOP COMPLETE! ---")
                
                if self.model.weather_state == "WET":
                    self.tyre_compound = "intermediate"
                else:
                    self.tyre_compound = "medium"

                self.tyre_life_remaining = 1.0
                self.on_cliff = False
                self.tyre_grip_modifier = 1.0
                self.tyre_temp = 95.0
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
                self.mom_available = False # Reset MOM at the end of the lap
                self.energy_recovered_this_lap_mj = 0.0 # Reset per-lap counter
                print(f"--- AGENT {self.unique_id} COMPLETED LAP {self.laps_completed}! (Time: {current_lap_time:.2f}s) ---")
                
                if self.laps_completed >= self.model.race_laps and not self.model.race_over:
                    print(f"--- AGENT {self.unique_id} WINS THE RACE! (First to {self.laps_completed} laps) ---")
                    self.model.race_over = True 
                    self.status = "FINISHED"
            self.position = (next_node, leftover_progress_fraction)
        else:
            self.position = (current_node, progress_on_edge)

        # --- 4. ENERGY MODEL (Battery-First) ---
        
        C1_POWER = float(self.strategy['c_1_power'])
        if self.aero_mode == "X-MODE":
            C2_AERO_DRAG = float(self.strategy['c_2_x_mode_drag'])
        else: # Z-MODE
            C2_AERO_DRAG = float(self.strategy['c_2_z_mode_drag'])
        
        power_cost = C1_POWER * (self.velocity * self.velocity)
        drag_cost = C2_AERO_DRAG
        total_energy_cost_per_step = (power_cost + drag_cost) * self.model.time_step
        
        if self.mom_active:
            total_energy_cost_per_step += self.strategy.get('mom_energy_cost', 0.0) 
        
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

        # --- C. REGENERATION (FIXED) ---
        if self.aero_mode == "Z-MODE":
            
            # Use a flat, tunable regen-per-second
            regen_per_second = self.strategy.get('corner_regen_mj_per_second', 0.05)
            energy_gained = regen_per_second * self.model.time_step

            # (Removed the buggy lap limiter)
                
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
            else: # Default to medium or intermediate
                self.time_on_mediums_s += self.model.time_step 
                wear_rate = self.strategy['tyre_wear_rate_medium']
            
            tyre_wear = wear_rate * self.model.time_step
            if self.aero_mode == "Z-MODE": tyre_wear *= 1.5
            if self.mom_active: tyre_wear *= 2.0
            
            # --- Weather Tyre Wear ---
            is_wet = (self.model.weather_state == "WET")
            is_on_dry_tyres = self.tyre_compound in DRY_TYRES
            if is_wet and is_on_dry_tyres:
                tyre_wear *= 5.0 
            elif not is_wet and not is_on_dry_tyres:
                tyre_wear *= 5.0 
            # --- END NEW ---

            self.tyre_life_remaining -= tyre_wear
            
            # --- FIX: Use .get() for safety and define variables ---
            PIT_CLIFF_THRESHOLD = self.strategy.get('pit_tyre_cliff_threshold', 0.10)
            TYRE_CLIFF_MODIFIER = self.strategy.get('tyre_cliff_grip_modifier', 0.8)

            if not self.on_cliff and (self.tyre_life_remaining <= PIT_CLIFF_THRESHOLD):
                self.on_cliff = True
                self.tyre_grip_modifier = TYRE_CLIFF_MODIFIER
                print(f"--- AGENT {self.unique_id} TYRES FELL OFF A CLIFF! GRIP REDUCED. ---")

            if self.tyre_life_remaining <= 0:
                self.tyre_life_remaining = 0
                self.status = "CRASHED"
                self.velocity = 0

            # --- TYRE TEMPERATURE MODEL (TUNED) ---
            base_temp = 95.0
            temp_gain = 0.0
            temp_loss = 0.0
            
            if self.aero_mode == "Z-MODE":
                temp_gain = self.strategy.get('temp_gain_corners_per_sec', 1.5)
            else:
                temp_loss = self.strategy.get('temp_loss_straights_per_sec', 1.0)
            
            if self.mom_active:
                temp_gain += self.strategy.get('temp_gain_mom_per_sec', 2.0)
            
            self.tyre_temp += (temp_gain - temp_loss) * self.model.time_step
            
            self.tyre_temp = np.clip(self.tyre_temp, 95.0, 110.0)
            # --- END NEW ---
            
        # --- 6. Log Total Time ---
        if self.status != "FINISHED":
            self.total_race_time_s += self.model.time_step
            self.record_telemetry_step() # <-- Call the recording function
    
    # --- Telemetry Recording Function ---
    def record_telemetry_step(self):
        """Compiles and stores a full historical data point for CSV download."""
        
        current_time = self.model.env.now
        
        # --- Plank Wear (Simplified: Loss during X-Mode) ---
        if self.aero_mode == "X-MODE":
            # Use the car's unique factor
            self.plank_wear += self.strategy.get('plank_wear_rate', 0.005) * self.model.time_step * self.plank_wear_rate_factor 
        
        # --- Tyre Pressure (Simplified: Linear with Temperature) ---
        # Apply the car's unique factor to the final calculated pressure
        tyre_pressure_base = 28.0 + (self.tyre_temp - 95.0) * 0.2
        tyre_pressure = tyre_pressure_base * self.tyre_pressure_factor
        
        # --- Final Data Record ---
        data_point = {
            'sim_time': round(current_time, 2),
            'lap': self.laps_completed + 1,
            'driver': self.unique_id,
            'status': self.status,
            'tyre_life_pct': round(self.tyre_life_remaining * 100, 1),
            'tyre_temp_c': round(self.tyre_temp, 1),
            'tyre_pressure_psi': round(tyre_pressure, 1), # <-- UPDATED (NOISE ADDED IN MODEL)
            'soc_percent': round(self.battery_soc * 100, 1),
            'fuel_mj': round(self.fuel_energy_remaining, 2),
            'plank_wear_mm': round(self.plank_wear, 3),
            'front_wing_angle_deg': 12.0 if self.aero_mode == "Z-MODE" else 5.0,
            # Removed lateral_g
        }
        self.telemetry_history.append(data_point)
    # --- END Telemetry Recording Function ---