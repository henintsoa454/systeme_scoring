from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from ..models_classes.demande_credit import DemandeCredit
from ..models_classes.inspection_environnement import InspectionEnvironnement
from ..models_classes.rendezvous_inspection import RendezvousInspection
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from datetime import datetime,timedelta
from django.contrib import messages

def is_agent_inspection(user):
    return user.role == 'agent_inspection'

@login_required
@user_passes_test(is_agent_inspection)
def calendrier_inspections(request):
    return render(request, 'agent_inspection/calendrier_inspection.html')

@login_required
@user_passes_test(is_agent_inspection)
def agent_inspection_home(request):
    demandes_avec_rendezvous = RendezvousInspection.objects.values_list('demande_id', flat=True)
    demande_attente_inspection = DemandeCredit.objects.filter(
        statut_demande='en_attente_inspection'
    ).exclude(
        id__in=demandes_avec_rendezvous
    ).order_by('-date_demande')
    
    paginator = Paginator(demande_attente_inspection, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'agent_inspection/agent_inspection_home.html', context)

@login_required
@require_POST
@user_passes_test(is_agent_inspection)
def creer_rendezvous(request):
    demande_id = request.POST.get('demande_id')
    date_rendezvous_str = request.POST.get('date_rendezvous')
    
    try:
        demande = DemandeCredit.objects.get(id=demande_id)
        date_rendezvous = timezone.make_aware(datetime.strptime(date_rendezvous_str, '%Y-%m-%dT%H:%M'))
    except (DemandeCredit.DoesNotExist, ValueError) as e:
        return JsonResponse({'success': False, 'message': 'Données invalides'}, status=400)

    if not demande.client.email:
        return JsonResponse({
            'success': False, 
            'message': f"Ce client n'a pas d'adresse email. Veuillez le contacter par téléphone au {demande.client.numero_telephone}"
        }, status=400)

    debut_intervalle = date_rendezvous - timedelta(hours=2)
    fin_intervalle = date_rendezvous + timedelta(hours=2)
    
    rendezvous_existants = RendezvousInspection.objects.filter(
        agent_recouvrement=request.user,
        date_rendezvous__range=(debut_intervalle, fin_intervalle)
    ).exists()

    if rendezvous_existants:
        return JsonResponse({
            'success': False,
            'message': 'Un rendez vous pourrait être manquer à cette heure'
        }, status=400)
    rendezvous = RendezvousInspection.objects.create(
        agent_recouvrement=request.user,
        demande=demande,
        date_rendezvous=date_rendezvous
    )
    if demande.client.email:
        rendezvous.envoyer_notification()
    
    return JsonResponse({'success': True, 'message': 'Rendez-vous créé avec succès'})

@login_required
@require_POST
@user_passes_test(is_agent_inspection)
def creer_inspection(request):
    rendezvous_id = request.POST.get('rendezvous_id')
    rendezvous = get_object_or_404(RendezvousInspection, id=rendezvous_id)
    revenu = int(request.POST.get('revenu_moyen_mensuel'))
    depense = int(request.POST.get('depenses_moyennes_mensuelles'))
    revenu_estimation = revenu - depense
    if revenu != 0:
        marge_rentabilite = (revenu_estimation / revenu) * 100
    else:
        marge_rentabilite = 0
    inspection = InspectionEnvironnement.objects.create(
        nom_entreprise=request.POST.get('nom_entreprise'),
        adresse=request.POST.get('adresse'),
        secteur_activite=request.POST.get('secteur_activite'),
        statut_juridique=request.POST.get('statut_juridique'),
        annee_creation=request.POST.get('annee_creation'),
        etat_locaux=request.POST.get('etat_locaux'),
        types_equipements=request.POST.get('types_equipements'),
        nombre_employes=request.POST.get('nombre_employes'),
        qualification_personnel=request.POST.get('qualification_personnel'),
        systeme_gestion=request.POST.get('systeme_gestion'),
        revenu_moyen_mensuel=request.POST.get('revenu_moyen_mensuel'),
        depenses_moyennes_mensuelles=request.POST.get('depenses_moyennes_mensuelles'),
        rentabilite_estimee=marge_rentabilite,
        nombre_clients_reguliers=request.POST.get('nombre_clients_reguliers'),
        zone_geographique_ventes=request.POST.get('zone_geographique_ventes'),
        niveau_concurrence=request.POST.get('niveau_concurrence'),
        dependance_principale=request.POST.get('dependance_principale'),
        inspecte_par=request.user,
        demande_inspectee=rendezvous.demande
    )
    
    # Marquer le rendez-vous comme terminé
    rendezvous.termine = True
    rendezvous.inspection_complete = True
    rendezvous.save()
    
    rendezvous.demande.statut_demande = 'en_attente_validation'
    rendezvous.demande.save()
    return JsonResponse({'success': True, 'message': 'Inspection enregistrée avec succès'})

@login_required
def api_rendezvous(request):
    rendezvous = RendezvousInspection.objects.filter(agent_recouvrement=request.user)
    
    events = []
    for rdv in rendezvous:
        events.append({
            'id': rdv.id,
            'title': f"Inspection {rdv.demande.numero_credit}",
            'start': rdv.date_rendezvous.isoformat(),
            'color': '#28a745' if rdv.termine else '#ffc107',  # Correction ici
            'extendedProps': {
                'client': f"{rdv.demande.client.nom} {rdv.demande.client.prenom}",
                'demande': rdv.demande.numero_credit
            }
        })
    
    return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)

@login_required
def propositions_rendezvous(request):
    propositions = RendezvousInspection.objects.filter(
        agent_recouvrement=request.user,
        statut_proposition='en_attente',
        date_proposee__isnull=False
    ).select_related('demande', 'demande__client').order_by('-date_proposee')
    
    return render(request, 'agent_inspection/liste_proposition.html', {
        'propositions': propositions
    })
    
def traiter_proposition(request, token):
    proposition = get_object_or_404(
        RendezvousInspection, 
        token=token,
        agent_recouvrement=request.user
    )
    
    action = request.POST.get('action')
    
    if action == 'accepter':
        proposition.date_rendezvous = proposition.date_proposee
        proposition.statut_proposition = 'acceptee'
        proposition.save()
        messages.success(request, "La proposition a été acceptée.")
        
    elif action == 'refuser':
        proposition.statut_proposition = 'refusee'
        proposition.motif_refus = request.POST.get('motif_refus', '')
        proposition.save()
        messages.success(request, "La proposition a été refusée.")
    
    return redirect('propositions_rendezvous')