"""AIL Tariffa Dinamica - Componente principale con diagnostica e notifiche."""
import logging
from datetime import timedelta
import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, PLATFORMS, DEVICE_INFO, NOTIFICATION_CONFIG
from .scraper import AILTariffScraper

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(hours=6)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configurazione dell'integrazione da config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Sessione HTTP condivisa
    if "session" not in hass.data[DOMAIN]:
        hass.data[DOMAIN]["session"] = aiohttp.ClientSession()

    session = hass.data[DOMAIN]["session"]
    scraper = AILTariffScraper(session)

    # Coordinatore con supporto notifiche
    coordinator = AILDataUpdateCoordinator(hass, scraper, entry)
    await coordinator.async_config_entry_first_refresh()

    # Registrazione nel Device Registry ← CORRETTO
    device_registry = dr.async_get(hass)
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

    # Setup piattaforme: sensor, button, binary_sensor
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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
    """Coordinatore con tracciamento errori e notifiche."""

    def __init__(self, hass: HomeAssistant, scraper, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.scraper = scraper
        self._entry = entry
        self._last_error = None
        self._error_count = 0
        self._notified = False

    @property
    def diagnostic_data(self) -> dict:
        """Restituisce dati diagnostici per il binary sensor."""
        return {
            "last_update_success": self.last_update_success,
            "last_update_timestamp": self.last_update_success_timestamp.isoformat() if self.last_update_success_timestamp else None,
            "last_error": self._last_error,
            "error_count": self._error_count,
            "url": self.scraper.URL,
            "next_update": (self.last_update_success_timestamp + UPDATE_INTERVAL).isoformat() if self.last_update_success_timestamp else None
        }

    async def _async_update_data(self):
        """Metodo chiamato periodicamente per aggiornare i dati con gestione errori."""
        try:
            result = await self.scraper.fetch_tariffs()

            # Reset errori in caso di successo
            if self._last_error:
                _LOGGER.info("✅ Integrazione AIL ripristinata dopo errore: %s", self._last_error)
                self._last_error = None
                self._error_count = 0
                self._notified = False

            return result

        except Exception as err:
            error_msg = str(err)
            self._last_error = error_msg
            self._error_count += 1

            _LOGGER.error("❌ Errore aggiornamento AIL (tentativo #%d): %s", self._error_count, error_msg)

            # Notifica solo al primo errore (anti-spam)
            if NOTIFICATION_CONFIG["enabled"] and not self._notified:
                await self._send_error_notification(error_msg)
                self._notified = True

            raise UpdateFailed(f"Errore aggiornamento AIL: {error_msg}")

    async def _send_error_notification(self, error_msg: str):
        """Invia notifica Home Assistant quando si verifica un errore."""
        if "rete" in error_msg.lower() or "timeout" in error_msg.lower():
            suggestion = "Verifica la connessione internet o se il sito AIL è raggiungibile."
        elif "data" in error_msg.lower() or "mismatch" in error_msg.lower():
            suggestion = "La data sulla pagina AIL non corrisponde. Potrebbero aver cambiato formato."
        elif "tabella" in error_msg.lower() or "parsing" in error_msg.lower():
            suggestion = "La struttura HTML della pagina AIL potrebbe essere cambiata. Controlla il sito."
        elif "4 fasce" in error_msg.lower():
            suggestion = "Non tutte le fasce orarie sono state trovate. Verifica la tabella sul sito AIL."
        else:
            suggestion = "Controlla i log di Home Assistant per dettagli tecnici."

        message = (
            f"🔌 **Errore integrazione AIL Tariffa Dinamica**\n\n"
            f"❌ `{error_msg}`\n\n"
            f"🔧 {suggestion}\n\n"
            f"📦 Dispositivo: {DEVICE_INFO['name']}\n"
            f"🌐 URL: `{self.scraper.URL}`\n\n"
            f"_Questa notifica non si ripeterà finché l'errore persiste._"
        )

        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": NOTIFICATION_CONFIG["title"],
                "message": message,
                "notification_id": f"{DOMAIN}_error_{self._entry.entry_id}"
            }
        )
