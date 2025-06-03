from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models_classes.rendezvous_inspection import RendezvousInspection
from .models_classes.rendezvous_directeur import RendezvousDirecteur
from datetime import datetime

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

def proposer_date(request, token):
    rendezvous = get_object_or_404(RendezvousInspection, token=token)
    
    if request.method == 'POST':
        try:
            rendezvous.date_proposee = timezone.make_aware(
                datetime.strptime(request.POST['date_proposee'], '%Y-%m-%dT%H:%M'))
            rendezvous.raison_proposition = request.POST['raison_proposition']
            rendezvous.statut_proposition = 'en_attente'
            rendezvous.save()
            return redirect('confirmation_proposition')
            
        except (ValueError, KeyError) as e:
            messages.error(request, "Données invalides")
    
    return render(request, 'client/proposition_date_inspection.html', {'rendezvous': rendezvous})

def proposer_date_finalisation(request, token):
    rendezvous = get_object_or_404(RendezvousDirecteur, token=token)
    
    if request.method == 'POST':
        try:
            rendezvous.date_proposee = timezone.make_aware(
                datetime.strptime(request.POST['date_proposee'], '%Y-%m-%dT%H:%M'))
            rendezvous.raison_proposition = request.POST['raison_proposition']
            rendezvous.statut_proposition = 'en_attente'
            rendezvous.save()
            return redirect('confirmation_proposition')
            
        except (ValueError, KeyError) as e:
            messages.error(request, "Données invalides")
    
    return render(request, 'client/proposition_date_finalisation.html', {'rendezvous': rendezvous})
