from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count 
from ..models import Machine, ZoneExtrusion
from ..forms import MachineForm

from ..utils import (
    get_production_totale_jour, get_production_section_jour, get_dechets_totaux_jour,
    get_efficacite_moyenne_jour, get_machines_stats, get_zones_performance,
    get_extrusion_details_jour, get_imprimerie_details_jour, get_soudure_details_jour,
    get_recyclage_details_jour, get_chart_data_for_dashboard, get_analytics_kpis,
    get_analytics_table_data, calculer_pourcentage_production, calculer_pourcentage_section,
    get_objectif_section,
)


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
    
    return render(request, 'machine_confirmation_delete.html', context)

@login_required
def machine_detail_view(request, machine_id):
    """Détails d'une machine"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Historique de production pour cette machine (si extrusion)
    historique = []
    if machine.section == 'extrusion' and machine.zone_extrusion:
        from ..models import ProductionExtrusion
        historique = ProductionExtrusion.objects.filter(
            zone=machine.zone_extrusion
        ).order_by('-date_production')[:10]
    
    context = {
        'machine': machine,
        'historique': historique,
    }
    
    return render(request, 'machine_detail.html', context)

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
def machine_change_status_ajax(request, machine_id):
    """Changer le statut d'une machine (AJAX)"""
    if request.method == 'POST' and request.user.role in ['admin', 'superviseur']:
        machine = get_object_or_404(Machine, id=machine_id)
        nouvel_etat = request.POST.get('etat')
        
        if nouvel_etat in dict(Machine.ETATS).keys():
            machine.etat = nouvel_etat
            machine.save()
            return JsonResponse({
                'success': True,
                'message': f'Statut de la machine {machine.numero} mis à jour vers {machine.get_etat_display()}'
            })
        
        return JsonResponse({'success': False, 'message': 'Statut invalide'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def enregistrer_maintenance_view(request, machine_id):
    """Formulaire d'enregistrement de maintenance"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        # Logique d'enregistrement de maintenance
        description = request.POST.get('description', '')
        duree = request.POST.get('duree', '')
        technicien = request.POST.get('technicien', '')
        pieces_remplacees = request.POST.get('pieces_remplacees', '')
        
        # Créer l'historique de maintenance
        from ..models import HistoriqueMachine
        historique = HistoriqueMachine.objects.create(
            machine=machine,
            type_evenement='maintenance',
            description=description,
            duree_arret=duree,
            technicien=technicien,
            pieces_remplacees=pieces_remplacees,
            cree_par=request.user
        )
        
        # Mettre à jour la machine
        machine.derniere_maintenance = timezone.now().date()
        machine.etat = 'actif'
        machine.save()
        
        messages.success(request, f'Maintenance de la machine {machine.numero} enregistrée avec succès!')
        return redirect('machine_detail_ia', machine_id=machine_id)
    
    context = {
        'machine': machine,
    }
    return render(request, 'enregister_maintenance.html', context)

@login_required
def enregistrer_panne_view(request, machine_id):
    """Formulaire d'enregistrement de panne"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST':
        # Logique d'enregistrement de panne
        description = request.POST.get('description', '')
        duree_arret = request.POST.get('duree_arret', '')
        cout = request.POST.get('cout', '')
        technicien = request.POST.get('technicien', '')
        pieces_remplacees = request.POST.get('pieces_remplacees', '')
        
        # Créer l'historique de panne
        from ..models import HistoriqueMachine
        historique = HistoriqueMachine.objects.create(
            machine=machine,
            type_evenement='panne',
            description=description,
            duree_arret=duree_arret,
            cout_intervention=cout,
            technicien=technicien,
            pieces_remplacees=pieces_remplacees,
            cree_par=request.user
        )
        
        # Mettre à jour les statistiques de la machine
        machine.nombre_pannes_totales += 1
        machine.date_derniere_panne = timezone.now()
        machine.etat = 'panne'
        machine.save()
        
        messages.success(request, f'Panne de la machine {machine.numero} enregistrée avec succès!')
        return redirect('machine_detail_ia', machine_id=machine_id)
    
    context = {
        'machine': machine,
    }
    return render(request, 'enregister_panne.html', context)

@login_required
def simuler_capteurs_view(request, machine_id):
    """Simulation de mise à jour des capteurs (pour tests)"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    if request.method == 'POST' and request.user.role in ['admin', 'superviseur']:
        # Simulation des données de capteurs
        import random
        from decimal import Decimal
        
        # Mettre à jour les données simulées
        machine.temperature_actuelle = Decimal(str(round(random.uniform(60, 85), 2)))
        machine.consommation_electrique_kwh = Decimal(str(round(random.uniform(50, 120), 2)))
        machine.heures_fonctionnement_totales += Decimal('8.0')
        machine.heures_depuis_derniere_maintenance += Decimal('8.0')
        
        # Simuler une analyse IA
        machine.score_sante_global = Decimal(str(round(random.uniform(70, 95), 2)))
        machine.probabilite_panne_7_jours = Decimal(str(round(random.uniform(5, 40), 2)))
        machine.probabilite_panne_30_jours = Decimal(str(round(random.uniform(10, 60), 2)))
        
        # Simuler des anomalies occasionnelles
        if random.random() < 0.2:  # 20% de chance d'anomalie
            machine.anomalie_detectee = True
            anomalies = ['Surchauffe', 'Surconsommation', 'Vibrations anormales', 'Bruit excessif']
            machine.type_anomalie = random.choice(anomalies)
        else:
            machine.anomalie_detectee = False
            machine.type_anomalie = ''
        
        machine.date_derniere_analyse_ia = timezone.now()
        machine.save()
        
        messages.success(request, f'Données des capteurs simulées pour la machine {machine.numero}!')
        return redirect('machine_detail_ia', machine_id=machine_id)
    
    context = {
        'machine': machine,
    }
    return render(request, 'simuler_capteurs.html', context)