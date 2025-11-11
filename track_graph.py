import networkx as nx

def build_bahrain_track():
    """
    Creates a high-fidelity, physics-based graph of the Bahrain F1 circuit.
    This new model includes all 15 turns.
    (This is the stable version *before* pit lanes)
    """
    G = nx.DiGraph() 
    # --- Node Definitions (Visually Accurate Coords) ---
    G.add_node("n_t15_apex", pos=(800, 700)) # T15 Apex (Start of main straight)
    G.add_node("n_t1_brake", pos=(800, 150)) # T1 Braking Zone
    G.add_node("n_t1_apex", pos=(770, 100)) # T1 Apex
    G.add_node("n_t2_apex", pos=(700, 150)) # T2 Apex
    G.add_node("n_t3_exit", pos=(700, 200)) # T3 Exit
    G.add_node("n_t4_brake", pos=(650, 350)) # T4 Braking Zone
    G.add_node("n_t4_apex", pos=(610, 380)) # T4 Apex
    G.add_node("n_t5_entry", pos=(400, 380)) # T5/T6 Entry
    G.add_node("n_t7_apex", pos=(350, 420)) # T7 Apex
    G.add_node("n_t8_brake", pos=(300, 380)) # T8 Braking
    G.add_node("n_t8_apex", pos=(270, 350)) # T8 Apex
    G.add_node("n_t9_entry", pos=(200, 420)) # T9/T10 Entry
    G.add_node("n_t10_apex", pos=(150, 400)) # T10 Apex
    G.add_node("n_t11_brake", pos=(150, 650)) # T11 Braking
    G.add_node("n_t11_apex", pos=(180, 700)) # T11 Apex
    G.add_node("n_t12_apex", pos=(250, 750)) # T12 Apex (fast sweeper)
    G.add_node("n_t13_brake", pos=(500, 750)) # T13 Braking
    G.add_node("n_t13_apex", pos=(550, 780)) # T13 Apex
    G.add_node("n_t14_brake", pos=(750, 780)) # T14 Braking

    # --- Edge Definitions (Track Segments) ---
    
    # 1. Main Straight (T15 to T1)
    G.add_edge("n_t15_apex", "n_t1_brake", 
        length=1100, 
        radius=None, 
        x_mode_allowed=True,
        mom_detection=True,
        is_finish_line=True, # This edge IS the finish line
        is_pit_entry_decision=True) # This is the corner to decide
 
    # 2. T1/T2/T3 Complex
    G.add_edge("n_t1_brake", "n_t1_apex", length=110, radius=60, x_mode_allowed=False)
    G.add_edge("n_t1_apex", "n_t2_apex", length=100, radius=70, x_mode_allowed=False)
    G.add_edge("n_t2_apex", "n_t3_exit", length=100, radius=70, x_mode_allowed=False)
    
    # 3. Straight to T4
    G.add_edge("n_t3_exit", "n_t4_brake", length=250, radius=None, x_mode_allowed=False)
    
    # 4. T4
    G.add_edge("n_t4_brake", "n_t4_apex", length=120, radius=75, x_mode_allowed=False)
    
    # 5. Straight to T5
    G.add_edge("n_t4_apex", "n_t5_entry", length=300, radius=None, x_mode_allowed=True)
    
    # 6. T5/T6/T7 (Fast Sweepers)
    G.add_edge("n_t5_entry", "n_t7_apex", length=450, radius=150, x_mode_allowed=False)
    
    # 7. Short straight to T8
    G.add_edge("n_t7_apex", "n_t8_brake", length=150, radius=None, x_mode_allowed=False)
    
    # 8. T8
    G.add_edge("n_t8_brake", "n_t8_apex", length=100, radius=55, x_mode_allowed=False)
    
    # 9. T9/T10 (The Infield)
    G.add_edge("n_t8_apex", "n_t9_entry", length=200, radius=None, x_mode_allowed=False)
    G.add_edge("n_t9_entry", "n_t10_apex", length=200, radius=50, x_mode_allowed=False) # Tight
    
    # 10. Straight to T11
    G.add_edge("n_t10_apex", "n_t11_brake", length=700, radius=None, x_mode_allowed=True, mom_detection=True)
    
    # 11. T11/T12
    G.add_edge("n_t11_brake", "n_t11_apex", length=150, radius=80, x_mode_allowed=False)
    G.add_edge("n_t11_apex", "n_t12_apex", length=200, radius=160, x_mode_allowed=False) # Fast
    
    # 12. Back Straight
    G.add_edge("n_t12_apex", "n_t13_brake", length=600, radius=None, x_mode_allowed=True, mom_detection=True)
    
    # 13. T13
    G.add_edge("n_t13_brake", "n_t13_apex", length=120, radius=65, x_mode_allowed=False)
    
    # 14. T14 / T15
    G.add_edge("n_t13_apex", "n_t14_brake", length=300, radius=None, x_mode_allowed=False)
    G.add_edge("n_t14_brake", "n_t15_apex", length=150, radius=70, x_mode_allowed=False)
    
    return G