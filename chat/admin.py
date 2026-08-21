from django.contrib import admin
from .models import Conversation, Message, ConversationChatbot, MessageChatbot


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display  = ['locataire', 'bailleur', 'logement', 'archivee', 'modifie_le']
    list_filter   = ['archivee']
    search_fields = ['locataire__email', 'bailleur__email']


@admin.register(ConversationChatbot)
class ConversationChatbotAdmin(admin.ModelAdmin):
    list_display  = ['utilisateur', 'session_id', 'titre', 'cree_le']
    search_fields = ['utilisateur__email']