import calendar
from io import BytesIO
from xhtml2pdf import pisa
import os
from calendar import monthrange
from django.contrib import messages
import tempfile
from datetime import datetime,timedelta
from django.template.loader import render_to_string, get_template
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from datetime import datetime, date
from django.core.serializers.json import DjangoJSONEncoder
from reportlab.lib.pagesizes import letter
from django.core.paginator import Paginator
from reportlab.pdfgen import canvas
from django.db.models import Sum, Count, Q
from weasyprint import HTML
from ..models_classes.rendezvous_directeur import RendezvousDirecteur
from ..models_classes.demande_credit import DemandeCredit
from ..models_classes.client import Client
from ..models_classes.custom_user import CustomUser
from ..models_classes.remboursement_credit import RemboursementCredit
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models.functions import TruncMonth, TruncDay

def is_directeur_agence(user):
    return user.role == 'directeur_agence'

@login_required
@user_passes_test(is_directeur_agence)
def directeur_home(request):
    now = datetime.now()
    debut_mois = datetime(now.year, now.month, 1)
    
    total_clients = Client.objects.count()

    demandes_mois = DemandeCredit.objects.filter(date_derniere_maj__gte=debut_mois)
    demandes_en_attente_inspection = demandes_mois.filter(statut_demande="en_attente_inspection").count()
    demandes_en_attente = demandes_mois.filter(statut_demande="en_attente_validation").count()
    demandes_signature = demandes_mois.filter(statut_demande="en_attente_signature").count()
    demandes_approuvees = demandes_mois.filter(statut_demande="approuvee").count()
    demandes_rejetees = demandes_mois.filter(statut_demande="rejete").count()
    
    remboursements_mois = RemboursementCredit.objects.filter(date_paiement__gte=debut_mois)    

    montant_emprunte = demandes_mois.filter(statut_demande="approuvee").aggregate(Sum("montant_total"))["montant_total__sum"] or 0
    benefice_mois = remboursements_mois.aggregate(Sum("somme_paye"))["somme_paye__sum"] or 0

    context = {
        "total_clients": total_clients,
        "demandes_en_attente_inspection": demandes_en_attente_inspection,
        "demandes_en_attente": demandes_en_attente,
        "demandes_signature": demandes_signature,
        "demandes_approuvees": demandes_approuvees,
        "demandes_rejetees": demandes_rejetees,
        "montant_emprunte": montant_emprunte,
        "benefice_mois": benefice_mois,
    }
    return render(request, "directeur_agence/directeur_home.html", context)

@login_required
@user_passes_test(is_directeur_agence)
def liste_attente(request):
    demandes_avec_rendezvous = RendezvousDirecteur.objects.values_list('demande_id', flat=True)
    demande_attente_inspection = DemandeCredit.objects.filter(
        statut_demande='en_attente_signature'
    ).exclude(
        id__in=demandes_avec_rendezvous
    ).order_by('-date_demande')
    
    paginator = Paginator(demande_attente_inspection, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'directeur_agence/liste_attente.html', context)

@login_required
@user_passes_test(is_directeur_agence)
def calendrier_finalisation(request):
    return render(request, 'directeur_agence/calendrier_finalisation.html')

@login_required
def api_finalisation(request):
    rendezvous = RendezvousDirecteur.objects.filter(directeur=request.user)
    
    events = []
    for rdv in rendezvous:
        events.append({
            'id': rdv.id,
            'title': f"{rdv.demande.client.nom} {rdv.demande.client.prenom} {rdv.demande.numero_credit}",
            'start': rdv.date_rendezvous,
            'color': '#28a745' if rdv.termine else '#ffc107',
            'extendedProps': {
                'client': f"{rdv.demande.client.nom} {rdv.demande.client.prenom}",
                'demande': rdv.demande.numero_credit,
                'demandeId': rdv.demande.id,
            }
        })
    
    return JsonResponse(events, safe=False, encoder=DjangoJSONEncoder)


@login_required
@user_passes_test(is_directeur_agence)
def resumedemande(request,demande_id):
    demande = get_object_or_404(DemandeCredit,id = demande_id)
    return render(request, 'directeur_agence/resumedemande.html', {"demande" : demande})

