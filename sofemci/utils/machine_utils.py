from django.db.models import Count
from ..models import Machine, ZoneExtrusion

def get_machines_stats():
    """Statistiques des machines"""
    return {
        'total': Machine.objects.count(),
        'actives': Machine.objects.filter(etat='actif').count(),
        'maintenance': Machine.objects.filter(etat='maintenance').count(),
        'pannes': Machine.objects.filter(etat='panne').count(),
    }

def get_zones_performance(date):
    """Performance des zones d'extrusion"""
    from django.db.models import Sum, Avg
    from ..models import ProductionExtrusion
    
    zones_performance = []
    for zone in ZoneExtrusion.objects.filter(active=True):
        prod_zone = ProductionExtrusion.objects.filter(
            date_production=date,
            zone=zone
        ).aggregate(
            total=Sum('total_production_kg'),
            machines=Avg('nombre_machines_actives'),
            efficacite=Avg('rendement_pourcentage')
        )
        
        zones_performance.append({
            'zone': zone,
            'production': prod_zone['total'] or 0,
            'machines_actives': int(prod_zone['machines'] or 0),
            'efficacite': round(prod_zone['efficacite'] or 0, 1)
        })
    
    return zones_performance

def get_zones_utilisateur(user):
    """Zones accessibles selon l'utilisateur"""
    if user.role == 'chef_extrusion':
        return ZoneExtrusion.objects.filter(chef_zone=user, active=True)
    return ZoneExtrusion.objects.filter(active=True)