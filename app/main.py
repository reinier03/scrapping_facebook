import requests
import shutil
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
from f_src.main_classes import scrapper as s
from f_src.main_classes import *



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
cola["uso"] = False
cola["cola_usuarios"] = []
# media_group_clases = {}
# usuarios = {}
## usuarios = {id_usuario_telegram : main_classes.Usuario()}

admin = int(os.environ["admin"])

if not "MONGO_URL" in os.environ:
    MONGO_URL = "mongodb://localhost:27017"
else:
    MONGO_URL = os.environ["MONGO_URL"]

cliente = MongoClient(MONGO_URL)
db = cliente["face"]
collection = db["usuarios"]
scrapper = s()


telebot.apihelper.ENABLE_MIDDLEWARE = True

bot = telebot.TeleBot(os.environ["token"], "html")

bot.set_my_commands([
    BotCommand("/start", "Información sobre el bot"),
    BotCommand("/cancel", "Cancela el proceso actual"),
    BotCommand("/publicar", "Comienza a publicar"),
    BotCommand("/delete", "Cambiar de cuenta"),

])

bot.send_message(os.environ["admin"], "El bot de publicaciones de Facebook está listo :)")


# @bot.middleware_handler()
# def cmd_middleware(bot: telebot.TeleBot, update: telebot.types.Update):
#     return



@bot.message_handler(func=lambda message: not message.chat.type == "private")
def not_private(m):
    return

@bot.message_handler(func=lambda message: not message.chat.id == admin)
def not_admin(m : telebot.types.Message):
    global scrapper, cola

    bot.send_message(m.chat.id, "Este bot no está disponible para el público.\n\nCualquier queja o sugerencia hablar con @mistakedelalaif")
    return

@bot.message_handler(commands=["start"])
def start(m):
    global scrapper, cola

    bot.send_message(m.chat.id,                      
"""
HOLA :D
¿Te parece tedioso estar re publicando por TODOS tus grupos en Facebook?
No te preocupes, yo me encargo por ti ;)

<u>Lista de Comandos</u>:
<b>/info</b> - Para obtener más información de las publicaciones
<b>/crear</b> - Crear una publicación
<b>/delete</b> - Para cerrar la cuenta actual y poder hacer loguin con una diferente
<b>/cancel</b> - Para CANCELAR la operación y no publicar (esto solo funciona si estás publicando)


Bot desarrollado por @mistakedelalaif, las dudas o quejas, ir a consultárselas a él
""")
    return




@bot.message_handler(commands=["cancel"])
def cmd_cancel(m):
    global scrapper, cola

    if cola["uso"] == m.from_user.id:
        bot.send_message(m.chat.id, "Muy Bien, Cancelaré la operación actual tan pronto cómo sea posible...")
        scrapper.temp_dict[m.from_user.id]["cancel"] = True
        

    else:
        bot.send_message(m.from_user.id, "¡No tienes ningún proceso activo!")

    return
    
@bot.message_handler(commands=["delete"])
def cmd_delete(m):
    global scrapper, cola

    if not collection.find_one({"telegram_id": m.from_user.id}):
        bot.send_message(m.chat.id, "Ni siquiera me has usado aún!\n\nNo tengo datos tuyos los cuales restablecer\nEnviame /info para comenzar a usarme :D")
        return
    
    msg = bot.send_message(m.chat.id, "La opción actual borrará la información que tengo de tu cuenta y tendrías que volver a ingresar todo desde cero nuevamente...\n\nEstás seguro que deseas hacerlo?", reply_markup=ReplyKeyboardMarkup(True, True).add("Si", "No"))
    

    bot.register_next_step_handler(msg, borrar_question)


