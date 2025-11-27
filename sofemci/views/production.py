from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Sum
from decimal import Decimal  
from datetime import date, timedelta, datetime
from ..models import ProductionExtrusion, ProductionSoudure, ProductionImprimerie, ProductionRecyclage, Equipe, ZoneExtrusion
from ..forms import ProductionExtrusionForm, ProductionImprimerieForm, ProductionSoudureForm, ProductionRecyclageForm
from ..utils import (
    get_production_totale_jour, get_production_section_jour, get_dechets_totaux_jour,
    get_efficacite_moyenne_jour, get_extrusion_details_jour, get_imprimerie_details_jour, 
    get_soudure_details_jour, get_recyclage_details_jour, calculer_pourcentage_production, 
    calculer_pourcentage_section, get_objectif_section, 
)


@login_required
def saisie_extrusion_view(request):
    # Initialisation des variables
    form = ProductionExtrusionForm()
    zones = ZoneExtrusion.objects.filter(active=True)
    equipes = Equipe.objects.all()
    today = timezone.now().date()
    
    try:
        if request.method == 'POST':
            form = ProductionExtrusionForm(request.POST)
            if form.is_valid():
                try:
                    production = form.save(commit=False)
                    equipe = production.equipe
                    production.heure_debut = equipe.heure_debut
                    production.heure_fin = equipe.heure_fin
                    production.cree_par = request.user
                    production.save()
                    
                    messages.success(request, "✅ Production extrusion enregistrée avec succès !")
                    return redirect('saisie_extrusion')
                    
                except Exception as save_error:
                    print(f"Erreur sauvegarde: {save_error}")
                    messages.error(request, f"❌ Erreur sauvegarde: {str(save_error)}")
            else:
                messages.error(request, "❌ Veuillez corriger les erreurs dans le formulaire.")
        
        # Si GET ou après erreur POST
        context = {
            'form': form,
            'zones': zones,
            'equipes': equipes,
            'today': today
        }
        return render(request, 'saisie_extrusion.html', context)
        
    except Exception as general_error:
        print(f"Erreur générale saisie_extrusion: {general_error}")
        messages.error(request, "❌ Une erreur inattendue s'est produite.")
        
        context = {
            'form': form,
            'zones': zones,
            'equipes': equipes,
            'today': today
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
                success_message = '✅ Production imprimerie enregistrée avec succès !'
            else:
                messages.error(request, 'Erreur dans le formulaire imprimerie')
        
        elif section == 'soudure' and 'soudure' in user_sections:
            form_soudure = ProductionSoudureForm(request.POST)
            if form_soudure.is_valid():
                production = form_soudure.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = '✅ Production soudure enregistrée avec succès !'
            else:
                messages.error(request, 'Erreur dans le formulaire soudure')
        
        elif section == 'recyclage' and 'recyclage' in user_sections:
            form_recyclage = ProductionRecyclageForm(request.POST)
            if form_recyclage.is_valid():
                production = form_recyclage.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = '✅ Production recyclage enregistrée avec succès !'
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
                'message': '✅ Production imprimerie enregistrée !'
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
                'message': '✅ Production soudure enregistrée !'
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
                'message': '✅ Production recyclage enregistrée !'
            })
        return JsonResponse({
            'success': False, 
            'errors': form.errors,
            'message': 'Erreur dans le formulaire'
        })
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


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
        production.save()
        
        return JsonResponse({'success': True, 'message': 'Production validée avec succès'})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})