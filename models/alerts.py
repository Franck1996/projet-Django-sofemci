from django.db import models
from django.utils import timezone

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
    cree_par = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    assigne_a = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='alertes_assignees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_resolution = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.get_type_alerte_display()} - {self.titre}"

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
    
    machine = models.ForeignKey('Machine', on_delete=models.CASCADE, related_name='alertes_ia')
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
        'CustomUser', 
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