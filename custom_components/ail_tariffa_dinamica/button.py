"""Pulsante per forzare l'aggiornamento manuale."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AILForceUpdateButton(coordinator)])

class AILForceUpdateButton(ButtonEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._attr_unique_id = f"{DOMAIN}_force_update"
        self._attr_name = "Forza Aggiornamento AIL"
        self._attr_icon = "mdi:refresh"
        self._attr_device_class = None  # Pulsante generico

    async def async_press(self) -> None:
        """Quando premuto, triggera un refresh immediato."""
        await self.coordinator.async_request_refresh()
