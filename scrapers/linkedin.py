# scrapers/linkedin.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from .base_scraper import BaseScraper
import time
 
SEARCH_URL = ('https://www.linkedin.com/jobs/search/?keywords={kw}'
              '&location=Tunisia&f_TPR=r604800')
 
KEYWORDS = ['developpeur','data analyst','devops','ingenieur logiciel',
            'data engineer','chef de projet','ux designer']
 
class LinkedInScraper(BaseScraper):
    def __init__(self):
        super().__init__('linkedin')
        opts = Options()
        opts.add_argument('--headless=new')
        opts.add_argument('--no-sandbox')
        opts.add_argument(f'--user-agent={self.ua.random}')
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
 
    def scrape_keyword(self, keyword: str) -> list[dict]:
        url = SEARCH_URL.format(kw=keyword.replace(' ', '%20'))
        self.driver.get(url)
        time.sleep(3)
        # Scroll to load more cards
        for _ in range(5):
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1.5)
        cards = self.driver.find_elements(By.CSS_SELECTOR, '.job-search-card')
        jobs = []
        for card in cards:
            try:
                title   = card.find_element(By.CSS_SELECTOR, '.base-search-card__title').text
                company = card.find_element(By.CSS_SELECTOR, '.base-search-card__subtitle').text
                loc     = card.find_element(By.CSS_SELECTOR, '.job-search-card__location').text
                link    = card.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                jobs.append({'title': title, 'company': company,
                             'location': loc, 'source_url': link,
                             'source': 'linkedin'})
            except Exception:
                continue
        return jobs
 
    def run(self):
        all_jobs = []
        for kw in KEYWORDS:
            all_jobs.extend(self.scrape_keyword(kw))
            self.random_delay(3, 6)
        self.driver.quit()
        return self.save_jobs(all_jobs)
