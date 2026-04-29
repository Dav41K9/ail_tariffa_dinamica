"""Scraper per le tariffe dinamiche AIL con validazione data."""
import re
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
import aiohttp

_LOGGER = logging.getLogger(__name__)

class AILTariffScraper:
    URL = "https://www.ail.ch/aziende/elettricita/prodotti/Tariffa-dinamica/tariffa-dinamica.html"
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        
    async def fetch_tariffs(self, expected_date: date | None = None) -> dict:
        if expected_date is None:
            current = datetime.now()
            expected_date = current.date() if current.hour < 18 else current.date() + timedelta(days=1)
            
        _LOGGER.debug("Fetching AIL tariffs, expected date on page: %s", expected_date)
        
        try:
            async with self.session.get(self.URL, timeout=30) as response:
                response.raise_for_status()
                html = await response.text()
        except aiohttp.ClientError as e:
            raise ValueError(f"Errore di rete: {e}")
        except TimeoutError:
            raise ValueError("Timeout download pagina AIL")
            
        return self._parse_html(html, expected_date)
    
    def _parse_html(self, html: str, expected_date: date) -> dict:
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1️⃣ Estrai e valida data
        page_date_obj, date_str = self._extract_and_validate_date(soup, expected_date)
        _LOGGER.info("Data pagina validata: %s", date_str)
        
        # 2️⃣ Trova la tabella delle tariffe
        table = None
        for tbl in soup.find_all('table'):
            # Cerca una tabella che contiene una delle fasce orarie
            if any(fascia in tbl.get_text() for fascia in ["Mattutina", "Solare", "Serale", "Notturna"]):
                table = tbl
                break
                
        if not table:
            raise ValueError("Tabella tariffe non trovata")
        
        # 3️⃣ Estrai le righe (salta l'header)
        rows = []
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            all_rows = table.find_all('tr')
            # Salta la prima riga se contiene "Fascia" o "Utilizzo"
            rows = [r for r in all_rows if 'Fascia' not in r.get_text() and 'Utilizzo' not in r.get_text()]
        
        results = {}
        fascia_keywords = ["Mattutina", "Solare", "Serale", "Notturna"]
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:  # Almeno fascia + prezzo
                continue
                
            # Estrai il nome della fascia dalla prima cella (gestisci <strong>, <b>, ecc.)
            first_cell = cells[0]
            # get_text(strip=True) rimuove tutti i tag e whitespace extra
            fascia_text = first_cell.get_text(separator=' ', strip=True)
            
            # Cerca quale fascia è presente nel testo
            fascia_name = None
            for kw in fascia_keywords:
                if kw in fascia_text:
                    fascia_name = kw
                    break
                    
            if not fascia_name:
                continue  # Salta righe non pertinenti
                
            # Estrai il prezzo dall'ULTIMA cella (colonna "Totale")
            last_cell = cells[-1]
            price_text = last_cell.get_text(strip=True)
            
            # Cerca un numero con formato italiano: 27,49
            match = re.search(r'(\d+,\d+)', price_text)
            if not match:
                _LOGGER.warning("Nessun prezzo valido trovato per %s in: '%s'", fascia_name, price_text)
                continue
                
            # Converti "27,49" → 27.49 (float)
            value = float(match.group(1).replace(',', '.'))
            
            from .const import TIME_SLOTS
            results[TIME_SLOTS[fascia_name]] = value
            _LOGGER.debug("✓ Trovata %s: %.2f CHF/100kWh", fascia_name, value)
            
        if len(results) != 4:
            raise ValueError(f"Trovate solo {len(results)}/4 fasce orarie. Dettagli: {list(results.keys())}")
            
        results["date"] = date_str
        return results
    
    def _extract_and_validate_date(self, soup: BeautifulSoup, expected_date: date) -> tuple[date, str]:
        months_map = {
            'gennaio': 1, 'febbraio': 2, 'marzo': 3, 'aprile': 4, 'maggio': 5, 'giugno': 6,
            'luglio': 7, 'agosto': 8, 'settembre': 9, 'ottobre': 10, 'novembre': 11, 'dicembre': 12
        }
        month_names = '|'.join(months_map.keys())
        # Pattern flessibile: "29 aprile 2026" con possibili spazi/tag attorno
        date_pattern = re.compile(r'(\d{1,2})\s+(' + month_names + r')\s+(20\d{2})', re.IGNORECASE)
        
        # Cerca in tutti gli elementi di testo della pagina
        for element in soup.find_all(string=True):
            text = str(element).strip()
            match = date_pattern.search(text)
            if match:
                day, month_it, year = match.groups()
                month = months_map.get(month_it.lower())
                if not month:
                    continue
                page_date = date(int(year), month, int(day))
                
                if page_date != expected_date:
                    raise ValueError(
                        f"⚠️ Data mismatch: pagina={page_date}, attesa={expected_date}. "
                        f"Prima delle 18:00 la pagina mostra le tariffe di oggi; dopo le 18:00 quelle di domani."
                    )
                return page_date, f"{day} {month_it} {year}"  # Formato leggibile
                
        raise ValueError("Impossibile trovare una data valida nella pagina AIL")
