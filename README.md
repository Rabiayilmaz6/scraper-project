## Project Overview

This project is a web scraper application that automatically extracts and stores information about all campgrounds across the United States from [The Dyrt](https://thedyrt.com/search) website. The application leverages The Dyrt's map interface to collect latitude/longitude and other campground data through API requests.

## Technical Features

1. **Database Integration**
   - Connection to PostgreSQL database
   - Usage of SQLAlchemy ORM
   - Appropriate schema design for campground data
   - Efficient update mechanisms

2. **Data Extraction Process**
   - Analysis of The Dyrt's map interface network requests
   - Identification of API endpoints and data extraction
   - API requests using Requests and HTTPX libraries
   - Browser-based scraping option

3. **Data Validation**
   - Data validation with Pydantic
   - Checking required fields
   - Storage of validated data in the database

4. **Scheduler Implementation**
   - Cron-like scheduling system for regular updates
   - Automatic data refresh at specified intervals

5. **Data Update Mechanism**
   - Checking for the existence of records and updating them
   - Prevention of duplicate entries

6. **Error Handling**
   - Catching errors that may occur during HTTP requests
   - Retry mechanisms when necessary
   - Comprehensive logging system

7. **Advanced Features**
   - API endpoints for scraper control
   - Multi-page data extraction (pagination)
   - Scanning the US map using a grid system
   - Progress tracking and ability to resume interrupted operations
   - Address information derivation from latitude/longitude data

## Project Structure

```
scraper_project/
├── src/                           # Main source code folder
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   └── api.py                 # FastAPI application
│   ├── db/                        # Database operations
│   │   ├── __init__.py
│   │   ├── connection.py          # Database connection
│   │   ├── models.py              # SQLAlchemy ORM models
│   │   ├── rebuild.py             # Database rebuild
│   │   └── setup.py               # Database setup
│   ├── models/                    # Pydantic data models
│   │   ├── __init__.py
│   │   └── campground.py          # Campground data model
│   ├── scraper/                   # Web scraping modules
│   │   ├── __init__.py
│   │   ├── api_client.py          # API client
│   │   ├── scraper.py             # Main scraper functions
│   │   ├── data_processor.py      # Data processing
│   │   ├── browser_wrapper.py     # Browser-based scraping
│   │   ├── geocoding.py           # Address resolution
│   │   └── browser/               # Browser automation modules
│   │       ├── __init__.py
│   │       └── browser_scraper.py
│   ├── scheduler/                 # Scheduling modules
│   │   ├── __init__.py
│   │   ├── simple_scheduler.py    # Simple scheduler
│   │   └── job_scheduler.py       # Advanced job scheduler
│   └── __init__.py
├── main.py                        # Main entry point
├── improved_scrapers.py           # Improved scraper implementation
├── address_update_test.py         # Address update test
├── standalone_api.py              # Standalone API server
├── docker-compose.yml             # Docker Compose configuration
├── Dockerfile                     # Docker configuration
├── requirements.txt               # Python dependencies
└── README.md                      # Project documentation
```

## Data Model

The campground data model includes the following fields:

- **Basic Information:** id, type, name, links
- **Location Information:** latitude, longitude, region_name, administrative_area, nearest_city_name, address
- **Accommodation Details:** accommodation_type_names, bookable, camper_types, operator
- **Media:** photo_url, photo_urls, photos_count
- **Reviews:** rating, reviews_count
- **Price Information:** price_low, price_high
- **Additional Details:** availability_updated_at, slug

## Improved Scraper

The ImprovedDyrtScraper class has the following features to comprehensively collect all US campground data:

1. **Grid-Based Approach:**
   - US boundaries (approximate) are defined
   - The map is divided into NxN grid cells
   - Each cell is processed separately

2. **Pagination Support:**
   - Pagination is used to retrieve all results for each grid cell
   - A specific number of campgrounds are retrieved per page

3. **Progress Tracking:**
   - Progress is stored in a JSON file
   - Support for resuming interrupted operations
   - Tracking of processed cells

4. **Data Validation:**
   - Data validation with Pydantic models
   - Conversion of API responses to local models

5. **Address Resolution:**
   - Extraction of address information from latitude/longitude coordinates
   - Usage of Nominatim (OpenStreetMap) API
   - Retry mechanism

## Installation and Execution

### Requirements

- Python 3.10+
- PostgreSQL database
- Optional: Docker and Docker Compose

### Installation

1. **Development Environment:**

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Windows)
.venv\\Scripts\\activate
# OR (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

2. **Installation with Docker:**

```bash
# Run with Docker Compose
docker compose up --build
```

### Execution Options

```bash
# Initialize the database
python3 main.py --init-db

# Run the scraper once
python3 main.py --run-once

# Use the improved scraper
python3 main.py --improved

# Start the API server
python3 main.py --api --port 8080

```

### Command Line Parameters

- `--run-once`: Run the scraper once and exit
- `--browser`: Use browser-based scraper instead of API-based
- `--schedule`: Run the scraper on a schedule
- `--interval HOURS`: Interval in hours for scheduled runs
- `--init-db`: Initialize the database tables
- `--rebuild-db`: Rebuild the database (WARNING: Deletes all data!)
- `--api`: Start the API server
- `--port PORT`: Port for the API server
- `--update-addresses`: Update addresses for campgrounds without addresses
- `--address-batch-size`: Batch size for address updates
- `--grid-size`: Grid size for dividing the US map (NxN)
- `--max-pages`: Maximum pages to retrieve per grid cell
- `--items-per-page`: Items per page in API requests
- `--no-resume`: Don't resume from previous run, start fresh
- `--improved`: Use improved scraper for better coverage

## API Endpoints

The standalone API server and main API server offer several endpoints:

## Error Handling and Logging

The application has a comprehensive error handling and logging system:

- Retry mechanism for HTTP requests
- Error catching and logging
- Protection against unexpected API response formats
- Progress tracking and restart support

## SQL Query Issue Solution

In SQLAlchemy 2.0, raw SQL queries must be explicitly declared as text using the `text()` function:

```python
from sqlalchemy import text

# Correct usage:
db.execute(text(\"SELECT * FROM campgrounds\"))

# Incorrect usage:
db.execute(\"SELECT * FROM campgrounds\")  # Deprecated in SQLAlchemy 2.0
```

This change resolves the following error message:
```
{\"detail\":\"Textual SQL expression 'SELECT COUNT(*) FROM camp...' should be explicitly declared as text('SELECT COUNT(*) FROM camp...')\"}
```

## Docker Support

The project can be easily run with Docker and Docker Compose:

## Tips and Best Practices

1. **Efficient Data Extraction:**
   - Keep the grid_size parameter small for small tests (e.g., 2x2)
   - Increase the max_pages value for large data extractions
   - Adjust time.sleep() values to avoid overloading the API

2. **Database Management:**
   - Regularly back up the database when working with large datasets
   - Use indexing for efficient queries

3. **Debugging:**
   - Set the logging level to DEBUG for more detailed logs
   - Store unexpected API responses in the unexpected_response.json file

4. **Address Resolution:**
   - Apply rate limiting to avoid overusing the Nominatim API
   - Use the --address-batch-size parameter for bulk address updates

5. **API Usage:**
   - Adjust pagination parameters appropriately for large datasets
   - Use query parameters for custom filters

## Conclusion

The Dyrt Web Scraper project provides a comprehensive solution for automatically collecting, validating, and storing campground data across the United States. Its grid-based approach, pagination support, and progress tracking enable efficient processing of large amounts of data. The API server and scheduled tasks allow remote control of the scraper and planning regular updates.
