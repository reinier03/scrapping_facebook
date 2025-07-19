from f_src.chrome_driver import uc_driver
from selenium.webdriver.support.ui import WebDriverWait
from f_src.usefull_functions import *
import time
import os
import threading

class scrapper:

    driver = uc_driver(True)
    
    if os.name == "nt":
        wait = WebDriverWait(driver, 80)
    else:
        wait = WebDriverWait(driver, 30)

    wait_s = WebDriverWait(driver, 8)
    temp_dict = {}



class Usuario:

    def __init__(self, telegram_id):
        self.id = time.time()
        self.telegram_id = telegram_id
        self.folder = user_folder(telegram_id)
        self.publicaciones: list[Publicacion] = None
        self.cookies: list[Cookies] = None
        self.temp_dict = {}
        


    def __setattr__(self, name, value):
        self[name] = value

class Cookies:

    def __init__(self, id_usuario, cookies_list, cookies_path):
        self.cookies_dict = cookies_list
        self.id_usuario = id_usuario
        self.cookies_path = cookies_path
        self.cuentas = []



class Publicacion:

    def __init__(self, id_usuario: int):
        self.id_usuario = id_usuario
        self.id_publicacion = False
        self.texto = False
        self.adjuntos = []
        self.titulo = False




class MediaGroupCollector:

    def __init__(self, user_id, telegram_id):
        self.user_id = user_id
        self.telegram_id = telegram_id
        self.timer = None
        self.fotos = []
        self.TIMEOUT = 8


