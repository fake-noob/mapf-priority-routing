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
            
            if next_step in occupied_current:
                blocker = occupied_current[next_step]
                
                # TIE-BREAKER LOGIC: Yield if priority is lower, OR if priorities are equal but ID is higher
                should_yield = False
                if blocker.base_priority > agent.base_priority:
                    should_yield = True
                elif blocker.base_priority == agent.base_priority and blocker.id > agent.id:
                    should_yield = True
                
                if should_yield and blocker.state != "YIELDING":
                    
                    # 1. Force the blocker to surrender
                    blocker.state = "YIELDING"
                    if blocker.original_goal is None:
                        blocker.original_goal = blocker.goal
                    blocker.path = [] 
                    
<<<<<<< Updated upstream
                    # 2. Create the Winner's Forcefield (Winner's body + next 10 steps)
                    # Increased to 10 to ensure complete clearance of long 1-tile alleys!
=======
                    # 2. Create the Winner's Forcefield (Winner's body + next 15 steps)
>>>>>>> Stashed changes
                    forcefield = [(agent.row, agent.col)]
                    for pr, pc in agent.path[:15]:
                        forcefield.append((pr, pc))
                    
<<<<<<< Updated upstream
                    # 3. Blocker calculates escape route
                    park_r, park_c = find_nearest_safe_zone(blocker.row, blocker.col, grid_data, forcefield)
                    
                    if park_r is not None:
                        blocker.set_goal(grid_data, park_r, park_c, forcefield)
                    else:
                        # DETOUR: If no parking, calculate route all the way around the forcefield
                        blocker.set_goal(grid_data, blocker.original_goal[0], blocker.original_goal[1], forcefield)
=======
                    # 3. Blocker queries the RL model for the optimal yielding coordinate
                    park_r, park_c = blocker.row, blocker.col
                    if rl_env and blocker.policy_net:
                        park_r, park_c = blocker.select_yield_coordinate(rl_env, swarm)
>>>>>>> Stashed changes
                        
                    # 4. Fallback search if RL gives bad spot
                    if (park_r, park_c) == (blocker.row, blocker.col) or (park_r, park_c) in forcefield:
                        found_escape = False
                        for radius in range(1, 10):
                            for r_adj in range(blocker.row - radius, blocker.row + radius + 1):
                                for c_adj in range(blocker.col - radius, blocker.col + radius + 1):
                                    if 0 <= r_adj < len(grid_data) and 0 <= c_adj < len(grid_data[0]):
                                        if grid_data[r_adj][c_adj] != 1 and (r_adj, c_adj) not in forcefield:
                                            park_r, park_c = r_adj, c_adj
                                            found_escape = True
                                            break
                                if found_escape: break
                            if found_escape: break
                    
                    blocker.set_goal(grid_data, park_r, park_c, forcefield)