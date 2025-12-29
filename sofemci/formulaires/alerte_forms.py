"""
Formulaires liés aux alertes et notifications
"""
from django import forms
from ..models import Alerte, CustomUser

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