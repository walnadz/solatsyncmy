"""Constants for the Waktu Solat Malaysia integration."""
from homeassistant.const import Platform

# Integration domain
DOMAIN = "solatsyncmy"

# Platforms
PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

# API Configuration
API_BASE_URL = "https://api.waktusolat.app"
API_TIMEOUT = 30

# Default values
DEFAULT_ZONE = "SGR01"  # Selangor default
DEFAULT_NAME = "Waktu Solat Malaysia"
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds

# Configuration keys
CONF_ZONE = "zone"
CONF_AZAN_ENABLED = "azan_enabled"
CONF_AZAN_FAJR_ENABLED = "azan_fajr_enabled"
CONF_AZAN_DHUHR_ENABLED = "azan_dhuhr_enabled"
CONF_AZAN_ASR_ENABLED = "azan_asr_enabled"
CONF_AZAN_MAGHRIB_ENABLED = "azan_maghrib_enabled"
CONF_AZAN_ISHA_ENABLED = "azan_isha_enabled"
CONF_MEDIA_PLAYER = "media_player_entity_id"
CONF_AZAN_VOLUME = "azan_volume"

# Prayer names
PRAYER_TIMES = ["fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]
AZAN_PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]  # Syuruk doesn't have azan

# Device info
MANUFACTURER = "Waktu Solat Malaysia"
MODEL = "Prayer Times API"
SW_VERSION = "1.0.0"

# Icons
ICON_MOSQUE = "mdi:mosque"
ICON_CLOCK = "mdi:clock"
ICON_SUNRISE = "mdi:weather-sunset-up"
ICON_SUNSET = "mdi:weather-sunset-down"
ICON_MOON = "mdi:moon-waning-crescent"

# Prayer time icons mapping
PRAYER_ICONS = {
    "fajr": "mdi:weather-sunset-up",
    "syuruk": "mdi:weather-sunny",
    "dhuhr": "mdi:weather-sunny",
    "asr": "mdi:weather-partly-cloudy",
    "maghrib": "mdi:weather-sunset-down",
    "isha": "mdi:moon-waning-crescent",
}

# Azan file paths (relative to integration directory)
AZAN_FILE_NORMAL = "sounds/azan.mp3"
AZAN_FILE_FAJR = "sounds/azanfajr.mp3"

# Service names
SERVICE_PLAY_AZAN = "play_azan"

# Attributes
ATTR_NEXT_PRAYER = "next_prayer"
ATTR_NEXT_PRAYER_TIME = "next_prayer_time"
ATTR_TIME_TO_NEXT_PRAYER = "time_to_next_prayer"
ATTR_ZONE = "zone"
ATTR_HIJRI_DATE = "hijri_date"
ATTR_PRAYER_TIMES = "prayer_times" 