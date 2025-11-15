# pygame_vis.py -- snapshot-aware visualizer for the snapshot-mode writer
import pygame
import sys
import json
import networkx as nx
import os
import time
import glob
from json import JSONDecodeError

# --- ensure relative paths work from script folder ---
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except Exception:
    pass

# --- 1. PYGAME & FONT INITIALIZATION ---
pygame.init()
pygame.font.init()

# --- 2. SCREEN & COLOR DEFINITIONS ---
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 800
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Delta-V Sim")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 25, 25)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 50)
GREY = (100, 100, 100)
CYAN = (0, 255, 255)
DARK_BLUE = (0, 0, 150)
TRACK_COLOR = (200, 200, 200)
PURPLE = (255, 0, 255) # For Pitting

# Agent Visuals
AGENT_RADIUS = 8
AGENT_COLORS = {
    'Ocon': BLUE,
    'Bearman': RED,
    'Verstappen': (0, 0, 139), # DarkBlue
    'Perez': (0, 0, 139),
    'Hamilton': (220, 0, 0), # Ferrari Red
    'Leclerc': (220, 0, 0),
    'Norris': (255, 135, 0), # McLaren Orange
    'Piastri': (255, 135, 0),
}

# Fonts
try:
    FONT_HUD = pygame.font.Font('Consolas', 20)
    FONT_AGENT = pygame.font.Font('Consolas', 15)
except Exception:
    FONT_HUD = pygame.font.SysFont('Consolas', 18)
    FONT_AGENT = pygame.font.SysFont('Consolas', 15)

# --- 3. (BUTTONS REMOVED) ---
# Fonts
try:
    FONT_HUD_B = pygame.font.Font('Consolas', 20)
    FONT_AGENT_B = pygame.font.Font('Consolas', 15)
    # --- NEW: Banner Font ---
    FONT_BANNER = pygame.font.Font('Consolas', 30) # Larger for the banner
    # --- END NEW ---
except Exception:
    FONT_HUD_B = pygame.font.SysFont('Consolas', 18)
    FONT_AGENT_B = pygame.font.SysFont('Consolas', 15)
    # --- NEW: Banner Font Fallback ---
    FONT_BANNER = pygame.font.SysFont('Arial', 28, bold=True) # Fallback with bold
    # --- END NEW ---

# --- 4. TRACK (same pit-lane nodes as writer) ---
def build_bahrain_track():
    G = nx.DiGraph()
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

    # Pit edges
    G.add_edge("n_t15_apex", "n_pit_entry", length=50, radius=100, is_pit_lane=True, x_mode_allowed=False)
    G.add_edge("n_pit_entry", "n_pit_stall", length=400, radius=None, is_pit_lane=True, x_mode_allowed=False)
    G.add_edge("n_pit_stall", "n_pit_exit", length=1, radius=None, is_pit_lane=True, x_mode_allowed=False)
    G.add_edge("n_pit_exit", "n_t1_apex", length=450, radius=None, is_pit_lane=True, x_mode_allowed=False)

    return G

# Robust loader
def load_simulation_data_from_snapshots(prefix="data_snapshot_", folder=".", max_retries=8, base_delay=0.02, debug=False):
    pattern = os.path.join(folder, f"{prefix}*.json")
    raw_files = glob.glob(pattern)
    if not raw_files:
        return None, None

    files_with_mtime = []
    for p in raw_files:
        try:
            m = os.path.getmtime(p)
            files_with_mtime.append((p, m))
        except (FileNotFoundError, PermissionError, OSError):
            continue

    if not files_with_mtime:
        return None, None

    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
    candidates = [p for p, _ in files_with_mtime[:3]]

    if debug:
        print("Snapshot candidates:", candidates)

    for candidate in candidates:
        attempt = 0
        while attempt < max_retries:
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data, candidate
            except FileNotFoundError:
                break
            except PermissionError:
                attempt += 1
                time.sleep(base_delay * (1.5 ** attempt))
                continue
            except JSONDecodeError:
                attempt += 1
                time.sleep(base_delay * (1.5 ** attempt))
                continue
            except Exception:
                break
    return None, None

