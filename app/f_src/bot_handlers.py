import telebot
from telebot.types import ForceReply

def get_user(m , bot , user , info, temp_dict, **kwargs):

    temp_dict[user][info] = m.text
    temp_dict[user]["completed"] = True
            
    return


def choose_perfil(m,bot,user, info,  temp_dict):
    if not m.text in temp_dict[user]["perfiles"]:
        temp_dict[user]["msg"] = bot.send_message(user, "La información ingresada es incorrecta! Intentalo de nuevo!\n\nCual de los perfiles de esta cuenta quieres usar?", reply_markup = temp_dict[user]["teclado"])
        
        return bot.register_next_step_handler(temp_dict[user]["msg"], choose_perfil, bot , user , info, temp_dict)
    
    temp_dict[user]["res"] = temp_dict[user]["perfiles"].index(m.text)
    temp_dict[user]["completed"] = True
    return 


def get_codigo(m,bot,user, info, temp_dict):
    if not m.text[0:2].isdigit():
        temp_dict[user]["msg"] = bot.send_message(m.chat.id, "El código introducido es incorrecto\nInténtalo de nuevo\n\nIntroduce uno de los códigos de respaldo de Facebook a continuación\n\n(Estos códigos son de 8 dígitos numéricos y puedes obtenerlos en el centro de cuentas en los ajustes de tu cuenta de Facebook)", reply_markup=ForceReply())
        
        bot.register_next_step_handler(temp_dict[user]["msg"], get_codigo, bot,user, info, temp_dict)
    
    else:
        
        temp_dict[user]["res"] = m
        temp_dict[user]["completed"] = True    
        return
    
    
def perfil_pregunta(m,bot,user, info, temp_dict):
            
    if not m.text.lower() in ["si", "no"]:
        temp_dict[user]["msg"]=bot.send_message(m.chat.id, "Has introducido una respuesta incorrecta...por favor pulse uno de los botones a continuación\n\nEl perfil actual es: " + "<b>" + temp_dict[user]["res"][1] + "</b>" + "\n\n¿Quieres cambiar de perfil?", reply_markup=temp_dict[user]["teclado"])
        
        bot.register_next_step_handler(temp_dict[user]["msg"], perfil_pregunta,bot,user, info, temp_dict)
    else:
        temp_dict[user]["res"] = m
        temp_dict[user]["completed"] = True
        return


def captcha_getter(m, bot:telebot.TeleBot ,user, info, temp_dict, file):

    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True
    return
    
def perfil_seleccion(m, bot:telebot.TeleBot ,user, info, temp_dict, teclado):
    if not m.text in temp_dict[user]["lista_perfiles"]:
        temp_dict[user]["msg"] = bot.send_message(m.chat.id, "¡Selecciona uno de los perfiles! ¡No ingreses nada por tu cuenta!\n\nVuelve a intentarlo", reply_markup = teclado)
        
        bot.register_next_step_handler(temp_dict[user]["msg"], perfil_seleccion, temp_dict[user]["teclado"])
        
    else:
        temp_dict[user]["res"] = m.text
        temp_dict[user]["completed"] = True
        
        return


def correo_o_numero(m, bot:telebot.TeleBot ,user, info, temp_dict):
    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True

    return m.text

def correo_o_numero_verificacion(m, bot:telebot.TeleBot ,user, info, temp_dict):

    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True

    return m.text


def email_verification(m, bot:telebot.TeleBot ,user, info, temp_dict):

    temp_dict[user]["res"] = m.text
    temp_dict[user]["completed"] = True

    return m.text


