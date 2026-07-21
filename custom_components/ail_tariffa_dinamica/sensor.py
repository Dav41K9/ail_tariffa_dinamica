"""Sensori per le tariffe AIL + data + fascia più economica."""
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, SENSOR_CONFIGS, TIME_SLOTS, TARIFF_UNIT

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Configura i sensori per AIL."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entry_id = entry.entry_id

    entities = [
        AILTariffSensor(coordinator, entry_id, slot_key, config)
        for slot_key, config in SENSOR_CONFIGS.items()
    ]

    entities.append(AILTariffDateSensor(coordinator, entry_id))
    entities.append(AILCheapestSlotSensor(coordinator, entry_id))

    async_add_entities(entities, update_before_add=True)


class AILTariffSensor(CoordinatorEntity, SensorEntity):
    """Sensore per una singola fascia tariffaria."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str, slot_key: str, config: dict):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._slot_key = slot_key
        self._config = config

        self._attr_unique_id = f"{DOMAIN}_{slot_key}"
        self._attr_name = config["name"]
        self._attr_icon = config["icon"]

        # Le tariffe sono prezzi istantanei (CHF/100kWh), non importi cumulati.
        # Non usare SensorDeviceClass.MONETARY perché richiede state_class total.
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = TARIFF_UNIT
        self._attr_suggested_display_precision = 2

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "fascia_oraria": self._config["time_slot"],
            "integration": DOMAIN,
        }

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._slot_key)
        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None


class AILTariffDateSensor(CoordinatorEntity, SensorEntity):
    """Mostra la data di validità delle tariffe."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_date"
        self._attr_name = "Data Tariffe AIL"
        self._attr_icon = "mdi:calendar"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("date")


class AILCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Indica la fascia oraria con tariffa più economica."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{DOMAIN}_cheapest_slot"
        self._attr_name = "Fascia AIL più economica"
        self._attr_icon = "mdi:star-check"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    def _tariff_data(self) -> dict[str, float]:
        """Estrae solo i valori tariffari numerici."""
        if not self.coordinator.data:
            return {}

        return {
            k: float(v)
            for k, v in self.coordinator.data.items()
            if isinstance(v, (int, float))
        }

    @property
    def native_value(self) -> str | None:
        tariff_data = self._tariff_data()
        if not tariff_data:
            return None

        cheapest = min(tariff_data, key=tariff_data.get)

        reverse_map = {v: k for k, v in TIME_SLOTS.items()}
        return reverse_map.get(cheapest, cheapest.capitalize())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        tariff_data = self._tariff_data()
        if not tariff_data:
            return {}

        cheapest = min(tariff_data, key=tariff_data.get)
        reverse_map = {v: k for k, v in TIME_SLOTS.items()}
        slot_name = reverse_map.get(cheapest, cheapest.capitalize())

        return {
            "fascia": slot_name,
            "prezzo": f"{tariff_data[cheapest]:.2f} {TARIFF_UNIT}",
            "orario": SENSOR_CONFIGS.get(cheapest, {}).get("time_slot"),
        }
