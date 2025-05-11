"""
Database rebuild module for the Dyrt Scraper application.
"""
import logging
from src.db.connection import engine, Base
from src.db.models import CampgroundDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def rebuild_db():
    """
    Rebuild the database by dropping and recreating all tables.
    WARNING: This will delete all data!
    """
    logger.info("Dropping all tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully.")
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error rebuilding database: {e}")
        raise

if __name__ == "__main__":
    rebuild_db()
