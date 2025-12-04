# P:\sofemci\sofemci\sofemci\admin.py
# ADMINISTRATION DJANGO POUR SOFEM-CI

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from datetime import datetime
from decimal import Decimal
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
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
        'provenance',
        'est_nouvelle',
        'etat', 
        'score_sante_global',
        'probabilite_panne_7_jours',
        'derniere_maintenance'
    ]
    
    list_filter = [
        'section', 
        'type_machine', 
        'etat', 
        'provenance',
        'est_nouvelle',
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
                'provenance',
                'est_nouvelle',
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
# FONCTIONS UTILITAIRES POUR EXPORTS
# ==========================================

def create_pdf_export(title, headers, data, filename):
    """Crée un PDF pour l'export"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(letter))
    width, height = landscape(letter)
    
    # Titre
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, title)
    
    # Date
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 80, f"Date d'export: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    p.drawString(50, height - 100, f"Nombre d'enregistrements: {len(data)}")
    
    # En-têtes
    p.setFont("Helvetica-Bold", 10)
    col_width = (width - 100) / len(headers)
    x_positions = [50 + i * col_width for i in range(len(headers))]
    
    y = height - 130
    for i, header in enumerate(headers):
        p.drawString(x_positions[i], y, header[:20])  # Limiter à 20 caractères
    
    # Ligne de séparation
    p.line(50, y - 5, width - 50, y - 5)
    
    # Données
    p.setFont("Helvetica", 9)
    y -= 25
    
    for row in data:
        if y < 100:  # Nouvelle page
            p.showPage()
            y = height - 50
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, y, f"{title} - Suite")
            y -= 80
        
        for i, value in enumerate(row):
            p.drawString(x_positions[i], y, str(value)[:20])  # Limiter à 20 caractères
        
        y -= 20
    
    # Pied de page
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 30, "Généré par SOFEM-CI - Système de gestion d'usine")
    
    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def create_excel_export(title, headers, data, filename):
    """Crée un fichier Excel pour l'export"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = title[:31]  # Limite Excel
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    # En-têtes
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    # Données
    for row_num, row_data in enumerate(data, 2):
        for col_num, cell_value in enumerate(row_data, 1):
            ws.cell(row=row_num, column=col_num, value=cell_value)
    
    # Ajuster la largeur
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    return response

# ==========================================
# ADMINISTRATION PRODUCTION EXTRUSION
# ==========================================

@admin.register(ProductionExtrusion)
class ProductionExtrusionAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'zone', 'equipe', 'total_production_kg', 
                   'rendement_pourcentage', 'valide', 'cree_par']
    list_filter = ['date_production', 'zone', 'equipe', 'valide']
    search_fields = ['chef_zone']
    readonly_fields = ['total_production_kg', 'rendement_pourcentage', 
                      'taux_dechet_pourcentage', 'production_par_machine', 
                      'date_creation', 'date_modification', 'cree_par']
    ordering = ['-date_production']
    
    # ACTIONS POUR EXTRUSION
    actions = ['valider_production', 'invalider_production', 
               'export_pdf_action', 'export_excel_action']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_action(self, request, queryset):
        """Export PDF de la production extrusion"""
        headers = ['Date', 'Zone', 'Équipe', 'Matière (kg)', 'Production (kg)', 'Rendement %', 'Déchets (kg)', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production.strftime('%d/%m/%Y'),
                str(obj.zone),
                str(obj.equipe),
                f"{obj.matiere_premiere_kg:.2f}",
                f"{obj.total_production_kg:.2f}" if obj.total_production_kg else "0.00",
                f"{obj.rendement_pourcentage:.2f}%" if obj.rendement_pourcentage else "0.00%",
                f"{obj.dechets_kg:.2f}",
                "✓ Validé" if obj.valide else "✗ En attente"
            ])
        
        title = "RAPPORT PRODUCTION EXTRUSION - SOFEM-CI"
        filename = f"production_extrusion_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_pdf_export(title, headers, data, filename)
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        """Export Excel de la production extrusion"""
        headers = ['Date', 'Zone', 'Équipe', 'Heure Début', 'Heure Fin', 
                  'Chef Zone', 'Matière (kg)', 'Machines', 'Machinistes',
                  'Bobines (kg)', 'Finis (kg)', 'Semi-Finis (kg)', 'Déchets (kg)',
                  'Total Prod (kg)', 'Rendement %', 'Taux Déchet %', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production,
                str(obj.zone),
                str(obj.equipe),
                obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '',
                obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '',
                obj.chef_zone,
                float(obj.matiere_premiere_kg),
                obj.nombre_machines_actives,
                obj.nombre_machinistes,
                float(obj.nombre_bobines_kg),
                float(obj.production_finis_kg),
                float(obj.production_semi_finis_kg),
                float(obj.dechets_kg),
                float(obj.total_production_kg) if obj.total_production_kg else 0,
                float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0,
                float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0,
                "Validé" if obj.valide else "En attente"
            ])
        
        title = "Production Extrusion"
        filename = f"production_extrusion_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_excel_export(title, headers, data, filename)
    export_excel_action.short_description = "📊 Exporter en Excel"

