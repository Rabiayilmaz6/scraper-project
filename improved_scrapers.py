"""
Improved scraper module for The Dyrt web scraper application.
This version gets ALL campgrounds instead of just the first page.
"""
import logging
import time
import json
from typing import Dict, List, Optional
import requests
from pydantic import ValidationError
import os.path

from src.models.campground import Campground
from src.scraper.data_processor import CampgroundProcessor
from src.db.connection import SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class ImprovedDyrtApiClient:
    """
    Improved API client for interacting with The Dyrt's API.
    Now includes pagination to get ALL campgrounds.
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
                logger.debug(f"Making {method} request to {url}")
                
                if method.upper() == "GET":
                    response = self.session.get(url=url, params=params, timeout=30)
                elif method.upper() == "POST":
                    response = self.session.post(url=url, params=params, json=json_data, timeout=30)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                response.raise_for_status()
                
                json_response = response.json()
                logger.debug(f"Successfully received response from {url}")
                
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
    
    def search_campgrounds_paginated(self, bounds: Dict[str, float], max_pages: int = 20, per_page: int = 100) -> List[Dict]:
        """
        Search for campgrounds within specified bounds using pagination to get all results.
        
        Args:
            bounds: Map bounds as {"north": float, "east": float, "south": float, "west": float}
            max_pages: Maximum number of pages to retrieve (protection against infinite loops)
            per_page: Number of results per page
            
        Returns:
            List of campground data dictionaries
        """
        bounds_str = f"{bounds['south']},{bounds['west']},{bounds['north']},{bounds['east']}"
        all_campgrounds = []
        page = 1
        
        while page <= max_pages:
            params = {
                "bounds": bounds_str,
                "sort": "recommended",
                "page": page,
                "per_page": per_page
            }
            
            logger.info(f"Searching campgrounds with bounds: {bounds_str} (Page {page})")
            
            try:
                response = self._make_request("GET", self.SEARCH_ENDPOINT, params=params)
                
                campgrounds = []
                total_pages = 1  # Default in case we can't determine total pages
                
                if isinstance(response, dict):
                    # Extract campgrounds based on response format
                    if "results" in response and "campgrounds" in response["results"]:
                        campgrounds = response["results"]["campgrounds"]
                        total_pages = response.get("meta", {}).get("total_pages", 1)
                    elif "campgrounds" in response:
                        campgrounds = response["campgrounds"]
                        total_pages = response.get("meta", {}).get("total_pages", 1)
                    elif "data" in response:
                        campgrounds = response["data"]
                        total_pages = response.get("meta", {}).get("total_pages", 1)
                    else:
                        logger.warning(f"Unexpected response format on page {page}. Keys: {response.keys()}")
                        with open(f"unexpected_response_page{page}.json", "w") as f:
                            json.dump(response, f, indent=2)
                        logger.info(f"Saved unexpected response to unexpected_response_page{page}.json")
                elif isinstance(response, list):
                    campgrounds = response
                
                # Add campgrounds to our collection
                all_campgrounds.extend(campgrounds)
                logger.info(f"Found {len(campgrounds)} campgrounds on page {page}")
                
                # Check if we've reached the last page
                if len(campgrounds) < per_page or page >= total_pages:
                    logger.info(f"Reached the last page or end of results at page {page}")
                    break

                time.sleep(0.5)
                page += 1
            
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break
        
        logger.info(f"Completed pagination search: Found total {len(all_campgrounds)} campgrounds across {page} pages")
        return all_campgrounds
    
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


class ImprovedDyrtScraper:
    """
    Improved scraper class for The Dyrt website.
    Gets ALL campgrounds using pagination.
    """
    
    US_BOUNDS = {
        "west": -125.0,
        "east": -66.0,
        "north": 49.0,
        "south": 24.0
    }
    
    GRID_SIZE = 20  
    
    def __init__(self, grid_size: int = 20):
        """
        Initialize the scraper.
        
        Args:
            grid_size: Size of the grid for dividing US map (N x N)
        """
        self.GRID_SIZE = grid_size
        self.db_session = SessionLocal()
        self.api_client = ImprovedDyrtApiClient()
        self.data_processor = CampgroundProcessor(self.db_session)
        
        # Create a stats file to track progress
        self.stats_file = "scraper_stats.json"
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, "w") as f:
                json.dump({"total_campgrounds": 0, "processed_cells": []}, f)
    
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
        # Calculate the width and height of each grid cell
        lon_step = (self.US_BOUNDS["east"] - self.US_BOUNDS["west"]) / self.GRID_SIZE
        lat_step = (self.US_BOUNDS["north"] - self.US_BOUNDS["south"]) / self.GRID_SIZE
        
        grid_bounds = []
        
        # Generate bounds for each grid cell
        for i in range(self.GRID_SIZE):
            for j in range(self.GRID_SIZE):
                # Calculate the corners of this grid cell
                west = self.US_BOUNDS["west"] + j * lon_step
                east = self.US_BOUNDS["west"] + (j + 1) * lon_step
                south = self.US_BOUNDS["south"] + i * lat_step
                north = self.US_BOUNDS["south"] + (i + 1) * lat_step
                
                cell_id = f"{i}-{j}"
                
                grid_bounds.append({
                    "cell_id": cell_id,
                    "west": west,
                    "east": east,
                    "south": south,
                    "north": north
                })
        
        logger.info(f"Generated {len(grid_bounds)} grid cells for scraping")
        return grid_bounds
    
    def _load_stats(self) -> Dict:
        """
        Load scraper statistics from file.
        """
        try:
            with open(self.stats_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"total_campgrounds": 0, "processed_cells": []}
    
    def _save_stats(self, stats: Dict):
        """
        Save scraper statistics to file.
        """
        with open(self.stats_file, "w") as f:
            json.dump(stats, f, indent=2)
    
    def run(self, max_pages_per_cell: int = 10, per_page: int = 100, resume: bool = True) -> int:
        """
        Run the scraper to collect all campground data across the US.
        
        Args:
            max_pages_per_cell: Maximum number of pages to retrieve per grid cell
            per_page: Number of results per page
            resume: Whether to resume from last run or start fresh
            
        Returns:
            Total number of campgrounds scraped and stored
        """
        stats = self._load_stats() if resume else {"total_campgrounds": 0, "processed_cells": []}
        total_campgrounds = stats["total_campgrounds"]
        processed_cells = set(stats["processed_cells"])
        
        grid_bounds = self._generate_grid_bounds()
        
        try:
            for i, bounds in enumerate(grid_bounds):
                cell_id = bounds["cell_id"]
                
                # Skip already processed cells if resuming
                if resume and cell_id in processed_cells:
                    logger.info(f"Skipping already processed cell {i+1}/{len(grid_bounds)} (ID: {cell_id})")
                    continue
                
                logger.info(f"Processing grid cell {i+1}/{len(grid_bounds)} (ID: {cell_id})")
                
                # Get all campgrounds for this grid cell with pagination
                campground_data = self.api_client.search_campgrounds_paginated(
                    bounds=bounds,
                    max_pages=max_pages_per_cell,
                    per_page=per_page
                )
                
                # Skip if no campgrounds found
                if not campground_data:
                    logger.info(f"No campgrounds found in grid cell {cell_id}")
                    processed_cells.add(cell_id)
                    stats["processed_cells"] = list(processed_cells)
                    self._save_stats(stats)
                    continue
                
                # Parse and validate the campground data
                validated_campgrounds = self.api_client.parse_and_validate_campgrounds(campground_data)
                
                # Store the validated campgrounds
                stored_count = self.data_processor.store_campgrounds(validated_campgrounds)
                total_campgrounds += stored_count
                
                # Update stats and save
                processed_cells.add(cell_id)
                stats["total_campgrounds"] = total_campgrounds
                stats["processed_cells"] = list(processed_cells)
                self._save_stats(stats)
                
                # Add a small delay to avoid overwhelming the API
                time.sleep(1.0)
            
            logger.info(f"Scraper run completed. Total campgrounds: {total_campgrounds}")
            return total_campgrounds
            
        except Exception as e:
            logger.error(f"Error during scraper run: {e}")
            raise
        finally:
            self.close()


def run_improved_scraper(grid_size: int = 10, max_pages_per_cell: int = 10, per_page: int = 100, resume: bool = True):
    """
    Run the improved scraper as a standalone function.
    
    Args:
        grid_size: Size of the grid for dividing US map (N x N)
        max_pages_per_cell: Maximum number of pages to retrieve per grid cell
        per_page: Number of results per page
        resume: Whether to resume from last run or start fresh
    """
    logger.info("Starting The Dyrt improved scraper...")
    
    try:
        with ImprovedDyrtScraper(grid_size=grid_size) as scraper:
            total = scraper.run(
                max_pages_per_cell=max_pages_per_cell,
                per_page=per_page,
                resume=resume
            )
            logger.info(f"Scraper completed successfully. Total campgrounds: {total}")
    except Exception as e:
        logger.error(f"Scraper failed: {e}")


if __name__ == "__main__":
    # Allow running this module directly
    run_improved_scraper(
        grid_size=20,  # 20x20 grid
        max_pages_per_cell=10,  # 10 pages per grid cell
        per_page=100,  # 100 campgrounds per page
        resume=True  # Resume from last run
    )
