# P:\sofemci\sofemci\sofemci\admin.py
# ADMINISTRATION DJANGO POUR SOFEM-CI

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.contrib import messages
from datetime import datetime
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
# ADMINISTRATION PRODUCTION AVEC EXPORTS
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
    
    # ACTIONS - DOIT ÊTRE UNE LISTE
    actions = ['valider_production', 'invalider_production', 
               'export_pdf_action', 'export_excel_action']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    # Action 1: Valider
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    # Action 2: Invalider
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    # Action 3: Export PDF
    def export_pdf_action(self, request, queryset):
        """Export PDF de la production extrusion"""
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        import io
        
        # Créer un buffer pour le PDF
        buffer = io.BytesIO()
        
        # Créer le PDF
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Titre
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "RAPPORT PRODUCTION EXTRUSION - SOFEM-CI")
        
        # Informations
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"Date d'export: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        p.drawString(50, height - 100, f"Nombre d'enregistrements: {queryset.count()}")
        
        # En-têtes du tableau
        p.setFont("Helvetica-Bold", 10)
        headers = ['Date', 'Zone', 'Équipe', 'Matière (kg)', 'Production (kg)', 'Rendement %', 'Déchets (kg)', 'Statut']
        x_positions = [50, 120, 200, 280, 360, 440, 520, 600]
        
        y = height - 130
        for i, header in enumerate(headers):
            p.drawString(x_positions[i], y, header)
        
        # Ligne de séparation
        p.line(50, y - 5, width - 50, y - 5)
        
        # Données
        p.setFont("Helvetica", 9)
        y -= 25
        
        for obj in queryset:
            if y < 100:  # Nouvelle page si nécessaire
                p.showPage()
                y = height - 50
                p.setFont("Helvetica-Bold", 10)
                p.drawString(50, y, "RAPPORT PRODUCTION EXTRUSION - Suite")
                y -= 80
            
            # Données formatées
            data = [
                obj.date_production.strftime('%d/%m/%Y'),
                str(obj.zone)[:15],  # Limiter la taille
                str(obj.equipe)[:10],
                f"{obj.matiere_premiere_kg:.2f}",
                f"{obj.total_production_kg:.2f}" if obj.total_production_kg else "0.00",
                f"{obj.rendement_pourcentage:.2f}%" if obj.rendement_pourcentage else "0.00%",
                f"{obj.dechets_kg:.2f}",
                "✓ Validé" if obj.valide else "✗ En attente"
            ]
            
            for i, value in enumerate(data):
                p.drawString(x_positions[i], y, str(value))
            
            y -= 20
        
        # Pied de page
        p.setFont("Helvetica-Oblique", 8)
        p.drawString(50, 30, f"Généré automatiquement par le système SOFEM-CI - Page 1")
        
        p.save()
        buffer.seek(0)
        
        # Retourner le PDF
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="production_extrusion_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"'
        return response
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    # Action 4: Export Excel
    def export_excel_action(self, request, queryset):
        """Export Excel de la production extrusion"""
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        from django.http import HttpResponse
        import io
        
        # Créer un workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Production Extrusion"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # En-têtes
        headers = ['Date', 'Zone', 'Équipe', 'Heure Début', 'Heure Fin', 
                  'Chef Zone', 'Matière (kg)', 'Machines', 'Machinistes',
                  'Bobines (kg)', 'Finis (kg)', 'Semi-Finis (kg)', 'Déchets (kg)',
                  'Total Prod (kg)', 'Rendement %', 'Taux Déchet %', 
                  'Prod/Machine', 'Observations', 'Statut']
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
        
        # Données
        for row_num, obj in enumerate(queryset, 2):
            ws.cell(row=row_num, column=1, value=obj.date_production)
            ws.cell(row=row_num, column=2, value=str(obj.zone))
            ws.cell(row=row_num, column=3, value=str(obj.equipe))
            ws.cell(row=row_num, column=4, value=obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '')
            ws.cell(row=row_num, column=5, value=obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '')
            ws.cell(row=row_num, column=6, value=obj.chef_zone)
            ws.cell(row=row_num, column=7, value=float(obj.matiere_premiere_kg))
            ws.cell(row=row_num, column=8, value=obj.nombre_machines_actives)
            ws.cell(row=row_num, column=9, value=obj.nombre_machinistes)
            ws.cell(row=row_num, column=10, value=float(obj.nombre_bobines_kg))
            ws.cell(row=row_num, column=11, value=float(obj.production_finis_kg))
            ws.cell(row=row_num, column=12, value=float(obj.production_semi_finis_kg))
            ws.cell(row=row_num, column=13, value=float(obj.dechets_kg))
            ws.cell(row=row_num, column=14, value=float(obj.total_production_kg) if obj.total_production_kg else 0)
            ws.cell(row=row_num, column=15, value=float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0)
            ws.cell(row=row_num, column=16, value=float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0)
            ws.cell(row=row_num, column=17, value=float(obj.production_par_machine) if obj.production_par_machine else 0)
            ws.cell(row=row_num, column=18, value=obj.observations[:100] if obj.observations else '')
            ws.cell(row=row_num, column=19, value="Validé" if obj.valide else "En attente")
        
        # Formater les colonnes numériques
        for col in ['G', 'J', 'K', 'L', 'M', 'N']:  # Colonnes avec valeurs numériques
            for row in range(2, len(queryset) + 2):
                cell = ws[f'{col}{row}']
                cell.number_format = '#,##0.00'
        
        for col in ['O', 'P']:  # Pourcentages
            for row in range(2, len(queryset) + 2):
                cell = ws[f'{col}{row}']
                cell.number_format = '0.00%'
        
        # Ajuster la largeur des colonnes
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    cell_value = str(cell.value) if cell.value else ''
                    if len(cell_value) > max_length:
                        max_length = len(cell_value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Sauvegarder dans le buffer
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        # Retourner le fichier Excel
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="production_extrusion_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"'
        return response
    export_excel_action.short_description = "📊 Exporter en Excel"

@admin.register(ProductionImprimerie)
class ProductionImprimerieAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'total_production_kg', 'taux_dechet_pourcentage', 
                   'valide', 'cree_par']
    list_filter = ['date_production', 'valide']
    readonly_fields = ['total_production_kg', 'taux_dechet_pourcentage', 
                      'date_creation', 'date_modification']
    ordering = ['-date_production']
    
    # ACTIONS
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
        from django.http import HttpResponse
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.pdfgen import canvas
        import io
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        # Titre
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, "RAPPORT PRODUCTION IMPRIMERIE - SOFEM-CI")
        
        # Données
        p.setFont("Helvetica", 10)
        y = height - 100
        
        for obj in queryset:
            if y < 100:
                p.showPage()
                y = height - 50
            
            p.drawString(50, y, f"Date: {obj.date_production.strftime('%d/%m/%Y')}")
            p.drawString(200, y, f"Production: {obj.total_production_kg:.2f} kg")
            p.drawString(350, y, f"Déchets: {obj.dechets_kg:.2f} kg")
            p.drawString(500, y, f"Statut: {'Validé' if obj.valide else 'En attente'}")
            
            y -= 25
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="production_imprimerie_{datetime.now().strftime('%Y%m%d')}.pdf"'
        return response
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        """Export Excel de la production imprimerie"""
        import openpyxl
        from django.http import HttpResponse
        import io
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Production Imprimerie"
        
        # En-têtes
        headers = ['Date', 'Heure Début', 'Heure Fin', 'Machines Actives',
                  'Bobines Finies (kg)', 'Bobines Semi-Finies (kg)', 
                  'Déchets (kg)', 'Total Production (kg)', 'Taux Déchet %', 
                  'Observations', 'Statut']
        
        for col_num, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_num, value=header)
        
        # Données
        for row_num, obj in enumerate(queryset, 2):
            ws.cell(row=row_num, column=1, value=obj.date_production)
            ws.cell(row=row_num, column=2, value=obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '')
            ws.cell(row=row_num, column=3, value=obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '')
            ws.cell(row=row_num, column=4, value=obj.nombre_machines_actives)
            ws.cell(row=row_num, column=5, value=float(obj.production_bobines_finies_kg))
            ws.cell(row=row_num, column=6, value=float(obj.production_bobines_semi_finies_kg))
            ws.cell(row=row_num, column=7, value=float(obj.dechets_kg))
            ws.cell(row=row_num, column=8, value=float(obj.total_production_kg) if obj.total_production_kg else 0)
            ws.cell(row=row_num, column=9, value=float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0)
            ws.cell(row=row_num, column=10, value=obj.observations[:100] if obj.observations else '')
            ws.cell(row=row_num, column=11, value="Validé" if obj.valide else "En attente")
        
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="production_imprimerie_{datetime.now().strftime('%Y%m%d')}.xlsx"'
        return response
    export_excel_action.short_description = "📊 Exporter en Excel"

