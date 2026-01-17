# sofemci/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
import re
from django.db import IntegrityError
from django.db.models.signals import pre_save
from django.dispatch import receiver

# ==========================================
# MODÈLE UTILISATEUR PERSONNALISÉ
# ==========================================

class CustomUser(AbstractUser):
    """Utilisateur personnalisé pour SOFEM-CI"""
    
    # Constantes pour les rôles
    CHEF_EXT1 = 'CHEF_EXT1'
    CHEF_EXT2 = 'CHEF_EXT2'
    CHEF_EXT3 = 'CHEF_EXT3'
    CHEF_EXT4 = 'CHEF_EXT4'
    CHEF_EXT5 = 'CHEF_EXT5'
    CHEF_RECYCL = 'CHEF_RECYCL'
    CHEF_IMPRIM = 'CHEF_IMPRIM'
    CHEF_SOUD = 'CHEF_SOUD'
    SUPERVISEUR = 'SUPERVISEUR'
    DIRECTION = 'DIRECTION'
    ADMIN = 'ADMIN'
    VISITEUR = 'VISITEUR'
    
    ROLE_CHOICES = [
        (ADMIN, 'Administrateur'),
        (SUPERVISEUR, 'Superviseur'),
        (CHEF_EXT1, 'Chef de Zone1'),
        (CHEF_EXT2, 'Chef de Zone2'),
        (CHEF_EXT3, 'Chef de Zone3'),
        (CHEF_EXT4, 'Chef de Zone4'),
        (CHEF_EXT5, 'Chef de Zone5'),
        (CHEF_RECYCL, 'Chef RECYCLAGE'),
        (CHEF_IMPRIM, 'Chef IMPRIMERIE'),
        (CHEF_SOUD, 'Chef SOUDURE'),
        (VISITEUR, 'Visiteur'),
        (DIRECTION, 'Direction'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=CHEF_EXT1,
        verbose_name="Rôle"
    )
    
    telephone = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        verbose_name="Téléphone",
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Format: '+2250102030405' ou '0102030405'"
        )]
    )
    
    date_embauche = models.DateField(
        verbose_name="Date d'embauche",
        blank=True,
        null=True
    )
    
    # Champs additionnels pour tracking
    matricule = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Matricule",
        help_text="Généré automatiquement si vide. Format: SOF-YYYY-NNNN"
    )
    
    service = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Service/Service"
    )
    
    signature = models.ImageField(
        upload_to='signatures/',
        blank=True,
        null=True,
        verbose_name="Signature"
    )
    
    dernier_acces = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernier accès"
    )
    
    est_actif = models.BooleanField(
        default=True,
        verbose_name="Actif"
    )
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['matricule'], name='customuser_matricule_idx'),
            models.Index(fields=['role'], name='customuser_role_idx'),
            models.Index(fields=['last_name', 'first_name'], name='customuser_name_idx'),
        ]
    
    def __str__(self):
        full_name = self.get_full_name()
        if full_name:
            return f"{full_name} ({self.get_role_display()})"
        return f"{self.username} ({self.get_role_display()})"
    
    def get_nom_complet(self):
        """Retourne le nom complet formaté"""
        nom_complet = f"{self.last_name or ''} {self.first_name or ''}".strip()
        return nom_complet if nom_complet else self.username
    
    # ================= MÉTHODES UTILITAIRES POUR LES RÔLES =================
    
    def is_chef_extrusion(self):
        """Vérifie si l'utilisateur est un chef d'extrusion"""
        return self.role in [self.CHEF_EXT1, self.CHEF_EXT2, self.CHEF_EXT3, 
                           self.CHEF_EXT4, self.CHEF_EXT5]
    
    def is_chef_section(self):
        """Vérifie si l'utilisateur est un chef d'autre section"""
        return self.role in [self.CHEF_RECYCL, self.CHEF_IMPRIM, self.CHEF_SOUD]
    
    def is_direction(self):
        """Vérifie si l'utilisateur est direction"""
        return self.role == self.DIRECTION
    
    def is_superviseur(self):
        """Vérifie si l'utilisateur est superviseur"""
        return self.role == self.SUPERVISEUR
    
    def is_admin(self):
        """Vérifie si l'utilisateur est admin"""
        return self.role == self.ADMIN or self.is_superuser
    
    def get_section_affectee(self):
        """Retourne la section affectée de l'utilisateur"""
        if self.is_chef_extrusion():
            zone_map = {
                self.CHEF_EXT1: 'Zone 1',
                self.CHEF_EXT2: 'Zone 2',
                self.CHEF_EXT3: 'Zone 3',
                self.CHEF_EXT4: 'Zone 4',
                self.CHEF_EXT5: 'Zone 5'
            }
            return zone_map.get(self.role, 'Extrusion')
        elif self.is_chef_section():
            section_map = {
                self.CHEF_RECYCL: 'recyclage',
                self.CHEF_IMPRIM: 'imprimerie',
                self.CHEF_SOUD: 'soudure'
            }
            return section_map.get(self.role, 'section')
        return None
    
    def is_visiteur(self):
        """Vérifie si l'utilisateur est visiteur"""
        return self.role == self.VISITEUR
    
    def is_chef_zone(self, zone_num=None):
        """Vérifie si l'utilisateur est chef d'une zone spécifique"""
        if not self.is_chef_extrusion():
            return False
        if zone_num is None:
            return True
        zone_map = {
            1: self.CHEF_EXT1,
            2: self.CHEF_EXT2,
            3: self.CHEF_EXT3,
            4: self.CHEF_EXT4,
            5: self.CHEF_EXT5
        }
        return self.role == zone_map.get(zone_num)
    
    def can_access_section(self, section_name):
        """Vérifie si l'utilisateur peut accéder à une section spécifique"""
        if self.is_admin() or self.is_direction() or self.is_superviseur():
            return True
        
        section_roles = {
            'extrusion': [self.CHEF_EXT1, self.CHEF_EXT2, self.CHEF_EXT3, 
                         self.CHEF_EXT4, self.CHEF_EXT5],
            'recyclage': [self.CHEF_RECYCL],
            'imprimerie': [self.CHEF_IMPRIM],
            'soudure': [self.CHEF_SOUD]
        }
        
        return self.role in section_roles.get(section_name.lower(), [])
    
    # ================= MÉTHODES POUR GESTION DES MATRICULES =================
    
    @classmethod
    def _get_next_matricule_number(cls):
        """Retourne le prochain numéro de matricule disponible pour l'année en cours"""
        annee = timezone.now().year
        prefixe = f"SOF-{annee}-"
        
        # Chercher tous les matricules de l'année en cours
        matricules_existants = cls.objects.filter(
            matricule__startswith=prefixe
        ).exclude(matricule__isnull=True).exclude(matricule__exact='').values_list('matricule', flat=True)
        
        # Extraire les numéros existants
        numeros_existants = []
        pattern = re.compile(rf'^{re.escape(prefixe)}(\d{{4}})$')
        
        for matricule in matricules_existants:
            if not matricule:
                continue
            match = pattern.match(matricule)
            if match:
                try:
                    numeros_existants.append(int(match.group(1)))
                except (ValueError, TypeError):
                    continue
        
        # Trouver le prochain numéro disponible
        if not numeros_existants:
            return 1
        
        max_numero = max(numeros_existants)
        
        # Chercher le premier "trou" dans la séquence
        for i in range(1, max_numero + 2):
            if i not in numeros_existants:
                return i
        
        # Si pas de trou, prendre le suivant
        return max_numero + 1
    
    @classmethod
    def generate_matricule(cls):
        """Génère un matricule unique"""
        annee = timezone.now().year
        numero = cls._get_next_matricule_number()
        return f"SOF-{annee}-{numero:04d}"
    
    def clean(self):
        """Validation avant sauvegarde"""
        super().clean()
        
        # Vérifier le format du matricule s'il est fourni manuellement
        if self.matricule and self.matricule.strip():
            matricule = self.matricule.strip()
            
            # Valider le format
            if not re.match(r'^SOF-\d{4}-\d{4}$', matricule):
                raise ValidationError({
                    'matricule': "Format invalide. Format attendu: SOF-YYYY-NNNN"
                })
            
            # Vérifier que l'année est valide
            try:
                annee_matricule = int(matricule.split('-')[1])
                annee_actuelle = timezone.now().year
                
                if annee_matricule < 2000 or annee_matricule > annee_actuelle + 1:
                    raise ValidationError({
                        'matricule': f"L'année doit être entre 2000 et {annee_actuelle + 1}"
                    })
            except (ValueError, IndexError):
                raise ValidationError({
                    'matricule': "Format d'année invalide"
                })
            
            # Vérifier l'unicité (sauf pour cet utilisateur)
            qs = CustomUser.objects.filter(matricule=matricule)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            
            if qs.exists():
                raise ValidationError({
                    'matricule': f"Le matricule '{matricule}' est déjà utilisé par un autre utilisateur."
                })
    
    def save(self, *args, **kwargs):
        """Sauvegarde avec gestion robuste des matricules"""
        is_new = self.pk is None
        
        # Nettoyer le matricule
        if self.matricule:
            self.matricule = self.matricule.strip()
            if not self.matricule:
                self.matricule = None
        
        # Générer un matricule si vide (nouvel utilisateur seulement)
        if not self.matricule and is_new:
            self.matricule = self.generate_matricule()
        
        # Pour les utilisateurs existants sans matricule, vérifier s'il faut en générer un
        elif not self.matricule and not is_new:
            try:
                ancien = CustomUser.objects.get(pk=self.pk)
                if not ancien.matricule:
                    self.matricule = self.generate_matricule()
            except CustomUser.DoesNotExist:
                pass
        
        # Valider avant sauvegarde
        try:
            self.full_clean()
        except ValidationError as e:
            # Si validation échoue à cause du matricule, essayer de générer un matricule automatique
            if 'matricule' in e.message_dict:
                if is_new or not self.matricule:
                    self.matricule = self.generate_matricule()
                else:
                    # Pour les matricules manuels invalides, lever l'exception
                    raise
        
        # Tentative de sauvegarde avec gestion des erreurs d'intégrité
        try:
            super().save(*args, **kwargs)
        
        except IntegrityError as e:
            # Si erreur d'unicité du matricule
            if 'matricule' in str(e).lower():
                if is_new or not self.matricule:
                    # Régénérer un matricule unique et réessayer
                    self.matricule = self.generate_matricule()
                    super().save(*args, **kwargs)
                else:
                    # Pour les matricules manuels en conflit, lever l'exception
                    raise ValidationError({
                        'matricule': f"Le matricule '{self.matricule}' est déjà utilisé. "
                                     f"Veuillez en choisir un autre ou laisser vide pour générer automatiquement."
                    })
            else:
                # Autre erreur d'intégrité
                raise
    
    # ================= MÉTHODES UTILITAIRES SUPPLÉMENTAIRES =================
    
    def get_matricule_info(self):
        """Retourne des informations sur le matricule"""
        if not self.matricule:
            return None
        
        try:
            match = re.match(r'^SOF-(\d{4})-(\d{4})$', self.matricule)
            if match:
                return {
                    'annee': int(match.group(1)),
                    'numero': int(match.group(2)),
                    'format': 'valide'
                }
        except (ValueError, AttributeError):
            pass
        
        return {'format': 'invalide'}
    
    @classmethod
    def fix_duplicate_matricules(cls):
        """Corrige les matricules dupliqués dans la base"""
        from django.db.models import Count
        
        # Trouver les matricules dupliqués
        duplicates = cls.objects.values('matricule').annotate(
            count=Count('matricule')
        ).filter(count__gt=1, matricule__isnull=False)
        
        corrections = []
        
        for dup in duplicates:
            matricule = dup['matricule']
            users = cls.objects.filter(matricule=matricule).order_by('date_joined')
            
            # Garder le premier (le plus ancien), corriger les autres
            for i, user in enumerate(users):
                if i == 0:
                    corrections.append(f"✓ Gardé: {user.username} - {matricule}")
                    continue
                
                # Générer un nouveau matricule unique
                nouveau_matricule = cls.generate_matricule()
                ancien_matricule = user.matricule
                user.matricule = nouveau_matricule
                user.save()
                
                corrections.append(
                    f"✓ Corrigé: {user.username} - {ancien_matricule} → {nouveau_matricule}"
                )
        
        return corrections
    
    @classmethod
    def validate_all_matricules(cls):
        """Valide tous les matricules dans la base"""
        errors = []
        
        for user in cls.objects.filter(matricule__isnull=False):
            try:
                user.full_clean()
            except ValidationError as e:
                errors.append({
                    'user': f"{user.username} (ID: {user.id})",
                    'matricule': user.matricule,
                    'error': str(e)
                })
        
        return errors

