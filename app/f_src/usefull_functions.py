import time
import sys
import os
from f_src import bot_handlers
import telebot
import re
from traceback import format_exc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import Chrome
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from tempfile import gettempdir
import cv2
import numpy
import pyautogui


def liberar_cola(scrapper, message, bot, cola):
    cola["uso"] = False      

    for i in cola["cola_usuarios"]:
        try:
            bot.send_message(i, "Ya estoy disponible para Publicar :D\n\nÚsame antes de que alguien más me ocupe")
        except:
            pass

    scrapper.temp_dict[message.from_user.id] = {}
    return

def obtener_grupos(scrapper, user):

    #forma antigua---
    #scrapper.temp_dict[user]["lista_grupos"] = scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[class="m bg-s2"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"]')[scrapper.temp_dict[user]["padre"]].find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-focusable="true"][data-type="container"]')
    try:
        scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Create a group")]')))
    
    except:
        load(scrapper, "https://m.facebook.com/groups/")
        scrapper.temp_dict[user]["e"] = scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Create a group")]')))

    scrapper.temp_dict[user]["e"] = scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "Create a group")]')

    for i in range(4):
        scrapper.temp_dict[user]["e"] = scrapper.temp_dict[user]["e"].find_element(By.XPATH, '..')


    return scrapper.temp_dict[user]["e"].find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-focusable="true"][data-type="container"]')

def if_cambio(scrapper, user):
    
    
    for i in range(10):
        scrapper.temp_dict[user]["captura"] = numpy.array(pyautogui.screenshot(os.path.join(str(user_folder(user)), "prueba.png")))

        if numpy.sum(cv2.absdiff(scrapper.temp_dict["original"] , scrapper.temp_dict[user]["captura"])) > scrapper.temp_dict["original"].shape[1] * scrapper.temp_dict["original"].shape[0] * 3 * 255 * 0.15:
            os.remove(os.path.join(str(user_folder(user)), "prueba.png"))
            os.remove(os.path.join(str(user_folder(user)), "original.png"))
            del scrapper.temp_dict[user]["captura"]
            del scrapper.temp_dict["original"]
            return True
        
        else:
            time.sleep(5)



    raise Exception("No se encontraron cambios en la GUI para que apareciera la ventana de la selección de fotos")


def envia_fotos_gui(scrapper, user, photo_path):
    scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "hotos")]')))

    if os.path.isfile(os.path.join(str(user_folder(user)), "original.png")):
        os.remove(os.path.join(str(user_folder(user)), "original.png"))

    scrapper.temp_dict["original"] = numpy.array(pyautogui.screenshot(os.path.join(str(user_folder(user)), "original.png")))

    
    scrapper.driver.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]').click()

    
    
    if if_cambio(scrapper, user) == True:
        if os.name != "nt":
            pyautogui.write(photo_path).replace("\\", "/")

        else:
            pyautogui.write(photo_path).replace("/", "\\")

        pyautogui.press("tab")
        pyautogui.press("tab")
        pyautogui.press("enter")


        time.sleep(2)

def envia_fotos_input(scrapper, user, photo_path):
    
    scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(@aria-label, "hotos")]')))

    try:
        scrapper.driver.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]').click()
    except:
        scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "hotos")]').click()

    scrapper.driver.find_element(By.XPATH, '//input').send_keys(photo_path)
    
    return True
    
    # try:
    #     scrapper.driver.execute_script('arguments[0].removeAttribute("data-client-focused-component")', scrapper.driver.find_element(By.XPATH, '//*[contains(@data-client-focused-component, "true")]'))
    # except:
    #     pass

    # scrapper.driver.execute_script('arguments[0].setAttribute("accept", "image/jpeg"); arguments[0].setAttribute("multiple", "true")', scrapper.driver.find_element(By.XPATH, '//input'))


    # scrapper.driver.execute_script('arguments[0].setAttribute("data-client-focused-component", "true")', scrapper.driver.find_element(By.XPATH, '//*[contains(@aria-label, "hotos")]'))


    # scrapper.driver.execute_script('arguments[0].setAttribute("width", "50px")', scrapper.driver.find_element(By.XPATH, '//input'))

    # scrapper.driver.execute_script('arguments[0].setAttribute("height", "50px")', scrapper.driver.find_element(By.XPATH, '//input'))
    
    # scrapper.driver.execute_script('arguments[0].setAttribute("display", "block")', scrapper.driver.find_element(By.XPATH, '//input'))

    # scrapper.driver.execute_script('arguments[0].setAttribute("style", "display: block; width: 100px; height: 100px; text: Hola")', scrapper.driver.find_element(By.XPATH, '//input'))

    # scrapper.driver.find_element(By.XPATH, '//input').text

    # scrapper.driver.find_element(By.CSS_SELECTOR, 'h2').click()

    # time.sleep(1)

    # scrapper.temp_dict[user]["a"].send_keys_to_element(scrapper.driver.find_element(By.XPATH, '//input'), photo_path).perform()
    # scrapper.driver.find_element(By.XPATH, '//input').send_keys(photo_path)
    
    

