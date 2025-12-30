from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

# ==========================================
# MODÈLE UTILISATEUR PERSONNALISÉ
# ==========================================

class CustomUser(AbstractUser):
    """Utilisateurs avec rôles spécifiques à l'usine"""
    ROLES = [
        ('admin', 'Administrateur'),
        ('chef_extrusion', 'Chef Zone Extrusion'),
        ('chef_soudure', 'Chef Zone Soudure'),
        ('chef_imprimerie', 'Chef Zone Imprimerie'),
        ('chef_recyclage', 'Chef Zone Recyclage'),
        ('superviseur', 'Superviseur'),
        ('direction', 'Direction'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLES, default='superviseur')
    telephone = models.CharField(max_length=20, blank=True)
    date_embauche = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

# ==========================================
# MODÈLES DE BASE (ÉQUIPES, ZONES, MACHINES)
# ==========================================

class Equipe(models.Model):
    """Équipes de travail A, B, C"""
    EQUIPES_CHOICES = [
        ('A', 'Équipe A (06h00 - 14h00)'),
        ('B', 'Équipe B (14h00 - 22h00)'),
        ('C', 'Équipe C (22h00 - 06h00)'),
    ]
    
    nom = models.CharField(max_length=1, choices=EQUIPES_CHOICES, unique=True)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    chef_equipe = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Équipe"
        verbose_name_plural = "Équipes"
    
    def __str__(self):
        return self.get_nom_display()

class ZoneExtrusion(models.Model):
    """Zones d'extrusion (1 à 5)"""
    numero = models.IntegerField(unique=True, validators=[MinValueValidator(1)])
    nom = models.CharField(max_length=50)
    nombre_machines_max = models.IntegerField(default=4)
    chef_zone = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Zone Extrusion"
        verbose_name_plural = "Zones Extrusion"
        ordering = ['numero']
    
    def __str__(self):
        return f"Zone {self.numero} - {self.nom}"

# sofemci/models.py - Section Machine enrichie pour IA

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
    
    # Champs existants
    numero = models.CharField(max_length=10)
    type_machine = models.CharField(max_length=20, choices=TYPES_MACHINE)
    section = models.CharField(max_length=20, choices=SECTIONS)
    zone_extrusion = models.ForeignKey(ZoneExtrusion, on_delete=models.CASCADE, null=True, blank=True)
    etat = models.CharField(max_length=15, choices=ETATS, default='actif')
    date_installation = models.DateField(null=True, blank=True)
    derniere_maintenance = models.DateField(null=True, blank=True)
    capacite_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)
    
    # ========================================
    # NOUVEAUX CHAMPS POUR IA
    # ========================================
    
    # Heures de fonctionnement
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
    
    # ========================================
    # MÉTHODES POUR CALCULS IA
    # ========================================
    
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
        """Vérifie si la machine est en surchauffe"""
        try:
            # Conversion en Decimal pour éviter l'erreur
            seuil_surchauffe = Decimal('0.9')  # 90% de la température max
            
            # Calcul avec des Decimals
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
                
            # Conversion en Decimal
            temp_actuelle = Decimal(str(self.temperature_actuelle))
            temp_nominale = Decimal(str(self.temperature_nominale))
            
            pourcentage = (temp_actuelle / temp_nominale) * Decimal('100')
            return min(pourcentage, Decimal('100'))  # Limite à 100%
        except (TypeError, ValueError, AttributeError, ZeroDivisionError):
            return 0
    
    def risque_surchauffe(self):
        """Calcule le risque de surchauffe en pourcentage"""
        try:
            if not self.temperature_max_autorisee or self.temperature_max_autorisee == 0:
                return 0
                
            # Conversion en Decimal
            temp_actuelle = Decimal(str(self.temperature_actuelle))
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

        """Vérifie si la machine est en surchauffe"""
        if self.temperature_actuelle and self.temperature_max_autorisee > 0:
            return self.temperature_actuelle >= self.temperature_max_autorisee * 0.95  # 95% du max
        return False
    
    def est_en_surconsommation(self):
        """Vérifie si la machine est en surconsommation"""
        variation = self.variation_consommation()
        return variation > 20  # Plus de 20% au-dessus de la normale
    
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


