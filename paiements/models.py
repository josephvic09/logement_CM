from django.db import models
from accounts.models import Utilisateur
from logements.models import Reservation
import uuid
import random
import string


class Paiement(models.Model):

    TYPE_CHOICES = [
        ('RESERVATION', 'Réservation logement'),
        ('ABONNEMENT',  'Abonnement premium'),
        ('BOOST',       'Boost annonce'),
    ]
    METHODE_CHOICES = [
        ('MTN_MOMO',     'MTN Mobile Money'),
        ('ORANGE_MONEY', 'Orange Money'),
        ('ESPECES',      'Espèces'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE',  'En attente'),
        ('TRAITEMENT',  'En cours de traitement'),
        ('REUSSI',      'Réussi'),
        ('ECHOUE',      'Échoué'),
        ('REMBOURSE',   'Remboursé'),
        ('ANNULE',      'Annulé'),
    ]

    uuid              = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    reference         = models.CharField(max_length=50, unique=True, blank=True)
    utilisateur       = models.ForeignKey(
                          Utilisateur, on_delete=models.CASCADE,
                          related_name='paiements'
                        )
    type_paiement     = models.CharField(max_length=20, choices=TYPE_CHOICES)
    methode           = models.CharField(max_length=20, choices=METHODE_CHOICES)
    montant           = models.PositiveBigIntegerField()
    statut            = models.CharField(
                          max_length=20, choices=STATUT_CHOICES,
                          default='EN_ATTENTE'
                        )
    reservation       = models.ForeignKey(
                          Reservation, on_delete=models.SET_NULL,
                          null=True, blank=True, related_name='paiements'
                        )
    telephone         = models.CharField(max_length=20, blank=True)
    transaction_id    = models.CharField(max_length=100, blank=True)
    code_confirmation = models.CharField(max_length=10, blank=True)
    message_operateur = models.TextField(blank=True)
    cree_le           = models.DateTimeField(auto_now_add=True)
    traite_le         = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Paiement'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.reference} — {self.montant_formate} ({self.get_statut_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = 'LCM' + ''.join(
                random.choices(string.digits, k=10)
            )
        if not self.code_confirmation:
            self.code_confirmation = ''.join(
                random.choices(string.digits, k=6)
            )
        super().save(*args, **kwargs)

    @property
    def montant_formate(self):
        return f"{self.montant:,} FCFA".replace(',', ' ')

    @property
    def est_reussi(self):
        return self.statut == 'REUSSI'

    def generer_transaction_id(self):
        """Simule un ID de transaction opérateur."""
        prefix = 'MTN' if self.methode == 'MTN_MOMO' else 'ORG'
        return prefix + ''.join(random.choices(string.digits, k=12))


class Abonnement(models.Model):

    PLAN_CHOICES = [
        ('BASIC',    'Basic — Gratuit'),
        ('STARTER',  'Starter — 5 000 FCFA/mois'),
        ('PRO',      'Pro — 10 000 FCFA/mois'),
        ('BUSINESS', 'Business — 25 000 FCFA/mois'),
    ]
    STATUT_CHOICES = [
        ('ACTIF',  'Actif'),
        ('EXPIRE', 'Expiré'),
        ('ANNULE', 'Annulé'),
    ]
    PRIX_PLANS = {
        'BASIC':    0,
        'STARTER':  5000,
        'PRO':      10000,
        'BUSINESS': 25000,
    }
    ANNONCES_PLANS = {
        'BASIC':    3,
        'STARTER':  10,
        'PRO':      30,
        'BUSINESS': 100,
    }

    utilisateur = models.ForeignKey(
                    Utilisateur, on_delete=models.CASCADE,
                    related_name='abonnements'
                  )
    plan        = models.CharField(
                    max_length=20, choices=PLAN_CHOICES,
                    default='BASIC'
                  )
    statut      = models.CharField(
                    max_length=20, choices=STATUT_CHOICES,
                    default='ACTIF'
                  )
    debut       = models.DateTimeField()
    fin         = models.DateTimeField()
    paiement    = models.ForeignKey(
                    Paiement, on_delete=models.SET_NULL,
                    null=True, blank=True
                  )
    cree_le     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Abonnement'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.utilisateur} — {self.get_plan_display()}"

    @property
    def prix(self):
        return self.PRIX_PLANS.get(self.plan, 0)

    @property
    def nb_annonces_autorisees(self):
        return self.ANNONCES_PLANS.get(self.plan, 3)