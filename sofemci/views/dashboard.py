from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models import (
    ProductionExtrusion, ProductionSoudure, ProductionImprimerie,
    ProductionRecyclage, Equipe, Machine, ZoneExtrusion
)

from ..utils import (
    get_production_totale_jour, get_production_section_jour, get_dechets_totaux_jour,
    get_efficacite_moyenne_jour, get_machines_stats, get_zones_performance,
    get_extrusion_details_jour, get_imprimerie_details_jour, get_soudure_details_jour,
    get_recyclage_details_jour, get_chart_data_for_dashboard, get_analytics_kpis,
    get_analytics_table_data, calculer_pourcentage_production, calculer_pourcentage_section,
    get_objectif_section,
)

# ==========================================
# FONCTIONS UTILITAIRES DASHBOARD
# ==========================================

def get_production_totale_jour(date):
    """Production totale d'un jour"""
    total = Decimal('0')

    # Extrusion
    extrusion_total = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += extrusion_total

    # Imprimerie
    imprimerie_total = ProductionImprimerie.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += imprimerie_total

    # Soudure
    soudure_total = ProductionSoudure.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += soudure_total

    # Recyclage
    recyclage_total = ProductionRecyclage.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += recyclage_total

    return total

def get_production_section_jour(section, date):
    """Production d'une section pour un jour"""
    models_map = {
        'extrusion': ProductionExtrusion,
        'imprimerie': ProductionImprimerie,
        'soudure': ProductionSoudure,
        'recyclage': ProductionRecyclage,
    }

    model = models_map.get(section)
    if not model:
        return Decimal('0')

    result = model.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    return result

