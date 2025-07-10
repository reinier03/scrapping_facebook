from f_src.main_classes import scrapper as s
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



cliente = MongoClient(MONGO_URL)
db = cliente["face"]
collection = db["usuarios"]



temp_dict = {}
# {"id_": random, "telegram_id": 1747104645, "user" : "example@gmail.com", cookies : cookies_dict}






    
def esperar(scrapper: s, etiqueta, elementos, intentos=6):
    '''
    Esta funcion se asegura de que los elementos están disponibles en el DOM
    si no se cumplen las condiciones, se espera 5 segundos y se vuelve a intentar
    '''
    contador = 1
    while True:
        try:
            e = scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, etiqueta)) >= elementos + 1))
            
        except IndexError:
            if contador >= intentos:
                return ("error", "Ingresaste un índice no válido")
            pass
        
        except:
            pass
            
        finally:
            try:
                if e == True:
                    return ("ok", scrapper.driver.find_elements(By.CSS_SELECTOR, etiqueta)[elementos])
            
            except:
                pass
            
            if contador >= intentos:
                return ("error", "no se han obtenido la etiqueta: " + str(etiqueta))

            else:
                contador += 1
                time.sleep(5)




    

def guardar_cookies(scrapper: s, user, **kwargs):
    
    global temp_dict
    try:
        temp_dict[user]["dict_cookies"] = cargar_cookies(scrapper, user, hacer_loguin=False)
        
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
                
                temp_dict[user]["dic"]["cookies"] = scrapper.driver.get_cookies()


                dill.dump(temp_dict[user]["dic"], file_cookies)
                
        else:
            temp_dict[user]["dic"]["cookies"] = scrapper.driver.get_cookies()


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



def cargar_cookies(scrapper: s, user, bot=False , hacer_loguin=True):
    
    
    #si hay cookies
    if list(filter(lambda file: "cookies.pkl" in file, os.listdir(user_folder(user)))):
        
        if hacer_loguin:
            scrapper.driver.get("https://facebook.com/robots.txt")
        
        with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as file_cookies:
            try:
                temp_dict[user]["cookies_dict"] = dill.load(file_cookies)
            
            except:
                return ("error", format_exc())
            
            if not hacer_loguin:
                return ("ok", temp_dict[user]["cookies_dict"])
            
            
            for cookie in temp_dict[user]["cookies_dict"]["cookies"]:
                scrapper.driver.add_cookie(cookie)
                    
                             
    else:
        try:
            
            temp_dict[user]["res"] = collection.find_one({'_id': user})["cookies"]
            if temp_dict[user]["res"]:
                #loguin por cookies
                if hacer_loguin:
                    scrapper.driver.get("https://facebook.com/robots.txt")
                    
                with open(os.path.join(user_folder(user), "cookies.pkl"), "wb") as cookies:
                    cookies.write(temp_dict[user]["res"])
                    
                with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as cookies:
                    temp_dict[user]["cookies_dict"] = dill.load(cookies)
                    
                    if not hacer_loguin:
                        return ("ok", temp_dict[user]["cookies_dict"])
                    
                    for cookies in temp_dict[user]["cookies_dict"]["cookies"]:
                        scrapper.driver.add_cookie(cookies)
                        
                        
            
                                    
        except Exception as e:
            try:
                if re.search('error=.*timeout', e.args[0]).group().split('(')[1]:
                    raise Exception("No hay conexión con la base de datos!" + "\nDescripción\n\n" + re.search('error=.*timeout', e.args[0]).group().split('(')[1])

            except:
                pass
            
            finally:
                return Exception("Error intentando acceder a la base de datos:\n\nDescripción:\n" + str(format_exc()))
    
    if hacer_loguin == True:
        #Porqué lo pongo en un while True? porque vivo en Cuba :( MI conexion a internet es lentisima entonces si no controlo esto arrojara un timeout
        if os.name == "nt":
            try:
                scrapper.driver.get("https://facebook.com")
            except:
                pass
            
            while True:
                
                try:
                    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                    break
                except:
                    pass
                
        else:
            scrapper.driver.get("https://facebook.com")
        
            
        # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nMuy Bien, Ya accedí a Facebook :D", chat_id=user, message_id=temp_dict[user]["info"].message_id)
        
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

        try:
            #podria salir un recuadro para elegir el perfil
            if len(scrapper.driver.find_element(By.CSS_SELECTOR, 'img[data-type="image"][class="img contain"]')) == 4:

                #Aqui elijo el perfil
                scrapper.driver.find_element(By.CSS_SELECTOR, 'div[tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m bg-s5"]').click()

                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
                
                with open(os.path.join(user_folder(user), "cookies.pkl"), "rb") as file_cookies:
                    
                    temp_dict[user]["password"] = dill.load(file_cookies)["password"]

                    for i in temp_dict[user]["password"]:
                        scrapper.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(i)

                        time.sleep(0.5)

                    #click en continuar
                    scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-tti-phase="-1"][data-focusable="true"][data-type="container"][tabindex="0"]')[1].click()

                    #saldra un cartel de doble autenticacion obligatoria
                    #en este punto, si el usuario ya confirmo una doble autenticacion anteriormente, facebook ira directamente a la main page y no requerirá verificacion
                    try:
                        scrapper.wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[class="fl ac am"]')))
                        
                        #dare en aceptar
                        try:
                            scrapper.driver.find_element(By.CSS_SELECTOR, 'div[class="fl ac am"]').click()

                            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'input[type="text"]')))

                            handlers(bot, user , "Introduce tu número de movil (con el código regional adelante, ejemplo: +53, +52 , +01, etc) o tu correo electrónico para enviar el código de verificación" , "correo_o_numero", temp_dict)

                            for i in temp_dict[user]["res"]:

                                scrapper.driver.find_element(By.CSS_SELECTOR, 'input[type="text"]').send_keys(i)

                                time.sleep(0.5)

                            handlers(bot, user , "Ahora introduce el código del SMS o el código que se te fué enviado a Whatsapp, revisa ambas\n\nEn caso de que no llegue, espera un momento..." , "correo_o_numero_verificacion", temp_dict)

                            for i in temp_dict[user]["res"]:

                                scrapper.driver.find_element(By.CSS_SELECTOR, 'input[type="password"]').send_keys(i)

                                time.sleep(0.5)
                            
                            #Cuidado aqui! No termine de localizar el boton para continuar, este lo agrego porque creo que funcionará
                            scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-tti-phase="-1"][data-focusable="true"][data-type="container"][tabindex="0"]')[1].click()

                        except:

                            pass
                        

                    except:
                        pass

        except:
            pass


        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))

        try:
            
            bot.send_message(user, "🆕 Mensaje de Información\n\nMuy Bien, Ya accedí a Facebook :D")
            # scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="main"]')))
            print("Se cargaron cookies ")
            return ("ok", "login con cookies exitosamente", temp_dict[user]["cookies_dict"])
    
        except Exception as er:
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
            raise Exception("ID usuario: "+ str(user) + "\n\nDescripción del error:\n" + str(format_exc()))
    
    else:
        print("Se cargaron cookies_2")
        return ("ok", "login con cookies exitosamente", temp_dict[user]["cookies_dict"])
        

