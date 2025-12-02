# sofemci/views/exports.py
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
import csv
import io
from datetime import datetime, timedelta

# Vue principale des exports
@login_required
def page_exports(request):
    """Page principale des exports"""
    return render(request, 'exports/exports.html')

# Exports par période
@login_required
def export_journalier(request):
    """Export journalier"""
    date_str = request.GET.get('date', datetime.now().strftime('%Y-%m-%d'))
    
    # Créer un fichier CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Section', 'Quantité', 'Unité'])
    writer.writerow([date_str, 'Extrusion', '1000', 'kg'])
    writer.writerow([date_str, 'Imprimerie', '500', 'mètres'])
    
    # Retourner le fichier
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="export_journalier_{date_str}.csv"'
    return response

@login_required
def export_hebdomadaire(request):
    """Export hebdomadaire"""
    # Implémentation similaire
    return HttpResponse("Export hebdomadaire")

@login_required
def export_mensuel(request):
    """Export mensuel"""
    return HttpResponse("Export mensuel")

@login_required
def export_periode_personnalisee(request):
    """Export pour période personnalisée"""
    return HttpResponse("Export période personnalisée")

@login_required
def export_comparatif_periodes(request):
    """Export comparatif"""
    return HttpResponse("Export comparatif")

@login_required
def export_global_toutes_sections(request):
    """Export global"""
    return HttpResponse("Export global")

@login_required
def api_previsualisation_export(request):
    """API pour prévisualisation des exports"""
    return JsonResponse({
        'success': True,
        'data': {
            'periodes': ['2024-01-01', '2024-01-02', '2024-01-03'],
            'sections': ['Extrusion', 'Imprimerie', 'Soudure'],
            'totaux': [1000, 500, 300]
        }
    })