# sofemci/views.py
from django.http import HttpResponse
from django.template.loader import render_to_string
import io
import pandas as pd
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Avg, Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json
from .models import ProductionExtrusion, ProductionSoudure, ProductionImprimerie, ProductionRecyclage, Equipe
from .models import Machine, AlerteIA
import logging
from .models import *
from .forms import *


logger = logging.getLogger(__name__)
# ==========================================
# AUTHENTIFICATION
# ==========================================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

# ==========================================
# DASHBOARD PRINCIPAL
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
    objectif_total = Decimal('75000')  # 75 tonnes/jour
    
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
    if request.user.role not in ['direction', 'admin']:
        messages.error(request, 'Accès refusé. Réservé à la direction.')
        return redirect('dashboard')
    
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    context = {
        'ca_mensuel': get_ca_mensuel(debut_mois, today),
        'objectif_ca': Decimal('50000000'),  # À paramétrer
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

# ==========================================
# SAISIE PRODUCTION
# ==========================================

@login_required
def saisie_extrusion_view(request):
    if request.user.role not in ['chef_extrusion', 'superviseur', 'admin']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductionExtrusionForm(request.POST, user=request.user)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            messages.success(request, 'Production d\'extrusion enregistrée avec succès !')
            return redirect('saisie_extrusion')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = ProductionExtrusionForm(user=request.user)
    
    context = {
        'form': form,
        'today': timezone.now().date(),
        'zones': get_zones_utilisateur(request.user),
        'equipes': Equipe.objects.all(),
        'productions_recentes': ProductionExtrusion.objects.filter(
            cree_par=request.user if request.user.role == 'chef_extrusion' else Q()
        ).select_related('zone', 'equipe').order_by('-date_creation')[:10],
    }
    
    return render(request, 'saisie_extrusion.html', context)

@login_required
def saisie_sections_view(request):
    user_sections = []
    if request.user.role == 'chef_imprimerie' or request.user.role in ['superviseur', 'admin']:
        user_sections.append('imprimerie')
    if request.user.role == 'chef_soudure' or request.user.role in ['superviseur', 'admin']:
        user_sections.append('soudure')
    if request.user.role == 'chef_recyclage' or request.user.role in ['superviseur', 'admin']:
        user_sections.append('recyclage')
    
    if not user_sections:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    context = {
        'today': timezone.now().date(),
        'user_sections': user_sections,
        'form_imprimerie': ProductionImprimerieForm() if 'imprimerie' in user_sections else None,
        'form_soudure': ProductionSoudureForm() if 'soudure' in user_sections else None,
        'form_recyclage': ProductionRecyclageForm() if 'recyclage' in user_sections else None,
        'equipes': Equipe.objects.all(),
    }
    
    return render(request, 'saisie_sections.html', context)

@login_required
def saisie_imprimerie_ajax(request):
    if request.method == 'POST':
        form = ProductionImprimerieForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({'success': True, 'message': 'Production imprimerie enregistrée !'})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def saisie_soudure_ajax(request):
    if request.method == 'POST':
        form = ProductionSoudureForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({'success': True, 'message': 'Production soudure enregistrée !'})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def saisie_recyclage_ajax(request):
    if request.method == 'POST':
        form = ProductionRecyclageForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({'success': True, 'message': 'Production recyclage enregistrée !'})
        return JsonResponse({'success': False, 'errors': form.errors})
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

# ==========================================
# HISTORIQUE
# ==========================================
def historique_view(request):
    # Récupérer les paramètres de filtrage
    section_filter = request.GET.get('section', '')
    equipe_filter = request.GET.get('equipe', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    periode = request.GET.get('periode', 'ce_mois')
    tri = request.GET.get('tri', '-date')
    page_number = request.GET.get('page', 1)
    
    # Déterminer la période par défaut
    today = timezone.now().date()
    if periode == 'mois_dernier':
        periode_debut = today.replace(day=1) - timedelta(days=1)
        periode_debut = periode_debut.replace(day=1)
        periode_fin = today.replace(day=1) - timedelta(days=1)
    elif periode == 'trimestre':
        current_quarter = (today.month - 1) // 3 + 1
        first_month_of_quarter = 3 * current_quarter - 2
        periode_debut = today.replace(month=first_month_of_quarter, day=1)
        periode_fin = today
    else:
        periode_debut = today.replace(day=1)
        periode_fin = today
    
    # Si dates personnalisées sont fournies
    if date_debut:
        try:
            periode_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        except ValueError:
            periode_debut = today.replace(day=1)
    
    if date_fin:
        try:
            periode_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
        except ValueError:
            periode_fin = today

    # Récupérer toutes les équipes
    equipes = Equipe.objects.all()

    # Construire les données agrégées par date
    productions_data = {}
    
    # Fonction utilitaire pour ajouter des données
    def add_production_data(queryset, section_key, production_field):
        for production in queryset:
            date_str = production.date_production.isoformat()
            if date_str not in productions_data:
                productions_data[date_str] = {
                    'date_production': production.date_production,
                    'extrusion': Decimal('0'),
                    'soudure': Decimal('0'),
                    'imprimerie': Decimal('0'),
                    'recyclage': Decimal('0')
                }
            productions_data[date_str][section_key] += getattr(production, production_field)

    # Récupérer les données
    # Extrusion
    queryset_extrusion = ProductionExtrusion.objects.filter(
        date_production__range=[periode_debut, periode_fin]
    )
    if equipe_filter:
        queryset_extrusion = queryset_extrusion.filter(equipe_id=equipe_filter)
    add_production_data(queryset_extrusion, 'extrusion', 'nombre_bobines_kg')

    # Soudure
    queryset_soudure = ProductionSoudure.objects.filter(
        date_production__range=[periode_debut, periode_fin]
    )
    if equipe_filter:
        queryset_soudure = queryset_soudure.filter(equipe_id=equipe_filter)
    add_production_data(queryset_soudure, 'soudure', 'production_bobines_finies_kg')

    # Imprimerie
    queryset_imprimerie = ProductionImprimerie.objects.filter(
        date_production__range=[periode_debut, periode_fin]
    )
    add_production_data(queryset_imprimerie, 'imprimerie', 'production_bobines_finies_kg')

    # Recyclage
    queryset_recyclage = ProductionRecyclage.objects.filter(
        date_production__range=[periode_debut, periode_fin]
    )
    if equipe_filter:
        queryset_recyclage = queryset_recyclage.filter(equipe_id=equipe_filter)
    add_production_data(queryset_recyclage, 'recyclage', 'production_broyage_kg')

    # Convertir en liste
    productions_list = []
    for date_str, data in productions_data.items():
        total_jour = data['extrusion'] + data['soudure'] + data['imprimerie'] + data['recyclage']
        productions_list.append({
            'id': hash(date_str),
            'date_production': data['date_production'],
            'extrusion': data['extrusion'],
            'soudure': data['soudure'],
            'imprimerie': data['imprimerie'],
            'recyclage': data['recyclage'],
            'total_jour': total_jour
        })

    # Filtrer par section
    if section_filter:
        productions_list = [p for p in productions_list if p[section_filter] > 0]

    # Trier
    reverse_sort = tri.startswith('-')
    sort_field = tri.lstrip('-')
    
    if sort_field == 'date':
        productions_list.sort(key=lambda x: x['date_production'], reverse=reverse_sort)
    elif sort_field == 'total':
        productions_list.sort(key=lambda x: x['total_jour'], reverse=reverse_sort)

    # Calculer les totaux globaux - APPROCHE SÉCURISÉE
    totaux = {
        'extrusion': {
            'total': sum(p['extrusion'] for p in productions_list),
            'dechets': Decimal('0')
        },
        'soudure': {
            'total': sum(p['soudure'] for p in productions_list),
            'dechets': Decimal('0')
        },
        'imprimerie': {
            'total': sum(p['imprimerie'] for p in productions_list),
            'dechets': Decimal('0')
        },
        'recyclage': {
            'total': sum(p['recyclage'] for p in productions_list),
            'dechets': Decimal('0')
        }
    }

    # Calculer les déchets seulement pour les modèles qui ont ce champ
    try:
        totaux['extrusion']['dechets'] = queryset_extrusion.aggregate(total=Sum('dechets_kg'))['total'] or Decimal('0')
    except:
        totaux['extrusion']['dechets'] = Decimal('0')
    
    try:
        totaux['soudure']['dechets'] = queryset_soudure.aggregate(total=Sum('dechets_kg'))['total'] or Decimal('0')
    except:
        totaux['soudure']['dechets'] = Decimal('0')
    
    try:
        totaux['imprimerie']['dechets'] = queryset_imprimerie.aggregate(total=Sum('dechets_kg'))['total'] or Decimal('0')
    except:
        totaux['imprimerie']['dechets'] = Decimal('0')
    
    # Recyclage n'a pas dechets_kg, on laisse à 0

    # Calculer le total général et la moyenne
    total_general = totaux['extrusion']['total'] + totaux['soudure']['total'] + totaux['imprimerie']['total'] + totaux['recyclage']['total']
    totaux['general'] = {
        'total': total_general,
        'moyenne_jour': total_general / len(productions_list) if productions_list else Decimal('0')
    }

    # Pagination
    paginator = Paginator(productions_list, 25)
    page_obj = paginator.get_page(page_number)

    context = {
        'productions': page_obj,
        'totaux': totaux,
        'equipes': equipes,
        'periode_debut': periode_debut,
        'periode_fin': periode_fin,
        'sections': [
            ('extrusion', 'Extrusion'),
            ('soudure', 'Soudure'), 
            ('imprimerie', 'Imprimerie'),
            ('recyclage', 'Recyclage')
        ],
        'request': request,
    }
    
    return render(request, 'historique.html', context)

# ==========================================
# RAPPORTS
# ==========================================


# ==========================================
# API
# ==========================================

@login_required
def api_calculs_production(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=400)
    
    try:
        data = json.loads(request.body)
        section = data.get('section')
        
        if section == 'extrusion':
            return calculate_extrusion_metrics(data)
        elif section == 'imprimerie':
            return calculate_imprimerie_metrics(data)
        elif section == 'soudure':
            return calculate_soudure_metrics(data)
        elif section == 'recyclage':
            return calculate_recyclage_metrics(data)
        
        return JsonResponse({'error': 'Section invalide'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_dashboard_data(request):
    today = timezone.now().date()
    
    data = {
        'timestamp': timezone.now().isoformat(),
        'production_totale': float(get_production_totale_jour(today)),
        'machines_actives': Machine.objects.filter(etat='actif').count(),
        'alertes_count': Alerte.objects.filter(statut__in=['nouveau', 'en_cours']).count(),
        'efficacite_moyenne': float(get_efficacite_moyenne_jour(today)),
    }
    
    return JsonResponse(data)

# ==========================================
# FONCTIONS UTILITAIRES (VRAIES DONNÉES)
# ==========================================

def get_production_totale_jour(date):
    """Production totale d'un jour"""
    total = Decimal('0')
    
    total += ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
    total += ProductionImprimerie.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
    total += ProductionSoudure.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
    total += ProductionRecyclage.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
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
    
    return model.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')

def get_dechets_totaux_jour(date):
    """Total des déchets d'un jour"""
    total = Decimal('0')
    
    for model in [ProductionExtrusion, ProductionImprimerie, ProductionSoudure]:
        total += model.objects.filter(date_production=date).aggregate(
            Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    
    return total

def get_efficacite_moyenne_jour(date):
    """Efficacité moyenne d'un jour"""
    efficacite = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Avg('rendement_pourcentage'))['rendement_pourcentage__avg'] or Decimal('0')
    
    return round(efficacite, 1) if efficacite else 0

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
        
        zones_performance.append({
            'zone': zone,
            'production': prod_zone['total'] or 0,
            'machines_actives': int(prod_zone['machines'] or 0),
            'efficacite': round(prod_zone['efficacite'] or 0, 1)
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
            'efficacite': 95,  # Valeur par défaut
            'pourcentage_objectif': 0,
            'objectif': get_objectif_section('extrusion'),
        }
    
    # Calcul du temps de travail
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    # Agrégations
    aggregats = productions.aggregate(
        matiere_premiere=Sum('matiere_premiere_kg'),
        prod_finis=Sum('production_finis_kg'),
        prod_semi_finis=Sum('production_semi_finis_kg'),
        total_prod=Sum('total_production_kg'),
        dechets=Sum('dechets_kg'),
        machinistes_total=Sum('nombre_machinistes'),
        count_productions=Count('id')
    )
    
    # Extraire les valeurs
    nombre_moyen_machinistes = (aggregats['machinistes_total'] / aggregats['count_productions']) if aggregats['count_productions'] > 0 else 0
    
    total_prod = aggregats['total_prod'] or Decimal('0')
    dechets = aggregats['dechets'] or Decimal('0')
    matiere_premiere = aggregats['matiere_premiere'] or Decimal('0')
    
    # Calcul du taux de déchets
    taux_dechet = (dechets / (total_prod + dechets) * 100) if (total_prod + dechets) > 0 else Decimal('0')
    
    # Calcul du rendement (efficacité)
    efficacite = (total_prod / matiere_premiere * 100) if matiere_premiere > 0 else Decimal('0')
    
    # Objectif et pourcentage
    objectif = get_objectif_section('extrusion')
    pourcentage_objectif = calculer_pourcentage_section('extrusion', total_prod)
    
    return {
        'temps_travail': round(temps_total_minutes / 60, 1),
        'machinistes_moyen': round(nombre_moyen_machinistes, 0),
        'matiere_premiere': aggregats['matiere_premiere'] or 0,
        'production_finis': aggregats['prod_finis'] or 0,
        'production_semi_finis': aggregats['prod_semi_finis'] or 0,
        'production_totale': total_prod,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
        'efficacite': round(efficacite, 1),
        'pourcentage_objectif': pourcentage_objectif,
        'objectif': objectif,
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
            'efficacite': 92,  # Valeur par défaut
            'pourcentage_objectif': 0,
            'objectif': get_objectif_section('imprimerie'),
            'pourcentage_bobines_finies': 0,
            'pourcentage_bobines_semi_finies': 0,
        }
    
    # Calcul du temps de travail
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    # Agrégations
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bobines_finis=Sum('production_bobines_finies_kg'),
        bobines_semi_finis=Sum('production_bobines_semi_finies_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg'),
        count_productions=Count('id')
    )
    
    total = aggregats['total'] or Decimal('0')
    dechets = aggregats['dechets'] or Decimal('0')
    bobines_finies = aggregats['bobines_finis'] or Decimal('0')
    bobines_semi_finies = aggregats['bobines_semi_finis'] or Decimal('0')
    
    # Calculs
    taux_dechet = (dechets / (total + dechets) * 100) if (total + dechets) > 0 else Decimal('0')
    pourcentage_bobines_finies = (bobines_finies / total * 100) if total > 0 else Decimal('0')
    pourcentage_bobines_semi_finies = (bobines_semi_finies / total * 100) if total > 0 else Decimal('0')
    
    objectif = get_objectif_section('imprimerie')
    pourcentage_objectif = calculer_pourcentage_section('imprimerie', total)
    
    return {
        'temps_travail': round(temps_total_minutes / 60, 1),
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='imprimerie').count(),
        'equipes_actives': aggregats['count_productions'],
        'bobines_finies': bobines_finies,
        'bobines_semi_finies': bobines_semi_finies,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
        'efficacite': 92,  # À calculer selon vos critères
        'pourcentage_objectif': pourcentage_objectif,
        'objectif': objectif,
        'pourcentage_bobines_finies': round(pourcentage_bobines_finies, 1),
        'pourcentage_bobines_semi_finies': round(pourcentage_bobines_semi_finies, 1),
        'objectif_bobines_finies_atteint': pourcentage_bobines_finies >= 65,
    }

def get_soudure_details_jour(date):
    """Détails soudure du jour"""
    productions = ProductionSoudure.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'temps_travail': 0,
            'machines_actives': 0,
            'machines_totales': Machine.objects.filter(section='soudure').count(),
            'operateurs': 0,
            'production_bretelles': 0,
            'production_rema': 0,
            'production_batta': 0,
            'production_sac_emballage': 0,
            'production_totale': 0,
            'dechets_totaux': 0,
            'taux_dechet': 0,
            'efficacite': 88,
            'pourcentage_objectif': 0,
            'objectif': get_objectif_section('soudure'),
            'pourcentage_bretelles': 0,
            'pourcentage_rema': 0,
            'pourcentage_batta': 0,
            'pourcentage_sac_emballage': 0,
        }
    
    # Calcul du temps de travail
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    # Agrégations
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bretelles=Sum('production_bretelles_kg'),
        rema=Sum('production_rema_kg'),
        batta=Sum('production_batta_kg'),
        sac_emballage=Sum('production_sac_emballage_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg'),
        count_productions=Count('id')
    )
    
    # Extraction des valeurs
    total = aggregats['total'] or Decimal('0')
    dechets = aggregats['dechets'] or Decimal('0')
    bretelles = aggregats['bretelles'] or Decimal('0')
    rema = aggregats['rema'] or Decimal('0')
    batta = aggregats['batta'] or Decimal('0')
    sac_emballage = aggregats['sac_emballage'] or Decimal('0')
    
    # Calculs de pourcentages
    taux_dechet = (dechets / (total + dechets) * 100) if (total + dechets) > 0 else Decimal('0')
    pourcentage_bretelles = (bretelles / total * 100) if total > 0 else Decimal('0')
    pourcentage_rema = (rema / total * 100) if total > 0 else Decimal('0')
    pourcentage_batta = (batta / total * 100) if total > 0 else Decimal('0')
    pourcentage_sac_emballage = (sac_emballage / total * 100) if total > 0 else Decimal('0')
    
    objectif = get_objectif_section('soudure')
    pourcentage_objectif = calculer_pourcentage_section('soudure', total)
    
    production_specifique_total = bretelles + rema + batta + sac_emballage
    pourcentage_production_specifique = (production_specifique_total / total * 100) if total > 0 else Decimal('0')
    
    return {
        'temps_travail': round(temps_total_minutes / 60, 1),
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='soudure').count(),
        'operateurs': 8,  # À adapter selon vos données
        'production_bretelles': bretelles,
        'production_rema': rema,
        'production_batta': batta,
        'production_sac_emballage': sac_emballage,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
        'efficacite': 88,
        'pourcentage_objectif': pourcentage_objectif,
        'objectif': objectif,
        'pourcentage_bretelles': round(pourcentage_bretelles, 1),
        'pourcentage_rema': round(pourcentage_rema, 1),
        'pourcentage_batta': round(pourcentage_batta, 1),
        'pourcentage_sac_emballage': round(pourcentage_sac_emballage, 1),
        'production_specifique_total': production_specifique_total,
        'pourcentage_production_specifique': round(pourcentage_production_specifique, 1),
    }