def get_dechets_totaux_jour(date):
    """Total des déchets d'un jour"""
    total = Decimal('0')

    # Extrusion
    extrusion_dechets = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    total += extrusion_dechets

    # Imprimerie
    imprimerie_dechets = ProductionImprimerie.objects.filter(date_production=date).aggregate(
        Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    total += imprimerie_dechets

    # Soudure
    soudure_dechets = ProductionSoudure.objects.filter(date_production=date).aggregate(
        Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    total += soudure_dechets

    return total

def get_efficacite_moyenne_jour(date):
    """Efficacité moyenne d'un jour"""
    # L'Avg() renvoie un float, mais nous devons le traiter pour la compatibilité
    efficacite_float = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Avg('rendement_pourcentage'))['rendement_pourcentage__avg']

    # Convertir en Decimal si ce n'est pas None, puis arrondir
    if efficacite_float is not None:
        # Conversion du float au Decimal pour le round éventuel, puis au type de retour attendu
        return round(Decimal(str(efficacite_float)), 1)

    return Decimal('0')

def get_machines_stats():
    """Statistiques des machines"""
    return {
        'total': Machine.objects.count(),
        'actives': Machine.objects.filter(etat='actif').count(),
        'maintenance': Machine.objects.filter(etat='maintenance').count(),
        'pannes': Machine.objects.filter(etat='panne').count(),
    }

def get_zones_performance(date):
    """Performance des zones d'extrusion"""
    zones_performance = []
    for zone in ZoneExtrusion.objects.filter(active=True):
        prod_zone = ProductionExtrusion.objects.filter(
            date_production=date,
            zone=zone
        ).aggregate(
            total=Sum('total_production_kg'),
            machines=Avg('nombre_machines_actives'),
            efficacite=Avg('rendement_pourcentage')
        )

        # Les résultats de l'agrégation Avg() sont des floats, on les convertit en Decimal pour l'affichage
        machines_avg = prod_zone['machines']
        efficacite_avg = prod_zone['efficacite']

        machines_actives = int(round(Decimal(str(machines_avg)), 0)) if machines_avg is not None else 0
        efficacite = round(Decimal(str(efficacite_avg)), 1) if efficacite_avg is not None else 0

        zones_performance.append({
            'zone': zone,
            'production': prod_zone['total'] or 0,
            'machines_actives': machines_actives,
            'efficacite': efficacite
        })

    return zones_performance

def get_zones_utilisateur(user):
    """Zones accessibles selon l'utilisateur"""
    if user.role == 'chef_extrusion':
        return ZoneExtrusion.objects.filter(chef_zone=user, active=True)
    return ZoneExtrusion.objects.filter(active=True)

def get_extrusion_details_jour(date):
    """Détails extrusion du jour"""
    productions = ProductionExtrusion.objects.filter(date_production=date)

    if not productions.exists():
        return {
            'temps_travail': 0,
            'machinistes_moyen': 0,
            'matiere_premiere': 0,
            'production_finis': 0,
            'production_semi_finis': 0,
            'production_totale': 0,
            'dechets_totaux': 0,
            'taux_dechet': 0,
        }

    aggregats = productions.aggregate(
        matiere_premiere=Sum('matiere_premiere_kg'),
        prod_finis=Sum('production_finis_kg'),
        prod_semi_finis=Sum('production_semi_finis_kg'),
        total_prod=Sum('total_production_kg'),
        dechets=Sum('dechets_kg'),
        machinistes_total=Sum('nombre_machinistes'),
        count_productions=Count('id')
    )

    nombre_moyen_machinistes = (aggregats['machinistes_total'] / aggregats['count_productions']) if aggregats['count_productions'] > 0 else 0

    total_prod = aggregats['total_prod'] or 0
    dechets = aggregats['dechets'] or 0

    # S'assurer que les calculs de taux se font entre Decimals
    somme_total = total_prod + dechets
    taux_dechet = (dechets / somme_total * Decimal('100')) if somme_total > 0 else 0

    return {
        'temps_travail': 8,
        'machinistes_moyen': round(nombre_moyen_machinistes, 0),
        'matiere_premiere': aggregats['matiere_premiere'] or 0,
        'production_finis': aggregats['prod_finis'] or 0,
        'production_semi_finis': aggregats['prod_semi_finis'] or 0,
        'production_totale': total_prod,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_imprimerie_details_jour(date):
    """Détails imprimerie du jour"""
    productions = ProductionImprimerie.objects.filter(date_production=date)

    if not productions.exists():
        return {
            'temps_travail': 0,
            'machines_actives': 0,
            'machines_totales': Machine.objects.filter(section='imprimerie').count(),
            'bobines_finies': 0,
            'bobines_semi_finies': 0,
            'production_totale': 0,
            'dechets_totaux': 0,
            'taux_dechet': 0,
        }

    # Correction: Nommer explicitement les clés pour qu'elles correspondent à l'accès ci-dessous
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bobines_finies=Sum('production_bobines_finies_kg'), # Clé 'bobines_finies'
        bobines_semi_finies=Sum('production_bobines_semi_finies_kg'), # Clé 'bobines_semi_finies'
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )

    # Gérer la possibilité que l'Avg (machines) soit None (float)
    machines_avg_float = aggregats.get('machines')
    machines_actives = round(Decimal(str(machines_avg_float)), 0) if machines_avg_float is not None else 0

    # Utiliser .get(key) ou l'opérateur 'or' pour fournir une valeur par défaut Decimal('0') si la clé est présente mais None
    bobines_finis = aggregats.get('bobines_finies') or Decimal('0')
    bobines_semi_finies = aggregats.get('bobines_semi_finies') or Decimal('0')

    total = aggregats.get('total') or Decimal('0')
    dechets = aggregats.get('dechets') or Decimal('0')

    # S'assurer que les calculs de taux se font entre Decimals
    somme_total = total + dechets
    taux_dechet = (dechets / somme_total * Decimal('100')) if somme_total > 0 else 0

    return {
        'temps_travail': 8,
        'machines_actives': machines_actives,
        'machines_totales': Machine.objects.filter(section='imprimerie').count(),
        'bobines_finies': bobines_finis,
        'bobines_semi_finies': bobines_semi_finies,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_soudure_details_jour(date):
    """Détails soudure du jour"""
    productions = ProductionSoudure.objects.filter(date_production=date)

    if not productions.exists():
        return {
            'temps_travail': 0,
            'machines_actives': 0,
            'machines_totales': Machine.objects.filter(section='soudure').count(),
            'production_bretelles': 0,
            'production_rema': 0,
            'production_batta': 0,
            'production_totale': 0,
            'dechets_totaux': 0,
            'taux_dechet': 0,
        }

    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bretelles=Sum('production_bretelles_kg'),
        rema=Sum('production_rema_kg'),
        batta=Sum('production_batta_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )

    # Conversion de l'Avg() en Decimal
    machines_avg = aggregats['machines']
    machines_actives = round(Decimal(str(machines_avg)), 0) if machines_avg is not None else 0

    total = aggregats['total'] or 0
    dechets = aggregats['dechets'] or 0

    # S'assurer que les calculs de taux se font entre Decimals
    somme_total = total + dechets
    taux_dechet = (dechets / somme_total * Decimal('100')) if somme_total > 0 else 0

    return {
        'temps_travail': 8,
        'machines_actives': machines_actives,
        'machines_totales': Machine.objects.filter(section='soudure').count(),
        'production_bretelles': aggregats['bretelles'] or 0,
        'production_rema': aggregats['rema'] or 0,
        'production_batta': aggregats['batta'] or 0,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_recyclage_details_jour(date):
    """Détails recyclage du jour"""
    productions = ProductionRecyclage.objects.filter(date_production=date)

    if not productions.exists():
        return {
            'moulinex_actifs': 0,
            'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
            'total_broyage': 0,
            'total_bache_noir': 0,
            'production_totale': 0,
            'taux_transformation': 0,
            'rendement': 0,
            'productivite_par_moulinex': 0,
            'temps_travail': 0, # Ajout pour être complet
        }

    aggregats = productions.aggregate(
        moulinex=Avg('nombre_moulinex'),
        broyage=Sum('production_broyage_kg'),
        bache=Sum('production_bache_noir_kg'),
        total=Sum('total_production_kg')
    )

    broyage = aggregats['broyage'] or 0
    bache = aggregats['bache'] or 0
    total = aggregats['total'] or 0

    # CORRECTION DE L'ERREUR Decimal/float:
    # L'agrégation Avg() (moulinex_avg) retourne un float. Il faut le convertir en Decimal.
    moulinex_avg_float = aggregats['moulinex']
    moulinex_avg_decimal = Decimal(str(moulinex_avg_float)) if moulinex_avg_float is not None else Decimal('1') # Convertir float en Decimal

    # Correction pour le cas où l'agrégation retourne None (si aucune production)
    moulinex_avg = moulinex_avg_decimal if moulinex_avg_decimal > 0 else Decimal('1')

    # Calcul du taux de transformation (Decimal / Decimal)
    taux_transformation = (bache / broyage * Decimal('100')) if broyage > 0 else 0

    # Calcul de la productivité (Decimal / Decimal)
    productivite = (total / moulinex_avg) if moulinex_avg > 0 else 0

    return {
        'moulinex_actifs': round(moulinex_avg_decimal, 0) if moulinex_avg_float is not None else 0, # Utiliser le float converti pour l'arrondi
        'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
        'total_broyage': broyage,
        'total_bache_noir': bache,
        'production_totale': total,
        'taux_transformation': round(taux_transformation, 1),
        'rendement': round(taux_transformation, 1),
        'productivite_par_moulinex': round(productivite, 1),
        'temps_travail': 8,
    }


def get_chart_data_for_dashboard():
    """Données simplifiées pour graphiques"""
    return json.dumps({
        'months': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
        'extrusion': [100, 120, 130, 110, 140, 125, 135],
        'soudure': [80, 90, 85, 95, 100, 88, 92],
        'dechets': [5, 6, 4, 7, 5, 6, 5],
        'bache_noir': [60, 65, 70, 63, 68, 66, 69],
    })

def get_analytics_kpis():
    """KPIs simplifiés pour Analytics"""
    return {
        'production_totale_mois': 15000,
        'croissance_production': 12.5,
        'taux_dechet_mois': 3.2,
        'reduction_dechets': 2.3,
        'efficacite_moyenne': 87.5,
        'amélioration_efficacite': 3.2,
        'taux_transformation': 78.5,
        'amélioration_transformation': 5.1,
    }

def get_analytics_table_data():
    """Données tableau Analytics simplifiées"""
    return {
        'extrusion': {
            'production': 8000,
            'dechets': 224,
            'taux_dechet': 2.8,
            'efficacite': 89.2,
        },
        'imprimerie': {
            'production': 3500,
            'dechets': 108.5,
            'taux_dechet': 3.1,
            'efficacite': 91.5,
        },
        'soudure': {
            'production': 2500,
            'dechets': 95,
            'taux_dechet': 3.8,
            'efficacite': 85.3,
        },
        'recyclage': {
            'production': 1000,
            'taux_transformation': 78.2,
            'rendement': 82.5,
        },
    }

def calculer_pourcentage_production(production_actuelle, production_reference=None):
    """Calcule le pourcentage de production"""
    if production_reference is None:
        production_reference = Decimal('75000')

    if production_reference == 0:
        return 0

    pourcentage = (production_actuelle / production_reference) * Decimal('100')
    return round(pourcentage, 1)

def calculer_pourcentage_section(section, production_actuelle):
    """Calcule le pourcentage pour une section spécifique"""
    objectifs = {
        'extrusion': Decimal('35000'),
        'imprimerie': Decimal('20000'),
        'soudure': Decimal('12000'),
        'recyclage': Decimal('8000'),
    }

    objectif = objectifs.get(section, Decimal('10000'))

    if objectif == 0:
        return 0

    return round((production_actuelle / objectif) * Decimal('100'), 1)

def get_objectif_section(section):
    """Retourne l'objectif journalier d'une section"""
    objectifs = {
        'extrusion': Decimal('35000'),
        'imprimerie': Decimal('20000'),
        'soudure': Decimal('12000'),
        'recyclage': Decimal('8000'),
    }
    return objectifs.get(section, Decimal('10000'))

# ==========================================
# VUES DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = timezone.now().date()
    else:
        selected_date = timezone.now().date()

    # Calculs de production
    production_totale = get_production_totale_jour(selected_date)
    production_extrusion = get_production_section_jour('extrusion', selected_date)
    production_imprimerie = get_production_section_jour('imprimerie', selected_date)
    production_soudure = get_production_section_jour('soudure', selected_date)
    production_recyclage = get_production_section_jour('recyclage', selected_date)

    # Objectif journalier total
    objectif_total = Decimal('75000')

    context = {
        'today': selected_date,
        'selected_date': selected_date,
        'is_today': selected_date == timezone.now().date(),

        # Productions avec pourcentages
        'production_totale': production_totale,
        'pourcentage_production_totale': calculer_pourcentage_production(production_totale, objectif_total),
        'objectif_total': objectif_total,

        'production_extrusion': production_extrusion,
        'pourcentage_extrusion': calculer_pourcentage_section('extrusion', production_extrusion),
        'objectif_extrusion': get_objectif_section('extrusion'),

        'production_imprimerie': production_imprimerie,
        'pourcentage_imprimerie': calculer_pourcentage_section('imprimerie', production_imprimerie),
        'objectif_imprimerie': get_objectif_section('imprimerie'),

        'production_soudure': production_soudure,
        'pourcentage_soudure': calculer_pourcentage_section('soudure', production_soudure),
        'objectif_soudure': get_objectif_section('soudure'),

        'production_recyclage': production_recyclage,
        'pourcentage_recyclage': calculer_pourcentage_section('recyclage', production_recyclage),
        'objectif_recyclage': get_objectif_section('recyclage'),

        'total_dechets': get_dechets_totaux_jour(selected_date),
        'efficacite_moyenne': get_efficacite_moyenne_jour(selected_date),
        'machines_stats': get_machines_stats(),
        'zones_performance': get_zones_performance(selected_date),

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
def dashboard_ia_view(request):
    """Dashboard IA simplifié"""
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')

    # Statistiques simplifiées
    stats_parc = {
        'score_sante_moyen': 85.0,
        'machines_risque_critique': 2,
        'machines_risque_eleve': 5,
        'anomalies_detectees': 3,
    }

    # Machines critiques simplifiées
    machines_critiques = []
    for machine in Machine.objects.filter(etat='actif')[:5]:
        machines_critiques.append({
            'id': machine.id,
            'numero': machine.numero,
            'section': machine.section,
            'get_section_display': machine.get_section_display(),
            'probabilite_panne_7_jours': getattr(machine, 'probabilite_panne_7_jours', 0) or 0,
            'score_sante_global': getattr(machine, 'score_sante_global', 0) or 0,
        })

    # Alertes IA simplifiées
    alertes = []

    # Machines actives simplifiées
    machines_actives = []
    for machine in Machine.objects.filter(etat='actif')[:10]:
        machines_actives.append({
            'id': machine.id,
            'numero': machine.numero,
            'section': machine.section,
            'get_section_display': machine.get_section_display(),
            'score_sante_global': getattr(machine, 'score_sante_global', 0) or 0,
            'probabilite_panne_7_jours': getattr(machine, 'probabilite_panne_7_jours', 0) or 0,
        })

    context = {
        'stats_parc': stats_parc,
        'machines_critiques': machines_critiques,
        'alertes': alertes,
        'machines_actives': machines_actives,
    }

    return render(request, 'dashboard_ia.html', context)

@login_required
def dashboard_direction_view(request):
    """Vue simplifiée pour la direction"""
    if request.user.role not in ['direction', 'admin']:
        messages.error(request, 'Accès refusé. Réservé à la direction.')
        return redirect('dashboard')

    context = {
        'ca_mensuel': Decimal('45000000'),
        'objectif_ca': Decimal('50000000'),
        'taux_objectif_ca': 90,
        'production_mensuelle': Decimal('140000'),
        'objectif_production': Decimal('150000'),
        'taux_objectif_production': 93.3,
        'rendement_global': 87.5,
        'objectif_rendement': Decimal('85'),
        'difference_rendement': 2.5,
        'cout_production': Decimal('820'),
        'objectif_cout': Decimal('850'),
        'difference_cout': -30,
        'alertes_actives': [],
        'performances_sections': [],
        'labels_production': json.dumps(['Extrusion', 'Imprimerie', 'Soudure', 'Recyclage']),
        'data_production': json.dumps([80000, 35000, 25000, 10000]),
    }

    return render(request, 'dashboard_direction.html', context)

# ==========================================
# VUES DASHBOARD (Suite de la continuité)
# ==========================================

@login_required
def analytics_view(request):
    """
    Vue pour l'analyse détaillée des performances de production.
    Utilise les fonctions utilitaires 'get_analytics_kpis' et 'get_analytics_table_data'.
    """
    if request.user.role not in ['superviseur', 'admin', 'direction', 'chef_extrusion', 'chef_imprimerie', 'chef_soudure', 'chef_recyclage']:
        messages.error(request, 'Accès aux analyses refusé.')
        return redirect('dashboard')

    analytics_kpis = get_analytics_kpis()
    analytics_table = get_analytics_table_data()

    context = {
        'page_title': 'Analyses Détaillées',
        'kpis': analytics_kpis,
        'table_data': analytics_table,
        'periode_analyse': 'Mois en cours (Données Simulées)',
    }

    return render(request, 'analytics.html', context)


@login_required
def chart_data_api(request):
    """
    Endpoint API pour récupérer les données de graphique asynchrones.
    """

    # Récupérer les paramètres de l'URL
    period_type = request.GET.get('type', 'jour')
    date_str = request.GET.get('date', timezone.now().strftime('%Y-%m-%d'))

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    # LOGIQUE DE RÉCUPÉRATION DES DONNÉES EN FONCTION DU TYPE/DATE

    # 1. Cas 'jour'
    if period_type == 'jour':
        production_extrusion = get_production_section_jour('extrusion', selected_date)
        production_soudure = get_production_section_jour('soudure', selected_date)
        dechets_totaux = get_dechets_totaux_jour(selected_date)

        # Simulation de données horaires pour l'exemple
        data = {
            'labels': ['08h-10h', '10h-12h', '12h-14h', '14h-16h', '16h-18h', '18h-20h'],
            'extrusion': [
                round(production_extrusion * Decimal(0.1), 1),
                round(production_extrusion * Decimal(0.15), 1),
                round(production_extrusion * Decimal(0.2), 1),
                round(production_extrusion * Decimal(0.25), 1),
                round(production_extrusion * Decimal(0.2), 1),
                round(production_extrusion * Decimal(0.1), 1)
            ],
            'soudure': [
                round(production_soudure * Decimal(0.1), 1),
                round(production_soudure * Decimal(0.12), 1),
                round(production_soudure * Decimal(0.18), 1),
                round(production_soudure * Decimal(0.25), 1),
                round(production_soudure * Decimal(0.2), 1),
                round(production_soudure * Decimal(0.15), 1)
            ],
            'dechets': [
                round(dechets_totaux * Decimal(0.15), 1),
                round(dechets_totaux * Decimal(0.1), 1),
                round(dechets_totaux * Decimal(0.2), 1),
                round(dechets_totaux * Decimal(0.2), 1),
                round(dechets_totaux * Decimal(0.15), 1),
                round(dechets_totaux * Decimal(0.2), 1)
            ],
            'bache_noir': [0, 0, 0, 0, 0, 0],
        }

    # 2. Cas 'semaine' (Données simulées des 7 derniers jours)
    elif period_type == 'semaine':
        data = json.loads(get_chart_data_for_dashboard())
        # S'assurer que les données sont des listes de nombres pour le JSON
        data['extrusion'] = [float(d) for d in data['extrusion']]
        data['soudure'] = [float(d) for d in data['soudure']]
        data['dechets'] = [float(d) for d in data['dechets']]
        data['bache_noir'] = [float(d) for d in data['bache_noir']]

    # 3. Cas 'mois' (Simulation mensuelle)
    elif period_type == 'mois':
        data = {
            'labels': ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
            'extrusion': [45000, 38000, 42000, 39000],
            'soudure': [18000, 16000, 20000, 17000],
            'dechets': [1200, 1100, 1300, 1150],
            'bache_noir': [5000, 4800, 5200, 4900],
        }

    else: # Par défaut
        data = json.loads(get_chart_data_for_dashboard())

    return JsonResponse(data)