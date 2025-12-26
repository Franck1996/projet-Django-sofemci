from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

class Machine(models.Model):
    """Machines avec données pour prédiction IA"""
    TYPES_MACHINE = [
        ('extrudeuse', 'Extrudeuse'),
        ('refroidisseur', 'Refroidisseur'),
        ('enrouleur', 'Enrouleur'),
        ('imprimante', 'Imprimante'),
        ('soudeuse', 'Soudeuse'),
        ('moulinex', 'Moulinex'),
    ]
    
    ETATS = [
        ('actif', 'Active'),
        ('maintenance', 'Maintenance'),
        ('arret', 'Arrêtée'),
        ('panne', 'En Panne'),
    ]
    
    SECTIONS = [
        ('extrusion', 'Extrusion'),
        ('imprimerie', 'Imprimerie'),
        ('soudure', 'Soudure'),
        ('recyclage', 'Recyclage'),
    ]
    
    PROVENANCE_CHOICES = [
        ('chine', 'Chine'),
        ('allemagne', 'Allemagne'),
        ('italie', 'Italie'),
        ('france', 'France'),
        ('usa', 'États-Unis'),
        ('japon', 'Japon'),
        ('autre', 'Autre'),
    ]
    
    # Champs de base
    numero = models.CharField(max_length=10)
    type_machine = models.CharField(max_length=20, choices=TYPES_MACHINE)
    section = models.CharField(max_length=20, choices=SECTIONS)
    zone_extrusion = models.ForeignKey('ZoneExtrusion', on_delete=models.CASCADE, null=True, blank=True)
    etat = models.CharField(max_length=15, choices=ETATS, default='actif')
    date_installation = models.DateField(null=True, blank=True)
    derniere_maintenance = models.DateField(null=True, blank=True)
    capacite_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)
    
    # NOUVEAUX CHAMPS AJOUTÉS
    provenance = models.CharField(
        max_length=20,
        choices=PROVENANCE_CHOICES,
        default='autre',
        verbose_name="Provenance",
        help_text="Pays d'origine de la machine"
    )
    est_nouvelle = models.BooleanField(
        default=True,
        verbose_name="Machine neuve",
        help_text="Indique si la machine était neuve lors de l'installation"
    )
    
    # Champs pour IA - Heures de fonctionnement
    heures_fonctionnement_totales = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Heures de fonctionnement totales",
        help_text="Nombre total d'heures depuis installation"
    )
    heures_depuis_derniere_maintenance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Heures depuis dernière maintenance"
    )
    
    # Planification maintenance
    prochaine_maintenance_prevue = models.DateField(
        null=True, 
        blank=True,
        verbose_name="Prochaine maintenance prévue"
    )
    frequence_maintenance_jours = models.IntegerField(
        default=90,
        verbose_name="Fréquence maintenance (jours)",
        help_text="Intervalle recommandé entre maintenances"
    )
    
    # Historique pannes
    nombre_pannes_totales = models.IntegerField(
        default=0,
        verbose_name="Nombre de pannes totales"
    )
    nombre_pannes_6_derniers_mois = models.IntegerField(
        default=0,
        verbose_name="Pannes - 6 derniers mois"
    )
    nombre_pannes_1_dernier_mois = models.IntegerField(
        default=0,
        verbose_name="Pannes - dernier mois"
    )
    date_derniere_panne = models.DateTimeField(
        null=True, 
        blank=True,
        verbose_name="Date dernière panne"
    )
    duree_moyenne_reparation = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name="Durée moyenne réparation (heures)"
    )
    
    # Consommation électrique
    consommation_electrique_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Consommation électrique actuelle (kWh)",
        help_text="Consommation moyenne par heure"
    )
    consommation_electrique_nominale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Consommation nominale (kWh)",
        help_text="Consommation normale à pleine charge"
    )
    
    # Température
    temperature_actuelle = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Température actuelle (°C)"
    )
    temperature_nominale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Température nominale (°C)",
        help_text="Température normale de fonctionnement"
    )
    temperature_max_autorisee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Température max autorisée (°C)"
    )
    
    # Scores de santé (calculés par IA)
    score_sante_global = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100,
        verbose_name="Score santé global (%)",
        help_text="Score calculé par l'IA (0-100)"
    )
    probabilite_panne_7_jours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Probabilité panne 7 jours (%)",
        help_text="Risque de panne dans les 7 prochains jours"
    )
    probabilite_panne_30_jours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Probabilité panne 30 jours (%)"
    )
    
    # Anomalies détectées
    anomalie_detectee = models.BooleanField(
        default=False,
        verbose_name="Anomalie détectée"
    )
    type_anomalie = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Type d'anomalie",
        help_text="Ex: Surchauffe, Surconsommation, Vibrations"
    )
    date_derniere_analyse_ia = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Dernière analyse IA"
    )
    
    # Métadonnées
    derniere_mise_a_jour_donnees = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour données"
    )
    
    class Meta:
        unique_together = ['numero', 'section']
        ordering = ['section', 'numero']
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
    
    def __str__(self):
        return f"{self.section.title()} - Machine {self.numero}"
    
    def calculer_age_machine(self):
        """Retourne l'âge de la machine en jours"""
        if self.date_installation:
            return (timezone.now().date() - self.date_installation).days
        return 0
    
    def jours_depuis_derniere_maintenance(self):
        """Retourne le nombre de jours depuis la dernière maintenance"""
        if self.derniere_maintenance:
            return (timezone.now().date() - self.derniere_maintenance).days
        return self.calculer_age_machine()
    
    def maintenance_requise(self):
        """Vérifie si une maintenance est requise"""
        jours = self.jours_depuis_derniere_maintenance()
        return jours >= self.frequence_maintenance_jours
    
    def jours_avant_prochaine_maintenance(self):
        """Retourne le nombre de jours avant la prochaine maintenance"""
        if self.prochaine_maintenance_prevue:
            delta = (self.prochaine_maintenance_prevue - timezone.now().date()).days
            return max(0, delta)
        return 0
    
    def taux_utilisation(self):
        """Calcule le taux d'utilisation de la machine"""
        age_jours = self.calculer_age_machine()
        if age_jours > 0:
            heures_potentielles = age_jours * 24
            return (float(self.heures_fonctionnement_totales) / heures_potentielles) * 100
        return 0
    
    def variation_consommation(self):
        """Calcule la variation de consommation par rapport à la normale"""
        if self.consommation_electrique_nominale > 0:
            variation = ((self.consommation_electrique_kwh - self.consommation_electrique_nominale) 
                        / self.consommation_electrique_nominale) * 100
            return round(variation, 2)
        return 0
    
    def variation_temperature(self):
        """Calcule la variation de température par rapport à la normale"""
        if self.temperature_actuelle and self.temperature_nominale > 0:
            variation = ((self.temperature_actuelle - self.temperature_nominale) 
                        / self.temperature_nominale) * 100
            return round(variation, 2)
        return 0
    
    def est_en_surchauffe(self):
        try:
            if not self.temperature_actuelle or not self.temperature_max_autorisee:
                return False
            seuil_surchauffe = Decimal('0.9')
            temperature_max = Decimal(str(self.temperature_max_autorisee))
            temperature_actuelle = Decimal(str(self.temperature_actuelle))
            return temperature_actuelle >= (temperature_max * seuil_surchauffe)
        except (TypeError, ValueError, AttributeError):
            return False
    
    def pourcentage_utilisation_temperature(self):
        """Calcule le pourcentage d'utilisation de la température"""
        try:
            if not self.temperature_nominale or self.temperature_nominale == 0:
                return 0
            temp_actuelle = Decimal(str(self.temperature_actuelle)) if self.temperature_actuelle else Decimal('0')
            temp_nominale = Decimal(str(self.temperature_nominale))
            pourcentage = (temp_actuelle / temp_nominale) * Decimal('100')
            return min(pourcentage, Decimal('100'))
        except (TypeError, ValueError, AttributeError, ZeroDivisionError):
            return 0
    
    def risque_surchauffe(self):
        """Calcule le risque de surchauffe en pourcentage"""
        try:
            if not self.temperature_max_autorisee or self.temperature_max_autorisee == 0:
                return 0
            temp_actuelle = Decimal(str(self.temperature_actuelle)) if self.temperature_actuelle else Decimal('0')
            temp_max = Decimal(str(self.temperature_max_autorisee))
            if temp_actuelle >= temp_max:
                return Decimal('100')
            risque = (temp_actuelle / temp_max) * Decimal('100')
            return min(risque, Decimal('100'))
        except (TypeError, ValueError, AttributeError, ZeroDivisionError):
            return 0
    
    def consommation_actuelle_kwh(self):
        """Calcule la consommation électrique actuelle"""
        try:
            if not self.consommation_electrique_kwh:
                return Decimal('0')
            return Decimal(str(self.consommation_electrique_kwh))
        except (TypeError, ValueError):
            return Decimal('0')
    
    def est_en_surconsommation(self):
        """Vérifie si la machine est en surconsommation"""
        variation = self.variation_consommation()
        return variation > 20
    
    def niveau_risque(self):
        """Retourne le niveau de risque (faible, moyen, élevé, critique)"""
        if self.probabilite_panne_7_jours >= 70:
            return 'critique'
        elif self.probabilite_panne_7_jours >= 40:
            return 'élevé'
        elif self.probabilite_panne_7_jours >= 20:
            return 'moyen'
        else:
            return 'faible'
    
    def facteurs_risque(self):
        """Retourne la liste des facteurs de risque détectés"""
        facteurs = []
        
        if self.maintenance_requise():
            facteurs.append('Maintenance en retard')
        
        if self.est_en_surchauffe():
            facteurs.append('Surchauffe détectée')
        
        if self.est_en_surconsommation():
            facteurs.append('Surconsommation électrique')
        
        if self.nombre_pannes_1_dernier_mois > 0:
            facteurs.append(f'{self.nombre_pannes_1_dernier_mois} panne(s) récente(s)')
        
        if self.heures_depuis_derniere_maintenance > self.frequence_maintenance_jours * 24:
            facteurs.append('Heures de fonctionnement élevées')
        
        if self.anomalie_detectee:
            facteurs.append(f'Anomalie: {self.type_anomalie}')
        
        return facteurs

class HistoriqueMachine(models.Model):
    """Historique des événements et mesures pour chaque machine"""
    
    TYPE_EVENEMENT = [
        ('maintenance', 'Maintenance'),
        ('panne', 'Panne'),
        ('reparation', 'Réparation'),
        ('mesure', 'Mesure'),
        ('alerte', 'Alerte'),
    ]
    
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='historique')
    date_evenement = models.DateTimeField(default=timezone.now)
    type_evenement = models.CharField(max_length=20, choices=TYPE_EVENEMENT)
    
    # Mesures au moment de l'événement
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    consommation_kwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    heures_fonctionnement = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Détails
    description = models.TextField(blank=True)
    duree_arret = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Durée arrêt (heures)"
    )
    cout_intervention = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Coût (FCFA)"
    )
    
    # Technicien
    technicien = models.CharField(max_length=100, blank=True)
    pieces_remplacees = models.TextField(blank=True, help_text="Liste des pièces")
    
    cree_par = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-date_evenement']
        verbose_name = "Historique Machine"
        verbose_name_plural = "Historiques Machines"
    
    def __str__(self):
        return f"{self.machine.numero} - {self.get_type_evenement_display()} - {self.date_evenement.strftime('%d/%m/%Y')}"