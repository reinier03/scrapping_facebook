from f_src.chrome_driver import uc_driver
from selenium.webdriver.support.ui import WebDriverWait

class scrapper:

    driver = uc_driver(True)
    wait = WebDriverWait(driver, 30)
    wait_s = WebDriverWait(driver, 8)