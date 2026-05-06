# settings.py
# Central configuration file for the Micro-Swarm Sorting Simulation

# -----------------------------------------
# 1. Grid & Window Geometry
# -----------------------------------------
TILE_SIZE = 40       # Size of each grid square in pixels. 
GRID_COLS = 35       # Total number of columns.
GRID_ROWS = 25       # Total number of rows.

# The Pygame window size is dynamically calculated based on the grid
SCREEN_WIDTH = TILE_SIZE * GRID_COLS
SCREEN_HEIGHT = TILE_SIZE * GRID_ROWS

# -----------------------------------------
# 2. Time & Synchronization (The "Ticks")
# -----------------------------------------
FPS = 5              # Frames per second. Kept intentionally low (5 ticks/sec) 
                     # so you can visually debug the pathfinding and deadlocks.

# -----------------------------------------
# 3. Kinematic Penalties (For A* Heuristic)
# -----------------------------------------
# By weighting a turn heavily, A* will mathematically prefer longer, 
# straighter arteries over zig-zagging through narrow veins.
COST_FORWARD = 10    # Mathematical cost to move 1 tile forward.
COST_TURN = 10       # Mathematical cost to pivot 90 degrees in place.

# -----------------------------------------
# 4. Swarm Logic Constraints
# -----------------------------------------
DEADLOCK_TIMEOUT = 3 # Number of consecutive blocked ticks before PIBT/CSP logic triggers.
PRIORITY_EMERGENCY = 1 # Lower number = Higher priority
PRIORITY_STANDARD = 2

# -----------------------------------------
# 5. Environment Colors (RGB)
# -----------------------------------------
COLOR_BG = (245, 245, 245)         # Off-white floor (walkable space)
COLOR_WALL = (50, 50, 50)          # Dark gray for physical storage racks
COLOR_PARKING = (200, 220, 255)    # Light blue for charging/idle bays
COLOR_DISPENSER = (100, 200, 100)  # Green for medication pickup nodes

COLOR_AGENT_STD = (50, 150, 250)   # Blue for standard robots
COLOR_AGENT_EMG = (250, 50, 50)    # Red for emergency robots
COLOR_GRID_LINES = (220, 220, 220) # Faint lines to easily see the 1-tile bottlenecks