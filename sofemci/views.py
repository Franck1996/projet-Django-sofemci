# sofemci/views.py
# 🎯 TOUTES LES VUES DE L'APPLICATION SOFEM-CI

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, CreateView, UpdateView
from django.db.models import Sum, Avg, Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import *
from .forms import *

# ==========================================
# VUES AUTHENTIFICATION
# ==========================================

def login_view(request):
    """Connexion utilisateur - Page login.html"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
            return redirect('dashboard')
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'login.html')

def logout_view(request):
    """Déconnexion utilisateur"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================

@login_required
def dashboard_view(request):
    """Dashboard principal - Page dashboard.html (maquette dashboard_principal)"""
    today = timezone.now().date()
    
    # Métriques du jour pour le dashboard
    context = {
        # Production totale du jour
        'production_totale': get_production_totale_jour(today),
        'production_extrusion': get_production_section_jour('extrusion', today),
        'production_imprimerie': get_production_section_jour('imprimerie', today),
        'production_soudure': get_production_section_jour('soudure', today),
        'production_recyclage': get_production_section_jour('recyclage', today),
        
        # Déchets totaux
        'total_dechets': get_dechets_totaux_jour(today),
        
        # Efficacité moyenne
        'efficacite_moyenne': get_efficacite_moyenne_jour(today),
        
        # État des machines
        'machines_stats': get_machines_stats(),
        
        # Zones d'extrusion avec performance
        'zones_performance': get_zones_performance(today),
        
        # Alertes récentes
        'alertes': Alerte.objects.filter(
            statut__in=['nouveau', 'en_cours']
        ).order_by('-date_creation')[:5],
        
        # Données pour les cards des sections
        'section_data': get_sections_data(today),
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def dashboard_direction_view(request):
    """Dashboard Direction - Page dashboard_direction.html (maquette dashboard_direction)"""
    # Seule la direction peut accéder
    if request.user.role not in ['direction', 'admin']:
        messages.error(request, 'Accès refusé. Réservé à la direction.')
        return redirect('dashboard')
    
    # Période d'analyse (mois en cours)
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    # KPI Exécutifs pour la direction
    context = {
        # Production mensuelle
        'production_mensuelle': get_production_totale_periode(debut_mois, today),
        'croissance_pourcentage': get_croissance_mensuelle(debut_mois, today),
        'efficacite_globale': get_efficacite_globale_periode(debut_mois, today),
        'taux_qualite': get_taux_qualite_periode(debut_mois, today),
        'taux_dechet_global': get_taux_dechet_global_periode(debut_mois, today),
        
        # Performance par section pour la direction
        'sections_executive': get_sections_executive_data(debut_mois, today),
        
        # Alertes critiques
        'alertes_critiques': Alerte.objects.filter(
            type_alerte__in=['critique', 'important'],
            statut__in=['nouveau', 'en_cours']
        ).order_by('-date_creation')[:10],
        
        # Tendances pour graphiques
        'tendances_journalieres': get_tendances_journalieres(debut_mois, today),
        
        # Période d'affichage
        'periode_debut': debut_mois,
        'periode_fin': today,
    }
    
    return render(request, 'dashboard_direction.html', context)

# ==========================================
# VUES SAISIE PRODUCTION EXTRUSION
# ==========================================

@login_required
def saisie_extrusion_view(request):
    """Saisie production extrusion - Page saisie_extrusion.html"""
    # Vérifier les permissions
    if request.user.role not in ['chef_extrusion', 'superviseur', 'admin']:
        messages.error(request, 'Accès refusé. Réservé aux chefs d\'extrusion.')
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
            messages.error(request, 'Erreur dans le formulaire. Veuillez corriger.')
    else:
        form = ProductionExtrusionForm(user=request.user)
    
    # Données pour le template
    context = {
        'form': form,
        'zones': get_zones_utilisateur(request.user),
        'equipes': Equipe.objects.all(),
        'productions_recentes': ProductionExtrusion.objects.filter(
            cree_par=request.user if request.user.role == 'chef_extrusion' else Q()
        ).select_related('zone', 'equipe').order_by('-date_creation')[:10],
    }
    
    return render(request, 'saisie_extrusion.html', context)

# ==========================================
# VUES SAISIE AUTRES SECTIONS
# ==========================================

@login_required
def saisie_sections_view(request):
    """Saisie autres sections - Page saisie_sections.html (maquette saisie_sections_autres)"""
    # Déterminer quelle section selon le rôle
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
        'user_sections': user_sections,
        'form_imprimerie': ProductionImprimerieForm() if 'imprimerie' in user_sections else None,
        'form_soudure': ProductionSoudureForm() if 'soudure' in user_sections else None,
        'form_recyclage': ProductionRecyclageForm() if 'recyclage' in user_sections else None,
        'equipes': Equipe.objects.all(),
    }
    
    return render(request, 'saisie_sections.html', context)

