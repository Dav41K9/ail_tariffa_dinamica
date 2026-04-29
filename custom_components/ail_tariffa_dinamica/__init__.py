"""Inizializzazione integrazione AIL Tariffa Dinamica."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import AILTariffCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup da config entry (UI)."""
    _LOGGER.info("🔌 Setup integrazione AIL Tariffa Dinamica")
    
    coordinator = AILTariffCoordinator(hass)
    await coordinator.async_setup()
    
    # Forza primo aggiornamento immediato (utile al setup)
    await coordinator.async_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listener per rimozione integrazione
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    
    return True

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Gestisce aggiornamento opzioni (future)."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload integrazione."""
    coordinator: AILTariffCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_close()
    
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        
    return unloaded