# V-Guard Inverter for Home Assistant

Monitor and configure a V-Guard Wi-Fi smart inverter from Home Assistant over your own MQTT broker, without the V-Guard cloud.

This is an independent community integration. It is not made, supported or endorsed by V-Guard Industries.

## Features

- **Local push.** Readings arrive over MQTT every couple of seconds; nothing is polled from the cloud.
- **Power:** mains and output voltage, output frequency, load, and whether the house runs on mains or battery.
- **Battery:** voltage, charging current, status, health, capacity and the estimated backup time.
- **Backup energy:** a running total of energy supplied from the battery, usable in the Energy dashboard.
- **Settings:** inverter mode (Normal, UPS, Equipment), turbo charging, mains changeover buzzer, appliance mode, daytime load usage, performance level and load alarm threshold.
- **Discovery:** finds inverters on the broker during setup.
- **Availability:** entities go unavailable when the inverter drops off the broker or stops reporting.

## Requirements

- Home Assistant 2025.3 or newer, with the [MQTT integration](https://www.home-assistant.io/integrations/mqtt/) set up.
- An MQTT broker on your network (for example the Mosquitto add-on), listening on port 1883.
- A DNS server you control (AdGuard Home, Pi-hole or your router) that the inverter uses.
- A V-Guard smart inverter already connected to your Wi-Fi with the V-Guard app.

## Point the inverter at your broker

The inverter's Wi-Fi module connects to `vguardbox.com` on port 1883 (plain MQTT). Redirect that name to your broker:

- **AdGuard Home:** Filters → DNS rewrites → add `vguardbox.com` → your broker's IP.
- **Pi-hole:** Local DNS → DNS Records → add `vguardbox.com` → your broker's IP.
- **Router:** add a static DNS entry for `vguardbox.com` pointing at your broker.

Then power-cycle the inverter, or wait for it to reconnect. To check it worked, listen on the broker:

```bash
mosquitto_sub -h <broker-ip> -t 'device/dups/#' -v
```

You should see `device/dups/CE01/lwt/<serial> online` within a minute. Telemetry starts once Home Assistant asks for it.

The V-Guard app stops working remotely while the inverter talks to your broker instead of the cloud.

## Installation

### With HACS (recommended)

1. Open **HACS** in Home Assistant.
2. Search for **V-Guard Inverter**, open it, and click **Download**.
3. **Restart Home Assistant.**

Not listed yet? Open **HACS → ⋮ → Custom repositories**, add `https://github.com/dtechterminal/vguard_ups_ha` as an **Integration**, then search again.

### Manually

Download the source code of the [latest release](https://github.com/dtechterminal/vguard_ups_ha/releases/latest), copy its `custom_components/vguard_inverter` folder into your Home Assistant `config/custom_components/` folder, and restart Home Assistant.

## Setup

1. Go to **Settings → Devices & services → Add integration** and choose **V-Guard Inverter**.
2. Choose **Find inverters on MQTT**. Setup listens on the broker for a few seconds and lists the inverters it heard.
3. Pick your inverter.

If nothing is found, choose **Enter the serial number** instead. The serial number is the last part of the inverter's topic, `device/dups/CE01/<serial>`.

## Entities

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

The firmware version and Wi-Fi MAC address appear on the device page.

## How it works

The inverter publishes a retained `online`/`offline` message on `device/dups/<model>/lwt/<serial>`. After it receives `start` on `apps/dups/<model>/<serial>` it streams telemetry on `device/dups/<model>/<serial>` for about four minutes. The integration sends `start` every minute so the stream never stops. Settings are changed by sending `<code>:<value>` (for example `VG099:1`) to the same topic, and the next telemetry confirms the change.

## Troubleshooting

- **No inverters found:** check that `vguardbox.com` resolves to your broker from the inverter's network, and that `mosquitto_sub` (above) shows the `lwt` topic.
- **Entities unavailable:** the inverter is offline on the broker or has stopped streaming. Check its Wi-Fi and the broker.
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
