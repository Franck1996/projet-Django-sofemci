# sofemci/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
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
from .models.base import Equipe, ZoneExtrusion
from .models.machines import Machine, HistoriqueMachine
from .models.production import ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage
from .models.alerts import Alerte, AlerteIA
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
    


# ==========================================
# FONCTION D'EXPORT PDF ULTRA PROFESSIONNELLE
# ==========================================

def create_ultra_professional_pdf(title, queryset, filename):
    """Crée une fiche de production ULTRA professionnelle OPTIMISÉE NOIR ET BLANC"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    
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
    
    # 1. EN-TÊTE CORPORATE - NOIR ET BLANC
    header_style = ParagraphStyle(
        'CorporateHeader',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.black,
        spaceAfter=0.3*cm,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    header_table = Table([[Paragraph(f"<b>{title}</b>", header_style)]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#F0F0F0')),  # Gris clair
        ('TEXTCOLOR', (0, 0), (0, 0), colors.black),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ('TOPPADDING', (0, 0), (0, 0), 10),
        ('BOX', (0, 0), (0, 0), 1.5, colors.black),  # Bordure noire
    ]))
    elements.append(header_table)
    
    # 2. INFORMATIONS DE PÉRIODE
    dates = [obj.date_production for obj in queryset]
    if dates:
        min_date = min(dates).strftime('%d/%m/%Y')
        max_date = max(dates).strftime('%d/%m/%Y')
        period_text = f"<b>Période analysée :</b> Du {min_date} au {max_date}" if min_date != max_date else f"<b>Date :</b> {min_date}"
    else:
        period_text = f"<b>Date :</b> {datetime.now().strftime('%d/%m/%Y')}"
    
    info_text = f"""
    {period_text} | <b>Nombre d'enregistrements :</b> {len(queryset)} | <b>Généré le :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
    """
    
    elements.append(Paragraph(info_text, ParagraphStyle('InfoStyle', fontSize=10, 
                                                      textColor=colors.HexColor('#333333'),
                                                      spaceAfter=0.5*cm)))
    
    # 3. SÉPARATEUR DÉCORATIF - LIGNE NOIRE
    separator = Table([['']], colWidths=[doc.width])
    separator.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 2, colors.black),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(separator)
    
    # 4. TABLEAU PRINCIPAL - DESIGN NOIR ET BLANC
    # MODIFICATION ICI : En-têtes mieux répartis et colonne Équipe élargie
    headers_row1 = [
        'INFORMATIONS DE BASE', '', '', '', '', '',
        'PRODUCTION (kg)', '', '', '', '', ''
    ]
    
    headers_row2 = [
        'Date', 'Zone', 'Équipe', 'Matière\nPremière', 'Machines\nActives', 'Personnel',
        'Bobines', 'Finis', 'Semi-Finis', 'Déchets', 'Total', 'Rendement\n(%)'
    ]
    
    # Préparer les données
    table_data = [headers_row1, headers_row2]
    
    for idx, obj in enumerate(queryset.order_by('date_production', 'zone')):
        rendement = float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0
        
        # MODIFICATION ICI : Équipe formatée pour éviter débordement
        equipe_nom = str(obj.equipe)
        # Limiter la longueur si nécessaire
        if len(equipe_nom) > 15:
            equipe_nom = equipe_nom[:12] + "..."
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            str(obj.zone),
            equipe_nom,  # <-- Utiliser le nom formaté
            f"{float(obj.matiere_premiere_kg):,.0f}",
            str(obj.nombre_machines_actives),
            str(obj.nombre_machinistes),
            f"{float(obj.nombre_bobines_kg):,.0f}",
            f"{float(obj.production_finis_kg):,.0f}",
            f"{float(obj.production_semi_finis_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{rendement:.1f}%"
        ]
        table_data.append(row_data)
    
    # MODIFICATION IMPORTANTE ICI : Colonne Équipe élargie (4.0cm au lieu de 3.5cm)
    col_widths = [2.5*cm, 3.0*cm, 4.0*cm, 2.2*cm, 1.8*cm, 1.8*cm, 
                  2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    # STYLE NOIR ET BLANC PROFESSIONNEL
    table.setStyle(TableStyle([
        # Fusion des en-têtes principaux
        ('SPAN', (0, 0), (5, 0)),   # Informations de base
        ('SPAN', (6, 0), (11, 0)),  # Production
        
        # En-tête 1 - Gris foncé
        ('BACKGROUND', (0, 0), (5, 1), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (5, 1), colors.white),
        ('FONTNAME', (0, 0), (5, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (5, 0), 12),
        ('FONTSIZE', (0, 1), (5, 1), 9),
        ('ALIGN', (0, 1), (5, 1), 'CENTER'),
        
        # En-tête 2 - Gris moyen
        ('BACKGROUND', (6, 0), (11, 1), colors.HexColor('#606060')),
        ('TEXTCOLOR', (6, 0), (11, 1), colors.white),
        ('FONTNAME', (6, 0), (11, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (6, 0), (11, 0), 12),
        ('FONTSIZE', (6, 1), (11, 1), 9),
        ('ALIGN', (6, 1), (11, 1), 'CENTER'),
        
        # Alignement et padding
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 2), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 8),
        
        # Bordures professionnelles NOIRES
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, 1), 1.5, colors.black),
        
        # Ligne de séparation
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.white),
        
        # Alternance des couleurs des lignes - Gris très clair
        ('ROWBACKGROUNDS', (2, 2), (-1, -1), 
         [colors.white, colors.HexColor('#F8F8F8')]),
        
        # Mise en valeur spéciale - Police plus épaisse
        ('FONTNAME', (10, 2), (10, -1), 'Helvetica-Bold'),  # Total Production
        ('FONTNAME', (11, 2), (11, -1), 'Helvetica-Bold'),  # Rendement
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 5. DASHBOARD DES INDICATEURS CLÉS - NOIR ET BLANC
    if queryset:
        # Calcul des indicateurs
        total_matiere = sum(float(obj.matiere_premiere_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        total_dechets = sum(float(obj.dechets_kg) for obj in queryset)
        rendements = [float(obj.rendement_pourcentage) for obj in queryset if obj.rendement_pourcentage]
        avg_rendement = sum(rendements) / len(rendements) if rendements else 0
        
        # Titre section KPI
        elements.append(Paragraph("📊 DASHBOARD DES INDICATEURS CLÉS", 
                                ParagraphStyle('KPITitle', fontSize=14, 
                                             textColor=colors.black,
                                             spaceAfter=0.5*cm,
                                             fontName='Helvetica-Bold')))
        
        # Cartes KPI en 2x2 avec motifs noir et blanc
        kpi_data = [
            ["PRODUCTION TOTALE", f"{total_production:,.0f} kg", "🏭", '#000000'],
            ["MATIÈRE PREMIÈRE", f"{total_matiere:,.0f} kg", "⚙️", '#404040'],
            ["RENDEMENT MOYEN", f"{avg_rendement:.1f}%", "📈", '#606060'],
            ["DÉCHETS TOTAUX", f"{total_dechets:,.0f} kg", "🗑️", '#808080']
        ]
        
        kpi_table_data = []
        for i in range(0, 4, 2):
            row = []
            for j in range(2):
                if i + j < 4:
                    kpi = kpi_data[i + j]
                    cell_content = f"""
                    <para alignment='center'>
                    <font name='Helvetica' size=9>{kpi[0]}</font><br/>
                    <font name='Helvetica-Bold' size=14>{kpi[2]} {kpi[1]}</font>
                    </para>
                    """
                    cell = Paragraph(cell_content, ParagraphStyle(
                        'KPICell', 
                        alignment=1,
                        fontSize=9,
                        spaceBefore=6,
                        spaceAfter=6
                    ))
                    row.append(cell)
                else:
                    row.append('')
            kpi_table_data.append(row)
        
        kpi_table = Table(kpi_table_data, colWidths=[doc.width/2 - 1*cm, doc.width/2 - 1*cm])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F0F0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 6. ANALYSE AUTOMATIQUE - CADRE GRIS
        analysis_text = "<b>🔍 ANALYSE AUTOMATIQUE :</b><br/>"
        
        if avg_rendement >= 85:
            analysis_text += "✓ <b>Rendement excellent</b> - Performance optimale de production<br/>"
        elif avg_rendement >= 70:
            analysis_text += "⚠ <b>Rendement acceptable</b> - Possibilité d'amélioration<br/>"
        else:
            analysis_text += "✗ <b>Rendement faible</b> - Nécessite une investigation approfondie<br/>"
            
        if total_dechets / (total_production + 0.001) * 100 > 15:
            analysis_text += "✗ <b>Taux de déchet élevé</b> - Optimisation nécessaire des processus"
        else:
            analysis_text += "✓ <b>Gestion des déchets optimale</b> - Processus bien maîtrisé"
        
        analysis_para = Paragraph(analysis_text, ParagraphStyle(
            'Analysis', 
            fontSize=9,
            textColor=colors.black,
            backColor=colors.HexColor('#F0F0F0'),
            borderPadding=10,
            borderColor=colors.black,
            borderWidth=1
        ))
        elements.append(analysis_para)
    
    # 7. PIED DE PAGE CORPORATE - NOIR ET BLANC
    elements.append(Spacer(1, 1.2*cm))
    
    # Ligne de séparation
    footer_separator = Table([['']], colWidths=[doc.width])
    footer_separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (0, 0), 5),
    ]))
    elements.append(footer_separator)
    
    # Informations footer
    footer_text = f"""
    <b>SOFEM-CI</b> | Usine de Production d'Emballage | Abidjan, Côte d'Ivoire<br/>
    <i>Document confidentiel - Réf: PROD-{datetime.now().strftime('%Y%m%d')}-001 | Page 1/1</i>
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'ProfessionalFooter',
        fontSize=8,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        fontName='Helvetica'
    ))
    elements.append(footer_para)
    
    # 8. GÉNÉRER LE PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response
