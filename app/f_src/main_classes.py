from f_src.chrome_driver import uc_driver
from selenium.webdriver.support.ui import WebDriverWait
import os

class scrapper:

    driver = uc_driver(True)
    
    if os.name == "nt":
        wait = WebDriverWait(driver, 80)
    else:
        wait = WebDriverWait(driver, 30)

    wait_s = WebDriverWait(driver, 8)
    temp_dict = {}