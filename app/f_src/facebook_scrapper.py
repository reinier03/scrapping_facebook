import f_src.bot_handlers
from f_src.chrome_driver import *
import f_src
from f_src.usefull_functions import *
import time 
from traceback import format_exc
import os
import dill
import random
import re
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from selenium.webdriver import Chrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, InvalidSelectorException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
import seleniumbase
from pymongo import MongoClient
import tempfile
import shutil


#variables de entorno

if not "MONGO_URL" in os.environ:
    MONGO_URL = "mongodb://localhost:27017"
else:
    MONGO_URL = os.environ["MONGO_URL"]



driver = uc_driver()


    
wait = WebDriverWait(driver, 20)
cliente = MongoClient(MONGO_URL)
db = cliente["face"]
collection = db["usuarios"]



temp_dict = {}
wait_s = WebDriverWait(driver, 8)
# {"id_": random, "telegram_id": 1747104645, "user" : "example@gmail.com", cookies : cookies_binary}






    
def esperar(etiqueta, elementos, intentos=6):
    '''
    Esta funcion se asegura de que los elementos están disponibles en el DOM
    si no se cumplen las condiciones, se espera 5 segundos y se vuelve a intentar
    '''
    contador = 1
    while True:
        try:
            e = wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, etiqueta)) >= elementos + 1))
            
        except IndexError:
            if contador >= intentos:
                return ("error", "Ingresaste un índice no válido")
            pass
        
        except:
            pass
            
        finally:
            try:
                if e == True:
                    return ("ok", driver.find_elements(By.CSS_SELECTOR, etiqueta)[elementos])
            
            except:
                pass
            
            if contador >= intentos:
                return ("error", "no se han obtenido la etiqueta: " + str(etiqueta))

            else:
                contador += 1
                time.sleep(5)




    

def guardar_cookies(driver, user, **kwargs):
    
    global temp_dict
    try:
        temp_dict[user]["dict_cookies"] = cargar_cookies(driver, user, hacer_loguin=False)
        
        if isinstance(temp_dict[user]["dict_cookies"], Exception):
            temp_dict[user]["dict_cookies"] = ("error", e.args[0])
            
    except Exception as e:
        temp_dict[user]["dict_cookies"] = ("error", e.args[0])
        
    temp_dict[user]["dic"] = {}
    if temp_dict[user]["dict_cookies"][0] == "ok":
        temp_dict[user]["dict_cookies"] = temp_dict[user]["dict_cookies"][-1]
        #si ya habían datos guardados y no se le pasó por parametro a la funcion entonces se mantienen esos datos
        for key, value in temp_dict[user]["dict_cookies"].items():
            if not temp_dict[user]["dic"].get(key):
                temp_dict[user]["dic"][key] = value
    else:
        temp_dict[user]["dict_cookies"] = {}
        
    with open(os.path.join(user_folder(user), "cookies.pkl"), "wb") as file_cookies:
        #recorrer los kwargs y agregarlos a las cookies
        if kwargs:
            if kwargs.get("cookiespkl"):
                dill.dump(kwargs.get("cookiespkl"), file_cookies)
                
            else:
                for key, value in kwargs.items():
                    temp_dict[user]["dic"][key] = value
                
                temp_dict[user]["dic"]["cookies"] = driver.get_cookies()


                dill.dump(temp_dict[user]["dic"], file_cookies)
                
        else:
            temp_dict[user]["dic"]["cookies"] = driver.get_cookies()


            dill.dump(temp_dict[user]["dic"], file_cookies)


    try:
        with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as cookies:
            collection.update_one({"telegram_id": user}, {"$set": {"cookies": dill.load(cookies)}})
            
    except:
        del temp_dict[user]["dic"], temp_dict[user]["dict_cookies"]
        raise Exception("error", "Error en ingresar las cookies a la base de datos:\n\nDescripción del error:\n" + str(format_exc()))
    
    del temp_dict[user]["dic"]
    try:
        del temp_dict[user]["dict_cookies"]
        
    except:
        pass
    
    print("Se guardaron cookies!")
    return ("ok", os.path.join(user_folder(user), "cookies.pkl"))



