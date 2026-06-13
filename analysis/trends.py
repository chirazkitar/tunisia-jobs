# analysis/trends.py
import pandas as pd
from database.db_manager import DBManager
 
def run_trends_analysis() -> pd.DataFrame:
    db = DBManager()
    df = db.get_all_jobs_with_date()
    df['posted_at'] = pd.to_datetime(df['posted_at'])
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
 
    # Skills trend — top 10 skills per month
    skill_rows = []
    for _, row in df.iterrows():
        from analysis.skills_analysis import extract_skills
        for skill in extract_skills(row.get('description', '')):
            skill_rows.append({'year_month': row['year_month'], 'skill': skill})
    skill_df = pd.DataFrame(skill_rows)
    skill_trend = (skill_df.groupby(['year_month', 'skill'])
                            .size()
                            .reset_index(name='count'))
 
    db.save_trends(monthly_total, monthly_sector, skill_trend)
    return monthly_total
