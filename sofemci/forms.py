# sofemci/forms.py
# 🎯 TOUS LES FORMULAIRES DE L'APPLICATION SOFEM-CI

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal

from .models import *

# ==========================================
# FORMULAIRE DE CONNEXION
# ==========================================

class LoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé"""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom d\'utilisateur',
            'id': 'username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe',
            'id': 'password'
        })
    )

# ==========================================
# FORMULAIRES DE PRODUCTION EXTRUSION
# ==========================================

class ProductionExtrusionForm(forms.ModelForm):
    """Formulaire saisie production Extrusion - EXACTEMENT comme dans votre maquette"""
    
    class Meta:
        model = ProductionExtrusion
        fields = [
            'date_production', 'zone', 'equipe', 'heure_debut', 'heure_fin',
            'matiere_premiere_kg', 'nombre_machines_actives', 'nombre_machinistes',
            'nombre_bobines_kg', 'production_finis_kg', 'production_semi_finis_kg',
            'dechets_kg', 'chef_zone', 'observations'
        ]
        
        widgets = {
            'date_production': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().date()
            }),
            'zone': forms.Select(attrs={'class': 'form-control'}),
            'equipe': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '14:00'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '22:00'
            }),
            'matiere_premiere_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'matiere_premiere'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '4',
                'id': 'nb_machines'
            }),
            'nombre_machinistes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'id': 'nb_machinistes'
            }),
            'nombre_bobines_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'production_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'prod_finis'
            }),
            'production_semi_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'prod_semi_finis'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'dechets'
            }),
            'chef_zone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du chef de zone',
                'id': 'chef_zone'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Incidents, remarques, problèmes rencontrés...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les zones selon l'utilisateur
        if self.user and self.user.role == 'chef_extrusion':
            self.fields['zone'].queryset = ZoneExtrusion.objects.filter(
                chef_zone=self.user, active=True
            )
        else:
            self.fields['zone'].queryset = ZoneExtrusion.objects.filter(active=True)
        
        # Pré-remplir le chef de zone
        if self.user and not self.instance.pk:
            self.fields['chef_zone'].initial = f"{self.user.first_name} {self.user.last_name}"
    
    def clean_date_production(self):
        date = self.cleaned_data['date_production']
        
        # Pas de date future
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        # Limite 30 jours passé
        limite = timezone.now().date() - timezone.timedelta(days=30)
        if date < limite:
            raise ValidationError("Impossible de saisir plus de 30 jours.")
        
        return date
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date_production')
        zone = cleaned_data.get('zone')
        equipe = cleaned_data.get('equipe')
        
        # Vérifier unicité
        if date and zone and equipe:
            existing = ProductionExtrusion.objects.filter(
                date_production=date, zone=zone, equipe=equipe
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError("Production existe déjà pour cette zone, équipe et date.")
        
        return cleaned_data

# ==========================================
# FORMULAIRES AUTRES SECTIONS
# ==========================================


class FiltreHistoriqueForm(forms.Form):
    """Formulaire de filtres pour l'historique"""
    section = forms.ChoiceField(
        choices=[
            ('', 'Toutes les sections'),
            ('extrusion', 'Extrusion'),
            ('imprimerie', 'Imprimerie'),
            ('soudure', 'Soudure'),
            ('recyclage', 'Recyclage'),
        ],
        required=False,
        label='Section'
    )
    date_debut = forms.DateField(
        required=False,
        label='Date début',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_fin = forms.DateField(
        required=False,
        label='Date fin',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    equipe = forms.ModelChoiceField(
        queryset=Equipe.objects.all(),
        required=False,
        label='Équipe'
    )


class ProductionImprimerieForm(forms.ModelForm):
    """Formulaire saisie production Imprimerie - EXACTEMENT comme dans votre maquette"""
    
    class Meta:
        model = ProductionImprimerie
        fields = [
            'date_production', 'heure_debut', 'heure_fin',
            'nombre_machines_actives', 'production_bobines_finies_kg',
            'production_bobines_semi_finies_kg', 'dechets_kg', 'observations'
        ]
        
        widgets = {
            'date_production': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().date()
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '14:00',
                'id': 'imp_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '22:00',
                'id': 'imp_heure_fin'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '10',
                'id': 'imp_nb_machines'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'imp_bobines_finies'
            }),
            'production_bobines_semi_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'imp_bobines_semi_finies'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'imp_dechets'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observations...'
            }),
        }
    
    def clean_date_production(self):
        date = self.cleaned_data['date_production']
        
        # Vérifier unicité
        existing = ProductionImprimerie.objects.filter(date_production=date)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        
        if existing.exists():
            raise ValidationError("Production imprimerie existe déjà pour cette date.")
        
        return date