def captcha(scrapper: s, user, bot: telebot.TeleBot):
    try:
        if "captcha" in  scrapper.driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src"):
            
            while True:
                #el enlace del captcha cambia cuando se introduce uno erróneo, ya que se vuelve a generar uno nuevo desde una dirección diferente
                temp_dict[user]["url_captcha"] = scrapper.driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src")
                #Esperar a que la foto se muestre adecuadamente en la pantalla para que selenium pueda hacerle captura
                scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh")))
                
            
                handlers(bot, user, "ATENCION!\nHa aparecido un captcha!\n\nIntroduce el código proporcionado en la foto CORRECTAMENTE para continuar...", "captcha", temp_dict, file=telebot.types.InputFile(make_captcha_screenshoot(scrapper.driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh"), user)))
                                   
                
                for i in temp_dict[user]["res"]:
                    scrapper.driver.find_element(By.CSS_SELECTOR, "input#«r1»").send_keys(i)
                    time.sleep(0.5)
                
                #click en continuar    
                
                scrapper.driver.find_elements(By.CSS_SELECTOR, "span.x1lliihq.x193iq5w.x6ikm8r.x10wlt62.xlyipyv.xuxw1ft")[-1].click()
                
                try:
                    
                    scrapper.wait.until(ec.url_changes(scrapper.driver.current_url))
                    
                except:
                    pass
                    
                finally:
                    try:                                   
                        if "captcha" in  scrapper.driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src"):
                            
                            if scrapper.driver.find_element(By.CSS_SELECTOR, "img.xz74otr.x168nmei.x13lgxp2.x5pf9jr.xo71vjh").get_attribute("src") != temp_dict[user]["url_captcha"]:
                                
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
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
        raise Exception("ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(format_exc()))
    
def loguin(scrapper: s, user, bot, **kwargs):

    """
    Si no se proporciona un user_id, se creará uno nuevo
    
    Hace loguin en Facebook, determinará si hacer loguin desde cero o no si se le proporciona un user y si hay algún archivo de ese usuario en la BD
    """
    
    global temp_dict
    

    if list(filter(lambda file: file == "cookies.pkl", os.listdir(user_folder(user)))):
        
        # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nHay cookies de la sesion, voy a cargarlas.\n\nEspere un momento...", chat_id=user, message_id=temp_dict[user]["info"].message_id)
        
        bot.send_message(user, "🆕 Mensaje de Información\n\nHay cookies de la sesion, voy a cargarlas.\n\nEspere un momento...")
        
        temp_dict[user]["res"] = cargar_cookies(scrapper, user, bot)    
        if temp_dict[user]["res"][0] == "error":
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
            raise Exception(temp_dict[user]["res"])
        

        if not collection.find_one({"telegram_id": user}):
            collection.insert_one({"_id": int(time.time()), "telegram_id": user})
            guardar_cookies(scrapper, user)
        
        return temp_dict[user]["res"]
    
    else:
        if collection.find_one({"telegram_id": user}):
            temp_dict[user]["res"] = collection.find_one({"telegram_id": user})
            if temp_dict[user]["res"].get("cookies"):
                guardar_cookies(scrapper, user, cookiespkl=temp_dict[user]["res"]["cookies"])
                return loguin(scrapper, user, bot)

            else:
                return loguin_cero(scrapper, user, bot)

        else:

            collection.insert_one({"_id": int(time.time()), "telegram_id": user})
                
            return loguin_cero(scrapper, user, bot)
            
                
        
    


# input.x1s85apg => Input para enviar los videos

def cookies_caducadas(scrapper: s, user, bot):
    global temp_dict
    
    if scrapper.driver.find_element(By.CSS_SELECTOR, 'div[class="_45ks"]'):
        temp_dict[user]["perfiles"] = scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[class="removableItem _95l5 _63fz"]')
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
            

                        
            scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'input[id="pass"][type="password"]')))[-1].send_keys(temp_dict[user]["password"])
            
            
            try:
                e = scrapper.driver.find_element(By.CSS_SELECTOR, 'input#email"')
                
            except:
                e = None
                
            if e:
                handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", temp_dict)
                

                
                scrapper.driver.find_element(By.CSS_SELECTOR, 'input#email"').send_keys(temp_dict[user]["user"])

            
            
            try:
                #click para recordar contraseña
                scrapper.driver.find_element(By.CSS_SELECTOR, 'span[class="_9ai8"]').click()
            
            except NoSuchElementException:
                pass
            
            #click en iniciar sesión
            scrapper.driver.find_elements(By.CSS_SELECTOR, 'button[name="login"]')[-1].click()
            scrapper.wait.until(ec.url_changes(scrapper.driver.current_url))
            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
            temp_dict[user]["res"] = captcha(scrapper, user, bot)
            if temp_dict[user]["res"] == "error":
                print(temp_dict[user]["res"][1])
                
            elif temp_dict[user]["res"][0] in ["ok", "no"]:
                guardar_cookies(scrapper, user)
                break

            elif scrapper.driver.find_element(By.CSS_SELECTOR, 'div[class="mvm _akly"]'):
                print("¡Contraseña incorrecta! ¡vuelve a intentarlo!")
                scrapper.driver.back()
                continue

def loguin_cero(scrapper: s, user, bot : telebot.TeleBot, load_url=True, **kwargs):
    global temp_dict
    print("Estoy usando el loguin desde cero")
    
    temp_dict[user] = {}
    
    def doble_auth(scrapper: s , user, bot: telebot.TeleBot):
        global temp_dict

        def doble_auth_codigo(scrapper: s , user, bot: telebot.TeleBot, temp_dict):
        # e = scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))

            try:
                #Si este elemento no está es que aún está en el loguin debido a que los datos introducidos fueron incorrectos (es el mismo de arriba)
                scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.ViewTransformsExtension"][data-bloks-visibility-state="entered"]')[3].click()

            except:

                scrapper.driver.find_element(By.CSS_SELECTOR, "input#m_login_password")
                info_message("Has introducido tus datos de loguin incorrectamente...\nPor favor, vuelve a intentarlo luego del próximo mensaje", bot, temp_dict, user)
                
                del temp_dict[user]["user"]
                del temp_dict[user]["password"]

                return loguin_cero(scrapper, user, bot)
            
            
            scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[role="radio"][data-bloks-name="bk.components.Flexbox"]')))
            
            
            scrapper.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'div[role="radio"][data-bloks-name="bk.components.Flexbox"]')))

            #aqui le doy click a el metodo de auth que en este caso sería por codigo de respaldo
            scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[role="radio"][data-bloks-name="bk.components.Flexbox"]')[3].click()

            #le doy click a continuar
            scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"][tabindex="0"]')[1].click()

            #el siguiente elemento es el input en el que va el código
            scrapper.wait.until(ec.element_to_be_clickable((By.CSS_SELECTOR, 'input[inputmode="numeric"]')))
            
            temp_dict[user]["e"] = scrapper.driver.find_element(By.CSS_SELECTOR, 'input[inputmode="numeric"]')
            
            
            handlers(bot, user, "A continuación, introduce uno de los códigos de respaldo de Facebook\n\n(Estos códigos son de 8 dígitos numéricos y puedes obtenerlos en el centro de cuentas en los ajustes de tu cuenta de Facebook)" , "codigo_respaldo", temp_dict, markup=ForceReply())
            
            #para borrar los espacios en el codigo de respaldo
            if re.search(r"\D", temp_dict[user]["res"].text):
                temp_dict[user]["res"].text = temp_dict[user]["res"].text.replace(re.search(r"\D+", temp_dict[user]["res"].text).group(), "")

            for i in temp_dict[user]["res"].text:
                temp_dict[user]["e"].send_keys(i)
                time.sleep(0.5)
            
            
            print("he ingresado los códigos")
            temp_dict[user]["url_actual"] = scrapper.driver.current_url
            

            #click en el boton de continuar
            scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.ViewTransformsExtension"][data-bloks-visibility-state="entered"]')[4].click()
            print("click en el boton de continuar")
            
            
            
            try:
                #este mensaje se muestra cuando el código es incorrecto
                if scrapper.wait_s.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'span[data-bloks-name="bk.components.TextSpan"]')) > 8)):
                    bot.send_message(user, "🆕 Mensaje de Información\n\nHas Introducido un código incorrecto!\n\nEspera un momento para volver a intentarlo...")
                    
                    return loguin_cero(scrapper, user, bot)
                    
            except:
                pass
            
            # #esperar a que no esté el botón
            # scrapper.wait.until(ec.invisibility_of_element_located((By.CSS_SELECTOR, 'div[class="xod5an3 xg87l8a"]')))
            
            
            
            
            return "ok"
        

        def doble_auth_email_verification(scrapper: s, user, bot, temp_dict):
            
            temp_dict[user]["url_actual"] = scrapper.driver.current_url
                    
            scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "Get a new code")]').click()

            # temp_dict[user]["email"] = scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "code we sent")]').text.split("to")[-1].strip()

            # print("Email a enviar codigo: " + temp_dict[user]["email"])

            handlers(bot, user, "A continuación, ingresa el código númerico que ha sido enviado al email vinculado a esta cuenta para finalizar el loguin...","email_verification", temp_dict)

            scrapper.driver.find_element(By.CSS_SELECTOR, 'input').send_keys(temp_dict[user]["res"].strip())


            scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "Continue")]').click()

            return "ok"


        scrapper.wait.until(ec.any_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.ViewTransformsExtension"][data-bloks-visibility-state="entered"]')) >= 4, ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "Check your email")]'))))

        try:
            if scrapper.driver.find_element(By.By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.ViewTransformsExtension"][data-bloks-visibility-state="entered"]') >= 4:
                temp_dict[user]["doble"] = True
                
        except:
            pass

        else:
            print("Haremos la doble autenticación con los códigos de recuperación")
            doble_auth_codigo(scrapper, user, bot, temp_dict)
                
        


        try:
            if scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "Check your email")]'):
                temp_dict[user]["doble"] = True                
        
        except:
            pass
        
        else:
            print("Haremos la doble autenticación enviando el código al correo")
            doble_auth_email_verification(scrapper, user, bot, temp_dict)
        
        

        if not temp_dict[user].get("doble"):
            raise Exception("Abriste la funcion de doble autenticacion pero realmente no habia...que paso?")
        
        try:
            temp_dict[user]["doble"] = False

            print("cambiar la url a la de save-device")
            scrapper.wait.until(ec.url_changes(temp_dict[user]["url_actual"]))
            print("ha cambiado!")

        except:
            pass


        #sustituto de remember_browser
        try:
            if scrapper.driver.find_element(By.CSS_SELECTOR, 'div#screen-root'):

                bot.send_message(user, "🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto")
        
                return ("ok", "se ha dado click en confiar dispositivo")
        
        except Exception as err:

            if not "save-device" in scrapper.driver.current_url:
            
            
                bot.send_message(user, "🆕 Mensaje de Información\n\nHas Introducido un código incorrecto! Vuelve a intentarlo!")
                
                
                return doble_auth(scrapper, user, bot)


            raise err
            
        

        
        #click en confiar en este dispositivo
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]')))
        scrapper.driver.find_element(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]').click()

        # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto", chat_id=user, message_id=temp_dict[user]["info"].message_id)     
        
        bot.send_message(user, "🆕 Mensaje de Información\n\nOk, el codigo introducido es correcto")
        
        return ("ok", "se ha dado click en confiar dispositivo")
            

            
            


    
    
    if load_url:

        if os.name == "nt":
            try:
                scrapper.driver.get("https://m.facebook.com/login/")
            except:
                pass
            
            while True:
                
                try:
                    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                    break
                except:
                    pass
                
        else:
            scrapper.driver.get("https://facebook.com")
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
    
    #-----------------obtener usuario para loguin---------------
    try:
        scrapper.wait.until(ec.visibility_of_element_located((By.ID, "m_login_email")))
        # temp_dict[user]["e"] = driver.find_element(By.ID, "m_login_email")
        temp_dict[user]["e"] = scrapper.driver.find_elements(By.CSS_SELECTOR, "input")[0]

    except:
        #A veces aparecerá una presentacion de unirse a facebook, le daré a que ya tengo una cuenta...
        scrapper.driver.find_element(By.XPATH, '//*[contains(text(), "I already have an account")]').click()

    
    scrapper.wait.until(ec.visibility_of_element_located((By.ID, "m_login_email")))

    if not temp_dict[user].get("user"):
        handlers(bot, user, "Introduce a continuación tu <b>Correo</b> o <b>Número de Teléfono</b> (agregando el código de tu país por delante ej: +53, +01, +52, etc) con el que te autenticas en Facebook: ", "user", temp_dict)


    temp_dict[user]["e"].send_keys(temp_dict[user]["user"])
    
    
    #-----------------obtener password para loguin---------------
    scrapper.wait.until(ec.visibility_of_element_located((By.ID, "m_login_password")))
    # temp_dict[user]["e"] = driver.find_element(By.ID, "m_login_password")
    temp_dict[user]["e"] = scrapper.driver.find_elements(By.CSS_SELECTOR, "input")[1]
    
    if not temp_dict[user].get("password"):
        handlers(bot, user, "Introduce a continuación la contraseña", "password", temp_dict)
    

    temp_dict[user]["url_actual"] = scrapper.driver.current_url
    
    temp_dict[user]["e"].send_keys(temp_dict[user]["password"])
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-anchor-id="replay"]')))

    scrapper.driver.find_element(By.CSS_SELECTOR, 'div[data-anchor-id="replay"]').click()
    
    try:
        scrapper.wait.until(ec.url_changes(temp_dict[user]["url_actual"]))
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'body')))
    except:
        pass
    


    
    
    try:
        #cuando no introduces bien ninguno de tus datos:
        if scrapper.driver.find_element(By.CSS_SELECTOR, 'div[class="wbloks_73"]'):
            
            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Al parecer los datos que me has enviado son incorrectos\nTe he enviado una captura de lo que me muestra Facebook\n\nPor favor ingrese <b>correctamente</b> sus datos otra vez...")
            del temp_dict[user]
            return loguin_cero(scrapper, user, bot)
            
    except:
        pass

    print("Tendrá doble auth?")
    if scrapper.driver.current_url.endswith("#"):
        print("Si, si tiene")
        temp_dict[user]["res"] = doble_auth(scrapper, user, bot)
        if "No se ha podido dar click en el botón de doble autenticación" in temp_dict[user]["res"][-1]:
                        
            temp_dict[user]["res"] = captcha(scrapper, user, bot)
            if temp_dict[user]["res"][0] == "error":
                raise Exception(temp_dict[user]["res"][1])
            
            if "two_factor" in scrapper.driver.current_url:
                #doble auntenticación
                temp_dict[user]["res"] = doble_auth(scrapper, user, bot)
                if temp_dict[user]["res"][0] == "error":
                    raise Exception(temp_dict[user]["res"][1])
                
        else:
            pass
            
            
    
    try:
        
        print("Pues no, no tiene")
        print("Voy a esperar a que salga la main page de facebook")
        # if scrapper.wait.until(ec.all_of(lambda driver: driver.find_element(By.CSS_SELECTOR, 'div[role=button][data-mcomponent="MContainer"][data-action-id="32746"]') and not "save-device" in driver.current_url)):
        if scrapper.wait.until(ec.all_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[data-tti-phase="-1"][role="button"][tabindex="0"][data-focusable="true"][data-mcomponent="MContainer"][data-type="container"]')) >= 3 and not "save-device" in driver.current_url)):
            
            guardar_cookies(scrapper, user, loguin={"user": temp_dict[user]["user"], "password": temp_dict[user]["password"]})

            print("He guardado las cookies")
            
            return ("ok", "loguin desde cero satisfactorio :)")
        
        
    except Exception as e:
        # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo", chat_id=user, message_id=temp_dict[user]["info"].message_id) 

        if "save-device" in scrapper.drive.current_url:

            scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]')))

            scrapper.drive.find_element(By.CSS_SELECTOR, 'div[data-bloks-name="bk.components.Flexbox"][role="button"]').click()

            scrapper.wait.until(ec.all_of(lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[data-tti-phase="-1"][role="button"][tabindex="0"][data-focusable="true"][data-mcomponent="MContainer"][data-type="container"]')) >= 3 and not "save-device" in driver.current_url))

            guardar_cookies(scrapper, user, loguin={"user": temp_dict[user]["user"], "password": temp_dict[user]["password"]})

            print("He guardado las cookies")
            
            return ("ok", "loguin desde cero satisfactorio :)")

        temp_dict[user]["res"] = make_screenshoot(scrapper.drive, user)
        
        bot.send_photo(user, telebot.types.InputFile(temp_dict[user]["res"]) , "🆕 Mensaje de Información\n\nNo has introducido tus datos correctamente, vuelve a intentarlo")

        del temp_dict[user]["user"]
        del temp_dict[user]["password"]

        return loguin_cero(scrapper, user, bot)
        
        
def publicacion(scrapper: s, bot:telebot.TeleBot, url, user, load_url=True, contador = 0, **kwargs):
    global temp_dict
    
    # temp_dict[user]["info"] = bot.edit_message_text(text="🆕 Mensaje de Información\n\nEstoy accediendo a la publicación del enlace que me proporcionaste...", chat_id=user, message_id=temp_dict[user]["info"].message_id)    
    
    
    bot.send_message(user, "🆕 Mensaje de Información\n\nEstoy accediendo a la publicación del enlace que me proporcionaste..." )
    
    temp_dict[user]["a"] = ActionChains(scrapper.driver, duration=0)
    
    if load_url:
        
        if os.name == "nt":
            try:
                scrapper.drive.get(url)
            except:
                pass
            
            while True:
                try:
                    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "body")))
                    break
                except:
                    pass
                
        else:
            scrapper.drive.get(url)
                
        
        time.sleep(5)
        print("Cargué el enlace proporcionado: {}".format(url))

    
    if not kwargs.get("temp_dic"):
        temp_dict[user]["publicacion"] = {"publicados" : [], "error" : []}
        
    else:
        temp_dict[user]["publicacion"] = kwargs.get("info_publicacion")
    
    #bucle para publicar por los grupos
    while True:
        
            
        # if contador != 0:
        #     #aqui compruebo que la ventana de compartir ya no esté interrumpiendo
        #     try:
        #         scrapper.wait.until(ec.visibility_of_element_located((By.XPATH, '//div[contains(@aria-label, "share")]')))
                
        #     except:
        #         raise Exception("Facebook me bloqueó?")
            
        
        # scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))


        #esperar el botón de compartir
        print("Buscaré el boton de compartir")
        try:
            temp_dict[user]["res"] = {1: scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//div[contains(@aria-label, "share")]')))}

        except:
            temp_dict[user]["res"] = {2: scrapper.wait_s.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-type="vscroller"]')))}

            
        #elemento de compartir existe
        if temp_dict[user]["res"].get(1):       
        
            temp_dict[user]["contador"] = 0

            while True:
                scrapper.drive.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.HOME)

                
                try:
                    print("buscando el elemento de compartir...")
                    temp_dict[user]["a"].scroll_by_amount(0, scrapper.drive.find_element(By.XPATH, '//div[contains(@aria-label, "share")]').location["y"] - scrapper.drive.find_element(By.XPATH, '//div[contains(@aria-label, "share")]').rect["height"] * 4).perform()
                
                #hay veces que la página se corrompe y no existe dicha publicación, con esto lo controlo iniciando un valor para cargar nuevamente la página
                except:
                    print("La página está corrupta, buscaré el elemento 'feed'")
                    scrapper.wait_s.until(ec.visibility_of_element_located((By.XPATH, '//*[contains(text(), "feed")]')))
                    

                    print("Encontré el elemento, volveré a cargarla")
                    temp_dict[user]["cargar"] = True

                    # El número de intentos límite es de 3
                    if temp_dict[user].get("cargar_limite"):
                        if temp_dict[user].get("cargar_limite") >= 3:
                            
                            raise Exception("Parece que la página de la publicación a compartir se ha corrompido")
                    
                        else: 
                            temp_dict[user]["cargar_limite"] += 1
                    

                    else:
                        temp_dict[user]["cargar_limite"] = 1
                    
                    
                    return publicacion(scrapper, bot, url, user, contador = contador, kwargs=kwargs)

                time.sleep(4)

                try:

                    scrapper.driver.find_element(By.XPATH, '//div[contains(@aria-label, "share")]').click()
                    temp_dict[user]["contador"] = 0
                    break

                except Exception as err:
                    temp_dict[user]["contador"] += 1

                    if temp_dict[user]["contador"] >= 4:
                        raise err

                    scrapper.driver.find_element(By.CSS_SELECTOR, 'body').send_keys(Keys.HOME)




            #click en el boton de compartir en la publicacion
            print("Le he dado click en el botón Compartir")
            

            
            try:

                temp_dict[user]["url_actual"] = scrapper.driver.current_url

                #elemento de los grupos
                scrapper.wait.until(ec.all_of(
                    lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[role="presentation"][class="m"]')) >= 5, 

                    lambda driver: len(driver.find_elements(By.CSS_SELECTOR, 'div[role="presentation"][class="m"]')[4].find_elements(By.CSS_SELECTOR, 'div[role="button"]')) >= 6))
                

            except:
                pass

            try:
                temp_dict[user]["e"] = scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[role="presentation"][class="m"]')[4].find_elements(By.CSS_SELECTOR, 'div[role="button"]')[5]

            except IndexError:
                temp_dict[user]["e"] = scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[role="presentation"][class="m"]')[4].find_element(By.XPATH, '//*[contains(text(), "gr")]')

            #click en compartir en grupos
            time.sleep(8)
            temp_dict[user]["e"].click()

            try:
                WebDriverWait(scrapper.driver, 5).until(ec.invisibility_of_element_located(temp_dict[user]["e"]))
            except:
                pass
            
            print("Click en Compartir Grupos")
            
            
            scrapper.wait.until(ec.url_changes(temp_dict[user]["url_actual"]))




        #obtener grupos
        print("Obteniendo grupos")
        scrapper.wait.until(ec.any_of(lambda driver: driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]')))

        temp_dict[user]["lista_grupos"] = scrapper.driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-focusable="true"]')
             
        
        if not temp_dict[user]["lista_grupos"]:
            
            give_error(bot, scrapper.driver, user, "¡No hay ningún grupo al que publicar!\n\nDescripcion del error:\n" + str(format_exc()))
        
        #si ya recorrimos todos los elementos de la lista...
        while len(temp_dict[user]["lista_grupos"]) < contador + 1:

            #apuntando el cursor encima de los grupos
            temp_dict[user]["a"].move_to_element(scrapper.driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]')).perform()
            
            #por alguna razón, cuando lo pruebo en el debugger esta linea me da error con la variable 'temp_dict[user]["lista_grupos"]' que almacena los grupos asi que lo pongo en un try-except
            
            hacer_scroll(scrapper.driver, user, temp_dict, temp_dict[user]["lista_grupos"], temp_dict[user]["lista_grupos"][-1], (contador + 1) // 9)

            
            
            temp_dict[user]["a"].scroll_from_origin(ScrollOrigin.from_element(temp_dict[user]["lista_grupos"][-1]), 0 , 50).perform()
            
            try:
                scrapper.wait_s.until(ec.any_of(lambda driver: len(temp_dict[user]["lista_grupos"]) < len(driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-focusable="true"]'))))
                
            except:
                pass
            
            #si ya se recorrieron todos los grupos y la lista de grupos guardada es igual a la que resulta de la búsqueda entonces se terminó exitosamente de publicar
            

            if len(temp_dict[user]["lista_grupos"]) == len(scrapper.driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-focusable="true"]')):
                
                try:
                    bot.unpin_chat_message(temp_dict[user]["info"].chat.id, temp_dict[user]["info"].message_id)
                except:
                    pass
                
                return ("ok", "Se ha publicado exitosamente en " + str(len(temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)")
            
            # si la lista de grupos guardada es menor a la nueva resultante de la busqueda, entonces se actualiza los elementos de la lista de grupos y se continua
            else:
                temp_dict[user]["lista_grupos"] = scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-focusable="true"]')))

                temp_dict[user]["lista_grupos"] = scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-type="vscroller"]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-focusable="true"]')
      
        
        
        
        # temp_dict[user]["a"].move_to_element(driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]')).perform()


        hacer_scroll(scrapper.driver, user, temp_dict, temp_dict[user]["lista_grupos"], temp_dict[user]["lista_grupos"][contador], (contador + 1) // 9)
        

        temp_dict[user]["publicacion"]["nombre"] = temp_dict[user]["lista_grupos"][contador].text
        # time.sleep(2)



        # scrapper.wait.until(ec.any_of(lambda driver: driver.find_element(By.CSS_SELECTOR, 'div[data-type="vscroller"]').find_elements(By.CSS_SELECTOR, 'div[data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-focusable="true"]')[1].text))

        try:
            temp_dict[user]["lista_grupos"][contador].click()
        except:
            print("Error intentando clickear en el grupo? Lo volveré a intentar")
            temp_dict[user]["a"].scroll_to_element(temp_dict[user]["lista_grupos"][contador]).perform()
            temp_dict[user]["a"].scroll_from_origin(ScrollOrigin.from_element(temp_dict[user]["lista_grupos"][contador]), 0 , -200).perform()
            temp_dict[user]["lista_grupos"][contador].click()

        
        def obtener_texto(temp_dict, error: bool):
            
            try:
                temp_dict[user]["info"] = bot.edit_message_text("✅Se ha publicado en: " + str(len(temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)\n❌Se han producido errores en: " + str(len(temp_dict[user]["publicacion"]["error"])) + " grupo(s)", user, temp_dict[user]["info"].message_id)
            except:
                temp_dict[user]["info"] = bot.send_message(user, "✅Se ha publicado en: " + str(len(temp_dict[user]["publicacion"]["publicados"])) + " grupo(s)\n❌Se han producido errores en: " + str(len(temp_dict[user]["publicacion"]["error"])) + " grupo(s)")
            
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
        
        #si la ventana se mantiene...
        temp_dict[user]["publicacion"]["publicados"].append(temp_dict[user]["publicacion"]["nombre"])
        temp_dict[user]["res"] = obtener_texto(temp_dict, False)
        
        if temp_dict[user]["res"][0] == "nuevo":
            temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, temp_dict[user]["res"][1])

        else:

            try:
                temp_dict[user]["publicacion"]["msg_publicacion"] = bot.edit_message_text(temp_dict[user]["res"][1] , user, temp_dict[user]["publicacion"]["msg_publicacion"].message_id)

            except:
                temp_dict[user]["publicacion"]["msg_publicacion"] = bot.send_message(user, temp_dict[user]["res"][1])
            
            
            
            
        
        
        #esperar a que aparezca el elemento de 'Publicar' 
        try:
            
            scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[role="button"][data-mcomponent="ServerTextArea"][data-type="text"]')))

            temp_dict[user]["res"] = ("ok", scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[role="button"][data-mcomponent="ServerTextArea"][data-type="text"]')[4])
            
        except:
            temp_dict[user]["res"] = ("error", "NO se pudo localizar el boton para publicar en los grupos")
        
        
        if temp_dict[user]["res"][0] == "error":
            give_error(bot, scrapper.driver, user, "ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(temp_dict[user]["res"][1]))
            return


        
        try:
            #click en publicar
            time.sleep(8)
            temp_dict[user]["res"][1].click()
            print("Publiqué exitosamente en: " + str(temp_dict[user]["publicacion"]["nombre"]))

            #cambiar descomentar para pruebas, este es el boton para cerrar la ventana de publicacion
            # driver.find_element(By.CSS_SELECTOR, 'div[class="xurb0ha"]').click()
        
        except:

            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user))) 
            return ("error" , "¿Facebook me habrá bloqueado?")
        
        
        
        
        contador += 1

        if temp_dict[user].get("cargar"):
            return publicacion(scrapper, bot, url, user, contador = contador, kwargs=kwargs)
            
                  
                

def elegir_cuenta(scrapper: s, user, bot , ver_actual=False):
    global temp_dict
    print("estoy dentro de la funcion de elegir la cuenta")
    
    scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))
    
    try:
        #si ya el menú de cuentas está desplegado... hay que omitir cosas
        temp_dict[user]["e"] = scrapper.driver.find_element(By.CSS_SELECTOR, 'div[role="list"]')

        temp_dict[user]["e"] = True
        
    except: 
        temp_dict[user]["e"] = False
        
    if not temp_dict[user]["e"]:  
        print("Voy a esperar a que salga el menu de cuentas")

        #este elemento es el de los ajustes del perfil (las 3 rayas de la derecha superior)
        temp_dict[user]["res"] = esperar(scrapper,'div[data-tti-phase="-1"][role="button"][tabindex="0"][data-focusable="true"][data-mcomponent="MContainer"][data-type="container"]', 2)

        temp_dict[user]["res"][1].click()

        #Elemento de Configuracion de cuenta
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))



        print("comprobaré si sale el botón de seleccionar otros perfiles, si es que hay")
        #Flecha para ver otros perfiles/cambiar
        
        scrapper.wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]')))

        temp_dict[user]["res"] = esperar(scrapper, 'div[tabindex="0"][role="button"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"][class="m"]', 3)


        if temp_dict[user]["res"][0].lower() == "error":
            

            temp_dict[user]["res"] = esperar(scrapper, 'div[role="button"][tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-mcomponent="MContainer"][data-type="container"]', 3)

            if temp_dict[user]["res"][0] == "error":

                raise Exception("No se pudo encontrar el desplegable para ver otros perfiles de la misma cuenta")


        temp_dict[user]["res"][1].click()
        
        temp_dict[user]["res"] = ("ok", "han salido")
        print("Click en ver todos los perfiles")
            
                
    

    
    
      
    
   
        

    #esperar a que salgan las cuentas
    # padre => "div.x1gslohp"
    print("Esperaré a que salgan todas las cuentas en el navegador")

    #este elemento es el padre de las cuentas, concretamente el 2do elemento en el html
    esperar(scrapper, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]', 1)


    print("Obteniendo los elementos de las cuentas...")


    temp_dict[user]["cuentas"] = scrapper.driver.find_elements(By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')[1].find_elements(By.CSS_SELECTOR, 'div[role="button"][tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-type="container"][data-mcomponent="MContainer"]')

    temp_dict[user]["cuentas"].remove(temp_dict[user]["cuentas"][0])

    
    #ahora quitaré el elemento que dice "Crear Perfil"
    for e, i in enumerate(temp_dict[user]["cuentas"]):

        try:
            if i.find_element(By.CSS_SELECTOR, 'img'):
                continue

        except:
            temp_dict[user]["cuentas"].remove(temp_dict[user]["cuentas"][e])
    
    if len(temp_dict[user]["cuentas"]) == 1:
        return ("ok", temp_dict[user]["cuentas"][0].text.split("\n")[0], "uno")

    
    
    
    if not ver_actual:
        
        print("Creando el teclado del mensaje...")
        temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, input_field_placeholder="Elige un perfil")
        temp_dict[user]["perfiles"] = []
    
        for e,cuenta in enumerate(temp_dict[user]["cuentas"], 1):     
            
            temp_dict[user]["perfiles"].append(cuenta.text.split("\n")[0])
            
            temp_dict[user]["teclado"].add(cuenta.text.split("\n")[0])               
            

                        
        print("Ahora elige la cuenta...")
        handlers(bot, user, "Cual de los perfiles de esta cuenta quieres usar?", "perfil_elegir", temp_dict, markup=temp_dict[user]["teclado"])
        
        temp_dict[user]["cuentas"][temp_dict[user]["res"]].click() 
        print("cuenta elegida!")
        scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, "div#screen-root")))
        guardar_cookies(scrapper, user)
        

        return ("ok", temp_dict[user]["perfiles"][temp_dict[user]["res"]])
        
    else:
        #para ver el perfil actual
        return ("ok", temp_dict[user]["cuentas"][0].text.split("\n")[0])
            


                     


    

    
    
    
        
        