# ==========================================
# ADMINISTRATION PRODUCTION IMPRIMERIE
# ==========================================

@admin.register(ProductionImprimerie)
class ProductionImprimerieAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'total_production_kg', 'taux_dechet_pourcentage', 
                   'valide', 'cree_par']
    list_filter = ['date_production', 'valide']
    readonly_fields = ['total_production_kg', 'taux_dechet_pourcentage', 
                      'date_creation', 'date_modification']
    ordering = ['-date_production']
    
    # ACTIONS POUR IMPRIMERIE - MÊME STRUCTURE
    actions = ['valider_production', 'invalider_production', 
               'export_pdf_action', 'export_excel_action']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_action(self, request, queryset):
        """Export PDF de la production imprimerie"""
        headers = ['Date', 'Heure Début', 'Heure Fin', 'Machines', 
                  'Bobines Finies (kg)', 'Bobines Semi (kg)', 'Déchets (kg)', 
                  'Total Prod (kg)', 'Taux Déchet %', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production.strftime('%d/%m/%Y'),
                obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '',
                obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '',
                obj.nombre_machines_actives,
                f"{obj.production_bobines_finies_kg:.2f}",
                f"{obj.production_bobines_semi_finies_kg:.2f}",
                f"{obj.dechets_kg:.2f}",
                f"{obj.total_production_kg:.2f}" if obj.total_production_kg else "0.00",
                f"{obj.taux_dechet_pourcentage:.2f}%" if obj.taux_dechet_pourcentage else "0.00%",
                "✓ Validé" if obj.valide else "✗ En attente"
            ])
        
        title = "RAPPORT PRODUCTION IMPRIMERIE - SOFEM-CI"
        filename = f"production_imprimerie_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_pdf_export(title, headers, data, filename)
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        """Export Excel de la production imprimerie"""
        headers = ['Date', 'Heure Début', 'Heure Fin', 'Machines Actives',
                  'Bobines Finies (kg)', 'Bobines Semi-Finies (kg)', 
                  'Déchets (kg)', 'Total Production (kg)', 'Taux Déchet %', 
                  'Observations', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production,
                obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '',
                obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '',
                obj.nombre_machines_actives,
                float(obj.production_bobines_finies_kg),
                float(obj.production_bobines_semi_finies_kg),
                float(obj.dechets_kg),
                float(obj.total_production_kg) if obj.total_production_kg else 0,
                float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0,
                obj.observations[:100] if obj.observations else '',
                "Validé" if obj.valide else "En attente"
            ])
        
        title = "Production Imprimerie"
        filename = f"production_imprimerie_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_excel_export(title, headers, data, filename)
    export_excel_action.short_description = "📊 Exporter en Excel"

# ==========================================
# ADMINISTRATION PRODUCTION SOUDURE
# ==========================================

