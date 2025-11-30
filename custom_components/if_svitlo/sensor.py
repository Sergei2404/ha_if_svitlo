from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BESvitloCurrentStatusSensor(coordinator, entry),
        BESvitloNextChangeSensor(coordinator, entry),
        BESvitloTodayIntervalsSensor(coordinator, entry),
        BESvitloTomorrowIntervalsSensor(coordinator, entry),
    ])

class BaseBESvitloSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry

    @property
    def available(self):
        return self.coordinator.last_update_success and self.coordinator.data is not None

class BESvitloCurrentStatusSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"IF Svitlo {self.entry.data['queue']} – Статус"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_current"

    @property
    def state(self):
        if self.coordinator.data is None:
            return "unknown"
        return "off" if self.coordinator.data.get("current_status") == 1 else "on"

class BESvitloNextChangeSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"IF Svitlo {self.entry.data['queue']} – Наступна зміна"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_next_change"

    @property
    def state(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("next_change")

class BESvitloTodayIntervalsSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"IF Svitlo {self.entry.data['queue']} – Сьогодні"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_intervals"

    @property
    def state(self):
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("today_intervals", "")

class BESvitloTomorrowIntervalsSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"IF Svitlo {self.entry.data['queue']} – Завтра"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_tomorrow_intervals"

    @property
    def state(self):
        if self.coordinator.data is None:
            return None
        tomorrow_intervals = self.coordinator.data.get("tomorrow_intervals")
        return tomorrow_intervals if tomorrow_intervals else "Немає відключень"