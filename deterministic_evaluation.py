"""
Deterministic MAPF Evaluation Suite
Mathematically synchronized edge cases for thesis evaluation
Analyzes grid.py to ensure exact coordinate placement on valid paths
"""

import pygame
from settings import *
from entities.agent import Agent
from algorithms.pathfinding import a_star_search

class EvaluationMetrics:
    """Tracks PASS/FAIL metrics for deterministic evaluation"""
    
    def __init__(self):
        self.reset_metrics()
        
    def reset_metrics(self):
        """Reset all metrics for new scenario"""
        self.start_time = pygame.time.get_ticks()
        self.tick_count = 0
        self.agent_static_ticks = {}  # agent_id -> static_count
        self.agent_goal_reached = {}  # agent_id -> bool
        self.path_oscillation_count = {}  # agent_id -> oscillation_count
        self.last_path_lengths = {}  # agent_id -> last_path_length
        self.position_history = {}  # agent_id -> list of positions
        self.position_swap_detected = False
        self.livelock_detected = False
        
    def update(self, agents):
        """Update metrics for current tick"""
        self.tick_count += 1
        
        for agent in agents:
            # Track goal achievement
            if agent.goal and (agent.row, agent.col) == agent.goal:
                self.agent_goal_reached[agent.id] = True
                
            # Track static agents (not moving and not at goal)
            current_path_length = len(agent.path) if agent.path else 0
            
            if agent.id not in self.agent_static_ticks:
                self.agent_static_ticks[agent.id] = 0
                self.path_oscillation_count[agent.id] = 0
                self.last_path_lengths[agent.id] = current_path_length
                
            # Check if agent is static (empty path) and not at goal
            if current_path_length == 0 and not self.agent_goal_reached.get(agent.id, False):
                self.agent_static_ticks[agent.id] += 1
            else:
                self.agent_static_ticks[agent.id] = 0
                
            # Check for path oscillation (rapid empty/full cycling)
            if (self.last_path_lengths[agent.id] == 0 and current_path_length > 0) or \
               (self.last_path_lengths[agent.id] > 0 and current_path_length == 0):
                self.path_oscillation_count[agent.id] += 1
                
            self.last_path_lengths[agent.id] = current_path_length
            
            # Update position history
            if agent.id not in self.position_history:
                self.position_history[agent.id] = []
            self.position_history[agent.id].append((agent.row, agent.col))
            
        # Check for position swapping (illegal movement)
        if len(agents) >= 2:
            for i in range(len(agents)):
                for j in range(i + 1, len(agents)):
                    # This would need previous positions to detect properly
                    # For now, we'll detect if agents are at each other's previous positions
                    pass
                    
    def evaluate_scenario(self, swarm):
        """
        Fair evaluation: FAIL if any agent doesn't reach destination or system crashes
        PASS: ONLY if ALL agents reach their exact goals
        """
        # Check for livelock (position oscillation)
        for agent_id, positions in self.position_history.items():
            if len(positions) >= 4:
                recent = positions[-4:]
                if recent[0] == recent[2] and recent[1] == recent[3]:
                    return "FAIL", f"Agent {agent_id} in livelock (position oscillation)"
        
        # Check for static agents with empty paths
        for agent in swarm:
            if agent.goal and (agent.row, agent.col) != agent.goal:
                if not agent.path and self.agent_static_ticks[agent.id] > 50:
                    return "FAIL", f"Agent {agent.id} static >50 ticks without path"
        
        # Check for illegal position swaps
        if len(self.position_history) >= 2:
            current_positions = {(a.id, (a.row, a.col)) for a in swarm}
            prev_positions = set()
            for agent_id, positions in self.position_history.items():
                if len(positions) >= 2:
                    prev_positions.add((agent_id, positions[-2]))
            
            # Detect if agents swapped positions
            for (id1, pos1), (id2, pos2) in [(a, b) for a in prev_positions for b in prev_positions if a[0] < b[0]]:
                if (id1, pos2) in current_positions and (id2, pos1) in current_positions:
                    return "FAIL", f"Illegal position swap between agents {id1} and {id2}"
        
        # FAIR EVALUATION: FAIL if any agent hasn't reached its exact goal
        agents_at_goals = 0
        for agent in swarm:
            if agent.goal and (agent.row, agent.col) == agent.goal:
                agents_at_goals += 1
            else:
                return "FAIL", f"Agent {agent.id} failed to reach destination at ({agent.row}, {agent.col}), goal was {agent.goal}"
        
        # Only PASS if ALL agents reached their exact goals
        if agents_at_goals == len(swarm):
            return "PASS", f"All {len(swarm)} agents reached their exact goals"
        
        return "FAIL", f"Only {agents_at_goals}/{len(swarm)} agents reached goals"

