from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib import messages
from decimal import Decimal
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.utils.timezone import now
from django.db import models
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from ..models_classes.demande_credit import DemandeCredit
from ..models_classes.client import Client
from ..models_classes.type_credit import TypeCredit
from ..models_classes.sous_types_credit import SousTypeCredit
from ..models_classes.remboursement_credit import RemboursementCredit

def is_gestionnaire_demande(user):
    return user.role == 'gestionnaire'

@login_required
@user_passes_test(is_gestionnaire_demande)
def gestionnaire_home(request):
    dernieres_demandes = DemandeCredit.objects.filter(
        statut_demande__in=['en_attente_validation', 'en_attente_signature']
    ).order_by('-date_demande')[:10]

    return render(request, 'gestionnaire_demande/gestionnaire_home.html', {'demandes': dernieres_demandes})

@login_required
@user_passes_test(is_gestionnaire_demande)
def gestionnaire_clients(request):
    clients = Client.objects.all()[:10]
    return render(request, 'gestionnaire_demande/gestionnaire_clients.html', {'clients': clients})


@login_required
@user_passes_test(is_gestionnaire_demande)
def recherche_clients(request):
    # Vérifiez si la requête est une requête AJAX de type GET
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            # Récupérez le paramètre 'search'
            search_query = request.GET.get('search', '').strip()

            # Filtrage des clients en fonction de la recherche
            if search_query:
                clients = Client.objects.filter(
                    Q(nom__icontains=search_query) |
                    Q(prenom__icontains=search_query) |
                    Q(n_cin__icontains=search_query)
                )[:10]  # Limitez à 10 résultats
            else:
                # Retournez tous les clients, avec une limite
                clients = Client.objects.all()[:10]

            # Transformez les clients en format JSON
            clients_data = [
                {
                    'nom': client.nom,
                    'prenom': client.prenom,
                    'date_naissance': client.date_naissance,
                    'n_cin': client.n_cin,
                    'email': client.email or 'N/A',
                }
                for client in clients
            ]

            # Retournez les données JSON
            return JsonResponse({'clients': clients_data})
        except Exception as e:
            # Loguez l'erreur pour débogage
            print(f"Erreur lors du traitement de la recherche : {e}")
            return JsonResponse({'error': 'Une erreur est survenue lors du traitement de la recherche.'}, status=500)

    # Retour pour les requêtes non valides
    return JsonResponse({'error': 'Requête invalide.'}, status=400)


from django.core.exceptions import ValidationError
from django.contrib import messages

@login_required
@user_passes_test(is_gestionnaire_demande)
def ajouter_client(request):
    if request.method == 'POST':
        try:
            client_data = {
                'nom': request.POST.get('nom'),
                'prenom': request.POST.get('prenom'),
                'date_naissance': request.POST.get('date_naissance'),
                'adresse': request.POST.get('adresse'),
                'email': request.POST.get('email'),
                'n_cin': request.POST.get('n_cin'),
                'statut_familial': request.POST.get('statut_familial'),
                'nbr_dependant': request.POST.get('nbr_dependant'),
                'situation_professionnelle': request.POST.get('situation_professionnelle'),
                'titre_emploie': request.POST.get('titre_emploie'),
                'nom_employeur': request.POST.get('nom_employeur'),
                'duree_emploie': request.POST.get('duree_emploie'),
                'revenu_mensuel': request.POST.get('revenu_mensuel'),
                'depense_mensuelles': request.POST.get('depense_mensuelles'),
                'dettes_existantes': request.POST.get('dettes_existantes'),
                'situation_bancaire': request.POST.get('situation_bancaire'),
            }
            # Création de l'instance Client
            client = Client(**client_data)
            client.full_clean()  # Validation des données du modèle
            client.save()
            messages.success(request, "Le client a été ajouté avec succès.")
            return redirect('gestionnaireclients')
        except ValidationError as e:
            messages.error(request, f"Erreur lors de l'ajout du client : {e}")

    return render(request, 'gestionnaire_demande/gestionnaire_client.html')

