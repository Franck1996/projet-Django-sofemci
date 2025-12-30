# sofemci/formulaires.py
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
    """Formulaire saisie production Extrusion - SANS CONTRAINTES MAX"""
    
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
                'class': 'form-control form-control-lg',
                'id': 'date_production'
            }),
            'zone': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'id': 'zone'
            }),
            'equipe': forms.Select(attrs={
                'class': 'form-control form-control-lg',
                'id': 'equipe'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control form-control-lg',
                'id': 'heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control form-control-lg',
                'id': 'heure_fin'
            }),
            'matiere_premiere_kg': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'matiere_premiere_kg'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0',
                'id': 'nombre_machines_actives'
            }),
            'nombre_machinistes': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': '0',
                'id': 'nombre_machinistes'
            }),
            'nombre_bobines_kg': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'nombre_bobines_kg'
            }),
            'production_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'production_finis_kg'
            }),
            'production_semi_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'production_semi_finis_kg'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control form-control-lg',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'dechets_kg'
            }),
            'chef_zone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Nom du chef de zone',
                'id': 'chef_zone'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Incidents, remarques, problèmes rencontrés...',
                'id': 'observations'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion de l'utilisateur"""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.instance.pk:
            full_name = f"{self.user.first_name} {self.user.last_name}".strip()
            self.fields['chef_zone'].initial = full_name if full_name else self.user.username
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date"""
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
        """Validation globale avec vérifications métier"""
        cleaned_data = super().clean()
        
        # Récupération des valeurs
        matiere = cleaned_data.get('matiere_premiere_kg')
        finis = cleaned_data.get('production_finis_kg')
        semi_finis = cleaned_data.get('production_semi_finis_kg')
        dechets = cleaned_data.get('dechets_kg')
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        
        # 1. Validation rendement matière
        if matiere and finis and semi_finis:
            production_totale = finis + semi_finis
            if production_totale > matiere:
                self.add_error('matiere_premiere_kg',
                    f"Erreur: Production totale ({production_totale} kg) > Matière première ({matiere} kg)")
                self.add_error('production_finis_kg',
                    "Vérifiez la cohérence avec la matière première")
        
        # 2. Validation déchets cohérents
        if matiere and dechets:
            if dechets > matiere:
                self.add_error('dechets_kg',
                    f"Erreur: Déchets ({dechets} kg) > Matière première ({matiere} kg)")
        
        # 3. Validation des heures
        if heure_debut and heure_fin:
            try:
                dt_debut = datetime.combine(datetime.min, heure_debut)
                dt_fin = datetime.combine(datetime.min, heure_fin)
                
                if dt_fin <= dt_debut:
                    # Travail de nuit : ajouter 24h
                    dt_fin_adj = datetime.combine(datetime.min, heure_fin)
                    dt_fin_adj = dt_fin_adj.replace(hour=dt_fin_adj.hour + 24)
                    duree = (dt_fin_adj - dt_debut).seconds / 3600
                    
                    if duree > 12:
                        self.add_error('heure_fin',
                            "Durée de travail trop longue (>12h). Vérifiez les heures.")
                else:
                    duree = (dt_fin - dt_debut).seconds / 3600
                    if duree > 12:
                        self.add_error('heure_fin',
                            "Durée de travail trop longue (>12h).")
                    
                    if duree < 1:
                        self.add_error('heure_fin',
                            "Durée de travail trop courte (<1h).")
            except Exception as e:
                self.add_error(None, f"Erreur validation heures: {e}")
        
        # 4. Validation machines vs machinistes (alerte seulement)
        machines = cleaned_data.get('nombre_machines_actives')
        machinistes = cleaned_data.get('nombre_machinistes')
        
        if machines and machinistes:
            if machinistes < machines:
                # Avertissement seulement, pas d'erreur bloquante
                print(f"Avertissement: {machinistes} machinistes pour {machines} machines")
            elif machinistes > machines * 3:
                # Avertissement seulement, pas d'erreur bloquante
                print(f"Avertissement: Beaucoup de machinistes ({machinistes}) pour {machines} machines")
        
        # 5. Validation valeurs positives
        if matiere and matiere < 0:
            self.add_error('matiere_premiere_kg', "La matière première ne peut pas être négative")
        if finis and finis < 0:
            self.add_error('production_finis_kg', "Les produits finis ne peuvent pas être négatifs")
        if semi_finis and semi_finis < 0:
            self.add_error('production_semi_finis_kg', "Les produits semi-finis ne peuvent pas être négatifs")
        if dechets and dechets < 0:
            self.add_error('dechets_kg', "Les déchets ne peuvent pas être négatifs")
        if machines and machines < 0:
            self.add_error('nombre_machines_actives', "Le nombre de machines ne peut pas être négatif")
        if machinistes and machinistes < 0:
            self.add_error('nombre_machinistes', "Le nombre de machinistes ne peut pas être négatif")
        
        return cleaned_data


class ProductionImprimerieForm(forms.ModelForm):
    """Formulaire saisie production Imprimerie - SANS CONTRAINTES MAX"""
    
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
                'id': 'imprimerie_date'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'imprimerie_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'imprimerie_heure_fin'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'id': 'imprimerie_machines'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'imprimerie_finies'
            }),
            'production_bobines_semi_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'imprimerie_semi_finies'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
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
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date"""
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date
    
    def clean(self):
        """Validation globale avec vérifications métier"""
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        machines = cleaned_data.get('nombre_machines_actives')
        finies = cleaned_data.get('production_bobines_finies_kg')
        semi_finies = cleaned_data.get('production_bobines_semi_finies_kg')
        dechets = cleaned_data.get('dechets_kg')
        
        # Validation des heures
        if heure_debut and heure_fin:
            try:
                dt_debut = datetime.combine(datetime.min, heure_debut)
                dt_fin = datetime.combine(datetime.min, heure_fin)
                
                if dt_fin <= dt_debut:
                    dt_fin_adj = datetime.combine(datetime.min, heure_fin)
                    dt_fin_adj = dt_fin_adj.replace(hour=dt_fin_adj.hour + 24)
                    duree = (dt_fin_adj - dt_debut).seconds / 3600
                    
                    if duree > 12:
                        self.add_error('heure_fin',
                            "Durée de travail trop longue (>12h). Vérifiez les heures.")
                else:
                    duree = (dt_fin - dt_debut).seconds / 3600
                    if duree > 12:
                        self.add_error('heure_fin', "Durée de travail trop longue (>12h).")
                    
                    if duree < 1:
                        self.add_error('heure_fin', "Durée de travail trop courte (<1h).")
            except Exception as e:
                self.add_error(None, f"Erreur validation heures: {e}")
        
        # Validation valeurs positives
        if machines and machines < 0:
            self.add_error('nombre_machines_actives', "Le nombre de machines ne peut pas être négatif")
        if finies and finies < 0:
            self.add_error('production_bobines_finies_kg', "Les bobines finies ne peuvent pas être négatives")
        if semi_finies and semi_finies < 0:
            self.add_error('production_bobines_semi_finies_kg', "Les bobines semi-finies ne peuvent pas être négatives")
        if dechets and dechets < 0:
            self.add_error('dechets_kg', "Les déchets ne peuvent pas être négatifs")
        
        return cleaned_data


