# sofemci/views/production_views.py (modifications importantes)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
import json

from ..utils.permissions import chef_extrusion_only, chef_section_only, direction_or_superviseur
from ..models import ProductionExtrusion, Equipe
from ..formulaires import (
    ProductionExtrusionForm, ProductionImprimerieForm,
    ProductionSoudureForm, ProductionRecyclageForm
)

@login_required
@chef_extrusion_only
def saisie_extrusion_view(request):
    """Saisie production extrusion - Accès restreint aux chefs extrusion"""
    # Vérifier si l'utilisateur est direction (lecture seule)
    if request.user.is_direction():
        messages.warning(request, "⛔ Accès refusé : Vous êtes en mode lecture seule.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductionExtrusionForm(request.POST, user=request.user)
        if form.is_valid():
            production = form.save(commit=False)
            production.cree_par = request.user
            
            # Si c'est un chef d'extrusion, assigner sa zone automatiquement
            if request.user.is_chef_extrusion():
                zone_map = {
                    request.user.CHEF_EXT1: 'Zone 1',
                    request.user.CHEF_EXT2: 'Zone 2',
                    request.user.CHEF_EXT3: 'Zone 3',
                    request.user.CHEF_EXT4: 'Zone 4',
                    request.user.CHEF_EXT5: 'Zone 5'
                }
                user_zone = zone_map.get(request.user.role)
                if user_zone:
                    # Récupérer l'objet Zone correspondant
                    from ..models import Zone
                    try:
                        zone_obj = Zone.objects.get(nom=user_zone)
                        production.zone = zone_obj
                    except Zone.DoesNotExist:
                        pass
            
            production.save()
            messages.success(request, '✅ Production d\'extrusion enregistrée avec succès !')
            return redirect('saisie_extrusion')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields[field].label if field in form.fields else field
                    messages.error(request, f"{field_name}: {error}")
    else:
        form = ProductionExtrusionForm(user=request.user)
    
    context = {
        'form': form,
        'today': timezone.now().date(),
        'equipes': Equipe.objects.all(),
    }
    
    # Si c'est un chef d'extrusion, limiter l'affichage aux productions de sa zone
    if request.user.is_chef_extrusion():
        zone_map = {
            request.user.CHEF_EXT1: 'Zone 1',
            request.user.CHEF_EXT2: 'Zone 2',
            request.user.CHEF_EXT3: 'Zone 3',
            request.user.CHEF_EXT4: 'Zone 4',
            request.user.CHEF_EXT5: 'Zone 5'
        }
        user_zone = zone_map.get(request.user.role)
        context['productions_recentes'] = ProductionExtrusion.objects.filter(
            zone__nom=user_zone
        ).select_related('zone', 'equipe').order_by('-date_creation')[:10]
        context['user_zone'] = user_zone
    else:
        # Pour superviseur/admin, afficher toutes les productions
        context['productions_recentes'] = ProductionExtrusion.objects.all().select_related('zone', 'equipe').order_by('-date_creation')[:10]
    
    return render(request, 'saisie_extrusion.html', context)

@login_required
@chef_section_only
def saisie_sections_view(request):
    """Saisie production autres sections - Accès restreint aux chefs de section"""
    # Vérifier si l'utilisateur est direction (lecture seule)
    if request.user.is_direction():
        messages.warning(request, "⛔ Accès refusé : Vous êtes en mode lecture seule.")
        return redirect('dashboard')
    
    today = timezone.now().date()
    equipes = Equipe.objects.all()
    
    # Déterminer l'onglet actif selon le rôle
    if request.user.role == request.user.CHEF_IMPRIM:
        active_tab = 'imprimerie'
    elif request.user.role == request.user.CHEF_SOUD:
        active_tab = 'soudure'
    elif request.user.role == request.user.CHEF_RECYCL:
        active_tab = 'recyclage'
    else:
        active_tab = 'imprimerie'
    
    # Formulaires initiaux
    form_imprimerie = ProductionImprimerieForm()
    form_soudure = ProductionSoudureForm()
    form_recyclage = ProductionRecyclageForm()
    
    if request.method == 'POST':
        section = request.POST.get('section', active_tab)
        active_tab = section
        
        # Vérifier que l'utilisateur a le droit d'accéder à cette section
        if (section == 'imprimerie' and not (request.user.role == request.user.CHEF_IMPRIM or request.user.is_superviseur() or request.user.is_admin())) or \
           (section == 'soudure' and not (request.user.role == request.user.CHEF_SOUD or request.user.is_superviseur() or request.user.is_admin())) or \
           (section == 'recyclage' and not (request.user.role == request.user.CHEF_RECYCL or request.user.is_superviseur() or request.user.is_admin())):
            messages.error(request, '❌ Accès non autorisé à cette section.')
            return redirect('saisie_sections')
        
        try:
            if section == 'imprimerie':
                form_imprimerie = ProductionImprimerieForm(request.POST)
                if form_imprimerie.is_valid():
                    production = form_imprimerie.save(commit=False)
                    production.cree_par = request.user
                    production.save()
                    messages.success(request, '✅ Production imprimerie enregistrée avec succès!')
                    form_imprimerie = ProductionImprimerieForm()
            
            elif section == 'soudure':
                form_soudure = ProductionSoudureForm(request.POST)
                if form_soudure.is_valid():
                    production = form_soudure.save(commit=False)
                    production.cree_par = request.user
                    production.save()
                    messages.success(request, '✅ Production soudure enregistrée avec succès!')
                    form_soudure = ProductionSoudureForm()
            
            elif section == 'recyclage':
                form_recyclage = ProductionRecyclageForm(request.POST)
                if form_recyclage.is_valid():
                    production = form_recyclage.save(commit=False)
                    production.cree_par = request.user
                    production.save()
                    messages.success(request, '✅ Production recyclage enregistrée avec succès!')
                    form_recyclage = ProductionRecyclageForm()
            
            else:
                messages.error(request, '❌ Section invalide')
        
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de l\'enregistrement: {str(e)}')
    
    context = {
        'today': today,
        'equipes': equipes,
        'active_tab': active_tab,
        'form_imprimerie': form_imprimerie,
        'form_soudure': form_soudure,
        'form_recyclage': form_recyclage,
        'user_role': request.user.role,
    }
    
    return render(request, 'saisie_sections.html', context)