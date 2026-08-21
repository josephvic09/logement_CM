from django.contrib import admin
from .models import Paiement, Abonnement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display  = ['reference', 'utilisateur', 'montant', 'methode', 'statut', 'cree_le']
    list_filter   = ['statut', 'methode', 'type_paiement']
    search_fields = ['reference', 'utilisateur__email']
    readonly_fields = ['reference', 'uuid', 'cree_le']


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'plan', 'statut', 'debut', 'fin']
    list_filter  = ['plan', 'statut']