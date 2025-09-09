"""Switch platform for Waktu Solat Malaysia azan automation."""
import logging
import os
from typing import Any, Dict, Optional

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
    CONF_AZAN_ENABLED,
    CONF_AZAN_FAJR_ENABLED,
    CONF_AZAN_DHUHR_ENABLED,
    CONF_AZAN_ASR_ENABLED,
    CONF_AZAN_MAGHRIB_ENABLED,
    CONF_AZAN_ISHA_ENABLED,
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
    
    # Create main azan automation switch
    entities.append(WaktuSolatAzanMainSwitch(coordinator, config_entry))
    
    # Create individual prayer azan switches
    prayer_config_map = {
        "fajr": CONF_AZAN_FAJR_ENABLED,
        "dhuhr": CONF_AZAN_DHUHR_ENABLED,
        "asr": CONF_AZAN_ASR_ENABLED,
        "maghrib": CONF_AZAN_MAGHRIB_ENABLED,
        "isha": CONF_AZAN_ISHA_ENABLED,
    }
    
    for prayer, config_key in prayer_config_map.items():
        entities.append(WaktuSolatAzanPrayerSwitch(coordinator, config_entry, prayer, config_key))
    
    async_add_entities(entities)


class WaktuSolatSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Base class for Waktu Solat Malaysia switch entities."""

    def __init__(
        self,
        coordinator: WaktuSolatCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._zone = config_entry.data["zone"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._config_entry.entry_id)},
            name=f"Solat Sync MY ({self._zone})",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=SW_VERSION,
            configuration_url="https://api.waktusolat.app/docs",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success


class WaktuSolatAzanMainSwitch(WaktuSolatSwitchEntity):
    """Main switch to enable/disable azan automation."""

    def __init__(
        self,
        coordinator: WaktuSolatCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the main azan switch."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_azan_main"
        self._attr_name = "Waktu Solat Azan Automation"
        self._attr_icon = "mdi:mosque"
        self._time_listeners = []

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._config_entry.options.get(CONF_AZAN_ENABLED, False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        new_options = dict(self._config_entry.options)
        new_options[CONF_AZAN_ENABLED] = True
        
        self.hass.config_entries.async_update_entry(
            self._config_entry, options=new_options
        )
        
        # Start time tracking for azan
        await self._setup_azan_automation()
        
        # Update the entity state immediately
        self.async_write_ha_state()
        
        # Update all prayer switches availability
        await self._update_prayer_switches()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        new_options = dict(self._config_entry.options)
        new_options[CONF_AZAN_ENABLED] = False
        
        self.hass.config_entries.async_update_entry(
            self._config_entry, options=new_options
        )
        
        # Stop time tracking
        self._cleanup_time_listeners()
        
        # Update the entity state immediately
        self.async_write_ha_state()
        
        # Update all prayer switches availability
        await self._update_prayer_switches()

    async def _update_prayer_switches(self) -> None:
        """Update all prayer switches to reflect availability changes."""
        # Trigger a coordinator update to refresh all entities
        await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Set up azan automation if enabled
        if self.is_on:
            await self._setup_azan_automation()

    async def async_will_remove_from_hass(self) -> None:
        """When entity will be removed from hass."""
        self._cleanup_time_listeners()
        await super().async_will_remove_from_hass()

    async def _setup_azan_automation(self) -> None:
        """Set up time-based automation for azan."""
        if not self.coordinator.data:
            return

        prayer_times = self.coordinator.data.get("prayer_times", {})
        
        for prayer in AZAN_PRAYERS:
            if prayer not in prayer_times:
                continue
                
            prayer_time = prayer_times[prayer]
            
            # Check if this prayer's azan is enabled
            prayer_config_map = {
                "fajr": CONF_AZAN_FAJR_ENABLED,
                "dhuhr": CONF_AZAN_DHUHR_ENABLED,
                "asr": CONF_AZAN_ASR_ENABLED,
                "maghrib": CONF_AZAN_MAGHRIB_ENABLED,
                "isha": CONF_AZAN_ISHA_ENABLED,
            }
            
            if not self._config_entry.options.get(prayer_config_map.get(prayer), True):
                continue
            
            # Set up time listener for this prayer
            listener = async_track_time_change(
                self.hass,
                self._azan_time_callback,
                hour=prayer_time.hour,
                minute=prayer_time.minute,
                second=0,
            )
            self._time_listeners.append(listener)
            
            _LOGGER.debug(
                "Set up azan automation for %s at %s",
                prayer,
                prayer_time.strftime("%H:%M"),
            )

    def _cleanup_time_listeners(self) -> None:
        """Clean up time listeners."""
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
        media_player = self._config_entry.options.get(CONF_MEDIA_PLAYER)
        if not media_player:
            _LOGGER.warning("No media player configured for azan")
            return

        # Check if media player exists
        if not self.hass.states.get(media_player):
            _LOGGER.error("Media player %s not found", media_player)
            return

        # Determine which azan file to use
        azan_file = AZAN_FILE_FAJR if prayer == "fajr" else AZAN_FILE_NORMAL
        
        # Get the full path to the azan file
        integration_dir = os.path.dirname(__file__)
        azan_path = os.path.join(integration_dir, azan_file)
        
        if not os.path.exists(azan_path):
            _LOGGER.error("Azan file not found: %s", azan_path)
            return

        # Set volume
        volume = self._config_entry.options.get(CONF_AZAN_VOLUME, 0.7)
        await self.hass.services.async_call(
            "media_player",
            "volume_set",
            {
                "entity_id": media_player,
                "volume_level": volume,
            },
        )

        # Play azan using the local file path
        file_url = f"/local/custom_components/{DOMAIN}/{azan_file}"
        await self.hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": media_player,
                "media_content_id": file_url,
                "media_content_type": "audio/mp3",
            },
        )
        
        _LOGGER.info("Playing %s azan on %s", prayer, media_player)


class WaktuSolatAzanPrayerSwitch(WaktuSolatSwitchEntity):
    """Switch to enable/disable azan for individual prayers."""

    def __init__(
        self,
        coordinator: WaktuSolatCoordinator,
        config_entry: ConfigEntry,
        prayer: str,
        config_key: str,
    ) -> None:
        """Initialize the prayer azan switch."""
        super().__init__(coordinator, config_entry)
        self._prayer = prayer
        self._config_key = config_key
        self._attr_unique_id = f"{config_entry.entry_id}_azan_{prayer}"
        self._attr_name = f"Waktu Solat Azan {prayer.title()}"
        self._attr_icon = "mdi:volume-high"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._config_entry.options.get(self._config_key, True)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # Only available if main azan automation is enabled
        main_enabled = self._config_entry.options.get(CONF_AZAN_ENABLED, False)
        return super().available and main_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        new_options = dict(self._config_entry.options)
        new_options[self._config_key] = True
        
        self.hass.config_entries.async_update_entry(
            self._config_entry, options=new_options
        )
        
        # Update the entity state immediately
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        new_options = dict(self._config_entry.options)
        new_options[self._config_key] = False
        
        self.hass.config_entries.async_update_entry(
            self._config_entry, options=new_options
        )
        
        # Update the entity state immediately
        self.async_write_ha_state() 