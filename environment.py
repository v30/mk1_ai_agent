import gymnasium as gym
from gymnasium import spaces
import numpy as np
import time
import cv2
import mss
from action_space import MK1ActionSpace

class MK1Environment(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(self):
        super().__init__()

        self.controller = MK1ActionSpace()
        self.action_space = spaces.Discrete(self.controller.n)

        self.observation_space = spaces.Box(
            low=np.array([0.0, 0.0, 0.0, 0.0], dtype=np.float32),
            high=np.array([1.0, 1.0, 1.0, 10.0], dtype=np.float32),
            dtype=np.float32
        )

        self.sct = mss.mss()
        self.monitor_base = self.sct.monitors[2]
        
        # Isolated bounding boxes with distinct coordinates
        self.p1_box = {
            "top": self.monitor_base["top"] + 52,
            "left": self.monitor_base["left"] + 40,
            "width": 840,
            "height": 9
        }
        
        self.p2_box = {
            "top": self.monitor_base["top"] + 52,
            "left": self.monitor_base["left"] + 1040,
            "width": 835,
            "height": 9
        }

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        initial_observation = self._get_current_telemetry()
        return initial_observation, {}

    def step(self, action):
        self._take_action(action)
        time.sleep(0.05) 
        observation = self._get_current_telemetry()
        reward = self._calculate_reward(observation)
        terminated = bool(observation[0] <= 0.0 or observation[1] <= 0.0)
        return observation, reward, terminated, False, {}

    def _take_action(self, action):
        self.controller.execute(action)

    def _get_current_telemetry(self):
        # 1. Isolated Pipeline for Player 1 (Smoke) - Depletes Right to Left
        p1_src = np.array(self.sct.grab(self.p1_box))
        player_hp = self._parse_player_one_health(p1_src)

        # 2. Isolated Pipeline for Player 2 (Sub-Zero) - Depletes Left to Right
        p2_src = np.array(self.sct.grab(self.p2_box))
        opponent_hp = self._parse_player_two_health(p2_src)

        return np.array([player_hp, opponent_hp, 0.0, 3.0], dtype=np.float32)

    def _parse_player_one_health(self, p1_slice):
        """
        Entity 1 Pipeline: Player 1 (Smoke)
        Tracks health by finding the brightest glowing tip of the active bar.
        P1 drains from Right to Left.
        """
        if p1_slice is None or p1_slice.size == 0:
            return 1.0

        hsv_p1 = cv2.cvtColor(p1_slice, cv2.COLOR_BGR2HSV)
        center_line = hsv_p1[4, :]
        
        start_x = 25   # Left edge near portrait
        end_x = 835    # Right edge near timer wheel
        total_width = float(end_x - start_x)
        
        # Scan from the left portrait frame inward toward the timer wheel
        # The first highly vibrant, bright pixel we hit is the leading edge of current health
        active_edge = end_x
        for x in range(start_x, end_x):
            v = center_line[x][2] # Value (Brightness)
            s = center_line[x][1] # Saturation
            
            # The active health bar tip glows intensely (V > 180) 
            # while the trailing ghost bar is dull and dark (V < 120)
            if v > 180 and s > 80:
                active_edge = x
                break
                
        # Remaining health extends from that active edge to the right anchor
        active_width = float(end_x - active_edge)
        ratio_p1 = active_width / total_width
        return float(np.clip(ratio_p1, 0.0, 1.0))

    def _parse_player_two_health(self, p2_slice):
        """
        Entity 2 Pipeline: Player 2 (Sub-Zero)
        Tracks health by finding the brightest glowing tip of the active bar.
        P2 drains from Left to Right.
        """
        if p2_slice is None or p2_slice.size == 0:
            return 1.0

        hsv_p2 = cv2.cvtColor(p2_slice, cv2.COLOR_BGR2HSV)
        center_line = hsv_p2[4, :]
        
        start_x = 5    # Left edge near timer wheel
        end_x = 815    # Right edge near portrait
        total_width = float(end_x - start_x)
        
        # Scan from the right portrait frame inward toward the timer wheel
        # The first highly vibrant, bright pixel we hit is the leading edge of current health
        active_edge = start_x
        for x in range(end_x - 1, start_x - 1, -1):
            v = center_line[x][2] # Value (Brightness)
            s = center_line[x][1] # Saturation
            
            # Identify the bright glowing tip of Sub-Zero's draining bar
            if v > 180 and s > 80:
                active_edge = x
                break
                
        # Remaining health extends from the left anchor up to that active edge
        active_width = float(active_edge - start_x)
        ratio_p2 = active_width / total_width
        return float(np.clip(ratio_p2, 0.0, 1.0))

    def _calculate_reward(self, current_obs):
        if not hasattr(self, 'prev_obs'):
            self.prev_obs = current_obs
            return 0.0
        player_hp_now, opponent_hp_now, _, _ = current_obs
        player_hp_old, opponent_hp_old, _, _ = self.prev_obs
        reward = ((opponent_hp_old - opponent_hp_now) * 10.0) - ((player_hp_old - player_hp_now) * 15.0)
        self.prev_obs = current_obs
        return float(reward)