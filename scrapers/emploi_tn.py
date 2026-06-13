# scrapers/emploi_tn.py
import requests
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from datetime import datetime
 
BASE = 'https://www.emploi.tn'
 
class EmploiTNScraper(BaseScraper):
    def __init__(self):
        super().__init__('emploi_tn')
 
    def fetch_listing_page(self, page: int) -> list[dict]:
        url = f'{BASE}/offres-emploi?page={page}'
        resp = requests.get(url, headers=self.get_headers(), timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'lxml')
        jobs = []
        for card in soup.select('.job-result-item'):
            title_el  = card.select_one('.job-result-title a')
            comp_el   = card.select_one('.job-company')
            loc_el    = card.select_one('.job-location')
            date_el   = card.select_one('.job-date')
            if not title_el: continue
            jobs.append({
                'title'      : title_el.get_text(strip=True),
                'company'    : comp_el.get_text(strip=True) if comp_el else '',
                'location'   : loc_el.get_text(strip=True) if loc_el else '',
                'posted_raw' : date_el.get_text(strip=True) if date_el else '',
                'source_url' : BASE + title_el['href'],
                'source'     : 'emploi_tn',
            })
        return jobs
 
    def fetch_job_detail(self, job: dict) -> dict:
        resp = requests.get(job['source_url'], headers=self.get_headers(), timeout=15)
        soup = BeautifulSoup(resp.text, 'lxml')
        desc_el = soup.select_one('.job-description')
        job['description'] = desc_el.get_text(separator=' ', strip=True) if desc_el else ''
        contract_el = soup.select_one('.contract-type')
        job['contract'] = contract_el.get_text(strip=True) if contract_el else ''
        return job
 
    def run(self, max_pages: int = 20):
        all_jobs = []
        for page in range(1, max_pages + 1):
            jobs = self.fetch_listing_page(page)
            if not jobs:
                break
            for job in jobs:
                self.random_delay()
                all_jobs.append(self.fetch_job_detail(job))
            self.random_delay(2, 5)
        return self.save_jobs(all_jobs)