def main(scrapper: s, bot: telebot.TeleBot, user, link_publicacion):
    """
    This function will do all the scrapping requesting to other functions and makes for sure that all is ok
    
    bot: instance of telebot
    user : telegram's user_id
    """
    global temp_dict

    temp_dict[user] = {}
    
    comprobar_BD(collection)
    
    temp_dict[user]["info"] = bot.send_message(user, "🆕 Mensaje de Información\n\nTe estaré informando acerca de la operación con este mensaje :)", reply_markup=telebot.types.ReplyKeyboardRemove())

    try:

        temp_dict[user]["res"] = loguin(scrapper, user, bot)
        if temp_dict[user]["res"][0] == "error":
            
            if "base de datos" in temp_dict[user]["res"][1]:

                bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)))
                raise Exception(temp_dict[user]["res"][1])
                
            raise Exception("Ha ocurrido un error en el loguin!\n\nDescripción:\n" + str(temp_dict[user]["res"][1]))
        
    except:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
        raise Exception("error intentando hacer loguin\nID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(format_exc()))

    print("Empezaré a comprobar si hay algún error luego del loguin")

    
            
    try:
        #comprobando estar en el inicio de la mainpage de facebook
        temp_dict[user]["e"] = scrapper.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div#screen-root')))

    except:
        temp_dict[user]["e"] = None

        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
        raise Exception("ID usuario: " + str(user) + "\nFaltó algo :(")
    

    print("A continuación miraré cual es la cuenta actual")    
    try:
        temp_dict[user]["res"] = elegir_cuenta(scrapper , user, bot, ver_actual=True)
        if temp_dict[user]["res"][0] == "error":

            bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "ID usuario: " + str(user) + "\n\nDescripción:\n" + str(temp_dict[user]["res"][1]))
            raise Exception("no")
        
        if not len(temp_dict[user]["res"]) == 3:
        
            temp_dict[user]["teclado"] = ReplyKeyboardMarkup(True, True, row_width=1, input_field_placeholder="¿Quieres cambiar a otro perfil?").add("Si", "No")
            

            handlers(bot, user, "El perfil actual es: <b>" + str(temp_dict[user]["res"][1]) + "</b>\n\n¿Quieres cambiar de perfil?", "perfil_pregunta", temp_dict, markup=temp_dict[user]["teclado"])

            
            
            if temp_dict[user]["res"].text.lower() == "si":
                temp_dict[user]["res"] = elegir_cuenta(scrapper, user, bot)
                if temp_dict[user]["res"][0] == "error":

                    bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
                    raise Exception("ID usuario: " + str(user) + "\n\nDescripción del error:\n" + str(temp_dict[user]["res"][1]))
                else:
                    # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nHe cambiado al perfil de: {temp_dict[user]["res"][1]}", chat_id=user, message_id=temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())
                    
                    bot.send_message(user, "🆕 Mensaje de Información\n\nHe cambiado al perfil de:  <b>" + str(temp_dict[user]["res"][1]) + "</b>\n\nLoguin completado exitosamente!", reply_markup=telebot.types.ReplyKeyboardRemove())

            else:
                # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nMuy bien, continuaré con el perfil actual", chat_id=user, message_id=temp_dict[user]["info"].message_id, reply_markup=telebot.types.ReplyKeyboardRemove())

                bot.send_message(user, "🆕 Mensaje de Información\n\nMuy bien, continuaré con el perfil actual\n\nLoguin completado exitosamente!", reply_markup=telebot.types.ReplyKeyboardRemove())
        else:
            bot.send_message(user, "Al parecer, solamente está el perfil de: " + str(temp_dict[user]["res"][1]) +"\n\nContinuaré con ese...")
        
    except:
        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
        raise Exception("Ha ocurrido un error intentando ver la cuenta actual! ID usuario: " + str(user) + "\n\nMensaje de error:\n" + str(format_exc()))
    
        

    
            
    temp_dict[user]["res"] = guardar_cookies(scrapper, user)    

    # temp_dict[user]["info"] = bot.edit_message_text(text=f"🆕 Mensaje de Información\n\nLoguin completado exitosamente!", chat_id=user, message_id=temp_dict[user]["info"].message_id)

    
    try:
        temp_dict[user]["res"] = publicacion(scrapper, bot , link_publicacion, user)
        
        if temp_dict[user]["res"][0] == "error":
            print(temp_dict[user]["res"][1])
            
        elif temp_dict[user]["res"][0] == "ok":
            bot.send_message(user, temp_dict[user]["res"][1])

    except:

        bot.send_photo(user, telebot.types.InputFile(make_screenshoot(scrapper.driver, user)), "Captura del error")
        raise Exception("Ha ocurrido un error intentando ver la cuenta actual! ID usuario: " + str(user) + "\n\nMensaje de error:\n" + str(format_exc()))



    
    return 







