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
    
    # Métriques du jour sélectionné (au lieu de today)
    context = {
        'today': selected_date,  # Date sélectionnée
        'selected_date': selected_date,  # Pour le formulaire
        'is_today': selected_date == timezone.now().date(),  # Savoir si c'est aujourd'hui
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

# Dans votre vue saisie_sections_view
@login_required
def saisie_sections_view(request):
    if request.method == 'POST':
        section = request.POST.get('section')
        print(f"Section reçue: {section}")  # Débogage
        
        try:
            if section == 'soudure':
                # Créer une instance du formulaire pour validation
                form_data = request.POST.copy()
                form = ProductionSoudureForm(form_data)
                
                if not form.is_valid():
                    print("Erreurs de formulaire:", form.errors)  # Débogage
                    messages.error(request, f"Erreur dans le formulaire: {form.errors}")
                    return redirect('saisie_sections')
                
                # Créer l'objet
                production = ProductionSoudure.objects.create(
                    date_production=request.POST.get('date_production'),
                    heure_debut=request.POST.get('heure_debut'),
                    heure_fin=request.POST.get('heure_fin'),
                    nombre_machines_actives=int(request.POST.get('nombre_machines_actives', 0)),
                    production_bobines_finies_kg=Decimal(request.POST.get('production_bobines_finies_kg', 0)),
                    production_bretelles_kg=Decimal(request.POST.get('production_bretelles_kg', 0)),
                    production_rema_kg=Decimal(request.POST.get('production_rema_kg', 0)),
                    production_batta_kg=Decimal(request.POST.get('production_batta_kg', 0)),
                    production_sac_emballage_kg=Decimal(request.POST.get('production_sac_emballage_kg', 0)),
                    dechets_kg=Decimal(request.POST.get('dechets_kg', 0)),
                    observations=request.POST.get('observations', ''),
                    cree_par=request.user,
                    valide=False
                )
                messages.success(request, 'Production soudure enregistrée avec succès!')
            
            # ... autres sections ...
            
        except Exception as e:
            print(f"Exception: {str(e)}")  # Débogage
            messages.error(request, f'Erreur lors de l\'enregistrement: {str(e)}')
        
        return redirect('saisie_sections')
    
    # GET request
    today = timezone.now().date()
    equipes = Equipe.objects.all()
    
    context = {
        'today': today,
        'equipes': equipes,
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
    
    # Permissions
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    # Statistiques du parc machines
    stats_parc = statistiques_parc_machines()
    
    # Machines à risque
    machines_critiques = obtenir_machines_a_risque(seuil_probabilite=70)
    ids_critiques = list(machines_critiques.values_list('id', flat=True))
    
    machines_risque_eleve = obtenir_machines_a_risque(seuil_probabilite=40).exclude(
        id__in=ids_critiques
    )
    
    # Alertes IA actives - CORRECTION ICI
    alertes_queryset = obtenir_alertes_actives()
    
    # Compter AVANT de slicer
    nombre_alertes_critiques = alertes_queryset.filter(niveau='critique').count()
    nombre_alertes_urgentes = alertes_queryset.filter(niveau='urgent').count()
    
    # Maintenant on peut slicer pour l'affichage
    alertes = alertes_queryset[:10]
    
    # Machines actives
    machines_actives = Machine.objects.filter(etat='actif').order_by('score_sante_global')
    
    context = {
        'stats_parc': stats_parc,
        'machines_critiques': machines_critiques,
        'machines_risque_eleve': machines_risque_eleve,
        'alertes': alertes,
        'machines_actives': machines_actives,
        'nombre_alertes_critiques': nombre_alertes_critiques,
        'nombre_alertes_urgentes': nombre_alertes_urgentes,
    }
    
    return render(request, 'dashboard_ia.html', context)
    """Dashboard principal de maintenance prédictive"""
    
    # Permissions
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    # Statistiques du parc machines
    stats_parc = statistiques_parc_machines()
    
    # Machines à risque - CORRECTION ICI
    machines_critiques = obtenir_machines_a_risque(seuil_probabilite=70)
    
    # Récupérer les IDs AVANT de slicer
    ids_critiques = list(machines_critiques.values_list('id', flat=True))
    
    machines_risque_eleve = obtenir_machines_a_risque(seuil_probabilite=40).exclude(
        id__in=ids_critiques
    )
    
    # Alertes IA actives
    alertes = obtenir_alertes_actives()[:10]
    
    # Machines actives
    machines_actives = Machine.objects.filter(etat='actif').order_by('score_sante_global')
    
    context = {
        'stats_parc': stats_parc,
        'machines_critiques': machines_critiques,
        'machines_risque_eleve': machines_risque_eleve,
        'alertes': alertes,
        'machines_actives': machines_actives,
        'nombre_alertes_critiques': alertes.filter(niveau='critique').count(),
        'nombre_alertes_urgentes': alertes.filter(niveau='urgent').count(),
    }
    
    return render(request, 'dashboard_ia.html', context)
    """Dashboard principal de maintenance prédictive"""
    
    # Permissions
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    # Statistiques du parc machines
    stats_parc = statistiques_parc_machines()
    
    # Machines à risque
    machines_critiques = obtenir_machines_a_risque(seuil_probabilite=70)
    machines_risque_eleve = obtenir_machines_a_risque(seuil_probabilite=40).exclude(
        id__in=machines_critiques.values_list('id', flat=True)
    )
    
    # Alertes IA actives
    alertes = obtenir_alertes_actives()[:10]
    
    # Graphique évolution scores de santé
    machines_actives = Machine.objects.filter(etat='actif').order_by('score_sante_global')
    
    context = {
        'stats_parc': stats_parc,
        'machines_critiques': machines_critiques,
        'machines_risque_eleve': machines_risque_eleve,
        'alertes': alertes,
        'machines_actives': machines_actives,
        'nombre_alertes_critiques': alertes.filter(niveau='critique').count(),
        'nombre_alertes_urgentes': alertes.filter(niveau='urgent').count(),
    }
    
    return render(request, 'dashboard_ia.html', context)


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