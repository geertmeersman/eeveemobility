"""Base EeveeMobility entity."""

from __future__ import annotations

from datetime import datetime
import logging

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EeveeMobilityDataUpdateCoordinator
from .const import ATTRIBUTION, DOMAIN, NAME, VERSION, WEBSITE

_LOGGER = logging.getLogger(__name__)


class EeveeMobilityEntity(CoordinatorEntity[EeveeMobilityDataUpdateCoordinator]):
    """Base EeveeMobility entity."""

    _attr_attribution = ATTRIBUTION
    _unrecorded_attributes = frozenset(
        {
            "data",
            "links",
            "meta",
            "fleet",
            "brand",
            "addresses",
            "address",
            "rates",
            "last_synced",
        }
    )

    def __init__(
        self,
        coordinator: EeveeMobilityDataUpdateCoordinator,
        description: EntityDescription,
        device_name: str,
        item_id: str,
    ) -> None:
        """Initialize EeveeMobility entities."""
        super().__init__(coordinator)
        self.entity_description = description
        self.item_id = item_id
        if item_id is None:
            self._identifier = description.key
        else:
            self._identifier = f"{description.key}_{item_id}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.config_entry.entry_id}_{device_name}")
            },
            name=f"{NAME} {device_name}",
            manufacturer=NAME,
            configuration_url=WEBSITE,
            entry_type=DeviceEntryType.SERVICE,
            sw_version=VERSION,
        )
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{self.entity_description.translation_key}_{self.entity_description.unique_id_fn(self.item)}"
        self.last_synced = datetime.now()
        _LOGGER.debug(f"[EeveeMobilityEntity|init] {self._identifier}")

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if len(self.coordinator.data):
            self.last_synced = datetime.now()
            self.async_write_ha_state()
            return
        _LOGGER.debug(
            f"[EeveeMobilityEntity|_handle_coordinator_update] {self._attr_unique_id}: async_write_ha_state ignored since API fetch failed or not found",
            True,
        )

    @property
    def item(self) -> dict | None:
        """Return the data for this entity safely."""
        data = self.coordinator.data or {}

        # First-level lookup: key may be missing
        group = data.get(self.entity_description.key)
        if group is None:
            return None

        # For iterated sensors (cars/fleets)
        if isinstance(group, list):
            # item_id might be None, out of range, or not an int
            if self.item_id is None:
                return None
            try:
                return group[self.item_id]
            except (IndexError, TypeError):
                return None

        # For single object sensors (user)
        return group

    @property
    def available(self) -> bool:
        """Return if the entity is available."""
        item = self.item
        if item is None:
            return False
        return super().available and self.entity_description.available_fn(item)

    async def async_update(self) -> None:
        """Update the entity.  Only used by the generic entity update service."""
        return
