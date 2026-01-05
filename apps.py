# sofemci/apps.py
from django.apps import AppConfig

class SofemciConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'sofemci'
    
    def ready(self):
        # Importez les signaux ici si vous en avez
        pass