def borrar_question(m):
    global scrapper, cola

    if m.text.lower() == "si": 
        
        for i in collection.find_one({"telegram_id": m.from_user.id})["cookies"]:
            scrapper.driver.delete_all_cookies()
        
        try:
            collection.delete_one({"telegram_id": m.from_user.id})
        except:
            pass
        try:
            shutil.rmtree(user_folder(m.from_user.id))
        except:
            pass
        

        bot.send_message(m.chat.id, "Ya se ha borrado todo exitosamente :-(", reply_markup=ReplyKeyboardRemove())

    else:
        bot.send_message(m.chat.id, "Operación Cancelada con éxito :D", reply_markup=ReplyKeyboardRemove())

    return


@bot.message_handler(commands=["cookies"])
def cmd_cookies(m):
    global scrapper, cola
    scrapper.temp_dict[m.from_user.id]["msg"] = bot.send_message(m.chat.id, "A continuación envia el archivo cookies.pkl al que tienes acceso")
    bot.register_next_step_handler(scrapper.temp_dict[m.from_user.id]["msg"], obtener_cookies)
    
    
def obtener_cookies(m):
    global scrapper, cola
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
            


@bot.message_handler(commands=["info"])
def cmd_publish(m):
    global scrapper, cola
    
    
    
    bot.send_message(m.chat.id,
"""A continuación ve a Facebook y sigue estos pasos para compartir la publicacion

1 - Selecciona la publicación
2 - Dale en el botón de '↪ Compartir'
3 - Luego en el menú que aparece dale a 'Obtener Enlace'
4 - Pega dicho enlace en el siguiente mensaje y envíamelo

Ahora enviame el enlace de la publicación aquí y me ocuparé del resto ;)
""")
    
    return
    


def notificar(m):
    global scrapper, cola
    m.text = m.text.lower()
    if not m.text in ["si", "no"]:
        msg = bot.send_message(m.chat.id, "¡Toca uno de los botones disponibles!\n\n<b>¿Quieres que te notifique cuando esté disponible para que me uses?</b>", reply_markup=ReplyKeyboardMarkup(True, True).add("Si", "No"))  

        bot.register_next_step_handler(msg, notificar)
        return

    if m.text == "si":
        cola["cola_usuarios"].append(m.from_user.id)
        bot.send_message(m.from_user.id, "Muy bien, <b>te notificaré</b> cuando esté desocupado")
    else:
        bot.send_message(m.from_user.id, "Muy bien, <b>NO te notificaré</b> entonces")

    return


def call_notificar(c):
    global scrapper, cola

    cola["cola_usuarios"].remove(c.from_user.id)
    bot.send_message(c.message.chat.id, "Muy bien, te dejaré de notificar")

    return




#--------------------OJO : Las siguientes lineas son para el futuro, si funciona-----------

# @bot.message_handler(commands=["crear"])
# def cmd_crear(m):
#     usuarios[m.from_user.id] = Usuario(m.from_user.id)

#     m = bot.send_message(m.chat.id, "Aquí podrás crear la publicación que quieres que se comparta en Facebook (en principio, será solo 1)\n\nA continuación de este mensaje, enviame el texto de la publicación o presiona en 'Sin texto' para no poner texto", reply_markup=ReplyKeyboardMarkup(True, True).add("Sin texto"))

#     bot.register_next_step_handler(m, crear_texto)

#     return


# def crear_texto(m: telebot.types.Message):
#     if not m.content_type == "text":
#         m = bot.send_message(m.chat.id, "No me envíes otra cosa que no sea el texto de la Publicación!\nVuelve a intentarlo\n\nnA continuación de este mensaje, enviame el texto de la publicación o presiona en 'Sin texto' para no poner texto", reply_markup=ReplyKeyboardMarkup(True, True).add("Sin texto", "Cancelar Operación"))

#         bot.register_next_step_handler(m, crear_texto)

#     elif m.text.lower() == "cancelar operación":
#         bot.send_message(m.chat.id, "Operación Cancelada", reply_markup=telebot.types.ReplyKeyboardRemove())

#     elif m.text.lower() == "sin texto":
#         m = bot.send_message(m.chat.id, "¡Muy bien, tu publicación no tendrá texto entonces!\n\nA continuación de este mensaje, enviame las FOTOS que quieres que tenga dicha publicación", reply_markup=telebot.types.ReplyKeyboardRemove())
    
