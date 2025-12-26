from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class Equipe(models.Model):
    """Équipes de travail A, B, C"""
    EQUIPES_CHOICES = [
        ('A', 'Équipe A (06h00 - 14h00)'),
        ('B', 'Équipe B (14h00 - 22h00)'),
        ('C', 'Équipe C (22h00 - 06h00)'),
    ]
    
    nom = models.CharField(max_length=1, choices=EQUIPES_CHOICES, unique=True)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    chef_equipe = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Équipe"
        verbose_name_plural = "Équipes"
    
    def __str__(self):
        return self.get_nom_display()

class ZoneExtrusion(models.Model):
    """Zones d'extrusion (1 à 5)"""
    numero = models.IntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    nom = models.CharField(max_length=50)
    nombre_machines_max = models.IntegerField(default=4)
    chef_zone = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Zone Extrusion"
        verbose_name_plural = "Zones Extrusion"
        ordering = ['numero']
    
    def __str__(self):
        return f"Zone {self.numero} - {self.nom}"