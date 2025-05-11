FROM python:3.10-slim

WORKDIR /src

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    wget \
    gnupg \
    libgconf-2-4 \
    ca-certificates \
    libglib2.0-0 \
    libnss3 \
    libxss1 \
    libasound2 \
    libxtst6 \
    xvfb \
    libgbm1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/src
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Create a non-root user to run the application
RUN useradd -m appuser && chown -R appuser:appuser /src
USER appuser

# Command to run when the container starts
# Default: Initialize the database and run the browser-based scraper
CMD ["python", "main.py", "--init-db", "--run-once", "--browser"]
