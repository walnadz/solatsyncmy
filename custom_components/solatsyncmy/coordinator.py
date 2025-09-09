"""Data update coordinator for Waktu Solat Malaysia."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    API_BASE_URL,
    API_TIMEOUT,
    CONF_ZONE,
    DEFAULT_SCAN_INTERVAL,
    PRAYER_TIMES,
)

_LOGGER = logging.getLogger(__name__)


class WaktuSolatCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Waktu Solat API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.zone = entry.data[CONF_ZONE]
        self.entry = entry
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Get current date for API call
            now = dt_util.now()
            year = now.year
            month = now.month
            
            # Use v2 API endpoint for better data format
            url = f"{API_BASE_URL}/v2/solat/{self.zone}"
            params = {"year": year, "month": month}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Error communicating with API: {response.status}")
                    
                    data = await response.json()
                    
                    if "prayers" not in data:
                        raise UpdateFailed("Invalid data format from API")
                    
                    # Process the prayer times data
                    return self._process_prayer_data(data, now)
                    
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timeout communicating with API") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _process_prayer_data(self, api_data: Dict[str, Any], current_time: datetime) -> Dict[str, Any]:
        """Process the API data into a format we can use."""
        prayers_data = api_data["prayers"]
        current_day = current_time.day
        
        # Find today's prayer times
        today_prayers = None
        for prayer_day in prayers_data:
            if prayer_day["day"] == current_day:
                today_prayers = prayer_day
                break
        
        if not today_prayers:
            raise UpdateFailed(f"No prayer times found for day {current_day}")
        
        # Convert timestamps to datetime objects and format times
        prayer_times = {}
        prayer_times_formatted = {}
        
        for prayer in PRAYER_TIMES:
            if prayer in today_prayers:
                # V2 API returns Unix timestamps
                timestamp = today_prayers[prayer]
                prayer_datetime = datetime.fromtimestamp(timestamp, tz=current_time.tzinfo)
                prayer_times[prayer] = prayer_datetime
                prayer_times_formatted[prayer] = prayer_datetime.strftime("%H:%M")
        
        # Calculate next prayer
        next_prayer_info = self._calculate_next_prayer(prayer_times, current_time)
        
        return {
            "zone": api_data.get("zone", self.zone),
            "year": api_data.get("year", current_time.year),
            "month": api_data.get("month", current_time.strftime("%b").upper()),
            "month_number": api_data.get("month_number", current_time.month),
            "hijri_date": today_prayers.get("hijri", ""),
            "prayer_times": prayer_times,
            "prayer_times_formatted": prayer_times_formatted,
            "next_prayer": next_prayer_info["name"],
            "next_prayer_time": next_prayer_info["time"],
            "time_to_next_prayer": next_prayer_info["time_remaining"],
            "last_updated": current_time,
        }

    def _calculate_next_prayer(self, prayer_times: Dict[str, datetime], current_time: datetime) -> Dict[str, Any]:
        """Calculate the next prayer time."""
        # Filter out syuruk as it's not a prayer time for azan
        prayer_order = ["fajr", "dhuhr", "asr", "maghrib", "isha"]
        
        next_prayer = None
        next_time = None
        
        for prayer in prayer_order:
            if prayer in prayer_times and prayer_times[prayer] > current_time:
                next_prayer = prayer
                next_time = prayer_times[prayer]
                break
        
        # If no prayer found for today, next prayer is Fajr tomorrow
        if not next_prayer:
            next_prayer = "fajr"
            # We'll need to fetch tomorrow's data, for now use a placeholder
            next_time = current_time.replace(hour=5, minute=30, second=0, microsecond=0) + timedelta(days=1)
        
        time_remaining = next_time - current_time
        
        return {
            "name": next_prayer,
            "time": next_time,
            "time_remaining": str(time_remaining).split('.')[0],  # Remove microseconds
        }

    async def async_get_zones(self) -> Optional[list]:
        """Get all available zones from the API."""
        try:
            url = f"{API_BASE_URL}/zones"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        zones = await response.json()
                        return zones
                    return None
                    
        except Exception as err:
            _LOGGER.error("Error fetching zones: %s", err)
            return None 