import logging
import os

def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("web-scraper")
    if int(os.getenv("NETWORK_DEBUG", 1)):
        logger.setLevel(logging.DEBUG)

