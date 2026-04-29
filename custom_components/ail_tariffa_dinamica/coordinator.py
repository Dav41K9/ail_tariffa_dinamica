"""Coordinator per aggiornamento tariffe con scheduling serale."""
from datetime import datetime, timedelta
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util.dt import now as ha_now
import aiohttp
from .scraper import AILTariffScraper
from .const import DOMAIN, UPDATE_TIME

_LOGGER = logging.getLogger(__name__)

class AILTariffCoordinator(DataUpdateCoordinator[dict[str, float]]):
    """Coordinator con aggiornamento giornaliero alle 18:15 e notifiche su errore."""
    
    def __init__(self, hass: HomeAssistant):
        self.hass = hass
        self._session = None
        super().__init__(
            hass,
            _LOGGER,
            name="AIL Tariffa Dinamica",
            update_interval=timedelta(hours=24),
        )
        
    async def async_setup(self):
        """Setup iniziale: crea sessione e programma primo aggiornamento."""
        self._session = aiohttp.ClientSession()
        self.scraper = AILTariffScraper(self._session)
        self._schedule_next_update()
        
    async def _async_update_data(self) -> dict[str, float]:
        """Esegui scraping con gestione errori e notifiche."""
        try:
            # Data attesa: domani se siamo prima delle 18, oggi se dopo
            current = ha_now()
            expected_date = current.date() + timedelta(days=1) if current.hour < 18 else current.date()
            
            data = await self.scraper.fetch_tariffs(expected_date)
            _LOGGER.info("✅ Tariffe aggiornate con successo per %s", expected_date)
            return data
            
        except ValueError as e:
            _LOGGER.warning("⚠️ Validazione fallita: %s", e)
            # Notifica se configurato
            await self._send_notification(f"⚠️ AIL: aggiornamento fallito\n{e}", warning=True)
            raise UpdateFailed(str(e)) from e
            
        except Exception as e:
            _LOGGER.error("❌ Errore imprevisto: %s", e, exc_info=True)
            await self._send_notification(f"❌ AIL: errore imprevisto\n{type(e).__name__}: {e}", error=True)
            raise UpdateFailed(f"Errore imprevisto: {e}") from e
    
    def _schedule_next_update(self):
        """Programma il prossimo aggiornamento alle 18:15."""
        current = ha_now()
        target_today = current.replace(hour=UPDATE_TIME[0], minute=UPDATE_TIME[1], second=0, microsecond=0)
        
        next_update = target_today if current < target_today else target_today + timedelta(days=1)
        self._set_next_refresh(next_update)
        _LOGGER.info("📅 Prossimo aggiornamento programmato per: %s", next_update)
    
    async def _send_notification(self, message: str, warning: bool = False, error: bool = False):
        """Invia notifica se il servizio persistent_notification è disponibile."""
        try:
            title = "AIL Tariffa Dinamica"
            if error:
                title = f"❌ {title}"
            elif warning:
                title = f"⚠️ {title}"
                
            await self.hass.services.async_call(
                "persistent_notification", "create",
                {"title": title, "message": message, "notification_id": f"{DOMAIN}_update_alert"}
            )
        except Exception as e:
            _LOGGER.debug("Impossibile inviare notifica: %s", e)
    
    async def async_close(self):
        """Chiudi la sessione HTTP quando l'integrazione viene rimossa."""
        if self._session and not self._session.closed:
            await self._session.close()