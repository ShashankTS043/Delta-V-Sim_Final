# dashboard1.py
import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
import json
import subprocess
import sys
import os
import signal
import threading
import queue

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
        "title": "Pre-event Modelling",
        "type": "analysis",
        "script": "monte_carlo.py",
        "config": "starting_grid.json"
    },
    "delta_v": {
        "title": "Head-to-Head Runs",
        "type": "analysis",
        "script": "monte_carlo.py",
        "config": "two_car_grid.json"
    }
}

class GodModeDashboard(ThemedTk):
    
    def __init__(self):
        super().__init__()
        
        # --- 1. Core State ---
        self.sim_process = None
        self.pending_sim_info = {}
        self.is_paused = False
        self.output_queue = queue.Queue()  
        
        # --- 2. Setup Theme and Window ---
        self.set_theme("equilux")  
        self.title("Delta-V Sim: Race Control")
        self.geometry("300x885")  
        self.resizable(False, False)
        
        # --- 3. Define Styles ---
        self.setup_styles()
        
        # --- 4. Create Page Frames ---
        self.main_menu_frame = ttk.Frame(self)
        self.control_page_frame = ttk.Frame(self, padding=20)
        
        self.create_main_menu_page()
        self.create_control_page()  
        
        # --- 5. Show Main Menu on Start ---
        self.show_page("main_menu")
        
        self.after(100, self.process_output_queue)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Configures all the ttk styles."""
        self.style = ttk.Style(self)
        self.style.configure("TFrame", background=self.style.lookup("TFrame", "background"))
        self.style.configure("TLabel", background=self.style.lookup("TFrame", "background"))
        self.style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        self.style.configure("Status.TLabel", font=("Consolas", 12, "italic"))
        
        self.style.configure("GP.TButton", font=("Arial", 12, "bold"), foreground="lime green")
        self.style.configure("GS.TButton", font=("Arial", 12, "bold"), foreground="#77DD77")
        self.style.configure("DV.TButton", font=("Arial", 12, "bold"), foreground="#77B5FE")
        
        self.style.configure("Start.TButton", font=("Arial", 10, "bold"), foreground="lime green")
        self.style.configure("Pause.TButton", font=("Arial", 10, "bold"), foreground="yellow")
        self.style.configure("Reset.TButton", font=("Arial", 10, "bold"), foreground="#FF6B6B")
        self.style.configure("Output.TFrame", background=self.style.lookup("TFrame", "background"))


    # --- Page 1: Main Menu ---
    
    def create_main_menu_page(self):
        frame = self.main_menu_frame
        frame.configure(padding=20)
        title = ttk.Label(frame, text="Select Simulation", style="Title.TLabel")
        title.pack(pady=20)
        gp_button = ttk.Button(frame, text="Grand Prix (Live)", style="GP.TButton", command=lambda: self.go_to_control_page("grand_prix"))
        gp_button.pack(fill=tk.X, ipady=15, pady=5)
        gs_button = ttk.Button(frame, text="Pre-event Modelling", style="GS.TButton", command=lambda: self.go_to_control_page("grid_sim"))
        gs_button.pack(fill=tk.X, ipady=15, pady=5)
        dv_button = ttk.Button(frame, text="Head-to-Head Runs", style="DV.TButton", command=lambda: self.go_to_control_page("delta_v"))
        dv_button.pack(fill=tk.X, ipady=15, pady=5)

    # --- Page 2: Control Page ---

    def create_control_page(self):
        """Populates the Control Page frame with buttons AND output area."""
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
        control_frame.columnconfigure((0, 1, 2), weight=1)
        
        self.start_button = ttk.Button(control_frame, text="Start", style="Start.TButton", command=self.execute_start)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5, ipady=10)
        self.pause_button = ttk.Button(control_frame, text="Pause", style="Pause.TButton", command=self.toggle_pause_resume)
        self.pause_button.grid(row=0, column=1, sticky="ew", padx=5, ipady=10)
        
        self.reset_button = ttk.Button(
            control_frame,
            text="Reset",
            style="Reset.TButton",
            command=self.execute_reset
        )
        self.reset_button.grid(row=0, column=2, sticky="ew", padx=5, ipady=10)
        
        # --- Output Text Area Frame ---
        self.output_frame = ttk.Frame(frame, style="Output.TFrame")
        
        self.output_text = tk.Text(
            self.output_frame,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.style.lookup("TFrame", "background"),  
            fg="white",  
            font=("Consolas", 9)
        )
        self.output_scrollbar = ttk.Scrollbar(
            self.output_frame,
            orient=tk.VERTICAL,
            command=self.output_text.yview
        )
        self.output_text.configure(yscrollcommand=self.output_scrollbar.set)
        
        self.output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # --- END NEW ---
        
        back_button = ttk.Button(
            frame,
            text="< Back to Main Menu",
            command=self.go_to_main_menu
        )
        back_button.pack(pady=(20, 0), anchor="s")

    # --- Page Navigation & Logic ---

    def show_page(self, page_name):
        self.main_menu_frame.pack_forget()
        self.control_page_frame.pack_forget()
        
        if page_name == "main_menu":
            self.main_menu_frame.pack(fill=tk.BOTH, expand=True)
        elif page_name == "control":
            self.control_page_frame.pack(fill=tk.BOTH, expand=True)

    def go_to_control_page(self, sim_key):
        self.pending_sim_info = SIMS[sim_key]
        self.control_title_var.set(self.pending_sim_info["title"])
        
        self.control_status_var.set("Ready to Start")
        self.start_button.configure(state=tk.NORMAL)
        self.pause_button.configure(text="Pause", state=tk.DISABLED)
        self.reset_button.configure(state=tk.DISABLED)
        self.is_paused = False
        
        self.output_frame.pack_forget()  
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.configure(state=tk.DISABLED)
        
        self.show_page("control")

    def go_to_main_menu(self):
        self.execute_reset(going_back=True)  
        self.show_page("main_menu")

    # --- Simulation Execution ---

    def execute_start(self):
        info = self.pending_sim_info
        print(f"--- Dashboard: Starting Sim: {info['title']} ---")
        
        try:
            # Set commands to a known "unpaused" state
            self.write_command({"pause_active": False, "vsc_active": False})
            
            # Use sys.executable to ensure we use the same Python interpreter
            python_exe = sys.executable 
            
            if info["type"] == "analysis":
                self.sim_process = subprocess.Popen(
                    [python_exe, info["script"], info["config"]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                self.output_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
                self.clear_and_write_output("ANALYSIS RUNNING...\nThis may take several minutes.\n\n")
                
                # Start threads to read stdout and stderr
                threading.Thread(target=self.stream_output, args=(self.sim_process.stdout,), daemon=True).start()
                threading.Thread(target=self.stream_output, args=(self.sim_process.stderr,), daemon=True).start()
                
                # Start polling for the analysis to complete
                self.after(1000, self.check_analysis_sim)

            else:  # 'live'
                # Launch the live sim in its own process
                self.sim_process = subprocess.Popen([python_exe, info["script"], info["config"]])
            
            self.control_status_var.set("SIMULATION RUNNING")
            self.start_button.configure(state=tk.DISABLED)
            self.reset_button.configure(state=tk.NORMAL)
            
            if info["type"] == "live":
                self.pause_button.configure(state=tk.NORMAL)
            else:
                self.pause_button.configure(text="Pause (N/A)", state=tk.DISABLED)
                
        except Exception as e:
            print(f"Error starting simulation: {e}")
            self.control_status_var.set("ERROR: Could not start.")

    def toggle_pause_resume(self):
        if self.is_paused:
            print("--- Dashboard: Resuming Simulation ---")
            self.write_command({"pause_active": False})
            self.pause_button.configure(text="Pause")
            self.control_status_var.set("SIMULATION RUNNING")
            self.is_paused = False
        else:
            print("--- Dashboard: Pausing Simulation ---")
            self.write_command({"pause_active": True})
            self.pause_button.configure(text="Resume")
            self.control_status_var.set("SIMULATION PAUSED")
            self.is_paused = True

    def execute_reset(self, going_back=False):
        if self.sim_process:
            print("--- Dashboard: Sending Terminate Signal to Backend ---")
            try:
                self.sim_process.terminate()  
                self.sim_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("--- Dashboard: Process did not terminate, sending KILL signal ---")
                self.sim_process.kill()
            except Exception as e:
                print(f"Error killing process: {e}")
            
            self.sim_process = None
        
        if not going_back:
            self.control_status_var.set("Ready to Start")
            self.start_button.configure(state=tk.NORMAL)
            self.pause_button.configure(text="Pause", state=tk.DISABLED)
            self.reset_button.configure(state=tk.DISABLED)
            self.is_paused = False
            self.output_frame.pack_forget()

    # --- Output Streaming Functions ---
    
    def stream_output(self, pipe):
        try:
            for line in iter(pipe.readline, ''):
                self.output_queue.put(line)
        except Exception as e:
            # This might happen if the pipe is closed
            print(f"Error reading pipe: {e}")
        finally:
            pipe.close()

    def process_output_queue(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.write_output(line)
        except queue.Empty:
            pass  
        
        self.after(100, self.process_output_queue)

    def write_output(self, text):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)  
        self.output_text.configure(state=tk.DISABLED)

    def clear_and_write_output(self, text):
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", text)
        self.output_text.configure(state=tk.DISABLED)

    def check_analysis_sim(self):
        if self.sim_process is None:  
            return
            
        if self.sim_process.poll() is None:
            # Process is still running, check again
            self.after(1000, self.check_analysis_sim)
        else:
            # Process has finished
            print("--- Dashboard: Analysis simulation complete. ---")
            self.sim_process = None
            self.control_status_var.set("ANALYSIS COMPLETE")
            self.reset_button.configure(state=tk.DISABLED)
            self.start_button.configure(state=tk.NORMAL)
            self.write_output("\n--- ANALYSIS COMPLETE ---")

    # --- Utility Functions ---

    def write_command(self, data):
        """Atomically updates the JSON command file."""
        try:
            current_data = {}
            if os.path.exists(COMMAND_FILE):
                try:
                    with open(COMMAND_FILE, 'r') as f:
                        current_data = json.load(f)
                except json.JSONDecodeError:
                    current_data = {} # Overwrite corrupted file
            
            # Update the local dictionary with new commands
            current_data.update(data)
            
            # Write the new, combined data
            with open(COMMAND_FILE, 'w') as f:
                json.dump(current_data, f, indent=2)
        except Exception as e:
            print(f"Error writing to {COMMAND_FILE}: {e}")

    def on_closing(self):
        print("--- Dashboard: Close requested. Resetting simulation... ---")
        self.execute_reset(going_back=True)  
        self.destroy()  

if __name__ == "__main__":
    app = GodModeDashboard()
    
    # Set a known initial state for the command file on startup
    try:
        with open(COMMAND_FILE, 'w') as f:
             json.dump({"vsc_active": False, "pause_active": False}, f, indent=2)
    except Exception as e:
        print(f"Warning: Could not write initial {COMMAND_FILE}: {e}")
        
    app.mainloop()