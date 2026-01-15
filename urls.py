"""
P_8_FINAL/urls.py - URLs principales du projet SOFEM-CI
Version corrigée avec la nouvelle structure organisée des vues
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

# ==========================================
# IMPORTS DES VUES DEPUIS LA STRUCTURE ORGANISÉE
# ==========================================

# Import depuis sofemci.views (depuis le __init__.py du dossier views)
from sofemci.views import production_views
from sofemci.views import dashboard_views
from sofemci.views import auth_views
from sofemci.views import (
    # Vues d'authentification
    
    
    # Vues dashboard
    dashboard_ia_view,
    
    # Vues production
    saisie_extrusion_view, saisie_sections_view,
    
    # Vues machines
    machines_list_view, machine_create_view, machine_edit_view,
    machine_delete_view, machine_detail_view, machine_change_status_ajax,
    
    # APIs utilitaires
    api_create_zone, 
    
    # Vues IA/maintenance prédictive
    lancer_analyse_complete, enregistrer_maintenance_view, 
    enregistrer_panne_view, traiter_alerte_ia, liste_alertes_ia,
    simuler_capteurs_view, api_machines_status, api_alertes_count,
    api_statistiques_ia
)

# ==========================================
# URLS PRINCIPALES
# ==========================================

urlpatterns = [
    # ==========================================
    # ADMIN DJANGO
    # ==========================================
    path('admin/', admin.site.urls),
    
    # ==========================================
    # AUTHENTIFICATION
    # ==========================================
    path('', auth_views.login_view, name='login'),
    path('login/', auth_views.login_view, name='login'),
    path('logout/', auth_views.logout_view, name='logout'),
    
    # ==========================================
    # DASHBOARDS
    # ==========================================
    path('dashboard/', dashboard_views.dashboard_view, name='dashboard'),
    path('dashboard/ia/', dashboard_ia_view, name='dashboard_ia'),
    
    # ==========================================
    # SAISIE PRODUCTION
    # ==========================================
    path('saisie/extrusion/', production_views.saisie_extrusion_view, name='saisie_extrusion'),
    path('saisie/sections/', production_views.saisie_sections_view, name='saisie_sections'),
    
   
    
    
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
    # APIs UTILITAIRES
    # ==========================================
    path('api/zones/create/', api_create_zone, name='api_create_zone'),
    
    # ==========================================
    # IA - MAINTENANCE PRÉDICTIVE
    # ==========================================
    path('ia/analyser/', lancer_analyse_complete, name='lancer_analyse_complete'),
    path('ia/machine/<int:machine_id>/maintenance/', enregistrer_maintenance_view, name='enregistrer_maintenance'),
    path('ia/machine/<int:machine_id>/panne/', enregistrer_panne_view, name='enregistrer_panne'),
    path('ia/machine/<int:machine_id>/simuler/', simuler_capteurs_view, name='simuler_capteurs'),
    path('ia/alertes/', liste_alertes_ia, name='liste_alertes_ia'),
    path('ia/alerte/<int:alerte_id>/traiter/', traiter_alerte_ia, name='traiter_alerte_ia'),
    
    # ==========================================
    # APIs IA
    # ==========================================
    path('api/ia/machines-status/', api_machines_status, name='api_machines_status'),
    path('api/ia/alertes-count/', api_alertes_count, name='api_alertes_count'),
    path('api/ia/statistiques/', api_statistiques_ia, name='api_statistiques_ia'),
]


# ==========================================
# DEBUG TOOLBAR (Développement)
# ==========================================
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    
    # Fichiers statiques/media en développement
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==========================================
# CONFIGURATION ADMIN
# ==========================================
admin.site.site_header = "Administration SOFEM-CI"
admin.site.site_title = "SOFEM-CI Admin"
admin.site.index_title = "Gestion de l'usine d'emballages plastiques"