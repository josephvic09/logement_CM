from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['destinataire', 'type_notif', 'titre', 'lue', 'cree_le']
    list_filter   = ['type_notif', 'lue']
    search_fields = ['destinataire__email', 'titre']