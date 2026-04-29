"""Binary sensor diagnostico per l'integrazione AIL Tariffa Dinamica."""
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory  # ← IMPORT NECESSARIO
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
    async_add_entities([entity], update_before_add=True)


class AILHealthSensor(CoordinatorEntity, BinarySensorEntity):
    """
    Binary sensor che indica lo stato di salute dell'integrazione.
    
    Con BinarySensorDeviceClass.PROBLEM:
    - is_on = False → ✅ Verde (nessun problema)
    - is_on = True  → ❌ Rosso (problema rilevato)
    """

    _attr_has_entity_name = True  # ← Importante per l'integrazione moderna

    def __init__(self, coordinator, entry: ConfigEntry):
        super().__init__(coordinator)
        self._entry_id = entry.entry_id
        config = DIAGNOSTIC_CONFIG["health"]

        self._attr_unique_id = f"{DOMAIN}_health_{entry.entry_id}"
        self._attr_name = config["name"]
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC  # ← ENUM, non stringa!
        self._attr_icon = config["icon_ok"]

    @property
    def device_info(self) -> DeviceInfo:
        """Collega il sensore al dispositivo AIL."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
        )

    @property
    def is_on(self) -> bool:
        """
        Restituisce True se c'è un problema, False se tutto OK.
        BinarySensor con device_class 'problem' inverte visualmente:
        - is_on=False → ✅ verde (OK)
        - is_on=True  → ❌ rosso (ERRORE)
        """
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
