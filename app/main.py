import os
import telebot
from telebot.types import *
import f_src
import sys
import dill
import re
from traceback import format_exc
import threading
from flask import Flask, request
import subprocess
from pymongo import MongoClient
from f_src import facebook_scrapper
from f_src.usefull_functions import *
import requests

"""
-------------------------------------------------------
Variables de Entorno a Definir:
-------------------------------------------------------
token = token del bot
admin = ID del administrador del bot
MONGO_URL = Enlace del cluster de MongoDB (Atlas)
webhook_url = Si esta variable es definida se usará el metodo webhook, sino pues se usara el método polling
"""



cola = {}
cola["cola"] = []
cola["uso"] = False
admin = os.environ["admin"]

if not "MONGO_URL" in os.environ:
    MONGO_URL = "mongodb://localhost:27017"
else:
    MONGO_URL = os.environ["MONGO_URL"]



cliente = MongoClient(MONGO_URL)
db = cliente["face"]
collection = db["usuarios"]


telebot.apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(os.environ["token"], "html",)

bot.set_my_commands([
    BotCommand("/start", "Información sobre el bot"),
    BotCommand("/publicar", "Empieza a publicar en Facebook :)")
])

bot.send_message(os.environ["admin"], "El bot de publicaciones de Facebook está listo :)")



@bot.message_handler(func=lambda message: not message.chat.id == int(os.environ["admin"]))
def not_admin(m):
    bot.send_message(m.chat.id, "No disponible para el publico")
    return

@bot.message_handler(func=lambda message: not message.chat.type == "private")
def not_private(m):
    return

@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(m.chat.id,                      
"""
HOLA :D
¿Te parece tedioso estar re publicando por TODOS tus grupos en Facebook?
No te preocupes, yo me encargo por ti ;)

Envia /publicar para comenzar

Bot desarrollado por @mistakedelalaif, las dudas o quejas, ir a consultárselas a él
""")
    return

@bot.message_handler(commands=["cookies"])
def cmd_cookies(m):
    msg = bot.send_message(m.chat.id, "A continuación envia el archivo cookies.pkl al que tienes acceso")
    bot.register_next_step_handler(msg, capturar_archivo)
    
    
def capturar_archivo(m):
    if not m.document:
        bot.send_message(m.chat.id, "Operación Cancelada")
        return
    
    with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "wb") as file:
        file.write(bot.download_file(bot.get_file(m.document.file_id).file_path))
        
    if not collection.find({"telegram_id": m.from_user.id}):
        
        with open(os.path.join(user_folder(m.from_user.id), "cookies.pkl"), "rb") as file:
            collection.insert_one({"id_": time.time(), "telegram_id": m.from_user.id, "cookies" : dill.load(file)["cookies"]})
    
    bot.send_message(m.chat.id, "Cookies capturadas :)")
    
    return
            


@bot.message_handler(commands=["publicar"])
def cmd_publish(m):
    global cola
    
    if cola["uso"]:
        bot.send_message(m.chat.id, "Al parecer alguien ya me está usando :(\nLo siento pero por ahora estoy ocupado, te avisaré cuando ya esté disponible")
        
        if not m.from_user.id in cola["cola"]:
            cola["cola"].append(m.from_user.id)
            
        return
    
    texto = (
"""A continuación ve a Facebook y sigue estos pasos para compartir la publicacion

1 - Selecciona la publicación
2 - Dale en el botón de '↪ Compartir'
3 - Luego en el menú que aparece dale a 'Obtener Enlace'
4 - Pega dicho enlace en el siguiente mensaje y envíamelo

Ahora enviame el enlace de la publicación
""")
    
    msg = bot.send_message(m.chat.id, texto, reply_markup=telebot.types.ForceReply())
    bot.register_next_step_handler(msg, get_url, texto)
    
    