# --- MAP SCALING FUNCTIONS (UPDATED) ---
def get_track_bounds(pos_dict):
    if not pos_dict:
        return (0, 1, 0, 1)
    min_x, max_x, min_y, max_y = float('inf'), float('-inf'), float('inf'), float('-inf')
    for x, y in pos_dict.values():
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
    if min_x == max_x: max_x += 1
    if min_y == max_y: max_y += 1
    return (min_x, max_x, min_y, max_y)

def scale_pos(world_pos, bounds, map_area_dims, padding, map_start_x):
    """
    Converts a raw (x, y) track coordinate to a final (draw_x, draw_y) screen coordinate.
    """
    min_x, max_x, min_y, max_y = bounds
    map_width, map_height = map_area_dims # This is the *size* of the map drawing area
    
    world_width = max_x - min_x
    world_height = max_y - min_y
    if world_width == 0 or world_height == 0:
        return (padding + map_start_x, padding) # Avoid division by zero
    
    # Calculate scale factors to fit inside the map area (with padding)
    scale_x = (map_width - padding * 2) / world_width
    scale_y = (map_height - padding * 2) / world_height
    scale = min(scale_x, scale_y)
    
    # Apply the formula to get local coords
    raw_x, raw_y = world_pos
    draw_x_local = ((raw_x - min_x) * scale) + padding
    draw_y_local = ((raw_y - min_y) * scale) + padding
    
    # Add the map's starting X offset to get the final screen position
    return (int(draw_x_local + map_start_x), int(draw_y_local))

# --- DRAWING (UPDATED) ---
def draw_track(graph, pos_dict, bounds, map_area_dims, padding, map_start_x):
    """Draws the track graph (edges and nodes), scaled to the screen."""
    for u, v, data in graph.edges(data=True):
        if data.get('is_pit_lane'): color = PURPLE
        elif data.get('x_mode_allowed'): color = YELLOW
        else: color = TRACK_COLOR
        
        # Scale the world positions to screen positions
        screen_pos_u = scale_pos(pos_dict[u], bounds, map_area_dims, padding, map_start_x)
        screen_pos_v = scale_pos(pos_dict[v], bounds, map_area_dims, padding, map_start_x)
        
        pygame.draw.line(SCREEN, color, screen_pos_u, screen_pos_v, 5)
        
    for node_id, coordinates in pos_dict.items():
        # Draw Nodes
        screen_pos = scale_pos(coordinates, bounds, map_area_dims, padding, map_start_x)
        pygame.draw.circle(SCREEN, DARK_BLUE, screen_pos, 5)

