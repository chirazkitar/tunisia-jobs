# analysis/salary_analysis.py
import re
import pandas as pd
from database.db_manager import DBManager

PATTERNS = [
    r'(\d[\d\s]*)[\s]*[-–—][\s]*(\d[\d\s]*)[\s]*TND',
    r'De[\s]+(\d[\d\s]*)[\s]+[àa][\s]+(\d[\d\s]*)[\s]*TND',
    r'Salaire[\s]*:[\s]*(\d[\d\s]*)[\s]*TND',
]

def parse_salary(text: str):
    if not text:
        return None, None
    text = text.replace('\xa0', ' ').replace(',', '')
    for pattern in PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            nums = [float(n.replace(' ', '')) for n in m.groups()]
            if len(nums) == 2:
                return min(nums), max(nums)
            return nums[0], nums[0]
    return None, None

def run_salary_analysis() -> pd.DataFrame:
    db = DBManager()
    df = db.get_jobs_with_salary_raw()

    # No salary data yet — return empty DataFrame gracefully
    if df.empty or 'salary_raw' not in df.columns:
        print('[salary_analysis] No salary data available yet, skipping.')
        return pd.DataFrame(columns=['avg_min', 'avg_max', 'count'])

    df[['min_tnd', 'max_tnd']] = df['salary_raw'].apply(
        lambda x: pd.Series(parse_salary(x)))
    df = df.dropna(subset=['min_tnd'])

    if df.empty:
        print('[salary_analysis] No parseable salary ranges found yet, skipping.')
        return pd.DataFrame(columns=['avg_min', 'avg_max', 'count'])

    df['mid_tnd'] = (df['min_tnd'] + df['max_tnd']) / 2
    stats = df.groupby('title_normalized').agg(
        avg_min=('min_tnd', 'mean'),
        avg_max=('max_tnd', 'mean'),
        count=('job_id', 'count')
    ).sort_values('avg_min', ascending=False)
    db.save_salary_analysis(df)
    return stats