import time
import random
from settings import *

class TaskDispatcher:
    def __init__(self):
        self.start_time = time.time()
        self.completed_tasks = 0
        self.total_steps_taken = 0
        
        # Valid coordinates based on your 'Labyrinth' map design
        self.parking_nodes = [(4, 2), (6, 2), (18, 2), (20, 2)]
        self.dispenser_nodes = [(10, 28), (12, 28), (14, 28), (16, 28)]

    def assign_tasks(self, swarm, grid_data):
        """Checks for idle robots and assigns them new continuous tasks."""
        for robot in swarm:
            # If the robot is completely idle, has no goal, and isn't currently yielding
            if not robot.path and robot.goal is None and robot.state == "NORMAL":
                
                self.completed_tasks += 1
                
                # Send Emergency robots strictly to Dispensers, Standard to random
                if robot.priority == PRIORITY_EMERGENCY:
                    target = random.choice(self.dispenser_nodes)
                else:
                    # 50/50 chance to go to parking or a dispenser
                    if random.choice([True, False]):
                        target = random.choice(self.parking_nodes)
                    else:
                        target = random.choice(self.dispenser_nodes)
                
                # Assign the new target
                robot.set_goal(grid_data, target[0], target[1])

    def print_metrics(self):
        """Prints live data to the terminal for your report."""
        elapsed_time = round(time.time() - self.start_time, 2)
        print(f"--- LIVE METRICS ---")
        print(f"Elapsed Time (Makespan): {elapsed_time} seconds")
        print(f"Tasks Completed: {self.completed_tasks}")
        print(f"Sum of Costs (Total Steps): {self.total_steps_taken}")
        print("--------------------\n")