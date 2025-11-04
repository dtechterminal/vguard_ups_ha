# V-Guard Inverter Integration for Home Assistant

![V-Guard Logo](icon.png)

This integration allows you to monitor and control your V-Guard Inverter from Home Assistant using MQTT.

## Features

- **Real-time monitoring** of inverter status, battery levels, and power metrics
- **Control capabilities** for inverter settings and modes
- **Intuitive icons** for all entities to improve dashboard visualization
- **Graphical history display** for voltage, ampere, signal strength, temperature, battery, and energy sensors using Home Assistant's built-in graphs
- **Thread-safe implementation** to prevent Home Assistant crashes
- **HACS compatible** for easy installation and updates

## Prerequisites

### DNS Setup (Required)

V-Guard inverters try to connect to `vguardbox.com` for their cloud service. To use this local integration, you need to redirect this domain to your local MQTT broker.

**Option 1: Using Pi-hole or AdGuard Home**
1. Go to your Pi-hole/AdGuard admin panel
2. Navigate to Local DNS → DNS Records (or Custom filtering → DNS rewrites)
3. Add a new record:
   - Domain: `vguardbox.com`
   - IP Address: `192.168.0.4` (or your MQTT broker IP)
4. Save the record

**Option 2: Router DNS Override**
1. Access your router's admin panel
2. Look for DNS settings or Local DNS
3. Add a static DNS entry for `vguardbox.com` pointing to your MQTT broker IP
4. Save and restart your router if needed

**Option 3: /etc/hosts file** (for testing only)
Add to your `/etc/hosts` file:
```
192.168.0.4  vguardbox.com
```

**Verify DNS Setup:**
```bash
ping vguardbox.com
# Should resolve to your local MQTT broker IP
```

### MQTT Broker Setup

You need an MQTT broker running on your network and configured in Home Assistant:

1. **Install Mosquitto** (if not already installed):
   - Add-on method: Install "Mosquitto broker" from Home Assistant add-ons
   - Or run Mosquitto separately on your network

2. **Configure MQTT in Home Assistant**:
   - Go to **Settings** → **Devices & Services**
   - Click **Add Integration** → Search for "MQTT"
   - Configure broker settings:
     - Broker: IP where Mosquitto is running (e.g., `192.168.0.4` or `localhost` if using add-on)
     - Port: `1883`
     - Leave username/password blank if not configured

3. **Verify MQTT is working**:
   - Go to **Developer Tools** → **MQTT**
   - Try listening to topic: `device/dups/CE01/#`
   - You should see messages from your inverter

**Important**: The MQTT broker configured in Home Assistant must be the same one your inverter connects to (via DNS redirect).

## Installation

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Add"
6. Search for "V-Guard Inverter" and install it
7. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `vguard_inverter` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

1. Go to Configuration > Integrations
2. Click the "+" button to add a new integration
3. Search for "V-Guard Inverter"
4. Choose setup method:
   - **Automatic Discovery (Recommended)**: The integration will automatically scan for V-Guard inverters on your MQTT broker
   - **Manual Configuration**: Enter your inverter's IP address, MQTT port, and serial number manually
5. Click "Submit"

## Available Entities

### Sensors

| Entity | Description | Icon | Graph Display |
|--------|-------------|------|--------------|
| Wi-Fi Signal | Signal strength of the inverter's Wi-Fi connection | mdi:wifi | Yes |
| Temperature | Inverter temperature | mdi:thermometer | Yes |
| Battery Voltage | Current battery voltage | mdi:battery-outline | Yes |
| Battery Percentage | Current battery charge level | mdi:battery-charging-outline | Yes |
| Input Voltage | Input voltage from the mains | mdi:flash | Yes |
| Output Voltage | Output voltage to connected devices | mdi:flash-outline | Yes |
| Charging Current | Current flowing to the battery | mdi:current-ac | Yes |
| Total Energy | Total energy consumption | mdi:lightning-bolt | Yes |
| Energy Usage | Current energy usage | mdi:power-plug | Yes |
| System Uptime | Time since last restart | mdi:timer-outline | No |
| Battery Health | Health status of the battery | mdi:heart-pulse | No |
| Wi-Fi MAC ID | MAC address of the inverter's Wi-Fi module | mdi:access-point-network | No |

### Controls

| Entity | Description | Icon | Type |
|--------|-------------|------|------|
| Inverter Mode | Select between Normal, UPS, or Equipment modes | mdi:home-lightning-bolt-outline | Select |
| Performance Level | Adjust the performance level (1-7) | mdi:speedometer | Number |
| Load Alarm Threshold | Set the threshold for load alarms (50-100%) | mdi:alert-circle-outline | Number |
| Turbo Charging | Toggle turbo charging mode | mdi:battery-charging-high | Switch |
| Advance Low Battery Alarm | Toggle advance low battery alarm | mdi:battery-alert | Switch |
| Mains Changeover Buzzer | Toggle the buzzer for mains changeover | mdi:volume-high | Switch |
| Appliance Mode | Toggle appliance mode | mdi:power-standby | Switch |
| Daytime Load Usage | Toggle daytime load usage | mdi:weather-sunny | Switch |
| Battery Type Lock | Lock/unlock battery type switching | mdi:lock | Switch |

