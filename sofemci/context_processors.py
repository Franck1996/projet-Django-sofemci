# sofemci/context_processors.py
"""
Processeurs de contexte pour SOFEM-CI
"""

def user_access_context(request):
    """Ajoute les informations d'accès utilisateur au contexte"""
    if request.user.is_authenticated:
        user_role = request.user.role
        
        # Déterminer les permissions
        if user_role in ['CHEF_RECYCL', 'CHEF_IMPRIM', 'CHEF_SOUD']:
            show_extrusion = False
            show_other_sections = True
        elif user_role in ['CHEF_EXT1', 'CHEF_EXT2', 'CHEF_EXT3', 'CHEF_EXT4', 'CHEF_EXT5']:
            show_extrusion = True
            show_other_sections = False
        elif user_role == 'DIRECTION':
            show_extrusion = True
            show_other_sections = True
        elif user_role in ['ADMIN', 'SUPERVISEUR']:
            show_extrusion = True
            show_other_sections = True
        else:
            show_extrusion = True
            show_other_sections = True
        
        return {
            'user_role': user_role,
            'user_show_extrusion': show_extrusion,
            'user_show_other_sections': show_other_sections,
            'is_direction': user_role == 'DIRECTION',
            'is_admin_or_supervisor': user_role in ['ADMIN', 'SUPERVISEUR'],
        }
    
    return {}