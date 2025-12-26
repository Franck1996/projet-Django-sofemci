# sofemci/views/auth.py - VERSION CORRIGÉE
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

def login_view(request):
    """Vue de connexion"""
    # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.get_full_name() or user.username} !')
            
            # Redirection selon le rôle
            if user.role == 'chef_extrusion':
                return redirect('saisie_extrusion')
            elif user.role in ['chef_imprimerie', 'chef_soudure', 'chef_recyclage']:
                return redirect('saisie_sections')
            else:
                # Admin, superviseur, direction
                return redirect('dashboard')
        else:
            messages.error(request, 'Identifiants incorrects')
    
    return render(request, 'login.html')

@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')