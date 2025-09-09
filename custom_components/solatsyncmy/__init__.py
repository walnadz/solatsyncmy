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
    LOCAL_AUDIO_PATHS,
    SERVICE_PLAY_AZAN,
    SERVICE_TEST_AUDIO,
    PRAYER_NAMES,
    CONF_AUDIO_SOURCE,
    AUDIO_SOURCE_BUNDLED,
    AUDIO_SOURCE_REMOTE,
    AUDIO_SOURCE_LOCAL_ONLY,
    AUDIO_SOURCE_MIXED,
    CONF_REMOTE_FAJR_URL,
    CONF_REMOTE_AZAN_URL,
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
    # Setup audio files (bundled and detect local)
    await _setup_audio_files(hass, entry)
    
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
        sw_version="1.0.11",
    )

    # Register services
    await _register_services(hass)

    
    return True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Solat Sync MY component."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        
        # Unregister services if this is the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_PLAY_AZAN)
            hass.services.async_remove(DOMAIN, SERVICE_TEST_AUDIO)
    
    return unload_ok


async def _setup_audio_files(hass: HomeAssistant, entry: ConfigEntry = None) -> None:
    """Set up audio files for azan playback based on audio source configuration."""
    try:
        # Get audio source configuration
        audio_source = AUDIO_SOURCE_BUNDLED  # Default
        if entry and entry.options:
            audio_source = entry.options.get(CONF_AUDIO_SOURCE, AUDIO_SOURCE_BUNDLED)
        
        _LOGGER.info("🎵 Setting up audio files with source: %s", audio_source)
        
        # Create www/solatsyncmy directory
        www_dir = hass.config.path("www")
        audio_dir = os.path.join(www_dir, "solatsyncmy")
        os.makedirs(audio_dir, exist_ok=True)
        
        # Handle different audio source types
        if audio_source == AUDIO_SOURCE_REMOTE:
            # Remote URLs - no file setup needed
            _LOGGER.info("🌐 Using remote audio URLs - no local file setup required")
            return
            
        elif audio_source == AUDIO_SOURCE_LOCAL_ONLY:
            # Local files only - just scan for existing files
            await _scan_local_audio_files(hass, audio_dir)
            _LOGGER.info("📁 Local-only audio source configured")
            return
            
        elif audio_source in [AUDIO_SOURCE_BUNDLED, AUDIO_SOURCE_MIXED]:
            # Bundled files (with override) or mixed fallback
            integration_dir = os.path.dirname(__file__)
            audio_source_dir = os.path.join(integration_dir, "audio")
            
            bundled_files = [AZAN_FILE_NORMAL, AZAN_FILE_FAJR]
            local_files_detected = []
            
            for audio_file in bundled_files:
                target_path = os.path.join(audio_dir, audio_file)
                source_path = os.path.join(audio_source_dir, audio_file)
                
                # Check if local file already exists (user manually placed)
                if os.path.exists(target_path):
                    local_files_detected.append(audio_file)
                    _LOGGER.info("🎵 Local audio file detected: %s", audio_file)
                    continue
                
                # Copy bundled file if available
                if os.path.exists(source_path):
                    shutil.copy2(source_path, target_path)
                    _LOGGER.info("📁 Copied bundled audio file: %s", audio_file)
                else:
                    # Create placeholder file
                    with open(target_path, 'w') as f:
                        f.write("# Placeholder - Replace with your azan file\n")
                    _LOGGER.warning("⚠️  Created placeholder for missing audio file: %s", audio_file)
            
            # Scan for additional local audio files
            await _scan_local_audio_files(hass, audio_dir)
            
            if local_files_detected:
                _LOGGER.info("🔊 Audio setup complete! Detected %d custom files", len(local_files_detected))
        
    except Exception as err:
        _LOGGER.error("Failed to setup audio files: %s", err)


async def _scan_local_audio_files(hass: HomeAssistant, audio_dir: str) -> None:
    """Scan for additional local audio files."""
    try:
        # Check common audio file locations
        audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg']
        found_files = []
        
        # Check integration audio directory
        for file in os.listdir(audio_dir):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                file_path = os.path.join(audio_dir, file)
                file_size = os.path.getsize(file_path)
                
                # Skip tiny placeholder files
                if file_size > 1024:  # > 1KB
                    found_files.append({
                        'name': file,
                        'path': file_path,
                        'size': file_size,
                        'location': 'www/solatsyncmy/'
                    })
        
        # Check other common locations
        for search_path in LOCAL_AUDIO_PATHS:
            search_full_path = hass.config.path(search_path.lstrip('/'))
            if os.path.exists(search_full_path):
                for root, dirs, files in os.walk(search_full_path):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in audio_extensions):
                            if 'azan' in file.lower() or 'adhan' in file.lower():
                                file_path = os.path.join(root, file)
                                file_size = os.path.getsize(file_path)
                                
                                if file_size > 1024:  # > 1KB
                                    rel_path = os.path.relpath(file_path, hass.config.path())
                                    found_files.append({
                                        'name': file,
                                        'path': file_path,
                                        'size': file_size,
                                        'location': rel_path
                                    })
        
        if found_files:
            _LOGGER.info("🎼 Audio files detected:")
            for file_info in found_files:
                size_mb = file_info['size'] / 1024 / 1024
                _LOGGER.info("   📀 %s (%.1f MB) - %s", 
                           file_info['name'], size_mb, file_info['location'])
        
    except Exception as err:
        _LOGGER.error("Error scanning local audio files: %s", err)