def validate_coordinates(map_data, coords, name):
    """Validate that coordinates are on valid paths (not walls)"""
    for row, col in coords:
        if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
            raise ValueError(f"{name}: Coordinate ({row}, {col}) out of bounds")
        if map_data[row][col] == 1:
            raise ValueError(f"{name}: Coordinate ({row}, {col}) is on a wall")
    print(f"✓ {name}: All coordinates validated")

def load_scenario(scenario_id, map_data, device=None, policy_net=None):
    """
    Load deterministic edge cases with mathematically synchronized collision points
    Args:
        scenario_id: 1-6 for the six scenarios
        map_data: 2D grid array from HospitalGrid
        device: PyTorch device for RL agents
        policy_net: Neural network policy for RL agents
    Returns:
        swarm: List of 3 Agent objects
    """
    
    if scenario_id == 1:
        return _create_funnel_conga_line(map_data, device, policy_net)
    elif scenario_id == 2:
        return _create_blind_switchback_meet(map_data, device, policy_net)
    elif scenario_id == 3:
        return _create_professors_trap(map_data, device, policy_net)
    elif scenario_id == 4:
        return _create_crossroads_ambush(map_data, device, policy_net)
    elif scenario_id == 5:
        return _create_parking_lot_deadlock(map_data, device, policy_net)
    elif scenario_id == 6:
        return _create_dispenser_bottleneck(map_data, device, policy_net)
    else:
        raise ValueError(f"Invalid scenario_id: {scenario_id}. Use 1-6.")

def _create_funnel_conga_line(map_data, device, policy_net):
    """
    SCENARIO 1: The Funnel Conga Line
    Red (Emergency) moves Left in 1-tile corridor
    Blue 1 & 2 move Right in same corridor
    Collision point: (4, 20) - center of 1-wide choke
    """
    print("\n=== SCENARIO 1: Funnel Conga Line ===")
    
    # Validate all spawn and goal coordinates (using actual grid layout)
    spawn_coords = [(4, 24), (4, 4), (4, 6)]  # Red, Blue1, Blue2
    goal_coords = [(4, 4), (4, 24), (4, 22)]   # Red, Blue1, Blue2
    validate_coordinates(map_data, spawn_coords, "Funnel Conga Spawns")
    validate_coordinates(map_data, goal_coords, "Funnel Conga Goals")
    
    swarm = [
        Agent(3, start_col=24, start_row=4, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net),  # Red
        Agent(1, start_col=4, start_row=4, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),   # Blue 1
        Agent(2, start_col=6, start_row=4, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),   # Blue 2
    ]
    
    # Set goals - Red moves LEFT, Blues move RIGHT
    swarm[0].set_goal(map_data, 4, 4)   # Red: (4,24) -> (4,4)
    swarm[1].set_goal(map_data, 4, 24)  # Blue1: (4,4) -> (4,24)
    swarm[2].set_goal(map_data, 4, 22)  # Blue2: (4,6) -> (4,22)
    
    print("Red (Emergency): (4,24) -> (4,4) [LEFT]")
    print("Blue 1 (Standard): (4,4) -> (4,24) [RIGHT]")
    print("Blue 2 (Standard): (4,6) -> (4,22) [RIGHT]")
    print("Expected collision at: (4,20) center of 1-wide choke")
    
    return swarm

