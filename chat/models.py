from django.db import models
from accounts.models import Utilisateur
from logements.models import Logement
import uuid


class Conversation(models.Model):

    uuid      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    locataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='conv_locataire')
    bailleur  = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='conv_bailleur')
    logement  = models.ForeignKey(Logement, on_delete=models.CASCADE,
                                   related_name='conversations', null=True, blank=True)
    archivee  = models.BooleanField(default=False)
    cree_le   = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversation'
        unique_together = [('locataire', 'bailleur', 'logement')]
        ordering = ['-modifie_le']

    def __str__(self):
        return f"{self.locataire} ↔ {self.bailleur}"

    def dernier_message(self):
        return self.messages.order_by('-cree_le').first()

    def nb_non_lus(self, utilisateur):
        return self.messages.filter(
            non_lu=True
        ).exclude(expediteur=utilisateur).count()


class Message(models.Model):

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                      related_name='messages')
    expediteur   = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,
                                      related_name='messages_envoyes')
    contenu      = models.TextField()
    non_lu       = models.BooleanField(default=True)
    lu_le        = models.DateTimeField(null=True, blank=True)
    supprime     = models.BooleanField(default=False)
    cree_le      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message'
        ordering = ['cree_le']

    def __str__(self):
        return f"{self.expediteur} : {self.contenu[:50]}"


class ConversationChatbot(models.Model):

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE,
                                     null=True, blank=True,
                                     related_name='chatbot_convs')
    session_id  = models.CharField(max_length=64)
    titre       = models.CharField(max_length=200, blank=True)
    cree_le     = models.DateTimeField(auto_now_add=True)
    modifie_le  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Conversation Chatbot'
        ordering = ['-modifie_le']

    def __str__(self):
        return f"Chatbot — {self.utilisateur or self.session_id}"


class MessageChatbot(models.Model):

    ROLE_CHOICES = [
        ('USER',      'Utilisateur'),
        ('ASSISTANT', 'Assistant IA'),
    ]

    conversation = models.ForeignKey(ConversationChatbot, on_delete=models.CASCADE,
                                      related_name='messages')
    role         = models.CharField(max_length=10, choices=ROLE_CHOICES)
    contenu      = models.TextField()
    logements_sugeres = models.ManyToManyField(Logement, blank=True)
    cree_le      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Message Chatbot'
        ordering = ['cree_le']

    def __str__(self):
        return f"{self.role} : {self.contenu[:50]}"