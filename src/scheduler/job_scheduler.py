"""
Scheduler module for The Dyrt scraper application.
"""
import logging
import time
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.scraper.scraper import run_scraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class ScraperScheduler:
    """
    Scheduler for running The Dyrt scraper on a regular basis.
    """
    
    def __init__(self):
        """
        Initialize the scheduler.
        """
        self.scheduler = BackgroundScheduler()
        self.running = False
        
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, signum, frame):
        """
        Handle shutdown signals gracefully.
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """
        Start the scheduler.
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            self.scheduler.start()
            self.running = True
            logger.info("Scheduler started")
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """
        Stop the scheduler.
        """
        if not self.running:
            logger.warning("Scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown()
            self.running = False
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            raise
    
    def add_job(self, cron_expression="0 0 * * *"):
        """
        Add the scraper job to the scheduler with the given cron expression.
        
        Args:
            cron_expression: Cron expression for scheduling (default: daily at midnight)
        """
        try:
            self.scheduler.add_job(
                run_scraper,
                trigger=CronTrigger.from_crontab(cron_expression),
                id="dyrt_scraper",
                name="The Dyrt Scraper",
                replace_existing=True
            )
            
            logger.info(f"Added scraper job with schedule: {cron_expression}")
            
            self.scheduler.add_job(
                run_scraper,
                id="dyrt_scraper_initial",
                name="The Dyrt Scraper (Initial Run)",
                replace_existing=True,
                next_run_time=datetime.now()
            )
            
            logger.info("Added one-time job for immediate execution")
            
        except Exception as e:
            logger.error(f"Error adding scraper job: {e}")
            raise

def run_scheduler(cron_expression="0 0 * * *"):
    """
    Run the scheduler as a standalone function.
    
    Args:
        cron_expression: Cron expression for scheduling (default: daily at midnight)
    """
    logger.info("Starting The Dyrt scraper scheduler...")
    
    try:
        scheduler = ScraperScheduler()
        scheduler.add_job(cron_expression)
        scheduler.start()
        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            scheduler.stop()
            
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")

if __name__ == "__main__":
    run_scheduler()