class ProductionSoudureForm(forms.ModelForm):
    """Formulaire saisie production Soudure - EXACTEMENT comme dans votre maquette"""
    
    class Meta:
        model = ProductionSoudure
        fields = [
            'date_production', 'heure_debut', 'heure_fin',
            'nombre_machines_actives', 'production_bobines_finies_kg',
            'production_bretelles_kg', 'production_rema_kg', 'production_batta_kg',
            'production_sac_emballage_kg',
            'dechets_kg', 'observations'
        ]
        
        widgets = {
            'date_production': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().date()
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '14:00',
                'id': 'sou_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '22:00',
                'id': 'sou_heure_fin'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '8',
                'id': 'sou_nb_machines'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'sou_bobines_finies'
            }),
            'production_bretelles_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'sou_bretelles'
            }),
            'production_rema_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'sou_rema'
            }),
            'production_batta_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'sou_batta'
            }),
            'production_sac_emballage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Sacs imprimés',
                'id': 'sou_sac_emballage'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'sou_dechets'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observations...'
            }),
        }

class ProductionRecyclageForm(forms.ModelForm):
    """Formulaire saisie production Recyclage - EXACTEMENT comme dans votre maquette"""
    
    class Meta:
        model = ProductionRecyclage
        fields = [
            'date_production', 'equipe', 'nombre_moulinex',
            'production_broyage_kg', 'production_bache_noir_kg', 'observations'
        ]
        
        widgets = {
            'date_production': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().date(),
                'id': 'rec_date'
            }),
            'equipe': forms.Select(attrs={
                'class': 'form-control',
                'id': 'rec_equipe'
            }),
            'nombre_moulinex': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5',
                'id': 'rec_nb_moulinex'
            }),
            'production_broyage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'rec_broyage'
            }),
            'production_bache_noir_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'rec_bache_noir'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Qualité des matières recyclées, incidents, améliorations...',
                'id': 'rec_observations'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date_production')
        equipe = cleaned_data.get('equipe')
        
        # Vérifier unicité
        if date and equipe:
            existing = ProductionRecyclage.objects.filter(
                date_production=date, equipe=equipe
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError("Production recyclage existe déjà pour cette équipe et date.")
        
        return cleaned_data

# ==========================================
# FORMULAIRE DE FILTRAGE HISTORIQUE
# ==========================================

class FiltreHistoriqueForm(forms.Form):
    """Formulaire de filtrage pour l'historique - EXACTEMENT comme dans votre maquette"""
    
    MOIS_CHOICES = [
        ('', 'Tous les mois'),
        ('2025-01', 'Janvier 2025'),
        ('2025-02', 'Février 2025'),
        ('2025-03', 'Mars 2025'),
        ('2025-04', 'Avril 2025'),
        ('2025-05', 'Mai 2025'),
        ('2025-06', 'Juin 2025'),
        ('2025-07', 'Juillet 2025'),
        ('2025-08', 'Août 2025'),
        ('2025-09', 'Septembre 2025'),
        ('2025-10', 'Octobre 2025'),
        ('2025-11', 'Novembre 2025'),
        ('2025-12', 'Décembre 2025'),
    ]
    
    SECTION_CHOICES = [
        ('', 'Toutes les sections'),
        ('extrusion', 'Extrusion'),
        ('imprimerie', 'Imprimerie'),
        ('soudure', 'Soudure'),
        ('recyclage', 'Recyclage'),
    ]
    
    ZONE_CHOICES = [
        ('', 'Toutes les zones'),
        ('1', 'Zone 1'),
        ('2', 'Zone 2'),
        ('3', 'Zone 3'),
        ('4', 'Zone 4'),
        ('5', 'Zone 5'),
    ]
    
    mois = forms.ChoiceField(
        choices=MOIS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'mois'}),
        initial=f'{timezone.now().year}-{timezone.now().month:02d}'
    )
    
    section = forms.ChoiceField(
        choices=SECTION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'section'})
    )
    
    zone = forms.ChoiceField(
        choices=ZONE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'zone'})
    )
    
    equipe = forms.ModelChoiceField(
        queryset=Equipe.objects.all(),
        required=False,
        empty_label='Toutes les équipes',
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'equipe'})
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Date de début'
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        label='Date de fin'
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_fin < date_debut:
                raise ValidationError("Date de fin doit être après date de début.")
        
        return cleaned_data

