"""
Fonctions utilitaires pour les vues SOFEM-CI - VERSION COMPLÈTE
"""
#P:\p_S_final\sofemci\sofemci\views\utils_views.py:
from django.db.models import Sum, Avg, Count, Q, F, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
import json

from ..models import (
    ProductionExtrusion,
    ProductionImprimerie,
    ProductionSoudure,
    ProductionRecyclage,
    Machine,
    Alerte,
    AlerteIA,
    CustomUser,
    ZoneExtrusion,
    Equipe,
    HistoriqueMachine
)

# ==========================================
# FONCTIONS DE PRODUCTION - JOUR
# ==========================================

def get_production_totale_jour(date=None):
    """Calcule la production totale pour un jour donné"""
    if date is None:
        date = timezone.now().date()
    
    # Production extrusion
    prod_extrusion = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    # Production imprimerie
    prod_imprimerie = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    # Production soudure
    prod_soudure = ProductionSoudure.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    # Production recyclage
    prod_recyclage = ProductionRecyclage.objects.filter(
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    return float(prod_extrusion + prod_imprimerie + prod_soudure + prod_recyclage)

def get_production_section_jour(section, date=None):
    """Calcule la production d'une section pour un jour donné"""
    if date is None:
        date = timezone.now().date()
    
    if section.upper() == 'EXTRUSION':
        prod = ProductionExtrusion.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    elif section.upper() == 'IMPRIMERIE':
        prod = ProductionImprimerie.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    elif section.upper() == 'SOUDURE':
        prod = ProductionSoudure.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    elif section.upper() == 'RECYCLAGE':
        prod = ProductionRecyclage.objects.filter(
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    else:
        prod = 0
    
    return float(prod)

def get_production_par_section_jour(date=None):
    """Retourne la production de toutes les sections pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    return {
        'extrusion': get_production_section_jour('EXTRUSION', date),
        'imprimerie': get_production_section_jour('IMPRIMERIE', date),
        'soudure': get_production_section_jour('SOUDURE', date),
        'recyclage': get_production_section_jour('RECYCLAGE', date),
    }

# ==========================================
# FONCTIONS DE PRODUCTION - PÉRIODE
# ==========================================

def get_production_periode(date_debut, date_fin):
    """Calcule la production totale pour une période"""
    
    prod_extrusion = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    prod_imprimerie = ProductionImprimerie.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    prod_soudure = ProductionSoudure.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    prod_recyclage = ProductionRecyclage.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    return {
        'extrusion': float(prod_extrusion),
        'imprimerie': float(prod_imprimerie),
        'soudure': float(prod_soudure),
        'recyclage': float(prod_recyclage),
        'total': float(prod_extrusion + prod_imprimerie + prod_soudure + prod_recyclage)
    }

def get_production_par_section(date_debut, date_fin):
    """Retourne la production détaillée par section"""
    return get_production_periode(date_debut, date_fin)

def get_production_section_periode(section, date_debut, date_fin):
    """Calcule la production d'une section pour une période"""
    
    if section.upper() == 'EXTRUSION':
        prod = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    elif section.upper() == 'IMPRIMERIE':
        prod = ProductionImprimerie.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    elif section.upper() == 'SOUDURE':
        prod = ProductionSoudure.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    elif section.upper() == 'RECYCLAGE':
        prod = ProductionRecyclage.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    else:
        prod = 0
    
    return float(prod)

# ==========================================
# FONCTIONS DE RENDEMENT ET QUALITÉ
# ==========================================

def get_rendement_moyen_periode(date_debut, date_fin):
    """Calcule le rendement moyen sur une période"""
    
    rendement_extrusion = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
    
    return float(rendement_extrusion)

def get_rendement_section_periode(section, date_debut, date_fin):
    """Calcule le rendement d'une section sur une période"""
    
    if section.upper() == 'EXTRUSION':
        rendement = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
    else:
        rendement = 0
    
    return float(rendement)

def get_taux_dechet_moyen(date_debut, date_fin):
    """Calcule le taux de déchet moyen sur une période"""
    
    # Extrusion
    extr = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
    
    # Imprimerie
    impr = ProductionImprimerie.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
    
    # Soudure
    soud = ProductionSoudure.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
    
    # Moyenne globale
    moyennes = [x for x in [extr, impr, soud] if x > 0]
    if moyennes:
        return float(sum(moyennes) / len(moyennes))
    return 0.0

def get_taux_dechet_section(section, date_debut, date_fin):
    """Calcule le taux de déchet d'une section"""
    
    if section.upper() == 'EXTRUSION':
        taux = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
    elif section.upper() == 'IMPRIMERIE':
        taux = ProductionImprimerie.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
    elif section.upper() == 'SOUDURE':
        taux = ProductionSoudure.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
    else:
        taux = 0
    
    return float(taux)

# ==========================================
# FONCTIONS DE PRODUCTION JOURNALIÈRE
# ==========================================

def get_production_journaliere_7j():
    """Retourne la production journalière des 7 derniers jours"""
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=7)
    
    productions = []
    current_date = date_debut
    
    while current_date <= date_fin:
        total = get_production_totale_jour(current_date)
        productions.append({
            'date': current_date.strftime('%d/%m'),
            'date_complete': current_date,
            'total': total
        })
        current_date += timedelta(days=1)
    
    return productions

def get_production_journaliere_30j():
    """Retourne la production journalière des 30 derniers jours"""
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=30)
    
    productions = []
    current_date = date_debut
    
    while current_date <= date_fin:
        total = get_production_totale_jour(current_date)
        productions.append({
            'date': current_date.strftime('%d/%m'),
            'date_complete': current_date,
            'total': total
        })
        current_date += timedelta(days=1)
    
    return productions

def get_production_hebdomadaire():
    """Retourne la production par semaine sur les 12 dernières semaines"""
    date_fin = timezone.now().date()
    
    productions = []
    
    for i in range(12):
        fin_semaine = date_fin - timedelta(weeks=i)
        debut_semaine = fin_semaine - timedelta(days=6)
        
        prod = get_production_periode(debut_semaine, fin_semaine)
        
        productions.insert(0, {
            'semaine': f"S{debut_semaine.isocalendar()[1]}",
            'debut': debut_semaine,
            'fin': fin_semaine,
            'total': prod['total']
        })
    
    return productions

def get_production_mensuelle():
    """Retourne la production par mois sur les 12 derniers mois"""
    date_fin = timezone.now().date()
    
    productions = []
    
    for i in range(12):
        # Calculer le premier jour du mois
        if date_fin.month - i <= 0:
            mois = 12 + (date_fin.month - i)
            annee = date_fin.year - 1
        else:
            mois = date_fin.month - i
            annee = date_fin.year
        
        debut_mois = date(annee, mois, 1)
        
        # Dernier jour du mois
        if mois == 12:
            fin_mois = date(annee + 1, 1, 1) - timedelta(days=1)
        else:
            fin_mois = date(annee, mois + 1, 1) - timedelta(days=1)
        
        prod = get_production_periode(debut_mois, fin_mois)
        
        productions.insert(0, {
            'mois': debut_mois.strftime('%B %Y'),
            'debut': debut_mois,
            'fin': fin_mois,
            'total': prod['total']
        })
    
    return productions

# ==========================================
# FONCTIONS DE MACHINES
# ==========================================

def get_nombre_machines_totales():
    """Retourne le nombre total de machines"""
    return Machine.objects.count()

def get_machines_actives():
    """Retourne le nombre de machines actives"""
    return Machine.objects.filter(etat='ACTIVE').count()

def get_machines_en_panne():
    """Retourne le nombre de machines en panne"""
    return Machine.objects.filter(etat='PANNE').count()

def get_machines_maintenance():
    """Retourne le nombre de machines en maintenance"""
    return Machine.objects.filter(etat='MAINTENANCE').count()

def get_machines_inactives():
    """Retourne le nombre de machines inactives"""
    return Machine.objects.filter(etat='INACTIVE').count()

def get_machines_hors_service():
    """Retourne le nombre de machines hors service"""
    return Machine.objects.filter(etat='HORS_SERVICE').count()

def get_machines_par_section():
    """Retourne le nombre de machines par section"""
    return Machine.objects.values('section').annotate(
        total=Count('id'),
        actives=Count('id', filter=Q(etat='ACTIVE')),
        en_panne=Count('id', filter=Q(etat='PANNE'))
    ).order_by('section')

def get_machines_par_etat():
    """Retourne le nombre de machines par état"""
    return Machine.objects.values('etat').annotate(
        total=Count('id')
    ).order_by('-total')

def get_taux_disponibilite_machines():
    """Calcule le taux de disponibilité des machines"""
    total = Machine.objects.count()
    if total == 0:
        return 0.0
    
    actives = Machine.objects.filter(etat='ACTIVE').count()
    return float((actives / total) * 100)

def get_score_sante_moyen():
    """Calcule le score de santé moyen des machines"""
    score = Machine.objects.filter(
        etat='ACTIVE'
    ).aggregate(avg=Avg('score_sante_global'))['avg'] or 0
    
    return float(score)

def get_score_sante_section(section):
    """Calcule le score de santé moyen d'une section"""
    score = Machine.objects.filter(
        section=section.upper(),
        etat='ACTIVE'
    ).aggregate(avg=Avg('score_sante_global'))['avg'] or 0
    
    return float(score)

def get_machines_a_risque(seuil=40):
    """Retourne les machines avec probabilité de panne élevée"""
    return Machine.objects.filter(
        Q(probabilite_panne_7_jours__gte=seuil) | Q(score_sante_global__lte=70)
    ).order_by('-probabilite_panne_7_jours')

