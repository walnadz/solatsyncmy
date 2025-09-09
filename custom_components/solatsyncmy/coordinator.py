"""Data update coordinator for Waktu Solat Malaysia."""
import logging
from datetime import datetime, timedelta, date
from typing import Any, Dict, Optional

import aiohttp
import async_timeout
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN, 
    API_BASE_URL, 
    API_TIMEOUT, 
    DEFAULT_SCAN_INTERVAL,
    PRAYER_TIMES,
    PRAYER_NAMES,
)

_LOGGER = logging.getLogger(__name__)


class WaktuSolatCoordinator(DataUpdateCoordinator):
    """Coordinator to fetch prayer times from the API."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.zone = config_entry.data["zone"]
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch prayer times from API."""
        try:
            # Get today's prayer times
            today_data = await self._fetch_prayer_times_for_date(date.today())
            
            # Check if we need next day's prayer times (after Isyak)
            current_time = dt_util.now()
            today_isha = today_data.get("prayer_times", {}).get("isha")
            
            data = today_data.copy()
            
            # If current time is after Isyak, also fetch next day's prayer times
            if today_isha and current_time.time() > today_isha.time():
                tomorrow = date.today() + timedelta(days=1)
                next_day_data = await self._fetch_prayer_times_for_date(tomorrow)
                data["next_day_prayer_times"] = next_day_data.get("prayer_times", {})
                _LOGGER.debug("Fetched next day prayer times after Isyak")
            
            # Calculate next prayer information
            data.update(self._calculate_next_prayer(data))
            
            return data
            
        except Exception as err:
            _LOGGER.error("Error fetching prayer times: %s", err)
            raise UpdateFailed(f"Error fetching prayer times: {err}")

    async def _fetch_prayer_times_for_date(self, target_date: date) -> Dict[str, Any]:
        """Fetch prayer times for a specific date."""
        year = target_date.year
        month = target_date.month
        day = target_date.day
        
        # API v2 returns monthly data, not daily
        url = f"{API_BASE_URL}/v2/solat/{self.zone}"
        params = {"year": year, "month": month}
        
        _LOGGER.debug("Fetching prayer times from: %s with params: %s", url, params)
        
        async with async_timeout.timeout(API_TIMEOUT):
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"API request failed with status {response.status}")
                    
                    json_data = await response.json()
                    
                    # Check if we have the expected structure
                    if "zone" not in json_data or "prayers" not in json_data:
                        raise UpdateFailed(f"API returned unexpected structure: {json_data}")
                    
                    # Find today's prayer times from the monthly data
                    prayers_data = json_data.get("prayers", [])
                    target_day_data = None
                    
                    for prayer_day in prayers_data:
                        if prayer_day.get("day") == day:
                            target_day_data = prayer_day
                            break
                    
                    if not target_day_data:
                        raise UpdateFailed(f"No prayer data found for day {day}")
                    
                    # Extract prayer times from Unix timestamps
                    prayer_times = {}
                    for prayer in PRAYER_TIMES:
                        if prayer in target_day_data:
                            try:
                                # Convert Unix timestamp to datetime object
                                timestamp = target_day_data[prayer]
                                if isinstance(timestamp, (int, float)):
                                    time_obj = datetime.fromtimestamp(timestamp)
                                    # Convert to the local timezone
                                    prayer_times[prayer] = dt_util.as_local(time_obj)
                                else:
                                    _LOGGER.warning("Invalid timestamp for %s: %s", prayer, timestamp)
                                    continue
                            except (ValueError, TypeError, OSError) as err:
                                _LOGGER.warning("Failed to parse %s time '%s': %s", prayer, target_day_data.get(prayer), err)
                                continue
                    
                    # Format times for display
                    prayer_times_formatted = {}
                    for prayer, time_obj in prayer_times.items():
                        if time_obj:
                            prayer_times_formatted[prayer] = time_obj.strftime("%H:%M")
                    
                    result = {
                        "prayer_times": prayer_times,
                        "prayer_times_formatted": prayer_times_formatted,
                        "zone": json_data.get("zone", self.zone),
                        "date": target_date.strftime("%Y-%m-%d"),
                        "hijri_date": target_day_data.get("hijri"),
                        "location": self.zone,  # API doesn't provide location name
                    }
                    
                    _LOGGER.debug("Successfully parsed prayer times for %s: %s", target_date, prayer_times_formatted)
                    return result

    def _calculate_next_prayer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate next prayer information."""
        prayer_times = data.get("prayer_times", {})
        next_day_times = data.get("next_day_prayer_times", {})
        
        if not prayer_times:
            return {}
        
        current_time = dt_util.now()
        next_prayer = None
        next_prayer_time = None
        
        # Find next prayer for today (excluding syuruk as it's not a prayer with azan)
        prayers_with_azan = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        
        for prayer in prayers_with_azan:
            prayer_time = prayer_times.get(prayer)
            if prayer_time and current_time < prayer_time:
                next_prayer = prayer
                next_prayer_time = prayer_time
                break
        
        # If no prayer left today, next prayer is tomorrow's Subuh
        if not next_prayer:
            next_prayer = "fajr"
            if next_day_times and "fajr" in next_day_times:
                next_prayer_time = next_day_times["fajr"]
            else:
                # Fallback: tomorrow's Subuh (will be fetched in next update)
                tomorrow_fajr = prayer_times.get("fajr")
                if tomorrow_fajr:
                    next_prayer_time = tomorrow_fajr + timedelta(days=1)
        
        # Calculate time remaining
        time_to_next_prayer = None
        if next_prayer_time:
            time_diff = next_prayer_time - current_time
            if time_diff.total_seconds() > 0:
                hours = int(time_diff.total_seconds() // 3600)
                minutes = int((time_diff.total_seconds() % 3600) // 60)
                
                if hours > 0:
                    time_to_next_prayer = f"{hours}h {minutes}m"
                else:
                    time_to_next_prayer = f"{minutes}m"
            else:
                time_to_next_prayer = "Now"
        
        return {
            "next_prayer": next_prayer,
            "next_prayer_time": next_prayer_time.isoformat() if next_prayer_time else None,
            "time_to_next_prayer": time_to_next_prayer,
            "next_prayer_malay": PRAYER_NAMES.get(next_prayer, next_prayer.title()) if next_prayer else None,
        } 