@admin.register(ProductionSoudure)
class ProductionSoudureAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'total_production_kg', 'total_production_specifique_kg',
                   'valide', 'cree_par']
    list_filter = ['date_production', 'valide']
    readonly_fields = ['total_production_kg', 'total_production_specifique_kg', 
                      'taux_dechet_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']
    
    # ACTIONS
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
        from django.http import HttpResponse
        response = HttpResponse("Export PDF Soudure", content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="soudure.txt"'
        self.message_user(request, "Export PDF test pour soudure")
        return response
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        from django.http import HttpResponse
        response = HttpResponse("Export Excel Soudure", content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="soudure.csv"'
        self.message_user(request, "Export Excel test pour soudure")
        return response
    export_excel_action.short_description = "📊 Exporter en Excel"

@admin.register(ProductionRecyclage)
class ProductionRecyclageAdmin(admin.ModelAdmin):
    list_display = ['date_production', 'equipe', 'total_production_kg', 
                   'production_par_moulinex', 'valide', 'cree_par']
    list_filter = ['date_production', 'equipe', 'valide']
    readonly_fields = ['total_production_kg', 'production_par_moulinex', 
                      'taux_transformation_pourcentage', 'date_creation', 'date_modification']
    ordering = ['-date_production']
    
    # ACTIONS
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
        from django.http import HttpResponse
        response = HttpResponse("Export PDF Recyclage", content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="recyclage.txt"'
        self.message_user(request, "Export PDF test pour recyclage")
        return response
    export_pdf_action.short_description = "📄 Exporter en PDF"
    
    def export_excel_action(self, request, queryset):
        from django.http import HttpResponse
        response = HttpResponse("Export Excel Recyclage", content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="recyclage.csv"'
        self.message_user(request, "Export Excel test pour recyclage")
        return response
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