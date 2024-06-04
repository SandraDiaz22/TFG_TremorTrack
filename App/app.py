from flask import Flask, jsonify, render_template, request, make_response, session, redirect, url_for, send_from_directory, g, flash
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

#Traducciones
from flask_babel import Babel, _ 

from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, time
import os
import json
import pandas as pd

#Librería para encriptar contraseñas
import hashlib

#Configuración app
from config import DevelopmentConfig

#Base de datos
from modelosbbdd import db, Administrador, Medico, Paciente, Registros, Videos

#Funciones creadas por la alumna
from fechasRegistros import actualizar_fechas_registros, obtener_fechas_registro
from analizarVideos import analizarVideos

#Librerías de machine learning para las predicciones
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from statsmodels.tsa.holtwinters import Holt
from statsmodels.tsa.holtwinters import ExponentialSmoothing




#----------------------------------------------------------------
#Inicializar aplicación y traducciones
app = Flask(__name__, static_url_path='/static')
babel= Babel(app)

#Configuración
app.config.from_object(DevelopmentConfig)
app.secret_key = b'claveSuperMegaSecreta' #Clave secreta para las sesiones
app.permanent_session_lifetime = timedelta(hours=1) #Duración limitada de las sesiones(1 hora de inactividad)


#Conexion base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maria@localhost/parkinson'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)

#Para tener las bbdd en la plantilla
@app.context_processor
def usuarioActual():
    #Obtener el nombre de usuario y rol de la sesión
    username = session.get('username')
    rol = session.get('rol')

    #Obtener el usuario de la bbdd
    usuario = None
    if rol == 'administrador':
        usuario = Administrador.query.filter_by(nombre_de_usuario=username).first()
    elif rol == 'medico':
        usuario = Medico.query.filter_by(nombre_de_usuario=username).first()
    elif rol == 'paciente':
        usuario = Paciente.query.filter_by(nombre_de_usuario=username).first()

    #Usuario ahora disponible en layout
    return dict(usuario=usuario)


#Fotos
app.static_folder = 'fotos'


#Determina la página en la que nos encontramos(para el navbar)
@app.before_request
def pagina_actual():
    if request.endpoint:
        g.page = request.endpoint.split('.')[-1]
#----------------------------------------------------------------




#----------------------------------------------------------------
#Traducción

#Idioma predeterminado (español)
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
#Dicionario de idiomas
app.config['LANGUAGES'] = {
    'en': 'Inglés',
    'es': 'Español',
    'fr': 'Francés'
}

#Función que obtiene el idioma elegido por el usuario en la cookie
#sino el preferido del navegador del usuario
#y sino pone el idioma predeterminado
def get_locale():
    #Intenta obtener el idioma almacenado en la cookie
    idioma_cookie = request.cookies.get('idioma')
    if idioma_cookie:
        return idioma_cookie
    
    #Si no hay idioma almacenado en la cookie, utiliza el idioma preferido del navegador
    idioma_navegador = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    if idioma_navegador is not None:
        return idioma_navegador
    
    #Si el navegador no especifica, utiliza el predeterminado, español
    return app.config['BABEL_DEFAULT_LOCALE']


#Inicializar babel con get_locale como selector de idioma
babel = Babel(app, locale_selector=get_locale)

#Pasar get_locale a la plantilla
@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)

#Ruta para cambiar el idioma y guardar el elegido en una cookie
@app.route('/cambiar_idioma/<idioma>')
def cambiar_idioma(idioma):
    if idioma in app.config['LANGUAGES']:
        #Mete el idioma en una cookie con una duración de 1 día
        respuesta = make_response(redirect(request.referrer))
        respuesta.set_cookie('idioma', value=idioma, max_age=86400)
        return respuesta
    return 'Idioma no válido'
#----------------------------------------------------------------



#Proteccion anti cross-site request forgery
#csrf = CSRFProtect()
#quitado de login porque daba error aunque antes funcionaba
            #<!-- Campos ocultos vs ataques
            #{{ form.honeypot }}
            #<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/> -->



#----------------------------------------------------------------
#Ruta para poder mostrar las imágenes
@app.route('/get_image/<filename>')
def get_image(filename):
    return send_from_directory('static/fotos', filename)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Ruta para poder mostrar los vídeos
@app.route('/get_video/<int:id_paciente>/<filename>')
def get_video(id_paciente, filename):
    return send_from_directory('static/videos/{}/'.format(id_paciente), filename)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Mensaje personalizado en las páginas no existentes (error 404)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página principal de la aplicación. Contiene:
