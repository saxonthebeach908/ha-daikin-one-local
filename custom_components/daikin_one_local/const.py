"""Constants for the Daikin One Local integration."""

DOMAIN = "daikin_one_local"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30  # seconds
CONF_SCAN_INTERVAL = "scan_interval"

# Enumerations from Daikin One Local API v1.0
MODE_OFF = 0
MODE_HEAT = 1
MODE_COOL = 2
MODE_AUTO = 3
MODE_EMERGENCY_HEAT = 4
MODE_FAN = 5
MODE_DRY = 6

FAN_AUTO = 0  # API calls this "off": fan runs only with equipment
FAN_ON = 1
FAN_SCHEDULED = 2  # circulate per thermostat schedule

STATE_NAMES = {
    1: "cool",
    2: "overcool_dehumidify",
    3: "heat",
    4: "fan",
    5: "idle",
    6: "waiting_to_cool",
    7: "waiting_to_heat",
    8: "aux_heat",
}
