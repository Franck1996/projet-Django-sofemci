# sofemci/context_processors.py
from django.conf import settings

def sofemci_config(request):
    """Injecte la configuration SOFEM-CI dans tous les templates"""
    return {
        'SOFEMCI_CONFIG': getattr(settings, 'SOFEMCI_CONFIG', {}),
        'COMPANY_NAME': getattr(settings, 'SOFEMCI_CONFIG', {}).get('COMPANY_NAME', 'SOFEM-CI'),
        'DEBUG': settings.DEBUG,
    }