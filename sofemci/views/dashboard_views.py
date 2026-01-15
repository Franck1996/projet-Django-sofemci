"""
Vue dashboard unique qui s'adapte au rôle de l'utilisateur
"""
from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Sum, Avg, Count, Q
import json

from ..models import (
    Alerte, CustomUser, Machine, ProductionExtrusion, 
    ProductionImprimerie, ProductionSoudure, ProductionRecyclage,
)
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
    calculate_percentage_of_goal,
)

def safe_dict_get(data, key, default=None):
    """Sécurise l'accès aux dictionnaires"""
    if isinstance(data, dict):
        return data.get(key, default)
    return default

def safe_list_get(data, index, default=None):
    """Sécurise l'accès aux listes"""
    if isinstance(data, list) and index < len(data):
        return data[index]
    return default

@login_required
def dashboard_view(request):
    """Dashboard unique qui s'adapte au rôle de l'utilisateur"""
    user = request.user
    today = timezone.now().date()
    
    # Récupérer la date depuis le paramètre GET, sinon utiliser aujourd'hui
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today
    
    # Déterminer les permissions d'affichage selon le rôle
    is_chef_extrusion = user.is_chef_extrusion()
    is_chef_section = user.is_chef_section()
    is_direction = user.is_direction()
    is_superviseur = user.is_superviseur()
    is_admin = user.is_admin()
    read_only = is_direction  # La direction a un accès lecture seule
    
    # Initialiser le contexte de base
    context = {
        'today': today,
        'selected_date': selected_date,
        'is_today': selected_date == today,
        'user': user,
        'user_role': user.role,
        'user_role_display': user.get_role_display(),
        'user_section': user.get_section_affectee(),
        
        # Permissions d'affichage
        'show_extrusion': is_chef_extrusion or is_superviseur or is_admin or is_direction,
        'show_sections': is_chef_section or is_superviseur or is_admin or is_direction,
        'show_admin': is_admin,
        'is_direction': is_direction,
        'is_superviseur': is_superviseur,
        'is_admin': is_admin,
        'read_only': read_only,
        
        # Données générales
        'production_totale': get_production_totale_jour(selected_date),
        'efficacite_moyenne': get_efficacite_moyenne_jour(selected_date),
        'total_dechets': get_dechets_totaux_jour(selected_date),
        
        # Alertes (tous les rôles)
        'alertes': Alerte.objects.filter(
            statut__in=['NOUVELLE', 'EN_COURS']  # CORRECTION : Majuscules
        ).order_by('-date_creation')[:5],
    }
    
    # Récupérer et traiter les statistiques des machines
    machines_stats_data = get_machines_stats()
    if isinstance(machines_stats_data, dict):
        context['machines_stats'] = machines_stats_data
        # Calculer le pourcentage de machines actives
        total = safe_dict_get(machines_stats_data, 'total', 0)
        actives = safe_dict_get(machines_stats_data, 'actives', 0)
        if total > 0:
            context['pourcentage_machines_actives'] = (actives / total) * 100
        else:
            context['pourcentage_machines_actives'] = 0
    else:
        context['machines_stats'] = {}
        context['pourcentage_machines_actives'] = 0
    
    # Chart data (pour direction et superviseur seulement)
    if is_direction or is_superviseur or is_admin:
        try:
            context['chart_data'] = get_chart_data_for_dashboard()
        except Exception as e:
            print(f"Erreur chart_data: {e}")
            context['chart_data'] = None
        
        try:
            context['analytics_kpis'] = get_analytics_kpis()
        except Exception as e:
            print(f"Erreur analytics_kpis: {e}")
            context['analytics_kpis'] = None
        
        try:
            context['analytics_table'] = get_analytics_table_data()
        except Exception as e:
            print(f"Erreur analytics_table: {e}")
            context['analytics_table'] = None
    
    # Calculer les pourcentages pour les métriques
    if context['production_totale'] > 0:
        context['pourcentage_production_totale'] = (context['production_totale'] / 100000) * 100
        context['pourcentage_dechets'] = (context['total_dechets'] / context['production_totale']) * 100 if context['production_totale'] > 0 else 0
    else:
        context['pourcentage_production_totale'] = 0
        context['pourcentage_dechets'] = 0
    
    # Données spécifiques pour chefs d'extrusion
    if is_chef_extrusion and not is_direction:
        zone_map = {
            CustomUser.CHEF_EXT1: 'Zone 1',
            CustomUser.CHEF_EXT2: 'Zone 2',
            CustomUser.CHEF_EXT3: 'Zone 3',
            CustomUser.CHEF_EXT4: 'Zone 4',
            CustomUser.CHEF_EXT5: 'Zone 5'
        }
        user_zone = zone_map.get(user.role, 'Zone 1')
        
        # Récupérer les données de production pour la zone
        productions = ProductionExtrusion.objects.filter(
            zone__nom=user_zone,
            date_production=selected_date  # CORRECTION : date_production au lieu de date_creation__date
        ).aggregate(
            total_produit=Sum('total_production_kg'),
            total_rebut=Sum('dechets'),
            avg_efficience=Avg('rendement_pourcentage')
        )
        
        extrusion_stats = get_extrusion_details_jour(selected_date)
        
        context.update({
            'user_zone': user_zone,
            'production_extrusion': productions['total_produit'] or 0,
            'extrusion_stats': extrusion_stats,
            'zones_performance': get_zones_performance(selected_date),
        })
        
        # Calculer les pourcentages pour l'extrusion
        if context['production_extrusion'] > 0:
            context['pourcentage_extrusion'] = (context['production_extrusion'] / context['production_totale']) * 100 if context['production_totale'] > 0 else 0
        else:
            context['pourcentage_extrusion'] = 0
            
        if isinstance(extrusion_stats, dict):
            stats = extrusion_stats
            production_totale = stats.get('production_totale', 0)
            if production_totale > 0:
                context['pourcentage_semi_finis'] = (stats.get('production_semi_finis', 0) / production_totale) * 100
                context['pourcentage_finis'] = (stats.get('production_finis', 0) / production_totale) * 100
                context['pourcentage_dechets_extrusion'] = (stats.get('dechets', 0) / production_totale) * 100
            else:
                context['pourcentage_semi_finis'] = 0
                context['pourcentage_finis'] = 0
                context['pourcentage_dechets_extrusion'] = 0
    
    # Données spécifiques pour chefs de section
    elif is_chef_section and not is_direction:
        section_map = {
            CustomUser.CHEF_RECYCL: 'RECYCLAGE',
            CustomUser.CHEF_IMPRIM: 'IMPRIMERIE',
            CustomUser.CHEF_SOUD: 'SOUDURE'
        }
        user_section = section_map.get(user.role, 'IMPRIMERIE')
        
        # Récupérer les données selon la section
        if user_section == 'IMPRIMERIE':
            productions = ProductionImprimerie.objects.filter(
                date_production=selected_date
            ).aggregate(total_produit=Sum('total_production_kg'))
            
            imprimerie_stats = get_imprimerie_details_jour(selected_date)
            
            context['production_imprimerie'] = productions['total_produit'] or 0
            context['imprimerie_stats'] = imprimerie_stats
            
            # Calculer les pourcentages pour l'imprimerie
            if context['production_imprimerie'] > 0:
                context['pourcentage_imprimerie'] = (context['production_imprimerie'] / context['production_totale']) * 100 if context['production_totale'] > 0 else 0
            else:
                context['pourcentage_imprimerie'] = 0
                
            if isinstance(imprimerie_stats, dict):
                stats = imprimerie_stats
                production_totale = stats.get('production_totale', 0)
                if production_totale > 0:
                    context['pourcentage_bobines_finies'] = (stats.get('bobines_finies', 0) / production_totale) * 100
                    context['pourcentage_bobines_semi'] = (stats.get('bobines_semi', 0) / production_totale) * 100
                    context['pourcentage_dechets_imprimerie'] = (stats.get('dechets', 0) / production_totale) * 100
                
                # Pour les machines dans l'imprimerie
                machines_totales = stats.get('nombre_machines', 0)  # CORRECTION : 'nombre_machines' au lieu de 'machines_totales'
                if machines_totales > 0:
                    # Estimate machines actives based on some logic
                    context['pourcentage_machines_imprimerie'] = 85  # Valeur par défaut
                else:
                    context['pourcentage_machines_imprimerie'] = 0
                    
        elif user_section == 'SOUDURE':
            productions = ProductionSoudure.objects.filter(
                date_production=selected_date
            ).aggregate(total_produit=Sum('total_production_kg'))
            
            soudure_stats = get_soudure_details_jour(selected_date)
            
            context['production_soudure'] = productions['total_produit'] or 0
            context['soudure_stats'] = soudure_stats
            
            # Calculer les pourcentages pour la soudure
            if context['production_soudure'] > 0:
                context['pourcentage_soudure'] = (context['production_soudure'] / context['production_totale']) * 100 if context['production_totale'] > 0 else 0
            else:
                context['pourcentage_soudure'] = 0
                
            if isinstance(soudure_stats, dict):
                stats = soudure_stats
                production_totale = stats.get('production_totale', 0)
                if production_totale > 0:
                    context['pourcentage_bobines_finies'] = (stats.get('bobines_finies', 0) / production_totale) * 100
                    context['pourcentage_dechets_soudure'] = (stats.get('dechets', 0) / production_totale) * 100
                
                # Pour les équipes dans la soudure
                equipes = stats.get('equipes', 0)
                if equipes > 0:
                    context['pourcentage_equipes_soudure'] = 90  # Valeur par défaut
                else:
                    context['pourcentage_equipes_soudure'] = 0
                    
        elif user_section == 'RECYCLAGE':
            productions = ProductionRecyclage.objects.filter(
                date_production=selected_date
            ).aggregate(total_produit=Sum('total_production_kg'))
            
            recyclage_stats = get_recyclage_details_jour(selected_date)
            
            context['production_recyclage'] = productions['total_produit'] or 0
            context['recyclage_stats'] = recyclage_stats
            
            # Calculer les pourcentages pour le recyclage
            if context['production_recyclage'] > 0:
                context['pourcentage_recyclage'] = (context['production_recyclage'] / context['production_totale']) * 100 if context['production_totale'] > 0 else 0
            else:
                context['pourcentage_recyclage'] = 0
                
            if isinstance(recyclage_stats, dict):
                stats = recyclage_stats
                production_totale = stats.get('production_totale', 0)
                matiere_entree = stats.get('matiere_entree', 0)
                if matiere_entree > 0:
                    context['pourcentage_taux_recyclage'] = (production_totale / matiere_entree) * 100
                else:
                    context['pourcentage_taux_recyclage'] = 0
    
    # Données pour direction (lecture seule, toutes les sections)
    elif is_direction:
        context.update({
            'production_extrusion': get_production_section_jour('EXTRUSION', selected_date),
            'production_imprimerie': get_production_section_jour('IMPRIMERIE', selected_date),
            'production_soudure': get_production_section_jour('SOUDURE', selected_date),
            'production_recyclage': get_production_section_jour('RECYCLAGE', selected_date),
            'extrusion_stats': get_extrusion_details_jour(selected_date),
            'imprimerie_stats': get_imprimerie_details_jour(selected_date),
            'soudure_stats': get_soudure_details_jour(selected_date),
            'recyclage_stats': get_recyclage_details_jour(selected_date),
            'zones_performance': get_zones_performance(selected_date),
        })
        
        # Calculer les pourcentages pour toutes les sections (direction)
        for section in ['extrusion', 'imprimerie', 'soudure', 'recyclage']:
            production = context.get(f'production_{section}', 0)
            if production > 0 and context['production_totale'] > 0:
                context[f'pourcentage_{section}'] = (production / context['production_totale']) * 100
            else:
                context[f'pourcentage_{section}'] = 0
    
    # Données pour superviseur/admin (toutes les sections, accès complet)
    elif is_superviseur or is_admin:
        context.update({
            'production_extrusion': get_production_section_jour('EXTRUSION', selected_date),
            'production_imprimerie': get_production_section_jour('IMPRIMERIE', selected_date),
            'production_soudure': get_production_section_jour('SOUDURE', selected_date),
            'production_recyclage': get_production_section_jour('RECYCLAGE', selected_date),
            'extrusion_stats': get_extrusion_details_jour(selected_date),
            'imprimerie_stats': get_imprimerie_details_jour(selected_date),
            'soudure_stats': get_soudure_details_jour(selected_date),
            'recyclage_stats': get_recyclage_details_jour(selected_date),
            'zones_performance': get_zones_performance(selected_date),
        })
        
        # Calculer les pourcentages pour toutes les sections (superviseur/admin)
        for section in ['extrusion', 'imprimerie', 'soudure', 'recyclage']:
            production = context.get(f'production_{section}', 0)
            if production > 0 and context['production_totale'] > 0:
                context[f'pourcentage_{section}'] = (production / context['production_totale']) * 100
            else:
                context[f'pourcentage_{section}'] = 0
    
    # Calculer les pourcentages pour les analytics (si disponibles)
    analytics_kpis = context.get('analytics_kpis')
    if isinstance(analytics_kpis, dict):
        production_totale_mois = analytics_kpis.get('production_mois', 0)
        if production_totale_mois:
            try:
                context['pourcentage_kpi_production'] = calculate_percentage_of_goal(
                    Decimal(str(production_totale_mois)), 
                    Decimal('150000')
                )
            except:
                context['pourcentage_kpi_production'] = 0
    
    analytics_table = context.get('analytics_table')
    if isinstance(analytics_table, list):
        for i, row in enumerate(analytics_table):
            if isinstance(row, dict):
                production = row.get('production', 0)
                if production > 0 and context['production_totale'] > 0:
                    context[f'pourcentage_table_{i}'] = (production / context['production_totale']) * 100
                else:
                    context[f'pourcentage_table_{i}'] = 0
    
    return render(request, 'dashboard.html', context)