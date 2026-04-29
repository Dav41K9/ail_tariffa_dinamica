"""Binary sensor diagnostico per l'integrazione AIL Tariffa Dinamica."""
import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, DIAGNOSTIC_CONFIG, DEVICE_INFO

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Configura il binary sensor diagnostico per AIL."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entity = AILHealthSensor(coordinator, entry)
    async_add_entities([entity])


class AILHealthSensor(CoordinatorEntity, BinarySensorEntity):
    """
    Binary sensor che indica lo stato di salute dell'integrazione.
    
    is_on = True  → Tutto OK ✅
    is_on = False → C'è un errore ⚠️
    """
    
    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        config = DIAGNOSTIC_CONFIG["health"]
        
        self._attr_unique_id = f"{DOMAIN}_health_{entry.entry_id}"
        self._attr_name = config["name"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = "diagnostic"  ← Appare sotto "Diagnostic" nel dispositivo

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
    def is_on(self) -> bool:
        """
        Restituisce True se l'integrazione è sana, False se c'è un errore.
        Nota: BinarySensor con device_class 'problem' mostra:
        - ✅ verde quando is_on = False (nessun problema)
        - ❌ rosso quando is_on = True (problema rilevato)
        """
        # Invertiamo la logica: last_update_success=True → nessun problema → is_on=False
        return not self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Icona dinamica in base allo stato."""
        config = DIAGNOSTIC_CONFIG["health"]
        return config["icon_ok"] if not self.is_on else config["icon_error"]

    @property
    def extra_state_attributes(self) -> dict:
        """Attributi diagnostici dettagliati."""
        diag = self.coordinator.diagnostic_data
        return {
            "ultimo_aggiornamento_riuscito": diag["last_update_timestamp"],
            "prossimo_aggiornamento_previsto": diag["next_update"],
            "ultimo_errore": diag["last_error"],
            "conteggio_errori_consecutivi": diag["error_count"],
            "url_monitorato": diag["url"],
            "integrazione": DOMAIN,
            "versione": DEVICE_INFO["sw_version"]
        }
