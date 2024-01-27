from flask import Flask, render_template, request, make_response, session, redirect, url_for, send_from_directory

from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy

import form
from config import DevelopmentConfig
from modelosbbdd import db, Administrador, Medico, Paciente, Registros, Videos

import csv
import os


#Inicializar aplicación
app = Flask(__name__)

#Configuracion
app.config.from_object(DevelopmentConfig)

#Conexion base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:maria@localhost/parkinson'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#Fotos
app.static_folder = 'fotos'

#Proteccion anti cross-site request forgery
#csrf = CSRFProtect()
#quitado de login porque daba error aunque antes funcionaba
            #<!-- Campos ocultos vs ataques
            #{{ form.honeypot }}
            #<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/> -->



#----------------------------------------------------------------
#Mensaje personalizado en las paginas no existentes (error 404)
@app.errorhandler(404)
def page_not_found(e):
    if request.method == 'POST':
        return redirect(url_for('paginaprincipal'))
    
    return render_template('404.html'), 404
#----------------------------------------------------------------



#----------------------------------------------------------------
#Ruta para poder mostrar las imágenes
@app.route('/get_image/<filename>')
def get_image(filename):
    return send_from_directory('static/fotos', filename)
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página principal de la aplicación. Contiene:
#       - Información sobre las funciones de TremorTrack
#       - Logos
#       - Barra superior con diferentes funcionalidades (Sobre nosotros, Contacto, Idioma)
#       - Botón que lleva al formulario de Iniciar Sesión
@app.route('/', methods = ['GET', 'POST'])
def paginaprincipal():
    if request.method == 'POST':
        return redirect(url_for('login'))

    return render_template('paginaprincipal.html')
#----------------------------------------------------------------



#----------------------------------------------------------------
#Página de inicio de sesión. Contiene:
#       - Datos de admin, médico y paciente para las pruebas
#       - Formulario
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
#Por ahora solo contiene el tipo de usuario
@app.route('/BienvenidaMedico/<name>')
def BienvenidaMedico(name):
    #base de datos para la foto
    medico = Medico.query.get(1)

    return render_template('BienvenidaMedico.html', name=name, medico=medico)
#----------------------------------------------------------------


#----------------------------------------------------------------
#Página de bienvenida para pacientes.
#Por ahora solo contiene el tipo de usuario
@app.route('/BienvenidaPaciente/<name>', methods=['GET', 'POST'])
def BienvenidaPaciente(name):
    #base de datos para la foto
    paciente = Paciente.query.get(1)

    return render_template('BienvenidaPaciente.html', name=name, paciente=paciente)
#----------------------------------------------------------------





























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

    app.run() #Ejecutar