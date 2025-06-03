import random
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from cemapp.models import DemandeCredit, RemboursementCredit

class Command(BaseCommand):
    help = 'Generate test data for credit system from 2000 to present'

    def handle(self, *args, **options):
        # Période de génération : 2000 à aujourd'hui
        start_date = datetime(2000, 1, 1)
        end_date = datetime.now()
        today = datetime.now().date()
        
        # Paramètres fixes pour les clés étrangères
        AGENCE_ID = 1
        CLIENT_IDS = [5, 6, 7, 8]  # IDs des clients disponibles
        SOUS_TYPE_ID = 1
        USER_ID = 1

        current_date = start_date
        while current_date <= end_date:
            num_demandes = random.randint(3, 10)
            
            for i in range(num_demandes):
                date_demande = current_date.replace(day=random.randint(1, 28))
                date_demande_date = timezone.make_aware(date_demande).date()
                duree = random.choice([6, 12, 18, 24])
                montant_total = random.randint(300000, 19000000)
                montant_mensuel = round(montant_total / duree, 2)
                
                # Créer la demande de crédit
                demande = DemandeCredit.objects.create(
                    numero_credit=f"CAS-{date_demande.strftime('%m%d%Y')}-{i+1}",
                    agence_id=AGENCE_ID,
                    client_id=random.choice(CLIENT_IDS),
                    sous_type_credit_id=SOUS_TYPE_ID,
                    duree=duree,
                    montant_total=montant_total,
                    montant_payer_mois=montant_mensuel,
                    motif_credit=random.choice([
                        "Achat équipement", 
                        "Fond de roulement",
                        "Extension activité",
                        "Projet personnel",
                        "Santé",
                        "Education",
                        "Achat véhicule"
                    ]),
                    date_demande=date_demande_date,
                    statut_demande='approuve',
                    date_derniere_maj=date_demande_date + timedelta(days=random.randint(1, 3)),
                    enregistre_par_id=USER_ID,
                    traite_par_id=USER_ID
                )
                
                # Créer les remboursements avec dates réalistes
                for mois in range(1, duree + 1):
                    date_echeance = date_demande_date + relativedelta(months=mois)
                    
                    # Ne créer le remboursement que si la date d'échéance est passée
                    if date_echeance <= today:
                        # Déterminer si le paiement est à temps ou en retard
                        if random.random() < 0.9:  # 90% à temps
                            date_paiement = date_echeance - timedelta(days=random.randint(0, 3))
                        else:  # 10% en retard
                            date_paiement = date_echeance + timedelta(days=random.randint(1, 15))
                        
                        # S'assurer que la date de paiement n'est pas dans le futur
                        date_paiement = min(date_paiement, today)
                        
                        RemboursementCredit.objects.create(
                            demande=demande,
                            numero_paiement=mois,
                            somme_attendu=montant_mensuel,
                            somme_paye=montant_mensuel,
                            type_paiement='normal',
                            statut='payé',
                            penalite=0,
                            date_echeance=date_echeance,
                            date_paiement=date_paiement
                        )
                    else:
                        # Pour les échéances futures, créer seulement l'échéance sans paiement
                        RemboursementCredit.objects.create(
                            demande=demande,
                            numero_paiement=mois,
                            somme_attendu=montant_mensuel,
                            somme_paye=0,
                            type_paiement='normal',
                            statut='en_retard' if date_echeance < today else 'à venir',
                            penalite=0,
                            date_echeance=date_echeance,
                            date_paiement=None
                        )
                
                self.stdout.write(f'Créé demande {demande.numero_credit} (montant: {montant_total:,} MGA) avec {duree} remboursements')

            # Passer au mois suivant
            current_date += relativedelta(months=1)
            if current_date.month == 1:
                self.stdout.write(f"Terminé année {current_date.year-1}")

        self.stdout.write(self.style.SUCCESS('Données générées avec succès!'))