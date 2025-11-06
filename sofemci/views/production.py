from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q

from ..models import ProductionExtrusion, ProductionSoudure, ProductionImprimerie, ProductionRecyclage, Equipe, ZoneExtrusion
from ..forms import ProductionExtrusionForm, ProductionImprimerieForm, ProductionSoudureForm, ProductionRecyclageForm, FiltreHistoriqueForm

from ..utils import (
    get_production_totale_jour, get_production_section_jour, get_dechets_totaux_jour,
    get_efficacite_moyenne_jour, get_machines_stats, get_zones_performance,
    get_extrusion_details_jour, get_imprimerie_details_jour, get_soudure_details_jour,
    get_recyclage_details_jour, get_chart_data_for_dashboard, get_analytics_kpis,
    get_analytics_table_data, calculer_pourcentage_production, calculer_pourcentage_section,
    get_objectif_section, get_productions_filtrees
)


@login_required
def saisie_extrusion_view(request):
    if request.user.role not in ['chef_extrusion', 'superviseur', 'admin']:
        messages.error(request, 'Accès refusé.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductionExtrusionForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                production = form.save(commit=False)
                production.cree_par = request.user
                production.save()
                
                messages.success(request, 'pup pup ✅ Production d\'extrusion enregistrée avec succès dans la base de données !')
                return redirect('historique')
                
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'enregistrement: {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs dans le formulaire.')
    else:
        form = ProductionExtrusionForm(user=request.user)
    
    context = {
        'form': form,
        'today': timezone.now().date(),
        'zones': ZoneExtrusion.objects.filter(active=True),
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
                success_message = 'pup pup ✅ Production imprimerie enregistrée avec succès dans la base de données !'
            else:
                messages.error(request, 'Erreur dans le formulaire imprimerie')
        
        elif section == 'soudure' and 'soudure' in user_sections:
            form_soudure = ProductionSoudureForm(request.POST)
            if form_soudure.is_valid():
                production = form_soudure.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = 'pup pup ✅ Production soudure enregistrée avec succès dans la base de données !'
            else:
                messages.error(request, 'Erreur dans le formulaire soudure')
        
        elif section == 'recyclage' and 'recyclage' in user_sections:
            form_recyclage = ProductionRecyclageForm(request.POST)
            if form_recyclage.is_valid():
                production = form_recyclage.save(commit=False)
                production.cree_par = request.user
                production.save()
                success_message = 'pup pup ✅ Production recyclage enregistrée avec succès dans la base de données !'
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
def historique_view(request):
    form = FiltreHistoriqueForm(request.GET or None)
    
    # Variables par défaut
    periode_debut = None
    periode_fin = None
    
    # Appliquer les filtres
    if form.is_valid():
        filters = form.cleaned_data
        from .dashboard import get_productions_filtrees
        productions_data, totaux = get_productions_filtrees(filters)
        periode_debut = filters.get('date_debut')
        periode_fin = filters.get('date_fin')
    else:
        # Filtres par défaut (mois en cours)
        today = timezone.now().date()
        debut_mois = today.replace(day=1)
        default_filters = {
            'date_debut': debut_mois,
            'date_fin': today,
        }
        from .dashboard import get_productions_filtrees
        productions_data, totaux = get_productions_filtrees(default_filters)
        periode_debut = debut_mois
        periode_fin = today
    
    # Combiner toutes les productions pour l'affichage unifié
    all_productions = []
    
    # Extrusion
    for prod in productions_data['extrusion']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'extrusion',
            'equipe': prod.equipe,
            'zone': prod.zone,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': prod.dechets_kg,
            'rendement_pourcentage': prod.rendement_pourcentage,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': prod.heure_debut,
            'heure_fin': prod.heure_fin,
        })
    
    # Imprimerie
    for prod in productions_data['imprimerie']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'imprimerie',
            'equipe': None,
            'zone': None,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': prod.dechets_kg,
            'rendement_pourcentage': None,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': prod.heure_debut,
            'heure_fin': prod.heure_fin,
        })
    
    # Soudure
    for prod in productions_data['soudure']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'soudure',
            'equipe': None,
            'zone': None,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': prod.dechets_kg,
            'rendement_pourcentage': None,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': prod.heure_debut,
            'heure_fin': prod.heure_fin,
        })
    
    # Recyclage
    for prod in productions_data['recyclage']:
        all_productions.append({
            'id': prod.id,
            'date_production': prod.date_production,
            'section': 'recyclage',
            'equipe': prod.equipe,
            'zone': None,
            'total_production_kg': prod.total_production_kg,
            'dechets_kg': 0,
            'rendement_pourcentage': None,
            'valide': prod.valide,
            'cree_par': prod.cree_par,
            'heure_debut': None,
            'heure_fin': None,
        })
    
    # Trier par date décroissante
    all_productions.sort(key=lambda x: x['date_production'], reverse=True)
    
    # Pagination
    paginator = Paginator(all_productions, 20)
    page_number = request.GET.get('page')
    productions_page = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'productions': productions_page,
        'equipes': Equipe.objects.all(),
        'totaux': totaux,
        'periode_debut': periode_debut,
        'periode_fin': periode_fin,
    }
    
    return render(request, 'historique.html', context)

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
                'message': 'pup pup ✅ Production imprimerie enregistrée dans la base de données !'
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
                'message': 'pup pup ✅ Production soudure enregistrée dans la base de données !'
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
                'message': 'pup pup ✅ Production recyclage enregistrée dans la base de données !'
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