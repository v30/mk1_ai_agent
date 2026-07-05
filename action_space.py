import pydirectinput
import time

# Restore original pause setting
pydirectinput.PAUSE = 0.001 

KEY_MAP = {
    "forward": "d",
    "backward": "a",
    "jump": "w",
    "crouch": "s",
    "front_punch": "1",
    "back_punch": "2",
    "front_kick": "3",
    "back_kick": "4",
    "throw": "5",
    "block": "6",
    "kameo": "7",
    "flip_stance": "8",
    "talisman": "q",
    "start": "enter",      # Map start to enter
    "confirm": "enter"     # Map confirm to enter
}

class MK1ActionSpace:
    def __init__(self):
        self.actions = {
            0: ("NO_OP", self.no_operation),
            1: ("MOVE_FORWARD", lambda: self.hold_key("forward", 0.1)),
            2: ("MOVE_BACKWARD", lambda: self.hold_key("backward", 0.1)),
            3: ("JUMP", lambda: self.tap_key("jump")),
            4: ("CROUCH", lambda: self.hold_key("crouch", 0.15)),
            5: ("FRONT_PUNCH", lambda: self.tap_key("front_punch")),
            6: ("BACK_PUNCH", lambda: self.tap_key("back_punch")),
            7: ("FRONT_KICK", lambda: self.tap_key("front_kick")),
            8: ("BACK_KICK", lambda: self.tap_key("back_kick")),
            9: ("THROW", lambda: self.tap_key("throw")),
            10: ("BLOCK", lambda: self.hold_key("block", 0.2)),
            11: ("KAMEO", lambda: self.tap_key("kameo")),
            12: ("FLIP_STANCE", lambda: self.tap_key("flip_stance")),
            13: ("TALISMAN", lambda: self.tap_key("talisman"))
        }
        
    @property
    def n(self):
        return len(self.actions)

    def execute(self, action_index):
        action_name, action_func = self.actions.get(action_index, ("NO_OP", self.no_operation))
        print(f"DEBUG: Executing action index {action_index}: {action_name}") 
        action_func()
        return action_name

    def execute_raw_button(self, bind_name):
        """Allows direct execution of UI/Menu keys (like start or confirm) by key name."""
        bind_lower = bind_name.lower()
        if bind_lower in KEY_MAP:
            pydirectinput.press(KEY_MAP[bind_lower])

    def tap_key(self, bind_name):
        # Force string to lowercase to match KEY_MAP dictionary keys safely
        bind_lower = bind_name.lower()
        if bind_lower in KEY_MAP:
            pydirectinput.press(KEY_MAP[bind_lower])

    def hold_key(self, bind_name, duration):
        # Force string to lowercase to match KEY_MAP dictionary keys safely
        bind_lower = bind_name.lower()
        if bind_lower in KEY_MAP:
            pydirectinput.keyDown(KEY_MAP[bind_lower])
            time.sleep(duration)
            pydirectinput.keyUp(KEY_MAP[bind_lower])

    def no_operation(self):
        """Force release all keys to stop any stuck movement."""
        for key in KEY_MAP.values():
            pydirectinput.keyUp(key)