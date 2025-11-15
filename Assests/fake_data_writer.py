import networkx as nx
import json
import time
import numpy as np
import sys
import os
import tempfile
import glob
from datetime import datetime
import random

# -------------------------
# Helper: time parsing / formatting
# -------------------------
def parse_time_to_seconds(t):
    if t is None: return None
    try: return float(str(t))
    except (ValueError, TypeError): pass
    parts = str(t).split(':')
    try:
        if len(parts) == 2: return int(parts[0]) * 60.0 + float(parts[1])
        elif len(parts) == 3: return int(parts[0]) * 3600.0 + int(parts[1]) * 60.0 + float(parts[2])
    except Exception: return None
    return None

def format_seconds_to_str(s):
    if s is None: return "0:00.000"
    try: s = float(s)
    except (ValueError, TypeError): return "0:00.000"
    minutes = int(s // 60)
    seconds = s - minutes*60
    return f"{minutes}:{seconds:06.3f}"

# -------------------------
# 1. HIGH-FIDELITY TRACK DEFINITION
# -------------------------
def build_bahrain_track():
    G = nx.DiGraph() 
    # (Node Definitions)
    G.add_node("n_t15_apex", pos=(800, 700))
    G.add_node("n_t1_brake", pos=(800, 150))
    G.add_node("n_t1_apex", pos=(770, 100))
    G.add_node("n_t2_apex", pos=(700, 150))
    G.add_node("n_t3_exit", pos=(700, 200))
    G.add_node("n_t4_brake", pos=(650, 350))
    G.add_node("n_t4_apex", pos=(610, 380))
    G.add_node("n_t5_entry", pos=(400, 380))
    G.add_node("n_t7_apex", pos=(350, 420))
    G.add_node("n_t8_brake", pos=(300, 380))
    G.add_node("n_t8_apex", pos=(270, 350))
    G.add_node("n_t9_entry", pos=(200, 420))
    G.add_node("n_t10_apex", pos=(150, 400))
    G.add_node("n_t11_brake", pos=(150, 650))
    G.add_node("n_t11_apex", pos=(180, 700))
    G.add_node("n_t12_apex", pos=(250, 750))
    G.add_node("n_t13_brake", pos=(500, 750))
    G.add_node("n_t13_apex", pos=(550, 780))
    G.add_node("n_t14_brake", pos=(750, 780))
    G.add_node("n_pit_entry", pos=(790, 650))
    G.add_node("n_pit_stall", pos=(790, 400))
    G.add_node("n_pit_exit", pos=(790, 120))
    # (Edge Definitions)
    G.add_edge("n_t15_apex", "n_t1_brake", length=1100, radius=None, x_mode_allowed=True, mom_detection=True, is_finish_line=True)
    G.add_edge("n_t1_brake", "n_t1_apex", length=110, radius=60, x_mode_allowed=False)
    G.add_edge("n_t1_apex", "n_t2_apex", length=100, radius=70, x_mode_allowed=False)
    G.add_edge("n_t2_apex", "n_t3_exit", length=100, radius=70, x_mode_allowed=False)
    G.add_edge("n_t3_exit", "n_t4_brake", length=250, radius=None, x_mode_allowed=False)
    G.add_edge("n_t4_brake", "n_t4_apex", length=120, radius=75, x_mode_allowed=False)
    G.add_edge("n_t4_apex", "n_t5_entry", length=300, radius=None, x_mode_allowed=True)
    G.add_edge("n_t5_entry", "n_t7_apex", length=450, radius=150, x_mode_allowed=False)
    G.add_edge("n_t7_apex", "n_t8_brake", length=150, radius=None, x_mode_allowed=False)
    G.add_edge("n_t8_brake", "n_t8_apex", length=100, radius=55, x_mode_allowed=False)
    G.add_edge("n_t8_apex", "n_t9_entry", length=200, radius=None, x_mode_allowed=False)
    G.add_edge("n_t9_entry", "n_t10_apex", length=200, radius=50, x_mode_allowed=False)
    G.add_edge("n_t10_apex", "n_t11_brake", length=700, radius=None, x_mode_allowed=True, mom_detection=True)
    G.add_edge("n_t11_brake", "n_t11_apex", length=150, radius=80, x_mode_allowed=False)
    G.add_edge("n_t11_apex", "n_t12_apex", length=200, radius=160, x_mode_allowed=False)
    G.add_edge("n_t12_apex", "n_t13_brake", length=600, radius=None, x_mode_allowed=True, mom_detection=True)
    G.add_edge("n_t13_brake", "n_t13_apex", length=120, radius=65, x_mode_allowed=False)
    G.add_edge("n_t13_apex", "n_t14_brake", length=300, radius=None, x_mode_allowed=False)
    G.add_edge("n_t14_brake", "n_t15_apex", length=150, radius=70, x_mode_allowed=False, is_pit_entry_decision=True)
    G.add_edge("n_t15_apex", "n_pit_entry", length=50, radius=100, is_pit_lane=True, x_mode_allowed=False)
    G.add_edge("n_pit_entry", "n_pit_stall", length=400, radius=None, is_pit_lane=True, x_mode_allowed=False)
    G.add_edge("n_pit_stall", "n_pit_exit", length=1, radius=None, is_pit_lane=True, x_mode_allowed=False)
    G.add_edge("n_pit_exit", "n_t1_apex", length=450, radius=None, is_pit_lane=True, x_mode_allowed=False)
    return G

# -------------------------
# 2. IO Utilities (Snapshot Writer)
# -------------------------
def write_simulation_data(data, folder=".", prefix="data_snapshot_", keep_last=12):
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception:
        pass
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    fname = f"{prefix}{ts}.json"
    temp_path = os.path.join(folder, f"{fname}.tmp")
    final_path = os.path.join(folder, fname)
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.rename(temp_path, final_path)
    except Exception as e:
        print(f"Error writing snapshot file {final_path}: {e}")
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except Exception: pass
        return None
    # prune older snapshots
    try:
        pattern = os.path.join(folder, f"{prefix}*.json")
        files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
        for old in files[keep_last:]:
            try: os.remove(old)
            except Exception: pass
    except Exception:
        pass
    return final_path

def read_command(file_path="commands.json"):
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f: command_data = json.load(f)
        try: os.remove(file_path)
        except Exception: pass
        return command_data
    except Exception as e:
        print(f"Error reading command: {e}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except Exception: pass
        return None

# -------------------------
# 3. Initial Data (22 cars)
# -------------------------
def get_initial_data(pos):
    start_pos = list(pos["n_t15_apex"])
    haas_drivers = ["Ocon      ", "Bearman   "]
    other_drivers = ["Verstappen", "Perez     ", "Hamilton  ", "Russell   ", "Leclerc   ", "Sainz     ", "Norris    ", "Piastri   ", "Alonso    ", "Stroll    ", "Gasly     ", "Tsunoda   ", "Ricciardo ", "Albon     ", "Sargeant  ", "Bottas    ", "Zhou      ", "Magnussen ", "Hulkenberg", "Lawson    ", "Drugovich "]
    all_driver_ids = haas_drivers + other_drivers
    agents_list = []
    for i, driver_id in enumerate(all_driver_ids):
        current_start_pos = [start_pos[0] + (i % 2) * 20, start_pos[1] + (i // 2) * 20]
        vehicle_state = {
            "battery_soc": float(np.random.uniform(0.85, 0.95)), "aero_mode": "Z-MODE", "mom_available": False,
            "fuel_remaining_mj": 3000.0, "tyre_compound": "medium", "tyre_life": 1.0,
            "on_cliff": False, "mom_active": False, "pit_stops_made": 0
        }
        status = "RACING"
        if driver_id == "Verstappen": status = "CRASHED"
        elif driver_id == "Hamilton": status = "PITTING"
        elif driver_id == "Norris": vehicle_state["on_cliff"] = True
        elif driver_id == "Piastri": vehicle_state["mom_active"] = True

        agents_list.append({
            "id": driver_id, "team": "Haas" if driver_id in haas_drivers else "AI_Team", "rank": i + 1,
            "position": current_start_pos, "status": status,
            "lap_data": {"current_lap": 1, "last_lap_time": "0:00.000", "fastest_lap_time": "0:00.000"},
            "vehicle_state": vehicle_state
        })
    return {"race_status": {"timestamp": "0:00:00.0", "current_lap": 1, "total_laps": 57, "safety_car": "NONE"}, "agents": agents_list}

# -------------------------
# 4. Sorting key
# -------------------------
def get_sort_key(agent):
    status = agent.get('status', '').upper()
    if status in ("CRASHED", "OUT_OF_ENERGY"): return -1e9
    pit_penalty = -500.0 if status == "PITTING" else 0.0
    lap = agent.get('lap_data', {}).get('current_lap', 0)
    last_time = parse_time_to_seconds(agent.get('lap_data', {}).get('last_lap_time', None)) or 9999.0
    return (lap * 100000.0) - last_time + pit_penalty

# -------------------------
# 5. Path & Server Loop (VARIABLE "HARD STOP" PIT)
# -------------------------
BASE_DRAIN_RATE = 0.008
BASE_REGEN_RATE = 0.005
SPEED_FAST = 0.020
SPEED_MEDIUM = 0.012
SPEED_SLOW = 0.008
SPEED_PIT = 0.005
MOM_DETECTION_DISTANCE = 75
UPDATES_PER_SEC = 100 # Based on time.sleep(0.01)
MIN_PIT_STOP_SEC = 1.8
MAX_PIT_STOP_SEC = 2.5

def run_fake_server(G):
    pos = nx.get_node_attributes(G, 'pos')
    data = get_initial_data(pos)

    agent_states = {}
    lap_times = {}
    now = time.time()
    
    for agent in data['agents']:
        agent_id = agent['id']
        agent_states[agent_id] = {
            "current_node": "n_t15_apex", "next_node": "n_t1_brake", "progress": 0.0,
            "speed_factor": float(np.random.uniform(0.95, 1.05)),
            "will_pit": (agent['status'] == "PITTING")
        }
        lap_times[agent_id] = now

    start_time = now
    vsc_timer = 0

    print("--- FAKE DATA SERVER (VARIABLE HARD STOP v5) STARTED ---")

    while True:
        current_time = time.time()
        elapsed_time = current_time - start_time
        data['race_status']['timestamp'] = format_seconds_to_str(elapsed_time)

        # VSC scheduler
        if vsc_timer > 0:
            vsc_timer -= 1
            if vsc_timer == 0:
                print("EVENT: VSC ENDING")
                data['race_status']['safety_car'] = "NONE"
        elif random.randint(0, 7000) == 1:
            print("EVENT: VIRTUAL SAFETY CAR (VSC) DEPLOYED")
            data['race_status']['safety_car'] = "VSC"
            vsc_timer = int(UPDATES_PER_SEC * 3)

        # read any external commands
        command = read_command()
        if command:
            print(f"RECEIVED COMMAND: {command}")
            for agent_data in data['agents']:
                if agent_data['id'] == command.get('agent'):
                    if command.get('command') == "toggle_mom":
                        agent_data['vehicle_state']['mom_available'] = not agent_data['vehicle_state']['mom_available']
                    elif command.get('command') == "toggle_aero":
                        v_state = agent_data['vehicle_state']
                        v_state['aero_mode'] = "X-MODE" if v_state['aero_mode'] == "Z-MODE" else "Z-MODE"

        # iterate agents
        for agent_data in data['agents']:
            agent_id = agent_data['id']
            state = agent_states[agent_id]
            v_state = agent_data['vehicle_state']

            if agent_data['status'] in ("CRASHED", "OUT_OF_ENERGY"):
                continue
            if random.randint(0, 10000) == 1 and agent_data['status'] == "RACING":
                print(f"EVENT: {agent_id} has CRASHED!")
                agent_data['status'] = "CRASHED"
                continue

            current_node_name = state["current_node"]
            next_node_name = state["next_node"]
            try:
                edge_data = G.edges[current_node_name, next_node_name]
            except Exception:
                successors = list(G.successors(current_node_name))
                if successors: state["next_node"] = successors[0]
                else: state["next_node"] = "n_t1_brake"
                edge_data = G.edges[current_node_name, state["next_node"]]

            # determine base speed
            if edge_data.get('is_pit_lane'):
                current_speed = SPEED_PIT
            elif edge_data.get('radius') is None:
                current_speed = SPEED_FAST
            elif edge_data.get('radius') > 100:
                current_speed = SPEED_MEDIUM
            else:
                current_speed = SPEED_SLOW

            # VSC slow-down
            speed_multiplier = 0.6 if data['race_status'].get('safety_car') == "VSC" else 1.0
            agent_speed = current_speed * state['speed_factor'] * speed_multiplier
            
            # --- "HARD STOP" PIT LOGIC WITH VARIABLE TIMER ---
            if state["current_node"] == "n_pit_stall":
                if 'pit_timer' not in state:
                    random_duration_sec = random.uniform(MIN_PIT_STOP_SEC, MAX_PIT_STOP_SEC)
                    total_frames = int(random_duration_sec * UPDATES_PER_SEC)
                    state['pit_timer'] = total_frames
                    state['progress'] = 0.0 # Pin them to the start
                    print(f"EVENT: {agent_id} beginning {random_duration_sec:.2f}s pit stop.")

                state['pit_timer'] -= 1

                if state['pit_timer'] <= 0:
                    state['progress'] = 1.0 # Force segment completion
                else:
                    agent_speed = 0.0 # STAY STOPPED
            
            state['progress'] += agent_speed
            # --- END EDIT ---

            # Segment completion block
            if state['progress'] >= 1.0:
                # --- "PIT STOP COMPLETE" LOGIC (FIXED) ---
                if current_node_name == "n_pit_stall":
                    print(f"EVENT: {agent_id} has COMPLETED pit stop.")
                    agent_data['status'] = "RACING"
                    v_state['on_cliff'] = False
                    v_state['pit_stops_made'] = v_state.get('pit_stops_made', 0) + 1
                    v_state['tyre_life'] = 1.0
                    v_state['tyre_compound'] = "hard"
                    state['will_pit'] = False
                    if 'pit_timer' in state:
                        del state['pit_timer']
                    
                    # --- THIS IS THE FIX ---
                    # Manually set the next segment to be the pit exit ramp
                    # and skip the rest of the path-finding logic for this frame.
                    state['current_node'] = "n_pit_exit"
                    state['next_node'] = "n_t1_apex"
                    state['progress'] = 0.0
                    continue # <-- This skips the "teleport" bug
                    # --- END FIX ---
                # --- END EDIT ---

                if edge_data.get('is_finish_line'):
                    lap_time = current_time - lap_times[agent_id]
                    lap_times[agent_id] = current_time
                    agent_data['lap_data']['last_lap_time'] = format_seconds_to_str(lap_time)
                    agent_data['lap_data']['current_lap'] += 1
                    data['race_status']['current_lap'] = agent_data['lap_data']['current_lap']
                    fastest_val = parse_time_to_seconds(agent_data['lap_data'].get('fastest_lap_time'))
                    if (fastest_val is None) or (lap_time < fastest_val):
                        agent_data['lap_data']['fastest_lap_time'] = format_seconds_to_str(lap_time)

                state['current_node'] = state['next_node']
                state['progress'] = 0.0

                if state['current_node'] == "n_t15_apex" and state.get('will_pit'):
                    state['next_node'] = "n_pit_entry"
                    agent_data['status'] = "PITTING"
                else:
                    successors = list(G.successors(state['current_node']))
                    if successors:
                        state['next_node'] = successors[0]
                    else:
                        state['next_node'] = "n_t1_brake"
                try:
                    edge_data = G.edges[state['current_node'], state['next_node']]
                except Exception:
                    pass

            # update interpolated position
            try:
                start_pos = np.array(pos[state['current_node']])
                end_pos = np.array(pos[state['next_node']])
                new_pos = start_pos + (end_pos - start_pos) * state['progress']
                agent_data['position'] = new_pos.tolist()
            except Exception:
                pass

            # battery/fuel/tyre changes
            if not edge_data.get('is_pit_lane') and agent_data['status'] == "RACING":
                if edge_data.get('x_mode_allowed'):
                    v_state['aero_mode'] = "X-MODE"
                    v_state['battery_soc'] = max(0.0, v_state['battery_soc'] - BASE_DRAIN_RATE * (agent_speed / SPEED_FAST))
                    v_state['fuel_remaining_mj'] -= 0.02 * state['speed_factor']
                    v_state['tyre_life'] -= 0.00005 * state['speed_factor']
                else:
                    v_state['aero_mode'] = "Z-MODE"
                    v_state['battery_soc'] = min(1.0, v_state['battery_soc'] + BASE_REGEN_RATE * (1.0 - (agent_speed / SPEED_MEDIUM)))
                    v_state['fuel_remaining_mj'] -= 0.005 * state['speed_factor']
                    v_state['tyre_life'] -= 0.0002 * state['speed_factor']

            v_state['fuel_remaining_mj'] = max(0.0, v_state['fuel_remaining_mj'])
            v_state['tyre_life'] = max(0.0, v_state['tyre_life'])

            if v_state['tyre_life'] < 0.15 and not v_state['on_cliff'] and agent_data['status'] == "RACING":
                print(f"EVENT: {agent_id} has hit the tyre cliff!")
                v_state['on_cliff'] = True
                state['will_pit'] = True

            if v_state['fuel_remaining_mj'] == 0.0 and agent_data['status'] == "RACING":
                print(f"EVENT: {agent_id} has run out of fuel!")
                agent_data['status'] = "OUT_OF_ENERGY"
                continue

        # Haas MOM proximity logic
        try:
            ocon_data = next(a for a in data['agents'] if a['id'] == 'Ocon')
            bearman_data = next(a for a in data['agents'] if a['id'] == 'Bearman')
            ocon_pos = np.array(ocon_data['position'])
            bearman_pos = np.array(bearman_data['position'])
            distance = np.linalg.norm(ocon_pos - bearman_pos)
            b_state = agent_states['Bearman']
            b_curr_node = b_state["current_node"]
            b_next_node = b_state["next_node"]
            b_edge_data = G.edges[b_curr_node, b_next_node]
            if distance < MOM_DETECTION_DISTANCE and b_edge_data.get('mom_detection'):
                bearman_data['vehicle_state']['mom_available'] = True
            else:
                bearman_data['vehicle_state']['mom_available'] = False

            if bearman_data['vehicle_state']['mom_available'] and random.randint(0, 10) > 7:
                 bearman_data['vehicle_state']['mom_active'] = True
            else:
                 bearman_data['vehicle_state']['mom_active'] = False
        except (StopIteration, KeyError):
            pass

        # Sort & update ranks
        data['agents'].sort(key=get_sort_key, reverse=True)
        for i, agent in enumerate(data['agents']):
            agent['rank'] = i + 1

        # write to disk and sleep
        write_simulation_data(data)
        time.sleep(0.01)

# -------------------------
# 6. entrypoint
# -------------------------
if __name__ == '__main__':
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        if 'numpy' not in sys.modules: raise ImportError("NumPy not found")
        if 'networkx' not in sys.modules: raise ImportError("NetworkX not found")
        G = build_bahrain_track()
        run_fake_server(G)
    except ImportError as e:
        print(f"FATAL ERROR: {e}. Please ensure libraries are installed in your venv.")
    except KeyError as e:
        print(f"FATAL ERROR: A node key was wrong. Check your agent_states logic. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in the data writer: {e}")
        print("Stopping server.")