@admin.register(ProductionSoudure)
class ProductionSoudureAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'total_production_kg', 'total_production_specifique_kg',
                   'valide', 'cree_par']
    list_filter = ['date_production', 'valide']
    readonly_fields = ['total_production_kg', 'total_production_specifique_kg', 
                      'taux_dechet_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']
    
    # ACTIONS POUR SOUDURE - MÊME STRUCTURE
    actions = ['valider_production', 'invalider_production', 
               'export_pdf_action', 'export_excel_action']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_action(self, request, queryset):
        """Export PDF de la production soudure"""
        headers = ['Date', 'Heure Début', 'Heure Fin', 'Machines',
                  'Bobines Finies (kg)', 'Bretelles (kg)', 'Rema (kg)', 
                  'Batta (kg)', 'Sac Emballage (kg)', 'Déchets (kg)', 
                  'Total Prod (kg)', 'Taux Déchet %', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production.strftime('%d/%m/%Y'),
                obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '',
                obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '',
                obj.nombre_machines_actives,
                f"{obj.production_bobines_finies_kg:.2f}",
                f"{obj.production_bretelles_kg:.2f}",
                f"{obj.production_rema_kg:.2f}",
                f"{obj.production_batta_kg:.2f}",
                f"{obj.production_sac_emballage_kg:.2f}",
                f"{obj.dechets_kg:.2f}",
                f"{obj.total_production_kg:.2f}" if obj.total_production_kg else "0.00",
                f"{obj.taux_dechet_pourcentage:.2f}%" if obj.taux_dechet_pourcentage else "0.00%",
                "✓ Validé" if obj.valide else "✗ En attente"
            ])
        
        title = "RAPPORT PRODUCTION SOUDURE - SOFEM-CI"
        filename = f"production_soudure_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_pdf_export(title, headers, data, filename)
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        """Export Excel de la production soudure"""
        headers = ['Date', 'Heure Début', 'Heure Fin', 'Machines Actives',
                  'Bobines Finies (kg)', 'Bretelles (kg)', 'Rema (kg)', 
                  'Batta (kg)', 'Sac Emballage (kg)', 'Déchets (kg)',
                  'Total Production (kg)', 'Taux Déchet %', 
                  'Observations', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production,
                obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '',
                obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '',
                obj.nombre_machines_actives,
                float(obj.production_bobines_finies_kg),
                float(obj.production_bretelles_kg),
                float(obj.production_rema_kg),
                float(obj.production_batta_kg),
                float(obj.production_sac_emballage_kg),
                float(obj.dechets_kg),
                float(obj.total_production_kg) if obj.total_production_kg else 0,
                float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0,
                obj.observations[:100] if obj.observations else '',
                "Validé" if obj.valide else "En attente"
            ])
        
        title = "Production Soudure"
        filename = f"production_soudure_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_excel_export(title, headers, data, filename)
    export_excel_action.short_description = "📊 Exporter en Excel"

# ==========================================
# ADMINISTRATION PRODUCTION RECYCLAGE
# ==========================================

@admin.register(ProductionRecyclage)
class ProductionRecyclageAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'equipe', 'total_production_kg', 
                   'production_par_moulinex', 'valide', 'cree_par']
    list_filter = ['date_production', 'equipe', 'valide']
    readonly_fields = ['total_production_kg', 'production_par_moulinex', 
                      'taux_transformation_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']
    
    # ACTIONS POUR RECYCLAGE - MÊME STRUCTURE
    actions = ['valider_production', 'invalider_production', 
               'export_pdf_action', 'export_excel_action']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_action(self, request, queryset):
        """Export PDF de la production recyclage"""
        headers = ['Date', 'Équipe', 'Moulinex', 'Broyage (kg)', 
                  'Bâche Noire (kg)', 'Total Prod (kg)', 
                  'Prod/Moulinex', 'Taux Transfo %', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production.strftime('%d/%m/%Y'),
                str(obj.equipe),
                obj.nombre_moulinex,
                f"{obj.production_broyage_kg:.2f}",
                f"{obj.production_bache_noir_kg:.2f}",
                f"{obj.total_production_kg:.2f}" if obj.total_production_kg else "0.00",
                f"{obj.production_par_moulinex:.2f}" if obj.production_par_moulinex else "0.00",
                f"{obj.taux_transformation_pourcentage:.2f}%" if obj.taux_transformation_pourcentage else "0.00%",
                "✓ Validé" if obj.valide else "✗ En attente"
            ])
        
        title = "RAPPORT PRODUCTION RECYCLAGE - SOFEM-CI"
        filename = f"production_recyclage_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_pdf_export(title, headers, data, filename)
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        """Export Excel de la production recyclage"""
        headers = ['Date', 'Équipe', 'Nombre Moulinex',
                  'Broyage (kg)', 'Bâche Noire (kg)', 'Total Production (kg)',
                  'Production/Moulinex', 'Taux Transformation %', 
                  'Observations', 'Statut']
        
        data = []
        for obj in queryset:
            data.append([
                obj.date_production,
                str(obj.equipe),
                obj.nombre_moulinex,
                float(obj.production_broyage_kg),
                float(obj.production_bache_noir_kg),
                float(obj.total_production_kg) if obj.total_production_kg else 0,
                float(obj.production_par_moulinex) if obj.production_par_moulinex else 0,
                float(obj.taux_transformation_pourcentage) if obj.taux_transformation_pourcentage else 0,
                obj.observations[:100] if obj.observations else '',
                "Validé" if obj.valide else "En attente"
            ])
        
        title = "Production Recyclage"
        filename = f"production_recyclage_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        return create_excel_export(title, headers, data, filename)
    export_excel_action.short_description = "📊 Exporter en Excel"

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