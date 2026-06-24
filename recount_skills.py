# recount_skills.py — run once to force fresh skills count
# python recount_skills.py
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()
from analysis.skills_analysis import run_skills_analysis
from database.db_manager import DBManager

db = DBManager()
# Wipe cached results completely
db.execute("TRUNCATE analysis_skills")
print("Cleared analysis_skills table")

# Rerun fresh
result = run_skills_analysis()
print(f"\nTop 20 skills:")
print(result.head(20).to_string(index=False))