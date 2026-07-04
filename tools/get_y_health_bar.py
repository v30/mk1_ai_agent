import os
import mss
import numpy as np
import cv2
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
ROOT_DIR = TOOLS_DIR.parent
DEBUG_DIR = ROOT_DIR / "debug_images"

# Ensure the debug directory exists cleanly
os.makedirs(DEBUG_DIR, exist_ok=True)

sct = mss.MSS()
monitor = sct.monitors[2] 

print("=======================================================")
print(">>> VISUAL COORDINATE STRIP SCANNER")
print(">>> IMPORTANT: Run this during a live match round!")
print("=======================================================")

for i in range(3, 0, -1):
    print(f"Scanning in {i}...")
    time.sleep(1.0)

print(">>> Capturing wide top-left quadrant...")
full = np.array(sct.grab(monitor))

# Grab a massive 300px tall by 800px wide area from the top left
quadrant = full[0:300, 0:800].copy()

# Draw horizontal lines every 20 pixels with text labels
for y in range(0, 300, 20):
    cv2.line(quadrant, (0, y), (800, y), (0, 0, 255), 1)
    cv2.putText(quadrant, f"Y={y}", (10, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

# Target path inside our new debug folder
save_path = DEBUG_DIR / "debug_y_coordinates.png"
cv2.imwrite(str(save_path), quadrant)

print("\nScan completed successfully!")
print(f"Image saved to: {save_path}")
print("Open 'debug_images/debug_y_coordinates.png' to see what Y values frame the bar!")