import requests
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelosbbdd import Medico
from config import Config 

#Obtener las credenciales de la base de datos desde Config.py (más seguro)
user = Config.DB_USER
password = Config.DB_PASSWORD
host = Config.DB_HOST
database = Config.DB_NAME
conexionbbdd = f'mysql+pymysql://{user}:{password}@{host}/{database}'
#Conexión a la base de datos
engine = create_engine(conexionbbdd)
Session = sessionmaker(bind=engine)
session = Session()




#Función que guarda en la base de datos de médicos una imagen de una persona aleatoria no existente
#de la página 'thispersondoesnotexist.com' 
def guardar_imagen(id_medico):
    try:
        response = requests.get("https://thispersondoesnotexist.com/")

        if response.status_code == 200: #OK

            #Extraer la imagen
            imagen = response.content


            #Guardar la imagen en los archivos
            ruta_imagen = os.path.join('static/fotos', f"fotoMedico{id_medico}.png").replace('\\', '/')
            with open(ruta_imagen, 'wb') as f:
                f.write(imagen)
            
            print(f"Imagen del médico con ID {id_medico} guardada en los archivos")


            #Obtener el médico de la bbdd
            paciente = session.query(Medico).filter_by(id_medico=id_medico).first()

            #Guardarle la imagen
            paciente.foto = f"/get_image/fotoMedico{id_medico}.png"
            session.commit()

            print(f"Ruta de la imagen actualizada en la base de datos para el médico con ID {id_medico}")
        else:
            print(f"Error al descargar la imagen para el médico con ID {id_medico}")
    
    except Exception as e:
        print(f"Error al guardar: {e}")






#Función principal que itera sobre todos los médicos en la base de datos y descarga sus fotos
def main():
    try:
        #Todos los médicos de la base de datos
        medicos = session.query(Medico).all()

	    #Para cada uno que no tenga ya foto, se llama a la función
        for medico in medicos:
            if not medico.foto:
                guardar_imagen(medico.id_medico)

    except Exception as e:
        print(f"Error del main: {e}")



if __name__ == "__main__":
    main()
    