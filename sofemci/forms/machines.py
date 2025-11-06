from django import forms
from django.core.exceptions import ValidationError

from ..models import Machine, ZoneExtrusion

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
            'provenance', 'est_nouvelle',
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
            'provenance': forms.Select(attrs={
                'class': 'form-control'
            }),
            'est_nouvelle': forms.CheckboxInput(attrs={
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
            'provenance': 'Pays d\'origine',
            'est_nouvelle': 'Machine neuve',
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
                raise ValidationError({
                    'zone_numero': 'Le numéro de zone est obligatoire pour une machine d\'extrusion.'
                })
            if not zone_nom:
                raise ValidationError({
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