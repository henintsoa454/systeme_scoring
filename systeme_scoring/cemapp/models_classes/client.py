from django.db import models
from django.db.models import Sum, F
from django.core.exceptions import ValidationError
from datetime import date
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

class Client(models.Model):
    STATUT_FAMILIAL_CHOICES = [
        ('celibataire', 'Célibataire'),
        ('marie', 'Marié(e)'),
        ('divorce', 'Divorcé(e)'),
        ('veuf', 'Veuf/Veuve'),
    ]
    
    SITUATION_PROFESSIONNELLE_CHOICES = [
        ('employe', 'Employé'),
        ('independant', 'Indépendant'),
        ('etudiant', 'Étudiant'),
        ('retraite', 'Retraité'),
        ('sans_emploi', 'Sans emploi'),
    ]
    
    SECTEUR_ACTIVITE_CHOICES = [
        ('agriculture', 'Agriculture'),
        ('industrie', 'Industrie'),
        ('services', 'Services'),
        ('commerce', 'Commerce'),
        ('education', 'Éducation'),
        ('sante', 'Santé'),
        ('informatique', 'Informatique'),
        ('autres', 'Autres'),
        ('aucun', 'aucun'),
    ]
    
    TYPE_CONTRAT_CHOICES = [
        ('cdi', 'CDI'),
        ('cdd', 'CDD'),
        ('freelance', 'Freelance'),
        ('temporaire', 'Temporaire'),
        ('stage', 'Stage'),
        ('aucun', 'Aucun'),
    ]
    
    SITUATION_BANCAIRE_CHOICES = [
        ('excellent', 'Excellent'),
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('faible', 'Faible'),
        ('mauvais', 'Mauvais'),
    ]


    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    date_naissance = models.DateField()
    adresse = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    numero_telephone = models.CharField(max_length=15,blank=True,null=True)
    n_cin = models.CharField(max_length=12)
    statut_familial = models.CharField(max_length=50, choices=STATUT_FAMILIAL_CHOICES)
    nbr_dependant = models.IntegerField(blank=True, null=True)
    situation_professionnelle = models.CharField(max_length=50, choices=SITUATION_PROFESSIONNELLE_CHOICES)
    titre_emploie = models.CharField(max_length=100, blank=True, null=True)
    nom_employeur = models.CharField(max_length=255, blank=True, null=True)
    adresse_professionnelle = models.CharField(max_length=255, blank=True, null=True)
    duree_emploie = models.IntegerField(blank=True, null=True)
    revenu_mensuel = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    depense_mensuelles = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dettes_existantes = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    situation_bancaire = models.CharField(max_length=50, choices=SITUATION_BANCAIRE_CHOICES, blank=True, null=True)
    historique_credit = models.TextField(blank=True, null=True)
    solde_bancaire = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    secteur_activite = models.CharField(max_length=100, choices=SECTEUR_ACTIVITE_CHOICES, blank=True, null=True)
    type_contrat = models.CharField(max_length=50, choices=TYPE_CONTRAT_CHOICES, blank=True, null=True)
    valeur_actifs = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    historique_paiement = models.TextField(blank=True, null=True)

    def clean(self):
        if self.situation_professionnelle == 'sans_emploi':
            if self.nom_employeur or self.duree_emploie:
                raise ValidationError("Les champs liés à l'emploi ne doivent pas être remplis pour une personne sans emploi.")
            if not self.revenu_mensuel or self.revenu_mensuel <= 0:
                raise ValidationError("Veuillez spécifier un revenu alternatif pour une personne sans emploi.")

    def age(self):
        today = date.today()
        return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)) 
    
    def calculer_ponctualite(self):
        from ..models import DemandeCredit, RemboursementCredit  # Import local pour éviter les importations circulaires
        
        # Obtenir toutes les demandes terminées du client
        demandes_terminees = DemandeCredit.objects.filter(client=self, statut_demande='termine')

        # Obtenir tous les remboursements liés à ces demandes
        remboursements = RemboursementCredit.objects.filter(demande__in=demandes_terminees)

        # Calcul des indicateurs
        total_remboursements = remboursements.count()
        remboursements_en_retard = remboursements.filter(statut='en_retard').count()
        total_jours_retard = remboursements.filter(statut='en_retard').aggregate(
            total_retard=Sum(F('date_paiement') - F('date_echeance'))
        )['total_retard']

        taux_retards = (remboursements_en_retard / total_remboursements) * 100 if total_remboursements > 0 else 0
        retard_moyen = (total_jours_retard.days / remboursements_en_retard) if remboursements_en_retard > 0 else 0

        if total_remboursements == 0:
            score_ponctualite = 0  # Aucun historique = score 0
            niveau_ponctualite = "N/A"
        elif taux_retards <= 10:
            score_ponctualite = 90  # Ponctuel
            niveau_ponctualite = "Ponctuel"
        elif taux_retards <= 30:
            score_ponctualite = 60  # Acceptable
            niveau_ponctualite = "Acceptable"
        else:
            score_ponctualite = 30  # Médiocre
            niveau_ponctualite = "Médiocre"

        return {
            "score": score_ponctualite,
            "niveau": niveau_ponctualite,
            "taux_retards": round(taux_retards, 2),
            "retard_moyen": round(retard_moyen, 2) if remboursements_en_retard > 0 else "N/A",
        }
        
    def notifierRefus(self,raison_refus,demande):
        subject = f"Refus de votre demande de crédit : {demande.numero_credit}"
        html_message = render_to_string('emails/notification_refus.html', {
            'raisonRefus': raison_refus,
            'demande': demande
        })
        plain_message = strip_tags(html_message)
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [demande.client.email],
            html_message=html_message
        )