# sofemci/utils/permissions.py
"""
Utilitaires de permissions par rôle
"""
from django.core.exceptions import PermissionDenied

def check_user_permission(user, required_role=None, required_roles=None):
    """Vérifie si l'utilisateur a la permission requise"""
    if not user.is_authenticated:
        return False
    
    if required_roles:
        return user.role in required_roles
    elif required_role:
        return user.role == required_role
    
    return True

def chef_extrusion_only(view_func):
    """Décorateur pour accès chefs extrusion uniquement"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_chef_extrusion() and not request.user.is_superviseur() and not request.user.is_admin():
            raise PermissionDenied("Accès réservé aux chefs d'extrusion, superviseurs et administrateurs")
        return view_func(request, *args, **kwargs)
    return wrapper

def chef_section_only(view_func):
    """Décorateur pour accès chefs autres sections uniquement"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_chef_section() and not request.user.is_superviseur() and not request.user.is_admin():
            raise PermissionDenied("Accès réservé aux chefs de section, superviseurs et administrateurs")
        return view_func(request, *args, **kwargs)
    return wrapper

def direction_or_superviseur(view_func):
    """Décorateur pour accès direction/superviseur/admin"""
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_direction() or request.user.is_superviseur() or request.user.is_admin()):
            raise PermissionDenied("Accès réservé à la direction, superviseurs et administrateurs")
        return view_func(request, *args, **kwargs)
    return wrapper