# ==========================================
# FONCTIONS PDF PROFESSIONNELLES POUR TOUTES LES SECTIONS
# ==========================================

def create_ultra_professional_pdf(title, queryset, filename):
    """Crée une fiche de production ULTRA professionnelle OPTIMISÉE NOIR ET BLANC"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    
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
    
    # 1. EN-TÊTE PRINCIPALE
    header_style = ParagraphStyle(
        'CorporateHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        spaceAfter=0.3*cm,
        alignment=1,  # CENTER
        fontName='Helvetica-Bold'
    )
    
    header_content = f"<b>{title}</b>"
    elements.append(Paragraph(header_content, header_style))
    
    # 2. INFORMATIONS DE PÉRIODE
    dates = [obj.date_production for obj in queryset]
    if dates:
        min_date = min(dates).strftime('%d/%m/%Y')
        max_date = max(dates).strftime('%d/%m/%Y')
        period_text = f"<b>Période analysée :</b> Du {min_date} au {max_date}" if min_date != max_date else f"<b>Date :</b> {min_date}"
    else:
        period_text = f"<b>Date :</b> {datetime.now().strftime('%d/%m/%Y')}"
    
    info_text = f"""
    {period_text} | <b>Nombre d'enregistrements :</b> {len(queryset)} | <b>Généré le :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
    """
    
    elements.append(Paragraph(info_text, ParagraphStyle('InfoStyle', fontSize=10, 
                                                      textColor=colors.HexColor('#333333'),
                                                      spaceAfter=1.0*cm,
                                                      alignment=1)))
    
    # 3. TABLEAU PRINCIPAL SEULEMENT
    # En-têtes simples
    headers = [
        'Date', 'Zone', 'Équipe', 'Matière P', 'Machines ', 'Personnel',
        'Bobines', 'Finis', 'Semi-Finis', 'Déchets', 'Total', 'yield (%)'
    ]
    
    # Préparer les données
    table_data = [headers]
    
    for obj in queryset.order_by('date_production', 'zone'):
        rendement = float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0
        
        # Formatage
        matiere_premiere = float(obj.matiere_premiere_kg)
        bobines = float(obj.nombre_bobines_kg)
        finis = float(obj.production_finis_kg)
        semi_finis = float(obj.production_semi_finis_kg)
        dechets = float(obj.dechets_kg)
        total = float(obj.total_production_kg) if obj.total_production_kg else 0
        
        # Formatage des nombres avec espace comme séparateur
        def format_number(num):
            return f"{num:,.0f}".replace(",", " ")
        
        # Date formatée correctement (pas de troncature)
        date_str = obj.date_production.strftime('%d/%m/%Y')
        
        # Formater l'équipe
        equipe_str = str(obj.equipe)
        
        row_data = [
            date_str,  # Date complète
            str(obj.zone),
            equipe_str,
            format_number(matiere_premiere),
            str(obj.nombre_machines_actives),
            str(obj.nombre_machinistes),
            format_number(bobines),
            format_number(finis),
            format_number(semi_finis),
            format_number(dechets),
            format_number(total) if total else "0",
            f"{rendement:.1f}"  # Rendement sans "%" dans la cellule
        ]
        table_data.append(row_data)
    
    # Largeurs de colonnes ajustées POUR LES BONNES BORDURES
    col_widths = [
        2.8*cm,  # Date (un peu plus large)
        3.2*cm,  # Zone
        5.0*cm,  # Équipe
        2.5*cm,  # Matière Première
        2.0*cm,  # Machines Actives
        2.0*cm,  # Personnel
        2.0*cm,  # Bobines
        2.0*cm,  # Finis
        2.0*cm,  # Semi-Finis
        2.0*cm,  # Déchets
        2.0*cm,  # Total
        2.0*cm   # Rendement (%)
    ]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # STYLE AVEC BORDURES PARFAITES
    table.setStyle(TableStyle([
        # === EN-TÊTE ===
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # === ALIGNEMENT DES DONNÉES ===
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),    # Date CENTRÉE
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),      # Zone à gauche
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),      # Équipe à gauche
        ('ALIGN', (3, 1), (10, -1), 'RIGHT'),    # Données numériques à droite
        ('ALIGN', (11, 1), (11, -1), 'CENTER'),  # Rendement CENTRÉ
        
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (-1, -1), 6),
        ('RIGHTPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        
        # === BORDURES COMPLÈTES ET BIEN ALIGNÉES ===
        # Bordures extérieures épaisses
        ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
        # Bordures intérieures verticales
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, colors.black),
        ('LINEBEFORE', (3, 0), (3, -1), 0.5, colors.black),
        ('LINEBEFORE', (4, 0), (4, -1), 0.5, colors.black),
        ('LINEBEFORE', (5, 0), (5, -1), 0.5, colors.black),
        ('LINEBEFORE', (6, 0), (6, -1), 0.5, colors.black),
        ('LINEBEFORE', (7, 0), (7, -1), 0.5, colors.black),
        ('LINEBEFORE', (8, 0), (8, -1), 0.5, colors.black),
        ('LINEBEFORE', (9, 0), (9, -1), 0.5, colors.black),
        ('LINEBEFORE', (10, 0), (10, -1), 0.5, colors.black),
        ('LINEBEFORE', (11, 0), (11, -1), 0.5, colors.black),
        # Bordures intérieures horizontales
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Sous l'en-tête
        ('LINEBELOW', (0, 1), (-1, -2), 0.25, colors.HexColor('#CCCCCC')),  # Lignes séparatrices
        
        # === ALTERNANCE DES COULEURS ===
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), 
         [colors.white, colors.HexColor('#F9F9F9')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 1.5*cm))
    
    # 4. PIED DE PAGE DIRECTEMENT APRÈS LE TABLEAU
    footer_text = f"""
    <b>SOFEM-CI</b> | Usine de Production d'Emballage | Abidjan, Côte d'Ivoire<br/>
    <i>Document confidentiel - Réf: PROD-{datetime.now().strftime('%Y%m%d')}-001 | Page 1/1</i>
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'ProfessionalFooter',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1,  # CENTER
        fontName='Helvetica',
        spaceBefore=0.5*cm
    ))
    elements.append(footer_para)
    
    # 5. GÉNÉRER LE PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def create_ultra_professional_pdf_soudure(title, queryset, filename):
    """Crée une fiche de production soudure ULTRA professionnelle NOIR ET BLANC AVEC TABLEAU AGRANDI"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=1.0*cm,  # MARGES RÉDUITES
        leftMargin=1.0*cm,
        topMargin=2.0*cm, 
        bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. EN-TÊTE PLUS COMPACT
    header_style = ParagraphStyle(
        'SoudureHeader',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=0.2*cm,
        alignment=1,  # CENTRÉ
        fontName='Helvetica-Bold'
    )
    
    header_content = f"<b>{title}</b>"
    elements.append(Paragraph(header_content, header_style))
    
    # 2. INFORMATIONS
    dates = [obj.date_production for obj in queryset]
    if dates:
        min_date = min(dates).strftime('%d/%m/%Y')
        max_date = max(dates).strftime('%d/%m/%Y')
        period_text = f"<b>PÉRIODE ANALYSÉE :</b> Du {min_date} au {max_date}" if min_date != max_date else f"<b>DATE :</b> {min_date}"
    else:
        period_text = f"<b>DATE :</b> {datetime.now().strftime('%d/%m/%Y')}"
    
    info_text = f"""
    {period_text} | <b>ENREGISTREMENTS :</b> {len(queryset)} | <b>GÉNÉRÉ LE :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
    """
    
    elements.append(Paragraph(info_text, ParagraphStyle('InfoStyle', fontSize=9,
                                                      textColor=colors.HexColor('#000000'),
                                                      spaceAfter=0.6*cm,
                                                      alignment=1)))
    
    # 3. TABLEAU PRINCIPAL - AGRANDI
    headers = [
        'DATE', 'CRÉNEAU', 'MACHINES', 
        'BOBINES (kg)', 'BRETELLES (kg)', 'REMA (kg)', 
        'BATTA (kg)', 'SAC (kg)', 'DÉCHETS (kg)', 'TOTAL (kg)'
    ]
    
    table_data = [headers]
    
    for obj in queryset.order_by('date_production'):
        heure_debut = obj.heure_debut.strftime('%Hh') if obj.heure_debut else '--'
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            heure_debut,
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
    
    # COLONNES AGRANDIES
    total_width = doc.width
    col_widths = [
        total_width * 0.10,  # DATE
        total_width * 0.08,  # CRÉNEAU
        total_width * 0.07,  # MACHINES
        total_width * 0.10,  # BOBINES
        total_width * 0.10,  # BRETELLES
        total_width * 0.10,  # REMA
        total_width * 0.10,  # BATTA
        total_width * 0.10,  # SAC
        total_width * 0.10,  # DÉCHETS
        total_width * 0.15   # TOTAL
    ]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # STYLE AGRANDI
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Données
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, 0), 1.5, colors.black),
        
        # Alternance
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), 
         [colors.white, colors.HexColor('#F5F5F5')]),
        
        # Mise en valeur
        ('FONTNAME', (9, 1), (9, -1), 'Helvetica-Bold'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 4. TABLEAU DES TOTAUX AGRANDI
    if queryset:
        total_bobines = sum(float(obj.production_bobines_finies_kg) for obj in queryset)
        total_bretelles = sum(float(obj.production_bretelles_kg) for obj in queryset)
        total_rema = sum(float(obj.production_rema_kg) for obj in queryset)
        total_batta = sum(float(obj.production_batta_kg) for obj in queryset)
        total_sac = sum(float(obj.production_sac_emballage_kg) for obj in queryset)
        total_dechets = sum(float(obj.dechets_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        
        # Tableau des totaux LARGE
        totals_headers = ['TYPE DE PRODUCTION', 'QUANTITÉ (kg)', '% DU TOTAL', 'CONTRIBUTION']
        totals_data = [totals_headers]
        
        types = [
            ('BOBINES FINIES', total_bobines),
            ('BRETELLES', total_bretelles),
            ('REMA-PLASTIQUE', total_rema),
            ('BATTA', total_batta),
            ('SAC EMBALLAGE', total_sac),
            ('DÉCHETS', total_dechets),
            ('TOTAL PRODUCTION', total_production)
        ]
        
        for type_name, qty in types:
            percentage = (qty / (total_production + 0.001)) * 100 if total_production > 0 else 0
            
            # Évaluation
            if type_name == 'TOTAL PRODUCTION':
                contrib = '📊 TOTAL GÉNÉRÉ'
            elif type_name == 'DÉCHETS':
                if percentage < 5:
                    contrib = '✅ FAIBLE'
                elif percentage < 10:
                    contrib = '⚠️ MOYEN'
                else:
                    contrib = '❌ ÉLEVÉ'
            else:
                if percentage > 20:
                    contrib = '📈 PRINCIPALE'
                elif percentage > 10:
                    contrib = '📊 SECONDAIRE'
                else:
                    contrib = '📉 MINEURE'
            
            totals_data.append([
                type_name,
                f"{qty:,.0f}",
                f"{percentage:.1f}%",
                contrib
            ])
        
        totals_table = Table(totals_data, colWidths=[total_width*0.30, total_width*0.20, total_width*0.20, total_width*0.30])
        totals_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#505050')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            
            ('FONTNAME', (0, 6), (-1, 6), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 6), (-1, 6), colors.HexColor('#E8E8E8')),
        ]))
        
        elements.append(Paragraph("<b>📊 RÉPARTITION DE LA PRODUCTION</b>", 
                                ParagraphStyle('TotalsTitle', fontSize=12, 
                                             spaceAfter=0.3*cm,
                                             alignment=1)))
        elements.append(totals_table)
    
    # 5. PIED DE PAGE
    elements.append(Spacer(1, 0.5*cm))
    
    footer_text = f"""
    <b>SOFEM-CI | SECTION SOUDURE</b> | Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | Page 1/1
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'Footer',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        fontName='Helvetica',
        spaceBefore=0.3*cm
    ))
    elements.append(footer_para)
    
    # 6. GÉNÉRER LE PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response


