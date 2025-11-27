from .auth import login_view, logout_view
from .dashboard import dashboard_view, dashboard_ia_view, dashboard_direction_view
from .production import (
    saisie_extrusion_view, saisie_sections_view,
    saisie_imprimerie_ajax, saisie_soudure_ajax, saisie_recyclage_ajax,
    api_production_details, api_valider_production
)
from .machines import (
    machines_list_view, machine_create_view, machine_edit_view,
    machine_delete_view, machine_detail_view, machine_detail_ia_view,
    machine_change_status_ajax, enregistrer_maintenance_view, enregistrer_panne_view,
    simuler_capteurs_view
)
from .alerts import (
    liste_alertes_ia, traiter_alerte_ia, lancer_analyse_complete
)

# Fonctions utilitaires
from .dashboard import (
    get_production_totale_jour, get_production_section_jour, get_dechets_totaux_jour,
    get_efficacite_moyenne_jour, get_machines_stats, get_zones_performance,
    get_extrusion_details_jour, get_imprimerie_details_jour, get_soudure_details_jour,
    get_recyclage_details_jour,
)

__all__ = [
    'login_view', 'logout_view',
    'dashboard_view', 'dashboard_ia_view', 'dashboard_direction_view',
    'saisie_extrusion_view', 'saisie_sections_view',
    'machines_list_view', 'machine_create_view', 'machine_edit_view',
    'machine_delete_view', 'machine_detail_view', 'machine_detail_ia_view',
    'liste_alertes_ia', 'traiter_alerte_ia', 'lancer_analyse_complete',
]