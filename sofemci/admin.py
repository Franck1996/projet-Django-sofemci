# sofemci/admin.py
# ADMINISTRATION DJANGO POUR SOFEM-CI - VERSION ULTRA PROFESSIONNELLE

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
from .models.users import CustomUser
from .models.base import Equipe, ZoneExtrusion
from .models.machines import Machine, HistoriqueMachine
from .models.production import ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage
from .models.alerts import Alerte, AlerteIA

# ==========================================
# FONCTION D'EXPORT PDF ULTRA PROFESSIONNELLE
# ==========================================

def create_ultra_professional_pdf(title, queryset, filename):
    """Crée une fiche de production ULTRA professionnelle avec design premium"""
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
    
    # 1. EN-TÊTE CORPORATE BLEU MARINE
    header_style = ParagraphStyle(
        'CorporateHeader',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.white,
        spaceAfter=0.3*cm,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    header_table = Table([[Paragraph(f"<b>{title}</b>", header_style)]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ('TOPPADDING', (0, 0), (0, 0), 10),
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
    
    # 3. SÉPARATEUR DÉCORATIF
    separator = Table([['']], colWidths=[doc.width])
    separator.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 2, colors.HexColor('#003366')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(separator)
    
    # 4. TABLEAU PRINCIPAL - DESIGN ULTRA PRO
    headers_row1 = [
        'INFORMATIONS DE PRODUCTION', '', '', '', '', '',
        'ANALYSE DE PRODUCTION (kg)', '', '', '', '', ''
    ]
    
    headers_row2 = [
        'Date', 'Zone', 'Équipe', 'Matière\nPremière (kg)', 'Machines\nActives', 'Personnel\nOpérationnel',
        'Bobines', 'Produits\nFinis', 'Semi-\nFinis', 'Déchets', 'Total\nProduction', 'Rendement\n(%)'
    ]
    
    # Préparer les données
    table_data = [headers_row1, headers_row2]
    
    for idx, obj in enumerate(queryset.order_by('date_production', 'zone')):
        rendement = float(obj.rendement_pourcentage) if obj.rendement_pourcentage else 0
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            str(obj.zone),
            str(obj.equipe),
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
    
    # Largeurs des colonnes optimisées
    col_widths = [2.5*cm, 3.2*cm, 3.5*cm, 2.2*cm, 1.8*cm, 2.0*cm, 
                  2.0*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.2*cm, 2.0*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    # STYLE ULTRA PROFESSIONNEL
    table.setStyle(TableStyle([
        # Fusion des en-têtes principaux
        ('SPAN', (0, 0), (5, 0)),   # Informations de production
        ('SPAN', (6, 0), (11, 0)),  # Analyse de production
        
        # En-tête 1 - Bleu marine
        ('BACKGROUND', (0, 0), (5, 1), colors.HexColor('#003366')),
        ('TEXTCOLOR', (0, 0), (5, 1), colors.white),
        ('FONTNAME', (0, 0), (5, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (5, 0), 12),
        ('FONTSIZE', (0, 1), (5, 1), 9),
        
        # En-tête 2 - Vert professionnel
        ('BACKGROUND', (6, 0), (11, 1), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (6, 0), (11, 1), colors.white),
        ('FONTNAME', (6, 0), (11, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (6, 0), (11, 0), 12),
        ('FONTSIZE', (6, 1), (11, 1), 9),
        
        # Alignement et padding
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 2), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 8),
        
        # Bordures professionnelles
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (-1, 1), 1.5, colors.HexColor('#003366')),
        
        # Ligne de séparation
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.white),
        
        # Alternance des couleurs des lignes
        ('ROWBACKGROUNDS', (2, 2), (-1, -1), 
         [colors.white, colors.HexColor('#F8F9FA')]),
        
        # Mise en valeur spéciale
        ('FONTNAME', (10, 2), (10, -1), 'Helvetica-Bold'),  # Total Production
        ('TEXTCOLOR', (10, 2), (10, -1), colors.HexColor('#2E7D32')),
        ('FONTNAME', (11, 2), (11, -1), 'Helvetica-Bold'),  # Rendement
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 5. DASHBOARD DES INDICATEURS CLÉS
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
                                             textColor=colors.HexColor('#003366'),
                                             spaceAfter=0.5*cm,
                                             fontName='Helvetica-Bold')))
        
        # Cartes KPI en 2x2
        kpi_data = [
            ["PRODUCTION TOTALE", f"{total_production:,.0f} kg", "🎯", '#2196F3'],
            ["MATIÈRE PREMIÈRE", f"{total_matiere:,.0f} kg", "⚙️", '#FF9800'],
            ["RENDEMENT MOYEN", f"{avg_rendement:.1f}%", "📈", '#2E7D32'],
            ["DÉCHETS TOTAUX", f"{total_dechets:,.0f} kg", "🗑️", '#D32F2F']
        ]
        
        kpi_table_data = []
        for i in range(0, 4, 2):
            row = []
            for j in range(2):
                if i + j < 4:
                    kpi = kpi_data[i + j]
                    cell_content = f"""
                    <para alignment='center'>
                    <font name='Helvetica' size=9 color='#666666'>{kpi[0]}</font><br/>
                    <font name='Helvetica-Bold' size=14 color='{kpi[3]}'>{kpi[2]} {kpi[1]}</font>
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
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FA')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#003366')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 6. ANALYSE AUTOMATIQUE
        analysis_text = "<b>🔍 ANALYSE AUTOMATIQUE :</b><br/>"
        
        if avg_rendement >= 85:
            analysis_text += "✅ <b>Rendement excellent</b> - Performance optimale de production<br/>"
        elif avg_rendement >= 70:
            analysis_text += "⚠️ <b>Rendement acceptable</b> - Possibilité d'amélioration<br/>"
        else:
            analysis_text += "❌ <b>Rendement faible</b> - Nécessite une investigation approfondie<br/>"
            
        if total_dechets / (total_production + 0.001) * 100 > 15:
            analysis_text += "❌ <b>Taux de déchet élevé</b> - Optimisation nécessaire des processus"
        else:
            analysis_text += "✅ <b>Gestion des déchets optimale</b> - Processus bien maîtrisé"
        
        analysis_para = Paragraph(analysis_text, ParagraphStyle(
            'Analysis', 
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            backColor=colors.HexColor('#FFF9C4'),
            borderPadding=10,
            borderColor=colors.HexColor('#FFD54F'),
            borderWidth=1
        ))
        elements.append(analysis_para)
    
    # 7. PIED DE PAGE CORPORATE
    elements.append(Spacer(1, 1.2*cm))
    
    # Ligne de séparation
    footer_separator = Table([['']], colWidths=[doc.width])
    footer_separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor('#003366')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 5),
    ]))
    elements.append(footer_separator)
    
    # Informations footer
    footer_text = f"""
    <b>SOFEM-CI</b> | Usine de Production d'Emballage |  Abidjan, Côte d'Ivoire<br/>
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

def create_ultra_professional_pdf_imprimerie(title, queryset, filename):
    """Crée une fiche de production imprimerie ULTRA professionnelle avec design premium"""
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
    
    # 1. EN-TÊTE CORPORATE VIOLET (IMPRIMERIE)
    header_style = ParagraphStyle(
        'ImprimerieHeader',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.white,
        spaceAfter=0.3*cm,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    header_table = Table([[Paragraph(f"<b>{title}</b>", header_style)]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#6A0DAD')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ('TOPPADDING', (0, 0), (0, 0), 10),
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
    
    # 3. SÉPARATEUR DÉCORATIF
    separator = Table([['']], colWidths=[doc.width])
    separator.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 2, colors.HexColor('#6A0DAD')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(separator)
    
    # 4. TABLEAU PRINCIPAL - DESIGN ULTRA PRO POUR IMPRIMERIE
    headers_row1 = [
        'INFORMATIONS DE BASE', '', '', '',
        'PRODUCTION BOBINES (kg)', '', '', ''
    ]
    
    headers_row2 = [
        'Date', 'Heure Début', 'Heure Fin', 'Machines Actives',
        'Produits Finis', 'Semi-Finis', 'Déchets', 'Total Production'
    ]
    
    # Préparer les données
    table_data = [headers_row1, headers_row2]
    
    for idx, obj in enumerate(queryset.order_by('date_production')):
        heure_debut = obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '--:--'
        heure_fin = obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '--:--'
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            heure_debut,
            heure_fin,
            str(obj.nombre_machines_actives),
            f"{float(obj.production_bobines_finies_kg):,.0f}",
            f"{float(obj.production_bobines_semi_finies_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0"
        ]
        table_data.append(row_data)
    
    # Largeurs des colonnes optimisées
    col_widths = [2.5*cm, 2.0*cm, 2.0*cm, 2.0*cm, 3.0*cm, 3.0*cm, 2.5*cm, 3.0*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    # STYLE ULTRA PROFESSIONNEL IMPRIMERIE
    table.setStyle(TableStyle([
        # Fusion des en-têtes principaux
        ('SPAN', (0, 0), (3, 0)),   # Informations de base
        ('SPAN', (4, 0), (7, 0)),   # Production bobines
        
        # En-tête 1 - Violet imprimerie
        ('BACKGROUND', (0, 0), (3, 1), colors.HexColor('#6A0DAD')),
        ('TEXTCOLOR', (0, 0), (3, 1), colors.white),
        ('FONTNAME', (0, 0), (3, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (3, 0), 12),
        ('FONTSIZE', (0, 1), (3, 1), 9),
        
        # En-tête 2 - Violet plus clair
        ('BACKGROUND', (4, 0), (7, 1), colors.HexColor('#9C27B0')),
        ('TEXTCOLOR', (4, 0), (7, 1), colors.white),
        ('FONTNAME', (4, 0), (7, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, 0), (7, 0), 12),
        ('FONTSIZE', (4, 1), (7, 1), 9),
        
        # Alignement et padding
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 2), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 8),
        
        # Bordures professionnelles
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (-1, 1), 1.5, colors.HexColor('#6A0DAD')),
        
        # Ligne de séparation
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.white),
        
        # Alternance des couleurs des lignes
        ('ROWBACKGROUNDS', (2, 2), (-1, -1), 
         [colors.white, colors.HexColor('#F3E5F5')]),
        
        # Mise en valeur spéciale
        ('FONTNAME', (7, 2), (7, -1), 'Helvetica-Bold'),  # Total Production
        ('TEXTCOLOR', (7, 2), (7, -1), colors.HexColor('#6A0DAD')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 5. DASHBOARD DES INDICATEURS CLÉS
    if queryset:
        # Calcul des indicateurs
        total_finis = sum(float(obj.production_bobines_finies_kg) for obj in queryset)
        total_semi = sum(float(obj.production_bobines_semi_finies_kg) for obj in queryset)
        total_dechets = sum(float(obj.dechets_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        
        taux_dechets = [float(obj.taux_dechet_pourcentage) for obj in queryset if obj.taux_dechet_pourcentage]
        avg_taux_dechet = sum(taux_dechets) / len(taux_dechets) if taux_dechets else 0
        
        # Titre section KPI
        elements.append(Paragraph("📊 DASHBOARD DES INDICATEURS CLÉS - IMPRIMERIE", 
                                ParagraphStyle('KPITitle', fontSize=14, 
                                             textColor=colors.HexColor('#6A0DAD'),
                                             spaceAfter=0.5*cm,
                                             fontName='Helvetica-Bold')))
        
        # Cartes KPI en 2x2
        kpi_data = [
            ["BOBINES FINIES", f"{total_finis:,.0f} kg", "✅", '#6A0DAD'],
            ["BOBINES SEMI", f"{total_semi:,.0f} kg", "🔄", '#9C27B0'],
            ["PRODUCTION TOTALE", f"{total_production:,.0f} kg", "🏭", '#2196F3'],
            ["TAUX DÉCHET MOYEN", f"{avg_taux_dechet:.1f}%", "🗑️", '#FF9800']
        ]
        
        kpi_table_data = []
        for i in range(0, 4, 2):
            row = []
            for j in range(2):
                if i + j < 4:
                    kpi = kpi_data[i + j]
                    cell_content = f"""
                    <para alignment='center'>
                    <font name='Helvetica' size=9 color='#666666'>{kpi[0]}</font><br/>
                    <font name='Helvetica-Bold' size=14 color='{kpi[3]}'>{kpi[2]} {kpi[1]}</font>
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
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3E5F5')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1C4E9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#6A0DAD')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 6. ANALYSE AUTOMATIQUE
        analysis_text = "<b>🔍 ANALYSE AUTOMATIQUE DE L'IMPRIMERIE :</b><br/>"
        
        if avg_taux_dechet <= 5:
            analysis_text += "✅ <b>Excellent contrôle des déchets</b> - Processus d'impression optimal<br/>"
        elif avg_taux_dechet <= 10:
            analysis_text += "⚠️ <b>Contrôle des déchets acceptable</b> - Peut être amélioré<br/>"
        else:
            analysis_text += "❌ <b>Taux de déchet trop élevé</b> - Nécessite optimisation immédiate<br/>"
            
        if total_finis > total_semi:
            analysis_text += "✅ <b>Priorité sur produits finis</b> - Stratégie de production efficace"
        else:
            analysis_text += "⚠️ <b>Trop de semi-finis</b> - Optimiser le flux de production"
        
        analysis_para = Paragraph(analysis_text, ParagraphStyle(
            'Analysis', 
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            backColor=colors.HexColor('#F3E5F5'),
            borderPadding=10,
            borderColor=colors.HexColor('#D1C4E9'),
            borderWidth=1
        ))
        elements.append(analysis_para)
    
    # 7. PIED DE PAGE CORPORATE
    elements.append(Spacer(1, 1.2*cm))
    
    # Ligne de séparation
    footer_separator = Table([['']], colWidths=[doc.width])
    footer_separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor('#6A0DAD')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 5),
    ]))
    elements.append(footer_separator)
    
    # Informations footer
    footer_text = f"""
    <b>SOFEM-CI - SECTION IMPRIMERIE</b> | Usine de Production d'Emballage | Abidjan, Côte d'Ivoire<br/>
    <i>Document confidentiel - Réf: IMPR-{datetime.now().strftime('%Y%m%d')}-001 | Page 1/1</i>
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


def create_ultra_professional_pdf_soudure(title, queryset, filename):
    """Crée une fiche de production soudure ULTRA professionnelle avec design premium"""
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
    
    # 1. EN-TÊTE CORPORATE ORANGE (SOUDURE)
    header_style = ParagraphStyle(
        'SoudureHeader',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.white,
        spaceAfter=0.3*cm,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    header_table = Table([[Paragraph(f"<b>{title}</b>", header_style)]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#E65100')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ('TOPPADDING', (0, 0), (0, 0), 10),
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
    
    # 3. SÉPARATEUR DÉCORATIF
    separator = Table([['']], colWidths=[doc.width])
    separator.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 2, colors.HexColor('#E65100')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(separator)
    
    # 4. TABLEAU PRINCIPAL - DESIGN ULTRA PRO POUR SOUDURE
    headers_row1 = [
        'INFORMATIONS DE BASE', '', '', '',
        'PRODUCTION STANDARD', '',
        'PRODUCTION SPÉCIFIQUE (kg)', '', '', '', '',
        'ANALYSE'
    ]
    
    headers_row2 = [
        'Date', 'Heure Début', 'Heure Fin', 'Machines',
        'Bobines Finies', 'Déchets',
        'Bretelles', 'Rema', 'Batta', 'Sac Emballage', 'Total Spécifique',
        'Total Général'
    ]
    
    # Préparer les données
    table_data = [headers_row1, headers_row2]
    
    for idx, obj in enumerate(queryset.order_by('date_production')):
        heure_debut = obj.heure_debut.strftime('%H:%M') if obj.heure_debut else '--:--'
        heure_fin = obj.heure_fin.strftime('%H:%M') if obj.heure_fin else '--:--'
        total_specifique = obj.total_production_specifique_kg or 0
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            heure_debut,
            heure_fin,
            str(obj.nombre_machines_actives),
            f"{float(obj.production_bobines_finies_kg):,.0f}",
            f"{float(obj.dechets_kg):,.0f}",
            f"{float(obj.production_bretelles_kg):,.0f}",
            f"{float(obj.production_rema_kg):,.0f}",
            f"{float(obj.production_batta_kg):,.0f}",
            f"{float(obj.production_sac_emballage_kg):,.0f}",
            f"{float(total_specifique):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0"
        ]
        table_data.append(row_data)
    
    # Largeurs des colonnes optimisées
    col_widths = [2.2*cm, 1.8*cm, 1.8*cm, 1.6*cm, 2.0*cm, 1.6*cm, 
                  1.8*cm, 1.6*cm, 1.6*cm, 2.0*cm, 2.2*cm, 2.0*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    # STYLE ULTRA PROFESSIONNEL SOUDURE
    table.setStyle(TableStyle([
        # Fusion des en-têtes principaux
        ('SPAN', (0, 0), (3, 0)),   # Informations de base
        ('SPAN', (4, 0), (5, 0)),   # Production standard
        ('SPAN', (6, 0), (10, 0)),  # Production spécifique
        ('SPAN', (11, 0), (11, 1)), # Analyse
        
        # En-tête 1 - Orange soudure
        ('BACKGROUND', (0, 0), (3, 1), colors.HexColor('#E65100')),
        ('TEXTCOLOR', (0, 0), (3, 1), colors.white),
        ('FONTNAME', (0, 0), (3, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (3, 0), 10),
        ('FONTSIZE', (0, 1), (3, 1), 8),
        
        # En-tête 2 - Orange moyen
        ('BACKGROUND', (4, 0), (5, 1), colors.HexColor('#FF9800')),
        ('TEXTCOLOR', (4, 0), (5, 1), colors.white),
        ('FONTNAME', (4, 0), (5, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (4, 0), (5, 0), 10),
        ('FONTSIZE', (4, 1), (5, 1), 8),
        
        # En-tête 3 - Orange clair
        ('BACKGROUND', (6, 0), (10, 1), colors.HexColor('#FFB74D')),
        ('TEXTCOLOR', (6, 0), (10, 1), colors.white),
        ('FONTNAME', (6, 0), (10, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (6, 0), (10, 0), 10),
        ('FONTSIZE', (6, 1), (10, 1), 8),
        
        # En-tête 4 - Analyse
        ('BACKGROUND', (11, 0), (11, 1), colors.HexColor('#795548')),
        ('TEXTCOLOR', (11, 0), (11, 1), colors.white),
        ('FONTNAME', (11, 0), (11, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (11, 0), (11, 0), 10),
        ('FONTSIZE', (11, 1), (11, 1), 8),
        
        # Alignement et padding
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 2), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 6),
        
        # Bordures professionnelles
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (-1, 1), 1.5, colors.HexColor('#E65100')),
        
        # Ligne de séparation
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.white),
        
        # Alternance des couleurs des lignes
        ('ROWBACKGROUNDS', (2, 2), (-1, -1), 
         [colors.white, colors.HexColor('#FFF3E0')]),
        
        # Mise en valeur spéciale
        ('FONTNAME', (11, 2), (11, -1), 'Helvetica-Bold'),  # Total Général
        ('TEXTCOLOR', (11, 2), (11, -1), colors.HexColor('#E65100')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 5. DASHBOARD DES INDICATEURS CLÉS
    if queryset:
        # Calcul des indicateurs
        total_bobines = sum(float(obj.production_bobines_finies_kg) for obj in queryset)
        total_bretelles = sum(float(obj.production_bretelles_kg) for obj in queryset)
        total_rema = sum(float(obj.production_rema_kg) for obj in queryset)
        total_batta = sum(float(obj.production_batta_kg) for obj in queryset)
        total_sac = sum(float(obj.production_sac_emballage_kg) for obj in queryset)
        total_dechets = sum(float(obj.dechets_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        
        # Titre section KPI
        elements.append(Paragraph("📊 DASHBOARD DES INDICATEURS CLÉS - SOUDURE", 
                                ParagraphStyle('KPITitle', fontSize=14, 
                                             textColor=colors.HexColor('#E65100'),
                                             spaceAfter=0.5*cm,
                                             fontName='Helvetica-Bold')))
        
        # Cartes KPI en 2x2
        kpi_data = [
            ["PRODUCTION TOTALE", f"{total_production:,.0f} kg", "🏭", '#E65100'],
            ["BOBINES FINIES", f"{total_bobines:,.0f} kg", "✅", '#FF9800'],
            ["BRETELLES", f"{total_bretelles:,.0f} kg", "🔗", '#FFB74D'],
            ["DÉCHETS TOTAUX", f"{total_dechets:,.0f} kg", "🗑️", '#795548']
        ]
        
        kpi_table_data = []
        for i in range(0, 4, 2):
            row = []
            for j in range(2):
                if i + j < 4:
                    kpi = kpi_data[i + j]
                    cell_content = f"""
                    <para alignment='center'>
                    <font name='Helvetica' size=9 color='#666666'>{kpi[0]}</font><br/>
                    <font name='Helvetica-Bold' size=14 color='{kpi[3]}'>{kpi[2]} {kpi[1]}</font>
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
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF3E0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#FFCC80')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E65100')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 6. ANALYSE AUTOMATIQUE
        analysis_text = "<b>🔍 ANALYSE AUTOMATIQUE DE LA SOUDURE :</b><br/>"
        
        # Analyse des priorités de production
        if total_bretelles > total_rema and total_bretelles > total_batta:
            analysis_text += "✅ <b>Priorité sur les bretelles</b> - Stratégie commerciale optimale<br/>"
        elif total_rema > total_bretelles and total_rema > total_batta:
            analysis_text += "⚠️ <b>Priorité sur Rema-Plastique</b> - Vérifier la demande marché<br/>"
        else:
            analysis_text += "ℹ️ <b>Production équilibrée</b> - Bonne diversification<br/>"
            
        # Analyse déchets
        taux_dechet_moyen = (total_dechets / (total_production + 0.001)) * 100
        if taux_dechet_moyen <= 8:
            analysis_text += "✅ <b>Faible taux de déchet</b> - Processus de soudure efficace"
        else:
            analysis_text += "⚠️ <b>Taux de déchet élevé</b> - Optimiser les paramètres de soudure"
        
        analysis_para = Paragraph(analysis_text, ParagraphStyle(
            'Analysis', 
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            backColor=colors.HexColor('#FFF3E0'),
            borderPadding=10,
            borderColor=colors.HexColor('#FFCC80'),
            borderWidth=1
        ))
        elements.append(analysis_para)
    
    # 7. PIED DE PAGE CORPORATE
    elements.append(Spacer(1, 1.2*cm))
    
    # Ligne de séparation
    footer_separator = Table([['']], colWidths=[doc.width])
    footer_separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor('#E65100')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 5),
    ]))
    elements.append(footer_separator)
    
    # Informations footer
    footer_text = f"""
    <b>SOFEM-CI - SECTION SOUDURE</b> | Usine de Production d'Emballage | Abidjan, Côte d'Ivoire<br/>
    <i>Document confidentiel - Réf: SOU-{datetime.now().strftime('%Y%m%d')}-001 | Page 1/1</i>
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


def create_ultra_professional_pdf_recyclage(title, queryset, filename):
    """Crée une fiche de production recyclage ULTRA professionnelle avec design premium"""
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
    
    # 1. EN-TÊTE CORPORATE VERT (RECYCLAGE)
    header_style = ParagraphStyle(
        'RecyclageHeader',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.white,
        spaceAfter=0.3*cm,
        alignment=0,
        fontName='Helvetica-Bold'
    )
    
    header_table = Table([[Paragraph(f"<b>{title}</b>", header_style)]], colWidths=[doc.width])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
        ('VALIGN', (0, 0), (0, 0), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 20),
        ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ('TOPPADDING', (0, 0), (0, 0), 10),
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
    
    # 3. SÉPARATEUR DÉCORATIF
    separator = Table([['']], colWidths=[doc.width])
    separator.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (0, 0), 2, colors.HexColor('#2E7D32')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 10),
    ]))
    elements.append(separator)
    
    # 4. TABLEAU PRINCIPAL - DESIGN ULTRA PRO POUR RECYCLAGE
    headers_row1 = [
        'INFORMATIONS DE BASE', '', '',
        'PRODUCTION RECYCLAGE (kg)', '', '',
        'INDICATEURS DE PERFORMANCE'
    ]
    
    headers_row2 = [
        'Date', 'Équipe', 'Moulinex',
        'Broyage', 'Bâche Noire', 'Total Production',
        'Prod/Moulinex', 'Taux Transformation'
    ]
    
    # Préparer les données
    table_data = [headers_row1, headers_row2]
    
    for idx, obj in enumerate(queryset.order_by('date_production', 'equipe')):
        taux_transfo = obj.taux_transformation_pourcentage or 0
        prod_par_moulinex = obj.production_par_moulinex or 0
        
        row_data = [
            obj.date_production.strftime('%d/%m/%Y'),
            str(obj.equipe)[:10],  # Limiter la longueur
            str(obj.nombre_moulinex),
            f"{float(obj.production_broyage_kg):,.0f}",
            f"{float(obj.production_bache_noir_kg):,.0f}",
            f"{float(obj.total_production_kg):,.0f}" if obj.total_production_kg else "0",
            f"{float(prod_par_moulinex):,.0f}",
            f"{float(taux_transfo):.1f}%"
        ]
        table_data.append(row_data)
    
    # Largeurs des colonnes optimisées
    col_widths = [2.5*cm, 3.0*cm, 2.0*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=2)
    
    # STYLE ULTRA PROFESSIONNEL RECYCLAGE
    table.setStyle(TableStyle([
        # Fusion des en-têtes principaux
        ('SPAN', (0, 0), (2, 0)),   # Informations de base
        ('SPAN', (3, 0), (5, 0)),   # Production recyclage
        ('SPAN', (6, 0), (7, 0)),   # Indicateurs de performance
        
        # En-tête 1 - Vert recyclage
        ('BACKGROUND', (0, 0), (2, 1), colors.HexColor('#2E7D32')),
        ('TEXTCOLOR', (0, 0), (2, 1), colors.white),
        ('FONTNAME', (0, 0), (2, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (2, 0), 12),
        ('FONTSIZE', (0, 1), (2, 1), 9),
        
        # En-tête 2 - Vert moyen
        ('BACKGROUND', (3, 0), (5, 1), colors.HexColor('#43A047')),
        ('TEXTCOLOR', (3, 0), (5, 1), colors.white),
        ('FONTNAME', (3, 0), (5, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (3, 0), (5, 0), 12),
        ('FONTSIZE', (3, 1), (5, 1), 9),
        
        # En-tête 3 - Vert clair
        ('BACKGROUND', (6, 0), (7, 1), colors.HexColor('#66BB6A')),
        ('TEXTCOLOR', (6, 0), (7, 1), colors.white),
        ('FONTNAME', (6, 0), (7, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (6, 0), (7, 0), 12),
        ('FONTSIZE', (6, 1), (7, 1), 9),
        
        # Alignement et padding
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 2), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 2), (-1, -1), 8),
        
        # Bordures professionnelles
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E0E0E0')),
        ('BOX', (0, 0), (-1, 1), 1.5, colors.HexColor('#2E7D32')),
        
        # Ligne de séparation
        ('LINEBELOW', (0, 1), (-1, 1), 1, colors.white),
        
        # Alternance des couleurs des lignes
        ('ROWBACKGROUNDS', (2, 2), (-1, -1), 
         [colors.white, colors.HexColor('#E8F5E9')]),
        
        # Mise en valeur spéciale
        ('FONTNAME', (5, 2), (5, -1), 'Helvetica-Bold'),  # Total Production
        ('TEXTCOLOR', (5, 2), (5, -1), colors.HexColor('#2E7D32')),
        ('FONTNAME', (7, 2), (7, -1), 'Helvetica-Bold'),  # Taux Transformation
        ('TEXTCOLOR', (7, 2), (7, -1), colors.HexColor('#43A047')),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.8*cm))
    
    # 5. DASHBOARD DES INDICATEURS CLÉS
    if queryset:
        # Calcul des indicateurs
        total_broyage = sum(float(obj.production_broyage_kg) for obj in queryset)
        total_bache = sum(float(obj.production_bache_noir_kg) for obj in queryset)
        total_production = sum(float(obj.total_production_kg) for obj in queryset if obj.total_production_kg)
        total_moulinex = sum(obj.nombre_moulinex for obj in queryset)
        
        taux_transfo_list = [float(obj.taux_transformation_pourcentage) for obj in queryset if obj.taux_transformation_pourcentage]
        avg_taux_transfo = sum(taux_transfo_list) / len(taux_transfo_list) if taux_transfo_list else 0
        
        prod_par_moulinex_list = [float(obj.production_par_moulinex) for obj in queryset if obj.production_par_moulinex]
        avg_prod_par_moulinex = sum(prod_par_moulinex_list) / len(prod_par_moulinex_list) if prod_par_moulinex_list else 0
        
        # Titre section KPI
        elements.append(Paragraph("📊 DASHBOARD DES INDICATEURS CLÉS - RECYCLAGE", 
                                ParagraphStyle('KPITitle', fontSize=14, 
                                             textColor=colors.HexColor('#2E7D32'),
                                             spaceAfter=0.5*cm,
                                             fontName='Helvetica-Bold')))
        
        # Cartes KPI en 2x2
        kpi_data = [
            ["BROYAGE TOTAL", f"{total_broyage:,.0f} kg", "🔄", '#2E7D32'],
            ["BÂCHE NOIRE", f"{total_bache:,.0f} kg", "⬛", '#43A047'],
            ["PROD/MOULINEX", f"{avg_prod_par_moulinex:,.0f} kg", "📊", '#66BB6A'],
            ["TAUX TRANSFO", f"{avg_taux_transfo:.1f}%", "♻️", '#4CAF50']
        ]
        
        kpi_table_data = []
        for i in range(0, 4, 2):
            row = []
            for j in range(2):
                if i + j < 4:
                    kpi = kpi_data[i + j]
                    cell_content = f"""
                    <para alignment='center'>
                    <font name='Helvetica' size=9 color='#666666'>{kpi[0]}</font><br/>
                    <font name='Helvetica-Bold' size=14 color='{kpi[3]}'>{kpi[2]} {kpi[1]}</font>
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
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#E8F5E9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#C8E6C9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2E7D32')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 0.8*cm))
        
        # 6. ANALYSE AUTOMATIQUE
        analysis_text = "<b>🔍 ANALYSE AUTOMATIQUE DU RECYCLAGE :</b><br/>"
        
        if avg_taux_transfo >= 75:
            analysis_text += "✅ <b>Excellente transformation</b> - Processus de recyclage optimal<br/>"
        elif avg_taux_transfo >= 50:
            analysis_text += "⚠️ <b>Transformation moyenne</b> - Possibilité d'amélioration<br/>"
        else:
            analysis_text += "❌ <b>Faible transformation</b> - Nécessite optimisation urgente<br/>"
            
        if avg_prod_par_moulinex >= 500:
            analysis_text += "✅ <b>Haute productivité par moulinex</b> - Utilisation optimale des ressources"
        elif avg_prod_par_moulinex >= 300:
            analysis_text += "⚠️ <b>Productivité acceptable</b> - Peut être améliorée"
        else:
            analysis_text += "❌ <b>Productivité faible</b> - Vérifier l'efficacité des équipements"
        
        analysis_para = Paragraph(analysis_text, ParagraphStyle(
            'Analysis', 
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            backColor=colors.HexColor('#E8F5E9'),
            borderPadding=10,
            borderColor=colors.HexColor('#C8E6C9'),
            borderWidth=1
        ))
        elements.append(analysis_para)
    
    # 7. PIED DE PAGE CORPORATE
    elements.append(Spacer(1, 1.2*cm))
    
    # Ligne de séparation
    footer_separator = Table([['']], colWidths=[doc.width])
    footer_separator.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor('#2E7D32')),
        ('BOTTOMPADDING', (0, 0), (0, 0), 5),
    ]))
    elements.append(footer_separator)
    
    # Informations footer
    footer_text = f"""
    <b>SOFEM-CI - SECTION RECYCLAGE</b> | Usine de Production d'Emballage | Abidjan, Côte d'Ivoire<br/>
    <i>Document confidentiel - Réf: RECY-{datetime.now().strftime('%Y%m%d')}-001 | Page 1/1</i>
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
        
        # CORRECTION ICI : Utiliser format_html correctement
        if rendement >= 85:
            return format_html('<span style="color: green; font-weight: bold;">{}%</span>', 
                              format(rendement, '.1f'))
        elif rendement >= 70:
            return format_html('<span style="color: orange; font-weight: bold;">{}%</span>', 
                              format(rendement, '.1f'))
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}%</span>', 
                              format(rendement, '.1f'))
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
        
        if taux <= 5:
            return format_html('<span style="color: green; font-weight: bold;">{}%</span>', 
                              format(taux, '.1f'))
        elif taux <= 10:
            return format_html('<span style="color: orange; font-weight: bold;">{}%</span>', 
                              format(taux, '.1f'))
        else:
            return format_html('<span style="color: red; font-weight: bold;">{}%</span>', 
                              format(taux, '.1f'))
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
    
    actions = ['valider_production', 'invalider_production']
    
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
    
    actions = ['valider_production', 'invalider_production']
    
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