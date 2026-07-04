import sys
from pathlib import Path

# Add the root to the path first!
sys.path.append(str(Path(__file__).parent.parent))

# Now you can safely import your modules
import importlib
import environment
import action_space
from environment import MK1Environment
import time

# Force reload
importlib.reload(action_space)
importlib.reload(environment)

env = MK1Environment()

print("Testing Action: Front Punch (Action 5) in 3 seconds...")
time.sleep(3)

# Test calling the action through the environment
time.sleep(1.0) # Give it a full second to breathe
env.step(0)     # Send a NO_OP first to clear state
time.sleep(0.5) 
env.step(5)     # Now try the punch