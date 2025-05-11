"""
Simple scheduler module using the schedule library for The Dyrt scraper application.
"""
import logging
import time
import signal
import sys
import schedule

from src.scraper.scraper import run_scraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class SimpleScraperScheduler:
    """
    Simple scheduler for running The Dyrt scraper on a regular basis using the schedule library.
    """
    
    def __init__(self):
        """
        Initialize the scheduler.
        """
        self.running = False
        
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
    
    def _shutdown(self, signum, frame):
        """
        Handle shutdown signals gracefully.
        """
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        sys.exit(0)
    
    def schedule_daily(self, hour=0, minute=0):
        """
        Schedule the scraper to run daily at the specified time.
        
        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_scraper)
        logger.info(f"Scheduled scraper to run daily at {hour:02d}:{minute:02d}")
    
    def schedule_interval(self, hours=24):
        """
        Schedule the scraper to run at regular intervals.
        
        Args:
            hours: Number of hours between runs
        """
        schedule.every(hours).hours.do(run_scraper)
        logger.info(f"Scheduled scraper to run every {hours} hours")
    
    def schedule_weekly(self, day="monday", hour=0, minute=0):
        """
        Schedule the scraper to run weekly on the specified day and time.
        
        Args:
            day: Day of the week (monday, tuesday, etc.)
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        day_method = getattr(schedule.every(), day.lower())

        day_method.at(f"{hour:02d}:{minute:02d}").do(run_scraper)
        logger.info(f"Scheduled scraper to run every {day} at {hour:02d}:{minute:02d}")
    
    def run_immediately(self):
        """
        Run the scraper immediately.
        """
        logger.info("Running scraper immediately...")
        run_scraper()
    
    def start(self):
        """
        Start the scheduler and keep running until stopped.
        """
        self.running = True
        logger.info("Scheduler started")
        

        self.run_immediately()

        while self.running:
            schedule.run_pending()
            time.sleep(1)

def run_simple_scheduler(interval_hours=24, run_immediately=True):
    """
    Run the simple scheduler as a standalone function.
    
    Args:
        interval_hours: Number of hours between runs
        run_immediately: Whether to run the scraper immediately on start
    """
    logger.info("Starting The Dyrt simple scraper scheduler...")
    
    try:
        scheduler = SimpleScraperScheduler()
        
        scheduler.schedule_interval(interval_hours)
        
        scheduler.start()
            
    except Exception as e:
        logger.error(f"Scheduler failed: {e}")

if __name__ == "__main__":
    run_simple_scheduler()
