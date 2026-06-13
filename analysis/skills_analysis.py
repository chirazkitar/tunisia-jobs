# analysis/skills_analysis.py
import pandas as pd
import re
from collections import Counter
from database.db_manager import DBManager
 
# Master skills dictionary — expand as needed
SKILLS_DICT = {
    # Frontend
    'react': 'frontend', 'angular': 'frontend', 'vue': 'frontend',
    'javascript': 'frontend', 'typescript': 'frontend', 'html': 'frontend',
    'css': 'frontend', 'sass': 'frontend', 'tailwind': 'frontend',
    # Backend
    'python': 'backend', 'java': 'backend', 'php': 'backend',
    'nodejs': 'backend', 'django': 'backend', 'spring': 'backend',
    'laravel': 'backend', 'fastapi': 'backend', 'express': 'backend',
    # Data / ML
    'pandas': 'data', 'numpy': 'data', 'scikit-learn': 'data',
    'tensorflow': 'data', 'pytorch': 'data', 'sql': 'data',
    'power bi': 'data', 'tableau': 'data', 'excel': 'data',
    # DevOps
    'docker': 'devops', 'kubernetes': 'devops', 'jenkins': 'devops',
    'git': 'devops', 'linux': 'devops', 'aws': 'devops', 'azure': 'devops',
    # Mobile
    'flutter': 'mobile', 'react native': 'mobile', 'android': 'mobile',
    'kotlin': 'mobile', 'swift': 'mobile',
    # Databases
    'mysql': 'database', 'postgresql': 'database', 'mongodb': 'database',
    'oracle': 'database', 'redis': 'database', 'elasticsearch': 'database',
}
 
def extract_skills(text: str) -> list[str]:
    text = text.lower()
    found = []
    for skill in SKILLS_DICT:
        # word-boundary match to avoid false positives
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text):
            found.append(skill)
    return found
 
def run_skills_analysis() -> pd.DataFrame:
    db = DBManager()
    df = db.get_all_jobs_with_description()
    counter = Counter()
    category_map = {}
    for desc in df['description'].dropna():
        skills = extract_skills(desc)
        counter.update(skills)
        for s in skills:
            category_map[s] = SKILLS_DICT[s]
    result = pd.DataFrame(counter.most_common(50),
                          columns=['skill', 'count'])
    result['category'] = result['skill'].map(category_map)
    result['pct_jobs'] = (result['count'] / len(df) * 100).round(1)
    db.save_skills_analysis(result)
    return result
