"""Costanti per l'integrazione AIL Tariffa Dinamica."""
from homeassistant.const import Platform, EntityCategory

DOMAIN = "ail_tariffa_dinamica"

# ⚠️ CRITICO: Usa Platform ENUM, non stringhe!
PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.BINARY_SENSOR]

# Ora di aggiornamento preferita
UPDATE_TIME = (18, 15)

# Mappatura fasce orarie
TIME_SLOTS = {
    "Mattutina": "mattutina",
    "Solare": "solare", 
    "Serale": "serale",
    "Notturna": "notturna"
}

# Configurazione sensori
SENSOR_CONFIGS = {
    "mattutina": {
        "name": "Tariffa Mattutina AIL",
        "time_slot": "06:00-10:00",
        "icon": "mdi:weather-sunny"
    },
    "solare": {
        "name": "Tariffa Solare AIL",
        "time_slot": "10:00-17:00", 
        "icon": "mdi:solar-power"
    },
    "serale": {
        "name": "Tariffa Serale AIL",
        "time_slot": "17:00-22:00",
        "icon": "mdi:weather-night"
    },
    "notturna": {
        "name": "Tariffa Notturna AIL",
        "time_slot": "22:00-06:00",
        "icon": "mdi:moon-waning-crescent"
    }
}

# Configurazione pulsante
BUTTON_CONFIG = {
    "refresh": {
        "name": "Aggiorna tariffe AIL",
        "icon": "mdi:refresh"
    }
}

# Configurazione diagnostica
DIAGNOSTIC_CONFIG = {
    "health": {
        "name": "Stato integrazione AIL",
        "icon_ok": "mdi:check-circle",
        "icon_error": "mdi:alert-circle"
    }
}

# Informazioni dispositivo - CRITICO: identifiers devono coincidere ovunque
DEVICE_INFO = {
    "manufacturer": "AIL (Aziende Industriali di Lugano)",
    "model": "Tariffa Dinamica",
    "name": "AIL Tariffa Dinamica",
    "sw_version": "1.1.0",
    "configuration_url": "https://www.ail.ch/aziende/elettricita/prodotti/Tariffa-dinamica/tariffa-dinamica.html"
}

# Configurazione notifiche
NOTIFICATION_CONFIG = {
    "title": "⚠️ AIL Tariffa Dinamica - Avviso",
    "enabled": True
}
