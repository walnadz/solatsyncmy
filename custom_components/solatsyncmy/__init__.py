"""Waktu Solat Malaysia integration for Home Assistant."""
import logging
from datetime import timedelta
import os
from typing import Any, Dict

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN, 
    PLATFORMS, 
    SERVICE_PLAY_AZAN,
    CONF_MEDIA_PLAYER,
    CONF_AZAN_VOLUME,
    AZAN_FILE_NORMAL,
    AZAN_FILE_FAJR,
    AZAN_PRAYERS
)
from .coordinator import WaktuSolatCoordinator

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waktu Solat Malaysia from a config entry."""
    _LOGGER.info("Setting up Waktu Solat Malaysia integration")
    
    coordinator = WaktuSolatCoordinator(hass, entry)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Register services
    async def async_play_azan_service(call: ServiceCall) -> None:
        """Handle play azan service call."""
        prayer = call.data.get("prayer")
        media_player = call.data.get("media_player")
        volume = call.data.get("volume", 0.7)
        
        if prayer not in AZAN_PRAYERS:
            _LOGGER.error("Invalid prayer: %s", prayer)
            return
            
        # Use configured media player if not specified
        if not media_player:
            media_player = entry.options.get(CONF_MEDIA_PLAYER)
            
        if not media_player:
            _LOGGER.error("No media player specified or configured")
            return
            
        # Check if media player exists
        if not hass.states.get(media_player):
            _LOGGER.error("Media player %s not found", media_player)
            return
            
        await _play_azan_file(hass, prayer, media_player, volume)
    
    # Register the service only if it's not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_PLAY_AZAN):
        hass.services.async_register(
            DOMAIN,
            SERVICE_PLAY_AZAN,
            async_play_azan_service,
        )
    
    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def _play_azan_file(hass: HomeAssistant, prayer: str, media_player: str, volume: float) -> None:
    """Play azan file for the specified prayer."""
    # Determine which azan file to use
    azan_file = AZAN_FILE_FAJR if prayer == "fajr" else AZAN_FILE_NORMAL
    
    # Get the full path to the azan file
    integration_dir = os.path.dirname(__file__)
    azan_path = os.path.join(integration_dir, azan_file)
    
    if not os.path.exists(azan_path):
        _LOGGER.error("Azan file not found: %s", azan_path)
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

    # Play azan using the local file path
    file_url = f"/local/custom_components/{DOMAIN}/{azan_file}"
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
            if hass.services.has_service(DOMAIN, SERVICE_PLAY_AZAN):
                hass.services.async_remove(DOMAIN, SERVICE_PLAY_AZAN)
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry) 