@login_required
def saisie_imprimerie_ajax(request):
    """Traitement AJAX saisie imprimerie"""
    if request.method == 'POST':
        form = ProductionImprimerieForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({'success': True, 'message': 'Production imprimerie enregistrée !'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def saisie_soudure_ajax(request):
    """Traitement AJAX saisie soudure"""
    if request.method == 'POST':
        form = ProductionSoudureForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({'success': True, 'message': 'Production soudure enregistrée !'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def saisie_recyclage_ajax(request):
    """Traitement AJAX saisie recyclage"""
    if request.method == 'POST':
        form = ProductionRecyclageForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({'success': True, 'message': 'Production recyclage enregistrée !'})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

# ==========================================
# VUE HISTORIQUE
# ==========================================

@login_required
def historique_view(request):
    """Historique production - Page historique.html (maquette historique_production)"""
    
    # Traitement des filtres
    form = FiltreHistoriqueForm(request.GET or None)
    
    # Données filtrées
    productions_data = {}
    totaux = {}
    
    if form.is_valid():
        # Appliquer les filtres
        filters = form.cleaned_data
        productions_data, totaux = get_productions_filtrees(filters)
    else:
        # Données par défaut (mois en cours)
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        default_filters = {
            'date_debut': debut_mois,
            'date_fin': today,
        }
        productions_data, totaux = get_productions_filtrees(default_filters)
    
    context = {
        'form': form,
        'productions_data': productions_data,
        'totaux': totaux,
        'can_export': request.user.role in ['superviseur', 'admin', 'direction'],
    }
    
    return render(request, 'historique.html', context)

# ==========================================
# VUES RAPPORTS
# ==========================================

@login_required
def rapports_view(request):
    """Page rapports"""
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    # Données pour les rapports
    context = {
        'rapports_mensuels': RapportMensuel.objects.all()[:12],
        'can_generate': request.user.role in ['admin', 'direction'],
    }
    
    return render(request, 'rapports.html', context)

# ==========================================
# API POUR LES CALCULS TEMPS RÉEL
# ==========================================

@login_required
def api_calculs_production(request):
    """API pour calculs temps réel dans les formulaires (comme dans vos maquettes)"""
    if request.method == 'POST':
        data = json.loads(request.body)
        section = data.get('section')
        
        if section == 'extrusion':
            # Calculs exactement comme dans votre maquette saisie_extrusion
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
        
        elif section == 'imprimerie':
            # Calculs pour imprimerie
            bobines_finies = float(data.get('bobines_finies', 0))
            bobines_semi_finies = float(data.get('bobines_semi_finies', 0))
            dechets = float(data.get('dechets', 0))
            
            total_production = bobines_finies + bobines_semi_finies
            taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
            
            return JsonResponse({
                'total_production': round(total_production, 1),
                'taux_dechet': round(taux_dechet, 1),
            })
        
        elif section == 'soudure':
            # Calculs pour soudure
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
        
        elif section == 'recyclage':
            # Calculs pour recyclage
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
    
    return JsonResponse({'error': 'Requête invalide'}, status=400)

@login_required
def api_dashboard_data(request):
    """API pour mise à jour temps réel du dashboard"""
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
# FONCTIONS UTILITAIRES
# ==========================================

def get_production_totale_jour(date):
    """Calcul production totale d'un jour"""
    prod_extrusion = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    
    prod_imprimerie = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    
    prod_soudure = ProductionSoudure.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    
    prod_recyclage = ProductionRecyclage.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    
    return prod_extrusion + prod_imprimerie + prod_soudure + prod_recyclage

def get_production_section_jour(section, date):
    """Production d'une section pour un jour"""
    if section == 'extrusion':
        return ProductionExtrusion.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    elif section == 'imprimerie':
        return ProductionImprimerie.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    elif section == 'soudure':
        return ProductionSoudure.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    elif section == 'recyclage':
        return ProductionRecyclage.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or Decimal('0')
    
    return Decimal('0')

def get_dechets_totaux_jour(date):
    """Total des déchets d'un jour"""
    dechets_extrusion = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('dechets_kg'))['total'] or Decimal('0')
    
    dechets_imprimerie = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(total=Sum('dechets_kg'))['total'] or Decimal('0')
    
    dechets_soudure = ProductionSoudure.objects.filter(
        date_production=date
    ).aggregate(total=Sum('dechets_kg'))['total'] or Decimal('0')
    
    return dechets_extrusion + dechets_imprimerie + dechets_soudure

def get_efficacite_moyenne_jour(date):
    """Efficacité moyenne d'un jour"""
    efficacite = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or Decimal('0')
    
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
    else:
        return ZoneExtrusion.objects.filter(active=True)

def get_sections_data(date):
    """Données des sections pour les cards du dashboard"""
    return {
        'extrusion': {
            'production': get_production_section_jour('extrusion', date),
            'zones_actives': ZoneExtrusion.objects.filter(active=True).count(),
            'status': 'active',
        },
        'imprimerie': {
            'production': get_production_section_jour('imprimerie', date),
            'machines': Machine.objects.filter(section='imprimerie', etat='actif').count(),
            'status': 'active',
        },
        'soudure': {
            'production': get_production_section_jour('soudure', date),
            'machines': Machine.objects.filter(section='soudure', etat='actif').count(),
            'status': 'maintenance' if Machine.objects.filter(section='soudure', etat='maintenance').exists() else 'active',
        },
        'recyclage': {
            'production': get_production_section_jour('recyclage', date),
            'moulinex': Machine.objects.filter(section='recyclage', etat='actif').count(),
            'status': 'active',
        },
    }

def get_productions_filtrees(filters):
    """Obtenir productions filtrées pour l'historique"""
    # Construction des filtres de dates
    date_filters = {}
    
    if filters.get('mois'):
        year, month = filters['mois'].split('-')
        date_filters['date_production__year'] = int(year)
        date_filters['date_production__month'] = int(month)
    
    if filters.get('date_debut'):
        date_filters['date_production__gte'] = filters['date_debut']
    
    if filters.get('date_fin'):
        date_filters['date_production__lte'] = filters['date_fin']
    
    # Données de production
    productions_data = {
        'extrusion': ProductionExtrusion.objects.filter(**date_filters).select_related('zone', 'equipe', 'cree_par'),
        'imprimerie': ProductionImprimerie.objects.filter(**date_filters).select_related('cree_par'),
        'soudure': ProductionSoudure.objects.filter(**date_filters).select_related('cree_par'),
        'recyclage': ProductionRecyclage.objects.filter(**date_filters).select_related('equipe', 'cree_par'),
    }
    
    # Calcul des totaux
    totaux = {
        'extrusion': productions_data['extrusion'].aggregate(total=Sum('total_production_kg'), dechets=Sum('dechets_kg')),
        'imprimerie': productions_data['imprimerie'].aggregate(total=Sum('total_production_kg'), dechets=Sum('dechets_kg')),
        'soudure': productions_data['soudure'].aggregate(total=Sum('total_production_kg'), dechets=Sum('dechets_kg')),
        'recyclage': productions_data['recyclage'].aggregate(total=Sum('total_production_kg')),
    }
    
    return productions_data, totaux

# Fonctions pour le dashboard direction (simplifiées)
def get_production_totale_periode(debut, fin):
    """Production totale sur période"""
    return get_production_totale_jour(debut)  # Simplifié pour l'exemple

def get_croissance_mensuelle(debut, fin):
    """Croissance mensuelle"""
    return 12.5  # Valeur exemple

def get_efficacite_globale_periode(debut, fin):
    """Efficacité globale période"""
    return 87.3  # Valeur exemple

def get_taux_qualite_periode(debut, fin):
    """Taux qualité période"""
    return 96.8  # Valeur exemple

def get_taux_dechet_global_periode(debut, fin):
    """Taux déchet global période"""
    return 3.2  # Valeur exemple

def get_sections_executive_data(debut, fin):
    """Données exécutives par section"""
    return {
        'extrusion': {'production': 58400, 'efficacite': 89.2, 'dechets': 1200},
        'imprimerie': {'production': 37200, 'efficacite': 91.5, 'dechets': 800},
        'soudure': {'production': 32800, 'efficacite': 85.3, 'dechets': 950},
        'recyclage': {'production': 16800, 'transformation': 78.2},
    }

def get_tendances_journalieres(debut, fin):
    """Tendances journalières pour graphiques"""
    return [
        {'date': '01/09', 'production': 12450},
        {'date': '02/09', 'production': 13200},
        {'date': '03/09', 'production': 11800},
        # ... autres jours
    ]