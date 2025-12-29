"""
Vues pour la maintenance prédictive IA
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
import json

from ..models import Machine, AlerteIA, HistoriqueMachine
from ..ia_predictive import (
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
    """Dashboard principal de maintenance prédictive"""
    
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
    
    # Alertes IA actives
    alertes_queryset = obtenir_alertes_actives()
    nombre_alertes_critiques = alertes_queryset.filter(niveau='critique').count()
    nombre_alertes_urgentes = alertes_queryset.filter(niveau='urgent').count()
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

# ==========================================
# FORMULAIRES IA
# ==========================================

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
            
            if duree:
                duree_float = float(duree)
            else:
                duree_float = 0
            
            if cout:
                cout_decimal = Decimal(cout)
            else:
                cout_decimal = None
            
            enregistrer_panne(machine, description, duree_float, technicien, cout_decimal)
            
            messages.warning(request, f'Panne enregistrée pour {machine.numero}')
            return redirect('machine_detail_ia', machine_id=machine_id)
        
        except Exception as e:
            messages.error(request, f'Erreur: {str(e)}')
    
    context = {'machine': machine}
    return render(request, 'enregistrer_panne.html', context)

# ==========================================
# GESTION ALERTES IA
# ==========================================

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
    from django.core.paginator import Paginator
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

# ==========================================
# SIMULATION CAPTEURS (TESTS)
# ==========================================

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

# ==========================================
# FONCTIONS SUPPLEMENTAIRES SI NECESSAIRE
# ==========================================

# Ajoutez cette vue si elle manque dans ia_predictive.py
@login_required
def machine_detail_ia_view(request, machine_id):
    """Vue détaillée d'une machine avec analyse IA"""
    
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Analyser la machine
    try:
        analyse = analyser_machine_specifique(machine_id)
    except Exception as e:
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