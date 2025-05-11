"""
API module for The Dyrt scraper application.
"""
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.db.connection import get_db
from src.db.models import CampgroundDB
from src.scraper.scraper import run_scraper
from src.scheduler.simple_scheduler import SimpleScraperScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="The Dyrt Scraper API",
    description="API for The Dyrt web scraper application",
    version="1.0.0",
)

scheduler = SimpleScraperScheduler()

def run_scraper_task():
    """
    Run the scraper as a background task.
    """
    try:
        run_scraper()
    except Exception as e:
        logger.error(f"Error running scraper: {e}")

@app.get("/")
async def root():
    """
    Root endpoint.
    """
    return {
        "message": "Welcome to The Dyrt Scraper API",
        "docs_url": "/docs",
    }

@app.get("/campgrounds")
async def get_campgrounds(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    state: Optional[str] = None,
    min_rating: Optional[float] = None,
):
    """
    Get a list of campgrounds.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        state: Filter by state/region
        min_rating: Filter by minimum rating
    """
    try:
        query = select(CampgroundDB)
        if state:
            query = query.where(CampgroundDB.administrative_area == state)
        
        if min_rating:
            query = query.where(CampgroundDB.rating >= min_rating)
        query = query.offset(skip).limit(limit)
        result = db.execute(query)
        campgrounds = result.scalars().all()
        campgrounds_list = []
        for campground in campgrounds:
            if not campground.name or (campground.latitude == 0 and campground.longitude == 0):
                continue
                
            campground_dict = {
                "id": campground.id,
                "name": campground.name or "Unknown Campground", 
                "latitude": campground.latitude,
                "longitude": campground.longitude,
                "region_name": campground.region_name or "Unknown Region",  
                "administrative_area": campground.administrative_area,
                "rating": campground.rating,
                "reviews_count": campground.reviews_count,
                "bookable": campground.bookable,
                "price_low": campground.price_low,
                "price_high": campground.price_high,
                "photo_url": campground.photo_url,
            }
            campgrounds_list.append(campground_dict)
        
        return campgrounds_list
    
    except Exception as e:
        logger.error(f"Error getting campgrounds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/campgrounds/{campground_id}")
async def get_campground(campground_id: str, db: Session = Depends(get_db)):
    """
    Get a specific campground by ID.
    
    Args:
        campground_id: Campground ID
        db: Database session
    """
    try:
        campground = db.query(CampgroundDB).filter(CampgroundDB.id == campground_id).first()
        if not campground:
            raise HTTPException(status_code=404, detail="Campground not found")
        campground_dict = {
            "id": campground.id,
            "type": campground.type,
            "name": campground.name or "Unknown Campground",
            "latitude": campground.latitude,
            "longitude": campground.longitude,
            "region_name": campground.region_name or "Unknown Region",
            "administrative_area": campground.administrative_area,
            "nearest_city_name": campground.nearest_city_name,
            "accommodation_type_names": campground.accommodation_type_names or [],
            "bookable": campground.bookable,
            "camper_types": campground.camper_types or [],
            "operator": campground.operator,
            "photo_url": campground.photo_url,
            "photo_urls": campground.photo_urls or [],
            "photos_count": campground.photos_count,
            "rating": campground.rating,
            "reviews_count": campground.reviews_count,
            "slug": campground.slug,
            "price_low": campground.price_low,
            "price_high": campground.price_high,
            "availability_updated_at": campground.availability_updated_at,
            "address": campground.address,
        }
        
        return campground_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campground {campground_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scraper/run")
async def trigger_scraper(background_tasks: BackgroundTasks):
    """
    Trigger the scraper to run.
    """
    try:
        background_tasks.add_task(run_scraper_task)
        
        return {
            "message": "Scraper started in the background",
            "started_at": datetime.now().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error triggering scraper: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/start")
async def start_scheduler(interval_hours: int = 24):
    """
    Start the scheduler.
    
    Args:
        interval_hours: Number of hours between runs
    """
    try:
        if scheduler.running:
            return {
                "message": "Scheduler is already running",
            }

        scheduler.schedule_interval(interval_hours)
        
        import threading
        scheduler_thread = threading.Thread(target=scheduler.start)
        scheduler_thread.daemon = True
        scheduler_thread.start()
        
        return {
            "message": f"Scheduler started with {interval_hours} hour interval",
            "started_at": datetime.now().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/stop")
async def stop_scheduler():
    """
    Stop the scheduler.
    """
    try:
        if not scheduler.running:
            return {
                "message": "Scheduler is not running",
            }
        scheduler.running = False
        
        return {
            "message": "Scheduler stopped",
            "stopped_at": datetime.now().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scheduler/status")
async def scheduler_status():
    """
    Get the scheduler status.
    """
    try:
        return {
            "running": scheduler.running,
        }
    
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def run_api(host="0.0.0.0", port=8000):
    """
    Run the API server.
    """
    import uvicorn
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_api()
