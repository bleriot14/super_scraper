#!/bin/bash

# Script to create the modular project structure for the web scraper

# Define base directory
BASE_DIR="project"

# Define directories
DIRS=(
    "$BASE_DIR"
    "$BASE_DIR/app"
    "$BASE_DIR/app/routers"
    "$BASE_DIR/app/core"
    "$BASE_DIR/app/utils"
    "$BASE_DIR/tests"
)

# Define files with their initial content
declare -A FILES=(
    ["$BASE_DIR/app/__init__.py"]=""
    ["$BASE_DIR/app/main.py"]='from fastapi import FastAPI
from app.routers import scraper
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(title="Web Scraper API", version="1.0.0")

app.include_router(scraper.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
'
    ["$BASE_DIR/app/routers/__init__.py"]=""
    ["$BASE_DIR/app/routers/scraper.py"]='from fastapi import APIRouter
from app.utils.scraper_helpers import open_page, extract_title
from pydantic import BaseModel

router = APIRouter(prefix="/scraper", tags=["Scraper"])

class ScraperTask(BaseModel):
    url: str

@router.post("/run")
async def run_scraper(task: ScraperTask):
    driver = open_page(task.url)
    try:
        title = extract_title(driver)
        return {"url": task.url, "title": title}
    except Exception as e:
        return {"message": "Error during scraping", "details": str(e)}
    finally:
        driver.quit()
'
    ["$BASE_DIR/app/core/__init__.py"]=""
    ["$BASE_DIR/app/core/driver.py"]='from selenium import webdriver

SELENIUM_HUB_URL = "http://192.168.1.4:4444/wd/hub"

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Remote(
        command_executor=SELENIUM_HUB_URL,
        options=options
    )
    return driver
'
    ["$BASE_DIR/app/core/logging_config.py"]='import logging
import os

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("web-scraper")
    if int(os.getenv("NETWORK_DEBUG", 1)):
        logger.setLevel(logging.DEBUG)
'
    ["$BASE_DIR/app/utils/__init__.py"]=""
    ["$BASE_DIR/app/utils/scraper_helpers.py"]='from app.core.driver import get_driver
import logging
import time

logger = logging.getLogger("web-scraper")

def open_page(url):
    logger.info(f"Opening URL: {url}")
    driver = get_driver()
    driver.get(url)
    logger.info("Page loaded successfully")
    return driver

def extract_title(driver):
    logger.info("Extracting page title")
    time.sleep(2)
    title = driver.title
    logger.info(f"Page title: {title}")
    return title
'
    ["$BASE_DIR/tests/__init__.py"]=""
    ["$BASE_DIR/tests/test_scraper.py"]=""
    ["$BASE_DIR/requirements.txt"]='fastapi
uvicorn
selenium
pydantic
'
    ["$BASE_DIR/Dockerfile"]='FROM python:3.9-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "app.main"]
'
)

# Create directories
for dir in "${DIRS[@]}"; do
    mkdir -p "$dir"
done

# Create files with initial content
for file in "${!FILES[@]}"; do
    echo "${FILES[$file]}" > "$file"
done

# Completion message
echo "Project structure created successfully in $BASE_DIR."
