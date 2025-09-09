"""Switch platform for Waktu Solat Malaysia azan automation."""
import asyncio
import logging
import os
from typing import Any, Dict, Optional
from datetime import datetime, time

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_time_change

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SW_VERSION,
    AZAN_PRAYERS,
    PRAYER_NAMES,
    PRAYER_ORDER,
    CONF_AZAN_ENABLED,
    CONF_AZAN_SUBUH_ENABLED,
    CONF_AZAN_ZOHOR_ENABLED,
    CONF_AZAN_ASAR_ENABLED,
    CONF_AZAN_MAGHRIB_ENABLED,
    CONF_AZAN_ISYAK_ENABLED,
    CONF_MEDIA_PLAYER,
    CONF_AZAN_VOLUME,
    AZAN_FILE_NORMAL,
    AZAN_FILE_FAJR,
)
from .coordinator import WaktuSolatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waktu Solat Malaysia switch entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Create main azan automation switch first (for proper ordering)
    entities.append(WaktuSolatAzanMainSwitch(coordinator, config_entry))
    
    # Create individual prayer azan switches in order: Subuh, Zohor, Asar, Maghrib, Isyak
    prayer_config_map = {
        "fajr": CONF_AZAN_SUBUH_ENABLED,
        "dhuhr": CONF_AZAN_ZOHOR_ENABLED, 
        "asr": CONF_AZAN_ASAR_ENABLED,
        "maghrib": CONF_AZAN_MAGHRIB_ENABLED,
        "isha": CONF_AZAN_ISYAK_ENABLED,
    }
    
    # Add prayer switches in the correct order
    prayer_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
    for prayer in prayer_order:
        if prayer in prayer_config_map:
            entities.append(WaktuSolatAzanPrayerSwitch(coordinator, config_entry, prayer, prayer_config_map[prayer]))
    
    async_add_entities(entities)


class WaktuSolatSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base class for Waktu Solat Malaysia switch entities."""

    def __init__(self, coordinator: WaktuSolatCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.config_entry = config_entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="Solat Sync MY",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=SW_VERSION,
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None


class WaktuSolatAzanMainSwitch(WaktuSolatSwitchEntity):
    """Switch to control overall azan automation."""

    def __init__(self, coordinator: WaktuSolatCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the main azan switch."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_azan_automation"
        self._attr_name = f"Waktu Solat Azan Automation"
        self._attr_icon = "mdi:mosque"
        self._time_listeners = []

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        return self.config_entry.options.get(CONF_AZAN_ENABLED, False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        new_options = dict(self.config_entry.options)
        new_options[CONF_AZAN_ENABLED] = True
        
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )
        
        # Set up time listeners for azan automation
        await self._setup_time_listeners()
        
        await self.coordinator.async_request_refresh()
        _LOGGER.info("🕌 Azan automation enabled")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        new_options = dict(self.config_entry.options)
        new_options[CONF_AZAN_ENABLED] = False
        
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )
        
        # Clean up time listeners
        self._cleanup_time_listeners()
        
        await self.coordinator.async_request_refresh()
        _LOGGER.info("🕌 Azan automation disabled")

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()
        
        # Set up time listeners if azan is enabled
        if self.is_on:
            await self._setup_time_listeners()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        super()._handle_coordinator_update()
        
        # Refresh time listeners when coordinator data changes
        if self.is_on:
            self.hass.async_create_task(self._setup_time_listeners())

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        await super().async_will_remove_from_hass()
        self._cleanup_time_listeners()

    async def _setup_time_listeners(self) -> None:
        """Set up time-based listeners for azan automation."""
        if not self.coordinator.data:
            _LOGGER.warning("No prayer time data available for azan setup")
            return

        self._cleanup_time_listeners()  # Clean up existing listeners first

        prayer_times = self.coordinator.data.get("prayer_times", {})
        
        for prayer in AZAN_PRAYERS:
            if prayer not in prayer_times:
                continue
                
            prayer_time = prayer_times[prayer]
            if not isinstance(prayer_time, time):
                continue
            
            # Check if this prayer's azan is enabled
            prayer_config_map = {
                "fajr": CONF_AZAN_SUBUH_ENABLED,
                "dhuhr": CONF_AZAN_ZOHOR_ENABLED,
                "asr": CONF_AZAN_ASAR_ENABLED,
                "maghrib": CONF_AZAN_MAGHRIB_ENABLED,
                "isha": CONF_AZAN_ISYAK_ENABLED,
            }
            
            config_key = prayer_config_map.get(prayer)
            if config_key and not self.config_entry.options.get(config_key, True):
                continue  # This prayer's azan is disabled
            
            # Set up time listener
            listener = async_track_time_change(
                self.hass,
                self._azan_time_callback,
                hour=prayer_time.hour,
                minute=prayer_time.minute,
                second=0
            )
            self._time_listeners.append(listener)
            
            prayer_name = PRAYER_NAMES.get(prayer, prayer)
            _LOGGER.info("⏰ Scheduled azan for %s at %s", prayer_name, prayer_time.strftime("%H:%M"))

    def _cleanup_time_listeners(self) -> None:
        """Clean up existing time listeners."""
        for listener in self._time_listeners:
            listener()

        self._time_listeners.clear()

    async def _azan_time_callback(self, now) -> None:
        """Callback when it's time for azan."""
        if not self.coordinator.data:
            return

        prayer_times = self.coordinator.data.get("prayer_times", {})
        current_prayer = None
        
        # Find which prayer this is
        for prayer in AZAN_PRAYERS:
            if prayer in prayer_times:
                prayer_time = prayer_times[prayer]
                if (prayer_time.hour == now.hour and 
                    prayer_time.minute == now.minute):
                    current_prayer = prayer
                    break
        
        if current_prayer:
            await self._play_azan(current_prayer)

    async def _play_azan(self, prayer: str) -> None:
        """Play azan for the specified prayer."""
        media_player = self.config_entry.options.get(CONF_MEDIA_PLAYER)
        if not media_player:
            _LOGGER.warning("No media player configured for azan")
            return

        # Check if media player exists
        if not self.hass.states.get(media_player):
            _LOGGER.error("Media player %s not found", media_player)
            return

        try:
            volume = self.config_entry.options.get(CONF_AZAN_VOLUME, 0.7)
            
            # Import the centralized audio playback function
            from . import _play_azan_file
            
            # Use the centralized audio playback with config entry
            await _play_azan_file(self.hass, prayer, media_player, volume, self.config_entry)
            
        except Exception as err:
            _LOGGER.error("❌ Failed to play azan for %s: %s", prayer, err)


