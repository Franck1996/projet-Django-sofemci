# sofemci/urls.py
# TOUTES LES URLS DE L'APPLICATION SOFEM-CI - VERSION RÉORGANISÉE

from django.contrib import admin
from django.urls import path, include  # AJOUTEZ include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Import des vues depuis les nouveaux modules
from .views.auth import login_view, logout_view
from .views.dashboard import dashboard_view, dashboard_ia_view, dashboard_direction_view
from .views.production import (
    saisie_extrusion_view, saisie_sections_view, 
    saisie_imprimerie_ajax, saisie_soudure_ajax, saisie_recyclage_ajax,
    api_production_details, api_valider_production
)
from .views.machines import (
    machines_list_view, machine_create_view, machine_edit_view,
    machine_delete_view, machine_detail_view, machine_detail_ia_view,
    machine_change_status_ajax, enregistrer_maintenance_view, enregistrer_panne_view,
    simuler_capteurs_view
)
from .views.alerts import (
    liste_alertes_ia, traiter_alerte_ia, lancer_analyse_complete
)

urlpatterns = [
    # ==========================================
    # ADMIN DJANGO
    # ==========================================
    path('admin/', admin.site.urls),
    
    # ==========================================
    # AUTHENTIFICATION
    # ==========================================
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)), 
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # ==========================================
    # DASHBOARDS
    # ==========================================
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/direction/', dashboard_direction_view, name='dashboard_direction'),
    path('dashboard/ia/', dashboard_ia_view, name='dashboard_ia'),
    
    # ==========================================
    # SAISIE PRODUCTION
    # ==========================================
    path('saisie/extrusion/', saisie_extrusion_view, name='saisie_extrusion'),
    path('saisie/sections/', saisie_sections_view, name='saisie_sections'),
    
    # AJAX pour saisie sections
    path('ajax/saisie/imprimerie/', saisie_imprimerie_ajax, name='ajax_imprimerie'),
    path('ajax/saisie/soudure/', saisie_soudure_ajax, name='ajax_soudure'),
    path('ajax/saisie/recyclage/', saisie_recyclage_ajax, name='ajax_recyclage'),
    
    # APIs Production
    path('api/production/<str:section>/<int:production_id>/', api_production_details, name='api_production_details'),
    path('api/production/<str:section>/<int:production_id>/valider/', api_valider_production, name='api_valider_production'),
    
    # ==========================================
    # GESTION DES MACHINES
    # ==========================================
    path('machines/', machines_list_view, name='machines_list'),
    path('machines/create/', machine_create_view, name='machine_create'),
    path('machines/<int:machine_id>/', machine_detail_view, name='machine_detail'),
    path('machines/<int:machine_id>/edit/', machine_edit_view, name='machine_edit'),
    path('machines/<int:machine_id>/delete/', machine_delete_view, name='machine_delete'),
    path('machines/<int:machine_id>/change-status/', machine_change_status_ajax, name='machine_change_status'),
    
    # ==========================================
    # MODULE IA - MAINTENANCE PRÉDICTIVE
    # ==========================================
    path('ia/dashboard/', dashboard_ia_view, name='dashboard_ia'),
    path('ia/machine/<int:machine_id>/', machine_detail_ia_view, name='machine_detail_ia'),
    path('ia/analyser/', lancer_analyse_complete, name='lancer_analyse_complete'),
    
    # Gestion maintenances et pannes
    path('ia/machine/<int:machine_id>/maintenance/', enregistrer_maintenance_view, name='enregistrer_maintenance'),
    path('ia/machine/<int:machine_id>/panne/', enregistrer_panne_view, name='enregistrer_panne'),
    path('ia/machine/<int:machine_id>/simuler/', simuler_capteurs_view, name='simuler_capteurs'),
    
    # Alertes IA
    path('ia/alertes/', liste_alertes_ia, name='liste_alertes_ia'),
    path('ia/alerte/<int:alerte_id>/traiter/', traiter_alerte_ia, name='traiter_alerte_ia'),
    
    # ==========================================
    # API POUR CALCULS TEMPS RÉEL (FONCTIONS SIMPLIFIÉES)
    # ==========================================
    path('api/calculs/', dashboard_view, name='api_calculs'),  # Redirigé vers dashboard
    path('api/dashboard/', dashboard_view, name='api_dashboard'),  # Redirigé vers dashboard
    
    # APIs IA (fonctions simplifiées)
    path('api/ia/machines-status/', dashboard_ia_view, name='api_machines_status'),  # Redirigé vers dashboard IA
    path('api/ia/alertes-count/', liste_alertes_ia, name='api_alertes_count'),  # Redirigé vers alertes
    path('api/ia/statistiques/', dashboard_ia_view, name='api_statistiques_ia'),  # Redirigé vers dashboard IA
    
    # API Zones (fonction simplifiée)
    path('api/zones/create/', machines_list_view, name='api_create_zone'),  # Redirigé vers machines
]

# ==========================================
# DEBUG TOOLBAR (Development only)
# ==========================================
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

# ==========================================
# FICHIERS STATIQUES ET MÉDIA (DÉVELOPPEMENT)
# ==========================================
if settings.DEBUG:
    # Servir les fichiers média (uploads utilisateurs)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Servir les fichiers statiques (CSS, JS, Images, Logos)
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()

# ==========================================
# CONFIGURATION ADMIN
# ==========================================
admin.site.site_header = "Administration SOFEM-CI"
admin.site.site_title = "SOFEM-CI Admin"
admin.site.index_title = "Gestion de l'usine d'emballages plastiques"