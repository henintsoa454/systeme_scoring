from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            user.last_login = timezone.now()
            user.save()
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_home')
            elif user.role == 'directeur_agence':
                return redirect('directeur_home')
            elif user.role == 'analyste_demande':
                return redirect('analyste_home')
            elif user.role == 'service_client':
                return redirect('offre_credit')
            elif user.role == 'gestionnaire':
                return redirect('gestionnaire_home')
            elif user.role == 'agent_inspection':
                return redirect('agent_inspection_home')
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')