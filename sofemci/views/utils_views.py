"""
Fonctions utilitaires pour les calculs et statistiques
"""
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from ..models import (
    ProductionExtrusion, ProductionImprimerie,
    ProductionSoudure, ProductionRecyclage,
    Machine, ZoneExtrusion, Equipe, Alerte, CustomUser
)

# ==========================================
# FONCTIONS DE PRODUCTION (JOUR)
# ==========================================

def get_production_totale_jour(date):
    """Production totale d'un jour"""
    total = Decimal('0')
    
    total += ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
    total += ProductionImprimerie.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
    total += ProductionSoudure.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
    total += ProductionRecyclage.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    
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
    
    return model.objects.filter(date_production=date).aggregate(
        Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')

def get_dechets_totaux_jour(date):
    """Total des déchets d'un jour"""
    total = Decimal('0')
    
    for model in [ProductionExtrusion, ProductionImprimerie, ProductionSoudure]:
        total += model.objects.filter(date_production=date).aggregate(
            Sum('dechets_kg'))['dechets_kg__sum'] or Decimal('0')
    
    return total

def get_efficacite_moyenne_jour(date):
    """Efficacité moyenne d'un jour"""
    efficacite = ProductionExtrusion.objects.filter(date_production=date).aggregate(
        Avg('rendement_pourcentage'))['rendement_pourcentage__avg'] or Decimal('0')
    
    return round(efficacite, 1) if efficacite else 0

# ==========================================
# FONCTIONS MACHINES
# ==========================================

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

# ==========================================
# FONCTIONS DÉTAILS PAR SECTION
# ==========================================

def get_extrusion_details_jour(date):
    """Détails extrusion du jour"""
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
    
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
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
        'temps_travail': round(temps_total_minutes / 60, 1),
        'machinistes_moyen': round(nombre_moyen_machinistes, 0),
        'matiere_premiere': aggregats['matiere_premiere'] or 0,
        'production_finis': aggregats['prod_finis'] or 0,
        'production_semi_finis': aggregats['prod_semi_finis'] or 0,
        'production_totale': total_prod,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_imprimerie_details_jour(date):
    """Détails imprimerie du jour"""
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
    
    total = aggregats['total'] or 0
    dechets = aggregats['dechets'] or 0
    taux_dechet = (dechets / (total + dechets) * 100) if (total + dechets) > 0 else 0
    
    return {
        'temps_travail': round(temps_total_minutes / 60, 1),
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='imprimerie').count(),
        'bobines_finies': aggregats['bobines_finis'] or 0,
        'bobines_semi_finies': aggregats['bobines_semi_finis'] or 0,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_soudure_details_jour(date):
    """Détails soudure du jour"""
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
        'temps_travail': round(temps_total_minutes / 60, 1),
        'machines_actives': round(aggregats['machines'] or 0, 0),
        'machines_totales': Machine.objects.filter(section='soudure').count(),
        'production_bretelles': aggregats['bretelles'] or 0,
        'production_rema': aggregats['rema'] or 0,
        'production_batta': aggregats['batta'] or 0,
        'production_totale': total,
        'dechets_totaux': dechets,
        'taux_dechet': round(taux_dechet, 1),
    }

def get_recyclage_details_jour(date):
    """Détails recyclage du jour"""
    productions = ProductionRecyclage.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'moulinex_actifs': 0,
            'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
            'total_broyage': 0,
            'total_bache_noir': 0,
            'production_totale': 0,
            'taux_transformation': 0,
            'rendement': 0,
            'productivite_par_moulinex': 0,
        }
    
    aggregats = productions.aggregate(
        moulinex=Avg('nombre_moulinex'),
        broyage=Sum('production_broyage_kg'),
        bache=Sum('production_bache_noir_kg'),
        total=Sum('total_production_kg')
    )
    
    broyage = aggregats['broyage'] or 0
    bache = aggregats['bache'] or 0
    total = aggregats['total'] or 0
    moulinex_avg = aggregats['moulinex'] or 1
    
    taux_transformation = (bache / broyage * 100) if broyage > 0 else 0
    productivite = (total / moulinex_avg) if moulinex_avg > 0 else 0
    
    return {
        'moulinex_actifs': round(moulinex_avg, 0),
        'moulinex_totaux': Machine.objects.filter(section='recyclage').count(),
        'total_broyage': broyage,
        'total_bache_noir': bache,
        'production_totale': total,
        'taux_transformation': round(taux_transformation, 1),
        'rendement': round(taux_transformation, 1),
        'productivite_par_moulinex': round(productivite, 1),
        'temps_travail': 8,
    }

# ==========================================
# FONCTIONS CALCULS EN TEMPS RÉEL
# ==========================================