# ========================================
# NOUVEAU MODÈLE: Historique Machine
# ========================================

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
    
    cree_par = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-date_evenement']
        verbose_name = "Historique Machine"
        verbose_name_plural = "Historiques Machines"
    
    def __str__(self):
        return f"{self.machine.numero} - {self.get_type_evenement_display()} - {self.date_evenement.strftime('%d/%m/%Y')}"


# ========================================
# NOUVEAU MODÈLE: Alerte IA
# ========================================

class AlerteIA(models.Model):
    """Alertes générées automatiquement par l'IA"""
    
    NIVEAU_ALERTE = [
        ('info', 'Information'),
        ('attention', 'Attention'),
        ('urgent', 'Urgent'),
        ('critique', 'Critique'),
    ]
    
    STATUT = [
        ('nouvelle', 'Nouvelle'),
        ('vue', 'Vue'),
        ('en_traitement', 'En traitement'),
        ('resolue', 'Résolue'),
        ('ignoree', 'Ignorée'),
    ]
    
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='alertes_ia')
    date_creation = models.DateTimeField(auto_now_add=True)
    niveau = models.CharField(max_length=20, choices=NIVEAU_ALERTE)
    statut = models.CharField(max_length=20, choices=STATUT, default='nouvelle')
    
    titre = models.CharField(max_length=200)
    message = models.TextField()
    
    # Prédictions IA
    probabilite_panne = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Probabilité panne (%)"
    )
    delai_estime_jours = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Délai estimé (jours)"
    )
    confiance_prediction = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Confiance prédiction (%)"
    )
    
    # Recommandations
    action_recommandee = models.TextField(
        blank=True,
        verbose_name="Action recommandée"
    )
    priorite = models.IntegerField(
        default=0,
        verbose_name="Priorité (0-10)"
    )
    
    # Traitement
    traite_par = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='alertes_ia_traitees'
    )
    date_traitement = models.DateTimeField(null=True, blank=True)
    commentaire_traitement = models.TextField(blank=True)
    
    # Métadonnées IA
    modele_ia_version = models.CharField(max_length=50, default='v1.0')
    donnees_analyse = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Données d'analyse JSON"
    )
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Alerte IA"
        verbose_name_plural = "Alertes IA"
    
    def __str__(self):
        return f"{self.machine.numero} - {self.titre} ({self.get_niveau_display()})"
    
    def marquer_comme_vue(self, user=None):
        """Marque l'alerte comme vue"""
        self.statut = 'vue'
        self.save()
    
    def prendre_en_charge(self, user):
        """Un utilisateur prend en charge l'alerte"""
        self.statut = 'en_traitement'
        self.traite_par = user
        self.date_traitement = timezone.now()
        self.save()
    
    def resoudre(self, commentaire=''):
        """Marque l'alerte comme résolue"""
        self.statut = 'resolue'
        self.commentaire_traitement = commentaire
        self.save()
    """Machines dans toutes les sections"""
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
    
    numero = models.CharField(max_length=10)
    type_machine = models.CharField(max_length=20, choices=TYPES_MACHINE)
    section = models.CharField(max_length=20, choices=SECTIONS)
    zone_extrusion = models.ForeignKey(ZoneExtrusion, on_delete=models.CASCADE, null=True, blank=True)
    etat = models.CharField(max_length=15, choices=ETATS, default='actif')
    date_installation = models.DateField(null=True, blank=True)
    derniere_maintenance = models.DateField(null=True, blank=True)
    capacite_horaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observations = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['numero', 'section']
        ordering = ['section', 'numero']
    
    def __str__(self):
        return f"{self.section.title()} - Machine {self.numero}"

# ==========================================
# MODÈLES DE PRODUCTION PAR SECTION
# ==========================================


