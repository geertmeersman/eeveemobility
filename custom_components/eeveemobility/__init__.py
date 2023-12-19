"""EeveeMobility integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path

from aioeeveemobility import EeveeMobilityClient
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import STORAGE_DIR, Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENTS_EXCLUDE_KEYS,
    EVENTS_LIMIT,
    PLATFORMS,
)
from .utils import filter_json

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EeveeMobility from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = EeveeMobilityClient(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
    )

    storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
    if storage_dir.is_file():
        storage_dir.unlink()
    storage_dir.mkdir(exist_ok=True)
    store: Store = Store(hass, 1, f"{DOMAIN}/{entry.entry_id}")
    dev_reg = dr.async_get(hass)
    hass.data[DOMAIN][
        entry.entry_id
    ] = coordinator = EeveeMobilityDataUpdateCoordinator(
        hass,
        config_entry=entry,
        dev_reg=dev_reg,
        client=client,
        store=store,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        storage = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}/{entry.entry_id}")
        storage.unlink(True)
        storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
        if storage_dir.is_dir() and not any(storage_dir.iterdir()):
            storage_dir.rmdir()

    return unload_ok


class EeveeMobilityDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for EeveeMobility."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        dev_reg: dr.DeviceRegistry,
        client: EeveeMobilityClient,
        store: Store,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=config_entry.data[CONF_SCAN_INTERVAL]),
        )
        self._debug = _LOGGER.isEnabledFor(logging.DEBUG)
        self._config_entry = config_entry
        self._device_registry = dev_reg
        self.hass = hass
        self.client = client
        self.store = store

    async def async_config_entry_first_refresh(self) -> None:
        """Refresh data for the first time when a config entry is setup."""
        self.data = await self.store.async_load() or {
            "user": {},
            "fleets": [],
            "cars": {},
        }
        _LOGGER.debug("Loading store data")
        await super().async_config_entry_first_refresh()

    async def get_data(self) -> dict | None:
        """Get the data from the Eevee client."""
        self.data["user"] = await self.client.request("user")
        _LOGGER.debug(f"User: {self.data['user']}")
        fleets = await self.client.request(f"user/{self.data['user'].get('id')}/fleets")
        self.data["fleets"] = {str(fleet.get("id")): fleet for fleet in fleets}
        _LOGGER.debug(f"Fleets: {self.data['fleets']}")
        cars = await self.client.request("cars")
        self.data.setdefault("cars", {})

        for car in cars:
            car_id = str(car.get("id"))
            events = await self.client.request(
                f"cars/{car_id}/events?limit=1&force_refresh=1"
            )
            _LOGGER.debug(f"{car_id} API total: {events.get('meta').get('total')}")
            car_info = await self.client.request(f"cars/{car_id}")
            _LOGGER.debug(f"Car: {car}")
            addresses = await self.client.request(f"cars/{car_id}/addresses")
            _LOGGER.debug(f"Addresses: {addresses}")
            if car_id in self.data["cars"]:
                total = events.get("meta").get("total")
                store_total = (
                    self.data["cars"].get(car_id).get("events").get("meta").get("total")
                )
                _LOGGER.debug(
                    f"{total} events in the API and {store_total} in the store"
                )
                if total != store_total:
                    limit = total - store_total + 1
                    _LOGGER.debug(f"Updating the store with {limit} events")
                    events = await self.client.request(
                        f"cars/{car_id}/events?limit={limit}"
                    )
                    self.data["cars"][car_id]["events"]["meta"]["total"] = total
                    # Remove the first item and replace it with it's most up to date version, supposing the API only updates the first item in the list
                    self.data["cars"][car_id]["events"]["data"].pop(0)
                    self.data["cars"][car_id]["events"]["data"] = (
                        filter_json(events.get("data"), EVENTS_EXCLUDE_KEYS)
                        + self.data["cars"][car_id]["events"]["data"]
                    )
                else:
                    self.data["cars"][car_id]["events"]["data"].pop(0)
                    self.data["cars"][car_id]["events"]["data"] = (
                        filter_json(events.get("data"), EVENTS_EXCLUDE_KEYS)
                        + self.data["cars"][car_id]["events"]["data"]
                    )

            else:
                car_events = {}
                page = 1
                self.data["cars"].setdefault(car_id, {})
                while True:
                    _LOGGER.debug(f"Fetching page {page}")
                    events = await self.client.request(
                        f"cars/{car_id}/events?limit={EVENTS_LIMIT}&page={page}"
                    )
                    if events.get("links").get("previous") is None:
                        car_events = filter_json(events, EVENTS_EXCLUDE_KEYS)
                    else:
                        car_events.get("data").extend(
                            filter_json(events.get("data"), EVENTS_EXCLUDE_KEYS)
                        )
                    if events.get("links").get("next") is None:
                        break
                    page += 1
                self.data["cars"][car_id]["events"] = car_events
            self.data["cars"][car_id]["car"] = filter_json(
                car_info, EVENTS_EXCLUDE_KEYS
            )
            self.data["cars"][car_id]["addresses"] = filter_json(
                addresses, EVENTS_EXCLUDE_KEYS
            )
        await self.store.async_save(self.data)

    async def _async_update_data(self) -> dict | None:
        """Update data."""
        _LOGGER.debug("Updating data")
        if self._debug:
            await self.get_data()
        else:
            try:
                await self.get_data()
            except Exception as exception:
                _LOGGER.warning(f"Exception {exception}")

        if len(self.data) > 0:
            current_items = {
                list(device.identifiers)[0][1]
                for device in dr.async_entries_for_config_entry(
                    self._device_registry, self._config_entry.entry_id
                )
            }

            if stale_items := current_items - {
                f"{self._config_entry.entry_id}_{self.data['user'].get('email')}"
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
            return self.data
        return {}


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.info("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        new = {**config_entry.data}
        # TODO: modify Config Entry data
        if CONF_SCAN_INTERVAL not in new:
            new[CONF_SCAN_INTERVAL] = DEFAULT_SCAN_INTERVAL

        config_entry.version = 2
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True
