# update_descriptions.py — backfill descriptions for keejob jobs marked N/A
import sys, os, logging, time, random
sys.path.insert(0, os.path.dirname(__file__))

import requests, urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup
from database.db_manager import DBManager
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'Accept-Language': 'fr-FR,fr;q=0.9',
}

def fetch_description(url: str) -> str:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, 'lxml')

        # keejob uses Tailwind — confirmed selector
        if 'keejob.com' in url:
            for sel in ['div.mt-4.text-gray-700',
                        'div[class*="text-gray-700"]',
                        'div[class*="prose"]']:
                el = soup.select_one(sel)
                if el:
                    text = el.get_text(separator=' ', strip=True)
                    if len(text) > 80:
                        return text[:3000]

        # emploitunisie / other sources
        for sel in ['.field-name-body', '.card-job-description',
                    '.job-description', '.description', '.field-items',
                    'main article', '.content', 'article']:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=' ', strip=True)
                if len(text) > 80:
                    return text[:3000]
    except Exception as e:
        logging.warning(f'fetch failed {url}: {e}')
    return ''

db    = DBManager()
jobs_df = db.fetch("""
    SELECT id, source_url, source
    FROM jobs
    WHERE source NOT IN ('linkedin')
      AND source_url IS NOT NULL AND source_url != ''
      AND (description IS NULL OR description = '' OR description = 'N/A')
    ORDER BY source, scraped_at DESC
    LIMIT 500
""")

total = len(jobs_df)
logging.info(f'Found {total} jobs needing descriptions')

if total == 0:
    logging.info('All done.')
    sys.exit(0)

updated = 0
marked  = 0
for _, row in jobs_df.iterrows():
    url  = row['source_url']
    jid  = int(row['id'])
    desc = fetch_description(url)
    if desc:
        db.execute("UPDATE jobs SET description = :d WHERE id = :id",
                   {'d': desc, 'id': jid})
        updated += 1
        if updated % 20 == 0:
            logging.info(f'Updated {updated}/{total}...')
    else:
        db.execute("UPDATE jobs SET description = 'N/A' WHERE id = :id",
                   {'id': jid})
        marked += 1
    time.sleep(random.uniform(0.3, 0.7))

logging.info(f'Done — updated: {updated} | marked N/A: {marked}')