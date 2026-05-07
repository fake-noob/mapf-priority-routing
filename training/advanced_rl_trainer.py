import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
import json
import time
from datetime import datetime
from collections import defaultdict, deque

from algorithms.rl_policy import YieldDQN
from environment.rl_env import CustomRLEnv
from environment.grid import HospitalGrid
from entities.agent import Agent
from algorithms.deadlock import resolve_deadlocks
from deterministic_evaluation import load_scenario
from settings import *

class AdvancedTrainer:
    """Advanced RL trainer with progressive training and fine-tuning"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.grid = HospitalGrid()
        self.rl_env = CustomRLEnv(self.grid)
        
        # Best parameters from optimization
        self.best_params = {
            'lr': 0.002,
            'epochs_per_scenario': 25,
            'reward_progress': 0.8,
            'reward_collision': -3.0,
            'reward_goal': 8.0,
            'reward_yield': -0.5,
            'epsilon_decay': 0.998
        }
        
        # Advanced training parameters
        self.advanced_params = {
            'progressive_epochs': [20, 30, 40, 50],  # Progressive training stages
            'adaptive_lr': True,
            'curriculum_learning': True,
            'experience_replay': True,
            'target_network_update': 100,
            'batch_size': 64,
            'memory_size': 10000
        }
        
        self.training_log = []
        
    def create_experience_buffer(self):
        """Create experience replay buffer"""
        return deque(maxlen=self.advanced_params['memory_size'])
    
    def calculate_adaptive_reward(self, agent, prev_pos, curr_pos, tick, max_ticks):
        """Advanced reward calculation with time-based weighting"""
        if not agent.goal:
            return 0
        
        # Distance-based reward
        prev_dist = abs(prev_pos[0] - agent.goal[0]) + abs(prev_pos[1] - agent.goal[1])
        curr_dist = abs(curr_pos[0] - agent.goal[0]) + abs(curr_pos[1] - agent.goal[1])
        
        # Base progress reward
        if curr_dist < prev_dist:
            progress_reward = self.best_params['reward_progress']
        elif curr_dist > prev_dist:
            progress_reward = -self.best_params['reward_progress'] * 0.5
        else:
            progress_reward = self.best_params['reward_yield']
        
        # Time-based urgency (higher reward as time progresses)
        time_urgency = tick / max_ticks
        urgency_bonus = progress_reward * (1 + time_urgency * 0.5)
        
        # Goal completion bonus
        if (curr_pos[0], curr_pos[1]) == agent.goal:
            return self.best_params['reward_goal'] + urgency_bonus
        
        return urgency_bonus
    
    def progressive_training_stage(self, policy_net, optimizer, stage, experience_buffer):
        """Execute one stage of progressive training"""
        epochs = self.advanced_params['progressive_epochs'][stage]
        print(f"\n🎯 Training Stage {stage + 1}: {epochs} epochs")
        
        # Adaptive learning rate
        if self.advanced_params['adaptive_lr']:
            lr = self.best_params['lr'] * (0.9 ** stage)  # Decay LR for later stages
            for param_group in optimizer.param_groups:
                param_group['lr'] = lr
            print(f"   Adaptive LR: {lr:.6f}")
        
        stage_results = []
        
        # Curriculum learning: start with easier scenarios
        if self.advanced_params['curriculum_learning']:
            scenario_order = [1, 2, 3, 4, 5, 6] if stage < 2 else [6, 5, 4, 3, 2, 1]
        else:
            scenario_order = list(range(1, 7))
        
        for scenario_id in scenario_order:
            scenario_results = []
            
            for epoch in range(epochs):
                # Load scenario
                swarm = load_scenario(scenario_id, self.grid.map_data, self.device, policy_net)
                
                total_reward = 0
                episode_experiences = []
                
                # Track positions for reward calculation
                prev_positions = [(a.row, a.col) for a in swarm]
                
                for tick in range(150):  # Longer episodes for better learning
                    for agent_idx, agent in enumerate(swarm):
                        if not agent.goal or (agent.row, agent.col) == agent.goal:
                            continue
                        
                        # Get state
                        state, goal_vector = self.rl_env.get_agent_state(agent, swarm)
                        prev_pos = prev_positions[agent_idx]
                        
                        # RL decision for yielding
                        if agent.state == "YIELDING":
                            try:
                                park_r, park_c = agent.select_yield_coordinate(self.rl_env, swarm)
                                
                                # Calculate advanced reward
                                curr_pos = (agent.row, agent.col)
                                reward = self.calculate_adaptive_reward(agent, prev_pos, curr_pos, tick, 150)
                                
                                # Store experience
                                experience = {
                                    'state': state,
                                    'goal_vector': goal_vector,
                                    'reward': reward,
                                    'agent_id': agent.id,
                                    'scenario': scenario_id,
                                    'epoch': epoch,
                                    'tick': tick
                                }
                                episode_experiences.append(experience)
                                
                                # Policy gradient update
                                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                                goal_tensor = torch.FloatTensor(goal_vector).unsqueeze(0).to(self.device)
                                
                                q_values = policy_net(state_tensor, goal_tensor)
                                loss = -torch.log(torch.softmax(q_values, dim=1).mean()) * reward
                                
                                optimizer.zero_grad()
                                loss.backward()
                                torch.nn.utils.clip_grad_norm_(policy_net.parameters(), 1.0)
                                optimizer.step()
                                
                                total_reward += reward
                            except:
                                continue
                    
                    # Update physics
                    resolve_deadlocks(swarm, self.grid.map_data, self.rl_env)
                    
                    # Move agents
                    for robot in swarm:
                        robot.move()
                    
                    # Update previous positions
                    prev_positions = [(a.row, a.col) for a in swarm]
                
                # Store experiences in replay buffer
                if self.advanced_params['experience_replay']:
                    for exp in episode_experiences:
                        experience_buffer.append(exp)
                
                # Calculate metrics
                agents_at_goals = sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)
                completion_rate = agents_at_goals / len(swarm)
                
                epoch_result = {
                    'epoch': epoch,
                    'agents_at_goals': agents_at_goals,
                    'completion_rate': completion_rate,
                    'total_reward': total_reward
                }
                scenario_results.append(epoch_result)
                
                if epoch % 10 == 0:
                    print(f"   Scenario {scenario_id}, Epoch {epoch}: {completion_rate:.1%} completion, Reward: {total_reward:.1f}")
            
            stage_results.append({
                'scenario_id': scenario_id,
                'epochs': scenario_results
            })
        
        return stage_results
    
    def experience_replay_training(self, policy_net, optimizer, experience_buffer, num_batches=50):
        """Train on stored experiences"""
        if len(experience_buffer) < self.advanced_params['batch_size']:
            return
        
        print(f"🔄 Experience Replay Training ({len(experience_buffer)} experiences)")
        
        for batch in range(num_batches):
            # Sample batch
            batch_experiences = random.sample(experience_buffer, min(self.advanced_params['batch_size'], len(experience_buffer)))
            
            batch_loss = 0
            for exp in batch_experiences:
                state_tensor = torch.FloatTensor(exp['state']).unsqueeze(0).to(self.device)
                goal_tensor = torch.FloatTensor(exp['goal_vector']).unsqueeze(0).to(self.device)
                reward = exp['reward']
                
                q_values = policy_net(state_tensor, goal_tensor)
                loss = -torch.log(torch.softmax(q_values, dim=1).mean()) * reward
                batch_loss += loss
            
            # Update on batch
            optimizer.zero_grad()
            batch_loss /= len(batch_experiences)
            batch_loss.backward()
            torch.nn.utils.clip_grad_norm_(policy_net.parameters(), 1.0)
            optimizer.step()
    
    def advanced_training(self):
        """Execute complete advanced training pipeline"""
        print("🚀 STARTING ADVANCED RL TRAINING")
        print(f"Building on optimized parameters: {self.best_params}")
        print(f"Advanced features: Progressive training, Experience replay, Adaptive learning")
        
        start_time = time.time()
        
        # Load best optimized model as starting point
        policy_net = YieldDQN().to(self.device)
        try:
            policy_net.load_state_dict(torch.load('best_trained_yield_dqn.pth'))
            print("✅ Loaded optimized model as starting point")
        except FileNotFoundError:
            print("⚠️ No optimized model found, starting from scratch")
        
        optimizer = optim.Adam(policy_net.parameters(), lr=self.best_params['lr'])
        experience_buffer = self.create_experience_buffer()
        
        # Progressive training stages
        for stage in range(len(self.advanced_params['progressive_epochs'])):
            stage_results = self.progressive_training_stage(policy_net, optimizer, stage, experience_buffer)
            
            # Experience replay between stages
            if self.advanced_params['experience_replay'] and stage > 0:
                self.experience_replay_training(policy_net, optimizer, experience_buffer)
            
            # Evaluate progress
            print(f"\n📊 Stage {stage + 1} Evaluation:")
            self.quick_evaluation(policy_net, stage + 1)
        
        # Final fine-tuning
        print(f"\n🔧 FINAL FINE-TUNING")
        self.fine_tuning(policy_net, optimizer, experience_buffer)
        
        end_time = time.time()
        training_time = end_time - start_time
        
        # Save advanced model
        torch.save(policy_net.state_dict(), 'advanced_trained_yield_dqn.pth')
        print(f"\n✅ Advanced training complete!")
        print(f"   Training time: {training_time/60:.1f} minutes")
        print(f"   Model saved: 'advanced_trained_yield_dqn.pth'")
        
        return policy_net
    
    def fine_tuning(self, policy_net, optimizer, experience_buffer, fine_tune_epochs=20):
        """Fine-tuning phase with focused training"""
        print(f"   Fine-tuning for {fine_tune_epochs} epochs per scenario")
        
        # Lower learning rate for fine-tuning
        for param_group in optimizer.param_groups:
            param_group['lr'] = self.best_params['lr'] * 0.1
        
        for scenario_id in range(1, 7):
            for epoch in range(fine_tune_epochs):
                swarm = load_scenario(scenario_id, self.grid.map_data, self.device, policy_net)
                
                for tick in range(100):
                    for agent in swarm:
                        if agent.state == "YIELDING":
                            try:
                                state, goal_vector = self.rl_env.get_agent_state(agent, swarm)
                                reward = self.calculate_adaptive_reward(agent, (agent.row, agent.col), (agent.row, agent.col), tick, 100)
                                
                                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                                goal_tensor = torch.FloatTensor(goal_vector).unsqueeze(0).to(self.device)
                                
                                q_values = policy_net(state_tensor, goal_tensor)
                                loss = -torch.log(torch.softmax(q_values, dim=1).mean()) * reward * 1.5  # Higher weight in fine-tuning
                                
                                optimizer.zero_grad()
                                loss.backward()
                                optimizer.step()
                            except:
                                continue
                    
                    resolve_deadlocks(swarm, self.grid.map_data, self.rl_env)
                    for robot in swarm:
                        robot.move()
        
        print(f"   Fine-tuning complete")
    
    def quick_evaluation(self, policy_net, stage):
        """Quick evaluation during training"""
        results = {}
        
        for scenario_id in range(1, 4):  # Quick test on first 3 scenarios
            swarm = load_scenario(scenario_id, self.grid.map_data, self.device, policy_net)
            
            agents_at_goals = 0
            for tick in range(100):
                resolve_deadlocks(swarm, self.grid.map_data, self.rl_env)
                for robot in swarm:
                    robot.move()
                agents_at_goals = sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)
                if agents_at_goals == len(swarm):
                    break
            
            results[scenario_id] = agents_at_goals / len(swarm)
        
        avg_success = np.mean(list(results.values()))
        print(f"   Quick eval: {avg_success:.1%} success rate on scenarios 1-3")
        
        return avg_success
    
    def final_evaluation(self, policy_net):
        """Comprehensive final evaluation"""
        print(f"\n🏁 FINAL ADVANCED MODEL EVALUATION")
        
        results = {}
        for scenario_id in range(1, 7):
            print(f"\n--- Advanced Model - Scenario {scenario_id} ---")
            
            swarm = load_scenario(scenario_id, self.grid.map_data, self.device, policy_net)
            
            agents_at_goals = 0
            for tick in range(200):
                resolve_deadlocks(swarm, self.grid.map_data, self.rl_env)
                for robot in swarm:
                    robot.move()
                agents_at_goals = sum(1 for a in swarm if a.goal and (a.row, a.col) == a.goal)
                
                if tick % 50 == 0:
                    print(f"Tick {tick}: {agents_at_goals}/{len(swarm)} agents at goals")
                
                if agents_at_goals == len(swarm):
                    print(f"✅ All agents reached goals at tick {tick}")
                    break
            
            success_rate = agents_at_goals / len(swarm)
            results[scenario_id] = success_rate
            status = "PASS" if success_rate == 1.0 else "FAIL"
            print(f"Scenario {scenario_id}: {status} ({success_rate:.1%})")
        
        overall_success = np.mean(list(results.values()))
        print(f"\n🏆 ADVANCED MODEL RESULTS:")
        print(f"Overall success rate: {overall_success:.1%}")
        print(f"Scenarios passed: {sum(1 for r in results.values() if r == 1.0)}/6")
        
        return results

if __name__ == "__main__":
    trainer = AdvancedTrainer()
    
    # Execute advanced training
    advanced_model = trainer.advanced_training()
    
    # Final evaluation
    final_results = trainer.final_evaluation(advanced_model)
    
    print(f"\n🎯 ADVANCED TRAINING COMPLETE!")
    print(f"📈 Use 'advanced_trained_yield_dqn.pth' for optimal performance")
    print(f"🔍 Compare with previous models to see improvement")