#       - Barra superior con diferentes funcionalidades (Contacto, Idioma, Iniciar Sesión)
#       - Información sobre las funciones de TremorTrack
#       - Logos
@app.route('/', methods = ['GET', 'POST'])
def paginaprincipal():
    return render_template('paginaprincipal.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página con información sobre los creadores de la página y de contacto. Contiene:
#       - Barra superior con diferentes funcionalidades
#       - Información sobre nosotros
#       - Información de contacto
@app.route('/contacto', methods = ['GET', 'POST'])
def contacto():
    return render_template('contacto.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de inicio de sesión. Contiene:
#       - Barra superior con diferentes funcionalidades
#       - Datos de admin, médico y paciente (solo en las pruebas)
#       - Formulario
@app.route('/login', methods=['GET', 'POST'])
def login():    
    #cuando den al botón de iniciar sesión
    if request.method == 'POST':

        #Obtener datos del formulario
        username = request.form.get('username')
        contraseña = request.form.get('password')

        #Hashear la contraseña
        contraseña_hasheada = hashlib.sha256(contraseña.encode()).hexdigest()

        #Buscar en la bbdd las credenciales
        usuario_medico = Medico.query.filter_by(nombre_de_usuario=username, contraseña=contraseña_hasheada).first()
        usuario_administrador = Administrador.query.filter_by(nombre_de_usuario=username, contraseña=contraseña_hasheada).first()
        usuario_paciente = Paciente.query.filter_by(nombre_de_usuario=username, contraseña=contraseña_hasheada).first()

        #Diferentes páginas de bienvenida según el usuario
        #Si es administrador
        if usuario_administrador:
            session['username'] = usuario_administrador.nombre_de_usuario #Almacenamos el username del admin en su sesión
            session['rol'] = 'administrador' #Y su rol de admin
            return redirect(url_for('BienvenidaAdmin'))
        
        #Si es médico
        elif usuario_medico:
            session['username'] = usuario_medico.nombre_de_usuario #Almacenamos el username del medico en su sesión
            session['rol'] = 'medico' #Y su rol de medico
            return redirect(url_for('BienvenidaMedico'))
        
        #Si es paciente
        elif usuario_paciente:
            session['username'] = usuario_paciente.nombre_de_usuario #Almacenamos el username del paciente en su sesión
            session['rol'] = 'paciente' #Y su rol de paciente
            return redirect(url_for('BienvenidaPaciente'))
        
        #Si no es ninguno
        else:
            idioma_cookie = request.cookies.get('idioma')
            #Dependiendo del idioma se muestra un mensaje de error o otro
            if idioma_cookie == 'en':
                error = 'Incorrect credentials. Please try again.'
            elif idioma_cookie == 'fr':
                error = 'Identifiants incorrects. Veuillez réessayer.'
            else:
                error = 'Credenciales incorrectas. Inténtalo de nuevo.'
            
            flash(error, 'error')  #Mostrar error al usuario
    

    return render_template('login.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de cierre de sesión. Redirige al usuario a la página principal
@app.route('/logout')
def logout():
    session.pop('username', None) #Elimina username de la sesión
    return redirect(url_for('paginaprincipal')) #Redirige a pp
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de bienvenida para administradores. Contiene:
#       - Barra superior con el perfil del usuario
#       - Datos de admin y botón para cerrar sesión
#       - Botón de acceso a la gestión de usuarios
@app.route('/BienvenidaAdmin')
def BienvenidaAdmin():
    #Verificar si el usuario está logueado como admin
    if 'username' not in session or session.get('rol') != 'administrador':
        print('Se debe iniciar sesión como administrador para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))

    #Nombre de usuario del admin logeado
    username_admin = session.get('username')

    #Objeto de ese admin en la bbdd
    admin = Administrador.query.filter_by(nombre_de_usuario=username_admin).first()
    
    #Si no existe en la bbdd
    if not admin:
        print('No se encontró ese usuario en la base de datos', 'error')
        return redirect(url_for('paginaprincipal'))
    
    return render_template('BienvenidaAdmin.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra todos los usuarios de la aplicación para hacer su gestión
@app.route('/gestionUsuarios')
def gestionUsuarios():
    #Verificar si el usuario está logueado como admin
    if 'username' not in session or session.get('rol') != 'administrador':
        print('Se debe iniciar sesión como administrador para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))
    
    #Obtener el id del admin logueado:
    #Nombre de usuario del admin logeado
    username_admin = session.get('username')
    #Objeto de ese admin en la bbdd
    admin = Administrador.query.filter_by(nombre_de_usuario=username_admin).first()
    id_admin_logueado = admin.id_admin
    
    #Consulta para obtener todos los administradores de la aplicación
    listadoAdministradores = Administrador.query.all()
    #Consulta para obtener todos los medicos de la aplicación
    listadoMedicos = Medico.query.all()
    #Consulta para obtener todos los pacientes de la aplicación
    listadoPacientes = Paciente.query.all()

    return render_template('gestionUsuarios.html', admins=listadoAdministradores, medicos=listadoMedicos ,pacientes=listadoPacientes, id_admin_logueado=id_admin_logueado)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que elimina al usuario con el id indicado
@app.route('/eliminarUsuario/<rol>/<int:idUsuario>', methods=['POST'])
def eliminarUsuario(rol, idUsuario):
    if request.method == 'POST':
        try:
            if rol == 'paciente':
                usuario = Paciente.query.get_or_404(idUsuario)
                #Eliminar sus vídeos asociados
                videos = Videos.query.filter_by(paciente=idUsuario).all()
                if videos:
                    for video in videos:
                        db.session.delete(video)
                    db.session.commit()
                #Eliminar sus registros asociados
                registros = Registros.query.filter_by(paciente=idUsuario).all()
                if registros:
                    for registro in registros:
                        db.session.delete(registro)
                    db.session.commit()
            
            elif rol == 'medico':
                usuario = Medico.query.get_or_404(idUsuario)
            
            elif rol == 'administrador':
                usuario = Administrador.query.get_or_404(idUsuario)
            
            db.session.delete(usuario) #Eliminamos usuario
            db.session.commit()
            return 'Usuario eliminado correctamente', 200
        
        except IntegrityError as e:
            if rol == 'medico' and 'a foreign key constraint fails' in str(e.orig):
                return 'No se puede eliminar al médico porque tiene pacientes a su cargo', 400
    else:
        return 'Método no permitido', 405
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que añade un usuario a la bbdd
@app.route('/agregarUsuario/<rol>', methods=['POST'])
def agregarUsuario(rol):
    if request.method == 'POST':
        #Recoger los datos introducidos por el admin
        datos_usuario = request.form.to_dict()
        foto = request.files['foto']
        if not datos_usuario or not foto:
            return 'Datos del usuario no proporcionados', 400

        #Verifica que estén los campos comunes para todos los roles
        campos_obligatorios = ['nombre', 'apellido', 'nombre_de_usuario', 'contraseña', 'correo_electronico']
        for campo in campos_obligatorios:
            if campo not in datos_usuario:
                return f'El campo {campo} es obligatorio', 400

        #Hashear la contraseña
        contraseña = datos_usuario['contraseña']
        contraseña_hasheada = hashlib.sha256(contraseña.encode()).hexdigest()

        #Si se añade un paciente
        if rol == 'paciente':
            #Verifica el resto de campos
            campos_paciente = ['fecha_de_nacimiento', 'direccion', 'telefono', 'sensor', 'id_medico', 'lateralidad']
            for campo in campos_paciente:
                if campo not in datos_usuario:
                    return f'El campo {campo} es obligatorio para el rol de paciente', 400

            #Crea un nuevo paciente(sin foto)
            nuevo_paciente = Paciente(  nombre=datos_usuario['nombre'], apellido=datos_usuario['apellido'],
                                        nombre_de_usuario=datos_usuario['nombre_de_usuario'], contraseña=contraseña_hasheada,
                                        correo_electronico=datos_usuario['correo_electronico'], fecha_de_nacimiento=datos_usuario['fecha_de_nacimiento'],
                                        direccion=datos_usuario['direccion'], telefono=datos_usuario['telefono'], 
                                        sensor=datos_usuario['sensor'], id_medico=datos_usuario['id_medico'],
                                        lateralidad=datos_usuario['lateralidad'])
   
            #Lo añade a la bbdd
            db.session.add(nuevo_paciente)
            db.session.commit()

            #Obtenemos su id
            id_paciente = nuevo_paciente.id_paciente

            #Foto del paciente
            nombre_imagen = f'fotoPaciente{id_paciente}.png'            #nombre
            ruta_imagen = os.path.join('static/fotos', nombre_imagen)   #ubicacion en local
            foto.save(ruta_imagen)                                      #guardar en local
            nuevo_paciente.foto = f'/get_image/{nombre_imagen}'         #para la bbdd
            db.session.commit()                 


        #Si es un médico
        elif rol == 'medico':
            #Crea un nuevo medico(sin foto)
            nuevo_medico = Medico(  nombre=datos_usuario['nombre'], apellido=datos_usuario['apellido'],
                                    nombre_de_usuario=datos_usuario['nombre_de_usuario'], contraseña=contraseña_hasheada,
                                    correo_electronico=datos_usuario['correo_electronico'])
   
            #Lo añade a la bbdd
            db.session.add(nuevo_medico)
            db.session.commit()

            #Obtenemos su id
            id_medico = nuevo_medico.id_medico

            #Foto del medico
            nombre_imagen = f'fotoMedico{id_medico}.png'                #nombre
            ruta_imagen = os.path.join('static/fotos', nombre_imagen)   #ubicacion en local
            foto.save(ruta_imagen)                                      #guardar en local
            nuevo_medico.foto = f'/get_image/{nombre_imagen}'           #para la bbdd
            db.session.commit()                 

        #Si es otro admin
        elif rol == 'administrador':
            #Crea un nuevo Administrador(sin foto)
            nuevo_administrador = Administrador(nombre=datos_usuario['nombre'], apellido=datos_usuario['apellido'],
                                                nombre_de_usuario=datos_usuario['nombre_de_usuario'], contraseña=contraseña_hasheada,
                                                correo_electronico=datos_usuario['correo_electronico'])
   
            #Lo añade a la bbdd
            db.session.add(nuevo_administrador)
            db.session.commit()

            #Obtenemos su id
            id_admin = nuevo_administrador.id_admin

            #Foto del Administrador
            nombre_imagen = f'fotoAdministrador{id_admin}.png'          #nombre
            ruta_imagen = os.path.join('static/fotos', nombre_imagen)   #ubicacion en local
            foto.save(ruta_imagen)                                      #guardar en local
            nuevo_administrador.foto = f'/get_image/{nombre_imagen}'    #para la bbdd
            db.session.commit()                 

        return 'Usuario agregado correctamente', 200
    else:
        return 'Método no permitido', 405
#----------------------------------------------------------------



#----------------------------------------------------------------
#Función que actualiza la informacion personal de los pacientes en la bbdd
@app.route('/actualizar_datos_personales', methods=['POST'])
def actualizar_datos_personales():
    if request.method == 'POST':
        #Recogemos los nuevos datos del paciente
        id_paciente = request.form.get('id_paciente')
        sensor = request.form.get('sensor')
        lateralidad = request.form.get('lateralidad')
        fecha_de_nacimiento = request.form.get('fecha_de_nacimientoP')
        direccion = request.form.get('direccionP')
        telefono = request.form.get('telefonoP')

        #Editamos al paciente
        paciente = Paciente.query.get(id_paciente)
        if paciente:
            paciente.fecha_de_nacimiento = fecha_de_nacimiento
            paciente.direccion = direccion
            paciente.telefono = telefono

            #Si es un paciente no puede editar los campos de sensor y lateralidad
            if sensor:
                paciente.sensor = sensor
                paciente.lateralidad = lateralidad

            db.session.commit() #Subir a la bbdd
            return 'Paciente editado correctamente', 200
        else:
            return 'Paciente no encontrado', 404
    else:
        return 'Método no permitido', 405
#----------------------------------------------------------------



#----------------------------------------------------------------
#Función para editar todos los campos de la bbdd de cada usuario
@app.route('/editar_usuario', methods=['POST'])
def editar_usuario():
    usuario_id = request.form.get('usuario_id')
    tipo_usuario = request.form.get('editar_tipo')

    #Obtenemos el usuario a editar
    if tipo_usuario == 'administrador':
        usuario = Administrador.query.get(usuario_id)
    elif tipo_usuario == 'medico':
        usuario = Medico.query.get(usuario_id)
    elif tipo_usuario == 'paciente':
        usuario = Paciente.query.get(usuario_id)

    if usuario:
        usuario.nombre = request.form.get('nombre')
        usuario.apellido = request.form.get('apellido')
        usuario.nombre_de_usuario = request.form.get('nombre_de_usuario')

        contraseña = request.form.get('contraseña')
        if contraseña:
            #Hashear la contraseña
            contraseña_hasheada = hashlib.sha256(contraseña.encode()).hexdigest()
            usuario.contraseña = contraseña_hasheada

        usuario.correo_electronico = request.form.get('correo_electronico')
        
        if tipo_usuario == 'paciente': #Campos extra de los pacientes
            usuario.fecha_de_nacimiento = request.form.get('fecha_de_nacimiento')
            usuario.direccion = request.form.get('direccion')
            usuario.telefono = request.form.get('telefono')
            usuario.sensor =  request.form.get('sensor')
            usuario.lateralidad =  request.form.get('lateralidad')
            usuario.id_medico = request.form.get('id_medico')
        
        db.session.commit()
        return 'Usuario editado correctamente', 200
    else:
        return 'Usuario no encontrado', 404
#----------------------------------------------------------------



#----------------------------------------------------------------
#Subida de archivos a la bbdd

#Configurar directorio donde se guardarán los archivos subidos
app.config['RUTA_REGISTROS'] = 'static/registros'
app.config['RUTA_VIDEOS'] = 'static/videos'
#Limitar el tamaño máximo
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
#Extensiones de archivo permitidas
EXTENSION_CSV = {'csv'}
EXTENSION_VIDEO = {'mp4'}

#Funciones que verifican que el archivo pasado tiene la extensión permitida
def CSVpermitido(archivo):
    return '.' in archivo and \
           archivo.rsplit('.', 1)[1].lower() in EXTENSION_CSV

def VIDEOpermitido(archivo):
    return '.' in archivo and \
           archivo.rsplit('.', 1)[1].lower() in EXTENSION_VIDEO


#Función que guarda en los archivos y sube a la base de datos el archivo
#del sensor introducido en la app
@app.route('/subirDatosSensor/<id_paciente>', methods=['POST'])
def subir_datos_sensor(id_paciente):
    archivo = request.files['archivo_sensor'] #Archivo introducido por el médico 
    print(archivo)
    if archivo and CSVpermitido(archivo.filename):
        #Obtener la fecha y hora actual(con segundos)
        fecha_subida = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Obtener fecha inicial y final del registro
        fecha_ini, fecha_fin = obtener_fechas_registro(archivo)
        fecha_ini_str = fecha_ini.strftime("%Y-%m-%d")
        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")

        #Generar un nombre único para el archivo
        nombre_archivo = f"stat_on_ID{id_paciente}_{fecha_ini_str}_a_{fecha_fin_str}_{fecha_subida}.csv"
        
        #Ruta de la carpeta del usuario dentro de static/registros
        ruta_usuario = os.path.join(app.config['RUTA_REGISTROS'], str(id_paciente))
        #Si no existe carpeta para ese usurio la crea
        os.makedirs(ruta_usuario, exist_ok=True)

        #Ruta completa del archivo
        ruta_archivo = os.path.join(ruta_usuario, nombre_archivo).replace('\\', '/')
        #Guardamos el archivo
        archivo.seek(0)  #Puntero al principio del archivo
        archivo.save(ruta_archivo)

        #Crea una instancia del modelo Registros
        nuevo_registro = Registros(paciente=id_paciente, datos_en_crudo=ruta_archivo)
        #Y la añade a la base de datos
        db.session.add(nuevo_registro)
        db.session.commit()

        print('Archivo CSV subido con éxito.')
        
        #Rellenar fecha inicial y final del registro en la bbdd
        actualizar_fechas_registros()
        print('Fechas actualizadas en la base de datos con éxito.')

        #Redireccionar al usuario(medico/admin) a la página anterior
        return redirect(request.referrer)


#Función que guarda en los archivos y sube a la base de datos el vídeo
#del sensor introducido en la app
@app.route('/subirVideo/<id_paciente>', methods=['POST'])
def subir_video(id_paciente):
    if request.method == 'POST':
        archivo_video = request.files['archivo_video']  #Archivo introducido por el médico 
        if archivo_video and VIDEOpermitido(archivo_video.filename):
            #Extrae la fecha, mano dominante, lentitud y amplitud del formulario
            fecha_video = request.form['fecha_video']
            mano_dominante = request.form['mano']
            lentitud = request.form['lentitud']
            amplitud = request.form['amplitud']

            #Obtener la fecha y hora actual(con segundos)
            fecha_subida = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            #Generar un nombre único para el archivo
            # ID_id_paciente_FECHA_MANO_FechaDeSubida.mp4
            nombre_archivo = f"ID{id_paciente}_{fecha_video}_{mano_dominante}_{fecha_subida}.mp4"

            #Carpeta donde se van a guardar los vídeos
            ruta_usuario = os.path.join(app.config['RUTA_VIDEOS'], str(id_paciente))
            #Si no existe carpeta para ese usurio la crea
            os.makedirs(ruta_usuario, exist_ok=True)
    
            #Ruta completa del archivo
            ruta_archivo = os.path.join(ruta_usuario, nombre_archivo).replace('\\', '/')
            #Guardamos el archivo
            archivo_video.save(ruta_archivo)

            #Crea una nueva instancia del modelo Videos
            nuevo_video = Videos(paciente=id_paciente, fecha=fecha_video, contenido=nombre_archivo, mano_dominante=mano_dominante, lentitud=lentitud, amplitud=amplitud)
            #Y la añade a la base de datos
            db.session.add(nuevo_video)
            db.session.commit()

            #Analizar vídeo subido para sacar sus características
            analizarVideos()

            print('Archivo de vídeo subido con éxito.')
            return jsonify({'message': 'Archivo de vídeo subido con éxito.'})
    return '', 400
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de bienvenida para médicos. Contiene:
#       - Barra superior con el perfil del usuario
#       - Datos de médico y botón para cerrar sesión
#       - Botón de acceso al listado de sus pacientes
@app.route('/BienvenidaMedico')
def BienvenidaMedico():
    #Verificar si el usuario está logueado como médico
    if 'username' not in session or session.get('rol') != 'medico':
        print('Se debe iniciar sesión como médico para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))

    #Nombre de usuario del medico logeado
    username_medico = session.get('username')

    #Objeto de ese medico en la bbdd
    medico = Medico.query.filter_by(nombre_de_usuario=username_medico).first()

    #Si no existe en la bbdd
    if not medico:
        print('No se encontró ese usuario en la base de datos', 'error')
        return redirect(url_for('login'))
    
    return render_template('BienvenidaMedico.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra el listado de sus pacientes a los médicos,
#permitiendo realizar ciertas acciones sobre ellos
@app.route('/listadoPacientes')
def listadoPacientes():
    #Verificar si el usuario está logueado como médico
    if 'username' not in session or session.get('rol') != 'medico':
        print('Se debe iniciar sesión como médico para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))
    
    #Qué médico pidió el listado
    username_medico = session.get('username')
    medico = Medico.query.filter_by(nombre_de_usuario=username_medico).first()

    #Consulta para obtener todos los pacientes del médico logeado
    listadoPacientes = Paciente.query.filter_by(id_medico=medico.id_medico).all()

    return render_template('listadoPacientes.html', pacientes=listadoPacientes)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra los datos del sensor del paciente.
#Filtra por usuario logueado y obtiene las fechas en las que hay
#registros del paciente para mostrarlas en el calendario
@app.route('/mostrarDatosSensor/<paciente>', methods=['GET', 'POST'])
def mostrarDatosSensor(paciente):
    #Verificar si el usuario está logueado
    if 'username' not in session:
        print('Se debe iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))
    
    #Obtener el rol del usuario de la sesión
    rol_usuario = session.get('rol')

    #Si es administrador, puede ver las gráficas de todos
    if rol_usuario == 'administrador':
        es_admin = True
        es_paciente = False
        es_medico = False
        pass
    #Si es paciente, solo puede acceder si coincide con el paciente pasado en la URL
    elif rol_usuario == 'paciente':
        es_admin = False
        es_paciente = True
        es_medico = False
        username_paciente = session.get('username')
        #Objeto de ese paciente en la bbdd
        pacienteSesion = Paciente.query.filter_by(nombre_de_usuario=username_paciente).first()
        idPacienteSesion= pacienteSesion.id_paciente
        #Si no coinciden, redirige a la pagina principal
        if str(paciente) != str(idPacienteSesion):
            print('Solo puedes acceder a tus propios datos', 'error')
            return redirect(url_for('paginaprincipal'))
    #Si es médico, verificar si el paciente está en su lista de pacientes asociados
    elif rol_usuario == 'medico':
        es_admin = False
        es_paciente = False
        es_medico = True
        username_medico = session.get('username')
        #Objeto de ese medico en la bbdd
        medico = Medico.query.filter_by(nombre_de_usuario=username_medico).first()
        listadoPacientes = Paciente.query.filter_by(id_medico=medico.id_medico).all() #Sus pacientes asociados
        listado_id_Pacientes = [str(paciente.id_paciente) for paciente in listadoPacientes] #Los id de sus pacientes
        #Si no está en la lista, redirige a la pagina principal
        if str(paciente) not in listado_id_Pacientes:
            print('No tienes permiso para acceder a los datos de este paciente', 'error')
            return redirect(url_for('paginaprincipal'))
    
    #base de datos de ese paciente
    bbddpaciente = Paciente.query.get(paciente)
    #Todos sus registros
    registros = Registros.query.filter_by(paciente=paciente).all()
    #Fechas en las que hay registros de ese paciente(para poner enable en el calendario)
    fechas = []
    for registro in registros:
        rango_fechas = generar_rango_fechas(registro.fecha_inicial, registro.fecha_final)
        #Agregar el rango de fechas en forma Y-m-d de ese registro al array
        fechas.extend([fecha.strftime('%Y-%m-%d') for fecha in rango_fechas])
    #Eliminar duplicados y ordenar las fechas
    fechas = sorted(set(fechas))
    #Convertir a una cadena JSON
    fechas_json = json.dumps(fechas)

    return render_template('mostrarDatosSensor.html', bbddpaciente=bbddpaciente, fechas=fechas_json, es_admin=es_admin, es_medico=es_medico, es_paciente=es_paciente)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Función para generar un rango de fechas entre dos fechas pasadas por parámetro
def generar_rango_fechas(fecha_inicial, fecha_final):
    delta = timedelta(days=1)
    fecha_actual = fecha_inicial
    while fecha_actual <= fecha_final:
        yield fecha_actual
        fecha_actual += delta
#----------------------------------------------------------------



#----------------------------------------------------------------
#Alteracion de la funcion creada por el equipo de desarrollo del sensor
#Se ha transformado para que genere los datos para crear las gráficas
#con chart.js en vez de crearlas con matploitlib
def plot3Axis(dataP, data, title, ylabel, xlabel, GeneralTitle, dayIni, dayFin):
    dataByDays = returnByDatas(dataP, dayIni, dayFin)
    dataByDays = dataByDays.fillna(0) #Cambia los NaN por 0
    time = [datetime.utcfromtimestamp(item / 1000.) for item in dataByDays['EPO']]

    data_values_list = []  #Lista para almacenar los datos de múltiples gráficos

    #Iterar sobre ColumnasAEstudiar (3 o 4 gráficos diferentes)
    for i, column in enumerate(data):
        data_values = {
            'labels': [t.strftime('%Y-%m-%d') for t in time], #Fechas en el eje X
            'datasets': [{
                'label': title[i], #Título de ese gráfico
                'data': dataByDays[column].tolist(), #Datos en esos días
                'yAxisID': ylabel[i], #Medida del Eje Y para ese gráfico
                'fill': False
            }]
        }
        data_values_list.append(data_values) #Añadir datos de ese gráfico en el total

    data_values_list.insert(0, {'GeneralTitle': GeneralTitle}) #Tíitulo general de las 3 gráficas
    
    return json.dumps(data_values_list) #Lo enviamos como JSON
#----------------------------------------------------------------



#----------------------------------------------------------------
#Alteracion de la funcion programada por los creadores del sensor para 
#preparar los datos para la funcion plot3Axis, filtrando los datos por fechas
def returnByDatas(data, ini, fin):
    if ini != -1 and fin != -1: #Si no son -1 
        #Transformamos los EPO a fecha y comparamos con ini y fin
        fechas_epo = [datetime.utcfromtimestamp(epo/1000) for epo in data['EPO']]
        fechas_df = pd.DataFrame({'EPO': fechas_epo})
        #Filtrar datos por fecha
        datosFiltrados = data[(fechas_df['EPO'] >= ini) & (fechas_df['EPO'] <= fin)]
    else:
        datosFiltrados = data  #Sino devuelve todos los datos sin filtrar
    return datosFiltrados
#----------------------------------------------------------------



#----------------------------------------------------------------
#Funcion que crea la gráfica a partir de lo enviado en el formulario
@app.route('/crearGrafico', methods=['POST'])
def crearGrafico():
    #Idioma actual 
    idioma_cookie = request.cookies.get('idioma')

    #Qué gráfico mostrar dependiendo de la seleccion del formulario        
    seleccion_grafico = request.form.get('seleccionGrafico')
    if seleccion_grafico == '1':
        if idioma_cookie == 'en':
            ColumnasAEstudiar = ['W_MEAN_FILT', 'W_STD', 'NUM_WALK']
            TitulosGraficas = ['Filtered Mean Gait', 'Standard Deviation of Gait', 'Number of Considered Steps']
            EjeYMedidas = ['m/s\u00b2','m/s\u00b2','Number of steps']
            TituloGeneral = 'Bradykinesia parameters'
        
        elif idioma_cookie == 'fr':
            ColumnasAEstudiar = ['W_MEAN_FILT', 'W_STD', 'NUM_WALK']
            TitulosGraficas = ['Marche moyenne filtrée', 'Écart-type moyen de la marche', 'Nombre de pas considérés']
            EjeYMedidas = ['m/s\u00b2','m/s\u00b2','Nombre de pas']
            TituloGeneral = 'Paramètres de bradykinésie'

        else:
            ColumnasAEstudiar = ['W_MEAN_FILT', 'W_STD', 'NUM_WALK']
            TitulosGraficas = ['Marcha media filtrada', 'Desviación estándar media de la marcha', 'Número de pasos considerados']
            EjeYMedidas = ['m/s\u00b2','m/s\u00b2','nº pasos']
            TituloGeneral = 'Parámetros de Bradicinesia'

    elif seleccion_grafico == '2':
        if idioma_cookie == 'en':
            ColumnasAEstudiar = ['FOG_EP', 'DYSKP', 'DYSKC']
            TitulosGraficas = ['FoG Episodes', 'Probability of Dyskinesia', 'Confidence in Dyskinesia']
            EjeYMedidas = ['Episodes', 'Probability', 'Confidence']
            TituloGeneral = 'FoG and dyskinesia parameters'
        
        elif idioma_cookie == 'fr':
            ColumnasAEstudiar = ['FOG_EP', 'DYSKP', 'DYSKC']
            TitulosGraficas = ['Épisodes de FoG', 'Probabilité de dyskinésie', 'Confiance en la dyskinésie']
            EjeYMedidas = ['Épisodes', 'Probabilité', 'Confiance']
            TituloGeneral = 'Paramètres de FoG et de dyskinésie'

        else:
            ColumnasAEstudiar = ['FOG_EP', 'DYSKP', 'DYSKC']
            TitulosGraficas = ['Episodios de FoG', 'Probabilidad de discinesia','Confianza en la discinesia']
            EjeYMedidas = ['Episodios','Probabilidad','Confianza']
            TituloGeneral = 'Parámetros de FoG y Discinesia'

    elif seleccion_grafico == '3':
        if idioma_cookie == 'en':
            ColumnasAEstudiar = ['LEN', 'NUM_STEPS', 'SPEED', 'CAD']
            TitulosGraficas = ['Step Length', 'Number of Steps', 'Stride Speed', 'Step Cadence']
            EjeYMedidas = ['m', 'Number of steps', 'm/s', 'steps/min']
            TituloGeneral = 'Step information'
            
        elif idioma_cookie == 'fr':
            ColumnasAEstudiar = ['LEN', 'NUM_STEPS', 'SPEED', 'CAD']
            TitulosGraficas = ['Longueur des pas', 'Nombre de pas', 'Vitesse de pas', 'Cadence des pas']
            EjeYMedidas = ['m', 'Nombre de pas', 'm/s', 'pas/min']
            TituloGeneral = 'Informations sur les pas'

        else:
            ColumnasAEstudiar = ['LEN', 'NUM_STEPS', 'SPEED', 'CAD']
            TitulosGraficas = ['Longitud de los pasos', 'Número de pasos', 'Velocidad de zancada', 'Cadencia de los pasos']
            EjeYMedidas = ['m','nº pasos','m/s','pasos/min']
            TituloGeneral = 'Información de los pasos'

    elif seleccion_grafico == '4':
        if idioma_cookie == 'en':
            ColumnasAEstudiar = ['MOTOR10', 'DYSK10', 'BRADY10']
            TitulosGraficas = ['Motor State 10 min', 'Dyskinesia 10 min', 'Bradykinesia 10 min']
            EjeYMedidas = ['0=OFF 1=ON 2=INT 3=NaN','0,3=NaN 1=Dysk yes 2=No Dysk','0=OFF 1=ON 2=INT 3=NaN']
            TituloGeneral = 'Motor state, dyskinesia, and bradykinesia parameters at 10 min' 

        elif idioma_cookie == 'fr':
            ColumnasAEstudiar = ['MOTOR10', 'DYSK10', 'BRADY10']
            TitulosGraficas = ['État moteur 10 min', 'Dyskinésie 10 min', 'Bradykinésie 10 min']
            EjeYMedidas = ['0=OFF 1=ON 2=INT 3=NaN','0,3=NaN 1=Dysk yes 2=No Dysk','0=OFF 1=ON 2=INT 3=NaN']
            TituloGeneral = 'Paramètres de le état moteur, dyskinésie et bradykinésie à 10 min'
        
        else:
            ColumnasAEstudiar = ['MOTOR10', 'DYSK10', 'BRADY10']
            TitulosGraficas = ['Estado motor 10 min', 'Discinesia 10 min', 'Bradicinesia 10 min']
            EjeYMedidas = ['0=OFF 1=ON 2=INT 3=NaN','0,3=NaN 1=Dysk yes 2=No Dysk','0=OFF 1=ON 2=INT 3=NaN']
            TituloGeneral = 'Parámetros de Estado Motor, Discinesia y Bradicinesia a 10 min'

    #Fecha inicio y fin del gráfico
    fecha_desde = request.form.get('fechaInicio')
    fecha_hasta = request.form.get('fechaFin')
    
    #Convertir las fechas a objetos datetime
    diaIni = datetime.strptime(fecha_desde, '%Y-%m-%d')
    diaFin = datetime.strptime(fecha_hasta, '%Y-%m-%d')

    #Escoger diaIni desde el principio del dia y diaFin hasta el final del dia
    diaIni = datetime.combine(diaIni.date(), time.min)
    diaFin = datetime.combine(diaFin.date(), time.max)
    
    #Datos de los registros del paciente
    id_paciente= request.form.get('id_paciente') #Qué paciente es
    #Todos sus registros    
    registros = Registros.query.filter_by(paciente=id_paciente).all()
    #Registro que contenga las fechas ini y fin
    registro_seleccionado = None
    for registro in registros:
        if registro.fecha_inicial <= diaIni.date() and registro.fecha_final >= diaFin.date():
            registro_seleccionado = registro
            break
    dataFrame_registro = pd.read_csv(registro_seleccionado.datos_en_crudo)

    #Llamada a la función hecha por S4C SDK
    datos_grafico = plot3Axis(dataFrame_registro, ColumnasAEstudiar, TitulosGraficas, EjeYMedidas, 'Data', TituloGeneral, diaIni, diaFin)

    return jsonify(datos_grafico = datos_grafico)
#----------------------------------------------------------------     



#----------------------------------------------------------------
#Página que muestra los vídeos del paciente a los médicos (admins y ese paciente).
#Muestra también gráficas con las características de los datos en el tiempo
#y permite predecirlas
@app.route('/mostrarVideos/<paciente>', methods=['GET', 'POST'])
def mostrarVideos(paciente):
    #Verificar si el usuario está logueado
    if 'username' not in session:
        print('Se debe iniciar sesión para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))
    
    #Obtener el rol del usuario de la sesión
    rol_usuario = session.get('rol')

    #Si es administrador, puede ver las gráficas de todos
    if rol_usuario == 'administrador':
        es_admin = True
        es_paciente = False
        es_medico = False
        pass
    #Si es paciente, solo puede acceder si coincide con el paciente pasado en la URL
    elif rol_usuario == 'paciente':
        es_admin = False
        es_paciente = True
        es_medico = False
        username_paciente = session.get('username')
        #Objeto de ese paciente en la bbdd
        pacienteSesion = Paciente.query.filter_by(nombre_de_usuario=username_paciente).first()
        idPacienteSesion= pacienteSesion.id_paciente
        #Si no coinciden, redirige a la pagina principal
        if str(paciente) != str(idPacienteSesion):
            print('Solo puedes acceder a tus propios videos', 'error')
            return redirect(url_for('paginaprincipal'))
    #Si es médico, verificar si el paciente está en su lista de pacientes asociados
    elif rol_usuario == 'medico':
        es_admin = False
        es_paciente = False
        es_medico = True
        username_medico = session.get('username')
        #Objeto de ese medico en la bbdd
        medico = Medico.query.filter_by(nombre_de_usuario=username_medico).first()
        listadoPacientes = Paciente.query.filter_by(id_medico=medico.id_medico).all() #Sus pacientes asociados
        listado_id_Pacientes = [str(paciente.id_paciente) for paciente in listadoPacientes] #Los id de sus pacientes
        #Si no está en la lista, redirige a la pagina principal
        if str(paciente) not in listado_id_Pacientes:
            print('No tienes permiso para acceder a los videos de este paciente', 'error')
            return redirect(url_for('paginaprincipal'))
    
    #base de datos de ese paciente
    bbddpaciente = Paciente.query.get(paciente)

    #vídeos de ese paciente
    videos = Videos.query.filter_by(paciente=paciente).all()
    #filtrar por mano del video
    videos_dcha = [video for video in videos if video.mano_dominante == 'derecha']
    videos_izq = [video for video in videos if video.mano_dominante == 'izquierda']

    #Las características de los vídeos las convertimos para generar la Gráfica
    datosVideos_dcha = [{
        'lentitud': video.lentitud,
        'amplitud': video.amplitud,
        'velocidad_media': video.velocidad_media,
        'frecuencia_max': video.frecuencia_max,
        'frecuencia_min': video.frecuencia_min,
        'promedio_max': video.promedio_max,
        'desv_estandar_max': video.desv_estandar_max,
        # 'diferencia_ranurada_min': video.diferencia_ranurada_min,
        # 'diferencia_ranurada_max': video.diferencia_ranurada_max,
        'fecha': video.fecha
    } for video in videos_dcha]

    datosVideos_izq = [{
        'lentitud': video.lentitud,
        'amplitud': video.amplitud,
        'velocidad_media': video.velocidad_media,
        'frecuencia_max': video.frecuencia_max,
        'frecuencia_min': video.frecuencia_min,
        'promedio_max': video.promedio_max,
        'desv_estandar_max': video.desv_estandar_max,
        # 'diferencia_ranurada_min': video.diferencia_ranurada_min,
        # 'diferencia_ranurada_max': video.diferencia_ranurada_max,
        'fecha': video.fecha
    } for video in videos_izq]

    return render_template('mostrarVideos.html', bbddpaciente=bbddpaciente, videos=videos, datosVideos_dcha=datosVideos_dcha, datosVideos_izq=datosVideos_izq, es_admin=es_admin, es_medico=es_medico, es_paciente=es_paciente)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Función que elimina el vídeo seleccionado
@app.route('/eliminarVideo', methods=['POST'])
def eliminarVideo():
    if request.method == 'POST':
        id_video = request.json['id_video']
        video = Videos.query.get(id_video)
        
        #Eliminar video de los archivos
        ruta_archivo = os.path.join(app.config['RUTA_VIDEOS'], str(video.paciente), video.contenido)
        try:
            #Eliminar
            os.remove(ruta_archivo)
        except OSError as e:
            print(f"No se pudo eliminar el archivo: {e}")
            return 'Error al eliminar el archivo', 500

        #Eliminar video de la bbdd
        db.session.delete(video)
        db.session.commit()
        return 'Vídeo eliminado correctamente', 200
    else:
        return 'Método no permitido', 405
#----------------------------------------------------------------



#----------------------------------------------------------------
#Función que predice las características de los videos con IA
#a partir de los datos disponibles utilizando el modelo 
#de suavizado exponencial de Holt
@app.route('/predecirVideo', methods=['POST'])
def predecirVideo():
    data = request.get_json()
    datos_videos_izq = data['datosVideos_izq']
    datos_videos_dcha = data['datosVideos_dcha']

    predicciones_izq = {}
    predicciones_dcha = {}
    n_pasos = 4 #Número de pasos hacia adelante para predecir

    #Predecir los datos de la mano izquierda
    for key in datos_videos_izq[0].keys():
        if key == 'fecha':
            continue
        #Por cada carcaterística 
        serie_tiempo_izq = [dato[key] for dato in datos_videos_izq]
        serie_tiempo_izq = [float(valor) for valor in serie_tiempo_izq]  # Convertir a float

        #Suavizado exponencial de Holt
        modelo_izq = Holt(serie_tiempo_izq) 

        #Entrenar modelo
        modelo_fit_izq = modelo_izq.fit()
        
        #Realizar la predicción para los próximos 'n_pasos' pasos
        prediccion_izq = modelo_fit_izq.forecast(n_pasos)
        
        #Guardar las predicciones para esa carcaterística
        predicciones_izq[key] = list(prediccion_izq)

    #Predecir los datos de la mano derecha
    for key in datos_videos_dcha[0].keys():
        if key == 'fecha':
            continue
        #Por cada carcaterística
        serie_tiempo_dcha = [dato[key] for dato in datos_videos_dcha]
        serie_tiempo_dcha = [float(valor) for valor in serie_tiempo_dcha]  # Convertir a float

        #Suavizado exponencial de Holt
        modelo_dcha = Holt(serie_tiempo_dcha) 

        #Entrenar modelo
        modelo_fit_dcha = modelo_dcha.fit()

        #Realizar la predicción para los próximos 'n_pasos' pasos
        prediccion_dcha = modelo_fit_dcha.forecast(n_pasos)

        #Guardar las predicciones para esa carcaterística
        predicciones_dcha[key] = list(prediccion_dcha)


    #Generar fechas futuras a partir de la última fecha en los datos
    def generar_fechas_futuras(fechas_existentes, n_pasos):
        #Convierte a datatime para trabajar con ellas
        fechas_existentes_dt = [datetime.strptime(fecha, '%a, %d %b %Y %H:%M:%S %Z') for fecha in fechas_existentes]
        #Calcula el intervalo entre fechas restando la primera y la última y dividiendo entre el número de fechas
        intervalo = (fechas_existentes_dt[-1] - fechas_existentes_dt[0]) / (len(fechas_existentes_dt) - 1)
        #Genera tantas fechas futuras como n pasos
        fechas_futuras = [(fechas_existentes_dt[-1] + intervalo * (i + 1)).strftime('%a, %d %b %Y %H:%M:%S %Z') for i in range(n_pasos)]
        return fechas_futuras


    #Fechas existentes en los datos
    fechas_existentes_izq = [dato['fecha'] for dato in datos_videos_izq]
    fechas_existentes_dcha = [dato['fecha'] for dato in datos_videos_dcha]

    #Llamar a la función para ampliar las fechas con fechas futuras
    fechas_futuras_izq = generar_fechas_futuras(fechas_existentes_izq, n_pasos)
    fechas_futuras_dcha = generar_fechas_futuras(fechas_existentes_dcha, n_pasos)

    #Juntar las predicciones con las fechas
    resultados_prediccion_izq = [{'fecha': fechas_futuras_izq[i], **{key: predicciones_izq[key][i] for key in predicciones_izq.keys()}} for i in range(n_pasos)]
    resultados_prediccion_dcha = [{'fecha': fechas_futuras_dcha[i], **{key: predicciones_dcha[key][i] for key in predicciones_dcha.keys()}} for i in range(n_pasos)]

    #Juntar las predicciones a los datos originales
    datos_con_prediccion_izq = datos_videos_izq + resultados_prediccion_izq
    datos_con_prediccion_dcha = datos_videos_dcha + resultados_prediccion_dcha

    #Devolver las predicciones de ambas manos convertidas a cadena json para poder mostrarla con chart.js en el html
    return jsonify({'izquierda': datos_con_prediccion_izq, 'derecha': datos_con_prediccion_dcha})
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de bienvenida para pacientes. Contiene:
#       - Barra superior con el perfil del usuario
#       - Datos de paciente y botón para cerrar sesión
#       - Botón para editar sus datos
#       - Botón de acceso a las gráficas del sensor
#       - Botón de acceso a la página de los vídeos
@app.route('/BienvenidaPaciente') #, methods=['GET', 'POST'])
def BienvenidaPaciente():
    #Verificar si el usuario está logueado como paciente
    if 'username' not in session or session.get('rol') != 'paciente':
        print('Se debe iniciar sesión como paciente para acceder a esta página', 'error')
        return redirect(url_for('paginaprincipal'))

    #Nombre de usuario del admin logeado
    username_paciente = session.get('username')

    #Objeto de ese paciente en la bbdd
    paciente = Paciente.query.filter_by(nombre_de_usuario=username_paciente).first()

    #Si no existe en la bbdd
    if not paciente:
        print('No se encontró ese usuario en la base de datos', 'error')
        return redirect(url_for('login'))

    #Su medico asignado
    medico = Medico.query.get(paciente.id_medico)

    return render_template('BienvenidaPaciente.html', medico=medico)
#----------------------------------------------------------------



if __name__=='__main__':
    #csrf.init_app(app) #Proteccion anti csrf

    app.run(debug=True) #Ejecutar