@login_required
@user_passes_test(is_directeur_agence)
def generate_contract_pdf(request, demande_id):
    demande = get_object_or_404(DemandeCredit, id=demande_id)
    client = demande.client
    
    context = {
        'demande': demande,
        'client': client,
        'date_aujourdhui': datetime.now().strftime("%d/%m/%Y")
    }
    
    template = get_template('client/contrat_credit.html')
    html = template.render(context)
    
    # Création du PDF
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        # Stocker en session que le PDF a été généré
        request.session['pdf_generated'] = True
        request.session['demande_id'] = demande_id
        
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Contrat_Credit_{demande.numero_credit}.pdf"'
        return response
    else:
        messages.error(request, "Erreur lors de la génération du PDF")
        return redirect('calendrierfinalisation')
    
@login_required
@user_passes_test(is_directeur_agence)
def pdf_download_complete(request):
    if request.session.get('pdf_generated', False):
        demande_id = request.session.get('demande_id')
        del request.session['pdf_generated']
        del request.session['demande_id']
        
        messages.success(request, "Le contrat a été téléchargé avec succès")
        
        demande = get_object_or_404(DemandeCredit, id = demande_id)
        demande.statut_demande = 'approuve'
        demande.save()
        rendezvous = get_object_or_404(RendezvousDirecteur, demande_id = demande_id)
        rendezvous.termine = True
        rendezvous.save()
        current_date = datetime.now()
        year = current_date.year
        month = current_date.month
        for mois in range(1, demande.duree + 1):
            new_month = month + mois
            year_offset = (new_month - 1) // 12
            final_month = (new_month - 1) % 12 + 1
            final_year = year + year_offset
            last_day = monthrange(final_year, final_month)[1]
            day = min(current_date.day, last_day)
            date_echeance = datetime(final_year, final_month, day)
            RemboursementCredit.objects.create(
                demande=demande,
                numero_paiement=mois,
                somme_attendu=demande.montant_payer_mois,
                somme_paye=demande.montant_payer_mois,  
                type_paiement='normal',
                statut='payé',
                penalite=0,
                date_echeance=date_echeance
        )
        return redirect('calendrierfinalisation')
    return redirect('calendrierfinalisation')

@login_required
@user_passes_test(is_directeur_agence)
def preview_contract(request, demande_id):
    demande = get_object_or_404(DemandeCredit, id=demande_id)
    client = demande.client
    date_premiere_echeance = datetime.now().date() + timedelta(days=15)
    
    context = {
        'demande': demande,
        'client': client,
        'date_aujourdhui': datetime.now().strftime("%d/%m/%Y"),
        'date_premiere_echeance': date_premiere_echeance.strftime("%d/%m/%Y"),
    }
    
    return render(request, 'client/contrat_credit.html', context)

@login_required
@require_POST
@user_passes_test(is_directeur_agence)
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
    
    rendezvous_existants = RendezvousDirecteur.objects.filter(
        directeur=request.user,
        date_rendezvous__range=(debut_intervalle, fin_intervalle)
    ).exists()

    if rendezvous_existants:
        return JsonResponse({
            'success': False,
            'message': 'Un rendez vous pourrait être manquer à cette heure'
        }, status=400)
    rendezvous = RendezvousDirecteur.objects.create(
        directeur=request.user,
        demande=demande,
        date_rendezvous=date_rendezvous
    )
    if demande.client.email:
        rendezvous.envoyer_notification()
    
    return JsonResponse({'success': True, 'message': 'Rendez-vous créé avec succès'})

@login_required
@user_passes_test(is_directeur_agence)
def performance_generale(request):
    year = request.GET.get("year", datetime.now().year)
    month = request.GET.get("month", None)
    
    years = list(range(year, 1917, -1))

    return render(request, 'directeur_agence/performance_generale.html', {"year": year, "month": month, "years": years})


def format_labels(data, group_by):
    if group_by == TruncDay:
        return [entry["period"].strftime("%d-%m-%Y") for entry in data]
    return [entry["period"].strftime("%B %Y") for entry in data]

