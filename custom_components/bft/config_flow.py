"""Config flow for BFT."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

from .api import BFTApi, BFTApiError
from .const import DOMAIN, DEFAULT_DEVICE_NAME


class BFTConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle BFT configuration."""

    VERSION = 1

    async def async_step_user(self, user_input=None):

        errors = {}

        if user_input is not None:

            api = BFTApi(
                self.hass,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )

            try:
                device_id = await api.get_device_id(
                    DEFAULT_DEVICE_NAME
                )

                await self.async_set_unique_id(device_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title="Tor",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        "device_id": device_id,
                        "device_name": DEFAULT_DEVICE_NAME,
                    },
                )

            except BFTApiError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )
