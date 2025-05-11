"""
Address update test script for The Dyrt scraper application.
"""
import logging
import time
from sqlalchemy import select
from src.db.connection import SessionLocal
from src.db.models import CampgroundDB
from src.scraper.geocoding import get_address, get_address_with_fallback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def update_addresses(batch_size: int = 100, force_update: bool = False):
    """
    Update addresses for campgrounds that don't have an address.
    Process in batches to avoid overwhelming the geocoding service.
    
    Args:
        batch_size: Number of campgrounds to process in each batch
        force_update: If True, update all addresses even if they already exist
    """
    logger.info("Starting address update process...")
    
    db = SessionLocal()
    try:
        # Adresi olmayan veya güncellenmesi gereken kamp alanlarını bul
        query = db.query(CampgroundDB).filter(
            CampgroundDB.latitude.isnot(None),
            CampgroundDB.longitude.isnot(None)
        )
        
        if not force_update:
            query = query.filter(CampgroundDB.address.is_(None))
        
        campgrounds_to_update = query.all()
        
        logger.info(f"Found {len(campgrounds_to_update)} campgrounds that need address updates")
        
        if not campgrounds_to_update:
            logger.info("No campgrounds found that need address updates.")
            return 0
        
        # Batch'ler halinde işle
        updated_count = 0
        total_batches = (len(campgrounds_to_update) + batch_size - 1) // batch_size
        
        for i in range(0, len(campgrounds_to_update), batch_size):
            batch = campgrounds_to_update[i:i+batch_size]
            current_batch = i // batch_size + 1
            logger.info(f"Processing batch {current_batch}/{total_batches} ({len(batch)} campgrounds)")
            
            batch_updated = 0
            for campground in batch:
                try:
                    # Debug amaçlı koordinat kontrolü
                    if not campground.latitude or not campground.longitude:
                        logger.warning(f"Skipping campground {campground.id}: Invalid coordinates")
                        continue
                        
                    logger.info(f"Processing campground {campground.id} - Coordinates: {campground.latitude}, {campground.longitude}")
                    
                    # Birincil ve yedek mekanizmalarla adres almayı dene
                    address = get_address_with_fallback(campground.latitude, campground.longitude)
                    
                    if address:
                        old_address = campground.address
                        campground.address = address
                        
                        if old_address:
                            logger.info(f"Updated address for campground {campground.id}: {old_address} → {address}")
                        else:
                            logger.info(f"Added address for campground {campground.id}: {address}")
                            
                        batch_updated += 1
                        updated_count += 1
                    else:
                        logger.warning(f"No address found for campground {campground.id}")
                except Exception as e:
                    logger.warning(f"Error updating address for campground {campground.id}: {e}")
            
            # Toplu olarak güncelle
            db.commit()
            logger.info(f"Committed batch {current_batch} - updated {batch_updated} addresses")
            
            # API rate limit'e takılmamak için biraz bekle
            if i + batch_size < len(campgrounds_to_update):
                logger.info("Waiting 1 second before processing next batch...")
                time.sleep(1)
        
        logger.info(f"Address update completed. Total updated: {updated_count}/{len(campgrounds_to_update)}")
        return updated_count
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating addresses: {e}")
        raise
    
    finally:
        db.close()

def test_address_update():
    """
    Test updating addresses for a few campgrounds.
    """
    db = SessionLocal()
    try:
        # İlk 5 kamp alanını al
        campgrounds = db.query(CampgroundDB).limit(5).all()
        
        for i, campground in enumerate(campgrounds):
            logger.info(f"Testing campground {i+1}/{len(campgrounds)} (ID: {campground.id})")
            
            if not campground.latitude or not campground.longitude:
                logger.warning(f"Campground {campground.id} has no coordinates, skipping")
                continue
                
            logger.info(f"Coordinates: {campground.latitude}, {campground.longitude}")
            logger.info(f"Current address: {campground.address}")
            
            try:
                # Adres bilgisini al (fallback dahil)
                address = get_address_with_fallback(campground.latitude, campground.longitude)
                logger.info(f"Retrieved address: {address}")
                
                # Adres bilgisini güncelle
                if address:
                    campground.address = address
                    logger.info(f"Address updated to: {address}")
            except Exception as e:
                logger.error(f"Error during geocoding: {e}")
        
        # Değişiklikleri kaydet
        db.commit()
        logger.info("Changes committed to database")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during test: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Test ilk 5 kampground için
    logger.info("Testing address update for first 5 campgrounds...")
    test_address_update()
    
    # Adres güncellemesi yap
    logger.info("Running full address update...")
    update_addresses(batch_size=10)