def create_ultra_professional_pdf_recyclage(title, queryset, filename):
    """Crée une fiche de production recyclage ULTRA professionnelle NOIR ET BLANC AVEC TABLEAU AGRANDI"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=1.0*cm,  # MARGES RÉDUITES
        leftMargin=1.0*cm,
        topMargin=2.0*cm, 
        bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. EN-TÊTE PLUS COMPACT
    header_style = ParagraphStyle(
        'RecyclageHeader',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=0.2*cm,
        alignment=1,  # CENTRÉ
        fontName='Helvetica-Bold'
    )
    
    header_content = f"<b>{title}</b>"
    elements.append(Paragraph(header_content, header_style))
    
    # 2. INFORMATIONS
    dates = [obj.date_production for obj in queryset]
    if dates:
        min_date = min(dates).strftime('%d/%m/%Y')
        max_date = max(dates).strftime('%d/%m/%Y')
        period_text = f"<b>PÉRIODE ANALYSÉE :</b> Du {min_date} au {max_date}" if min_date != max_date else f"<b>DATE :</b> {min_date}"
    else:
        period_text = f"<b>DATE :</b> {datetime.now().strftime('%d/%m/%Y')}"
    
    info_text = f"""
    {period_text} | <b>ENREGISTREMENTS :</b> {len(queryset)} | <b>GÉNÉRÉ LE :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
    """
    
    elements.append(Paragraph(info_text, ParagraphStyle('InfoStyle', fontSize=9,
                                                      textColor=colors.HexColor('#000000'),
                                                      spaceAfter=0.6*cm,
                                                      alignment=1)))
    
    # 3. TABLEAU PRINCIPAL - AGRANDI
    headers = [
        'DATE', 'ÉQUIPE', 'MOULINEX', 
        'BROYAGE (kg)', 'BÂCHE NOIRE (kg)', 
        'TOTAL (kg)', 'PROD/MOULINEX', 'TAUX TRANSFO (%)'
    ]
    
    table_data = [headers]
    
    for obj in queryset.order_by('date_production', 'equipe'):
        taux_transfo = obj.taux_transformation_pourcentage or 0
        prod_par_moulinex = obj.production_par_moulinex or 0
        
        # Abréviation équipe
        equipe_abbr = str(obj.equipe)[:12] if obj.equipe else "-"
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            equipe_abbr,
            str(obj.nombre_moulinex),
            f"{float(obj.production_broyage_kg):,.0f}",
            f"{float(obj.production_bache_noir_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{prod_par_moulinex:,.0f}",
            f"{taux_transfo:.1f}%"
        ]
        table_data.append(row_data)
    
    # COLONNES AGRANDIES
    total_width = doc.width
    col_widths = [
        total_width * 0.12,  # DATE
        total_width * 0.15,  # ÉQUIPE
        total_width * 0.10,  # MOULINEX
        total_width * 0.12,  # BROYAGE
        total_width * 0.12,  # BÂCHE NOIRE
        total_width * 0.12,  # TOTAL
        total_width * 0.14,  # PROD/MOULINEX
        total_width * 0.13   # TAUX TRANSFO
    ]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # STYLE AGRANDI
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Données
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, 0), 1.5, colors.black),
        
        # Alternance
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), 
         [colors.white, colors.HexColor('#F5F5F5')]),
        
        # Mise en valeur
        ('FONTNAME', (5, 1), (5, -1), 'Helvetica-Bold'),  # Total
        ('FONTNAME', (7, 1), (7, -1), 'Helvetica-Bold'),  # Taux Transfo
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 4. TABLEAU DES INDICATEURS AGRANDI
    if queryset:
        total_broyage = sum(float(obj.production_broyage_kg) for obj in queryset)
        total_bache = sum(float(obj.production_bache_noir_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        total_moulinex = sum(obj.nombre_moulinex for obj in queryset)
        
        # Calculs
        taux_transfo_global = (total_bache / (total_broyage + 0.001)) * 100
        prod_moyenne_par_moulinex = total_production / (total_moulinex + 0.001) if total_moulinex > 0 else 0
        
        # Tableau d'indicateurs LARGE
        indicators_headers = ['INDICATEUR DE PERFORMANCE', 'VALEUR', 'OBJECTIF', 'ÉVALUATION']
        indicators_data = [indicators_headers]
        
        indicators = [
            ('Broyage Total', f"{total_broyage:,.0f} kg", "Maximiser", 
             '✅ Bon' if total_broyage > 0 else '❌ Nul'),
            ('Bâche Noire', f"{total_bache:,.0f} kg", "Maximiser", 
             '✅ Bon' if total_bache > 0 else '❌ Nul'),
            ('Taux Transformation', f"{taux_transfo_global:.1f}%", "> 75%", 
             '✅ Excellent' if taux_transfo_global >= 75 else '⚠️ Moyen' if taux_transfo_global >= 50 else '❌ Faible'),
            ('Prod/Moulinex Moy', f"{prod_moyenne_par_moulinex:,.0f} kg", "> 500 kg", 
             '✅ Haute' if prod_moyenne_par_moulinex >= 500 else '⚠️ Moyenne' if prod_moyenne_par_moulinex >= 300 else '❌ Faible'),
            ('Total Production', f"{total_production:,.0f} kg", "Maximiser", 
             '✅ Atteint' if total_production > 0 else '❌ Nul'),
        ]
        
        for name, value, target, evaluation in indicators:
            indicators_data.append([name, value, target, evaluation])
        
        indicators_table = Table(indicators_data, colWidths=[total_width*0.30, total_width*0.20, total_width*0.20, total_width*0.30])
        indicators_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#505050')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(Paragraph("<b>📈 INDICATEURS DE PERFORMANCE RECYCLAGE</b>", 
                                ParagraphStyle('IndicatorsTitle', fontSize=12, 
                                             spaceAfter=0.3*cm,
                                             alignment=1)))
        elements.append(indicators_table)
    
    # 5. PIED DE PAGE
    elements.append(Spacer(1, 0.5*cm))
    
    footer_text = f"""
    <b>SOFEM-CI | SECTION RECYCLAGE ♻</b> | Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | Page 1/1
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'Footer',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        fontName='Helvetica',
        spaceBefore=0.3*cm
    ))
    elements.append(footer_para)
    
    # 6. GÉNÉRER LE PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    return response

