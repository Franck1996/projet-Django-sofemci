from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q

from ..models import AlerteIA, Machine
from ..utils import (
    get_production_totale_jour, get_production_section_jour, get_dechets_totaux_jour,
    get_efficacite_moyenne_jour, get_machines_stats, get_zones_performance,
    get_extrusion_details_jour, get_imprimerie_details_jour, get_soudure_details_jour,
    get_recyclage_details_jour, get_chart_data_for_dashboard, get_analytics_kpis,
    get_analytics_table_data, calculer_pourcentage_production, calculer_pourcentage_section,
    get_objectif_section,
)



@login_required
def liste_alertes_ia(request):
    """Liste complète des alertes IA avec filtres"""
    if request.user.role not in ['superviseur', 'admin', 'direction']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    # Filtres
    niveau_filtre = request.GET.get('niveau', '')
    statut_filtre = request.GET.get('statut', '')
    section_filtre = request.GET.get('section', '')
    
    alertes = AlerteIA.objects.all().select_related('machine', 'traite_par')
    
    if niveau_filtre:
        alertes = alertes.filter(niveau=niveau_filtre)
    
    if statut_filtre:
        alertes = alertes.filter(statut=statut_filtre)
    
    if section_filtre:
        alertes = alertes.filter(machine__section=section_filtre)
    
    # Pagination
    paginator = Paginator(alertes.order_by('-date_creation'), 20)
    page_number = request.GET.get('page')
    alertes_page = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': AlerteIA.objects.count(),
        'nouvelles': AlerteIA.objects.filter(statut='nouvelle').count(),
        'en_traitement': AlerteIA.objects.filter(statut='en_traitement').count(),
        'resolues': AlerteIA.objects.filter(statut='resolue').count(),
        'par_niveau': AlerteIA.objects.values('niveau').annotate(count=Count('id')),
    }
    
    context = {
        'alertes': alertes_page,
        'stats': stats,
        'niveaux': AlerteIA.NIVEAU_ALERTE,
        'statuts': AlerteIA.STATUT,
        'sections': Machine.SECTIONS,
        'niveau_filtre': niveau_filtre,
        'statut_filtre': statut_filtre,
        'section_filtre': section_filtre,
    }
    
    return render(request, 'liste_alertes_la.html', context)

@login_required
def traiter_alerte_ia(request, alerte_id):
    """Prendre en charge ou résoudre une alerte IA"""
    alerte = get_object_or_404(AlerteIA, id=alerte_id)
    
    if request.user.role not in ['superviseur', 'admin']:
        messages.error(request, 'Permission refusée.')
        return redirect('liste_alertes_ia')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        commentaire = request.POST.get('commentaire', '')
        
        if action == 'prendre_en_charge':
            alerte.prendre_en_charge(request.user)
            messages.success(request, f'Alerte "{alerte.titre}" prise en charge.')
        
        elif action == 'resoudre':
            alerte.resoudre(commentaire)
            messages.success(request, f'Alerte "{alerte.titre}" marquée comme résolue.')
        
        elif action == 'ignorer':
            alerte.statut = 'ignoree'
            alerte.traite_par = request.user
            alerte.save()
            messages.info(request, f'Alerte "{alerte.titre}" ignorée.')
    
    return redirect('liste_alertes_ia')

@login_required
def lancer_analyse_complete(request):
    """Lance l'analyse IA sur toutes les machines"""
    if request.user.role not in ['admin', 'superviseur']:
        messages.error(request, 'Permission refusée.')
        return redirect('dashboard_ia')
    
    # Simulation d'analyse IA complète
    from django.utils import timezone
    import random
    from decimal import Decimal
    
    machines = Machine.objects.filter(etat='actif')
    nouvelles_alertes = 0
    
    for machine in machines:
        # Simulation d'analyse IA
        score_sante = Decimal(str(round(random.uniform(60, 95), 2)))
        proba_7j = Decimal(str(round(random.uniform(5, 80), 2)))
        proba_30j = Decimal(str(round(random.uniform(10, 90), 2)))
        
        # Mettre à jour les scores
        machine.score_sante_global = score_sante
        machine.probabilite_panne_7_jours = proba_7j
        machine.probabilite_panne_30_jours = proba_30j
        machine.date_derniere_analyse_ia = timezone.now()
        
        # Générer des alertes si nécessaire
        if proba_7j > 50:
            niveau = 'critique' if proba_7j > 70 else 'urgent' if proba_7j > 50 else 'attention'
            
            AlerteIA.objects.create(
                machine=machine,
                niveau=niveau,
                titre=f"Risque de panne élevé - {machine.numero}",
                message=f"Probabilité de panne dans les 7 jours: {proba_7j}%. Score de santé: {score_sante}%.",
                probabilite_panne=proba_7j,
                delai_estime_jours=7,
                confiance_prediction=Decimal('85.0'),
                action_recommandee="Effectuer une maintenance préventive et surveiller les paramètres.",
                priorite=8 if niveau == 'critique' else 6,
                modele_ia_version='v1.0'
            )
            nouvelles_alertes += 1
        
        machine.save()
    
    if nouvelles_alertes > 0:
        messages.success(request, f'Analyse IA terminée. {nouvelles_alertes} nouvelles alertes générées.')
    else:
        messages.info(request, 'Analyse IA terminée. Aucune nouvelle alerte critique détectée.')
    
    return redirect('dashboard_ia')