# ==========================================
# MODÈLES DE CONFIGURATION
# ==========================================

class Equipe(models.Model):
    """Équipe de production"""
    
    NOM_CHOICES = [
        ('MATIN', 'Équipe Du Matin'),
        ('SOIR', 'Équipe Du Soir'),
        ('NUIT', 'Équipe De Nuit'),
    ]
    
    nom = models.CharField(
        max_length=20,
        choices=NOM_CHOICES,
        verbose_name="Nom de l'équipe"
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )
    
    heure_fin = models.TimeField(
        verbose_name="Heure de fin"
    )
    
    chef_equipe = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipes_dirigees',
        verbose_name="Chef d'équipe"
    )
    
    nombre_membres = models.IntegerField(
        default=0,
        verbose_name="Nombre de membres"
    )
    
    est_active = models.BooleanField(
        default=True,
        verbose_name="Équipe active"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations"
    )
    
    class Meta:
        verbose_name = "Équipe"
        verbose_name_plural = "Équipes"
        ordering = ['heure_debut']
        indexes = [
            models.Index(fields=['nom'], name='equipe_nom_idx'),
            models.Index(fields=['est_active'], name='equipe_active_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_nom_display()} ({self.heure_debut.strftime('%Hh%M')}-{self.heure_fin.strftime('%Hh%M')})"
    
    def duree_travail(self):
        """Calcule la durée de travail"""
        debut = datetime.combine(datetime.today(), self.heure_debut)
        fin = datetime.combine(datetime.today(), self.heure_fin)
        if fin < debut:
            fin += timedelta(days=1)
        duree = fin - debut
        return duree.total_seconds() / 3600  # Retourne en heures

class ZoneExtrusion(models.Model):
    """Zone d'extrusion"""
    
    numero = models.IntegerField(
        unique=True,
        verbose_name="Numéro de zone",
        validators=[MinValueValidator(1)]
    )
    
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la zone"
    )
    
    capacite_max = models.PositiveBigIntegerField(
        default=100,
        validators=[MinValueValidator(1)],
        help_text="Capacité maximale de la zone d'extrusion"
    )
    
    nombre_machines_max = models.IntegerField(
        verbose_name="Nombre maximum de machines",
        default=10,
        validators=[MinValueValidator(1)]
    )
    
    chef_zone = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='zones_dirigees',
        verbose_name="Chef de zone"
    )
    
    temperature_optimale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Température optimale (°C)",
        default=180.00
    )
    
    pression_optimale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Pression optimale (bar)",
        default=150.00
    )
    
    active = models.BooleanField(
        default=True,
        verbose_name="Zone active"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations techniques"
    )
    
    class Meta:
        verbose_name = "Zone d'extrusion"
        verbose_name_plural = "Zones d'extrusion"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['numero'], name='zone_numero_idx'),
            models.Index(fields=['active'], name='zone_active_idx'),
            models.Index(fields=['chef_zone'], name='zone_chef_idx'),
        ]
    
    def __str__(self):
        return f"Zone {self.numero} - {self.nom}"
    
    def machines_actives(self):
        """Retourne le nombre de machines actives dans cette zone"""
        from django.db.models import Count
        return self.machine_set.filter(etat='ACTIVE').count()