def get_machines_critiques():
    """Retourne les machines en état critique"""
    return Machine.objects.filter(
        Q(probabilite_panne_7_jours__gte=70) | Q(score_sante_global__lte=50)
    ).order_by('-probabilite_panne_7_jours')

def get_machines_necessitant_maintenance():
    """Retourne les machines nécessitant une maintenance"""
    aujourdhui = timezone.now().date()
    return Machine.objects.filter(
        Q(prochaine_maintenance_prevue__lte=aujourdhui) |
        Q(prochaine_maintenance_prevue__isnull=True, derniere_maintenance__isnull=True)
    ).exclude(etat='MAINTENANCE')

def get_nombre_maintenances_prevues():
    """Retourne le nombre de maintenances prévues dans les 7 prochains jours"""
    aujourdhui = timezone.now().date()
    dans_7_jours = aujourdhui + timedelta(days=7)
    
    return Machine.objects.filter(
        prochaine_maintenance_prevue__range=[aujourdhui, dans_7_jours]
    ).count()

# ==========================================
# FONCTIONS D'ALERTES
# ==========================================

def get_nombre_alertes_actives():
    """Retourne le nombre d'alertes actives"""
    return Alerte.objects.filter(
        statut__in=['NOUVELLE', 'EN_COURS']
    ).count()

def get_nombre_alertes_nouvelles():
    """Retourne le nombre de nouvelles alertes"""
    return Alerte.objects.filter(statut='NOUVELLE').count()

def get_alertes_critiques():
    """Retourne les alertes critiques"""
    return Alerte.objects.filter(
        statut__in=['NOUVELLE', 'EN_COURS'],
        priorite__gte=4
    ).order_by('-priorite', '-date_creation')

def get_alertes_urgentes():
    """Retourne les alertes urgentes (priorité 5)"""
    return Alerte.objects.filter(
        statut__in=['NOUVELLE', 'EN_COURS'],
        priorite=5
    ).order_by('-date_creation')

def get_alertes_ia_actives():
    """Retourne les alertes IA actives"""
    return AlerteIA.objects.filter(
        statut='ACTIVE'
    ).count()

def get_alertes_ia_critiques():
    """Retourne les alertes IA critiques"""
    return AlerteIA.objects.filter(
        statut='ACTIVE',
        niveau='CRITIQUE'
    ).count()

def get_alertes_ia_haute():
    """Retourne les alertes IA de niveau haute"""
    return AlerteIA.objects.filter(
        statut='ACTIVE',
        niveau='HAUTE'
    ).count()

def get_alertes_par_section():
    """Retourne le nombre d'alertes par section"""
    return Alerte.objects.filter(
        statut__in=['NOUVELLE', 'EN_COURS']
    ).values('section').annotate(
        total=Count('id')
    ).order_by('-total')

def get_alertes_par_type():
    """Retourne le nombre d'alertes par type"""
    return Alerte.objects.filter(
        statut__in=['NOUVELLE', 'EN_COURS']
    ).values('type_alerte').annotate(
        total=Count('id')
    ).order_by('-total')

def get_alertes_en_retard():
    """Retourne les alertes en retard"""
    alertes = Alerte.objects.filter(
        statut__in=['NOUVELLE', 'EN_COURS']
    )
    
    alertes_retard = []
    for alerte in alertes:
        delai_max = alerte.date_creation + timedelta(hours=alerte.delai_resolution)
        if timezone.now() > delai_max:
            alertes_retard.append(alerte)
    
    return alertes_retard

# ==========================================
# FONCTIONS DE PERSONNEL
# ==========================================

def get_nombre_employes_actifs():
    """Retourne le nombre d'employés actifs"""
    return CustomUser.objects.filter(
        est_actif=True
    ).count()

def get_nombre_employes_total():
    """Retourne le nombre total d'employés"""
    return CustomUser.objects.count()

def get_employes_par_role():
    """Retourne le nombre d'employés par rôle"""
    return CustomUser.objects.filter(
        est_actif=True
    ).values('role').annotate(
        total=Count('id')
    ).order_by('-total')

def get_employes_par_service():
    """Retourne le nombre d'employés par service"""
    return CustomUser.objects.filter(
        est_actif=True
    ).values('service').annotate(
        total=Count('id')
    ).order_by('-total')

def get_equipes_actives():
    """Retourne les équipes actives"""
    return Equipe.objects.filter(est_active=True).count()

def get_nombre_equipes():
    """Retourne le nombre total d'équipes"""
    return Equipe.objects.count()

# ==========================================
# FONCTIONS DE ZONES
# ==========================================

def get_zones_actives():
    """Retourne le nombre de zones actives"""
    return ZoneExtrusion.objects.filter(active=True).count()

def get_nombre_zones():
    """Retourne le nombre total de zones"""
    return ZoneExtrusion.objects.count()

def get_production_par_zone(date_debut, date_fin):
    """Retourne la production par zone"""
    return ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).values('zone__numero', 'zone__nom').annotate(
        total=Sum('total_production_kg')
    ).order_by('-total')

def get_top_zones_production(limit=5):
    """Retourne les zones les plus productives"""
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=30)
    
    return ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).values('zone__numero', 'zone__nom').annotate(
        total=Sum('total_production_kg')
    ).order_by('-total')[:limit]

# ==========================================
# FONCTIONS DE STATISTIQUES AVANCÉES
# ==========================================

def get_statistiques_aujourdhui():
    """Retourne les statistiques du jour"""
    aujourd_hui = timezone.now().date()
    
    return {
        'date': aujourd_hui,
        'production_totale': get_production_totale_jour(aujourd_hui),
        'production_par_section': get_production_par_section_jour(aujourd_hui),
        'machines_actives': get_machines_actives(),
        'alertes_actives': get_nombre_alertes_actives(),
    }

def get_statistiques_hebdomadaires():
    """Retourne les statistiques de la semaine"""
    aujourd_hui = timezone.now().date()
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    fin_semaine = debut_semaine + timedelta(days=6)
    
    production = get_production_periode(debut_semaine, fin_semaine)
    
    return {
        'debut': debut_semaine,
        'fin': fin_semaine,
        'production_totale': production['total'],
        'production_par_section': production,
        'rendement_moyen': get_rendement_moyen_periode(debut_semaine, fin_semaine),
        'taux_dechet': get_taux_dechet_moyen(debut_semaine, fin_semaine)
    }

def get_statistiques_mensuelles():
    """Retourne les statistiques du mois"""
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    # Dernier jour du mois
    if aujourd_hui.month == 12:
        fin_mois = aujourd_hui.replace(year=aujourd_hui.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        fin_mois = aujourd_hui.replace(month=aujourd_hui.month + 1, day=1) - timedelta(days=1)
    
    production = get_production_periode(debut_mois, fin_mois)
    
    return {
        'debut': debut_mois,
        'fin': fin_mois,
        'production_totale': production['total'],
        'production_par_section': production,
        'rendement_moyen': get_rendement_moyen_periode(debut_mois, fin_mois),
        'taux_dechet': get_taux_dechet_moyen(debut_mois, fin_mois)
    }

def get_statistiques_annuelles():
    """Retourne les statistiques de l'année"""
    aujourd_hui = timezone.now().date()
    debut_annee = aujourd_hui.replace(month=1, day=1)
    
    production = get_production_periode(debut_annee, aujourd_hui)
    
    return {
        'debut': debut_annee,
        'fin': aujourd_hui,
        'production_totale': production['total'],
        'production_par_section': production,
        'rendement_moyen': get_rendement_moyen_periode(debut_annee, aujourd_hui),
        'taux_dechet': get_taux_dechet_moyen(debut_annee, aujourd_hui)
    }

def get_comparaison_periodes(date_debut_1, date_fin_1, date_debut_2, date_fin_2):
    """Compare deux périodes"""
    
    periode_1 = get_production_periode(date_debut_1, date_fin_1)
    periode_2 = get_production_periode(date_debut_2, date_fin_2)
    
    # Calcul de l'évolution en pourcentage
    if periode_2['total'] > 0:
        evolution = ((periode_1['total'] - periode_2['total']) / periode_2['total']) * 100
    else:
        evolution = 0
    
    return {
        'periode_1': periode_1,
        'periode_2': periode_2,
        'evolution_pourcent': float(evolution)
    }

def get_evolution_production(jours=30):
    """Calcule l'évolution de la production"""
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=jours)
    
    prod_actuelle = get_production_periode(date_debut, date_fin)
    
    # Période précédente
    date_fin_precedente = date_debut - timedelta(days=1)
    date_debut_precedente = date_fin_precedente - timedelta(days=jours)
    
    prod_precedente = get_production_periode(date_debut_precedente, date_fin_precedente)
    
    if prod_precedente['total'] > 0:
        evolution = ((prod_actuelle['total'] - prod_precedente['total']) / prod_precedente['total']) * 100
    else:
        evolution = 0
    
    return {
        'production_actuelle': prod_actuelle['total'],
        'production_precedente': prod_precedente['total'],
        'evolution_pourcent': float(evolution),
        'est_en_hausse': evolution > 0
    }

# ==========================================
# FONCTIONS KPI DASHBOARD
# ==========================================

