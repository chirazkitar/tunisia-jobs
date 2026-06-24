# analysis/skills_analysis.py
import pandas as pd
import re
from collections import Counter
from database.db_manager import DBManager

SKILLS_DICT = {
    'react': 'frontend', 'angular': 'frontend', 'vue': 'frontend',
    'vuejs': 'frontend', 'reactjs': 'frontend', 'angularjs': 'frontend',
    'javascript': 'frontend', 'typescript': 'frontend',
    'html': 'frontend', 'css': 'frontend', 'sass': 'frontend',
    'tailwind': 'frontend', 'bootstrap': 'frontend', 'jquery': 'frontend',
    'python': 'backend', 'java': 'backend', 'php': 'backend',
    'nodejs': 'backend', 'node.js': 'backend',
    'django': 'backend', 'flask': 'backend', 'fastapi': 'backend',
    'spring': 'backend', 'spring boot': 'backend',
    'laravel': 'backend', 'symfony': 'backend',
    'express': 'backend', '.net': 'backend', 'c#': 'backend',
    'c++': 'backend', 'ruby': 'backend', 'golang': 'backend',
    'pandas': 'data', 'numpy': 'data',
    'scikit-learn': 'data', 'scikit': 'data',
    'tensorflow': 'data', 'pytorch': 'data', 'keras': 'data',
    'sql': 'data', 'power bi': 'data', 'powerbi': 'data',
    'tableau': 'data', 'excel': 'data', 'vba': 'data',
    'machine learning': 'data', 'deep learning': 'data',
    'nlp': 'data', 'data science': 'data', 'data analyst': 'data',
    'data engineer': 'data', 'big data': 'data',
    'spark': 'data', 'hadoop': 'data', 'etl': 'data',
    'bi': 'data', 'business intelligence': 'data',
    'analyse de données': 'data', 'traitement de données': 'data',
    'docker': 'devops', 'kubernetes': 'devops', 'k8s': 'devops',
    'jenkins': 'devops', 'gitlab': 'devops', 'github': 'devops',
    'git': 'devops', 'linux': 'devops', 'unix': 'devops',
    'aws': 'devops', 'azure': 'devops', 'gcp': 'devops',
    'terraform': 'devops', 'ansible': 'devops', 'ci/cd': 'devops',
    'devops': 'devops', 'cloud': 'devops',
    'flutter': 'mobile', 'react native': 'mobile',
    'android': 'mobile', 'kotlin': 'mobile',
    'ios': 'mobile', 'swift': 'mobile', 'xamarin': 'mobile',
    'mysql': 'database', 'postgresql': 'database', 'postgres': 'database',
    'mongodb': 'database', 'oracle': 'database', 'redis': 'database',
    'elasticsearch': 'database', 'sql server': 'database',
    'sqlite': 'database', 'mariadb': 'database',
    'communication': 'soft', 'travail en équipe': 'soft',
    'gestion de projet': 'soft', 'management': 'soft',
    'leadership': 'soft', 'organisation': 'soft',
    'rigueur': 'soft', 'autonomie': 'soft',
    'français': 'language', 'anglais': 'language',
    'arabe': 'language', 'allemand': 'language',
    'espagnol': 'language', 'italien': 'language',
    'french': 'language', 'english': 'language', 'arabic': 'language',
    'sap': 'erp', 'odoo': 'erp', 'sage': 'erp',
    'microsoft office': 'tools', 'ms office': 'tools',
    'autocad': 'tools', 'solidworks': 'tools',
    'photoshop': 'tools', 'illustrator': 'tools', 'figma': 'tools',
    'jira': 'tools', 'trello': 'tools', 'scrum': 'tools', 'agile': 'tools',
}

def extract_skills(text: str) -> list:
    if not text or text.strip() in ('N/A', ''):
        return []
    text = text.lower()
    found = []
    for skill in SKILLS_DICT:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            found.append(skill)
    return found

def run_skills_analysis() -> pd.DataFrame:
    db = DBManager()
    df = db.fetch("""
        SELECT j.id, j.title, j.description, j.source,
               j.location, j.contract, j.posted_at,
               c.name AS company_name,
               s.name AS sector_name
        FROM jobs j
        LEFT JOIN companies c ON c.id = j.company_id
        LEFT JOIN sectors   s ON s.id = j.sector_id
        WHERE j.is_active = TRUE
          AND j.description IS NOT NULL
          AND j.description != ''
          AND j.description != 'N/A'
    """)

    if df.empty:
        print('[skills_analysis] No jobs with descriptions yet.')
        return pd.DataFrame(columns=['skill', 'count', 'category', 'pct_jobs'])

    counter      = Counter()
    category_map = {}
    for desc in df['description'].dropna():
        skills = extract_skills(desc)
        counter.update(skills)
        for s in skills:
            category_map[s] = SKILLS_DICT[s]

    if not counter:
        print('[skills_analysis] No skills found.')
        return pd.DataFrame(columns=['skill', 'count', 'category', 'pct_jobs'])

    result = pd.DataFrame(counter.most_common(), columns=['skill', 'count'])
    result['category'] = result['skill'].map(category_map)
    result['pct_jobs'] = (result['count'] / len(df) * 100).round(1)

    # Create table if not exists, then clear and refill
    db.execute("""
        CREATE TABLE IF NOT EXISTS analysis_skills (
            id          SERIAL PRIMARY KEY,
            run_date    DATE DEFAULT CURRENT_DATE,
            skill       VARCHAR(120),
            category    VARCHAR(60),
            job_count   INT,
            pct_jobs    NUMERIC(5,1)
        )
    """)
    db.execute("TRUNCATE analysis_skills")
    db.save_skills_analysis(result)
    print(f'[skills_analysis] {len(result)} skills tracked across {len(df)} jobs.')
    return result