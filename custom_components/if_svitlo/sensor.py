from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BESvitloCurrentStatusSensor(coordinator, entry),
        BESvitloNextChangeSensor(coordinator, entry),
        BESvitloTodayIntervalsSensor(coordinator, entry),
    ])

class BaseBESvitloSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self.entry = entry

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    @callback
    def _handle_coordinator_update(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.coordinator.async_add_listener(self._handle_coordinator_update)

class BESvitloCurrentStatusSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"BE Svitlo {self.entry.data['queue']} – Статус"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_current"

    @property
    def state(self):
        return "off" if self.coordinator.data["current_status"] == 1 else "on"

class BESvitloNextChangeSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"BE Svitlo {self.entry.data['queue']} – Наступна зміна"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_next_change"

    @property
    def state(self):
        return self.coordinator.data["next_change"]

class BESvitloTodayIntervalsSensor(BaseBESvitloSensor):
    @property
    def name(self):
        return f"BE Svitlo {self.entry.data['queue']} – Сьогодні"

    @property
    def unique_id(self):
        return f"{self.entry.entry_id}_intervals"

    @property
    def state(self):
        return self.coordinator.data["today_intervals"]