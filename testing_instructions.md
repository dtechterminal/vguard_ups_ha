# Testing Instructions for V-Guard Inverter Integration Fix

## Prerequisites
- Home Assistant installation with the V-Guard Inverter integration
- Access to Home Assistant logs
- V-Guard Inverter device connected to the same network

## Testing Steps

### 1. Install the Updated Integration
1. Back up your current V-Guard Inverter integration files
2. Replace the files with the updated versions:
   - sensor.py
   - switch.py
   - number.py
   - mode_select.py

### 2. Restart Home Assistant
```bash
# If using Home Assistant OS or Supervised
From the UI: Configuration > System > Restart

# If using Home Assistant Core
sudo systemctl restart home-assistant
```

### 3. Enable Debug Logging
Add the following to your `configuration.yaml` file:
```yaml
logger:
  default: info
  logs:
    custom_components.vguard_inverter: debug
```
Then restart Home Assistant again.

### 4. Verify Entity Initialization
1. Open the Home Assistant UI
2. Go to Developer Tools > States
3. Filter for "vguard" entities
4. Verify that all entities are listed, not just the Wi-Fi Signal entity

### 5. Monitor Entity Updates
1. Watch the Home Assistant logs for debug messages from the V-Guard Inverter integration
2. Look for messages like:
   - "Received message on device/dups/CE01/..."
   - "Keys found in data: [...]"
   - "Entities to update: X out of Y"
3. Verify that multiple entities are being updated, not just the Wi-Fi Signal entity

### 6. Test Entity Controls
1. Try controlling the switches, numbers, and select entities
2. Verify that the commands are sent correctly and the device responds

### 7. Check for Errors
1. Monitor the logs for any error messages
2. If you see warnings about "Only Wi-Fi Signal (VG011) is being updated", there may still be issues with the data format

## Troubleshooting
- If entities are still not updating correctly, check the debug logs for clues about the data format
- Ensure that the MQTT broker is correctly configured and accessible
- Verify that the V-Guard Inverter device is sending data to the MQTT broker

## Expected Results
- All entities should be properly initialized
- Multiple entities should be updated when new data is received
- No errors or warnings about entities not being updated
- Other Home Assistant integrations should work correctly alongside the V-Guard Inverter integration