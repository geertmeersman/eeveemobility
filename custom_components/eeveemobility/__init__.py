"""EeveeMobility integration."""
from __future__ import annotations

import logging

from aioeeveemobility import EeveeMobilityClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from requests.exceptions import ConnectionError

from .const import COORDINATOR_UPDATE_INTERVAL, DOMAIN, PLATFORMS
from .exceptions import (
    BadCredentialsException,
    EeveeMobilityException,
    EeveeMobilityServiceException,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EeveeMobility from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = EeveeMobilityClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    dev_reg = dr.async_get(hass)
    hass.data[DOMAIN][
        entry.entry_id
    ] = coordinator = EeveeMobilityDataUpdateCoordinator(
        hass,
        config_entry_id=entry.entry_id,
        dev_reg=dev_reg,
        client=client,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class EeveeMobilityDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for EeveeMobility."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry_id: str,
        dev_reg: dr.DeviceRegistry,
        client: EeveeMobilityClient,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self._debug = _LOGGER.isEnabledFor(logging.DEBUG)
        self._config_entry_id = config_entry_id
        self._device_registry = dev_reg
        self.client = client
        self.hass = hass

    async def get_data(self) -> dict | None:
        """Get the data from the Eevee client."""
        items = {}
        items["user"] = await self.client.request("user")
        _LOGGER.debug(f"User: {items['user']}")
        items["fleets"] = await self.client.request(
            f"user/{items['user'].get('id')}/fleets"
        )
        _LOGGER.debug(f"Fleets: {items['fleets']}")
        items["cars"] = {}
        cars = await self.client.request("cars")
        for idx, car in enumerate(cars):
            car_id = car.get("id")
            events = await self.client.request(
                f"cars/{car_id}/events?limit=50&force_refresh=1"
            )
            _LOGGER.debug(f"Events: {events}")
            car_info = await self.client.request(f"cars/{car_id}")
            _LOGGER.debug(f"Car: {car}")
            addresses = await self.client.request(f"cars/{car_id}/addresses")
            _LOGGER.debug(f"Addresses: {addresses}")
            items["cars"][idx] = {
                "car": car_info,
                "addresses": addresses,
                "events": events,
            }
        return items

    async def _async_update_data(self) -> dict | None:
        """Update data."""
        _LOGGER.debug("Updating data")
        items = {}
        if self._debug:
            items = await self.get_data()
        try:
            items = await self.get_data()
        except ConnectionError as exception:
            raise UpdateFailed(f"ConnectionError {exception}") from exception
        except BadCredentialsException as exception:
            raise UpdateFailed(f"BadCredentialsException {exception}") from exception
        except EeveeMobilityServiceException as exception:
            raise UpdateFailed(
                f"EeveeMobilityServiceException {exception}"
            ) from exception
        except EeveeMobilityException as exception:
            raise UpdateFailed(f"EeveeMobilityException {exception}") from exception
        except Exception as exception:
            raise UpdateFailed(f"Exception {exception}") from exception

        if len(items) > 0:
            current_items = {
                list(device.identifiers)[0][1]
                for device in dr.async_entries_for_config_entry(
                    self._device_registry, self._config_entry_id
                )
            }

            if stale_items := current_items - {
                f"{self._config_entry_id}_{items['user'].get('email')}"
            }:
                for device_key in stale_items:
                    if device := self._device_registry.async_get_device(
                        {(DOMAIN, device_key)}
                    ):
                        _LOGGER.debug(
                            f"[init|EeveeMobilityDataUpdateCoordinator|_async_update_data|async_remove_device] {device_key}",
                            True,
                        )
                        self._device_registry.async_remove_device(device.id)
            return items
        return []
