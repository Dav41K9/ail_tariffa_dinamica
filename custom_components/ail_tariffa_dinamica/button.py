"""Pulsante per aggiornamento manuale delle tariffe AIL."""
import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, BUTTON_CONFIG, DEVICE_INFO

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Configura il pulsante di refresh per l'integrazione AIL."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entity = AILRefreshButton(coordinator, entry)
    async_add_entities([entity])


class AILRefreshButton(ButtonEntity):
    """Pulsante per forzare l'aggiornamento delle tariffe."""
    
    def __init__(self, coordinator, entry: ConfigEntry):
        self.coordinator = coordinator
        self._entry_id = entry.entry_id
        config = BUTTON_CONFIG["refresh"]
        
        self._attr_unique_id = f"{DOMAIN}_refresh_{entry.entry_id}"
        self._attr_name = config["name"]
        self._attr_icon = config["icon"]

    @property
    def device_info(self) -> DeviceInfo:
        """Collega il pulsante al dispositivo AIL."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=DEVICE_INFO["name"],
            manufacturer=DEVICE_INFO["manufacturer"],
            model=DEVICE_INFO["model"],
            sw_version=DEVICE_INFO["sw_version"],
            configuration_url=DEVICE_INFO["configuration_url"]
        )

    async def async_press(self) -> None:
        """Gestisce la pressione del pulsante: forza refresh."""
        _LOGGER.info("🔄 Aggiornamento manuale tariffe AIL richiesto")
        await self.coordinator.async_request_refresh()
