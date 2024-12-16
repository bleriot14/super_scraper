from app.tasks.actions import open_page, click, get_elements, extract_attribute

def scrape_titles(url, title_selector):
    """Task: Open a page and scrape titles."""
    driver = open_page(url)
    try:
        elements = get_elements(driver, title_selector)
        titles = extract_attribute(elements, attribute="text")
        return titles
    finally:
        driver.quit()

def scrape_with_click(url, first_click_selector, second_selector):
    """Task: Open a page, click an element, and scrape content."""
    driver = open_page(url)
    try:
        click(driver, first_click_selector)
        elements = get_elements(driver, second_selector)
        content = extract_attribute(elements, attribute="text")
        return content
    finally:
        driver.quit()
