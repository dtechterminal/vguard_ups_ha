# Release Notes

## Version 2.1.1

### Changes
- **Fixed Default Port**: Changed default MQTT port from 8883 to 1883 (standard MQTT port)
- **Tested with Real Device**: Verified working with actual V-Guard inverter hardware

### Installation
1. Update the integration through HACS
2. Restart Home Assistant
3. Reconfigure if needed with the correct port (1883)

---

## Version 2.1.0

### New Features
- **Automatic Device Discovery**: Integration now automatically detects V-Guard inverters on MQTT
- **Improved Setup Flow**: Choose between automatic discovery or manual configuration
- **Better User Experience**: No need to manually enter serial numbers - just select from discovered devices

### How to Use
1. Go to Configuration > Integrations
2. Add "V-Guard Inverter"
3. Choose "Automatic Discovery" and wait 30 seconds
4. Select your inverter from the list
5. Done!

---

## Version 2.0.0

### Major Refactoring
- **MQTT Integration**: Now uses Home Assistant's built-in MQTT component instead of paho-mqtt
- **Better Async Support**: All entities use proper async/await patterns
- **Improved Device Registry**: Better device information and organization
- **Translation Support**: Added strings.json and translations for better UI
- **Cleaner Code**: Simplified entity management with better separation of concerns
- **Enhanced Error Handling**: Better logging and error recovery
- **Type Hints**: Added proper type annotations for better code quality

### Breaking Changes
- This is a major refactor. You may need to remove and re-add the integration after updating.
