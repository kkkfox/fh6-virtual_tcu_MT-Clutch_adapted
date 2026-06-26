import time
from concurrent.futures import ThreadPoolExecutor

import keyboard

from virtual_tcu.config.constants import Cfg
from virtual_tcu.config.store import ConfigStore
from virtual_tcu.input.interface import OutputInterface


class KeyboardOutput(OutputInterface):
    """Inject shift commands as keyboard key-presses (E / Q by default).

    When ``feat_clutch_assist`` is enabled the output sends a full clutch
    sequence around each shift press:

    1. Press clutch key (default: ``shift`` — the FH6 "Manual with Clutch"
       binding for Shift+E / Shift+Q).
    2. Wait ``clutch_pre_ms`` ms.
    3. Press the shift key (E or Q).
    4. Wait ``clutch_overlap_ms`` ms (key hold, same role as KEY_HOLD_S).
    5. Release the shift key.
    6. Wait ``clutch_release_ms`` ms.
    7. Release the clutch key.

    With the default ``clutch_key = "shift"`` this produces the exact key
    chord that FH6 expects for clutch-assisted sequential shifts.
    """

    def __init__(self, config: ConfigStore):
        self._config = config
        self._self_press_until: dict[str, float] = {}
        self.SELF_PRESS_WINDOW_S = 0.15
        self._blip_keys: tuple[str, str] | None = None
        # Single worker ensures keystrokes are executed sequentially without thread leaks
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="KB_Worker")

    # -- config properties -----------------------------------------------------

    @property
    def key_up(self) -> str:
        return str(self._config.get("shift_key_up", "e")).lower()

    @property
    def key_down(self) -> str:
        return str(self._config.get("shift_key_down", "q")).lower()

    @property
    def clutch_key(self) -> str:
        return str(self._config.get("clutch_key", "shift")).lower()

    @property
    def use_clutch(self) -> bool:
        return bool(self._config.get("feat_clutch_assist", False))

    @property
    def clutch_pre_ms(self) -> int:
        return int(self._config.get("clutch_pre_ms", 20))

    @property
    def clutch_overlap_ms(self) -> int:
        return int(self._config.get("clutch_overlap_ms", 55))

    @property
    def clutch_release_ms(self) -> int:
        return int(self._config.get("clutch_release_ms", 25))

    @property
    def blip_key(self) -> str:
        return str(self._config.get("blip_key", "w")).lower()

    @property
    def blip_ms(self) -> int:
        return int(self._config.get("blip_ms", 70))

    @property
    def use_blip(self) -> bool:
        return bool(self._config.get("feat_rev_blip", True))

    # -- OutputInterface -------------------------------------------------------

    def is_self_press(self, key: str) -> bool:
        return time.time() < self._self_press_until.get(key.lower(), 0.0)

    def shift_to(self, from_gear: int, target_gear: int):
        # from_gear and target_gear must be 0-10
        if not (0 <= from_gear <= 10) or not (0 <= target_gear <= 10):
            print(f"[Keyboard] invalid gear numbers: from {from_gear} to {target_gear}")
            return
        if from_gear == target_gear:
            return

        shifts_needed = abs(target_gear - from_gear)
        shift_key = self.key_up if target_gear > from_gear else self.key_down

        if self.use_clutch:

            def _multi_shift_clutch():
                for i in range(shifts_needed):
                    self._press_release_with_clutch(shift_key)
                    if i < shifts_needed - 1:
                        time.sleep(0.06)

            self._executor.submit(_multi_shift_clutch)
        else:

            def _multi_shift():
                for i in range(shifts_needed):
                    self._press_release(shift_key)
                    if i < shifts_needed - 1:
                        time.sleep(0.06)

            self._executor.submit(_multi_shift)

    def shift_no_clutch(self, from_gear: int, target_gear: int):
        """Pure sequential shift without clutch (racing transmission).

        Called by TCULogic when feat_clutch_assist is on but the car has a
        racing gearbox that does not need clutch for forward gears."""
        if not (0 <= from_gear <= 10) or not (0 <= target_gear <= 10):
            return
        if from_gear == target_gear:
            return

        is_downshift = target_gear < from_gear
        shifts_needed = abs(target_gear - from_gear)
        shift_key = self.key_up if target_gear > from_gear else self.key_down

        if is_downshift and self.use_blip:

            def _multi_shift_blip():
                for i in range(shifts_needed):
                    self._press_release_with_blip(shift_key)
                    if i < shifts_needed - 1:
                        time.sleep(0.06)

            self._executor.submit(_multi_shift_blip)
        else:

            def _multi_shift():
                for i in range(shifts_needed):
                    self._press_release(shift_key)
                    if i < shifts_needed - 1:
                        time.sleep(0.06)

            self._executor.submit(_multi_shift)

    def shutdown(self):
        self._executor.shutdown(wait=False)

    # -- relearn fuel-cut blip -------------------------------------------------

    def relearn_blip_supported(self) -> bool:
        return True

    def begin_relearn_blip(self, throttle_key: str, clutch_key: str) -> None:
        """Hold clutch (declutch) then throttle so the engine free-revs to the
        fuel cut with no wheel load — dodges the rev-limiter slip exclusion."""
        ck = (clutch_key or "shift").lower()
        tk = (throttle_key or "w").lower()
        self._blip_keys = (ck, tk)
        # Mark a generous self-press window so any paddle listener ignores the
        # held throttle/clutch as injected input for the duration of the blip.
        deadline = time.time() + 5.0
        self._self_press_until[ck] = deadline
        self._self_press_until[tk] = deadline
        try:
            keyboard.press(ck)
            time.sleep(0.03)
            keyboard.press(tk)
        except Exception as e:
            print(f"[KB] relearn blip press failed: {e}")

    def end_relearn_blip(self) -> None:
        ck, tk = self._blip_keys or ("shift", "w")
        try:
            keyboard.release(tk)
            keyboard.release(ck)
        except Exception as e:
            print(f"[KB] relearn blip release failed: {e}")
        finally:
            self._blip_keys = None

    # -- internals -------------------------------------------------------------

    def _press_release(self, key: str):
        """Simple press-hold-release without clutch."""
        try:
            key = key.lower()
            self._self_press_until[key] = time.time() + self.SELF_PRESS_WINDOW_S
            keyboard.press(key)
            time.sleep(Cfg.KEY_HOLD_S)
            keyboard.release(key)
        except Exception as e:
            print(f"[KB] Input simulation failed: {e}")

    def _press_release_with_clutch(self, key: str):
        """Press clutch → hold → press shift key → (rev-blip for downshifts) → release sequence.

        Timing is controlled by three tunable parameters:
          clutch_pre_ms     – delay between clutch press and shift key press
          clutch_overlap_ms – duration shift key and clutch are both held
          clutch_release_ms – delay between shift key release and clutch release
        """
        ck = self.clutch_key
        k = key.lower()
        is_downshift = k == self.key_down
        do_blip = is_downshift and self.use_blip
        blip_key = self.blip_key
        blip_s = max(0.02, self.blip_ms / 1000.0)

        pressed_ck = False
        pressed_blip = False
        pressed_k = False
        try:
            pre_s = self.clutch_pre_ms / 1000.0
            overlap_s = self.clutch_overlap_ms / 1000.0
            release_s = self.clutch_release_ms / 1000.0
            shift_hold_s = max(overlap_s, blip_s) if do_blip else overlap_s
            total_s = pre_s + shift_hold_s + release_s + 0.05
            deadline = time.time() + total_s + self.SELF_PRESS_WINDOW_S
            self._self_press_until[k] = deadline
            self._self_press_until[ck] = deadline
            if do_blip:
                self._self_press_until[blip_key] = deadline

            keyboard.press(ck)
            pressed_ck = True
            time.sleep(pre_s)

            keyboard.press(k)
            pressed_k = True
            if do_blip:
                print(f"[RevBlip] {blip_key} blip {blip_s*1000:.0f}ms (clutch assist)")
                keyboard.press(blip_key)
                pressed_blip = True
                time.sleep(blip_s)
                keyboard.release(blip_key)
                pressed_blip = False
                time.sleep(max(0.0, shift_hold_s - blip_s))
            else:
                time.sleep(shift_hold_s)

            keyboard.release(k)
            pressed_k = False
            time.sleep(release_s)

            keyboard.release(ck)
            pressed_ck = False
        except Exception as e:
            print(f"[KB] Clutch-assisted shift failed: {e}")
        finally:
            try:
                if pressed_blip:
                    keyboard.release(blip_key)
                if pressed_k:
                    keyboard.release(k)
                if pressed_ck:
                    keyboard.release(ck)
            except Exception:
                pass

    def _press_release_with_blip(self, key: str):
        """Downshift rev-match without clutch: shift + throttle together, then release."""
        blip_key = self.blip_key
        blip_s = max(0.02, self.blip_ms / 1000.0)
        hold_s = max(Cfg.KEY_HOLD_S, blip_s)
        k = key.lower()
        pressed_blip = False
        pressed_k = False
        try:
            deadline = time.time() + hold_s + 0.05 + self.SELF_PRESS_WINDOW_S
            self._self_press_until[k] = deadline
            self._self_press_until[blip_key] = deadline

            keyboard.press(k)
            pressed_k = True
            print(f"[RevBlip] {blip_key} blip {blip_s*1000:.0f}ms (sequential)")
            keyboard.press(blip_key)
            pressed_blip = True
            time.sleep(blip_s)
            keyboard.release(blip_key)
            pressed_blip = False
            time.sleep(max(0.0, hold_s - blip_s))
            keyboard.release(k)
            pressed_k = False
        except Exception as e:
            print(f"[KB] Blip shift failed: {e}")
        finally:
            try:
                if pressed_blip:
                    keyboard.release(blip_key)
                if pressed_k:
                    keyboard.release(k)
            except Exception:
                pass
