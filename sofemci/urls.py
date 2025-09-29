# sofemci/urls.py
# 🎯 TOUTES LES URLS DE L'APPLICATION SOFEM-CI

from django.contrib import admin
from django.urls import path
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
    path('dashboard/', views.dashboard_view, name='dashboard'),                    # Maquette dashboard_principal
    path('dashboard/direction/', views.dashboard_direction_view, name='dashboard_direction'),  # Maquette dashboard_direction
    
    # ==========================================
    # SAISIE PRODUCTION
    # ==========================================
    # Extrusion
    path('saisie/extrusion/', views.saisie_extrusion_view, name='saisie_extrusion'),  # Maquette saisie_extrusion
    
    # Autres sections (onglets)
    path('saisie/sections/', views.saisie_sections_view, name='saisie_sections'),     # Maquette saisie_sections_autres
    
    # AJAX pour saisie sections
    path('ajax/saisie/imprimerie/', views.saisie_imprimerie_ajax, name='ajax_imprimerie'),
    path('ajax/saisie/soudure/', views.saisie_soudure_ajax, name='ajax_soudure'),
    path('ajax/saisie/recyclage/', views.saisie_recyclage_ajax, name='ajax_recyclage'),
    
    # ==========================================
    # HISTORIQUE ET RAPPORTS
    # ==========================================
    path('historique/', views.historique_view, name='historique'),                # Maquette historique_production
    path('rapports/', views.rapports_view, name='rapports'),
    
    # ==========================================
    # API POUR CALCULS TEMPS RÉEL
    # ==========================================
    path('api/calculs/', views.api_calculs_production, name='api_calculs'),       # Pour calculs dans vos maquettes
    path('api/dashboard/', views.api_dashboard_data, name='api_dashboard'),       # Pour mise à jour dashboard
    
    # ==========================================
    # GESTION (OPTIONNEL)
    # ==========================================
    # Ces URLs seront ajoutées plus tard si besoin
    # path('users/', views.users_list, name='users_list'),
    # path('machines/', views.machines_list, name='machines_list'),
    # path('alertes/', views.alertes_list, name='alertes_list'),
]

# ==========================================
# FICHIERS STATIQUES ET MÉDIA
# ==========================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ==========================================
# CONFIGURATION ADMIN
# ==========================================
admin.site.site_header = "Administration SOFEM-CI"
admin.site.site_title = "SOFEM-CI Admin"
admin.site.index_title = "Gestion de l'usine d'emballages plastiques"