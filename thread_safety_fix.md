# Thread Safety Fix for V-Guard Inverter Integration

## Issue Description

The V-Guard Inverter integration was experiencing thread safety issues with the following error:

```
ERROR (paho-mqtt-client-) [custom_components.vguard_inverter.sensor] Error processing telemetry: Detected code that calls async_write_ha_state from a thread other than the event loop, which may cause Home Assistant to crash or data to corrupt.
```

This error occurred because the integration was calling `async_write_ha_state()` from MQTT callback threads, which run outside of Home Assistant's main event loop. According to Home Assistant's documentation on [asyncio thread safety](https://developers.home-assistant.io/docs/asyncio_thread_safety/#async_write_ha_state), this can cause crashes or data corruption.

## Root Cause

The issue was present in multiple files:

1. In `sensor.py`, the MQTT message handler was directly calling `hass.async_create_task(entity.async_write_ha_state())` from the MQTT callback thread.
2. In `switch.py`, the `turn_on` and `turn_off` methods were using `asyncio.run_coroutine_threadsafe(self.async_write_ha_state(), self._hass.loop)`.
3. In `number.py`, the `set_value` method was using `asyncio.run_coroutine_threadsafe(self.async_write_ha_state(), self._hass.loop)`.
4. In `mode_select.py`, the `select_option` method was using `asyncio.run_coroutine_threadsafe(self.async_write_ha_state(), self._hass.loop)`.

All of these approaches are not thread-safe because they directly call `async_write_ha_state()` from a non-event-loop thread.

## Solution

The fix involved creating a thread-safe helper function in `sensor.py` that properly schedules entity state updates on the event loop:

```python
def schedule_entity_update(hass, entity):
    """Schedule entity state update on the event loop in a thread-safe way."""
    def _update_entity_state():
        """Update entity state on the event loop."""
        entity.async_schedule_update_ha_state()
    
    # Use call_soon_threadsafe to schedule the update on the event loop
    hass.loop.call_soon_threadsafe(_update_entity_state)
```

This function uses `hass.loop.call_soon_threadsafe()` to schedule a function that updates the entity state on the event loop, which is the recommended approach for thread safety in Home Assistant.

The function was then used in all four component files to replace the non-thread-safe approaches:

1. In `sensor.py`, replaced `hass.async_create_task(entity.async_write_ha_state())` with `schedule_entity_update(hass, entity)`.
2. In `switch.py`, replaced `asyncio.run_coroutine_threadsafe(self.async_write_ha_state(), self._hass.loop)` with `schedule_entity_update(self._hass, self)`.
3. In `number.py`, replaced `asyncio.run_coroutine_threadsafe(self.async_write_ha_state(), self._hass.loop)` with `schedule_entity_update(self._hass, self)`.
4. In `mode_select.py`, replaced `asyncio.run_coroutine_threadsafe(self.async_write_ha_state(), self._hass.loop)` with `schedule_entity_update(self._hass, self)`.

## Benefits

This fix ensures that:

1. Entity state updates are properly scheduled on the event loop.
2. The integration follows Home Assistant's thread safety guidelines.
3. The risk of crashes or data corruption is eliminated.
4. All entities can be updated correctly without thread safety issues.

## Testing

To verify that the fix works correctly:

1. Check the Home Assistant logs for the thread safety error message. It should no longer appear.
2. Verify that all entities are updating correctly.
3. Test the functionality of switches, numbers, and selects to ensure they work as expected.