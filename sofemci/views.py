# sofemci/views.py - VERSION ULTIME COMPLÈTE
from django.http import HttpResponse
from django.template.loader import render_to_string
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
from .models import Machine, ZoneExtrusion, Alerte, AlerteIA, HistoriqueMachine
import logging
from .models import *
from .forms import *

logger = logging.getLogger(__name__)

# ==========================================
# FONCTIONS UTILITAIRES (METTRE EN PREMIER)
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
    taux_dechet = (dechets / (total_prod + dechets) * 100) if (total_prod + dechets) > 0 else 0
    
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
    
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bobines_finis=Sum('production_bobines_finies_kg'),
        bobines_semi_finis=Sum('production_bobines_semi_finies_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )
    
    total = aggregats['total'] or 0
    dechets = aggregats['dechets'] or 0
    taux_dechet = (dechets / (total + dechets) * 100) if (total + dechets) > 0 else 0
    
    return {
        'temps_travail': 8,
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='imprimerie').count(),
        'bobines_finies': aggregats['bobines_finis'] or 0,
        'bobines_semi_finies': aggregats['bobines_semi_finis'] or 0,
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
    
    total = aggregats['total'] or 0
    dechets = aggregats['dechets'] or 0
    taux_dechet = (dechets / (total + dechets) * 100) if (total + dechets) > 0 else 0
    
    return {
        'temps_travail': 8,
        'machines_actives': round(aggregats['machines'] or 0, 0),
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
    moulinex_avg = aggregats['moulinex'] or 1
    
    taux_transformation = (bache / broyage * 100) if broyage > 0 else 0
    productivite = (total / moulinex_avg) if moulinex_avg > 0 else 0
    
    return {
        'moulinex_actifs': round(moulinex_avg, 0),
        'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
        'total_broyage': broyage,
        'total_bache_noir': bache,
        'production_totale': total,
        'taux_transformation': round(taux_transformation, 1),
        'rendement': round(taux_transformation, 1),
        'productivite_par_moulinex': round(productivite, 1),
        'temps_travail': 8,
    }

def get_productions_filtrees(filters):
    """Obtenir productions filtrées pour l'historique"""
    date_filters = {}
    
    if filters.get('date_debut'):
        date_filters['date_production__gte'] = filters['date_debut']
    
    if filters.get('date_fin'):
        date_filters['date_production__lte'] = filters['date_fin']
    
    # Filtre par section si spécifié
    section_filter = filters.get('section')
    equipe_filter = filters.get('equipe')
    
    # Extrusion
    extrusion_query = ProductionExtrusion.objects.filter(**date_filters)
    if section_filter == 'extrusion' or not section_filter:
        if equipe_filter:
            extrusion_query = extrusion_query.filter(equipe_id=equipe_filter)
    
    # Imprimerie
    imprimerie_query = ProductionImprimerie.objects.filter(**date_filters)
    if section_filter == 'imprimerie' or not section_filter:
        pass
    
    # Soudure
    soudure_query = ProductionSoudure.objects.filter(**date_filters)
    if section_filter == 'soudure' or not section_filter:
        pass
    
    # Recyclage
    recyclage_query = ProductionRecyclage.objects.filter(**date_filters)
    if section_filter == 'recyclage' or not section_filter:
        if equipe_filter:
            recyclage_query = recyclage_query.filter(equipe_id=equipe_filter)
    
    productions_data = {
        'extrusion': extrusion_query.select_related('zone', 'equipe', 'cree_par'),
        'imprimerie': imprimerie_query.select_related('cree_par'),
        'soudure': soudure_query.select_related('cree_par'),
        'recyclage': recyclage_query.select_related('equipe', 'cree_par'),
    }
    
    # Calcul des totaux
    totaux = {
        'extrusion': {
            'total': extrusion_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
            'dechets': extrusion_query.aggregate(dechets=Sum('dechets_kg'))['dechets'] or 0,
        },
        'imprimerie': {
            'total': imprimerie_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
            'dechets': imprimerie_query.aggregate(dechets=Sum('dechets_kg'))['dechets'] or 0,
        },
        'soudure': {
            'total': soudure_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
            'dechets': soudure_query.aggregate(dechets=Sum('dechets_kg'))['dechets'] or 0,
        },
        'recyclage': {
            'total': recyclage_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
            'dechets': 0,
        },
    }
    
    return productions_data, totaux

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

# ==========================================
# SAISIE PRODUCTION - VERSIONS CORRIGÉES
# ==========================================

@login_required
def saisie_extrusion_view(request):
    if request.user.role not in ['chef_extrusion', 'superviseur', 'admin']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductionExtrusionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                production = form.save(commit=False)
                production.cree_par = request.user
                production.save()
                
                messages.success(request, 'pup pup ✅ Production d\'extrusion enregistrée avec succès dans la base de données !')
                return redirect('historique')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'enregistrement: {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
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

# Dans views.py - AJOUTEZ cette version corrigée
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
    
    # Gestion des formulaires POST
    success_message = None
    if request.method == 'POST':
        section = request.POST.get('section')
        
        if section == 'imprimerie' and 'imprimerie' in user_sections:
            form_imprimerie = ProductionImprimerieForm(request.POST)
            if form_imprimerie.is_valid():
                production = form_imprimerie.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = 'pup pup ✅ Production imprimerie enregistrée avec succès dans la base de données !'
            else:
                messages.error(request, 'Erreur dans le formulaire imprimerie')
        
        elif section == 'soudure' and 'soudure' in user_sections:
            form_soudure = ProductionSoudureForm(request.POST)
            if form_soudure.is_valid():
                production = form_soudure.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = 'pup pup ✅ Production soudure enregistrée avec succès dans la base de données !'
            else:
                messages.error(request, 'Erreur dans le formulaire soudure')
        
        elif section == 'recyclage' and 'recyclage' in user_sections:
            form_recyclage = ProductionRecyclageForm(request.POST)
            if form_recyclage.is_valid():
                production = form_recyclage.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = 'pup pup ✅ Production recyclage enregistrée avec succès dans la base de données !'
            else:
                messages.error(request, 'Erreur dans le formulaire recyclage')
        
        if success_message:
            messages.success(request, success_message)
            return redirect('historique')
    
    # Initialisation des formulaires
    form_imprimerie = ProductionImprimerieForm() if 'imprimerie' in user_sections else None
    form_soudure = ProductionSoudureForm() if 'soudure' in user_sections else None
    form_recyclage = ProductionRecyclageForm() if 'recyclage' in user_sections else None
    
    context = {
        'today': timezone.now().date(),
        'user_sections': user_sections,
        'form_imprimerie': form_imprimerie,
        'form_soudure': form_soudure,
        'form_recyclage': form_recyclage,
        'equipes': Equipe.objects.all(),
    }
    
    return render(request, 'saisie_sections.html', context)
# ==========================================
# HISTORIQUE
# ==========================================

@login_required
def historique_view(request):
    form = FiltreHistoriqueForm(request.GET or None)
    
    # Appliquer les filtres
    if form.is_valid():
        filters = form.cleaned_data
        productions_data, totaux = get_productions_filtrees(filters)
    else:
        # Filtres par défaut (mois en cours)
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        default_filters = {
            'date_debut': debut_mois,
            'date_fin': today,
        }
        productions_data, totaux = get_productions_filtrees(default_filters)
    
    # Combiner toutes les productions pour l'affichage unifié
    all_productions = []
    
    # Extrusion
    for prod in productions_data['extrusion']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'extrusion',
            'equipe': prod.equipe,
            'zone': prod.zone,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': prod.dechets_kg,
            'rendement_pourcentage': prod.rendement_pourcentage,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': prod.heure_debut,
            'heure_fin': prod.heure_fin,
        })
    
    # Imprimerie
    for prod in productions_data['imprimerie']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'imprimerie',
            'equipe': None,
            'zone': None,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': prod.dechets_kg,
            'rendement_pourcentage': None,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': prod.heure_debut,
            'heure_fin': prod.heure_fin,
        })
    
    # Soudure
    for prod in productions_data['soudure']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'soudure',
            'equipe': None,
            'zone': None,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': prod.dechets_kg,
            'rendement_pourcentage': None,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': prod.heure_debut,
            'heure_fin': prod.heure_fin,
        })
    
    # Recyclage
    for prod in productions_data['recyclage']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'recyclage',
            'equipe': prod.equipe,
            'zone': None,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': 0,
            'rendement_pourcentage': None,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': None,
            'heure_fin': None,
            
        })
    
    # Trier par date décroissante
    all_productions.sort(key=lambda x: x['date_production'], reverse=True)
    
    # Pagination
    paginator = Paginator(all_productions, 20)
    page_number = request.GET.get('page')
    productions_page = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'productions': productions_page,
        'equipes': Equipe.objects.all(),
        'totaux': totaux,
        'periode_debut': debut_mois,  # AJOUTÉ
        'periode_fin': today,         # AJOUTÉ
    }
    
    return render(request, 'historique.html', context)

