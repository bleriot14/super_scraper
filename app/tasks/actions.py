import logging
import time
from selenium.common.exceptions import TimeoutException, NoSuchElementException,ElementClickInterceptedException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.core.driver import get_driver
from selenium.webdriver.support.ui import WebDriverWait
import sqlite3



logger = logging.getLogger("web-scraper")


class WebScraper:
    def __init__(self,db_path='menu_data.db'):
        self.driver = get_driver()
        self.visited_urls=set()
        self.visited_urls = set()
        self.db_path = db_path
        self._setup_database()

    def _setup_database(self):
        """
        SQLite veritabanına bağlanır ve gerekli tabloyu oluşturur.
        """
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Tabloyu oluştur
        columns = ', '.join([f"hierarchy_{i} TEXT" for i in range(1, 21)])
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            href TEXT,
            {columns}
        );
        """
        self.cursor.execute(create_table_query)
        self.conn.commit()
        logger.info("SQLite veritabanı ve tablo hazırlandı.")


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
    def scrape_menu(self, locator_list, exit_function, wait_time=5):
        """
        Tüm menü çubuğu ve alt menüler taranarak en alt seviyedeki menü elemanlarının bilgilerini SQLite veritabanına kaydeder.
        
        :param locator_list: Menü çubuğu elementlerini tanımlayan locator'ların listesi
        :param exit_function: En alt menü seviyesine ulaşılıp ulaşılmadığını kontrol eden bir fonksiyon
        :param wait_time: Elementlerin yüklenmesini beklemek için kullanılacak süre
        """
        def traverse_menu(current_path, current_level=0):
            for locator in locator_list:
                try:
                    elements = WebDriverWait(self.driver, wait_time).until(
                        EC.presence_of_all_elements_located(locator)
                    )
                    logger.info(f"Found {len(elements)} elements using locator: {locator}")
                except TimeoutException:
                    logger.warning(f"No elements found for locator: {locator}")
                    continue

                for index in range(len(elements)):
                    try:
                        # Elementleri yeniden bul
                        refreshed_elements = WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_all_elements_located(locator)
                        )
                        if index >= len(refreshed_elements):
                            logger.warning("Element listesi değişti, atlanıyor.")
                            continue
                        element = refreshed_elements[index]

                        # Tıklanabilirliği kontrol et
                        WebDriverWait(self.driver, wait_time).until(
                            EC.element_to_be_clickable(locator)
                        )
                        element_text = element.text.strip()
                        logger.info(f"Clicking on '{element_text}' at level {current_level}")
                        element.click()

                        # Yeni sayfanın yüklenmesini bekle
                        WebDriverWait(self.driver, wait_time).until(
                            EC.staleness_of(element)
                        )
                        WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_all_elements_located(locator_list[0])
                        )

                        new_url = self.driver.current_url
                        if new_url in self.visited_urls:
                            logger.info(f"URL '{new_url}' has already been visited. Skipping.")
                            self.driver.back()
                            continue
                        self.visited_urls.add(new_url)

                        if exit_function(self.driver):
                            href = self.driver.current_url
                            # Hierarchy'yi 20 sütuna dağıt
                            hierarchy_columns = [None] * 20
                            for i, level in enumerate(current_path + [element_text]):
                                if i < 20:
                                    hierarchy_columns[i] = level
                                else:
                                    logger.warning(f"Hiyerarşi seviyesi {i+1} aşılmış. Fazladan seviyeler atlanacak.")

                            # Veritabanına ekle
                            insert_query = f"""
                            INSERT INTO menu (url, href, {', '.join([f'hierarchy_{i}' for i in range(1, 21)])})
                            VALUES (?, ?, {', '.join(['?'] * 20)});
                            """
                            data = [new_url, href] + hierarchy_columns
                            self.cursor.execute(insert_query, data)
                            self.conn.commit()
                            logger.info(f"Reached end-level menu item: {element_text} with href: {href}")
                        else:
                            traverse_menu(current_path + [element_text], current_level + 1)

                        # Geri dön
                        self.driver.back()
                        WebDriverWait(self.driver, wait_time).until(
                            EC.presence_of_all_elements_located(locator_list[0])
                        )
                        logger.info("Navigated back to previous menu")
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException) as e:
                        logger.error(f"Error processing element '{element_text}' at level {current_level}: {e}. Skipping.")
                        continue
                    except Exception as e:
                        logger.error(f"Unexpected error: {e}. Skipping.")
                        continue

        traverse_menu(current_path=[])
        
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
