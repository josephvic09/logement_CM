from django.contrib import admin
from .models import Logement, PhotoLogement, Ville, Quartier, Avis, Reservation, Signalement


@admin.register(Logement)
class LogementAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'bailleur', 'ville', 'type_offre', 'prix', 'statut', 'disponible', 'cree_le']
    list_filter   = ['statut', 'type_offre', 'type_logement', 'disponible', 'ville']
    search_fields = ['titre', 'adresse', 'bailleur__email']
    actions       = ['valider_annonces', 'suspendre_annonces']

    def valider_annonces(self, request, queryset):
        queryset.update(statut='PUBLIE')
    valider_annonces.short_description = "✅ Valider les annonces"

    def suspendre_annonces(self, request, queryset):
        queryset.update(statut='SUSPENDU')
    suspendre_annonces.short_description = "⛔ Suspendre les annonces"


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'region', 'actif']
    search_fields = ['nom']


@admin.register(Quartier)
class QuartierAdmin(admin.ModelAdmin):
    list_display  = ['nom', 'ville', 'populaire']
    list_filter   = ['ville']
    search_fields = ['nom']


@admin.register(Avis)
class AvisAdmin(admin.ModelAdmin):
    list_display  = ['auteur', 'logement', 'note', 'approuve', 'cree_le']
    list_filter   = ['approuve', 'note']
    actions       = ['approuver_avis']

    def approuver_avis(self, request, queryset):
        queryset.update(approuve=True)
    approuver_avis.short_description = "✅ Approuver les avis"


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['locataire', 'logement', 'type_demande', 'statut', 'date_debut', 'cree_le']
    list_filter  = ['statut', 'type_demande']


@admin.register(Signalement)
class SignalementAdmin(admin.ModelAdmin):
    list_display = ['auteur', 'logement', 'motif', 'traite', 'cree_le']
    list_filter  = ['motif', 'traite']