def get_kpi_dashboard():
    """Retourne tous les KPI pour le dashboard"""
    aujourd_hui = timezone.now().date()
    hier = aujourd_hui - timedelta(days=1)
    debut_mois = aujourd_hui.replace(day=1)
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    
    # Production
    prod_aujourdhui = get_production_totale_jour(aujourd_hui)
    prod_hier = get_production_totale_jour(hier)
    prod_mois = get_production_periode(debut_mois, aujourd_hui)
    prod_semaine = get_production_periode(debut_semaine, aujourd_hui)
    
    # Évolution
    if prod_hier > 0:
        evolution_jour = ((prod_aujourdhui - prod_hier) / prod_hier) * 100
    else:
        evolution_jour = 0
    
    return {
        # Production
        'production_aujourdhui': prod_aujourdhui,
        'production_hier': prod_hier,
        'production_semaine': prod_semaine['total'],
        'production_mois': prod_mois['total'],
        'evolution_jour': float(evolution_jour),
        
        # Machines
        'machines_totales': get_nombre_machines_totales(),
        'machines_actives': get_machines_actives(),
        'machines_en_panne': get_machines_en_panne(),
        'machines_maintenance': get_machines_maintenance(),
        'taux_disponibilite': get_taux_disponibilite_machines(),
        
        # Alertes
        'alertes_actives': get_nombre_alertes_actives(),
        'alertes_nouvelles': get_nombre_alertes_nouvelles(),
        'alertes_critiques': get_alertes_critiques().count(),
        'alertes_ia': get_alertes_ia_actives(),
        'alertes_ia_critiques': get_alertes_ia_critiques(),
        
        # Personnel
        'employes_actifs': get_nombre_employes_actifs(),
        'equipes_actives': get_equipes_actives(),
        
        # Qualité
        'score_sante_moyen': get_score_sante_moyen(),
        'rendement_moyen': get_rendement_moyen_periode(debut_mois, aujourd_hui),
        'taux_dechet': get_taux_dechet_moyen(debut_mois, aujourd_hui),
        
        # Maintenance
        'maintenances_prevues': get_nombre_maintenances_prevues(),
        'machines_a_risque': get_machines_a_risque().count(),
    }

# ==========================================
# FONCTIONS DE GRAPHIQUES
# ==========================================

def get_donnees_graphique_production(jours=30):
    """Retourne les données pour le graphique de production"""
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=jours)
    
    donnees = {
        'dates': [],
        'extrusion': [],
        'imprimerie': [],
        'soudure': [],
        'recyclage': [],
        'total': []
    }
    
    current_date = date_debut
    while current_date <= date_fin:
        # Extrusion
        extr = ProductionExtrusion.objects.filter(
            date_production=current_date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
        
        # Imprimerie
        impr = ProductionImprimerie.objects.filter(
            date_production=current_date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
        
        # Soudure
        soud = ProductionSoudure.objects.filter(
            date_production=current_date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
        
        # Recyclage
        recy = ProductionRecyclage.objects.filter(
            date_production=current_date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
        
        donnees['dates'].append(current_date.strftime('%d/%m'))
        donnees['extrusion'].append(float(extr))
        donnees['imprimerie'].append(float(impr))
        donnees['soudure'].append(float(soud))
        donnees['recyclage'].append(float(recy))
        donnees['total'].append(float(extr + impr + soud + recy))
        
        current_date += timedelta(days=1)
    
    return donnees

def get_donnees_graphique_rendement(jours=30):
    """Retourne les données pour le graphique de rendement"""
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=jours)
    
    donnees = {
        'dates': [],
        'rendement': [],
        'taux_dechet': []
    }
    
    current_date = date_debut
    while current_date <= date_fin:
        rendement = ProductionExtrusion.objects.filter(
            date_production=current_date
        ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
        
        dechet = ProductionExtrusion.objects.filter(
            date_production=current_date
        ).aggregate(avg=Avg('taux_dechet_pourcentage'))['avg'] or 0
        
        donnees['dates'].append(current_date.strftime('%d/%m'))
        donnees['rendement'].append(float(rendement))
        donnees['taux_dechet'].append(float(dechet))
        
        current_date += timedelta(days=1)
    
    return donnees

def get_donnees_graphique_machines():
    """Retourne les données pour le graphique de répartition des machines"""
    etats = get_machines_par_etat()
    
    return {
        'labels': [e['etat'] for e in etats],
        'valeurs': [e['total'] for e in etats]
    }

def get_donnees_graphique_alertes():
    """Retourne les données pour le graphique des alertes"""
    types = get_alertes_par_type()
    
    return {
        'labels': [t['type_alerte'] for t in types],
        'valeurs': [t['total'] for t in types]
    }

# ==========================================
# FONCTIONS D'EXPORT
# ==========================================

def preparer_donnees_export_production(date_debut, date_fin):
    """Prépare les données pour l'export Excel"""
    
    # Extrusion
    extrusion = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).values(
        'date_production',
        'zone__nom',
        'equipe__nom',
        'total_production_kg',
        'rendement_pourcentage',
        'taux_dechet_pourcentage'
    )
    
    return {
        'extrusion': list(extrusion),
    }

# ==========================================
# FONCTIONS DE VALIDATION
# ==========================================

def valider_production(production_id, section):
    """Valide une entrée de production"""
    if section.upper() == 'EXTRUSION':
        prod = ProductionExtrusion.objects.get(id=production_id)
    elif section.upper() == 'IMPRIMERIE':
        prod = ProductionImprimerie.objects.get(id=production_id)
    elif section.upper() == 'SOUDURE':
        prod = ProductionSoudure.objects.get(id=production_id)
    elif section.upper() == 'RECYCLAGE':
        prod = ProductionRecyclage.objects.get(id=production_id)
    else:
        return False
    
    prod.valide = True
    prod.save()
    return True

# ==========================================
# FONCTIONS UTILITAIRES DIVERSES
# ==========================================

def calculer_objectif_mensuel():
    """Calcule l'objectif de production mensuel"""
    # Objectif par défaut: 100 000 kg/mois
    return 100000.0

def calculer_pourcentage_objectif(production, objectif):
    """Calcule le pourcentage de l'objectif atteint"""
    if objectif <= 0:
        return 0.0
    return float((production / objectif) * 100)

def get_jours_travailles_mois():
    """Retourne le nombre de jours travaillés dans le mois"""
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    # Compte les jours où il y a eu de la production
    jours = ProductionExtrusion.objects.filter(
        date_production__range=[debut_mois, aujourd_hui]
    ).values('date_production').distinct().count()
    
    return jours

def get_moyenne_production_jour_mois():
    """Calcule la moyenne de production par jour pour le mois"""
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    prod_mois = get_production_periode(debut_mois, aujourd_hui)
    jours = get_jours_travailles_mois()
    
    if jours > 0:
        return float(prod_mois['total'] / jours)
    return 0.0

# ==========================================
# FONCTIONS DE DÉCHETS
# ==========================================

def get_dechets_totaux_jour(date=None):
    """Calcule le total des déchets pour un jour donné"""
    if date is None:
        date = timezone.now().date()
    
    # Déchets extrusion
    dechets_extrusion = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('dechets'))['total'] or 0
    
    # Déchets imprimerie
    dechets_imprimerie = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(total=Sum('dechets'))['total'] or 0
    
    # Déchets soudure
    dechets_soudure = ProductionSoudure.objects.filter(
        date_production=date
    ).aggregate(total=Sum('dechets'))['total'] or 0
    
    return float(dechets_extrusion + dechets_imprimerie + dechets_soudure)

def get_dechets_periode(date_debut, date_fin):
    """Calcule le total des déchets pour une période"""
    
    dechets_extrusion = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('dechets'))['total'] or 0
    
    dechets_imprimerie = ProductionImprimerie.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('dechets'))['total'] or 0
    
    dechets_soudure = ProductionSoudure.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('dechets'))['total'] or 0
    
    return {
        'extrusion': float(dechets_extrusion),
        'imprimerie': float(dechets_imprimerie),
        'soudure': float(dechets_soudure),
        'total': float(dechets_extrusion + dechets_imprimerie + dechets_soudure)
    }

def get_dechets_section_jour(section, date=None):
    """Calcule les déchets d'une section pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    if section.upper() == 'EXTRUSION':
        dechets = ProductionExtrusion.objects.filter(
            date_production=date
        ).aggregate(total=Sum('dechets'))['total'] or 0
    elif section.upper() == 'IMPRIMERIE':
        dechets = ProductionImprimerie.objects.filter(
            date_production=date
        ).aggregate(total=Sum('dechets'))['total'] or 0
    elif section.upper() == 'SOUDURE':
        dechets = ProductionSoudure.objects.filter(
            date_production=date
        ).aggregate(total=Sum('dechets'))['total'] or 0
    else:
        dechets = 0
    
    return float(dechets)

def get_dechets_section_periode(section, date_debut, date_fin):
    """Calcule les déchets d'une section pour une période"""
    
    if section.upper() == 'EXTRUSION':
        dechets = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('dechets'))['total'] or 0
    elif section.upper() == 'IMPRIMERIE':
        dechets = ProductionImprimerie.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('dechets'))['total'] or 0
    elif section.upper() == 'SOUDURE':
        dechets = ProductionSoudure.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('dechets'))['total'] or 0
    else:
        dechets = 0
    
    return float(dechets)

# ==========================================
# FONCTIONS DE MATIÈRE PREMIÈRE
# ==========================================

def get_matiere_premiere_jour(date=None):
    """Calcule le total de matière première utilisée pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    matiere = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('matiere_premiere_kg'))['total'] or 0
    
    return float(matiere)

def get_matiere_premiere_periode(date_debut, date_fin):
    """Calcule le total de matière première pour une période"""
    
    matiere = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('matiere_premiere_kg'))['total'] or 0
    
    return float(matiere)

def get_consommation_matiere_section(section, date_debut, date_fin):
    """Calcule la consommation de matière première d'une section"""
    
    if section.upper() == 'EXTRUSION':
        matiere = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(total=Sum('matiere_premiere_kg'))['total'] or 0
    else:
        matiere = 0
    
    return float(matiere)

