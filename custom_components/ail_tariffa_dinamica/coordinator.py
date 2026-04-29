"""Coordinator per aggiornamento tariffe con scheduling serale + refresh manuale."""
from datetime import datetime, timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.dt import now as ha_now
from homeassistant.helpers.event import async_call_later
import aiohttp
from .scraper import AILTariffScraper
from .const import DOMAIN, UPDATE_TIME

_LOGGER = logging.getLogger(__name__)

class AILTariffCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._session = None
        self._unsub_timer = None
        # update_interval=None perché gestiamo manualmente il timer giornaliero
        super().__init__(hass, _LOGGER, name="AIL Tariffa Dinamica", update_interval=None)
        
    async def async_setup(self):
        self._session = aiohttp.ClientSession()
        self.scraper = AILTariffScraper(self._session)
        # Primo refresh immediato per popolare i sensori all'installazione
        await self.async_refresh()
        # Poi programma il prossimo aggiornamento automatico alle 18:15
        self._schedule_next_update()
        
    def _schedule_next_update(self):
        """Programma il prossimo aggiornamento automatico alle 18:15."""
        current = ha_now()
        target_today = datetime(current.year, current.month, current.day, UPDATE_TIME[0], UPDATE_TIME[1], tzinfo=current.tzinfo)
        
        if current >= target_today:
            target_today += timedelta(days=1)
            
        delay = (target_today - current).total_seconds()
        _LOGGER.info("📅 Prossimo aggiornamento automatico programmato tra %.1f minuti (%s)", delay/60, target_today)
        
        if self._unsub_timer:
            self._unsub_timer()
        self._unsub_timer = async_call_later(self.hass, delay, self._async_trigger_update)

    async def _async_trigger_update(self, _hass=None):
        """Callback del timer: aggiorna e riprogramma per il giorno successivo."""
        _LOGGER.info("⏰ Trigger automatico aggiornamento tariffe AIL")
        await self.async_refresh()
        self._schedule_next_update()  # Riprogramma per domani alle 18:15
        
    async def _async_update_data(self) -> dict:
        try:
            current = ha_now()
            
            # ✅ LOGICA CORRETTA:
            # Prima delle 18:00 → la pagina mostra le tariffe di OGGI
            # Dopo le 18:00 → la pagina mostra le tariffe di DOMANI
            if current.hour < 18:
                expected_date = current.date()
            else:
                expected_date = current.date() + timedelta(days=1)
                
            _LOGGER.debug("Fetching tariffs: current=%s, expected_date_on_page=%s", current, expected_date)
            
            data = await self.scraper.fetch_tariffs(expected_date)
            _LOGGER.info("✅ Tariffe aggiornate con successo per %s", data.get("date"))
            return data
            
        except ValueError as e:
            _LOGGER.warning("⚠️ Validazione fallita: %s", e)
            await self._send_notification(f"⚠️ AIL: aggiornamento fallito\n{e}", warning=True)
            raise UpdateFailed(str(e)) from e
        except Exception as e:
            _LOGGER.error("❌ Errore imprevisto: %s", e, exc_info=True)
            await self._send_notification(f"❌ AIL: errore imprevisto\n{type(e).__name__}: {e}", error=True)
            raise UpdateFailed(f"Errore imprevisto: {e}") from e
    
    async def _send_notification(self, message: str, warning: bool = False, error: bool = False):
        try:
            title = "AIL Tariffa Dinamica"
            if error: title = f"❌ {title}"
            elif warning: title = f"⚠️ {title}"
            await self.hass.services.async_call(
                "persistent_notification", "create",
                {"title": title, "message": message, "notification_id": f"{DOMAIN}_update_alert"}
            )
        except Exception as e:
            _LOGGER.debug("Impossibile inviare notifica: %s", e)
    
    async def async_close(self):
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None
        if self._session and not self._session.closed:
            await self._session.close()
