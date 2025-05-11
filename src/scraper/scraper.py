"""
Main scraper module for The Dyrt scraper application.
"""
import logging
import time
from typing import List, Dict
from sqlalchemy.orm import Session

from src.scraper.api_client import DyrtApiClient
from src.scraper.data_processor import CampgroundProcessor
from src.db.connection import SessionLocal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class DyrtScraper:
    """
    Main scraper class for The Dyrt website.
    """
    
    US_BOUNDS = {
        "west": -125.0,
        "east": -66.0,
        "north": 49.0,
        "south": 24.0
    }
    
    GRID_SIZE = 10  # 10x10 grid = 100 sub-regions
    
    def __init__(self):
        """
        Initialize the scraper.
        """
        self.db_session = SessionLocal()
        self.api_client = DyrtApiClient()
        self.data_processor = CampgroundProcessor(self.db_session)
    
    def close(self):
        """
        Close all resources.
        """
        self.db_session.close()
        self.api_client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _generate_grid_bounds(self) -> List[Dict[str, float]]:
        """
        Generate a grid of bounds to cover the entire US.
        
        Returns:
            List of bound dictionaries for each grid cell
        """
        lon_step = (self.US_BOUNDS["east"] - self.US_BOUNDS["west"]) / self.GRID_SIZE
        lat_step = (self.US_BOUNDS["north"] - self.US_BOUNDS["south"]) / self.GRID_SIZE
        
        grid_bounds = []
        
        for i in range(self.GRID_SIZE):
            for j in range(self.GRID_SIZE):
                west = self.US_BOUNDS["west"] + j * lon_step
                east = self.US_BOUNDS["west"] + (j + 1) * lon_step
                south = self.US_BOUNDS["south"] + i * lat_step
                north = self.US_BOUNDS["south"] + (i + 1) * lat_step
                
                grid_bounds.append({
                    "west": west,
                    "east": east,
                    "south": south,
                    "north": north
                })
        
        logger.info(f"Generated {len(grid_bounds)} grid cells for scraping")
        return grid_bounds
    
    def run(self, limit_per_request: int = 50) -> int:
        """
        Run the scraper to collect all campground data across the US.
        
        Args:
            limit_per_request: Maximum number of results per API request
            
        Returns:
            Total number of campgrounds scraped and stored
        """
        total_campgrounds = 0
        grid_bounds = self._generate_grid_bounds()
        
        try:
            for i, bounds in enumerate(grid_bounds):
                logger.info(f"Processing grid cell {i+1}/{len(grid_bounds)}")
                
                campground_data = self.api_client.search_campgrounds(
                    bounds=bounds,
                    limit=limit_per_request
                )
                
                validated_campgrounds = self.api_client.parse_and_validate_campgrounds(campground_data)
                
                stored_count = self.data_processor.store_campgrounds(validated_campgrounds)
                total_campgrounds += stored_count
                
                time.sleep(0.5)
            
            logger.info(f"Scraper run completed. Total campgrounds: {total_campgrounds}")
            return total_campgrounds
            
        except Exception as e:
            logger.error(f"Error during scraper run: {e}")
            raise
        finally:
            self.close()

def run_scraper():
    """
    Run the scraper as a standalone function.
    """
    logger.info("Starting The Dyrt scraper...")
    
    try:
        with DyrtScraper() as scraper:
            total = scraper.run()
            logger.info(f"Scraper completed successfully. Total campgrounds: {total}")
    except Exception as e:
        logger.error(f"Scraper failed: {e}")

if __name__ == "__main__":
    run_scraper()

def update_addresses(batch_size: int = 100):
    """
    Update addresses for campgrounds that don't have an address.
    Process in batches to avoid overwhelming the geocoding service.
    
    Args:
        batch_size: Number of campgrounds to process in each batch
    """
    import time
    from src.db.connection import SessionLocal
    from src.db.models import CampgroundDB
    from src.scraper.geocoding import get_address
    
    logger.info("Starting address update process...")
    
    db = SessionLocal()
    try:
        # Adresi olmayan kamp alanlarını bul
        campgrounds_without_address = db.query(CampgroundDB).filter(
            CampgroundDB.address.is_(None),
            CampgroundDB.latitude.isnot(None),
            CampgroundDB.longitude.isnot(None)
        ).all()
        
        logger.info(f"Found {len(campgrounds_without_address)} campgrounds without address")
        
        if not campgrounds_without_address:
            logger.info("No campgrounds found that need address updates.")
            return 0
        
        # Batch'ler halinde işle
        updated_count = 0
        total_batches = (len(campgrounds_without_address) + batch_size - 1) // batch_size
        
        for i in range(0, len(campgrounds_without_address), batch_size):
            batch = campgrounds_without_address[i:i+batch_size]
            current_batch = i // batch_size + 1
            logger.info(f"Processing batch {current_batch}/{total_batches} ({len(batch)} campgrounds)")
            
            batch_updated = 0
            for campground in batch:
                try:
                    address = get_address(campground.latitude, campground.longitude)
                    if address:
                        campground.address = address
                        logger.info(f"Updated address for campground {campground.id}: {address}")
                        batch_updated += 1
                        updated_count += 1
                except Exception as e:
                    logger.warning(f"Error updating address for campground {campground.id}: {e}")
            
            # Toplu olarak güncelle
            db.commit()
            logger.info(f"Committed batch {current_batch} - updated {batch_updated} addresses")
            
            # API rate limit'e takılmamak için biraz bekle
            if i + batch_size < len(campgrounds_without_address):
                logger.info("Waiting 1 second before processing next batch...")
                time.sleep(1)
        
        logger.info(f"Address update completed. Total updated: {updated_count}/{len(campgrounds_without_address)}")
        return updated_count
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating addresses: {e}")
        raise
    
    finally:
        db.close()