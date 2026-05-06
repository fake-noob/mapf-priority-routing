import numpy as np
import torch
import math
from settings import GRID_ROWS, GRID_COLS

class CustomRLEnv:
    def __init__(self, grid, fov_size=7):
        self.grid = grid
        self.fov_size = fov_size
        self.half_fov = fov_size // 2

    def get_agent_state(self, agent, swarm_agents):
        """
        Extracts the localized state for a given agent.
        Returns a tensor of shape (3, fov_size, fov_size) and a goal vector of shape (2).
        Channels:
        0: Walls/Obstacles
        1: Other agents' projected positions/bodies
        2: Priorities of other agents (0 if empty, higher if priority)
        """
        state = np.zeros((3, self.fov_size, self.fov_size), dtype=np.float32)
        
        for i in range(self.fov_size):
            for j in range(self.fov_size):
                r = agent.row - self.half_fov + i
                c = agent.col - self.half_fov + j
                
                # Check bounds
                if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
                    if self.grid.map_data[r][c] == 1:
                        state[0, i, j] = 1.0 # Wall
                        
                    for other in swarm_agents:
                        if other.id != agent.id:
                            # Consider projected path or current position
                            if (other.row == r and other.col == c) or (other.path and other.path[0] == (r, c)):
                                state[1, i, j] = 1.0 # Agent presence
                                state[2, i, j] = 1.0 if other.priority == 1 else 0.5 # Priority mapping
                else:
                    state[0, i, j] = 1.0 # Out of bounds is a wall

        # Goal vector normalized
        if agent.goal:
            dx = agent.goal[1] - agent.col
            dy = agent.goal[0] - agent.row
            dist = math.hypot(dx, dy)
            if dist > 0:
                dx /= dist
                dy /= dist
        else:
            dx, dy = 0, 0
            
        goal_vector = np.array([dx, dy], dtype=np.float32)
        
        return state, goal_vector
