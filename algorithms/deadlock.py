from settings import *
from environment.rl_env import CustomRLEnv

def resolve_deadlocks(swarm, grid_data, rl_env=None):
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
                    forcefield = [(agent.row, agent.col)]
                    for pr, pc in agent.path[:10]:
                        forcefield.append((pr, pc))
                    
                    # 3. Blocker queries the RL model for the optimal yielding coordinate
                    if rl_env and blocker.policy_net:
                        # Use RL model to find the best yield coordinate
                        park_r, park_c = blocker.select_yield_coordinate(rl_env, swarm)
                        if (park_r, park_c) != (blocker.row, blocker.col):
                            blocker.set_goal(grid_data, park_r, park_c, forcefield)
                        else:
                            # Fallback if RL suggests staying put but we are blocking
                            blocker.set_goal(grid_data, blocker.original_goal[0], blocker.original_goal[1], forcefield)
                    else:
                        # Fallback for when model/env is missing (e.g., baseline tests)
                        park_r, park_c = blocker.original_goal[0], blocker.original_goal[1]
                        blocker.set_goal(grid_data, park_r, park_c, forcefield)
                        
                    # Blocker inherits priority to push others out of its escape route
                    blocker.priority = agent.priority