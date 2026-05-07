import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import json
import time
from datetime import datetime
from collections import defaultdict

from algorithms.rl_policy import YieldDQN
from environment.rl_env import CustomRLEnv
from environment.grid import HospitalGrid
from entities.agent import Agent
from algorithms.deadlock import resolve_deadlocks
from deterministic_evaluation import load_scenario
from settings import *

class CostBasedEvaluator:
    """Evaluates performance based on path cost and destination completion"""
    
    def __init__(self):
        self.grid = HospitalGrid()
        self.rl_env = CustomRLEnv(self.grid)
        
    def calculate_optimal_cost(self, start, goal):
        """Calculate optimal path cost using Manhattan distance (no obstacles)"""
        return abs(start[0] - goal[0]) + abs(start[1] - goal[1])
    
    def calculate_actual_cost(self, agent, path_history):
        """Calculate actual path cost taken by agent"""
        if len(path_history) < 2:
            return 0
        
        cost = 0
        for i in range(1, len(path_history)):
            prev, curr = path_history[i-1], path_history[i]
            cost += abs(prev[0] - curr[0]) + abs(prev[1] - curr[1])
        
        return cost
    
    def evaluate_scenario_cost(self, swarm, path_histories, max_ticks):
        """
        Evaluate scenario with cost-based metric
        Returns: score (lower is better), details dict
        """
        total_score = 0
        details = {
            'agents': [],
            'total_optimal_cost': 0,
            'total_actual_cost': 0,
            'agents_reached_goal': 0,
            'completion_rate': 0,
            'cost_efficiency': 0,
            'penalty_score': 0
        }
        
        for i, agent in enumerate(swarm):
            if i >= len(path_histories):
                path_histories.append([(agent.row, agent.col)])
            
            agent_history = path_histories[i]
            start_pos = agent_history[0] if agent_history else (agent.row, agent.col)
            current_pos = (agent.row, agent.col)
            
            # Calculate costs
            optimal_cost = self.calculate_optimal_cost(start_pos, agent.goal) if agent.goal else 0
            actual_cost = self.calculate_actual_cost(agent, agent_history)
            
            # Check if reached goal
            reached_goal = agent.goal and current_pos == agent.goal
            
            # Calculate agent score
            if reached_goal:
                # Cost efficiency: actual/optimal (lower is better, 1.0 is perfect)
                cost_ratio = actual_cost / optimal_cost if optimal_cost > 0 else 1.0
                agent_score = cost_ratio
                details['agents_reached_goal'] += 1
            else:
                # Heavy penalty for not reaching destination
                agent_score = 10.0  # Maximum penalty
                details['penalty_score'] += 10.0
            
            agent_details = {
                'id': agent.id,
                'start': start_pos,
                'goal': agent.goal,
                'current': current_pos,
                'optimal_cost': optimal_cost,
                'actual_cost': actual_cost,
                'reached_goal': reached_goal,
                'score': agent_score
            }
            
            details['agents'].append(agent_details)
            details['total_optimal_cost'] += optimal_cost
            details['total_actual_cost'] += actual_cost
            total_score += agent_score
        
        # Calculate aggregate metrics
        details['completion_rate'] = details['agents_reached_goal'] / len(swarm)
        
        if details['total_optimal_cost'] > 0:
            details['cost_efficiency'] = details['total_actual_cost'] / details['total_optimal_cost']
        else:
            details['cost_efficiency'] = 1.0
        
        # Final score (lower is better)
        details['final_score'] = total_score / len(swarm)
        
        return details['final_score'], details

