from flask import Flask, render_template, request, make_response, session
import form
from flask_wtf import CSRFProtect

#Inicializar aplicación
app = Flask(__name__)
#Clave secreta para firmar sesiones
app.secret_key = 'contraseña_super_mega_secreta'
#Proteccion anti cross-site request forgery
csrf = CSRFProtect(app)



@app.route('/', methods = ['GET', 'POST'])
def index():
    #return "Hola Mundo!" #Antes de crear index.html

    nombre = "Sandra" #Pasar variables al html
    num = 1
    lista=[1,2,3,4,5,6,7]
    comment_form = form.CommentForm(request.form)
    if request.method == 'POST' and comment_form.validate(): #formulario correcto
        #imprimo datos formulario
        print(comment_form.username.data)
        print(comment_form.idPaciente.data)
        #creo sesion
        session['idPaciente'] = comment_form.idPaciente.data

    else:
        print("Error en el formulario.")

    cookie= request.cookies.get('galletita')
    print(cookie)

    return render_template('index.html', nombre=nombre, num=num, lista=lista, form=comment_form)



@app.route('/acceso', methods=['POST'])
def acceso():
    #return "<h1> Contacto <h1>"#Antes de crear contacto.html

    idPaciente = request.form.get("idPaciente")
    return render_template('acceso.html', idPaciente=idPaciente)


@app.route('/cookie')
def cookie():
    response = make_response(render_template('cookie.html'))
    response.set_cookie('galletita', 'Cookie de Sandra')
    return response



if __name__=='__main__':
    app.run(debug=True) #Ejecutar