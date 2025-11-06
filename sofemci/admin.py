# sofemci/admin.py
# ADMINISTRATION DJANGO POUR SOFEM-CI

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models.users import CustomUser
from .models.base import Equipe, ZoneExtrusion
from .models.machines import Machine, HistoriqueMachine
from .models.production import ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage
from .models.alerts import Alerte, AlerteIA

# ==========================================
# ADMINISTRATION UTILISATEURS
# ==========================================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'role', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'date_joined']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering = ['username']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations SOFEM-CI', {
            'fields': ('role', 'telephone', 'date_embauche')
        }),
    )

# ==========================================
# ADMINISTRATION RAPPORTS
# ==========================================


# ==========================================
# ADMINISTRATION CONFIGURATION
# ==========================================

@admin.register(Equipe)
class EquipeAdmin(admin.ModelAdmin):
    list_display = ['nom', 'heure_debut', 'heure_fin', 'chef_equipe']
    list_filter = ['nom']

@admin.register(ZoneExtrusion)
class ZoneExtrusionAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nom', 'nombre_machines_max', 'chef_zone', 'active']
    list_filter = ['active', 'chef_zone']
    ordering = ['numero']

@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = [
        'numero', 
        'type_machine', 
        'section', 
        'provenance',  # Nouveau champ
        'est_nouvelle',  # Nouveau champ
        'etat', 
        'score_sante_global',
        'probabilite_panne_7_jours',
        'derniere_maintenance'
    ]
    
    list_filter = [
        'section', 
        'type_machine', 
        'etat', 
        'provenance',  # Nouveau filtre
        'est_nouvelle',  # Nouveau filtre
        'anomalie_detectee'
    ]
    
    search_fields = ['numero', 'observations']
    
    fieldsets = (
        ('Informations de base', {
            'fields': (
                'numero', 
                'type_machine', 
                'section', 
                'zone_extrusion',
                'provenance',  # Nouveau champ
                'est_nouvelle',  # Nouveau champ
                'etat',
                'date_installation',
                'capacite_horaire',
                'observations'
            )
        }),
        ('Maintenance', {
            'fields': (
                'derniere_maintenance',
                'prochaine_maintenance_prevue',
                'frequence_maintenance_jours',
                'heures_fonctionnement_totales',
                'heures_depuis_derniere_maintenance'
            )
        }),
        ('Historique pannes', {
            'fields': (
                'nombre_pannes_totales',
                'nombre_pannes_6_derniers_mois',
                'nombre_pannes_1_dernier_mois',
                'date_derniere_panne',
                'duree_moyenne_reparation'
            )
        }),
        ('Consommation et Température', {
            'fields': (
                'consommation_electrique_kwh',
                'consommation_electrique_nominale',
                'temperature_actuelle',
                'temperature_nominale',
                'temperature_max_autorisee'
            )
        }),
        ('Analyses IA', {
            'fields': (
                'score_sante_global',
                'probabilite_panne_7_jours',
                'probabilite_panne_30_jours',
                'anomalie_detectee',
                'type_anomalie',
                'date_derniere_analyse_ia'
            )
        }),
    )
    
    readonly_fields = ['derniere_mise_a_jour_donnees']
    

# ==========================================
# ADMINISTRATION PRODUCTION
# ==========================================

@admin.register(ProductionExtrusion)
class ProductionExtrusionAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'zone', 'equipe', 'total_production_kg', 'rendement_pourcentage', 'valide', 'cree_par']
    list_filter = ['date_production', 'zone', 'equipe', 'valide']
    search_fields = ['chef_zone']
    readonly_fields = ['total_production_kg', 'rendement_pourcentage', 'taux_dechet_pourcentage', 'production_par_machine', 'date_creation', 'date_modification']
    ordering = ['-date_production']

@admin.register(ProductionImprimerie)
class ProductionImprimerieAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'total_production_kg', 'taux_dechet_pourcentage', 'valide', 'cree_par']
    list_filter = ['date_production', 'valide']
    readonly_fields = ['total_production_kg', 'taux_dechet_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']

@admin.register(ProductionSoudure)
class ProductionSoudureAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'total_production_kg', 'total_production_specifique_kg', 'valide', 'cree_par']
    list_filter = ['date_production', 'valide']
    readonly_fields = ['total_production_kg', 'total_production_specifique_kg', 'taux_dechet_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']

@admin.register(ProductionRecyclage)
class ProductionRecyclageAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'equipe', 'total_production_kg', 'production_par_moulinex', 'valide', 'cree_par']
    list_filter = ['date_production', 'equipe', 'valide']
    readonly_fields = ['total_production_kg', 'production_par_moulinex', 'taux_transformation_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']

# ==========================================
# ADMINISTRATION SYSTÈME
# ==========================================

@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    list_display = ['titre', 'type_alerte', 'statut', 'section', 'cree_par', 'assigne_a', 'date_creation', 'date_resolution']
    list_filter = ['type_alerte', 'statut', 'section', 'cree_par', 'assigne_a']
    search_fields = ['titre', 'message', 'section']
    ordering = ['-date_creation']
    date_hierarchy = 'date_creation'
    readonly_fields = ['date_creation']

@admin.register(AlerteIA)
class AlerteIAAdmin(admin.ModelAdmin):
    list_display = ['machine', 'titre', 'niveau', 'statut', 'probabilite_panne', 'date_creation']
    list_filter = ['niveau', 'statut', 'date_creation']
    search_fields = ['machine__numero', 'titre']  

@admin.register(HistoriqueMachine)
class HistoriqueMachineAdmin(admin.ModelAdmin):
    list_display = ['machine', 'type_evenement', 'date_evenement', 'technicien']
    list_filter = ['type_evenement', 'date_evenement']
    search_fields = ['machine__numero', 'description']

