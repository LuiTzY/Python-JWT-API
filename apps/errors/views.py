import json
import datetime
import os
import uuid
import glob
#Ruta donde se van a guardar y leer los archivos que presenten errores
ERROR_STORAGE_URL = "D:\Zoom Grabaciones\Errors"

#Funcion para cargar el error en un formato json en la carpeta de errors en este caso
def load_json_error(error):
    #
    error_filename = generate_file_error_name()
    error_data = {
        "error":f"{error}",
        "OcurredAT":datetime.datetime.now()
    }
    with open(f"{os.path.join(ERROR_STORAGE_URL,error_filename)}", "w", encoding="UTF-8") as error_json:
        #Escribira el error dentro del programa
        json.dump(error_data,error_json, indent=4)

def get_registred_errors():
    #tambien se pudiera utilizar os.scandir 
    errors_files = glob.glob("*.json")
    print(f"Estos son los errores encontrados {errors_files}")
    return len(errors_files) #devolvera el largo de archivos que encuentre

def generate_file_error_name():
    #va a generar un uuid aleatorio de 32 caracteres
    unique_id = uuid.uuid4().hex
    #El nombre del archivo sera error, el uuid unico generado mas la extension de json
    filename = f"error_{unique_id}.json"
    #se retorna el nombre del archivo
    return filename