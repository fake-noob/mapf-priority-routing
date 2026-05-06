import torch
import torch.optim as optim
import torch.nn as nn
import random
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

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def train():
    print(f"Training on device: {device}")
    policy_net = YieldDQN().to(device)
    target_net = YieldDQN().to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    
    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    memory = deque(maxlen=10000)
    
    grid = HospitalGrid()
    env = CustomRLEnv(grid)
    
    epochs = 1000
    steps_done = 0
    
    for epoch in range(epochs):
        # Reset custom environment / agents here
        # E.g., agent1 = Agent(1, ...), agent2 = Agent(2, ...), etc.
        # For this skeleton, we assume a continuous training loop of gathering experiences
        
        # Pseudo-code for memory gathering:
        # 1. State = env.get_agent_state(agent, others)
        # 2. Action = epsilon-greedy action selection
        # 3. Step env (agent runs A* to chosen yield node)
        # 4. Next_State, Reward, Done = env.observe()
        # 5. memory.append((State, Action, Next_State, Reward, Done))
        
        if len(memory) > BATCH_SIZE:
            transitions = random.sample(memory, BATCH_SIZE)
            # Train model...
            
            optimizer.zero_grad()
            # Calculate loss: target_Q vs current_Q
            # loss.backward()
            optimizer.step()
            
        if epoch % 10 == 0:
            target_net.load_state_dict(policy_net.state_dict())
            print(f"Epoch {epoch} completed.")

if __name__ == '__main__':
    train()
