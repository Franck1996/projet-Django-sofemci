# sofemci/urls.py
# TOUTES LES URLS DE L'APPLICATION SOFEM-CI

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    # ==========================================
    # ADMIN DJANGO
    # ==========================================
    path('admin/', admin.site.urls),

    # ==========================================
    # AUTHENTIFICATION
    # ==========================================
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ==========================================
    # DASHBOARDS
    # ==========================================
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/direction/', views.dashboard_direction_view, name='dashboard_direction'),

    # ==========================================
    # SAISIE PRODUCTION
    # ==========================================
    path('saisie/extrusion/', views.saisie_extrusion_view, name='saisie_extrusion'),
    path('saisie/sections/', views.saisie_sections_view, name='saisie_sections'),

    # AJAX
    path('ajax/saisie/imprimerie/', views.saisie_imprimerie_ajax, name='ajax_imprimerie'),
    path('ajax/saisie/soudure/', views.saisie_soudure_ajax, name='ajax_soudure'),
    path('ajax/saisie/recyclage/', views.saisie_recyclage_ajax, name='ajax_recyclage'),

    # ==========================================
    # MACHINES
    # ==========================================
    path('machines/', views.machines_list_view, name='machines_list'),
    path('machines/create/', views.machine_create_view, name='machine_create'),
    path('machines/<int:machine_id>/', views.machine_detail_view, name='machine_detail'),
    path('machines/<int:machine_id>/edit/', views.machine_edit_view, name='machine_edit'),
    path('machines/<int:machine_id>/delete/', views.machine_delete_view, name='machine_delete'),
    path('machines/<int:machine_id>/change-status/', views.machine_change_status_ajax, name='machine_change_status'),

    path('api/zones/create/', views.api_create_zone, name='api_create_zone'),

    # ==========================================
    # API
    # ==========================================
    path('api/calculs/', views.api_calculs_production, name='api_calculs'),
    path('api/dashboard/', views.api_dashboard_data, name='api_dashboard'),

    # ==========================================
    # IA - MAINTENANCE PRÉDICTIVE
    # ==========================================
    path('ia/dashboard/', views.dashboard_ia_view, name='dashboard_ia'),
    path('ia/machine/<int:machine_id>/', views.machine_detail_ia_view, name='machine_detail_ia'),
    path('ia/analyser/', views.lancer_analyse_complete, name='lancer_analyse_complete'),

    path('ia/machine/<int:machine_id>/maintenance/', views.enregistrer_maintenance_view, name='enregistrer_maintenance'),
    path('ia/machine/<int:machine_id>/panne/', views.enregistrer_panne_view, name='enregistrer_panne'),
    path('ia/machine/<int:machine_id>/simuler/', views.simuler_capteurs_view, name='simuler_capteurs'),

    path('ia/alertes/', views.liste_alertes_ia, name='liste_alertes_ia'),
    path('ia/alerte/<int:alerte_id>/traiter/', views.traiter_alerte_ia, name='traiter_alerte_ia'),

    path('api/ia/machines-status/', views.api_machines_status, name='api_machines_status'),
    path('api/ia/alertes-count/', views.api_alertes_count, name='api_alertes_count'),
    path('api/ia/statistiques/', views.api_statistiques_ia, name='api_statistiques_ia'),
]

# ==========================================
# DEBUG TOOLBAR (OBLIGATOIRE)
# ==========================================
if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==========================================
# CONFIGURATION ADMIN
# ==========================================
admin.site.site_header = "Administration SOFEM-CI"
admin.site.site_title = "SOFEM-CI Admin"
admin.site.index_title = "Gestion de l'usine d'emballages plastiques"