class ProductionSoudureForm(forms.ModelForm):
    """Formulaire saisie production Soudure - SANS CONTRAINTES MAX"""
    
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
                'id': 'soudure_date'
            }),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'soudure_heure_debut'
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
                'id': 'soudure_heure_fin'
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'id': 'soudure_machines'
            }),
            'production_bobines_finies_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'soudure_bobines_finies'
            }),
            'production_bretelles_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'soudure_bretelles'
            }),
            'production_rema_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'soudure_rema'
            }),
            'production_batta_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'soudure_batta'
            }),
            'production_sac_emballage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'soudure_sac_emballage'
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
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
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date"""
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date
    
    def clean(self):
        """Validation globale avec vérifications métier"""
        cleaned_data = super().clean()
        heure_debut = cleaned_data.get('heure_debut')
        heure_fin = cleaned_data.get('heure_fin')
        machines = cleaned_data.get('nombre_machines_actives')
        finies = cleaned_data.get('production_bobines_finies_kg')
        dechets = cleaned_data.get('dechets_kg')
        
        # Validation des heures
        if heure_debut and heure_fin:
            try:
                dt_debut = datetime.combine(datetime.min, heure_debut)
                dt_fin = datetime.combine(datetime.min, heure_fin)
                
                if dt_fin <= dt_debut:
                    dt_fin_adj = datetime.combine(datetime.min, heure_fin)
                    dt_fin_adj = dt_fin_adj.replace(hour=dt_fin_adj.hour + 24)
                    duree = (dt_fin_adj - dt_debut).seconds / 3600
                    
                    if duree > 12:
                        self.add_error('heure_fin',
                            "Durée de travail trop longue (>12h). Vérifiez les heures.")
                else:
                    duree = (dt_fin - dt_debut).seconds / 3600
                    if duree > 12:
                        self.add_error('heure_fin', "Durée de travail trop longue (>12h).")
                    
                    if duree < 1:
                        self.add_error('heure_fin', "Durée de travail trop courte (<1h).")
            except Exception as e:
                self.add_error(None, f"Erreur validation heures: {e}")
        
        # Validation valeurs positives
        if machines and machines < 0:
            self.add_error('nombre_machines_actives', "Le nombre de machines ne peut pas être négatif")
        if finies and finies < 0:
            self.add_error('production_bobines_finies_kg', "Les bobines finies ne peuvent pas être négatives")
        if dechets and dechets < 0:
            self.add_error('dechets_kg', "Les déchets ne peuvent pas être négatifs")
        
        return cleaned_data


class ProductionRecyclageForm(forms.ModelForm):
    """Formulaire saisie production Recyclage - SANS CONTRAINTES MAX"""
    
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
                'id': 'recyclage_date'
            }),
            'equipe': forms.Select(attrs={
                'class': 'form-control',
                'id': 'recyclage_equipe'
            }),
            'nombre_moulinex': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'id': 'recyclage_moulinex'
            }),
            'production_broyage_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'recyclage_broyage'
            }),
            'production_bache_noir_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00',
                'id': 'recyclage_bache_noir'
            }),
            'observations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes, incidents, remarques...',
                'id': 'recyclage_observations'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        """Initialisation avec gestion de l'utilisateur"""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.instance.pk:
            self.fields['date_production'].initial = timezone.now().date()
    
    def clean_date_production(self):
        """Validation de la date"""
        date = self.cleaned_data['date_production']
        
        if not date:
            raise ValidationError("La date de production est obligatoire.")
        
        if date > timezone.now().date():
            raise ValidationError("Impossible de saisir pour le futur.")
        
        return date
    
    def clean(self):
        """Validation globale avec vérifications métier"""
        cleaned_data = super().clean()
        production_broyage = cleaned_data.get('production_broyage_kg')
        production_bache = cleaned_data.get('production_bache_noir_kg')
        moulinex = cleaned_data.get('nombre_moulinex')
        
        # Validation transformation
        if production_broyage and production_bache:
            taux_transformation = (production_bache / production_broyage) * 100
            if taux_transformation > 100:
                self.add_error('production_bache_noir_kg',
                    f"Erreur: Bâche ({production_bache} kg) > Broyage ({production_broyage} kg)")
        
        # Validation valeurs positives
        if production_broyage and production_broyage < 0:
            self.add_error('production_broyage_kg', "La production broyage ne peut pas être négative")
        if production_bache and production_bache < 0:
            self.add_error('production_bache_noir_kg', "La bâche noire ne peut pas être négative")
        if moulinex and moulinex < 0:
            self.add_error('nombre_moulinex', "Le nombre de moulinex ne peut pas être négatif")
        
        return cleaned_data