import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time
import cv2
import mss
import win32gui
import ctypes

# Initialize Win32 user32 for virtual keyboard injection later
user32 = ctypes.windll.user32

class MK1AIEv(gym.Env):
    """
    Custom Gymnasium Environment wrapping Mortal Kombat 1.
    This acts as the pipeline interface between PyTorch and the game process.
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super(MK1AIEv, self).__init__()

        # ----------------------------------------------------
        # 1. THE ACTION SPACE (The Agent's Output Contract)
        # ----------------------------------------------------
        # We limit the AI to a simple Discrete list of 6 macro intents.
        # 0: Idle, 1: Move Left, 2: Move Right, 3: Crouch, 4: Attack, 5: Fireball Macro
        self.action_space = spaces.Discrete(6)

        # ----------------------------------------------------
        # 2. THE OBSERVATION SPACE (The Agent's Input Contract)
        # ----------------------------------------------------
        # We pass the AI an array of 4 floats representing game telemetry:
        # [Player_HP, Opponent_HP, Player_Is_Attacking, Distance_Between]
        # We must define the low/high mathematical bounds for this schema.
        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 10.0], dtype=np.float32),
            dtype=np.float32
        )

        # Core system tracking for screen capture
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[2] # Set to your game monitor index

    def reset(self, seed=None, options=None):
        """
        Resets the environment to an initial state for a new episode (match).
        """
        super().reset(seed=seed)
        print(">>> Gym Environment Resetting: Preparing next round...")
        
        # Gather our initial state values
        initial_observation = self._get_current_telemetry()
        info = {} # Supplementary debugging metrics can go here

        return initial_observation, info

    def step(self, action):
        """
        The Core Architectural Loop Step (MDP Transition).
        Takes an action from the AI, applies it, checks results, and returns metrics.
        """
        # 1. Execute the action chosen by the AI
        self._take_action(action)

        # 2. Let the game tick forward slightly to reflect the state change
        time.sleep(0.05) 

        # 3. Retrieve the updated environment state
        observation = self._get_current_telemetry()

        # 4. Compute the Reward Scalar (The Brain's Motivation engine)
        reward = self._calculate_reward(observation)

        # 5. Check if the match is over (Episode Termination Conditions)
        terminated = False
        truncated = False
        
        # Simple terminal mockup: if player or enemy hit zero health
        if observation[0] <= 0.0 or observation[1] <= 0.0:
            terminated = True

        info = {} # Debugging meta info for tensorboard logs

        return observation, reward, terminated, truncated, info

    def _get_current_telemetry(self):
        """
        Processes a live screen capture to generate the dense feature vector.
        Extracts player health and opponent health using verified HSV masks.
        """
        full = np.array(self.sct.grab(self.monitor))
        
        # LOCKED IN: Your custom verified health bar crops
        player_hp_bar   = full[50:63, 40:880]   
        opponent_hp_bar = full[50:63, 1040:1875] 

        # Parse percentages using your precise system-specific baselines
        player_hp = self._parse_health_percentage(player_hp_bar, max_pixels=8998.0)
        opponent_hp = self._parse_health_percentage(opponent_hp_bar, max_pixels=9000.0)

        is_attacking = 0.0
        distance = 3.0  
        
        return np.array([player_hp, opponent_hp, is_attacking, distance], dtype=np.float32)

    def _parse_health_percentage(self, hp_bar_slice, max_pixels):
        """
        Filters the image to isolate the exact yellow/orange health bar color,
        ignoring embedded text and background elements.
        """
        if hp_bar_slice is None or hp_bar_slice.size == 0:
            return 1.0

        # 1. Convert BGR screen capture to HSV color space
        hsv = cv2.cvtColor(hp_bar_slice, cv2.COLOR_BGR2HSV)
        
        # 2. Match your system's exact health bar gradient signatures
        lower_yellow = np.array([10, 60, 200])
        upper_yellow = np.array([25, 110, 255])
        
        # 3. Mask out everything else
        mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # 4. Apply the morphological 2x2 opening to match our calibration pipeline
        kernel = np.ones((2,2), np.uint8)
        clean_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # 5. Count remaining white pixels
        active_pixels = cv2.countNonZero(clean_mask)
        
        # 6. Return normalized float between 0.0 and 1.0
        ratio = active_pixels / max_pixels
        return float(np.clip(ratio, 0.0, 1.0))

    def _take_action(self, action):
        """
        Maps the integer output of the PPO network to physical Windows keystrokes.
        """
        # Mapping our 6 discrete actions to basic test keys 
        # (Using standard hexadecimal Virtual Key codes)
        VK_LEFT  = 0x25
        VK_RIGHT = 0x27
        VK_DOWN  = 0x28
        VK_SEMI  = 0xBA # ; key (assume attack 1)
        VK_W     = 0x57 # W key (assume attack 2)

        if action == 0:   # Idle
            pass
        elif action == 1: # Move Left
            user32.keybd_event(VK_LEFT, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_LEFT, 0, 2, 0)
        elif action == 2: # Move Right
            user32.keybd_event(VK_RIGHT, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_RIGHT, 0, 2, 0)
        elif action == 3: # Crouch
            user32.keybd_event(VK_DOWN, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_DOWN, 0, 2, 0)
        elif action == 4: # Attack 1
            user32.keybd_event(VK_SEMI, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_SEMI, 0, 2, 0)
        elif action == 5: # Special / Fireball macro string!
            user32.keybd_event(VK_DOWN, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_DOWN, 0, 2, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_LEFT, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_LEFT, 0, 2, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_W, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_W, 0, 2, 0)

    def _calculate_reward(self, current_obs):
        """
        Calculates the fitness function scalar based on changes in health states.
        """
        # If this is the very first step of a round, initialize the state memory
        if not hasattr(self, 'prev_obs'):
            self.prev_obs = current_obs
            return 0.0

        player_hp_now, opponent_hp_now, _, _ = current_obs
        player_hp_old, opponent_hp_old, _, _ = self.prev_obs

        # Calculate differences (old health minus current health)
        damage_dealt = opponent_hp_old - opponent_hp_now
        damage_taken = player_hp_old - player_hp_now

        # Reward Architecture: Positive reinforcement for landing hits,
        # steep penalty for failing to defend or taking damage.
        reward = (damage_dealt * 10.0) - (damage_taken * 15.0)

        # Cache current observations as history for the next iteration step
        self.prev_obs = current_obs
        return float(reward)