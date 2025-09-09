"""Sensor platform for Waktu Solat Malaysia."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SW_VERSION,
    PRAYER_TIMES,
    PRAYER_ICONS,
    ATTR_NEXT_PRAYER,
    ATTR_NEXT_PRAYER_TIME,
    ATTR_TIME_TO_NEXT_PRAYER,
    ATTR_ZONE,
    ATTR_HIJRI_DATE,
    ATTR_PRAYER_TIMES,
)
from .coordinator import WaktuSolatCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Waktu Solat Malaysia sensor entities."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Create individual prayer time sensors
    for prayer in PRAYER_TIMES:
        entities.append(WaktuSolatPrayerTimeSensor(coordinator, config_entry, prayer))
    
    # Create next prayer sensor
    entities.append(WaktuSolatNextPrayerSensor(coordinator, config_entry))
    
    async_add_entities(entities)


class WaktuSolatEntity(CoordinatorEntity, SensorEntity):
    """Base class for Waktu Solat Malaysia entities."""

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
        return self.coordinator.last_update_success and self.coordinator.data is not None


class WaktuSolatPrayerTimeSensor(WaktuSolatEntity):
    """Sensor for individual prayer times."""

    def __init__(
        self,
        coordinator: WaktuSolatCoordinator,
        config_entry: ConfigEntry,
        prayer: str,
    ) -> None:
        """Initialize the prayer time sensor."""
        super().__init__(coordinator, config_entry)
        self._prayer = prayer
        self._attr_unique_id = f"{config_entry.entry_id}_{prayer}"
        self._attr_name = f"Waktu Solat {prayer.title()}"
        self._attr_icon = PRAYER_ICONS.get(prayer, "mdi:clock")
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> Optional[datetime]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        prayer_times = self.coordinator.data.get("prayer_times", {})
        return prayer_times.get(self._prayer)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
        
        attrs = {
            ATTR_ZONE: self.coordinator.data.get("zone"),
            ATTR_HIJRI_DATE: self.coordinator.data.get("hijri_date"),
        }
        
        # Add formatted time
        prayer_times_formatted = self.coordinator.data.get("prayer_times_formatted", {})
        if self._prayer in prayer_times_formatted:
            attrs["formatted_time"] = prayer_times_formatted[self._prayer]
        
        return attrs


class WaktuSolatNextPrayerSensor(WaktuSolatEntity):
    """Sensor for the next prayer information."""

    def __init__(
        self,
        coordinator: WaktuSolatCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the next prayer sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_next_prayer"
        self._attr_name = "Waktu Solat Next Prayer"
        self._attr_icon = "mdi:clock-alert"

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        return self.coordinator.data.get("next_prayer", "").title()

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
        
        attrs = {
            ATTR_ZONE: self.coordinator.data.get("zone"),
            ATTR_HIJRI_DATE: self.coordinator.data.get("hijri_date"),
            ATTR_NEXT_PRAYER: self.coordinator.data.get("next_prayer"),
            ATTR_NEXT_PRAYER_TIME: self.coordinator.data.get("next_prayer_time"),
            ATTR_TIME_TO_NEXT_PRAYER: self.coordinator.data.get("time_to_next_prayer"),
        }
        
        # Add all prayer times for the day
        prayer_times_formatted = self.coordinator.data.get("prayer_times_formatted", {})
        attrs[ATTR_PRAYER_TIMES] = prayer_times_formatted
        
        return attrs 