from django.core.management.base import BaseCommand
from cemapp.models import DemandeCredit, RemboursementCredit

class Command(BaseCommand):
    help = 'Supprime les demandes de crédit ne commençant pas par CAS'

    def handle(self, *args, **options):
        # Compter le nombre de demandes avant suppression
        total_avant = DemandeCredit.objects.count()
        
        # Récupérer les demandes à supprimer
        demandes_a_supprimer = DemandeCredit.objects.exclude(numero_credit__startswith='CAS')
        
        # Supprimer les remboursements associés en premier
        for demande in demandes_a_supprimer:
            RemboursementCredit.objects.filter(demande=demande).delete()
        
        # Supprimer les demandes
        nb_supprimes, _ = demandes_a_supprimer.delete()
        
        # Compter le nombre de demandes après suppression
        total_apres = DemandeCredit.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Suppression terminée : {nb_supprimes} demandes supprimées '
                f'(total avant: {total_avant}, après: {total_apres})'
            )
        )