def draw_agents(agents_data, bounds, map_area_dims, padding, map_start_x):
    """Draws all agents and their status indicators, scaled to the screen."""
    for agent in agents_data:
        try:
            agent_id = agent.get('id', 'Unknown')
            world_pos = (agent['position'][0], agent['position'][1])
            # --- SCALE IT ---
            screen_pos = scale_pos(world_pos, bounds, map_area_dims, padding, map_start_x)
            x, y = screen_pos[0], screen_pos[1]
            # --- END SCALE ---
            
            v_state = agent.get('vehicle_state', {})
            status = agent.get('status', 'RACING')

            if status == "CRASHED" or status == "OUT_OF_ENERGY":
                pygame.draw.line(SCREEN, RED, (x - AGENT_RADIUS, y - AGENT_RADIUS), (x + AGENT_RADIUS, y + AGENT_RADIUS), 3)
                pygame.draw.line(SCREEN, RED, (x + AGENT_RADIUS, y - AGENT_RADIUS), (x - AGENT_RADIUS, y + AGENT_RADIUS), 3)
                continue
            elif status == "PITTING":
                color = PURPLE if (pygame.time.get_ticks() // 200) % 2 else GREY
            else:
                if status == "FINISHED":
                    continue
                color = AGENT_COLORS.get(agent_id, GREY)

            pygame.draw.circle(SCREEN, color, (x, y), AGENT_RADIUS)

            if v_state.get('on_cliff'):
                cliff_color = RED if (pygame.time.get_ticks() // 150) % 2 else WHITE
                pygame.draw.circle(SCREEN, cliff_color, (x, y), AGENT_RADIUS + 5, 2)
            if v_state.get('mom_active'):
                mom_color = GREEN if (pygame.time.get_ticks() // 100) % 2 else WHITE
                pygame.draw.circle(SCREEN, mom_color, (x, y), AGENT_RADIUS + 2, 2)
            
            # De-clutter labels (only show for Haas)
            if agent_id == "Ocon" or agent_id == "Bearman":
                name_text = FONT_AGENT.render(agent_id, True, WHITE)
                SCREEN.blit(name_text, (x + AGENT_RADIUS + 2, y - AGENT_RADIUS))
                soc_val = v_state.get('battery_soc', 0)
                try: soc_txt = f"SOC: {float(soc_val):.0%}"
                except Exception: soc_txt = "SOC: --"
                soc_text = FONT_AGENT.render(soc_txt, True, WHITE)
                SCREEN.blit(soc_text, (x + AGENT_RADIUS + 2, y + AGENT_RADIUS - 8))
        except Exception:
            continue

def draw_status_hud(sim_data, snapshot_name=None):
    """Draws the main leaderboard (NOW ON THE LEFT)."""
    font = FONT_HUD
    # --- LAYOUT FLIP: Move HUD to the left ---
    x_pos, y_offset = 30, 70  # (Fixed your 20, 900 typo)

    r_status = sim_data.get('race_status', {}) if sim_data else {}
    status_lines = [
        f"TIME: {r_status.get('timestamp', '0:00:00.0')}",
        f"LAP: {r_status.get('current_lap', 0)} / {r_status.get('total_laps', 0)}",
        f"SAFETY CAR: {r_status.get('safety_car', 'NONE')}"
    ]
    for line in status_lines:
        SCREEN.blit(font.render(line, True, CYAN), (x_pos, y_offset))
        y_offset += 25

    SCREEN.blit(font.render("--- LIVE 2026 LEADERBOARD ---", True, CYAN), (x_pos, y_offset))
    y_offset += 30
    
    # (Added your custom lines)
    SCREEN.blit(font.render("--- Baharain Intl Cirucit ---", True, CYAN), (x_pos, y_offset))
    y_offset += 30
    SCREEN.blit(font.render("--- Weather : Dry ---", True, CYAN), (x_pos, y_offset))
    y_offset += 30

    # (Using your aligned header)
    header_text = font.render("R  |   ID     | PITS |   TYRE  |  SOC |  FUEL | STATUS", True, GREY)
    SCREEN.blit(header_text, (x_pos, y_offset))
    y_offset += 25

    agents = (sim_data or {}).get('agents', [])
    try:
        agents.sort(key=lambda a: a.get('rank', 99))
    except Exception:
        pass

    for agent in agents[:20]: # Show top 20
        try:
            v_state = agent.get('vehicle_state', {})
            l_data = agent.get('lap_data', {})
            rank = agent.get('rank', '-')
            agent_id = agent.get('id', 'N/A')
            pits = v_state.get('pit_stops_made', 0)
            
            tyre_compound = v_state.get('tyre_compound', '?')[0].upper() if v_state.get('tyre_compound') else '?'
            tyre_life = v_state.get('tyre_life', 0)
            tyre_display = f"{tyre_compound} | {tyre_life:.0%}"
            
            soc = v_state.get('battery_soc', 0)
            fuel = v_state.get('fuel_remaining_mj', 0)
            status = agent.get('status', 'N/A')
            
            try: soc_disp = f"{float(soc):.0%}"
            except Exception: soc_disp = "--"
            
            # (Using your aligned data line)
            line = f"{rank:<2} | {agent_id:<8} | {pits:<4} | {tyre_display:<7} | {soc_disp:<4} | {fuel:<5.0f} | {status}"
            
            if status == "RACING": text_color = GREEN if rank == 1 else WHITE
            elif status == "PITTING": text_color = PURPLE
            elif status == "CRASHED" or status == "OUT_OF_ENERGY": text_color = RED
            else: text_color = GREY
                
            SCREEN.blit(font.render(line, True, text_color), (x_pos, y_offset))
            y_offset += 25
        except Exception:
            continue

# --- MAIN LOOP (UPDATED) ---
# MAIN LOOP (UPDATED)
def run_demo():
    running = True
    clock = pygame.time.Clock()

    track_graph = build_bahrain_track()
    track_positions = nx.get_node_attributes(track_graph, 'pos')
    
    # --- NEW LAYOUT DEFINITIONS ---
    HUD_WIDTH = 680 # Define the width of the text area on the left
    MAP_START_X = HUD_WIDTH # The map will start where the HUD ends
    MAP_WIDTH = SCREEN_WIDTH - HUD_WIDTH # The map gets the rest of the space
    MAP_PADDING = 40 # Padding *inside* the map area
    
    # The 'screen_dims' for the map is now just its own drawing area
    map_area_dims = (MAP_WIDTH, SCREEN_HEIGHT) 
    track_bounds = get_track_bounds(track_positions)
    # --- END NEW LAYOUT ---

    sim_cache = None
    snapshot_in_use = None
    last_read_ts = 0.0
    READ_INTERVAL = 1.0 / 30.0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # (Mouse click logic is removed)

        now = time.time()
        if now - last_read_ts >= READ_INTERVAL:
            new_data, new_snapshot = load_simulation_data_from_snapshots(prefix="data_snapshot_", folder=".")
            last_read_ts = now
            if new_data is not None:
                sim_cache = new_data
                snapshot_in_use = new_snapshot

        sim_data = sim_cache

        SCREEN.fill(BLACK)
        
        # --- DRAWING (UPDATED ORDER) ---
        
        # --- NEW: DRAW THE TEXT HERO BANNER ---
        banner_text_surface = FONT_BANNER.render("DELTA-V SIMULATOR", True, CYAN)
        SCREEN.blit(banner_text_surface, (20, 20)) # Position at top-left
        # --- END NEW ---

        # Draw the track, passing in the new map layout variables
        draw_track(track_graph, track_positions, track_bounds, map_area_dims, MAP_PADDING, MAP_START_X)

        if sim_data is None:
            msg = "Waiting for data snapshots (start the writer)..."
            # Draw the message in the *center* of the map area
            SCREEN.blit(FONT_HUD.render(msg, True, WHITE), (MAP_START_X + 20, 20))
        else:
            # Draw the HUD (on the left, starts lower)
            draw_status_hud(sim_data, snapshot_name=snapshot_in_use)
            # Draw the Agents (on the right, in the map area)
            draw_agents(sim_data.get('agents', []), track_bounds, map_area_dims, MAP_PADDING, MAP_START_X)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

# (get_track_bounds is unchanged)
def get_track_bounds(pos_dict):
    if not pos_dict:
        return (0, 1, 0, 1)
    min_x, max_x, min_y, max_y = float('inf'), float('-inf'), float('inf'), float('-inf')
    for x, y in pos_dict.values():
        min_x, max_x = min(min_x, x), max(max_x, x)
        min_y, max_y = min(min_y, y), max(max_y, y)
    if min_x == max_x: max_x += 1
    if min_y == max_y: max_y += 1
    return (min_x, max_x, min_y, max_y)

if __name__ == '__main__':
    run_demo()