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
        full_path = os.path.join(self.PATH, node)
        try:
            val = str(max(0, min(1023, int(float(value)))))
            with open(full_path, "w") as f:
                f.write(val + "\n")
                f.flush() # Force it out of Python's memory
            # print(f"DEBUG: Wrote {val} to {node}") # Check your logs for this!
        except Exception as e:
            # THIS IS THE SMOKING GUN:
            print(f"ERROR writing to {node}: {e}")

    def sync(self, state):
        from ..confloader import CONFIG

        target_mode = state._mode
        is_battery_alert = False

        # Fallback colors if palette isn't ready
        primary_rgb = [110, 255, 0] # Knulli green! :)
        secondary_rgb = [0, 0, 0]

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
            c1 = state._palette[0].bg
            c2 = state._palette[0].fg
            
            primary_rgb = [int(x * 255) for x in c1]
            secondary_rgb = [int(x * 255) for x in c2]
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
                target_mode, primary_rgb = cfg["mode"], cfg["color"]
                is_battery_alert = True
        elif bat_pct <= low_threshold:
            # Only check low/critical if NOT charging
            if bat_pct <= 10:
                cfg = bat_map.get("Critical")
                if cfg: (target_mode, primary_rgb, is_battery_alert) = (cfg["mode"], cfg["color"], True)
            elif bat_pct <= 20:
                cfg = bat_map.get("Low")
                if cfg: (target_mode, primary_rgb, is_battery_alert) = (cfg["mode"], cfg["color"], True)

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

        print(f"DEBUG: Applying settings -> Mode: {target_mode} (HW ID: {hw_id}), Speed: {hw_speed}, Brightness: {brightness}, Primary Color: {primary_rgb}, Secondary Color: {secondary_rgb}")

        # 4. Apply colors if not a rainbow mode
        if hw_id not in [3, 4, 6]:
            
            # In case of static mode, set the "custum" color nodes,
            # otherwise set the standard RGB nodes. This is based 
            # on reverse-engineering and may need adjustments for
            # different hardware versions.
            if hw_id == 1:
                self._set_sysfs("custum_rgb_r", primary_rgb[0])
                self._set_sysfs("custum_rgb_g", primary_rgb[1])
                self._set_sysfs("custum_rgb_b", primary_rgb[2])
            elif hw_id == 5:
                # Mode 5:
                # Convert 0-255 (Additive) to 553-3 (Inverted)
                def to_mode5(val):
                    return int(round(553 - (float(val) * (550.0 / 255.0))))
                self._set_sysfs("led_level", 255)
                self._set_sysfs("led_sync_colour", 0)

                # Standard Inverted 10-bit Math
                def to_mode5(val):
                    return int(round(553 - (float(val) * (550.0 / 255.0))))
                
                self._set_sysfs("led_sync_colour", 0)
                self._set_sysfs("custum_rgb_r", 0)
                self._set_sysfs("custum_rgb_g", 0)
                self._set_sysfs("custum_rgb_b", 0)

                # Pulse Color (Primary)
                # Maps [110, 255, 0] -> 315, 3, 553
                self._set_sysfs("Led_rgb_r1", to_mode5(primary_rgb[0]))
                self._set_sysfs("Led_rgb_g1", to_mode5(primary_rgb[1]))
                self._set_sysfs("Led_rgb_b1", to_mode5(primary_rgb[2]))

                # Background Color (Secondary)
                # Maps [20, 120, 5] -> 509, 294, 542
                self._set_sysfs("Led_rgb_r2", to_mode5(secondary_rgb[0]))
                self._set_sysfs("Led_rgb_g2", to_mode5(secondary_rgb[1]))
                self._set_sysfs("Led_rgb_b2", to_mode5(secondary_rgb[2]))
            else:
                self._set_sysfs("custum_rgb_r", 0)
                self._set_sysfs("custum_rgb_g", 0)
                self._set_sysfs("custum_rgb_b", 0)
                for i in ["1", "2"]:
                    self._set_sysfs(f"Led_rgb_r{i}", primary_rgb[0])
                    self._set_sysfs(f"Led_rgb_g{i}", primary_rgb[1])
                    self._set_sysfs(f"Led_rgb_b{i}", primary_rgb[2])

        # Very important! Must be set in any case to apply the changes,
        # even if only brightness or mode changes without color changes!
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