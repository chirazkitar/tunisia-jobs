# analysis/trends.py
import pandas as pd
from database.db_manager import DBManager
from analysis.skills_analysis import extract_skills

def run_trends_analysis() -> pd.DataFrame:
    db = DBManager()
    df = db.get_all_jobs_with_date()

    # No jobs yet — return empty DataFrame gracefully
    if df.empty:
        print('[trends] No jobs in DB yet, skipping.')
        return pd.DataFrame(columns=['year_month', 'total_jobs', 'growth_pct'])

    df['posted_at'] = pd.to_datetime(df['posted_at'], errors='coerce')
    df = df.dropna(subset=['posted_at'])

    if df.empty:
        print('[trends] No jobs with valid dates, skipping.')
        return pd.DataFrame(columns=['year_month', 'total_jobs', 'growth_pct'])

    df['year_month'] = df['posted_at'].dt.to_period('M')

    # Jobs per month per sector
    monthly_sector = (df.groupby(['year_month', 'sector_name'])
                        .size()
                        .reset_index(name='job_count'))

    # Growth rate MoM
    monthly_total = (df.groupby('year_month')
                       .size()
                       .reset_index(name='total_jobs'))
    monthly_total['growth_pct'] = (
        monthly_total['total_jobs'].pct_change() * 100).round(1)

    # Skills trend per month
    skill_rows = []
    for _, row in df.iterrows():
        for skill in extract_skills(row.get('description', '') or ''):
            skill_rows.append({'year_month': row['year_month'], 'skill': skill})

    skill_trend = pd.DataFrame(skill_rows)
    if not skill_trend.empty:
        skill_trend = (skill_trend.groupby(['year_month', 'skill'])
                                  .size()
                                  .reset_index(name='count'))
    else:
        skill_trend = pd.DataFrame(columns=['year_month', 'skill', 'count'])

    db.save_trends(monthly_total, monthly_sector, skill_trend)
    return monthly_total