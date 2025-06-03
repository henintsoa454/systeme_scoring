from django.db import models
from .agence import Agence
from .client import Client
from .sous_types_credit import SousTypeCredit
from .custom_user import CustomUser
from ml_models.model_manager import ModelManager
import pandas as pd
import numpy as np
from django.contrib import messages

class DemandeCredit(models.Model):
    STATUT_CHOICES = [
        ('en_attente_inspection',"En attente d' inspection"),
        ('en_attente_validation', 'En attente de validation'),
        ('en_attente_signature', 'En attente de signature'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
        ('termine', 'Terminé'),
    ]

    agence = models.ForeignKey(Agence, on_delete=models.CASCADE, default=1)
    numero_credit = models.CharField(max_length=20, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    sous_type_credit = models.ForeignKey(SousTypeCredit, on_delete=models.CASCADE)
    duree = models.IntegerField()
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    montant_payer_mois = models.DecimalField(max_digits=10, decimal_places=2)
    motif_credit = models.TextField()
    date_demande = models.DateField()
    statut_demande = models.CharField( max_length=25, choices=STATUT_CHOICES, default='en_attente', null=False, blank=False)
    date_derniere_maj = models.DateField(auto_now_add=True)
    enregistre_par = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_enregistrees')
    traite_par = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='demandes_traitees')

    
    def get_statut_display(self):
        return dict(self.STATUT_CHOICES).get(self.statut_demande, "Statut inconnu")
    
    def est_modifiable(self):
        return self.statut_demande == 'en_attente_validation'
    
    def est_payable(self):
        return self.statut_demande == 'approuve'
    
    def get_scoring_client(self,user):
        model_manager = ModelManager()
        client = self.client
        scores = {}

        try:
            # Chargement des encodeurs
            encoder_situation_familiale = model_manager.load_encoder("situation_familiale")
            encoder_secteur_activite = model_manager.load_encoder("secteur_activite")
            encoder_situation_professionnelle = model_manager.load_encoder("situation_professionnelle")
            encoder_type_contrat = model_manager.load_encoder("type_contrat")
            encoder_situation_bancaire = model_manager.load_encoder("situation_bancaire")
            encoder_capacite_remboursement = model_manager.load_encoder("capacite_remboursement")

            # Chargement des modèles
            model_situation_familiale = model_manager.load_model("situation_familiale",user)
            model_situation_professionnelle = model_manager.load_model("situation_professionnelle",user)
            model_situation_financiere = model_manager.load_model("situation_financiere",user)
            model_capacite_remboursement = model_manager.load_model("capacite_remboursement",user)

            # Encodage de statut familial
            encoded_family_status = encoder_situation_familiale.transform([[client.statut_familial]])[0][0]

            # Situation familiale
            scores["Situation familiale"] = model_situation_familiale.predict(
                [[encoded_family_status, client.nbr_dependant, client.age()]]
            )[0]

            # Situation professionnelle
            profession_key = next(
                (key for key, value in client.SITUATION_PROFESSIONNELLE_CHOICES if value == client.situation_professionnelle), None
            )
            activity_sector_key = next(
                (key for key, value in client.SECTEUR_ACTIVITE_CHOICES if value == client.secteur_activite), None
            )
            contract_type_key = next(
                (key for key, value in client.TYPE_CONTRAT_CHOICES if value == client.type_contrat), None
            )

            encoded_profession = encoder_situation_professionnelle.transform([[profession_key]])[0][0]
            encoded_contract_type = encoder_type_contrat.transform([[contract_type_key]])[0][0]

            duree_emploie = client.duree_emploie
            if(duree_emploie is None):
                duree_emploie = 0
             
            profession_data = pd.DataFrame({
                'situation_professionnelle': [encoded_profession],
                'duree_emploie': duree_emploie,
                'revenu_mensuel': [client.revenu_mensuel],
                'secteur_activite': [activity_sector_key],
                'type_contrat': [encoded_contract_type]
            })

            # Encodage des variables catégoriques
            profession_data['secteur_activite'] = encoder_secteur_activite.transform(profession_data['secteur_activite'])

            # Réindexation des colonnes attendues par le modèle
            expected_columns = ['situation_professionnelle', 'duree_emploie', 'revenu_mensuel', 'secteur_activite', 'type_contrat']
            profession_data = profession_data.reindex(columns=expected_columns, fill_value=0)
            # Prédiction avec le modèle
            scores["Situation professionnelle"] = model_situation_professionnelle.predict(profession_data)[0]

            # Situation financière
            financial_status_key = next(
                (key for key, value in client.SITUATION_BANCAIRE_CHOICES if value == client.situation_bancaire), None
            )
            encoded_financial_status = encoder_situation_bancaire.transform([[financial_status_key]])[0][0]
            scores["Situation financière"] = model_situation_financiere.predict([
                [client.revenu_mensuel, client.depense_mensuelles, client.dettes_existantes, client.nbr_dependant, duree_emploie, encoded_financial_status]
            ])[0]

            # Capacité de remboursement
            repayment_capacity_data = [
                client.revenu_mensuel, 
                client.depense_mensuelles, 
                client.dettes_existantes, 
                self.montant_total, 
                self.sous_type_credit.taux_interet,
            ]
            scores["Capacité de remboursement"] = model_capacite_remboursement.predict([repayment_capacity_data])
            scores["Capacité de remboursement"] = encoder_capacite_remboursement.inverse_transform(scores["Capacité de remboursement"])[0]
            
            scores_dict = {
                "situation_familiale": scores["Situation familiale"],
                "situation_professionnelle": scores["Situation professionnelle"],
                "situation_financiere": scores["Situation financière"],
                "ponctualite": client.calculer_ponctualite(),
                "capacite_remboursement": scores["Capacité de remboursement"],
            }
               
            if(self.sous_type_credit.type_credit.nom == 'Crédit aux Entrepreneurs'):
                scores_dict = {
                "situation_familiale": scores["Situation familiale"],
                "situation_professionnelle": scores["Situation professionnelle"],
                "situation_financiere": scores["Situation financière"],
                "ponctualite": client.calculer_ponctualite(),
                "capacite_remboursement": scores["Capacité de remboursement"],
                "inspection_environnement": self.get_scoring_inspection(user)['inspection_environnement'],
            }

            return scores_dict

        except Exception as e:
            raise RuntimeError(f"Erreur lors du calcul du scoring client: {e}")
        
    def get_scoring_inspection(self,user):
        from ..models import InspectionEnvironnement
        model_manager = ModelManager()
        try:
            modele_inspection_environnement =  model_manager.load_model("inspection_environnement",user)
            encoder_inspection_environnement = model_manager.load_encoder("inspection_environnement")
            encoder_statut_judiciaire = model_manager.load_encoder("statut_juridique") 
            
            inspection_environnement =  InspectionEnvironnement.objects.get(demande_inspectee = self)
            
            data_dict = {
                "statut_juridique": inspection_environnement.statut_juridique,
                "annee_creation": inspection_environnement.annee_creation,
                "etat_locaux": inspection_environnement.etat_locaux,
                "nombre_employes": inspection_environnement.nombre_employes,
                "revenu_moyen_mensuel": inspection_environnement.revenu_moyen_mensuel,
                "depenses_moyennes_mensuelles": inspection_environnement.depenses_moyennes_mensuelles,
                "rentabilite_estimee": inspection_environnement.rentabilite_estimee,
                "systeme_gestion": inspection_environnement.systeme_gestion,
                "nombre_clients_reguliers": inspection_environnement.nombre_clients_reguliers,
                "niveau_concurrence": inspection_environnement.niveau_concurrence,
            }
            
            data_dict["statut_juridique"] = encoder_statut_judiciaire.transform([data_dict["statut_juridique"]])[0]
            ordinal_features = ["etat_locaux", "systeme_gestion", "niveau_concurrence"]
            ordinal_values = [[data_dict[feature] for feature in ordinal_features]]
            encoded_ordinal_values = encoder_inspection_environnement.transform(ordinal_values)[0]
            
            final_data = np.array([
                data_dict["statut_juridique"],
                data_dict["annee_creation"],
                encoded_ordinal_values[0],
                data_dict["nombre_employes"],
                data_dict["revenu_moyen_mensuel"],
                data_dict["depenses_moyennes_mensuelles"],
                data_dict["rentabilite_estimee"],
                encoded_ordinal_values[1],
                data_dict["nombre_clients_reguliers"],
                encoded_ordinal_values[2],
            ]).reshape(1, -1)
            
            prediction = modele_inspection_environnement.predict(final_data)[0]
            
            score_dict = {
                'inspection_environnement': prediction
            }
            
            return score_dict
        except Exception as e:
            raise RuntimeError(f"Erreur lors du calcul du scoring client: {e}")

    
    def __str__(self):
        return f"Demande {self.numero_credit} - {self.client}"
    
    
