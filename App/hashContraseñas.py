import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from modelosbbdd import Administrador, Medico, Paciente
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



#Tabla administradores
administradores = session.query(Administrador).all()
#Por cada admin, cambiamos la contraseña por ella misma hasheada
for admin in administradores:
    contraseña_hasheada = hashlib.sha256(admin.contraseña.encode()).hexdigest()
    admin.contraseña = contraseña_hasheada



#Tabla médicos
medicos = session.query(Medico).all()
#Por cada médico, hasheamos su contraseña
for medico in medicos:
    contraseña_hasheada = hashlib.sha256(medico.contraseña.encode()).hexdigest()
    medico.contraseña = contraseña_hasheada



#Tabla pacientes
pacientes = session.query(Paciente).all()
#Por cada paciente, hasheamos su contraseña
for paciente in pacientes:
    contraseña_hasheada = hashlib.sha256(paciente.contraseña.encode()).hexdigest()
    paciente.contraseña = contraseña_hasheada


#Guardar cambios
session.commit()
session.close()
