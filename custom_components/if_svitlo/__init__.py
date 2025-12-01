from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from datetime import timedelta
from .coordinator import BESvitloCoordinator
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    queue = entry.data["queue"]
    # Читаємо update_interval з data або options
    update_interval_seconds = entry.options.get("update_interval") or entry.data.get("update_interval", 60)
    update_interval = timedelta(seconds=update_interval_seconds)
    coordinator = BESvitloCoordinator(hass, queue, update_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)