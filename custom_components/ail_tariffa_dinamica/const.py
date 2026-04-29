"""Costanti per l'integrazione AIL Tariffa Dinamica."""
DOMAIN = "ail_tariffa_dinamica"
UPDATE_TIME = (18, 15)  # Ora di aggiornamento: 18:15

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