# ==========================================
# FORMULAIRES GESTION UTILISATEURS
# ==========================================

class CustomUserForm(forms.ModelForm):
    """Formulaire création/modification utilisateur"""
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'telephone', 'date_embauche', 'is_active']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# ==========================================
# FORMULAIRES MACHINES - VERSION ACTUALISÉE
# ==========================================

class MachineForm(forms.ModelForm):
    """Formulaire gestion machines - AVEC PROVENANCE ET EST_NOUVELLE"""
    
    # Champs personnalisés pour la zone d'extrusion
    zone_numero = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Numéro de zone (1-10)',
            'min': 1,
            'max': 10
        }),
        label='Numéro de Zone'
    )
    
    zone_nom = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom de la zone'
        }),
        label='Nom de la Zone'
    )
    
    class Meta:
        model = Machine
        fields = [
            'numero', 'type_machine', 'section', 
            'provenance', 'est_nouvelle',  # CHAMPS AJOUTÉS
            'etat', 'capacite_horaire', 'date_installation', 
            'derniere_maintenance', 'observations'
        ]
        
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: EXT-01, IMP-05, SOU-03'
            }),
            'type_machine': forms.Select(attrs={
                'class': 'form-control'
            }),
            'section': forms.Select(attrs={
                'class': 'form-control'
            }),
            'provenance': forms.Select(attrs={  # NOUVEAU
                'class': 'form-control'
            }),
            'est_nouvelle': forms.CheckboxInput(attrs={  # NOUVEAU
                'class': 'form-check-input',
                'id': 'id_est_nouvelle'
            }),
            'etat': forms.Select(attrs={
                'class': 'form-control'
            }),
            'capacite_horaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Ex: 150'
            }),
            'date_installation': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'derniere_maintenance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Particularités, historique, recommandations...'
            }),
        }
        
        labels = {
            'numero': 'Numéro de la machine',
            'type_machine': 'Type de machine',
            'section': 'Section',
            'provenance': 'Pays d\'origine',  # NOUVEAU
            'est_nouvelle': 'Machine neuve',  # NOUVEAU
            'etat': 'État actuel',
            'capacite_horaire': 'Capacité horaire (kg/h)',
            'date_installation': 'Date d\'installation',
            'derniere_maintenance': 'Dernière maintenance',
            'observations': 'Observations / Notes',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Champ caché pour zone_extrusion
        self.fields['zone_extrusion'] = forms.ModelChoiceField(
            queryset=ZoneExtrusion.objects.filter(active=True),
            required=False,
            widget=forms.HiddenInput()
        )
        
        # Si modification, pré-remplir les champs zone
        if self.instance and self.instance.pk and self.instance.zone_extrusion:
            self.fields['zone_numero'].initial = self.instance.zone_extrusion.numero
            self.fields['zone_nom'].initial = self.instance.zone_extrusion.nom
    
    def clean(self):
        cleaned_data = super().clean()
        section = cleaned_data.get('section')
        zone_numero = cleaned_data.get('zone_numero')
        zone_nom = cleaned_data.get('zone_nom')
        
        # VALIDATION : Zone obligatoire pour Extrusion
        if section == 'extrusion':
            if not zone_numero:
                raise forms.ValidationError({
                    'zone_numero': 'Le numéro de zone est obligatoire pour une machine d\'extrusion.'
                })
            if not zone_nom:
                raise forms.ValidationError({
                    'zone_nom': 'Le nom de la zone est obligatoire pour une machine d\'extrusion.'
                })
            
            # Créer ou récupérer la zone
            zone, created = ZoneExtrusion.objects.get_or_create(
                numero=zone_numero,
                defaults={'nom': zone_nom, 'nombre_machines_max': 4, 'active': True}
            )
            cleaned_data['zone_extrusion'] = zone
        else:
            # Pour les autres sections, pas de zone
            cleaned_data['zone_extrusion'] = None
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.zone_extrusion = self.cleaned_data.get('zone_extrusion')
        if commit:
            instance.save()
        return instance

# ==========================================
# FORMULAIRES ALERTES
# ==========================================

class AlerteForm(forms.ModelForm):
    """Formulaire création alerte"""
    
    class Meta:
        model = Alerte
        fields = ['titre', 'message', 'type_alerte', 'section', 'assigne_a']
        
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'type_alerte': forms.Select(attrs={'class': 'form-control'}),
            'section': forms.TextInput(attrs={'class': 'form-control'}),
            'assigne_a': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer utilisateurs assignables
        self.fields['assigne_a'].queryset = CustomUser.objects.filter(is_active=True)