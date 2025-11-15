import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
import sys
import time
import os
import glob
from json import JSONDecodeError

# --- 1. "SNAPSHOT-AWARE" DATA READER ---
# (This is the same robust loader from your pygame_vis.py)
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

# --- 2. MATPLOTLIB ANIMATION FUNCTION (SINGLE PLOT) ---

# Create a 1-row, 1-column subplot
fig, ax1 = plt.subplots(1, 1, figsize=(9, 8))
fig.canvas.manager.set_window_title('Aether Mission Control (Tyre Life)')

# Cache variables
sim_cache = None
last_read_ts = 0.0
READ_INTERVAL = 1.0 / 5.0  # read up to 5 Hz

def animate(frame):
    """
    This function is called every 'interval' milliseconds.
    It reads the newest snapshot (throttled) and draws ONE chart for Tyre Life.
    """
    global sim_cache, last_read_ts

    # Throttle reads
    now = time.time()
    if (now - last_read_ts) >= READ_INTERVAL:
        # --- THIS IS THE FIX ---
        # Read from snapshots, not the old data.json
        new_data, new_snapshot_name = load_simulation_data_from_snapshots(prefix="data_snapshot_", folder=".")
        # --- END FIX ---
        last_read_ts = now
        if new_data is not None:
            sim_cache = new_data  # Update the cache

    data = sim_cache
    if data is None:
        # show a helpful "waiting" annotation
        ax1.clear()
        ax1.text(0.5, 0.5, "Waiting for data snapshots...\nStart the writer",
                 horizontalalignment='center', verticalalignment='center', transform=ax1.transAxes,
                 fontsize=12, color='gray')
        ax1.set_xticks([])
        ax1.set_yticks([])
        return

    agents = data.get('agents')
    if not agents:
        return

    try:
        # Normalize JSON into a DataFrame
        df = pd.json_normalize(agents)
        # Ensure columns exist (defensive)
        for col in ['rank', 'id', 'vehicle_state.tyre_life', 'status']:
            if col not in df.columns:
                df[col] = None

        # Select the columns we need and sort by rank (ascending)
        df = df[['rank', 'id', 'vehicle_state.tyre_life', 'status']]
        # coerce rank to numeric for sorting
        df['rank'] = pd.to_numeric(df['rank'], errors='coerce').fillna(9999)
        df = df.sort_values(by='rank', ascending=True).reset_index(drop=True)

        # Labels (driver names)
        y_labels = df['id'].astype(str)

        # --- PLOT 1: TYRE LIFE ---
        ax1.clear()
        tyre_pct = (df['vehicle_state.tyre_life'].fillna(0).astype(float) * 100).clip(0, 100)
        
        # --- Create a color list based on status ---
        colors = []
        for status in df['status']:
            if status == "PITTING":
                colors.append('purple')
            elif status == "CRASHED" or status == "OUT_OF_ENERGY":
                colors.append('darkred')
            else:
                colors.append('red') # Default racing color
                
        bars1 = ax1.barh(y_labels, tyre_pct, color=colors)
        ax1.invert_yaxis()
        ax1.set_title('Live Tyre Life (%)')
        ax1.set_xlabel('Tyre Life Remaining (%)')
        ax1.set_xlim(0, 100)
        
        # annotate percentages on bars
        for rect, val in zip(bars1, tyre_pct):
            ax1.text(rect.get_width() + 1.5, rect.get_y() + rect.get_height() / 2,
                     f"{val:.0f}%", va='center', fontsize=9)

        # Small visual tweaks
        plt.tight_layout()

    except Exception as e:
        # Don't crash the animation — print error to console for debugging
        print(f"Error during plotting: {e}", file=sys.stderr)

# --- 3. START THE ANIMATION ---
def run_leaderboard():
    print("--- LIVE MISSION CONTROL (MATPLOTLIB) STARTED ---")
    print("--- This window will update every 1 second ---")

    # Disable frame caching to avoid the UserWarning
    ani = animation.FuncAnimation(fig, animate, interval=1000, cache_frame_data=False)

    try:
        plt.show()
    except Exception as e:
        print(f"Matplotlib window closed or crashed: {e}", file=sys.stderr)

if __name__ == '__main__':
    run_leaderboard()