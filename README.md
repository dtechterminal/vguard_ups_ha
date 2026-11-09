# V-Guard Smart for Home Assistant

Monitor and control V-Guard Wi-Fi smart inverters and water heaters from Home Assistant over your own MQTT broker, without the V-Guard cloud.

This is an independent community integration. It is not made, supported or endorsed by V-Guard Industries.

## Features

- **Local push.** Readings arrive over MQTT every couple of seconds; nothing is polled from the cloud.
- **Power:** mains and output voltage, output frequency, load, and whether the house runs on mains or battery.
- **Battery:** voltage, charging current, status, health, capacity and the estimated backup time.
- **Backup energy:** a running total of energy supplied from the battery, usable in the Energy dashboard.
- **Settings:** inverter mode (Normal, UPS, Equipment), turbo charging, mains changeover buzzer, appliance mode, daytime load usage, performance level and load alarm threshold.
- **Water heaters (beta):** power, target temperature (30–75 °C), water temperature and whether it's heating.
- **Discovery:** finds devices on the broker during setup.
- **Availability:** entities go unavailable when a device drops off the broker or stops reporting.

Water heater support is built from an earlier version's notes and has been checked against a simulated heater, not yet a real one. Please [open an issue](https://github.com/dtechterminal/vguard_ups_ha/issues) with a debug log if yours doesn't respond.

## Requirements

- Home Assistant 2025.3 or newer, with the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) set up.
- An MQTT broker on your network (for example the Mosquitto add-on), listening on port 1883.
- A DNS server you control (AdGuard Home, Pi-hole or your router) that the inverter uses.
- A V-Guard smart inverter or water heater already connected to your Wi-Fi with the V-Guard app.

## Point the devices at your broker

V-Guard devices connect to `vguardbox.com` with plain MQTT: inverters on port 1883, water heaters on port 8883 (without TLS). Make your broker listen on both, for example in `mosquitto.conf`:

```
listener 1883
listener 8883
allow_anonymous true
```

Then redirect `vguardbox.com` to your broker:

- **AdGuard Home:** Filters → DNS rewrites → add `vguardbox.com` → your broker's IP.
- **Pi-hole:** Local DNS → DNS Records → add `vguardbox.com` → your broker's IP.
- **Router:** add a static DNS entry for `vguardbox.com` pointing at your broker.

Then power-cycle the devices, or wait for them to reconnect. To check it worked, listen on the broker:

```bash
mosquitto_sub -h <broker-ip> -t 'device/#' -v
```

An inverter shows `device/dups/CE01/lwt/<serial> online` within a minute; its telemetry starts once Home Assistant asks for it. A water heater shows up under `device/smartewh/3013/` while it's switched on.

The V-Guard app stops working remotely while the devices talk to your broker instead of the cloud.

## Installation

### With HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Search for **V-Guard Smart**, open it, and click **Download**.
3. **Restart Home Assistant.**

Not listed yet? Open **HACS → ⋮ → Custom repositories**, add `https://github.com/dtechterminal/vguard_ups_ha` as an **Integration**, then search again.

### Manually

Download the source code of the [latest release](https://github.com/dtechterminal/vguard_ups_ha/releases/latest), copy its `custom_components/vguard_inverter` folder into your Home Assistant `config/custom_components/` folder, and restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add integration** and choose **V-Guard Smart**.
2. Choose **Find devices on MQTT**. Setup listens on the broker for a few seconds and lists the devices it heard. Switch a water heater on first; it's only on the broker while it has power.
3. Pick your device. For a water heater, setup then asks for its encryption key (see below); leave it empty to start with.

If nothing is found, choose **Enter the serial number** instead. The serial number is the last part of the device's topic, `device/dups/CE01/<serial>` or `device/smartewh/3013/<serial>`.

### Water heater encryption key

The V-Guard app encrypts water heater commands with a 16-character key and IV that V-Guard's cloud gives it for each heater. If your heater shows its readings but ignores power and temperature changes, it needs them. The V-Guard app's account API returns them with your product list (`key` and `iv`). Add them by removing the heater and setting it up again.

## Entities

### Inverter

| Entity | Type | Notes |
|---|---|---|
| Mains voltage, Output voltage | Sensor | V |
| Output frequency | Sensor | Hz |
| Load | Sensor | % of the inverter's rating; 0 while on mains |
| Power source | Sensor | Mains or Battery |
| Battery voltage, Charging current | Sensor | V, A |
| Battery status | Sensor | Normal, Charging or Low |
| Battery health | Sensor | % |
| Backup time | Sensor | Estimated minutes on battery at the current load |
| Backup energy used | Sensor | Wh supplied from the battery, total increasing |
| Battery capacity, Low battery alarm voltage | Sensor | Diagnostic |
| Wi-Fi signal, Wi-Fi network | Sensor | Diagnostic, disabled by default |
| Inverter mode | Select | Normal, UPS or Equipment |
| Turbo charging, Mains changeover buzzer, Appliance mode, Daytime load usage | Switch | Inverter settings |
| Performance level, Load alarm threshold | Number | Inverter settings |

### Water heater (beta)

| Entity | Type | Notes |
|---|---|---|
| Water heater | Water heater | On/off, target temperature 30–75 °C, current water temperature |
| Heating | Binary sensor | On while the element heats |
| Wi-Fi signal, Wi-Fi network | Sensor | Diagnostic, disabled by default |

The firmware version and Wi-Fi MAC address appear on the device page.

## How it works

The inverter publishes a retained `online`/`offline` message on `device/dups/<model>/lwt/<serial>`. After it receives `start` on `apps/dups/<model>/<serial>` it streams telemetry on `device/dups/<model>/<serial>` for about four minutes. The integration sends `start` every minute so the stream never stops. Settings are changed by sending `<code>:<value>` (for example `VG099:1`) to the same topic, and the next telemetry confirms the change.

A water heater uses the same scheme under `smartewh`: `VG094:1`/`VG094:0` switch it on and off, and `VG007:38<temperature>01001000` sets the target. With a key, commands are AES-128-CBC encrypted and base64 encoded, as the V-Guard app sends them.

## Troubleshooting

- **No devices found:** check that `vguardbox.com` resolves to your broker from the device's network, and that `mosquitto_sub` (above) shows the `lwt` topic. Water heaters only appear while switched on.
- **Entities unavailable:** the device is offline on the broker or has stopped reporting. Check its power, Wi-Fi and the broker. A water heater switched off at the wall shows as unavailable.
- **Water heater ignores commands:** add its encryption key (above).
- **Debug logging:** add this to `configuration.yaml` and restart:

  ```yaml
  logger:
    logs:
      custom_components.vguard_inverter: debug
  ```

## Upgrading from 2.x

Version 3.0 rewrites the integration. Existing entries are migrated, but most entities are new because several 2.x sensors were mapped to the wrong values (for example "Battery Percentage" was the load). Remove old entities that show as unavailable, and update dashboards and automations to the new entity IDs.

## License

The code is MIT licensed. The V-Guard name and logo belong to V-Guard Industries; see [docs/branding.md](docs/branding.md).
