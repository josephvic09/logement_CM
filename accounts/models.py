from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
import uuid


class UtilisateurManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'SUPER_ADMIN')
        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ('LOCATAIRE',   'Locataire'),
        ('BAILLEUR',    'Bailleur'),
        ('ADMIN',       'Administrateur'),
        ('SUPER_ADMIN', 'Super Administrateur'),
    ]
    GENRE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('A', 'Autre'),
    ]

    uuid           = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email          = models.EmailField(unique=True)
    nom            = models.CharField(max_length=100)
    prenom         = models.CharField(max_length=100)
    telephone      = models.CharField(max_length=20, blank=True)
    genre          = models.CharField(max_length=1, choices=GENRE_CHOICES, blank=True)
    date_naissance = models.DateField(null=True, blank=True)
    bio            = models.TextField(blank=True, max_length=500)
    avatar         = models.ImageField(upload_to='avatars/%Y/%m/', blank=True)

    ville    = models.CharField(max_length=100, blank=True, default='Yaoundé')
    quartier = models.CharField(max_length=100, blank=True)
    adresse  = models.CharField(max_length=255, blank=True)

    role       = models.CharField(max_length=20, choices=ROLE_CHOICES, default='LOCATAIRE')
    is_active  = models.BooleanField(default=False)
    is_staff   = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_premium  = models.BooleanField(default=False)

    email_verified         = models.BooleanField(default=False)
    email_verify_token     = models.CharField(max_length=64, blank=True)
    reset_password_token   = models.CharField(max_length=64, blank=True)
    reset_password_expires = models.DateTimeField(null=True, blank=True)

    notifications_email = models.BooleanField(default=True)
    notifications_push  = models.BooleanField(default=True)
    mode_sombre         = models.BooleanField(default=False)

    premium_debut = models.DateTimeField(null=True, blank=True)
    premium_fin   = models.DateTimeField(null=True, blank=True)

    nb_connexions         = models.PositiveIntegerField(default=0)
    derniere_connexion_ip = models.GenericIPAddressField(null=True, blank=True)

    date_inscription  = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['nom', 'prenom']
    objects = UtilisateurManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_inscription']

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"

    def get_full_name(self):
        return f"{self.prenom} {self.nom}".strip()

    def get_short_name(self):
        return self.prenom

    @property
    def est_bailleur(self):
        return self.role in ('BAILLEUR', 'ADMIN', 'SUPER_ADMIN')

    @property
    def est_admin(self):
        return self.role in ('ADMIN', 'SUPER_ADMIN')

    @property
    def premium_actif(self):
        if self.is_premium and self.premium_fin:
            return timezone.now() <= self.premium_fin
        return False

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return '/static/images/avatar_default.png'


class LogActivite(models.Model):

    ACTION_CHOICES = [
        ('CONNEXION',      'Connexion'),
        ('DECONNEXION',    'Déconnexion'),
        ('INSCRIPTION',    'Inscription'),
        ('MODIF_PROFIL',   'Modification profil'),
        ('MODIF_MDP',      'Changement mot de passe'),
        ('RESET_MDP',      'Réinitialisation MDP'),
        ('ANNONCE_CREATE', 'Création annonce'),
        ('ANNONCE_UPDATE', 'Modification annonce'),
        ('ANNONCE_DELETE', 'Suppression annonce'),
        ('RESERVATION',    'Réservation'),
        ('PAIEMENT',       'Paiement'),
        ('SIGNALEMENT',    'Signalement'),
    ]

    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    action      = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    succes      = models.BooleanField(default=True)
    cree_le     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log d'activité"
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.utilisateur} - {self.action}"