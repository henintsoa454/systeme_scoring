import json
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from sklearn.base import ClassifierMixin, RegressorMixin
from sklearn.metrics import f1_score, mean_squared_error, precision_score, recall_score,accuracy_score,r2_score
from systeme_scoring import settings
from ml_models.model_manager import ModelManager
from ..models_classes.inspection_environnement import InspectionEnvironnement
from ..models_classes.demande_credit import DemandeCredit
from ..models_classes.client import Client
from random import choice, randint, uniform
from datetime import datetime, timedelta
from decimal import Decimal
from django.http import HttpResponse, JsonResponse
import numpy as np
import pandas as pd
from django.core.mail import send_mail

def is_analyste(user):
    return user.role == 'analyste_demande'

@login_required
@user_passes_test(is_analyste)
def analyste_home(request):
    demandes_en_attente = DemandeCredit.objects.filter(statut_demande='en_attente_validation').order_by('-date_demande')

    paginator = Paginator(demandes_en_attente, 7)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'analyste_demande/analyste_home.html', context)

@login_required
@user_passes_test(is_analyste)
def details_demande(request, demande_id):
    demande = get_object_or_404(DemandeCredit,id=demande_id)
    client = demande.client
    scores_dict = demande.get_scoring_client(request.user)
    inspection_environnement = get_object_or_404(InspectionEnvironnement,demande_inspectee_id=demande_id)
    if(demande.sous_type_credit.type_credit.nom == 'Crédit aux Entrepreneurs'):
        scores = [
            scores_dict["situation_familiale"],
            scores_dict["situation_professionnelle"],
            scores_dict["situation_financiere"],
            scores_dict["inspection_environnement"],
        ]
        score_general = sum(scores) / len(scores)
        return render(request, "analyste_demande/details_scoring_demande.html", {"client": client, "demande": demande, "inspection": inspection_environnement, "scores": scores_dict, "score_general": score_general})
    else:
        scores = [
            scores_dict["situation_familiale"],
            scores_dict["situation_professionnelle"],
            scores_dict["situation_financiere"],
        ]
        score_general = sum(scores) / len(scores)

        return render(request, "analyste_demande/details_scoring_demande.html", {"client": client, "demande": demande, "scores": scores_dict, "score_general": score_general})


def feature_importance_page(request):
    """
    Affiche la page de modification des importances des colonnes.
    """
    return render(request, "analyste_demande/importance_modele.html")

def get_feature_importances(request):
    """
    Charge l'importance des colonnes et les métriques d'un modèle pour un utilisateur connecté.
    """
    model_key = request.GET.get("model_key")
    if not model_key:
        return JsonResponse({"error": "Model key is required."}, status=400)

    user = request.user  # Utilisateur connecté

    try:
        model_manager = ModelManager()
        model = model_manager.load_model(model_key, user)

        # Récupérer les métriques sauvegardées
        metrics = getattr(model, "metrics_", None)
        if metrics is None:
            return JsonResponse({"error": "Metrics are not available for the selected model."}, status=400)

        # Récupérer l'importance des caractéristiques si disponible
        if hasattr(model, "feature_importances_"):
            feature_importances = model.feature_importances_
            feature_names = model.feature_names_in_ if hasattr(model, "feature_names_in_") else [
                f"Feature {i}" for i in range(len(feature_importances))
            ]

            data = [
                {"feature": name, "importance": float(importance)}
                for name, importance in zip(feature_names, feature_importances)
            ]
        else:
            data = []

        # Réponse JSON structurée
        return JsonResponse({
            "data": data,
            "metrics": metrics
        })

    except FileNotFoundError as e:
        return JsonResponse({"error": str(e)}, status=404)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

def update_feature_importances(request):
    """
    Met à jour les importances des colonnes pour un utilisateur connecté et un modèle donné.
    """
    if request.method == "POST":
        model_key = request.POST.get("model_key", None)
        updated_importances = request.POST.get("updated_importances", None)

        if not model_key or not updated_importances:
            return JsonResponse({"error": "Model key and updated importances are required."}, status=400)

        try:
            model_manager = ModelManager()
            user = request.user  # Utilisateur connecté
            model = model_manager.load_model(model_key, user)

            # Mettre à jour les importances
            updated_importances = json.loads(updated_importances)  # Convertir le JSON en dictionnaire
            for i, feature in enumerate(model.feature_names_in_):
                if feature in updated_importances:
                    model.feature_importances_[i] = updated_importances[feature]

            # Sauvegarder le modèle modifié dans le cache utilisateur
            model_manager.update_model_cache(user.id, model_key, model)
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=405)

@login_required
@user_passes_test(is_analyste)    
def refus_demande(request, demande_id):
    demande = DemandeCredit.objects.get(id=demande_id)

    if request.method == 'POST':
        raison_refus = request.POST.get('raisonRefus')
        print(raison_refus)
        demande.statut_demande = "rejete"
        demande.date_derniere_maj = datetime.now()
        demande.traite_par = request.user
        demande.save()

        demande.client.notifierRefus(raison_refus,demande)
        return redirect('analyste_home')
    
@login_required
@user_passes_test(is_analyste)    
def transmettre_demande(request, demande_id):
    demande = DemandeCredit.objects.get(id=demande_id)
    demande.statut_demande = "en_attente_signature"
    demande.date_derniere_maj = datetime.now()
    demande.traite_par = request.user
    demande.save()

    return redirect('analyste_home')   
    



    