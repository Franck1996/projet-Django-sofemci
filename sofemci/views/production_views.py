"""
Vues de saisie de production (toutes sections)
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
import json

from ..models import (
    ProductionExtrusion, ProductionImprimerie, 
    ProductionSoudure, ProductionRecyclage,
    ZoneExtrusion, Equipe
)
from ..formulaires import (
    ProductionExtrusionForm, ProductionImprimerieForm,
    ProductionSoudureForm, ProductionRecyclageForm
)
from .utils_views import (
    get_zones_utilisateur,
    calculate_extrusion_metrics,
    calculate_imprimerie_metrics,
    calculate_soudure_metrics,
    calculate_recyclage_metrics,
)

@login_required
def saisie_extrusion_view(request):
    """Saisie production extrusion"""
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
    """Saisie production autres sections"""
    if request.method == 'POST':
        section = request.POST.get('section')
        print(f"Section reçue: {section}")
        
        try:
            if section == 'soudure':
                form_data = request.POST.copy()
                form = ProductionSoudureForm(form_data)
                
                if not form.is_valid():
                    print("Erreurs de formulaire:", form.errors)
                    messages.error(request, f"Erreur dans le formulaire: {form.errors}")
                    return redirect('saisie_sections')
                
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
            print(f"Exception: {str(e)}")
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
    """API AJAX pour saisie imprimerie"""
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
    """API AJAX pour saisie soudure"""
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
    """API AJAX pour saisie recyclage"""
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
    """API pour calculs en temps réel"""
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