class ProductionExtrusion(models.Model):
    """Production journalière par zone d'extrusion - EXACTEMENT comme dans vos maquettes"""
    
    # Informations de base
    date_production = models.DateField()
    zone = models.ForeignKey(ZoneExtrusion, on_delete=models.CASCADE)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    chef_zone = models.CharField(max_length=100, help_text="Nom du chef de zone")
    
    # Ressources utilisées
    matiere_premiere_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Matière première utilisée (kg)"
    )
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre moyen de machines actives"
    )
    nombre_machinistes = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre moyen de machinistes"
    )
    
    # Production
    nombre_bobines_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Nombre de bobines produites (kg)"
    )
    production_finis_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production produits finis (kg)"
    )
    production_semi_finis_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production produits semi-finis (kg)"
    )
    dechets_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )
    
    # Champs calculés automatiquement
    total_production_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rendement_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    taux_dechet_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    production_par_machine = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Observations et métadonnées
    observations = models.TextField(blank=True, verbose_name="Observations du jour")
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['date_production', 'zone', 'equipe']
        verbose_name = "Production Extrusion"
        verbose_name_plural = "Productions Extrusion"
        ordering = ['-date_production', 'zone']
    
    def save(self, *args, **kwargs):
        # Calculs automatiques EXACTEMENT comme dans vos maquettes
        self.total_production_kg = self.production_finis_kg + self.production_semi_finis_kg
        
        if self.matiere_premiere_kg > 0:
            self.rendement_pourcentage = (self.total_production_kg / self.matiere_premiere_kg) * 100
        
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (self.dechets_kg / (self.total_production_kg + self.dechets_kg)) * 100
        
        if self.nombre_machines_actives > 0:
            self.production_par_machine = self.total_production_kg / self.nombre_machines_actives
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.zone} - {self.date_production} - {self.equipe}"

class ProductionImprimerie(models.Model):
    """Production journalière section Imprimerie - EXACTEMENT comme dans vos maquettes"""
    
    # Informations de base
    date_production = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    
    # Ressources
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre moyen de machines actives"
    )
    
    # Production
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines produits finis (kg)"
    )
    production_bobines_semi_finies_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines semi-finis (kg)"
    )
    dechets_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )
    
    # Champs calculés
    total_production_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taux_dechet_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Métadonnées
    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['date_production']
        verbose_name = "Production Imprimerie"
        verbose_name_plural = "Productions Imprimerie"
        ordering = ['-date_production']
    
    def save(self, *args, **kwargs):
        # Calculs automatiques
        self.total_production_kg = self.production_bobines_finies_kg + self.production_bobines_semi_finies_kg
        
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (self.dechets_kg / (self.total_production_kg + self.dechets_kg)) * 100
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Imprimerie - {self.date_production}"

class ProductionSoudure(models.Model):
    """Production journalière section Soudure - EXACTEMENT comme dans vos maquettes"""
    
    # Informations de base
    date_production = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    
    # Ressources
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre moyen de machines actives"
    )
    
    # Production standard
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines produits finis (kg)"
    )
    
    # Production spécifique soudure
    production_bretelles_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production BRETELLE (EMBALLAGE) (kg)"
    )
    production_rema_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production REMA-PLASTIQUE (kg)"
    )
    production_batta_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production BATTA (kg)"
    )
    
    # NOUVEAU : Sac d'emballage imprimé
    production_sac_emballage_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0'),
        verbose_name="Production SAC D'EMBALLAGE IMPRIMÉ (kg)"
    )
    
    # Déchets
    dechets_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )
    
    # Champs calculés
    total_production_specifique_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Total production spécifique (Bretelle+Rema+Batta+Sac)"
    )
    total_production_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Total production globale"
    )
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Taux de déchets (%)"
    )
    
    # Métadonnées
    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['date_production']
        verbose_name = "Production Soudure"
        verbose_name_plural = "Productions Soudure"
        ordering = ['-date_production']
    
    def save(self, *args, **kwargs):
        # Calculs automatiques EXACTEMENT comme dans vos maquettes
        # MISE À JOUR : Inclut maintenant les sacs d'emballage
        self.total_production_specifique_kg = (
            self.production_bretelles_kg + 
            self.production_rema_kg + 
            self.production_batta_kg +
            self.production_sac_emballage_kg  # NOUVEAU
        )
        
        self.total_production_kg = (
            self.production_bobines_finies_kg + 
            self.total_production_specifique_kg
        )
        
        # Calcul taux de déchets
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (
                self.dechets_kg / (self.total_production_kg + self.dechets_kg)
            ) * 100
        else:
            self.taux_dechet_pourcentage = Decimal('0')
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Soudure - {self.date_production}"
    """Production journalière section Soudure - EXACTEMENT comme dans vos maquettes"""
    
    # Informations de base
    date_production = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    
    # Ressources
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre moyen de machines actives"
    )
    
    # Production standard
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines produits finis (kg)"
    )
    
    # Production spécifique soudure
    production_bretelles_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production BRETELLE (EMBALLAGE) (kg)"
    )
    production_rema_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production REMA-PLASTIQUE (kg)"
    )
    production_batta_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production BATTA (kg)"
    )
    
    # Déchets
    dechets_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )
    
    # Champs calculés
    total_production_specifique_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_production_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taux_dechet_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Métadonnées
    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['date_production']
        verbose_name = "Production Soudure"
        verbose_name_plural = "Productions Soudure"
        ordering = ['-date_production']
    
    def save(self, *args, **kwargs):
        # Calculs automatiques EXACTEMENT comme dans vos maquettes
        self.total_production_specifique_kg = (
            self.production_bretelles_kg + 
            self.production_rema_kg + 
            self.production_batta_kg
        )
        self.total_production_kg = self.production_bobines_finies_kg + self.total_production_specifique_kg
        
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (self.dechets_kg / (self.total_production_kg + self.dechets_kg)) * 100
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Soudure - {self.date_production}"

