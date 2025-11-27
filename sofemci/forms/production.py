from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from ..models import ProductionExtrusion, ProductionImprimerie, ProductionSoudure, ProductionRecyclage, Equipe, ZoneExtrusion


class ProductionExtrusionForm(forms.ModelForm):
    """Formulaire saisie production Extrusion - Version SANS validation d'unicité"""
    
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
            }),
            'zone': forms.Select(attrs={'class': 'form-control'}),
            'equipe': forms.Select(attrs={'class': 'form-control'}),
            'heure_debut': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
            }),
            'heure_fin': forms.TimeInput(attrs={
                'type': 'time',
                'class': 'form-control',
            }),
            'matiere_premiere_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'nombre_machines_actives': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '4',
            }),
            'nombre_machinistes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
            'nombre_bobines_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'production_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'production_semi_finis_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'dechets_kg': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00',
            }),
            'chef_zone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du chef de zone',
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
            full_name = f"{self.user.first_name} {self.user.last_name}".strip()
            self.fields['chef_zone'].initial = full_name if full_name else self.user.username
    
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
        """Validation SANS vérification d'unicité - Autorise tous les enregistrements"""
        cleaned_data = super().clean()
        
        # OPTIONNEL : Avertissement seulement (non bloquant)
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
                # Juste un avertissement dans la console, PAS d'erreur de validation
                existing_prod = existing.first()
                print(f"⚠️ Attention: Production existe déjà pour {date} - Zone {zone.numero} - {equipe.get_nom_display()}")
                # NE PAS lever d'exception ValidationError
        
        return cleaned_data
    
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

