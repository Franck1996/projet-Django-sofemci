from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from ..models import (
    ProductionExtrusion, ProductionSoudure, ProductionImprimerie, 
    ProductionRecyclage, Equipe, Machine, ZoneExtrusion
)

def get_production_totale_jour(date):
    """Production totale d'un jour"""
    total = Decimal('0')
    
    # Extrusion
    extrusion_total = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += extrusion_total
    
    # Imprimerie
    imprimerie_total = ProductionImprimerie.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += imprimerie_total
    
    # Soudure
    soudure_total = ProductionSoudure.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += soudure_total
    
    # Recyclage
    recyclage_total = ProductionRecyclage.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    total += recyclage_total
    
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
    
    result = model.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    return result

def get_dechets_totaux_jour(date):
    """Total des déchets d'un jour"""
    total = Decimal('0')
    
    # Extrusion
    extrusion_dechets = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    total += extrusion_dechets
    
    # Imprimerie
    imprimerie_dechets = ProductionImprimerie.objects.filter(date_production=date).aggregate(
        Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    total += imprimerie_dechets
    
    # Soudure
    soudure_dechets = ProductionSoudure.objects.filter(date_production=date).aggregate(
        Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    total += soudure_dechets
    
    return total

def get_efficacite_moyenne_jour(date):
    """Efficacité moyenne d'un jour"""
    efficacite = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Avg('rendement_pourcentage'))['rendement_pourcentage__avg'] or Decimal('0')
    
    return round(efficacite, 1) if efficacite else 0

def get_extrusion_details_jour(date):
    """Détails extrusion du jour - Version simplifiée"""
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
        'temps_travail': 8,
        'machinistes_moyen': round(nombre_moyen_machinistes, 0),
        'matiere_premiere': aggregats['matiere_premiere'] or 0,
        'production_finis': aggregats['prod_finis'] or 0,
        'production_semi_finis': aggregats['prod_semi_finis'] or 0,
        'production_totale': total_prod,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_imprimerie_details_jour(date):
    """Détails imprimerie du jour - Version simplifiée"""
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
        'temps_travail': 8,
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='imprimerie').count(),
        'bobines_finies': aggregats['bobines_finis'] or 0,
        'bobines_semi_finies': aggregats['bobines_semi_finis'] or 0,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_soudure_details_jour(date):
    """Détails soudure du jour - Version simplifiée"""
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
        'temps_travail': 8,
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='soudure').count(),
        'production_bretelles': aggregats['bretelles'] or 0,
        'production_rema': aggregats['rema'] or 0,
        'production_batta': aggregats['batta'] or 0,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_recyclage_details_jour(date=None):
    """Détails recyclage du jour - Version corrigée avec Decimal"""
    # Si pas de date fournie, utiliser aujourd'hui
    if date is None:
        date = timezone.now().date()
    
    productions = ProductionRecyclage.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'moulinex_actifs': 0,
            'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
            'total_broyage': Decimal('0.00'),
            'total_bache_noir': Decimal('0.00'),
            'production_totale': Decimal('0.00'),
            'taux_transformation': Decimal('0.00'),
            'rendement': Decimal('0.00'),
            'productivite_par_moulinex': Decimal('0.00'),
            'temps_travail': 8,
        }
    
    aggregats = productions.aggregate(
        moulinex=Avg('nombre_moulinex'),
        broyage=Sum('production_broyage_kg'),
        bache=Sum('production_bache_noir_kg'),
        total=Sum('total_production_kg')
    )
    
    # Utiliser Decimal explicitement
    broyage = Decimal(str(aggregats['broyage'] or '0'))
    bache = Decimal(str(aggregats['bache'] or '0'))
    total = Decimal(str(aggregats['total'] or '0'))
    moulinex_avg = Decimal(str(aggregats['moulinex'] or '1'))
    
    # Calculs sécurisés avec Decimal
    try:
        if broyage > Decimal('0'):
            taux_transformation = (bache / broyage) * Decimal('100')
        else:
            taux_transformation = Decimal('0')
    except Exception:
        taux_transformation = Decimal('0')
    
    try:
        if moulinex_avg > Decimal('0'):
            productivite = total / moulinex_avg
        else:
            productivite = Decimal('0')
    except Exception:
        productivite = Decimal('0')
    
    return {
        'moulinex_actifs': int(round(float(moulinex_avg), 0)),
        'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
        'total_broyage': broyage.quantize(Decimal('0.01')),
        'total_bache_noir': bache.quantize(Decimal('0.01')),
        'production_totale': total.quantize(Decimal('0.01')),
        'taux_transformation': taux_transformation.quantize(Decimal('0.01')),
        'rendement': taux_transformation.quantize(Decimal('0.01')),
        'productivite_par_moulinex': productivite.quantize(Decimal('0.01')),
        'temps_travail': 8,
    }
