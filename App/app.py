from flask import Flask, render_template, request, make_response, session, redirect, url_for, send_from_directory, g, flash

from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

import form
from config import DevelopmentConfig
from modelosbbdd import db, Administrador, Medico, Paciente, Registros, Videos
from flask_babel import Babel, _
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from Support_v0 import plot3Axis, returnByDatas

import csv
import os

import pandas as pd


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

#Determina la página en la que nos encontramos
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
    if archivo and CSVpermitido(archivo.filename):
        nombre_archivo = secure_filename(archivo.filename)

        #Ruta de la carpeta del usuario dentro de static/registros
        ruta_usuario = os.path.join(app.config['RUTA_REGISTROS'], str(id_paciente))
        #Si no existe carpeta para ese usurio la crea
        os.makedirs(ruta_usuario, exist_ok=True)

        #Ruta completa del archivo
        ruta_archivo = os.path.join(ruta_usuario, nombre_archivo).replace('\\', '/')
        #Guardamos el archivo
        archivo.save(ruta_archivo)

        #Extrae la fecha del formulario
        fecha_registro = request.form['fecha_sensor']

        #Crea una instancia del modelo Registros
        nuevo_registro = Registros(paciente=id_paciente, fecha=fecha_registro, datos_en_crudo=ruta_archivo)
        #Y la añade a la base de datos
        db.session.add(nuevo_registro)
        db.session.commit()

        flash('Archivo CSV subido con éxito.')
        return redirect(url_for('listadoPacientes'))



@app.route('/subirVideo/<id_paciente>', methods=['POST'])
def subir_video(id_paciente):
    archivo_video = request.files['archivo_video']  #Archivo introducido por el médico 
    if archivo_video and VIDEOpermitido(archivo_video.filename):
        nombre_archivo = secure_filename(archivo_video.filename)

        #Carpeta donde se van a guardar los vídeos
        ruta_usuario = os.path.join(app.config['RUTA_VIDEOS'], str(id_paciente))
        #Si no existe carpeta para ese usurio la crea
        os.makedirs(ruta_usuario, exist_ok=True)
   
        #Ruta completa del archivo
        ruta_archivo = os.path.join(ruta_usuario, nombre_archivo).replace('\\', '/')
        #Guardamos el archivo
        archivo_video.save(ruta_archivo)

        #Extrae la fecha y mano dominante del formulario
        fecha_video = request.form['fecha_video']
        mano_dominante = request.form['mano']

        #Crea una nueva instancia del modelo Videos
        nuevo_video = Videos(paciente=id_paciente, fecha=fecha_video, contenido=nombre_archivo, mano_dominante=mano_dominante)
        #Y la añade a la base de datos
        db.session.add(nuevo_video)
        db.session.commit()

        flash('Archivo de vídeo subido con éxito.')
        return redirect(url_for('listadoPacientes'))





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
@app.route('/get_video/<filename>')
def get_video(filename):
    return send_from_directory('static/videos', filename)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Mensaje personalizado en las paginas no existentes (error 404)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página principal de la aplicación. Contiene:
