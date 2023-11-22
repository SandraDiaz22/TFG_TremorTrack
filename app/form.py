from wtforms import Form, validators
from wtforms import StringField, DecimalField, HiddenField


def length_honeypot(form, field):
    if len(field.data) > 0:
        raise validators.ValidationError('El campo debe estar vacío.')

class FormularioAcceso(Form):
    #Acepta strings
    username = StringField('Nombre',
                            [validators.DataRequired(message='Campo obligatorio'),
                             validators.length(min=4, message='Ingrese un username válido')
                         ])
    #Acepta numeros
    idPaciente = DecimalField('Identificador de paciente',
                              [validators.DataRequired(message='Campo obligatorio'),
                               validators.NumberRange(min=0, max=100, message='Ingrese un id válido')
                            ])
    
    #Campo oculto para los usurios que ayuda contra ataques
    honeypot = HiddenField('', [length_honeypot])
