import pandas as pd
from datetime import datetime
from config import Config 
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelosbbdd import Registros


def actualizar_fechas_registros():
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
    
    #Todos los registros sin fecha
    registros = session.query(Registros).filter(Registros.fecha_inicial.is_(None), Registros.fecha_final.is_(None)).all()

    #Para cada uno, leerlo, obtener el primer y último EPO, 
    # trasformarlo a fecha y subirlo a la bbdd
    for registro in registros:
        #Leer el CSV
        ruta_csv = registro.datos_en_crudo
        fecha_ini, fecha_fin = obtener_fechas_registro(ruta_csv)

        #Actualizar bbdd
        registro.fecha_inicial = fecha_ini
        registro.fecha_final = fecha_fin
        session.commit()

    # Cerrar la sesión
    session.close()


def obtener_fechas_registro(archivo):    
    # Leer el CSV para obtener las fechas inicial y final
    csv = pd.read_csv(archivo, skiprows=1)  # Saltamos la línea de títulos

    # Primera y última fecha del registro
    fecha_ini_epo = csv.iloc[0, 0]
    fecha_fin_epo = csv.iloc[-1, 0]

    fecha_ini_epo = int(fecha_ini_epo)
    fecha_fin_epo = int(fecha_fin_epo)

    # Convertir de EPO a fecha
    fecha_ini = datetime.utcfromtimestamp(fecha_ini_epo / 1000.)
    fecha_fin = datetime.utcfromtimestamp(fecha_fin_epo / 1000.)

    return fecha_ini, fecha_fin

if __name__ == "__main__":
    actualizar_fechas_registros()