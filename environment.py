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
        
        # Health bar bounding boxes
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

        # Control States
        self.zero_hp_duration = 0
        self.match_ended = False
        self.is_menu_state = False  # Critical gate to block PPO actions
        
        # --- ADDED FOR PRACTICE MODE TRAJECTORIES ---
        self.current_step = 0
        self.max_steps_per_episode = 1000  # Artificially wraps up the episode after ~1000 actions

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        self.is_menu_state = True
        
        # --- ADDED: Reset the step counter every single episode ---
        self.current_step = 0
        
        # If a match ended, enter our active state machine loop
        if hasattr(self, 'match_ended') and self.match_ended:
            self._handle_post_match_navigation()
            self.match_ended = False

        self.prev_obs = None
        self.zero_hp_duration = 0

        # Safety Gate: Wait until the arena loads and health bars are verified full
        print("[ENV] Active Gate: Waiting for full health bars to register...")
        while True:
            obs = self._get_current_telemetry()
            
            # If we accidentally fell all the way back to character select out of the blue
            if obs[0] < 0.05 and obs[1] < 0.05:
                self._handle_post_match_navigation()
                
            if obs[0] > 0.8 and obs[1] > 0.8:
                print("[ENV] Match fully live! Releasing input block.")
                self.is_menu_state = False
                break
            time.sleep(0.5)

        initial_observation = self._get_current_telemetry()
        return initial_observation, {}

    def _handle_post_match_navigation(self):
        """
        State Machine Navigation: Actively samples the screen to determine if it needs
        to correct the Rematch menu cursor or re-select characters.
        """
        print("[ENV] Match concluded. Entering active screen monitoring...")
        
        # Allow initial time for fatality/win screens to finish before scanning
        time.sleep(10.0)
        
        menu_box = {
            "top": self.monitor_base["top"] + 800,
            "left": self.monitor_base["left"] + 800,
            "width": 320,
            "height": 200
        }

        while True:
            obs = self._get_current_telemetry()
            
            # STATE 1: Match is loading or running (health bars are filling up/present)
            if obs[0] > 0.5 and obs[1] > 0.5:
                print("[ENV] Gameplay UI detected. Exiting menu loop.")
                break
                
            # Grab current menu frame for color analysis
            menu_img = np.array(self.sct.grab(menu_box))
            hsv = cv2.cvtColor(menu_img, cv2.COLOR_BGR2HSV)
            
            # Check for the glowing orange selection lines under options
            # Look at the lower menu region (where MAIN MENU sits)
            lower_glow = hsv[120:, :, :]
            orange_mask_lower = cv2.inRange(lower_glow, np.array([5, 140, 140]), np.array([25, 255, 255]))
            
            # Look at the middle menu region (where CHARACTER SELECT sits)
            mid_glow = hsv[60:120, :, :]
            orange_mask_mid = cv2.inRange(mid_glow, np.array([5, 140, 140]), np.array([25, 255, 255]))

            # STATE 2: We are on the Post-Match Menu, but cursor is stuck on MAIN MENU
            if np.sum(orange_mask_lower) > 400:
                print("[ENV] Menu State: Cursor detected on Main Menu. Tapping UP.")
                self.controller.tap_key("jump") # Move up to Character Select
                time.sleep(0.8)
                continue

            # STATE 3: We are on the Post-Match Menu, but cursor is stuck on CHARACTER SELECT
            elif np.sum(orange_mask_mid) > 400:
                print("[ENV] Menu State: Cursor detected on Character Select. Tapping UP.")
                self.controller.tap_key("jump") # Move up to Rematch
                time.sleep(0.8)
                continue

            # STATE 4: Health bars are gone, and no orange menu glow is found -> We are on the Character Select Screen
            elif obs[0] < 0.05 and obs[1] < 0.05 and np.sum(orange_mask_lower) < 50 and np.sum(orange_mask_mid) < 50:
                print("[ENV] Character Select Screen State Detected! Picking Smoke...")
                time.sleep(1.0)
                self.controller.tap_key("forward") # Shift to Smoke
                time.sleep(0.5)
                self.controller.tap_key("confirm") # Confirm Smoke
                time.sleep(1.5)
                self.controller.tap_key("confirm") # Confirm Kameo
                time.sleep(1.5)
                self.controller.tap_key("confirm") # Confirm Stage
                print("[ENV] Selection submitted. Waiting out the arena loading sequence...")
                time.sleep(8.0)
                break

            # STATE 5: Default assumption - Cursor is safely sitting on REMATCH option
            else:
                print("[ENV] Menu State: Confirming Rematch selection.")
                self.controller.tap_key("confirm")
                time.sleep(2.5)

    def step(self, action):
        if self.is_menu_state:
            return self._get_current_telemetry(), 0.0, False, False, {}

        self._take_action(action)
        time.sleep(0.05) 
        observation = self._get_current_telemetry()
        reward = self._calculate_reward(observation)
        
        # --- ADDED: Increment the step tracking metric ---
        self.current_step += 1
        
        # Check standard HP conditions
        is_zero_hp = bool(observation[0] <= 0.0 or observation[1] <= 0.0)
        
        if is_zero_hp and not self.is_menu_state:
            self.zero_hp_duration += 1
        else:
            self.zero_hp_duration = 0
            
        # 1. Terminated means the match ended naturally via HP going down (Versus Mode)
        terminated = bool(self.zero_hp_duration > 25)
        if terminated:
            print("[ENV] Definite match termination recognized via HP drops.")
            self.is_menu_state = True
            self.match_ended = True

        # 2. Truncated means time/step limit expired (Practice Mode fake round reset)
        truncated = False
        if self.current_step >= self.max_steps_per_episode:
            print(f"[ENV] Trajectory complete ({self.max_steps_per_episode} steps). Reporting episode wrap-up to TensorBoard.")
            truncated = True

        # Return all required parameters back to Stable-Baselines3
        return observation, reward, terminated, truncated, {}

    def _take_action(self, action):
        self.controller.execute(action)

    def _get_current_telemetry(self):
        p1_src = np.array(self.sct.grab(self.p1_box))
        player_hp = self._parse_player_one_health(p1_src)

        p2_src = np.array(self.sct.grab(self.p2_box))
        opponent_hp = self._parse_player_two_health(p2_src)

        return np.array([player_hp, opponent_hp, 0.0, 3.0], dtype=np.float32)

    def _parse_player_one_health(self, p1_slice):
        if p1_slice is None or p1_slice.size == 0: return 0.0
        hsv_p1 = cv2.cvtColor(p1_slice, cv2.COLOR_BGR2HSV)
        center_line = hsv_p1[4, :]
        start_x, end_x = 25, 835
        total_width = float(end_x - start_x)
        
        active_edge = end_x
        for x in range(start_x, end_x):
            if center_line[x][2] > 180 and center_line[x][1] > 80:
                active_edge = x
                break
        return float(np.clip((end_x - active_edge) / total_width, 0.0, 1.0))

    def _parse_player_two_health(self, p2_slice):
        if p2_slice is None or p2_slice.size == 0: return 0.0
        hsv_p2 = cv2.cvtColor(p2_slice, cv2.COLOR_BGR2HSV)
        center_line = hsv_p2[4, :]
        start_x, end_x = 5, 815
        total_width = float(end_x - start_x)
        
        active_edge = start_x
        for x in range(end_x - 1, start_x - 1, -1):
            if center_line[x][2] > 180 and center_line[x][1] > 80:
                active_edge = x
                break
        return float(np.clip((active_edge - start_x) / total_width, 0.0, 1.0))

    def _calculate_reward(self, current_obs):
        if not hasattr(self, 'prev_obs') or self.prev_obs is None:
            self.prev_obs = current_obs
            return 0.0
        player_hp_now, opponent_hp_now, _, _ = current_obs
        player_hp_old, opponent_hp_old, _, _ = self.prev_obs
        reward = ((opponent_hp_old - opponent_hp_now) * 10.0) - ((player_hp_old - player_hp_now) * 15.0)
        self.prev_obs = current_obs
        return float(reward)