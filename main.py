# main.py
import schedule, time, logging
from scrapers.emploi_tn  import EmploiTNScraper
from scrapers.linkedin   import LinkedInScraper
from scrapers.tanitjobs  import TanitJobsScraper
from scrapers.rekrute    import ReKruteScraper
from analysis.skills_analysis import run_skills_analysis
from analysis.salary_analysis import run_salary_analysis
from analysis.trends          import run_trends_analysis
from ai.summarizer            import summarize_market
from dotenv import load_dotenv
 
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('scrape.log')]
)
 
def full_pipeline():
    logging.info('=== Pipeline started ===')
 
    # 1. Scraping
    scrapers = [EmploiTNScraper(), TanitJobsScraper(),
                ReKruteScraper(), LinkedInScraper()]
    for scraper in scrapers:
        try:
            n = scraper.run()
            logging.info(f'{scraper.source}: {n} new jobs inserted')
        except Exception as e:
            logging.error(f'{scraper.source} failed: {e}')
 
    # 2. Analysis
    skills_df  = run_skills_analysis()
    salary_df  = run_salary_analysis()
    trends_df  = run_trends_analysis()
    logging.info(f'Analysis complete: {len(skills_df)} skills tracked')
 
    # 3. AI Summary
    summary = summarize_market()
    logging.info(f'AI summary generated ({summary["tokens_used"]} tokens)')
 
    logging.info('=== Pipeline complete ===')
 
if __name__ == '__main__':
    import sys
    if '--once' in sys.argv:
        full_pipeline()             # One-shot run
    else:
        schedule.every().day.at('07:00').do(full_pipeline)
        logging.info('Scheduler started — daily run at 07:00')
        while True:
            schedule.run_pending()
            time.sleep(60)