def load(scrapper, url):

        
    if os.name == "nt":
        try:
            scrapper.driver.get(url)
        except:
            pass
        
        while True:
            try:
                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                break
            except:
                pass
            
    else:
        scrapper.driver.get(url)
            
    
    
    return 
        

def if_cancelar(scrapper, user, bot):
    if scrapper.temp_dict[user].get("cancel"):
        bot.send_message(user, "Operación cancelada :(")
        give_error(bot, scrapper.driver, user, "no", False)

    return "ok"
        

def hacer_scroll(driver: Chrome, user: int, temp_dict: dict, grupos: list , elemento, pasos: int, esperar = 1.3):

    #a partir de los ultimos 11 elementos el scroll es inútil
    if len(grupos) <= 11 or pasos == 0:
        if esperar:
            time.sleep(esperar)

        return "ok"

    temp_dict[user]["y_scroll"] = elemento.location["y"] - (elemento.rect["height"] * 3)
    temp_dict[user]["y_scroll"] = temp_dict[user]["y_scroll"] // pasos
    

    for i in range(int(pasos)):


        temp_dict[user]["a"].scroll_by_amount(0, temp_dict[user]["y_scroll"]).perform()

        if esperar:
            time.sleep(esperar)


    del temp_dict[user]["y_scroll"]

    return "ok"

def give_error(bot, driver, user, texto, foto=True):
    if foto:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del Error")

    raise Exception(texto)

def limpiar(driver: Chrome):
    a = ActionChains(driver, 0)
    """Limpia el cache periódicamente"""
    driver.switch_to.new_window()
    driver.get('chrome://settings/clearBrowserData')
    ActionChains(driver, 0).send_keys(Keys.TAB, Keys.ENTER).perform()
    time.sleep(2)  # Espera a que limpie
    
    driver.close()
    
    if len(driver.window_handles) > 1:
        for tab in driver.window_handles:
            if tab == driver.window_handles[0]:
                continue
                
            driver.switch_to.window(tab)
            driver.close()
    
    driver.switch_to.window(driver.window_handles[0])
    return "ok"


def clear_doom(driver: Chrome, hacer_limpieza=True):
    #https://stackoverflow.com/questions/73604732/selenium-webdriverexception-unknown-error-session-deleted-because-of-page-cras
    
    # driver.execute_script('document.body.innerHTML = ";"')
    
    #
    try:
        driver.execute_script('document.querySelectorAll("div.x78zum5.xdt5ytf.x1n2onr6.xat3117.xxzkxad").forEach(e => e.remove());')
        
    except:
        pass
    
    try:
        driver.execute_script('document.querySelectorAll("div[role=main]").forEach(e => e.remove());')
    except:
        pass
    
    if hacer_limpieza:
        limpiar(driver)
    
    return "ok"

def comprobar_BD(collection):
    try:
        collection.count_documents({})
        return "ok"
    
    except Exception as e:
        try:
            if re.search('error=.*timeout', e.args[0]).group().split('(')[1]:
                raise Exception("No hay conexión con la base de datos!" + "\n\nDescripción\n" + re.search('error=.*timeout', e.args[0]).group().split('(')[1])
        except:
            pass
        
        raise Exception("Conecta la Base de Datos!\n\nDescripción del error:\n" + format_exc())