class WaktuSolatAzanPrayerSwitch(WaktuSolatSwitchEntity):
    """Switch to control azan for individual prayers."""

    def __init__(
        self,
        coordinator: WaktuSolatCoordinator,
        config_entry: ConfigEntry,
        prayer: str,
        config_key: str
    ) -> None:
        """Initialize the prayer azan switch."""
        super().__init__(coordinator, config_entry)
        self.prayer = prayer
        self.config_key = config_key
        
        # Use Malay prayer names for display
        prayer_name = PRAYER_NAMES.get(prayer, prayer.title())
        
        self._attr_unique_id = f"{config_entry.entry_id}_azan_{prayer}"
        self._attr_name = f"Waktu Solat Azan {prayer_name}"
        self._attr_icon = "mdi:volume-high"

    @property
    def is_on(self) -> bool:
        """Return True if the switch is on."""
        return self.config_entry.options.get(self.config_key, True)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Only available if main azan automation is enabled
        main_enabled = self.config_entry.options.get(CONF_AZAN_ENABLED, False)
        return super().available and main_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        new_options = dict(self.config_entry.options)
        new_options[self.config_key] = True
        
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )
        
        # Refresh the main switch's time listeners
        await self._refresh_main_switch()
        
        await self.coordinator.async_request_refresh()
        prayer_name = PRAYER_NAMES.get(self.prayer, self.prayer.title())
        _LOGGER.info("🔊 Azan for %s enabled", prayer_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        new_options = dict(self.config_entry.options)
        new_options[self.config_key] = False
        
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        ) 
        
        # Refresh the main switch's time listeners
        await self._refresh_main_switch()
        
        await self.coordinator.async_request_refresh()
        prayer_name = PRAYER_NAMES.get(self.prayer, self.prayer.title())
        _LOGGER.info("🔇 Azan for %s disabled", prayer_name)

    async def _refresh_main_switch(self) -> None:
        """Refresh the main azan switch's time listeners."""
        # Find the main switch entity by triggering a coordinator refresh
        # The main switch will automatically refresh its listeners when coordinator data changes
        await self.coordinator.async_request_refresh() 