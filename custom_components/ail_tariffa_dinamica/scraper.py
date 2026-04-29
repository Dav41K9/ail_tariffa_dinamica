"""Scraper per le tariffe dinamiche AIL con validazione data."""
import re
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
import aiohttp

# Import spostato in cima per evitare problemi di caricamento
from .const import TIME_SLOTS

_LOGGER = logging.getLogger(__name__)


class AILTariffScraper:
    """Classe responsabile dello scraping delle tariffe AIL."""
    
    URL = "https://www.ail.ch/aziende/elettricita/prodotti/Tariffa-dinamica/tariffa-dinamica.html"

    def __init__(self, session: aiohttp.ClientSession):
        """Inizializza lo scraper con una sessione HTTP."""
        self.session = session

    async def fetch_tariffs(self, expected_date: date | None = None) -> dict:
        """
        Scarica e parsifica le tariffe dalla pagina AIL.
        
        Args:
            expected_date: Data attesa per la validazione (default: oggi/domani in base all'ora)
            
        Returns:
            dict con le tariffe per fascia + data di validità
        """
        if expected_date is None:
            current = datetime.now()
            # Se sono dopo le 18:00, le tariffe mostrate sono per il giorno dopo
            expected_date = current.date() if current.hour < 18 else current.date() + timedelta(days=1)

        _LOGGER.debug("Fetching AIL tariffs, expected date on page: %s", expected_date)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "it-CH,it;q=0.9,en;q=0.8"
            }
            async with self.session.get(self.URL, headers=headers, timeout=30) as response:
                response.raise_for_status()
                html = await response.text(encoding='utf-8')  # Encoding esplicito
        except aiohttp.ClientError as e:
            raise ValueError(f"Errore di rete: {e}")
        except TimeoutError:
            raise ValueError("Timeout download pagina AIL")
        except Exception as e:
            raise ValueError(f"Errore imprevisto durante il download: {e}")

        return self._parse_html(html, expected_date)

    def _parse_html(self, html: str, expected_date: date) -> dict:
        """Parsifica l'HTML estratto e valida i dati."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Estrai e valida la data
        page_date_obj, date_str = self._extract_and_validate_date(soup, expected_date)
        _LOGGER.info("✓ Data pagina validata: %s", date_str)

        # Cerca la tabella delle tariffe
        table = None
        for tbl in soup.find_all('table'):
            if any(fascia in tbl.get_text() for fascia in ["Mattutina", "Solare", "Serale", "Notturna"]):
                table = tbl
                break

        if not table:
            raise ValueError("Tabella tariffe non trovata nella pagina AIL")

        # Estrai le righe della tabella
        rows = []
        tbody = table.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
        else:
            # Fallback: cerca tr diretti escludendo header
            all_rows = table.find_all('tr')
            rows = [r for r in all_rows if 'Fascia' not in r.get_text() and 'Utilizzo' not in r.get_text()]

        results = {}
        fascia_keywords = ["Mattutina", "Solare", "Serale", "Notturna"]

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            # Estrai nome fascia dalla prima cella
            first_cell = cells[0]
            fascia_text = first_cell.get_text(separator=' ', strip=True)
            
            fascia_name = None
            for kw in fascia_keywords:
                if kw in fascia_text:
                    fascia_name = kw
                    break
            if not fascia_name:
                continue

            # Estrai prezzo dall'ultima cella
            last_cell = cells[-1]
            price_text = last_cell.get_text(strip=True)
            
            # Pulizia aggressiva del prezzo
            clean_price = price_text.replace('\xa0', '').replace('\u2009', '').replace(' ', '')
            clean_price = re.sub(r'[^\d.,]', '', clean_price)
            
            # Estrai valore numerico
            match = re.search(r'(\d+[,.]\d+)', clean_price)
            if not match:
                _LOGGER.warning("⚠️ Nessun prezzo valido per %s in: '%s' (pulito: '%s')", fascia_name, price_text, clean_price)
                continue

            value = float(match.group(1).replace(',', '.'))
            
            # Mappa il nome fascia alla chiave interna
            results[TIME_SLOTS[fascia_name]] = value
            _LOGGER.debug("✓ Trovata %s: %.2f CHF/100kWh", fascia_name, value)

        # Verifica di aver trovato tutte e 4 le fasce
        if len(results) != 4:
            raise ValueError(f"Trovate solo {len(results)}/4 fasce orarie. Dettagli: {list(results.keys())}")

        results["date"] = date_str
        return results

    def _extract_and_validate_date(self, soup: BeautifulSoup, expected_date: date) -> tuple[date, str]:
        """
        Estrae la data dalla pagina e la valida rispetto all'attesa.
        
        Returns:
            tuple con (date_obj, date_string_formatted)
        """
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
                if not month:
                    continue
                page_date = date(int(year), month, int(day))
                
                if page_date != expected_date:
                    raise ValueError(f"⚠️ Data mismatch: pagina={page_date}, attesa={expected_date}")
                
                return page_date, f"{day} {month_it} {year}"

        raise ValueError("Impossibile trovare una data valida nella pagina AIL")