def info_message(texto, bot:telebot.TeleBot, temp_dict, user, mensaje_obj=False , markup = False):
    if mensaje_obj:
        if not markup:
            temp_dict[user]["info"] = bot.edit_message_text("🆕 Mensaje de Información\n\n" + texto, chat_id=user, message_id=temp_dict[user]["info"].message_id)
        
        else:
            temp_dict[user]["info"] = bot.edit_message_text("🆕 Mensaje de Información\n\n" + texto, chat_id=user, message_id=temp_dict[user]["info"].message_id, reply_markup=markup)
    
    else:
        if not markup:
            temp_dict[user]["info"] = bot.send_message(user, "🆕 Mensaje de Información\n\n" + texto)
        
        else:
            temp_dict[user]["info"] = bot.send_message(user, "🆕 Mensaje de Información\n\n" + texto, reply_markup=markup)
            
    return temp_dict[user]["info"]

def main_folder():
    if os.name != "nt":
        if not os.path.dirname(os.path.abspath(__file__)).endswith("app"):
            
            return os.path.dirname(os.path.abspath(__file__)).split("app")[0] + "app"
        
        else:
            return os.path.dirname(os.path.abspath(__file__))
        
    else:
        return os.path.dirname(sys.argv[0])
            


def user_folder(user):
    user = str(user)
    carpeta_destino = gettempdir()
    # carpeta_destino = main_folder()
    
    if not "user_archive" in os.listdir(carpeta_destino):
        os.mkdir(os.path.join(carpeta_destino, "user_archive"))
        os.mkdir(os.path.join(carpeta_destino, "user_archive", user))
        
    if not list(filter(lambda file: file.startswith(user), os.listdir(os.path.join(carpeta_destino, "user_archive")))):
        os.mkdir(os.path.join(carpeta_destino, "user_archive",  user))
        
    return os.path.join(carpeta_destino, "user_archive",  user)
    
def make_screenshoot(driver, user, element=False, bot=False):
    user = str(user)
    if element:
        element.screenshot(os.path.join(user_folder(user) , str(user) + "_error_facebook.png"))
    else:
        driver.save_screenshot(os.path.join(user_folder(user) , str(user) + "_error_facebook.png"))
    
    if not bot:
        return os.path.join(user_folder(user) , str(user) + "_error_facebook.png")
    
    else:
        bot.send_photo(user, telebot.types.InputFile(os.path.join(user_folder(user) , str(user) + "_error_facebook.png")), "Captura")

        return os.path.join(user_folder(user) , str(user) + "_error_facebook.png")
    
def make_captcha_screenshoot(captcha_element, user):
    user = str(user)
    captcha_element.screenshot(os.path.join(user_folder(user), str(user) + "_captcha.png"))
    
    return os.path.join(user_folder(user), str(user) + "_captcha.png")


def handlers(bot, user , msg ,info, diccionario: dict , **kwargs):    

    temp_dict = diccionario.copy()

    if kwargs.get("file"):
        if kwargs.get("markup"):
            temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg, reply_markup=kwargs.get("markup"))
            
        else:
            temp_dict[user]["msg"] = bot.send_photo(user, kwargs.get("file"), caption=msg)
        
    else:
        if kwargs.get("markup"):
            temp_dict[user]["msg"] = bot.send_message(user, msg, reply_markup=kwargs.get("markup"))
        
        else:
            temp_dict[user]["msg"] = bot.send_message(user, msg)
    

    temp_dict[user]["completed"] = False   

    match info:
        
        case "user":
        
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict, diccionario=temp_dict)
            
        case "password":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict, diccionario=temp_dict)
            
        case "perfil_elegir":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.choose_perfil, bot,user, info, temp_dict)
            
        case "codigo_respaldo":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_codigo, bot,user, info, temp_dict)
            
        case "perfil_pregunta":
            
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.perfil_pregunta, bot,user, info, temp_dict)
            
        case "captcha":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.captcha_getter, bot,user, info, temp_dict, kwargs.get("file"))
            
        case "perfil_seleccion":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.perfil_seleccion, bot,user, info, temp_dict, kwargs.get("markup"))

        case "correo_o_numero":

            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.correo_o_numero, bot,user, info, temp_dict)


        case "correo_o_numero_verificacion":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.correo_o_numero_verificacion, bot,user, info, temp_dict)

        case "email_verification":
            

            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.email_verification, bot,user, info, temp_dict)
            
            
    while True:
        if not temp_dict[user]["completed"]:
            time.sleep(2)
            
        else:
            break
    

    
    diccionario[user].update(temp_dict[user])
    
    return