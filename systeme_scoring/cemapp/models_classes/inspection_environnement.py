from django.db import models
from .demande_credit import DemandeCredit
from .custom_user import CustomUser

class InspectionEnvironnement(models.Model):
    STATUT_JURIDIQUE_CHOICES = [
        ('individuelle', 'Entreprise individuelle'),
        ('sarl', 'SARL'),
        ('sa', 'SA'),
        ('autres', 'Autres'),
    ]

    ETAT_LOCAUX_CHOICES = [
        ('excellent', 'Excellent'),
        ('bon', 'Bon'),
        ('moyen', 'Moyen'),
        ('mediocre', 'Médiocre'),
    ]

    SYSTEME_GESTION_CHOICES = [
        ('manuel', 'Manuel'),
        ('informatise', 'Informatisé'),
    ]

    NIVEAU_CONCURRENCE_CHOICES = [
        ('faible', 'Faible'),
        ('moyen', 'Moyen'),
        ('fort', 'Fort'),
    ]
    
    nom_entreprise = models.CharField(max_length=255)
    adresse = models.TextField()
    secteur_activite = models.CharField(max_length=100)
    statut_juridique = models.CharField(max_length=50, choices=STATUT_JURIDIQUE_CHOICES)
    annee_creation = models.IntegerField()
    etat_locaux = models.CharField(max_length=50, choices=ETAT_LOCAUX_CHOICES)
    types_equipements = models.TextField(help_text="Liste des équipements disponibles")
    nombre_employes = models.IntegerField()
    qualification_personnel = models.TextField()
    systeme_gestion = models.CharField(max_length=50, choices=SYSTEME_GESTION_CHOICES)
    revenu_moyen_mensuel = models.DecimalField(max_digits=12, decimal_places=2)
    depenses_moyennes_mensuelles = models.DecimalField(max_digits=12, decimal_places=2)
    rentabilite_estimee = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Revenu - Dépenses"
    )
    nombre_clients_reguliers = models.IntegerField()
    zone_geographique_ventes = models.TextField()
    niveau_concurrence = models.CharField(max_length=50, choices=NIVEAU_CONCURRENCE_CHOICES)
    dependance_principale = models.TextField(
        help_text="Dépendance à un fournisseur ou client spécifique", blank=True, null=True
    )
    date_inspection = models.DateField(auto_now_add=True)
    inspecte_par = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, null=True, related_name='inspections'
    )
    demande_inspectee = models.ForeignKey(
        DemandeCredit, on_delete=models.SET_NULL, null=True, related_name='demandes_inspectee'
    )

    def __str__(self):
        return f"Inspection - {self.nom_entreprise} ({self.date_inspection})"

    class Meta:
        verbose_name = "Inspection Environnement"
        verbose_name_plural = "Inspections Environnements"
        ordering = ['-date_inspection']
