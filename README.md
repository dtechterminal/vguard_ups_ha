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

If you encounter any issues:

1. Enable debug logging by adding the following to your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.vguard_inverter: debug
   ```
2. Check that your inverter is connected to the same network
3. Verify that the MQTT connection is working
4. Check the Home Assistant logs for error messages

## Support

If you need help or want to report a bug, please open an issue on GitHub.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- Thanks to the Home Assistant community for their support and guidance