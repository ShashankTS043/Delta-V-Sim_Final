import networkx as nx

def build_bahrain_track():
    """
    Creates a graph model of the Bahrain F1 circuit.
    Nodes have (x, y) positions for the visualizer.
    Edges have lengths (meters) and track attributes.
    """
    G = nx.DiGraph() # A Directed Graph, so cars can only go one way

    # --- Define the Nodes (with (x, y) map positions) ---
    # These (x, y) coordinates are a simple 2D map for the demo
    G.add_node(0, pos=(1100, 300)) # Node 0: Start/Finish Line
    G.add_node(1, pos=(100, 300))  # Node 1: T1 Braking Zone
    G.add_node(2, pos=(100, 400))  # Node 2: T2 Apex (part of T1-2-3 complex)
    G.add_node(3, pos=(200, 500))  # Node 3: T4 Braking Zone
    G.add_node(4, pos=(1000, 500)) # Node 4: T5/T6 Braking
    G.add_node(5, pos=(1000, 100)) # Node 5: T11 Braking
    G.add_node(6, pos=(800, 100))  # Node 6: T13 Braking
    G.add_node(7, pos=(800, 300))  # Node 7: T14 Apex (final corner)

    # --- Define the Edges (the track segments) ---

    # Edge 0 -> 1 (Main Straight)
    G.add_edge(0, 1, 
               length=1100,  # meters
               type="STRAIGHT",
               x_mode_allowed=True,
               mom_detection=True) # Main MOM/DRS Zone

    # Edge 1 -> 2 (T1-T2 Complex)
    G.add_edge(1, 2, length=200, type="CORNER", x_mode_allowed=False)

    # Edge 2 -> 3 (T2-T3 Straight)
    G.add_edge(2, 3, length=550, type="STRAIGHT", x_mode_allowed=False) # Curved, no X-Mode

    # Edge 3 -> 4 (T4 Corner & Straight)
    G.add_edge(3, 4, length=600, type="CORNER", x_mode_allowed=False) # T4 and straight

    # Edge 4 -> 5 (T5-T6-T7-T8 Complex)
    G.add_edge(4, 5, length=900, type="CORNER", x_mode_allowed=False) # The twisty infield

    # Edge 5 -> 6 (Back Straight)
    G.add_edge(5, 6, 
               length=650, 
               type="STRAIGHT",
               x_mode_allowed=True,
               mom_detection=True) # Second MOM/DRS Zone

    # Edge 6 -> 7 (T13-T14)
    G.add_edge(6, 7, length=300, type="CORNER", x_mode_allowed=False)

    # Edge 7 -> 0 (Final Straight to S/F)
    G.add_edge(7, 0, 
               length=400, 
               type="STRAIGHT",
               x_mode_allowed=True,
               mom_detection=False) # Final MOM/DRS Zone

    return G