def get_recyclage_details_jour(date):
    """Détails recyclage du jour"""
    productions = ProductionRecyclage.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'moulinex_actifs': 0,
            'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
            'operateurs': 0,
            'temps_travail': 0,
            'total_broyage': 0,
            'total_bache_noir': 0,
            'production_totale': 0,
            'taux_transformation': 0,
            'rendement': 0,
            'productivite_par_moulinex': 0,
            'pourcentage_objectif': 0,
            'objectif': get_objectif_section('recyclage'),
            'pourcentage_broyage': 0,
            'pourcentage_bache_noir': 0,
        }
    
    # Agrégations
    aggregats = productions.aggregate(
        moulinex=Avg('nombre_moulinex'),
        broyage=Sum('production_broyage_kg'),
        bache=Sum('production_bache_noir_kg'),
        total=Sum('total_production_kg'),
        count_productions=Count('id')
    )
    
    broyage = aggregats['broyage'] or Decimal('0')
    bache = aggregats['bache'] or Decimal('0')
    total = aggregats['total'] or Decimal('0')
    moulinex_avg = aggregats['moulinex'] or 1
    
    # Calculs
    taux_transformation = (bache / broyage * 100) if broyage > 0 else Decimal('0')
    productivite = (total / moulinex_avg) if moulinex_avg > 0 else Decimal('0')
    pourcentage_broyage = (broyage / total * 100) if total > 0 else Decimal('0')
    pourcentage_bache_noir = (bache / total * 100) if total > 0 else Decimal('0')
    
    objectif = get_objectif_section('recyclage')
    rendement = calculer_pourcentage_section('recyclage', total)
    objectif_transformation_atteint = taux_transformation >= 75
    
    return {
        'moulinex_actifs': round(moulinex_avg, 0),
        'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
        'operateurs': 6,
        'temps_travail': 0,  # À calculer si vous avez les heures
        'total_broyage': broyage,
        'total_bache_noir': bache,
        'production_totale': total,
        'taux_transformation': round(taux_transformation, 1),
        'rendement': round(rendement, 1),
        'productivite_par_moulinex': round(productivite, 1),
        'pourcentage_objectif': calculer_pourcentage_section('recyclage', total),
        'objectif': objectif,
        'pourcentage_broyage': round(pourcentage_broyage, 1),
        'pourcentage_bache_noir': round(pourcentage_bache_noir, 1),
        'objectif_transformation_atteint': objectif_transformation_atteint,
        'objectif_productivite': Decimal('500'),
        'pourcentage_productivite': round((productivite / 500 * 100) if productivite > 0 else 0, 1),
    }
