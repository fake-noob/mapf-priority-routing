from settings import *

def find_nearest_safe_zone(start_row, start_col, grid_data, forcefield_walls):
    """Finds the nearest Parking (2) or Dispenser (3) zone outside the forcefield."""
    queue = [(start_row, start_col)]
    visited = set()
    visited.add((start_row, start_col))
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    while queue:
        r, c = queue.pop(0)
        
        if grid_data[r][c] in [2, 3] and (r, c) not in forcefield_walls:
            return r, c
            
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(grid_data) and 0 <= nc < len(grid_data[0]):
                if grid_data[nr][nc] != 1 and (nr, nc) not in visited and (nr, nc) not in forcefield_walls:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    return None, None

def resolve_deadlocks(swarm, grid_data):
    occupied_current = {(a.row, a.col): a for a in swarm}
    
    for agent in sorted(swarm, key=lambda x: x.priority):
        if agent.path:
            next_step = agent.path[0]
            
            # COLLISION DETECTED: We are about to step on someone!
            if next_step in occupied_current:
                blocker = occupied_current[next_step]
                
                # TIE-BREAKER LOGIC: Yield if priority is lower, OR if priorities are equal but ID is higher
                should_yield = False
                if blocker.priority > agent.priority:
                    should_yield = True
                elif blocker.priority == agent.priority and blocker.id > agent.id:
                    should_yield = True
                
                if should_yield and blocker.state != "YIELDING":
                    
                    # 1. Force the blocker to surrender
                    blocker.state = "YIELDING"
                    if blocker.original_goal is None:
                        blocker.original_goal = blocker.goal
                    blocker.path = [] 
                    
                    # 2. Create the Winner's Forcefield (Winner's body + next 10 steps)
                    # Increased to 10 to ensure complete clearance of long 1-tile alleys!
                    forcefield = [(agent.row, agent.col)]
                    for pr, pc in agent.path[:10]:
                        forcefield.append((pr, pc))
                    
                    # 3. Blocker calculates escape route
                    park_r, park_c = find_nearest_safe_zone(blocker.row, blocker.col, grid_data, forcefield)
                    
                    if park_r is not None:
                        blocker.set_goal(grid_data, park_r, park_c, forcefield)
                    else:
                        # DETOUR: If no parking, calculate route all the way around the forcefield
                        blocker.set_goal(grid_data, blocker.original_goal[0], blocker.original_goal[1], forcefield)
                        
                    # Blocker inherits priority to push others out of its escape route
                    blocker.priority = agent.priority