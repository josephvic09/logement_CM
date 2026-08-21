from django.urls import path
from . import views

app_name = 'paiements'

urlpatterns = [
    # Réservation
    path('payer/<int:reservation_id>/',
         views.initier_paiement,
         name='payer'),
    path('confirmer/<uuid:paiement_uuid>/',
         views.confirmer_paiement,
         name='confirmer'),
    path('recu/<uuid:paiement_uuid>/',
         views.recu_paiement,
         name='recu'),
    path('recu/<uuid:paiement_uuid>/telecharger/',
         views.telecharger_recu,
         name='telecharger_recu'),
    path('annuler/<uuid:paiement_uuid>/',
         views.annuler_paiement,
         name='annuler'),

    # Historique
    path('historique/',
         views.historique_paiements,
         name='historique'),

    # Abonnements
    path('abonnements/',
         views.abonnements,
         name='abonnements'),
    path('abonnements/souscrire/',
         views.souscrire_abonnement,
         name='souscrire_abonnement'),
    path('abonnements/confirmer/<uuid:paiement_uuid>/<str:plan>/',
         views.confirmer_abonnement,
         name='confirmer_abonnement'),
]