def create_ultra_professional_pdf_imprimerie(title, queryset, filename):
    """Crée une fiche de production imprimerie ULTRA professionnelle NOIR ET BLANC AVEC TABLEAU AGRANDI"""
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        rightMargin=1.0*cm,  # MARGES RÉDUITES POUR PLUS D'ESPACE
        leftMargin=1.0*cm,
        topMargin=2.0*cm, 
        bottomMargin=1.5*cm
    )
    elements = []
    styles = getSampleStyleSheet()
    
    # 1. EN-TÊTE CORPORATE - PLUS COMPACT POUR LIBÉRER DE L'ESPACE
    header_style = ParagraphStyle(
        'ImprimerieHeader',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.black,
        spaceAfter=0.2*cm,
        alignment=1,  # CENTRÉ
        fontName='Helvetica-Bold'
    )
    
    header_content = f"<b>{title}</b>"
    elements.append(Paragraph(header_content, header_style))
    
    # 2. INFORMATIONS DE PÉRIODE
    dates = [obj.date_production for obj in queryset]
    if dates:
        min_date = min(dates).strftime('%d/%m/%Y')
        max_date = max(dates).strftime('%d/%m/%Y')
        period_text = f"<b>PÉRIODE ANALYSÉE :</b> Du {min_date} au {max_date}" if min_date != max_date else f"<b>DATE :</b> {min_date}"
    else:
        period_text = f"<b>DATE :</b> {datetime.now().strftime('%d/%m/%Y')}"
    
    info_text = f"""
    {period_text} | <b>ENREGISTREMENTS :</b> {len(queryset)} | <b>GÉNÉRÉ LE :</b> {datetime.now().strftime('%d/%m/%Y à %H:%M')}
    """
    
    elements.append(Paragraph(info_text, ParagraphStyle('InfoStyle', fontSize=9,
                                                      textColor=colors.HexColor('#000000'),
                                                      spaceAfter=0.6*cm,
                                                      alignment=1)))
    
    # 3. TABLEAU PRINCIPAL - AGRANDI POUR OCCUPER TOUTE LA LARGEUR
    headers = [
        'DATE', 'CRÉNEAU HORAIRE', 'MACHINES', 
        'BOBINES FINIES (kg)', 'BOBINES SEMI (kg)', 
        'DÉCHETS (kg)', 'TOTAL (kg)', 'TAUX DÉCHET (%)'
    ]
    
    # Préparer les données
    table_data = [headers]
    
    for idx, obj in enumerate(queryset.order_by('date_production', 'heure_debut')):
        heure_debut = obj.heure_debut.strftime('%Hh%M') if obj.heure_debut else '--:--'
        heure_fin = obj.heure_fin.strftime('%Hh%M') if obj.heure_fin else '--:--'
        heures = f"{heure_debut} - {heure_fin}"
        
        taux_dechet = obj.taux_dechet_pourcentage or 0
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            heures,
            str(obj.nombre_machines_actives),
            f"{float(obj.production_bobines_finies_kg):,.0f}",
            f"{float(obj.production_bobines_semi_finies_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{taux_dechet:.1f}%"
        ]
        table_data.append(row_data)
    
    # COLONNES AGRANDIES POUR OCCUPER TOUTE LA PAGE
    total_width = doc.width
    col_widths = [
        total_width * 0.12,  # DATE
        total_width * 0.15,  # CRÉNEAU
        total_width * 0.08,  # MACHINES
        total_width * 0.14,  # BOBINES FINIES
        total_width * 0.12,  # BOBINES SEMI
        total_width * 0.10,  # DÉCHETS
        total_width * 0.14,  # TOTAL
        total_width * 0.15   # TAUX DÉCHET
    ]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # STYLE AVEC COLONNES PLUS LARGES
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),  # TEXTE PLUS GRAND
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        
        # Padding augmenté
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Données
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),  # TEXTE PLUS GRAND
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
        
        # Bordures
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('BOX', (0, 0), (-1, 0), 1.5, colors.black),
        
        # Alternance
        ('ROWBACKGROUNDS', (1, 1), (-1, -1), 
         [colors.white, colors.HexColor('#F5F5F5')]),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 4. SECTION STATISTIQUES AGRANDIE
    if queryset:
        total_bobines_finies = sum(float(obj.production_bobines_finies_kg) for obj in queryset)
        total_bobines_semi = sum(float(obj.production_bobines_semi_finies_kg) for obj in queryset)
        total_dechets = sum(float(obj.dechets_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        
        # Tableau de statistiques LARGE
        stats_headers = ['INDICATEUR', 'VALEUR', 'OBJECTIF', 'STATUT']
        stats_data = [stats_headers]
        
        stats = [
            ('Production Totale', f"{total_production:,.0f} kg", "Maximiser", 
             '✅ Atteint' if total_production > 0 else '❌ Nul'),
            ('Bobines Finies', f"{total_bobines_finies:,.0f} kg", 
             f"{(total_bobines_finies/(total_production+0.001)*100):.1f}%", 
             '✅ Bon' if (total_bobines_finies/(total_production+0.001)) > 0.6 else '⚠️ Moyen'),
            ('Taux Déchet', f"{(total_dechets/(total_production+0.001)*100):.1f}%", "< 5%", 
             '✅ Bon' if (total_dechets/(total_production+0.001)) < 0.05 else '❌ Élevé'),
            ('Productivité/Machine', f"{(total_production/sum(obj.nombre_machines_actives for obj in queryset)):,.0f} kg", "> 500 kg", 
             '✅ Bonne' if (total_production/(sum(obj.nombre_machines_actives for obj in queryset)+0.001)) > 500 else '⚠️ Faible'),
        ]
        
        for name, value, target, status in stats:
            stats_data.append([name, value, target, status])
        
        stats_table = Table(stats_data, colWidths=[total_width*0.25, total_width*0.25, total_width*0.25, total_width*0.25])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#505050')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(Paragraph("<b>📊 STATISTIQUES DE PERFORMANCE</b>", 
                                ParagraphStyle('StatsTitle', fontSize=12, 
                                             spaceAfter=0.3*cm,
                                             alignment=1)))
        elements.append(stats_table)
    
    # 5. PIED DE PAGE
    elements.append(Spacer(1, 0.5*cm))
    
    footer_text = f"""
    <b>SOFEM-CI | SECTION IMPRIMERIE</b> | Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} | Page 1/1
    """
    
    footer_para = Paragraph(footer_text, ParagraphStyle(
        'Footer',
        fontSize=9,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        fontName='Helvetica',
        spaceBefore=0.3*cm
    ))
    elements.append(footer_para)
    
    # 6. GÉNÉRER LE PDF
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
# ADMINISTRATION PRODUCTION EXTRUSION - VERSION ULTRA
# ==========================================

