import aiohttp
import logging
from datetime import datetime, date, time, timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from .const import API_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)

HA_REFRESH_INTERVAL = timedelta(seconds=30)


def parse_time(tstr):
    return datetime.strptime(tstr, "%H:%M").time()

def parse_date(dstr):
    """Parse date string in format DD.MM.YYYY"""
    return datetime.strptime(dstr, "%d.%m.%Y").date()


class BESvitloCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, queue: str, update_interval: timedelta = None):
        if update_interval is None:
            update_interval = timedelta(seconds=60)
        # HA refreshes every 30s; API is fetched at most once per update_interval
        super().__init__(
            hass,
            logger=_LOGGER,
            name="be_svitlo",
            update_interval=HA_REFRESH_INTERVAL,
        )
        self.queue = queue
        self._api_interval = update_interval
        self._last_api_fetch: datetime | None = None
        self._raw_data: list | None = None

    async def _fetch_api(self):
        url = API_URL.format(self.queue)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"HTTP {resp.status}")
                data = await resp.json()
        if not data or not isinstance(data, list) or len(data) == 0:
            raise UpdateFailed("Empty or invalid data from API")
        self._raw_data = data
        self._last_api_fetch = datetime.now()

    def _calculate(self) -> dict:
        data = self._raw_data
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        today_str = today.strftime("%d.%m.%Y")
        tomorrow_str = tomorrow.strftime("%d.%m.%Y")

        today_entry = None
        tomorrow_entry = None

        for item in data:
            if isinstance(item, dict):
                event_date = item.get("eventDate")
                if event_date == today_str:
                    today_entry = item
                elif event_date == tomorrow_str:
                    tomorrow_entry = item

        if today_entry is None:
            _LOGGER.warning(f"No schedule found for today ({today_str}), using first available entry")
            today_entry = data[0] if data else None

        if not isinstance(today_entry, dict) or "queues" not in today_entry:
            raise UpdateFailed("Invalid data structure from API")

        queues = today_entry.get("queues", {})
        intervals = queues.get(self.queue, []) if self.queue in queues else []
        if not isinstance(intervals, list):
            raise UpdateFailed("Invalid intervals format")

        tomorrow_intervals = []
        if tomorrow_entry and isinstance(tomorrow_entry, dict) and "queues" in tomorrow_entry:
            tomorrow_queues = tomorrow_entry.get("queues", {})
            if self.queue in tomorrow_queues:
                tomorrow_queue_data = tomorrow_queues[self.queue]
                if isinstance(tomorrow_queue_data, list):
                    for item in tomorrow_queue_data:
                        if isinstance(item, dict) and "from" in item and "to" in item:
                            tomorrow_intervals.append(f"{item['from']}-{item['to']}")

        now = datetime.now().time()
        current_status = 0
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
                current_status = 1

            if now < start:
                next_change = start if next_change is None else min(next_change, start)
            if now < end and current_status == 1:
                next_change = end if next_change is None else min(next_change, end)

        next_change_minutes = 0
        if next_change:
            now_dt = datetime.now()
            next_change_dt = datetime.combine(today, next_change)
            if next_change_dt < now_dt:
                next_change_dt = datetime.combine(tomorrow, next_change)
            delta = next_change_dt - now_dt
            next_change_minutes = int(delta.total_seconds() / 60)

        return {
            "current_status": current_status,
            "next_change": next_change.strftime("%H:%M") if next_change else None,
            "next_change_minutes": next_change_minutes,
            "today_intervals": ", ".join(today_ranges) if today_ranges else "",
            "tomorrow_intervals": ", ".join(tomorrow_intervals) if tomorrow_intervals else None,
        }

    async def _async_update_data(self):
        now = datetime.now()
        need_fetch = (
            self._raw_data is None
            or self._last_api_fetch is None
            or (now - self._last_api_fetch) >= self._api_interval
        )
        if need_fetch:
            _LOGGER.debug("Fetching schedule from API")
            await self._fetch_api()
        return self._calculate()
