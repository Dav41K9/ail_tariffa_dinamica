"""Sensori per le tariffe AIL + data + fascia più economica."""
import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, SENSOR_CONFIGS, TIME_SLOTS, DEVICE_INFO

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Configura i sensori per l'integrazione AIL."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        AILTariffSensor(coordinator, entry, slot_key, config)
        for slot_key, config in SENSOR_CONFIGS.items()
    ]
    entities.append(AILTariffDateSensor(coordinator, entry))
    entities.append(AILCheapestSlotSensor(coordinator, entry))
    
    async_add_entities(entities)


class AILTariffSensor(CoordinatorEntity, SensorEntity):
    """Sensore per una singola fascia oraria AIL."""
    
    def __init__(self, coordinator, entry: ConfigEntry, slot_key: str, config: dict):
        super().__init__(coordinator)
        self._slot_key = slot_key
        self._config = config
        self._entry_id = entry.entry_id
        
        self._attr_unique_id = f"{DOMAIN}_{slot_key}_{entry.entry_id}"
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
    def device_info(self) -> DeviceInfo:
        """Collega il sensore al dispositivo AIL."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=DEVICE_INFO["name"],
            manufacturer=DEVICE_INFO["manufacturer"],
            model=DEVICE_INFO["model"],
            sw_version=DEVICE_INFO["sw_version"],
            configuration_url=DEVICE_INFO["configuration_url"]
        )

    @property
    def native_value(self) -> float | None:
        """Restituisce il valore della tariffa."""
        # ✅ FIX 1: aggiunto ".data"
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._slot_key)


class AILTariffDateSensor(CoordinatorEntity, SensorEntity):
    """Mostra la data di validità delle tariffe."""
    
    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        
        self._attr_unique_id = f"{DOMAIN}_date_{entry.entry_id}"
        self._attr_name = "Data Tariffe AIL"
        self._attr_icon = "mdi:calendar"

    @property
    def device_info(self) -> DeviceInfo:
        """Collega il sensore al dispositivo AIL."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=DEVICE_INFO["name"],
            manufacturer=DEVICE_INFO["manufacturer"],
            model=DEVICE_INFO["model"],
            sw_version=DEVICE_INFO["sw_version"],
            configuration_url=DEVICE_INFO["configuration_url"]
        )

    @property
    def native_value(self) -> str | None:
        """Restituisce la data delle tariffe."""
        # ✅ FIX 2: aggiunto ".data"
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("date")


class AILCheapestSlotSensor(CoordinatorEntity, SensorEntity):
    """Sensore che indica la fascia oraria più economica."""
    
    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        
        self._attr_unique_id = f"{DOMAIN}_cheapest_slot_{entry.entry_id}"
        self._attr_name = "Fascia AIL più economica"
        self._attr_icon = "mdi:star-check"
        self._attr_extra_state_attributes = {}

    @property
    def device_info(self) -> DeviceInfo:
        """Collega il sensore al dispositivo AIL."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=DEVICE_INFO["name"],
            manufacturer=DEVICE_INFO["manufacturer"],
            model=DEVICE_INFO["model"],
            sw_version=DEVICE_INFO["sw_version"],
            configuration_url=DEVICE_INFO["configuration_url"]
        )

    @property
    def native_value(self) -> str | None:
        """Restituisce il nome della fascia con tariffa minima."""
        # ✅ FIX 3: aggiunto ".data"
        if not self.coordinator.data:
            return None

        tariff_data = {
            k: v for k, v in self.coordinator.data.items() 
            if isinstance(v, (int, float))
        }
        
        # ✅ FIX 4: completato "tariff_data"
        if not tariff_data:
            return None

        cheapest = min(tariff_data, key=tariff_data.get)
        reverse_map = {v: k for k, v in TIME_SLOTS.items()}
        slot_name = reverse_map.get(cheapest, cheapest.capitalize())

        self._attr_extra_state_attributes = {
            "fascia": slot_name,
            "prezzo": f"{tariff_data[cheapest]:.2f} CHF/100kWh",
            "orario": SENSOR_CONFIGS[cheapest]["time_slot"]
        }
        
        return slot_name
