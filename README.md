# V-Guard Inverter Integration for Home Assistant

![V-Guard Logo](icon.png)

This integration allows you to monitor and control your V-Guard Inverter from Home Assistant using MQTT.

## Features

- **Real-time monitoring** of inverter status, battery levels, and power metrics
- **Control capabilities** for inverter settings and modes
- **Intuitive icons** for all entities to improve dashboard visualization
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
4. Enter your inverter's IP address, MQTT port, and serial number
5. Click "Submit"

## Available Entities

### Sensors

| Entity | Description | Icon |
|--------|-------------|------|
| Wi-Fi Signal | Signal strength of the inverter's Wi-Fi connection | mdi:wifi |
| Temperature | Inverter temperature | mdi:thermometer |
| Battery Voltage | Current battery voltage | mdi:battery-outline |
| Battery Percentage | Current battery charge level | mdi:battery-charging-outline |
| Input Voltage | Input voltage from the mains | mdi:flash |
| Output Voltage | Output voltage to connected devices | mdi:flash-outline |
| Total Energy | Total energy consumption | mdi:lightning-bolt |
| Energy Usage | Current energy usage | mdi:power-plug |
| System Uptime | Time since last restart | mdi:timer-outline |
| Battery Health | Health status of the battery | mdi:heart-pulse |

### Controls

| Entity | Description | Icon |
|--------|-------------|------|
| Inverter Mode | Select between Normal, UPS, or Equipment modes | mdi:home-lightning-bolt-outline |
| Performance Level | Adjust the performance level (1-5) | mdi:speedometer |
| Load Alarm Threshold | Set the threshold for load alarms (50-100%) | mdi:alert-circle-outline |
| Turbo Charging | Toggle turbo charging mode | mdi:turbocharger |
| Advance Low Battery Alarm | Toggle advance low battery alarm | mdi:battery-alert |
| Mains Changeover Buzzer | Toggle the buzzer for mains changeover | mdi:volume-high |
| Appliance Mode | Toggle appliance mode | mdi:power-standby |
| Daytime Load Usage | Toggle daytime load usage | mdi:weather-sunny |
| Battery Type Lock | Lock/unlock battery type switching | mdi:lock |

## Recent Changes

### Version 1.0.1
- Added appropriate icons for all entities
- Removed hardcoded configuration values
- Made the integration HACS compatible
- Added V-Guard logo as integration icon
- Improved thread safety to prevent Home Assistant crashes

### Version 1.0.0
- Initial release
- Basic monitoring and control capabilities
- MQTT communication with the inverter

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
- V-Guard for making their inverter MQTT API available