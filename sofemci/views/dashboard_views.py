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
def get_user_access_config(user_role):
    """Détermine quelles sections afficher selon le rôle"""
    # Règles 1: CHEF_RECYCL, CHEF_IMPRIM, CHEF_SOUD -> seulement Autres Sections
    if user_role in ['CHEF_RECYCL', 'CHEF_IMPRIM', 'CHEF_SOUD']:
        return {
            'show_extrusion': False,
            'show_other_sections': True,
            'show_admin_access': False,
            'title': '🏭 Autres Sections'
        }
    
    # Règles 2: CHEF_EXT1 à CHEF_EXT5 -> seulement Extrusion
    elif user_role in ['CHEF_EXT1', 'CHEF_EXT2', 'CHEF_EXT3', 'CHEF_EXT4', 'CHEF_EXT5']:
        return {
            'show_extrusion': True,
            'show_other_sections': False,
            'show_admin_access': False,
            'title': '🔧 Extrusion'
        }
    
    # Règles 3: DIRECTION -> tout + admin lecture seule
    elif user_role == 'DIRECTION':
        return {
            'show_extrusion': True,
            'show_other_sections': True,
            'show_admin_access': True,
            'is_direction': True,
            'title': '🏭 Tableau de bord Direction'
        }
    
    # Admin et superviseurs voient tout
    elif user_role in ['ADMIN', 'SUPERVISEUR']:
        return {
            'show_extrusion': True,
            'show_other_sections': True,
            'show_admin_access': True,
            'title': '🏭 Tableau de bord Administrateur'
        }
    
    # Visiteurs par défaut
    else:
        return {
            'show_extrusion': True,
            'show_other_sections': True,
            'show_admin_access': False,
            'title': '🏭 Tableau de bord'
        }

@login_required
def dashboard_view(request):
    """Dashboard principal avec contrôle d'accès basé sur l'utilisateur"""
    
    # Récupérer la date depuis le paramètre GET, sinon utiliser aujourd'hui
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()
    
    # Récupérer l'utilisateur et son rôle
    user = request.user
    user_role = user.role
    
    # Obtenir la configuration d'accès selon le rôle
    access_config = get_user_access_config(user_role)
    
    # Calculer les pourcentages pour chaque section
    production_extrusion_val = get_production_section_jour('extrusion', selected_date)
    production_imprimerie_val = get_production_section_jour('imprimerie', selected_date)
    production_soudure_val = get_production_section_jour('soudure', selected_date)
    production_recyclage_val = get_production_section_jour('recyclage', selected_date)
    production_totale_val = get_production_totale_jour(selected_date)
    
    # Calculer les pourcentages (en prenant soin de diviser par zéro)
    def safe_divide(numerator, denominator):
        return (numerator / denominator * 100) if denominator > 0 else 0
    
    pourcentage_extrusion = safe_divide(production_extrusion_val, production_totale_val)
    pourcentage_imprimerie = safe_divide(production_imprimerie_val, production_totale_val)
    pourcentage_soudure = safe_divide(production_soudure_val, production_totale_val)
    pourcentage_recyclage = safe_divide(production_recyclage_val, production_totale_val)
    
    # Statistiques des machines
    machines_stats = get_machines_stats()
    pourcentage_machines_actives = (
        (machines_stats['actives'] / machines_stats['total'] * 100)
        if machines_stats['total'] > 0 else 0
    )
    
    # Total déchets
    total_dechets_val = get_dechets_totaux_jour(selected_date)
    pourcentage_dechets = safe_divide(total_dechets_val, production_totale_val)
    
    # Pourcentage de l'objectif (objectif quotidien: 75000 kg)
    objectif_quotidien = 75000
    pourcentage_production_totale = safe_divide(production_totale_val, objectif_quotidien)
    
    # Vérifier si l'utilisateur a accès à chaque section pour le bouton "Saisir"
    def user_can_access_section(user_role, section):
        """Détermine si l'utilisateur peut accéder à la section"""
        if user_role in ['ADMIN', 'SUPERVISEUR']:
            return True
        
        mapping = {
            'extrusion': ['CHEF_EXT1', 'CHEF_EXT2', 'CHEF_EXT3', 'CHEF_EXT4', 'CHEF_EXT5'],
            'imprimerie': ['CHEF_IMPRIM'],
            'soudure': ['CHEF_SOUD'],
            'recyclage': ['CHEF_RECYCL']
        }
        
        if section in mapping:
            return user_role in mapping[section]
        return False
    
    context = {
        # Dates
        'today': selected_date,
        'selected_date': selected_date,
        'is_today': selected_date == timezone.now().date(),
        
        # Contrôle d'accès
        'user_role': user_role,
        'user_full_name': user.get_full_name() or user.username,
        'access_config': access_config,
        
        # Permissions par section
        'can_access_extrusion': user_can_access_section(user_role, 'extrusion'),
        'can_access_imprimerie': user_can_access_section(user_role, 'imprimerie'),
        'can_access_soudure': user_can_access_section(user_role, 'soudure'),
        'can_access_recyclage': user_can_access_section(user_role, 'recyclage'),
        
        # Métriques principales
        'production_totale': production_totale_val,
        'pourcentage_production_totale': pourcentage_production_totale,
        'production_extrusion': production_extrusion_val,
        'production_imprimerie': production_imprimerie_val,
        'production_soudure': production_soudure_val,
        'production_recyclage': production_recyclage_val,
        
        # Pourcentages par section
        'pourcentage_extrusion': pourcentage_extrusion,
        'pourcentage_imprimerie': pourcentage_imprimerie,
        'pourcentage_soudure': pourcentage_soudure,
        'pourcentage_recyclage': pourcentage_recyclage,
        
        # Autres métriques
        'total_dechets': total_dechets_val,
        'pourcentage_dechets': pourcentage_dechets,
        'efficacite_moyenne': get_efficacite_moyenne_jour(selected_date),
        'machines_stats': machines_stats,
        'pourcentage_machines_actives': pourcentage_machines_actives,
        
        # Zones et performance
        'zones_performance': get_zones_performance(selected_date),
        'alertes': Alerte.objects.filter(
            statut__in=['nouveau', 'en_cours']
        ).order_by('-date_creation')[:5],
        
        # Statistiques détaillées
        'extrusion_stats': get_extrusion_details_jour(selected_date),
        'imprimerie_stats': get_imprimerie_details_jour(selected_date),
        'soudure_stats': get_soudure_details_jour(selected_date),
        'recyclage_stats': get_recyclage_details_jour(selected_date),
        
        # Analytics
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