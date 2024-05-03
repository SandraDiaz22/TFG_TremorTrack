from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from modelosbbdd import Videos

#Importar funcion de Catalin
from paddel.src.paddel.preprocessing.input.poses import extract_poses_ts



#Conexión a la base de datos
engine = create_engine('mysql+pymysql://root:maria@localhost/parkinson')
Session = sessionmaker(bind=engine)
session = Session()

def analizarVideos():
    #Todos los videos de la base de datos que no tienen todavía características
    videos = session.query(Videos).filter(Videos.estadisticas.is_(None)).all()

    for video in videos:
        video_path = video.contenido  #Ruta del video para pasar a la función
        video_id = video.id_video  #ID del video para control

        try:
            #Extrae las poses de la mano del vídeo con tiempos
            poses_df = extract_poses_ts(video_path)

            #Convertir el DataFrame a JSON para guardarlo
            poses_json = poses_df.to_json()

            #Actualizar bbdd
            video.estadisticas = poses_json
            session.commit()

            # Imprimir algunas estadísticas para el video actual
            print(f"Video ID: {video_id}, Numero de frames: {len(poses_df)}")

        except Exception as e:
            print(f"Error procesando el vídeo con ID {video_id}: {str(e)}")

if __name__ == "__main__":
    analizarVideos()