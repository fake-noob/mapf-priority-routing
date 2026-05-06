import pygame
from settings import *

class HospitalGrid:
    def __init__(self):
        # Initialize a 2D array for the grid. 
        # 0 = Walkable Floor, 1 = Wall/Rack, 2 = Parking Bay, 3 = Dispenser Node
        self.map_data = [[0 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        self._build_test_layout()

    def _build_test_layout(self):
        """Creates 'The Labyrinth': A highly irregular, real-world architectural trap."""
        
        # 1. Fill the entire map with walls (1)
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                self.map_data[r][c] = 1
                
        # 2. Left Staging Area (Parking Bays)
        for r in range(2, 23):
            self.map_data[r][1] = 2  # Parking
            self.map_data[r][2] = 0  # Assembly area
            self.map_data[r][3] = 0
            
        # 3. Right Staging Area (Dispensers)
        for r in range(8, 18):
            self.map_data[r][GRID_COLS-2] = 3 # Dispensers
            self.map_data[r][GRID_COLS-3] = 0 # Assembly area

        # ---------------------------------------------------------
        # SCENARIO 1: The Funnel (Top Corridor)
        # ---------------------------------------------------------
        # Starts 3-wide
        for r in range(2, 5):
            for c in range(4, 13):
                self.map_data[r][c] = 0
        # Narrows to 2-wide
        for r in range(3, 5):
            for c in range(13, 18):
                self.map_data[r][c] = 0
        # Chokes to 1-wide
        for c in range(18, 25):
            self.map_data[4][c] = 0

        # ---------------------------------------------------------
        # SCENARIO 2: The Double Switchback (Right Side)
        # ---------------------------------------------------------
        # Zig-zags down from the end of the funnel
        for r in range(4, 9):     # Drop down
            self.map_data[r][24] = 0
        for c in range(24, 29):   # Turn right
            self.map_data[8][c] = 0
        for r in range(8, 14):    # Drop down again
            self.map_data[r][28] = 0
        for c in range(28, GRID_COLS-3): # Connect to Dispensers
            self.map_data[13][c] = 0

        # ---------------------------------------------------------
        # SCENARIO 3: Wide-to-Narrow Blind Corners (Middle)
        # ---------------------------------------------------------
        # Wide middle artery (3-tiles wide)
        for r in range(12, 15):
            for c in range(4, 16):
                self.map_data[r][c] = 0
        # Blind 1-tile alley shooting UP from the artery
        for r in range(5, 12):
            self.map_data[r][12] = 0
        # Blind 1-tile alley shooting DOWN from the artery
        for r in range(15, 21):
            self.map_data[r][10] = 0

        # ---------------------------------------------------------
        # SCENARIO 4: The Tapered Bottom Highway 
        # ---------------------------------------------------------
        # Starts 2-wide
        for r in range(21, 23):
            for c in range(4, 20):
                self.map_data[r][c] = 0 
        # Tapers to 1-wide
        for c in range(20, 29):
            self.map_data[21][c] = 0
            
        # Connect bottom highway to the switchback area to complete the loop
        for r in range(13, 22):
            self.map_data[r][28] = 0

    def draw(self, surface):
        """Iterates through the 2D array and paints the corresponding colors."""
        surface.fill(COLOR_BG)
        
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                tile_val = self.map_data[r][c]
                
                # Calculate the exact pixel coordinates for this tile
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                
                # Paint the tile based on its integer value
                if tile_val == 1:
                    pygame.draw.rect(surface, COLOR_WALL, rect)
                elif tile_val == 2:
                    pygame.draw.rect(surface, COLOR_PARKING, rect)
                elif tile_val == 3:
                    pygame.draw.rect(surface, COLOR_DISPENSER, rect)
                    
                # Draw the faint grid lines over everything
                pygame.draw.rect(surface, COLOR_GRID_LINES, rect, 1)