# def get_productions_filtrees(filters):
#     """Obtenir productions filtrées pour l'historique"""
#     date_filters = {}
    
#     if filters.get('date_debut'):
#         date_filters['date_production__gte'] = filters['date_debut']
    
#     if filters.get('date_fin'):
#         date_filters['date_production__lte'] = filters['date_fin']
    
#     # Filtre par section si spécifié
#     section_filter = filters.get('section')
#     equipe_filter = filters.get('equipe')
    
#     # Extrusion
#     extrusion_query = ProductionExtrusion.objects.filter(**date_filters)
#     if section_filter == 'extrusion' or not section_filter:
#         if equipe_filter:
#             extrusion_query = extrusion_query.filter(equipe_id=equipe_filter)
    
#     # Imprimerie
#     imprimerie_query = ProductionImprimerie.objects.filter(**date_filters)
#     if section_filter == 'imprimerie' or not section_filter:
#         pass
    
#     # Soudure
#     soudure_query = ProductionSoudure.objects.filter(**date_filters)
#     if section_filter == 'soudure' or not section_filter:
#         pass
    
#     # Recyclage
#     recyclage_query = ProductionRecyclage.objects.filter(**date_filters)
#     if section_filter == 'recyclage' or not section_filter:
#         if equipe_filter:
#             recyclage_query = recyclage_query.filter(equipe_id=equipe_filter)
    
#     productions_data = {
#         'extrusion': extrusion_query.select_related('zone', 'equipe', 'cree_par'),
#         'imprimerie': imprimerie_query.select_related('cree_par'),
#         'soudure': soudure_query.select_related('cree_par'),
#         'recyclage': recyclage_query.select_related('equipe', 'cree_par'),
#     }
    
#     # Calcul des totaux
#     totaux = {
#         'extrusion': {
#             'total': extrusion_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
#             'dechets': extrusion_query.aggregate(dechets=Sum('dechets_kg'))['dechets'] or 0,
#         },
#         'imprimerie': {
#             'total': imprimerie_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
#             'dechets': imprimerie_query.aggregate(dechets=Sum('dechets_kg'))['dechets'] or 0,
#         },
#         'soudure': {
#             'total': soudure_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
#             'dechets': soudure_query.aggregate(dechets=Sum('dechets_kg'))['dechets'] or 0,
#         },
#         'recyclage': {
#             'total': recyclage_query.aggregate(total=Sum('total_production_kg'))['total'] or 0,
#             'dechets': 0,
#         },
#     }
    
#     return productions_data, totaux

def calculer_pourcentage_production(production_actuelle, production_reference=None):
    """Calcule le pourcentage de production"""
    if production_reference is None:
        production_reference = Decimal('75000')
    
    if production_reference == 0:
        return 0
    
    pourcentage = (production_actuelle / production_reference) * 100
    return round(pourcentage, 1)

def calculer_pourcentage_section(section, production_actuelle):
    """Calcule le pourcentage pour une section spécifique"""
    objectifs = {
        'extrusion': Decimal('35000'),
        'imprimerie': Decimal('20000'),
        'soudure': Decimal('12000'),
        'recyclage': Decimal('8000'),
    }
    
    objectif = objectifs.get(section, Decimal('10000'))
    
    if objectif == 0:
        return 0
    
    return round((production_actuelle / objectif) * 100, 1)

def get_objectif_section(section):
    """Retourne l'objectif journalier d'une section"""
    objectifs = {
        'extrusion': Decimal('35000'),
        'imprimerie': Decimal('20000'),
        'soudure': Decimal('12000'),
        'recyclage': Decimal('8000'),
    }
    return objectifs.get(section, Decimal('10000'))