def cargar_cookies(driver, user, bot=False , hacer_loguin=True):
    
    
    #si hay cookies
    if list(filter(lambda file: "cookies.pkl" in file, os.listdir(user_folder(user)))):
        
        if hacer_loguin:
            driver.get("https://facebook.com/robots.txt")
        
        with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as file_cookies:
            try:
                temp_dict[user]["cookies_dict"] = dill.load(file_cookies)
            
            except:
                return ("error", format_exc())
            
            if not hacer_loguin:
                return ("ok", temp_dict[user]["cookies_dict"])
            
            
            for cookie in temp_dict[user]["cookies_dict"]["cookies"]:
                driver.add_cookie(cookie)
                    
                             
    else:
        try:
            
            temp_dict[user]["res"] = collection.find_one({'_id': user})["cookies"]
            if temp_dict[user]["res"]:
                #loguin por cookies
                if hacer_loguin:
                    driver.get("https://facebook.com/robots.txt")
                    
                with open(os.path.join(user_folder(user), "cookies.pkl"), "wb") as cookies:
                    cookies.write(temp_dict[user]["res"])
                    
                with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as cookies:
                    temp_dict[user]["cookies_dict"] = dill.load(cookies)
                    
                    if not hacer_loguin:
                        return ("ok", temp_dict[user]["cookies_dict"])
                    
                    for cookies in temp_dict[user]["cookies_dict"]["cookies"]:
                        driver.add_cookie(cookies)
                        
                        
            
                                    
        except Exception as e:
            try:
                if re.search('error=.*timeout', e.args[0]).group().split('(')[1]:
                    raise Exception("No hay conexión con la base de datos!" + "\nDescripción\n\n" + re.search('error=.*timeout', e.args[0]).group().split('(')[1])

            except:
                pass
            
            finally:
                return Exception("Error intentando acceder a la base de datos:\n\nDescripción:\n" + str(format_exc))
    
    if hacer_loguin == True:
        #Porqué lo pongo en un while True? porque vivo en Cuba :( MI conexion a internet es lentisima entonces si no controlo esto arrojara un timeout
        if os.name == "nt":
            try:
                driver.get("https://facebook.com")
            except:
                pass
            
            while True:
                
                try:
                    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                    break
                except:
                    pass
                
        else:
            driver.get("https://facebook.com")
        
            
        # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nMuy Bien, Ya accedí a Facebook :D", chat_id=user, message_id=temp_dict[user]["info"].message_id)
        
        bot.send_message(user, "🆕 Mensaje de Información\n\nMuy Bien, Ya accedí a Facebook :D")

    
        try:
            wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
            # wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]')))
            print("Se cargaron cookies ")
            return ("ok", "login con cookies exitosamente", temp_dict[user]["cookies_dict"])
    
        except Exception as er:
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
            raise Exception("ID usuario: "+ str(user) + "\n\nDescripción del error:\n" + str(format_exc()))
    
    else:
        print("Se cargaron cookies_2")
        return ("ok", "login con cookies exitosamente", temp_dict[user]["cookies_dict"])
        

def captcha(driver , user, bot: telebot.TeleBot):
    try:
        if "captcha" in  driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src"):
            
            while True:
                #el enlace del captcha cambia cuando se introduce uno erróneo, ya que se vuelve a generar uno nuevo desde una dirección diferente
                temp_dict[user]["url_captcha"] = driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src")
                #Esperar a que la foto se muestre adecuadamente en la pantalla para que selenium pueda hacerle captura
                wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh")))
                
            
                handlers(bot, user, "ATENCION!\nHa aparecido un captcha!\n\nIntroduce el código proporcionado en la foto CORRECTAMENTE para continuar...", "captcha", temp_dict, file=telebot.types.InputFile(make_captcha_screenshoot(driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh"), user)))
                                   
                
                for i in temp_dict[user]["res"]:
                    driver.find_element(By.CSS_SELECTOR, "input#«r1»").send_keys(i)
                    time.sleep(0.5)
                
                #click en continuar    
                
                driver.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft")[-1].click()
                
                try:
                    
                    wait.until(ec.url_changes(driver.current_url))
                    
                except:
                    pass
                    
                finally:
                    try:                                   
                        if "captcha" in  driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src"):
                            
                            if driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src") != temp_dict[user]["url_captcha"]:
                                
                                # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nEl codigo que introduciste es incorrecto! :( \n\nVuelve a intentarlo", chat_id=user, message_id=temp_dict[user]["info"].message_id)
                                
                                bot.send_message(user, "🆕 Mensaje de Información\n\nEl codigo que introduciste es incorrecto! :( \n\nVuelve a intentarlo")
                                
                                continue
                            
                        else:
                                                
                            # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nEl código introducido es correcto :)\n\nSeguiré procediendo...", chat_id=user, message_id=temp_dict[user]["info"].message_id)
                            
                            bot.send_message(user, "🆕 Mensaje de Información\n\nEl código introducido es correcto :)\n\nSeguiré procediendo...")
                            
                            return ("ok", "captcha resuelto!")    
                            
                    except NoSuchElementException:
                        print("captcha resuelto")
                        return ("ok", "captcha resuelto!")    

                
                    
                
                
                
                
        else: 
            return ("no", "Al parecer no hay captcha")
    except NoSuchElementException:
        return ("no", "Al parecer no hay captcha")
    
    except:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
        raise Exception("ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(format_exc()))
    
def loguin(driver: seleniumbase.Driver, user, bot, **kwargs):

    """
    Si no se proporciona un user_id, se creará uno nuevo
    
    Hace loguin en Facebook, determinará si hacer loguin desde cero o no si se le proporciona un user y si hay algún archivo de ese usuario en la BD
    """
    
    global temp_dict
    

    if list(filter(lambda file: file == "cookies.pkl", os.listdir(user_folder(user)))):
        
        # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nHay cookies de la sesion, voy a cargarlas.\n\nEspere un momento...", chat_id=user, message_id=temp_dict[user]["info"].message_id)
        
        bot.send_message(user, "🆕 Mensaje de Información\n\nHay cookies de la sesion, voy a cargarlas.\n\nEspere un momento...")
        
        temp_dict[user]["res"] = cargar_cookies(driver, user, bot)    
        if temp_dict[user]["res"][0] == "error":
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
            raise Exception(temp_dict[user]["res"])
        

        if not collection.find_one({"telegram_id": user}):
            collection.insert_one({"_id": int(time.time()), "telegram_id": user})
            guardar_cookies(driver, user)
        
        return temp_dict[user]["res"]
    
    else:
        if collection.find_one({"telegram_id": user}):
            temp_dict[user]["res"] = collection.find_one({"telegram_id": user})
            if temp_dict[user]["res"].get("cookies"):
                guardar_cookies(driver, user, cookiespkl=temp_dict[user]["res"]["cookies"])
                return loguin(driver, user, bot)

            else:
                return loguin_cero(driver, user, bot)

        else:

            collection.insert_one({"_id": int(time.time()), "telegram_id": user})
                
            return loguin_cero(driver, user, bot)
            
                
        
    


# input.x1s85apg => Input para enviar los videos

def cookies_caducadas(driver, user, bot):
    global temp_dict
    
    if driver.find_element(By.CSS_SELECTOR, 'div[class="_45ks"]'):
        temp_dict[user]["perfiles"] = driver.find_elements(By.CSS_SELECTOR, 'div[class="removableItem _95l5 _63fz"]')
        temp_dict[user]["texto"] = ""
        temp_dict[user]["lista_perfiles"] = []
        temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, row_width=1, input_field_placeholder="Selecciona una cuenta")
        
        for e,i in enumerate(temp_dict[user]["perfiles"], 1):
            temp_dict[user]["lista_perfiles"].append(i.text)
            temp_dict[user]["texto"] += str(e) + " => " + i.text
            temp_dict[user]["teclado"].add(i.text)
            
        
        handlers(bot, user, "¿Cual cuenta deseas usar?\n\n" + str(temp_dict[user]["texto"]), "perfil_seleccion", temp_dict, markup=temp_dict[user]["teclado"])
        

        
        #le resto uno para coincidir con el índice
        temp_dict[user]["perfiles"][temp_dict[user]["res"]].click()
        
        while True:
            handlers(bot, user, "Introduce la contraseña de esta cuenta a continuación", "password" ,temp_dict)
            

                        
            wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'input[id="pass"][type="password"]')))[-1].send_keys(temp_dict[user]["password"])
            
            
            try:
                e = driver.find_element(By.CSS_SELECTOR, 'input#email"')
                
            except:
                e = None
                
            if e:
                handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", temp_dict)
                

                
                driver.find_element(By.CSS_SELECTOR, 'input#email"').send_keys(temp_dict[user]["user"])

            
            
            try:
                #click para recordar contraseña
                driver.find_element(By.CSS_SELECTOR, 'span[class="_9ai8"]').click()
            
            except NoSuchElementException:
                pass
            
            #click en iniciar sesión
            driver.find_elements(By.CSS_SELECTOR, 'button[name="login"]')[-1].click()
            wait.until(ec.url_changes(driver.current_url))
            wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
            temp_dict[user]["res"] = captcha(driver, user, bot)
            if temp_dict[user]["res"] == "error":
                print(temp_dict[user]["res"][1])
                
            elif temp_dict[user]["res"][0] in ["ok", "no"]:
                guardar_cookies(driver, user)
                break

            elif driver.find_element(By.CSS_SELECTOR, 'div[class="mvm _akly"]'):
                print("¡Contraseña incorrecta! ¡vuelve a intentarlo!")
                driver.back()
                continue

