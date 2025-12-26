# sofemci/models/production.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from .base import ZoneExtrusion, Equipe
from .users import CustomUser


class ProductionExtrusion(models.Model):
    """Production journalière par zone d'extrusion - SANS CONTRAINTE D'UNICITÉ"""

    # Informations de base
    date_production = models.DateField()
    zone = models.ForeignKey(ZoneExtrusion, on_delete=models.CASCADE)
    equipe = models.ForeignKey(Equipe, on_delete=models.CASCADE)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    chef_zone = models.CharField(max_length=100, help_text="Nom du chef de zone")

    # Ressources utilisées
    matiere_premiere_kg = models.DecimalField(
        max_digits=10,  # Augmenté pour éviter l'erreur "Out of range"
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Matière première utilisée (kg)"
    )
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre moyen de machines actives"
    )
    nombre_machinistes = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Nombre moyen de machinistes"
    )

    # Production
    nombre_bobines_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Nombre de bobines produites (kg)"
    )
    production_finis_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production produits finis (kg)"
    )
    production_semi_finis_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production produits semi-finis (kg)"
    )
    dechets_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )

    # Champs calculés automatiquement
    total_production_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )
    rendement_pourcentage = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )
    production_par_machine = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )

    # Observations et métadonnées
    observations = models.TextField(blank=True, verbose_name="Observations du jour")
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Production Extrusion"
        verbose_name_plural = "Productions Extrusion"
        ordering = ['-date_production', 'zone']

    def save(self, *args, **kwargs):
        # Calculs automatiques EXACTEMENT comme dans vos maquettes
        self.total_production_kg = self.production_finis_kg + self.production_semi_finis_kg

        # Calcul rendement (pourcentage)
        self.rendement_pourcentage = Decimal('0.00')
        if self.matiere_premiere_kg and self.matiere_premiere_kg > 0:
            self.rendement_pourcentage = (self.total_production_kg / self.matiere_premiere_kg) * 100

        # Calcul taux de déchets
        self.taux_dechet_pourcentage = Decimal('0.00')
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (
                self.dechets_kg / (self.total_production_kg + self.dechets_kg)
            ) * 100

        # Calcul production par machine
        self.production_par_machine = Decimal('0.00')
        if self.nombre_machines_actives > 0:
            self.production_par_machine = self.total_production_kg / self.nombre_machines_actives

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.zone} - {self.date_production} - {self.equipe}"


class ProductionImprimerie(models.Model):
    """Production journalière section Imprimerie - SANS CONTRAINTE D'UNICITÉ"""

    # Informations de base
    date_production = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    # Ressources
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre moyen de machines actives"
    )

    # Production
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines produits finis (kg)"
    )
    production_bobines_semi_finies_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines semi-finis (kg)"
    )
    dechets_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )

    # Champs calculés
    total_production_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )

    # Métadonnées
    observations = models.TextField(blank=True)
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Production Imprimerie"
        verbose_name_plural = "Productions Imprimerie"
        ordering = ['-date_production']

    def save(self, *args, **kwargs):
        # Calculs automatiques
        self.total_production_kg = (
            self.production_bobines_finies_kg + self.production_bobines_semi_finies_kg
        )

        self.taux_dechet_pourcentage = Decimal('0.00')
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (
                self.dechets_kg / (self.total_production_kg + self.dechets_kg)
            ) * 100

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Imprimerie - {self.date_production}"


class ProductionSoudure(models.Model):
    """Production journalière section Soudure - SANS CONTRAINTE D'UNICITÉ"""

    # Informations de base
    date_production = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()

    # Ressources
    nombre_machines_actives = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre moyen de machines actives"
    )

    # Production standard
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production bobines produits finis (kg)"
    )

    # Production spécifique soudure
    production_bretelles_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production BRETELLE (EMBALLAGE) (kg)"
    )
    production_rema_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production REMA-PLASTIQUE (kg)"
    )
    production_batta_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production BATTA (kg)"
    )

    # NOUVEAU : Sac d'emballage imprimé
    production_sac_emballage_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        default=Decimal('0'),
        verbose_name="Production SAC D'EMBALLAGE IMPRIMÉ (kg)"
    )

    # Déchets
    dechets_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Total des déchets (kg)"
    )

    # Champs calculés
    total_production_specifique_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total production spécifique (Bretelle+Rema+Batta+Sac)"
    )
    total_production_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total production globale"
    )
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=10,  # Augmenté
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
        verbose_name = "Production Soudure"
        verbose_name_plural = "Productions Soudure"
        ordering = ['-date_production']

    def save(self, *args, **kwargs):
        # Calculs automatiques
        self.total_production_specifique_kg = (
            self.production_bretelles_kg +
            self.production_rema_kg +
            self.production_batta_kg +
            self.production_sac_emballage_kg
        )

        self.total_production_kg = (
            self.production_bobines_finies_kg +
            self.total_production_specifique_kg
        )

        self.taux_dechet_pourcentage = Decimal('0.00')
        if self.total_production_kg + self.dechets_kg > 0:
            self.taux_dechet_pourcentage = (
                self.dechets_kg / (self.total_production_kg + self.dechets_kg)
            ) * 100
        else:
            self.taux_dechet_pourcentage = Decimal('0')

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Soudure - {self.date_production}"


class ProductionRecyclage(models.Model):
    """Production journalière section Recyclage - SANS CONTRAINTE D'UNICITÉ"""

    # Informations de base
    date_production = models.DateField()
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        verbose_name="Équipe qui a travaillé"
    )

    # Ressources
    nombre_moulinex = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de moulinex"
    )

    # Production
    production_broyage_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production journalière de broyage (kg)"
    )
    production_bache_noir_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="Production de bâche noire (kg)"
    )

    # Champs calculés
    total_production_kg = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )
    production_par_moulinex = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )
    taux_transformation_pourcentage = models.DecimalField(
        max_digits=10,  # Augmenté
        decimal_places=2, 
        null=True, 
        blank=True
    )

    # Métadonnées
    observations = models.TextField(blank=True, verbose_name="Observations")
    cree_par = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    valide = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Production Recyclage"
        verbose_name_plural = "Productions Recyclage"
        ordering = ['-date_production']

    def save(self, *args, **kwargs):
        # Calculs automatiques
        self.total_production_kg = self.production_broyage_kg + self.production_bache_noir_kg

        self.production_par_moulinex = Decimal('0.00')
        if self.nombre_moulinex > 0:
            self.production_par_moulinex = self.total_production_kg / self.nombre_moulinex

        self.taux_transformation_pourcentage = Decimal('0.00')
        if self.production_broyage_kg > 0:
            self.taux_transformation_pourcentage = (
                self.production_bache_noir_kg / self.production_broyage_kg
            ) * 100

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Recyclage - {self.date_production} - {self.equipe}"