def get_productions_filtrees(filters):
    """Obtenir productions filtrées pour l'historique"""
    date_filters = {}
    
    if filters.get('mois'):
        year, month = filters['mois'].split('-')
        date_filters['date_production__year'] = int(year)
        date_filters['date_production__month'] = int(month)
    
    if filters.get('date_debut'):
        date_filters['date_production__gte'] = filters['date_debut']
    
    if filters.get('date_fin'):
        date_filters['date_production__lte'] = filters['date_fin']
    
    productions_data = {
        'extrusion': ProductionExtrusion.objects.filter(**date_filters).select_related('zone', 'equipe', 'cree_par'),
        'imprimerie': ProductionImprimerie.objects.filter(**date_filters).select_related('cree_par'),
        'soudure': ProductionSoudure.objects.filter(**date_filters).select_related('cree_par'),
        'recyclage': ProductionRecyclage.objects.filter(**date_filters).select_related('equipe', 'cree_par'),
    }
    
    totaux = {
        'extrusion': productions_data['extrusion'].aggregate(total=Sum('total_production_kg'), dechets=Sum('dechets_kg')),
        'imprimerie': productions_data['imprimerie'].aggregate(total=Sum('total_production_kg'), dechets=Sum('dechets_kg')),
        'soudure': productions_data['soudure'].aggregate(total=Sum('total_production_kg'), dechets=Sum('dechets_kg')),
        'recyclage': productions_data['recyclage'].aggregate(total=Sum('total_production_kg')),
    }
    
    return productions_data, totaux

# Fonctions pour Dashboard Direction
def get_ca_mensuel(debut, fin):
    """CA mensuel - À adapter selon votre modèle de pricing"""
    production_totale = get_production_totale_periode(debut, fin)
    prix_moyen_kg = Decimal('320')  # Prix moyen par kg - À paramétrer
    return production_totale * prix_moyen_kg

