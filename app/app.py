from flask import Flask, render_template, request, make_response, session
#from flask import g #para variables globales si hubiera
import form
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
import csv
import os
from flask_sqlalchemy import SQLAlchemy
from modelosbbdd import db, Administrador, Medico, Paciente, Registros, Videos


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
csrf = CSRFProtect()


#Mensaje personalizado en las paginas no existentes (error 404)
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


#Decoradores que se ejecutan antes y despues
#@app.before_request
#def before_request():
#    pass
#@app.after_request
#def after_request(response):
#    return response


@app.route('/', methods = ['GET', 'POST'])
def index():
    #return "Hola Mundo!" #Antes de crear index.html

    #nombre = "Sandra" #Pasar variables al html
    #num = 1
    #lista=[1,2,3,4,5,6,7]

    formulario = form.FormularioAcceso(request.form)
    administrador = Administrador.query.get(1)
    medico = Medico.query.get(1)
    paciente = Paciente.query.get(1)

    cookie= request.cookies.get('galletita')
    print(cookie)

    #return render_template('index.html', nombre=nombre, num=num, lista=lista, form=formulario)

    return render_template('index.html', form=formulario, administrador=administrador, medico=medico, paciente=paciente)



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


@app.route('/cookie')
def cookie():
    response = make_response(render_template('cookie.html'))
    response.set_cookie('galletita', 'Cookie de Sandra')
    return response


if __name__=='__main__':
    csrf.init_app(app) #Proteccion anti csrf

    app.run() #Ejecutar