# ==========================================
# FONCTIONS DE MACHINES ACTIVES
# ==========================================

def get_machines_actives_section(section):
    """Retourne le nombre de machines actives d'une section"""
    return Machine.objects.filter(
        section=section.upper(),
        etat='ACTIVE'
    ).count()

def get_machines_section(section):
    """Retourne toutes les machines d'une section"""
    return Machine.objects.filter(section=section.upper())

def get_nombre_machines_section(section):
    """Retourne le nombre total de machines d'une section"""
    return Machine.objects.filter(section=section.upper()).count()

# ==========================================
# FONCTIONS DE PRODUCTION SPÉCIFIQUES
# ==========================================

def get_production_bobines_jour(date=None):
    """Calcule la production de bobines pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    # Extrusion
    bobines_extr = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('nombre_bobines_kg'))['total'] or 0
    
    # Imprimerie
    bobines_impr = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(
        finies=Sum('production_bobines_finies_kg'),
        semi=Sum('production_bobines_semi_finies_kg')
    )
    
    total_impr = (bobines_impr['finies'] or 0) + (bobines_impr['semi'] or 0)
    
    # Soudure
    bobines_soud = ProductionSoudure.objects.filter(
        date_production=date
    ).aggregate(total=Sum('production_bobines_finies_kg'))['total'] or 0
    
    return float(bobines_extr + total_impr + bobines_soud)

def get_production_finis_jour(date=None):
    """Calcule la production de produits finis pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    finis_extr = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('production_finis_kg'))['total'] or 0
    
    finis_impr = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(total=Sum('production_bobines_finies_kg'))['total'] or 0
    
    finis_soud = ProductionSoudure.objects.filter(
        date_production=date
    ).aggregate(total=Sum('production_bobines_finies_kg'))['total'] or 0
    
    return float(finis_extr + finis_impr + finis_soud)

def get_production_semi_finis_jour(date=None):
    """Calcule la production de produits semi-finis pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    semi_extr = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(total=Sum('production_semi_finis_kg'))['total'] or 0
    
    semi_impr = ProductionImprimerie.objects.filter(
        date_production=date
    ).aggregate(total=Sum('production_bobines_semi_finies_kg'))['total'] or 0
    
    return float(semi_extr + semi_impr)

# ==========================================
# FONCTIONS D'ÉQUIPES
# ==========================================

def get_equipes():
    """Retourne toutes les équipes"""
    return Equipe.objects.all()

def get_equipe_par_nom(nom):
    """Retourne une équipe par son nom"""
    return Equipe.objects.filter(nom=nom).first()

def get_production_equipe_jour(equipe_id, date=None):
    """Calcule la production d'une équipe pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    prod_extr = ProductionExtrusion.objects.filter(
        equipe_id=equipe_id,
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    prod_recyc = ProductionRecyclage.objects.filter(
        equipe_id=equipe_id,
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    return float(prod_extr + prod_recyc)

def get_performance_equipe(equipe_id, date_debut, date_fin):
    """Calcule la performance d'une équipe sur une période"""
    
    prod_extr = ProductionExtrusion.objects.filter(
        equipe_id=equipe_id,
        date_production__range=[date_debut, date_fin]
    ).aggregate(
        total=Sum('total_production_kg'),
        rendement=Avg('rendement_pourcentage')
    )
    
    prod_recyc = ProductionRecyclage.objects.filter(
        equipe_id=equipe_id,
        date_production__range=[date_debut, date_fin]
    ).aggregate(
        total=Sum('total_production_kg')
    )
    
    return {
        'production_totale': float((prod_extr['total'] or 0) + (prod_recyc['total'] or 0)),
        'rendement_moyen': float(prod_extr['rendement'] or 0)
    }

# ==========================================
# FONCTIONS DE ZONES
# ==========================================

def get_production_zone_jour(zone_id, date=None):
    """Calcule la production d'une zone pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    prod = ProductionExtrusion.objects.filter(
        zone_id=zone_id,
        date_production=date
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    return float(prod)

def get_production_zone_periode(zone_id, date_debut, date_fin):
    """Calcule la production d'une zone pour une période"""
    
    prod = ProductionExtrusion.objects.filter(
        zone_id=zone_id,
        date_production__range=[date_debut, date_fin]
    ).aggregate(
        total=Sum('total_production_kg'),
        rendement=Avg('rendement_pourcentage')
    )
    
    return {
        'production_totale': float(prod['total'] or 0),
        'rendement_moyen': float(prod['rendement'] or 0)
    }

def get_zones():
    """Retourne toutes les zones"""
    return ZoneExtrusion.objects.all()

def get_zone_par_numero(numero):
    """Retourne une zone par son numéro"""
    return ZoneExtrusion.objects.filter(numero=numero).first()

# ==========================================
# FONCTIONS DE TEMPS DE PRODUCTION
# ==========================================

def get_temps_production_jour(date=None):
    """Calcule le temps total de production pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    productions = ProductionExtrusion.objects.filter(date_production=date)
    
    temps_total = 0
    for prod in productions:
        temps_total += prod.duree_production()
    
    return float(temps_total)

def get_productivite_horaire_jour(date=None):
    """Calcule la productivité horaire pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    production = get_production_totale_jour(date)
    temps = get_temps_production_jour(date)
    
    if temps > 0:
        return float(production / temps)
    return 0.0

def get_productivite_horaire_periode(date_debut, date_fin):
    """Calcule la productivité horaire moyenne pour une période"""
    
    productions = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    )
    
    production_totale = 0
    temps_total = 0
    
    for prod in productions:
        production_totale += float(prod.total_production_kg)
        temps_total += prod.duree_production()
    
    if temps_total > 0:
        return float(production_totale / temps_total)
    return 0.0

# ==========================================
# FONCTIONS DE VALIDATION ET STATUT
# ==========================================

def get_nombre_productions_validees(date_debut, date_fin):
    """Retourne le nombre de productions validées"""
    
    extr = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=True
    ).count()
    
    impr = ProductionImprimerie.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=True
    ).count()
    
    soud = ProductionSoudure.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=True
    ).count()
    
    recyc = ProductionRecyclage.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=True
    ).count()
    
    return extr + impr + soud + recyc

def get_nombre_productions_en_attente(date_debut, date_fin):
    """Retourne le nombre de productions en attente de validation"""
    
    extr = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=False
    ).count()
    
    impr = ProductionImprimerie.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=False
    ).count()
    
    soud = ProductionSoudure.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=False
    ).count()
    
    recyc = ProductionRecyclage.objects.filter(
        date_production__range=[date_debut, date_fin],
        valide=False
    ).count()
    
    return extr + impr + soud + recyc

# ==========================================
# FONCTIONS D'HISTORIQUE
# ==========================================

def get_historique_machine(machine_id, limit=20):
    """Retourne l'historique d'une machine"""
    return HistoriqueMachine.objects.filter(
        machine_id=machine_id
    ).order_by('-date_evenement')[:limit]

def get_nombre_pannes_periode(date_debut, date_fin):
    """Retourne le nombre de pannes sur une période"""
    return HistoriqueMachine.objects.filter(
        type_evenement='PANNE',
        date_evenement__range=[date_debut, date_fin]
    ).count()

def get_nombre_maintenances_periode(date_debut, date_fin):
    """Retourne le nombre de maintenances sur une période"""
    return HistoriqueMachine.objects.filter(
        type_evenement='MAINTENANCE',
        date_evenement__range=[date_debut, date_fin]
    ).count()

def get_cout_total_maintenance(date_debut, date_fin):
    """Calcule le coût total des maintenances"""
    cout = HistoriqueMachine.objects.filter(
        type_evenement='MAINTENANCE',
        date_evenement__range=[date_debut, date_fin]
    ).aggregate(total=Sum('cout_intervention'))['total'] or 0
    
    return float(cout)

# ==========================================
# FONCTIONS SUPPLÉMENTAIRES
# ==========================================

def get_taux_utilisation_machines(date_debut, date_fin):
    """Calcule le taux d'utilisation des machines"""
    total_machines = get_nombre_machines_totales()
    if total_machines == 0:
        return 0.0
    
    # Calculer le nombre moyen de machines actives par jour
    jours = (date_fin - date_debut).days + 1
    total_actives = 0
    
    current_date = date_debut
    while current_date <= date_fin:
        # Compter les machines actives ce jour
        prod = ProductionExtrusion.objects.filter(
            date_production=current_date
        ).aggregate(machines=Sum('nombre_machines_actives'))['machines'] or 0
        
        total_actives += prod
        current_date += timedelta(days=1)
    
    if jours > 0:
        moyenne_actives = total_actives / jours
        return float((moyenne_actives / total_machines) * 100)
    
    return 0.0

# ==========================================
# FONCTIONS D'EFFICACITÉ ET PERFORMANCE
# ==========================================

def get_efficacite_moyenne_jour(date=None):
    """Calcule l'efficacité moyenne pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    # L'efficacité est basée sur le rendement
    efficacite = ProductionExtrusion.objects.filter(
        date_production=date
    ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
    
    return float(efficacite)

def get_efficacite_periode(date_debut, date_fin):
    """Calcule l'efficacité moyenne pour une période"""
    
    efficacite = ProductionExtrusion.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
    
    return float(efficacite)

def get_efficacite_section(section, date_debut, date_fin):
    """Calcule l'efficacité d'une section"""
    
    if section.upper() == 'EXTRUSION':
        efficacite = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
    else:
        # Pour les autres sections, utiliser un calcul basé sur production/objectif
        efficacite = 0
    
    return float(efficacite)