@admin.register(ProductionExtrusion)
class ProductionExtrusionAdmin(admin.ModelAdmin):
    # AFFICHAGE OPTIMISÉ POUR NE PAS DÉBORDER
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
    
    list_display_links = ['date_production_short', 'get_zone_compact', 'get_equipe_compact']
    
    list_filter = ['date_production', 'zone', 'equipe', 'valide']
    search_fields = ['chef_zone', 'observations', 'zone__nom', 'equipe__nom']
    
    readonly_fields = [
        'total_production_kg', 
        'rendement_pourcentage', 
        'taux_dechet_pourcentage', 
        'production_par_machine', 
        'date_creation', 
        'date_modification', 
        'cree_par'
    ]
    
    ordering = ['-date_production']
    
    # Configuration de l'affichage des colonnes
    list_per_page = 50
    list_max_show_all = 200
    
    # FONCTIONS D'AFFICHAGE COMPACT POUR LES COLONNES
    
    def date_production_short(self, obj):
        """Date formatée en format compact"""
        return obj.date_production.strftime('%d/%m')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_zone_compact(self, obj):
        """Zone formatée en format ultra-compact"""
        if obj.zone and obj.zone.nom:
            # Prendre les 3 premières lettres du nom de la zone
            return f"Z{obj.zone.numero}:{obj.zone.nom[:8]}"
        return f"Z{obj.zone.numero}"
    get_zone_compact.short_description = "📍 Zone"
    get_zone_compact.admin_order_field = 'zone__numero'
    
    def get_equipe_compact(self, obj):
        """Équipe formatée en format ultra-compact"""
        if not obj.equipe:
            return "-"
        
        # Récupérer l'heure de début de l'équipe
        heure_debut = obj.equipe.heure_debut.strftime('%Hh') if obj.equipe.heure_debut else "?"
        
        # Formater de manière ultra compacte
        # Exemple: "Mat (8h-16h)" ou "Soir (16h-00h)"
        equipe_nom = obj.equipe.nom.lower()
        if "matin" in equipe_nom or "jour" in equipe_nom:
            return f"🟢 {heure_debut}"
        elif "soir" in equipe_nom:
            return f"🔵 {heure_debut}"
        elif "nuit" in equipe_nom:
            return f"🌙 {heure_debut}"
        else:
            # Prendre les premières lettres du nom
            abbreviation = ''.join([word[0].upper() for word in obj.equipe.nom.split()[:2]])
            return f"👥 {abbreviation[:3]}"
    get_equipe_compact.short_description = "👥 Équipe"
    get_equipe_compact.admin_order_field = 'equipe__nom'
    
    def get_matiere_premiere(self, obj):
        """Matière première formatée"""
        return f"{float(obj.matiere_premiere_kg):,.0f} kg"
    get_matiere_premiere.short_description = "⚙️ Matière"
    get_matiere_premiere.admin_order_field = 'matiere_premiere_kg'
    
    def get_machines_actives(self, obj):
        """Machines actives formatées"""
        return f"{obj.nombre_machines_actives}📊"
    get_machines_actives.short_description = "🖥️ Machines"
    get_machines_actives.admin_order_field = 'nombre_machines_actives'
    
    def get_personnel(self, obj):
        """Personnel formaté"""
        return f"{obj.nombre_machinistes}👷"
    get_personnel.short_description = "👷 Pers"
    get_personnel.admin_order_field = 'nombre_machinistes'
    
    def get_bobines(self, obj):
        """Bobines formatées"""
        return f"{float(obj.nombre_bobines_kg):,.0f}📦"
    get_bobines.short_description = "📦 Bobines"
    get_bobines.admin_order_field = 'nombre_bobines_kg'
    
    def get_finis(self, obj):
        """Produits finis formatés"""
        return f"{float(obj.production_finis_kg):,.0f}✅"
    get_finis.short_description = "✅ Finis"
    get_finis.admin_order_field = 'production_finis_kg'
    
    def get_semi_finis(self, obj):
        """Semi-finis formatés"""
        return f"{float(obj.production_semi_finis_kg):,.0f}🔄"
    get_semi_finis.short_description = "🔄 Semi"
    get_semi_finis.admin_order_field = 'production_semi_finis_kg'
    
    def get_dechets(self, obj):
        """Déchets formatés"""
        return f"{float(obj.dechets_kg):,.0f}🗑️"
    get_dechets.short_description = "🗑️ Déchets"
    get_dechets.admin_order_field = 'dechets_kg'
    
    def get_total_production(self, obj):
        """Total production formaté"""
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}🏭"
        return "0 🏭"
    get_total_production.short_description = "🏭 Total"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_rendement(self, obj):
        """Rendement formaté avec couleur selon la performance"""
        if not obj.rendement_pourcentage:
            return "0.0%"
        
        rendement = float(obj.rendement_pourcentage)
        rendement_formatted = format(rendement, '.1f')
        
        # CORRECTION ICI : format_html prend d'abord le format string, puis les arguments
        if rendement >= 85:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}%</span>', 
                rendement_formatted
            )
        elif rendement >= 70:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}%</span>', 
                rendement_formatted
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}%</span>', 
                rendement_formatted
            )
    get_rendement.short_description = "📈 Rendement"
    get_rendement.admin_order_field = 'rendement_pourcentage'
    
    def get_status_icon(self, obj):
        """Icône de statut de validation"""
        if obj.valide:
            return format_html('<span style="color: green;">✅ Validé</span>')
        else:
            return format_html('<span style="color: red;">❌ En attente</span>')
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    # Ajouter un tri personnalisé pour certains champs
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('zone', 'equipe')
    
    # Configuration des champs dans l'édition
    fieldsets = (
        ('📅 Informations de base', {
            'fields': (
                'date_production',
                'zone',
                'equipe',
                'chef_zone',
                'heure_debut',
                'heure_fin'
            )
        }),
        ('⚙️ Ressources utilisées', {
            'fields': (
                'matiere_premiere_kg',
                'nombre_machines_actives',
                'nombre_machinistes'
            )
        }),
        ('📦 Production détaillée', {
            'fields': (
                'nombre_bobines_kg',
                'production_finis_kg',
                'production_semi_finis_kg',
                'dechets_kg'
            )
        }),
        ('📊 Calculs automatiques', {
            'fields': (
                'total_production_kg',
                'rendement_pourcentage',
                'taux_dechet_pourcentage',
                'production_par_machine'
            ),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': (
                'observations',
                'valide',
                'cree_par'
            )
        })
    )
    
    # ACTIONS ULTRA PROFESSIONNELLES
    actions = [
        'valider_production', 
        'invalider_production', 
        'export_pdf_fiche_production_ultra',
        'export_excel_fiche_production'
    ]
    
    # Métadonnées
    class Media:
        css = {
            'all': ('admin/css/production.css',)
        }
    
    def changelist_view(self, request, extra_context=None):
        # Ajouter un titre personnalisé
        if extra_context is None:
            extra_context = {}
        extra_context['title'] = '📊 Tableau de Production Extrusion - Vue Compacte'
        return super().changelist_view(request, extra_context=extra_context)
    
    # Méthodes existantes (restent inchangées)
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider la production"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider la production"
    
    # ⭐⭐⭐ FONCTION D'EXPORT PDF ULTRA PROFESSIONNELLE ⭐⭐⭐
    def export_pdf_fiche_production_ultra(self, request, queryset):
        """Export PDF ULTRA professionnel de la fiche de production"""
        title = "FICHE DE PRODUCTION EXTRUSION"
        filename = f"Fiche_Production_Extrusion_UltraPro_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # Vérifier qu'il y a des données
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        try:
            # APPEL DE LA FONCTION ULTRA PROFESSIONNELLE
            return create_ultra_professional_pdf(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur lors de la génération du PDF: {str(e)}", messages.ERROR)
            # Fallback vers un PDF simple
            return self.create_simple_pdf_fallback(title, queryset, filename)
    
    export_pdf_fiche_production_ultra.short_description = "🏆 Fiche Production Ultra Pro (PDF)"
    
    def create_simple_pdf_fallback(self, title, queryset, filename):
        """Fallback simple si la version ultra échoue"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, title)
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y = height - 120
        for obj in queryset:
            p.drawString(50, y, f"{obj.date_production} - {obj.zone} - {obj.equipe}")
            y -= 20
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}_simple.pdf"'
        return response
    
    def export_excel_fiche_production(self, request, queryset):
        """Export Excel professionnel"""
        title = "FICHE DE PRODUCTION EXTRUSION"
        filename = f"Fiche_Production_Extrusion_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Production Extrusion"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        blue_header = PatternFill(start_color="1A4B8C", end_color="1A4B8C", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # En-tête
        ws.merge_cells('A1:L1')
        ws['A1'] = "SOFEM-CI - FICHE DE PRODUCTION EXTRUSION"
        ws['A1'].font = Font(bold=True, size=16, color="1A4B8C")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Date
        ws.merge_cells('A2:L2')
        ws['A2'] = f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(size=11, color="666666")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws.append([])
        
        # En-têtes tableau
        headers = [
            'Date', 'Zone', 'Équipe', 'Matière (kg)', 'Machines Actives', 'Machinistes',
            'Bobines (kg)', 'Finis (kg)', 'Semi-Finis (kg)', 'Déchets (kg)', 
            'Total Production (kg)', 'Rendement (%)'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = header_font
            cell.fill = blue_header
            cell.alignment = center_alignment
        
        # Données
        row_num = 5
        for obj in queryset.order_by('date_production', 'zone'):
            ws.cell(row=row_num, column=1, value=obj.date_production).number_format = 'DD/MM/YYYY'
            ws.cell(row=row_num, column=2, value=str(obj.zone))
            ws.cell(row=row_num, column=3, value=str(obj.equipe))
            ws.cell(row=row_num, column=4, value=float(obj.matiere_premiere_kg))
            ws.cell(row=row_num, column=5, value=int(obj.nombre_machines_actives))
            ws.cell(row=row_num, column=6, value=int(obj.nombre_machinistes))
            ws.cell(row=row_num, column=7, value=float(obj.nombre_bobines_kg))
            ws.cell(row=row_num, column=8, value=float(obj.production_finis_kg))
            ws.cell(row=row_num, column=9, value=float(obj.production_semi_finis_kg))
            ws.cell(row=row_num, column=10, value=float(obj.dechets_kg))
            ws.cell(row=row_num, column=11, value=float(obj.total_production_kg) if obj.total_production_kg else 0)
            ws.cell(row=row_num, column=12, value=float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0)
            
            row_num += 1
        
        # Formater les colonnes
        for col in ['D', 'G', 'H', 'I', 'J', 'K']:
            for row in range(5, row_num):
                cell = ws[f'{col}{row}']
                cell.number_format = '#,##0'
        
        # Ajuster largeur
        column_widths = {
            'A': 12,  # Date
            'B': 15,  # Zone
            'C': 12,  # Équipe
            'D': 12,  # Matière
            'E': 10,  # Machines
            'F': 10,  # Machinistes
            'G': 12,  # Bobines
            'H': 12,  # Finis
            'I': 12,  # Semi-finis
            'J': 12,  # Déchets
            'K': 15,  # Total
            'L': 12   # Rendement
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Sauvegarder
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response
    
    export_excel_fiche_production.short_description = "📊 Exporter en Excel"
# ==========================================
# ADMINISTRATION PRODUCTION IMPRIMERIE
# ==========================================

@admin.register(ProductionImprimerie)
class ProductionImprimerieAdmin(admin.ModelAdmin):
    # AFFICHAGE OPTIMISÉ POUR NE PAS DÉBORDER
    list_display = [
        'date_production_short',
        'get_heures_creneau',
        'get_machines_actives',
        'get_bobines_finies',
        'get_bobines_semi',
        'get_dechets',
        'get_total_production',
        'get_taux_dechet',
        'get_status_icon',
    ]
    
    list_display_links = ['date_production_short']
    
    list_filter = ['date_production', 'valide']
    search_fields = ['observations']
    
    readonly_fields = [
        'total_production_kg', 
        'taux_dechet_pourcentage', 
        'date_creation', 
        'date_modification', 
        'cree_par'
    ]
    
    ordering = ['-date_production']
    
    # Configuration de l'affichage des colonnes
    list_per_page = 50
    list_max_show_all = 200
    
    # FONCTIONS D'AFFICHAGE COMPACT POUR LES COLONNES
    
    def date_production_short(self, obj):
        """Date formatée en format compact"""
        return obj.date_production.strftime('%d/%m')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_heures_creneau(self, obj):
        """Créneau horaire formaté"""
        heure_debut = obj.heure_debut.strftime('%Hh%M') if obj.heure_debut else "--:--"
        heure_fin = obj.heure_fin.strftime('%Hh%M') if obj.heure_fin else "--:--"
        return f"{heure_debut}→{heure_fin}"
    get_heures_creneau.short_description = "🕒 Créneau"
    
    def get_machines_actives(self, obj):
        """Machines actives formatées"""
        return f"{obj.nombre_machines_actives}🖨️"
    get_machines_actives.short_description = "🖥️ Machines"
    get_machines_actives.admin_order_field = 'nombre_machines_actives'
    
    def get_bobines_finies(self, obj):
        """Bobines finies formatées"""
        return f"{float(obj.production_bobines_finies_kg):,.0f}✅"
    get_bobines_finies.short_description = "✅ Finies"
    get_bobines_finies.admin_order_field = 'production_bobines_finies_kg'
    
    def get_bobines_semi(self, obj):
        """Bobines semi-finies formatées"""
        return f"{float(obj.production_bobines_semi_finies_kg):,.0f}🔄"
    get_bobines_semi.short_description = "🔄 Semi"
    get_bobines_semi.admin_order_field = 'production_bobines_semi_finies_kg'
    
    def get_dechets(self, obj):
        """Déchets formatés"""
        return f"{float(obj.dechets_kg):,.0f}🗑️"
    get_dechets.short_description = "🗑️ Déchets"
    get_dechets.admin_order_field = 'dechets_kg'
    
    def get_total_production(self, obj):
        """Total production formaté"""
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}🏭"
        return "0 🏭"
    get_total_production.short_description = "🏭 Total"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_taux_dechet(self, obj):
        """Taux de déchet formaté avec couleur"""
        if not obj.taux_dechet_pourcentage:
            return "0.0%"
        
        taux = float(obj.taux_dechet_pourcentage)
        taux_formatted = format(taux, '.1f')
        
        if taux <= 5:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
        elif taux <= 10:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
    get_taux_dechet.short_description = "📉 Taux Déchet"
    get_taux_dechet.admin_order_field = 'taux_dechet_pourcentage'
    
    def get_status_icon(self, obj):
        """Icône de statut de validation"""
        if obj.valide:
            return format_html('<span style="color: green;">✅ Validé</span>')
        else:
            return format_html('<span style="color: red;">❌ En attente</span>')
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    # Configuration des champs dans l'édition
    fieldsets = (
        ('📅 Informations de base', {
            'fields': (
                'date_production',
                'heure_debut',
                'heure_fin',
                'nombre_machines_actives',
            )
        }),
        ('📦 Production détaillée', {
            'fields': (
                'production_bobines_finies_kg',
                'production_bobines_semi_finies_kg',
                'dechets_kg',
            )
        }),
        ('📊 Calculs automatiques', {
            'fields': (
                'total_production_kg',
                'taux_dechet_pourcentage',
            ),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': (
                'observations',
                'valide',
                'cree_par'
            )
        })
    )
    
    # ACTIONS PROFESSIONNELLES
    actions = [
        'valider_production', 
        'invalider_production', 
        'export_pdf_fiche_imprimerie_ultra',
        'export_excel_fiche_imprimerie'
    ]
    
    # Métadonnées
    class Media:
        css = {
            'all': ('admin/css/production.css',)
        }
    
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['title'] = '🖨️ Tableau de Production Imprimerie - Vue Compacte'
        return super().changelist_view(request, extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions imprimerie validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider la production"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions imprimerie invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider la production"
    
    # FONCTION D'EXPORT PDF ULTRA PROFESSIONNELLE POUR IMPRIMERIE
    def export_pdf_fiche_imprimerie_ultra(self, request, queryset):
        """Export PDF ULTRA professionnel de la fiche de production imprimerie"""
        title = "FICHE DE PRODUCTION IMPRIMERIE"
        filename = f"Fiche_Production_Imprimerie_UltraPro_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        try:
            return create_ultra_professional_pdf_imprimerie(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur lors de la génération du PDF: {str(e)}", messages.ERROR)
            return self.create_simple_pdf_fallback(title, queryset, filename)
    
    export_pdf_fiche_imprimerie_ultra.short_description = "🏆 Fiche Imprimerie Ultra Pro (PDF)"
    
    def create_simple_pdf_fallback(self, title, queryset, filename):
        """Fallback simple"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, title)
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y = height - 120
        for obj in queryset:
            p.drawString(50, y, f"{obj.date_production} - Bobines finies: {obj.production_bobines_finies_kg}kg")
            y -= 20
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}_simple.pdf"'
        return response
    
    def export_excel_fiche_imprimerie(self, request, queryset):
        """Export Excel professionnel pour imprimerie"""
        title = "FICHE DE PRODUCTION IMPRIMERIE"
        filename = f"Fiche_Production_Imprimerie_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Production Imprimerie"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        purple_header = PatternFill(start_color="6A0DAD", end_color="6A0DAD", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # En-tête
        ws.merge_cells('A1:H1')
        ws['A1'] = "SOFEM-CI - FICHE DE PRODUCTION IMPRIMERIE"
        ws['A1'].font = Font(bold=True, size=16, color="6A0DAD")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Date
        ws.merge_cells('A2:H2')
        ws['A2'] = f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(size=11, color="666666")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws.append([])
        
        # En-têtes tableau
        headers = [
            'Date', 'Heure Début', 'Heure Fin', 'Machines Actives',
            'Bobines Finies (kg)', 'Bobines Semi-Finies (kg)', 'Déchets (kg)', 
            'Total Production (kg)', 'Taux Déchet (%)', 'Statut'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = header_font
            cell.fill = purple_header
            cell.alignment = center_alignment
        
        # Données
        row_num = 5
        for obj in queryset.order_by('date_production'):
            ws.cell(row=row_num, column=1, value=obj.date_production).number_format = 'DD/MM/YYYY'
            ws.cell(row=row_num, column=2, value=obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '')
            ws.cell(row=row_num, column=3, value=obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '')
            ws.cell(row=row_num, column=4, value=int(obj.nombre_machines_actives))
            ws.cell(row=row_num, column=5, value=float(obj.production_bobines_finies_kg))
            ws.cell(row=row_num, column=6, value=float(obj.production_bobines_semi_finies_kg))
            ws.cell(row=row_num, column=7, value=float(obj.dechets_kg))
            ws.cell(row=row_num, column=8, value=float(obj.total_production_kg) if obj.total_production_kg else 0)
            ws.cell(row=row_num, column=9, value=float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0)
            ws.cell(row=row_num, column=10, value="Validé" if obj.valide else "En attente")
            
            row_num += 1
        
        # Formater les colonnes
        for col in ['E', 'F', 'G', 'H']:
            for row in range(5, row_num):
                cell = ws[f'{col}{row}']
                cell.number_format = '#,##0'
        
        # Ajuster largeur
        column_widths = {
            'A': 12,  # Date
            'B': 10,  # Heure Début
            'C': 10,  # Heure Fin
            'D': 12,  # Machines
            'E': 15,  # Bobines Finies
            'F': 15,  # Bobines Semi
            'G': 12,  # Déchets
            'H': 15,  # Total
            'I': 12,  # Taux Déchet
            'J': 12   # Statut
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Sauvegarder
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response
    
    export_excel_fiche_imprimerie.short_description = "📊 Exporter en Excel"

# ==========================================
# ADMINISTRATION PRODUCTION SOUDURE - VERSION ULTRA CORRIGÉE
# ==========================================

@admin.register(ProductionSoudure)
class ProductionSoudureAdmin(admin.ModelAdmin):
    # AFFICHAGE OPTIMISÉ POUR NE PAS DÉBORDER
    list_display = [
        'date_production_short',
        'get_heures_creneau',
        'get_machines_actives',
        'get_bobines_finies',
        'get_bretelles',
        'get_rema',
        'get_batta',
        'get_sac_emballage',
        'get_dechets',
        'get_total_production',
        'get_status_icon',
    ]
    
    list_display_links = ['date_production_short']
    
    list_filter = ['date_production', 'valide']
    search_fields = ['observations']
    
    readonly_fields = [
        'total_production_kg', 
        'total_production_specifique_kg',
        'taux_dechet_pourcentage', 
        'date_creation', 
        'date_modification', 
        'cree_par'
    ]
    
    ordering = ['-date_production']
    
    # Configuration de l'affichage des colonnes
    list_per_page = 50
    list_max_show_all = 200
    
    # FONCTIONS D'AFFICHAGE COMPACT POUR LES COLONNES
    
    def date_production_short(self, obj):
        """Date formatée en format compact"""
        return obj.date_production.strftime('%d/%m')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_heures_creneau(self, obj):
        """Créneau horaire formaté"""
        heure_debut = obj.heure_debut.strftime('%Hh%M') if obj.heure_debut else "--:--"
        heure_fin = obj.heure_fin.strftime('%Hh%M') if obj.heure_fin else "--:--"
        return f"{heure_debut}→{heure_fin}"
    get_heures_creneau.short_description = "🕒 Créneau"
    
    def get_machines_actives(self, obj):
        """Machines actives formatées"""
        return f"{obj.nombre_machines_actives}🔧"
    get_machines_actives.short_description = "🖥️ Machines"
    get_machines_actives.admin_order_field = 'nombre_machines_actives'
    
    def get_bobines_finies(self, obj):
        """Bobines finies formatées"""
        return f"{float(obj.production_bobines_finies_kg):,.0f}✅"
    get_bobines_finies.short_description = "✅ Bobines"
    get_bobines_finies.admin_order_field = 'production_bobines_finies_kg'
    
    def get_bretelles(self, obj):
        """Bretelles formatées"""
        return f"{float(obj.production_bretelles_kg):,.0f}🔗"
    get_bretelles.short_description = "🔗 Bretelles"
    get_bretelles.admin_order_field = 'production_bretelles_kg'
    
    def get_rema(self, obj):
        """Rema formatée"""
        return f"{float(obj.production_rema_kg):,.0f}🔄"
    get_rema.short_description = "🔄 Rema"
    get_rema.admin_order_field = 'production_rema_kg'
    
    def get_batta(self, obj):
        """Batta formatée"""
        return f"{float(obj.production_batta_kg):,.0f}📦"
    get_batta.short_description = "📦 Batta"
    get_batta.admin_order_field = 'production_batta_kg'
    
    def get_sac_emballage(self, obj):
        """Sac d'emballage formaté"""
        return f"{float(obj.production_sac_emballage_kg):,.0f}🛍️"
    get_sac_emballage.short_description = "🛍️ Sac"
    get_sac_emballage.admin_order_field = 'production_sac_emballage_kg'
    
    def get_dechets(self, obj):
        """Déchets formatés"""
        return f"{float(obj.dechets_kg):,.0f}🗑️"
    get_dechets.short_description = "🗑️ Déchets"
    get_dechets.admin_order_field = 'dechets_kg'
    
    def get_total_production(self, obj):
        """Total production formaté"""
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}🏭"
        return "0 🏭"
    get_total_production.short_description = "🏭 Total"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_taux_dechet(self, obj):
        """Taux de déchet formaté avec couleur"""
        if not obj.taux_dechet_pourcentage:
            return "0.0%"
        
        taux = float(obj.taux_dechet_pourcentage)
        taux_formatted = format(taux, '.1f')
        
        if taux <= 5:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
        elif taux <= 10:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
    get_taux_dechet.short_description = "📉 Taux Déchet"
    get_taux_dechet.admin_order_field = 'taux_dechet_pourcentage'
    
    def get_status_icon(self, obj):
        """Icône de statut de validation"""
        if obj.valide:
            return format_html('<span style="color: green;">✅ Validé</span>')
        else:
            return format_html('<span style="color: red;">❌ En attente</span>')
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    # Ajouter un tri personnalisé pour certains champs
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset
    
    # Configuration des champs dans l'édition
    fieldsets = (
        ('📅 Informations de base', {
            'fields': (
                'date_production',
                'heure_debut',
                'heure_fin',
                'nombre_machines_actives',
            )
        }),
        ('📦 Production bobines standards', {
            'fields': (
                'production_bobines_finies_kg',
            )
        }),
        ('🔧 Production spécifique soudure', {
            'fields': (
                'production_bretelles_kg',
                'production_rema_kg',
                'production_batta_kg',
                'production_sac_emballage_kg',
            )
        }),
        ('🗑️ Gestion déchets', {
            'fields': (
                'dechets_kg',
            )
        }),
        ('📊 Calculs automatiques', {
            'fields': (
                'total_production_specifique_kg',
                'total_production_kg',
                'taux_dechet_pourcentage',
            ),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': (
                'observations',
                'valide',
                'cree_par'
            )
        })
    )
    
    # ACTIONS PROFESSIONNELLES
    actions = [
        'valider_production', 
        'invalider_production', 
        'export_pdf_fiche_soudure_ultra',
        'export_excel_fiche_soudure'
    ]
    
    # Métadonnées
    class Media:
        css = {
            'all': ('admin/css/production.css',)
        }
    
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['title'] = '🔧 Tableau de Production Soudure - Vue Compacte'
        return super().changelist_view(request, extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions soudure validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider la production"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions soudure invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider la production"
    
    # ⭐⭐⭐ FONCTION D'EXPORT PDF ULTRA PROFESSIONNELLE POUR SOUDURE ⭐⭐⭐
    def export_pdf_fiche_soudure_ultra(self, request, queryset):
        """Export PDF ULTRA professionnel de la fiche de production soudure"""
        title = "FICHE DE PRODUCTION SOUDURE"
        filename = f"Fiche_Production_Soudure_UltraPro_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # Vérifier qu'il y a des données
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        try:
            # APPEL DE LA FONCTION ULTRA PROFESSIONNELLE SPÉCIFIQUE À LA SOUDURE
            return create_ultra_professional_pdf_soudure(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur lors de la génération du PDF: {str(e)}", messages.ERROR)
            # Fallback vers un PDF simple
            return self.create_simple_pdf_fallback(title, queryset, filename)
    
    export_pdf_fiche_soudure_ultra.short_description = "🏆 Fiche Soudure Ultra Pro (PDF)"
    
    def create_simple_pdf_fallback(self, title, queryset, filename):
        """Fallback simple si la version ultra échoue"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, title)
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y = height - 120
        for obj in queryset:
            p.drawString(50, y, f"{obj.date_production} - Total: {obj.total_production_kg}kg")
            y -= 20
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}_simple.pdf"'
        return response
    
    def export_excel_fiche_soudure(self, request, queryset):
        """Export Excel professionnel pour soudure"""
        title = "FICHE DE PRODUCTION SOUDURE"
        filename = f"Fiche_Production_Soudure_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Production Soudure"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        orange_header = PatternFill(start_color="E65100", end_color="E65100", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # En-tête
        ws.merge_cells('A1:N1')
        ws['A1'] = "SOFEM-CI - FICHE DE PRODUCTION SOUDURE"
        ws['A1'].font = Font(bold=True, size=16, color="E65100")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Date
        ws.merge_cells('A2:N2')
        ws['A2'] = f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(size=11, color="666666")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws.append([])
        
        # En-têtes tableau
        headers = [
            'Date', 'Heure Début', 'Heure Fin', 'Machines Actives',
            'Bobines Finies (kg)', 'Bretelles (kg)', 'Rema (kg)', 
            'Batta (kg)', 'Sac Emballage (kg)', 'Déchets (kg)',
            'Total Spécifique (kg)', 'Total Production (kg)', 
            'Taux Déchet (%)', 'Statut'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = header_font
            cell.fill = orange_header
            cell.alignment = center_alignment
        
        # Données
        row_num = 5
        for obj in queryset.order_by('date_production'):
            ws.cell(row=row_num, column=1, value=obj.date_production).number_format = 'DD/MM/YYYY'
            ws.cell(row=row_num, column=2, value=obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '')
            ws.cell(row=row_num, column=3, value=obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '')
            ws.cell(row=row_num, column=4, value=int(obj.nombre_machines_actives))
            ws.cell(row=row_num, column=5, value=float(obj.production_bobines_finies_kg))
            ws.cell(row=row_num, column=6, value=float(obj.production_bretelles_kg))
            ws.cell(row=row_num, column=7, value=float(obj.production_rema_kg))
            ws.cell(row=row_num, column=8, value=float(obj.production_batta_kg))
            ws.cell(row=row_num, column=9, value=float(obj.production_sac_emballage_kg))
            ws.cell(row=row_num, column=10, value=float(obj.dechets_kg))
            ws.cell(row=row_num, column=11, value=float(obj.total_production_specifique_kg) if obj.total_production_specifique_kg else 0)
            ws.cell(row=row_num, column=12, value=float(obj.total_production_kg) if obj.total_production_kg else 0)
            ws.cell(row=row_num, column=13, value=float(obj.taux_dechet_pourcentage) if obj.taux_dechet_pourcentage else 0)
            ws.cell(row=row_num, column=14, value="Validé" if obj.valide else "En attente")
            
            row_num += 1
        
        # Formater les colonnes numériques
        for col in ['E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']:
            for row in range(5, row_num):
                cell = ws[f'{col}{row}']
                cell.number_format = '#,##0'
        
        for col in ['M']:  # Pourcentages
            for row in range(5, row_num):
                cell = ws[f'{col}{row}']
                cell.number_format = '0.00%'
        
        # Ajuster la largeur des colonnes
        column_widths = {
            'A': 12,  # Date
            'B': 10,  # Heure Début
            'C': 10,  # Heure Fin
            'D': 12,  # Machines
            'E': 12,  # Bobines Finies
            'F': 12,  # Bretelles
            'G': 10,  # Rema
            'H': 10,  # Batta
            'I': 15,  # Sac Emballage
            'J': 12,  # Déchets
            'K': 15,  # Total Spécifique
            'L': 15,  # Total Production
            'M': 12,  # Taux Déchet
            'N': 12   # Statut
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Sauvegarder
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response
    
    export_excel_fiche_soudure.short_description = "📊 Exporter en Excel"
# ==========================================
# ADMINISTRATION PRODUCTION RECYCLAGE
# ==========================================

@admin.register(ProductionRecyclage)
class ProductionRecyclageAdmin(admin.ModelAdmin):
    # AFFICHAGE OPTIMISÉ POUR NE PAS DÉBORDER
    list_display = [
        'date_production_short',
        'get_equipe_compact',
        'get_moulinex',
        'get_broyage',
        'get_bache_noire',
        'get_total_production',
        'get_production_par_moulinex',
        'get_taux_transformation',
        'get_status_icon',
    ]
    
    list_display_links = ['date_production_short', 'get_equipe_compact']
    
    list_filter = ['date_production', 'equipe', 'valide']
    search_fields = ['observations', 'equipe__nom']
    
    readonly_fields = [
        'total_production_kg', 
        'production_par_moulinex',
        'taux_transformation_pourcentage', 
        'date_creation', 
        'date_modification', 
        'cree_par'
    ]
    
    ordering = ['-date_production']
    
    # Configuration de l'affichage des colonnes
    list_per_page = 50
    list_max_show_all = 200
    
    # FONCTIONS D'AFFICHAGE COMPACT POUR LES COLONNES
    
    def date_production_short(self, obj):
        """Date formatée en format compact"""
        return obj.date_production.strftime('%d/%m')
    date_production_short.short_description = "📅 Date"
    date_production_short.admin_order_field = 'date_production'
    
    def get_equipe_compact(self, obj):
        """Équipe formatée en format ultra-compact"""
        if not obj.equipe:
            return "-"
        
        # Formater de manière ultra compacte
        equipe_nom = obj.equipe.nom.lower()
        if "matin" in equipe_nom or "jour" in equipe_nom:
            return f"🟢 M"
        elif "soir" in equipe_nom:
            return f"🔵 S"
        elif "nuit" in equipe_nom:
            return f"🌙 N"
        else:
            # Prendre les premières lettres du nom
            abbreviation = ''.join([word[0].upper() for word in obj.equipe.nom.split()[:2]])
            return f"👥 {abbreviation[:2]}"
    get_equipe_compact.short_description = "👥 Équipe"
    get_equipe_compact.admin_order_field = 'equipe__nom'
    
    def get_moulinex(self, obj):
        """Nombre de moulinex formaté"""
        return f"{obj.nombre_moulinex}⚙️"
    get_moulinex.short_description = "⚙️ Moulinex"
    get_moulinex.admin_order_field = 'nombre_moulinex'
    
    def get_broyage(self, obj):
        """Broyage formaté"""
        return f"{float(obj.production_broyage_kg):,.0f}🔄"
    get_broyage.short_description = "🔄 Broyage"
    get_broyage.admin_order_field = 'production_broyage_kg'
    
    def get_bache_noire(self, obj):
        """Bâche noire formatée"""
        return f"{float(obj.production_bache_noir_kg):,.0f}⬛"
    get_bache_noire.short_description = "⬛ Bâche"
    get_bache_noire.admin_order_field = 'production_bache_noir_kg'
    
    def get_total_production(self, obj):
        """Total production formaté"""
        if obj.total_production_kg:
            return f"{float(obj.total_production_kg):,.0f}🏭"
        return "0 🏭"
    get_total_production.short_description = "🏭 Total"
    get_total_production.admin_order_field = 'total_production_kg'
    
    def get_production_par_moulinex(self, obj):
        """Production par moulinex formatée"""
        if obj.production_par_moulinex:
            return f"{float(obj.production_par_moulinex):,.0f}📊"
        return "0 📊"
    get_production_par_moulinex.short_description = "📊 Prod/Moul"
    get_production_par_moulinex.admin_order_field = 'production_par_moulinex'
    
    def get_taux_transformation(self, obj):
        """Taux de transformation formaté avec couleur"""
        if not obj.taux_transformation_pourcentage:
            return "0.0%"
        
        taux = float(obj.taux_transformation_pourcentage)
        taux_formatted = format(taux, '.1f')
        
        if taux >= 80:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
        elif taux >= 60:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}%</span>', 
                taux_formatted
            )
    get_taux_transformation.short_description = "📈 Taux Transfo"
    get_taux_transformation.admin_order_field = 'taux_transformation_pourcentage'
    
    def get_status_icon(self, obj):
        """Icône de statut de validation"""
        if obj.valide:
            return format_html('<span style="color: green;">✅ Validé</span>')
        else:
            return format_html('<span style="color: red;">❌ En attente</span>')
    get_status_icon.short_description = "📋 Statut"
    get_status_icon.admin_order_field = 'valide'
    
    # Ajouter un tri personnalisé
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('equipe')
    
    # Configuration des champs dans l'édition
    fieldsets = (
        ('📅 Informations de base', {
            'fields': (
                'date_production',
                'equipe',
                'nombre_moulinex',
            )
        }),
        ('♻️ Production recyclage', {
            'fields': (
                'production_broyage_kg',
                'production_bache_noir_kg',
            )
        }),
        ('📊 Calculs automatiques', {
            'fields': (
                'total_production_kg',
                'production_par_moulinex',
                'taux_transformation_pourcentage',
            ),
            'classes': ('collapse',)
        }),
        ('📝 Informations supplémentaires', {
            'fields': (
                'observations',
                'valide',
                'cree_par'
            )
        })
    )
    
    # ACTIONS PROFESSIONNELLES
    actions = [
        'valider_production', 
        'invalider_production', 
        'export_pdf_fiche_recyclage_ultra',
        'export_excel_fiche_recyclage'
    ]
    
    # Métadonnées
    class Media:
        css = {
            'all': ('admin/css/production.css',)
        }
    
    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['title'] = '♻️ Tableau de Production Recyclage - Vue Compacte'
        return super().changelist_view(request, extra_context=extra_context)
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
    
    def valider_production(self, request, queryset):
        updated = queryset.update(valide=True)
        self.message_user(request, f'{updated} productions recyclage validées avec succès.', messages.SUCCESS)
    valider_production.short_description = "✅ Valider la production"
    
    def invalider_production(self, request, queryset):
        updated = queryset.update(valide=False)
        self.message_user(request, f'{updated} productions recyclage invalidées.', messages.WARNING)
    invalider_production.short_description = "❌ Invalider la production"
    
    # ⭐⭐⭐ FONCTION D'EXPORT PDF ULTRA PROFESSIONNELLE POUR RECYCLAGE ⭐⭐⭐
    def export_pdf_fiche_recyclage_ultra(self, request, queryset):
        """Export PDF ULTRA professionnel de la fiche de production recyclage"""
        title = "FICHE DE PRODUCTION RECYCLAGE"
        filename = f"Fiche_Production_Recyclage_UltraPro_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # Vérifier qu'il y a des données
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        try:
            # APPEL DE LA FONCTION ULTRA PROFESSIONNELLE SPÉCIFIQUE AU RECYCLAGE
            return create_ultra_professional_pdf_recyclage(title, queryset, filename)
        except Exception as e:
            self.message_user(request, f"Erreur lors de la génération du PDF: {str(e)}", messages.ERROR)
            # Fallback vers un PDF simple
            return self.create_simple_pdf_fallback(title, queryset, filename)
    
    export_pdf_fiche_recyclage_ultra.short_description = "🏆 Fiche Recyclage Ultra Pro (PDF)"
    
    def create_simple_pdf_fallback(self, title, queryset, filename):
        """Fallback simple si la version ultra échoue"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=landscape(letter))
        width, height = landscape(letter)
        
        p.setFont("Helvetica-Bold", 16)
        p.drawString(50, height - 50, title)
        
        p.setFont("Helvetica", 10)
        p.drawString(50, height - 80, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        y = height - 120
        for obj in queryset:
            p.drawString(50, y, f"{obj.date_production} - {obj.equipe} - Bâche: {obj.production_bache_noir_kg}kg")
            y -= 20
        
        p.save()
        buffer.seek(0)
        
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}_simple.pdf"'
        return response
    
    def export_excel_fiche_recyclage(self, request, queryset):
        """Export Excel professionnel pour recyclage"""
        title = "FICHE DE PRODUCTION RECYCLAGE"
        filename = f"Fiche_Production_Recyclage_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        if not queryset.exists():
            self.message_user(request, "Aucune donnée à exporter.", messages.WARNING)
            return None
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Production Recyclage"
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        green_header = PatternFill(start_color="2E7D32", end_color="2E7D32", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center")
        
        # En-tête
        ws.merge_cells('A1:I1')
        ws['A1'] = "SOFEM-CI - FICHE DE PRODUCTION RECYCLAGE"
        ws['A1'].font = Font(bold=True, size=16, color="2E7D32")
        ws['A1'].alignment = Alignment(horizontal="center", vertical="center")
        
        # Date
        ws.merge_cells('A2:I2')
        ws['A2'] = f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        ws['A2'].font = Font(size=11, color="666666")
        ws['A2'].alignment = Alignment(horizontal="center", vertical="center")
        
        ws.append([])
        
        # En-têtes tableau
        headers = [
            'Date', 'Équipe', 'Nombre Moulinex',
            'Broyage (kg)', 'Bâche Noire (kg)', 'Total Production (kg)',
            'Production/Moulinex', 'Taux Transformation (%)', 'Statut'
        ]
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num, value=header)
            cell.font = header_font
            cell.fill = green_header
            cell.alignment = center_alignment
        
        # Données
        row_num = 5
        for obj in queryset.order_by('date_production', 'equipe'):
            ws.cell(row=row_num, column=1, value=obj.date_production).number_format = 'DD/MM/YYYY'
            ws.cell(row=row_num, column=2, value=str(obj.equipe))
            ws.cell(row=row_num, column=3, value=int(obj.nombre_moulinex))
            ws.cell(row=row_num, column=4, value=float(obj.production_broyage_kg))
            ws.cell(row=row_num, column=5, value=float(obj.production_bache_noir_kg))
            ws.cell(row=row_num, column=6, value=float(obj.total_production_kg) if obj.total_production_kg else 0)
            ws.cell(row=row_num, column=7, value=float(obj.production_par_moulinex) if obj.production_par_moulinex else 0)
            ws.cell(row=row_num, column=8, value=float(obj.taux_transformation_pourcentage) if obj.taux_transformation_pourcentage else 0)
            ws.cell(row=row_num, column=9, value="Validé" if obj.valide else "En attente")
            
            row_num += 1
        
        # Formater les colonnes numériques
        for col in ['D', 'E', 'F', 'G']:
            for row in range(5, row_num):
                cell = ws[f'{col}{row}']
                cell.number_format = '#,##0'
        
        for col in ['H']:  # Pourcentages
            for row in range(5, row_num):
                cell = ws[f'{col}{row}']
                cell.number_format = '0.00%'
        
        # Ajuster la largeur des colonnes
        column_widths = {
            'A': 12,  # Date
            'B': 15,  # Équipe
            'C': 12,  # Moulinex
            'D': 12,  # Broyage
            'E': 12,  # Bâche Noire
            'F': 15,  # Total Production
            'G': 15,  # Prod/Moulinex
            'H': 15,  # Taux Transformation
            'I': 12   # Statut
        }
        
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width
        
        # Sauvegarder
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        return response
    
    export_excel_fiche_recyclage.short_description = "📊 Exporter en Excel"
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