def get_production_totale_periode(debut, fin):
    """Production totale sur période"""
    total = Decimal('0')
    for model in [ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage]:
        total += model.objects.filter(
            date_production__gte=debut,
            date_production__lte=fin
        ).aggregate(Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    return total

def calculate_percentage_of_goal(actual, goal):
    """Calculer pourcentage d'objectif atteint"""
    if goal == 0:
        return 0
    return round((actual / goal) * 100, 1)

def get_efficacite_globale_periode(debut, fin):
    """Efficacité globale période"""
    efficacite = ProductionExtrusion.objects.filter(
        date_production__gte=debut,
        date_production__lte=fin
    ).aggregate(Avg('rendement_pourcentage'))['rendement_pourcentage__avg'] or Decimal('0')
    return round(efficacite, 1)

def get_cout_production_moyen(debut, fin):
    """Coût de production moyen - Estimation basée sur consommation"""
    matiere_premiere = ProductionExtrusion.objects.filter(
        date_production__gte=debut,
        date_production__lte=fin
    ).aggregate(Sum('matiere_premiere_kg'))['matiere_premiere_kg__sum'] or Decimal('0')
    
    production_totale = get_production_totale_periode(debut, fin)
    
    if production_totale == 0:
        return Decimal('0')
    
    cout_matiere_kg = Decimal('600')  # À paramétrer
    cout_total = matiere_premiere * cout_matiere_kg
    
    return round(cout_total / production_totale, 0)

def get_performances_sections(debut, fin):
    """Performance détaillée par section"""
    sections = []
    
    for section_name, model in [
        ('Extrusion', ProductionExtrusion),
        ('Imprimerie', ProductionImprimerie),
        ('Soudure', ProductionSoudure),
        ('Recyclage', ProductionRecyclage)
    ]:
        data = model.objects.filter(
            date_production__gte=debut,
            date_production__lte=fin
        ).aggregate(
            production=Sum('total_production_kg'),
            dechets=Sum('dechets_kg') if hasattr(model, 'dechets_kg') else None
        )
        
        production = data['production'] or 0
        dechets = data['dechets'] or 0
        
        # Calcul performance globale (à adapter selon vos critères)
        performance = 85  # Placeholder - calculer selon vos KPIs
        
        sections.append({
            'nom': section_name,
            'production': production,
            'dechets': dechets,
            'performance': performance,
            'rendement': 87,  # À calculer
            'cout': 850,  # À calculer
        })
    
    return sections

def get_production_par_section(debut, fin):
    """Production par section pour graphiques"""
    return [
        float(get_production_section_periode('extrusion', debut, fin)),
        float(get_production_section_periode('imprimerie', debut, fin)),
        float(get_production_section_periode('soudure', debut, fin)),
        float(get_production_section_periode('recyclage', debut, fin)),
    ]

def get_production_section_periode(section, debut, fin):
    """Production d'une section sur une période"""
    models_map = {
        'extrusion': ProductionExtrusion,
        'imprimerie': ProductionImprimerie,
        'soudure': ProductionSoudure,
        'recyclage': ProductionRecyclage,
    }
    
    model = models_map.get(section)
    if not model:
        return Decimal('0')
    
    return model.objects.filter(
        date_production__gte=debut,
        date_production__lte=fin
    ).aggregate(Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')

# Fonctions Analytics Dashboard
def get_chart_data_for_dashboard():
    """Données pour graphiques Analytics"""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    # Simuler 30 jours de données
    days = []
    for i in range(30):
        day = debut_mois + timedelta(days=i)
        if day <= today:
            days.append(day.strftime('%d/%m'))
    
    return json.dumps({
        'months': days,
        'extrusion': [float(get_production_section_jour('extrusion', debut_mois + timedelta(days=i))) for i in range(len(days))],
        'soudure': [float(get_production_section_jour('soudure', debut_mois + timedelta(days=i))) for i in range(len(days))],
        'dechets': [float(get_dechets_totaux_jour(debut_mois + timedelta(days=i))) for i in range(len(days))],
        'bache_noir': [float(ProductionRecyclage.objects.filter(date_production=debut_mois + timedelta(days=i)).aggregate(Sum('production_bache_noir_kg'))['production_bache_noir_kg__sum'] or 0) for i in range(len(days))],
    })

def get_analytics_kpis():
    """KPIs pour Analytics"""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    production_mois = get_production_totale_periode(debut_mois, today)
    dechets_mois = sum([get_dechets_totaux_jour(debut_mois + timedelta(days=i)) for i in range((today - debut_mois).days + 1)])
    
    return {
        'production_totale_mois': production_mois,
        'croissance_production': 12.5,  # À calculer vs mois précédent
        'taux_dechet_mois': round((dechets_mois / production_mois * 100) if production_mois > 0 else 0, 1),
        'reduction_dechets': 2.3,  # À calculer vs mois précédent
        'efficacite_moyenne': get_efficacite_globale_periode(debut_mois, today),
        'amélioration_efficacite': 3.2,  # À calculer
        'taux_transformation': 78.5,  # À calculer depuis recyclage
        'amélioration_transformation': 5.1,
    }

def get_analytics_table_data():
    """Données tableau Analytics"""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    return {
        'extrusion': {
            'production': get_production_section_periode('extrusion', debut_mois, today),
            'dechets': ProductionExtrusion.objects.filter(date_production__gte=debut_mois, date_production__lte=today).aggregate(Sum('dechets_kg'))['dechets_kg__sum'] or 0,
            'taux_dechet': 2.8,
            'efficacite': 89.2,
        },
        'imprimerie': {
            'production': get_production_section_periode('imprimerie', debut_mois, today),
            'dechets': ProductionImprimerie.objects.filter(date_production__gte=debut_mois, date_production__lte=today).aggregate(Sum('dechets_kg'))['dechets_kg__sum'] or 0,
            'taux_dechet': 3.1,
            'efficacite': 91.5,
        },
        'soudure': {
            'production': get_production_section_periode('soudure', debut_mois, today),
            'dechets': ProductionSoudure.objects.filter(date_production__gte=debut_mois, date_production__lte=today).aggregate(Sum('dechets_kg'))['dechets_kg__sum'] or 0,
            'taux_dechet': 3.8,
            'efficacite': 85.3,
        },
        'recyclage': {
            'production': get_production_section_periode('recyclage', debut_mois, today),
            'taux_transformation': 78.2,
            'rendement': 82.5,
        },
    }

# Fonctions pour calculs temps réel
def calculate_extrusion_metrics(data):
    """Calculs extrusion"""
    matiere_premiere = float(data.get('matiere_premiere', 0))
    prod_finis = float(data.get('production_finis', 0))
    prod_semi_finis = float(data.get('production_semi_finis', 0))
    dechets = float(data.get('dechets', 0))
    nb_machines = int(data.get('nombre_machines', 1))
    
    total_production = prod_finis + prod_semi_finis
    rendement = (total_production / matiere_premiere * 100) if matiere_premiere > 0 else 0
    taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
    prod_par_machine = total_production / nb_machines if nb_machines > 0 else 0
    
    return JsonResponse({
        'total_production': round(total_production, 1),
        'rendement': round(rendement, 1),
        'taux_dechet': round(taux_dechet, 1),
        'production_par_machine': round(prod_par_machine, 1),
    })

def calculate_imprimerie_metrics(data):
    """Calculs imprimerie"""
    bobines_finies = float(data.get('bobines_finies', 0))
    bobines_semi_finies = float(data.get('bobines_semi_finies', 0))
    dechets = float(data.get('dechets', 0))
    
    total_production = bobines_finies + bobines_semi_finies
    taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
    
    return JsonResponse({
        'total_production': round(total_production, 1),
        'taux_dechet': round(taux_dechet, 1),
    })

def calculate_soudure_metrics(data):
    """Calculs soudure"""
    bobines_finies = float(data.get('bobines_finies', 0))
    bretelles = float(data.get('bretelles', 0))
    rema = float(data.get('rema', 0))
    batta = float(data.get('batta', 0))
    sac_emballage = float(data.get('sac_emballage', 0))  # NOUVEAU
    dechets = float(data.get('dechets', 0))
    
    total_specifique = bretelles + rema + batta + sac_emballage
    total_production = bobines_finies + total_specifique
    taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
    
    return JsonResponse({
        'total_production': round(total_production, 1),
        'total_specifique': round(total_specifique, 1),
        'taux_dechet': round(taux_dechet, 1),
    })

def calculate_recyclage_metrics(data):
    """Calculs recyclage"""
    broyage = float(data.get('broyage', 0))
    bache_noir = float(data.get('bache_noir', 0))
    nb_moulinex = int(data.get('nombre_moulinex', 1))
    
    total_production = broyage + bache_noir
    prod_par_moulinex = total_production / nb_moulinex if nb_moulinex > 0 else 0
    taux_transformation = (bache_noir / broyage * 100) if broyage > 0 else 0
    
    return JsonResponse({
        'total_production': round(total_production, 1),
        'production_par_moulinex': round(prod_par_moulinex, 1),
        'taux_transformation': round(taux_transformation, 1),
    })

# Fonctions pour rapports
@login_required
def rapports_view(request):
    """
    Vue principale pour la génération de rapports
    Gère à la fois l'affichage HTML et les exports PDF/Excel
    """
    # Vérification des permissions
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé. Seuls les superviseurs et administrateurs peuvent générer des rapports.')
        return redirect('dashboard')
    
    # Récupération des paramètres
    mois_selectionne = request.GET.get('mois', timezone.now().strftime('%m'))
    annee_selectionnee = request.GET.get('annee', timezone.now().year)
    section_selectionnee = request.GET.get('section', '')
    export_type = request.GET.get('export')
    
    # Génération du rapport si des paramètres sont fournis
    rapport = None
    if request.GET.get('mois') or export_type:
        try:
            rapport = generer_rapport_mensuel(
                int(annee_selectionnee), 
                int(mois_selectionne), 
                section_selectionnee
            )
        except Exception as e:
            messages.error(request, f'Erreur lors de la génération du rapport: {str(e)}')
    
    # Gestion des exports
    if export_type == 'excel' and rapport:
        return generer_rapport_excel(rapport, int(annee_selectionnee), int(mois_selectionne), section_selectionnee)
    elif export_type == 'pdf' and rapport:
        return generer_rapport_pdf(rapport, int(annee_selectionnee), int(mois_selectionne), section_selectionnee)
    
    # Préparation du contexte pour l'affichage HTML
    context = {
        'rapport': rapport,
        'mois_disponibles': get_mois_disponibles(),
        'annees_disponibles': range(2023, timezone.now().year + 1),  # Depuis 2023
        'annee_courante': int(annee_selectionnee),
        'mois_nom': get_nom_mois(int(mois_selectionne)) if request.GET.get('mois') else '',
        'section_selectionnee': section_selectionnee,
    }
    
    # Ajout des données pour les graphiques si rapport existe
    if rapport:
        context.update({
            'labels_sections': json.dumps([s['nom'] for s in rapport['sections']]),
            'data_sections': json.dumps([s['production'] for s in rapport['sections']]),
        })
    else:
        context.update({
            'labels_sections': json.dumps([]),
            'data_sections': json.dumps([]),
        })
    
    return render(request, 'rapports.html', context)




def generer_rapport_mensuel(annee, mois, section):
    """
    Génère les données du rapport mensuel
    À ADAPTER avec vos vraies données de base de données
    """
    # Données simulées - REMPLACEZ par vos vraies données
    sections_data = [
        {
            'nom': 'Extrusion',
            'production': 42150,
            'rendement': 97.2,
            'dechets': 1150,
            'taux_dechet': 2.8,
            'jours_actifs': 22,
            'jours_total': 30,
            'production_jour': 1916,
            'production_journaliere': []
        },
        {
            'nom': 'Imprimerie', 
            'production': 21580,
            'rendement': 96.5,
            'dechets': 750,
            'taux_dechet': 3.5,
            'jours_actifs': 20,
            'jours_total': 30,
            'production_jour': 1079,
            'production_journaliere': []
        },
        {
            'nom': 'Soudure',
            'production': 12540,
            'rendement': 96.0,
            'dechets': 500,
            'taux_dechet': 4.0,
            'jours_actifs': 18,
            'jours_total': 30,
            'production_jour': 697,
            'production_journaliere': []
        },
        {
            'nom': 'Recyclage',
            'production': 9150,
            'rendement': 97.5,
            'dechets': 0,
            'taux_dechet': 0,
            'jours_actifs': 15,
            'jours_total': 30,
            'production_jour': 610,
            'production_journaliere': []
        }
    ]
    
    # Générer des données journalières simulées
    for section_data in sections_data:
        for i in range(1, section_data['jours_actifs'] + 1):
            section_data['production_journaliere'].append({
                'date': datetime(annee, mois, i),
                'equipe': 'A' if i % 2 == 0 else 'B',
                'production': section_data['production_jour'] * (0.8 + 0.4 * (i % 10) / 10),
                'rendement': section_data['rendement'] * (0.95 + 0.1 * (i % 10) / 10),
                'dechets': section_data['taux_dechet'] * (0.8 + 0.4 * (i % 10) / 10),
                'valide': True,
                'statut': 'Validé'
            })
    
    # Filtrer par section si spécifié
    if section:
        sections_data = [s for s in sections_data if s['nom'].lower() == section]
    
    # Calculer les totaux généraux
    total_production = sum(s['production'] for s in sections_data)
    rendement_moyen = sum(s['rendement'] for s in sections_data) / len(sections_data) if sections_data else 0
    taux_dechet_moyen = sum(s['taux_dechet'] for s in sections_data) / len(sections_data) if sections_data else 0
    
    return {
        'total_production': total_production,
        'rendement_moyen': rendement_moyen,
        'taux_dechet_moyen': taux_dechet_moyen,
        'jours_production': max(s['jours_actifs'] for s in sections_data) if sections_data else 0,
        'taux_activite': (max(s['jours_actifs'] for s in sections_data) / 30 * 100) if sections_data else 0,
        'evolution_production': 5.2,  # Données simulées
        'evolution_rendement': 1.5,
        'evolution_dechets': -0.8,
        'sections': sections_data
    }


def generer_rapport_excel(rapport, annee, mois, section):
    """Génère un rapport Excel détaillé"""
    # Créer un DataFrame pour les données détaillées
    data_detaille = []
    for section_data in rapport.sections:
        for jour in section_data.production_journaliere:
            data_detaille.append({
                'Section': section_data.nom,
                'Date': jour.date.strftime('%d/%m/%Y'),
                'Équipe': jour.equipe,
                'Production (kg)': jour.production,
                'Rendement (%)': jour.rendement,
                'Déchets (%)': jour.dechets,
                'Statut': jour.statut
            })
    
    # Créer un DataFrame pour la synthèse
    data_synthese = []
    for section_data in rapport.sections:
        data_synthese.append({
            'Section': section_data.nom,
            'Production Totale (kg)': section_data.production,
            'Rendement Moyen (%)': section_data.rendement,
            'Déchets Totaux (kg)': section_data.dechets,
            'Taux Déchet (%)': section_data.taux_dechet,
            'Jours Actifs': f"{section_data.jours_actifs}/{section_data.jours_total}",
            'Production/Jour (kg)': section_data.production_jour
        })
    
    # Créer le fichier Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Feuille détaillée
        if data_detaille:
            df_detaille = pd.DataFrame(data_detaille)
            df_detaille.to_excel(writer, sheet_name='Détails Journaliers', index=False)
        
        # Feuille synthèse
        df_synthese = pd.DataFrame(data_synthese)
        df_synthese.to_excel(writer, sheet_name='Synthèse Sections', index=False)
        
        # Feuille indicateurs
        indicateurs_data = {
            'Indicateur': [
                'Production Totale (kg)',
                'Rendement Moyen (%)',
                'Taux Déchet Moyen (%)',
                'Jours de Production',
                'Taux Activité (%)',
                'Évolution Production (%)',
                'Évolution Rendement (%)'
            ],
            'Valeur': [
                rapport.total_production,
                rapport.rendement_moyen,
                rapport.taux_dechet_moyen,
                rapport.jours_production,
                rapport.taux_activite,
                rapport.evolution_production,
                rapport.evolution_rendement
            ]
        }
        df_indicateurs = pd.DataFrame(indicateurs_data)
        df_indicateurs.to_excel(writer, sheet_name='Indicateurs Clés', index=False)
    
    # Préparer la réponse
    output.seek(0)
    nom_fichier = f"rapport_production_{get_nom_mois(mois)}_{annee}"
    if section:
        nom_fichier += f"_{section}"
    nom_fichier += ".xlsx"
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    
    return response

def generer_rapport_pdf(rapport, annee, mois, section):
    """Génère un rapport PDF professionnel"""
    context = {
        'rapport': rapport,
        'annee': annee,
        'mois': get_nom_mois(mois),
        'section': section,
        'date_generation': timezone.now(),
        'entreprise': 'SOFEM-CI',
    }
    
    # Rendre le template HTML
    html_string = render_to_string('reports/rapport_pdf.html', context)
    
    # Configuration PDF
    font_config = FontConfiguration()
    html = HTML(string=html_string)
    
    # Générer le PDF
    pdf_file = html.write_pdf(font_config=font_config)
    
    # Préparer la réponse
    nom_fichier = f"rapport_production_{get_nom_mois(mois)}_{annee}"
    if section:
        nom_fichier += f"_{section}"
    nom_fichier += ".pdf"
    
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nom_fichier}"'
    
    return response

def get_mois_disponibles():
    """Retourne la liste des mois disponibles"""
    return [
        {'value': '01', 'nom': 'Janvier'},
        {'value': '02', 'nom': 'Février'},
        {'value': '03', 'nom': 'Mars'},
        {'value': '04', 'nom': 'Avril'},
        {'value': '05', 'nom': 'Mai'},
        {'value': '06', 'nom': 'Juin'},
        {'value': '07', 'nom': 'Juillet'},
        {'value': '08', 'nom': 'Août'},
        {'value': '09', 'nom': 'Septembre'},
        {'value': '10', 'nom': 'Octobre'},
        {'value': '11', 'nom': 'Novembre'},
        {'value': '12', 'nom': 'Décembre'},
    ]

def get_nom_mois(mois):
    """Retourne le nom du mois"""
    mois_noms = {
        1: 'Janvier', 2: 'Février', 3: 'Mars', 4: 'Avril',
        5: 'Mai', 6: 'Juin', 7: 'Juillet', 8: 'Août',
        9: 'Septembre', 10: 'Octobre', 11: 'Novembre', 12: 'Décembre'
    }
    return mois_noms.get(mois, '')





@login_required
def machines_list_view(request):
    """Liste de toutes les machines"""
    if request.user.role not in ['admin', 'superviseur']:
        messages.error(request, 'Accès refusé. Réservé aux administrateurs.')
        return redirect('dashboard')
    
    # Filtres
    section_filter = request.GET.get('section', '')
    etat_filter = request.GET.get('etat', '')
    zone_filter = request.GET.get('zone', '')
    
    machines = Machine.objects.all().select_related('zone_extrusion')
    
    if section_filter:
        machines = machines.filter(section=section_filter)
    if etat_filter:
        machines = machines.filter(etat=etat_filter)
    if zone_filter:
        machines = machines.filter(zone_extrusion__numero=zone_filter)
    
    # Pagination
    paginator = Paginator(machines.order_by('section', 'numero'), 20)
    page_number = request.GET.get('page')
    machines_page = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': Machine.objects.count(),
        'actives': Machine.objects.filter(etat='actif').count(),
        'maintenance': Machine.objects.filter(etat='maintenance').count(),
        'pannes': Machine.objects.filter(etat='panne').count(),
        'par_section': Machine.objects.values('section').annotate(count=Count('id')),
    }
    
    context = {
        'machines': machines_page,
        'stats': stats,
        'sections': Machine.SECTIONS,
        'etats': Machine.ETATS,
        'zones': ZoneExtrusion.objects.filter(active=True),
        'section_filter': section_filter,
        'etat_filter': etat_filter,
        'zone_filter': zone_filter,
    }
    
    return render(request, 'machines_list.html', context)

