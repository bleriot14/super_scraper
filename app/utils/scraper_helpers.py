from app.core.driver import get_driver
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

