import voluptuous as vol
from homeassistant import config_entries
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
            vol.Required("queue"): vol.In(QUEUES)
        })
        return self.async_show_form(step_id="user", data_schema=schema)