# SilkyRGB
#### The Smoothest light effects in the Handheld World™ [WIP]

RGB Manager Daemon that completely takes over control of all RGB leds on supported devices.

#### Highlights and features:
 * Silky Smooth effects, transitions and animations
 * Unique effects available for different RGB layouts
 * Refined Colors and Palettes
 * Configuration API
 * Notification API for battery warnings and system feedback
 * Input based effects
 * Low resource use (1-5% on one core, 20MB RAM)

#### Supported OS:
 * Knulli Alpha

#### Supported Devices:
 * all Anbernic H700 devices with RGB
 * A133P devices: TrimUI Smart Pro

#### WIP Devices:
 * A133P: Trimui Brick
 * SD865: Retroid Pocket 5

### API Endpoints

Base URL: `http://localhost:1235`

#### Configuration

* **GET** `/reload-config`: Forces the controller to reload and apply settings from the configuration file.  
* **POST** `/set-config`: Sets a single configuration option.  
  * Payload: `[key] [value]` (e.g., `brightness.max 100`)  
* **GET** `/get-settings`: Retrieves all available configuration settings metadata.

#### Light Control & Discovery

This section handles triggering effects and discovering available animations/colors.

* **POST** `/animation`: Triggers a sequence of effects, wrapped in smooth fade-in/out.  
  * Payload: Semicolon-separated commands (e.g., `cheevo; blink 2 #FF00FF`)  
  * Command Formats:  
    1. Preset: `[preset_name]` (e.g., `battery_charging`)  
    2. Custom Noti: `[notification_name] [count] [hex_color]`  
* **GET** `/get-modes˙`: Retrieves available continuous animation modes.  
* **GET** `/get-animations`: Retrieves available temporary notification effects.  
* **GET** `/get-palettes`: Retrieves available named color palettes.
* **GET** `/get-colors`: Retrieves available named colors.

#### Device Status Updates

These endpoints push status changes from the handheld system to the controller.

* **POST** `/update-battery-state`: Updates battery percentage and charging state, triggering alerts based on config.  
  * Payload: `[percentage] [state]` (e.g., `75 Discharging`)  
* **POST** `/update-screen-state`: Updates screen brightness for adaptive lighting control.  
  * Payload: `[brightness_value`] (Integer `0-100`)

#### System Management

* **GET** `/kill`: Triggers a final system shutdown animation and terminates the daemon.