async def _register_services(hass: HomeAssistant) -> None:
    """Register services for the integration."""
    
    def get_config_entry():
        """Get the first config entry for this integration."""
        entries = hass.config_entries.async_entries(DOMAIN)
        return entries[0] if entries else None
    
    async def play_azan_service(call: ServiceCall) -> None:
        """Service to play azan for a specific prayer."""
        prayer = call.data.get("prayer")
        media_player = call.data.get("media_player")
        volume = call.data.get("volume", 0.7)
        
        if not prayer:
            _LOGGER.error("Prayer parameter is required")
            return
        
        if not media_player:
            _LOGGER.error("Media player parameter is required")
            return
        
        entry = get_config_entry()
        await _play_azan_file(hass, prayer, media_player, volume, entry)
    
    async def test_audio_service(call: ServiceCall) -> None:
        """Service to test audio playback with detailed diagnostics."""
        media_player = call.data.get("media_player")
        audio_file = call.data.get("audio_file", AZAN_FILE_NORMAL)
        volume = call.data.get("volume", 0.5)
        
        if not media_player:
            _LOGGER.error("Media player parameter is required")
            return
        
        entry = get_config_entry()
        await _test_audio_playback(hass, media_player, audio_file, volume, entry)
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_PLAY_AZAN,
        play_azan_service,
        schema=vol.Schema({
            vol.Required("prayer"): str,
            vol.Required("media_player"): str,
            vol.Optional("volume", default=0.7): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
        }),
    )
    
    hass.services.async_register(
        DOMAIN,
        SERVICE_TEST_AUDIO,
        test_audio_service,
        schema=vol.Schema({
            vol.Required("media_player"): str,
            vol.Optional("audio_file", default=AZAN_FILE_NORMAL): str,
            vol.Optional("volume", default=0.5): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
        }),
    )


async def _get_audio_urls(hass: HomeAssistant, prayer: str, audio_source: str, entry: ConfigEntry = None) -> list:
    """Get audio URLs based on the configured audio source."""
    audio_urls = []
    
    try:
        if audio_source == AUDIO_SOURCE_REMOTE:
            # Remote URLs from configuration
            if entry and entry.options:
                if prayer == "fajr":
                    remote_url = entry.options.get(CONF_REMOTE_FAJR_URL, "").strip()
                else:
                    remote_url = entry.options.get(CONF_REMOTE_AZAN_URL, "").strip()
                
                if remote_url:
                    audio_urls.append(remote_url)
                    _LOGGER.debug("🌐 Using remote URL: %s", remote_url)
                else:
                    _LOGGER.warning("⚠️  No remote URL configured for %s", prayer)
        
        elif audio_source == AUDIO_SOURCE_LOCAL_ONLY:
            # Local files only - no bundled fallback
            audio_urls = await _get_local_audio_urls(hass, prayer)
            
        elif audio_source == AUDIO_SOURCE_MIXED:
            # Local preferred, bundled fallback
            audio_urls = await _get_local_audio_urls(hass, prayer)
            if not audio_urls:
                # Fallback to bundled files
                audio_urls = await _get_bundled_audio_urls(hass, prayer)
                
        else:  # AUDIO_SOURCE_BUNDLED (default)
            # Bundled with user override
            audio_urls = await _get_bundled_audio_urls(hass, prayer)
            
    except Exception as err:
        _LOGGER.error("Error getting audio URLs: %s", err)
    
    return audio_urls


async def _get_local_audio_urls(hass: HomeAssistant, prayer: str) -> list:
    """Get local audio file URLs."""
    audio_urls = []
    
    # Check if user has custom named files first
    custom_files = [
        f"azan_{prayer}.mp3",
        f"adhan_{prayer}.mp3", 
        f"{PRAYER_NAMES.get(prayer, prayer).lower()}.mp3"
    ]
    
    for custom_file in custom_files:
        custom_path = hass.config.path("www", "solatsyncmy", custom_file)
        if os.path.exists(custom_path) and os.path.getsize(custom_path) > 1024:
            audio_urls.append(f"/local/solatsyncmy/{custom_file}")
            _LOGGER.debug("✅ Found custom audio file: %s", custom_path)
            break
    
    return audio_urls


