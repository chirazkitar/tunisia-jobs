# scrapers/rekrute.py
BASE_R = 'https://www.rekrute.com'
 
class ReKruteScraper(BaseScraper):
    def __init__(self): super().__init__('rekrute')
 
    def run(self, max_pages=10):
        jobs = []
        for page in range(1, max_pages + 1):
            url  = f'{BASE_R}/offres.html?s=1&p={page}&r=1&pays=TN'
            resp = requests.get(url, headers=self.get_headers(), timeout=15)
            soup = BeautifulSoup(resp.text, 'lxml')
            cards = soup.select('.post-id')
            if not cards: break
            for c in cards:
                title_el = c.select_one('a.titreJob')
                comp_el  = c.select_one('.company')
                loc_el   = c.select_one('.location')
                sal_el   = c.select_one('.salary')
                if not title_el: continue
                jobs.append({'title': title_el.text.strip(),
                             'company': comp_el.text.strip() if comp_el else '',
                             'location': loc_el.text.strip() if loc_el else '',
                             'salary_raw': sal_el.text.strip() if sal_el else '',
                             'source_url': BASE_R + title_el['href'],
                             'source': 'rekrute'})
            self.random_delay()
        return self.save_jobs(jobs)
