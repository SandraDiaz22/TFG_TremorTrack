from wtforms import Form, validators
from wtforms import StringField, DecimalField, HiddenField


def length_honeypot(form, field):
    if len(field.data) > 0:
        raise validators.ValidationError('El campo debe estar vacío.')

class FormularioAcceso(Form):
    #Acepta strings
    username = StringField('Nombre de usuario',
                            [validators.DataRequired(message='Campo obligatorio'),
                             validators.length(min=4, message='Ingrese un username válido')
                         ])
    #Acepta numeros
    contraseña = StringField('Contraseña',
                              [validators.DataRequired(message='Campo obligatorio'),
                               validators.length(min=0,  message='Ingrese una contraseña válida')
                            ])
    
    #Campo oculto para los usurios que ayuda contra ataques
    honeypot = HiddenField('', [length_honeypot])