#     else:
        

#         usuarios[m.from_user.id].publicaciones.append(Publicacion(usuarios[m.from_user.id].id))
#         usuarios[m.from_user.id].publicaciones[-1].texto = m.text

#         media_group_clases[m.from_user.id] = (MediaGroupCollector(usuarios[m.from_user.id].id, m.from_user.id))

#         bot.send_message(m.chat.id, "A continuación envía las fotos (o la foto) de la publicación que quieres compartir", reply_markup=telebot.types.ReplyKeyboardRemove())

#         return



# @bot.message_handler(content_types=["photo"])
# def photo_handler(m: telebot.types.Message):
#     if m.media_group_id and media_group_clases.get(m.from_user.id):
#         with media_group_clases.get(m.from_user.id) as user_media:
#             print("recibí una foto de: {}".format(user_media.telegram_id))
            
#             if user_media.timer:
#                 user_media.timer.close()

#             user_media.fotos.append(bot.get_file(m.photo[-1].file_id).file_path)
            
#             user_media.timer = threading.Timer(user_media.TIMEOUT, get_photos, (media_group_clases, user_media))
#             user_media.timer.start()
            
#     else:
#         return
    

# def get_photos(media_group_clases: dict, user_media: MediaGroupCollector):

#     if not os.path.isdir(os.path.join(user_folder(user_media.telegram_id), "publicaciones")):
#         os.mkdir(os.path.join(user_folder(user_media.telegram_id), "publicaciones"))

#     for foto in user_media.fotos:
#         with open(os.path.join(user_folder(user_media.telegram_id), "publicaciones" , "u-{}_i-{}.jpg").format(user_media.user_id, len(usuarios[user_media.telegram_id].publicaciones)), "wb") as foto:
            
#             foto.write(bot.download_file(foto))

#             usuarios[user_media.telegram_id].publicaciones[-1].adjuntos.append(os.path.join(user_folder(user_media.td:elegram_id), "publicaciones" , "u-{}_i-{}.jpg").format(user_media.user_id, len(usuarios[user_media.telegram_id].publicaciones)))

#             usuarios[user_media.telegram_id].publicaciones[-1].id_publicacion = len(usuarios[user_media.telegram_id].publicaciones)


#     del media_group_clases[user_media.telegram_id]

#     return

            
#--------------------------------------------------------------------------------------


@bot.message_handler(commands=["publicar"])
def get_work(m: telebot.types.Message):
    global cola, scrapper

    if scrapper.temp_dict.get(m.from_user.id):
        pass
    
    elif cola.get("uso"):

        if not m.from_user.id in cola["cola_usuarios"]:

            msg = bot.send_message(m.chat.id, "Al parecer alguien ya me está usando :(\nLo siento pero por ahora estoy ocupado\n\n<b>¿Quieres que te notifique cuando dejen de usarme?</b>", reply_markup=ReplyKeyboardMarkup(True, True).add("Si", "No"))  

            bot.register_next_step_handler(msg, notificar)
            return


                 

    
    elif not cola.get("uso"):            
        
        
        cola["uso"] = m.from_user.id
        scrapper.temp_dict[m.from_user.id] = {}
        
        if m.from_user.id in cola["cola_usuarios"]:
            cola["cola_usuarios"].remove(m.from_user.id)

        for i in cola["cola_usuarios"]:
            try:
                bot.send_message(i, "Olvídalo :/\nYa me están usando nuevamente\n\n<b>Te volveré a avisar cuando esté desocupado</b>, pero debes de estar atento", reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("No notificar más", callback_data="no_mas")]
                    ]
                ))

                bot.register_callback_query_handler(call_notificar, lambda call: call.data == "no_mas" and call.from_user.id == i)

            except:
                pass
        
        m = bot.send_message(m.chat.id, "Envíame a continuación el texto de la Publicación...", reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))

        bot.register_next_step_handler(m, get_work_texto)


