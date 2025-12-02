# P:\sofemci\sofemci\sofemci\admin_mixins.py
from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponse
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count
import datetime
from decimal import Decimal
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl import Workbook
import json


class ExportPDFExcelMixin:
    """
    Mixin pour ajouter les fonctionnalités d'export PDF/Excel 
    aux classes ModelAdmin existantes
    """
    
    # Ajouter les URLs d'export
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('export-pdf/<str:period>/', 
                 self.admin_site.admin_view(self.export_pdf_view), 
                 name=f'{self.model._meta.model_name}_export_pdf'),
            path('export-excel/<str:period>/', 
                 self.admin_site.admin_view(self.export_excel_view), 
                 name=f'{self.model._meta.model_name}_export_excel'),
            path('export-custom/', 
                 self.admin_site.admin_view(self.export_custom_view), 
                 name=f'{self.model._meta.model_name}_export_custom'),
        ]
        return custom_urls + urls
    
    # Méthodes pour récupérer les périodes
    def get_period_dates(self, period):
        """Retourne les dates de début et fin selon la période"""
        today = datetime.date.today()
        
        period_map = {
            'today': (today, today),
            'yesterday': (today - datetime.timedelta(days=1), today - datetime.timedelta(days=1)),
            'this_week': (today - datetime.timedelta(days=today.weekday()), 
                         today - datetime.timedelta(days=today.weekday()) + datetime.timedelta(days=6)),
            'last_week': (today - datetime.timedelta(days=today.weekday() + 7), 
                         today - datetime.timedelta(days=today.weekday() + 7) + datetime.timedelta(days=6)),
            'this_month': (today.replace(day=1),
                          today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1),
            'last_month': ((today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1),
                          today.replace(day=1) - datetime.timedelta(days=1)),
            'this_year': (today.replace(month=1, day=1), today.replace(month=12, day=31)),
            'all': (None, None)
        }
        
        return period_map.get(period, (today, today))
    
    def get_period_text(self, period):
        """Retourne le texte descriptif de la période"""
        periods = {
            'today': "Aujourd'hui",
            'yesterday': 'Hier',
            'this_week': 'Cette semaine',
            'last_week': 'Semaine dernière',
            'this_month': 'Ce mois',
            'last_month': 'Mois dernier',
            'this_year': 'Cette année',
            'all': 'Toutes les données'
        }
        return periods.get(period, period)
    
    # Actions d'export pour la liste d'admin
    def export_pdf_today(self, request, queryset):
        """Action pour exporter en PDF (aujourd'hui)"""
        return self.export_pdf_view(request, 'today')
    export_pdf_today.short_description = "📄 Exporter PDF (Aujourd'hui)"
    
    def export_pdf_month(self, request, queryset):
        """Action pour exporter en PDF (ce mois)"""
        return self.export_pdf_view(request, 'this_month')
    export_pdf_month.short_description = "📄 Exporter PDF (Ce mois)"
    
    def export_excel_today(self, request, queryset):
        """Action pour exporter en Excel (aujourd'hui)"""
        return self.export_excel_view(request, 'today')
    export_excel_today.short_description = "📊 Exporter Excel (Aujourd'hui)"
    
    def export_excel_month(self, request, queryset):
        """Action pour exporter en Excel (ce mois)"""
        return self.export_excel_view(request, 'this_month')
    export_excel_month.short_description = "📊 Exporter Excel (Ce mois)"
    
    def export_custom_action(self, request, queryset):
        """Action pour export personnalisé"""
        return redirect(f'/admin/sofemci/{self.model._meta.model_name}/export-custom/')
    export_custom_action.short_description = "⚙️ Export personnalisé"
    
    # Vues d'export
    def export_pdf_view(self, request, period='today'):
        """Vue générique pour exporter en PDF - À surcharger dans chaque admin"""
        raise NotImplementedError("Cette méthode doit être implémentée dans la classe admin")
    
    def export_excel_view(self, request, period='today'):
        """Vue générique pour exporter en Excel - À surcharger dans chaque admin"""
        raise NotImplementedError("Cette méthode doit être implémentée dans la classe admin")
    
    def export_custom_view(self, request):
        """Vue pour export personnalisé avec dates"""
        if request.method == 'POST':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            export_format = request.POST.get('format', 'pdf')
            
            # Formater les dates
            try:
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                start_date = datetime.date.today() - datetime.timedelta(days=30)
                end_date = datetime.date.today()
            
            if export_format == 'pdf':
                return self.export_pdf_custom(request, start_date, end_date)
            else:
                return self.export_excel_custom(request, start_date, end_date)
        
        # Afficher le formulaire
        context = {
            'opts': self.model._meta,
            'title': f'Export personnalisé - {self.model._meta.verbose_name_plural}',
            'has_view_permission': self.has_view_permission(request),
        }
        return render(request, 'admin/production/export_custom.html', context)
    
    def export_pdf_custom(self, request, start_date, end_date):
        """Export PDF avec dates personnalisées - À surcharger"""
        raise NotImplementedError("Cette méthode doit être implémentée dans la classe admin")
    
    def export_excel_custom(self, request, start_date, end_date):
        """Export Excel avec dates personnalisées - À surcharger"""
        raise NotImplementedError("Cette méthode doit être implémentée dans la classe admin")
    
    # Méthodes utilitaires pour les exports
    def create_pdf_response(self, buffer, filename):
        """Crée une réponse HTTP pour un PDF"""
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def create_excel_response(self, buffer, filename):
        """Crée une réponse HTTP pour un Excel"""
        response = HttpResponse(
            buffer,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    def format_decimal(self, value, decimals=2):
        """Formate une valeur Decimal"""
        if value is None:
            return "0.00"
        return f"{value:.{decimals}f}"
    
    def get_excel_styles(self):
        """Retourne les styles Excel de base"""
        return {
            'header_font': Font(bold=True, color="FFFFFF", size=12),
            'header_fill': PatternFill(start_color="366092", end_color="366092", fill_type="solid"),
            'center_alignment': Alignment(horizontal="center", vertical="center"),
            'thin_border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            ),
            'data_font': Font(size=10),
            'currency_format': '#,##0.00',
            'percent_format': '0.00%',
        }