# ==========================================
# MODÈLES MACHINES
# ==========================================

class Machine(models.Model):
    """Machine de production avec champs complets"""
    
    TYPE_MACHINE_CHOICES = [
        ('EXTRUDEUSE', 'Extrudeuse'),
        ('IMPRIMANTE', 'Machine d\'impression'),
        ('SOUDEUSE', 'Soudeuse'),
        ('MOULINEX', 'Moulinex (Recyclage)'),
        ('BROYEUSE', 'Broyeuse'),
        ('TRANSFORMATEUR', 'Transformateur'),
        ('COMPACTEUR', 'Compacteur'),
        ('CONVOYEUR', 'Convoyeur'),
        ('MELANGEUR', 'Mélangeur'),
        ('AUTRE', 'Autre'),
    ]
    
    SECTION_CHOICES = [
        ('EXTRUSION', 'Extrusion'),
        ('IMPRIMERIE', 'Imprimerie'),
        ('SOUDURE', 'Soudure'),
        ('RECYCLAGE', 'Recyclage'),
        ('MAINTENANCE', 'Maintenance'),
        ('STOCKAGE', 'Stockage'),
    ]
    
    ETAT_CHOICES = [
        ('ACTIVE', '🟢 Active'),
        ('INACTIVE', '🔴 Inactive'),
        ('MAINTENANCE', '🟡 En maintenance'),
        ('PANNE', '🔴 En panne'),
        ('HORS_SERVICE', '⚫ Hors service'),
    ]
    
    # Aliases pour compatibilité avec les vues
    SECTIONS = SECTION_CHOICES
    ETATS = ETAT_CHOICES
    
    PROVENANCE_CHOICES = [
        ('LOCAL', 'Local (Abidjan)'),
        ('IMPORT_FRANCE', 'Importé de France'),
        ('IMPORT_CHINE', 'Importé de Chine'),
        ('IMPORT_ALLEMAGNE', 'Importé d\'Allemagne'),
        ('USAGÉ_LOCAL', 'Usagé (marché local)'),
        ('USAGÉ_IMPORT', 'Usagé (importé)'),
        ('NEUF_LOCAL', 'Neuf (fournisseur local)'),
        ('NEUF_IMPORT', 'Neuf (importé)'),
        ('SOFEM_CI', 'Fabrication SOFEM-CI'),
        ('AUTRE', 'Autre origine'),
    ]
    
    # === CHAMPS DE BASE ===
    numero = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Numéro de machine"
    )
    
    type_machine = models.CharField(
        max_length=50,
        choices=TYPE_MACHINE_CHOICES,
        verbose_name="Type de machine"
    )
    
    section = models.CharField(
        max_length=50,
        choices=SECTION_CHOICES,
        verbose_name="Section"
    )
    
    zone_extrusion = models.ForeignKey(
        ZoneExtrusion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Zone d'extrusion (si applicable)"
    )
    
    # === CHAMPS AJOUTÉS ===
    provenance = models.CharField(
        max_length=50,
        choices=PROVENANCE_CHOICES,
        default='LOCAL',
        verbose_name="Provenance",
        help_text="Origine de la machine"
    )
    
    est_nouvelle = models.BooleanField(
        default=True,
        verbose_name="Machine neuve?",
        help_text="Cochez si la machine est neuve (non usagée)"
    )
    
    etat = models.CharField(
        max_length=20,
        choices=ETAT_CHOICES,
        default='ACTIVE',
        verbose_name="État"
    )
    
    date_installation = models.DateField(
        verbose_name="Date d'installation",
        default=timezone.now
    )
    
    capacite_horaire = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Capacité horaire (kg/h)",
    )
    
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations techniques"
    )
    
    # === CHAMPS MAINTENANCE ===
    derniere_maintenance = models.DateField(
        verbose_name="Date dernière maintenance",
        blank=True,
        null=True
    )
    
    prochaine_maintenance_prevue = models.DateField(
        verbose_name="Prochaine maintenance prévue",
        blank=True,
        null=True
    )
    
    frequence_maintenance_jours = models.IntegerField(
        verbose_name="Fréquence maintenance (jours)",
        default=30,
        validators=[MinValueValidator(1)]
    )
    
    heures_fonctionnement_totales = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Heures fonctionnement totales",
    )
    
    heures_depuis_derniere_maintenance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Heures depuis dernière maintenance",
    )
    
    # === HISTORIQUE PANNES ===
    nombre_pannes_totales = models.IntegerField(
        verbose_name="Nombre total de pannes",
        default=0
    )
    
    nombre_pannes_6_derniers_mois = models.IntegerField(
        verbose_name="Pannes (6 derniers mois)",
        default=0
    )
    
    nombre_pannes_1_dernier_mois = models.IntegerField(
        verbose_name="Pannes (1 dernier mois)",
        default=0
    )
    
    date_derniere_panne = models.DateField(
        verbose_name="Date dernière panne",
        blank=True,
        null=True
    )
    
    duree_moyenne_reparation = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Durée moyenne réparation (heures)",
    )
    
    # === CONSOMMATION ET TEMPÉRATURE ===
    consommation_electrique_kwh = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Consommation électrique (kWh)",
    )
    
    consommation_electrique_nominale = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Consommation nominale (kWh)",
    )
    
    temperature_actuelle = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Température actuelle (°C)",
    )
    
    temperature_nominale = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Température nominale (°C)",
    )
    
    temperature_max_autorisee = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Température max autorisée (°C)",
        default=200.00
    )
    
    # === ANALYSES IA ===
    score_sante_global = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Score santé global (%)",
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    probabilite_panne_7_jours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Probabilité panne (7 jours, %)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    probabilite_panne_30_jours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Probabilité panne (30 jours, %)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    anomalie_detectee = models.BooleanField(
        default=False,
        verbose_name="Anomalie détectée"
    )
    
    type_anomalie = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Type d'anomalie"
    )
    
    date_derniere_analyse_ia = models.DateTimeField(
        verbose_name="Date dernière analyse IA",
        blank=True,
        null=True
    )
    
    # === TRACKING ===
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    derniere_mise_a_jour_donnees = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière mise à jour données"
    )
    
    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
        ordering = ['numero']
        indexes = [
            models.Index(fields=['section', 'etat'], name='machine_section_etat_idx'),
            models.Index(fields=['numero'], name='machine_numero_idx'),
            models.Index(fields=['type_machine'], name='machine_type_idx'),
            models.Index(fields=['zone_extrusion'], name='machine_zone_idx'),
            models.Index(fields=['etat'], name='machine_etat_idx'),
        ]
    
    def __str__(self):
        return f"Machine {self.numero} - {self.get_type_machine_display()}"
    
    def clean(self):
        """Validation personnalisée"""
        super().clean()
        
        # Validation température
        if float(self.temperature_actuelle) > float(self.temperature_max_autorisee):
            raise ValidationError({
                'temperature_actuelle': 
                    f"La température actuelle ({self.temperature_actuelle}°C) "
                    f"dépasse la température maximale autorisée ({self.temperature_max_autorisee}°C)."
            })
        
        # Validation consommation
        if float(self.consommation_electrique_nominale) > 0:
            consommation_max = float(self.consommation_electrique_nominale) * 1.2
            if float(self.consommation_electrique_kwh) > consommation_max:
                raise ValidationError({
                    'consommation_electrique_kwh': 
                        f"La consommation électrique actuelle ({self.consommation_electrique_kwh} kWh) "
                        f"dépasse de plus de 20% la consommation nominale ({self.consommation_electrique_nominale} kWh)."
                })
    
    def est_en_maintenance(self):
        """Vérifie si la machine est en maintenance"""
        return self.etat == 'MAINTENANCE'
    
    def jours_depuis_maintenance(self):
        """Calcule les jours depuis la dernière maintenance"""
        if not self.derniere_maintenance:
            return None
        delta = timezone.now().date() - self.derniere_maintenance
        return delta.days
    
    def necessite_maintenance(self):
        """Vérifie si la machine nécessite une maintenance"""
        jours = self.jours_depuis_maintenance()
        if jours is None:
            return False
        return jours >= self.frequence_maintenance_jours
    
    def save(self, *args, **kwargs):
        """Logique avant sauvegarde"""
        self.full_clean()
        super().save(*args, **kwargs)

