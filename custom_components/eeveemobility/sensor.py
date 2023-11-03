"""EeveeMobility sensor platform."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import EeveeMobilityDataUpdateCoordinator
from .const import DOMAIN
from .entity import EeveeMobilityEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class EeveeMobilitySensorDescription(SensorEntityDescription):
    """Sensor entity description for EeveeMobility."""

    available_fn: Callable | None = None
    value_fn: Callable | None = None
    attributes_fn: Callable | None = None
    entity_picture_fn: Callable | None = None
    unique_id_fn: Callable | None = None
    translation_key: str | None = None


SENSOR_TYPES: tuple[EeveeMobilitySensorDescription, ...] = (
    EeveeMobilitySensorDescription(
        key="user",
        translation_key="user",
        unique_id_fn=lambda user: user.get("email"),
        icon="mdi:face-man",
        available_fn=lambda user: user.get("email") is not None,
        value_fn=lambda user: user.get("email"),
        attributes_fn=lambda user: user,
    ),
    EeveeMobilitySensorDescription(
        key="fleets",
        translation_key="fleet",
        unique_id_fn=lambda fleet: fleet.get("id"),
        icon="mdi:car-2-plus",
        available_fn=lambda fleet: fleet.get("id") is not None,
        value_fn=lambda fleet: fleet.get("fleet").get("name"),
        attributes_fn=lambda fleet: fleet,
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="car",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:car-electric",
        entity_picture_fn=lambda car: car.get("car").get("image"),
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("display_name"),
        attributes_fn=lambda car: car.get("car"),
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="odometer",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:counter",
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("odometer"),
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="battery",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:battery",
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("battery_level"),
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="carbon_emission_saved",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:molecule-co2",
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("carbon_emission_saved") / 1000,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        suggested_display_precision=0,
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="range",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:map-marker-distance",
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("range"),
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="license",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:numeric",
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("license"),
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="is_charging",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:ev-station",
        available_fn=lambda car: car.get("car") is not None,
        value_fn=lambda car: car.get("car").get("is_charging"),
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="addresses",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:map-marker",
        available_fn=lambda car: car.get("addresses") is not None,
        value_fn=lambda car: len(car.get("addresses")),
        attributes_fn=lambda car: {"addresses": car.get("addresses")},
    ),
    EeveeMobilitySensorDescription(
        key="cars",
        translation_key="events",
        unique_id_fn=lambda car: car.get("car").get("id"),
        icon="mdi:calendar-multiple",
        available_fn=lambda car: car.get("events") is not None,
        value_fn=lambda car: car.get("events").get("meta").get("total"),
        attributes_fn=lambda car: car.get("events"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the EeveeMobility sensors."""
    _LOGGER.debug("[sensor|async_setup_entry|async_add_entities|start]")
    coordinator: EeveeMobilityDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_name = ""
    entities: list[EeveeMobilitySensor] = []

    for sensor_type in SENSOR_TYPES:
        _LOGGER.debug(f"Searching for {sensor_type.key}-{sensor_type.translation_key}")
        if sensor_type.key in coordinator.data:
            _LOGGER.debug("Key found")
            item_id = None
            if sensor_type.key == "user":
                device_name = coordinator.data[sensor_type.key].get("email")
                entities.append(
                    EeveeMobilitySensor(coordinator, sensor_type, device_name, item_id)
                )
            elif sensor_type.key in ["fleets", "cars"]:
                for index, _ in enumerate(coordinator.data[sensor_type.key]):
                    entities.append(
                        EeveeMobilitySensor(
                            coordinator, sensor_type, device_name, index
                        )
                    )

    async_add_entities(entities)
    return


class EeveeMobilitySensor(EeveeMobilityEntity, RestoreSensor, SensorEntity):
    """Representation of an EeveeMobility sensor."""

    entity_description: EeveeMobilitySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EeveeMobilityDataUpdateCoordinator,
        description: EntityDescription,
        device_name: str,
        item_id: str,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, device_name, item_id)
        self.entity_id = f"sensor.{DOMAIN}_{self.entity_description.translation_key}_{self.entity_description.unique_id_fn(self.item)}"
        self._value: StateType = None

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self._value

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if self.coordinator.data is None:
            sensor_data = await self.async_get_last_sensor_data()
            if sensor_data is not None:
                self._value = sensor_data.native_value
            else:
                await self.coordinator.async_request_refresh()
        else:
            self._value = self.entity_description.value_fn(self.item)

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        if self.entity_description.entity_picture_fn is None:
            return None
        return self.entity_description.entity_picture_fn(self.item)

    @property
    def extra_state_attributes(self):
        """Return attributes for sensor."""
        if not self.coordinator.data:
            return {}
        attributes = {
            "last_synced": self.last_synced,
        }
        if self.entity_description.attributes_fn:
            return attributes | self.entity_description.attributes_fn(self.item)
        return attributes
