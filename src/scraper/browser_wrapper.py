"""
Browser-based scraper wrapper for The Dyrt scraper application.
"""
import logging
from sqlalchemy.orm import Session

from src.scraper.browser.browser_scraper import scrape_campgrounds
from src.scraper.data_processor import CampgroundProcessor
from src.db.connection import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def run_browser_scraper():
    """
    Run the browser-based scraper and store the results in the database.
    """
    logger.info("Starting browser-based scraper...")
    
    try:
        db_session = SessionLocal()
        
        data_processor = CampgroundProcessor(db_session)
        
        campgrounds = scrape_campgrounds()
        
        if not campgrounds:
            logger.warning("No campgrounds found")
            return 0
        
        logger.info(f"Found {len(campgrounds)} campgrounds")
        
        stored_count = data_processor.store_campgrounds(campgrounds)
        
        logger.info(f"Stored {stored_count} campgrounds in the database")
        
        return stored_count
        
    except Exception as e:
        logger.error(f"Error running browser-based scraper: {e}")
        raise
    finally:
        if 'db_session' in locals():
            db_session.close()

if __name__ == "__main__":
    run_browser_scraper()
