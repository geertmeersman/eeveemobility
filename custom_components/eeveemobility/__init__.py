"""EeveeMobility integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.storage import STORAGE_DIR, Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import EeveeMobilityClient
from .const import (
    CUSTOM_HEADERS,
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
        hass=hass,
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        custom_headers=CUSTOM_HEADERS,
    )

    storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
    if storage_dir.is_file():
        storage_dir.unlink()
    storage_dir.mkdir(exist_ok=True)
    store: Store = Store(hass, 1, f"{DOMAIN}/{entry.entry_id}")
    dev_reg = dr.async_get(hass)
    hass.data[DOMAIN][entry.entry_id] = coordinator = (
        EeveeMobilityDataUpdateCoordinator(
            hass,
            config_entry=entry,
            dev_reg=dev_reg,
            client=client,
            store=store,
        )
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # Unload the platforms first
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

        # Define blocking file operations
        def remove_storage_files():
            storage = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}/{entry.entry_id}")
            storage.unlink(missing_ok=True)  # Unlink (delete) the storage file

            storage_dir = Path(f"{hass.config.path(STORAGE_DIR)}/{DOMAIN}")
            # If the directory exists and is empty, remove it
            if storage_dir.is_dir() and not any(storage_dir.iterdir()):
                storage_dir.rmdir()

        # Offload the file system operations to a thread
        await hass.async_add_executor_job(remove_storage_files)

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

        meta = events.get("meta") if events else None
        total = meta.get("total") if meta else None

        if total is None:
            _LOGGER.warning(f"Missing 'meta.total' for car {car_id}: {events}")
            continue

        _LOGGER.debug(f"{car_id} API total: {total}")

        car_info = await self.client.request(f"cars/{car_id}")
        _LOGGER.debug(f"Car: {car}")
        addresses = await self.client.request(f"cars/{car_id}/addresses")
        _LOGGER.debug(f"Addresses: {addresses}")

        self.data["cars"].setdefault(car_id, {})

        if car.get("enabled"):
            car_data = self.data["cars"].get(car_id, {})
            store_total = car_data.get("events", {}).get("meta", {}).get("total")

            _LOGGER.debug(f"{total} events in the API and {store_total} in the store")

            if store_total is not None and total != store_total:
                limit = total - store_total + 1
                _LOGGER.debug(f"Updating the store with {limit} events")
                events = await self.client.request(
                    f"cars/{car_id}/events?limit={limit}"
                )
                self.data["cars"][car_id].setdefault("events", {}).setdefault(
                    "meta", {}
                )["total"] = total
                self.data["cars"][car_id].setdefault("events", {}).setdefault(
                    "data", []
                )
                if self.data["cars"][car_id]["events"]["data"]:
                    self.data["cars"][car_id]["events"]["data"].pop(0)
                self.data["cars"][car_id]["events"]["data"] = (
                    filter_json(events.get("data"), EVENTS_EXCLUDE_KEYS)
                    + self.data["cars"][car_id]["events"]["data"]
                )
            else:
                self.data["cars"][car_id].setdefault("events", {}).setdefault(
                    "data", []
                )
                if self.data["cars"][car_id]["events"]["data"]:
                    self.data["cars"][car_id]["events"]["data"].pop(0)
                self.data["cars"][car_id]["events"]["data"] = (
                    filter_json(events.get("data"), EVENTS_EXCLUDE_KEYS)
                    + self.data["cars"][car_id]["events"]["data"]
                )
        else:
            car_events = {}
            page = 1
            while True:
                _LOGGER.debug(f"Fetching page {page}")
                try:
                    events = await self.client.request(
                        f"cars/{car_id}/events?limit={EVENTS_LIMIT}&page={page}"
                    )
                    if events.get("links", {}).get("previous") is None:
                        car_events = filter_json(events, EVENTS_EXCLUDE_KEYS)
                    else:
                        car_events.setdefault("data", []).extend(
                            filter_json(events.get("data"), EVENTS_EXCLUDE_KEYS)
                        )
                    if events.get("links", {}).get("next") is None:
                        break
                except Exception as exception:
                    _LOGGER.warning(f"Exception {exception}")
                    break
                page += 1
                break  # No more than 1 page for the moment
            self.data["cars"][car_id]["events"] = car_events

        self.data["cars"][car_id]["car"] = filter_json(car_info, EVENTS_EXCLUDE_KEYS)
        if addresses:
            self.data["cars"][car_id]["addresses"] = filter_json(
                addresses, EVENTS_EXCLUDE_KEYS
            )

    await self.store.async_save(self.data)


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
