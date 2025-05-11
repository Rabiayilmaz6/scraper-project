"""
Data processor module for The Dyrt scraper application.
"""
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from src.models.campground import Campground
from src.db.models import CampgroundDB
from src.scraper.geocoding import get_address

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class CampgroundProcessor:
    """
    Process and store campground data in the database.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the processor with a database session.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
    
    def _convert_to_db_model(self, campground: Campground) -> CampgroundDB:
        """
        Convert a Pydantic Campground model to a SQLAlchemy CampgroundDB model.
        
        Args:
            campground: Pydantic Campground model
            
        Returns:
            SQLAlchemy CampgroundDB model
        """
        try:
            if hasattr(campground.links, 'dict'):
                links_dict = campground.links.dict()
            else:
                links_dict = {"self": str(campground.links.self)}
        except AttributeError:
            links_dict = {"self": str(campground.links.self) if hasattr(campground.links, 'self') else "https://thedyrt.com"}
        except Exception as e:
            # Ultimate fallback
            logger.warning(f"Error converting links to dict: {e}")
            links_dict = {"self": "https://thedyrt.com"}
        
        try:
            photo_url_str = str(campground.photo_url) if campground.photo_url else None
            photo_urls_str = [str(url) for url in campground.photo_urls] if campground.photo_urls else []
        except Exception as e:
            logger.warning(f"Error converting photo URLs to strings: {e}")
            photo_url_str = None
            photo_urls_str = []
        
        # Adres bilgisini al veya boş bırak
        address = None
        if hasattr(campground, 'address') and campground.address:
            # Eğer adres zaten varsa kullan
            address = campground.address
        elif campground.latitude and campground.longitude:
            # Yoksa ve koordinatlar varsa geocoding kullan
            try:
                address = get_address(campground.latitude, campground.longitude)
                logger.info(f"Retrieved address for campground {campground.id}: {address}")
            except Exception as e:
                logger.warning(f"Error retrieving address for campground {campground.id}: {e}")
        
        return CampgroundDB(
            id=campground.id,
            type=campground.type,
            links=links_dict,
            name=campground.name,
            latitude=campground.latitude,
            longitude=campground.longitude,
            region_name=campground.region_name,
            administrative_area=campground.administrative_area,
            nearest_city_name=campground.nearest_city_name,
            accommodation_type_names=campground.accommodation_type_names,
            bookable=campground.bookable,
            camper_types=campground.camper_types,
            operator=campground.operator,
            photo_url=photo_url_str,
            photo_urls=photo_urls_str,
            photos_count=campground.photos_count,
            rating=campground.rating,
            reviews_count=campground.reviews_count,
            slug=campground.slug,
            price_low=campground.price_low,
            price_high=campground.price_high,
            availability_updated_at=campground.availability_updated_at,
            address=address,
            updated_at=datetime.now()
        )
    
    def store_campgrounds(self, campgrounds: List[Campground]) -> int:
        """
        Store multiple campgrounds in the database.
        Will update existing records if they already exist.
        
        Args:
            campgrounds: List of validated Campground objects
            
        Returns:
            Number of campgrounds stored
        """
        if not campgrounds:
            logger.warning("No campgrounds to store")
            return 0
        
        try:
            count = 0
            for campground in campgrounds:
                db_campground = self._convert_to_db_model(campground)
                
                links_json = {"self": str(db_campground.links["self"])} if isinstance(db_campground.links, dict) else {"self": "https://thedyrt.com"}
                photo_urls_str = [str(url) for url in db_campground.photo_urls] if db_campground.photo_urls else []
                
                stmt = insert(CampgroundDB).values(
                    id=db_campground.id,
                    type=db_campground.type,
                    links=links_json,
                    name=db_campground.name,
                    latitude=db_campground.latitude,
                    longitude=db_campground.longitude,
                    region_name=db_campground.region_name,
                    administrative_area=db_campground.administrative_area,
                    nearest_city_name=db_campground.nearest_city_name,
                    accommodation_type_names=db_campground.accommodation_type_names,
                    bookable=db_campground.bookable,
                    camper_types=db_campground.camper_types,
                    operator=db_campground.operator,
                    photo_url=db_campground.photo_url,
                    photo_urls=photo_urls_str,
                    photos_count=db_campground.photos_count,
                    rating=db_campground.rating,
                    reviews_count=db_campground.reviews_count,
                    slug=db_campground.slug,
                    price_low=db_campground.price_low,
                    price_high=db_campground.price_high,
                    availability_updated_at=db_campground.availability_updated_at,
                    address=db_campground.address,
                    updated_at=datetime.now()
                )
                
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],
                    set_={
                        'address': db_campground.address,
                        'type': db_campground.type,
                        'links': links_json,
                        'name': db_campground.name,
                        'latitude': db_campground.latitude,
                        'longitude': db_campground.longitude,
                        'region_name': db_campground.region_name,
                        'administrative_area': db_campground.administrative_area,
                        'nearest_city_name': db_campground.nearest_city_name,
                        'accommodation_type_names': db_campground.accommodation_type_names,
                        'bookable': db_campground.bookable,
                        'camper_types': db_campground.camper_types,
                        'operator': db_campground.operator,
                        'photo_url': db_campground.photo_url,
                        'photo_urls': photo_urls_str,
                        'photos_count': db_campground.photos_count,
                        'rating': db_campground.rating,
                        'reviews_count': db_campground.reviews_count,
                        'slug': db_campground.slug,
                        'price_low': db_campground.price_low,
                        'price_high': db_campground.price_high,
                        'availability_updated_at': db_campground.availability_updated_at,
                        'address': db_campground.address,
                        'updated_at': datetime.now()
                    }
                )
                
                self.db.execute(stmt)
                count += 1
            
            self.db.commit()
            logger.info(f"Successfully stored {count} campgrounds in the database")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error storing campgrounds: {e}")
            raise
