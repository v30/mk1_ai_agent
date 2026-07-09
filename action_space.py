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
    "start": "enter",      
    "confirm": "enter"     
}

class MK1ActionSpace:
    def __init__(self):
        self.actions = {
            # --- 1. CORE MOVEMENT & BASIC BUTTONS (0 - 13) ---
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
            13: ("TALISMAN", lambda: self.tap_key("talisman")),
            
            # --- 2. SMOKE SPECIAL MOVES (14 - 24) ---
            14: ("SMOKE_SHADOW_BLADE", lambda: self._execute_sequence(["crouch", "forward", "front_punch"])),
            15: ("SMOKE_ENHANCED_SHADOW_BLADE", lambda: self._execute_sequence_enhanced(["crouch", "forward", "front_punch"])),
            16: ("SMOKE_BOMB", lambda: self._execute_sequence(["crouch", "forward", "back_punch"])),
            17: ("SMOKE_ENHANCED_BOMB", lambda: self._execute_sequence_enhanced(["crouch", "forward", "back_punch"])),
            18: ("SMOKE_VICIOUS_VAPORS", lambda: self._execute_sequence(["backward", "forward", "front_kick"])),
            19: ("SMOKE_ENHANCED_VICIOUS_VAPORS", lambda: self._execute_sequence_enhanced(["backward", "forward", "front_kick"])),
            20: ("SMOKE_VICIOUS_VAPORS_CANCEL", self.macro_vicious_vapors_cancel),
            21: ("SMOKE_PORT", lambda: self._execute_sequence(["crouch", "backward", "back_kick"])),
            22: ("SMOKE_ENHANCED_PORT", lambda: self._execute_sequence_enhanced(["crouch", "backward", "back_kick"])),
            23: ("SMOKE_PORT_CANCEL", self.macro_smoke_port_cancel),
            24: ("SMOKE_FATAL_BLOW", self.macro_fatal_blow),

            # --- 3. GROUND COMBO STRINGS FROM LIST (25 - 31) ---
            25: ("COMBO_NEVER_SUBMIT", lambda: self._execute_combo(["front_punch", "front_punch"])),                    # 1, 1
            26: ("COMBO_MISSING_THE_TOES", lambda: self._execute_combo(["forward", "front_punch", "back_punch", "back_punch", "back_kick"])), # F+1, 2, 2, 4
            27: ("COMBO_KUTTING_ROOM_FOUR", lambda: self._execute_combo(["forward", "front_punch", "back_punch", "throw"])), # F+1, 2, 1+3 (Throw bind handles dual-press)
            28: ("COMBO_EVERYWHERE", lambda: self._execute_combo(["back_punch", "front_punch", "back_punch"])),          # 2, 1, 2
            29: ("COMBO_VIOLENT_TENDENCIES", lambda: self._execute_combo(["backward", "back_punch", "front_kick", "back_kick"])), # B+2, 3, 4 (Overhead launcher setup)
            30: ("COMBO_SOARING_ASSASSIN", lambda: self._execute_combo(["forward", "front_kick", "back_punch", "back_kick"])),   # F+3, 2, 4 (Low starter to overhead mix)
            31: ("COMBO_INHALATION", lambda: self._execute_combo(["crouch", "front_kick", "back_kick"])),                 # D+3, 4

            # --- 4. FAST STRATEGIC POKES & FLATS FROM LIST (32 - 35) ---
            32: ("POKE_LOW_SHANK", lambda: self._execute_combo(["crouch", "front_punch"])),         # D+1 (Fastest check)
            33: ("POKE_TELE_STAB", lambda: self._execute_combo(["backward", "back_punch"])),        # B+2 (Standalone Overhead)
            34: ("POKE_SWEEPING_SMOKE", lambda: self._execute_combo(["backward", "back_kick"])),    # B+4 (Long-range low sweep)
            35: ("ATTACK_FACE_WALK", lambda: self._execute_combo(["forward", "back_kick"])),        # F+4 (High heavy damage)

            # --- 5. AERIAL COMBO STRINGS (36 - 38) ---
            36: ("AIR_SMOKED_OUT", lambda: self._execute_air_combo(["front_punch", "front_punch", "back_punch"])),  # J+1, 1, 2
            37: ("AIR_CUTTER", lambda: self._execute_air_combo(["back_punch", "front_punch", "front_punch"])),      # J+2, 1, 1
            38: ("AIR_AIRING_OUT", lambda: self._execute_air_combo(["front_kick", "back_kick", "back_kick"])),      # J+3, 4, 4

            # --- 6. THROWS & UTILITIES (39 - 40) ---
            39: ("THROW_FORWARD", lambda: self._execute_combo(["forward", "throw"])),               # F+Throw
            40: ("KOMBO_BREAKER", lambda: self._execute_combo(["forward", "block"]))                # F+Block (Breaks combos when hit)
        }
        
    @property
    def n(self):
        return len(self.actions)

    def execute(self, action_index):
        action_name, action_func = self.actions.get(action_index, ("NO_OP", self.no_operation))
        print(f"DEBUG: Executing action index {action_index}: {action_name}") 
        action_func()
        return action_name

    def _execute_sequence(self, keys, press_delay=0.04, gap_delay=0.01):
        """Standard rapid execution helper for special moves."""
        for key in keys:
            pydirectinput.keyDown(KEY_MAP[key])
            time.sleep(press_delay)
            pydirectinput.keyUp(KEY_MAP[key])
            time.sleep(gap_delay)

    def _execute_combo(self, keys, press_delay=0.05, dial_delay=0.06):
        """Standard ground combo string runner with directional processing."""
        i = 0
        while i < len(keys):
            if keys[i] in ["forward", "backward", "crouch", "jump"] and i + 1 < len(keys):
                dir_key = KEY_MAP[keys[i]]
                atk_key = KEY_MAP[keys[i+1]]
                pydirectinput.keyDown(dir_key)
                pydirectinput.keyDown(atk_key)
                time.sleep(press_delay)
                pydirectinput.keyUp(dir_key)
                pydirectinput.keyUp(atk_key)
                i += 2
            else:
                atk_key = KEY_MAP[keys[i]]
                pydirectinput.keyDown(atk_key)
                time.sleep(press_delay)
                pydirectinput.keyUp(atk_key)
                i += 1
            time.sleep(dial_delay)

    def _execute_air_combo(self, attack_keys, jump_delay=0.12, press_delay=0.05, dial_delay=0.06):
        """Specialized aerial runner. Forces a forward-jump before running the string digits."""
        # 1. Execute Forward Jump (Up + Forward simultaneously)
        pydirectinput.keyDown(KEY_MAP["jump"])
        pydirectinput.keyDown(KEY_MAP["forward"])
        time.sleep(press_delay)
        pydirectinput.keyUp(KEY_MAP["jump"])
        pydirectinput.keyUp(KEY_MAP["forward"])
        
        # 2. Short pause to wait for the upward character arc to meet the enemy
        time.sleep(jump_delay)
        
        # 3. Dial the air attacks in sequence
        for key in attack_keys:
            atk_key = KEY_MAP[key]
            pydirectinput.keyDown(atk_key)
            time.sleep(press_delay)
            pydirectinput.keyUp(atk_key)
            time.sleep(dial_delay)

    def _execute_sequence_enhanced(self, keys, press_delay=0.04, gap_delay=0.01):
        for key in keys[:-1]:
            pydirectinput.keyDown(KEY_MAP[key])
            time.sleep(press_delay)
            pydirectinput.keyUp(KEY_MAP[key])
            time.sleep(gap_delay)
        final_attack_key = KEY_MAP[keys[-1]]
        block_key = KEY_MAP["block"]
        pydirectinput.keyDown(final_attack_key)
        pydirectinput.keyDown(block_key)
        time.sleep(press_delay + 0.02)
        pydirectinput.keyUp(final_attack_key)
        pydirectinput.keyUp(block_key)

    def macro_vicious_vapors_cancel(self):
        self._execute_sequence(["backward", "forward", "front_kick"])
        time.sleep(0.05)
        pydirectinput.keyDown(KEY_MAP["backward"])
        pydirectinput.keyDown(KEY_MAP["block"])
        time.sleep(0.1)
        pydirectinput.keyUp(KEY_MAP["backward"])
        pydirectinput.keyUp(KEY_MAP["block"])

    def macro_smoke_port_cancel(self):
        self._execute_sequence(["crouch", "backward", "back_kick"])
        pydirectinput.keyDown(KEY_MAP["forward"])
        time.sleep(0.25)
        pydirectinput.keyUp(KEY_MAP["forward"])

    def macro_fatal_blow(self):
        pydirectinput.keyDown(KEY_MAP["flip_stance"])
        pydirectinput.keyDown(KEY_MAP["block"])
        time.sleep(0.15)
        pydirectinput.keyUp(KEY_MAP["flip_stance"])
        pydirectinput.keyUp(KEY_MAP["block"])

    def execute_raw_button(self, bind_name):
        bind_lower = bind_name.lower()
        if bind_lower in KEY_MAP:
            pydirectinput.press(KEY_MAP[bind_lower])

    def tap_key(self, bind_name):
        bind_lower = bind_name.lower()
        if bind_lower in KEY_MAP:
            pydirectinput.press(KEY_MAP[bind_lower])

    def hold_key(self, bind_name, duration):
        bind_lower = bind_name.lower()
        if bind_lower in KEY_MAP:
            pydirectinput.keyDown(KEY_MAP[bind_lower])
            time.sleep(duration)
            pydirectinput.keyUp(KEY_MAP[bind_lower])

    def no_operation(self):
        for key in KEY_MAP.values():
            pydirectinput.keyUp(key)