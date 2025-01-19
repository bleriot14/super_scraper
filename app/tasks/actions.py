import logging
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.core.driver import get_driver
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger("web-scraper")


class WebScraper:
    def __init__(self, db_path='menu_data.db'):
        self.driver = get_driver()
        self.db_path = db_path

    def scrape_and_save_menu(self, worker_function,locator, is_loaded_locator, is_leaf, wait_time=0.5, initial_visited_categories=None, initial_located_categories=None):
        """
        Menü yapısını tarar ve bir dosyaya kaydeder.
        """
        worker_function(self.driver, locator, is_loaded_locator, is_leaf, wait_time, initial_visited_categories, initial_located_categories)

    def open_page(self, url, locator: tuple, definition: str, wait_time=3):
        """Open a URL in the browser and verify if the expected element is visible."""
        logger.info(f"Operation: {definition}")
        logger.info(f"Opening URL: {url}")
        self.driver.get(url)
        time.sleep(wait_time)
        try:
            self.check_element(locator, definition=f"Check element after opening URL: {url}")
            logger.info("Page loaded successfully and element is present")
        except TimeoutException:
            logger.warning(f"Page loaded but the expected element was not found. Definition: {definition}")


    def select_multiple(self, locator: tuple, definition: str):
        """
        Find all elements matching a locator and return their elements in a list.

        :param locator: Tuple containing the locator strategy and value (e.g., (By.CLASS_NAME, "example-class"))
        :param definition: A string describing the operation
        :return: A list of WebElements for the matching elements
        """
        logger.info(f"Operation: {definition}")
        by, value = locator
        logger.info(f"Finding all elements matching locator {by}: {value}")

        try:
            # Ana elementleri bul
            elements = self.driver.find_elements(by, value)
            logger.info(f"Found {len(elements)} elements matching locator {by}: {value}")

            result_elements = []
            for parent_element in elements:
                try:
                    # Alt elementleri bekle ve bul
                    child_element = WebDriverWait(parent_element, 2).until(
                        EC.presence_of_element_located((by, value))
                    )
                    result_elements.append(child_element)
                    logger.info(f"Child element found for parent: {parent_element}")
                except TimeoutException:
                    logger.warning(f"Timeout: Child elements might not have loaded before selection for parent: {parent_element}")
                except NoSuchElementException:
                    logger.warning(f"NoSuchElement: Child elements might not have loaded before selection for parent: {parent_element}")
                except Exception as e:
                    logger.error(f"An unexpected error occurred while finding child elements: {e}")

            return result_elements
        except Exception as e:
            logger.warning(f"Failed to select multiple elements: {e}. Definition: {definition}")
            return []

    def input_text(self, locator: tuple, text: str, definition: str, wait_time=5):
        """Wait for an input field to be visible and input text into it."""
        logger.info(f"Operation: {definition}")
        by, value = locator
        logger.info(f"Preparing to input text into element with {by}: {value}")
        try:
            element = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator)
            )
            element.clear()
            element.send_keys(text)
            logger.info(f"Successfully input text: '{text}' into element with {by}: {value}")
        except TimeoutException:
            logger.warning(f"Element not visible within {wait_time} seconds: {by} = {value}. Skipping input. Definition: {definition}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while inputting text: {e}. Definition: {definition}")

    def check_element(self, locator: tuple, definition: str, wait_time=5):
        """Explicit wait ile elementi kontrol et."""
        logger.info(f"Operation: {definition}")
        by, value = locator
        logger.info(f"Checking for element with {by}: {value}")
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located(locator)
            )
            WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located(locator)
            )
            logger.info("Element found and visible")
            return True
        except TimeoutException:
            logger.warning(f"Element not found within {wait_time} seconds: {by} = {value}. Definition: {definition}")
            return False

    def click(self, locator: tuple, definition: str, wait_time=5, expected_as_disappear=False):
        """Wait for an element to be clickable and perform a click. If expected_as_disappear is True, 
        repeatedly click until the element disappears or maximum retries are reached."""
        logger.info(f"Operation: {definition}")
        by, value = locator
        logger.info(f"Waiting to click element with {by}: {value}")

        try:
            if expected_as_disappear:
                retries = 0
                max_retries = 3

                while retries < max_retries:
                    try:
                        element = WebDriverWait(self.driver, wait_time).until(
                            EC.element_to_be_clickable(locator)
                        )
                        element.click()
                        logger.info(f"Click attempt {retries + 1} performed successfully")

                        # Wait for the element to disappear
                        WebDriverWait(self.driver, wait_time).until_not(
                            EC.presence_of_element_located(locator)
                        )
                        logger.info("Element disappeared after click")
                        return  # Exit the function as the element has disappeared
                    except TimeoutException:
                        retries += 1
                        logger.warning(f"Attempt {retries}: Element did not disappear within {wait_time} seconds.")

                logger.error(f"Element did not disappear after {max_retries} attempts: {by} = {value}. Definition: {definition}")
            else:
                element = WebDriverWait(self.driver, wait_time).until(
                    EC.element_to_be_clickable(locator)
                )
                element.click()
                logger.info("Click action performed successfully")

        except TimeoutException:
            logger.warning(f"Element not clickable within {wait_time} seconds: {by} = {value}. Skipping click. Definition: {definition}")
        except Exception as e:
            logger.error(f"An unexpected error occurred while clicking the element: {e}. Definition: {definition}")

    def get_elements(self, locator: tuple, definition: str):
        """Get a list of elements matching the locator."""
        logger.info(f"Operation: {definition}")
        by, value = locator
        logger.info(f"Getting elements with {by}: {value}")
        try:
            elements = self.driver.find_elements(by, value)
            logger.info(f"Found {len(elements)} elements")
            return elements
        except Exception as e:
            logger.warning(f"Failed to get elements: {e}. Definition: {definition}")
            return []

    def extract_attribute(self, elements, attribute="text", definition: str = ""):
        """Extract an attribute (or text) from a list of elements."""
        logger.info(f"Operation: {definition}")
        logger.info(f"Extracting attribute: {attribute}")
        extracted = []
        for element in elements:
            try:
                value = element.text if attribute == "text" else element.get_attribute(attribute)
                extracted.append(value)
            except Exception as e:
                logger.warning(f"Failed to extract attribute: {e}")
                extracted.append(None)
        return extracted

    def quit(self, definition: str = "Quit the browser"):
        """Close the driver and quit the browser."""
        logger.info(f"Operation: {definition}")
        logger.info("Quitting the browser")
        self.driver.quit()

        
    def close(self):
        """
        Veritabanı bağlantısını kapatır.
        """
        self.conn.close()
        logger.info("SQLite veritabanı bağlantısı kapatıldı.")

# Kullanım örneği:
# from app.tasks.actions import WebScraper
# scraper = WebScraper()
# scraper.open_page("https://example.com", (By.ID, "example-id"))
# elements = scraper.get_elements((By.CLASS_NAME, "example-class"))
# texts = scraper.extract_attribute(elements, "text")
# scraper.quit()