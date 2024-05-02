from wtforms import Form, validators, StringField, HiddenField
from wtforms.validators import Regexp


def length_honeypot(form, field):
    if len(field.data) > 0:
        raise validators.ValidationError('El campo debe estar vacío.')

class FormularioAcceso(Form):
    #Acepta strings
    username = StringField('Nombre de usuario',
                            [validators.DataRequired(message='Campo obligatorio'),
                             validators.length(min=4, max=50, message='Ingrese un nombre de usuario válido'),
                             Regexp('^[a-zA-Z0-9_-]+$', message='El nombre de usuario tiene caracteres no permitidos.')
                         ])
    #Acepta numeros
    contraseña = StringField('Contraseña',
                              [validators.DataRequired(message='Campo obligatorio'),
                               validators.length(min=1, max=50, message='Ingrese una contraseña válida')
                            ])
    
    #Campo oculto para los usurios que ayuda contra ataques
    honeypot = HiddenField('', [length_honeypot])
