import os
import time
import pygetwindow as gw
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
from environment import MK1Environment

class FocusValidationCallback(BaseCallback):
    """
    Custom Stable-Baselines3 callback that runs at every step.
    If 'Mortal Kombat™ 1' is not the active window, it pauses execution 
    and checks again periodically until focus is restored.
    """
    def __init__(self, target_window_title="Mortal Kombat™ 1", check_interval=1.0, verbose=0):
        super().__init__(verbose)
        self.target_title = target_window_title
        self.check_interval = check_interval
        self.paused_notified = False

    def _on_step(self) -> bool:
        # Check the currently active foreground window on Windows
        active_window = gw.getActiveWindow()
        
        if active_window is None or self.target_title not in active_window.title:
            if not self.paused_notified:
                print(f"\n[PAUSE] Focus lost! Active window: '{active_window.title if active_window else 'None'}'.")
                print(f"[PAUSE] Freezing training loop. Switch back to '{self.target_title}' to resume.")
                self.paused_notified = True
            
            # Enter an idle block until focus returns
            while True:
                time.sleep(self.check_interval)
                current_active = gw.getActiveWindow()
                if current_active and self.target_title in current_active.title:
                    print(f"\n[RESUME] Focus restored on '{self.target_title}'. Continuing training loop...")
                    self.paused_notified = False
                    # Brief grace window so inputs don't fire instantly upon clicking the screen
                    time.sleep(0.5) 
                    break
                    
        return True # Continue training execution step

def main():
    print("--- Initializing Mortal Kombat 1 AI Training Harness ---")
    
    # 1. Instantiate the Custom Gymnasium Environment & Apply Mandatory Wrappers
    base_env = MK1Environment()
    env = DummyVecEnv([lambda: base_env])
    env = VecFrameStack(env, n_stack=4, channels_order="first")

    # 2. Configure Logging Directories
    log_dir = "./tensorboard_logs/"
    model_dir = "./trained_models/"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    # Path to the primary persistence model file
    final_model_path = os.path.join(model_dir, "mk1_ppo_model_final.zip")

    # 3. Initialize or Load the PPO Agent
    if os.path.exists(final_model_path):
        print(f"\n[INFO] Found existing brain weights at {final_model_path}!")
        print(">>> Loading saved model to continue training sequence...")
        model = PPO.load(
            final_model_path, 
            env=env, 
            tensorboard_log=log_dir,
            device="cuda"
        )
    else:
        print("\n[INFO] No saved brain weights found.")
        print(">>> Initializing a brand-new PPO Neural Network Model...")
        model = PPO(
            policy="MlpPolicy", 
            env=env,
            verbose=1,                  
            tensorboard_log=log_dir,    
            learning_rate=3e-4,         
            n_steps=2048,               
            batch_size=64,              
            n_epochs=10,
            device="cuda"
        )

    # 4. Create Training Lifecycle Callbacks
    checkpoint_callback = CheckpointCallback(
        save_freq=10000, 
        save_path=model_dir,
        name_prefix="mk1_ppo_model"
    )
    
    # Instantiate our safety gate focus callback
    focus_callback = FocusValidationCallback(target_window_title="Mortal Kombat™ 1")

    # 5. Window Switch Countdown Delay
    print("\n=======================================================")
    print(">>> PREPARING EXECUTION ENGINE...")
    print(">>> Switch to the Mortal Kombat 1 window NOW!")
    print("=======================================================")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1.0)
    print(">>> ENGINE RUNNING. Starting Training Loop.")
    print("Press CTRL+C in this terminal to stop training and save checkpoints.")
    
    try:
        # Combine the callbacks into a sequential execution list
        model.learn(
            total_timesteps=500000, 
            callback=[checkpoint_callback, focus_callback], # <-- Triggers focus verification alongside saving routines
            tb_log_name="PPO_MK1_Run_1",
            reset_num_timesteps=False
        )
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving safe progress checkpoint...")
        model.save(os.path.join(model_dir, "mk1_ppo_model_interrupted"))

    # Final cleanup when done
    print("Training sequence finalized. Saving terminal model state.")
    model.save(final_model_path)

if __name__ == "__main__":
    main()