def loguin_cero(driver: seleniumbase.Driver, user, bot : telebot.TeleBot, load_url=True, **kwargs):
    global temp_dict
    print("Estoy usando el loguin desde cero")
    
    temp_dict[user] = {}
    
    def doble_auth(driver: seleniumbase.Driver , user, bot: telebot.TeleBot):
        global temp_dict
        # e = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
        try:
            temp_dict[user]["e"] = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "span.xuxw1ft")))
            temp_dict[user]["e"].click()
        except:
            make_screenshoot(driver, user)
            return ("error", "ID usuario: " + str(user) + "\n\nNo se ha podido dar click en el botón de doble autenticación")
        
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "div.x1nn3v0j")))
        
        #aqui le doy click a el metodo de auth que en este caso sería por codigo de verificacion
        wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "input.xh8yej3")))
        driver.find_elements(By.CSS_SELECTOR, "input.xh8yej3")[-1].click()
        #le doy click a continuar

        driver.find_elements(By.CSS_SELECTOR, "span.xuxw1ft")[-1].click()
        #el siguiente elemento es el input en el que va el código
        
        temp_dict[user]["e"] = wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, "input.xha3pab")))
        temp_dict[user]["e"] = driver.find_element(By.CSS_SELECTOR, "input.xha3pab")

        
        
            
        handlers(bot, user, "A continuación, introduce uno de los códigos de respaldo de Facebook\n\n(Estos códigos son de 8 dígitos numéricos y puedes obtenerlos en el centro de cuentas en los ajustes de tu cuenta de Facebook)" , "codigo_respaldo", temp_dict, markup=ForceReply())
        
        
        for i in temp_dict[user]["res"].text:
            temp_dict[user]["e"].send_keys(i)
            time.sleep(0.5)
        
           
        print("he ingresado los códigos")
        temp_dict[user]["url_actual"] = driver.current_url
        
        #click en el boton de continuar
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="xod5an3 xg87l8a"]'))).find_element(By.CSS_SELECTOR, 'span[class="x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft"]').click()
        print("click en el boton de continuar")
        
        
        
        try:
            #este mensaje se muestra cuando el código es incorrecto
            if wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'span[class="x1lliihq x1plvlek xryxfnj x1n2onr6 x1ji0vk5 x18bv5gf x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs x1s928wv xhkezso x1gmr53x x1cpjm7i x1fgarty x1943h6x xnk8lw1 xuarlqh xuemr51 x1ff8u0n x1a1m0xk x1yc453h xtoi2st x676frb"]'))):
                bot.send_message(user, "🆕 Mensaje de Información\n\nHas Introducido un código incorrecto! Vuelve a intentarlo!")
                
                driver.refresh()
                return doble_auth(driver, user, bot)
                
        except:
            pass
        
        #esperar a que no esté el botón
        wait.until(ec.invisibility_of_element_located((By.CSS_SELECTOR, 'div[class="xod5an3 xg87l8a"]')))
           
        try:
            print("cambiar la url a la de remember_browser")
            wait.until(ec.url_changes(temp_dict[user]["url_actual"]))
            print("ha cambiado!")

        except:
            pass
        
        
        
        if not "remember_browser" in driver.current_url:
            
            # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nHas Introducido un código incorrecto! Vuelve a intentarlo!", chat_id=user, message_id=temp_dict[user]["info"].message_id)  
            
            bot.send_message(user, "🆕 Mensaje de Información\n\nHas Introducido un código incorrecto! Vuelve a intentarlo!")
            
            driver.refresh()
            return doble_auth(driver, user, bot)
            
        

        
        #click en confiar en este dispositivo
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'span[class="x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft"]')))
        driver.find_element(By.CSS_SELECTOR, 'span[class="x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft"]').click()

        # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto", chat_id=user, message_id=temp_dict[user]["info"].message_id)     
        
        bot.send_message(user, "🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto")
        
        return ("ok", "se ha dado click en confiar dispositivo")
                

            
            


    
    
    if load_url:
        driver.get("https://facebook.com")
    
    e = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
    
    #-----------------obtener usuario para loguin---------------
    e = wait.until(ec.visibility_of_element_located((By.ID, "email")))
    
    #cambiar
    handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", temp_dict)


    e.send_keys(temp_dict[user]["user"])
    
    
    #-----------------obtener password para loguin---------------
    e = wait.until(ec.visibility_of_element_located((By.ID, "pass")))
    

    handlers(bot, user, "Introduce a continuación la contraseña", "password", temp_dict)
    
    
    temp_dict[user]["url_actual"] = driver.current_url
    
    e.send_keys(temp_dict[user]["password"])
    
    e = wait.until(ec.visibility_of_element_located((By.NAME, "login")))
    e.click()
    try:
        wait.until(ec.url_changes(temp_dict[user]["url_actual"]))
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
    except:
        print("no cambio?")
    
    
    captcha(driver, user, bot)

    
    
    try:
        #cuando no introduces bien ninguno de tus datos:
        if driver.find_element(By.CSS_SELECTOR, 'div[class="_9ay7"]'):
            # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nAl parecer los datos que me has enviado son incorrectos\nEl mensaje que me ha mostrado Facebook al intentar usar los datos que me proporcionaste fué el siguiente:\n\n<blockquote>{driver.find_element(By.CSS_SELECTOR, 'div[class="_9ay7"]').text}</blockquote>\n\nPor favor ingrese nuevamente correctamente sus datos", chat_id=user, message_id=temp_dict[user]["info"].message_id) 
            
            bot.send_message(user, "🆕 Mensaje de Información\n\nAl parecer los datos que me has enviado son incorrectos\nEl mensaje que me ha mostrado Facebook al intentar usar los datos que me proporcionaste fué el siguiente:\n\n<blockquote>" + str(driver.find_element(By.CSS_SELECTOR, 'div[class="_9ay7"]').text) + "</blockquote>\n\nPor favor ingrese nuevamente correctamente sus datos")
            del temp_dict[user]
            loguin_cero(driver, user, bot)
            
    except:
        pass
    
    try:
        #cuando no introduces bien la contraseña:
        if driver.find_element(By.CSS_SELECTOR, 'div[class="pam uiBoxGray"]'):
            
            # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nAl parecer no has introducido adecuadamente tus credenciales\nEl mensaje que me ha mostrado Facebook al intentar usar los datos que me proporcionaste fué el siguiente:\n\n<blockquote>{driver.find_element(By.CSS_SELECTOR, 'div[class="pam uiBoxGray"]').text}</blockquote>\n\nPor favor ingrese nuevamente correctamente sus datos", chat_id=user, message_id=temp_dict[user]["info"].message_id) 
            
            bot.send_message(user, "🆕 Mensaje de Información\n\nAl parecer no has introducido adecuadamente tus credenciales\nEl mensaje que me ha mostrado Facebook al intentar usar los datos que me proporcionaste fué el siguiente:\n\n<blockquote>" + str(driver.find_element(By.CSS_SELECTOR, 'div[class="pam uiBoxGray"]').text) + "</blockquote>\n\nPor favor ingrese nuevamente correctamente sus datos")
            
            del temp_dict[user]
            loguin_cero(driver, user, bot)
        
    
    except:
        pass
    
    try:
        #cuando la contraseña que ingresaste era antigua
        if driver.find_element(By.CSS_SELECTOR, 'div#error_box'):
            
            # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nAl parecer no has introducido adecuadamente tus credenciales\nEl mensaje que me ha mostrado Facebook al intentar usar los datos que me proporcionaste fué el siguiente:\n\n<blockquote>{driver.find_element(By.CSS_SELECTOR, 'div[class="pam uiBoxGray"]').text}</blockquote>\n\nPor favor ingrese nuevamente correctamente sus datos", chat_id=user, message_id=temp_dict[user]["info"].message_id) 
            
            bot.send_message(user, "🆕 Mensaje de Información\n\nAl parecer no has introducido adecuadamente tus credenciales\nEl mensaje que me ha mostrado Facebook al intentar usar los datos que me proporcionaste fué el siguiente:\n\n<blockquote>" + driver.find_element(By.CSS_SELECTOR, 'div[class="pam uiBoxGray"]').text + "</blockquote>\n\nPor favor ingrese nuevamente correctamente sus datos")
            
            del temp_dict[user]
            loguin_cero(driver, user, bot)
    except:
        pass
    
    if "two_step_verification" in driver.current_url:
        temp_dict[user]["res"] = doble_auth(driver, user, bot)
        if "No se ha podido dar click en el botón de doble autenticación" in temp_dict[user]["res"][-1]:
                        
            temp_dict[user]["res"] = captcha(driver, user, bot)
            if temp_dict[user]["res"][0] == "error":
                return temp_dict[user]["res"]
            
            if "two_factor" in driver.current_url:
                #doble auntenticación
                temp_dict[user]["res"] = doble_auth(driver, user, bot)
                if temp_dict[user]["res"][0] == "error":
                    return temp_dict[user]["res"]
                
        else:
            pass
            
            
    
    try:
        print("Voy a esperar a que salga la main page de facebook")
        if wait.until(ec.all_of(lambda driver: driver.find_element(By.CSS_SELECTOR, 'svg[class="x3ajldb"]') and not "remember_browser" in driver.current_url)):
        # wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
            
            guardar_cookies(driver, user, loguin={"user": temp_dict[user]["user"], "password": temp_dict[user]["password"]})

            print("He guardado las cookies")
            
            return ("ok", "loguin desde cero satisfactorio :)")
        
        else:    
            # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo", chat_id=user, message_id=temp_dict[user]["info"].message_id) 
            
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)) , "🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo")

            return loguin_cero(driver, user, bot) 
        
    except Exception as e:
        # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo", chat_id=user, message_id=temp_dict[user]["info"].message_id) 
        
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)) , "🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo")
        return loguin_cero(driver, user, bot)
        
        
