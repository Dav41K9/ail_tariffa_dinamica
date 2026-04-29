"""Scraper diagnostico e robusto per le tariffe dinamiche AIL."""
import re
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
import aiohttp
from .const import TIME_SLOTS

_LOGGER = logging.getLogger(__name__)

class AILTariffScraper:
    URL = "https://www.ail.ch/aziende/elettricita/prodotti/Tariffa-dinamica/tariffa-dinamica.html"

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    async def fetch_tariffs(self, expected_date: date | None = None) -> dict:
        if expected_date is None:
            current = datetime.now()
            expected_date = current.date() if current.hour < 18 else current.date() + timedelta(days=1)

        _LOGGER.info("🔍 Fetching AIL tariffs for expected date: %s", expected_date)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-CH,it;q=0.9,en;q=0.8"
            }
            async with self.session.get(self.URL, headers=headers, timeout=30) as response:
                response.raise_for_status()
                html = await response.text()
        except Exception as e:
            _LOGGER.error("❌ Errore di rete: %s", e)
            raise ValueError(f"Errore di rete: {e}")

        # 💾 Salva HTML per debug manuale
        try:
            with open("/config/ail_debug.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception:
            pass

        return self._parse_html(html, expected_date)

    def _parse_html(self, html: str, expected_date: date) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Validazione data
        page_date_obj, date_str = self._extract_and_validate_date(soup, expected_date)
        _LOGGER.info("📅 Data pagina valida: %s", date_str)

        # Trova tabella
        table = None
        for tbl in soup.find_all('table'):
            if any(f in tbl.get_text() for f in ["Mattutina", "Solare", "Serale", "Notturna"]):
                table = tbl
                break
        if not table:
            raise ValueError("Tabella tariffe non trovata")

        results = {}
        fascia_keywords = ["Mattutina", "Solare", "Serale", "Notturna"]

        for row in table.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            fascia_text = cells[0].get_text(separator=' ', strip=True)
            fascia_name = next((kw for kw in fascia_keywords if kw in fascia_text), None)
            if not fascia_name:
                continue

            price_text = cells[-1].get_text(strip=True)
            
            # 🔧 PULIZIA AGGRESSIVA: rimuove NBSP, spazi, valute, simboli
            clean_price = price_text.replace('\xa0', '').replace('\u2009', '').replace(' ', '')
            clean_price = re.sub(r'[^\d.,]', '', clean_price)  # Tieni solo numeri, punti e virgole
            
            # 🔍 LOG DIAGNOSTICO: mostra esattamente cosa c'è nella stringa
            _LOGGER.debug("💰 Grezzo: %r | Pulito: %r", price_text, clean_price)

            # Regex blindata
            match = re.search(r'(\d+[.,]\d+)', clean_price)
            if not match:
                _LOGGER.warning("⚠️ Regex fallita per %s. Stringa pulita: '%s'", fascia_name, clean_price)
                continue

            # Conversione sicura
            try:
                value = float(match.group(1).replace(',', '.'))
                results[TIME_SLOTS[fascia_name]] = value
                _LOGGER.info("✓ Trovata %s: %.2f CHF/100kWh", fascia_name, value)
            except ValueError as e:
                _LOGGER.error("❌ Errore conversione float per %s: %s", fascia_name, e)
                continue

        if len(results) != 4:
            _LOGGER.error("❌ Trovate solo %d/4 fasce. Dati parziali: %s", len(results), results)
            raise ValueError(f"Trovate solo {len(results)}/4 fasce orarie")

        results["date"] = date_str
        return results

    def _extract_and_validate_date(self, soup: BeautifulSoup, expected_date: date) -> tuple[date, str]:
        months_map = {
            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
            'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
        }
        month_names = '|'.join(months_map.keys())
        date_pattern = re.compile(r'(\d{1,2})\s+(' + month_names + r')\s+(20\d{2})', re.IGNORECASE)

        for element in soup.find_all(string=True):
            text = str(element).strip()
            match = date_pattern.search(text)
            if match:
                day, month_it, year = match.groups()
                month = months_map.get(month_it.lower())
                if not month: continue
                page_date = date(int(year), month, int(day))
                if page_date != expected_date:
                    raise ValueError(f"⚠️ Data mismatch: pagina={page_date}, attesa={expected_date}")
                return page_date, f"{day} {month_it} {year}"
        raise ValueError("Impossibile trovare una data valida")
