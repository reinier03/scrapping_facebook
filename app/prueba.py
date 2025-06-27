import dill
from f_src.chrome_driver import uc_driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

d = uc_driver(True)

wait = WebDriverWait(d, 80)
user = 1234567
temp_dict = {}
temp_dict[user] = {}


d.get("https://facebook.com")


breakpoint()