"""Sensor platform for Waktu Solat Malaysia."""
import logging
from datetime import datetime, timedelta
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
    PRAYER_NAMES,
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
    
    # Create individual prayer time sensors with Malay names
    for prayer in PRAYER_TIMES:
        entities.append(WaktuSolatPrayerTimeSensor(coordinator, config_entry, prayer))
    
    # Create next prayer sensor
    entities.append(WaktuSolatNextPrayerSensor(coordinator, config_entry))
    
    async_add_entities(entities)


class WaktuSolatEntity(CoordinatorEntity, SensorEntity):
    """Base class for Waktu Solat Malaysia entities."""

    def __init__(self, coordinator: WaktuSolatCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the entity."""
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


class WaktuSolatPrayerTimeSensor(WaktuSolatEntity):
    """Sensor for individual prayer times."""

    def __init__(
        self, 
        coordinator: WaktuSolatCoordinator, 
        config_entry: ConfigEntry, 
        prayer: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self.prayer = prayer
        
        # Use Malay prayer names for display
        prayer_name = PRAYER_NAMES.get(prayer, prayer.title())
        
        self._attr_unique_id = f"{config_entry.entry_id}_{prayer}"
        self._attr_name = f"Waktu Solat {prayer_name}"
        self._attr_icon = PRAYER_ICONS.get(prayer, "mdi:clock")
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> Optional[datetime]:
        """Return the prayer time."""
        if not self.coordinator.data:
            return None
            
        prayer_times = self.coordinator.data.get("prayer_times", {})
        
        # Check if we need to show next day's prayer times
        current_time = dt_util.now()
        
        # If current time is after Isyak, show next day's prayer times for all prayers except Syuruk
        if self.prayer != "syuruk":
            isha_time = prayer_times.get("isha")
            if isha_time and current_time.time() > isha_time.time():
                # Get next day's prayer times
                next_day_data = self.coordinator.data.get("next_day_prayer_times")
                if next_day_data and self.prayer in next_day_data:
                    return next_day_data[self.prayer]
        
        return prayer_times.get(self.prayer)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
            
        attrs = {
            ATTR_ZONE: self.coordinator.data.get("zone"),
            "prayer_name": PRAYER_NAMES.get(self.prayer, self.prayer.title()),
            "prayer_name_english": self.prayer.title(),
        }
        
        # Add Hijri date if available
        hijri_date = self.coordinator.data.get("hijri_date")
        if hijri_date:
            attrs[ATTR_HIJRI_DATE] = hijri_date
            
        return attrs


class WaktuSolatNextPrayerSensor(WaktuSolatEntity):
    """Sensor for next prayer information."""

    def __init__(self, coordinator: WaktuSolatCoordinator, config_entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_next_prayer"
        self._attr_name = "Waktu Solat Next Prayer"
        self._attr_icon = "mdi:clock-alert"

    @property
    def native_value(self) -> Optional[str]:
        """Return the next prayer name in Malay."""
        if not self.coordinator.data:
            return None
            
        next_prayer = self._get_next_prayer()
        if next_prayer:
            return PRAYER_NAMES.get(next_prayer, next_prayer.title())
        return None

    def _get_next_prayer(self) -> Optional[str]:
        """Get the next prayer."""
        if not self.coordinator.data:
            return None
            
        prayer_times = self.coordinator.data.get("prayer_times", {})
        if not prayer_times:
            return None
            
        current_time = dt_util.now()
        
        # Find next prayer for today
        for prayer in PRAYER_TIMES:
            if prayer == "syuruk":  # Skip syuruk as it's not a prayer with azan
                continue
                
            prayer_time = prayer_times.get(prayer)
            if prayer_time and current_time < prayer_time:
                return prayer
        
        # If no prayer left today, next prayer is Subuh tomorrow
        return "fajr"

    def _get_next_prayer_time(self) -> Optional[datetime]:
        """Get the next prayer time."""
        if not self.coordinator.data:
            return None
            
        prayer_times = self.coordinator.data.get("prayer_times", {})
        next_prayer = self._get_next_prayer()
        
        if not next_prayer:
            return None
            
        # If next prayer is Subuh and we're past today's Isyak, get tomorrow's Subuh
        current_time = dt_util.now()
        isha_time = prayer_times.get("isha")
        
        if (next_prayer == "fajr" and isha_time and 
            current_time.time() > isha_time.time()):
            # Get next day's Subuh time
            next_day_data = self.coordinator.data.get("next_day_prayer_times")
            if next_day_data and "fajr" in next_day_data:
                return next_day_data["fajr"]
                
        return prayer_times.get(next_prayer)

    def _calculate_time_to_prayer(self) -> Optional[str]:
        """Calculate time remaining to next prayer."""
        next_prayer_time = self._get_next_prayer_time()
        if not next_prayer_time:
            return None
            
        current_time = dt_util.now()
        time_diff = next_prayer_time - current_time
        
        if time_diff.total_seconds() < 0:
            return "Passed"
            
        hours = int(time_diff.total_seconds() // 3600)
        minutes = int((time_diff.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}
            
        next_prayer = self._get_next_prayer()
        next_prayer_time = self._get_next_prayer_time()
        time_to_prayer = self._calculate_time_to_prayer()
        
        attrs = {
            ATTR_ZONE: self.coordinator.data.get("zone"),
            ATTR_NEXT_PRAYER: next_prayer,
            ATTR_NEXT_PRAYER_TIME: next_prayer_time.isoformat() if next_prayer_time else None,
            ATTR_TIME_TO_NEXT_PRAYER: time_to_prayer,
            "next_prayer_malay": PRAYER_NAMES.get(next_prayer, next_prayer.title()) if next_prayer else None,
        }
        
        # Add all prayer times for reference
        prayer_times = self.coordinator.data.get("prayer_times", {})
        formatted_times = {}
        for prayer, time_obj in prayer_times.items():
            if time_obj:
                formatted_times[prayer] = time_obj.strftime("%H:%M")
        attrs[ATTR_PRAYER_TIMES] = formatted_times
        
        # Add Hijri date if available
        hijri_date = self.coordinator.data.get("hijri_date")
        if hijri_date:
            attrs[ATTR_HIJRI_DATE] = hijri_date
            
        return attrs 