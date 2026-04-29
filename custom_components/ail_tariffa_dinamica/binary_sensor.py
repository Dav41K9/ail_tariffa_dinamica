"""Binary sensor diagnostico per l'integrazione AIL Tariffa Dinamica."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    
    # CRITICO: update_before_add=True forza il primo update prima di registrare
    async_add_entities([entity], update_before_add=True)
    _LOGGER.info("✓ Binary sensor diagnostico registrato: %s", entity.unique_id)


class AILHealthSensor(CoordinatorEntity, BinarySensorEntity):
    """
    Binary sensor che indica lo stato di salute dell'integrazione.
    
    Con BinarySensorDeviceClass.PROBLEM:
    - is_on = False → ✅ Verde (nessun problema, tutto OK)
    - is_on = True  → ❌ Rosso (problema rilevato)
    """
    
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        config = DIAGNOSTIC_CONFIG["health"]

        self._attr_unique_id = f"{DOMAIN}_health_{entry.entry_id}"
        self._attr_name = config["name"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = config["icon_ok"]
        
        _LOGGER.debug("AILHealthSensor inizializzato: %s", self._attr_unique_id)

    @property
    def device_info(self) -> DeviceInfo:
        """Collega il sensore al dispositivo AIL."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    @property
    def available(self) -> bool:  # ← CRITICO: gestisce lo stato "unavailable"
        """
        Restituisce True solo se il coordinatore ha dati validi.
        Previene lo stato 'unavailable' quando l'integrazione non è ancora pronta.
        """
        return (
            self.coordinator is not None 
            and hasattr(self.coordinator, 'data') 
            and self.coordinator.data is not None
        )

    @property
    def is_on(self) -> bool | None:
        """
        Restituisce True se c'è un problema, False se tutto OK.
        Restituisce None se i dati non sono ancora disponibili.
        """
        if not self.available:
            return None
            
        # last_update_success è gestito dal DataUpdateCoordinator base
        return not self.coordinator.last_update_success

    @property
    def icon(self) -> str:
        """Icona dinamica in base allo stato."""
        config = DIAGNOSTIC_CONFIG["health"]
        # Se non disponibile, mostra icona grigia
        if not self.available:
            return "mdi:help-circle"
        return config["icon_ok"] if not self.is_on else config["icon_error"]

    @property
    def extra_state_attributes(self) -> dict | None:
        """Attributi diagnostici dettagliati."""
        if not self.available or not hasattr(self.coordinator, 'diagnostic_data'):
            return None
            
        try:
            diag = self.coordinator.diagnostic_data
            return {
                "ultimo_aggiornamento_riuscito": diag.get("last_update_timestamp"),
                "prossimo_aggiornamento_previsto": diag.get("next_update"),
                "ultimo_errore": diag.get("last_error"),
                "conteggio_errori_consecutivi": diag.get("error_count", 0),
                "url_monitorato": diag.get("url"),
                "integrazione": DOMAIN,
                "versione": DEVICE_INFO["sw_version"]
            }
        except Exception as err:
            _LOGGER.warning("Errore nel recupero attributi diagnostici: %s", err)
            return None
