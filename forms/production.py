# sofemci/forms.py
# FORMULAIRES COMPLETS POUR SOFEM-CI - VERSION PROFESSIONNELLE

from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from ..models import (
    ProductionExtrusion,
    ProductionImprimerie,
    ProductionSoudure,
    ProductionRecyclage,
    Equipe,
    ZoneExtrusion
)


class ProductionExtrusionForm(forms.ModelForm):
    """Formulaire saisie production Extrusion - VERSION PROFESSIONNELLE (SANS validation d'unicité stricte)"""
    
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
                'id': 'extrusion_date'
            }),
            'zone': forms.Select(attrs={
                'class': 'form-control',
                'id': 'extrusion_zone'
            }),
            'equipe': forms.Select(attrs={
                'class': 'form-control',
                'id': 'extrusion_equipe'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'extrusion_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'extrusion_heure_fin'
            }),
            'matiere_premiere_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'extrusion_matiere'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '',
                'max': '200',
                'id': 'extrusion_machines'
            }),
            'nombre_machinistes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'id': 'extrusion_machinistes'
            }),
            'nombre_bobines_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'extrusion_bobines'
            }),
            'production_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'extrusion_finis'
            }),
            'production_semi_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'extrusion_semi_finis'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'extrusion_dechets'
            }),
            'chef_zone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du chef de zone',
                'id': 'extrusion_chef_zone'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Incidents, remarques, problèmes rencontrés...',
                'id': 'extrusion_observations'
            }),
        }

    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion de l'utilisateur"""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.personnaliser_selon_utilisateur()
            self.pre_remplir_champs()

    def personnaliser_selon_utilisateur(self):
        """Personnalise le queryset du champ zone selon le rôle de l'utilisateur"""
        if self.user and self.user.role == 'chef_extrusion':
            self.fields['zone'].queryset = ZoneExtrusion.objects.filter(
                chef_zone=self.user, active=True
            )
        else:
            self.fields['zone'].queryset = ZoneExtrusion.objects.filter(active=True)

    def pre_remplir_champs(self):
        """Pré-remplit automatiquement le chef de zone et la date"""
        if self.user and not self.instance.pk:
            full_name = f"{self.user.first_name} {self.user.last_name}".strip()
            self.fields['chef_zone'].initial = full_name if full_name else self.user.username
            self.fields['date_production'].initial = timezone.now().date()

    def clean_date_production(self):
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        limite = timezone.now().date() - timezone.timedelta(days=30)
        if date < limite:
            raise ValidationError("Impossible de saisir plus de 30 jours.")

        return date

    def clean(self):
        """Validation globale SANS vérification d'unicité (avec avertissement)"""
        cleaned_data = super().clean()
        
        # Avertissement pour doublons (non bloquant)
        date = cleaned_data.get('date_production')
        zone = cleaned_data.get('zone')
        equipe = cleaned_data.get('equipe')
        
        if date and zone and equipe:
            existing = ProductionExtrusion.objects.filter(
                date_production=date, 
                zone=zone, 
                equipe=equipe
            )
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                print(f"⚠️ Attention: Production existe déjà pour {date} - Zone {zone.numero} - {equipe.get_nom_display()}")
        
        return cleaned_data


class ProductionImprimerieForm(forms.ModelForm):
    """Formulaire saisie production Imprimerie - PERMET PLUSIEURS ENREGISTREMENTS"""
    
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
                'value': timezone.now().date(),
                'id': 'imprimerie_date'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '14:00',
                'id': 'imprimerie_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '22:00',
                'id': 'imprimerie_heure_fin'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '500',
                'id': 'imprimerie_machines'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'imprimerie_finies'
            }),
            'production_bobines_semi_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'imprimerie_semi_finies'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'imprimerie_dechets'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observations, incidents, remarques...',
                'id': 'imprimerie_observations'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion de l'utilisateur"""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.instance.pk:
            # Pré-remplir la date
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date SANS vérification d'unicité"""
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        # Pas de date future
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date
    
    def clean(self):
        """Validation globale avec avertissement non bloquant"""
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        date = cleaned_data.get('date_production')
        
        # Validation des heures
        if heure_debut and heure_fin:
            try:
                dt_debut = datetime.combine(datetime.min, heure_debut)
                dt_fin = datetime.combine(datetime.min, heure_fin)
                
                # J'ai ajusté la condition pour ne pas utiliser `(dt_debut - dt_fin).seconds > 10 * 3600` 
                # car le sens de la comparaison est suffisant.
                if dt_fin < dt_debut:
                    self.add_error('heure_fin', 
                        "L'heure de fin doit être après l'heure de début, ou le lendemain (si l'heure de début est plus tard que l'heure de fin).")
            except Exception as e:
                self.add_error(None, f"Erreur validation heures: {e}")
        
        # Avertissement pour doublons (non bloquant)
        if date:
            existing = ProductionImprimerie.objects.filter(date_production=date)
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                # Avertissement seulement dans la console
                print(f"⚠️ Attention: {existing.count()} production(s) imprimerie existe(nt) déjà pour {date}")
        
        return cleaned_data