class HistoriqueMachine(models.Model):
    """Historique des événements de machine"""
    
    TYPE_EVENEMENT_CHOICES = [
        ('MAINTENANCE', 'Maintenance'),
        ('PANNE', 'Panne'),
        ('REPARATION', 'Réparation'),
        ('CONTROLE', 'Contrôle technique'),
        ('CALIBRAGE', 'Calibrage'),
        ('NETTOYAGE', 'Nettoyage'),
        ('AMELIORATION', 'Amélioration'),
        ('REMIS_EN_SERVICE', 'Remis en service'),
        ('HORS_SERVICE', 'Mis hors service'),
    ]
    
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='historique',
        verbose_name="Machine"
    )
    
    type_evenement = models.CharField(
        max_length=20,
        choices=TYPE_EVENEMENT_CHOICES,
        verbose_name="Type d'événement"
    )
    
    date_evenement = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de l'événement"
    )
    
    technicien = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Technicien"
    )
    
    description = models.TextField(
        verbose_name="Description détaillée"
    )
    
    duree_intervention = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Durée intervention (heures)",
    )
    
    cout_intervention = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Coût intervention (FCFA)",
    )
    
    pieces_utilisees = models.TextField(
        blank=True,
        null=True,
        verbose_name="Pièces utilisées"
    )
    
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations"
    )
    
    signature_technicien = models.ImageField(
        upload_to='signatures_techniciens/',
        blank=True,
        null=True,
        verbose_name="Signature technicien"
    )
    
    class Meta:
        verbose_name = "Historique machine"
        verbose_name_plural = "Historiques machines"
        ordering = ['-date_evenement']
        indexes = [
            models.Index(fields=['machine', 'date_evenement'], name='historique_machine_date_idx'),
            models.Index(fields=['type_evenement'], name='historique_type_idx'),
            models.Index(fields=['technicien'], name='historique_technicien_idx'),
        ]
    
    def __str__(self):
        return f"{self.machine.numero} - {self.get_type_evenement_display()} - {self.date_evenement.strftime('%d/%m/%Y')}"

