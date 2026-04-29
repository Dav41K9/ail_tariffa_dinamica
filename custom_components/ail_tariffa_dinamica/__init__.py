"""AIL Tariffa Dinamica - Componente principale."""
import logging
from datetime import timedelta
import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, PLATFORMS, DEVICE_INFO
from .scraper import AILTariffScraper

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=6)  # Aggiornamento ogni 6 ore


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurazione dell'integrazione da config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Sessione HTTP condivisa
    if "session" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["session"] = aiohttp.ClientSession()
    
    session = hass.data[DOMAIN]["session"]
    scraper = AILTariffScraper(session)
    
    # Coordinatore per aggiornamenti periodici
    coordinator = AILDataUpdateCoordinator(hass, scraper)
    await coordinator.async_config_entry_first_refresh()
    
    # Registrazione nel Device Registry
    device_registry = hass.helpers.device_registry.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        manufacturer=DEVICE_INFO["manufacturer"],
        model=DEVICE_INFO["model"],
        name=DEVICE_INFO["name"],
        sw_version=DEVICE_INFO["sw_version"],
        configuration_url=DEVICE_INFO["configuration_url"]
    )
    
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup delle piattaforme (sensori)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Listener per aggiornamento config
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimozione dell'integrazione."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    # Chiudi sessione HTTP se non ci sono più entry
    if not hass.data[DOMAIN]:
        session = hass.data[DOMAIN].pop("session", None)
        if session:
            await session.close()
    
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload dell'integrazione al cambio config."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


class AILDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinatore per il polling periodico delle tariffe."""
    
    def __init__(self, hass: HomeAssistant, scraper: AILTariffScraper):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.scraper = scraper
    
    async def _async_update_data(self):
        """Metodo chiamato periodicamente per aggiornare i dati."""
        try:
            return await self.scraper.fetch_tariffs()
        except Exception as err:
            _LOGGER.error("Errore aggiornamento tariffe AIL: %s", err)
            raise UpdateFailed(f"Errore aggiornamento AIL: {err}")
