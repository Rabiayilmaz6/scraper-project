# The Dyrt Web Scraper

## Overview

This application scrapes campground data from The Dyrt website (https://thedyrt.com/search) and stores it in a PostgreSQL database. The scraper leverages The Dyrt's map interface, which exposes latitude/longitude and other campground data through API requests.

## Features

- **Data Extraction**: Extracts comprehensive campground data from The Dyrt's API
- **Database Integration**: Stores data in PostgreSQL with proper schema and validation
- **Data Validation**: Validates data using Pydantic models
- **Scheduler**: Cron-like scheduling for regular updates
- **Update Mechanism**: Updates existing records when new data is available
- **Error Handling**: Comprehensive error handling with retry mechanisms
- **API**: RESTful API endpoints to control the scraper and access data
- **Geocoding**: Resolves addresses from latitude/longitude coordinates

## Architecture

The application is structured into several modules:

- **db**: Database connection and models
- **models**: Pydantic models for data validation
- **scraper**: Core scraper functionality
- **scheduler**: Scheduling system for regular updates
- **api**: RESTful API endpoints

## Installation

### Prerequisites

- Python 3.10+
- PostgreSQL database
- Docker and Docker Compose (optional)

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd scraper_project
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the environment variables (or use .env file):

```bash
export DB_URL=postgresql://user:password@localhost:5432/case_study
```

## Usage

### Running with Python

Initialize the database:

```bash
python main.py --init-db
```

Run the scraper once:

```bash
python main.py --run-once
```

Run the scraper on a schedule:

```bash
python main.py --schedule --interval 12  # Run every 12 hours
```

Start the API server:

```bash
python main.py --api --port 8000
```

### Running with Docker Compose

Start the entire stack (PostgreSQL and scraper):

```bash
docker compose up
```

## API Documentation

When the API server is running, you can access the documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### API Endpoints

- `GET /campgrounds`: Get a list of campgrounds
- `GET /campgrounds/{campground_id}`: Get a specific campground
- `POST /scraper/run`: Trigger the scraper to run
- `POST /scheduler/start`: Start the scheduler
- `POST /scheduler/stop`: Stop the scheduler
- `GET /scheduler/status`: Get the scheduler status

## Design Decisions

1. **ORM vs. Raw SQL**: SQLAlchemy was chosen as the ORM to simplify database operations and provide better integration with Python objects.

2. **API Framework**: FastAPI was selected for its performance, automatic documentation, and ease of use.

3. **Scheduling**: Two scheduling options are provided:
   - APScheduler: More powerful and flexible
   - Schedule: Simpler and easier to use

4. **Error Handling**: The application includes comprehensive error handling with retry mechanisms to ensure robustness.

5. **Geocoding**: The application uses the Nominatim service (OpenStreetMap) to resolve addresses from latitude/longitude coordinates.

## Future Improvements

- Implement multithreading or asynchronous processing for improved performance
- Add user authentication for the API
- Implement data analytics features
- Add more comprehensive logging and monitoring
- Expand the API with more filtering and sorting options

## Contact

For questions or support, please contact: info@smart-maple.com
