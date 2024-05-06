from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Administrador(db.Model):
    id_admin = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_de_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(64), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=True)

class Medico(db.Model):
    id_medico = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_de_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(64), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=True)

class Paciente(db.Model):
    id_paciente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre_de_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(64), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=True)
    fecha_de_nacimiento = db.Column(db.Date, nullable=False)
    sensor = db.Column(db.Enum('SI', 'NO'), nullable=True)
    direccion = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    id_medico = db.Column(db.Integer, db.ForeignKey('medico.id_medico'), nullable=True)


class Registros(db.Model):
    id_registro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paciente = db.Column(db.Integer, db.ForeignKey('paciente.id_paciente'), nullable=True)
    datos_en_crudo = db.Column(db.String(250), nullable=False)
    fecha_inicial = db.Column(db.Date, nullable=True)
    fecha_final = db.Column(db.Date, nullable=True)

class Videos(db.Model):
    id_video = db.Column(db.Integer, primary_key=True, autoincrement=True)
    paciente = db.Column(db.Integer, db.ForeignKey('paciente.id_paciente'), nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    contenido = db.Column(db.String(250), nullable=False)
    mano_dominante = db.Column(db.Enum('derecha', 'izquierda'), nullable=False)
    lentitud =  db.Column(db.Enum('0','1','2','3','4'), nullable=True)
    amplitud = db.Column(db.Enum('0','1','2','3','4'), nullable=True)
    velocidad_media = db.Column(db.String(50), nullable=True)
    frecuencia_max = db.Column(db.String(50), nullable=True)
    frecuencia_min = db.Column(db.String(50), nullable=True)
    promedio_max = db.Column(db.String(50), nullable=True)
    desv_estandar_max = db.Column(db.String(50), nullable=True)
    diferencia_ranurada_min = db.Column(db.String(50), nullable=True)
    diferencia_ranurada_max = db.Column(db.String(50), nullable=True)

    