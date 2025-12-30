# sofemci/views/production_views.py
"""
Vues de saisie de production (toutes sections) - VERSION AMÉLIORÉE
"""
from decimal import Decimal
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
    """Saisie production extrusion - VERSION AMÉLIORÉE"""
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
            # Affichage détaillé des erreurs
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_name}: {error}")
    
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
    """Saisie production autres sections - VERSION AMÉLIORÉE"""
    
    today = timezone.now().date()
    equipes = Equipe.objects.all()
    active_tab = 'imprimerie'
    
    # Formulaires initiaux
    form_imprimerie = ProductionImprimerieForm()
    form_soudure = ProductionSoudureForm()
    form_recyclage = ProductionRecyclageForm()
    
    if request.method == 'POST':
        section = request.POST.get('section', 'imprimerie')
        active_tab = section
        
        try:
            if section == 'imprimerie':
                form_imprimerie = ProductionImprimerieForm(request.POST)
                if form_imprimerie.is_valid():
                    production = form_imprimerie.save(commit=False)
                    production.cree_par = request.user
                    production.save()
                    messages.success(request, '✅ Production imprimerie enregistrée avec succès!')
                    # Réinitialiser le formulaire
                    form_imprimerie = ProductionImprimerieForm()
                else:
                    # Affichage détaillé des erreurs
                    for field, errors in form_imprimerie.errors.items():
                        for error in errors:
                            field_name = form_imprimerie.fields[field].label if field in form_imprimerie.fields else field
                            messages.error(request, f"Imprimerie - {field_name}: {error}")
            
            elif section == 'soudure':
                form_soudure = ProductionSoudureForm(request.POST)
                if form_soudure.is_valid():
                    production = form_soudure.save(commit=False)
                    production.cree_par = request.user
                    production.save()
                    messages.success(request, '✅ Production soudure enregistrée avec succès!')
                    # Réinitialiser le formulaire
                    form_soudure = ProductionSoudureForm()
                else:
                    # Affichage détaillé des erreurs
                    for field, errors in form_soudure.errors.items():
                        for error in errors:
                            field_name = form_soudure.fields[field].label if field in form_soudure.fields else field
                            messages.error(request, f"Soudure - {field_name}: {error}")
            
            elif section == 'recyclage':
                form_recyclage = ProductionRecyclageForm(request.POST)
                if form_recyclage.is_valid():
                    production = form_recyclage.save(commit=False)
                    production.cree_par = request.user
                    production.save()
                    messages.success(request, '✅ Production recyclage enregistrée avec succès!')
                    # Réinitialiser le formulaire
                    form_recyclage = ProductionRecyclageForm()
                else:
                    # Affichage détaillé des erreurs
                    for field, errors in form_recyclage.errors.items():
                        for error in errors:
                            field_name = form_recyclage.fields[field].label if field in form_recyclage.fields else field
                            messages.error(request, f"Recyclage - {field_name}: {error}")
            
            else:
                messages.error(request, '❌ Section invalide')
        
        except Exception as e:
            print(f"Exception: {str(e)}")
            messages.error(request, f'❌ Erreur lors de l\'enregistrement: {str(e)}')
    
    context = {
        'today': today,
        'equipes': equipes,
        'active_tab': active_tab,
        'form_imprimerie': form_imprimerie,
        'form_soudure': form_soudure,
        'form_recyclage': form_recyclage,
    }
    
    return render(request, 'saisie_sections.html', context)

@login_required
def saisie_imprimerie_ajax(request):
    """API AJAX pour saisie imprimerie - VERSION AMÉLIORÉE"""
    if request.method == 'POST':
        form = ProductionImprimerieForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({
                'success': True, 
                'message': '✅ Production imprimerie enregistrée !'
            })
        
        # Retourne les erreurs en JSON
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = list(field_errors)
        
        return JsonResponse({
            'success': False, 
            'errors': errors,
            'message': '❌ Veuillez corriger les erreurs ci-dessous'
        })
    
    return JsonResponse({
        'success': False, 
        'message': '❌ Méthode non autorisée'
    }, status=405)

@login_required
def saisie_soudure_ajax(request):
    """API AJAX pour saisie soudure - VERSION AMÉLIORÉE"""
    if request.method == 'POST':
        form = ProductionSoudureForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({
                'success': True, 
                'message': '✅ Production soudure enregistrée !'
            })
        
        # Retourne les erreurs en JSON
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = list(field_errors)
        
        return JsonResponse({
            'success': False, 
            'errors': errors,
            'message': '❌ Veuillez corriger les erreurs ci-dessous'
        })
    
    return JsonResponse({
        'success': False, 
        'message': '❌ Méthode non autorisée'
    }, status=405)

@login_required
def saisie_recyclage_ajax(request):
    """API AJAX pour saisie recyclage - VERSION AMÉLIORÉE"""
    if request.method == 'POST':
        form = ProductionRecyclageForm(request.POST)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            production.save()
            return JsonResponse({
                'success': True, 
                'message': '✅ Production recyclage enregistrée !'
            })
        
        # Retourne les erreurs en JSON
        errors = {}
        for field, field_errors in form.errors.items():
            errors[field] = list(field_errors)
        
        return JsonResponse({
            'success': False, 
            'errors': errors,
            'message': '❌ Veuillez corriger les erreurs ci-dessous'
        })
    
    return JsonResponse({
        'success': False, 
        'message': '❌ Méthode non autorisée'
    }, status=405)

@login_required
def api_calculs_production(request):
    """API pour calculs en temps réel - VERSION AMÉLIORÉE"""
    if request.method != 'POST':
        return JsonResponse({
            'error': '❌ Méthode non autorisée'
        }, status=400)
    
    try:
        data = json.loads(request.body)
        section = data.get('section')
        
        if section == 'extrusion':
            result = calculate_extrusion_metrics(data)
        elif section == 'imprimerie':
            result = calculate_imprimerie_metrics(data)
        elif section == 'soudure':
            result = calculate_soudure_metrics(data)
        elif section == 'recyclage':
            result = calculate_recyclage_metrics(data)
        else:
            return JsonResponse({
                'error': '❌ Section invalide'
            }, status=400)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'error': f'❌ Erreur serveur: {str(e)}'
        }, status=500)