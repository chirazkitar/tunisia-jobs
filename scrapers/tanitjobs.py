# scrapers/tanitjobs.py  (pattern identical to emploi_tn, different selectors)
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
 
BASE = 'https://www.tanitjobs.com'
 
class TanitJobsScraper(BaseScraper):
    def __init__(self): super().__init__('tanitjobs')
 
    def run(self, max_pages=15):
        jobs = []
        for page in range(1, max_pages + 1):
            url  = f'{BASE}/jobs/?page={page}&country=TN'
            resp = requests.get(url, headers=self.get_headers(), timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')
            cards = soup.select('.job-listing')
            if not cards: break
            for c in cards:
                title_el = c.select_one('h2 a')
                comp_el  = c.select_one('.company-name')
                loc_el   = c.select_one('.location')
                if not title_el: continue
                jobs.append({'title': title_el.text.strip(),
                             'company': comp_el.text.strip() if comp_el else '',
                             'location': loc_el.text.strip() if loc_el else '',
                             'source_url': BASE + title_el['href'],
                             'source': 'tanitjobs'})
            self.random_delay()
        return self.save_jobs(jobs)
