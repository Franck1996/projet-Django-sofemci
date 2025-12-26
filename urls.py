# sofemci/urls.py - VERSION CORRIGÉE SANS BOUCLE
from django.contrib import admin
from django.urls import path, include  
from django.conf import settings
from django.conf.urls.static import static

# Import des vues principales
from .views.auth import login_view, logout_view
from .views.dashboard import dashboard_view, dashboard_ia_view
from .views.production import (
    saisie_extrusion_view, 
    saisie_sections_view,
    saisie_imprimerie_ajax,
    saisie_soudure_ajax,
    saisie_recyclage_ajax,
    api_valider_production
)
from .views.machines import (
    machines_list_view, machine_create_view, machine_edit_view,
    machine_delete_view, machine_detail_view
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
    path('', login_view, name='home'),  # ← CORRECTION ICI
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # ==========================================
    # DASHBOARDS
    # ==========================================
    path('dashboard/', dashboard_view, name='dashboard'),
    path('dashboard/ia/', dashboard_ia_view, name='dashboard_ia'),
    
    # ==========================================
    # SAISIE PRODUCTION
    # ==========================================
    path('saisie/extrusion/', saisie_extrusion_view, name='saisie_extrusion'),
    path('saisie/sections/', saisie_sections_view, name='saisie_sections'),
    
    # ==========================================
    # APIs PRODUCTION
    # ==========================================
    path('api/production/<str:section>/<int:production_id>/valider/', 
         api_valider_production, name='api_valider_production'),
    
    # APIs AJAX
    path('ajax/saisie/imprimerie/', saisie_imprimerie_ajax, name='ajax_imprimerie'),
    path('ajax/saisie/soudure/', saisie_soudure_ajax, name='ajax_soudure'),
    path('ajax/saisie/recyclage/', saisie_recyclage_ajax, name='ajax_recyclage'),
    
    # ==========================================
    # GESTION DES MACHINES
    # ==========================================
    path('machines/', machines_list_view, name='machines_list'),
    path('machines/create/', machine_create_view, name='machine_create'),
    path('machines/<int:machine_id>/', machine_detail_view, name='machine_detail'),
    path('machines/<int:machine_id>/edit/', machine_edit_view, name='machine_edit'),
    path('machines/<int:machine_id>/delete/', machine_delete_view, name='machine_delete'),
]

# ==========================================
# APIs SUPPLÉMENTAIRES (temporaires)
# ==========================================
from django.http import JsonResponse

urlpatterns += [
    path('api/calculs/', lambda request: JsonResponse({'success': False, 'message': 'À implémenter'}), 
         name='api_calculs'),
    path('api/dashboard/', lambda request: JsonResponse({'success': False, 'message': 'À implémenter'}), 
         name='api_dashboard'),
]

# ==========================================
# FICHIERS STATIQUES (Développement)
# ==========================================
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
    
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==========================================
# CONFIGURATION ADMIN
# ==========================================
admin.site.site_header = "Administration SOFEM-CI"
admin.site.site_title = "SOFEM-CI Admin"
admin.site.index_title = "Gestion de l'usine d'emballages plastiques"
