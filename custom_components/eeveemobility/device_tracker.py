"""EeveeMobility device tracking."""
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_BATTERY_LEVEL, ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import EeveeMobilityDataUpdateCoordinator
from .const import DOMAIN
from .entity import EeveeMobilityEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up an EeveeMobility device_tracker entry."""

    _LOGGER.debug("Creating REST device tracker")
    coordinator: EeveeMobilityDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    if coordinator.data is not None and "cars" in coordinator.data:
        for idx in coordinator.data.get("cars"):
            if "events" in coordinator.data.get("cars").get(idx):
                events = coordinator.data.get("cars").get(idx).get("events")
                if "data" in events and events.get("meta").get("total") > 0:
                    async_add_entities(
                        [
                            EeveeMobilityGPSEntity(
                                hass,
                                entry,
                                coordinator,
                                coordinator.data["user"].get("email"),
                                idx,
                            )
                        ]
                    )


@dataclass
class DeviceTrackerEntityDescription(EntityDescription):
    """Device tracker entity description for EeveeMobility."""

    unique_id_fn: Callable | None = None
    available_fn: Callable | None = None


class EeveeMobilityGPSEntity(EeveeMobilityEntity, TrackerEntity, RestoreEntity):
    """Represent a tracked device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: EeveeMobilityDataUpdateCoordinator,
        device_name: str,
        item_id: str,
    ):
        """Set up GPS entity."""
        self.coordinator = coordinator
        self.entity_description = DeviceTrackerEntityDescription(
            key="cars",
            translation_key="gps",
            icon="mdi:crosshairs-gps",
            unique_id_fn=lambda car: car.get("car").get("id"),
            available_fn=lambda car: car.get("car") is not None,
        )
        self.entry = entry
        super().__init__(coordinator, self.entity_description, device_name, item_id)
        self._attr_translation_key = "gps"
        self.entity_id = f"device_tracker.{DOMAIN}_{self.entity_description.translation_key}_{self.entity_description.unique_id_fn(self.item)}"
        self._item_id = item_id
        self._longitude = None
        self._latitude = None
        self._battery = None
        self._attributes = None

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the device.

        Percentage from 0-100.
        """
        return self._battery

    @property
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        return self._latitude

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        return self._longitude

    @property
    def source_type(self) -> SourceType:
        """Return the source type of the device."""
        return SourceType.GPS

    def update_gps_state(self):
        """Update state based on REST GPS State."""
        if self.coordinator is None:
            self._location = (None, None)
            return False
        if len(self.coordinator.data) and "events" in self.coordinator.data.get(
            "cars"
        ).get(self._item_id):
            events = self.coordinator.data.get("cars").get(self._item_id).get("events")
            if "data" in events and events.get("meta").get("total") > 0:
                for event in events.get("data"):
                    address = None
                    if event.get("type") == "parked":
                        address = event.get("parked").get("address")
                    elif event.get("type") == "driving":
                        address = event.get("trip").get("end_address")
                    elif event.get("type") == "charging":
                        address = event.get("charge").get("address")
                    if address is not None:
                        self._latitude = address.get(ATTR_LATITUDE)
                        self._longitude = address.get(ATTR_LONGITUDE)
                        self._battery = event.get("percent_end")
                        self.last_synced = datetime.now()
                        self._attributes = {
                            "last_synced": self.last_synced,
                        }
                        self.async_write_ha_state()
                        return True
        return False

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT events."""
        await super().async_added_to_hass()

        # Don't restore if status is fetched from coordinator data
        if self.update_gps_state():
            return

        if (state := await self.async_get_last_state()) is None:
            self._location = (None, None)
            self._battery = None
            return

        attr = state.attributes
        self._latitude = attr.get(ATTR_LATITUDE)
        self._longitude = attr.get(ATTR_LONGITUDE)
        self._battery = attr.get(ATTR_BATTERY_LEVEL)
