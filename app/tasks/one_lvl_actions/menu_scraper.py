import time
from collections import deque
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from datetime import datetime
from neo4j import GraphDatabase
import json
import os


def load_progress(visited_file, located_file):
    """
    Kaydedilmiş progress'i yükler.
    
    Args:
        visited_file (str): Ziyaret edilmiş kategorilerin bulunduğu dosya yolu
        located_file (str): Bulunmuş kategorilerin bulunduğu dosya yolu
    
    Returns:
        tuple: (visited_categories, located_categories) veya hata durumunda (None, None)
    """
    try:
        with open(visited_file, 'r') as f:
            visited_categories = set(json.load(f))
        
        with open(located_file, 'r') as f:
            located_list = json.load(f)
            # Convert the loaded data into proper tuples
            located_categories = deque()
            for item in located_list:
                if isinstance(item, list) and len(item) == 2:
                    # If item is already a list of [category, parent_url]
                    located_categories.append(tuple(item))
                elif isinstance(item, dict):
                    # If item is just a category dictionary
                    located_categories.append((item, None))
                else:
                    logging.warning(f"Unexpected item format in located_list: {item}")
                    continue
            
        logging.info(f"Progress loaded from {visited_file} and {located_file}")
        return visited_categories, located_categories
    except Exception as e:
        logging.error(f"Progress yüklenirken hata oluştu: {e}")
        return None, None

def scrape_menu(driver, locator, is_loaded_locator, is_leaf, wait_time=10, visited_file=None, located_file=None):
    """
    Breadth-First Search kullanarak menü yapısını tarar ve bulunan düğümleri Neo4j'ye kaydeder.

    :param driver: Selenium WebDriver instance  
    :param locator: Menü elemanlarını tanımlayan locator (tuple olarak, örneğin (By.CSS_SELECTOR, "selector"))
    :param is_loaded_locator: Sayfanın yüklenip yüklenemdiğini anlamak için kullanılan element
    :param is_leaf: Bir düğümün yaprak olup olmadığını kontrol eden fonksiyon  
    :param wait_time: Elementlerin yüklenmesini beklerken maksimum süre
    :param visited_file: Ziyaret edilmiş kategorilerin yüklenecegi dosya yolu
    :param located_file: Bulunmuş kategorilerin yüklenecegi dosya yolu
    """
    # Logging yapılandırması
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Neo4j bağlantısı için gerekli bilgileri burada tanımlayın
    neo4j_uri = "bolt://localhost:7687"  # Neo4j URI
    neo4j_user = "neo4j"                # Kullanıcı adı
    neo4j_password = "password"         # Şifre
    
    # Neo4j driver'ı başlat
    driver_graph = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    # Progress dosyaları için timestamp oluştur
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    progress_dir = "scraping_progress"
    os.makedirs(progress_dir, exist_ok=True)
    
    # Progress dosya yollarını belirle
    save_visited_file = f"{progress_dir}/{timestamp}_visited.json"
    save_located_file = f"{progress_dir}/{timestamp}_located.json"
    
    def save_progress(visited, located):
        """Progress'i dosyaya kaydet"""
        with open(save_visited_file, 'w') as f:
            json.dump(list(visited), f)
        
        with open(save_located_file, 'w') as f:
            located_list = [(cat, parent_url) for cat, parent_url in located]
            json.dump(located_list, f)
        
        logging.info(f"Progress saved to {save_visited_file} and {save_located_file}")

    def create_category(tx, category):
        """
        Neo4j'ye kategori düğümü ekler.
        """
        tx.run("""
            MERGE (c:Categoryv2 {url: $url})
            SET c.name = $name,
                c.level = $level,
                c.timestamp = $timestamp
        """, name=category['category_name'], level=category['level'], url=category['url'], timestamp=category['timestamp'])
    
    def create_relationship(tx, parent_url, child_url):
        """
        Neo4j'ye kategori ilişkisi ekler.
        """
        tx.run("""
            MATCH (parent:Categoryv2 {url: $parent_url})
            MATCH (child:Categoryv2 {url: $child_url})
            MERGE (parent)-[:HAS_SUBCATEGORY]->(child)
        """, parent_url=parent_url, child_url=child_url)
    
    # Başlangıç kategorilerini yükle
    if visited_file and located_file:
        visited_categories, located_categories = load_progress(visited_file, located_file)
        if visited_categories is None or located_categories is None:
            visited_categories = set()
            located_categories = deque()
    else:
        visited_categories = set()
        located_categories = deque()
    
    # Eğer located_categories boşsa, root düğümü ekle
    if not located_categories:
        root = {
            'category_name': 'Root',
            'level': 0,
            'url': driver.current_url,
            'timestamp': datetime.now().isoformat()
        }
        located_categories.append((root, None))  # (kategori, parent_url)

    with driver_graph.session() as session:
        progress_counter = 0
        while located_categories:
            current_category, parent_url = located_categories.popleft()
            category_id = current_category['url']
            
            if category_id in visited_categories:
                continue
            
            logging.info(f"İşleniyor: {current_category['category_name']} (Seviye: {current_category['level']})")
            
            try:
                driver.get(current_category['url'])
                WebDriverWait(driver, wait_time).until(EC.presence_of_element_located(is_loaded_locator))
            except TimeoutException:
                logging.error(f"Sayfa yüklenemedi: {current_category['url']}")
                visited_categories.add(category_id)
                continue
            
            # Neo4j'ye düğüm ekleme
            try:
                session.write_transaction(create_category, current_category)
                if parent_url:
                    session.write_transaction(create_relationship, parent_url, current_category['url'])
            except Exception as e:
                logging.error(f"Neo4j'e kategori eklenirken hata oluştu: {e}")
                visited_categories.add(category_id)
                continue
            
            if is_leaf(driver):
                logging.info(f"Yaprak düğüm: {current_category['category_name']}")
                visited_categories.add(category_id)
                continue
            
            try:
                elements = WebDriverWait(driver, wait_time).until(EC.presence_of_all_elements_located(locator))
            except TimeoutException:
                logging.warning(f"Alt kategoriler bulunamadı: {current_category['category_name']}")
                visited_categories.add(category_id)
                continue
            
            for elem in elements:
                try:
                    if elem.is_enabled() and elem.is_displayed():
                        category_name = elem.text.strip()
                        category_url = elem.get_attribute('href')
                        if not category_url:
                            logging.warning(f"URL bulunamadı: {category_name}")
                            continue
                        if category_url in visited_categories:
                            continue
                        # Linkin yüklendiğini kontrol et
                        try:
                            WebDriverWait(driver, wait_time).until(EC.element_to_be_clickable(locator))
                        except TimeoutException:
                            logging.warning(f"Element tıklanabilir değil: {category_name}")
                            continue
                        category = {
                            'category_name': category_name,
                            'level': current_category['level'] + 1,
                            'url': category_url,
                            'timestamp': datetime.now().isoformat()
                        }
                        located_categories.append((category, current_category['url']))
                except Exception as e:
                    logging.error(f"Alt kategori işlenemedi: {e}")
            
            visited_categories.add(category_id)
            
            # Her 10 işlemde bir progress'i kaydet
            progress_counter += 1
            if progress_counter % 10 == 0:
                save_progress(visited_categories, located_categories)
        
        # Son durumu kaydet
        save_progress(visited_categories, located_categories)
        logging.info("Tüm kategoriler işlendi.")
    
    # Neo4j sürücüsünü kapat
    driver_graph.close()
