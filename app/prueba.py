import dill
from f_src.chrome_driver import uc_driver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

d = uc_driver(True)

wait = WebDriverWait(d, 80)
user = 1234567
temp_dict = {}
temp_dict[user] = {}

d.get("https://facebook.com/robots.txt")

with open(r"D:\Programacion\Proyectos personales\webscrapping\revolico_scrapping\user_archive\cookies.pkl", "rb") as f:
    c = dill.load(f)
    
    for i in c["cookies"]:
        d.add_cookie(i)


d.get("https://facebook.com")


breakpoint()


print("estoy dentro de la funcion de elegir la cuenta")
    
    
try:
    #si ya el menú de cuentas está desplegado... hay que omitir cosas
    temp_dict[user]["e"] = d.find_element(By.CSS_SELECTOR, 'div[role="list"]')

    temp_dict[user]["e"] = True
    
except: 
    temp_dict[user]["e"] = False
    
if not temp_dict[user]["e"]:  
    print("Voy a esperar a que salga el menu de cuentas")
    #este elemento es el de los ajustes del perfil (las 3 rayas de la derecha superior)
    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role=button][data-mcomponent="MContainer"][data-action-id="32746"]'))).click()

    #Elemento de Configuracion de cuenta
    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="list"]')))

    print("comprobaré si sale el botón de seleccionar otros perfiles, si es que hay")
    #Flecha para ver otros perfiles/cambiar
    wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, 'div[role="button"][data-action-id="32745"]')))

    try:
        d.find_element(By.CSS_SELECTOR, 'div[role="button"][data-action-id="32745"]').click()
        
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

    #este elemento es el padre de las cuentas, concretamente el 2do elemento en el html
    wait.until(ec.visibility_of_all_elements_located((By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')))


    print("Obteniendo los elementos de las cuentas...")
    temp_dict[user]["cuentas"] = d.find_elements(By.CSS_SELECTOR, 'div[data-action-id="99"][data-mcomponent="MContainer"][data-type="container"][tabindex="0"][data-tti-phase="-1"][data-focusable="true"]')[1].find_elements(By.CSS_SELECTOR, 'div[role="button"][tabindex="0"][data-focusable="true"][data-tti-phase="-1"][data-type="container"][data-mcomponent="MContainer"]')
    #remuevo el último elemento porque no es una cuenta sino una opcion de facebook en el mismo menú de cuentas
    
    # if not ver_actual:
    
    print("Creando el teclado del mensaje...")