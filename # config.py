# config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'sua-chave-secreta-super-segura-aqui-123456789'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'loja.db'
    
class DevelopmentConfig(Config):
    DEBUG = True
    
class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'MUDE-ESTA-CHAVE-EM-PRODUCAO'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}