def get_work_texto(m: telebot.types.Message):
    global scrapper, cola
        
    if m.text == "Cancelar Operación":
        liberar_cola(scrapper, m, bot, cola)
        bot.send_message(m.chat.id, "Operación Cancelada :(", reply_markup = telebot.types.ReplyKeyboardRemove())

        return

    if not m.content_type == "text":
        bot.send_message(m.chat.id, "Mal! No has enviado texto...\n\nEnvíame a continuación el texto de la Publicación...", reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))

        bot.register_next_step_handler(m, get_work_texto)

        return
    
        

    scrapper.temp_dict[m.from_user.id]["texto_p"] = m.text

    m = bot.send_message(m.chat.id, "A continuación. envíame 1 foto para la publicación (Por ahora solo admitimos 1)",reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))


    bot.register_next_step_handler(m, get_work_foto)

    
def get_work_foto(m: telebot.types.Message):
    global scrapper, cola

    if m.text == "Cancelar Operación":
        liberar_cola(scrapper, m, bot, cola)
        bot.send_message(m.chat.id, "Operación Cancelada :(", reply_markup = telebot.types.ReplyKeyboardRemove())
        return

    if not m.photo:
        m = bot.send_message(m.chat.id, "Envíame 1 foto!\n\n¿Tan dificil es? Inténtalo nuevamente", reply_markup = telebot.types.ReplyKeyboardMarkup(True, True).add("Cancelar Operación"))

        bot.register_next_step_handler(m, get_work_foto)
        return


    with open(os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png"), "wb") as file:
        scrapper.temp_dict[m.from_user.id]["foto_p"] = os.path.join(user_folder(m.from_user.id) , "foto_publicacion.png")
        file.write(bot.download_file(bot.get_file(m.photo[-1].file_id).file_path))

    

    try:
        try:
            facebook_scrapper.main(scrapper, bot, m.from_user.id)        
        except Exception as e:
            print("Ha ocurrido un error! Revisa el bot, te dará más detalles")
            scrapper.temp_dict[m.from_user.id]["res"] = str(format_exc())

            if isinstance(e.args, tuple):
                if "no" == str(e.args[0]).lower():
                    pass
                
                else:
                    bot.send_message(m.from_user.id, "Ha ocurrido un error inesperado! Reenviale a @mistakedelalaif este mensaje\n\n<blockquote expandable>" + str(scrapper.temp_dict[m.from_user.id]["res"]) + "</blockquote>")

            else:
                bot.send_message(m.from_user.id, "Ha ocurrido un error inesperado! Reenviale a @mistakedelalaif este mensaje\n\n<blockquote expandable>" + str(scrapper.temp_dict[m.from_user.id]["res"]) + "</blockquote>")
        
        
            
        
            
            
    except:
        try:
            bot.send_message(m.chat.id, "Ha ocurrido un error inesperado! Reenviale a @mistakedelalaif este mensaje\n\n<blockquote expandable>" + scrapper.temp_dict[m.from_user.id]["res"] + "</blockquote>")
            
        except:
            try:
                with open(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"), "w") as file:
                    file.write(f"Ha ocurrido un error inesperado!\nID del usuario: {m.from_user.id}\n\n{scrapper.temp_dict[m.from_user.id]["res"]}")
                    
                with open(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"), "r") as file:
                    bot.send_document(m.from_user.id, telebot.types.InputFile(file, file_name="error_" + str(m.from_user.id) + ".txt"))
                    
                os.remove(os.path.join(user_folder(m.from_user.id), "error_" + str(m.from_user.id) + ".txt"))
                
            except:
                try:
                    bot.send_message(m.chat.id, "Ha ocurrido un error fatal")
                except:
                    print("ERROR FATAL:\nHe perdido la conexion a telegram :(")
                    
                
                
    
    liberar_cola(scrapper, m, bot, cola)

    return

    

    

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
    bot.infinity_polling(timeout=80,)