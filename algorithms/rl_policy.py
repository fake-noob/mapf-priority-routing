import torch
import torch.nn as nn
import torch.nn.functional as F

class YieldDQN(nn.Module):
    def __init__(self, fov_size=7, grid_channels=3):
        super(YieldDQN, self).__init__()
        self.fov_size = fov_size
        
        # Convolutional layers to process the localized FOV
        self.conv1 = nn.Conv2d(grid_channels, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        
        self.flatten_size = 64 * fov_size * fov_size
        
        # Fully connected layers
        self.fc1 = nn.Linear(self.flatten_size + 2, 256) # +2 for goal vector (dx, dy)
        self.fc2 = nn.Linear(256, fov_size * fov_size)   # Output: Q-value for each coordinate in FOV

    def forward(self, fov_grid, goal_vector):
        x = F.relu(self.conv1(fov_grid))
        x = F.relu(self.conv2(x))
        x = x.view(-1, self.flatten_size)
        
        x = torch.cat((x, goal_vector), dim=1)
        x = F.relu(self.fc1(x))
        q_values = self.fc2(x)
        
        return q_values