# ==========================================
# MODÈLES DE PRODUCTION
# ==========================================

class ProductionExtrusion(models.Model):
    """Production de la section extrusion"""
    
    # === INFORMATIONS GÉNÉRALES ===
    date_production = models.DateField(
        verbose_name="Date de production"
    )
    
    zone = models.ForeignKey(
        ZoneExtrusion,
        on_delete=models.PROTECT,
        verbose_name="Zone d'extrusion"
    )
    
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.PROTECT,
        verbose_name="Équipe"
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )
    
    heure_fin = models.TimeField(
        verbose_name="Heure de fin"
    )
    
    chef_zone = models.CharField(
        max_length=100,
        verbose_name="Chef de zone"
    )
    
    # === RESSOURCES UTILISÉES ===
    matiere_premiere_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Matière première (kg)",
        validators=[MinValueValidator(0)],
    )
    
    nombre_machines_actives = models.IntegerField(
        verbose_name="Nombre de machines actives",
        validators=[MinValueValidator(0)],
        default=0
    )
    
    nombre_machinistes = models.IntegerField(
        verbose_name="Nombre de machinistes",
        validators=[MinValueValidator(0)],
        default=0
    )
    
    # === PRODUCTION ===
    nombre_bobines_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Nombre de bobines (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_finis_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production finis (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_semi_finis_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production semi-finis (kg)",
        validators=[MinValueValidator(0)],
    )
    
    dechets = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Déchets générés (kg)",
        validators=[MinValueValidator(0)],
    )
    
    # === CALCULS AUTOMATIQUES ===
    total_production_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production totale (kg)",
    )
    
    rendement_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Rendement matière (%)",
    )
    
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taux de déchet (%)",
    )
    
    production_par_machine = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production par machine (kg)",
    )
    
    # === INFORMATIONS SUPPLÉMENTAIRES ===
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations"
    )
    
    valide = models.BooleanField(
        default=False,
        verbose_name="Validé"
    )
    
    cree_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productions_extrusion_creees',
        verbose_name="Créé par"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Production extrusion"
        verbose_name_plural = "Productions extrusion"
        ordering = ['-date_production', 'zone']
        unique_together = ['date_production', 'zone', 'equipe']
        indexes = [
            models.Index(fields=['date_production', 'zone'], name='prod_extrusion_date_zone_idx'),
            models.Index(fields=['valide'], name='prod_extrusion_valide_idx'),
            models.Index(fields=['date_creation'], name='prod_extrusion_creation_idx'),
            models.Index(fields=['equipe'], name='prod_extrusion_equipe_idx'),
        ]
    
    def __str__(self):
        return f"Extrusion {self.date_production} - {self.zone} - {self.equipe}"
    
    def clean(self):
        """Validation avant sauvegarde"""
        super().clean()
        
        # Validation production vs matière première
        if float(self.matiere_premiere_kg) > 0:
            production_totale = float(self.production_finis_kg) + float(self.production_semi_finis_kg)
            if production_totale > float(self.matiere_premiere_kg):
                raise ValidationError({
                    'production_finis_kg': 
                        f"La production totale ({production_totale} kg) ne peut pas "
                        f"dépasser la matière première ({self.matiere_premiere_kg} kg).",
                    'production_semi_finis_kg': 
                        f"La production totale ({production_totale} kg) ne peut pas "
                        f"dépasser la matière première ({self.matiere_premiere_kg} kg)."
                })
    
    def save(self, *args, **kwargs):
        """Calcul automatique des indicateurs avant sauvegarde"""
        # Production totale
        self.total_production_kg = self.production_finis_kg + self.production_semi_finis_kg
        
        # Rendement matière
        if float(self.matiere_premiere_kg) > 0:
            self.rendement_pourcentage = (self.total_production_kg / self.matiere_premiere_kg) * 100
        else:
            self.rendement_pourcentage = 0
        
        # Taux de déchet
        total_avec_dechets = self.total_production_kg + self.dechets
        if float(total_avec_dechets) > 0:
            self.taux_dechet_pourcentage = (self.dechets / total_avec_dechets) * 100
        else:
            self.taux_dechet_pourcentage = 0
        
        # Production par machine
        if self.nombre_machines_actives > 0:
            self.production_par_machine = self.total_production_kg / self.nombre_machines_actives
        else:
            self.production_par_machine = 0
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def duree_production(self):
        """Calcule la durée de production en heures"""
        try:
            debut = datetime.combine(self.date_production, self.heure_debut)
            fin = datetime.combine(self.date_production, self.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            duree = fin - debut
            return duree.total_seconds() / 3600
        except (TypeError, AttributeError):
            return 0
    
    def productivite_horaire(self):
        """Calcule la productivité horaire"""
        duree = self.duree_production()
        if duree > 0:
            return float(self.total_production_kg) / duree
        return 0

class ProductionImprimerie(models.Model):
    """Production de la section imprimerie"""
    
    date_production = models.DateField(
        verbose_name="Date de production"
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )
    
    heure_fin = models.TimeField(
        verbose_name="Heure de fin"
    )
    
    nombre_machines_actives = models.IntegerField(
        verbose_name="Nombre de machines actives",
        validators=[MinValueValidator(0)],
        default=0
    )
    
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production bobines finies (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_bobines_semi_finies_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production bobines semi-finies (kg)",
        validators=[MinValueValidator(0)],
    )
    
    dechets = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Déchets générés (kg)",
        validators=[MinValueValidator(0)],
    )
    
    # === CALCULS AUTOMATIQUES ===
    total_production_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production totale (kg)",
    )
    
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taux de déchet (%)",
    )
    
    # === INFORMATIONS SUPPLÉMENTAIRES ===
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations"
    )
    
    valide = models.BooleanField(
        default=False,
        verbose_name="Validé"
    )
    
    cree_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productions_imprimerie_creees',
        verbose_name="Créé par"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Production imprimerie"
        verbose_name_plural = "Productions imprimerie"
        ordering = ['-date_production']
        indexes = [
            models.Index(fields=['date_production'], name='prod_imprimerie_date_idx'),
            models.Index(fields=['valide'], name='prod_imprimerie_valide_idx'),
            models.Index(fields=['date_creation'], name='prod_imprimerie_creation_idx'),
        ]
    
    def __str__(self):
        return f"Imprimerie {self.date_production}"
    
    def save(self, *args, **kwargs):
        """Calcul automatique des indicateurs"""
        self.total_production_kg = self.production_bobines_finies_kg + self.production_bobines_semi_finies_kg
        
        total_avec_dechets = self.total_production_kg + self.dechets
        if float(total_avec_dechets) > 0:
            self.taux_dechet_pourcentage = (self.dechets / total_avec_dechets) * 100
        else:
            self.taux_dechet_pourcentage = 0
        
        super().save(*args, **kwargs)
    
    def duree_production(self):
        """Calcule la durée de production"""
        try:
            debut = datetime.combine(self.date_production, self.heure_debut)
            fin = datetime.combine(self.date_production, self.heure_fin)
            if fin < debut:
                fin += timedelta(days=1)
            duree = fin - debut
            return duree.total_seconds() / 3600
        except (TypeError, AttributeError):
            return 0

