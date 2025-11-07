import networkx as nx

def build_bahrain_track():
    """
    Creates a high-fidelity, physics-based graph of the Bahrain F1 circuit.
    This new model includes all 15 turns.
    """
    G = nx.DiGraph() 

    # --- Node Definitions ---
    # G.add_node("n_finish", pos=(920, 430))    <-- DELETED THIS NODE
    G.add_node("n_t1_brake", pos=(200, 430))   
    G.add_node("n_t1_apex", pos=(150, 460))    
    G.add_node("n_t2_apex", pos=(200, 500))    
    G.add_node("n_t3_exit", pos=(300, 480))    
    G.add_node("n_t4_brake", pos=(450, 500))   
    G.add_node("n_t4_apex", pos=(480, 540))    
    G.add_node("n_t5_entry", pos=(600, 470))   
    G.add_node("n_t7_apex", pos=(650, 440))    
    G.add_node("n_t8_brake", pos=(700, 500))   
    G.add_node("n_t8_apex", pos=(680, 530))    
    G.add_node("n_t9_entry", pos=(650, 600))   
    G.add_node("n_t10_apex", pos=(680, 650))   
    G.add_node("n_t11_brake", pos=(1000, 600)) 
    G.add_node("n_t11_apex", pos=(1050, 580))  
    G.add_node("n_t12_apex", pos=(1080, 500))  
    G.add_node("n_t13_brake", pos=(1100, 200)) 
    G.add_node("n_t13_apex", pos=(1080, 150))  
    G.add_node("n_t14_brake", pos=(850, 150))  
    G.add_node("n_t15_apex", pos=(800, 300))   # This is now the last node in the loop

    # --- Edge Definitions (Track Segments) ---
    
    # 1. Main Straight (T15 back to T1)
    G.add_edge("n_t15_apex", "n_t1_brake", 
               length=1100, 
               radius=None, 
               x_mode_allowed=True,
               mom_detection=True,
               is_finish_line=True) # <-- NEW: This edge IS the finish line

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
    
    # 14. T14
    G.add_edge("n_t13_apex", "n_t14_brake", length=300, radius=None, x_mode_allowed=False)
    G.add_edge("n_t14_brake", "n_t15_apex", length=150, radius=70, x_mode_allowed=False)
    
    # 15. Link back to Finish Line (DELETED)
    # G.add_edge("n_t1_brake", "n_finish", length=0, radius=None, x_mode_allowed=False) <-- DELETED
               
    return G