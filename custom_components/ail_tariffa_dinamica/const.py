"""Costanti per l'integrazione AIL Tariffa Dinamica."""
from homeassistant.const import Platform

DOMAIN = "ail_tariffa_dinamica"
PLATFORMS = [Platform.SENSOR, Platform.BUTTON, Platform.BINARY_SENSOR]  # ← Aggiunto BINARY_SENSOR

# Configurazione sensori
SENSOR_CONFIGS = {
    "mattutina": {
        "name": "Tariffa Mattutina AIL",
        "icon": "mdi:weather-sunny",
        "time_slot": "06:00 - 10:00"
    },
    "solare": {
        "name": "Tariffa Solare AIL",
        "icon": "mdi:weather-partly-cloudy",
        "time_slot": "10:00 - 17:00"
    },
    "serale": {
        "name": "Tariffa Serale AIL",
        "icon": "mdi:weather-night-partly-cloudy",
        "time_slot": "17:00 - 21:00"
    },
    "notturna": {
        "name": "Tariffa Notturna AIL",
        "icon": "mdi:weather-night",
        "time_slot": "21:00 - 06:00"
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

# Mappatura nomi fascia → chiavi interne
TIME_SLOTS = {
    "Mattutina": "mattutina",
    "Solare": "solare",
    "Serale": "serale",
    "Notturna": "notturna"
}

# Informazioni dispositivo per il Device Registry
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
    "enabled": True  # Imposta False per disabilitare le notifiche
}
