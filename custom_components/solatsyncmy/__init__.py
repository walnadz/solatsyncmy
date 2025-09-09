"""Waktu Solat Malaysia integration for Home Assistant."""
import logging
import os
import shutil

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers import device_registry as dr
import voluptuous as vol

from .const import (
    DOMAIN,
    AZAN_FILE_FAJR,
    AZAN_FILE_NORMAL,
    CONF_MEDIA_PLAYER,
    CONF_AZAN_VOLUME,
)
from .coordinator import WaktuSolatCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
]

# Service schema for play_azan
PLAY_AZAN_SERVICE_SCHEMA = vol.Schema({
    vol.Required("prayer"): vol.In(["fajr", "dhuhr", "asr", "maghrib", "isha"]),
    vol.Optional("media_player"): str,
    vol.Optional("volume", default=0.7): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waktu Solat Malaysia from a config entry."""
    # Copy audio files to www folder for media player access
    await _setup_audio_files(hass)
    
    # Create coordinator
    coordinator = WaktuSolatCoordinator(hass, entry.data["zone"])
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register device
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Solat Sync MY",
        manufacturer="Solat Sync MY",
        model="Prayer Times",
        sw_version="1.0.3",
    )

    # Register the play_azan service
    async def handle_play_azan(call: ServiceCall) -> None:
        """Handle the play_azan service call."""
        prayer = call.data["prayer"]
        media_player = call.data.get("media_player")
        volume = call.data.get("volume", 0.7)
        
        # If no media player specified, try to get from config
        if not media_player:
            media_player = entry.options.get(CONF_MEDIA_PLAYER)
            
        if not media_player:
            _LOGGER.error("No media player specified for play_azan service")
            return
            
        await _play_azan_file(hass, prayer, media_player, volume)

    hass.services.async_register(
        DOMAIN,
        "play_azan",
        handle_play_azan,
        schema=PLAY_AZAN_SERVICE_SCHEMA,
    )

    
    return True


async def _setup_audio_files(hass: HomeAssistant) -> None:
    """Copy audio files to www folder for media player access."""
    # Create www/solatsyncmy directory
    www_dir = hass.config.path("www")
    solat_www_dir = os.path.join(www_dir, "solatsyncmy")
    
    # Create directory if it doesn't exist
    os.makedirs(solat_www_dir, exist_ok=True)
    
    # Get source audio directory
    integration_dir = os.path.dirname(__file__)
    audio_dir = os.path.join(integration_dir, "audio")
    
    # Copy audio files
    for audio_file in [AZAN_FILE_FAJR, AZAN_FILE_NORMAL]:
        source_path = os.path.join(audio_dir, audio_file)
        dest_path = os.path.join(solat_www_dir, audio_file)
        
        if os.path.exists(source_path):
            if not os.path.exists(dest_path):
                shutil.copy2(source_path, dest_path)
                _LOGGER.info("Copied %s to www folder", audio_file)
        else:
            _LOGGER.error("Audio file not found: %s", source_path)


async def _play_azan_file(hass: HomeAssistant, prayer: str, media_player: str, volume: float) -> None:
    """Play azan file for the specified prayer."""
    # Determine which azan file to use
    azan_file = AZAN_FILE_FAJR if prayer == "fajr" else AZAN_FILE_NORMAL
    
    # Check if media player exists
    if not hass.states.get(media_player):
        _LOGGER.error("Media player %s not found", media_player)
        return

    # Set volume
    await hass.services.async_call(
        "media_player",
        "volume_set",
        {
            "entity_id": media_player,
            "volume_level": volume,
        },
    )

    # Play azan using the www folder path
    file_url = f"/local/solatsyncmy/{azan_file}"
    await hass.services.async_call(
        "media_player",
        "play_media",
        {
            "entity_id": media_player,
            "media_content_id": file_url,
            "media_content_type": "audio/mp3",
        },
    )
    
    _LOGGER.info("Playing %s azan on %s", prayer, media_player)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Waktu Solat Malaysia integration")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # If this was the last config entry, remove the domain entirely and services
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            # Remove services when no more integrations are loaded
            if hass.services.has_service(DOMAIN, "play_azan"):
                hass.services.async_remove(DOMAIN, "play_azan")
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry) 