def get_taux_reussite_production(date_debut, date_fin):
    """Calcule le taux de réussite de la production (validées vs total)"""
    
    total = (
        ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).count() +
        ProductionImprimerie.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).count() +
        ProductionSoudure.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).count() +
        ProductionRecyclage.objects.filter(
            date_production__range=[date_debut, date_fin]
        ).count()
    )
    
    if total == 0:
        return 0.0
    
    validees = get_nombre_productions_validees(date_debut, date_fin)
    
    return float((validees / total) * 100)

def get_performance_globale():
    """Calcule la performance globale du système"""
    
    # Score basé sur plusieurs facteurs
    disponibilite = get_taux_disponibilite_machines()
    sante = get_score_sante_moyen()
    
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    rendement = get_rendement_moyen_periode(debut_mois, aujourd_hui)
    
    # Moyenne pondérée
    performance = (disponibilite * 0.3 + sante * 0.3 + rendement * 0.4)
    
    return float(performance)

def get_indice_qualite(date_debut, date_fin):
    """Calcule un indice de qualité basé sur le taux de déchet"""
    
    taux_dechet = get_taux_dechet_moyen(date_debut, date_fin)
    
    # Indice de qualité = 100 - taux_dechet
    # Plus le taux de déchet est faible, meilleure est la qualité
    indice = max(0, 100 - taux_dechet)
    
    return float(indice)

# ==========================================
# FONCTIONS DE CAPACITÉ ET CHARGE
# ==========================================

def get_capacite_totale_machines():
    """Calcule la capacité totale horaire de toutes les machines"""
    
    capacite = Machine.objects.filter(
        etat='ACTIVE'
    ).aggregate(total=Sum('capacite_horaire'))['total'] or 0
    
    return float(capacite)

def get_capacite_section(section):
    """Calcule la capacité totale d'une section"""
    
    capacite = Machine.objects.filter(
        section=section.upper(),
        etat='ACTIVE'
    ).aggregate(total=Sum('capacite_horaire'))['total'] or 0
    
    return float(capacite)

def get_taux_charge_machines(date_debut, date_fin):
    """Calcule le taux de charge des machines"""
    
    capacite = get_capacite_totale_machines()
    if capacite == 0:
        return 0.0
    
    # Production réelle
    production = get_production_periode(date_debut, date_fin)
    jours = (date_fin - date_debut).days + 1
    
    # Heures de travail (8h par jour par exemple)
    heures_travail = jours * 8
    
    # Capacité théorique
    capacite_theorique = capacite * heures_travail
    
    if capacite_theorique > 0:
        taux_charge = (production['total'] / capacite_theorique) * 100
        return float(min(taux_charge, 100.0))
    
    return 0.0

def get_capacite_utilisee_pourcentage(date=None):
    """Calcule le pourcentage de capacité utilisée pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    capacite = get_capacite_totale_machines()
    if capacite == 0:
        return 0.0
    
    production = get_production_totale_jour(date)
    
    # Supposons 8h de travail par jour
    capacite_jour = capacite * 8
    
    if capacite_jour > 0:
        utilisation = (production / capacite_jour) * 100
        return float(min(utilisation, 100.0))
    
    return 0.0

# ==========================================
# FONCTIONS DE COÛTS ET ÉCONOMIE
# ==========================================

def get_cout_production_jour(date=None):
    """Estime le coût de production pour un jour (simplifié)"""
    if date is None:
        date = timezone.now().date()
    
    # Coût basé sur la matière première (hypothèse: 1000 FCFA/kg)
    matiere = get_matiere_premiere_jour(date)
    cout_matiere = matiere * 1000
    
    # Coût machines (maintenance, etc.)
    maintenances = HistoriqueMachine.objects.filter(
        date_evenement__date=date,
        type_evenement='MAINTENANCE'
    ).aggregate(total=Sum('cout_intervention'))['total'] or 0
    
    return float(cout_matiere + maintenances)

def get_cout_production_periode(date_debut, date_fin):
    """Estime le coût de production pour une période"""
    
    matiere = get_matiere_premiere_periode(date_debut, date_fin)
    cout_matiere = matiere * 1000
    
    maintenances = HistoriqueMachine.objects.filter(
        date_evenement__range=[date_debut, date_fin],
        type_evenement='MAINTENANCE'
    ).aggregate(total=Sum('cout_intervention'))['total'] or 0
    
    pannes = HistoriqueMachine.objects.filter(
        date_evenement__range=[date_debut, date_fin],
        type_evenement='PANNE'
    ).aggregate(total=Sum('cout_intervention'))['total'] or 0
    
    return float(cout_matiere + maintenances + pannes)

def get_economie_recyclage(date_debut, date_fin):
    """Calcule l'économie réalisée grâce au recyclage"""
    
    prod_recyclage = ProductionRecyclage.objects.filter(
        date_production__range=[date_debut, date_fin]
    ).aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    # Hypothèse: économie de 500 FCFA par kg recyclé
    economie = prod_recyclage * 500
    
    return float(economie)

# ==========================================
# FONCTIONS DE TEMPS D'ARRÊT
# ==========================================

def get_temps_arret_jour(date=None):
    """Calcule le temps d'arrêt total pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    arrets = HistoriqueMachine.objects.filter(
        date_evenement__date=date,
        type_evenement__in=['PANNE', 'MAINTENANCE']
    ).aggregate(total=Sum('duree_intervention'))['total'] or 0
    
    return float(arrets)

def get_temps_arret_periode(date_debut, date_fin):
    """Calcule le temps d'arrêt total pour une période"""
    
    arrets = HistoriqueMachine.objects.filter(
        date_evenement__range=[date_debut, date_fin],
        type_evenement__in=['PANNE', 'MAINTENANCE']
    ).aggregate(total=Sum('duree_intervention'))['total'] or 0
    
    return float(arrets)

def get_taux_disponibilite_periode(date_debut, date_fin):
    """Calcule le taux de disponibilité sur une période"""
    
    jours = (date_fin - date_debut).days + 1
    machines_totales = get_nombre_machines_totales()
    
    if machines_totales == 0:
        return 0.0
    
    # Heures totales possibles (24h * jours * machines)
    heures_totales = 24 * jours * machines_totales
    
    # Heures d'arrêt
    heures_arret = get_temps_arret_periode(date_debut, date_fin)
    
    # Disponibilité
    if heures_totales > 0:
        disponibilite = ((heures_totales - heures_arret) / heures_totales) * 100
        return float(max(0, disponibilite))
    
    return 0.0

def get_mtbf():
    """Calcule le MTBF (Mean Time Between Failures) - Temps moyen entre pannes"""
    
    # Sur les 6 derniers mois
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=180)
    
    nombre_pannes = get_nombre_pannes_periode(date_debut, date_fin)
    
    if nombre_pannes == 0:
        return 0.0
    
    # Temps total en heures
    temps_total = 180 * 24
    
    mtbf = temps_total / nombre_pannes
    
    return float(mtbf)

def get_mttr():
    """Calcule le MTTR (Mean Time To Repair) - Temps moyen de réparation"""
    
    # Sur les 6 derniers mois
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=180)
    
    duree_moyenne = HistoriqueMachine.objects.filter(
        date_evenement__range=[date_debut, date_fin],
        type_evenement='REPARATION'
    ).aggregate(avg=Avg('duree_intervention'))['avg'] or 0
    
    return float(duree_moyenne)

# ==========================================
# FONCTIONS DE PRÉVISIONS
# ==========================================

def prevoir_production_jour():
    """Prévoit la production du jour basée sur la moyenne des 7 derniers jours"""
    
    date_fin = timezone.now().date() - timedelta(days=1)
    date_debut = date_fin - timedelta(days=7)
    
    productions = []
    current_date = date_debut
    
    while current_date <= date_fin:
        prod = get_production_totale_jour(current_date)
        productions.append(prod)
        current_date += timedelta(days=1)
    
    if productions:
        moyenne = sum(productions) / len(productions)
        return float(moyenne)
    
    return 0.0

def prevoir_production_mois():
    """Prévoit la production du mois basée sur les données actuelles"""
    
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    # Production actuelle du mois
    prod_actuelle = get_production_periode(debut_mois, aujourd_hui)
    
    # Jours écoulés
    jours_ecoules = (aujourd_hui - debut_mois).days + 1
    
    # Jours dans le mois
    if aujourd_hui.month == 12:
        jours_total = 31
    else:
        prochain_mois = aujourd_hui.replace(month=aujourd_hui.month + 1, day=1)
        jours_total = (prochain_mois - debut_mois).days
    
    # Prévision
    if jours_ecoules > 0:
        production_jour_moyenne = prod_actuelle['total'] / jours_ecoules
        prevision = production_jour_moyenne * jours_total
        return float(prevision)
    
    return 0.0

def get_objectif_production_jour():
    """Retourne l'objectif de production journalier"""
    # Objectif par défaut: 3000 kg/jour
    return 3000.0

def get_objectif_production_mois():
    """Retourne l'objectif de production mensuel"""
    # Objectif par défaut: 90000 kg/mois
    return 90000.0

def get_ecart_objectif_jour(date=None):
    """Calcule l'écart par rapport à l'objectif du jour"""
    if date is None:
        date = timezone.now().date()
    
    production = get_production_totale_jour(date)
    objectif = get_objectif_production_jour()
    
    ecart = production - objectif
    
    return {
        'production': production,
        'objectif': objectif,
        'ecart': float(ecart),
        'pourcentage': float((production / objectif * 100) if objectif > 0 else 0)
    }

