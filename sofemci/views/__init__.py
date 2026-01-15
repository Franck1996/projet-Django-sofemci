"""
Importation centralisée de toutes les vues
"""

# Import des vues d'authentification
from .auth_views import login_view, logout_view

# Import des vues dashboard
from .dashboard_views import (
    dashboard_view,
)

# Import des vues de production
from .production_views import (
    saisie_extrusion_view,
    saisie_sections_view,
)

# Import des vues machines
from .machine_views import (
    machines_list_view,
    machine_create_view,
    machine_edit_view,
    machine_delete_view,
    machine_detail_view,
    machine_change_status_ajax,
    api_create_zone,
)

# Import des vues IA
from .ia_views import (
    dashboard_ia_view,
    machine_detail_ia_view,
    lancer_analyse_complete,
    enregistrer_maintenance_view,
    enregistrer_panne_view,
    traiter_alerte_ia,
    liste_alertes_ia,
    simuler_capteurs_view,
    api_machines_status,
    api_alertes_count,
    api_statistiques_ia,
)

# Import des fonctions utilitaires
from .utils_views import (
    get_production_totale_jour,
    get_production_section_jour,
    get_dechets_totaux_jour,
    get_efficacite_moyenne_jour,
    get_machines_stats,
    get_zones_performance,
    get_zones_utilisateur,
    get_extrusion_details_jour,
    get_imprimerie_details_jour,
    get_soudure_details_jour,
    get_recyclage_details_jour,
    calculate_extrusion_metrics,
    calculate_imprimerie_metrics,
    calculate_soudure_metrics,
    calculate_recyclage_metrics,
    get_ca_mensuel,
    get_production_totale_periode,
    calculate_percentage_of_goal,
    get_efficacite_globale_periode,
    get_cout_production_moyen,
    get_performances_sections,
    get_production_par_section,
    get_production_section_periode,
    get_chart_data_for_dashboard,
    get_analytics_kpis,
    get_analytics_table_data,
    get_mois_disponibles,
    get_nom_mois,
)

# Export de toutes les vues
__all__ = [
    # Auth
    'login_view',
    'logout_view',
    
    # Dashboard
    'dashboard_view',
    
    # Production
    'saisie_extrusion_view',
    'saisie_sections_view',
    'saisie_imprimerie_ajax',
    'saisie_soudure_ajax',
    'saisie_recyclage_ajax',
    'api_calculs_production',
    
    # Machines
    'machines_list_view',
    'machine_create_view',
    'machine_edit_view',
    'machine_delete_view',
    'machine_detail_view',
    'machine_change_status_ajax',
    'api_create_zone',
    
    # IA
    'dashboard_ia_view',
    'machine_detail_ia_view',
    'lancer_analyse_complete',
    'enregistrer_maintenance_view',
    'enregistrer_panne_view',
    'traiter_alerte_ia',
    'liste_alertes_ia',
    'simuler_capteurs_view',
    'api_machines_status',
    'api_alertes_count',
    'api_statistiques_ia',
    
    # Utilitaires
    'get_production_totale_jour',
    'get_production_section_jour',
    'get_dechets_totaux_jour',
    'get_efficacite_moyenne_jour',
    'get_machines_stats',
    'get_zones_performance',
    'get_zones_utilisateur',
    'get_extrusion_details_jour',
    'get_imprimerie_details_jour',
    'get_soudure_details_jour',
    'get_recyclage_details_jour',
    'calculate_extrusion_metrics',
    'calculate_imprimerie_metrics',
    'calculate_soudure_metrics',
    'calculate_recyclage_metrics',
    'get_ca_mensuel',
    'get_production_totale_periode',
    'calculate_percentage_of_goal',
    'get_efficacite_globale_periode',
    'get_cout_production_moyen',
    'get_performances_sections',
    'get_production_par_section',
    'get_production_section_periode',
    'get_chart_data_for_dashboard',
    'get_analytics_kpis',
    'get_analytics_table_data',
    'get_mois_disponibles',
    'get_nom_mois',
]