# sofemci/context_processors.py
"""
Processeurs de contexte pour les templates
"""
def user_permissions(request):
    """Ajoute les permissions de l'utilisateur au contexte des templates"""
    context = {}
    
    if request.user.is_authenticated:
        user = request.user
        context.update({
            'user_can_edit_extrusion': not user.is_direction() and (user.is_chef_extrusion() or user.is_superviseur() or user.is_admin()),
            'user_can_edit_sections': not user.is_direction() and (user.is_chef_section() or user.is_superviseur() or user.is_admin()),
            'user_can_view_all': user.is_direction() or user.is_superviseur() or user.is_admin(),
        })
    
    return context