class ProductionSoudureForm(forms.ModelForm):
    """Formulaire saisie production Soudure - PERMET PLUSIEURS ENREGISTREMENTS"""
    
    class Meta:
        model = ProductionSoudure
        fields = [
            'date_production', 'heure_debut', 'heure_fin',
            'nombre_machines_actives', 'production_bobines_finies_kg',
            'production_bretelles_kg', 'production_rema_kg', 'production_batta_kg',
            'production_sac_emballage_kg', 'dechets_kg', 'observations'
        ]

        widgets = {
            'date_production': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().date(),
                'id': 'soudure_date'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '14:00',
                'id': 'soudure_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '22:00',
                'id': 'soudure_heure_fin'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '500',
                'id': 'soudure_machines'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'soudure_bobines_finies'
            }),
            'production_bretelles_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'soudure_bretelles'
            }),
            'production_rema_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'soudure_rema'
            }),
            'production_batta_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'soudure_batta'
            }),
            'production_sac_emballage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'soudure_sac_emballage'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'soudure_dechets'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observations, incidents, remarques...',
                'id': 'soudure_observations'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion de l'utilisateur"""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.instance.pk:
            # Pré-remplir la date
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date SANS vérification d'unicité"""
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        # Pas de date future
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date
    
    def clean(self):
        """Validation globale avec avertissement non bloquant"""
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        date = cleaned_data.get('date_production')
        
        # Validation des heures
        if heure_debut and heure_fin:
            try:
                dt_debut = datetime.combine(datetime.min, heure_debut)
                dt_fin = datetime.combine(datetime.min, heure_fin)
                
                # J'ai ajusté la condition
                if dt_fin < dt_debut:
                    self.add_error('heure_fin', 
                        "L'heure de fin doit être après l'heure de début, ou le lendemain.")
            except Exception as e:
                self.add_error(None, f"Erreur validation heures: {e}")
        
        # Avertissement pour doublons (non bloquant)
        if date:
            existing = ProductionSoudure.objects.filter(date_production=date)
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                # Avertissement seulement dans la console
                print(f"⚠️ Attention: {existing.count()} production(s) soudure existe(nt) déjà pour {date}")
        
        return cleaned_data


class ProductionRecyclageForm(forms.ModelForm):
    """Formulaire saisie production Recyclage - PERMET PLUSIEURS ENREGISTREMENTS"""
    
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
                'id': 'recyclage_date'
            }),
            'equipe': forms.Select(attrs={
                'class': 'form-control',
                'id': 'recyclage_equipe'
            }),
            'nombre_moulinex': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '500',
                'id': 'recyclage_moulinex'
            }),
            'production_broyage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'recyclage_broyage'
            }),
            'production_bache_noir_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
                'id': 'recyclage_bache_noir'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Qualité des matières recyclées, incidents, améliorations...',
                'id': 'recyclage_observations'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion de l'utilisateur"""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.instance.pk:
            # Pré-remplir la date
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date SANS vérification d'unicité"""
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        # Pas de date future
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date
    
    def clean(self):
        """Validation globale avec avertissement non bloquant"""
        cleaned_data = super().clean()
        date = cleaned_data.get('date_production')
        equipe = cleaned_data.get('equipe')
        
        # Avertissement pour doublons (non bloquant)
        if date and equipe:
            existing = ProductionRecyclage.objects.filter(
                date_production=date, 
                equipe=equipe
            )
            
            if self.instance and self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                # Avertissement seulement dans la console
                print(f"⚠️ Attention: {existing.count()} production(s) recyclage existe(nt) déjà pour {date} - Équipe {equipe.get_nom_display()}")
        
        return cleaned_data


# ==========================================
# FORMULAIRES UTILISATEURS ET AUTRES
# ==========================================

from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from ..models.users import CustomUser

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


class CustomUserCreationForm(UserCreationForm):
    """Formulaire création utilisateur"""
    
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'telephone', 'date_embauche']
        
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class CustomUserUpdateForm(forms.ModelForm):
    """Formulaire modification utilisateur"""
    
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