def get_performance_generale(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    today = date.today()

    # Initialisation des filtres
    base_filters = Q(date_derniere_maj__lte=today)
    remboursements_base_filters = Q(date_paiement__lte=today)
    
    # Conversion et validation des paramètres
    try:
        if year:
            year = int(year)
            base_filters &= Q(date_derniere_maj__year=year)
            remboursements_base_filters &= Q(date_paiement__year=year)
        
        if month:
            month = int(month)
            if month < 1 or month > 12:
                return JsonResponse({'error': 'Le mois doit être entre 1 et 12'}, status=400)
                
            base_filters &= Q(date_derniere_maj__month=month)
            remboursements_base_filters &= Q(date_paiement__month=month)
            
            # Vérification de l'année si mois est spécifié
            if not year:
                year = today.year
    except ValueError:
        return JsonResponse({'error': 'Paramètres invalides'}, status=400)

    # Détermination du group_by
    group_by = TruncDay if month else TruncMonth
    remboursements_group_by = TruncDay if month else TruncMonth

    # Récupération des données
    emprunts_data = (
        DemandeCredit.objects.filter(base_filters)
        .annotate(period=group_by('date_demande'))
        .values('period')
        .annotate(total=Sum('montant_total'))
        .order_by('period')
    )

    remboursements_data = (
        RemboursementCredit.objects.filter(remboursements_base_filters)
        .annotate(period=remboursements_group_by('date_paiement'))
        .values('period')
        .annotate(total=Sum('somme_paye'))
        .order_by('period')
    )

    # Préparation des labels
    if month:
        try:
            days_in_month = calendar.monthrange(year, month)[1]
            labels = [str(day) for day in range(1, days_in_month + 1)]
            
            emprunts_dict = {entry['period'].day: float(entry['total']) for entry in emprunts_data}
            remboursements_dict = {entry['period'].day: float(entry['total']) for entry in remboursements_data}
            
            emprunts = [emprunts_dict.get(day, 0) for day in range(1, days_in_month + 1)]
            remboursements = [remboursements_dict.get(day, 0) for day in range(1, days_in_month + 1)]
        except (ValueError, calendar.IllegalMonthError):
            return JsonResponse({'error': 'Mois/année invalide'}, status=400)
    else:
        month_names = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
        ]
        labels = month_names
        
        emprunts_dict = {entry['period'].month: float(entry['total']) for entry in emprunts_data}
        remboursements_dict = {entry['period'].month: float(entry['total']) for entry in remboursements_data}
        
        emprunts = [emprunts_dict.get(m, 0) for m in range(1, 13)]
        remboursements = [remboursements_dict.get(m, 0) for m in range(1, 13)]

    return JsonResponse({
        'emprunts_vs_remboursements': {
            'labels': labels,
            'emprunts': emprunts,
            'remboursements': remboursements,
        }
    })
    
@login_required
@user_passes_test(is_directeur_agence)
def performance_employes(request):
    year = request.GET.get("year", datetime.now().year)
    month = request.GET.get("month", None)
    
    years = list(range(year, 1917, -1))

    return render(request, 'directeur_agence/performance_analyste.html', {"year": year, "month": month, "years": years})

def get_performance_employes(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    try:
        # Filtres de base
        filters = Q()
        
        if year:
            year = int(year)
            filters &= Q(date_demande__year=year)
        
        if month:
            month = int(month)
            filters &= Q(date_demande__month=month)
        
        # Récupération des données groupées par statut
        stats = (
            DemandeCredit.objects
            .filter(filters)
            .values('statut_demande')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        
        # Formatage des données pour le frontend
        result = {item['statut_demande']: item['count'] for item in stats}
        
        statuts_possibles = dict(DemandeCredit.STATUT_CHOICES)
        for statut in statuts_possibles:
            if statut not in result:
                result[statut] = 0
        
        return JsonResponse({
            'success': True,
            'data': result,
            'year': year if year else 'Toutes années',
            'month': month if month else 'Tous mois'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@user_passes_test(is_directeur_agence)
def gestion_employes(request):
    agence_directeur = request.user.agence
    
    roles_autorises = ['service_client', 'gestionnaire', 'analyste_demande']
    
    employes = CustomUser.objects.filter(
        agence=agence_directeur,
        role__in=roles_autorises
    ).order_by('role', 'username')
    
    roles = CustomUser.objects.filter(role__in=roles_autorises).values_list('role', flat=True).distinct()
    
    return render(request, 'directeur_agence/gestion_employes.html', {
        "employes": employes,
        "roles": roles
    })
    
@login_required
@user_passes_test(is_directeur_agence)
def save_employe(request):
    if request.method == "POST":
        employe_id = request.POST.get('id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        role = request.POST.get('role')

        # Vérifier si un employé existe (modification)
        if employe_id:
            employe = get_object_or_404(CustomUser, id=employe_id)
            employe.username = username
            employe.email = email
            employe.role = role
            employe.save()
            return JsonResponse({"success": True, "message": "Employé modifié avec succès"})
        else:
            # Ajouter un nouvel employé
            agence_directeur = request.user.agence
            CustomUser.objects.create(
                username=username,
                email=email,
                role=role,
                agence=agence_directeur
            )
            return JsonResponse({"success": True, "message": "Nouvel employé ajouté avec succès"})
    return JsonResponse({"success": False, "errors": "Méthode non autorisée"})