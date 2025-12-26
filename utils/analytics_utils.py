from django.db.models import Sum, Avg
from datetime import datetime, timedelta
from decimal import Decimal
from ..models import ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage

def get_extrusion_details_jour_complet(date):
    """Détails complets extrusion du jour avec calcul temps"""
    productions = ProductionExtrusion.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'temps_travail_total': 0,
            'nombre_machines': 0,
            'production_bobines_finis': 0,
            'production_bobines_semi_finis': 0,
            'total_production': 0,
            'total_dechets': 0,
        }
    
    # Temps de travail
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bobines_finis=Sum('production_finis_kg'),
        bobines_semi_finis=Sum('production_semi_finis_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )
    
    return {
        'temps_travail_total': round(temps_total_minutes / 60, 1),
        'nombre_machines': round(aggregats['machines'] or 0, 0),
        'production_bobines_finis': aggregats['bobines_finis'] or 0,
        'production_bobines_semi_finis': aggregats['bobines_semi_finis'] or 0,
        'total_production': aggregats['total'] or 0,
        'total_dechets': aggregats['dechets'] or 0,
    }

def get_imprimerie_details_jour_complet(date):
    """Détails complets imprimerie du jour avec calcul temps"""
    productions = ProductionImprimerie.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'temps_travail_total': 0,
            'nombre_machines': 0,
            'production_bobines_finis': 0,
            'production_bobines_semi_finis': 0,
            'total_production': 0,
            'total_dechets': 0,
        }
    
    # Temps de travail
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bobines_finis=Sum('production_bobines_finies_kg'),
        bobines_semi_finis=Sum('production_bobines_semi_finies_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )
    
    return {
        'temps_travail_total': round(temps_total_minutes / 60, 1),
        'nombre_machines': round(aggregats['machines'] or 0, 0),
        'production_bobines_finis': aggregats['bobines_finis'] or 0,
        'production_bobines_semi_finis': aggregats['bobines_semi_finis'] or 0,
        'total_production': aggregats['total'] or 0,
        'total_dechets': aggregats['dechets'] or 0,
    }

def get_soudure_details_jour_complet(date):
    """Détails complets soudure du jour avec calcul temps"""
    productions = ProductionSoudure.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'temps_travail_total': 0,
            'nombre_machines': 0,
            'production_bobines_finis': 0,
            'production_bretelles': 0,
            'production_rema': 0,
            'production_batta': 0,
            'total_production': 0,
            'total_dechets': 0,
        }
    
    # Temps de travail
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    aggregats = productions.aggregate(
        machines=Avg('nombre_machines_actives'),
        bobines=Sum('production_bobines_finies_kg'),
        bretelles=Sum('production_bretelles_kg'),
        rema=Sum('production_rema_kg'),
        batta=Sum('production_batta_kg'),
        total=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )
    
    return {
        'temps_travail_total': round(temps_total_minutes / 60, 1),
        'nombre_machines': round(aggregats['machines'] or 0, 0),
        'production_bobines_finis': aggregats['bobines'] or 0,
        'production_bretelles': aggregats['bretelles'] or 0,
        'production_rema': aggregats['rema'] or 0,
        'production_batta': aggregats['batta'] or 0,
        'total_production': aggregats['total'] or 0,
        'total_dechets': aggregats['dechets'] or 0,
    }

def get_recyclage_details_jour():
    """Détails production recyclage aujourd'hui"""
    try:
        today = timezone.now().date()
        
        # Récupérer les données
        productions = ProductionRecyclage.objects.filter(date_production=today)
        
        if not productions.exists():
            return {
                'total_production_kg': Decimal('0.00'),
                'production_par_moulinex': Decimal('0.00'),
                'taux_transformation': Decimal('0.00'),
                'count': 0
            }
        
        # Initialiser avec Decimal
        total_production = Decimal('0.00')
        total_broyage = Decimal('0.00')
        total_bache = Decimal('0.00')
        total_moulinex = 0
        
        # Calculer les totaux
        for prod in productions:
            total_production += (prod.total_production_kg or Decimal('0.00'))
            total_broyage += (prod.production_broyage_kg or Decimal('0.00'))
            total_bache += (prod.production_bache_noir_kg or Decimal('0.00'))
            total_moulinex += (prod.nombre_moulinex or 0)
        
        # Calcul production par moulinex
        if total_moulinex > 0:
            # Convertir total_moulinex en Decimal pour la division
            production_par_moulinex = total_production / Decimal(str(total_moulinex))
        else:
            production_par_moulinex = Decimal('0.00')
        
        # Calcul taux transformation
        if total_broyage > Decimal('0'):
            taux_transformation = (total_bache / total_broyage) * Decimal('100')
        else:
            taux_transformation = Decimal('0.00')
        
        # Formater pour l'affichage
        return {
            'total_production_kg': total_production.quantize(Decimal('0.01')),
            'production_par_moulinex': production_par_moulinex.quantize(Decimal('0.01')),
            'taux_transformation': taux_transformation.quantize(Decimal('0.01')),
            'count': productions.count()
        }
        
    except Exception as e:
        print(f"Erreur dans get_recyclage_details_jour: {e}")
        return {
            'total_production_kg': Decimal('0.00'),
            'production_par_moulinex': Decimal('0.00'),
            'taux_transformation': Decimal('0.00'),
            'count': 0
        }