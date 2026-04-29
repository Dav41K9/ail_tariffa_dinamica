# 🤝 Come contribuire

Grazie per voler contribuire a **AIL Tariffa Dinamica**! 🎉

## 🐞 Segnalare bug

1. Cerca tra le [issue esistenti](https://github.com/yourusername/ail-ha-integration/issues) per evitare duplicati
2. Usa il template "Bug Report" per descrivere il problema
3. Includi: versione HA, log rilevanti, passi per riprodurre

## 💡 Proporre nuove funzionalità

1. Apri una "Feature Request" descrivendo:
   - Cosa vorresti che facesse l'integrazione
   - Perché sarebbe utile
   - Eventuali idee di implementazione

2. Attendi feedback prima di iniziare a codificare

## 🔧 Sviluppare e testare

```bash
# Fork e clona la repo
git clone https://github.com/tuo-username/ail-ha-integration.git
cd ail-ha-integration

# Crea virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o: venv\Scripts\activate  # Windows

# Installa dipendenze
pip install -r requirements.txt

# Esegui test
pytest tests/ -v

# Formatta il codice prima del PR
black custom_components/ail_tariffa_dinamica/
isort custom_components/ail_tariffa_dinamica/
