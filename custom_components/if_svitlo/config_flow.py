import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

QUEUES = [f"{i}.{j}" for i in range(1, 5) for j in (1, 2)]

class BESvitloFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Черга {user_input['queue']}",
                data=user_input
            )

        schema = vol.Schema({
            vol.Required("queue"): vol.In(QUEUES),
            vol.Optional("update_interval", default=60): vol.All(
                vol.Coerce(int),
                vol.Range(min=10, max=3600)
            )
        })
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return BESvitloOptionsFlowHandler(config_entry)


class BESvitloOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            # Оновлюємо дані конфігурації
            return self.async_create_entry(title="", data=user_input)

        # Отримуємо поточне значення з options або data
        current_interval = (
            self.config_entry.options.get("update_interval") or
            self.config_entry.data.get("update_interval", 60)
        )
        
        schema = vol.Schema({
            vol.Required(
                "update_interval",
                default=current_interval
            ): vol.All(
                vol.Coerce(int),
                vol.Range(min=10, max=3600)
            )
        })
        return self.async_show_form(step_id="init", data_schema=schema)