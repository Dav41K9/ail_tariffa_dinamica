"""Scraper per le tariffe dinamiche AIL con validazione data."""
import re
import logging
from datetime import datetime, timedelta, date
from bs4 import BeautifulSoup
import aiohttp

_LOGGER = logging.getLogger(__name__)

class AILTariffScraper:
    """Classe per scaricare e parsare le tariffe AIL."""
    
    URL = "https://www.ail.ch/aziende/elettricita/prodotti/Tariffa-dinamica/tariffa-dinamica.html"
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        
    async def fetch_tariffs(self, expected_date: date | None = None) -> dict[str, float]:
        """
        Scarica e valida le tariffe.
        
        Args:
            expected_date: Data attesa (default: domani)
            
        Returns:
            Dict con chiavi: mattutina, solare, serale, notturna
            
        Raises:
            ValueError: Se validazione fallisce
        """
        if expected_date is None:
            expected_date = datetime.now().date() + timedelta(days=1)
        
        _LOGGER.debug("Fetching AIL tariffs, expected date: %s", expected_date)
        
        try:
            async with self.session.get(self.URL, timeout=30) as response:
                response.raise_for_status()
                html = await response.text()
        except aiohttp.ClientError as e:
            raise ValueError(f"Errore di rete durante il download: {e}")
        except TimeoutError:
            raise ValueError("Timeout durante il download della pagina AIL")
            
        return self._parse_html(html, expected_date)
    
    def _parse_html(self, html: str, expected_date: date) -> dict[str, float]:
        """Parsa l'HTML ed estrae le tariffe con validazione data."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1️⃣ Estrai e valida la data
        page_date = self._extract_and_validate_date(soup, expected_date)
        _LOGGER.info("Data pagina validata: %s", page_date)
        
        # 2️⃣ Trova la tabella
        table = soup.find('table')
        if not table:
            raise ValueError("Tabella tariffe non trovata nella pagina")
            
        # 3️⃣ Estrai righe (gestisci tbody se presente)
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')[1:]  # Salta header
        
        results = {}
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 6:
                continue
                
            # Estrai nome fascia
            fascia_cell = cells[0].get_text(strip=True)
            fascia_name = None
            for it_name in ["Mattutina", "Solare", "Serale", "Notturna"]:
                if it_name in fascia_cell:
                    fascia_name = it_name
                    break
                    
            if not fascia_name:
                continue
                
            # Estrai totale (ultima colonna, numero rosso)
            total_cell = cells[-1]
            total_text = total_cell.get_text(strip=True)
            match = re.search(r'(\d+,\d+)', total_text)
            if not match:
                _LOGGER.warning("Nessun prezzo trovato per %s: '%s'", fascia_name, total_text)
                continue
                
            value = float(match.group(1).replace(',', '.'))
            from .const import TIME_SLOTS
            results[TIME_SLOTS[fascia_name]] = value
            _LOGGER.debug("Trovata tariffa %s: %.2f CHF/100kWh", fascia_name, value)
            
        if len(results) != 4:
            raise ValueError(f"Trovate solo {len(results)}/4 fasce orarie. Dati incompleti.")
            
        return results
    
    def _extract_and_validate_date(self, soup: BeautifulSoup, expected_date: date) -> date:
        """Estrae la data dalla pagina e la valida contro quella attesa."""
        # Cerca heading con formato "29 aprile 2026"
        date_pattern = re.compile(r'(\d{1,2})\s+(' + '|'.join([
            'gennaio','febbraio','marzo','aprile','maggio','giugno',
            'luglio','agosto','settembre','ottobre','novembre','dicembre'
        ]) + r')\s+(20\d{2})', re.IGNORECASE)
        
        # Cerca in tutto il testo della pagina
        for element in soup.find_all(string=True):
            text = str(element).strip()
            match = date_pattern.search(text)
            if match:
                day, month_it, year = match.groups()
                months = {
                    'gennaio':1,'febbraio':2,'marzo':3,'aprile':4,'maggio':5,'giugno':6,
                    'luglio':7,'agosto':8,'settembre':9,'ottobre':10,'novembre':11,'dicembre':12
                }
                page_date = date(int(year), months[month_it.lower()], int(day))
                
                if page_date != expected_date:
                    raise ValueError(
                        f"⚠️ Data mismatch: pagina={page_date}, attesa={expected_date}. "
                        f"I dati potrebbero non essere ancora aggiornati (caricamento previsto alle 18:00)."
                    )
                return page_date
                
        raise ValueError("Impossibile trovare una data valida nella pagina AIL")