class ProductionRecyclage(models.Model):
    """Production journalière section Recyclage - EXACTEMENT comme dans vos maquettes"""
    
    # Informations de base
    date_production = models.DateField()
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE, verbose_name="Équipe qui a travaillé")
    
    # Ressources
    nombre_moulinex = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre de moulinex"
    )
    
    # Production
    production_broyage_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production journalière de broyage (kg)"
    )
    production_bache_noir_kg = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production de bâche noire (kg)"
    )
    
    # Champs calculés
    total_production_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    production_par_moulinex = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    taux_transformation_pourcentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Métadonnées
    observations = models.TextField(blank=True, verbose_name="Observations")
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['date_production', 'equipe']
        verbose_name = "Production Recyclage"
        verbose_name_plural = "Productions Recyclage"
        ordering = ['-date_production']
    
    def save(self, *args, **kwargs):
        # Calculs automatiques EXACTEMENT comme dans vos maquettes
        self.total_production_kg = self.production_broyage_kg + self.production_bache_noir_kg
        
        if self.nombre_moulinex > 0:
            self.production_par_moulinex = self.total_production_kg / self.nombre_moulinex
        
        if self.production_broyage_kg > 0:
            self.taux_transformation_pourcentage = (self.production_bache_noir_kg / self.production_broyage_kg) * 100
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Recyclage - {self.date_production} - {self.equipe}"

# ==========================================
# MODÈLES SYSTÈME (ALERTES, RAPPORTS)
# ==========================================

class Alerte(models.Model):
    """Système d'alertes pour la production"""
    TYPES_ALERTE = [
        ('critique', 'Critique'),
        ('important', 'Important'),
        ('info', 'Information'),
        ('maintenance', 'Maintenance'),
    ]
    
    STATUTS = [
        ('nouveau', 'Nouveau'),
        ('en_cours', 'En Cours'),
        ('resolu', 'Résolu'),
        ('ferme', 'Fermé'),
    ]
    
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type_alerte = models.CharField(max_length=15, choices=TYPES_ALERTE)
    statut = models.CharField(max_length=15, choices=STATUTS, default='nouveau')
    section = models.CharField(max_length=20)
    
    # Métadonnées
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    assigne_a = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='alertes_assignees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.get_type_alerte_display()} - {self.titre}"

class RapportMensuel(models.Model):
    """Rapports mensuels automatiques"""
    mois = models.DateField()  # Premier jour du mois
    
    # Totaux mensuels
    total_production_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total_extrusion_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total_imprimerie_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total_soudure_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total_recyclage_kg = models.DecimalField(max_digits=12, decimal_places=2)
    total_dechets_kg = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Métriques
    rendement_moyen = models.DecimalField(max_digits=5, decimal_places=2)
    taux_dechet_moyen = models.DecimalField(max_digits=5, decimal_places=2)
    nombre_jours_production = models.IntegerField()
    
    # Métadonnées
    genere_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_generation = models.DateTimeField(auto_now_add=True)
    fichier_pdf = models.FileField(upload_to='rapports/', null=True, blank=True)
    fichier_excel = models.FileField(upload_to='rapports/', null=True, blank=True)
    
    class Meta:
        unique_together = ['mois']
        ordering = ['-mois']
    
    def __str__(self):
        return f"Rapport {self.mois.strftime('%B %Y')}"


        # ============================================
# MODIFICATIONS POUR views.py
# ============================================

# Ajouter ces fonctions utilitaires dans views.py