def publicacion(driver: Chrome, bot:telebot.TeleBot, url, user, load_url=True, contador = 0, **kwargs):
    global temp_dict
    
    # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nEstoy accediendo a la publicación del enlace que me proporcionaste...", chat_id=user, message_id=temp_dict[user]["info"].message_id)    
    
    
    bot.send_message(user, "🆕 Mensaje de Información\n\nEstoy accediendo a la publicación del enlace que me proporcionaste..." )
    
    temp_dict[user]["a"] = ActionChains(driver, duration=0)
    
    if load_url:
        
        if os.name == "nt":
            try:
                driver.get(url)
            except:
                pass
            
            while True:
                try:
                    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                    break
                except:
                    pass
                
        else:
            driver.get(url)
                
        
        time.sleep(5)
        print("Cargué el enlace proporcionado: {}".format(url))
    
    
    if not kwargs.get("temp_dic"):
        temp_dict[user]["publicacion"] = {"publicados" : [], "error" : []}
        
    else:
        temp_dict[user]["publicacion"] = kwargs.get("info_publicacion")
    
    
    #bucle para publicar por los grupos
    while True:
        
        #bucle para si la lista de grupos desaparece magicamente
        while True:
            
            if contador != 0:
                #aqui compruebo que la ventana de compartir ya no esté interrumpiendo
                try:
                    wait.until(ec.invisibility_of_element((By.CSS_SELECTOR, 'div[class="x1l90r2v xyamay9 x1n2onr6"]')))
                    
                except:
                    bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura Error")
                    raise Exception("Facebook me bloqueó?")
                
            #esperar el botón de compartir
            print("Buscaré el boton de compartir")
            temp_dict[user]["res"] = wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'span[data-ad-rendering-role="share_button"]')))
            
            if len(temp_dict[user]["res"]) == 1:
                temp_dict[user]["res"] = esperar('span[data-ad-rendering-role="share_button"]', 0)
                
            else:
                temp_dict[user]["res"] = esperar('span[data-ad-rendering-role="share_button"]', 1)
        
            if temp_dict[user]["res"][0] == "error":
                give_error(bot, driver, user, "ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(temp_dict[user]["res"]))
                
                return
        
            else:
                temp_dict[user]["res"] = temp_dict[user]["res"][1]
                    
                    
            #click en el boton de compartir en la publicacion
            time.sleep(5)
            temp_dict[user]["res"].click()
            print("Le he dado click en el botón Compartir")
            

            #comprobar si ya existe el elemento de grupos en el DOM
            # res = esperar('i[class="x1b0d499 xep6ejk"]', 9)
            temp_dict[user]["res"] = esperar('div[class="xnfxvih xh8yej3"]', 1)
            
            if temp_dict[user]["res"][0] == "error":
                
                give_error(bot, driver, user, "ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(temp_dict[user]["res"][1]))
                return
                    


            #click en compartir en grupos
            # time.sleep(2)
            temp_dict[user]["res"][1].find_elements(By.CSS_SELECTOR, 'i[class="x1b0d499 xep6ejk"]')[4].click()
            print("Click en Compartir Grupos")

            #esperar lista de grupos
            try:
                print("Esperando lista de grupos visibles")
                wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')))
                break
                
            except Exception as err:
                try:
                    #a veces la lista de grupos aparece y magicamente desaparece, mostrando de nuevo la publicacion con el boton de compartir, en esta condicion, si el boton compartir de la publicacion vuelve a aparecer entonces se le da de nuevo
                    if len(driver.find_elements(By.CSS_SELECTOR, 'div[role="dialog"]')) >= 3:
                        continue
                except:
                    bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
                    raise err


        #obtener grupos
        print("Obteniendo grupos")
        temp_dict[user]["lista_grupos"] = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')
        
        if not temp_dict[user]["lista_grupos"] or len(temp_dict[user]["lista_grupos"]) < contador:
            try:
                temp_dict[user]["lista_grupos"] = wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')))
            except:
                temp_dict[user]["lista_grupos"] = False
                
        
        
        
        
        if not temp_dict[user]["lista_grupos"]:
            
            give_error(bot, driver, user, "¡No hay ningún grupo al que publicar!\n\nDescripcion del error:\n" + str(format_exc()))
        
        #si ya recorrimos todos los elementos de la lista...
        while len(temp_dict[user]["lista_grupos"]) < contador + 1:
            
            temp_dict[user]["a"].move_to_element(driver.find_element(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')).perform()
            
            #por alguna razón, cuando lo pruebo en el debugger esta linea me da error con la variable 'temp_dict[user]["lista_grupos"]' que almacena los grupos asi que lo pongo en un try-except
            try:
                temp_dict[user]["a"].scroll_to_element(temp_dict[user]["lista_grupos"][-1]).perform()
            except:
                temp_dict[user]["a"].scroll_to_element(driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')[-1]).perform()
            
            
            temp_dict[user]["a"].scroll_from_origin(ScrollOrigin.from_element(temp_dict[user]["lista_grupos"][-1]), 0 , 50).perform()
            
            #cambiar valor
            try:
                wait_s.until(ec.any_of(lambda driver: len(temp_dict[user]["lista_grupos"]) < len(driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]'))))
                
            except:
                pass
            
            #si ya se recorrieron todos los grupos y la lista de grupos guardada es igual a la que resulta de la búsqueda entonces se terminó exitosamente de publicar
            

            if len(temp_dict[user]["lista_grupos"]) == len(driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')):
                bot.unpin_chat_message(temp_dict[user]["info"].chat.id, temp_dict[user]["info"].message_id)
                
                return ("ok", "Se ha publicado exitosamente en " + str(len(temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)")
            
            # si la lista de grupos guardada es menor a la nueva resultante de la busqueda, entonces se actualiza los elementos de la lista de grupos y se continua
            else:
                temp_dict[user]["lista_grupos"] = wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')))
      
        
        
        temp_dict[user]["a"].move_to_element(driver.find_element(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')).perform()
        temp_dict[user]["a"].scroll_to_element(temp_dict[user]["lista_grupos"][contador]).perform()
        temp_dict[user]["publicacion"]["nombre"] = temp_dict[user]["lista_grupos"][contador].text.split("\n")[0].strip()
        # time.sleep(2)
        temp_dict[user]["lista_grupos"][contador].click()
        
        def obtener_texto(temp_dict, error: bool):
            
            temp_dict[user]["info"] = bot.edit_message_text("✅Se ha publicado en: " + str(len(temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)\n❌Se han producido errores en: " + str(len(temp_dict[user]["publicacion"]["error"])) + " grupo(s)", user, temp_dict[user]["info"].message_id)
            
            #4000 caracteres es el limite de telegram para los mensajes, si sobrepasa la cantidad tengo que enviar otro mensaje            
            if len(temp_dict[user]["publicacion"]["texto_publicacion"] + "❌ " + temp_dict[user]["publicacion"]["nombre"] + "\n") >= 4000:
                
                
                if error == True:
                    temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1) + "=> ❌ " + temp_dict[user]["publicacion"]["nombre"] + "\n"
                else:
                    temp_dict[user]["publicacion"]["texto_publicacion"] = str(contador + 1) + "=> ✅ " + temp_dict[user]["publicacion"]["nombre"] + "\n"
                    
                    
                #para asegurarme de que hay que enviar un nuevo mensaje retorno "nuevo"
                return ("nuevo", temp_dict[user]["publicacion"]["texto_publicacion"])
                    
            else:
                
                if error == True:
                    temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1) + "=> ❌ " + temp_dict[user]["publicacion"]["nombre"] + "\n"
                    
                else:
                    temp_dict[user]["publicacion"]["texto_publicacion"] += str(contador + 1) + "=> ✅ " + temp_dict[user]["publicacion"]["nombre"] + "\n"

                return ("no", temp_dict[user]["publicacion"]["texto_publicacion"])
        
        
        
        if not temp_dict[user]["publicacion"].get("msg_publicacion"):
            
            temp_dict[user]["publicacion"]["texto_publicacion"] = ""
            temp_dict[user]["publicacion"]["publicados"] = []
            temp_dict[user]["publicacion"]["error"] = []
                        
            
            # temp_dict[user]["info"] = bot.edit_message_text(text=f"✅Se ha publicado en: {str(len(temp_dict[user]["publicacion"]["publicados"]))} grupo(s)\n❌Se han producido errores en: {str(len(temp_dict[user]["publicacion"]["error"]))} grupo(s)", chat_id=user, message_id=temp_dict[user]["info"].message_id)
            
            temp_dict[user]["info"] = bot.send_message(user, "✅Se ha publicado en: " + str(len(temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)\n❌Se han producido errores en: " + str(len(temp_dict[user]["publicacion"]["error"])) + " grupo(s)")
            
            bot.pin_chat_message(user, temp_dict[user]["info"].message_id, True)
            
            temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, "Lista de Grupos en los que se ha Publicado:\n\n")
        try:
            #esperaré x segundos para ver si desaparece la ventana para publicar
            wait_s.until(ec.any_of(lambda driver: not len(driver.find_elements('div[role="dialog"]')) >= 3))
            
            temp_dict[user]["publicacion"]["error"].append(temp_dict[user]["publicacion"]["nombre"])
            temp_dict[user]["res"] = obtener_texto(temp_dict, True)
            
            if temp_dict[user]["res"][0] == "nuevo":
                temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, temp_dict[user]["res"][0])
                
            else:
                temp_dict[user]["publicacion"]["msg_publicacion"] = bot.edit_message_text(temp_dict[user]["res"][1] , user, temp_dict[user]["publicacion"]["msg_publicacion"].message_id)
            
            return publicacion(driver, url, user,load_url=False, contador=contador + 1, info_publicacion=temp_dict[user]["publicacion"])
        
        except:
            #si la ventana se mantiene...
            temp_dict[user]["publicacion"]["publicados"].append(temp_dict[user]["publicacion"]["nombre"])
            temp_dict[user]["res"] = obtener_texto(temp_dict, False)
            
            if temp_dict[user]["res"][0] == "nuevo":
                temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, temp_dict[user]["res"][1])
            else:
                temp_dict[user]["publicacion"]["msg_publicacion"] = bot.edit_message_text(temp_dict[user]["res"][1] , user, temp_dict[user]["publicacion"]["msg_publicacion"].message_id)
            
            
            
            
        
        
        #esperar a que aparezca el elemento de 'Publicar' 
        try:
            
            temp_dict[user]["res"] = ("ok", wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="x1l90r2v xyamay9 x1n2onr6"]'))).find_element(By.CSS_SELECTOR, 'div.x1i10hfl.xjbqb8w.x1ejq31n'))
            
        except:
            temp_dict[user]["res"] = ("error", "NO se pudo localizar el boton para publicar en los grupos")
        
        
        if temp_dict[user]["res"][0] == "error":
            make_screenshoot(driver, user)
            return ("error", "ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(temp_dict[user]["res"][1]))


        #click en publicar cambiar
        # time.sleep(2)
        try:
            temp_dict[user]["res"][1].click()
        
            #cambiar descomentar para pruebas, este es el boton para cerrar la ventana de publicacion
            # driver.find_element(By.CSS_SELECTOR, 'div[class="xurb0ha"]').click()
        
        except:
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user, driver.find_element(By.CSS_SELECTOR, 'div[class="x1l90r2v xyamay9 x1n2onr6"]')))) 
            return ("error" , "¿Facebook me habrá bloqueado?")
        
        
        
        
        contador += 1
            
                  
                

def elegir_cuenta(driver, user, bot ,ver_actual=False):
    global temp_dict
    print("estoy dentro de la funcion de elegir la cuenta")
    
    
    try:
        #si ya el menú de cuentas está desplegado... hay que omitir cosas
        temp_dict[user]["e"] = driver.find_element(By.CSS_SELECTOR, 'div.x1gslohp')

        temp_dict[user]["e"] = True
        
    except: 
        temp_dict[user]["e"] = False
        
    if not temp_dict[user]["e"]:  
        print("Voy a esperar a que salga el menu de cuentas")
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'svg[class="x3ajldb"]'))).click()
        #comprobaré si sale el botón de seleccionar otros perfiles, si es que hay 
        print("comprobaré si sale el botón de seleccionar otros perfiles, si es que hay")
        wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div.x1gslohp')))

        try:
            driver.find_element(By.CSS_SELECTOR, 'div.x1gslohp').find_elements(By.CSS_SELECTOR, 'span')[-1].click()
            
            temp_dict[user]["res"] = ("ok", "han salido")
            print("Click en ver todos los perfiles")
            
        except:
            temp_dict[user]["res"] = ("error", "la lista no está, el usuario tiene solamente 1 perfil")
                
    
    else:        
        print("La Lista de perfiles ya es visible")
        temp_dict[user]["res"] = ("ok", "la lista está")
    
    
      
    
    if temp_dict[user]["res"][0] == "ok":        
        

        #esperar a que salgan las cuentas
        # padre => "div.x1gslohp"
        print("Esperaré a que salgan todas las cuentas en el navegador")
        # wait.until(ec.any_of(lambda d: d.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')))
        wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')))


        print("Obteniendo los elementos de las cuentas...")
        temp_dict[user]["cuentas"] = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"][data-visualcompletion="ignore-dynamic"]')
        #remuevo el último elemento porque no es una cuenta sino una opcion de facebook en el mismo menú de cuentas
        temp_dict[user]["cuentas"].remove(temp_dict[user]["cuentas"][-1])
        
        # if not ver_actual:
        
        print("Creando el teclado del mensaje...")
        
        if not ver_actual:
            
            temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, input_field_placeholder="Elige un perfil")
            temp_dict[user]["perfiles"] = []
        
            for e,cuenta in enumerate(temp_dict[user]["cuentas"], 1):     
                
                temp_dict[user]["perfiles"].append(cuenta.text.split("\n")[0])
                
                temp_dict[user]["teclado"].add(cuenta.text.split("\n")[0])               
                

                            
            print("Ahora elige la cuenta...")
            handlers(bot, user, "Cual de los perfiles de esta cuenta quieres usar?", "perfil_elegir", temp_dict, markup=temp_dict[user]["teclado"])
            
            temp_dict[user]["cuentas"][temp_dict[user]["res"]].click() 
            print("cuenta elegida!")
            wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
            guardar_cookies(driver, user)
            

            return ("ok", temp_dict[user]["perfiles"][temp_dict[user]["res"]])
            
        else:
            #para ver el perfil actual
            return ("ok", "".join(list(map(lambda i: i.split("\n")[0], temp_dict[user]["cuentas"][0].text))))
                


                     
    
    else:
        print("Al parecer solamente hay 1 perfil")
        #Perfil principal
        temp_dict[user]["e"] = driver.find_element(By.CSS_SELECTOR, 'div.x1gslohp').find_element(By.CSS_SELECTOR, 'a[tabindex="0"]')
        
        temp_dict[user]["res"] = ("ok", temp_dict[user]["e"].text)

        return temp_dict[user]["res"]

    

    
    
    
        
        
def main(bot: telebot.TeleBot, user, link_publicacion):
    """
    This function will do all the scrapping requesting to other functions and makes for sure that all is ok
    
    bot: instance of telebot
    user : telegram's user_id
    """
    global temp_dict

    temp_dict[user] = {}
    
    comprobar_BD(collection)
    
    temp_dict[user]["info"] = bot.send_message(user, "🆕 Mensaje de Información\n\nTe estaré informando acerca de la operación con este mensaje :)")

    try:
        temp_dict[user]["res"] = loguin(driver, user, bot)
        if temp_dict[user]["res"][0] == "error":
            
            if "base de datos" in temp_dict[user]["res"][1]:

                bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)))
                raise Exception(temp_dict[user]["res"][1])
                
            raise Exception("Ha ocurrido un error en el loguin!\n\nDescripción:\n" + str(temp_dict[user]["res"][1]))
        
    except:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
        raise Exception("error intentando hacer loguin\nID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(format_exc()))

    print("Empezaré a comprobar si hay algún error luego del loguin")
    #podria aparecer un dialogo sobre si guardar la información de la cuenta        
    try:    
        temp_dict[user]["e"] = driver.find_element(By.CSS_SELECTOR, 'div[class="x1n2onr6 x1ja2u2z x1afcbsf xdt5ytf x1a2a7pz x71s49j x1qjc9v5 xrjkcco x58fqnu x1mh14rs xfkwgsy x104qc98 x78zum5 x1plvlek xryxfnj xh8yej3 xrlsmeg"]')
        
    except:
        temp_dict[user]["e"] = False
    
    finally:
        if temp_dict[user]["e"]:
            #le doy que si
            temp_dict[user]["e"].find_element(By.CSS_SELECTOR, 'span[class="x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft"]').click()
            
            try:
                temp_dict[user]["e"] = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]')))  
            except:
                temp_dict[user]["e"] = None
                bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), caption="Captura del error")
                raise Exception("Faltó algo al intentar loguear :(")
                
                
    try:
        driver.find_element(By.CSS_SELECTOR, 'div[class="_45ks"]')
        try:
            temp_dict[user]["res"] = cookies_caducadas(driver, user, bot)
            if temp_dict[user]["res"][0] == "error":
                bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
                raise Exception(temp_dict[user]["res"][1])
                
        except:

            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
            raise Exception("Ha ocurrido un error con loguin de cookies caducadas! ID del usuario: " + str(user) + "\n\nMensaje de error:\n" + str(format_exc()))

            
    
    except:
        pass
    
            
    try:
        #comprobando estar en el inicio de la mainpage de facebook
        temp_dict[user]["e"] = wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]')))

    except:
        temp_dict[user]["e"] = None

        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
        raise Exception("ID usuario: " + str(user) + "\nFaltó algo :(")
    

    print("A continuación eligiré una cuenta")    
    try:
        temp_dict[user]["res"] = elegir_cuenta(driver , user, bot, ver_actual=True)
        if temp_dict[user]["res"][0] == "error":

            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "ID usuario: " + str(user) + "\n\nDescripción:\n" + str(temp_dict[user]["res"][1]))
            raise Exception("no")
        
    except:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
        raise Exception("Ha ocurrido un error intentando ver la cuenta actual! ID usuario: " + str(user) + "\n\nMensaje de error:\n" + str(format_exc()))
    
    else:
        temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, row_width=1, input_field_placeholder="¿Quieres cambiar a otro perfil?").add("Si", "No")
        

        handlers(bot, user, "El perfil actual es: <b>" + str(temp_dict[user]["res"][1]) + "</b>\n\n¿Quieres cambiar de perfil?", "perfil_pregunta", temp_dict, markup=temp_dict[user]["teclado"])

        
        
        if temp_dict[user]["res"].text.lower() == "si":
            temp_dict[user]["res"] = elegir_cuenta(driver, user, bot)
            if temp_dict[user]["res"][0] == "error":

                bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
                raise Exception("ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(temp_dict[user]["res"][1]))
            else:
                # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nHe cambiado al perfil de: {temp_dict[user]["res"][1]}", chat_id=user, message_id=temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())
                
                bot.send_message(user, "🆕 Mensaje de Información\n\nHe cambiado al perfil de:  <b>" + str(temp_dict[user]["res"][1]) + "</b>\n\nLoguin completado exitosamente!", reply_markup=telebot.types.ReplyKeyboardRemove())

        else:
            # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nMuy bien, continuaré con el perfil actual", chat_id=user, message_id=temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())

            bot.send_message(user, "🆕 Mensaje de Información\n\nMuy bien, continuaré con el perfil actual\n\nLoguin completado exitosamente!", reply_markup=telebot.types.ReplyKeyboardRemove())

    
            
    temp_dict[user]["res"] = guardar_cookies(driver, user)    

    # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nLoguin completado exitosamente!", chat_id=user, message_id=temp_dict[user]["info"].message_id)

    
    try:
        temp_dict[user]["res"] = publicacion(driver, bot , link_publicacion, user)
        if temp_dict[user]["res"][0] == "error":
            print(temp_dict[user]["res"][1])
        
    except:

        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(driver, user)), "Captura del error")
        raise Exception("Ha ocurrido un error intentando ver la cuenta actual! ID usuario: " + str(user) + "\n\nMensaje de error:\n" + str(format_exc()))


    bot.send_message(user, temp_dict[user]["res"])
    
    return 







