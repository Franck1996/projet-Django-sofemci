from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
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
    actif = models.BooleanField(default=True)
    
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
    numero = models.IntegerField(unique=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
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

class Machine(models.Model):
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
        validators=[MinValueValidator(0), MaxValueValidator(4)],
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
        validators=[MinValueValidator(0), MaxValueValidator(10)],
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
        validators=[MinValueValidator(0), MaxValueValidator(8)],
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
        validators=[MinValueValidator(0), MaxValueValidator(5)],
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

