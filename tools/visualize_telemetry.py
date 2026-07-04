import cv2
import numpy as np
import time
from environment import MK1Environment

def main():
    print("Starting Telemetry Visualizer...")
    print("Press 'q' in the OpenCV window to exit.")
    
    env = MK1Environment()
    
    # Wait a brief second for screen capture initialization
    time.sleep(1.0)
    
    while True:
        # 1. Grab telemetry via the fully split environment pipeline
        obs = env._get_current_telemetry()
        player_pct = obs[0] * 100.0
        opponent_pct = obs[1] * 100.0
        
        # 2. Capture the full viewport baseline via the internal monitor config
        full_frame = np.array(env.sct.grab(env.monitor_base))
        # Convert BGRA to BGR to prevent drawing color profile mismatches
        debug_frame = cv2.cvtColor(full_frame, cv2.COLOR_BGRA2BGR)
        
        # 3. Draw isolation bounding boxes around the exact distinct entities we are tracking
        # Player 1 Bounding Frame (Green Box)
        p1 = env.p1_box
        cv2.rectangle(debug_frame, (p1["left"], p1["top"]), 
                      (p1["left"] + p1["width"], p1["top"] + p1["height"]), (0, 255, 0), 2)
        
        # Player 2 Bounding Frame (Red Box)
        p2 = env.p2_box
        cv2.rectangle(debug_frame, (p2["left"], p2["top"]), 
                      (p2["left"] + p2["width"], p2["top"] + p2["height"]), (0, 0, 255), 2)
        
        # 4. Render text data readouts matching the exact engine outputs
        cv2.putText(debug_frame, f"P1 HP: {player_pct:.1f}%", (40, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.putText(debug_frame, f"P2 HP: {opponent_pct:.1f}%", (1040, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        
        # Resize frame downward so it scales cleanly onto any desktop view during execution
        display_frame = cv2.resize(debug_frame, (1280, 720))
        cv2.imshow("MK1 Telemetry Engine - Debug Window", display_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()