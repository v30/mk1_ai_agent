import mss
import numpy as np
import cv2
import time
from pathlib import Path

# Programmatically locate the root folder relative to this file
TOOLS_DIR = Path(__file__).parent
ROOT_DIR = TOOLS_DIR.parent

# Using mss.MSS() to clear up that deprecation warning
sct = mss.MSS()
monitor = sct.monitors[2] 

print("=======================================================")
print(">>> HEALTH BAR CROPPING DIAGNOSTIC TOOL")
print(">>> Switch to the Mortal Kombat 1 window NOW!")
print("=======================================================")

for i in range(3, 0, -1):
    print(f"Capturing screen in {i}...")
    time.sleep(1.0)

print(">>> Capturing frame...")
full = np.array(sct.grab(monitor))

# Crop the active UI coordinates from the captured frame
player_hp_bar   = full[48:62, 160:760]
opponent_hp_bar = full[48:62, 1160:1760]

# Generate absolute, safe file paths
player_save_path = ROOT_DIR / "test_player_hp.png"
opponent_save_path = ROOT_DIR / "test_opponent_hp.png"

# Write using exact absolute string paths
cv2.imwrite(str(player_save_path), player_hp_bar)
cv2.imwrite(str(opponent_save_path), opponent_hp_bar)

print("\nCrops saved successfully directly to your root folder!")
print(f"Paths:\n -> {player_save_path}\n -> {opponent_save_path}")