import heapq
from settings import *

class Node:
    def __init__(self, row, col, direction, g, h, parent):
        self.row = row
        self.col = col
        self.direction = direction
        self.g = g
        self.h = h
        self.f = g + h
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f

def get_heuristic(r1, c1, r2, c2):
    return (abs(r1 - r2) + abs(c1 - c2)) * COST_FORWARD

def a_star_search(grid_data, start_row, start_col, goal_row, goal_col, initial_dir=None, dynamic_walls=None):
    if dynamic_walls is None:
        dynamic_walls = []
        
    open_set = []
    closed_set = set()
    
    start_node = Node(start_row, start_col, initial_dir, 0, get_heuristic(start_row, start_col, goal_row, goal_col), None)
    heapq.heappush(open_set, start_node)
    
    directions = [(-1, 0, 'UP'), (1, 0, 'DOWN'), (0, -1, 'LEFT'), (0, 1, 'RIGHT')]
    
    while open_set:
        current = heapq.heappop(open_set)
        
        if current.row == goal_row and current.col == goal_col:
            path = []
            while current:
                path.append((current.row, current.col))
                current = current.parent
            return path[::-1]
            
        state = (current.row, current.col, current.direction)
        if state in closed_set:
            continue
        closed_set.add(state)
        
        for dr, dc, d_name in directions:
            nr, nc = current.row + dr, current.col + dc
            
            if nr < 0 or nr >= GRID_ROWS or nc < 0 or nc >= GRID_COLS:
                continue
            if grid_data[nr][nc] == 1:
                continue
                
            # THE FIX: Treat higher-priority agents as solid walls during calculation!
            if (nr, nc) in dynamic_walls:
                continue
                
            turn_cost = 0
            if current.direction is not None and current.direction != d_name:
                if (current.direction == 'UP' and d_name == 'DOWN') or \
                   (current.direction == 'DOWN' and d_name == 'UP') or \
                   (current.direction == 'LEFT' and d_name == 'RIGHT') or \
                   (current.direction == 'RIGHT' and d_name == 'LEFT'):
                    turn_cost = COST_TURN * 2
                else:
                    turn_cost = COST_TURN
                    
            new_g = current.g + COST_FORWARD + turn_cost
            new_h = get_heuristic(nr, nc, goal_row, goal_col)
            
            neighbor_state = (nr, nc, d_name)
            if neighbor_state not in closed_set:
                neighbor_node = Node(nr, nc, d_name, new_g, new_h, current)
                heapq.heappush(open_set, neighbor_node)
                
    return []