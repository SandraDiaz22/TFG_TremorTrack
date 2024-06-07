from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from modelosbbdd import Videos
from config import Config 

#Importar funcion de Catalin
from paddel.src.paddel.preprocessing.input.poses import extract_poses_ts
from paddel.src.paddel.preprocessing.input.fresh import extract_fresh_features
from paddel.src.paddel.preprocessing.input.classic import extract_classic_features
from paddel.src.paddel.preprocessing.input.time_series import extract_time_series

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

def analizarVideos():
    #Todos los videos de la base de datos que no tienen todavía características
    videos = session.query(Videos).filter(Videos.velocidad_media.is_(None)).all()

    for video in videos:
        video_id = video.id_video  #ID del video para control
        video_path = "static/videos/" + str(video.paciente) + "/" + video.contenido #Ruta al video

        try:
            #Extrae las poses de la mano del vídeo con tiempos
            poses_ts = extract_poses_ts(video_path)
            
            time_series = extract_time_series(poses_ts)
            time_series["id"] = 0  # id for tsfresh

            #Características básicas
            caracteristicas = extract_classic_features(time_series)

            #Actualizar bbdd con las 7 características devueltas por la función
            video.velocidad_media = str(caracteristicas["angle__mean_speed"])
            video.frecuencia_max = str(caracteristicas["angle__frequency_of_maximums"])
            video.frecuencia_min = str(caracteristicas["angle__frequency_of_minimums"])
            video.promedio_max = str(caracteristicas["angle__average_of_maximums"])
            video.desv_estandar_max = str(caracteristicas["angle__std_of_maximums"])
            video.diferencia_ranurada_min = str(caracteristicas["angle__slotted_difference_of_frequency_of_minimums"])
            video.diferencia_ranurada_max = str(caracteristicas["angle__slotted_difference_of_average_of_maximums"])

            #Más características
            caracteristicas_fresh = extract_fresh_features(time_series)
            #Convertir las características a JSON
            caracteristicas_fresh_json = caracteristicas_fresh.to_json()

            #Actualizar bbdd
            video.caracteristicas = str(caracteristicas_fresh_json)

            session.commit()

            # Imprimir algunas estadísticas para el video actual
            print(f"Video con ID {video_id} analizado.")

        except Exception as e:
            print(f"Error procesando el vídeo con ID {video_id}: {str(e)}")

if __name__ == "__main__":
    analizarVideos()