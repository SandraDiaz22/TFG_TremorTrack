import requests
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelosbbdd import Paciente

#Conexion base de datos
engine = create_engine('mysql+pymysql://root:maria@localhost/parkinson')
Session = sessionmaker(bind=engine)
session = Session()




#Función que guarda en la base de datos una imagen de una persona aleatoria no existente
#de la página 'thispersondoesnotexist.com' 
def guardar_imagen(id_paciente):
    try:
        response = requests.get("https://thispersondoesnotexist.com/")

        if response.status_code == 200: #OK

            #Extraer la imagen
            imagen = response.content


            #Guardar la imagen en los archivos
            ruta_imagen = os.path.join('app2/static/fotos', f"fotoPaciente{id_paciente}.png").replace('\\', '/')
            with open(ruta_imagen, 'wb') as f:
                f.write(imagen)
            
            print(f"Imagen del paciente con ID {id_paciente} guardada en los archivos")


            #Obtener el paciente de la bbdd
            paciente = session.query(Paciente).filter_by(id_paciente=id_paciente).first()

            #Guardarle la imagen
            paciente.foto = f"/get_image/fotoPaciente{id_paciente}.png"
            session.commit()

            print(f"Ruta de la imagen actualizada en la base de datos para el paciente con ID {id_paciente}")
        else:
            print(f"Error al descargar la imagen para el paciente con ID {id_paciente}")
    
    except Exception as e:
        print(f"Error al guardar: {e}")






#Función principal que itera sobre todos los pacientes en la base de datos y descarga sus fotos
def main():
    try:
        #Todos los pacientes de la base de datos
        pacientes = session.query(Paciente).all()

	    #Para cada uno que no tenga ya foto, se llama a la función
        for paciente in pacientes:
            if not paciente.foto:
                guardar_imagen(paciente.id_paciente)

    except Exception as e:
        print(f"Error del main: {e}")



if __name__ == "__main__":
    main()
    