from selenium import webdriver

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

