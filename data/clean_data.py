# data/clean_data.py
# Cleans raw jobs from DB and returns a clean DataFrame
# Run: python data/clean_data.py

import sys, os, re, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
from database.db_manager import DBManager
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

CITY_MAP = {
    'tunis': 'Tunis', 'le bardo': 'Tunis', 'la marsa': 'Tunis', 'carthage': 'Tunis',
    'ariana': 'Ariana', 'ben arous': 'Ben Arous', 'manouba': 'Manouba',
    'sfax': 'Sfax', 'sousse': 'Sousse', 'monastir': 'Monastir', 'mahdia': 'Mahdia',
    'nabeul': 'Nabeul', 'hammamet': 'Nabeul', 'bizerte': 'Bizerte', 'beja': 'Béja',
    'jendouba': 'Jendouba', 'siliana': 'Siliana', 'zaghouan': 'Zaghouan',
    'kairouan': 'Kairouan', 'sidi bouzid': 'Sidi Bouzid', 'kasserine': 'Kasserine',
    'gafsa': 'Gafsa', 'tozeur': 'Tozeur', 'kebili': 'Kébili',
    'gabès': 'Gabès', 'médenine': 'Médenine', 'tataouine': 'Tataouine',
    'gaafour': 'Siliana', 'sahline': 'Monastir', 'rades': 'Ben Arous',
}

CONTRACT_MAP = {
    'cdi': 'CDI', 'contrat à durée indéterminée': 'CDI',
    'cdd': 'CDD', 'contrat à durée déterminée': 'CDD',
    'sivp': 'SIVP', 'stage': 'Stage', 'stagiaire': 'Stage',
    'freelance': 'Freelance', 'indépendant': 'Freelance',
    'intérim': 'Intérim', 'interim': 'Intérim',
    'alternance': 'Alternance', 'apprentissage': 'Alternance',
}

SOURCE_LABELS = {
    'optioncarriere': 'Keejob',
    'tanitjobs':      'EmploiTunisie',
    'rekrute':        'ReKrute',
    'linkedin':       'LinkedIn',
}

def clean_title(t):
    if not isinstance(t, str):
        return t
    t = re.sub(
        r'\s*-\s*(Tunis|Sfax|Sousse|Monastir|Ariana|Bizerte|Nabeul|Gabès|Gafsa|'
        r'Kairouan|Médenine|Ben Arous|Manouba|Mahdia|Tozeur|Kebili|Tataouine|'
        r'Beja|Jendouba|Siliana|Zaghouan|Gaafour|Sahline|Rades|El Mourouj|'
        r'France|Paris|Maroc|Abidjan|Dubai|Sofia|Bulgaria|Tunisia|Tunisie).*$',
        '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*[\(\[]?[HhFfMm]/[HhFfMm][\)\]]?', '', t)
    return re.sub(r'\s+', ' ', t).strip()

def normalize_location(loc):
    if not isinstance(loc, str) or not loc.strip():
        return 'Non précisé'
    loc_lower = loc.lower().strip()
    for key, val in CITY_MAP.items():
        if key in loc_lower:
            return val
    if any(k in loc_lower for k in ['tunisie', 'tunisia', ' tn']):
        return 'Tunisie (non précisé)'
    return loc.strip().title()[:50] if loc.strip() else 'Non précisé'

def normalize_contract(c):
    if not isinstance(c, str) or not c.strip():
        return 'Non précisé'
    c_lower = c.lower().strip()
    for key, val in CONTRACT_MAP.items():
        if key in c_lower:
            return val
    return c.strip()[:30]

def get_clean_jobs() -> pd.DataFrame:
    db   = DBManager()
    jobs = db.fetch("""
        SELECT j.id, j.title, j.description, j.location, j.contract,
               j.experience, j.source, j.posted_at, j.scraped_at,
               c.name AS company, s.name AS sector
        FROM jobs j
        LEFT JOIN companies c ON c.id = j.company_id
        LEFT JOIN sectors   s ON s.id = j.sector_id
        WHERE j.is_active = TRUE
    """)
    logging.info(f'Loaded {len(jobs)} raw jobs')

    jobs['title_clean']     = jobs['title'].apply(clean_title)
    jobs['location_clean']  = jobs['location'].apply(normalize_location)
    jobs['contract_clean']  = jobs['contract'].apply(normalize_contract)
    jobs['source_label']    = jobs['source'].map(SOURCE_LABELS).fillna(jobs['source'])
    jobs['sector']          = jobs['sector'].fillna('Non classifié')
    jobs['company']         = jobs['company'].fillna('').str.strip()
    jobs['posted_at']       = pd.to_datetime(jobs['posted_at'],  errors='coerce')
    jobs['scraped_at']      = pd.to_datetime(jobs['scraped_at'], errors='coerce')
    jobs['scrape_date']     = jobs['scraped_at'].dt.date
    jobs['scrape_month']    = jobs['scraped_at'].dt.to_period('M').astype(str)
    jobs['has_description'] = jobs['description'].apply(
        lambda d: 'Oui' if isinstance(d, str) and len(d) > 80 and d != 'N/A' else 'Non')

    logging.info(f'Cleaning done — {len(jobs)} jobs ready')
    return jobs

if __name__ == '__main__':
    df = get_clean_jobs()
    print(df[['title_clean', 'location_clean', 'contract_clean',
              'source_label', 'scrape_month']].head(10).to_string(index=False))