@login_required
@user_passes_test(is_gestionnaire_demande)
def modifie_client(request, client_id):
    client = get_object_or_404(Client, id=client_id)

    if request.method == "POST":
        try:
            # Mise à jour des champs existants
            client.nom = request.POST.get('nom')
            client.prenom = request.POST.get('prenom')
            client.date_naissance = request.POST.get('date_naissance')
            client.adresse = request.POST.get('adresse')
            client.email = request.POST.get('email')
            client.n_cin = request.POST.get('n_cin')
            client.statut_familial = request.POST.get('statut_familial')
            client.nbr_dependant = request.POST.get('nbr_dependant')
            client.situation_professionnelle = request.POST.get('situation_professionnelle')
            client.titre_emploie = request.POST.get('titre_emploie')
            client.nom_employeur = request.POST.get('nom_employeur')
            client.duree_emploie = request.POST.get('duree_emploie')
            client.revenu_mensuel = request.POST.get('revenu_mensuel')
            client.depense_mensuelles = request.POST.get('depense_mensuelles')
            client.dettes_existantes = request.POST.get('dettes_existantes')
            client.situation_bancaire = request.POST.get('situation_bancaire')

            # Mise à jour des nouveaux champs
            client.secteur_activite = request.POST.get('secteur_activite')
            client.type_contrat = request.POST.get('type_contrat')
            client.solde_bancaire = request.POST.get('solde_bancaire')
            client.valeur_actifs = request.POST.get('valeur_actifs')
            client.montant_emprunts_en_cours = request.POST.get('montant_emprunts_en_cours')
            client.historique_credit = request.POST.get('historique_credit')
            client.historique_paiement = request.POST.get('historique_paiement')

            # Validation et sauvegarde
            client.full_clean()
            client.save()
            messages.success(request, "Les informations du client ont été mises à jour avec succès.")
            return redirect('gestionnaireclients')
        except ValidationError as e:
            messages.error(request, f"Erreur lors de la modification du client : {e}")

    return render(request, 'gestionnaire_demande/modifie_client.html', {'client': client})



@login_required
@user_passes_test(is_gestionnaire_demande)
def gestionnaire_demandes(request):
    search_query = request.GET.get('q', '')
    if search_query:
        demandes = DemandeCredit.objects.filter(
            client__nom__icontains=search_query
        ) | DemandeCredit.objects.filter(
            numero_credit__icontains=search_query
        ) | DemandeCredit.objects.filter(
            statut_demande__icontains=search_query
        )
    else:
        demandes = DemandeCredit.objects.all().order_by('-date_demande')[:10]

    context = {
        'demandes': demandes,
        'search_query': search_query,
    }
    return render(request, 'gestionnaire_demande/gestionnaire_demandes.html', context)

