"""Binary sensor entity to indicate the need to resupply."""
import logging


from homeassistant import config_entries, core
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers import entity_platform
from homeassistant.const import STATE_UNAVAILABLE
from . import InventoryManagerItem, InventoryManagerEntityType
from .const import (
    CONF_SENSOR_BEFORE_EMPTY,
    DOMAIN,
    STRING_PROBLEM_ENTITY,
    UNIQUE_ID,
    ENTITY_ID,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Set up sensors from a config entry created in the integrations UI."""
    _LOGGER.debug("binary_sensor.async_setup_entry %s", config_entry.data)
    config = hass.data[DOMAIN][config_entry.entry_id]

    entity_id = config.entity_config[InventoryManagerEntityType.WARNING][
        ENTITY_ID
    ]

    # Prevent duplicates by checking existing entities
    existing_entities = [entity.entity_id for entity in hass.states.async_all()]

    if entity_id in existing_entities:
        _LOGGER.debug("Skipping duplicate entity setup: %s", entity_id)
        return

    sensors = [WarnSensor(hass, config, entity_id)]
    async_add_entities(sensors, update_before_add=True)


class WarnSensor(BinarySensorEntity):
    """Represents a warning entity."""

    _attr_has_entity_name = True

    def __init__(self, hass: core.HomeAssistant, item: InventoryManagerItem, entity_id):
        """Create a new object."""
        super().__init__()
        _LOGGER.debug("Initializing WarnSensor for %s", item.name)
        self.hass = hass
        self.item: InventoryManagerItem = item
        _LOGGER.debug("WarnSensor - setting WARNING for %s", item.name)
        self.item.entity[InventoryManagerEntityType.WARNING] = self
        self.platform = entity_platform.async_get_current_platform()

        self.device_id = item.device_id
        self.device_info = item.device_info

        self.should_poll = False
        self.device_class = BinarySensorDeviceClass.PROBLEM
        self.unique_id = item.entity_config[InventoryManagerEntityType.WARNING][
            UNIQUE_ID
        ]

        self.translation_key = STRING_PROBLEM_ENTITY
        self.available = False
        self.is_on = False
        self.entity_id = entity_id
        _LOGGER.debug("WarnSensor - %s has ID `%s` `%s`", item.name, self.unique_id, self.entity_id)

    def update(self):
        """Update the state of the entity."""
        _LOGGER.debug("Updating binary sensor for %s", self.device_id)

        days_remaining = self.item.days_remaining()
        if days_remaining == STATE_UNAVAILABLE:
            self.is_on = False
            self.available = False
        else:
            self.available = True
            self.is_on = days_remaining < self.item.data[CONF_SENSOR_BEFORE_EMPTY]
        self.schedule_update_ha_state()
