import os
import time
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from environment import MK1AIEv

def main():
    print("--- Initializing Mortal Kombat 1 AI Training Harness ---")
    
    # 1. Instantiate the Custom Gymnasium Environment
    env = MK1AIEv()

    # 2. Configure Logging Directories
    log_dir = "./tensorboard_logs/"
    model_dir = "./trained_models/"
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    # 3. Initialize the PPO Agent
    print("Initializing PPO Neural Network Model...")
    model = PPO(
        policy="MlpPolicy", 
        env=env,
        verbose=1,                  
        tensorboard_log=log_dir,    
        learning_rate=3e-4,         
        n_steps=2048,               
        batch_size=64,              
        n_epochs=10                 
    )

    # 4. Create a Training Lifecycle Callback
    checkpoint_callback = CheckpointCallback(
        save_freq=10000, 
        save_path=model_dir,
        name_prefix="mk1_ppo_model"
    )

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
        model.learn(
            total_timesteps=500000, 
            callback=checkpoint_callback,
            tb_log_name="PPO_MK1_Run_1"
        )
    except KeyboardInterrupt:
        print("\nTraining interrupted by user. Saving safe progress checkpoint...")
        model.save(os.path.join(model_dir, "mk1_ppo_model_interrupted"))

    # Final cleanup when done
    print("Training sequence finalized. Saving terminal model state.")
    model.save(os.path.join(model_dir, "mk1_ppo_model_final"))

if __name__ == "__main__":
    main()