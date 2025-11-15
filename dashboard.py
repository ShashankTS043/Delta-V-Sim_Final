import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import json
import subprocess
import sys
import os
import signal

COMMAND_FILE = "commands.json"

# --- Simulation Definitions ---
SIMS = {
    "grand_prix": {
        "title": "Grand Prix (Live)",
        "type": "live",
        "script": "run.py",
        "config": "starting_grid.json"
    },
    "grid_sim": {
        "title": "GrandPrix Sim (Analysis)",
        "type": "analysis",
        "script": "monte_carlo.py",
        "config": "starting_grid.json"
    },
    "delta_v": {
        "title": "Team-mate Delta-V (Analysis)",
        "type": "analysis",
        "script": "monte_carlo.py",
        "config": "two_car_grid.json"
    }
}

class GodModeDashboard(ThemedTk):
    
    def __init__(self):
        super().__init__()
        
        # --- 1. Core State ---
        self.sim_process = None         # Stores the running subprocess
        self.pending_sim_info = {}      # Info for the sim we're about to start
        self.is_paused = False          # Tracks pause state for the button text
        
        # --- 2. Setup Theme and Window ---
        self.set_theme("equilux") 
        self.title("Delta-V Sim: Race Control")
        self.geometry("450x350") 
        self.resizable(False, False)
        
        # --- 3. Define Styles ---
        self.setup_styles()
        
        # --- 4. Create Page Frames ---
        # We create both "pages" (frames) at the start
        self.main_menu_frame = ttk.Frame(self)
        self.control_page_frame = ttk.Frame(self, padding=20)
        
        self.create_main_menu_page()
        self.create_control_page()
        
        # --- 5. Show Main Menu on Start ---
        self.show_page("main_menu")
        
        # Handle window close [X] button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Configures all the ttk styles."""
        style = ttk.Style(self)
        style.configure("TFrame", background=style.lookup("TFrame", "background"))
        style.configure("TLabel", background=style.lookup("TFrame", "background"))
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Status.TLabel", font=("Consolas", 12, "italic"))
        
        style.configure("GP.TButton", font=("Arial", 12, "bold"), foreground="lime green")
        style.configure("GS.TButton", font=("Arial", 12, "bold"), foreground="#77DD77")
        style.configure("DV.TButton", font=("Arial", 12, "bold"), foreground="#77B5FE")
        
        style.configure("Start.TButton", font=("Arial", 10, "bold"), foreground="lime green")
        style.configure("Pause.TButton", font=("Arial", 10, "bold"), foreground="yellow")
        style.configure("Reset.TButton", font=("Arial", 10, "bold"), foreground="#FF6B6B")

    # --- Page 1: Main Menu ---
    
    def create_main_menu_page(self):
        """Populates the Main Menu frame with 3 buttons."""
        frame = self.main_menu_frame
        frame.configure(padding=20)
        
        title = ttk.Label(frame, text="Select Simulation", style="Title.TLabel")
        title.pack(pady=20)

        gp_button = ttk.Button(
            frame,
            text="Grand Prix (Live)",
            style="GP.TButton",
            command=lambda: self.go_to_control_page("grand_prix")
        )
        gp_button.pack(fill=tk.X, ipady=15, pady=5)
        
        gs_button = ttk.Button(
            frame,
            text="GrandPrix Sim (Analysis)",
            style="GS.TButton",
            command=lambda: self.go_to_control_page("grid_sim")
        )
        gs_button.pack(fill=tk.X, ipady=15, pady=5)
        
        dv_button = ttk.Button(
            frame,
            text="Team-mate Delta-V (Analysis)",
            style="DV.TButton",
            command=lambda: self.go_to_control_page("delta_v")
        )
        dv_button.pack(fill=tk.X, ipady=15, pady=5)

    # --- Page 2: Control Page ---

    def create_control_page(self):
        """Populates the Control Page frame with buttons."""
        frame = self.control_page_frame
        
        self.control_title_var = tk.StringVar(value="SIMULATION")
        title = ttk.Label(frame, textvariable=self.control_title_var, style="Title.TLabel")
        title.pack(pady=10)
        
        self.control_status_var = tk.StringVar(value="Ready to Start")
        status = ttk.Label(frame, textvariable=self.control_status_var, style="Status.TLabel")
        status.pack(pady=10)
        
        # --- Control Button Frame ---
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        # --- THIS IS THE FIX ---
        # Changed 'column_configure' to 'columnconfigure'
        control_frame.columnconfigure((0, 1, 2), weight=1)
        # --- END FIX ---
        
        self.start_button = ttk.Button(
            control_frame,
            text="Start",
            style="Start.TButton",
            command=self.execute_start
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5, ipady=10)
        
        self.pause_button = ttk.Button(
            control_frame,
            text="Pause",
            style="Pause.TButton",
            command=self.toggle_pause_resume
        )
        self.pause_button.grid(row=0, column=1, sticky="ew", padx=5, ipady=10)
        
        self.reset_button = ttk.Button(
            control_frame,
            text="Reset",
            style="Reset.TButton",
            command=self.execute_reset
        )
        self.reset_button.grid(row=0, column=2, sticky="ew", padx=5, ipady=10)
        
        back_button = ttk.Button(
            frame,
            text="< Back to Main Menu",
            command=self.go_to_main_menu
        )
        back_button.pack(pady=(20, 0), anchor="s")

    # --- Page Navigation & Logic ---

    def show_page(self, page_name):
        """Hides all pages and shows the requested one."""
        self.main_menu_frame.pack_forget()
        self.control_page_frame.pack_forget()
        
        if page_name == "main_menu":
            self.main_menu_frame.pack(fill=tk.BOTH, expand=True)
        elif page_name == "control":
            self.control_page_frame.pack(fill=tk.BOTH, expand=True)

    def go_to_control_page(self, sim_key):
        """Called by Main Menu. Sets up the Control Page."""
        self.pending_sim_info = SIMS[sim_key]
        
        # Set title
        self.control_title_var.set(self.pending_sim_info["title"])
        
        # Reset button states
        self.control_status_var.set("Ready to Start")
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(text="Pause", state=tk.DISABLED)
        self.reset_button.configure(state=tk.DISABLED)
        self.is_paused = False
        
        self.show_page("control")

    def go_to_main_menu(self):
        """Called by Back button. Kills sim and returns to menu."""
        self.execute_reset(going_back=True) # Kills any running sim
        self.show_page("main_menu")

    # --- Simulation Execution ---

    def execute_start(self):
        """Called by 'Start' on Control Page. Launches the sim."""
        info = self.pending_sim_info
        print(f"--- Dashboard: Starting Sim: {info['title']} ---")
        
        try:
            self.write_command({"pause_active": False, "vsc_active": False})
            self.sim_process = subprocess.Popen([sys.executable, info["script"], info["config"]])
            
            self.control_status_var.set("SIMULATION RUNNING")
            self.start_button.configure(state=tk.DISABLED)
            self.reset_button.configure(state=tk.NORMAL)
            
            # CRITICAL: Only enable Pause for "live" sims
            if info["type"] == "live":
                self.pause_button.configure(state=tk.NORMAL)
            else:
                self.pause_button.configure(text="Pause (N/A)", state=tk.DISABLED)
                
        except Exception as e:
            print(f"Error starting simulation: {e}")
            self.control_status_var.set("ERROR: Could not start.")

    def toggle_pause_resume(self):
        """Called by 'Pause' button. Flips the pause state."""
        if self.is_paused:
            # --- RESUME ---
            print("--- Dashboard: Resuming Simulation ---")
            self.write_command({"pause_active": False})
            self.pause_button.configure(text="Pause")
            self.control_status_var.set("SIMULATION RUNNING")
            self.is_paused = False
        else:
            # --- PAUSE ---
            print("--- Dashboard: Pausing Simulation ---")
            self.write_command({"pause_active": True})
            self.pause_button.configure(text="Resume")
            self.control_status_var.set("SIMULATION PAUSED")
            self.is_paused = True

    def execute_reset(self, going_back=False):
        """Called by 'Reset'. Kills the sim and resets the page."""
        if self.sim_process:
            print("--- Dashboard: Sending Terminate Signal to Backend ---")
            try:
                self.sim_process.terminate() 
                self.sim_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.sim_process.kill()
            except Exception as e:
                print(f"Error killing process: {e}")
            
            self.sim_process = None
        
        # Don't reset UI if we're just going back to the menu
        if not going_back:
            self.control_status_var.set("Ready to Start")
            self.start_button.configure(state=tk.NORMAL)
            self.pause_button.configure(text="Pause", state=tk.DISABLED)
            self.reset_button.configure(state=tk.DISABLED)
            self.is_paused = False

    def write_command(self, data):
        """Helper function to write to the JSON file."""
        try:
            current_data = {}
            if os.path.exists(COMMAND_FILE):
                try:
                    with open(COMMAND_FILE, 'r') as f:
                        current_data = json.load(f)
                except json.JSONDecodeError:
                    current_data = {}
            
            current_data.update(data)
            with open(COMMAND_FILE, 'w') as f:
                json.dump(current_data, f, indent=2)
        except Exception as e:
            print(f"Error writing to {COMMAND_FILE}: {e}")

    def on_closing(self):
        """Called when the user clicks the 'X' button on the window."""
        print("--- Dashboard: Close requested. Resetting simulation... ---")
        self.execute_reset(going_back=True) # Kill any running process
        self.destroy() # Close the window

if __name__ == "__main__":
    app = GodModeDashboard()
    
    # Ensure commands.json is clean on start
    try:
        with open(COMMAND_FILE, 'w') as f:
             json.dump({"vsc_active": False, "pause_active": False}, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not write initial {COMMAND_FILE}: {e}")
        
    app.mainloop()