class ProductionSoudure(models.Model):
    """Production de la section soudure"""
    
    date_production = models.DateField(
        verbose_name="Date de production"
    )
    
    heure_debut = models.TimeField(
        verbose_name="Heure de début"
    )
    
    heure_fin = models.TimeField(
        verbose_name="Heure de fin"
    )
    
    nombre_machines_actives = models.IntegerField(
        verbose_name="Nombre de machines actives",
        validators=[MinValueValidator(0)],
        default=0
    )
    
    # === PRODUCTION STANDARD ===
    production_bobines_finies_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production bobines finies (kg)",
        validators=[MinValueValidator(0)],
    )
    
    # === PRODUCTION SPÉCIFIQUE SOUDURE ===
    production_bretelles_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production bretelles (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_rema_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production REMA-Plastique (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_batta_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production BATTA (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_sac_emballage_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production sac d'emballage imprimé (kg)",
        validators=[MinValueValidator(0)],
    )
    
    dechets = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Déchets générés (kg)",
        validators=[MinValueValidator(0)],
    )
    
    # === CALCULS AUTOMATIQUES ===
    total_production_specifique_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production spécifique totale (kg)",
    )
    
    total_production_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production totale (kg)",
    )
    
    taux_dechet_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taux de déchet (%)",
    )
    
    # === INFORMATIONS SUPPLÉMENTAIRES ===
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations"
    )
    
    valide = models.BooleanField(
        default=False,
        verbose_name="Validé"
    )
    
    cree_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productions_soudure_creees',
        verbose_name="Créé par"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Production soudure"
        verbose_name_plural = "Productions soudure"
        ordering = ['-date_production']
        indexes = [
            models.Index(fields=['date_production'], name='prod_soudure_date_idx'),
            models.Index(fields=['valide'], name='prod_soudure_valide_idx'),
            models.Index(fields=['date_creation'], name='prod_soudure_creation_idx'),
        ]
    
    def __str__(self):
        return f"Soudure {self.date_production}"
    
    def save(self, *args, **kwargs):
        """Calcul automatique des indicateurs"""
        # Production spécifique totale
        self.total_production_specifique_kg = (
            self.production_bretelles_kg + 
            self.production_rema_kg + 
            self.production_batta_kg + 
            self.production_sac_emballage_kg
        )
        
        # Production totale
        self.total_production_kg = self.production_bobines_finies_kg + self.total_production_specifique_kg
        
        # Taux de déchet
        total_avec_dechets = self.total_production_kg + self.dechets
        if float(total_avec_dechets) > 0:
            self.taux_dechet_pourcentage = (self.dechets / total_avec_dechets) * 100
        else:
            self.taux_dechet_pourcentage = 0
        
        super().save(*args, **kwargs)

class ProductionRecyclage(models.Model):
    """Production de la section recyclage"""
    
    date_production = models.DateField(
        verbose_name="Date de production"
    )
    
    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.PROTECT,
        verbose_name="Équipe"
    )
    
    nombre_moulinex = models.IntegerField(
        verbose_name="Nombre de moulinex",
        validators=[MinValueValidator(0)],
        default=0
    )
    
    production_broyage_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production broyage (kg)",
        validators=[MinValueValidator(0)],
    )
    
    production_bache_noir_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Bâche noire produite (kg)",
        validators=[MinValueValidator(0)],
    )

    dechets = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Déchets générés (kg)",
        validators=[MinValueValidator(0)],
    )
    
    # === CALCULS AUTOMATIQUES ===
    total_production_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production totale (kg)",
    )
    
    production_par_moulinex = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Production par moulinex (kg)",
    )
    
    taux_transformation_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taux de transformation (%)",
    )

    taux_dechet_pourcentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Taux de déchet (%)",
    )
    
    # === INFORMATIONS SUPPLÉMENTAIRES ===
    observations = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observations"
    )
    
    valide = models.BooleanField(
        default=False,
        verbose_name="Validé"
    )
    
    cree_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='productions_recyclage_creees',
        verbose_name="Créé par"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    
    class Meta:
        verbose_name = "Production recyclage"
        verbose_name_plural = "Productions recyclage"
        ordering = ['-date_production', 'equipe']
        indexes = [
            models.Index(fields=['date_production', 'equipe'], name='prod_recyclage_date_equipe_idx'),
            models.Index(fields=['valide'], name='prod_recyclage_valide_idx'),
            models.Index(fields=['date_creation'], name='prod_recyclage_creation_idx'),
        ]
    
    def __str__(self):
        return f"Recyclage {self.date_production} - {self.equipe}"
    
    def clean(self):
        """Validation personnalisée"""
        super().clean()
        # Note: On ne bloque plus si bâche > broyage, seulement avertissement
        if float(self.production_broyage_kg) > 0 and float(self.production_bache_noir_kg) > float(self.production_broyage_kg):
            # Log warning mais pas d'erreur
            pass
    
    def save(self, *args, **kwargs):
        """Calcul automatique des indicateurs"""
        # Production totale = bâche noire produite
        self.total_production_kg = self.production_bache_noir_kg
        
        # Production par moulinex
        if self.nombre_moulinex > 0:
            self.production_par_moulinex = self.total_production_kg / self.nombre_moulinex
        else:
            self.production_par_moulinex = 0
        
        # Taux de transformation
        if float(self.production_broyage_kg) > 0:
            self.taux_transformation_pourcentage = (self.production_bache_noir_kg / self.production_broyage_kg) * 100
        else:
            self.taux_transformation_pourcentage = 0

        # Taux de déchet
        total_avec_dechets = self.total_production_kg + self.dechets
        if float(total_avec_dechets) > 0:
            self.taux_dechet_pourcentage = (self.dechets / total_avec_dechets) * 100
        else:
            self.taux_dechet_pourcentage = 0
        
        self.full_clean()
        super().save(*args, **kwargs)

