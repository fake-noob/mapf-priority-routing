import pygame
import math
from settings import *
from algorithms.pathfinding import a_star_search

pygame.font.init() # Initialize fonts

class Agent:
    def __init__(self, agent_id, start_col, start_row, priority=PRIORITY_STANDARD):
        self.id = agent_id
        self.col = start_col
        self.row = start_row
        self.priority = priority
        self.base_priority = priority 
        self.state = "NORMAL"         
        self.original_goal = None     
        self.direction = 'RIGHT' 
        
        if self.priority == PRIORITY_EMERGENCY:
            self.base_color = COLOR_AGENT_EMG  
        else:
            self.base_color = COLOR_AGENT_STD  
            
        self.path = []
        self.goal = None
        self.font = pygame.font.SysFont(None, 24)

    def set_goal(self, grid_data, goal_row, goal_col, dynamic_walls=None):
        self.goal = (goal_row, goal_col)
        full_path = a_star_search(grid_data, self.row, self.col, goal_row, goal_col, self.direction, dynamic_walls)
        
        if full_path and len(full_path) > 1:
            self.path = full_path[1:] 
        else:
            self.path = []

    def move(self):
        if self.path:
            next_step = self.path.pop(0) 
            if next_step[0] < self.row: self.direction = 'UP'
            elif next_step[0] > self.row: self.direction = 'DOWN'
            elif next_step[1] < self.col: self.direction = 'LEFT'
            elif next_step[1] > self.col: self.direction = 'RIGHT'
            self.row = next_step[0]
            self.col = next_step[1]

    def draw(self, surface):
        center_x = (self.col * TILE_SIZE) + (TILE_SIZE // 2)
        center_y = (self.row * TILE_SIZE) + (TILE_SIZE // 2)
        
        current_color = (200, 200, 50) if self.state == "YIELDING" else self.base_color
        
        # 1. DRAW GOAL TARGET (CROSSHAIR)
        if self.goal:
            gx = (self.goal[1] * TILE_SIZE) + (TILE_SIZE // 2)
            gy = (self.goal[0] * TILE_SIZE) + (TILE_SIZE // 2)
            pygame.draw.circle(surface, current_color, (gx, gy), 12, 2)
            pygame.draw.line(surface, current_color, (gx-12, gy), (gx+12, gy), 2)
            pygame.draw.line(surface, current_color, (gx, gy-12), (gx, gy+12), 2)

        # 2. DRAW DASHED PATH LINES
        if self.path:
            points = [(center_x, center_y)] + [((pc * TILE_SIZE) + (TILE_SIZE // 2), (pr * TILE_SIZE) + (TILE_SIZE // 2)) for pr, pc in self.path]
            width = 2 if self.state == "YIELDING" else 3
            dash_len = 5 + (self.id * 5) # Unique dash lengths based on Agent ID
            
            for i in range(len(points) - 1):
                p1, p2 = points[i], points[i+1]
                dist = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
                if dist == 0: continue
                dashes = max(1, int(dist / dash_len))
                for j in range(dashes):
                    if j % 2 == 0:
                        sx = p1[0] + (p2[0] - p1[0]) * j / dashes
                        sy = p1[1] + (p2[1] - p1[1]) * j / dashes
                        ex = p1[0] + (p2[0] - p1[0]) * (j + 1) / dashes
                        ey = p1[1] + (p2[1] - p1[1]) * (j + 1) / dashes
                        pygame.draw.line(surface, current_color, (sx, sy), (ex, ey), width)
                
        # 3. DRAW AGENT BODY
        radius = (TILE_SIZE // 2) - 4 
        pygame.draw.circle(surface, current_color, (center_x, center_y), radius)
        
        # 4. DRAW AGENT ID NUMBER
        text_surf = self.font.render(str(self.id), True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=(center_x, center_y))
        surface.blit(text_surf, text_rect)