@login_required
@user_passes_test(is_gestionnaire_demande)
def nouvelle_demande(request):
    if request.method == "POST":
        client_id = request.POST.get('client')
        sous_type_credit_id = request.POST.get('sous_type_credit')
        duree = request.POST.get('duree')
        montant_total = request.POST.get('montant_total')
        motif_credit = request.POST.get('motif_credit')

        if not client_id:
            messages.error(request, "Vous devez sélectionner un client.")
            return redirect('nouvelledemande')

        # Validation des champs requis
        if not all([client_id, sous_type_credit_id, duree, montant_total, motif_credit]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return redirect('nouvelledemande')

        # Récupération des objets liés
        client = get_object_or_404(Client, id=client_id)
        sous_type_credit = get_object_or_404(SousTypeCredit, id=sous_type_credit_id)
        taux_interet = sous_type_credit.taux_interet

        # Calcul du montant à payer par mois avec taux d'intérêt
        try:
                montant_total = Decimal(montant_total)  # Assurez-vous que montant_total est un Decimal
                duree = Decimal(duree)
                taux_interet = Decimal(taux_interet)

                montant_mensuel = (montant_total / duree) * (1 + taux_interet / Decimal(100))
                
        except ZeroDivisionError:
            messages.error(request, "La durée ne peut pas être zéro.")
            return redirect('nouvelledemande')

        # Génération du numéro de crédit
        today_str = now().strftime('%m%d%Y')
        prefixe = sous_type_credit.prefixe if hasattr(sous_type_credit, 'prefixe') else 'GEN'
        numero_credit = f"DC-{prefixe}-{today_str}-{DemandeCredit.objects.count() + 1}"

        # Création de la demande
        statut_demande = "en_attente_validation"
        if(sous_type_credit.type_credit.nom == 'Crédit aux Entrepreneurs'):
            statut_demande = "en_attente_inspection"
        demande = DemandeCredit.objects.create(
            numero_credit=numero_credit,
            client=client,
            sous_type_credit=sous_type_credit,
            duree=duree,
            montant_total=montant_total,
            montant_payer_mois=montant_mensuel,
            motif_credit=motif_credit,
            statut_demande = statut_demande
        )
        

        messages.success(request, f"La demande {demande.numero_credit} a été créée avec succès.")
        return redirect('gestionnairedemandes')

    # Récupération des clients et types de crédit pour le formulaire
    clients = Client.objects.all()
    types_credit = TypeCredit.objects.all()

    return render(request, 'gestionnaire_demande/nouvelle_demande.html', {
        'clients': clients,
        'types_credit': types_credit,
    })


@login_required
@user_passes_test(is_gestionnaire_demande)
def modifier_demande(request, demande_id):
    demande = get_object_or_404(DemandeCredit, id=demande_id)

    # Vérifiez si la demande est modifiable
    if not demande.est_modifiable():
        messages.error(request, "Seules les demandes en attente peuvent être modifiées.")
        return redirect('gestionnairedemandes')

    if request.method == 'POST':
        sous_type_credit_id = request.POST.get('sous_type_credit')
        duree = request.POST.get('duree')
        montant_total = request.POST.get('montant_total')
        motif_credit = request.POST.get('motif_credit')

        # Validation des champs requis
        if sous_type_credit_id and duree and montant_total:
            sous_type_credit = get_object_or_404(SousTypeCredit, id=sous_type_credit_id)
            taux_interet = sous_type_credit.taux_interet

            # Calcul du montant à payer par mois avec taux d'intérêt
            try:
                montant_total = Decimal(montant_total)  # Assurez-vous que montant_total est un Decimal
                duree = Decimal(duree)
                taux_interet = Decimal(taux_interet)

                montant_mensuel = (montant_total / duree) * (1 + taux_interet / Decimal(100))
            except ZeroDivisionError:
                messages.error(request, "La durée ne peut pas être zéro.")
                return redirect('modificationdemande', demande_id=demande_id)

            # Mise à jour de la demande
            demande.sous_type_credit = sous_type_credit
            demande.duree = duree
            demande.montant_total = montant_total
            demande.montant_payer_mois = montant_mensuel
            demande.motif_credit = motif_credit
            demande.save()

            messages.success(request, "La demande a été modifiée avec succès.")
            return redirect('gestionnairedemandes')
        else:
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")

    types_credit = TypeCredit.objects.all()
    sous_types_credit = SousTypeCredit.objects.filter(type_credit=demande.sous_type_credit.type_credit)

    return render(request, 'gestionnaire_demande/modifie_demande.html', {
        'demande': demande,
        'types_credit': types_credit,
        'sous_types_credit': sous_types_credit,
    })
 
@login_required
@user_passes_test(is_gestionnaire_demande)   
def payer_demande(request, demande_id):
    demande = get_object_or_404(DemandeCredit, id=demande_id)
    
    # Vérification du statut de la demande
    if demande.statut != 'approuve':
        messages.error(request, "Cette demande n'est pas approuvée et ne peut pas être payée.")
        return redirect('gestionedemandes')  # Redirection vers la page principale des demandes
    
    if request.method == 'POST':
        somme_paye = request.POST.get('somme_paye')

        try:
            somme_paye = Decimal(somme_paye)
        except (ValueError, TypeError):
            messages.error(request, "Veuillez entrer un montant valide.")
            return render(request, 'gestionnaire_demande/payer_demande.html', {'demande': demande})

        if somme_paye <= 0:
            messages.error(request, "Le montant doit être supérieur à zéro.")
            return render(request, 'gestionnaire_demande/payer_demande.html', {'demande': demande})

        # Enregistrement du remboursement
        dernier_payement = (
            RemboursementCredit.objects.filter(numero_credit=demande)
            .order_by('-n_payement')
            .first()
        )
        prochain_numero = (dernier_payement.n_payement + 1) if dernier_payement else 1

        remboursement = RemboursementCredit.objects.create(
            numero_credit=demande,
            date_payement=now(),
            somme_paye=somme_paye,
            n_payement=prochain_numero
        )

        # Mise à jour du statut si paiement total atteint
        total_rembourse = (
            RemboursementCredit.objects.filter(numero_credit=demande)
            .aggregate(total=models.Sum('somme_paye'))['total'] or Decimal(0)
        )

        if total_rembourse >= demande.montant_total:
            demande.statut = 'termine'  # Statut à définir pour les demandes terminées
            demande.save()

        messages.success(request, f"Le paiement de {somme_paye} a été enregistré avec succès.")
        return redirect('gestionedemandes')  # Redirection vers la gestion des demandes

    return render(request, 'gestionnaire_demande/paye_demande.html', {'demande': demande})

def paiement(request, demande_id):
    demande = get_object_or_404(DemandeCredit, id=demande_id)
    
    if request.method == 'POST':
        somme_paye = float(request.POST.get('somme_paye'))
        type_paiement = request.POST.get('type_paiement', 'normal')

        montant_restant = demande.montant_total - sum(r.somme_paye for r in demande.remboursements.all())
        if somme_paye > montant_restant:
            messages.error(request, "La somme payée dépasse le montant restant.")
            return redirect('effectuer_paiement', demande_id=demande.id)
        
        if demande.statut_demande == 'termine':
            messages.error(request, "Cette demande est déjà terminée.")
            return redirect('effectuer_paiement', demande_id=demande.id)

        numero_paiement = demande.remboursements.count() + 1

        remboursement = RemboursementCredit(
            demande=demande,
            somme_paye=somme_paye,
            numero_paiement=numero_paiement,
            type_paiement=type_paiement,
        )
        remboursement.save()

        montant_restant -= somme_paye
        if montant_restant <= 0:
            demande.statut_demande = 'termine'
            demande.save()

        messages.success(request, "Paiement effectué avec succès.")
        return redirect('detail_demande', demande_id=demande.id)

    return render(request, 'gestionnaire_demande/paiement.html', {'demande': demande})

@login_required
@user_passes_test(is_gestionnaire_demande) 
def page_telechargement(request):
    return render(request, 'gestionnaire_demande/telechargement.html')

@login_required
@user_passes_test(is_gestionnaire_demande)
def telecharger_document(request):
    type_document = request.GET.get('type')
    client_id = request.GET.get('client_id')
    demande_id = request.GET.get('demande_id')
    annee = request.GET.get('annee')

    context = {}
    template_name = ""
    filename = ""

    if type_document == "recapitulatif":
        demande = get_object_or_404(DemandeCredit, id=demande_id)
        context = {"demande": demande, "client": demande.client}
        template_name = "documents/recapitulatif_demande.html"
        filename = f"recapitulatif_{demande.numero_credit}.pdf"

    elif type_document == "certificat_solvabilite":
        client = get_object_or_404(Client, id=client_id)
        score_solvabilite = client.calculer_solvabilite()  # Exemple d'une méthode
        context = {"client": client, "score_solvabilite": score_solvabilite}
        template_name = "documents/certificat_solvabilite.html"
        filename = f"certificat_solvabilite_{client.nom}.pdf"

    elif type_document == "declaration_fiscale":
        client = get_object_or_404(Client, id=client_id)
        paiements_annuels = client.get_paiements_annuels(annee)  # Exemple d'une méthode
        context = {"client": client, "annee": annee, "paiements": paiements_annuels}
        template_name = "documents/declaration_fiscale.html"
        filename = f"declaration_fiscale_{annee}_{client.nom}.pdf"

    # Générer le PDF à partir du template et du contexte
    html_content = render_to_string(template_name, context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # Utilisation de xhtml2pdf pour générer le PDF
    pisa_status = pisa.CreatePDF(html_content, dest=response)

    # Si une erreur survient lors de la génération
    if pisa_status.err:
        return HttpResponse("Erreur lors de la génération du PDF", status=500)

    return response


@require_http_methods(["GET"])
def sous_types_credit_api(request, type_credit_id):
    try:
        sous_types = SousTypeCredit.objects.filter(type_credit_id=type_credit_id)
        if not sous_types.exists():
            return JsonResponse({'error': 'Aucun sous-type trouvé pour ce type de crédit.'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'ID invalide.'}, status=400)

    data = [
        {
            'id': st.id,
            'nom': st.nom,
            'montant_min': st.montant_min if st.montant_min is not None else 0,
            'montant_max': st.montant_max if st.montant_max is not None else 0,
            'taux_interet': st.taux_interet if hasattr(st, 'taux_interet') else 0,
        } 
        for st in sous_types
    ]
    return JsonResponse(data, safe=False)


