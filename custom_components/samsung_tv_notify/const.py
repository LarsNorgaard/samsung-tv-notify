"""Constants for Samsung TV Notify."""

DOMAIN = "samsung_tv_notify"

# The HA Notify Tizen app installed on the TV (see tv-app/ in the repository).
APP_ID = "HAnotifyPC.HANotify"

CONF_AUTO_START = "auto_start"
CONF_DISPLAY_TIME = "display_time"

DEFAULT_PORT = 8099
DEFAULT_AUTO_START = True
DEFAULT_DISPLAY_TIME = 10

# Samsung's open REST API on the TV (device info and app launch, no pairing).
TV_API_PORT = 8001

# How long to wait for the notification service after launching the app.
START_TIMEOUT = 20
SCAN_INTERVAL_SECONDS = 60
