from flask import Flask, render_template, request

#Inicializar aplicación
app = Flask(__name__)

@app.route('/')
def index():
    #return "Hola Mundo!" #Antes de crear index.html

    nombre = "Sandra" #Pasar variables al html
    num = 1
    lista=[1,2,3,4,5,6,7]
    return render_template('index.html', nombre=nombre, num=num, lista=lista)



@app.route('/acceso', methods=['POST'])
def acceso():
    #return "<h1> Contacto <h1>"#Antes de crear contacto.html

    idPaciente = request.form.get("idPaciente")
    return render_template('acceso.html', idPaciente=idPaciente)



if __name__=='__main__':
    app.run(debug=True) #Ejecutar