from django.urls import path
from . import views

app_name = 'logements'

urlpatterns = [

    # ─── Pages principales ───────────────────────────
    path('',
         views.accueil,
         name='accueil'),

    path('recherche/',
         views.recherche,
         name='recherche'),

    path('carte/',
         views.carte,
         name='carte'),

    # ─── Gestion annonces (Bailleur) ─────────────────
    path('creer/',
         views.creer_logement,
         name='creer'),

    path('modifier/<slug:slug>/',
         views.modifier_logement,
         name='modifier'),

    path('supprimer/<slug:slug>/',
         views.supprimer_logement,
         name='supprimer'),

    # ─── Détail logement ─────────────────────────────
    path('logements/<slug:slug>/',
         views.detail_logement,
         name='detail'),

    # ─── Actions ─────────────────────────────────────
    path('logements/<int:logement_id>/favori/',
         views.toggle_favori,
         name='toggle_favori'),

    path('logements/<int:logement_id>/reserver/',
         views.faire_reservation,
         name='reserver'),

    path('logements/<int:logement_id>/signaler/',
         views.signaler_logement,
         name='signaler'),

    # ─── Admin ───────────────────────────────────────
    
    path('gestion/logements/<int:logement_id>/valider/',
     views.admin_valider_logement,
     name='admin_valider'),

    # ─── API ─────────────────────────────────────────
    path('api/quartiers/',
         views.api_quartiers_par_ville,
         name='api_quartiers'),

    path('api/logements/carte/',
         views.api_logements_carte,
         name='api_carte'),

]