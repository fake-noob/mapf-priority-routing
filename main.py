import pygame
import sys
import torch
from settings import *
from environment.grid import HospitalGrid
from environment.rl_env import CustomRLEnv
from entities.agent import Agent
from algorithms.deadlock import resolve_deadlocks
from algorithms.rl_policy import YieldDQN
from deterministic_evaluation import load_scenario as load_deterministic_scenario, EvaluationMetrics

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Micro Swarm Edge Cases (Press 1-6)")
    clock = pygame.time.Clock()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    policy_net = YieldDQN().to(device)
    
    # Load advanced model if available
    try:
        policy_net.load_state_dict(torch.load('advanced_trained_yield_dqn.pth'))
        print("✓ Loaded ADVANCED RL model (100% Success Rate)")
    except FileNotFoundError:
        try:
            policy_net.load_state_dict(torch.load('best_trained_yield_dqn.pth'))
            print("✓ Loaded OPTIMIZED RL model (Cost Efficiency: 1.06)")
        except FileNotFoundError:
            try:
                policy_net.load_state_dict(torch.load('trained_yield_dqn.pth'))
                print("✓ Loaded trained RL model")
            except FileNotFoundError:
                print("⚠ No trained model found, using untrained model")
    
    policy_net.eval()
    
    hospital_grid = HospitalGrid()
    rl_env = CustomRLEnv(hospital_grid)
    
    swarm = []
    scenario_active = False
    current_scenario_id = None
    evaluation_metrics = None
    tick_count = 0
    running = True
    
    while running:
        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: 
                    swarm = load_deterministic_scenario(1, hospital_grid.map_data, device, policy_net)
                    scenario_active = True
                    current_scenario_id = 1
                    evaluation_metrics = EvaluationMetrics()
                    tick_count = 0
                    print("=== SCENARIO 1: Funnel Conga Line ===")
                elif event.key == pygame.K_2: 
                    swarm = load_deterministic_scenario(2, hospital_grid.map_data, device, policy_net)
                    scenario_active = True
                    current_scenario_id = 2
                    evaluation_metrics = EvaluationMetrics()
                    tick_count = 0
                    print("=== SCENARIO 2: Blind Switchback Meet ===")
                elif event.key == pygame.K_3: 
                    swarm = load_deterministic_scenario(3, hospital_grid.map_data, device, policy_net)
                    scenario_active = True
                    current_scenario_id = 3
                    evaluation_metrics = EvaluationMetrics()
                    tick_count = 0
                    print("=== SCENARIO 3: Professor's Trap ===")
                elif event.key == pygame.K_4: 
                    swarm = load_deterministic_scenario(4, hospital_grid.map_data, device, policy_net)
                    scenario_active = True
                    current_scenario_id = 4
                    evaluation_metrics = EvaluationMetrics()
                    tick_count = 0
                    print("=== SCENARIO 4: Crossroads Ambush ===")
                elif event.key == pygame.K_5: 
                    swarm = load_deterministic_scenario(5, hospital_grid.map_data, device, policy_net)
                    scenario_active = True
                    current_scenario_id = 5
                    evaluation_metrics = EvaluationMetrics()
                    tick_count = 0
                    print("=== SCENARIO 5: Parking Lot Deadlock ===")
                elif event.key == pygame.K_6: 
                    swarm = load_deterministic_scenario(6, hospital_grid.map_data, device, policy_net)
                    scenario_active = True
                    current_scenario_id = 6
                    evaluation_metrics = EvaluationMetrics()
                    tick_count = 0
                    print("=== SCENARIO 6: Dispenser Bottleneck ===")

        # --- PHYSICS & STATE LOGIC ---
        if scenario_active:
            tick_count += 1
            
            # Update evaluation metrics
            if evaluation_metrics:
                evaluation_metrics.update(swarm)
                
                # Check for PASS/FAIL conditions every 10 ticks
                if tick_count % 10 == 0:
                    result, reason = evaluation_metrics.evaluate_scenario(swarm)
                    if result == "FAIL":
                        print(f"FAIL at tick {tick_count}: {reason}")
                    elif tick_count % 50 == 0:  # Progress update
                        goals_reached = sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)
                        print(f"Tick {tick_count}: {goals_reached}/{len(swarm)} agents at goals")
            
            resolve_deadlocks(swarm, hospital_grid.map_data, rl_env)
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
            
        # Check for scenario completion
        if scenario_active and evaluation_metrics and tick_count > 0:
            all_at_goals = all(robot.goal and (robot.row, robot.col) == robot.goal for robot in swarm)
            
            if all_at_goals or tick_count >= 500:  # Max timeout
                result, reason = evaluation_metrics.evaluate_scenario(swarm)
                print(f"\n{'='*50}")
                print(f"SCENARIO {current_scenario_id} RESULT: {result}")
                if reason:
                    print(f"Reason: {reason}")
                print(f"Completed in {tick_count} ticks")
                print(f"{'='*50}")
                
                # Reset scenario
                scenario_active = False
                current_scenario_id = None
                evaluation_metrics = None
                swarm = []
            
        if not scenario_active:
            font = pygame.font.SysFont(None, 32)
            lines = [
                "Deterministic MAPF Evaluation Suite",
                "",
                "1: Funnel Conga Line",
                "2: Blind Switchback Meet", 
                "3: Professor's Trap",
                "4: Crossroads Ambush",
                "5: Parking Lot Deadlock",
                "6: Dispenser Bottleneck",
                "",
                "Press 1-6 to load scenarios"
            ]
            
            y_offset = SCREEN_HEIGHT//2 - len(lines) * 12
            for i, line in enumerate(lines):
                color = (255, 255, 255) if i == 0 else (200, 200, 200)
                text = font.render(line, True, color)
                text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y_offset + i * 25))
                screen.blit(text, text_rect)
            
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()