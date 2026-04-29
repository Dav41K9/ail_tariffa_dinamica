"""Sensori per le tariffe AIL + data + fascia più economica."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENSOR_CONFIGS, TIME_SLOTS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Configura i sensori per AIL."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Sensori tariffe per ogni fascia
    entities = [
        AILTariffSensor(coordinator, slot_key, config)
        for slot_key, config in SENSOR_CONFIGS.items()
    ]
    
    # Sensori aggiuntivi
    entities.append(AILTariffDateSensor(coordinator))
    entities.append(AILCheapestSlotSensor(coordinator))
    
    async_add_entities(entities, update_before_add=True)


class AILTariffSensor(CoordinatorEntity, SensorEntity):
    """Sensore per una singola fascia tariffaria."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator, slot_key: str, config: dict):
        super().__init__(coordinator)
        self._slot_key = slot_key
        self._config = config
        
        self._attr_unique_id = f"{DOMAIN}_{slot_key}"
        self._attr_name = config["name"]
        self._attr_icon = config["icon"]
        self._attr_device_class = SensorDeviceClass.MONETARY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "CHF/100kWh"
        self._attr_extra_state_attributes = {
            "fascia_oraria": config["time_slot"],
            "integration": DOMAIN
        }

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._slot_key)


class AILTariffDateSensor(CoordinatorEntity, SensorEntity):
    """Mostra la data di validità delle tariffe."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_date"
        self._attr_name = "Data Tariffe AIL"
        self._attr_icon = "mdi:calendar"

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("date")


class AILCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Indica la fascia oraria con tariffa più economica."""
    
    _attr_has_entity_name = True

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_cheapest_slot"
        self._attr_name = "Fascia AIL più economica"
        self._attr_icon = "mdi:star-check"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None

        # Filtra solo le fasce orarie (esclude "date")
        tariff_data = {
            k: v for k, v in self.coordinator.data.items() 
            if isinstance(v, (int, float))
        }
        if not tariff_data:
            return None

        cheapest = min(tariff_data, key=tariff_data.get)
        
        # Mappa inversa per nome leggibile
        reverse_map = {v: k for k, v in TIME_SLOTS.items()}
        slot_name = reverse_map.get(cheapest, cheapest.capitalize())

        self._attr_extra_state_attributes = {
            "fascia": slot_name,
            "prezzo": f"{tariff_data[cheapest]:.2f} CHF/100kWh",
            "orario": SENSOR_CONFIGS[cheapest]["time_slot"]
        }
        return slot_name
