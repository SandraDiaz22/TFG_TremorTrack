from flask import Flask, jsonify, render_template, request, make_response, session, redirect, url_for, send_from_directory, g, flash

from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

from config import DevelopmentConfig
from modelosbbdd import db, Administrador, Medico, Paciente, Registros, Videos
import hashlib
from flask_babel import Babel, _
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, time

from fechasRegistros import actualizar_fechas_registros, obtener_fechas_registro
from analizarVideos import analizarVideos

import form
import csv
import os
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import io
import base64


from statsmodels.tsa.holtwinters import SimpleExpSmoothing




#Inicializar aplicación
app = Flask(__name__, static_url_path='/static')
babel= Babel(app)

#Configuracion
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
#Traduccion

#Idioma predeterminado (español)
app.config['BABEL_DEFAULT_LOCALE'] = 'es'
#Dicionario de idiomas
app.config['LANGUAGES'] = {
    'en': 'Inglés',
    'es': 'Español',
    'fr': 'Francés'
}

#Funcion que obtiene el idioma preferido del navegador del usuario
#y sino pone el idioma predeterminado
def get_locale():
    idioma_navegador = request.accept_languages.best_match(app.config['LANGUAGES'].keys())
    if idioma_navegador is not None:
        return idioma_navegador
    else:
        return app.config['BABEL_DEFAULT_LOCALE']


#Inicializar babel con get_locale como selector de idioma
babel = Babel(app, locale_selector=get_locale)

#Pasar get_locale a la plantilla
@app.context_processor
def inject_get_locale():
    return dict(get_locale=get_locale)
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
#Mensaje personalizado en las paginas no existentes (error 404)
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
#       - Datos de admin, médico y paciente para las pruebas
#       - Formulario
@app.route('/login', methods=['GET', 'POST'])
def login():    
    #formulario de form.py
    formulario = form.FormularioAcceso(request.form)

    #cuando den al botón de iniciar sesión
    if request.method == 'POST':

        #Obtener datos del formulario
        username = request.form.get('username')
        contraseña = request.form.get('contraseña')

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
            error = 'Credenciales incorrectas. Inténtalo de nuevo.'
            flash(error, 'error')  #Mostrar error al usuario
    

    return render_template('login.html', form=formulario)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de cierre de sesión. Redirige al usuario a la página principal
@app.route('/logout')
def logout():
    session.pop('username', None) #Elimina username de la sesión
    return redirect(url_for('paginaprincipal')) #Redirige a pp
#----------------------------------------------------------------




#----------------------------------------------------------------
#Página de bienvenida para administradores.
#Por ahora solo contiene el tipo de usuario
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
    
    #Obtener el id del admin logueado
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
        if rol == 'paciente':
            usuario = Paciente.query.get_or_404(idUsuario)
        
        elif rol == 'medico':
            usuario = Medico.query.get_or_404(idUsuario)
        
        elif rol == 'administrador':
            usuario = Administrador.query.get_or_404(idUsuario)
        
        db.session.delete(usuario)
        db.session.commit()
        return 'Usuario eliminado correctamente', 200
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
            paciente.sensor = sensor
            paciente.lateralidad = lateralidad
            paciente.fecha_de_nacimiento = fecha_de_nacimiento
            paciente.direccion = direccion
            paciente.telefono = telefono
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
        
        if tipo_usuario == 'paciente':
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
#Página de bienvenida para médicos.
#Por ahora solo contiene foto y dos botones
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
#Página que muestra el listado de pacientes a los médicos.
#Por ahora la lista con los botones pero feo
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
#Página que muestra los datos del sensor del paciente a los médicos.
#Sacamos todos los registros de ese paciente en las fechas selecionadas y creamos la gráfica TODO
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
        #Filtrar datos por fecha (ini y fin son 2019-07-24 00:00:00 2019-07-26 23:59:59.999999)
        #datosFiltrados = data[(data['EPO'] >= ini.timestamp() * 1000) & (data['EPO'] <= fin.timestamp() * 1000)] #saca del 23 al 26
        #datosFiltrados = data[(data['EPO'] >= (ini.timestamp() * 1000) + 86400000) & (data['EPO'] <= (fin.timestamp() * 1000) + 86400000)] #saca del 24 al 27

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
    #Qué gráfico mostrar dependiendo de la seleccion del formulario        
    seleccion_grafico = request.form.get('seleccionGrafico')
    if seleccion_grafico == '1':
        ColumnasAEstudiar = ['W_MEAN_FILT', 'W_STD', 'NUM_WALK']
        TitulosGraficas = ['Marcha media filtrada', 'Desviación estándar media de la marcha', 'Número de pasos considerados']
        EjeYMedidas = ['m/s\u00b2','m/s\u00b2','nº pasos']
        TituloGeneral = 'Parámetros de Bradicinesia'
    elif seleccion_grafico == '2':
        ColumnasAEstudiar = ['FOG_EP', 'DYSKP', 'DYSKC']
        TitulosGraficas = ['Episodios de FoG', 'Probabilidad de discinesia','Confianza en la discinesia']
        EjeYMedidas = ['Episodios','Probabilidad','Confianza']
        TituloGeneral = 'Parámetros de FoG y Discinesia'
    elif seleccion_grafico == '3':
        ColumnasAEstudiar = ['LEN', 'NUM_STEPS', 'SPEED', 'CAD']
        TitulosGraficas = ['Longitud de los pasos', 'Número de pasos', 'Velocidad de zancada', 'Cadencia de los pasos']
        EjeYMedidas = ['m','nº pasos','m/s','pasos/min']
        TituloGeneral = 'Información de los pasos'
    elif seleccion_grafico == '4':
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


    #Llamada genérica a la función hecha por S4C SDK
    datos_grafico = plot3Axis(dataFrame_registro, ColumnasAEstudiar, TitulosGraficas, EjeYMedidas, 'Data', TituloGeneral, diaIni, diaFin)

    return jsonify(datos_grafico = datos_grafico)

