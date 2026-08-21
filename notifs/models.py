from django.db import models
from accounts.models import Utilisateur


class Notification(models.Model):

    TYPE_CHOICES = [
        ('MESSAGE',     'Nouveau message'),
        ('RESERVATION', 'Réservation'),
        ('VALIDATION',  'Annonce validée'),
        ('REJET',       'Annonce rejetée'),
        ('AVIS',        'Nouvel avis'),
        ('PAIEMENT',    'Paiement'),
        ('FAVORI',      'Nouveau favori'),
        ('SYSTEME',     'Système'),
    ]

    ICONE_MAP = {
        'MESSAGE':     'message-circle',
        'RESERVATION': 'calendar-check',
        'VALIDATION':  'check-circle',
        'REJET':       'x-circle',
        'AVIS':        'star',
        'PAIEMENT':    'credit-card',
        'FAVORI':      'heart',
        'SYSTEME':     'bell',
    }

    COULEUR_MAP = {
        'MESSAGE':     '#6366f1',
        'RESERVATION': '#f59e0b',
        'VALIDATION':  '#10b981',
        'REJET':       '#ef4444',
        'AVIS':        '#f59e0b',
        'PAIEMENT':    '#10b981',
        'FAVORI':      '#ef4444',
        'SYSTEME':     '#6366f1',
    }

    destinataire = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE,
        related_name='notifications'
    )
    type_notif   = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre        = models.CharField(max_length=200)
    message      = models.TextField()
    lien         = models.CharField(max_length=300, blank=True)
    lue          = models.BooleanField(default=False)
    lue_le       = models.DateTimeField(null=True, blank=True)
    cree_le      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        ordering = ['-cree_le']
        indexes  = [
            models.Index(fields=['destinataire', 'lue']),
            models.Index(fields=['-cree_le']),
        ]

    def __str__(self):
        return f"{self.destinataire} — {self.titre}"

    @property
    def icone(self):
        return self.ICONE_MAP.get(self.type_notif, 'bell')

    @property
    def couleur(self):
        return self.COULEUR_MAP.get(self.type_notif, '#6366f1')