# ⚡ AIL Tariffa Dinamica per Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![License](https://img.shields.io/github/license/yourusername/ail-ha-integration)](LICENSE)

Integrazione personalizzata per Home Assistant che legge le **tariffe elettriche dinamiche giornaliere** di [AIL (Aziende Industriali di Lugano)](https://www.ail.ch) e le rende disponibili come sensori per automazioni intelligenti.

> 🇨🇭 Specifico per clienti AIL in Ticino, Svizzera

---

## ✨ Funzionalità

- 📊 **4 sensori** per le fasce orarie: Mattutina (06-10), Solare (10-17), Serale (17-22), Notturna (22-06)
- 💡 **Sensore bonus**: "Fascia più economica" per automazioni ottimizzate
- 🔒 **Validazione data**: controllo automatico che i dati siano per il giorno corretto
- ⏰ **Aggiornamento automatico**: ogni giorno alle 18:15 (quando AIL pubblica le nuove tariffe)
- 🔔 **Notifiche di errore**: avviso in UI se l'aggiornamento fallisce
- 🎨 **Configurazione via UI**: nessun YAML richiesto
- 🇮🇹 **Localizzazione italiana**: nomi e descrizioni in italiano

---

## 🚀 Installazione

### Metodo 1: HACS (Consigliato)

1. Apri **HACS** → **Integrazioni**
2. Clicca sui 3 puntini in alto a destra → **Repository personalizzati**
3. Aggiungi:
   - Repository: `https://github.com/yourusername/ail-ha-integration`
   - Categoria: `Integration`
4. Clicca **Aggiungi**, poi cerca "AIL Tariffa Dinamica" e installa
5. **Riavvia Home Assistant**

### Metodo 2: Installazione manuale
---
```bash
# Copia la cartella nel tuo config di Home Assistant:
config/custom_components/ail_tariffa_dinamica/
```

---

⚠️ Disclaimer: Questa integrazione non è affiliata, sponsorizzata o approvata da AIL SA. L'uso è a proprio rischio. Le tariffe sono pubblicate da AIL e potrebbero cambiare formato senza preavviso.
