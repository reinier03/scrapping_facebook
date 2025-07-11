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

def give_error(bot, driver, user, texto):
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
    
    if not "user_archive" in os.listdir(main_folder()):
        os.mkdir(os.path.join(main_folder(), "user_archive"))
        os.mkdir(os.path.join(main_folder(), "user_archive", user))
        
    if not list(filter(lambda file: file.startswith(user), os.listdir(os.path.join(main_folder(), "user_archive")))):
        os.mkdir(os.path.join(main_folder(), "user_archive",  user))
        
    return os.path.join(main_folder(), "user_archive",  user)
    
def make_screenshoot(driver, user, element=False, bot=False):
    user = str(user)
    if element:
        element.screenshot(os.path.join(user_folder(user) , str(user) + "_error_facebook.png"))
    else:
        driver.save_screenshot(os.path.join(user_folder(user) , str(user) + "_error_facebook.png"))
    
    if not bot:
        return os.path.join(user_folder(user) , str(user) + "_error_facebook.png")
    
    else:
        if element:
            bot.send_photo(user, telebot.types.InputFile(os.path.join(user_folder(user) , str(user) + "_error_facebook.png")), "Captura de un elemento en el HTML")
        else:
            bot.send_photo(user, telebot.types.InputFile(os.path.join(user_folder(user) , str(user) + "_error_facebook.png")), "Captura de pantalla")

        return os.path.join(user_folder(user) , str(user) + "_error_facebook.png")
    
def make_captcha_screenshoot(captcha_element, user):
    user = str(user)
    captcha_element.screenshot(os.path.join(user_folder(user), str(user) + "_captcha.png"))
    
    return os.path.join(user_folder(user), str(user) + "_captcha.png")


def handlers(bot, user , msg ,info, temp_dict , **kwargs):    
    
    
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
        
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict)
            
        case "password":
            
            bot.register_next_step_handler(temp_dict[user]["msg"], bot_handlers.get_user, bot,user, info, temp_dict)
            
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
    

    
    temp_dict[user]["completed"] = False  
    
    return