import torch
import torch.optim as optim
import torch.nn as nn
import random
import numpy as np
from collections import deque
from algorithms.rl_policy import YieldDQN
from environment.rl_env import CustomRLEnv
from environment.grid import HospitalGrid
from entities.agent import Agent
from settings import *

# Hyperparameters
BATCH_SIZE = 64
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY = 2000
LR = 1e-4
MEMORY_SIZE = 10000
TARGET_UPDATE = 10

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
    
    def push(self, state, goal_vector, action, reward, next_state, next_goal_vector, done):
        self.memory.append((state, goal_vector, action, reward, next_state, next_goal_vector, done))
    
    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)
    
    def __len__(self):
        return len(self.memory)

def select_action(policy_net, state, goal_vector, fov_size, epsilon, device):
    """Epsilon-greedy action selection."""
    if random.random() < epsilon:
        action = random.randint(0, fov_size * fov_size - 1)
    else:
        state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(device)
        goal_tensor = torch.tensor(goal_vector, dtype=torch.float32).unsqueeze(0).to(device)
        with torch.no_grad():
            q_values = policy_net(state_tensor, goal_tensor)
            action = q_values.argmax(dim=1).item()
    return action

def compute_loss(batch, policy_net, target_net, gamma, device):
    """Compute MSE loss for DQN update."""
    states, goal_vectors, actions, rewards, next_states, next_goal_vectors, dones = zip(*batch)
    
    state_batch = torch.tensor(np.array(states), dtype=torch.float32).to(device)
    goal_batch = torch.tensor(np.array(goal_vectors), dtype=torch.float32).to(device)
    action_batch = torch.tensor(actions, dtype=torch.long).to(device)
    reward_batch = torch.tensor(rewards, dtype=torch.float32).to(device)
    next_state_batch = torch.tensor(np.array(next_states), dtype=torch.float32).to(device)
    next_goal_batch = torch.tensor(np.array(next_goal_vectors), dtype=torch.float32).to(device)
    done_batch = torch.tensor(dones, dtype=torch.float32).to(device)
    
    q_values = policy_net(state_batch, goal_batch)
    q_selected = q_values.gather(1, action_batch.unsqueeze(1)).squeeze(1)
    
    with torch.no_grad():
        next_q_values = target_net(next_state_batch, next_goal_batch)
        next_q_max = next_q_values.max(dim=1)[0]
        target_q = reward_batch + gamma * next_q_max * (1 - done_batch)
    
    criterion = nn.MSELoss()
    return criterion(q_selected, target_q)

def train():
    print(f"Training on device: {device}")
    
    policy_net = YieldDQN().to(device)
    target_net = YieldDQN().to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    
    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    memory = ReplayMemory(MEMORY_SIZE)
    
    grid = HospitalGrid()
    env = CustomRLEnv(grid)
    fov_size = env.fov_size
    
    epochs = 1000
    steps_done = 0
    
    agents = [
        Agent(1, 5, 5, priority=PRIORITY_STANDARD, device=device, policy_net=policy_net),
        Agent(2, 15, 15, priority=PRIORITY_EMERGENCY, device=device, policy_net=policy_net)
    ]
    agents[0].set_goal(grid.map_data, 20, 20)
    agents[1].set_goal(grid.map_data, 5, 20)
    
    for epoch in range(epochs):
        for agent in agents:
            if agent.goal is None:
                continue
            
            state, goal_vector = env.get_agent_state(agent, agents)
            epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * np.exp(-steps_done / EPSILON_DECAY)
            action = select_action(policy_net, state, goal_vector, fov_size, epsilon, device)
            
            local_row = action // fov_size
            local_col = action % fov_size
            yield_row = max(0, min(GRID_ROWS - 1, agent.row - env.half_fov + local_row))
            yield_col = max(0, min(GRID_COLS - 1, agent.col - env.half_fov + local_col))
            
            if grid.map_data[yield_row][yield_col] == 1:
                reward = -1.0
                next_state, next_goal_vector = state, goal_vector
                done = False
            else:
                agent.set_goal(grid.map_data, yield_row, yield_col)
                agent.move()
                next_state, next_goal_vector = env.get_agent_state(agent, agents)
                
                new_dist = abs(agent.goal[0] - agent.row) + abs(agent.goal[1] - agent.col)
                reward = -0.1 if new_dist > 0 else 10.0
                done = new_dist == 0
            
            memory.push(state, goal_vector, action, reward, next_state, next_goal_vector, float(done))
            steps_done += 1
        
        if len(memory) > BATCH_SIZE:
            batch = memory.sample(BATCH_SIZE)
            loss = compute_loss(batch, policy_net, target_net, GAMMA, device)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        if epoch % TARGET_UPDATE == 0:
            target_net.load_state_dict(policy_net.state_dict())
            print(f"Epoch {epoch}, Steps {steps_done}, Epsilon {epsilon:.4f}")
            
    torch.save(policy_net.state_dict(), 'trained_yield_dqn.pth')
    print("Training finished and model saved to trained_yield_dqn.pth")

if __name__ == '__main__':
    train()