# ==========================================
# MODÈLES D'ALERTES
# ==========================================

class Alerte(models.Model):
    """Système d'alertes générales"""
    
    TYPE_ALERTE_CHOICES = [
        ('PRODUCTION', 'Production'),
        ('QUALITE', 'Qualité'),
        ('SECURITE', 'Sécurité'),
        ('MAINTENANCE', 'Maintenance'),
        ('STOCK', 'Stock'),
        ('PERSONNEL', 'Personnel'),
        ('SYSTEME', 'Système'),
        ('AUTRE', 'Autre'),
    ]
    
    STATUT_CHOICES = [
        ('NOUVELLE', '🆕 Nouvelle'),
        ('EN_COURS', '🔄 En cours'),
        ('RESOLUE', '✅ Résolue'),
        ('ANNULEE', '❌ Annulée'),
    ]
    
    SECTION_CHOICES = [
        ('EXTRUSION', 'Extrusion'),
        ('IMPRIMERIE', 'Imprimerie'),
        ('SOUDURE', 'Soudure'),
        ('RECYCLAGE', 'Recyclage'),
        ('GENERAL', 'Général'),
        ('MAINTENANCE', 'Maintenance'),
        ('ADMIN', 'Administration'),
    ]
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de l'alerte"
    )
    
    type_alerte = models.CharField(
        max_length=20,
        choices=TYPE_ALERTE_CHOICES,
        verbose_name="Type d'alerte"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='NOUVELLE',
        verbose_name="Statut"
    )
    
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        verbose_name="Section concernée"
    )
    
    message = models.TextField(
        verbose_name="Message détaillé"
    )
    
    cree_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='alertes_creees',
        verbose_name="Créé par"
    )
    
    assigne_a = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertes_assignees',
        verbose_name="Assigné à"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    date_resolution = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de résolution"
    )
    
    delai_resolution = models.IntegerField(
        verbose_name="Délai de résolution (heures)",
        default=24
    )
    
    priorite = models.IntegerField(
        verbose_name="Priorité (1-5)",
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    solution = models.TextField(
        blank=True,
        null=True,
        verbose_name="Solution apportée"
    )
    
    pieces_jointes = models.FileField(
        upload_to='alertes/',
        blank=True,
        null=True,
        verbose_name="Pièces jointes"
    )
    
    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-date_creation', 'priorite']
        indexes = [
            models.Index(fields=['statut', 'section'], name='alerte_statut_section_idx'),
            models.Index(fields=['date_creation'], name='alerte_date_creation_idx'),
            models.Index(fields=['cree_par'], name='alerte_cree_par_idx'),
            models.Index(fields=['assigne_a'], name='alerte_assigne_a_idx'),
            models.Index(fields=['priorite'], name='alerte_priorite_idx'),
        ]
    
    def __str__(self):
        return f"{self.get_type_alerte_display()}: {self.titre}"
    
    def est_en_retard(self):
        """Vérifie si l'alerte est en retard"""
        if self.statut == 'RESOLUE' or self.statut == 'ANNULEE':
            return False
        
        delai_max = self.date_creation + timedelta(hours=self.delai_resolution)
        return timezone.now() > delai_max
    
    def jours_ouverture(self):
        """Calcule le nombre de jours d'ouverture"""
        if self.date_resolution:
            delta = self.date_resolution - self.date_creation
        else:
            delta = timezone.now() - self.date_creation
        
        return delta.days
    
    def save(self, *args, **kwargs):
        """Met à jour la date de résolution si nécessaire"""
        if self.statut == 'RESOLUE' and not self.date_resolution:
            self.date_resolution = timezone.now()
        elif self.statut != 'RESOLUE':
            self.date_resolution = None
        
        super().save(*args, **kwargs)

class AlerteIA(models.Model):
    """Alertes générées par l'IA"""
    
    NIVEAU_CHOICES = [
        ('CRITIQUE', '🔴 Critique'),
        ('HAUTE', '🟠 Haute'),
        ('MOYENNE', '🟡 Moyenne'),
        ('BASSE', '🟢 Basse'),
        ('INFORMATION', '🔵 Information'),
    ]
    
    machine = models.ForeignKey(
        Machine,
        on_delete=models.CASCADE,
        related_name='alertes_ia',
        verbose_name="Machine"
    )
    
    titre = models.CharField(
        max_length=200,
        verbose_name="Titre de l'alerte"
    )
    
    niveau = models.CharField(
        max_length=20,
        choices=NIVEAU_CHOICES,
        verbose_name="Niveau d'alerte"
    )
    
    statut = models.CharField(
        max_length=20,
        choices=[
            ('ACTIVE', 'Active'),
            ('TRAITEE', 'Traitée'),
            ('IGNOREE', 'Ignorée'),
        ],
        default='ACTIVE',
        verbose_name="Statut"
    )
    
    message = models.TextField(
        verbose_name="Message IA"
    )
    
    probabilite_panne = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Probabilité de panne (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    variables_anormales = models.JSONField(
        verbose_name="Variables anormales",
        default=dict,
        help_text="Données anormales détectées"
    )
    
    recommandations = models.TextField(
        default='',
        blank=True,
        verbose_name="Recommandations IA"
    )
    
    date_creation = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de création"
    )
    
    date_traitement = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Date de traitement"
    )
    
    traite_par = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Traité par"
    )
    
    action_traitement = models.TextField(
        blank=True,
        null=True,
        verbose_name="Action de traitement"
    )
    
    class Meta:
        verbose_name = "Alerte IA"
        verbose_name_plural = "Alertes IA"
        ordering = ['-date_creation', 'niveau']
        indexes = [
            models.Index(fields=['machine', 'statut'], name='alerte_ia_machine_statut_idx'),
            models.Index(fields=['date_creation'], name='alerte_ia_date_creation_idx'),
            models.Index(fields=['niveau'], name='alerte_ia_niveau_idx'),
            models.Index(fields=['traite_par'], name='alerte_ia_traite_par_idx'),
        ]
    
    def __str__(self):
        return f"IA: {self.machine.numero} - {self.titre}"
    
    def get_couleur_niveau(self):
        """Retourne la couleur CSS selon le niveau"""
        couleurs = {
            'CRITIQUE': 'danger',
            'HAUTE': 'warning',
            'MOYENNE': 'info',
            'BASSE': 'success',
            'INFORMATION': 'primary',
        }
        return couleurs.get(self.niveau, 'secondary')
    
    def save(self, *args, **kwargs):
        """Met à jour la date de traitement"""
        if self.statut == 'TRAITEE' and not self.date_traitement:
            self.date_traitement = timezone.now()
        elif self.statut != 'TRAITEE':
            self.date_traitement = None
        
        super().save(*args, **kwargs)

