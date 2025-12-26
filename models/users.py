from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Utilisateurs avec rôles spécifiques à l'usine"""
    ROLES = [
        ('admin', 'Administrateur'),
        ('chef_extrusion', 'Chef Zone Extrusion'),
        ('chef_soudure', 'Chef Zone Soudure'),
        ('chef_imprimerie', 'Chef Zone Imprimerie'),
        ('chef_recyclage', 'Chef Zone Recyclage'),
        ('superviseur', 'Superviseur'),
        ('direction', 'Direction'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLES, default='superviseur')
    telephone = models.CharField(max_length=20, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"