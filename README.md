# Delta-V Sim: A 2026 F1 Strategy Simulator

**[TrackShift Innovation Challenge 2025]**

A lightweight, agent-based simulator built in Python to model the complex strategic landscape of the 2026 Formula 1 regulations.

![Bahrain Circuit Graph](httpsloc://imageof(Bahrain%20F1%20track%20layout%20diagram))

---

## 1. The Problem: The 2026 "Energy Reset"

The 2026 F1 regulations are the biggest strategic shift in decades. Winning will no longer be about the fastest car, but the smartest energy strategy.

* **New 50/50 Power Unit:** A 350kW MGU-K and a 3000 MJ/hr energy cap make energy a finite, tactical resource.
* **Active Aerodynamics:** Manual "X-Mode" (low-drag) and "Z-Mode" (high-grip) create a new strategic choice for every straight and corner.
* **Manual Override Mode (MOM):** The new "push-to-pass" system is a complex, lap-long energy boost that replaces simple DRS.

## 2. Our Solution: Delta-V Sim

Delta-V Sim is a platform that lets a team like **MoneyGram Haas F1** run thousands of 2026 race simulations to find the optimal energy strategy *before* the first race.

Our simulator models the complex interplay between:
* Battery State of Charge (SOC)
* Active Aero (X-Mode vs. Z-Mode)
* Manual Override (MOM) deployment

## 3. Core Architecture

Our simulator is built as a lightweight, multi-layered framework in Python:

* **Simulation Core (Mesa):** We use Mesa to give each `F1Agent` an autonomous "brain" to execute its own strategy.
* **Environment & Track (NetworkX):** The racetrack is a `networkx` directed graph. This allows us to model any F1 track (like our current Bahrain model) by defining nodes (braking zones) and edges (straights, corners).
* **Data & Analytics:** All agent states are logged for real-time analysis and can be run in a "Monte Carlo" mode to find the winningest strategies.
* **Visualization (Pygame & Matplotlib):** A decoupled frontend to show the live 2D race and data leaderboards.

## 4. How to Run (Local Setup)

This project uses Python 3.12+ and a virtual environment.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/ShashankTS043/Delta-V-Sim.git](https://github.com/ShashankTS043/Delta-V-Sim.git)
    cd Delta-V-Sim
    ```

2.  **Create and activate the virtual environment:**
    ```bash
    # On macOS
    python3 -m venv venv
    source venv/bin/activate
    
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install all required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the headless (terminal-only) simulation:**
    ```bash
    python3 run.py
    ```

## 5. Our Team
* Shashank T S
* Shreekesh S
* Arjun H Athreya