import pandas as pd
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelosbbdd import Registros


def actualizar_fechas_registros():
    #Conexion base de datos
    engine = create_engine('mysql+pymysql://root:maria@localhost/parkinson')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    #Todos los registros sin fecha
    registros = session.query(Registros).filter(Registros.fecha_inicial.is_(None), Registros.fecha_final.is_(None)).all()

    #Para cada uno, leerlo, obtener el primer y último EPO, 
    # trasformarlo a fecha y subirlo a la bbdd
    for registro in registros:
        #Leer el CSV
        ruta_csv = registro.datos_en_crudo
        csv = pd.read_csv(ruta_csv, skiprows=1) #Saltamos la línea de títulos
        
        #Primera y última fecha del registro
        fecha_ini_epo = csv.iloc[0,0]
        fecha_fin_epo = csv.iloc[-1,0]

        fecha_ini_epo = int(fecha_ini_epo)
        fecha_fin_epo = int(fecha_fin_epo)

        #Convertir de EPO a fecha
        fecha_ini = datetime.utcfromtimestamp(fecha_ini_epo/1000.)
        fecha_fin = datetime.utcfromtimestamp(fecha_fin_epo/1000.)

        #Actualizar bbdd
        registro.fecha_inicial = fecha_ini
        registro.fecha_final = fecha_fin
        session.commit()

    # Cerrar la sesión
    session.close()

if __name__ == "__main__":
    actualizar_fechas_registros()