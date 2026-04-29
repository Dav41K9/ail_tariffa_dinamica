"""Sensori per le tariffe AIL + sensore fascia più economica."""
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, SENSOR_CONFIGS

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensori da config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # 4 sensori per fasce orarie
    entities = [
        AILTariffSensor(coordinator, slot_key, config)
        for slot_key, config in SENSOR_CONFIGS.items()
    ]
    
    # +1 sensore: fascia più economica del giorno
    entities.append(AILCheapestSlotSensor(coordinator))
    
    async_add_entities(entities)


class AILTariffSensor(CoordinatorEntity, SensorEntity):
    """Sensore per una fascia oraria specifica."""
    
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
        """Restituisce il valore della tariffa."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self._slot_key)


class AILCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensore che indica la fascia oraria più economica del giorno."""
    
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_cheapest_slot"
        self._attr_name = "Fascia AIL più economica"
        self._attr_icon = "mdi:star-check"
        self._attr_extra_state_attributes = {}
        
    @property
    def native_value(self) -> str | None:
        """Restituisce il nome della fascia più economica."""
        if not self.coordinator.data:
            return None
            
        data = self.coordinator.data
        if not data:
            return None
            
        # Trova la chiave con valore minimo
        cheapest = min(data, key=data.get)
        
        # Mappa inversa per nome leggibile
        from .const import TIME_SLOTS
        reverse_map = {v: k for k, v in TIME_SLOTS.items()}
        slot_name = reverse_map.get(cheapest, cheapest.capitalize())
        
        # Aggiorna attributi
        self._attr_extra_state_attributes = {
            "fascia": slot_name,
            "prezzo": f"{data[cheapest]:.2f} CHF/100kWh",
            "orario": SENSOR_CONFIGS[cheapest]["time_slot"]
        }
        
        return slot_name
