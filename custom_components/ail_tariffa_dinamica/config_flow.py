"""Config Flow per configurazione UI con validazioni."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

class AILTariffConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gestisce la configurazione via UI."""
    
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    
    async def async_step_user(self, user_input=None):
        """Step iniziale: conferma configurazione."""
        if user_input is not None:
            # Unica istanza per dominio
            await self.async_set_unique_id("ail_tariffa_dinamica_main")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="AIL Tariffa Dinamica", data={})
            
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "info": "📊 Questa integrazione leggerà automaticamente le tariffe dinamiche AIL ogni giorno alle 18:15.\n\n"
                       "✅ Verranno creati 5 sensori:\n"
                       "• 4 sensori per le fasce orarie (Mattutina, Solare, Serale, Notturna)\n"
                       "• 1 sensore 'Fascia più economica' per automazioni intelligenti\n\n"
                       "🔒 La data sulla pagina viene validata: se i dati non sono aggiornati, "
                       "riceverai una notifica e i sensori manterranno l'ultimo valore valido."
            }
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AILTariffOptionsFlow(config_entry)


class AILTariffOptionsFlow(config_entries.OptionsFlow):
    """Gestione opzioni avanzate (future)."""
    def __init__(self, config_entry):
        self.config_entry = config_entry
        
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
            
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                # Placeholder per future opzioni: orario personalizzato, notifiche, ecc.
            }),
            description_placeholders={"note": "Opzioni avanzate in arrivo nella prossima versione! 🚀"}
        )