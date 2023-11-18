"""Config flow to configure the Eevee Mobililty integration."""
from abc import ABC, abstractmethod
import logging
from typing import Any

from aioeeveemobility import EeveeMobilityClient
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowHandler, FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.typing import UNDEFINED
import voluptuous as vol

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    NAME,
    SCAN_INTERVAL_MAX,
    SCAN_INTERVAL_MIN,
)
from .exceptions import BadCredentialsException, EeveeMobilityServiceException
from .models import EeveeMobilityConfigEntryData

_LOGGER = logging.getLogger(__name__)

DEFAULT_ENTRY_DATA = EeveeMobilityConfigEntryData(
    email=None,
    password=None,
    scan_interval=DEFAULT_SCAN_INTERVAL,
)


class EeveeMobilityCommonFlow(ABC, FlowHandler):
    """Base class for EeveeMobility flows."""

    def __init__(self, initial_data: EeveeMobilityConfigEntryData) -> None:
        """Initialize EeveeMobilityCommonFlow."""
        self.initial_data = initial_data
        self.new_entry_data = EeveeMobilityConfigEntryData()
        self.new_title: str | None = None

    @abstractmethod
    def finish_flow(self) -> FlowResult:
        """Finish the flow."""

    def new_data(self):
        """Construct new data."""
        return DEFAULT_ENTRY_DATA | self.initial_data | self.new_entry_data

    async def async_validate_input(self, user_input: dict[str, Any]) -> None:
        """Validate user credentials."""

        client = EeveeMobilityClient(
            email=user_input[CONF_EMAIL],
            password=user_input[CONF_PASSWORD],
        )

        user = await self.hass.async_add_executor_job(client.request, "user")

        return user

    async def async_step_connection_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle connection configuration."""
        errors: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            test = await self.test_connection(user_input)
            if not test["errors"]:
                self.new_title = user_input[CONF_EMAIL]
                self.new_entry_data |= user_input
                await self.async_set_unique_id(f"{DOMAIN}_" + user_input[CONF_EMAIL])
                self._abort_if_unique_id_configured()
                _LOGGER.debug(f"New account {self.new_title} added")
                return self.finish_flow()
            errors = test["errors"]
        fields = {
            vol.Required(CONF_EMAIL): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="email")
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
            vol.Required(
                CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
            ): NumberSelector(
                NumberSelectorConfig(
                    min=SCAN_INTERVAL_MIN,
                    max=SCAN_INTERVAL_MAX,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
        return self.async_show_form(
            step_id="connection_init",
            data_schema=vol.Schema(fields),
            errors=errors,
        )

    async def test_connection(self, user_input: dict[str, Any] | None = None) -> dict:
        """Test the connection to EeveeMobility."""
        errors: dict = {}
        user: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            try:
                user = await self.async_validate_input(user_input)
            except AssertionError as exception:
                errors["base"] = "cannot_connect"
                _LOGGER.debug(f"[test_connection|login] AssertionError {exception}")
            except ConnectionError:
                errors["base"] = "cannot_connect"
            except EeveeMobilityServiceException:
                errors["base"] = "service_error"
            except BadCredentialsException:
                errors["base"] = "invalid_auth"
            except Exception as exception:
                errors["base"] = "unknown"
                _LOGGER.debug(exception)
        return {"user": user, "errors": errors}

    async def async_step_email_password(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure password."""
        errors: dict = {}

        if user_input is not None:
            user_input = self.new_data() | user_input
            test = await self.test_connection(user_input)
            if not test["errors"]:
                self.new_entry_data |= EeveeMobilityConfigEntryData(
                    password=user_input[CONF_PASSWORD],
                )
                _LOGGER.debug(
                    f"Password and email changed for {test['user'].get('email')}"
                )
                return self.finish_flow()

        fields = {
            vol.Required(CONF_EMAIL): TextSelector(
                TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="email")
            ),
            vol.Required(CONF_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD, autocomplete="current-password"
                )
            ),
        }
        return self.async_show_form(
            step_id="email_password",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields),
                self.initial_data
                | EeveeMobilityConfigEntryData(
                    password=None,
                ),
            ),
            errors=errors,
        )

    async def async_step_scan_interval(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Configure update interval."""
        errors: dict = {}

        if user_input is not None:
            self.new_entry_data |= user_input
            return self.finish_flow()

        fields = {
            vol.Required(CONF_SCAN_INTERVAL): NumberSelector(
                NumberSelectorConfig(
                    min=SCAN_INTERVAL_MIN,
                    max=SCAN_INTERVAL_MAX,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
        return self.async_show_form(
            step_id="scan_interval",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(fields),
                self.initial_data,
            ),
            errors=errors,
        )


class EeveeMobilityOptionsFlow(EeveeMobilityCommonFlow, OptionsFlow):
    """Handle EeveeMobility options."""

    general_settings: dict

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize EeveeMobility options flow."""
        self.config_entry = config_entry
        super().__init__(initial_data=config_entry.data)  # type: ignore[arg-type]

    @callback
    def finish_flow(self) -> FlowResult:
        """Update the ConfigEntry and finish the flow."""
        new_data = DEFAULT_ENTRY_DATA | self.initial_data | self.new_entry_data
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            data=new_data,
            title=self.new_title or UNDEFINED,
        )
        self.hass.async_create_task(
            self.hass.config_entries.async_reload(self.config_entry.entry_id)
        )
        return self.async_create_entry(title="", data={})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage EeveeMobility options."""
        return self.async_show_menu(
            step_id="options_init",
            menu_options=[
                "email_password",
                "scan_interval",
            ],
        )


class EeveeMobilityConfigFlow(EeveeMobilityCommonFlow, ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EeveeMobility."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize EeveeMobility Config Flow."""
        super().__init__(initial_data=DEFAULT_ENTRY_DATA)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> EeveeMobilityOptionsFlow:
        """Get the options flow for this handler."""
        return EeveeMobilityOptionsFlow(config_entry)

    @callback
    def finish_flow(self) -> FlowResult:
        """Create the ConfigEntry."""
        title = self.new_title or NAME
        return self.async_create_entry(
            title=title,
            data=DEFAULT_ENTRY_DATA | self.new_entry_data,
        )

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle a flow initialized by the user."""
        return await self.async_step_connection_init()
