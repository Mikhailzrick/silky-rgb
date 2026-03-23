import os, time

class RGBDriver:

    def __init__(self, extra: dict = None) -> None:
        # 'extra' is the 'driver_extra_params' dictionary from the JSON
        self.config = extra if extra is not None else {}
        self._battery_trust_established = False
        
        # Pulling directly from the 'extra' dict
        self.PATH = self.config.get("hw_path")
        self.HW_MODES = self.config.get("hw_modes", {})
        print(f"DEBUG: Driver initialized. Looking for hardware at: {self.PATH}")

    def _set_sysfs(self, node, value):
        try:
            # Force absolute integer, no floats, capped at 255
            val = max(0, min(255, int(float(value))))
            with open(os.path.join(self.PATH, node), "w") as f:
                f.write(str(val))
        except Exception:
            pass

    def sync(self, state):
        from ..confloader import CONFIG

        target_mode = state._mode
        is_battery_alert = False
        target_color = [255, 255, 255] # Fallback if palette isn't ready

        # 1. Get Battery Info
        val = state.DEV.BATTERY.get('percentage')
        try:
            raw_pct = int(val) if val is not None else -1
        except:
            raw_pct = -1
        # If the battery percentage is at 0 on launch, we consider the battery info to be untrustworthy
        if raw_pct > 0:
            self._battery_trust_established = True
        if not self._battery_trust_established and raw_pct <= 0:
            # While in this 'Limbo', we stay in "regular" mode
            bat_pct = 100
        else:
            bat_pct = int(raw_pct)
        bat_status = state.DEV.BATTERY.get('state', 'Discharging')
        bat_map = self.config.get("battery_mapping", {})

        print(f"DEBUG: Sync with state: mode={target_mode}, battery={bat_pct}%/{bat_status}")

        # Get the primary color from the selected palette
        try:
            p = state._palette[0].bg 
            target_color = [int(p[0] * 255), int(p[1] * 255), int(p[2] * 255)]
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
            # Only check low/critical if NOT charging
            if bat_pct <= 10:
                cfg = bat_map.get("Critical")
                if cfg: (target_mode, target_color, is_battery_alert) = (cfg["mode"], cfg["color"], True)
            elif bat_pct <= 20:
                cfg = bat_map.get("Low")
                if cfg: (target_mode, target_color, is_battery_alert) = (cfg["mode"], cfg["color"], True)

        # Only set brightness to 0 if the mode is 'null' and no battery alert is active.
        if target_mode == "null" and not is_battery_alert:
            self._set_sysfs("led_level", 0)
            self._set_sysfs("led_set", 1)
            return
        
        # Enable RGB in any case.
        self._set_sysfs("led_switch", 1)

        # 3. Apply Brightness and Hardware IDs
        base_br = getattr(state, "_target_br", 100)
        brightness = int(float(base_br) * 2.55)
        self._set_sysfs("led_level", brightness)

        mode_data = self.HW_MODES.get(target_mode, self.HW_MODES.get("static", {"hw_id": 1, "hw_speed": 4}))
        hw_id = mode_data.get("hw_id", 1)
        hw_speed = mode_data.get("hw_speed", 4)
        
        self._set_sysfs("led_mode", hw_id)
        self._set_sysfs("led_speed", hw_speed)

        print(f"DEBUG: Applying settings -> Mode: {target_mode} (HW ID: {hw_id}), Speed: {hw_speed}, Brightness: {brightness}, Color: {target_color}")

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