## Recent Changes

### Version 2.2.4
- **Fixed Unknown Values**: Entities now become available after receiving first MQTT message, even if their specific value isn't in that message
- **Better Availability Logic**: All entities (sensors, switches, selects, numbers) now properly show as available instead of unknown
- **Improved User Experience**: Entities will show their last known value or default instead of remaining unavailable indefinitely

### Version 2.2.3
- **Fixed MQTT Publishing**: Corrected MQTT API usage in `__init__.py` for start command
- **Entity Availability**: Added proper availability tracking - entities now show as available once they receive data
- **All Entities Working**: Sensors, switches, selects, and numbers now properly update from MQTT messages

### Version 2.2.2
- **Critical Fix**: Fixed type hint syntax errors that prevented entities from loading
- Changed `callable | None` to `Optional[Callable]` for Python 3.9+ compatibility
- All platforms now load correctly and entities appear in Home Assistant

### Version 2.2.1
- **Better Error Handling**: Enhanced MQTT subscription error handling
- **Improved Logging**: More detailed debug messages for troubleshooting
- **Documentation**: Added MQTT broker setup guide and testing documentation
- **Test Script**: Included test_discovery.py for local testing before deployment

### Version 2.2.0
- **Improved Discovery**: Better MQTT topic handling for both telemetry and LWT messages
- **DNS Setup Guide**: Added detailed instructions for redirecting vguardbox.com to local MQTT broker
- **Better Logging**: Enhanced debug logging for troubleshooting discovery issues
- **Validation**: Added serial number validation during discovery
- **Prerequisites Section**: Documented required DNS and MQTT setup

### Version 2.1.1
- **Fixed Default Port**: Changed default MQTT port from 8883 to 1883 (standard MQTT port)
- **Tested with Real Device**: Verified working with actual V-Guard inverter hardware

### Version 2.1.0
- **Automatic Device Discovery**: Integration now automatically detects V-Guard inverters on MQTT
- **Improved Setup Flow**: Choose between automatic discovery or manual configuration
- **Better User Experience**: No need to manually enter serial numbers - just select from discovered devices

### Version 2.0.0
- **Major Refactoring**: Completely rebuilt to follow modern Home Assistant patterns
- **MQTT Integration**: Now uses Home Assistant's built-in MQTT component instead of paho-mqtt
- **Better Async Support**: All entities use proper async/await patterns
- **Improved Device Registry**: Better device information and organization
- **Translation Support**: Added strings.json and translations for better UI
- **Cleaner Code**: Simplified entity management with better separation of concerns
- **Enhanced Error Handling**: Better logging and error recovery
- **Type Hints**: Added proper type annotations for better code quality

### Version 1.0.3
- Extended graphical history display to more sensors (WiFi signal, temperature, battery, energy)
- Fixed Wi-Fi MAC address formatting to display in standard colon-separated format
- Fixed Turbo charging icon display issue
- Fixed Performance level and Load alarm Threshold "unknown" states
- Combined duplicate switches and sensors for cleaner interface
- Updated documentation with entity types and improved descriptions

## Troubleshooting

### Automatic Discovery Not Finding Devices

1. **Verify DNS Setup**: Make sure `vguardbox.com` resolves to your MQTT broker
   ```bash
   ping vguardbox.com
   # Should show your MQTT broker IP (e.g., 192.168.0.4)
   ```

2. **Check MQTT Messages**: Verify the inverter is publishing data
   ```bash
   mosquitto_sub -h 192.168.0.4 -p 1883 -t "device/dups/CE01/#" -v
   ```
   You should see messages like `device/dups/CE01/{serial}`

3. **Enable Debug Logging**: Add to your `configuration.yaml` and restart HA:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.vguard_inverter: debug
       homeassistant.components.mqtt: debug
   ```

   Then check logs at **Settings** → **System** → **Logs** and look for:
   - `"Starting MQTT discovery"` - Discovery started
   - `"Received discovery message"` - Messages are being received
   - `"Discovered V-Guard inverter"` - Device found
   - Any error messages

4. **Check MQTT Integration**: Ensure Home Assistant's MQTT integration is configured and connected

5. **Use Manual Configuration**: If discovery fails, you can manually enter:
   - Host: Your MQTT broker IP (e.g., `192.168.0.4`)
   - Port: `1883`
   - Serial: Your inverter serial number (visible in MQTT topic)

### Other Issues

1. Check that your inverter is connected to the same network
2. Verify that the MQTT broker is running and accessible
3. Check the Home Assistant logs for error messages
4. Restart the inverter if needed

## Support

If you need help or want to report a bug, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Thanks to the Home Assistant community for their support and guidance