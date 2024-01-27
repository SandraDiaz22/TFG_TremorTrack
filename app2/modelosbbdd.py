from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Administrador(db.Model):
    id_admin = db.Column(db.Integer, primary_key=True)
    nombre_de_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(64), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)

class Medico(db.Model):
    id_medico = db.Column(db.Integer, primary_key=True)
    nombre_de_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(64), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=False)

class Paciente(db.Model):
    id_paciente = db.Column(db.Integer, primary_key=True)
    nombre_de_usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(64), nullable=False)
    correo_electronico = db.Column(db.String(255), unique=True, nullable=False)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    foto = db.Column(db.String(255), nullable=False)
    fecha_de_nacimiento = db.Column(db.Date, nullable=False)
    sensor = db.Column(db.Enum('SI', 'NO'), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(15), nullable=False)
    id_medico = db.Column(db.Integer, db.ForeignKey('medico.id_medico'), nullable=True)


class Registros(db.Model):
    fecha = db.Column(db.Date, primary_key=True)
    paciente = db.Column(db.Integer, db.ForeignKey('paciente.id_paciente'), nullable=True)
    datos_en_crudo = db.Column(db.Text, nullable=False)

class Videos(db.Model):
    fecha = db.Column(db.Date, primary_key=True)
    paciente = db.Column(db.Integer, db.ForeignKey('paciente.id_paciente'), nullable=True)
    contenido = db.Column(db.LargeBinary, nullable=False)
    mano_dominante = db.Column(db.Enum('mano derecha', 'mano izquierda'), nullable=False)
    