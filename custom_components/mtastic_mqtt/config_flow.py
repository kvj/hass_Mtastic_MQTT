from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector

from .constants import DOMAIN

import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

async def _validate(hass, input: dict) -> (str | None, dict):
    if "id" in input and (len(input["id"]) != 9 or input["id"][0] != "!"):
        return "invalid_id", None
    # if not input.get("pb_topic") and not input.get("json_topic"):
    #     return "no_topic", None
    # if input.get("pb_topic") and input.get("json_topic"):
    #     return "no_topic", None
    return None, input

def _create_schema(hass, input: dict, flow: str = "config"):
    schema = vol.Schema({})
    if flow == "config":
        schema = schema.extend({
            vol.Required("title", description={"suggested_value": input.get("title", "")}): selector({"text": {}}),
        })
    schema = schema.extend({
        vol.Required("id", description={"suggested_value": input.get("id", "")}): selector({
            "text": {}
        }),
        vol.Required("pb_topic", description={"suggested_value": input.get("pb_topic", "")}): selector({
            "text": {}
        }),
        vol.Optional("key", description={"suggested_value": input.get("key", "")}): selector({
            "text": { "type": "password" }
        }),
        vol.Optional("stat_topic", description={"suggested_value": input.get("stat_topic", "")}): selector({
            "text": {}
        }),
    })
    return schema

class ConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):


    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=_create_schema(self.hass, {
            }))
        else:
            _LOGGER.debug(f"Input: {user_input}")
            err, data = await _validate(self.hass, user_input)
            if err is None:
                # await self.async_set_unique_id(data["id"])
                # self._abort_if_unique_id_configured()
                _LOGGER.debug(f"Ready to save: {data}")
                return self.async_create_entry(title=data["title"], options=data, data={})
            else:
                return self.async_show_form(step_id="user", data_schema=_create_schema(self.hass, user_input), errors=dict(base=err))

    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlowWithConfigEntry):

    def __init__(self, entry):
        super().__init__(entry)

    async def async_step_init(self, user_input=None):
        if user_input is None:
            _LOGGER.debug(f"Making options: {self.config_entry.as_dict()}")
            return self.async_show_form(step_id="init", data_schema=_create_schema(self.hass, self.options, flow="options"))
        else:
            _LOGGER.debug(f"Input: {user_input}")
            err, data = await _validate(self.hass, user_input)
            if err is None:
                _LOGGER.debug(f"Ready to update: {data}")
                result = self.async_create_entry(title="", data=data)
                return result
            else:
                return self.async_show_form(step_id="init", data_schema=_create_schema(self.hass, user_input, flow="options"), errors=dict(base=err))
