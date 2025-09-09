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
CONF_AZAN_SUBUH_ENABLED = "azan_subuh_enabled"
CONF_AZAN_ZOHOR_ENABLED = "azan_zohor_enabled"
CONF_AZAN_ASAR_ENABLED = "azan_asar_enabled"
CONF_AZAN_MAGHRIB_ENABLED = "azan_maghrib_enabled"
CONF_AZAN_ISYAK_ENABLED = "azan_isyak_enabled"
CONF_MEDIA_PLAYER = "media_player_entity_id"
CONF_AZAN_VOLUME = "azan_volume"
CONF_LOCAL_AUDIO_PATH = "local_audio_path"  # For local audio files

# Prayer names mapping (API uses English, display uses Malay)
PRAYER_TIMES = ["fajr", "syuruk", "dhuhr", "asr", "maghrib", "isha"]
AZAN_PRAYERS = ["fajr", "dhuhr", "asr", "maghrib", "isha"]  # Syuruk doesn't have azan

# Prayer name translations
PRAYER_NAMES = {
    "fajr": "Subuh",
    "syuruk": "Syuruk", 
    "dhuhr": "Zohor",
    "asr": "Asar",
    "maghrib": "Maghrib",
    "isha": "Isyak",
}

# Prayer order for controls (global automation first, then prayer order)
PRAYER_ORDER = ["automation", "fajr", "dhuhr", "asr", "maghrib", "isha"]

# Device info
MANUFACTURER = "Waktu Solat Malaysia"
MODEL = "Prayer Times API"
SW_VERSION = "1.0.11"

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

# Azan file names (files will be copied to www/solatsyncmy/)
AZAN_FILE_NORMAL = "azan.mp3"
AZAN_FILE_FAJR = "azanfajr.mp3"  # Different azan for Subuh

# Local audio paths (for manual file placement)
LOCAL_AUDIO_PATHS = [
    "/config/www/",
    "/config/media/",
    "/media/",
    "/share/",
]

# Service names
SERVICE_PLAY_AZAN = "play_azan"
SERVICE_TEST_AUDIO = "test_audio"

# Attributes
ATTR_NEXT_PRAYER = "next_prayer"
ATTR_NEXT_PRAYER_TIME = "next_prayer_time"
ATTR_TIME_TO_NEXT_PRAYER = "time_to_next_prayer"
ATTR_ZONE = "zone"
ATTR_HIJRI_DATE = "hijri_date"
ATTR_PRAYER_TIMES = "prayer_times" 