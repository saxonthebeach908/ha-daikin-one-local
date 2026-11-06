# Daikin One Local

Home Assistant integration for Daikin One+ and One Touch thermostats using Daikin's official **Local API v1**. Control and status stay on your LAN, with no cloud account.

## Requirements

- A Daikin One+ or One Touch thermostat. Tested on firmware 4.1.6.
- Local API enabled on the thermostat at **Settings > Wi-Fi > Local API**.
- A fixed IP address for the thermostat. Set a DHCP reservation on your router.

## Installation (HACS)

1. In HACS, open the menu, choose **Custom repositories**, and add `https://github.com/saxonthebeach908/ha-daikin-one-local` as type **Integration**.
2. Install **Daikin One Local** and restart Home Assistant.
3. Go to **Settings > Devices & services > Add integration > Daikin One Local** and enter the thermostat's IP address. The port is 80.

## What you get

| Entity | Notes |
|---|---|
| Climate | Off, Heat, Cool and Auto (heat/cool range), depending on the modes the thermostat reports. Fan modes are Auto, On and Circulate. Emergency heat appears as a preset where it is supported. |
| Indoor temperature | The thermostat's reported space temperature, which includes the average of any remote sensors. |
| Indoor humidity | Created only when the thermostat reports humidity. |
| Equipment state | Cooling, overcool for dehumidification, heating, fan, idle, waiting, or auxiliary heat. |

Setpoints are sent in Celsius as the API requires. When the thermostat is set to Fahrenheit, values are rounded to whole degrees so that 77°F does not land as 76.9°F.

## Limitations of the Local API

- The API has no access to schedules, dehumidification targets, individual remote sensors or dealer settings. Manage those on the thermostat or in the Daikin One Home app.
- The API has no authentication. Anyone on your network can control the thermostat. Keep it on a trusted network or VLAN.
- Polling only. The default interval is 30 seconds and can be changed in the integration's options.

## API reference

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Model, brand, firmware, API version |
| GET | `/query/info` | Current state |
| POST | `/control` | `mode`, `fan`, `heatSetpoint`, `coolSetpoint` (°C), form-encoded. Returns 200 with an empty body on success. |
| POST | `/settings` | `tempUnits`, `setpointDelta` |

Enums: mode 0 off, 1 heat, 2 cool, 3 auto, 4 emergency heat, 5 fan, 6 dry. Fan 0 auto, 1 on, 2 scheduled. State 1 cool, 2 overcool for dehumidification, 3 heat, 4 fan, 5 idle, 6 waiting to cool, 7 waiting to heat, 8 aux heat.

## Development

```
pip install pytest-homeassistant-custom-component
pytest
```

Not affiliated with or endorsed by Daikin.
