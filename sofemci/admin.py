# sofemci/admin.py
# ADMINISTRATION DJANGO POUR SOFEM-CI

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
from .models import HistoriqueMachine, AlerteIA

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

@admin.register(RapportMensuel)
class RapportMensuelAdmin(admin.ModelAdmin):
    list_display = ['mois', 'total_production_kg', 'rendement_moyen', 'taux_dechet_moyen', 'genere_par', 'date_generation']
    list_filter = ['mois', 'genere_par']
    readonly_fields = ['date_generation']
    ordering = ['-mois']
    
    fieldsets = (
        ('Période', {
            'fields': ('mois',)
        }),
        ('Statistiques Globales', {
            'fields': ('total_production_kg', 'total_extrusion_kg', 'total_imprimerie_kg', 
                      'total_soudure_kg', 'total_recyclage_kg', 'total_dechets_kg')
        }),
        ('Indicateurs', {
            'fields': ('rendement_moyen', 'taux_dechet_moyen', 'nombre_jours_production')
        }),
        ('Fichiers', {
            'fields': ('fichier_pdf', 'fichier_excel')
        }),
    )

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
    list_display = ['numero', 'type_machine', 'section', 'zone_extrusion', 'etat']
    list_filter = ['section', 'etat', 'type_machine']
    search_fields = ['numero']
    ordering = ['section', 'numero']

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