def get_ecart_objectif_mois():
    """Calcule l'écart par rapport à l'objectif du mois"""
    
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    production = get_production_periode(debut_mois, aujourd_hui)
    objectif = get_objectif_production_mois()
    
    ecart = production['total'] - objectif
    
    return {
        'production': production['total'],
        'objectif': objectif,
        'ecart': float(ecart),
        'pourcentage': float((production['total'] / objectif * 100) if objectif > 0 else 0)
    }

# ==========================================
# FONCTIONS DE RAPPORTS
# ==========================================

def generer_rapport_journalier(date=None):
    """Génère un rapport complet pour un jour"""
    if date is None:
        date = timezone.now().date()
    
    return {
        'date': date,
        'production_totale': get_production_totale_jour(date),
        'production_par_section': get_production_par_section_jour(date),
        'dechets_totaux': get_dechets_totaux_jour(date),
        'matiere_premiere': get_matiere_premiere_jour(date),
        'machines_actives': get_machines_actives(),
        'alertes_actives': get_nombre_alertes_actives(),
        'efficacite': get_efficacite_moyenne_jour(date),
        'objectif': get_ecart_objectif_jour(date)
    }

def generer_rapport_hebdomadaire():
    """Génère un rapport complet pour la semaine"""
    
    aujourd_hui = timezone.now().date()
    debut_semaine = aujourd_hui - timedelta(days=aujourd_hui.weekday())
    fin_semaine = debut_semaine + timedelta(days=6)
    
    production = get_production_periode(debut_semaine, fin_semaine)
    dechets = get_dechets_periode(debut_semaine, fin_semaine)
    
    return {
        'periode': f"{debut_semaine.strftime('%d/%m/%Y')} - {fin_semaine.strftime('%d/%m/%Y')}",
        'debut': debut_semaine,
        'fin': fin_semaine,
        'production_totale': production['total'],
        'production_par_section': production,
        'dechets_totaux': dechets['total'],
        'rendement_moyen': get_rendement_moyen_periode(debut_semaine, fin_semaine),
        'taux_dechet': get_taux_dechet_moyen(debut_semaine, fin_semaine),
        'efficacite': get_efficacite_periode(debut_semaine, fin_semaine),
        'nombre_pannes': get_nombre_pannes_periode(debut_semaine, fin_semaine),
        'nombre_maintenances': get_nombre_maintenances_periode(debut_semaine, fin_semaine)
    }

# ==========================================
# FONCTIONS MANQUANTES POUR DASHBOARD
# ==========================================

