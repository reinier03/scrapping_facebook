from f_src.chrome_driver import uc_driver
from selenium.webdriver.support.ui import WebDriverWait
from usefull_functions import *
import time
import os

class scrapper:

    driver = uc_driver(True)
    
    if os.name == "nt":
        wait = WebDriverWait(driver, 80)
    else:
        wait = WebDriverWait(driver, 30)

    wait_s = WebDriverWait(driver, 8)
    temp_dict = {}



class Usuario:

    def __init__(self, id, telegram_id):
        self.id = id
        self.telegram_id = telegram_id
        self.folder = user_folder(telegram_id)
        self.publicaciones: list[Publicacion] = None
        self.cookies: list[Cookies] = None
        self.temp_dict = {}


    def __setattr__(self, name, value):
        self.temp_dict[name] = value

class Cookies:

    def __init__(self, id_usuario, cookies_list, cookies_path):
        self.cookies_dict = cookies_list
        self.id_usuario = id_usuario
        self.cookies_path = cookies_path
        self.cuentas = None



class Publicacion:

    def __init__(self, id_usuario: int, texto: str, adjuntos: list, titulo: str):
        self.id_usuario = id_usuario
        self.texto = texto
        self.adjuntos = adjuntos
        self.titulo = titulo
        self.id = "p{}-{}".format(id_usuario, time.time())