def get_url(m, texto):
    global cola
    
    if cola["uso"]:
        bot.send_message(m.chat.id ,"Al parecer alguien ya me está usando :(\nLo siento pero por ahora estoy ocupado, te avisaré cuando ya esté disponible")
        
        if not m.from_user.id in cola["cola"]:
            cola["cola"].append(m.from_user.id)
            
        return
    
    
    if not m.text.lower().startswith("https://www.facebook.com"):
        msg = bot.send_message(m.chat.id, f"Este enlace no es de Facebook! Inténtalo de nuevo...\n\n{texto}")
        
        return bot.register_next_step_handler(msg, get_url, texto)
    
    
    try:
        cola["uso"] = True
        if not m.from_user.id in cola["cola"]:
            cola["cola"].insert(0, m.from_user.id)
        
        try:
            facebook_scrapper.main(bot, m.from_user.id , m.text)
            
        except Exception as e:
            print("Ha ocurrido un error! Revisa el bot, te dará más detalles")
            if "no" == str(e.args).lower():
                pass
            
            else:
                bot.send_message(m.from_user.id, "Ha ocurrido un error inesperado! Reenviale a @mistakedelalaif este mensaje\n\n<blockquote expandable>" + str(e.args[0]) + "</blockquote>")
        
        
            
        
            
            
    except:
        try:
            bot.send_message(m.chat.id, "Ha ocurrido un error inesperado! Reenviale a @mistakedelalaif este mensaje\n\n<blockquote expandable>" + format_exc() + "</blockquote>")
            
        except:
            try:
                with open(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"), "w") as file:
                    file.write(f"Ha ocurrido un error inesperado!\nID del usuario: {m.from_user.id}\n\n{format_exc()}")
                    
                with open(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"), "r") as file:
                    bot.send_document(m.from_user.id, telebot.types.InputFile(file, file_name="error_" + str(m.from_user.id) + ".txt"))
                    
                os.remove(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"))
                
            except:
                try:
                    bot.send_message(m.chat.id, "Ha ocurrido un error fatal")
                except:
                    print("ERROR FATAL:\nHe perdido la conexion a telegram :(")
                    
                
                
    
    cola["uso"] = False      
    
    if m.from_user.id in cola["cola"]:
        cola["cola"].remove(m.from_user.id)
    
    bot.send_message(m.chat.id, "Operación Terminada")
    print("He terminado con: " + str(m.from_user.id))

@bot.message_handler(func=lambda x: True)
def cmd_any(m):
    bot.send_message(m.chat.id, m.text)
    
    

app = Flask(__name__)

@app.route("/", methods=['POST', 'GET'])
def webhook():
    global dic_temp
    
    if request.method.lower() == "post":   
        
            
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            try:
                if "host" in update.message.text and update.message.chat.id in [admin, 1413725506]:
                    bot.send_message(update.message.chat.id, f"El url del host es: <code>{request.url}</code>")
                    
                    #en los host gratuitos, cuando pasa un tiempo de inactividad el servicio muere, entonces hago este GET a la url para que no muera  
                    if not list(filter(lambda i: i.name == "hilo_requests", threading.enumerate())):
                        
                        def hilo_requests():
                            while True:
                                requests.get(os.getenv("webhook_url"))
                                time.sleep(60)
                                

                        threading.Thread(target=hilo_requests, name="hilo_requests").start()

            except:
                pass
            
            bot.process_new_updates([update])       
    else:
        return f"<a href='https://t.me/{bot.user.username}'>Contáctame</a>"
        
    return f"<a href='https://t.me/{bot.user.username}'>Contáctame</a>"

@app.route("/healthz")
def check():
    return "200 OK"


def flask():
    if os.getenv("webhook_url"):
        bot.remove_webhook()
        time.sleep(2)
        bot.set_webhook(url=os.environ["webhook_url"])
    
    app.run(host="0.0.0.0", port=5000)


try:
    print(f"La dirección del servidor es:{request.host_url}")
    
except:
    hilo_flask=threading.Thread(name="hilo_flask", target=flask)
    hilo_flask.start()
    
if not os.getenv("webhook_url"):
    bot.remove_webhook()
    time.sleep(2)
    bot.infinity_polling()