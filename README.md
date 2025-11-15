# Delta-V Sim: F1 Strategy Simulator

**TrackShift Innovation Challenge 2025 Submission**

Delta-V Sim is a professional-grade, stochastic Formula 1 strategy simulator. Built as a "digital twin," it models the complex interplay between energy management (MOM), tyre degradation, and race events to allow teams to test and validate strategies in a virtual environment.



---

##  Core Features

* **Universal AI Architecture:** The core `agent.py` "brain" can operate in two distinct modes based on the strategy file provided:
    1) **"Pro+ Mode" (Stochastic Race):** A full 22-car simulation with random events (VSCs, Driver Errors) to test high-level "aggressive" vs. "conservative" strategies.
    2) **"Pro++ Mode" (Deterministic Dyno):** A 1v1 "dyno test" to compare two specific, deterministic `energy_deployment_map` strategies against each other.
* **"Reason Engine":** A headless Monte Carlo analyzer (`monte_carlo.py`) that runs hundreds of simulations to provide statistical validation of a strategy's performance.
* **"God-Mode" Dashboard:** A Tkinter-based "Race Control" panel that can inject live events (like a Virtual Safety Car) into the simulation in real-time.
* **High-Fidelity Physics:** The simulation models track segments, corner radii, tyre cliffs, battery SoC, fuel burn, and the full 2026-spec aero (X-Mode & Z-Mode) and MOM (Manual Overtake Mode) power unit regulations.

---

## Repository Structure

This repository is organized into three distinct branches:

* **`main`:** Contains this README, the `LICENSE`, and other project-wide metadata. **No code lives here.**
* **`Backend`:** Contains all the core simulation logic. This includes the `agent.py`, `model.py`, `track_graph.py`, and the `monte_carlo.py` "Reason Engine."
* **`Frontend`:** Contains the `dashboard.py` Tkinter application for the "God-Mode" Race Control panel.

---

## How to Run

### 1. Backend Simulation (The "Reason Engine")

To run a full stochastic analysis of a strategy:

1.  Switch to the `Backend` branch:
    ```bash
    git checkout Backend
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the Monte Carlo analyzer, pointing it at a grid file:
    ```bash
    python monte_carlo.py starting_grid.json
    ```

### 2. Live "God-Mode" Simulation

This requires two terminals.

**Terminal 1 (Run the Simulator):**

1.  Switch to the `Backend` branch:
    ```bash
    git checkout Backend
    ```
2.  Start the live simulator:
    ```bash
    python run.py starting_grid.json
    ```
    *(The simulation will now listen for commands from `commands.json`)*

**Terminal 2 (Run the Dashboard):**

1.  Switch to the `Frontend` branch:
    ```bash
    git checkout Frontend
    ```
2.  Start the "God-Mode" dashboard:
    ```bash
    python dashboard.py
    ```
    *(You can now use the dashboard to trigger a VSC in the running simulation.)*

---

## Contributors

Please see the `CONTRIBUTING.md` file for details on how to contribute to this project.