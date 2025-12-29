"""
Importation de tous les formulaires pour un accès facile
"""
# Ré-export pour compatibilité rétroactive
from .auth_forms import LoginForm
from .production_forms import (
    ProductionExtrusionForm,
    ProductionImprimerieForm,
    ProductionSoudureForm,
    ProductionRecyclageForm
)
from .machine_forms import MachineForm
from .alerte_forms import AlerteForm
from .utilisateur_forms import CustomUserForm

__all__ = [
    'LoginForm',
    'ProductionExtrusionForm',
    'ProductionImprimerieForm',
    'ProductionSoudureForm',
    'ProductionRecyclageForm',
    'MachineForm',
    'AlerteForm',
    'CustomUserForm',
]