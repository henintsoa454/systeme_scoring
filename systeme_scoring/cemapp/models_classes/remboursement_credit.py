from datetime import timedelta
from django.db import models
from django.utils.timezone import now
from .demande_credit import DemandeCredit

class RemboursementCredit(models.Model):    
    TYPE_CHOICES = [
        ('normal', 'Normal'),
        ('anticipe', 'Remboursement anticipé'),
    ]
    STATUT_CHOICES = [
        ('payé', 'Payé'),
        ('en_retard', 'En Retard'),
        ('anticipé', 'Anticipé'),
    ]

    demande = models.ForeignKey(DemandeCredit, on_delete=models.CASCADE, related_name='remboursements')
    date_paiement = models.DateTimeField(default=now)
    somme_paye = models.DecimalField(max_digits=10, decimal_places=2)
    somme_attendu = models.DecimalField(max_digits=10, decimal_places=2)
    numero_paiement = models.IntegerField()
    type_paiement = models.CharField(max_length=20, choices=TYPE_CHOICES, default='normal', null=False, blank=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='payé')
    date_echeance = models.DateField(editable=False)
    penalite = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['numero_paiement']
        unique_together = ('demande', 'numero_paiement')

    def __str__(self):
        return f"Remboursement {self.numero_paiement} - {self.demande.numero_credit}"

    def clean(self):
        super().clean()
        if self.somme_paye > self.montant_restant():
            raise ValueError("Le montant payé ne peut pas dépasser le montant restant.")

    def montant_restant(self):
        total_paye = self.demande.remboursements.aggregate(models.Sum('somme_paye'))['somme_paye__sum'] or 0
        return self.demande.montant_total - total_paye

    def retard_en_jours(self):
        if self.date_paiement > self.date_echeance:
            return (self.date_paiement - self.date_echeance).days
        return 0
