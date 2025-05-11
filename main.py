"""
Main entrypoint for The Dyrt web scraper case study.

This application scrapes campground data from The Dyrt website
(https://thedyrt.com/search) and stores it in a PostgreSQL database.

Usage:
    The scraper can be run directly (`python main.py`) or via Docker Compose (`docker compose up`).
    
    Command line arguments:
    --run-once: Run the scraper once and exit
    --schedule: Run the scraper on a schedule (default: every 24 hours)
    --interval HOURS: Set the interval in hours for scheduled runs (default: 24)
    --init-db: Initialize the database tables
    --api: Start the API server
    --port PORT: Port for the API server (default: 8000)
    
Example:
    python main.py --run-once
    python main.py --schedule --interval 12
    python main.py --api --port 8080

If you have any questions in mind you can connect to me directly via info@smart-maple.com
"""
import argparse
import logging
import sys
import threading

from src.db.setup import init_db
from src.db.rebuild import rebuild_db
from src.scraper.scraper import run_scraper
from src.scraper.browser_wrapper import run_browser_scraper
from src.scheduler.simple_scheduler import run_simple_scheduler
from src.api.api import run_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="The Dyrt Web Scraper")
    
    # Add command line arguments
    parser.add_argument("--run-once", action="store_true", help="Run the scraper once and exit")
    parser.add_argument("--browser", action="store_true", help="Use browser-based scraper instead of API-based")
    parser.add_argument("--schedule", action="store_true", help="Run the scraper on a schedule")
    parser.add_argument("--interval", type=int, default=24, help="Interval in hours for scheduled runs")
    parser.add_argument("--init-db", action="store_true", help="Initialize the database tables")
    parser.add_argument("--rebuild-db", action="store_true", help="Rebuild the database (WARNING: Deletes all data!)")
    parser.add_argument("--api", action="store_true", help="Start the API server")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API server")
    parser.add_argument("--update-addresses", action="store_true", help="Update addresses for campgrounds without address")
    parser.add_argument("--address-batch-size", type=int, default=100, help="Batch size for address updates")
    parser.add_argument("--force-update-addresses", action="store_true", help="Force update addresses even if they already exist")
    
    return parser.parse_args()

def main():
    """
    Main entry point for the application.
    """
    # Parse command line arguments
    args = parse_args()
    
    
    try:
        # Rebuild the database if requested
        if args.rebuild_db:
            logger.info("Rebuilding database...")
            rebuild_db()
            logger.info("Database rebuilt successfully")
        
        # Initialize the database if requested
        if args.init_db:
            logger.info("Initializing database...")
            init_db()
            logger.info("Database initialized successfully")
        
        # Update addresses if requested
        if args.update_addresses:
            logger.info("Updating addresses for campgrounds...")
            from address_update_test import update_addresses
            update_addresses(batch_size=args.address_batch_size, force_update=args.force_update_addresses)
            logger.info("Address updates completed")
            return
        # Run the scraper once if requested
        if args.run_once:
            logger.info("Running scraper once...")
            
            # Choose which scraper to run based on arguments
            if args.browser:
                logger.info("Using browser-based scraper")
                run_browser_scraper()
            else:
                logger.info("Using API-based scraper")
                run_scraper()
                
            logger.info("Scraper completed")
            return
        
        # Run the scheduler if requested
        if args.schedule:
            logger.info(f"Running scheduler with {args.interval} hour interval...")
            run_simple_scheduler(interval_hours=args.interval)
            return
        
        # Start the API server if requested
        if args.api:
            logger.info(f"Starting API server on port {args.port}...")
            api_thread = None
            
            # If scheduler is also requested, run it in a separate thread
            if args.schedule:
                logger.info(f"Also running scheduler with {args.interval} hour interval in background...")
                scheduler_thread = threading.Thread(
                    target=run_simple_scheduler,
                    args=(args.interval,),
                    daemon=True
                )
                scheduler_thread.start()
            
            # Run the API server in the main thread
            run_api(port=args.port)
            return
            
        # Default behavior: run once
        if not any([args.init_db, args.run_once, args.schedule, args.api]):
            logger.info("No action specified, running scraper once...")
            run_scraper()
            logger.info("Scraper completed")
    
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("The Dyrt Web Scraper starting...")
    main()
