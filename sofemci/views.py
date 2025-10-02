# sofemci/views.py
from django.shortcuts import render, redirect, get_object_or_404
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

from .models import *
from .forms import *

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
    today = timezone.now().date()
    
    # Données réelles
    context = {
        'today': today,
        'production_totale': get_production_totale_jour(today),
        'production_extrusion': get_production_section_jour('extrusion', today),
        'production_imprimerie': get_production_section_jour('imprimerie', today),
        'production_soudure': get_production_section_jour('soudure', today),
        'production_recyclage': get_production_section_jour('recyclage', today),
        'total_dechets': get_dechets_totaux_jour(today),
        'efficacite_moyenne': get_efficacite_moyenne_jour(today),
        'machines_stats': get_machines_stats(),
        'zones_performance': get_zones_performance(today),
        'alertes': Alerte.objects.filter(
            statut__in=['nouveau', 'en_cours']
        ).order_by('-date_creation')[:5],
        'extrusion_stats': get_extrusion_details_jour(today),
        'imprimerie_stats': get_imprimerie_details_jour(today),
        'soudure_stats': get_soudure_details_jour(today),
        'recyclage_stats': get_recyclage_details_jour(today),
        # Données pour graphiques Analytics
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

@login_required
def historique_view(request):
    form = FiltreHistoriqueForm(request.GET or None)
    
    if form.is_valid():
        filters = form.cleaned_data
        productions_data, totaux = get_productions_filtrees(filters)
    else:
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        default_filters = {
            'date_debut': debut_mois,
            'date_fin': today,
        }
        productions_data, totaux = get_productions_filtrees(default_filters)
    
    # Combiner toutes les productions pour l'affichage unifié
    all_productions = []
    for section, prods in productions_data.items():
        for prod in prods:
            all_productions.append({
                'id': prod.id,
                'date_production': prod.date_production,
                'section': section,
                'equipe': getattr(prod, 'equipe', None),
                'total_production_kg': prod.total_production_kg,
                'dechets_kg': getattr(prod, 'dechets_kg', 0),
                'rendement_pourcentage': getattr(prod, 'rendement_pourcentage', None),
                'valide': prod.valide,
            })
    
    # Pagination
    paginator = Paginator(all_productions, 20)
    page_number = request.GET.get('page')
    productions = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'productions': productions,
        'equipes': Equipe.objects.all(),
        'totaux': totaux,
    }
    
    return render(request, 'historique.html', context)

# ==========================================
# RAPPORTS
# ==========================================

@login_required
def rapports_view(request):
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    # Génération du rapport si demandé
    mois_selectione = request.GET.get('mois', timezone.now().strftime('%m'))
    annee_selectionnee = request.GET.get('annee', timezone.now().year)
    section_selectionnee = request.GET.get('section', '')
    
    rapport = None
    if request.GET.get('mois'):
        rapport = generer_rapport_mensuel(int(annee_selectionnee), int(mois_selectione), section_selectionnee)
    
    context = {
        'rapport': rapport,
        'mois_disponibles': get_mois_disponibles(),
        'annees_disponibles': range(2024, timezone.now().year + 1),
        'annee_courante': int(annee_selectionnee),
        'mois_nom': get_nom_mois(int(mois_selectione)) if request.GET.get('mois') else '',
        'section_selectionnee': section_selectionnee,
        'labels_sections': json.dumps(['Extrusion', 'Imprimerie', 'Soudure', 'Recyclage']),
        'data_sections': json.dumps([28400, 17200, 9800, 6800]) if rapport else json.dumps([]),
    }
    
    return render(request, 'rapports.html', context)

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
        }
    
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
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
        'temps_travail': round(temps_total_minutes / 60, 1),
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
    
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
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
        'temps_travail': round(temps_total_minutes / 60, 1),
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
    
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
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
        'temps_travail': round(temps_total_minutes / 60, 1),
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
        'temps_travail': 8,  # Valeur par défaut
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
    dechets = float(data.get('dechets', 0))
    
    total_specifique = bretelles + rema + batta
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
def generer_rapport_mensuel(annee, mois, section=''):
    """Générer rapport mensuel"""
    debut = datetime(annee, mois, 1).date()
    if mois == 12:
        fin = datetime(annee + 1, 1, 1).date() - timedelta(days=1)
    else:
        fin = datetime(annee, mois + 1, 1).date() - timedelta(days=1)
    
    return {
        'total_production': get_production_totale_periode(debut, fin),
        'rendement_moyen': get_efficacite_globale_periode(debut, fin),
        'taux_dechet_moyen': 3.2,  # À calculer
        'evolution_production': 12.5,
        'evolution_rendement': 3.2,
        'evolution_dechets': -2.1,
        'jours_production': (fin - debut).days + 1,
        'taux_activite': 95,
        'sections': get_sections_rapport(debut, fin, section),
    }

def get_sections_rapport(debut, fin, section_filtre=''):
    """Détails sections pour rapport"""
    sections_data = []
    
    sections_list = [section_filtre] if section_filtre else ['extrusion', 'imprimerie', 'soudure', 'recyclage']
    
    for section in sections_list:
        production = get_production_section_periode(section, debut, fin)
        
        sections_data.append({
            'nom': section.capitalize(),
            'production': production,
            'rendement': 87.5,  # À calculer
            'dechets': 0,  # À calculer
            'taux_dechet': 3.2,
            'jours_actifs': 28,
            'jours_total': (fin - debut).days + 1,
            'production_jour': production / ((fin - debut).days + 1) if (fin - debut).days > 0 else 0,
            'production_journaliere': [],  # À compléter si nécessaire
        })
    
    return sections_data

def get_mois_disponibles():
    """Liste des mois disponibles"""
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    
    return [{'value': f'2025-{i:02d}', 'nom': mois_noms[i-1] + ' 2025', 'selected': i == timezone.now().month}
            for i in range(1, 13)]

def get_nom_mois(mois_num):
    """Nom du mois"""
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    return mois_noms[mois_num - 1] if 1 <= mois_num <= 12 else ''


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