@login_required
def machine_create_view(request):
    """Créer une nouvelle machine"""
    if request.user.role not in ['admin', 'superviseur']:
        messages.error(request, 'Accès refusé.')
        return redirect('machines_list')
    
    if request.method == 'POST':
        form = MachineForm(request.POST)
        
        # DEBUG - Affichage dans la console
        print("=" * 50)
        print("DEBUG CRÉATION MACHINE")
        print("=" * 50)
        print(f"Formulaire valide: {form.is_valid()}")
        
        if form.is_valid():
            try:
                machine = form.save()
                print(f"✅ Machine créée: {machine.numero}")
                messages.success(request, f'Machine {machine.numero} créée avec succès !')
                return redirect('machines_list')
            except Exception as e:
                print(f"❌ Erreur sauvegarde: {e}")
                messages.error(request, f'Erreur lors de la sauvegarde: {str(e)}')
        else:
            # Afficher les erreurs dans la console
            print("❌ ERREURS DU FORMULAIRE:")
            for field, errors in form.errors.items():
                print(f"  {field}: {errors}")
            
            # Ajouter un message d'erreur visible
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = MachineForm()
    
    context = {
        'form': form,
        'action': 'Créer',
        'show_errors': request.method == 'POST',  # Pour afficher les erreurs
    }
    
    return render(request, 'machine_form.html', context)

