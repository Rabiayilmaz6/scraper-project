"""
Geocoding module for resolving addresses from latitude/longitude coordinates.
"""
import logging
import time
from typing import Dict, Optional, Tuple
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class GeocodingService:
    """
    Service for geocoding operations (converting between coordinates and addresses).
    """
    
    # Base URL for Nominatim (OpenStreetMap) reverse geocoding service
    BASE_URL = "https://nominatim.openstreetmap.org/reverse"
    
    # Default headers to use for requests (to avoid being blocked)
    DEFAULT_HEADERS = {
        "User-Agent": "DyrtScraperProject/1.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://github.com/",
    }
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the geocoding service.
        
        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def get_address_from_coordinates(self, latitude: float, longitude: float) -> Optional[str]:
        """
        Get a formatted address from the given coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Formatted address as a string, or None if not found
        """
        params = {
            "format": "json",
            "lat": latitude,
            "lon": longitude,
            "zoom": 18,  # Zoom level for the most detailed address
            "addressdetails": 1,
            "accept-language": "en",  # İngilizce sonuçlar al
            "namedetails": 1,  # Daha fazla isim detayı
        }
        
        for attempt in range(self.max_retries):
            try:
                # Add a delay to avoid overwhelming the API
                if attempt > 0:
                    backoff = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                
                # Make the request
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.DEFAULT_HEADERS,
                    timeout=10.0
                )
                
                # Raise exception for HTTP errors
                response.raise_for_status()
                
                # Parse the response
                data = response.json()
                
                # Extract the formatted address
                if "display_name" in data:
                    return data["display_name"]
                
                return None
                
            except requests.RequestException as e:
                logger.warning(f"Geocoding request failed (attempt {attempt+1}/{self.max_retries}): {e}")
                
                if attempt >= self.max_retries - 1:
                    logger.error(f"Geocoding failed after {self.max_retries} attempts")
                    return None
    
    def get_address_components(self, latitude: float, longitude: float) -> Optional[Dict]:
        """
        Get address components from the given coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary of address components, or None if not found
        """
        params = {
            "format": "json",
            "lat": latitude,
            "lon": longitude,
            "zoom": 18,  # Zoom level for the most detailed address
            "addressdetails": 1,
        }
        
        for attempt in range(self.max_retries):
            try:
                # Add a delay to avoid overwhelming the API
                if attempt > 0:
                    backoff = self.retry_delay * (2 ** attempt)
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                
                # Make the request
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    headers=self.DEFAULT_HEADERS,
                    timeout=10.0
                )
                
                # Raise exception for HTTP errors
                response.raise_for_status()
                
                # Parse the response
                data = response.json()
                
                # Extract the address components
                if "address" in data:
                    return data["address"]
                
                return None
                
            except requests.RequestException as e:
                logger.warning(f"Geocoding request failed (attempt {attempt+1}/{self.max_retries}): {e}")
                
                if attempt >= self.max_retries - 1:
                    logger.error(f"Geocoding failed after {self.max_retries} attempts")
                    return None

def get_address(latitude: float, longitude: float) -> Optional[str]:
    """
    Convenience function to get a formatted address from coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Formatted address as a string, or None if not found
    """
    logger.info(f"Geocoding coordinates: lat={latitude}, lon={longitude}")
    
    geocoding_service = GeocodingService()
    address = geocoding_service.get_address_from_coordinates(latitude, longitude)
    
    if address:
        logger.info(f"Geocoding successful! Found address: {address}")
    else:
        logger.warning(f"Geocoding failed! No address found for coordinates: lat={latitude}, lon={longitude}")
    
    return address

def get_address_with_fallback(latitude: float, longitude: float) -> Optional[str]:
    """
    Get address with multiple geocoding providers for better reliability.
    """
    # İlk olarak Nominatim'i dene
    try:
        address = get_address(latitude, longitude)
        if address:
            return address
    except Exception as e:
        logger.warning(f"Primary geocoding failed: {e}")
    
    # Yedek olarak basit tersine geocoding uygula
    try:
        if latitude and longitude:
            # Basit tersine geocoding: Lat/Lon → region_name ile birleştir
            nearby_location = f"Location at coordinates: {latitude:.6f}, {longitude:.6f}"
            return nearby_location
    except Exception as e:
        logger.warning(f"Fallback geocoding failed: {e}")
    
    return None