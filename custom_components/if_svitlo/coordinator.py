import aiohttp
import logging
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

def parse_time(tstr):
    return datetime.strptime(tstr, "%H:%M").time()

class BESvitloCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, queue: str):
        super().__init__(
            hass,
            logger=_LOGGER,
            name="be_svitlo",
            update_interval=timedelta(seconds=60),  # оновлення раз на хвилину
        )
        self.queue = queue

    async def _async_update_data(self):
        url = API_URL.format(self.queue)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()

        # Очікується масив із одним елементом (план на сьогодні)
        if not data:
            return None

        entry = data[0]
        intervals = entry["queues"][self.queue]

        now = datetime.now().time()

        current_status = 0  # за замовчуванням "увімкнено"
        next_change = None
        today_ranges = []

        for item in intervals:
            start = parse_time(item["from"])
            end   = parse_time(item["to"])

            today_ranges.append(f"{item['from']}-{item['to']}")

            if start <= now < end:
                current_status = 1  # вимкнено зараз

            # знаходження наступної зміни
            if now < start:
                if next_change is None:
                    next_change = start
                else:
                    next_change = min(next_change, start)
            if now < end and current_status == 1:
                # коли повернеться світло
                if next_change is None:
                    next_change = end
                else:
                    next_change = min(next_change, end)

        return {
            "current_status": current_status,
            "next_change": next_change.strftime("%H:%M") if next_change else None,
            "today_intervals": ", ".join(today_ranges),
        }