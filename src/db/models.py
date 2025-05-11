"""
SQLAlchemy models for the Dyrt Scraper application.
"""
from sqlalchemy import Column, String, Float, Boolean, Integer, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import JSONB

from src.db.connection import Base

class CampgroundDB(Base):
    """
    SQLAlchemy model for campgrounds table.
    Corresponds to the Pydantic model in src/models/campground.py
    """
    __tablename__ = "campgrounds"

    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    links = Column(JSONB, nullable=False)  # Store as JSON
    name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    region_name = Column(String, nullable=False)
    administrative_area = Column(String, nullable=True)
    nearest_city_name = Column(String, nullable=True)
    accommodation_type_names = Column(ARRAY(String), nullable=False, default=[])
    bookable = Column(Boolean, nullable=False, default=False)
    camper_types = Column(ARRAY(String), nullable=False, default=[])
    operator = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    photo_urls = Column(ARRAY(String), nullable=False, default=[])
    photos_count = Column(Integer, nullable=False, default=0)
    rating = Column(Float, nullable=True)
    reviews_count = Column(Integer, nullable=False, default=0)
    slug = Column(String, nullable=True)
    price_low = Column(Float, nullable=True)
    price_high = Column(Float, nullable=True)
    availability_updated_at = Column(DateTime, nullable=True)
    address = Column(String, nullable=True)  # Bonus field
    
    # Add timestamp fields for data management
    created_at = Column(DateTime, nullable=False, server_default="now()")
    updated_at = Column(DateTime, nullable=False, server_default="now()", onupdate="now()")
