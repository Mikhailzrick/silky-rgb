import os, time
from ..state import RGBState
from ..confloader import CONFIG

STATE = RGBState.get()

class RGBDriver:
    def __init__(self, extra: dict = None) -> None:
        # 'extra' is the 'driver_extra_params' dictionary from the JSON
        self.config = extra if extra is not None else {}
        
        # Pulling directly from the 'extra' dict
        self.PATH = self.config.get("hw_path")
        self.HW_MODES = self.config.get("hw_modes", {})

    def _set_sysfs(self, node, value):
        try:
            with open(os.path.join(self.PATH, node), "w") as f:
                f.write(str(value))
        except Exception:
            pass

    def sync(self):
        # 1. Pull the User's Threshold from knulli.conf
        try:
            low_threshold = int(CONFIG.get("battery.low.threshold", 20))
        except (ValueError, TypeError):
            low_threshold = 20

        # 2. Determine the Target State based on priority
        # Looking up 'battery_mapping' directly inside the 'extra' dict
        bat_map = self.config.get("battery_mapping", {})
        
        target_mode = STATE.mode
        target_color = STATE.color
        is_battery_alert = False

        if STATE.battery_status == "Charging":
            cfg = bat_map.get("Charging")
            target_mode, target_color = cfg["mode"], cfg["color"]
            is_battery_alert = True
        elif STATE.battery_percent <= 10:
            cfg = bat_map.get("Critical")
            target_mode, target_color = cfg["mode"], cfg["color"]
            is_battery_alert = True
        elif STATE.battery_percent <= low_threshold:
            cfg = bat_map.get("Low")
            target_mode, target_color = cfg["mode"], cfg["color"]
            is_battery_alert = True

        # 3. Handle "No Effect" (null) override
        if target_mode == "null" and not is_battery_alert:
            self._set_sysfs("led_level", 0)
            self._set_sysfs("led_set", 1)
            return

        # 4. Handle LED Brightness
        base_br = STATE.brightness 
        
        if CONFIG.get('brightness.adaptive', False):
            factor = STATE._target_sc / 100.0
            final_br = base_br * factor
        else:
            final_br = base_br

        hw_brightness = int(final_br * 2.55)
        self._set_sysfs("led_level", hw_brightness)

        # 5. Mode & Speed Lookup
        mode_data = self.HW_MODES.get(target_mode, self.HW_MODES.get("static", {}))
        hw_id = mode_data.get("hw_id", 1)
        hw_speed = mode_data.get("hw_speed", 0)

        # 6. Apply Hardware State
        self._set_sysfs("led_mode", hw_id)
        self._set_sysfs("led_speed", hw_speed)

        # 7. Apply Color (Skip for rainbow modes 3, 4, 6)
        if hw_id not in [3, 4, 6]:
            r, g, b = target_color
            for i in ["1", "2"]:
                self._set_sysfs(f"Led_rgb_r{i}", r)
                self._set_sysfs(f"Led_rgb_g{i}", g)
                self._set_sysfs(f"Led_rgb_b{i}", b)
        
        self._set_sysfs("led_set", 1)

    def write(self, data):
        # Bypassed by the render flag in device.py
        pass

    def cheevo(self):
        self._set_sysfs("led_mode", 4)
        self._set_sysfs("led_speed", 6)
        self._set_sysfs("led_set", 1)
        time.sleep(1.5)
        self.sync()