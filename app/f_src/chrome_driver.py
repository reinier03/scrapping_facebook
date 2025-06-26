from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import seleniumbase
import os


def anadir_opciones(o, container=False):
    
    
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
    
    o.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, como Gecko) Chrome/135.0.0.0 Safari/537.36")
    
        
    if container:
        o.add_argument("--headless=new")
        # o.add_argument("--headless")
        # o.add_argument("--user-agent=Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.7151.116 Mobile Safari/537.36")        
        
        o.add_argument("--single-process")
        o.add_argument("--disable-dev-shm-usage")
        o.add_argument("--disable-gpu")
        o.add_argument("--window-size=393,851")
        o.add_argument("--disable-extensions")
        o.add_argument("--disable-software-rasterizer")
        o.add_argument("--disable-application-cache")                
        o.add_argument("--enable-javascript")                
        o.add_argument("--disable-infobars")
        o.add_argument("--js-flags='--max-old-space-size=2048'")


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


def uc_driver():

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
    
    o = anadir_opciones(o, True)
    
    driver = uc.Chrome(
        use_subprocess=False,
        options=o,
        log_level=3,
        keep_alive=True,
        driver_executable_path='/usr/lib/chromium/chromedriver'
        # driver_executable_path=r'C:\Users\Reima\AppData\Local\Programs\Python\Python312\Lib\site-packages\seleniumbase\drivers\chromedriver.exe'
    )
    
    if os.name != "nt":
        set_device_metrics_override = dict({"width": 375, "height": 812, "deviceScaleFactor": 50, "mobile": True})
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', set_device_metrics_override) 
        
    return driver