def get_extrusion_details_jour(date):
    """Obtenir tous les détails de l'extrusion pour un jour donné"""
    
    productions = ProductionExtrusion.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'temps_travail_total': 0,
            'nombre_moyen_machinistes': 0,
            'matiere_premiere_total': 0,
            'production_finis': 0,
            'production_semi_finis': 0,
            'total_production': 0,
            'total_dechets': 0,
            'nombre_zones_actives': 0,
            'rendement_global': 0,
        }
    
    # Calculer le temps de travail total
    temps_total_minutes = 0
    for prod in productions:
        if prod.heure_debut and prod.heure_fin:
            debut = datetime.combine(date, prod.heure_debut)
            fin = datetime.combine(date, prod.heure_fin)
            # Gérer le cas où la fin est après minuit
            if fin < debut:
                fin += timedelta(days=1)
            temps_total_minutes += (fin - debut).total_seconds() / 60
    
    temps_heures = temps_total_minutes / 60
    
    # Aggrégations
    aggregats = productions.aggregate(
        matiere_premiere=Sum('matiere_premiere_kg'),
        prod_finis=Sum('production_finis_kg'),
        prod_semi_finis=Sum('production_semi_finis_kg'),
        total_prod=Sum('total_production_kg'),
        dechets=Sum('dechets_kg'),
        machinistes_total=Sum('nombre_machinistes'),
        count_productions=Count('id')
    )
    
    # Calcul nombre moyen de machinistes
    nombre_moyen_machinistes = (
        aggregats['machinistes_total'] / aggregats['count_productions']
    ) if aggregats['count_productions'] > 0 else 0
    
    # Calcul du rendement global
    rendement_global = 0
    if aggregats['matiere_premiere'] and aggregats['matiere_premiere'] > 0:
        rendement_global = (
            (aggregats['total_prod'] or 0) / aggregats['matiere_premiere'] * 100
        )
    
    # Nombre de zones actives
    zones_actives = productions.values('zone').distinct().count()
    
    return {
        'temps_travail_total': round(temps_heures, 1),
        'nombre_moyen_machinistes': round(nombre_moyen_machinistes, 0),
        'matiere_premiere_total': aggregats['matiere_premiere'] or 0,
        'production_finis': aggregats['prod_finis'] or 0,
        'production_semi_finis': aggregats['prod_semi_finis'] or 0,
        'total_production': aggregats['total_prod'] or 0,
        'total_dechets': aggregats['dechets'] or 0,
        'nombre_zones_actives': zones_actives,
        'rendement_global': round(rendement_global, 1),
    }

def get_imprimerie_details_jour(date):
    """Détails imprimerie du jour"""
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
        machines=Avg('nombre_machines'),
        bobines_finis=Sum('production_bobines_finis_kg'),
        bobines_semi_finis=Sum('production_bobines_semi_finis_kg'),
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

def get_soudure_details_jour(date):
    """Détails soudure du jour"""
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
        machines=Avg('nombre_machines'),
        bobines=Sum('production_bobines_finis_kg'),
        bretelles=Sum('production_bretelles_kg'),
        rema=Sum('production_rema_plastique_kg'),
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

def get_recyclage_details_jour(date):
    """Détails recyclage du jour"""
    productions = ProductionRecyclage.objects.filter(date_production=date)
    
    if not productions.exists():
        return {
            'nombre_moulinex': 0,
            'production_broyage': 0,
            'production_bache_noir': 0,
            'total_production': 0,
            'equipes_actives': [],
        }
    
    aggregats = productions.aggregate(
        moulinex=Avg('nombre_moulinex'),
        broyage=Sum('production_broyage_kg'),
        bache=Sum('production_bache_noir_kg'),
        total=Sum('total_production_kg')
    )
    
    # Équipes qui ont travaillé
    equipes = productions.values_list('equipe__nom', flat=True).distinct()
    
    return {
        'nombre_moulinex': round(aggregats['moulinex'] or 0, 0),
        'production_broyage': aggregats['broyage'] or 0,
        'production_bache_noir': aggregats['bache'] or 0,
        'total_production': aggregats['total'] or 0,
        'equipes_actives': list(equipes),
    }

# ==========================================
# CONFIGURATION AUTH
# ==========================================

# Indiquer à Django d'utiliser notre modèle User personnalisé
AUTH_USER_MODEL = 'sofemci.CustomUser'

