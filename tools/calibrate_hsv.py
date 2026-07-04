import os
import mss
import numpy as np
import cv2
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
ROOT_DIR = TOOLS_DIR.parent
DEBUG_DIR = ROOT_DIR / "debug_images"

os.makedirs(DEBUG_DIR, exist_ok=True)

sct = mss.MSS()
monitor = sct.monitors[2] 

print("=======================================================")
print(">>> HSV CALIBRATION - MATCHED TO SYSTEM SPECIFICS")
print("=======================================================")

for i in range(3, 0, -1):
    print(f"Counting in {i}...")
    time.sleep(1.0)

full = np.array(sct.grab(monitor))

# Using your verified coordinates
player_hp_bar   = full[50:63, 40:880]
opponent_hp_bar = full[50:63, 1040:1875]

hsv_p = cv2.cvtColor(player_hp_bar, cv2.COLOR_BGR2HSV)
hsv_o = cv2.cvtColor(opponent_hp_bar, cv2.COLOR_BGR2HSV)

# TARGETED LIMITS based on your sampled data
lower_yellow = np.array([10, 60, 200])
upper_yellow = np.array([25, 110, 255])

mask_p = cv2.inRange(hsv_p, lower_yellow, upper_yellow)
mask_o = cv2.inRange(hsv_o, lower_yellow, upper_yellow)

# Clean up any stray single-pixel text edge remnants
kernel = np.ones((2,2), np.uint8)
clean_mask_p = cv2.morphologyEx(mask_p, cv2.MORPH_OPEN, kernel)
clean_mask_o = cv2.morphologyEx(mask_o, cv2.MORPH_OPEN, kernel)

player_pixel_count = cv2.countNonZero(clean_mask_p)
opponent_pixel_count = cv2.countNonZero(clean_mask_o)

cv2.imwrite(str(DEBUG_DIR / "mask_player_final.png"), clean_mask_p)
cv2.imwrite(str(DEBUG_DIR / "mask_opponent_final.png"), clean_mask_o)

print("\n--- TARGETED CALIBRATION RESULTS ---")
print(f"Verified Player Full HP Pixel Count: {player_pixel_count}")
print(f"Verified Opponent Full HP Pixel Count: {opponent_pixel_count}")
print(f"\nClean masks saved to {DEBUG_DIR}/")