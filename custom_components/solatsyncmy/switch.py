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
        
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Azan automation enabled")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        new_options = dict(self.config_entry.options)
        new_options[CONF_AZAN_ENABLED] = False
        
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )
        
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Azan automation disabled")


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
        
        await self.coordinator.async_request_refresh()
        prayer_name = PRAYER_NAMES.get(self.prayer, self.prayer.title())
        _LOGGER.info("Azan for %s enabled", prayer_name)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        new_options = dict(self.config_entry.options)
        new_options[self.config_key] = False
        
        self.hass.config_entries.async_update_entry(
            self.config_entry, options=new_options
        )
        
        await self.coordinator.async_request_refresh()
        prayer_name = PRAYER_NAMES.get(self.prayer, self.prayer.title())
        _LOGGER.info("Azan for %s disabled", prayer_name) 