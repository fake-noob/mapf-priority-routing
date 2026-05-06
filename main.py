import pygame
import sys
from settings import *
from environment.grid import HospitalGrid
from entities.agent import Agent
from algorithms.deadlock import resolve_deadlocks

def load_scenario(scenario_id, grid_data):
    """6 Rigorous Edge Cases - Mathematically Synchronized for Guaranteed Collisions."""
    swarm = []
    
    if scenario_id == 1:
        # EDGE CASE 1: The Funnel Choke
        print("\n--- Edge Case 1: The Funnel Choke ---")
        swarm = [
            Agent(1, start_col=21, start_row=4, priority=PRIORITY_STANDARD),
            Agent(2, start_col=23, start_row=4, priority=PRIORITY_STANDARD),
            Agent(3, start_col=17, start_row=4, priority=PRIORITY_EMERGENCY)
        ]
        swarm[0].set_goal(grid_data, 4, 2)
        swarm[1].set_goal(grid_data, 5, 2)
        swarm[2].set_goal(grid_data, 21, 10) 

    elif scenario_id == 2:
        # EDGE CASE 2: Overtake Protocol
        print("\n--- Edge Case 2: Overtake Protocol ---")
        swarm = [
            Agent(1, start_col=10, start_row=21, priority=PRIORITY_STANDARD),
            Agent(2, start_col=8, start_row=21, priority=PRIORITY_EMERGENCY)
        ]
        swarm[0].set_goal(grid_data, 13, 28)
        swarm[1].set_goal(grid_data, 13, 28) 

    elif scenario_id == 3:
        # EDGE CASE 3: T-Junction Crash
        print("\n--- Edge Case 3: Synchronized T-Junction Crash ---")
        # Junction is at (Row 4, Col 12). Both agents are exactly 4 steps away.
        swarm = [
            # Blue moving Right (Starts at Col 8)
            Agent(1, start_col=8, start_row=4, priority=PRIORITY_STANDARD),   
            # Red moving Up (Starts at Row 8)
            Agent(2, start_col=12, start_row=8, priority=PRIORITY_EMERGENCY) 
        ]
        swarm[0].set_goal(grid_data, 4, 28) 
        swarm[1].set_goal(grid_data, 4, 2)  

    elif scenario_id == 4:
        # EDGE CASE 4: Vertical Alley Head-to-Head (The Detour)
        print("\n--- Edge Case 4: High vs Low Head-to-Head in 1-Tile Alley ---")
        # Alley is Col 12. They meet exactly in the middle at Row 12.
        swarm = [
            # Blue moving Down (Starts at Row 8)
            Agent(1, start_col=12, start_row=8, priority=PRIORITY_STANDARD),  
            # Red moving Up (Starts at Row 16)
            Agent(2, start_col=12, start_row=16, priority=PRIORITY_EMERGENCY) 
        ]
        swarm[0].set_goal(grid_data, 21, 12)
        swarm[1].set_goal(grid_data, 4, 12)

    elif scenario_id == 5:
        # EDGE CASE 5: Equal Priority Tie-Breaker Crash
        print("\n--- Edge Case 5: Equal Priority Head-to-Head (Tie-Breaker) ---")
        # Bottom Highway (Row 21). Both are Standard priority.
        swarm = [
            # Blue 1 moving Right (Starts at Col 10)
            Agent(1, start_col=10, start_row=21, priority=PRIORITY_STANDARD),
            # Blue 2 moving Left (Starts at Col 18)
            Agent(2, start_col=18, start_row=21, priority=PRIORITY_STANDARD)
        ]
        swarm[0].set_goal(grid_data, 21, 28)
        swarm[1].set_goal(grid_data, 21, 2)

    elif scenario_id == 6:
        # EDGE CASE 6: The 3-Way Gridlock
        print("\n--- Edge Case 6: 3-Way Synchronized Gridlock ---")
        # Junction is at (Row 21, Col 12). All 3 are exactly 4 steps away.
        swarm = [
            # Blue 1 moving Right (Starts at Col 8)
            Agent(1, start_col=8, start_row=21, priority=PRIORITY_STANDARD),
            # Blue 2 moving Left (Starts at Col 16)
            Agent(2, start_col=16, start_row=21, priority=PRIORITY_STANDARD),
            # Red moving Down (Starts at Row 17)
            Agent(3, start_col=12, start_row=17, priority=PRIORITY_EMERGENCY)
        ]
        swarm[0].set_goal(grid_data, 21, 28)
        swarm[1].set_goal(grid_data, 21, 2)
        swarm[2].set_goal(grid_data, 21, 28)

    return swarm

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Micro Swarm Edge Cases (Press 1-6)")
    clock = pygame.time.Clock()
    
    hospital_grid = HospitalGrid()
    
    swarm = []
    scenario_active = False
    running = True
    
    while running:
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: swarm, scenario_active = load_scenario(1, hospital_grid.map_data), True
                elif event.key == pygame.K_2: swarm, scenario_active = load_scenario(2, hospital_grid.map_data), True
                elif event.key == pygame.K_3: swarm, scenario_active = load_scenario(3, hospital_grid.map_data), True
                elif event.key == pygame.K_4: swarm, scenario_active = load_scenario(4, hospital_grid.map_data), True
                elif event.key == pygame.K_5: swarm, scenario_active = load_scenario(5, hospital_grid.map_data), True
                elif event.key == pygame.K_6: swarm, scenario_active = load_scenario(6, hospital_grid.map_data), True

        # --- PHYSICS & STATE LOGIC ---
        if scenario_active:
            resolve_deadlocks(swarm, hospital_grid.map_data)
            occupied_tiles = [(a.row, a.col) for a in swarm]
            
            for robot in swarm:
                dynamic_walls = []
                # 1. Project Forcefields for standard collision avoidance
                for other in swarm:
                    if other.id != robot.id:
                        if other.priority < robot.priority: 
                            dynamic_walls.append((other.row, other.col))
                            if other.path:
                                for pr, pc in other.path[:3]: 
                                    dynamic_walls.append((pr, pc))

                # 2. Movement Execution
                if robot.path:
                    next_step = robot.path[0]
                    if next_step not in occupied_tiles:
                        occupied_tiles.remove((robot.row, robot.col))
                        occupied_tiles.append(next_step)
                        robot.move()
                else:
                    # 3. Wait-State Recovery Protocol
                    if robot.state == "YIELDING":
                        safe = True
                        for other in swarm:
                            if other.priority < robot.priority and other.path:
                                if (robot.row, robot.col) in other.path[:5]: 
                                    safe = False # Danger remains, keep waiting
                        
                        if safe:
                            robot.state = "NORMAL"
                            robot.priority = robot.base_priority
                            if robot.original_goal:
                                robot.goal = robot.original_goal
                                robot.original_goal = None
                                robot.set_goal(hospital_grid.map_data, robot.goal[0], robot.goal[1], dynamic_walls)
                    
                    # 4. Continuous Goal Seeking
                    elif robot.state == "NORMAL" and robot.goal and (robot.row, robot.col) != robot.goal:
                        robot.set_goal(hospital_grid.map_data, robot.goal[0], robot.goal[1], dynamic_walls)
                        
                    # Goal Reached
                    if robot.goal and (robot.row, robot.col) == robot.goal:
                        robot.goal = None 

        # --- RENDERING ---
        hospital_grid.draw(screen)
        for robot in swarm:
            robot.draw(screen)
            
        if not scenario_active:
            font = pygame.font.SysFont(None, 40)
            text = font.render("Press 1, 2, 3, 4, 5, or 6 to Load Scenario", True, (0, 0, 0))
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            bg_rect = text_rect.inflate(20, 20)
            pygame.draw.rect(screen, (255, 255, 255), bg_rect)
            pygame.draw.rect(screen, (0, 0, 0), bg_rect, 2)
            screen.blit(text, text_rect)
            
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()