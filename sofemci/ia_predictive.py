# sofemci/ia_predictive.py
# Module d'Intelligence Artificielle pour Prédiction de Pannes
from django.db.models import F, Avg, Sum, Count, Max, Min
import numpy as np
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal
from .models import (
    Machine, AlerteIA, HistoriqueMachine,
    ProductionExtrusion, ProductionImprimerie, 
    ProductionSoudure, ProductionRecyclage,
    ZoneExtrusion
)


class MoteurPredictionPannes:
    """
    Moteur d'IA pour la prédiction de pannes machines
    Utilise un algorithme de scoring basé sur plusieurs facteurs
    """
    
    # Poids des différents facteurs dans le calcul du risque (AMÉLIORÉ)
    POIDS = {
        'age_machine': 0.12,              # Réduit de 0.15
        'heures_fonctionnement': 0.18,    # Réduit de 0.20
        'historique_pannes': 0.20,        # Réduit de 0.25
        'maintenance_retard': 0.15,       # Maintenu
        'temperature': 0.10,              # Maintenu
        'consommation': 0.10,             # Maintenu
        'taux_utilisation': 0.05,         # Maintenu
        'performance_production': 0.10,   # NOUVEAU
    }
    
    def __init__(self, machine):
        self.machine = machine
        self.score_sante = 100
        self.facteurs_risque = []
        self.anomalies = []
    
    def analyser_machine(self):
        """
        Analyse complète de la machine et calcul des scores
        Retourne un dictionnaire avec tous les résultats
        """
        # Calcul de chaque facteur
        score_age = self._analyser_age()
        score_heures = self._analyser_heures_fonctionnement()
        score_pannes = self._analyser_historique_pannes()
        score_maintenance = self._analyser_maintenance()
        score_temperature = self._analyser_temperature()
        score_consommation = self._analyser_consommation()
        score_utilisation = self._analyser_taux_utilisation()
        
        # NOUVEAU : Analyse de la performance de production
        score_production = self._analyser_performance_production()
        
        # NOUVEAU : Analyse des risques par zone
        score_zone = self._analyser_risques_zone()
        
        # Calcul du score de santé global (moyenne pondérée)
        self.score_sante = (
            score_age * self.POIDS['age_machine'] +
            score_heures * self.POIDS['heures_fonctionnement'] +
            score_pannes * self.POIDS['historique_pannes'] +
            score_maintenance * self.POIDS['maintenance_retard'] +
            score_temperature * self.POIDS['temperature'] +
            score_consommation * self.POIDS['consommation'] +
            score_utilisation * self.POIDS['taux_utilisation'] +
            score_production * self.POIDS['performance_production']
        )
        
        # Ajustement selon les risques de zone
        self.score_sante = self.score_sante * (score_zone / 100)
        
        # Calcul des probabilités de panne
        prob_7j = self._calculer_probabilite_panne(7)
        prob_30j = self._calculer_probabilite_panne(30)
        
        # Détection d'anomalies
        self._detecter_anomalies()
        
        # Mise à jour de la machine
        self._mettre_a_jour_machine(prob_7j, prob_30j)
        
        # Génération d'alertes si nécessaire
        self._generer_alertes(prob_7j, prob_30j)
        
        return {
            'score_sante': round(self.score_sante, 2),
            'probabilite_panne_7j': round(prob_7j, 2),
            'probabilite_panne_30j': round(prob_30j, 2),
            'niveau_risque': self._niveau_risque(prob_7j),
            'facteurs_risque': self.facteurs_risque,
            'anomalies': self.anomalies,
            'scores_detail': {
                'age': score_age,
                'heures': score_heures,
                'pannes': score_pannes,
                'maintenance': score_maintenance,
                'temperature': score_temperature,
                'consommation': score_consommation,
                'utilisation': score_utilisation,
                'production': score_production,  # NOUVEAU
                'zone': score_zone,  # NOUVEAU
            }
        }
    
    def _analyser_age(self):
        """Analyse l'âge de la machine"""
        age_jours = self.machine.calculer_age_machine()
        
        if age_jours < 365:
            score = 100
        elif age_jours < 1095:
            score = 90
        elif age_jours < 1825:
            score = 80
            self.facteurs_risque.append('Machine de plus de 3 ans')
        elif age_jours < 2555:
            score = 70
            self.facteurs_risque.append('Machine de plus de 5 ans')
        else:
            score = 60
            self.facteurs_risque.append('Machine ancienne (>7 ans)')
        
        return score
    
    def _analyser_heures_fonctionnement(self):
        """Analyse les heures de fonctionnement"""
        heures_totales = float(self.machine.heures_fonctionnement_totales)
        heures_depuis_maintenance = float(self.machine.heures_depuis_derniere_maintenance)
        
        limite_heures = self.machine.frequence_maintenance_jours * 8
        
        if heures_depuis_maintenance < limite_heures * 0.5:
            score = 100
        elif heures_depuis_maintenance < limite_heures * 0.75:
            score = 85
        elif heures_depuis_maintenance < limite_heures:
            score = 70
            self.facteurs_risque.append('Maintenance bientôt nécessaire')
        elif heures_depuis_maintenance < limite_heures * 1.2:
            score = 50
            self.facteurs_risque.append('Maintenance en retard')
        else:
            score = 30
            self.facteurs_risque.append('Maintenance très en retard')
        
        return score
    
    def _analyser_historique_pannes(self):
        """Analyse l'historique des pannes"""
        pannes_totales = self.machine.nombre_pannes_totales
        pannes_6_mois = self.machine.nombre_pannes_6_derniers_mois
        pannes_1_mois = self.machine.nombre_pannes_1_dernier_mois
        
        score = 100
        
        if pannes_1_mois > 0:
            score -= pannes_1_mois * 25
            self.facteurs_risque.append(f'{pannes_1_mois} panne(s) ce mois')
        
        if pannes_6_mois > 2:
            score -= (pannes_6_mois - 2) * 10
            self.facteurs_risque.append(f'{pannes_6_mois} pannes sur 6 mois')
        
        if pannes_totales > 10:
            score -= 15
            self.facteurs_risque.append('Historique de pannes important')
        
        return max(score, 0)
    
    def _analyser_maintenance(self):
        """Analyse l'état de la maintenance"""
        jours_depuis_maintenance = self.machine.jours_depuis_derniere_maintenance()
        frequence = self.machine.frequence_maintenance_jours
        
        if jours_depuis_maintenance < frequence * 0.5:
            score = 100
        elif jours_depuis_maintenance < frequence * 0.75:
            score = 90
        elif jours_depuis_maintenance < frequence:
            score = 75
        elif jours_depuis_maintenance < frequence * 1.1:
            score = 50
            self.facteurs_risque.append('Maintenance requise')
        elif jours_depuis_maintenance < frequence * 1.3:
            score = 30
            self.facteurs_risque.append('Maintenance urgente')
        else:
            score = 10
            self.facteurs_risque.append('Maintenance critique')
        
        return score
    
    def _analyser_temperature(self):
        """Analyse la température de fonctionnement"""
        if not self.machine.temperature_actuelle:
            return 100
        
        temp_actuelle = float(self.machine.temperature_actuelle)
        temp_nominale = float(self.machine.temperature_nominale)
        temp_max = float(self.machine.temperature_max_autorisee)
        
        if temp_nominale == 0:
            return 100
        
        if temp_actuelle < temp_nominale * 1.05:
            score = 100
        elif temp_actuelle < temp_nominale * 1.10:
            score = 85
            self.anomalies.append(f'Température légèrement élevée ({temp_actuelle}°C)')
        elif temp_actuelle < temp_nominale * 1.15:
            score = 70
            self.anomalies.append(f'Température élevée ({temp_actuelle}°C)')
            self.facteurs_risque.append('Surchauffe modérée')
        elif temp_actuelle < temp_max:
            score = 50
            self.anomalies.append(f'Température très élevée ({temp_actuelle}°C)')
            self.facteurs_risque.append('Risque de surchauffe')
        else:
            score = 20
            self.anomalies.append(f'SURCHAUFFE CRITIQUE ({temp_actuelle}°C)')
            self.facteurs_risque.append('SURCHAUFFE CRITIQUE')
        
        return score
    
    def _analyser_consommation(self):
        """Analyse la consommation électrique"""
        if self.machine.consommation_electrique_nominale == 0:
            return 100
        
        conso_actuelle = float(self.machine.consommation_electrique_kwh)
        conso_nominale = float(self.machine.consommation_electrique_nominale)
        
        variation = ((conso_actuelle - conso_nominale) / conso_nominale) * 100
        
        if abs(variation) < 10:
            score = 100
        elif abs(variation) < 20:
            score = 85
            if variation > 0:
                self.anomalies.append(f'Surconsommation de {variation:.1f}%')
            else:
                self.anomalies.append(f'Sous-consommation de {abs(variation):.1f}%')
        elif abs(variation) < 30:
            score = 70
            self.facteurs_risque.append('Consommation anormale')
        else:
            score = 50
            self.facteurs_risque.append('Consommation très anormale')
        
        return score
    
    def _analyser_taux_utilisation(self):
        """Analyse le taux d'utilisation"""
        taux = self.machine.taux_utilisation()
        
        if taux < 30:
            score = 100
        elif taux < 50:
            score = 95
        elif taux < 70:
            score = 90
        elif taux < 85:
            score = 80
            self.facteurs_risque.append('Taux d\'utilisation élevé')
        else:
            score = 70
            self.facteurs_risque.append('Taux d\'utilisation très élevé')
        
        return score
    
    def _analyser_performance_production(self):
        """
        NOUVEAU : Analyse la performance de production de la machine
        Détecte les baisses de rendement, excès de déchets, efficacité réduite
        """
        score = 100
        periode_analyse = timezone.now().date() - timedelta(days=7)
        
        # Selon la section, analyser la production correspondante
        if self.machine.section == 'extrusion' and self.machine.zone_extrusion:
            productions = ProductionExtrusion.objects.filter(
                zone=self.machine.zone_extrusion,
                date_production__gte=periode_analyse
            )
            
            if productions.exists():
                # 1. Analyser le rendement moyen
                rendement_moyen = productions.aggregate(
                    avg=Avg('rendement_pourcentage')
                )['avg'] or 100
                
                if rendement_moyen < 70:
                    score -= 30
                    self.facteurs_risque.append(f'Rendement faible: {rendement_moyen:.1f}%')
                    self.anomalies.append(f'Baisse significative de rendement ({rendement_moyen:.1f}%)')
                elif rendement_moyen < 80:
                    score -= 15
                    self.facteurs_risque.append(f'Rendement en baisse: {rendement_moyen:.1f}%')
                
                # 2. Analyser l'évolution du taux de déchets
                taux_dechets = productions.aggregate(
                    total_prod=Sum('total_production_kg'),
                    total_dechets=Sum('dechets_kg')
                )
                
                if taux_dechets['total_prod'] and taux_dechets['total_prod'] > 0:
                    pourcentage_dechets = (
                        float(taux_dechets['total_dechets'] or 0) / 
                        float(taux_dechets['total_prod']) * 100
                    )
                    
                    if pourcentage_dechets > 5:
                        score -= 20
                        self.facteurs_risque.append(f'Taux de déchets élevé: {pourcentage_dechets:.1f}%')
                        self.anomalies.append(f'Déchets anormalement élevés ({pourcentage_dechets:.1f}%)')
                    elif pourcentage_dechets > 3:
                        score -= 10
                        self.facteurs_risque.append(f'Déchets en hausse: {pourcentage_dechets:.1f}%')
                
                # 3. Détecter une chute brutale de production
                productions_list = list(productions.order_by('-date_production')[:3])
                if len(productions_list) >= 2:
                    prod_recente = float(productions_list[0].total_production_kg)
                    prod_anterieure = float(productions_list[1].total_production_kg)
                    
                    if prod_anterieure > 0:
                        variation = ((prod_recente - prod_anterieure) / prod_anterieure) * 100
                        
                        if variation < -20:
                            score -= 25
                            self.facteurs_risque.append(f'Chute de production: {abs(variation):.1f}%')
                            self.anomalies.append(f'Production en chute libre ({variation:.1f}%)')
        
        elif self.machine.section == 'imprimerie':
            productions = ProductionImprimerie.objects.filter(
                date_production__gte=periode_analyse
            )
            
            if productions.exists():
                # Analyser le taux de déchets
                taux_dechets = productions.aggregate(
                    total_prod=Sum('total_production_kg'),
                    total_dechets=Sum('dechets_kg')
                )
                
                if taux_dechets['total_prod'] and taux_dechets['total_prod'] > 0:
                    pourcentage_dechets = (
                        float(taux_dechets['total_dechets'] or 0) / 
                        float(taux_dechets['total_prod']) * 100
                    )
                    
                    if pourcentage_dechets > 4:
                        score -= 20
                        self.facteurs_risque.append(f'Déchets imprimerie élevés: {pourcentage_dechets:.1f}%')
                
                # Détecter baisse de production totale
                prod_moyenne = productions.aggregate(
                    avg=Avg('total_production_kg')
                )['avg'] or 0
                
                if prod_moyenne < 500:
                    score -= 15
                    self.facteurs_risque.append('Production imprimerie faible')
        
        elif self.machine.section == 'soudure':
            productions = ProductionSoudure.objects.filter(
                date_production__gte=periode_analyse
            )
            
            if productions.exists():
                # Analyser déchets soudure
                taux_dechets = productions.aggregate(
                    total_prod=Sum('total_production_kg'),
                    total_dechets=Sum('dechets_kg')
                )
                
                if taux_dechets['total_prod'] and taux_dechets['total_prod'] > 0:
                    pourcentage_dechets = (
                        float(taux_dechets['total_dechets'] or 0) / 
                        float(taux_dechets['total_prod']) * 100
                    )
                    
                    if pourcentage_dechets > 5:
                        score -= 20
                        self.facteurs_risque.append(f'Déchets soudure élevés: {pourcentage_dechets:.1f}%')
        
        elif self.machine.section == 'recyclage':
            productions = ProductionRecyclage.objects.filter(
                date_production__gte=periode_analyse
            )
            
            if productions.exists():
                # Analyser le taux de transformation
                totaux = productions.aggregate(
                    broyage=Sum('production_broyage_kg'),
                    bache=Sum('production_bache_noir_kg')
                )
                
                if totaux['broyage'] and totaux['broyage'] > 0:
                    taux_transformation = (
                        float(totaux['bache'] or 0) / 
                        float(totaux['broyage']) * 100
                    )
                    
                    if taux_transformation < 60:
                        score -= 25
                        self.facteurs_risque.append(f'Taux transformation faible: {taux_transformation:.1f}%')
                        self.anomalies.append(f'Recyclage inefficace ({taux_transformation:.1f}%)')
                    elif taux_transformation < 70:
                        score -= 10
                        self.facteurs_risque.append(f'Transformation en baisse: {taux_transformation:.1f}%')
        
        return max(score, 0)
    
    def _analyser_risques_zone(self):
        """
        NOUVEAU : Analyse les risques au niveau de la zone
        Corrèle les problèmes entre machines d'une même zone
        """
        score_zone = 100
        
        if self.machine.section != 'extrusion' or not self.machine.zone_extrusion:
            return score_zone
        
        zone = self.machine.zone_extrusion
        
        # 1. Analyser l'état des autres machines de la zone
        machines_zone = Machine.objects.filter(
            zone_extrusion=zone,
            etat='actif'
        ).exclude(id=self.machine.id)
        
        if machines_zone.exists():
            # Compter les machines à risque dans la zone
            machines_risque = machines_zone.filter(
                probabilite_panne_7_jours__gte=40
            ).count()
            
            if machines_risque >= 2:
                score_zone -= 20
                self.facteurs_risque.append(f'Zone {zone.numero}: {machines_risque} autres machines à risque')
                self.anomalies.append(f'Problème généralisé dans la zone {zone.nom}')
            elif machines_risque >= 1:
                score_zone -= 10
                self.facteurs_risque.append(f'Zone {zone.numero}: 1 autre machine à risque')
            
            # Analyser les pannes récentes dans la zone
            pannes_zone_recentes = machines_zone.filter(
                date_derniere_panne__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            if pannes_zone_recentes >= 2:
                score_zone -= 15
                self.facteurs_risque.append(f'Zone {zone.numero}: {pannes_zone_recentes} pannes récentes')
            
            # Température moyenne de la zone
            temp_moyenne_zone = machines_zone.aggregate(
                avg=Avg('temperature_actuelle')
            )['avg']
            
            if temp_moyenne_zone and temp_moyenne_zone > 85:
                score_zone -= 10
                self.facteurs_risque.append(f'Zone {zone.numero}: température ambiante élevée')
        
        # 2. Analyser la production globale de la zone
        periode_analyse = timezone.now().date() - timedelta(days=7)
        productions_zone = ProductionExtrusion.objects.filter(
            zone=zone,
            date_production__gte=periode_analyse
        )
        
        if productions_zone.exists():
            # Rendement moyen de la zone
            rendement_zone = productions_zone.aggregate(
                avg=Avg('rendement_pourcentage')
            )['avg'] or 100
            
            if rendement_zone < 75:
                score_zone -= 15
                self.facteurs_risque.append(f'Zone {zone.numero}: rendement global faible ({rendement_zone:.1f}%)')
            
            # Nombre de machines actives vs production
            machines_actives_prod = productions_zone.aggregate(
                avg=Avg('nombre_machines_actives')
            )['avg'] or 0
            
            machines_disponibles = zone.nombre_machines_max
            taux_utilisation_zone = (machines_actives_prod / machines_disponibles * 100) if machines_disponibles > 0 else 0
            
            if taux_utilisation_zone < 50:
                score_zone -= 10
                self.facteurs_risque.append(f'Zone {zone.numero}: sous-utilisée ({taux_utilisation_zone:.0f}%)')
        
        return max(score_zone, 0)
    
    def _calculer_probabilite_panne(self, jours):
        """Calcule la probabilité de panne sur N jours"""
        risque_base = 100 - self.score_sante
        
        if self.machine.nombre_pannes_1_dernier_mois > 0:
            risque_base += 20 * self.machine.nombre_pannes_1_dernier_mois
        
        if self.machine.nombre_pannes_6_derniers_mois > 2:
            risque_base += 10
        
        facteur_temps = jours / 30
        probabilite = risque_base * facteur_temps
        
        return min(max(probabilite, 0), 100)
    
    def _detecter_anomalies(self):
        """Détection d'anomalies améliorée avec corrélations"""
        # Anomalie existante
        if self.machine.est_en_surchauffe() and self.machine.est_en_surconsommation():
            self.anomalies.append('ALERTE: Surchauffe ET surconsommation simultanées')
            self.facteurs_risque.append('Anomalie critique détectée')
        
        # NOUVEAU : Anomalie température + baisse de production
        periode = timezone.now().date() - timedelta(days=3)
        
        if self.machine.section == 'extrusion' and self.machine.zone_extrusion:
            if self.machine.est_en_surchauffe():
                productions_recentes = ProductionExtrusion.objects.filter(
                    zone=self.machine.zone_extrusion,
                    date_production__gte=periode
                )
                
                if productions_recentes.exists():
                    rendement = productions_recentes.aggregate(
                        avg=Avg('rendement_pourcentage')
                    )['avg'] or 100
                    
                    if rendement < 75:
                        self.anomalies.append('CORRÉLATION: Surchauffe + Baisse rendement')
                        self.facteurs_risque.append('Défaillance thermique probable')
        
        # NOUVEAU : Surconsommation + excès de déchets
        if self.machine.est_en_surconsommation():
            if self.machine.section == 'extrusion' and self.machine.zone_extrusion:
                productions_recentes = ProductionExtrusion.objects.filter(
                    zone=self.machine.zone_extrusion,
                    date_production__gte=periode
                )
                
                taux_dechets = productions_recentes.aggregate(
                    prod=Sum('total_production_kg'),
                    dechets=Sum('dechets_kg')
                )
                
                if taux_dechets['prod'] and taux_dechets['prod'] > 0:
                    pct_dechets = (
                        float(taux_dechets['dechets'] or 0) / 
                        float(taux_dechets['prod']) * 100
                    )
                    
                    if pct_dechets > 4:
                        self.anomalies.append(
                            f'CORRÉLATION: Surconsommation + Déchets élevés ({pct_dechets:.1f}%)'
                        )
                        self.facteurs_risque.append('Dysfonctionnement de transformation')
    
    def _mettre_a_jour_machine(self, prob_7j, prob_30j):
        """Met à jour les données de la machine"""
        self.machine.score_sante_global = Decimal(str(round(self.score_sante, 2)))
        self.machine.probabilite_panne_7_jours = Decimal(str(round(prob_7j, 2)))
        self.machine.probabilite_panne_30_jours = Decimal(str(round(prob_30j, 2)))
        self.machine.anomalie_detectee = len(self.anomalies) > 0
        self.machine.type_anomalie = ', '.join(self.anomalies[:3]) if self.anomalies else ''
        self.machine.date_derniere_analyse_ia = timezone.now()
        self.machine.save()
    
    def _generer_alertes(self, prob_7j, prob_30j):
        """Génère des alertes IA si nécessaire"""
        
        if prob_7j >= 70:
            self._creer_ou_mettre_a_jour_alerte(
                niveau='critique',
                titre=f'RISQUE CRITIQUE - Machine {self.machine.numero}',
                message=f'Probabilité de panne dans les 7 jours: {prob_7j:.1f}%. '
                       f'Facteurs: {", ".join(self.facteurs_risque[:3])}',
                probabilite_panne=Decimal(str(prob_7j)),
                delai_estime_jours=7,
                confiance_prediction=Decimal('85.0'),
                action_recommandee='Arrêt immédiat pour maintenance préventive',
                priorite=10
            )
        
        elif prob_7j >= 40:
            self._creer_ou_mettre_a_jour_alerte(
                niveau='urgent',
                titre=f'ATTENTION - Machine {self.machine.numero}',
                message=f'Probabilité de panne dans les 7 jours: {prob_7j:.1f}%. '
                       f'Intervention recommandée rapidement.',
                probabilite_panne=Decimal(str(prob_7j)),
                delai_estime_jours=7,
                confiance_prediction=Decimal('75.0'),
                action_recommandee='Planifier maintenance dans les 48h',
                priorite=7
            )
        
        if self.machine.maintenance_requise():
            jours_retard = self.machine.jours_depuis_derniere_maintenance() - self.machine.frequence_maintenance_jours
            self._creer_ou_mettre_a_jour_alerte(
                niveau='attention',
                titre=f'Maintenance requise - Machine {self.machine.numero}',
                message=f'Maintenance en retard de {jours_retard} jours',
                probabilite_panne=Decimal(str(prob_30j)),
                delai_estime_jours=30,
                confiance_prediction=Decimal('90.0'),
                action_recommandee='Planifier maintenance préventive',
                priorite=5
            )
        
        if self.anomalies:
            self._creer_ou_mettre_a_jour_alerte(
                niveau='urgent',
                titre=f'Anomalie détectée - Machine {self.machine.numero}',
                message=f'Anomalies: {", ".join(self.anomalies)}',
                probabilite_panne=Decimal(str(prob_7j)),
                delai_estime_jours=3,
                confiance_prediction=Decimal('80.0'),
                action_recommandee='Inspection immédiate de la machine',
                priorite=8,
                donnees_analyse={'anomalies': self.anomalies}
            )
    
    def _creer_ou_mettre_a_jour_alerte(self, niveau, titre, message, probabilite_panne, 
                                         delai_estime_jours, confiance_prediction, 
                                         action_recommandee, priorite, donnees_analyse=None):
        """Crée ou met à jour une alerte pour éviter les doublons"""
        alerte_existante = AlerteIA.objects.filter(
            machine=self.machine,
            niveau=niveau,
            statut__in=['nouvelle', 'vue', 'en_traitement']
        ).first()
        
        if alerte_existante:
            alerte_existante.titre = titre
            alerte_existante.message = message
            alerte_existante.probabilite_panne = probabilite_panne
            alerte_existante.delai_estime_jours = delai_estime_jours
            alerte_existante.confiance_prediction = confiance_prediction
            alerte_existante.action_recommandee = action_recommandee
            alerte_existante.priorite = priorite
            alerte_existante.date_creation = timezone.now()
            if donnees_analyse:
                alerte_existante.donnees_analyse = donnees_analyse
                alerte_existante.save()
        else:
            AlerteIA.objects.create(
                machine=self.machine,
                niveau=niveau,
                titre=titre,
                message=message,
                probabilite_panne=probabilite_panne,
                delai_estime_jours=delai_estime_jours,
                confiance_prediction=confiance_prediction,
                action_recommandee=action_recommandee,
                priorite=priorite,
                donnees_analyse=donnees_analyse or {}
            )
    
    def _niveau_risque(self, probabilite):
        """Détermine le niveau de risque"""
        if probabilite >= 70:
            return 'critique'
        elif probabilite >= 40:
            return 'élevé'
        elif probabilite >= 20:
            return 'moyen'
        else:
            return 'faible'


# ========================================
# Fonctions principales d'analyse
# ========================================

def analyser_toutes_machines():
    """
    Analyse toutes les machines actives
    À exécuter périodiquement (ex: toutes les heures)
    """
    machines = Machine.objects.filter(etat__in=['actif', 'maintenance'])
    resultats = []
    
    for machine in machines:
        moteur = MoteurPredictionPannes(machine)
        resultat = moteur.analyser_machine()
        resultats.append({
            'machine': machine.numero,
            'section': machine.section,
            'resultat': resultat
        })
    
    return resultats


def analyser_machine_specifique(machine_id):
    """Analyse une machine spécifique"""
    try:
        machine = Machine.objects.get(id=machine_id)
        moteur = MoteurPredictionPannes(machine)
        return moteur.analyser_machine()
    except Machine.DoesNotExist:
        return None


# ========================================
# Fonctions utilitaires
# ========================================

def obtenir_machines_a_risque(seuil_probabilite=40):
    """Retourne les machines avec risque de panne élevé"""
    return Machine.objects.filter(
        probabilite_panne_7_jours__gte=seuil_probabilite,
        etat='actif'
    ).order_by('-probabilite_panne_7_jours')


def obtenir_alertes_actives():
    """Retourne toutes les alertes IA actives"""
    return AlerteIA.objects.filter(
        statut__in=['nouvelle', 'vue', 'en_traitement']
    ).select_related('machine').order_by('-priorite', '-date_creation')


def statistiques_parc_machines():
    """Retourne des statistiques sur l'ensemble du parc machines"""
    machines = Machine.objects.filter(etat__in=['actif', 'maintenance'])
    
    if not machines.exists():
        return None
    
    return {
        'nombre_total': machines.count(),
        'score_sante_moyen': machines.aggregate(avg=Avg('score_sante_global'))['avg'] or 0,
        'machines_risque_critique': machines.filter(probabilite_panne_7_jours__gte=70).count(),
        'machines_risque_eleve': machines.filter(
            probabilite_panne_7_jours__gte=40,
            probabilite_panne_7_jours__lt=70
        ).count(),
        'machines_maintenance_requise': machines.filter(
            heures_depuis_derniere_maintenance__gte=F('frequence_maintenance_jours') * 24
        ).count(),
        'anomalies_detectees': machines.filter(anomalie_detectee=True).count(),
    }


# ========================================
# NOUVELLES FONCTIONS - Analyse Zone et Production
# ========================================

def analyser_zone_complete(zone_id):
    """
    NOUVEAU : Analyse complète d'une zone d'extrusion
    Retourne un rapport détaillé sur toutes les machines de la zone
    """
    try:
        zone = ZoneExtrusion.objects.get(id=zone_id)
    except ZoneExtrusion.DoesNotExist:
        return None
    
    machines_zone = Machine.objects.filter(
        zone_extrusion=zone,
        etat__in=['actif', 'maintenance']
    )
    
    if not machines_zone.exists():
        return None
    
    # Analyser chaque machine
    analyses_machines = []
    for machine in machines_zone:
        moteur = MoteurPredictionPannes(machine)
        analyse = moteur.analyser_machine()
        analyses_machines.append({
            'machine': machine,
            'analyse': analyse
        })
    
    # Statistiques de zone
    periode = timezone.now().date() - timedelta(days=7)
    productions_zone = ProductionExtrusion.objects.filter(
        zone=zone,
        date_production__gte=periode
    )
    
    stats_zone = {
        'zone': zone,
        'nombre_machines': machines_zone.count(),
        'machines_a_risque': machines_zone.filter(
            probabilite_panne_7_jours__gte=40
        ).count(),
        'score_sante_moyen': machines_zone.aggregate(
            avg=Avg('score_sante_global')
        )['avg'] or 0,
        'rendement_moyen_7j': productions_zone.aggregate(
            avg=Avg('rendement_pourcentage')
        )['avg'] or 0,
        'production_totale_7j': productions_zone.aggregate(
            total=Sum('total_production_kg')
        )['total'] or 0,
        'taux_dechets_7j': 0,
        'analyses_machines': analyses_machines,
    }
    
    # Calcul taux déchets zone
    totaux = productions_zone.aggregate(
        prod=Sum('total_production_kg'),
        dechets=Sum('dechets_kg')
    )
    if totaux['prod'] and totaux['prod'] > 0:
        stats_zone['taux_dechets_7j'] = round(
            (float(totaux['dechets'] or 0) / float(totaux['prod'])) * 100, 2
        )
    
    return stats_zone


def obtenir_rapport_production_machines():
    """
    NOUVEAU : Génère un rapport corrélant production et état des machines
    pour toutes les sections
    """
    periode = timezone.now().date() - timedelta(days=7)
    rapport = {}
    
    # Extrusion
    zones_extrusion = ZoneExtrusion.objects.filter(active=True)
    rapport['extrusion'] = []
    
    for zone in zones_extrusion:
        machines = Machine.objects.filter(
            zone_extrusion=zone,
            etat='actif'
        )
        
        productions = ProductionExtrusion.objects.filter(
            zone=zone,
            date_production__gte=periode
        )
        
        if machines.exists() and productions.exists():
            rapport['extrusion'].append({
                'zone': zone.nom,
                'machines_actives': machines.count(),
                'machines_a_risque': machines.filter(
                    probabilite_panne_7_jours__gte=40
                ).count(),
                'rendement_moyen': productions.aggregate(
                    avg=Avg('rendement_pourcentage')
                )['avg'] or 0,
                'production_kg': productions.aggregate(
                    total=Sum('total_production_kg')
                )['total'] or 0,
            })
    
    # Imprimerie
    machines_imprimerie = Machine.objects.filter(
        section='imprimerie',
        etat='actif'
    )
    productions_imprimerie = ProductionImprimerie.objects.filter(
        date_production__gte=periode
    )
    
    rapport['imprimerie'] = {
        'machines_actives': machines_imprimerie.count(),
        'machines_a_risque': machines_imprimerie.filter(
            probabilite_panne_7_jours__gte=40
        ).count(),
        'production_kg': productions_imprimerie.aggregate(
            total=Sum('total_production_kg')
        )['total'] or 0,
    }
    
    # Soudure
    machines_soudure = Machine.objects.filter(
        section='soudure',
        etat='actif'
    )
    productions_soudure = ProductionSoudure.objects.filter(
        date_production__gte=periode
    )
    
    rapport['soudure'] = {
        'machines_actives': machines_soudure.count(),
        'machines_a_risque': machines_soudure.filter(
            probabilite_panne_7_jours__gte=40
        ).count(),
        'production_kg': productions_soudure.aggregate(
            total=Sum('total_production_kg')
        )['total'] or 0,
    }
    
    # Recyclage
    machines_recyclage = Machine.objects.filter(
        section='recyclage',
        etat='actif'
    )
    productions_recyclage = ProductionRecyclage.objects.filter(
        date_production__gte=periode
    )
    
    rapport['recyclage'] = {
        'moulinex_actifs': machines_recyclage.count(),
        'moulinex_a_risque': machines_recyclage.filter(
            probabilite_panne_7_jours__gte=40
        ).count(),
        'production_kg': productions_recyclage.aggregate(
            total=Sum('total_production_kg')
        )['total'] or 0,
    }
    
    return rapport


# ========================================
# Simulation de données capteurs
# ========================================

def simuler_donnees_capteurs(machine, temperature=None, consommation=None):
    """
    Simule la mise à jour des données capteurs
    En production, ces données viendraient de vrais capteurs IoT
    """
    import random
    
    if temperature is None:
        base = float(machine.temperature_nominale)
        variation = random.uniform(-5, 15)
        temperature = base + variation
    
    if consommation is None:
        base = float(machine.consommation_electrique_nominale)
        variation = random.uniform(-10, 25)
        consommation = base * (1 + variation/100)
    
    machine.temperature_actuelle = Decimal(str(round(temperature, 2)))
    machine.consommation_electrique_kwh = Decimal(str(round(consommation, 2)))
    machine.save()
    
    return analyser_machine_specifique(machine.id)


def incrementer_heures_fonctionnement(machine, heures):
    """Incrémente les heures de fonctionnement d'une machine"""
    machine.heures_fonctionnement_totales += Decimal(str(heures))
    machine.heures_depuis_derniere_maintenance += Decimal(str(heures))
    machine.save()


def enregistrer_maintenance(machine, description, technicien, pieces_remplacees=''):
    """Enregistre une maintenance effectuée"""
    # Créer l'historique
    HistoriqueMachine.objects.create(
        machine=machine,
        type_evenement='maintenance',
        temperature=machine.temperature_actuelle,
        consommation_kwh=machine.consommation_electrique_kwh,
        heures_fonctionnement=machine.heures_fonctionnement_totales,
        description=description,
        technicien=technicien,
        pieces_remplacees=pieces_remplacees
    )
    
    # Mettre à jour la machine
    machine.derniere_maintenance = timezone.now().date()
    machine.heures_depuis_derniere_maintenance = Decimal('0')
    machine.prochaine_maintenance_prevue = (
        timezone.now().date() + timedelta(days=machine.frequence_maintenance_jours)
    )
    machine.save()
    
    return analyser_machine_specifique(machine.id)


def enregistrer_panne(machine, description, duree_arret, technicien='', cout=None):
    """Enregistre une panne"""
    # Créer l'historique
    HistoriqueMachine.objects.create(
        machine=machine,
        type_evenement='panne',
        temperature=machine.temperature_actuelle,
        consommation_kwh=machine.consommation_electrique_kwh,
        heures_fonctionnement=machine.heures_fonctionnement_totales,
        description=description,
        duree_arret=Decimal(str(duree_arret)),
        cout_intervention=Decimal(str(cout)) if cout else None,
        technicien=technicien
    )
    
    # Mettre à jour les compteurs de pannes
    machine.nombre_pannes_totales += 1
    machine.nombre_pannes_1_dernier_mois += 1
    machine.nombre_pannes_6_derniers_mois += 1
    machine.date_derniere_panne = timezone.now()
    machine.etat = 'panne'
    machine.save()
    
    return analyser_machine_specifique(machine.id)