def calculate_extrusion_metrics(data):
    """Calculs extrusion"""
    matiere_premiere = float(data.get('matiere_premiere', 0))
    prod_finis = float(data.get('production_finis', 0))
    prod_semi_finis = float(data.get('production_semi_finis', 0))
    dechets = float(data.get('dechets', 0))
    nb_machines = int(data.get('nombre_machines', 1))
    
    total_production = prod_finis + prod_semi_finis
    rendement = (total_production / matiere_premiere * 100) if matiere_premiere > 0 else 0
    taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
    prod_par_machine = total_production / nb_machines if nb_machines > 0 else 0
    
    return {
        'total_production': round(total_production, 1),
        'rendement': round(rendement, 1),
        'taux_dechet': round(taux_dechet, 1),
        'production_par_machine': round(prod_par_machine, 1),
    }

def calculate_imprimerie_metrics(data):
    """Calculs imprimerie"""
    bobines_finies = float(data.get('bobines_finies', 0))
    bobines_semi_finies = float(data.get('bobines_semi_finies', 0))
    dechets = float(data.get('dechets', 0))
    
    total_production = bobines_finies + bobines_semi_finies
    taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
    
    return {
        'total_production': round(total_production, 1),
        'taux_dechet': round(taux_dechet, 1),
    }

def calculate_soudure_metrics(data):
    """Calculs soudure"""
    bobines_finies = float(data.get('bobines_finies', 0))
    bretelles = float(data.get('bretelles', 0))
    rema = float(data.get('rema', 0))
    batta = float(data.get('batta', 0))
    dechets = float(data.get('dechets', 0))
    
    total_specifique = bretelles + rema + batta
    total_production = bobines_finies + total_specifique
    taux_dechet = (dechets / (total_production + dechets) * 100) if (total_production + dechets) > 0 else 0
    
    return {
        'total_production': round(total_production, 1),
        'total_specifique': round(total_specifique, 1),
        'taux_dechet': round(taux_dechet, 1),
    }

def calculate_recyclage_metrics(data):
    """Calculs recyclage"""
    broyage = float(data.get('broyage', 0))
    bache_noir = float(data.get('bache_noir', 0))
    nb_moulinex = int(data.get('nombre_moulinex', 1))
    
    total_production = broyage + bache_noir
    prod_par_moulinex = total_production / nb_moulinex if nb_moulinex > 0 else 0
    taux_transformation = (bache_noir / broyage * 100) if broyage > 0 else 0
    
    return {
        'total_production': round(total_production, 1),
        'production_par_moulinex': round(prod_par_moulinex, 1),
        'taux_transformation': round(taux_transformation, 1),
    }

# ==========================================
# FONCTIONS DASHBOARD DIRECTION
# ==========================================

def get_ca_mensuel(debut, fin):
    """CA mensuel - À adapter selon votre modèle de pricing"""
    production_totale = get_production_totale_periode(debut, fin)
    prix_moyen_kg = Decimal('320')  # Prix moyen par kg - À paramétrer
    return production_totale * prix_moyen_kg

