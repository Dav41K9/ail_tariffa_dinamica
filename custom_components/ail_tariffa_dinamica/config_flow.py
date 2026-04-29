"""Config Flow per configurazione UI."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import DOMAIN

class AILTariffConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id("ail_tariffa_dinamica_main")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="AIL Tariffa Dinamica", data={})
            
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={
                "info": "📊 Lettura tariffe AIL ogni giorno alle 18:15.\n\n"
                       "✅ 4 sensori fasce orarie + 1 sensore Data + 1 sensore Fascia più economica\n"
                       "🔘 Pulsante 'Forza Aggiornamento' per refresh manuale\n"
                       "🔒 Validazione data automatica. Notifiche in caso di errore."
            }
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return AILTariffOptionsFlow()


class AILTariffOptionsFlow(config_entries.OptionsFlow):
    # Rimosso __init__ per compatibilità HA 2024+
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({}),
            description_placeholders={"note": "Opzioni avanzate in arrivo! 🚀"}
        )
