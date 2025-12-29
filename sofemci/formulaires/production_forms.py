"""
Formulaires liés à la production (Extrusion, Imprimerie, Soudure, Recyclage)
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import (
    ProductionExtrusion, ProductionImprimerie, 
    ProductionSoudure, ProductionRecyclage, ZoneExtrusion
)

class ProductionExtrusionForm(forms.ModelForm):
    """Formulaire saisie production Extrusion"""
    
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

class ProductionImprimerieForm(forms.ModelForm):
    """Formulaire saisie production Imprimerie"""
    
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
    """Formulaire saisie production Soudure"""
    
    class Meta:
        model = ProductionSoudure
        fields = [
            'date_production',
            'heure_debut',
            'heure_fin',
            'nombre_machines_actives',
            'production_bobines_finies_kg',
            'production_bretelles_kg',
            'production_rema_kg',
            'production_batta_kg',
            'production_sac_emballage_kg',
            'dechets_kg',
            'observations',
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
                'value': '14:00'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'value': '22:00'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '8'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'production_bretelles_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'production_rema_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'production_batta_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'production_sac_emballage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observations...'
            }),
        }
    
    def clean_date_production(self):
        date = self.cleaned_data['date_production']
        
        # Pas de date future
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date

class ProductionRecyclageForm(forms.ModelForm):
    """Formulaire saisie production Recyclage"""
    
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