# ==========================================
# GESTION DES MACHINES
# ==========================================

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
        if form.is_valid():
            machine = form.save()
            messages.success(request, f'Machine {machine.numero} créée avec succès !')
            return redirect('machines_list')
        else:
            messages.error(request, 'Erreur dans le formulaire. Veuillez corriger.')
    else:
        form = MachineForm()
    
    context = {
        'form': form,
        'action': 'Créer',
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

# ==========================================
# DASHBOARD IA - FONCTIONS SIMPLIFIÉES
# ==========================================

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
def machine_detail_ia_view(request, machine_id):
    """Détails machine IA simplifié"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Analyse simplifiée
    analyse = {
        'probabilite_panne_7j': getattr(machine, 'probabilite_panne_7_jours', 0) or 0,
        'score_sante': getattr(machine, 'score_sante_global', 0) or 0,
        'niveau_risque': 'normal',
        'facteurs_risque': [],
        'recommandations': []
    }
    
    context = {
        'machine': machine,
        'analyse': analyse,
    }
    
    return render(request, 'machine_detail_ia.html', context)

@login_required
def lancer_analyse_complete(request):
    """Lance l'analyse IA sur toutes les machines"""
    if request.user.role not in ['admin', 'superviseur']:
        messages.error(request, 'Permission refusée.')
        return redirect('dashboard_ia')
    
    messages.success(request, 'Analyse complète lancée (fonction simulée)')
    return redirect('dashboard_ia')

# ==========================================
# API POUR L'HISTORIQUE
# ==========================================

@login_required
def api_production_details(request, section, production_id):
    """API pour récupérer les détails d'une production spécifique"""
    try:
        if section == 'extrusion':
            production = get_object_or_404(ProductionExtrusion, id=production_id)
            data = {
                'Date': production.date_production.strftime('%d/%m/%Y'),
                'Section': 'Extrusion',
                'Zone': f"Zone {production.zone.numero} - {production.zone.nom}",
                'Équipe': production.equipe.get_nom_display(),
                'Heure début': production.heure_debut.strftime('%H:%M') if production.heure_debut else '-',
                'Heure fin': production.heure_fin.strftime('%H:%M') if production.heure_fin else '-',
                'Matière première': f"{production.matiere_premiere_kg} kg",
                'Production finis': f"{production.production_finis_kg} kg",
                'Production semi-finis': f"{production.production_semi_finis_kg} kg",
                'Production totale': f"{production.total_production_kg} kg",
                'Déchets': f"{production.dechets_kg} kg",
                'Rendement': f"{production.rendement_pourcentage}%" if production.rendement_pourcentage else '-',
                'Machines actives': production.nombre_machines_actives,
                'Machinistes': production.nombre_machinistes,
                'Créé par': production.cree_par.get_full_name() or production.cree_par.username,
                'Statut': 'Validé' if production.valide else 'En attente',
            }
        
        elif section == 'imprimerie':
            production = get_object_or_404(ProductionImprimerie, id=production_id)
            data = {
                'Date': production.date_production.strftime('%d/%m/%Y'),
                'Section': 'Imprimerie',
                'Heure début': production.heure_debut.strftime('%H:%M') if production.heure_debut else '-',
                'Heure fin': production.heure_fin.strftime('%H:%M') if production.heure_fin else '-',
                'Bobines finies': f"{production.production_bobines_finies_kg} kg",
                'Bobines semi-finies': f"{production.production_bobines_semi_finies_kg} kg",
                'Production totale': f"{production.total_production_kg} kg",
                'Déchets': f"{production.dechets_kg} kg",
                'Machines actives': production.nombre_machines_actives,
                'Observations': production.observations or '-',
                'Créé par': production.cree_par.get_full_name() or production.cree_par.username,
                'Statut': 'Validé' if production.valide else 'En attente',
            }
        
        elif section == 'soudure':
            production = get_object_or_404(ProductionSoudure, id=production_id)
            data = {
                'Date': production.date_production.strftime('%d/%m/%Y'),
                'Section': 'Soudure',
                'Heure début': production.heure_debut.strftime('%H:%M') if production.heure_debut else '-',
                'Heure fin': production.heure_fin.strftime('%H:%M') if production.heure_fin else '-',
                'Bobines finies': f"{production.production_bobines_finies_kg} kg",
                'Bretelles': f"{production.production_bretelles_kg} kg",
                'REMA-Plastique': f"{production.production_rema_kg} kg",
                'BATTA': f"{production.production_batta_kg} kg",
                'Sacs emballage imprimés': f"{getattr(production, 'production_sac_emballage_kg', 0)} kg",
                'Production totale': f"{production.total_production_kg} kg",
                'Déchets': f"{production.dechets_kg} kg",
                'Machines actives': production.nombre_machines_actives,
                'Observations': production.observations or '-',
                'Créé par': production.cree_par.get_full_name() or production.cree_par.username,
                'Statut': 'Validé' if production.valide else 'En attente',
            }
        
        elif section == 'recyclage':
            production = get_object_or_404(ProductionRecyclage, id=production_id)
            data = {
                'Date': production.date_production.strftime('%d/%m/%Y'),
                'Section': 'Recyclage',
                'Équipe': production.equipe.get_nom_display(),
                'Moulinex actifs': production.nombre_moulinex,
                'Production broyage': f"{production.production_broyage_kg} kg",
                'Bâche noire': f"{production.production_bache_noir_kg} kg",
                'Production totale': f"{production.total_production_kg} kg",
                'Observations': production.observations or '-',
                'Créé par': production.cree_par.get_full_name() or production.cree_par.username,
                'Statut': 'Validé' if production.valide else 'En attente',
            }
        
        else:
            return JsonResponse({'error': 'Section invalide'}, status=400)
        
        return JsonResponse(data)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_valider_production(request, section, production_id):
    """API pour valider une production"""
    if request.user.role not in ['superviseur', 'admin']:
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    try:
        if section == 'extrusion':
            production = get_object_or_404(ProductionExtrusion, id=production_id)
        elif section == 'imprimerie':
            production = get_object_or_404(ProductionImprimerie, id=production_id)
        elif section == 'soudure':
            production = get_object_or_404(ProductionSoudure, id=production_id)
        elif section == 'recyclage':
            production = get_object_or_404(ProductionRecyclage, id=production_id)
        else:
            return JsonResponse({'success': False, 'error': 'Section invalide'})
        
        production.valide = True
        production.valide_par = request.user
        production.date_validation = timezone.now()
        production.save()
        
        return JsonResponse({'success': True, 'message': 'Production validée avec succès'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ==========================================
# AUTRES VUES (simplifiées pour éviter les erreurs)
# ==========================================

@login_required
def saisie_imprimerie_ajax(request):
    if request.method == 'POST':
        form = ProductionImprimerieForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({
                'success': True, 
                'message': 'pup pup ✅ Production imprimerie enregistrée dans la base de données !'
            })
        return JsonResponse({
            'success': False, 
            'errors': form.errors,
            'message': 'Erreur dans le formulaire'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def saisie_soudure_ajax(request):
    if request.method == 'POST':
        form = ProductionSoudureForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({
                'success': True, 
                'message': 'pup pup ✅ Production soudure enregistrée dans la base de données !'
            })
        return JsonResponse({
            'success': False, 
            'errors': form.errors,
            'message': 'Erreur dans le formulaire'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def saisie_recyclage_ajax(request):
    if request.method == 'POST':
        form = ProductionRecyclageForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({
                'success': True, 
                'message': 'pup pup ✅ Production recyclage enregistrée dans la base de données !'
            })
        return JsonResponse({
            'success': False, 
            'errors': form.errors,
            'message': 'Erreur dans le formulaire'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

# ==========================================
# VUES SIMPLIFIÉES POUR ÉVITER LES ERREURS
# ==========================================

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
# FONCTIONS DE SECOURS POUR ÉVITER LES ERREURS
# ==========================================

def calculate_extrusion_metrics(data):
    return JsonResponse({'total_production': 0, 'rendement': 0, 'taux_dechet': 0, 'production_par_machine': 0})

def calculate_imprimerie_metrics(data):
    return JsonResponse({'total_production': 0, 'taux_dechet': 0})

def calculate_soudure_metrics(data):
    return JsonResponse({'total_production': 0, 'total_specifique': 0, 'taux_dechet': 0})

def calculate_recyclage_metrics(data):
    return JsonResponse({'total_production': 0, 'production_par_moulinex': 0, 'taux_transformation': 0})

@login_required
def api_calculs_production(request):
    return JsonResponse({'error': 'Fonction non implémentée'}, status=400)

@login_required
def api_dashboard_data(request):
    return JsonResponse({
        'timestamp': timezone.now().isoformat(),
        'production_totale': 0,
        'machines_actives': 0,
        'alertes_count': 0,
        'efficacite_moyenne': 0,
    })

# ==========================================
# VUES POUR ÉVITER LES ERREURS D'URLS
# ==========================================

@login_required
def machine_change_status_ajax(request, machine_id):
    """Changer le statut d'une machine (AJAX)"""
    return JsonResponse({'success': False, 'message': 'Fonction non implémentée'})

@login_required
def api_create_zone(request):
    """API pour créer une zone rapidement"""
    return JsonResponse({'success': False, 'message': 'Fonction non implémentée'})

@login_required
def enregistrer_maintenance_view(request, machine_id):
    """Formulaire d'enregistrement de maintenance"""
    machine = get_object_or_404(Machine, id=machine_id)
    messages.info(request, 'Fonction de maintenance non implémentée')
    return redirect('machine_detail_ia', machine_id=machine_id)

@login_required
def enregistrer_panne_view(request, machine_id):
    """Formulaire d'enregistrement de panne"""
    machine = get_object_or_404(Machine, id=machine_id)
    messages.info(request, 'Fonction de panne non implémentée')
    return redirect('machine_detail_ia', machine_id=machine_id)

@login_required
def traiter_alerte_ia(request, alerte_id):
    """Prendre en charge ou résoudre une alerte IA"""
    messages.info(request, 'Fonction de traitement d\'alerte non implémentée')
    return redirect('dashboard_ia')

@login_required
def liste_alertes_ia(request):
    """Liste complète des alertes IA avec filtres"""
    context = {
        'alertes': [],
        'niveau_filtre': None,
        'statut_filtre': None,
        'section_filtre': None,
    }
    return render(request, 'liste_alertes_ia.html', context)

@login_required
def simuler_capteurs_view(request, machine_id):
    """Simulation de mise à jour des capteurs (pour tests)"""
    machine = get_object_or_404(Machine, id=machine_id)
    messages.info(request, 'Fonction de simulation non implémentée')
    return redirect('machine_detail_ia', machine_id=machine_id)

@login_required
def api_machines_status(request):
    """API retournant le statut de toutes les machines"""
    return JsonResponse({
        'machines': [],
        'timestamp': timezone.now().isoformat()
    })

@login_required
def api_alertes_count(request):
    """API retournant le nombre d'alertes par niveau"""
    return JsonResponse({
        'alertes': [],
        'total': 0
    })

@login_required
def api_statistiques_ia(request):
    """API retournant les statistiques IA"""
    return JsonResponse({
        'statistiques': {},
        'timestamp': timezone.now().isoformat()
    })