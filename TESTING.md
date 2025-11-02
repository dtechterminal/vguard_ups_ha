# Testing Guide for V-Guard Integration

## Test Discovery Logic Locally

Before deploying to Home Assistant, test the discovery logic:

### 1. Test MQTT Discovery

```bash
cd /tmp
python3 test_discovery.py
```

This will:
- Connect to the MQTT broker at 192.168.0.4:1883
- Subscribe to `device/dups/CE01/#`
- Listen for 10 seconds
- Report any discovered devices

**Expected Output:**
```
✓ Connected to MQTT broker
✓ Subscribed to topic: device/dups/CE01/#
📨 Received message on topic: device/dups/CE01/lwt/XXXX
   ✓ Discovered new device: XXXX
Discovery Complete - Found 1 device(s)
```

### 2. Verify MQTT Messages

```bash
mosquitto_sub -h 192.168.0.4 -p 1883 -t "device/dups/CE01/#" -v
```

You should see:
- `device/dups/CE01/lwt/{serial}` with payload "online"
- `device/dups/CE01/{serial}` with JSON telemetry data

### 3. Test in Home Assistant

1. **Enable Debug Logging** in `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.vguard_inverter: debug
       homeassistant.components.mqtt: debug
   ```

2. **Restart Home Assistant**

3. **Add Integration**:
   - Settings → Devices & Services → Add Integration
   - Search "V-Guard Inverter"
   - Choose "Automatic Discovery"

4. **Check Logs** (Settings → System → Logs):
   Look for these messages:
   - ✅ `"Starting MQTT discovery on topic: device/dups/CE01/#"`
   - ✅ `"MQTT integration found in Home Assistant"`
   - ✅ `"Successfully subscribed to MQTT topic"`
   - ✅ `"Received discovery message on topic: ..."`
   - ✅ `"✓ Discovered V-Guard inverter: XXXX"`
   - ✅ `"Discovery complete. Found 1 device(s)"`

5. **If No Devices Found**, check:
   - ❌ `"MQTT integration is not set up"` → Configure MQTT integration first
   - ❌ `"Failed to subscribe to MQTT"` → Check MQTT broker configuration
   - ❌ No "Received discovery message" → Inverter not publishing or wrong broker

### 4. Common Issues

**Issue**: Discovery finds no devices
**Solutions**:
1. Verify MQTT integration is configured with correct broker IP
2. Check DNS: `vguardbox.com` → MQTT broker IP
3. Test MQTT manually: `mosquitto_sub -h <broker_ip> -p 1883 -t "device/dups/CE01/#" -v`
4. Check HA logs for errors

**Issue**: MQTT integration not found
**Solution**: Configure MQTT integration in Home Assistant first

**Issue**: Wrong broker IP
**Solution**: Use manual configuration and specify correct broker IP

## Testing Checklist

Before releasing a version:

- [ ] Test discovery script finds devices
- [ ] Verify MQTT messages are received
- [ ] Test in Home Assistant with debug logging
- [ ] Check automatic discovery works
- [ ] Test manual configuration works
- [ ] Verify all sensors update
- [ ] Test switches/selects/numbers work
- [ ] Check error handling with no MQTT
- [ ] Verify documentation is accurate
