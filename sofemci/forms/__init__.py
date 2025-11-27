from .auth import LoginForm
from .production import (
    ProductionExtrusionForm, ProductionImprimerieForm, 
    ProductionSoudureForm, ProductionRecyclageForm, 
)
from .machines import MachineForm
from .alerts import AlerteForm

__all__ = [
    'LoginForm',
    'ProductionExtrusionForm',
    'ProductionImprimerieForm', 
    'ProductionSoudureForm',
    'ProductionRecyclageForm',
    'MachineForm',
    'AlerteForm',
]