@login_required
def machine_edit_view(request, machine_id):
    """Modifier une machine existante"""
    if request.user.role not in ['admin', 'superviseur']:
        messages.error(request, 'Accès refusé.')
        return redirect('machines_list')
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        form = MachineForm(request.POST, instance=machine)
        if form.is_valid():
            machine = form.save()
            messages.success(request, f'Machine {machine.numero} modifiée avec succès !')
            return redirect('machines_list')
        else:
            messages.error(request, 'Erreur dans le formulaire.')
    else:
        form = MachineForm(instance=machine)
    
    context = {
        'form': form,
        'machine': machine,
        'action': 'Modifier',
    }
    
    return render(request, 'machine_form.html', context)

@login_required
def machine_delete_view(request, machine_id):
    """Supprimer une machine"""
    if request.user.role not in ['admin']:
        messages.error(request, 'Accès refusé. Seuls les administrateurs peuvent supprimer.')
        return redirect('machines_list')
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        numero = machine.numero
        machine.delete()
        messages.success(request, f'Machine {numero} supprimée avec succès.')
        return redirect('machines_list')
    
    context = {
        'machine': machine,
    }
    
    return render(request, 'machine_confirm_delete.html', context)

@login_required
def machine_detail_view(request, machine_id):
    """Détails d'une machine"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Historique de production pour cette machine (si extrusion)
    historique = []
    if machine.section == 'extrusion' and machine.zone_extrusion:
        historique = ProductionExtrusion.objects.filter(
            zone=machine.zone_extrusion
        ).order_by('-date_production')[:10]
    
    context = {
        'machine': machine,
        'historique': historique,
    }
    
    return render(request, 'machine_detail.html', context)

@login_required
def machine_change_status_ajax(request, machine_id):
    """Changer le statut d'une machine (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    if request.user.role not in ['admin', 'superviseur']:
        return JsonResponse({'success': False, 'message': 'Accès refusé'})
    
    machine = get_object_or_404(Machine, id=machine_id)
    new_status = request.POST.get('status')
    
    if new_status not in dict(Machine.ETATS).keys():
        return JsonResponse({'success': False, 'message': 'Statut invalide'})
    
    machine.etat = new_status
    machine.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Statut de la machine {machine.numero} mis à jour',
        'new_status': machine.get_etat_display()
    })


