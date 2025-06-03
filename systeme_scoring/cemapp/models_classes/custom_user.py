from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from .agence import Agence
from datetime import date

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, role=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            username=username,
            email=self.normalize_email(email),
            role=role
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, role=None):
        user = self.create_user(username, email, password, role='admin')
        user.is_admin = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('directeur_agence', "Directeur de l' Agence"),
        ('analyste_demande','Analyste des Demandes'),
        ('gestionnaire', 'Gestionnaire des Demandes'),
        ('service_client', 'Service Client'),
        ('agent_inspection', "Agent d' Inspection"),
    ]

    agence = models.ForeignKey(Agence, on_delete=models.CASCADE, default=1)

    nom = models.CharField(max_length=255, default="Anonyme")
    prenom = models.CharField(max_length=255, default="Anonyme")
    date_naissance = models.DateField(default=date(1990, 1, 1))

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    numero_telephone = models.CharField(max_length=15,blank=True,null=True)
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default='service_client')

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'role']
    
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username