#       - Barra superior con diferentes funcionalidades (Sobre nosotros, Contacto, Idioma, Iniciar Sesión)
#       - Información sobre las funciones de TremorTrack
#       - Logos
@app.route('/', methods = ['GET', 'POST'])
def paginaprincipal():
    return render_template('paginaprincipal.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página con información sobre los creadores de la página. Contiene:
#       - Barra superior con diferentes funcionalidades (Sobre nosotros, Contacto, Idioma, Página principal, Iniciar Sesión)
#       - Información sobre nosotros
#       - Logos
@app.route('/sobreNosotros', methods = ['GET', 'POST'])
def sobreNosotros():
    return render_template('sobreNosotros.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página con información de contacto. Contiene:
#       - Barra superior con diferentes funcionalidades (Sobre nosotros, Contacto, Idioma, Página principal, Iniciar Sesión)
#       - Información de contacto
#       - Logos
@app.route('/contacto', methods = ['GET', 'POST'])
def contacto():
    return render_template('contacto.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de inicio de sesión. Contiene:
#       - Barra superior con diferentes funcionalidades (Sobre nosotros, Contacto, Idioma, Página principal)
#       - Datos de admin, médico y paciente para las pruebas
#       - Formulario
#       - Logos
@app.route('/login', methods=['GET', 'POST'])
def login():

    #formulario de form.py
    formulario = form.FormularioAcceso(request.form)


    #cuando den al botón de iniciar sesión
    if request.method == 'POST':

        #Obtener datos del formulario
        username = request.form.get('username')
        contraseña = request.form.get('contraseña')

        #Buscar en la bbdd las credenciales
        usuario_medico = Medico.query.filter_by(nombre_de_usuario=username, contraseña=contraseña).first()
        usuario_administrador = Administrador.query.filter_by(nombre_de_usuario=username, contraseña=contraseña).first()
        usuario_paciente = Paciente.query.filter_by(nombre_de_usuario=username, contraseña=contraseña).first()


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
            print(error)
    

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
    #Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Se debe iniciar sesión como administrador para acceder a esta página', 'error')
        return redirect(url_for('login'))

    #Nombre de usuario del admin logeado
    username_admin = session.get('username')

    #Objeto de ese admin en la bbdd
    admin = Administrador.query.filter_by(nombre_de_usuario=username_admin).first()
    
    #Si no existe en la bbdd
    if not admin:
        flash('No se encontró ese usuario en la base de datos', 'error')
        return redirect(url_for('login'))
    
    return render_template('BienvenidaAdmin.html')
#----------------------------------------------------------------


#----------------------------------------------------------------
#Página de bienvenida para médicos.
#Por ahora solo contiene foto y dos botones
@app.route('/BienvenidaMedico')
def BienvenidaMedico():
    #Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Se debe iniciar sesión como médico para acceder a esta página', 'error')
        return redirect(url_for('login'))

    #Nombre de usuario del admin logeado
    username_medico = session.get('username')

    #Objeto de ese medico en la bbdd
    medico = Medico.query.filter_by(nombre_de_usuario=username_medico).first()

    #Si no existe en la bbdd
    if not medico:
        flash('No se encontró ese usuario en la base de datos', 'error')
        return redirect(url_for('login'))
    
    return render_template('BienvenidaMedico.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra el listado de pacientes a los médicos.
#Por ahora la lista con los botones pero feo
@app.route('/listadoPacientes')
def listadoPacientes():
    #Qué médico pidió el listado
    username_medico = session.get('username')
    medico = Medico.query.filter_by(nombre_de_usuario=username_medico).first()

    #Consulta para obtener todos los pacientes del médico logeado
    listadoPacientes = Paciente.query.filter_by(id_medico=medico.id_medico).all()

    return render_template('listadoPacientes.html', pacientes=listadoPacientes)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra los datos del sensor del paciente a los médicos.
#Sacamos todos los registros de ese paciente en las fechas selecionadas y creamos la gráfica
@app.route('/mostrarDatosSensor/<paciente>', methods=['GET', 'POST'])
def mostrarDatosSensor(paciente):
    #base de datos de ese paciente
    bbddpaciente = Paciente.query.get(paciente)

    #Formulario de qué grafico mostrar
    if request.method == 'POST':
        fecha_desde = request.form.get('fecha_desde')
        fecha_hasta = request.form.get('fecha_hasta')

        #cnvertir las fechas a objetos datetime como los de la bbdd
        fecha_desde = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
        fecha_hasta = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()

        #registros de ese paciente dentro de esas fechas
        registros = Registros.query.filter_by(paciente=paciente) \
                                    .filter(Registros.fecha.between(fecha_desde, fecha_hasta)).all()
        
        #si no tiene registros hacer algo (MEJORARLO)
        if not registros:
            flash('No se encontraron registros para ese usuario en la base de datos', 'error')
            return redirect(url_for('listadoPacientes'))
        
        #extraer los datos de los CSV de esas fechas
        datos_en_crudo = []
        for registro in registros:
            archivo_csv = os.path.join(app.root_path, registro.datos_en_crudo)
            datos_registro = pd.read_csv(archivo_csv)
            datos_en_crudo.append(datos_registro)
        
        #generar el gráfico
        for columnas in datos_en_crudo:
            if 'EPO' in columnas.columns and 'NUM_STEPS' in columnas.columns:
                dataP = datos_registro[['EPO', 'NUM_STEPS']]
        
                #Función de support_v0 para crear gráficos con matplotlib
                plot3Axis(dataP, ['NUM_STEPS'], ['Título:Número de pasos detectados'], ['Eje y: nº de pasos'], ['Eje x: Tiempo'], 'Título general del gráfico', fecha_desde, fecha_hasta)


        return render_template('mostrarDatosSensor.html', bbddpaciente=bbddpaciente, data=datos_en_crudo)

    #Si no envian formulario
    return render_template('mostrarDatosSensor.html', bbddpaciente=bbddpaciente)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de bienvenida para pacientes.
#Por ahora solo contiene el tipo de usuario
@app.route('/BienvenidaPaciente') #, methods=['GET', 'POST'])
def BienvenidaPaciente():
    #Verificar si el usuario está logueado
    if 'username' not in session:
        flash('Se debe iniciar sesión como paciente para acceder a esta página', 'error')
        return redirect(url_for('login'))

    #Nombre de usuario del admin logeado
    username_paciente = session.get('username')

    #Objeto de ese paciente en la bbdd
    paciente = Paciente.query.filter_by(nombre_de_usuario=username_paciente).first()

    #Si no existe en la bbdd
    if not paciente:
        flash('No se encontró ese usuario en la base de datos', 'error')
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