def _create_blind_switchback_meet(map_data, device, policy_net):
    """
    SCENARIO 2: The Blind Switchback Meet
    Red and Blue meet in middle corridor
    """
    print("\n=== SCENARIO 2: Blind Switchback Meet ===")
    
    # Use validated coordinates from middle corridor area
    spawn_coords = [(12, 6), (12, 14), (13, 10)]  # Red, Blue1, Blue2
    goal_coords = [(12, 14), (12, 6), (13, 10)]   # Red, Blue1, Blue2
    validate_coordinates(map_data, spawn_coords, "Blind Switchback Spawns")
    validate_coordinates(map_data, goal_coords, "Blind Switchback Goals")
    
    swarm = [
        Agent(3, start_col=6, start_row=12, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net),   # Red
        Agent(1, start_col=14, start_row=12, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 1
        Agent(2, start_col=10, start_row=13, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 2
    ]
    
    # Set goals - Red moves RIGHT, Blue1 moves LEFT, Blue2 waits
    swarm[0].set_goal(map_data, 12, 14)  # Red: (12,6) -> (12,14) [RIGHT]
    swarm[1].set_goal(map_data, 12, 6)   # Blue1: (12,14) -> (12,6) [LEFT]
    swarm[2].set_goal(map_data, 13, 10)  # Blue2: (13,10) -> (13,10) [Already at goal]
    
    print("Red (Emergency): (12,6) -> (12,14) [RIGHT]")
    print("Blue 1 (Standard): (12,14) -> (12,6) [LEFT]")
    print("Blue 2 (Standard): (13,10) -> (13,10) [At goal]")
    print("Expected meeting at: (12,10) - middle corridor")
    
    return swarm

def _create_professors_trap(map_data, device, policy_net):
    """
    SCENARIO 3: The Professor's Trap (Permanent Junction Blockage)
    Blue moves down alley, Red moves up same alley
    Red's goal is exactly on T-junction at (13, 12)
    """
    print("\n=== SCENARIO 3: Professor's Trap ===")
    
    # Validate coordinates for T-junction trap
    spawn_coords = [(21, 12), (5, 12), (13, 12)]  # Red, Blue1, Blue2
    goal_coords = [(13, 12), (21, 12), (13, 12)]   # Red, Blue1, Blue2
    validate_coordinates(map_data, spawn_coords, "Professor's Trap Spawns")
    validate_coordinates(map_data, goal_coords, "Professor's Trap Goals")
    
    swarm = [
        Agent(3, start_col=12, start_row=21, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net),  # Red
        Agent(1, start_col=12, start_row=5, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),   # Blue 1
        Agent(2, start_col=12, start_row=13, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 2
    ]
    
    # Set goals - Red moves UP to T-junction, Blue1 moves DOWN, Blue2 waits
    swarm[0].set_goal(map_data, 13, 12)  # Red: (21,12) -> (13,12) [UP] - Permanent blockage
    swarm[1].set_goal(map_data, 21, 12)  # Blue1: (5,12) -> (21,12) [DOWN]
    swarm[2].set_goal(map_data, 13, 12)  # Blue2: (13,12) -> (13,12) [Already at goal]
    
    print("Red (Emergency): (21,12) -> (13,12) [UP] - Permanent T-junction blockage")
    print("Blue 1 (Standard): (5,12) -> (21,12) [DOWN] - Must yield to Red")
    print("Blue 2 (Standard): (13,12) -> (13,12) [At goal]")
    print("Expected: Red blocks T-junction, Blue1 backs to side alley")
    
    return swarm

def _create_crossroads_ambush(map_data, device, policy_net):
    """
    SCENARIO 4: Crossroads Ambush
    Multiple agents converge on a central intersection
    Emergency agent must force standard agents to yield
    """
    print("\n=== SCENARIO 4: Crossroads Ambush ===")
    
    # Validate coordinates for crossroads intersection (using middle corridor)
    spawn_coords = [(13, 6), (13, 14), (12, 10)]  # Red, Blue1, Blue2
    goal_coords = [(13, 14), (13, 6), (14, 10)]   # Red, Blue1, Blue2
    validate_coordinates(map_data, spawn_coords, "Crossroads Ambush Spawns")
    validate_coordinates(map_data, goal_coords, "Crossroads Ambush Goals")
    
    swarm = [
        Agent(3, start_col=6, start_row=13, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net),   # Red
        Agent(1, start_col=14, start_row=13, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 1
        Agent(2, start_col=10, start_row=12, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 2
    ]
    
    # Set goals - All converge on center area
    swarm[0].set_goal(map_data, 13, 14)  # Red: (13,6) -> (13,14) [RIGHT]
    swarm[1].set_goal(map_data, 13, 6)   # Blue1: (13,14) -> (13,6) [LEFT]
    swarm[2].set_goal(map_data, 14, 10)  # Blue2: (12,10) -> (14,10) [DOWN]
    
    print("Red (Emergency): (13,6) -> (13,14) [RIGHT]")
    print("Blue 1 (Standard): (13,14) -> (13,6) [LEFT]")
    print("Blue 2 (Standard): (12,10) -> (14,10) [DOWN]")
    print("Expected: Red forces yielding at crossroads intersection")
    
    return swarm

def _create_parking_lot_deadlock(map_data, device, policy_net):
    """
    SCENARIO 5: Parking Lot Deadlock
    Agents trapped in parking bay area with limited escape routes
    Tests priority-based escape resolution
    """
    print("\n=== SCENARIO 5: Parking Lot Deadlock ===")
    
    # Validate coordinates for parking bay area (using left staging area)
    spawn_coords = [(5, 2), (10, 2), (15, 2)]  # Red, Blue1, Blue2
    goal_coords = [(15, 3), (5, 3), (10, 3)]   # Red, Blue1, Blue2
    validate_coordinates(map_data, spawn_coords, "Parking Lot Deadlock Spawns")
    validate_coordinates(map_data, goal_coords, "Parking Lot Deadlock Goals")
    
    swarm = [
        Agent(3, start_col=2, start_row=5, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net),   # Red
        Agent(1, start_col=2, start_row=10, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 1
        Agent(2, start_col=2, start_row=15, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 2
    ]
    
    # Set goals - Create circular dependency in parking area
    swarm[0].set_goal(map_data, 15, 3)  # Red: (5,2) -> (15,3) [DOWN & RIGHT]
    swarm[1].set_goal(map_data, 5, 3)   # Blue1: (10,2) -> (5,3) [UP & RIGHT]
    swarm[2].set_goal(map_data, 10, 3)  # Blue2: (15,2) -> (10,3) [UP]
    
    print("Red (Emergency): (5,2) -> (15,3) [DOWN & RIGHT]")
    print("Blue 1 (Standard): (10,2) -> (5,3) [UP & RIGHT]")
    print("Blue 2 (Standard): (15,2) -> (10,3) [UP]")
    print("Expected: Priority-based escape from parking deadlock")
    
    return swarm

def _create_dispenser_bottleneck(map_data, device, policy_net):
    """
    SCENARIO 6: Bottom Highway Convergence
    Agents converge on bottom corridor with priority-based resolution
    """
    print("\n=== SCENARIO 6: Bottom Highway Convergence ===")
    
    # Validate coordinates for bottom highway area
    spawn_coords = [(21, 10), (21, 20), (21, 15)]  # Red, Blue1, Blue2
    goal_coords = [(21, 20), (21, 10), (21, 15)]   # Red, Blue1, Blue2
    validate_coordinates(map_data, spawn_coords, "Bottom Highway Convergence Spawns")
    validate_coordinates(map_data, goal_coords, "Bottom Highway Convergence Goals")
    
    swarm = [
        Agent(3, start_col=10, start_row=21, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net),  # Red
        Agent(1, start_col=20, start_row=21, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 1
        Agent(2, start_col=15, start_row=21, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),  # Blue 2
    ]
    
    # Set goals - All converge on center of bottom highway
    swarm[0].set_goal(map_data, 21, 20)  # Red: (21,10) -> (21,20) [RIGHT]
    swarm[1].set_goal(map_data, 21, 10)  # Blue1: (21,20) -> (21,10) [LEFT]
    swarm[2].set_goal(map_data, 21, 15)  # Blue2: (21,15) -> (21,15) [Already at goal]
    
    print("Red (Emergency): (21,10) -> (21,20) [RIGHT]")
    print("Blue 1 (Standard): (21,20) -> (21,10) [LEFT]")
    print("Blue 2 (Standard): (21,15) -> (21,15) [At goal]")
    print("Expected: Emergency forces yielding on bottom highway")
    
    return swarm

def run_deterministic_evaluation(scenario_id, max_ticks=500):
    """
    Run a complete deterministic evaluation with PASS/FAIL metrics
    Args:
        scenario_id: 1-6 for the six scenarios
        max_ticks: Maximum simulation ticks before timeout
    Returns:
        result: "PASS" or "FAIL"
        metrics: EvaluationMetrics object with detailed data
    """
    print(f"\n{'='*60}")
    print(f"STARTING DETERMINISTIC EVALUATION - SCENARIO {scenario_id}")
    print(f"{'='*60}")
    
    try:
        # Initialize environment
        from environment.grid import HospitalGrid
        from environment.rl_env import CustomRLEnv
        from algorithms.rl_policy import YieldDQN
        import torch
        
        grid = HospitalGrid()
        rl_env = CustomRLEnv(grid)
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        policy_net = YieldDQN().to(device)
        
        # Load best optimized model if available
        try:
            policy_net.load_state_dict(torch.load('best_trained_yield_dqn.pth'))
            print("✓ Using OPTIMIZED RL model (Cost Efficiency: 1.06)")
        except FileNotFoundError:
            try:
                policy_net.load_state_dict(torch.load('trained_yield_dqn.pth'))
                print("✓ Using trained RL model")
            except FileNotFoundError:
                print("⚠ No trained model found, using untrained model")
        
        policy_net.eval()
        
        # Load scenario
        swarm = load_scenario(scenario_id, grid.map_data, device, policy_net)
        
        # Initialize metrics
        metrics = EvaluationMetrics()
        
        print(f"Starting simulation with {len(swarm)} agents...")
        print(f"Max ticks: {max_ticks}")
        
        # Run simulation
        for tick in range(max_ticks):
            # Update metrics
            metrics.update(swarm)
            
            # Check for early completion
            all_at_goals = all(agent.goal and (agent.row, agent.col) == agent.goal for agent in swarm)
            if all_at_goals:
                print(f"All agents reached goals at tick {tick}")
                break
            
            # Physics update - CRASH DETECTION
            try:
                from algorithms.deadlock import resolve_deadlocks
                resolve_deadlocks(swarm, grid.map_data, rl_env)
            except Exception as e:
                print(f"CRASH in deadlock resolution at tick {tick}: {e}")
                return "FAIL", f"System crash: {e}"
            
            occupied_tiles = [(a.row, a.col) for a in swarm]
            
            for robot in swarm:
                # Dynamic wall projection
                dynamic_walls = []
                for other in swarm:
                    if other.id != robot.id:
                        if other.priority < robot.priority:
                            dynamic_walls.append((other.row, other.col))
                
                # Move robot - CRASH DETECTION
                try:
                    robot.move()  # Agent.move() takes no arguments
                except Exception as e:
                    print(f"CRASH in robot movement at tick {tick}: {e}")
                    return "FAIL", f"System crash: {e}"
                
                # Goal reached
                if robot.goal and (robot.row, robot.col) == robot.goal:
                    robot.goal = None
        
        # Final evaluation
        result, reason = metrics.evaluate_scenario(swarm)
        
        print(f"\n{'='*60}")
        print(f"EVALUATION RESULT: {result}")
        print(f"Total ticks: {tick + 1}")
        print(f"Agents at goals: {sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)}/{len(swarm)}")
        print(f"Reason: {reason}")
        print(f"{'='*60}")
        
        return result, metrics
        
    except Exception as e:
        print(f"CRASH during scenario setup: {e}")
        return "FAIL", f"System crash during setup: {e}"

if __name__ == "__main__":
    """Run all deterministic evaluations"""
    print("Running Deterministic MAPF Evaluation Suite")
    
    results = {}
    for scenario_id in [1, 2, 3, 4, 5, 6]:
        result, metrics = run_deterministic_evaluation(scenario_id)
        results[scenario_id] = result
        
    print(f"\n{'='*60}")
    print("FINAL RESULTS SUMMARY")
    print(f"{'='*60}")
    for scenario_id, result in results.items():
        print(f"Scenario {scenario_id}: {result}")
        
    pass_count = sum(1 for r in results.values() if r == "PASS")
    print(f"\nOverall: {pass_count}/6 scenarios PASSED")
