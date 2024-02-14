from flask import Flask, render_template, request, make_response, session, redirect, url_for, send_from_directory

from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

import form
from config import DevelopmentConfig
from modelosbbdd import db, Administrador, Medico, Paciente, Registros, Videos
from flask_babel import Babel, _

import csv
import os


#Inicializar aplicación
app = Flask(__name__, static_url_path='/static')
babel= Babel(app)

#Configuracion
app.config.from_object(DevelopmentConfig)

#Conexion base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maria@localhost/parkinson'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)

#Fotos
app.static_folder = 'fotos'



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

    #base de datos
    administrador = Administrador.query.get(1)
    medico = Medico.query.get(1)
    paciente = Paciente.query.get(1)

    #cuando den al botón de iniciar sesión
    if request.method == 'POST':

        #Obtener datos del formulario
        username = request.form.get('username')
        contraseña = request.form.get('contraseña')

        #Diferentes páginas de bienvenida según el usuario
        #Si es administrador
        if username == 'sandradiaz' and contraseña == '1234':
            return redirect(url_for('BienvenidaAdmin', name=username))
        
        #Si es médico
        elif username == 'josefelix' and contraseña == '1234':
            return redirect(url_for('BienvenidaMedico', name=username))
        
        #Si es paciente
        elif username == 'pepeaguilar' and contraseña == '1234':
            return redirect(url_for('BienvenidaPaciente', name=username))
        
        #Si no es ninguno
        else:
            error = 'Credenciales incorrectas. Inténtalo de nuevo.'
            print(error)
    

    return render_template('login.html', form=formulario, administrador=administrador, medico=medico, paciente=paciente)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de bienvenida para administradores.
#Por ahora solo contiene el tipo de usuario
@app.route('/BienvenidaAdmin/<name>')
def BienvenidaAdmin(name):
    return render_template('BienvenidaAdmin.html', name=name)
#----------------------------------------------------------------


#----------------------------------------------------------------
#Página de bienvenida para médicos.
#Por ahora solo contiene foto y dos botones
@app.route('/BienvenidaMedico/<name>')
def BienvenidaMedico(name):
    #base de datos para la foto
    medico = Medico.query.get(1)

    return render_template('BienvenidaMedico.html', name=name, medico=medico)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra el listado de pacientes a los médicos.
#Por ahora la lista con los botones pero feo
@app.route('/listadoPacientes')
def listadoPacientes():
    medico_id = 1 #Quien inició sesion (cambiar a bien hecho)

    #base de datos para la foto
    medico = Medico.query.get(medico_id)

    #Consulta para obtener todos los pacientes del médico logeado
    pacientes = Paciente.query.filter_by(id_medico=medico_id).all()


    return render_template('listadoPacientes.html', medico=medico, pacientes=pacientes)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página que muestra los datos del sensor del paciente a los médicos.
#Por ahora nada
@app.route('/mostrarDatosSensor/<paciente>')
def mostrarDatosSensor(paciente):
    return render_template('mostrarDatosSensor.html', paciente=paciente)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de bienvenida para pacientes.
#Por ahora solo contiene el tipo de usuario
@app.route('/BienvenidaPaciente/<name>', methods=['GET', 'POST'])
def BienvenidaPaciente(name):
    #base de datos para la foto
    paciente = Paciente.query.get(1)
    #base de datos para los registros
    registros = Registros.query.get(1)
    #base de datos para videos
    video = Videos.query.get(1)
   
    # Obtener la ruta completa al archivo CSV
    ruta_archivo = registros.datos_en_crudo
    ruta_completa = os.path.join(app.root_path, ruta_archivo)


    with open(ruta_completa, 'r') as file: #Abrir el CSV para leer los datos
        reader = csv.reader(file)
        data = [row for row in reader] #Convertir los datos a una lista de diccionarios

    return render_template('BienvenidaPaciente.html', name=name, paciente=paciente, data=data, video=video)
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