#----------------------------------------------------------------     





#----------------------------------------------------------------
#Página que muestra los vídeos del paciente a los médicos (admins y ese paciente).
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
#Función que predice la lentitud o amplitud con IA a partir de los datos disponibles
@app.route('/predecirVideo', methods=['POST'])
def predecirVideo():
    data = request.get_json()
    datos_videos_izq = data['datosVideos_izq']
    datos_videos_dcha = data['datosVideos_dcha']

    predicciones_izq = {}
    predicciones_dcha = {}
        
    
    #Genera fechas futuras
    # fecha_actual = datetime.now().date()
    # n_pasos = 4  # Número de pasos hacia adelante para predecir
    # fechas_futuras = [fecha_actual + timedelta(days=i) for i in range(1, n_pasos + 1)]

    # #Datos + fechas predicción sin datos
    # datos_ampliados = datos_videos + [(fecha, None) for fecha in fechas_futuras]

    #Predecir los datos de la mano izquierda
    for key in datos_videos_izq[0].keys():
        if key == 'fecha':
            continue
        #Por cada carcaterística 
        serie_tiempo_izq = [dato[key] for dato in datos_videos_izq]
        serie_tiempo_izq = [float(valor) for valor in serie_tiempo_izq]  # Convertir a float
        modelo_izq = SimpleExpSmoothing(serie_tiempo_izq) #Ajustar el modelo
        modelo_fit_izq = modelo_izq.fit()
        
        #Realizar la predicción para los próximos 'n_pasos' pasos
        n_pasos = 4
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
        modelo_dcha = SimpleExpSmoothing(serie_tiempo_dcha) #Ajustar el modelo
        modelo_fit_dcha = modelo_dcha.fit()

        #Realizar la predicción para los próximos 'n_pasos' pasos
        n_pasos = 4 
        prediccion_dcha = modelo_fit_dcha.forecast(n_pasos)

        #Guardar las predicciones para esa carcaterística
        predicciones_dcha[key] = list(prediccion_dcha)


    #Generar fechas futuras
    fechas_prediccion_izq = [dato['fecha'] for dato in datos_videos_izq] + [None] * n_pasos
    fechas_prediccion_dcha = [dato['fecha'] for dato in datos_videos_dcha] + [None] * n_pasos

    #Juntar las predicciones con las fechas para cada mano
    resultados_prediccion_izq = [{'fecha': fechas_prediccion_izq[i], **{key: predicciones_izq[key][i] for key in predicciones_izq.keys()}} for i in range(n_pasos)]
    resultados_prediccion_dcha = [{'fecha': fechas_prediccion_dcha[i], **{key: predicciones_dcha[key][i] for key in predicciones_dcha.keys()}} for i in range(n_pasos)]

    print(resultados_prediccion_izq)
    print(resultados_prediccion_dcha)

    #Devolver las predicciones de ambas manos convertidas a cadena json para poder mostrarla con chart.js en el html
    return jsonify({'izquierda': resultados_prediccion_izq, 'derecha': resultados_prediccion_dcha})
    
    
#----------------------------------------------------------------





#----------------------------------------------------------------
#Página de bienvenida para pacientes.
#Por ahora solo contiene el tipo de usuario
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





#@app.route('/upload', methods=['POST'])
#def upload_file():
#    file = request.files['file']
#    if file:
#        filename = secure_filename(file.filename)
#        file.save(os.path.join(app.root_path, 'static', 'registros', filename))
#        # Actualiza la base de datos con la ruta del archivo
#        registro = Registro.query.get(tu_id_registro)
#        registro.ruta_archivo = 'static/registros/' + filename
#        db.session.commit()























#Antiguo. Para saber como coger datos del csv en el futuro
@app.route('/acceso', methods=['POST'])
def acceso():
   
    formulario = form.FormularioAcceso(request.form)
    if request.method == 'POST' and formulario.validate(): #formulario correcto
        #imprimo datos formulario
        print(formulario.username.data)
        print(formulario.contraseña.data)
        #creo sesion
        session['username'] = formulario.username.data

    else:
        print("Error en el formulario.")

    #Obtener nombre y contraseña del formulario
    nombrePaciente = request.form.get("username")
    contraseña = request.form.get("contraseña")
    
    #base de datos
    administrador = Administrador.query.get(1)
    medico = Medico.query.get(1)
    paciente = Paciente.query.get(1)


     # Obtener la ruta completa al archivo CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'prueba.csv')


    with open(csv_path, 'r') as file: #Abrir el CSV para leer los datos
        reader = csv.reader(file)
        data = [row for row in reader] #Convertir los datos a una lista de diccionarios

    return render_template('acceso.html', contraseña=contraseña, username=nombrePaciente, data=data, administrador=administrador, medico=medico, paciente=paciente)



if __name__=='__main__':
    #csrf.init_app(app) #Proteccion anti csrf

    app.run(debug=True) #Ejecutar