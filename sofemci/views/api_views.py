"""
Vues API AJAX pour appels asynchrones
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

from .utils_views import (
    calculate_extrusion_metrics,
    calculate_imprimerie_metrics,
    calculate_soudure_metrics,
    calculate_recyclage_metrics,
)

# Ces fonctions seront déplacées ici depuis production_views.py
# Gardez les imports nécessaires

@login_required
@csrf_exempt
def api_calculs_extrusion(request):
    """API spécifique pour calculs extrusion"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=400)
    
    try:
        data = json.loads(request.body)
        return calculate_extrusion_metrics(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Ajouter d'autres APIs spécifiques si nécessaire