class ParameterOptimizer:
    """Optimizes RL training parameters"""
    
    def __init__(self):
        self.evaluator = CostBasedEvaluator()
        self.results_log = []
        self.best_params = None
        self.best_score = float('inf')
        
        # Parameter combinations to test
        self.param_combinations = [
            {
                'lr': 0.001,
                'epochs_per_scenario': 20,
                'reward_progress': 1.0,
                'reward_collision': -5.0,
                'reward_goal': 10.0,
                'reward_yield': -1.0,
                'epsilon_decay': 0.995
            },
            {
                'lr': 0.0005,
                'epochs_per_scenario': 30,
                'reward_progress': 2.0,
                'reward_collision': -10.0,
                'reward_goal': 15.0,
                'reward_yield': -2.0,
                'epsilon_decay': 0.99
            },
            {
                'lr': 0.0001,
                'epochs_per_scenario': 40,
                'reward_progress': 1.5,
                'reward_collision': -7.5,
                'reward_goal': 12.0,
                'reward_yield': -1.5,
                'epsilon_decay': 0.992
            },
            {
                'lr': 0.002,
                'epochs_per_scenario': 25,
                'reward_progress': 0.8,
                'reward_collision': -3.0,
                'reward_goal': 8.0,
                'reward_yield': -0.5,
                'epsilon_decay': 0.998
            },
            {
                'lr': 0.0008,
                'epochs_per_scenario': 35,
                'reward_progress': 1.2,
                'reward_collision': -6.0,
                'reward_goal': 11.0,
                'reward_yield': -1.2,
                'epsilon_decay': 0.993
            }
        ]
    
    def train_with_params(self, params, iteration):
        """Train model with specific parameter set"""
        print(f"\n{'='*60}")
        print(f"TRAINING ITERATION {iteration+1}")
        print(f"Parameters: {params}")
        print(f"{'='*60}")
        
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        policy_net = YieldDQN().to(device)
        optimizer = optim.Adam(policy_net.parameters(), lr=params['lr'])
        
        grid = HospitalGrid()
        rl_env = CustomRLEnv(grid)
        
        training_log = {
            'iteration': iteration,
            'params': params,
            'training_progress': [],
            'start_time': datetime.now().isoformat()
        }
        
        # Training loop
        for scenario_id in range(1, 7):
            scenario_log = {'scenario_id': scenario_id, 'epochs': []}
            
            for epoch in range(params['epochs_per_scenario']):
                # Load scenario
                swarm = load_scenario(scenario_id, grid.map_data, device, policy_net)
                
                # Track path history for cost calculation
                path_histories = [[] for _ in swarm]
                for i, agent in enumerate(swarm):
                    path_histories[i] = [(agent.row, agent.col)]
                
                total_reward = 0
                
                for tick in range(100):  # Shorter episodes for faster training
                    for agent_idx, agent in enumerate(swarm):
                        if not agent.goal or (agent.row, agent.col) == agent.goal:
                            continue
                        
                        prev_pos = (agent.row, agent.col)
                        prev_dist = abs(agent.row - agent.goal[0]) + abs(agent.col - agent.goal[1])
                        
                        # Get state and action
                        state, goal_vector = rl_env.get_agent_state(agent, swarm)
                        
                        # Use RL model for yielding decisions
                        if agent.state == "YIELDING":
                            try:
                                park_r, park_c = agent.select_yield_coordinate(rl_env, swarm)
                                
                                # Calculate reward based on parameters
                                curr_dist = abs(agent.row - agent.goal[0]) + abs(agent.col - agent.goal[1])
                                
                                # Progress reward
                                if curr_dist < prev_dist:
                                    reward = params['reward_progress']
                                elif curr_dist > prev_dist:
                                    reward = -params['reward_progress'] * 0.5
                                else:
                                    reward = params['reward_yield']  # Yielding penalty
                                
                                # Simple policy update
                                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(device)
                                goal_tensor = torch.FloatTensor(goal_vector).unsqueeze(0).to(device)
                                
                                q_values = policy_net(state_tensor, goal_tensor)
                                loss = -torch.log(torch.softmax(q_values, dim=1).mean()) * reward
                                
                                optimizer.zero_grad()
                                loss.backward()
                                optimizer.step()
                                
                                total_reward += reward
                            except:
                                continue
                        
                        # Check goal completion
                        if agent.goal and (agent.row, agent.col) == agent.goal:
                            total_reward += params['reward_goal']
                    
                    # Update physics
                    resolve_deadlocks(swarm, grid.map_data, rl_env)
                    
                    # Move agents and track paths
                    for robot in swarm:
                        robot.move()
                    
                    # Update path histories
                    for i, agent in enumerate(swarm):
                        path_histories[i].append((agent.row, agent.col))
                
                # Log epoch results
                agents_at_goals = sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)
                epoch_log = {
                    'epoch': epoch,
                    'agents_at_goals': agents_at_goals,
                    'total_reward': total_reward,
                    'completion_rate': agents_at_goals / len(swarm)
                }
                scenario_log['epochs'].append(epoch_log)
            
            training_log['training_progress'].append(scenario_log)
        
        # Evaluate trained model
        print(f"Evaluating trained model...")
        evaluation_score, evaluation_details = self.evaluate_trained_model(policy_net, params)
        
        training_log['evaluation_score'] = evaluation_score
        training_log['evaluation_details'] = evaluation_details
        training_log['end_time'] = datetime.now().isoformat()
        
        # Update best parameters
        if evaluation_score < self.best_score:
            self.best_score = evaluation_score
            self.best_params = params.copy()
            print(f"🏆 NEW BEST SCORE: {evaluation_score:.4f}")
            print(f"🏆 BEST PARAMS: {params}")
            
            # Save best model
            torch.save(policy_net.state_dict(), 'best_trained_yield_dqn.pth')
        
        self.results_log.append(training_log)
        
        return evaluation_score, evaluation_details
    
    def evaluate_trained_model(self, policy_net, params):
        """Evaluate trained model with cost-based metric"""
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        grid = HospitalGrid()
        rl_env = CustomRLEnv(grid)
        
        total_score = 0
        all_details = []
        
        for scenario_id in range(1, 7):
            swarm = load_scenario(scenario_id, grid.map_data, device, policy_net)
            
            # Track path histories
            path_histories = [[] for _ in swarm]
            for i, agent in enumerate(swarm):
                path_histories[i] = [(agent.row, agent.col)]
            
            # Run simulation
            for tick in range(200):
                resolve_deadlocks(swarm, grid.map_data, rl_env)
                for robot in swarm:
                    robot.move()
                
                # Update path histories
                for i, agent in enumerate(swarm):
                    path_histories[i].append((agent.row, agent.col))
                
                # Check completion
                agents_at_goals = sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)
                if agents_at_goals == len(swarm):
                    break
            
            # Evaluate cost
            score, details = self.evaluator.evaluate_scenario_cost(swarm, path_histories, 200)
            details['scenario_id'] = scenario_id
            all_details.append(details)
            total_score += score
        
        avg_score = total_score / 6
        return avg_score, all_details
    
    def run_optimization(self):
        """Run complete parameter optimization"""
        print("🚀 STARTING PARAMETER OPTIMIZATION")
        print(f"Testing {len(self.param_combinations)} parameter combinations")
        print(f"Evaluation metric: Cost-based (lower is better)")
        
        start_time = time.time()
        
        for i, params in enumerate(self.param_combinations):
            score, details = self.train_with_params(params, i)
            print(f"Iteration {i+1} Score: {score:.4f}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate comprehensive report
        self.generate_report(total_time)
        
        return self.best_params, self.best_score
    
    def generate_report(self, total_time):
        """Generate comprehensive training report"""
        report = {
            'optimization_summary': {
                'total_iterations': len(self.param_combinations),
                'best_score': self.best_score,
                'best_parameters': self.best_params,
                'total_time_minutes': total_time / 60,
                'timestamp': datetime.now().isoformat()
            },
            'all_results': self.results_log,
            'parameter_comparison': []
        }
        
        # Add parameter comparison
        for i, result in enumerate(self.results_log):
            report['parameter_comparison'].append({
                'iteration': i,
                'score': result['evaluation_score'],
                'params': result['params'],
                'improvement': result['evaluation_score'] - self.best_score
            })
        
        # Save detailed report
        with open('rl_optimization_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Print summary
        print(f"\n{'='*80}")
        print("🏆 OPTIMIZATION COMPLETE")
        print(f"{'='*80}")
        print(f"Best Score: {self.best_score:.4f}")
        print(f"Best Parameters: {self.best_params}")
        print(f"Total Time: {total_time/60:.1f} minutes")
        print(f"Best model saved as: 'best_trained_yield_dqn.pth'")
        print(f"Detailed report saved as: 'rl_optimization_report.json'")
        
        # Print parameter ranking
        print(f"\n📊 PARAMETER RANKING:")
        sorted_results = sorted(self.results_log, key=lambda x: x['evaluation_score'])
        for i, result in enumerate(sorted_results):
            print(f"{i+1}. Score: {result['evaluation_score']:.4f} | LR: {result['params']['lr']} | Epochs: {result['params']['epochs_per_scenario']}")
        
        return report

if __name__ == "__main__":
    optimizer = ParameterOptimizer()
    best_params, best_score = optimizer.run_optimization()
    
    print(f"\n✅ Optimization complete!")
    print(f"🎯 Use these parameters for best performance:")
    print(f"   {best_params}")
    print(f"📈 Best achieved score: {best_score:.4f}")
    print(f"💾 Best model: 'best_trained_yield_dqn.pth'")
