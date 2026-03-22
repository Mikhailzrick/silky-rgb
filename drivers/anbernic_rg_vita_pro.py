import os, time

class RGBDriver:
    def __init__(self, extra: dict = None) -> None:
        # 'extra' is the 'driver_extra_params' dictionary from the JSON
        self.config = extra if extra is not None else {}
        
        # Pulling directly from the 'extra' dict
        self.PATH = self.config.get("hw_path")
        self.HW_MODES = self.config.get("hw_modes", {})
        print(f"DEBUG: Driver initialized. Looking for hardware at: {self.PATH}")

    def _set_sysfs(self, node, value):
        try:
            with open(os.path.join(self.PATH, node), "w") as f:
                f.write(str(value))
        except Exception:
            pass

    def sync(self, state):
        from ..confloader import CONFIG

        # Enable RGB if it isn't already.
        self._set_sysfs("led_switch", 1)

        # 1. Pull the User's Threshold from knulli.conf
        try:
            low_threshold = int(CONFIG.get("battery.low.threshold", 20))
        except (ValueError, TypeError):
            low_threshold = 20

        # 2. Determine the Target State based on priority
        # Looking up 'battery_mapping' directly inside the 'extra' dict
        bat_map = self.config.get("battery_mapping", {})
        bat_pct = state.DEV.BATTERY.get('percentage', 100)
        bat_status = state.DEV.BATTERY.get('state', 'Discharging')
        target_mode = state._mode

        # Determine the target color from the primary palette, converting from 0.0-1.0 to 0-255.
        try:
            primary_palette = state._target_palette[0]
            # Convert the 0.0-1.0 floats back to 0-255 ints for sysfs
            target_color = [int(c * 255) for c in primary_palette.fg]
        except (AttributeError, IndexError, TypeError):
            # Fallback to white if the palette isn't ready
            target_color = [255, 255, 255]

        is_battery_alert = False

        if bat_status == "Charging":
            cfg = bat_map.get("Charging")
            target_mode, target_color = cfg["mode"], cfg["color"]
            is_battery_alert = True
        elif bat_pct <= low_threshold and bat_pct<= 10:
            cfg = bat_map.get("Critical")
            target_mode, target_color = cfg["mode"], cfg["color"]
            is_battery_alert = True
        elif bat_pct <= low_threshold:
            cfg = bat_map.get("Low")
            target_mode, target_color = cfg["mode"], cfg["color"]
            is_battery_alert = True

        # 3. Handle "No Effect" (null) override
        if target_mode == "null" and not is_battery_alert:
            self._set_sysfs("led_level", 0)
            self._set_sysfs("led_set", 1)
            return

        # 4. Handle LED Brightness
        base_br = getattr(state, "_target_br", 100) # The base level
        factor = getattr(state, "_target_sc", 100) / 100.0 # The dimming scale
        
        if CONFIG.get('brightness.adaptive', False):
            final_br = base_br * factor
        else:
            final_br = base_br

        # Convert 0-100 to 0-255 for the hardware
        self._set_sysfs("led_level", int(final_br * 2.55))

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

    def cheevo(self, state):
        self._set_sysfs("led_switch", 1)
        self._set_sysfs("led_mode", 4)
        self._set_sysfs("led_speed", 6)
        self._set_sysfs("led_set", 1)
        time.sleep(1.5)
        self.sync(state)
    
    def onKill(self):
        self._set_sysfs("led_switch", 0)
        self._set_sysfs("led_set", 1)