def get_production_totale_periode(debut, fin):
    """Production totale sur période"""
    total = Decimal('0')
    for model in [ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage]:
        total += model.objects.filter(
            date_production__gte=debut,
            date_production__lte=fin
        ).aggregate(Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')
    return total

def calculate_percentage_of_goal(actual, goal):
    """Calculer pourcentage d'objectif atteint"""
    if goal == 0:
        return 0
    return round((actual / goal) * 100, 1)

def get_efficacite_globale_periode(debut, fin):
    """Efficacité globale période"""
    efficacite = ProductionExtrusion.objects.filter(
        date_production__gte=debut,
        date_production__lte=fin
    ).aggregate(Avg('rendement_pourcentage'))['rendement_pourcentage__avg'] or Decimal('0')
    return round(efficacite, 1)

def get_cout_production_moyen(debut, fin):
    """Coût de production moyen - Estimation basée sur consommation"""
    matiere_premiere = ProductionExtrusion.objects.filter(
        date_production__gte=debut,
        date_production__lte=fin
    ).aggregate(Sum('matiere_premiere_kg'))['matiere_premiere_kg__sum'] or Decimal('0')
    
    production_totale = get_production_totale_periode(debut, fin)
    
    if production_totale == 0:
        return Decimal('0')
    
    cout_matiere_kg = Decimal('600')  # À paramétrer
    cout_total = matiere_premiere * cout_matiere_kg
    
    return round(cout_total / production_totale, 0)

def get_performances_sections(debut, fin):
    """Performance détaillée par section"""
    sections = []
    
    for section_name, model in [
        ('Extrusion', ProductionExtrusion),
        ('Imprimerie', ProductionImprimerie),
        ('Soudure', ProductionSoudure),
        ('Recyclage', ProductionRecyclage)
    ]:
        data = model.objects.filter(
            date_production__gte=debut,
            date_production__lte=fin
        ).aggregate(
            production=Sum('total_production_kg'),
            dechets=Sum('dechets_kg') if hasattr(model, 'dechets_kg') else None
        )
        
        production = data['production'] or 0
        dechets = data['dechets'] or 0
        
        sections.append({
            'nom': section_name,
            'production': production,
            'dechets': dechets,
            'performance': 85,  # Placeholder
            'rendement': 87,
            'cout': 850,
        })
    
    return sections

def get_production_par_section(debut, fin):
    """Production par section pour graphiques"""
    return [
        float(get_production_section_periode('extrusion', debut, fin)),
        float(get_production_section_periode('imprimerie', debut, fin)),
        float(get_production_section_periode('soudure', debut, fin)),
        float(get_production_section_periode('recyclage', debut, fin)),
    ]

def get_production_section_periode(section, debut, fin):
    """Production d'une section sur une période"""
    models_map = {
        'extrusion': ProductionExtrusion,
        'imprimerie': ProductionImprimerie,
        'soudure': ProductionSoudure,
        'recyclage': ProductionRecyclage,
    }
    
    model = models_map.get(section)
    if not model:
        return Decimal('0')
    
    return model.objects.filter(
        date_production__gte=debut,
        date_production__lte=fin
    ).aggregate(Sum('total_production_kg'))['total_production_kg__sum'] or Decimal('0')

# ==========================================
# FONCTIONS ANALYTICS
# ==========================================

def get_chart_data_for_dashboard():
    """Données pour graphiques Analytics"""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    # Simuler 30 jours de données
    days = []
    for i in range(30):
        day = debut_mois + timedelta(days=i)
        if day <= today:
            days.append(day.strftime('%d/%m'))
    
    return json.dumps({
        'months': days,
        'extrusion': [float(get_production_section_jour('extrusion', debut_mois + timedelta(days=i))) for i in range(len(days))],
        'soudure': [float(get_production_section_jour('soudure', debut_mois + timedelta(days=i))) for i in range(len(days))],
        'dechets': [float(get_dechets_totaux_jour(debut_mois + timedelta(days=i))) for i in range(len(days))],
        'bache_noir': [float(ProductionRecyclage.objects.filter(date_production=debut_mois + timedelta(days=i)).aggregate(Sum('production_bache_noir_kg'))['production_bache_noir_kg__sum'] or 0) for i in range(len(days))],
    })

def get_analytics_kpis():
    """KPIs pour Analytics"""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    production_mois = get_production_totale_periode(debut_mois, today)
    dechets_mois = sum([get_dechets_totaux_jour(debut_mois + timedelta(days=i)) for i in range((today - debut_mois).days + 1)])
    
    return {
        'production_totale_mois': production_mois,
        'croissance_production': 12.5,
        'taux_dechet_mois': round((dechets_mois / production_mois * 100) if production_mois > 0 else 0, 1),
        'reduction_dechets': 2.3,
        'efficacite_moyenne': get_efficacite_globale_periode(debut_mois, today),
        'amélioration_efficacite': 3.2,
        'taux_transformation': 78.5,
        'amélioration_transformation': 5.1,
    }

def get_analytics_table_data():
    """Données tableau Analytics"""
    today = timezone.now().date()
    debut_mois = today.replace(day=1)
    
    return {
        'extrusion': {
            'production': get_production_section_periode('extrusion', debut_mois, today),
            'dechets': ProductionExtrusion.objects.filter(date_production__gte=debut_mois, date_production__lte=today).aggregate(Sum('dechets_kg'))['dechets_kg__sum'] or 0,
            'taux_dechet': 2.8,
            'efficacite': 89.2,
        },
        'imprimerie': {
            'production': get_production_section_periode('imprimerie', debut_mois, today),
            'dechets': ProductionImprimerie.objects.filter(date_production__gte=debut_mois, date_production__lte=today).aggregate(Sum('dechets_kg'))['dechets_kg__sum'] or 0,
            'taux_dechet': 3.1,
            'efficacite': 91.5,
        },
        'soudure': {
            'production': get_production_section_periode('soudure', debut_mois, today),
            'dechets': ProductionSoudure.objects.filter(date_production__gte=debut_mois, date_production__lte=today).aggregate(Sum('dechets_kg'))['dechets_kg__sum'] or 0,
            'taux_dechet': 3.8,
            'efficacite': 85.3,
        },
        'recyclage': {
            'production': get_production_section_periode('recyclage', debut_mois, today),
            'taux_transformation': 78.2,
            'rendement': 82.5,
        },
    }

# ==========================================
# FONCTIONS UTILITAIRES DIVERSES
# ==========================================

def get_mois_disponibles():
    """Liste des mois disponibles"""
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    
    return [{'value': f'2025-{i:02d}', 'nom': mois_noms[i-1] + ' 2025', 'selected': i == timezone.now().month}
            for i in range(1, 13)]

def get_nom_mois(mois_num):
    """Nom du mois"""
    mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    return mois_noms[mois_num - 1] if 1 <= mois_num <= 12 else ''