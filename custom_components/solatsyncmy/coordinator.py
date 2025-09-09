"""Data update coordinator for Waktu Solat Malaysia."""
import asyncio
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
        
        # Monthly data cache
        self._monthly_cache = {}
        self._cache_month = None
        self._cache_year = None
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            # Reduced frequency since we cache monthly data
            update_interval=timedelta(minutes=15),  # Check every 15 minutes for prayer transitions
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch prayer times from API with intelligent caching."""
        try:
            current_date = date.today()
            current_month = current_date.month
            current_year = current_date.year
            
            # Check if we need to fetch new monthly data
            need_fetch = (
                not self._monthly_cache or
                self._cache_month != current_month or
                self._cache_year != current_year
            )
            
            if need_fetch:
                _LOGGER.info(
                    "Fetching monthly prayer data for %s/%s (zone: %s)",
                    current_month, current_year, self.zone
                )
                self._monthly_cache = await self._fetch_monthly_prayer_times(
                    current_year, current_month
                )
                self._cache_month = current_month
                self._cache_year = current_year
            else:
                _LOGGER.debug("Using cached monthly data for %s/%s", current_month, current_year)
            
            # Extract today's data from monthly cache
            today_data = self._extract_daily_data_from_cache(current_date)
            
            # Check if we need next day's prayer times (after Isyak)
            current_time = dt_util.now()
            today_isha = today_data.get("prayer_times", {}).get("isha")
            
            data = today_data.copy()
            
            if today_isha and current_time >= today_isha:
                # After Isyak, show tomorrow's prayer times
                tomorrow = current_date + timedelta(days=1)
                
                # Check if tomorrow is in a different month
                if tomorrow.month != current_month or tomorrow.year != current_year:
                    _LOGGER.info(
                        "Fetching next month's data for tomorrow (%s)",
                        tomorrow.strftime("%Y-%m-%d")
                    )
                    tomorrow_monthly_data = await self._fetch_monthly_prayer_times(
                        tomorrow.year, tomorrow.month
                    )
                    tomorrow_data = self._extract_daily_data_from_monthly(
                        tomorrow_monthly_data, tomorrow
                    )
                else:
                    # Tomorrow is in the same cached month
                    tomorrow_data = self._extract_daily_data_from_cache(tomorrow)
                
                data["next_day_prayer_times"] = tomorrow_data.get("prayer_times", {})
                data["next_day_hijri"] = tomorrow_data.get("hijri_date", "")
            
            _LOGGER.debug("Prayer times updated successfully for %s", current_date)
            return data
            
        except Exception as err:
            _LOGGER.error("Error fetching prayer times: %s", err)
            raise UpdateFailed(f"Error fetching prayer times: {err}")

    def _extract_daily_data_from_cache(self, target_date: date) -> Dict[str, Any]:
        """Extract specific day's data from cached monthly data."""
        if not self._monthly_cache:
            raise UpdateFailed("No cached monthly data available")
        
        return self._extract_daily_data_from_monthly(self._monthly_cache, target_date)

    def _extract_daily_data_from_monthly(self, monthly_data: Dict[str, Any], target_date: date) -> Dict[str, Any]:
        """Extract specific day's data from monthly API response."""
        prayers_data = monthly_data.get("prayers", [])
        target_day = target_date.day
        
        # Find the specific day's data
        day_data = None
        for prayer_day in prayers_data:
            if prayer_day.get("day") == target_day:
                day_data = prayer_day
                break
        
        if not day_data:
            raise UpdateFailed(f"No prayer data found for day {target_day}")
        
        # Convert Unix timestamps to datetime objects
        prayer_times = {}
        for prayer in PRAYER_TIMES:
            if prayer in day_data:
                timestamp = day_data[prayer]
                prayer_times[prayer] = datetime.fromtimestamp(timestamp)
        
        return {
            "prayer_times": prayer_times,
            "hijri_date": day_data.get("hijri", ""),
            "zone": monthly_data.get("zone", self.zone),
            "date": target_date.strftime("%Y-%m-%d"),
        }

    async def _fetch_monthly_prayer_times(self, year: int, month: int) -> Dict[str, Any]:
        """Fetch monthly prayer times from API."""
        url = f"{API_BASE_URL}/v2/solat/{self.zone}"
        params = {"year": year, "month": month}
        
        _LOGGER.debug("Fetching monthly data from: %s with params: %s", url, params)
        
        try:
            async with async_timeout.timeout(API_TIMEOUT):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            json_data = await response.json()
                            
                            # Validate response structure
                            if not isinstance(json_data, dict) or "prayers" not in json_data:
                                raise UpdateFailed(
                                    f"Invalid API response structure: {list(json_data.keys()) if isinstance(json_data, dict) else type(json_data)}"
                                )
                            
                            prayers_data = json_data["prayers"]
                            if not isinstance(prayers_data, list) or not prayers_data:
                                raise UpdateFailed("No prayer data in API response")
                            
                            _LOGGER.info(
                                "Successfully fetched %d days of prayer data for %s/%s",
                                len(prayers_data), month, year
                            )
                            return json_data
                        else:
                            error_text = await response.text()
                            raise UpdateFailed(f"API request failed with status {response.status}: {error_text}")
                            
        except asyncio.TimeoutError:
            raise UpdateFailed("API request timed out")
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"API request failed: {err}")

    async def _fetch_prayer_times_for_date(self, target_date: date) -> Dict[str, Any]:
        """Legacy method - now uses monthly caching for efficiency."""
        # This method is kept for compatibility but now uses the optimized monthly fetch
        monthly_data = await self._fetch_monthly_prayer_times(target_date.year, target_date.month)
        return self._extract_daily_data_from_monthly(monthly_data, target_date)

    def get_next_prayer_info(self) -> Dict[str, Any]:
        """Get information about the next upcoming prayer."""
        if not self.data:
            return {}
        
        current_time = dt_util.now()
        prayer_times = self.data.get("prayer_times", {})
        next_day_times = self.data.get("next_day_prayer_times", {})
        
        # Check today's remaining prayers
        for prayer in PRAYER_TIMES:
            prayer_time = prayer_times.get(prayer)
            if prayer_time and current_time < prayer_time:
                return {
                    "prayer": prayer,
                    "malay_name": PRAYER_NAMES.get(prayer, prayer),
                    "time": prayer_time,
                    "is_tomorrow": False,
                }
        
        # If no more prayers today, check tomorrow's first prayer
        if next_day_times:
            for prayer in PRAYER_TIMES:
                prayer_time = next_day_times.get(prayer)
                if prayer_time:
        return {
                        "prayer": prayer,
                        "malay_name": PRAYER_NAMES.get(prayer, prayer),
                        "time": prayer_time,
                        "is_tomorrow": True,
                    }
        
        return {} 