async def _get_bundled_audio_urls(hass: HomeAssistant, prayer: str) -> list:
    """Get bundled audio file URLs (with user override)."""
    audio_urls = []
    
    # Determine which azan file to use
    audio_file = AZAN_FILE_FAJR if prayer == "fajr" else AZAN_FILE_NORMAL
    
    # 1. Check for user override first
    user_override_path = hass.config.path("www", "solatsyncmy", audio_file)
    if os.path.exists(user_override_path) and os.path.getsize(user_override_path) > 1024:
        audio_urls.append(f"/local/solatsyncmy/{audio_file}")
        _LOGGER.debug("✅ Found user override file: %s", user_override_path)
    
    # 2. Check if user has custom named files
    if not audio_urls:
        local_urls = await _get_local_audio_urls(hass, prayer)
        audio_urls.extend(local_urls)
    
    # 3. Fallback to standard bundled file location
    if not audio_urls:
        www_path = f"/local/solatsyncmy/{audio_file}"
        local_file_path = hass.config.path("www", "solatsyncmy", audio_file)
        if os.path.exists(local_file_path):
            audio_urls.append(www_path)
            _LOGGER.debug("✅ Found bundled audio file: %s", local_file_path)
    
    return audio_urls


async def _play_azan_file(hass: HomeAssistant, prayer: str, media_player: str, volume: float, entry: ConfigEntry = None) -> None:
    """Play azan file with enhanced error handling and multiple audio source support."""
    try:
        _LOGGER.info("🕌 Playing %s azan on %s (volume: %.1f)", PRAYER_NAMES.get(prayer, prayer), media_player, volume)
        
        # Check if media player exists
        state = hass.states.get(media_player)
        if not state:
            _LOGGER.error("❌ Media player not found: %s", media_player)
            return
        
        # Get audio source configuration
        audio_source = AUDIO_SOURCE_BUNDLED  # Default
        if entry and entry.options:
            audio_source = entry.options.get(CONF_AUDIO_SOURCE, AUDIO_SOURCE_BUNDLED)
        
        # Get audio URLs based on source configuration
        audio_urls = await _get_audio_urls(hass, prayer, audio_source, entry)
        
        if not audio_urls:
            _LOGGER.error("❌ No audio source found for %s with source: %s", prayer, audio_source)
            return
        
        # Get current media player state
        current_state = state.state
        _LOGGER.debug("📱 Media player %s current state: %s", media_player, current_state)
        
        # Step 1: Turn on media player if it's off
        if current_state in ["off", "standby"]:
            _LOGGER.info("🔌 Turning on media player...")
            await hass.services.async_call(
                "media_player", "turn_on", {"entity_id": media_player}
            )
            await asyncio.sleep(3)  # Wait for power on
        
        # Step 2: Set volume
        _LOGGER.info("🔊 Setting volume to %.1f", volume)
        await hass.services.async_call(
            "media_player",
            "volume_set",
            {"entity_id": media_player, "volume_level": volume}
        )
        await asyncio.sleep(1)  # Wait for volume change
        
        # Step 3: Play audio file (try each URL until one works)
        for audio_url in audio_urls:
            try:
                _LOGGER.info("▶️  Attempting to play: %s", audio_url)
                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": media_player,
                        "media_content_id": audio_url,
                        "media_content_type": "music",
                    }
                )
                
                # Wait and check if playback started
                await asyncio.sleep(2)
                new_state = hass.states.get(media_player)
                if new_state and new_state.state == "playing":
                    _LOGGER.info("🎵 SUCCESS! Audio is playing")
                    return
                else:
                    _LOGGER.warning("⚠️  Media player not in playing state after command")
                    
            except Exception as err:
                _LOGGER.warning("❌ Failed to play %s: %s", audio_url, err)
                continue
        
        _LOGGER.error("❌ All audio URLs failed to play")
        
    except Exception as err:
        _LOGGER.error("❌ Error playing azan: %s", err)


async def _test_audio_playback(hass: HomeAssistant, media_player: str, audio_file: str, volume: float, entry: ConfigEntry = None) -> None:
    """Test audio playback with comprehensive diagnostics."""
    _LOGGER.info("🧪 AUDIO TEST STARTING - Media Player: %s, File: %s, Volume: %.1f", 
                 media_player, audio_file, volume)
    
    try:
        # Step 1: Check media player exists
        state = hass.states.get(media_player)
        if not state:
            _LOGGER.error("❌ TEST FAILED: Media player not found: %s", media_player)
            return
        
        _LOGGER.info("✅ Media player found: %s (state: %s)", media_player, state.state)
        
        # Step 2: Check audio file exists
        local_file_path = hass.config.path("www", "solatsyncmy", audio_file)
        if not os.path.exists(local_file_path):
            _LOGGER.error("❌ TEST FAILED: Audio file not found: %s", local_file_path)
            return
        
        file_size = os.path.getsize(local_file_path)
        _LOGGER.info("✅ Audio file found: %s (%.1f KB)", audio_file, file_size/1024)
        
        if file_size < 1024:
            _LOGGER.warning("⚠️  Audio file seems too small (%.1f KB) - might be placeholder", file_size/1024)
        
        # Step 3: Test playback
        await _play_azan_file(hass, "test", media_player, volume, entry)
        
        _LOGGER.info("🏁 AUDIO TEST COMPLETED")
        
    except Exception as err:
        _LOGGER.error("❌ AUDIO TEST ERROR: %s", err) 