def get_zones_performance(date=None):
    """Calcule la performance par zone"""
    if date is None:
        date = timezone.now().date()
    
    zones_data = []
    
    # Récupérer toutes les zones
    zones = ZoneExtrusion.objects.all()
    
    for zone in zones:
        # Production de la zone
        production = ProductionExtrusion.objects.filter(
            zone=zone,
            date_production=date
        ).aggregate(total=Sum('total_production_kg'))['total'] or 0
        
        # Rendement moyen
        rendement = ProductionExtrusion.objects.filter(
            zone=zone,
            date_production=date
        ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
        
        # Machines actives dans la zone
        machines_actives = Machine.objects.filter(
            zone_extrusion=zone,
            etat='ACTIVE'
        ).count()
        
        zones_data.append({
            'zone': zone.nom,
            'numero': zone.numero,
            'production': float(production),
            'rendement': float(rendement),
            'machines_actives': machines_actives,
            'performance': float(rendement)  # Score simplifié
        })
    
    return zones_data


def get_extrusion_details_jour(date=None):
    """Détails spécifiques pour l'extrusion"""
    if date is None:
        date = timezone.now().date()
    
    # Récupérer les données d'extrusion du jour
    productions = ProductionExtrusion.objects.filter(date_production=date)
    
    total_production = productions.aggregate(total=Sum('total_production_kg'))['total'] or 0
    total_dechets = productions.aggregate(total=Sum('dechets'))['total'] or 0
    rendement_moyen = productions.aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
    matiere_premiere = productions.aggregate(total=Sum('matiere_premiere_kg'))['total'] or 0
    
    # Calculer l'efficacité
    if matiere_premiere > 0:
        efficacite = (total_production / matiere_premiere) * 100
    else:
        efficacite = 0
    
    return {
        'production_totale': float(total_production),
        'dechets': float(total_dechets),
        'rendement_moyen': float(rendement_moyen),
        'matiere_premiere': float(matiere_premiere),
        'efficacite': float(efficacite),
        'nombre_zones': ProductionExtrusion.objects.filter(
            date_production=date
        ).values('zone').distinct().count(),
        'zones_actives': ZoneExtrusion.objects.filter(
            productionextrusion__date_production=date
        ).distinct().count()
    }


def get_imprimerie_details_jour(date=None):
    """Détails spécifiques pour l'imprimerie"""
    if date is None:
        date = timezone.now().date()
    
    productions = ProductionImprimerie.objects.filter(date_production=date)
    
    total_production = productions.aggregate(total=Sum('total_production_kg'))['total'] or 0
    total_dechets = productions.aggregate(total=Sum('dechets'))['total'] or 0
    bobines_finies = productions.aggregate(total=Sum('production_bobines_finies_kg'))['total'] or 0
    bobines_semi = productions.aggregate(total=Sum('production_bobines_semi_finies_kg'))['total'] or 0
    
    # Taux de qualité (simplifié)
    if total_production > 0:
        taux_qualite = (bobines_finies / total_production) * 100
    else:
        taux_qualite = 0
    
    # CORRECTION : Utiliser 'nombre_machines_actives' au lieu de 'machine'
    # Si vous voulez compter le nombre de lignes de production distinctes
    nombre_lignes_production = productions.count()
    
    # Ou si vous voulez la somme des machines actives
    total_machines_active = productions.aggregate(
        total=Sum('nombre_machines_actives')
    )['total'] or 0
    
    return {
        'production_totale': float(total_production),
        'dechets': float(total_dechets),
        'bobines_finies': float(bobines_finies),
        'bobines_semi': float(bobines_semi),
        'taux_qualite': float(taux_qualite),
        'nombre_machines': int(total_machines_active)  # CORRECTION ICI
    }



def get_soudure_details_jour(date=None):
    """Détails spécifiques pour la soudure"""
    if date is None:
        date = timezone.now().date()
    
    productions = ProductionSoudure.objects.filter(date_production=date)
    
    total_production = productions.aggregate(total=Sum('total_production_kg'))['total'] or 0
    total_dechets = productions.aggregate(total=Sum('dechets'))['total'] or 0
    bobines_finies = productions.aggregate(total=Sum('production_bobines_finies_kg'))['total'] or 0
    
    # Calcul d'efficacité (simplifié)
    if total_production > 0:
        efficacite = ((total_production - total_dechets) / total_production) * 100
    else:
        efficacite = 0

    nombre_entrees = productions.count()
    
    return {
        'production_totale': float(total_production),
        'dechets': float(total_dechets),
        'bobines_finies': float(bobines_finies),
        'efficacite': float(efficacite),
        'equipes': nombre_entrees  
    }


def get_recyclage_details_jour(date=None):
    """Détails spécifiques pour le recyclage - CORRIGÉ"""
    from django.db.models import Sum
    
    if date is None:
        date = timezone.now().date()
    
    productions = ProductionRecyclage.objects.filter(date_production=date)
    
    # 1. On utilise 'total_production_kg' (qui est égal à la bâche noire produite)
    total_production = productions.aggregate(total=Sum('total_production_kg'))['total'] or 0
    
    # 2. On remplace 'matiere_entree_kg' par 'production_broyage_kg'
    matiere_entree = productions.aggregate(total=Sum('production_broyage_kg'))['total'] or 0
    
    # Efficacité de recyclage
    if matiere_entree > 0:
        taux_recyclage = (total_production / matiere_entree) * 100
    else:
        taux_recyclage = 0
    
    # Économie estimée (simplifiée : 500 FCFA/kg)
    economie = total_production * 500 
    
    return {
        'production_totale': float(total_production),
        'matiere_entree': float(matiere_entree),
        'taux_recyclage': float(taux_recyclage),
        'economie_estimee': float(economie),
        'nombre_lots': productions.count()
    }


def get_chart_data_for_dashboard():
    """Données pour les graphiques du dashboard"""
    # Production des 7 derniers jours
    date_fin = timezone.now().date()
    date_debut = date_fin - timedelta(days=6)
    
    dates = []
    production_data = []
    rendement_data = []
    
    current_date = date_debut
    while current_date <= date_fin:
        # Production totale
        prod = get_production_totale_jour(current_date)
        
        # Rendement moyen
        rendement = ProductionExtrusion.objects.filter(
            date_production=current_date
        ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
        
        dates.append(current_date.strftime('%d/%m'))
        production_data.append(float(prod))
        rendement_data.append(float(rendement))
        
        current_date += timedelta(days=1)
    
    # Données par section pour le mois
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    section_data = {
        'extrusion': get_production_section_periode('EXTRUSION', debut_mois, aujourd_hui),
        'imprimerie': get_production_section_periode('IMPRIMERIE', debut_mois, aujourd_hui),
        'soudure': get_production_section_periode('SOUDURE', debut_mois, aujourd_hui),
        'recyclage': get_production_section_periode('RECYCLAGE', debut_mois, aujourd_hui),
    }
    
    return {
        'dates': dates,
        'production_journaliere': production_data,
        'rendement_journalier': rendement_data,
        'sections_labels': ['Extrusion', 'Imprimerie', 'Soudure', 'Recyclage'],
        'sections_data': [
            section_data['extrusion'],
            section_data['imprimerie'],
            section_data['soudure'],
            section_data['recyclage']
        ]
    }


def get_analytics_kpis():
    """KPIs analytiques pour le dashboard"""
    aujourd_hui = timezone.now().date()
    hier = aujourd_hui - timedelta(days=1)
    debut_mois = aujourd_hui.replace(day=1)
    
    # Production
    prod_aujourdhui = get_production_totale_jour(aujourd_hui)
    prod_hier = get_production_totale_jour(hier)
    prod_mois = get_production_periode(debut_mois, aujourd_hui)
    
    # Évolution
    if prod_hier > 0:
        evolution_jour = ((prod_aujourdhui - prod_hier) / prod_hier) * 100
    else:
        evolution_jour = 0
    
    # Objectifs
    objectif_journalier = 3000.0  # 3000 kg/jour
    if objectif_journalier > 0:
        pourcentage_objectif = (prod_aujourdhui / objectif_journalier) * 100
    else:
        pourcentage_objectif = 0
    
    # Machines
    taux_disponibilite = get_taux_disponibilite_machines()
    
    return {
        'production_aujourdhui': prod_aujourdhui,
        'evolution_vs_hier': float(evolution_jour),
        'taux_objectif': float(pourcentage_objectif),
        'taux_disponibilite': taux_disponibilite,
        'score_sante_moyen': get_score_sante_moyen(),
        'alertes_actives': get_nombre_alertes_actives(),
        'efficacite_moyenne': get_efficacite_moyenne_jour(aujourd_hui),
        'production_mois': prod_mois['total']
    }


def get_analytics_table_data():
    """Données pour le tableau analytique"""
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    # Données par section
    sections = ['EXTRUSION', 'IMPRIMERIE', 'SOUDURE', 'RECYCLAGE']
    
    table_data = []
    for section in sections:
        # Production
        prod = get_production_section_periode(section, debut_mois, aujourd_hui)
        
        # Rendement (pour les sections qui ont ce champ)
        if section == 'EXTRUSION':
            rendement = ProductionExtrusion.objects.filter(
                date_production__range=[debut_mois, aujourd_hui]
            ).aggregate(avg=Avg('rendement_pourcentage'))['avg'] or 0
        elif section == 'IMPRIMERIE':
            # CORRECTION : Utiliser un calcul différent pour l'imprimerie
            rendement = ProductionImprimerie.objects.filter(
                date_production__range=[debut_mois, aujourd_hui]
            ).aggregate(
                avg=Avg('taux_dechet_pourcentage')
            )['avg'] or 0
            rendement = 100 - rendement  # Transformer déchet en rendement
        elif section == 'SOUDURE':
            rendement = ProductionSoudure.objects.filter(
                date_production__range=[debut_mois, aujourd_hui]
            ).aggregate(
                avg=Avg('taux_dechet_pourcentage')
            )['avg'] or 0
            rendement = 100 - rendement if rendement else 85.0
        else:
            rendement = 90.0  # Valeur par défaut pour recyclage
        
        # Machines actives - CORRECTION
        if section == 'EXTRUSION':
            machines_actives = Machine.objects.filter(
                section=section,
                etat='ACTIVE'
            ).count()
        elif section == 'IMPRIMERIE':
            # Pour l'imprimerie, compter les machines de la section
            machines_actives = Machine.objects.filter(
                section=section,
                etat='ACTIVE'
            ).count()
        else:
            machines_actives = Machine.objects.filter(
                section=section,
                etat='ACTIVE'
            ).count()
        
        table_data.append({
            'section': section.title(),
            'production': float(prod),
            'rendement': float(rendement),
            'machines_actives': machines_actives,
            'performance': min(float(rendement), 100.0)
        })
    
    return table_data

def get_ca_mensuel(date_debut, date_fin):
    """Calcule le chiffre d'affaires mensuel (simplifié)"""
    # Hypothèse: 2000 FCFA/kg de production
    production = get_production_totale_periode(date_debut, date_fin)
    ca = production * Decimal('2000')
    
    return ca


def get_production_totale_periode(date_debut, date_fin):
    """Calcule la production totale pour une période"""
    production = get_production_periode(date_debut, date_fin)
    return Decimal(str(production['total']))


def calculate_percentage_of_goal(valeur, objectif):
    """Calcule le pourcentage par rapport à un objectif"""
    if objectif and objectif > 0:
        return (valeur / objectif) * Decimal('100')
    return Decimal('0')


def get_efficacite_globale_periode(date_debut, date_fin):
    """Calcule l'efficacité globale pour une période"""
    efficacite = get_efficacite_periode(date_debut, date_fin)
    return Decimal(str(efficacite))


def get_cout_production_moyen(date_debut, date_fin):
    """Calcule le coût de production moyen par kg"""
    cout_total = get_cout_production_periode(date_debut, date_fin)
    production = get_production_totale_periode(date_debut, date_fin)
    
    if production > 0:
        cout_moyen = Decimal(str(cout_total)) / production
    else:
        cout_moyen = Decimal('0')
    
    return cout_moyen


def get_performances_sections(date_debut, date_fin):
    """Calcule les performances par section"""
    sections = ['EXTRUSION', 'IMPRIMERIE', 'SOUDURE', 'RECYCLAGE']
    
    performances = []
    for section in sections:
        # Production
        prod = get_production_section_periode(section, date_debut, date_fin)
        
        # Efficacité
        efficacite = get_efficacite_section(section, date_debut, date_fin)
        
        # Coût (simplifié)
        if prod > 0:
            cout_kg = Decimal('850') * (Decimal('100') - Decimal(str(efficacite))) / Decimal('100')
        else:
            cout_kg = Decimal('850')
        
        performances.append({
            'section': section.title(),
            'production': Decimal(str(prod)),
            'efficacite': Decimal(str(efficacite)),
            'cout_moyen': cout_kg,
            'rendement': Decimal(str(min(efficacite, 100.0)))
        })
    
    return performances


def get_machines_stats():
    """Retourne les statistiques des machines pour le dashboard"""
    
    # Nombre total de machines
    total_machines = Machine.objects.count()
    
    # Machines par état
    machines_actives = Machine.objects.filter(etat='ACTIVE').count()
    machines_en_panne = Machine.objects.filter(etat='PANNE').count()
    machines_maintenance = Machine.objects.filter(etat='MAINTENANCE').count()
    machines_inactives = Machine.objects.filter(etat='INACTIVE').count()
    
    # Taux de disponibilité
    if total_machines > 0:
        taux_disponibilite = (machines_actives / total_machines) * 100
    else:
        taux_disponibilite = 0
    
    # Score de santé moyen
    score_sante = Machine.objects.filter(
        etat='ACTIVE'
    ).aggregate(avg=Avg('score_sante_global'))['avg'] or 0
    
    # Machines à risque
    machines_risque = Machine.objects.filter(
        Q(probabilite_panne_7_jours__gte=40) | Q(score_sante_global__lte=70)
    ).count()
    
    # Machines critiques
    machines_critiques = Machine.objects.filter(
        Q(probabilite_panne_7_jours__gte=70) | Q(score_sante_global__lte=50)
    ).count()
    
    # Répartition par section
    repartition_section = Machine.objects.values('section').annotate(
        total=Count('id'),
        actives=Count('id', filter=Q(etat='ACTIVE'))
    ).order_by('section')
    
    # Données pour les graphiques
    graph_data = {
        'etats': {
            'labels': ['Actives', 'En panne', 'Maintenance', 'Inactives'],
            'data': [
                machines_actives,
                machines_en_panne,
                machines_maintenance,
                machines_inactives
            ],
            'colors': ['#10b981', '#ef4444', '#f59e0b', '#6b7280']
        },
        'sections': {
            'labels': [],
            'data': [],
            'actives': []
        }
    }
    
    # Remplir les données par section
    for section in repartition_section:
        graph_data['sections']['labels'].append(section['section'].title())
        graph_data['sections']['data'].append(section['total'])
        graph_data['sections']['actives'].append(section['actives'])
    
    return {
        'total': total_machines,
        'actives': machines_actives,
        'en_panne': machines_en_panne,
        'maintenance': machines_maintenance,
        'inactives': machines_inactives,
        'taux_disponibilite': float(taux_disponibilite),
        'score_sante_moyen': float(score_sante),
        'machines_a_risque': machines_risque,
        'machines_critiques': machines_critiques,
        'repartition_section': list(repartition_section),
        'graph_data': graph_data,
        'maintenances_prevues': get_nombre_maintenances_prevues(),
        'probabilite_panne_moyenne': float(Machine.objects.aggregate(
            avg=Avg('probabilite_panne_7_jours')
        )['avg'] or 0)
    }


def get_production_par_section(date_debut, date_fin):
    """Retourne la production par section sous forme de liste"""
    production = get_production_periode(date_debut, date_fin)
    
    return [
        float(production['extrusion']),
        float(production['imprimerie']),
        float(production['soudure']),
        float(production['recyclage'])
    ]

def generer_rapport_mensuel():
    """Génère un rapport complet pour le mois"""
    
    aujourd_hui = timezone.now().date()
    debut_mois = aujourd_hui.replace(day=1)
    
    production = get_production_periode(debut_mois, aujourd_hui)
    dechets = get_dechets_periode(debut_mois, aujourd_hui)
    
    return {
        'mois': debut_mois.strftime('%B %Y'),
        'debut': debut_mois,
        'fin': aujourd_hui,
        'production_totale': production['total'],
        'production_par_section': production,
        'dechets_totaux': dechets['total'],
        'rendement_moyen': get_rendement_moyen_periode(debut_mois, aujourd_hui),
        'taux_dechet': get_taux_dechet_moyen(debut_mois, aujourd_hui),
        'efficacite': get_efficacite_periode(debut_mois, aujourd_hui),
        'nombre_pannes': get_nombre_pannes_periode(debut_mois, aujourd_hui),
        'nombre_maintenances': get_nombre_maintenances_periode(debut_mois, aujourd_hui),
        'cout_total': get_cout_production_periode(debut_mois, aujourd_hui),
        'objectif': get_ecart_objectif_mois()
    }

def get_zones_utilisateur(user):
    """Retourne les zones accessibles par un utilisateur"""
    if user.role in ['admin', 'direction', 'superviseur']:
        # Admin, direction et superviseurs voient toutes les zones
        return ZoneExtrusion.objects.all()
    elif user.role == 'operateur':
        # Opérateurs voient seulement les zones où ils sont affectés
        # Note: Vous devrez ajuster cette logique selon votre modèle d'utilisateur
        return ZoneExtrusion.objects.filter(operateurs=user).distinct()
    else:
        # Par défaut, retourner toutes les zones
        return ZoneExtrusion.objects.all()


def calculate_extrusion_metrics(production_instance):
    """Calcule les métriques pour une production d'extrusion"""
    metrics = {
        'rendement_pourcentage': 0.0,
        'taux_dechet_pourcentage': 0.0,
        'efficacite': 0.0,
        'productivite_horaire': 0.0
    }
    
    try:
        # Calcul du rendement
        if production_instance.matiere_premiere_kg and production_instance.matiere_premiere_kg > 0:
            metrics['rendement_pourcentage'] = (
                production_instance.total_production_kg / 
                production_instance.matiere_premiere_kg * 100
            )
        
        # Calcul du taux de déchet
        if production_instance.total_production_kg and production_instance.total_production_kg > 0:
            metrics['taux_dechet_pourcentage'] = (
                production_instance.dechets / 
                production_instance.total_production_kg * 100
            )
        
        # Calcul de l'efficacité (basé sur le rendement et la qualité)
        if metrics['rendement_pourcentage'] > 0:
            metrics['efficacite'] = (
                metrics['rendement_pourcentage'] * 0.7 + 
                (100 - metrics['taux_dechet_pourcentage']) * 0.3
            )
        
        # Calcul de la productivité horaire
        if production_instance.heures_travaillees and production_instance.heures_travaillees > 0:
            metrics['productivite_horaire'] = (
                production_instance.total_production_kg / 
                production_instance.heures_travaillees
            )
            
    except (AttributeError, ZeroDivisionError, TypeError):
        # Gérer les cas d'erreur
        pass
    
    return metrics


def calculate_imprimerie_metrics(production_instance):
    """Calcule les métriques pour une production d'imprimerie"""
    metrics = {
        'rendement_pourcentage': 0.0,
        'taux_dechet_pourcentage': 0.0,
        'taux_qualite': 0.0,
        'efficacite': 0.0
    }
    
    try:
        # CORRECTION : Vérifier si le champ existe
        matiere_entree = getattr(production_instance, 'matiere_entree_kg', 0)
        dechets = getattr(production_instance, 'dechets', 0)
        total_prod = getattr(production_instance, 'total_production_kg', 0)
        bobines_finies = getattr(production_instance, 'production_bobines_finies_kg', 0)
        
        # Calcul du rendement (production totale / entrée matière)
        if matiere_entree and matiere_entree > 0:
            total_production = (
                bobines_finies +
                getattr(production_instance, 'production_bobines_semi_finies_kg', 0)
            )
            metrics['rendement_pourcentage'] = (total_production / matiere_entree) * 100
        
        # Calcul du taux de déchet
        if total_prod and total_prod > 0:
            metrics['taux_dechet_pourcentage'] = (dechets / total_prod) * 100
        
        # Calcul du taux de qualité (bobines finies / total)
        if total_prod and total_prod > 0:
            metrics['taux_qualite'] = (bobines_finies / total_prod) * 100
        
        # Calcul de l'efficacité globale
        metrics['efficacite'] = (
            metrics['rendement_pourcentage'] * 0.4 +
            metrics['taux_qualite'] * 0.4 +
            (100 - metrics['taux_dechet_pourcentage']) * 0.2
        )
        
    except (AttributeError, ZeroDivisionError, TypeError) as e:
        # Gérer les cas d'erreur
        print(f"Erreur dans calculate_imprimerie_metrics: {e}")
        pass
    
    return metrics


    

def calculate_soudure_metrics(production_instance):
    """Calcule les métriques pour une production de soudure"""
    metrics = {
        'rendement_pourcentage': 0.0,
        'taux_dechet_pourcentage': 0.0,
        'efficacite': 0.0,
        'productivite': 0.0
    }
    
    try:
        # Calcul du rendement
        if production_instance.matiere_entree_kg and production_instance.matiere_entree_kg > 0:
            metrics['rendement_pourcentage'] = (
                production_instance.total_production_kg / 
                production_instance.matiere_entree_kg * 100
            )
        
        # Calcul du taux de déchet
        if production_instance.total_production_kg and production_instance.total_production_kg > 0:
            metrics['taux_dechet_pourcentage'] = (
                production_instance.dechets / 
                production_instance.total_production_kg * 100
            )
        
        # Calcul de l'efficacité
        metrics['efficacite'] = (
            metrics['rendement_pourcentage'] * 0.6 +
            (100 - metrics['taux_dechet_pourcentage']) * 0.4
        )
        
        # Calcul de la productivité (par machine ou par équipe)
        if production_instance.nombre_machines and production_instance.nombre_machines > 0:
            metrics['productivite'] = (
                production_instance.total_production_kg / 
                production_instance.nombre_machines
            )
            
    except (AttributeError, ZeroDivisionError, TypeError):
        # Gérer les cas d'erreur
        pass
    
    return metrics


def calculate_recyclage_metrics(production_instance):
    """Calcule les métriques pour une production de recyclage"""
    metrics = {
        'taux_recyclage': 0.0,
        'pureté_matiere': 0.0,
        'efficacite': 0.0,
        'economie_estimee': 0.0
    }
    
    try:
        # Calcul du taux de recyclage
        if production_instance.matiere_entree_kg and production_instance.matiere_entree_kg > 0:
            metrics['taux_recyclage'] = (
                production_instance.total_production_kg / 
                production_instance.matiere_entree_kg * 100
            )
        
        # Estimation de la pureté (basé sur le type de matière)
        # Note: Vous devrez ajuster cette logique selon vos besoins réels
        if production_instance.type_matiere_recyclee:
            purete_map = {
                'PLASTIQUE_PROPRE': 95.0,
                'PLASTIQUE_MIXTE': 85.0,
                'PLASTIQUE_CONTAMINE': 70.0,
                'DECHETS_INDUSTRIELS': 80.0
            }
            metrics['pureté_matiere'] = purete_map.get(
                production_instance.type_matiere_recyclee, 
                75.0
            )
        
        # Calcul de l'efficacité
        metrics['efficacite'] = (
            metrics['taux_recyclage'] * 0.5 +
            metrics['pureté_matiere'] * 0.3 +
            25.0  # Bonus fixe pour l'effort environnemental
        )
        
        # Estimation de l'économie (500 FCFA par kg recyclé)
        metrics['economie_estimee'] = production_instance.total_production_kg * 500
        
    except (AttributeError, TypeError):
        # Gérer les cas d'erreur
        pass
    
    return metrics

def get_mois_disponibles():
    """Retourne la liste des mois disponibles ayant des données de production"""
    
    # Récupérer tous les mois distincts ayant des données d'extrusion
    mois_extrusion = ProductionExtrusion.objects.dates(
        'date_production', 'month', order='DESC'
    ).distinct()
    
    # Récupérer tous les mois distincts ayant des données d'imprimerie
    mois_imprimerie = ProductionImprimerie.objects.dates(
        'date_production', 'month', order='DESC'
    ).distinct()
    
    # Récupérer tous les mois distincts ayant des données de soudure
    mois_soudure = ProductionSoudure.objects.dates(
        'date_production', 'month', order='DESC'
    ).distinct()
    
    # Récupérer tous les mois distincts ayant des données de recyclage
    mois_recyclage = ProductionRecyclage.objects.dates(
        'date_production', 'month', order='DESC'
    ).distinct()
    
    # Combiner tous les mois uniques
    tous_mois = set()
    for mois_list in [mois_extrusion, mois_imprimerie, mois_soudure, mois_recyclage]:
        for mois in mois_list:
            tous_mois.add(mois.strftime('%Y-%m'))
    
    # Convertir en liste triée par ordre décroissant
    mois_liste = sorted(tous_mois, reverse=True)
    
    # Si aucun mois n'est trouvé, ajouter le mois en cours
    if not mois_liste:
        mois_courant = timezone.now().strftime('%Y-%m')
        mois_liste = [mois_courant]
    
    # Formater pour l'affichage
    mois_formates = []
    for mois_str in mois_liste:
        annee, mois_num = mois_str.split('-')
        mois_num = int(mois_num)
        mois_formates.append({
            'valeur': mois_str,
            'nom': get_nom_mois(mois_num),
            'annee': annee,
            'mois_num': mois_num
        })
    
    return mois_formates


def get_nom_mois(mois_num):
    """Retourne le nom du mois en français à partir de son numéro"""
    
    noms_mois = {
        1: 'Janvier',
        2: 'Février',
        3: 'Mars',
        4: 'Avril',
        5: 'Mai',
        6: 'Juin',
        7: 'Juillet',
        8: 'Août',
        9: 'Septembre',
        10: 'Octobre',
        11: 'Novembre',
        12: 'Décembre'
    }
    
    return noms_mois.get(mois_num, '')