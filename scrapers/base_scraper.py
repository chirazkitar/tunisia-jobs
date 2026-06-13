# scrapers/base_scraper.py
import time, random, logging
from fake_useragent import UserAgent
from database.db_manager import DBManager
 
class BaseScraper:
    def __init__(self, source_name: str):
        self.source = source_name
        self.db = DBManager()
        self.ua = UserAgent()
        self.logger = logging.getLogger(source_name)
 
    def random_delay(self, min_s=1.5, max_s=4.0):
        time.sleep(random.uniform(min_s, max_s))
 
    def get_headers(self) -> dict:
        return {
            'User-Agent': self.ua.random,
            'Accept-Language': 'fr-TN,fr;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml',
        }
 
    def save_jobs(self, jobs: list[dict]) -> int:
        """Insert jobs into DB, skip duplicates. Returns count inserted."""
        inserted = 0
        for job in jobs:
            try:
                if self.db.insert_job(job):
                    inserted += 1
            except Exception as e:
                self.logger.warning(f'Skip duplicate: {e}')
        self.db.log_run(self.source, len(jobs), inserted)
        return inserted
 
    def run(self):
        raise NotImplementedError
