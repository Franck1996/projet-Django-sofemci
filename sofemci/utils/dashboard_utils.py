import json
from decimal import Decimal

def get_chart_data_for_dashboard():
    """Données simplifiées pour graphiques"""
    return json.dumps({
        'months': ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
        'extrusion': [100, 120, 130, 110, 140, 125, 135],
        'soudure': [80, 90, 85, 95, 100, 88, 92],
        'dechets': [5, 6, 4, 7, 5, 6, 5],
        'bache_noir': [60, 65, 70, 63, 68, 66, 69],
    })

def get_analytics_kpis():
    """KPIs simplifiés pour Analytics"""
    return {
        'production_totale_mois': 15000,
        'croissance_production': 12.5,
        'taux_dechet_mois': 3.2,
        'reduction_dechets': 2.3,
        'efficacite_moyenne': 87.5,
        'amélioration_efficacite': 3.2,
        'taux_transformation': 78.5,
        'amélioration_transformation': 5.1,
    }

def get_analytics_table_data():
    """Données tableau Analytics simplifiées"""
    return {
        'extrusion': {
            'production': 8000,
            'dechets': 224,
            'taux_dechet': 2.8,
            'efficacite': 89.2,
        },
        'imprimerie': {
            'production': 3500,
            'dechets': 108.5,
            'taux_dechet': 3.1,
            'efficacite': 91.5,
        },
        'soudure': {
            'production': 2500,
            'dechets': 95,
            'taux_dechet': 3.8,
            'efficacite': 85.3,
        },
        'recyclage': {
            'production': 1000,
            'taux_transformation': 78.2,
            'rendement': 82.5,
        },
    }