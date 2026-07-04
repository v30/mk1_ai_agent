import os
import mss
import numpy as np
import cv2
import time
from pathlib import Path

# Set up paths to mimic your environment structure
TOOLS_DIR = Path(__file__).parent
ROOT_DIR = TOOLS_DIR.parent

sct = mss.MSS()
monitor = sct.monitors[2] 

def parse_health_percentage(hp_bar_slice, max_pixels):
    if hp_bar_slice is None or hp_bar_slice.size == 0:
        return 1.0

    # 1. Convert to HSV
    hsv = cv2.cvtColor(hp_bar_slice, cv2.COLOR_BGR2HSV)
    
    # 2. Match your system's exact calibrated signature
    lower_yellow = np.array([10, 60, 200])
    upper_yellow = np.array([25, 110, 255])
    
    # 3. Mask out noise
    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    
    # 4. Apply the morphological cleanup kernel
    kernel = np.ones((2,2), np.uint8)
    clean_mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # 5. Calculate percentage based on your final numbers
    active_pixels = cv2.countNonZero(clean_mask)
    ratio = active_pixels / max_pixels
    return float(np.clip(ratio, 0.0, 1.0))

print("=======================================================")
print(">>> LIVE HEALTH TELEMETRY TESTER")
print(">>> Press CTRL+C in this terminal to stop the test.")
print("=======================================================")
print("Starting live feedback loop in 3 seconds...")
time.sleep(3.0)

try:
    while True:
        # Snap current frame
        full = np.array(sct.grab(monitor))
        
        # Crop utilizing your verified dimensions
        player_hp_bar   = full[50:63, 40:880]   
        opponent_hp_bar = full[50:63, 1040:1875] 

        # Calculate percentages
        player_hp = parse_health_percentage(player_hp_bar, max_pixels=8998.0)
        opponent_hp = parse_health_percentage(opponent_hp_bar, max_pixels=9000.0)

        # Print outputs cleanly on a single refreshing line
        print(f"Player HP: {player_hp*100:6.1f}% | Opponent HP: {opponent_hp*100:6.1f}%", end="\r", flush=True)
        
        # Limit loop speed to roughly 30 FPS to save CPU cycles during tests
        time.sleep(1.0 / 30.0)

except KeyboardInterrupt:
    print("\n\n>>> Telemetry test stopped successfully!")