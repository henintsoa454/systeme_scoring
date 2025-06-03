from django.db import models
from .custom_user import CustomUser
from .demande_credit import DemandeCredit
import datetime
import uuid
from django.db import models
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

class RendezvousDirecteur(models.Model):
    directeur = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    demande = models.ForeignKey(DemandeCredit, on_delete=models.CASCADE)
    date_rendezvous = models.DateTimeField(default=timezone.now)
    termine = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    modification_count = models.PositiveIntegerField(default=0)
    date_proposee = models.DateTimeField(null=True, blank=True)
    statut_proposition = models.CharField(
        max_length=20,
        choices=[
            ('en_attente', 'En attente'),
            ('acceptee', 'Acceptée'),
            ('refusee', 'Refusée')
        ],
        default='en_attente'
    )
    motif_refus = models.TextField(null=True, blank=True)
    raison_proposition = models.TextField(
        null=True, 
        blank=True,
        verbose_name="Raison du changement de date"
    )
    
    def __str__(self):
        return f"Inspection {self.demande.numero_credit} - {self.date_rendezvous}"
    
    def is_modifiable(self):
        now = datetime.now()
        return self.modification_count < 1 and self.date_rendezvous - datetime.timedelta(days=3) > now
    
    def envoyer_notification(self):
        subject = f"Rendez-vous pour finaliser votre demande de crédit N° : {self.demande.numero_credit}"
        html_message = render_to_string('emails/notification_finalisation.html', {
            'rendezvous': self,
            'modification_url': f"{settings.BASE_URL}/proposer-date-finale/{self.token}/"
        })
        plain_message = strip_tags(html_message)
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.demande.client.email],
            html_message=html_message
        )