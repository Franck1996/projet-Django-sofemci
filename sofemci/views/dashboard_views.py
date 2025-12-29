"""
Vues des dashboards (principal, direction, etc.)
"""
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
import json

from ..models import Alerte, CustomUser, Machine
from ..formulaires import LoginForm
from .utils_views import (
    get_production_totale_jour,
    get_production_section_jour,
    get_dechets_totaux_jour,
    get_efficacite_moyenne_jour,
    get_machines_stats,
    get_zones_performance,
    get_extrusion_details_jour,
    get_imprimerie_details_jour,
    get_soudure_details_jour,
    get_recyclage_details_jour,
    get_chart_data_for_dashboard,
    get_analytics_kpis,
    get_analytics_table_data,
    get_ca_mensuel,
    get_production_totale_periode,
    calculate_percentage_of_goal,
    get_efficacite_globale_periode,
    get_cout_production_moyen,
    get_performances_sections,
    get_production_par_section,
    get_production_section_periode,
)

@login_required
def dashboard_view(request):
    """Dashboard principal - Page dashboard.html"""
    
    # Récupérer la date depuis le paramètre GET, sinon utiliser aujourd'hui
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    context = {
        'today': selected_date,
        'selected_date': selected_date,
        'is_today': selected_date == timezone.now().date(),
        'production_totale': get_production_totale_jour(selected_date),
        'production_extrusion': get_production_section_jour('extrusion', selected_date),
        'production_imprimerie': get_production_section_jour('imprimerie', selected_date),
        'production_soudure': get_production_section_jour('soudure', selected_date),
        'production_recyclage': get_production_section_jour('recyclage', selected_date),
        'total_dechets': get_dechets_totaux_jour(selected_date),
        'efficacite_moyenne': get_efficacite_moyenne_jour(selected_date),
        'machines_stats': get_machines_stats(),
        'zones_performance': get_zones_performance(selected_date),
        'alertes': Alerte.objects.filter(
            statut__in=['nouveau', 'en_cours']
        ).order_by('-date_creation')[:5],
        'extrusion_stats': get_extrusion_details_jour(selected_date),
        'imprimerie_stats': get_imprimerie_details_jour(selected_date),
        'soudure_stats': get_soudure_details_jour(selected_date),
        'recyclage_stats': get_recyclage_details_jour(selected_date),
        'chart_data': get_chart_data_for_dashboard(),
        'analytics_kpis': get_analytics_kpis(),
        'analytics_table': get_analytics_table_data(),
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def dashboard_direction_view(request):
    """Dashboard direction avec KPIs financiers"""
    if request.user.role not in ['direction', 'admin']:
        messages.error(request, 'Accès refusé. Réservé à la direction.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    context = {
        'ca_mensuel': get_ca_mensuel(debut_mois, today),
        'objectif_ca': Decimal('50000000'),
        'taux_objectif_ca': calculate_percentage_of_goal(get_ca_mensuel(debut_mois, today), Decimal('50000000')),
        'production_mensuelle': get_production_totale_periode(debut_mois, today),
        'objectif_production': Decimal('150000'),
        'taux_objectif_production': calculate_percentage_of_goal(get_production_totale_periode(debut_mois, today), Decimal('150000')),
        'rendement_global': get_efficacite_globale_periode(debut_mois, today),
        'objectif_rendement': Decimal('85'),
        'difference_rendement': get_efficacite_globale_periode(debut_mois, today) - Decimal('85'),
        'cout_production': get_cout_production_moyen(debut_mois, today),
        'objectif_cout': Decimal('850'),
        'difference_cout': get_cout_production_moyen(debut_mois, today) - Decimal('850'),
        'alertes_actives': Alerte.objects.filter(
            type_alerte__in=['critique', 'important'],
            statut__in=['nouveau', 'en_cours']
        ).order_by('-date_creation')[:10],
        'performances_sections': get_performances_sections(debut_mois, today),
        'labels_production': json.dumps(['Extrusion', 'Imprimerie', 'Soudure', 'Recyclage']),
        'data_production': json.dumps(get_production_par_section(debut_mois, today)),
        'periode_debut': debut_mois,
        'periode_fin': today,
    }
    
    return render(request, 'dashboard_direction.html', context)

@login_required
def api_dashboard_data(request):
    """API pour données dashboard temps réel"""
    today = timezone.now().date()
    
    data = {
        'timestamp': timezone.now().isoformat(),
        'production_totale': float(get_production_totale_jour(today)),
        'machines_actives': Machine.objects.filter(etat='actif').count(),
        'alertes_count': Alerte.objects.filter(statut__in=['nouveau', 'en_cours']).count(),
        'efficacite_moyenne': float(get_efficacite_moyenne_jour(today)),
    }
    
    return JsonResponse(data)