"""
Coordinator for BrewPi ESP Control integration.
"""
import aiohttp
import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

class BrewPiDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, ip_address, scan_interval):
        super().__init__(
            hass,
            _LOGGER,
            name="BrewPi ESP Data",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.ip_address = ip_address
        self.data = None

    async def _async_update_data(self):
        url = f"http://{self.ip_address}/api/all_temp_control/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        self.data = await resp.json()
                        return self.data
                    raise UpdateFailed(f"API returned status {resp.status}")
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            raise UpdateFailed(f"Timeout updating BrewPi API: {e}")
        except Exception as e:
            raise UpdateFailed(f"Error updating BrewPi API: {e}")