@login_required
def api_create_zone(request):
    """API pour créer une zone rapidement"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    if request.user.role not in ['admin', 'superviseur']:
        return JsonResponse({'success': False, 'message': 'Accès refusé'})
    
    try:
        data = json.loads(request.body)
        numero = int(data.get('numero'))
        nom = data.get('nom')
        
        # Validation
        if not numero or numero < 1 or numero > 10:
            return JsonResponse({'success': False, 'message': 'Numéro de zone invalide (1-10)'})
        
        if not nom:
            return JsonResponse({'success': False, 'message': 'Nom de zone requis'})
        
        # Vérifier si existe déjà
        if ZoneExtrusion.objects.filter(numero=numero).exists():
            return JsonResponse({'success': False, 'message': f'La zone {numero} existe déjà'})
        
        # Créer la zone
        zone = ZoneExtrusion.objects.create(
            numero=numero,
            nom=nom,
            nombre_machines_max=4,
            active=True
        )
        
        return JsonResponse({
            'success': True,
            'zone': {
                'id': zone.id,
                'numero': zone.numero,
                'nom': zone.nom
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})




# Ajouter dans sofemci/views.py

from .ia_predictive import (
    analyser_toutes_machines,
    analyser_machine_specifique,
    obtenir_machines_a_risque,
    obtenir_alertes_actives,
    statistiques_parc_machines,
    simuler_donnees_capteurs,
    enregistrer_maintenance,
    enregistrer_panne
)

# ==========================================
# DASHBOARD IA - MAINTENANCE PRÉDICTIVE
# ==========================================
@login_required
def dashboard_ia_view(request):
    try:
        # Récupérer toutes les machines avec gestion des erreurs
        machines = Machine.objects.all()
        
        # Calculer les statistiques du parc avec valeurs par défaut
        stats_parc = {
            'score_sante_moyen': machines.aggregate(
                avg=Avg('score_sante_global')
            )['avg'] or 85.0,
            'machines_risque_critique': machines.filter(
                probabilite_panne_7_jours__gte=70
            ).count(),
            'machines_risque_eleve': machines.filter(
                probabilite_panne_7_jours__gte=40,
                probabilite_panne_7_jours__lt=70
            ).count(),
            'anomalies_detectees': machines.filter(
                anomalie_detectee=True
            ).count()
        }
        
        # Machines critiques avec gestion des erreurs
        machines_critiques = []
        for machine in machines.filter(probabilite_panne_7_jours__gte=70):
            try:
                # Vérifier si la méthode est_en_surchauffe existe et fonctionne
                if hasattr(machine, 'est_en_surchauffe'):
                    machine_data = {
                        'id': machine.id,
                        'numero': machine.numero,
                        'section': machine.section,
                        'get_section_display': machine.get_section_display(),
                        'probabilite_panne_7_jours': machine.probabilite_panne_7_jours or 0,
                        'score_sante_global': machine.score_sante_global or 0,
                        'temperature_actuelle': getattr(machine, 'temperature_actuelle', None),
                        'heures_fonctionnement_totales': getattr(machine, 'heures_fonctionnement_totales', 0),
                        'est_en_surchauffe': machine.est_en_surchauffe() if callable(getattr(machine, 'est_en_surchauffe', None)) else False,
                        'facteurs_risque': getattr(machine, 'get_facteurs_risque', lambda: [])()
                    }
                    machines_critiques.append(machine_data)
            except Exception as e:
                logger.error(f"Erreur avec machine {machine.id}: {e}")
                continue
        
        # Alertes IA actives
        alertes = AlerteIA.objects.filter(
            statut__in=['nouvelle', 'en_traitement']
        ).select_related('machine')[:10]
        
        # Machines actives pour le tableau
        machines_actives = []
        for machine in machines:
            try:
                machine_data = {
                    'id': machine.id,
                    'numero': machine.numero,
                    'section': machine.section,
                    'get_section_display': machine.get_section_display(),
                    'score_sante_global': machine.score_sante_global or 0,
                    'probabilite_panne_7_jours': machine.probabilite_panne_7_jours or 0,
                    'temperature_actuelle': getattr(machine, 'temperature_actuelle', None),
                    'consommation_electrique_kwh': getattr(machine, 'consommation_electrique_kwh', 0),
                    'est_en_surchauffe': machine.est_en_surchauffe() if callable(getattr(machine, 'est_en_surchauffe', None)) else False,
                    'est_en_surconsommation': getattr(machine, 'est_en_surconsommation', lambda: False)(),
                    'anomalie_detectee': getattr(machine, 'anomalie_detectee', False)
                }
                machines_actives.append(machine_data)
            except Exception as e:
                logger.error(f"Erreur avec machine active {machine.id}: {e}")
                continue
        
        context = {
            'stats_parc': stats_parc,
            'machines_critiques': machines_critiques,
            'alertes': alertes,
            'machines_actives': machines_actives,
        }
        
        return render(request, 'dashboard_ia.html', context)
        
    except Exception as e:
        logger.error(f"Erreur dans dashboard_ia_view: {e}")
        # Retourner un contexte vide sécurisé
        context = {
            'stats_parc': {
                'score_sante_moyen': 0,
                'machines_risque_critique': 0,
                'machines_risque_eleve': 0,
                'anomalies_detectees': 0
            },
            'machines_critiques': [],
            'alertes': [],
            'machines_actives': [],
        }
        return render(request, 'ia/dashboard_ia.html', context)
@login_required
def machine_detail_ia_view(request, machine_id):
    """Vue détaillée d'une machine avec analyse IA"""
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Analyser la machine - SANS créer de nouvelles alertes si elles existent déjà
    try:
        analyse = analyser_machine_specifique(machine_id)
    except Exception as e:
        # Si l'analyse échoue à cause d'alertes dupliquées, on continue sans bloquer
        print(f"Erreur lors de l'analyse: {e}")
        analyse = {
            'probabilite_panne_7j': machine.probabilite_panne_7_jours,
            'score_sante': machine.score_sante_global,
            'niveau_risque': 'normal',
            'facteurs_risque': [],
            'recommandations': []
        }
    
    # Historique de la machine
    historique = HistoriqueMachine.objects.filter(
        machine=machine
    ).order_by('-date_evenement')[:20]
    
    # Alertes pour cette machine
    alertes = AlerteIA.objects.filter(
        machine=machine,
        statut__in=['nouvelle', 'vue', 'en_traitement']
    ).order_by('-date_creation')
    
    # Graphique évolution température et consommation
    historique_recent = HistoriqueMachine.objects.filter(
        machine=machine,
        type_evenement='mesure',
        date_evenement__gte=timezone.now() - timedelta(days=30)
    ).order_by('date_evenement')
    
    donnees_graphique = {
        'dates': [h.date_evenement.strftime('%d/%m') for h in historique_recent],
        'temperatures': [float(h.temperature) if h.temperature else 0 for h in historique_recent],
        'consommations': [float(h.consommation_kwh) if h.consommation_kwh else 0 for h in historique_recent],
    }
    
    context = {
        'machine': machine,
        'analyse': analyse,
        'historique': historique,
        'alertes': alertes,
        'donnees_graphique': json.dumps(donnees_graphique),
    }
    
    return render(request, 'machine_detail_ia.html', context)

    """Vue détaillée d'une machine avec analyse IA"""
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Analyser la machine
    analyse = analyser_machine_specifique(machine_id)
    
    # Historique de la machine
    historique = HistoriqueMachine.objects.filter(
        machine=machine
    ).order_by('-date_evenement')[:20]
    
    # Alertes pour cette machine
    alertes = AlerteIA.objects.filter(
        machine=machine,
        statut__in=['nouvelle', 'vue', 'en_traitement']
    ).order_by('-date_creation')
    
    # Graphique évolution température et consommation
    historique_recent = HistoriqueMachine.objects.filter(
        machine=machine,
        type_evenement='mesure',
        date_evenement__gte=timezone.now() - timedelta(days=30)
    ).order_by('date_evenement')
    
    donnees_graphique = {
        'dates': [h.date_evenement.strftime('%d/%m') for h in historique_recent],
        'temperatures': [float(h.temperature) if h.temperature else 0 for h in historique_recent],
        'consommations': [float(h.consommation_kwh) if h.consommation_kwh else 0 for h in historique_recent],
    }
    
    context = {
        'machine': machine,
        'analyse': analyse,
        'historique': historique,
        'alertes': alertes,
        'donnees_graphique': json.dumps(donnees_graphique),
    }
    
    return render(request, 'machine_detail_ia.html', context)


@login_required
def lancer_analyse_complete(request):
    """Lance l'analyse IA sur toutes les machines"""
    
    if request.user.role not in ['admin', 'superviseur']:
        messages.error(request, 'Permission refusée.')
        return redirect('dashboard_ia')
    
    try:
        resultats = analyser_toutes_machines()
        
        # Compter les résultats
        critiques = sum(1 for r in resultats if r['resultat']['niveau_risque'] == 'critique')
        eleves = sum(1 for r in resultats if r['resultat']['niveau_risque'] == 'élevé')
        
        messages.success(
            request,
            f'Analyse complète terminée. {len(resultats)} machines analysées. '
            f'{critiques} critiques, {eleves} risque élevé.'
        )
    except Exception as e:
        messages.error(request, f'Erreur lors de l\'analyse: {str(e)}')
    
    return redirect('dashboard_ia')


@login_required
def enregistrer_maintenance_view(request, machine_id):
    """Formulaire d'enregistrement de maintenance"""
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        try:
            description = request.POST.get('description')
            technicien = request.POST.get('technicien')
            pieces = request.POST.get('pieces_remplacees', '')
            
            enregistrer_maintenance(machine, description, technicien, pieces)
            
            messages.success(request, f'Maintenance enregistrée pour {machine.numero}')
            return redirect('machine_detail_ia', machine_id=machine_id)
        
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    context = {'machine': machine}
    return render(request, 'enregistrer_maintenance.html', context)


