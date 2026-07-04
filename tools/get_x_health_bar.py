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
print(">>> HORIZONTAL COORDINATE STRIP SCANNER")
print(">>> IMPORTANT: Run this during a live match round!")
print("=======================================================")

for i in range(3, 0, -1):
    print(f"Scanning in {i}...")
    time.sleep(1.0)

print(">>> Capturing full width at calibrated Y band...")
full = np.array(sct.grab(monitor))

# Slice out the exact vertical region we just verified (60 to 80)
# We expand the slice slightly to 55:85 just to keep a tiny bit of border for context
x_strip = full[55:85, 0:full.shape[1]].copy()

# Draw vertical lines every 50 pixels across the entire width of the frame
for x in range(0, x_strip.shape[1], 50):
    cv2.line(x_strip, (x, 0), (x, x_strip.shape[0]), (0, 0, 255), 1)
    # Stagger the labels so they don't overlap and stay readable
    if x % 100 == 0:
        cv2.putText(x_strip, f"{x}", (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
    else:
        cv2.putText(x_strip, f"{x}", (x + 2, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)

save_path = DEBUG_DIR / "debug_x_coordinates.png"
cv2.imwrite(str(save_path), x_strip)

print("\nScan completed successfully!")
print(f"Image saved to: {save_path}")
print("Open 'debug_images/debug_x_coordinates.png' to map out the exact left and right limits!")