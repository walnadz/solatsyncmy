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
    coordinator = WaktuSolatCoordinator(hass, entry)
    
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
    """Setup audio files in www folder."""
    # Create www/solatsyncmy directory if it doesn't exist
    solat_www_dir = os.path.join(hass.config.path("www"), "solatsyncmy")
    
    def setup_files():
        try:
            os.makedirs(solat_www_dir, exist_ok=True)
            _LOGGER.info("Created/verified www directory: %s", solat_www_dir)
            
            # Get source audio directory
            integration_dir = os.path.dirname(__file__)
            audio_dir = os.path.join(integration_dir, "audio")
            
            _LOGGER.info("Looking for audio files in: %s", audio_dir)
            
            # Copy audio files
            for audio_file in [AZAN_FILE_FAJR, AZAN_FILE_NORMAL]:
                source_path = os.path.join(audio_dir, audio_file)
                dest_path = os.path.join(solat_www_dir, audio_file)
                
                _LOGGER.info("Processing audio file: %s", audio_file)
                _LOGGER.info("Source path: %s", source_path)
                _LOGGER.info("Destination path: %s", dest_path)
                
                if os.path.exists(source_path):
                    source_size = os.path.getsize(source_path)
                    _LOGGER.info("Source file exists, size: %d bytes", source_size)
                    
                    if not os.path.exists(dest_path):
                        shutil.copy2(source_path, dest_path)
                        dest_size = os.path.getsize(dest_path)
                        _LOGGER.info("Copied %s to www folder (size: %d bytes)", audio_file, dest_size)
                    else:
                        dest_size = os.path.getsize(dest_path)
                        _LOGGER.info("Audio file already exists in www folder (size: %d bytes)", dest_size)
                        
                        # Verify file integrity by comparing sizes
                        if source_size != dest_size:
                            _LOGGER.warning("File size mismatch, re-copying %s", audio_file)
                            shutil.copy2(source_path, dest_path)
                            new_size = os.path.getsize(dest_path)
                            _LOGGER.info("Re-copied %s (new size: %d bytes)", audio_file, new_size)
                else:
                    _LOGGER.error("Audio file not found: %s", source_path)
                    
        except Exception as e:
            _LOGGER.error("Error setting up audio files: %s", e)
            raise
    
    await hass.async_add_executor_job(setup_files)


async def _play_azan_file(hass: HomeAssistant, prayer: str, media_player: str, volume: float) -> None:
    """Play azan file for the specified prayer."""
    # Determine which azan file to use
    azan_file = AZAN_FILE_FAJR if prayer == "fajr" else AZAN_FILE_NORMAL
    
    # Check if media player exists
    if not hass.states.get(media_player):
        _LOGGER.error("Media player %s not found", media_player)
        return

    # Verify the audio file exists in www folder
    www_path = os.path.join(hass.config.path("www"), "solatsyncmy", azan_file)
    if not os.path.exists(www_path):
        _LOGGER.error("Audio file not found in www folder: %s", www_path)
        _LOGGER.info("Attempting to copy audio files again...")
        await _setup_audio_files(hass)
        
        # Check again after setup
        if not os.path.exists(www_path):
            _LOGGER.error("Failed to setup audio file: %s", www_path)
            return

    _LOGGER.info("Found audio file: %s (size: %d bytes)", www_path, os.path.getsize(www_path))

    # Set volume first (skip for players that don't support it or handle it differently)
    skip_volume_players = ['androidtv', 'unifi_tv', 'android_tv']
    if volume is not None and not any(x in media_player.lower() for x in skip_volume_players):
        try:
            await hass.services.async_call(
                "media_player",
                "volume_set",
                {
                    "entity_id": media_player,
                    "volume_level": volume,
                },
            )
            _LOGGER.info("Set volume to %.1f on %s", volume, media_player)
        except Exception as e:
            _LOGGER.warning("Failed to set volume on %s: %s", media_player, e)
    else:
        _LOGGER.info("Skipping volume control for %s (not supported or handled differently)", media_player)

    # Get Home Assistant base URL for external access
    base_url = hass.config.external_url or hass.config.internal_url or "http://localhost:8123"
    
    # Try multiple path formats for different media players
    path_formats = [
        f"/local/solatsyncmy/{azan_file}",  # Standard Home Assistant www path
        f"media-source://media_source/local/solatsyncmy/{azan_file}",  # Media source format
        f"{base_url}/local/solatsyncmy/{azan_file}",  # Base URL path
        f"http://localhost:8123/local/solatsyncmy/{azan_file}",  # Direct HTTP path
        f"http://192.168.0.114:8123/local/solatsyncmy/{azan_file}",  # Direct IP for some players
    ]
    
    # Different media types for different players
    if 'unifi_tv' in media_player.lower() or 'androidtv' in media_player.lower():
        # Android TV compatible formats - prioritize MPEG formats
        media_types = ["audio/mpeg", "audio/mp3", "music", "audio", "video/mp4"]
    elif 'homepod' in media_player.lower() or 'apple' in media_player.lower():
        # HomePod and Apple devices prefer specific formats
        media_types = ["music", "audio/mp3", "audio/mpeg", "audio/aac", "audio"]
    else:
        # Standard audio formats for other players
        media_types = ["audio/mp3", "audio/mpeg", "music", "audio"]
    
    success = False
    for i, file_url in enumerate(path_formats, 1):
        for j, media_type in enumerate(media_types, 1):
            try:
                _LOGGER.info("Attempt %d.%d: Playing %s azan using path: %s with type: %s", 
                           i, j, prayer, file_url, media_type)
                
                # Special handling for HomePods - try with announce parameter first
                service_data = {
                    "entity_id": media_player,
                    "media_content_id": file_url,
                    "media_content_type": media_type,
                }
                
                # For HomePods, try with announce parameter for better compatibility
                if 'homepod' in media_player.lower() or 'apple' in media_player.lower():
                    service_data["announce"] = True
                    _LOGGER.debug("Using announce=True for Apple/HomePod device")
                
                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    service_data,
                )
                
                _LOGGER.info("Successfully sent play command for %s azan on %s using %s", 
                           prayer, media_player, media_type)
                success = True
                break
                
            except Exception as e:
                _LOGGER.debug("Attempt %d.%d failed with %s: %s", i, j, media_type, e)
                
                # If HomePod failed with announce=True, try without it
                if ('homepod' in media_player.lower() or 'apple' in media_player.lower()) and 'announce' in str(e).lower():
                    try:
                        _LOGGER.debug("Retrying HomePod without announce parameter")
                        await hass.services.async_call(
                            "media_player",
                            "play_media",
                            {
                                "entity_id": media_player,
                                "media_content_id": file_url,
                                "media_content_type": media_type,
                            },
                        )
                        _LOGGER.info("Successfully sent play command for %s azan on %s using %s (without announce)", 
                                   prayer, media_player, media_type)
                        success = True
                        break
                    except Exception as e2:
                        _LOGGER.debug("Retry without announce also failed: %s", e2)
                        continue
                continue
        
        if success:
            break
    
    if not success:
        _LOGGER.error("All attempts to play azan failed. Check your media player configuration.")
        
        # Additional debugging info
        state = hass.states.get(media_player)
        if state:
            _LOGGER.info("Media player %s state: %s", media_player, state.state)
            _LOGGER.info("Media player attributes: %s", state.attributes)
        else:
            _LOGGER.error("Media player %s not found in states", media_player)


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