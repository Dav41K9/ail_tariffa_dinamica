"""Pulsante per aggiornamento manuale delle tariffe AIL."""
import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, BUTTON_CONFIG

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback
) -> None:
    """Configura il pulsante di refresh."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity = AILRefreshButton(coordinator, entry.entry_id)
    async_add_entities([entity], update_before_add=True)


class AILRefreshButton(CoordinatorEntity, ButtonEntity):
    """Pulsante per forzare l'aggiornamento delle tariffe."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        config = BUTTON_CONFIG["refresh"]
        
        self._attr_unique_id = f"{DOMAIN}_refresh_{entry_id}"
        self._attr_name = config["name"]
        self._attr_icon = config["icon"]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._entry_id)})

    async def async_press(self) -> None:
        """Gestisce la pressione del pulsante."""
        _LOGGER.info("Aggiornamento manuale tariffe AIL richiesto")
        await self.coordinator.async_request_refresh()
