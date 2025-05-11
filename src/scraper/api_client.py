"""
API client for The Dyrt scraper application.
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional
import httpx
import requests
from pydantic import ValidationError

from src.models.campground import Campground

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class DyrtApiClient:
    """
    API client for interacting with The Dyrt's API.
    Completely redesigned to directly use the frontend API endpoints.
    """
    
    BASE_URL = "https://thedyrt.com"
    SEARCH_ENDPOINT = "/api/v2/campgrounds/"
    
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://thedyrt.com/campgrounds",
        "Origin": "https://thedyrt.com",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """
        Initialize the API client.
        
        Args:
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
    
    def close(self):
        """
        Close the HTTP session.
        """
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
        """
        Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON body for POST requests
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Making {method} request to {url}")
                
                if method.upper() == "GET":
                    response = self.session.get(url=url, params=params, timeout=30)
                elif method.upper() == "POST":
                    response = self.session.post(url=url, params=params, json=json_data, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                json_response = response.json()
                logger.info(f"Successfully received response from {url}")
                
                return json_response
                
            except (requests.RequestException) as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {e}")
                
                if attempt < self.max_retries - 1:
                    backoff = self.retry_delay * (2 ** attempt) + (0.1 * attempt)
                    logger.info(f"Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise
    
    def search_campgrounds(self, bounds: Dict[str, float], limit: int = 50) -> List[Dict]:
        """
        Search for campgrounds within specified bounds using the actual frontend API.
        
        Args:
            bounds: Map bounds as {"north": float, "east": float, "south": float, "west": float}
            limit: Maximum number of results to return
            
        Returns:
            List of campground data dictionaries
        """
        bounds_str = f"{bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']}"
        
        params = {
            "bounds": bounds_str,
            "sort": "recommended",
            "page": 1,
            "per_page": limit
        }
        
        logger.info(f"Searching campgrounds with bounds: {bounds_str}")
        
        response = self._make_request("GET", self.SEARCH_ENDPOINT, params=params)
        
        campgrounds = []
        
        if isinstance(response, dict):
            if "results" in response and "campgrounds" in response["results"]:
                campgrounds = response["results"]["campgrounds"]
            elif "campgrounds" in response:
                campgrounds = response["campgrounds"]
            elif "data" in response:
                campgrounds = response["data"]
            else:
                logger.warning(f"Unexpected response format. Keys: {response.keys()}")
                with open("unexpected_response.json", "w") as f:
                    json.dump(response, f, indent=2)
                logger.info("Saved unexpected response to unexpected_response.json")
        elif isinstance(response, list):
            campgrounds = response
        
        logger.info(f"Found {len(campgrounds)} campgrounds in the specified bounds")
        return campgrounds
    
    def parse_and_validate_campgrounds(self, campground_data: List[Dict]) -> List[Campground]:
        """
        Parse and validate campground data using Pydantic models.
        
        Args:
            campground_data: List of campground data dictionaries from the API
            
        Returns:
            List of validated Campground objects
        """
        validated_campgrounds = []
        
        for data in campground_data:
            try:
                mapped_data = self._map_api_response_to_model(data)
                
                campground = Campground(**mapped_data)
                validated_campgrounds.append(campground)
            except ValidationError as e:
                logger.warning(f"Validation error for campground {data.get('id', 'unknown')}: {e}")
                logger.debug(f"Data: {data}")
                continue
            except Exception as e:
                logger.warning(f"Error processing campground {data.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Successfully validated {len(validated_campgrounds)} out of {len(campground_data)} campgrounds")
        return validated_campgrounds
    
    def _map_api_response_to_model(self, data: Dict) -> Dict:
        """
        Map API response fields to our Pydantic model fields.
        
        Args:
            data: Campground data from the API
            
        Returns:
            Mapped data ready for Pydantic model
        """
        mapped_data = {
            "id": data.get("id", ""),
            "type": data.get("type", "campground"),
            "links": {"self": data.get("url", "https://thedyrt.com")},
            "name": data.get("name", ""),
            "latitude": float(data.get("latitude", 0.0)),
            "longitude": float(data.get("longitude", 0.0)),
            "region-name": data.get("state", "Unknown"),
            "administrative-area": data.get("administrative_area", None),
            "nearest-city-name": data.get("nearest_city", None),
            "accommodation-type-names": data.get("accommodation_types", []),
            "bookable": data.get("bookable", False),
            "camper-types": data.get("camper_types", []),
            "operator": data.get("operator", None),
            "photo-url": data.get("primary_photo_url", None),
            "photo-urls": data.get("photo_urls", []),
            "photos-count": data.get("photos_count", 0),
            "rating": data.get("rating", None),
            "reviews-count": data.get("reviews_count", 0),
            "slug": data.get("slug", None),
            "price-low": data.get("price_low", None),
            "price-high": data.get("price_high", None),
            "availability-updated-at": data.get("availability_updated_at", None),
        }
        
        return mapped_data
