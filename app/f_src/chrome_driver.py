from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import seleniumbase
import os


def anadir_opciones(o, container=False, mobile=False):
    
    
    o.add_argument("--disable-web-security")
    o.add_argument("--disable-extensions")
    o.add_argument("--disable-notifications")
    o.add_argument("--ignore-certificate-errors")
    o.add_argument("--no-sandbox")
    o.add_argument("--log-level=3") #para no mostrar nada en la terminal
    o.add_argument("--allow-running-insecure-content")
    o.add_argument("--no-default-browser-check")
    o.add_argument("--no-first-run")
    o.add_argument("--no-proxy-server")
    o.add_argument("--disable-infobars")
    o.add_argument("--disable-blink-features=AutomationControlled")
    o.add_argument("--disable-features=ChromeWhatsNewUI")

    # o.add_argument("--single-process")
    # o.add_argument("--disable-dev-shm-usage")
    # o.add_argument("--disable-gpu")
    # o.add_argument("--window-size=393,851")
    # o.add_argument("--disable-extensions")
    # o.add_argument("--disable-application-cache")                
    # o.add_argument("--enable-javascript")                
    # o.add_argument("--disable-infobars")
    
    
        
    if container:
        o.add_argument("--headless=new")

    if mobile:
        # user-agent mobile
        o.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.116 Mobile Safari/537.36")        

    else:
        o.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/135.0.0.0 Safari/537.36")
        
        

        # o.add_argument("--disable-software-rasterizer")
        # o.add_argument("--use-gl=swiftshader")
        # o.add_argument("--disable-gpu-sandbox")
        # o.add_argument("--no-zygote")


    prefers = {"profile.default_content_setting_values.notifications": 2,
            "intl.accept_languages": ["es-ES", "es"],
            "credentials_enable_service": False}
    


    o.add_experimental_option("prefs", prefers)
    
    
    return o
    

def sb_driver():
    

    # options = Options()
    # options.add_argument("--headless=new")  # O usa "--headless" si hay errores con "new"
    # options.add_argument("--no-sandbox")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-gpu")
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument("--disable-software-rasterizer")
    driver = seleniumbase.Driver(
    browser="chrome",
    uc=True,
    headless=True)
    
    # driver = seleniumbase.Driver("chrome", locale_code="es", uc=True, headless=False)
        
    return driver


def selenium_driver():
    o = Options()

    o = anadir_opciones(o)
    
    #parametros a omitir en el inicio de chromedriver
    exp_opt= [
        "enable-automation",
        "ignore-certificate-errors",
        "enable-logging"
    ]
    
    o.add_experimental_option("excludeSwitches", exp_opt)
    o.add_experimental_option("excludeSwitches" , ["enable-automation"])
    o.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/135.0.0.0 Safari/537.36")

    s = Service("D:\\chromedriver.exe")

    driver = webdriver.Chrome(o , s)

    return driver


def uc_driver(mobile=False):

    o = uc.ChromeOptions()
    
    #desactivar el guardado de credenciales
    o.add_argument("--password-store=basic")
    #estas opciones son copiadas de arriba
    
    
    o.add_experimental_option(
        "prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled" : False
        }
    )
    
    

    
    if os.name != "nt":
        o = anadir_opciones(o, container=True , mobile=mobile)

        driver = uc.Chrome(
            options=o,
            log_level=3,
            keep_alive=True,
            driver_executable_path='/usr/lib/chromium/chromedriver',
            # driver_executable_path=r'C:\Users\Reima\AppData\Local\Programs\Python\Python312\Lib\site-packages\seleniumbase\drivers\chromedriver.exe'
        )

    else:
        o = anadir_opciones(o, mobile=mobile)
        driver = uc.Chrome(
            options=o,
            log_level=3,
            keep_alive=True,
            driver_executable_path=r'C:\Users\Reima\AppData\Local\Programs\Python\Python312\Lib\site-packages\seleniumbase\drivers\chromedriver.exe'
        )
    
    
    if mobile:
        driver.set_window_rect(height=851, width=300)
        driver.set_window_position(x=0, y=0)


    return driver