# ==========================================
# SIGNALS POUR CustomUser
# ==========================================

@receiver(pre_save, sender=CustomUser)
def customuser_pre_save(sender, instance, **kwargs):
    """
    Signal pour garantir l'unicité des matricules avant sauvegarde.
    Cette fonction est appelée juste avant chaque sauvegarde d'un CustomUser.
    """
    # Nettoyer le matricule
    if instance.matricule:
        instance.matricule = instance.matricule.strip()
        if not instance.matricule:
            instance.matricule = None
    
    # Vérifier les doublons pour les matricules non vides
    if instance.matricule:
        # Construire la requête pour vérifier l'unicité
        if instance.pk:
            # Utilisateur existant : exclure lui-même
            qs = CustomUser.objects.filter(
                matricule=instance.matricule
            ).exclude(pk=instance.pk)
        else:
            # Nouvel utilisateur : vérifier tous
            qs = CustomUser.objects.filter(matricule=instance.matricule)
        
        # Si un doublon est trouvé, générer un nouveau matricule
        if qs.exists():
            instance.matricule = CustomUser.generate_matricule()

# ==========================================
# FONCTIONS UTILITAIRES
# ==========================================

def calculer_rendement_matiere(production_totale, matiere_premiere):
    """Calcule le rendement matière en pourcentage"""
    try:
        if float(matiere_premiere) <= 0:
            return 0
        return (float(production_totale) / float(matiere_premiere)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def calculer_taux_dechet(dechets, production_totale):
    """Calcule le taux de déchet en pourcentage"""
    try:
        total = float(production_totale) + float(dechets)
        if total <= 0:
            return 0
        return (float(dechets) / total) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

def generer_numero_machine(section, type_machine):
    """Génère un numéro de machine unique"""
    prefixe = section[:3].upper() if section else 'GEN'
    type_code = type_machine[:3].upper() if type_machine else 'MCH'
    date_code = timezone.now().strftime('%y%m')
    
    try:
        # Chercher le dernier numéro pour cette combinaison
        dernier = Machine.objects.filter(
            section=section,
            type_machine=type_machine
        ).order_by('-numero').first()
        
        if dernier and dernier.numero.startswith(f"{prefixe}-{type_code}-{date_code}-"):
            try:
                sequence = int(dernier.numero.split('-')[-1]) + 1
            except (ValueError, IndexError):
                sequence = 1
        else:
            sequence = 1
        
        return f"{prefixe}-{type_code}-{date_code}-{sequence:03d}"
    except Exception:
        # Fallback en cas d'erreur
        timestamp = int(timezone.now().timestamp() % 10000)
        return f"{prefixe}-{type_code}-{date_code}-{timestamp:04d}"

# ==========================================
# MÉTHODES DE SERVICE
# ==========================================

def get_statistiques_machine(machine_id):
    """Retourne les statistiques d'une machine"""
    try:
        machine = Machine.objects.get(id=machine_id)
        return {
            'nom': f"{machine.numero}",
            'type': machine.get_type_machine_display(),
            'etat': machine.get_etat_display(),
            'score_sante': float(machine.score_sante_global),
            'prochaine_maintenance': machine.prochaine_maintenance_prevue,
            'heures_fonctionnement': float(machine.heures_fonctionnement_totales),
            'pannes_30_jours': machine.nombre_pannes_1_dernier_mois,
        }
    except (Machine.DoesNotExist, ValueError, TypeError):
        return None

def get_kpi_production(date_debut, date_fin):
    """Calcule les KPI de production sur une période"""
    from django.db.models import Sum, Avg
    
    try:
        productions = ProductionExtrusion.objects.filter(
            date_production__range=[date_debut, date_fin]
        )
        
        if not productions.exists():
            return None
        
        stats = {
            'production_totale': float(productions.aggregate(Sum('total_production_kg'))['total_production_kg__sum'] or 0),
            'matiere_totale': float(productions.aggregate(Sum('matiere_premiere_kg'))['matiere_premiere_kg__sum'] or 0),
            'rendement_moyen': float(productions.aggregate(Avg('rendement_pourcentage'))['rendement_pourcentage__avg'] or 0),
            'dechets_totaux': float(productions.aggregate(Sum('dechets'))['dechets__sum'] or 0),
            'nb_jours': productions.count(),
        }
        
        return stats
    except Exception:
        return None

# ==========================================
# CONSTANTES
# ==========================================

PRODUCTION_OBJECTIFS = {
    'EXTRUSION': {
        'rendement_min': 85.0,
        'taux_dechet_max': 5.0,
        'productivite_min': 500.0,  # kg/h
    },
    'IMPRIMERIE': {
        'rendement_min': 90.0,
        'taux_dechet_max': 3.0,
    },
    'SOUDURE': {
        'rendement_min': 88.0,
        'taux_dechet_max': 4.0,
    },
    'RECYCLAGE': {
        'taux_transformation_min': 75.0,
        'production_moulinex_min': 300.0,  # kg/moulinex
    }
}

SEUILS_ALERTE = {
    'TEMPERATURE_CRITIQUE': 220.0,  # °C
    'CONSOMMATION_CRITIQUE': 1.3,   # 30% au-dessus du nominal
    'SCORE_SANTE_CRITIQUE': 60.0,   # %
    'PROBABILITE_PANNE_CRITIQUE': 70.0,  # %
}