"""Waktu Solat Malaysia integration for Home Assistant."""
import logging
import os
import shutil
import asyncio

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

# Services are defined in services.yaml for UI integration


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

    # Register services
    await _register_services(hass)

    
    return True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Solat Sync MY component."""
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
        f"/media/local/solatsyncmy/{azan_file}",  # Alternative media path
        f"media-source://media_source/local/{azan_file}",  # Direct media source
        f"/local/{azan_file}",  # Direct local path (if files are in root www)
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
            services_to_remove = ["refresh_prayer_times", "play_azan", "test_audio"]
            for service_name in services_to_remove:
                if hass.services.has_service(DOMAIN, service_name):
                    hass.services.async_remove(DOMAIN, service_name)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry) 

async def _register_services(hass: HomeAssistant) -> None:
    """Register services for the integration."""
    
    async def handle_refresh_prayer_times(call):
        """Handle the refresh_prayer_times service call."""
        entity_id = call.data.get("entity_id")
        
        _LOGGER.info("Service call: refresh_prayer_times for entity %s", entity_id)
        
        # Find the coordinator(s) to refresh
        coordinators_to_refresh = []
        
        if entity_id:
            # Refresh specific entity's coordinator
            for entry_id, coordinator in hass.data[DOMAIN].items():
                # Check if this coordinator has the requested entity
                if any(entity_id in str(entity) for entity in coordinator.data.get("sensors", [])):
                    coordinators_to_refresh.append(coordinator)
        else:
            # Refresh all coordinators
            coordinators_to_refresh = list(hass.data[DOMAIN].values())
        
        if not coordinators_to_refresh:
            _LOGGER.warning("No coordinators found to refresh")
            return
            
        # Refresh coordinators
        for coordinator in coordinators_to_refresh:
            try:
                await coordinator.async_request_refresh()
                _LOGGER.info("Successfully refreshed prayer times data")
            except Exception as e:
                _LOGGER.error("Failed to refresh prayer times: %s", e)
    
    async def handle_play_azan(call):
        """Handle the play_azan service call."""
        prayer = call.data.get("prayer")
        media_player = call.data.get("media_player")
        volume = call.data.get("volume", 0.5)
        
        _LOGGER.info("Service call: play_azan for %s on %s", prayer, media_player)
        
        await _play_azan_file(hass, prayer, media_player, volume)
    
    async def handle_test_audio(call):
        """Handle the test_audio service call for debugging."""
        media_player = call.data.get("media_player")
        audio_file = call.data.get("audio_file", "azan.mp3")
        volume = call.data.get("volume", 0.5)
        
        _LOGGER.info("Service call: test_audio for %s on %s", audio_file, media_player)
        
        # Check if media player exists
        if not hass.states.get(media_player):
            _LOGGER.error("Media player %s not found", media_player)
            return

        # Get media player state for debugging
        state = hass.states.get(media_player)
        _LOGGER.info("Media player %s state: %s", media_player, state.state)
        _LOGGER.info("Media player attributes: %s", state.attributes)

        # Verify the audio file exists
        www_path = os.path.join(hass.config.path("www"), "solatsyncmy", audio_file)
        if not os.path.exists(www_path):
            _LOGGER.error("Audio file not found: %s", www_path)
            _LOGGER.info("Attempting to setup audio files...")
            await _setup_audio_files(hass)
            
            # Check again after setup
            if not os.path.exists(www_path):
                _LOGGER.error("Failed to setup audio file: %s", www_path)
                return

        _LOGGER.info("Found audio file: %s (size: %d bytes)", www_path, os.path.getsize(www_path))

        # Set volume first
        if volume is not None:
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

        # Get base URL
        base_url = hass.config.external_url or hass.config.internal_url or "http://localhost:8123"
        
        # Test different path formats one by one with detailed logging
        test_paths = [
            f"/local/solatsyncmy/{audio_file}",
            f"media-source://media_source/local/solatsyncmy/{audio_file}",
            f"{base_url}/local/solatsyncmy/{audio_file}",
            f"http://localhost:8123/local/solatsyncmy/{audio_file}",
        ]
        
        # Test different media types
        test_types = ["audio/mp3", "audio/mpeg", "music", "audio"]
        
        for i, file_url in enumerate(test_paths, 1):
            for j, media_type in enumerate(test_types, 1):
                try:
                    _LOGGER.info("Test %d.%d: Trying path=%s, type=%s", i, j, file_url, media_type)
                    
                    await hass.services.async_call(
                        "media_player",
                        "play_media",
                        {
                            "entity_id": media_player,
                            "media_content_id": file_url,
                            "media_content_type": media_type,
                        },
                    )
                    
                    _LOGGER.info("Test %d.%d: SUCCESS - Media sent to %s", i, j, media_player)
                    
                    # Wait a bit to see if it starts playing
                    await asyncio.sleep(2)
                    
                    # Check player state after command
                    new_state = hass.states.get(media_player)
                    _LOGGER.info("Player state after command: %s", new_state.state if new_state else "unknown")
                    
                    return  # Stop after first success
                    
                except Exception as e:
                    _LOGGER.warning("Test %d.%d: FAILED - %s", i, j, str(e))
                    continue
        
        _LOGGER.error("All test attempts failed for %s", media_player)
    
    # Register services without schemas to let services.yaml handle the UI
    # This allows Home Assistant to load the service definitions from services.yaml
    if not hass.services.has_service(DOMAIN, "refresh_prayer_times"):
        hass.services.async_register(
            DOMAIN, 
            "refresh_prayer_times", 
            handle_refresh_prayer_times
        )
    
    if not hass.services.has_service(DOMAIN, "play_azan"):
        hass.services.async_register(
            DOMAIN, 
            "play_azan", 
            handle_play_azan
        )
    
    if not hass.services.has_service(DOMAIN, "test_audio"):
        hass.services.async_register(
            DOMAIN, 
            "test_audio", 
            handle_test_audio
        )
    
    _LOGGER.info("Registered services: refresh_prayer_times, play_azan, test_audio") 