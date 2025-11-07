import networkx as nx

def build_bahrain_track():
    """
    Creates a physics-based graph of the Bahrain F1 circuit.
    Nodes have (x, y) positions.
    Edges have lengths (m), corner radius (m), and attributes.
    """
    G = nx.DiGraph() # A Directed Graph, so cars can only go one way

    # --- Define the Nodes (with (x, y) map positions) ---
    G.add_node(0, pos=(1100, 300)) # Node 0: Start/Finish Line
    G.add_node(1, pos=(100, 300))  # Node 1: T1 Braking Zone
    G.add_node(2, pos=(100, 400))  # Node 2: T2 Apex
    G.add_node(3, pos=(200, 500))  # Node 3: T4 Braking Zone
    G.add_node(4, pos=(1000, 500)) # Node 4: T5/T6 Braking
    G.add_node(5, pos=(1000, 100)) # Node 5: T11 Braking
    G.add_node(6, pos=(800, 100))  # Node 6: T13 Braking
    G.add_node(7, pos=(800, 300))  # Node 7: T14 Apex (final corner)

    # --- Define the Edges (the track segments) ---
    # We now use 'radius'. radius=None means it's a straight.
    
    # Edge 0 -> 1 (Main Straight)
    G.add_edge(0, 1, 
               length=1100, 
               radius=None, # None = STRAIGHT
               x_mode_allowed=True,
               mom_detection=True) 

    # Edge 1 -> 2 (T1-T2 Complex)
    G.add_edge(1, 2, length=200, radius=60, x_mode_allowed=False) # Tight corner
    
    # Edge 2 -> 3 (T2-T3 Straight)
    G.add_edge(2, 3, length=550, radius=None, x_mode_allowed=False) # Curved, but treat as straight
    
    # Edge 3 -> 4 (T4 Corner & Straight)
    G.add_edge(3, 4, length=600, radius=75, x_mode_allowed=False) # Medium corner
    
    # Edge 4 -> 5 (T5-T6-T7-T8 Complex)
    G.add_edge(4, 5, length=900, radius=150, x_mode_allowed=False) # Fast, sweeping corners
    
    # Edge 5 -> 6 (Back Straight)
    G.add_edge(5, 6, 
               length=650, 
               radius=None, 
               x_mode_allowed=True,
               mom_detection=True)
    
    # Edge 6 -> 7 (T13-T14)
    G.add_edge(6, 7, length=300, radius=50, x_mode_allowed=False) # Tight final corners
    
    # Edge 7 -> 0 (Final Straight to S/F)
    G.add_edge(7, 0, 
               length=400, 
               radius=None, 
               x_mode_allowed=True,
               mom_detection=False)
               
    return G