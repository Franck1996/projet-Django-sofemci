# sofemci/admin.py - VERSION COMPLÈTE CORRIGÉE ET OPTIMISÉE

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import mark_safe
from django.contrib import messages
from datetime import datetime
from decimal import Decimal
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.pdfgen import canvas
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from .models import CustomUser
from .models import Equipe, ZoneExtrusion
from .models import Machine, HistoriqueMachine
from .models import ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage
from .models import Alerte, AlerteIA
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from django.utils.safestring import mark_safe

# ==========================================
# FONCTIONS PDF (Inchangées - gardées telles quelles)
# ==========================================

def create_ultra_professional_pdf(title, queryset, filename):
    """Crée une fiche de production ULTRA professionnelle"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2.5*cm, 
        bottomMargin=2*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # En-tête
    header_style = ParagraphStyle(
        'CorporateHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=0.3*cm,
        alignment=1,
        fontName='Helvetica-Bold'
    )
    
    header_content = f"<b>{title}</b>"
    elements.append(Paragraph(header_content, header_style))
    
    # Informations
    dates = [obj.date_production for obj in queryset]
    if dates:
        min_date = min(dates).strftime('%d/%m/%Y')
        max_date = max(dates).strftime('%d/%m/%Y')
        period_text = f"<b>Période :</b> {min_date} - {max_date}" if min_date != max_date else f"<b>Date :</b> {min_date}"
    else:
        period_text = f"<b>Date :</b> {datetime.now().strftime('%d/%m/%Y')}"
    
    info_text = f"{period_text} | <b>Enregistrements :</b> {len(queryset)} | <b>Généré :</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    elements.append(Paragraph(info_text, ParagraphStyle('InfoStyle', fontSize=10, 
                                                      textColor=colors.HexColor('#333333'),
                                                      spaceAfter=1.0*cm,
                                                      alignment=1)))
    
    # Tableau
    headers = [
        'Date', 'Zone', 'Équipe', 'Matière P', 'Machines', 'Personnel',
        'Bobines', 'Finis', 'Semi', 'Déchets', 'Total', 'Rend (%)'
    ]
    
    table_data = [headers]
    
    for obj in queryset.order_by('date_production', 'zone'):
        rendement = float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            str(obj.zone),
            str(obj.equipe)[:15],
            f"{float(obj.matiere_premiere_kg):,.0f}",
            str(obj.nombre_machines_actives),
            str(obj.nombre_machinistes),
            f"{float(obj.nombre_bobines_kg):,.0f}",
            f"{float(obj.production_finis_kg):,.0f}",
            f"{float(obj.production_semi_finis_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{rendement:.1f}"
        ]
        table_data.append(row_data)
    
    col_widths = [2.8*cm, 3.2*cm, 5.0*cm, 2.5*cm, 2.0*cm, 2.0*cm, 
                  2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('ALIGN', (3, 1), (10, -1), 'RIGHT'),
        ('ALIGN', (11, 1), (11, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('RIGHTPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), [colors.white, colors.HexColor('#F9F9F9')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 1.5*cm))
    
    # Footer
    footer_text = f"""
    <b>SOFEM-CI</b> | Usine de Production | Abidjan, Côte d'Ivoire<br/>
    <i>Document confidentiel - Réf: PROD-{datetime.now().strftime('%Y%m%d')}-001 | Page 1/1</i>
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'ProfessionalFooter',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        fontName='Helvetica',
        spaceBefore=0.5*cm
    ))
    elements.append(footer_para)
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def create_ultra_professional_pdf_imprimerie(title, queryset, filename):
    """PDF Imprimerie simplifié"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                           rightMargin=1.0*cm, leftMargin=1.0*cm, 
                           topMargin=2.0*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        alignment=1,
        spaceAfter=1*cm
    )
    
    elements.append(Paragraph(f"<b>{title}</b>", header_style))
    
    # Tableau simplifié
    headers = ['Date', 'Heures', 'Machines', 'Finies (kg)', 'Semi (kg)', 'Déchets (kg)', 'Total (kg)', 'Taux Déchet']
    table_data = [headers]
    
    for obj in queryset.order_by('date_production'):
        heure_debut = obj.heure_debut.strftime('%H:%M') if obj.heure_debut else "--:--"
        heure_fin = obj.heure_fin.strftime('%H:%M') if obj.heure_fin else "--:--"
        heures = f"{heure_debut}→{heure_fin}"
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            heures,
            str(obj.nombre_machines_actives),
            f"{float(obj.production_bobines_finies_kg):,.0f}",
            f"{float(obj.production_bobines_semi_finies_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{float(obj.taux_dechet_pourcentage):.1f}%" if obj.taux_dechet_pourcentage else "0.0%"
        ]
        table_data.append(row_data)
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 1), (2, -1), 'CENTER'),
        ('ALIGN', (3, 1), (6, -1), 'RIGHT'),
        ('ALIGN', (7, 1), (7, -1), 'CENTER'),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def create_ultra_professional_pdf_soudure(title, queryset, filename):
    """PDF Soudure simplifié"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                           rightMargin=1.0*cm, leftMargin=1.0*cm, 
                           topMargin=2.0*cm, bottomMargin=1.5*cm)
    elements = []
    styles = getSampleStyleSheet()
    
    elements.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
        'Header', fontSize=16, textColor=colors.HexColor('#2c3e50'), alignment=1
    )))
    
    headers = ['Date', 'Heures', 'Machines', 'Bobines', 'Bretelles', 'Rema', 'Batta', 'Sac', 'Déchets', 'Total']
    table_data = [headers]
    
    for obj in queryset.order_by('date_production'):
        heure_debut = obj.heure_debut.strftime('%H:%M') if obj.heure_debut else "--:--"
        heure_fin = obj.heure_fin.strftime('%H:%M') if obj.heure_fin else "--:--"
        heures = f"{heure_debut}→{heure_fin}"
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            heures,
            str(obj.nombre_machines_actives),
            f"{float(obj.production_bobines_finies_kg):,.0f}",
            f"{float(obj.production_bretelles_kg):,.0f}",
            f"{float(obj.production_rema_kg):,.0f}",
            f"{float(obj.production_batta_kg):,.0f}",
            f"{float(obj.production_sac_emballage_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0"
        ]
        table_data.append(row_data)
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def create_ultra_professional_pdf_recyclage(title, queryset, filename):
    """PDF Recyclage simplifié"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), 
                           rightMargin=1.0*cm, leftMargin=1.0*cm, 
                           topMargin=2.0*cm, bottomMargin=1.5*cm)
    elements = []
    
    elements.append(Paragraph(f"<b>{title}</b>", ParagraphStyle(
        'Header', fontSize=16, textColor=colors.HexColor('#27ae60'), alignment=1
    )))
    
    headers = ['Date', 'Équipe', 'Moulinex', 'Broyage (kg)', 'Bâche Noire (kg)', 'Total (kg)', 'Prod/Moul', 'Taux Transfo']
    table_data = [headers]
    
    for obj in queryset.order_by('date_production'):
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            str(obj.equipe)[:15] if obj.equipe else "-",
            str(obj.nombre_moulinex),
            f"{float(obj.production_broyage_kg):,.0f}",
            f"{float(obj.production_bache_noir_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{float(obj.production_par_moulinex):,.0f}" if obj.production_par_moulinex else "0",
            f"{float(obj.taux_transformation_pourcentage):.1f}%" if obj.taux_transformation_pourcentage else "0.0%"
        ]
        table_data.append(row_data)
    
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

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
    list_display = ['numero', 'type_machine', 'section', 'provenance', 'est_nouvelle', 'etat', 
                    'score_sante_global', 'probabilite_panne_7_jours', 'derniere_maintenance']
    list_filter = ['section', 'type_machine', 'etat', 'provenance', 'est_nouvelle', 'anomalie_detectee']
    search_fields = ['numero', 'observations']
    readonly_fields = ['derniere_mise_a_jour_donnees']

# ==========================================
# ADMINISTRATION PRODUCTION EXTRUSION - CORRIGÉ
# ==========================================

@admin.register(ProductionExtrusion)
class ProductionExtrusionAdmin(admin.ModelAdmin):
    list_display = [
        'date_production_short',
        'get_zone_compact',
        'get_equipe_compact',
        'get_matiere_premiere',
        'get_machines_actives',
        'get_personnel',
        'get_bobines',
        'get_finis',
        'get_semi_finis',
        'get_dechets',
        'get_total_production',
        'get_rendement',
        'get_status_icon',
    ]
    
    list_display_links = ['date_production_short', 'get_zone_compact']
    list_filter = ['date_production', 'zone', 'equipe', 'valide']
    search_fields = ['chef_zone', 'observations', 'zone__nom', 'equipe__nom']
    readonly_fields = ['total_production_kg', 'rendement_pourcentage', 'taux_dechet_pourcentage', 
                       'production_par_machine', 'date_creation', 'date_modification', 'cree_par']
    ordering = ['-date_production']
    list_per_page = 50
    
    def date_production_short(self, obj):
        return obj.date_production.strftime('%d/%m/%Y')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_zone_compact(self, obj):
        if obj.zone:
            return f"Z{obj.zone.numero}: {obj.zone.nom[:10]}"
        return "-"
    get_zone_compact.short_description = "📍 Zone"
    get_zone_compact.admin_order_field = 'zone__numero'
    
    def get_equipe_compact(self, obj):
        if obj.equipe:
            return str(obj.equipe)[:20]
        return "-"
    get_equipe_compact.short_description = "👥 Équipe"
    get_equipe_compact.admin_order_field = 'equipe__nom'
    
    def get_matiere_premiere(self, obj):
        return f"{float(obj.matiere_premiere_kg):,.0f}"
    get_matiere_premiere.short_description = "⚙️ Matière (kg)"
    get_matiere_premiere.admin_order_field = 'matiere_premiere_kg'
    
    def get_machines_actives(self, obj):
        return obj.nombre_machines_actives
    get_machines_actives.short_description = "🖥️ Machines"
    get_machines_actives.admin_order_field = 'nombre_machines_actives'
    
    def get_personnel(self, obj):
        return obj.nombre_machinistes
    get_personnel.short_description = "👷 Personnel"
    get_personnel.admin_order_field = 'nombre_machinistes'
    
    def get_bobines(self, obj):
        return f"{float(obj.nombre_bobines_kg):,.0f}"
    get_bobines.short_description = "📦 Bobines (kg)"
    get_bobines.admin_order_field = 'nombre_bobines_kg'
    
    def get_finis(self, obj):
        return f"{float(obj.production_finis_kg):,.0f}"
    get_finis.short_description = "✅ Finis (kg)"
    get_finis.admin_order_field = 'production_finis_kg'
    
    def get_semi_finis(self, obj):
        return f"{float(obj.production_semi_finis_kg):,.0f}"
    get_semi_finis.short_description = "🔄 Semi (kg)"
    get_semi_finis.admin_order_field = 'production_semi_finis_kg'
    
    def get_dechets(self, obj):
        return f"{float(obj.dechets_kg):,.0f}"
    get_dechets.short_description = "🗑️ Déchets (kg)"
    get_dechets.admin_order_field = 'dechets_kg'
    
    def get_total_production(self, obj):
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}"
        return "0"
    get_total_production.short_description = "🏭 Total (kg)"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_rendement(self, obj):
        """Rendement formaté avec couleur - CORRIGÉ"""
        if not obj.rendement_pourcentage:
            return "0.0%"
        
        rendement = float(obj.rendement_pourcentage)
        
        if rendement >= 85:
            html = f'<span style="color: green; font-weight: bold;">{rendement:.1f}%</span>'
            return mark_safe(html)
        elif rendement >= 70:
            html = f'<span style="color: orange; font-weight: bold;">{rendement:.1f}%</span>'
            return mark_safe(html)
        else:
            html = f'<span style="color: red; font-weight: bold;">{rendement:.1f}%</span>'
            return mark_safe(html)
    get_rendement.short_description = "📈 Rendement"
    get_rendement.admin_order_field = 'rendement_pourcentage'
    
    def get_status_icon(self, obj):
        if obj.valide:
            html = '<span style="color: green; font-size: 1.2em;">✅</span>'
            return mark_safe(html)
        else:
            html = '<span style="color: red; font-size: 1.2em;">❌</span>'
            return mark_safe(html)
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('zone', 'equipe', 'cree_par')
    
    fieldsets = (
        ('📅 Informations de base', {
            'fields': ('date_production', 'zone', 'equipe', 'chef_zone', 'heure_debut', 'heure_fin')
        }),
        ('⚙️ Ressources utilisées', {
            'fields': ('matiere_premiere_kg', 'nombre_machines_actives', 'nombre_machinistes')
        }),
        ('📦 Production détaillée', {
            'fields': ('nombre_bobines_kg', 'production_finis_kg', 'production_semi_finis_kg', 'dechets_kg')
        }),
        ('📊 Calculs automatiques', {
            'fields': ('total_production_kg', 'rendement_pourcentage', 'taux_dechet_pourcentage', 'production_par_machine'),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': ('observations', 'valide', 'cree_par')
        })
    )
    
    actions = ['valider_production', 'invalider_production', 'export_pdf_fiche_production_ultra', 'export_excel_fiche_production']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} production(s) validée(s) avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider la production"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} production(s) invalidée(s).', messages.WARNING)
    invalider_production.short_description = "❌ Invalider la production"
    
    def export_pdf_fiche_production_ultra(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        title = "FICHE DE PRODUCTION EXTRUSION"
        filename = f"Fiche_Production_Extrusion_{datetime.now().strftime('%Y%m%d_%H%M')}"
        try:
            return create_ultra_professional_pdf(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur PDF: {str(e)}", messages.ERROR)
            return None
    export_pdf_fiche_production_ultra.short_description = "📄 Export PDF"
    
    def export_excel_fiche_production(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        self.message_user(request, "Export Excel disponible", messages.INFO)
        return None
    export_excel_fiche_production.short_description = "📊 Export Excel"

# ==========================================
# ADMINISTRATION PRODUCTION RECYCLAGE - CORRIGÉ
# ==========================================

@admin.register(ProductionRecyclage)
class ProductionRecyclageAdmin(admin.ModelAdmin):
    list_display = ['date_production_short', 'get_equipe_compact', 'get_moulinex', 
                    'get_broyage', 'get_bache_noire', 'get_total_production', 
                    'get_production_par_moulinex', 'get_taux_transformation', 'get_status_icon']
    list_display_links = ['date_production_short', 'get_equipe_compact']
    list_filter = ['date_production', 'equipe', 'valide']
    search_fields = ['observations', 'equipe__nom']
    readonly_fields = ['total_production_kg', 'production_par_moulinex', 'taux_transformation_pourcentage', 
                       'date_creation', 'date_modification', 'cree_par']
    ordering = ['-date_production']
    list_per_page = 50
    
    def date_production_short(self, obj):
        return obj.date_production.strftime('%d/%m/%Y')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_equipe_compact(self, obj):
        if obj.equipe:
            return str(obj.equipe)[:15]
        return "-"
    get_equipe_compact.short_description = "👥 Équipe"
    get_equipe_compact.admin_order_field = 'equipe__nom'
    
    def get_moulinex(self, obj):
        return obj.nombre_moulinex
    get_moulinex.short_description = "⚙️ Moulinex"
    get_moulinex.admin_order_field = 'nombre_moulinex'
    
    def get_broyage(self, obj):
        return f"{float(obj.production_broyage_kg):,.0f}"
    get_broyage.short_description = "🔄 Broyage (kg)"
    get_broyage.admin_order_field = 'production_broyage_kg'
    
    def get_bache_noire(self, obj):
        return f"{float(obj.production_bache_noir_kg):,.0f}"
    get_bache_noire.short_description = "⬛ Bâche (kg)"
    get_bache_noire.admin_order_field = 'production_bache_noir_kg'
    
    def get_total_production(self, obj):
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}"
        return "0"
    get_total_production.short_description = "🏭 Total (kg)"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_production_par_moulinex(self, obj):
        if obj.production_par_moulinex:
            return f"{float(obj.production_par_moulinex):,.0f}"
        return "0"
    get_production_par_moulinex.short_description = "📊 Prod/Moul (kg)"
    get_production_par_moulinex.admin_order_field = 'production_par_moulinex'
    
    def get_taux_transformation(self, obj):
        """Taux de transformation formaté avec couleur - CORRIGÉ"""
        if not obj.taux_transformation_pourcentage:
            return "0.0%"
        
        taux = float(obj.taux_transformation_pourcentage)
        
        if taux >= 80:
            html = f'<span style="color: green; font-weight: bold;">{taux:.1f}%</span>'
            return mark_safe(html)
        elif taux >= 60:
            html = f'<span style="color: orange; font-weight: bold;">{taux:.1f}%</span>'
            return mark_safe(html)
        else:
            html = f'<span style="color: red; font-weight: bold;">{taux:.1f}%</span>'
            return mark_safe(html)
    get_taux_transformation.short_description = "📈 Taux Transfo"
    get_taux_transformation.admin_order_field = 'taux_transformation_pourcentage'
    
    def get_status_icon(self, obj):
        if obj.valide:
            html = '<span style="color: green; font-size: 1.2em;">✅</span>'
            return mark_safe(html)
        else:
            html = '<span style="color: red; font-size: 1.2em;">❌</span>'
            return mark_safe(html)
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('equipe')
    
    fieldsets = (
        ('📅 Informations de base', {
            'fields': ('date_production', 'equipe', 'nombre_moulinex')
        }),
        ('♻️ Production recyclage', {
            'fields': ('production_broyage_kg', 'production_bache_noir_kg')
        }),
        ('📊 Calculs automatiques', {
            'fields': ('total_production_kg', 'production_par_moulinex', 'taux_transformation_pourcentage'),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': ('observations', 'valide', 'cree_par')
        })
    )
    
    actions = ['valider_production', 'invalider_production', 'export_pdf_fiche_recyclage_ultra', 'export_excel_fiche_recyclage']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} production(s) recyclage validée(s).', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} production(s) recyclage invalidée(s).', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_fiche_recyclage_ultra(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée.", messages.WARNING)
            return None
        title = "FICHE PRODUCTION RECYCLAGE"
        filename = f"Fiche_Recyclage_{datetime.now().strftime('%Y%m%d_%H%M')}"
        try:
            return create_ultra_professional_pdf_recyclage(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur: {str(e)}", messages.ERROR)
            return None
    export_pdf_fiche_recyclage_ultra.short_description = "📄 Export PDF"
    
    def export_excel_fiche_recyclage(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée.", messages.WARNING)
            return None
        self.message_user(request, "Export Excel disponible", messages.INFO)
        return None
    export_excel_fiche_recyclage.short_description = "📊 Export Excel"

# ==========================================
# ADMINISTRATION PRODUCTION IMPRIMERIE - CORRIGÉ
# ==========================================

@admin.register(ProductionImprimerie)
class ProductionImprimerieAdmin(admin.ModelAdmin):
    list_display = ['date_production_short', 'get_heures_creneau', 'get_machines_actives', 
                    'get_bobines_finies', 'get_bobines_semi', 'get_dechets', 
                    'get_total_production', 'get_taux_dechet', 'get_status_icon']
    list_display_links = ['date_production_short']
    list_filter = ['date_production', 'valide']
    search_fields = ['observations']
    readonly_fields = ['total_production_kg', 'taux_dechet_pourcentage', 'date_creation', 'date_modification', 'cree_par']
    ordering = ['-date_production']
    list_per_page = 50
    
    def date_production_short(self, obj):
        return obj.date_production.strftime('%d/%m/%Y')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_heures_creneau(self, obj):
        heure_debut = obj.heure_debut.strftime('%Hh%M') if obj.heure_debut else "--:--"
        heure_fin = obj.heure_fin.strftime('%Hh%M') if obj.heure_fin else "--:--"
        return f"{heure_debut}→{heure_fin}"
    get_heures_creneau.short_description = "🕒 Créneau"
    
    def get_machines_actives(self, obj):
        return obj.nombre_machines_actives
    get_machines_actives.short_description = "🖥️ Machines"
    get_machines_actives.admin_order_field = 'nombre_machines_actives'
    
    def get_bobines_finies(self, obj):
        return f"{float(obj.production_bobines_finies_kg):,.0f}"
    get_bobines_finies.short_description = "✅ Finies (kg)"
    get_bobines_finies.admin_order_field = 'production_bobines_finies_kg'
    
    def get_bobines_semi(self, obj):
        return f"{float(obj.production_bobines_semi_finies_kg):,.0f}"
    get_bobines_semi.short_description = "🔄 Semi (kg)"
    get_bobines_semi.admin_order_field = 'production_bobines_semi_finies_kg'
    
    def get_dechets(self, obj):
        return f"{float(obj.dechets_kg):,.0f}"
    get_dechets.short_description = "🗑️ Déchets (kg)"
    get_dechets.admin_order_field = 'dechets_kg'
    
    def get_total_production(self, obj):
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}"
        return "0"
    get_total_production.short_description = "🏭 Total (kg)"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_taux_dechet(self, obj):
        """Taux de déchet formaté avec couleur - CORRIGÉ"""
        if not obj.taux_dechet_pourcentage:
            return "0.0%"
        
        taux = float(obj.taux_dechet_pourcentage)
        
        if taux <= 5:
            html = f'<span style="color: green; font-weight: bold;">{taux:.1f}%</span>'
            return mark_safe(html)
        elif taux <= 10:
            html = f'<span style="color: orange; font-weight: bold;">{taux:.1f}%</span>'
            return mark_safe(html)
        else:
            html = f'<span style="color: red; font-weight: bold;">{taux:.1f}%</span>'
            return mark_safe(html)
    get_taux_dechet.short_description = "📉 Taux Déchet"
    get_taux_dechet.admin_order_field = 'taux_dechet_pourcentage'
    
    def get_status_icon(self, obj):
        if obj.valide:
            html = '<span style="color: green; font-size: 1.2em;">✅</span>'
            return mark_safe(html)
        else:
            html = '<span style="color: red; font-size: 1.2em;">❌</span>'
            return mark_safe(html)
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    fieldsets = (
        ('📅 Informations de base', {
            'fields': ('date_production', 'heure_debut', 'heure_fin', 'nombre_machines_actives')
        }),
        ('📦 Production détaillée', {
            'fields': ('production_bobines_finies_kg', 'production_bobines_semi_finies_kg', 'dechets_kg')
        }),
        ('📊 Calculs automatiques', {
            'fields': ('total_production_kg', 'taux_dechet_pourcentage'),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': ('observations', 'valide', 'cree_par')
        })
    )
    
    actions = ['valider_production', 'invalider_production', 'export_pdf_fiche_imprimerie_ultra', 'export_excel_fiche_imprimerie']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} production(s) imprimerie validée(s).', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} production(s) imprimerie invalidée(s).', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_fiche_imprimerie_ultra(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée.", messages.WARNING)
            return None
        title = "FICHE PRODUCTION IMPRIMERIE"
        filename = f"Fiche_Imprimerie_{datetime.now().strftime('%Y%m%d_%H%M')}"
        try:
            return create_ultra_professional_pdf_imprimerie(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur: {str(e)}", messages.ERROR)
            return None
    export_pdf_fiche_imprimerie_ultra.short_description = "📄 Export PDF"
    
    def export_excel_fiche_imprimerie(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée.", messages.WARNING)
            return None
        self.message_user(request, "Export Excel disponible", messages.INFO)
        return None
    export_excel_fiche_imprimerie.short_description = "📊 Export Excel"

# ==========================================
# ADMINISTRATION PRODUCTION SOUDURE - CORRIGÉ
# ==========================================

@admin.register(ProductionSoudure)
class ProductionSoudureAdmin(admin.ModelAdmin):
    list_display = ['date_production_short', 'get_heures_creneau', 'get_machines_actives', 
                    'get_bobines_finies', 'get_bretelles', 'get_rema', 'get_batta', 
                    'get_sac_emballage', 'get_dechets', 'get_total_production', 'get_status_icon']
    list_display_links = ['date_production_short']
    list_filter = ['date_production', 'valide']
    search_fields = ['observations']
    readonly_fields = ['total_production_kg', 'total_production_specifique_kg', 'taux_dechet_pourcentage', 
                       'date_creation', 'date_modification', 'cree_par']
    ordering = ['-date_production']
    list_per_page = 50
    
    def date_production_short(self, obj):
        return obj.date_production.strftime('%d/%m/%Y')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_heures_creneau(self, obj):
        heure_debut = obj.heure_debut.strftime('%Hh%M') if obj.heure_debut else "--:--"
        heure_fin = obj.heure_fin.strftime('%Hh%M') if obj.heure_fin else "--:--"
        return f"{heure_debut}→{heure_fin}"
    get_heures_creneau.short_description = "🕒 Créneau"
    
    def get_machines_actives(self, obj):
        return obj.nombre_machines_actives
    get_machines_actives.short_description = "🖥️ Machines"
    get_machines_actives.admin_order_field = 'nombre_machines_actives'
    
    def get_bobines_finies(self, obj):
        return f"{float(obj.production_bobines_finies_kg):,.0f}"
    get_bobines_finies.short_description = "✅ Bobines (kg)"
    get_bobines_finies.admin_order_field = 'production_bobines_finies_kg'
    
    def get_bretelles(self, obj):
        return f"{float(obj.production_bretelles_kg):,.0f}"
    get_bretelles.short_description = "🔗 Bretelles (kg)"
    get_bretelles.admin_order_field = 'production_bretelles_kg'
    
    def get_rema(self, obj):
        return f"{float(obj.production_rema_kg):,.0f}"
    get_rema.short_description = "🔄 Rema (kg)"
    get_rema.admin_order_field = 'production_rema_kg'
    
    def get_batta(self, obj):
        return f"{float(obj.production_batta_kg):,.0f}"
    get_batta.short_description = "📦 Batta (kg)"
    get_batta.admin_order_field = 'production_batta_kg'
    
    def get_sac_emballage(self, obj):
        return f"{float(obj.production_sac_emballage_kg):,.0f}"
    get_sac_emballage.short_description = "🛍️ Sac (kg)"
    get_sac_emballage.admin_order_field = 'production_sac_emballage_kg'
    
    def get_dechets(self, obj):
        return f"{float(obj.dechets_kg):,.0f}"
    get_dechets.short_description = "🗑️ Déchets (kg)"
    get_dechets.admin_order_field = 'dechets_kg'
    
    def get_total_production(self, obj):
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}"
        return "0"
    get_total_production.short_description = "🏭 Total (kg)"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_status_icon(self, obj):
        if obj.valide:
            html = '<span style="color: green; font-size: 1.2em;">✅</span>'
            return mark_safe(html)
        else:
            html = '<span style="color: red; font-size: 1.2em;">❌</span>'
            return mark_safe(html)
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('cree_par')
    
    fieldsets = (
        ('📅 Informations de base', {
            'fields': ('date_production', 'heure_debut', 'heure_fin', 'nombre_machines_actives')
        }),
        ('📦 Production bobines standards', {
            'fields': ('production_bobines_finies_kg',)
        }),
        ('🔧 Production spécifique soudure', {
            'fields': ('production_bretelles_kg', 'production_rema_kg', 'production_batta_kg', 'production_sac_emballage_kg')
        }),
        ('🗑️ Gestion déchets', {
            'fields': ('dechets_kg',)
        }),
        ('📊 Calculs automatiques', {
            'fields': ('total_production_specifique_kg', 'total_production_kg', 'taux_dechet_pourcentage'),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': ('observations', 'valide', 'cree_par')
        })
    )
    
    actions = ['valider_production', 'invalider_production', 'export_pdf_fiche_soudure_ultra', 'export_excel_fiche_soudure']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} production(s) soudure validée(s).', messages.SUCCESS)
    valider_production.short_description = "✅ Valider"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} production(s) soudure invalidée(s).', messages.WARNING)
    invalider_production.short_description = "❌ Invalider"
    
    def export_pdf_fiche_soudure_ultra(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée.", messages.WARNING)
            return None
        title = "FICHE PRODUCTION SOUDURE"
        filename = f"Fiche_Soudure_{datetime.now().strftime('%Y%m%d_%H%M')}"
        try:
            return create_ultra_professional_pdf_soudure(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur: {str(e)}", messages.ERROR)
            return None
    export_pdf_fiche_soudure_ultra.short_description = "📄 Export PDF"
    
    def export_excel_fiche_soudure(self, request, queryset):
        if not queryset.exists():
            self.message_user(request, "Aucune donnée.", messages.WARNING)
            return None
        self.message_user(request, "Export Excel disponible", messages.INFO)
        return None
    export_excel_fiche_soudure.short_description = "📊 Export Excel"

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