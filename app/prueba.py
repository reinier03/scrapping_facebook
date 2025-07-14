import dill
from f_src.chrome_driver import uc_driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.action_chains import ActionChains


d = uc_driver(True)

wait = WebDriverWait(d, 80)
user = 1234567
temp_dict = {}
temp_dict[user] = {}
a = ActionChains(d, 0)



with open(r"D:\Programacion\Proyectos personales\webscrapping\revolico_scrapping\user_archive\cookies.pkl", "rb") as file:
    c = dill.load(file)
    d.get("https://facebook.com/robots.txt")
    for i in c:
        d.add_cookie(i)


d.get("https://facebook.com")

driver = d


breakpoint()
