#Para separar nuestras configuraciones por entorno

import os

class Config(object):
    #Clave secreta para firmar sesiones
    SECRET_KEY = 'contraseña_super_mega_secreta'


class DevelopmentConfig(Config):
    DEBUG = True