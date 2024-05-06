from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from modelosbbdd import Videos

#Importar funcion de Catalin
from paddel.src.paddel.preprocessing.input.poses import extract_poses_ts
from paddel.src.paddel.preprocessing.input.classic import extract_classic_features


#Conexión a la base de datos
engine = create_engine('mysql+pymysql://root:maria@localhost/parkinson')
Session = sessionmaker(bind=engine)
session = Session()

def analizarVideos():

    video_path = "static/videos/1/CONTROL995_03-08-2023_DCHA_M-56-D.mp4"
    poses_df = extract_poses_ts(video_path)
    #print(poses_df)
    caracteristicas = extract_classic_features(poses_df)
    print(caracteristicas)




    #Todos los videos de la base de datos que no tienen todavía características
    # videos = session.query(Videos).filter(Videos.velocidad_media.is_(None)).all()

    # for video in videos:
    #     video_id = video.id_video  #ID del video para control
    #     video_path = "static/videos/" + str(video.paciente) + "/" + video.contenido #Ruta al video

    #     try:
    #         #Extrae las poses de la mano del vídeo con tiempos
    #         poses_df = extract_poses_ts(video_path)

    #         caracteristicas = extract_classic_features(poses_df)

    #         #Actualizar bbdd con las 7 características devueltas por la función
            # video.velocidad_media = caracteristicas["mean_speed"]
            # video.frecuencia_max = caracteristicas["frequency_of_maximums"]
            # video.frecuencia_min = caracteristicas["frequency_of_minimums"]
            # video.promedio_max = caracteristicas["average_of_maximums"]
            # video.desv_estandar_max = caracteristicas["std_of_maximums"]
            # video.diferencia_ranurada_min = caracteristicas["slotted_difference_of_frequency_of_minimums"]
            # video.diferencia_ranurada_max = caracteristicas["slotted_difference_of_average_of_maximums"]

    #         session.commit()

    #         # Imprimir algunas estadísticas para el video actual
    #         print(f"Video ID: {video_id}, Numero de frames: {len(poses_df)}")

    #     except Exception as e:
    #         print(f"Error procesando el vídeo con ID {video_id}: {str(e)}")

if __name__ == "__main__":
    analizarVideos()