@login_required
def enregistrer_panne_view(request, machine_id):
    """Formulaire d'enregistrement de panne"""
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        try:
            description = request.POST.get('description')
            duree = request.POST.get('duree_arret')
            technicien = request.POST.get('technicien', '')
            cout = request.POST.get('cout', None)
            
            enregistrer_panne(machine, description, float(duree), technicien, cout)
            
            messages.warning(request, f'Panne enregistrée pour {machine.numero}')
            return redirect('machine_detail_ia', machine_id=machine_id)
        
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    context = {'machine': machine}
    return render(request, 'enregistrer_panne.html', context)


@login_required
def traiter_alerte_ia(request, alerte_id):
    """Prendre en charge ou résoudre une alerte IA"""
    
    alerte = get_object_or_404(AlerteIA, id=alerte_id)
    
    action = request.POST.get('action')
    
    if action == 'prendre_en_charge':
        alerte.prendre_en_charge(request.user)
        messages.info(request, 'Alerte prise en charge')
    
    elif action == 'resoudre':
        commentaire = request.POST.get('commentaire', '')
        alerte.resoudre(commentaire)
        messages.success(request, 'Alerte résolue')
    
    elif action == 'ignorer':
        alerte.statut = 'ignoree'
        alerte.save()
        messages.info(request, 'Alerte ignorée')
    
    return redirect('dashboard_ia')


@login_required
def liste_alertes_ia(request):
    """Liste complète des alertes IA avec filtres"""
    
    # Filtres
    niveau = request.GET.get('niveau')
    statut = request.GET.get('statut')
    section = request.GET.get('section')
    
    alertes = AlerteIA.objects.select_related('machine', 'traite_par').all()
    
    if niveau:
        alertes = alertes.filter(niveau=niveau)
    if statut:
        alertes = alertes.filter(statut=statut)
    if section:
        alertes = alertes.filter(machine__section=section)
    
    alertes = alertes.order_by('-priorite', '-date_creation')
    
    # Pagination
    paginator = Paginator(alertes, 20)
    page = request.GET.get('page')
    alertes_page = paginator.get_page(page)
    
    context = {
        'alertes': alertes_page,
        'niveau_filtre': niveau,
        'statut_filtre': statut,
        'section_filtre': section,
    }
    
    return render(request, 'liste_alertes_ia.html', context)


@login_required
def simuler_capteurs_view(request, machine_id):
    """Simulation de mise à jour des capteurs (pour tests)"""
    
    if request.user.role != 'admin':
        messages.error(request, 'Accès admin requis')
        return redirect('dashboard_ia')
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        temperature = request.POST.get('temperature')
        consommation = request.POST.get('consommation')
        
        temp = float(temperature) if temperature else None
        conso = float(consommation) if consommation else None
        
        resultat = simuler_donnees_capteurs(machine, temp, conso)
        
        messages.success(
            request,
            f'Capteurs mis à jour. Score santé: {resultat["score_sante"]}%, '
            f'Risque panne 7j: {resultat["probabilite_panne_7j"]}%'
        )
        
        return redirect('machine_detail_ia', machine_id=machine_id)
    
    context = {'machine': machine}
    return render(request, 'simuler_capteurs.html', context)


# ==========================================
# API POUR DONNÉES TEMPS RÉEL
# ==========================================

@login_required
def api_machines_status(request):
    """API retournant le statut de toutes les machines"""
    
    machines = Machine.objects.filter(etat='actif').values(
        'id', 'numero', 'section', 'score_sante_global',
        'probabilite_panne_7_jours', 'temperature_actuelle',
        'consommation_electrique_kwh', 'anomalie_detectee'
    )
    
    return JsonResponse({
        'machines': list(machines),
        'timestamp': timezone.now().isoformat()
    })


@login_required
def api_alertes_count(request):
    """API retournant le nombre d'alertes par niveau"""
    
    alertes = AlerteIA.objects.filter(
        statut__in=['nouvelle', 'vue']
    ).values('niveau').annotate(count=Count('id'))
    
    return JsonResponse({
        'alertes': list(alertes),
        'total': sum(a['count'] for a in alertes)
    })


@login_required
def api_statistiques_ia(request):
    """API retournant les statistiques IA"""
    
    stats = statistiques_parc_machines()
    
    return JsonResponse({
        'statistiques': stats,
        'timestamp': timezone.now().isoformat()
    })



# Ajouter après les imports existants

def calculer_pourcentage_production(production_actuelle, production_reference=None):
    """
    Calcule le pourcentage de production par rapport à une référence
    Si pas de référence, utilise l'objectif journalier standard
    """
    if production_reference is None:
        # Objectifs journaliers standards par section (à ajuster selon votre réalité)
        objectifs_journaliers = {
            'extrusion': Decimal('35000'),  # 35 tonnes
            'imprimerie': Decimal('20000'),  # 20 tonnes
            'soudure': Decimal('12000'),     # 12 tonnes
            'recyclage': Decimal('8000'),    # 8 tonnes
        }
        production_reference = sum(objectifs_journaliers.values())
    
    if production_reference == 0:
        return 0
    
    pourcentage = (production_actuelle / production_reference) * 100
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
    
    return round((production_actuelle / objectif) * 100, 1)


def get_objectif_section(section):
    """Retourne l'objectif journalier d'une section"""
    objectifs = {
        'extrusion': Decimal('35000'),
        'imprimerie': Decimal('20000'),
        'soudure': Decimal('12000'),
        'recyclage': Decimal('8000'),
    }
    return objectifs.get(section, Decimal('10000'))


@login_required
def api_production_details(request, production_id):
    """API pour obtenir les détails d'une production"""
    date_str = str(production_id)
    
    # Parser la date depuis l'ID (format: YYYYMMDD)
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        date = datetime(year, month, day).date()
    except:
        return JsonResponse({'error': 'Date invalide'}, status=400)
    
    # Récupérer toutes les productions de cette date
    details = {
        'date': date.strftime('%d/%m/%Y'),
        'extrusion': [],
        'imprimerie': [],
        'soudure': [],
        'recyclage': []
    }
    
    # Extrusion
    for prod in ProductionExtrusion.objects.filter(date_production=date):
        details['extrusion'].append({
            'zone': f"Zone {prod.zone.numero}",
            'equipe': prod.equipe.get_nom_display(),
            'production': float(prod.total_production_kg),
            'dechets': float(prod.dechets_kg),
            'rendement': float(prod.rendement_pourcentage or 0)
        })
    
    # Imprimerie
    for prod in ProductionImprimerie.objects.filter(date_production=date):
        details['imprimerie'].append({
            'production': float(prod.total_production_kg),
            'dechets': float(prod.dechets_kg),
            'machines': prod.nombre_machines_actives
        })
    
    # Soudure
    for prod in ProductionSoudure.objects.filter(date_production=date):
        details['soudure'].append({
            'production': float(prod.total_production_kg),
            'bretelles': float(prod.production_bretelles_kg),
            'rema': float(prod.production_rema_kg),
            'batta': float(prod.production_batta_kg),
            'sac_emballage': float(prod.production_sac_emballage_kg),
            'dechets': float(prod.dechets_kg)
        })
    
    # Recyclage
    for prod in ProductionRecyclage.objects.filter(date_production=date):
        details['recyclage'].append({
            'equipe': prod.equipe.get_nom_display(),
            'broyage': float(prod.production_broyage_kg),
            'bache_noir': float(prod.production_bache_noir_kg),
            'moulinex': prod.nombre_moulinex
        })
    
    return JsonResponse(details)


@login_required
def export_fiche_production(request, production_id):
    """Exporter une fiche de production en PDF"""
    # Implémenter avec reportlab ou weasyprint
    # ... code d'export PDF
    pass


@login_required
def api_historique_stats(request):
    """API pour obtenir des statistiques sur une période"""
    date_debut = request.GET.get('date_debut')
    date_fin = request.GET.get('date_fin')
    
    # Calculer les stats
    stats = {
        'production_totale': 0,
        'nombre_jours': 0,
        'moyenne_jour': 0,
        'meilleur_jour': {},
        'par_section': {}
    }
    
    # ... logique de calcul
    
    return JsonResponse(stats)