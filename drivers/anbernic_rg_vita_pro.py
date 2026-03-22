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

        target_mode = state._mode
        is_battery_alert = False
        target_color = [255, 255, 255] # Fallback if palette isn't ready

        # 1. Get Battery Info
        bat_pct = int(state.DEV.BATTERY.get('percentage', 0))
        bat_status = state.DEV.BATTERY.get('state', 'Discharging')
        bat_map = self.config.get("battery_mapping", {})

        # Get the primary color from the selected palette
        try:
            primary_palette = state._target_palette[0]
            target_color = [int(c * 255) for c in primary_palette.fg]
        except (AttributeError, IndexError, TypeError):
            pass 

        # 2. Battery Alert Overwrites
        try:
            low_threshold = int(CONFIG.get("battery.low.threshold", 20))
        except:
            low_threshold = 20

        if bat_status == "Charging":
            cfg = bat_map.get("Charging")
            if cfg:
                target_mode, target_color = cfg["mode"], cfg["color"]
                is_battery_alert = True
        elif bat_pct <= low_threshold:
            is_battery_alert = True
            cfg = bat_map.get("Critical") if bat_pct <= 10 else bat_map.get("Low")
            if cfg:
                target_mode, target_color = cfg["mode"], cfg["color"]

        # Only set brightness to 0 if the mode is 'null' and no battery alert is active.
        if target_mode == "null" and not is_battery_alert:
            self._set_sysfs("led_level", 0)
            self._set_sysfs("led_set", 1)
            return
        
        # Enable RGB in any case.
        self._set_sysfs("led_switch", 1)

        # 3. Apply Brightness and Hardware IDs
        base_br = getattr(state, "_target_br", 100)
        self._set_sysfs("led_level", int(base_br * 2.55))

        mode_data = self.HW_MODES.get(target_mode, self.HW_MODES.get("static", {"hw_id": 1, "hw_speed": 0}))
        hw_id = mode_data.get("hw_id", 1)
        
        self._set_sysfs("led_mode", hw_id)
        self._set_sysfs("led_speed", mode_data.get("hw_speed", 0))

        # 4. Final Color Write
        if hw_id not in [3, 4, 6]:
            r, g, b = target_color

            # ALWAYS write these for Static Mode support
            self._set_sysfs("custum_rgb_r", r)
            self._set_sysfs("custum_rgb_g", g)
            self._set_sysfs("custum_rgb_b", b)

            # Standard RGB Nodes
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