import aiohttp
import logging
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

def parse_time(tstr):
    return datetime.strptime(tstr, "%H:%M").time()

def parse_date(dstr):
    """Parse date string in format DD.MM.YYYY"""
    return datetime.strptime(dstr, "%d.%m.%Y").date()

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

        # Очікується масив із записами для різних днів
        if not data or not isinstance(data, list) or len(data) == 0:
            raise UpdateFailed("Empty or invalid data from API")

        # Знаходимо запис для сьогодні
        today = datetime.now().date()
        today_str = today.strftime("%d.%m.%Y")
        
        entry = None
        for item in data:
            if isinstance(item, dict) and item.get("eventDate") == today_str:
                entry = item
                break
        
        # Якщо не знайдено сьогоднішній запис, беремо перший (fallback)
        if entry is None:
            _LOGGER.warning(f"No schedule found for today ({today_str}), using first available entry")
            entry = data[0]
        
        if not isinstance(entry, dict) or "queues" not in entry:
            raise UpdateFailed("Invalid data structure from API")
        
        queues = entry.get("queues", {})
        if self.queue not in queues:
            # Якщо черга не знайдена, можливо сьогодні немає відключень
            intervals = []
        else:
            intervals = queues[self.queue]
            if not isinstance(intervals, list):
                raise UpdateFailed("Invalid intervals format")

        now = datetime.now().time()

        current_status = 0  # за замовчуванням "увімкнено"
        next_change = None
        today_ranges = []

        for item in intervals:
            if not isinstance(item, dict) or "from" not in item or "to" not in item:
                continue
            try:
                start = parse_time(item["from"])
                end   = parse_time(item["to"])
            except (ValueError, KeyError) as e:
                _LOGGER.warning(f"Invalid time format in interval: {item}, error: {e}")
                continue

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