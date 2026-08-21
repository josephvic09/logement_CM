from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/',                         views.inscription,                name='inscription'),
    path('connexion/',                           views.connexion,                  name='connexion'),
    path('deconnexion/',                         views.deconnexion,                name='deconnexion'),
    path('verifier-email/<str:token>/',          views.verifier_email,             name='verifier_email'),
    path('verification-envoyee/',                views.verification_email_envoyee, name='verification_email_envoyee'),
    path('reset-password/',                      views.reset_password_demande,     name='reset_password_demande'),
    path('reset-password/<str:token>/',          views.reset_password_confirmer,   name='reset_password_confirmer'),
    path('changer-mot-de-passe/',                views.changer_mot_de_passe,       name='changer_mdp'),
    path('profil/',                              views.profil,                     name='profil'),
    path('tableau-de-bord/',                     views.tableau_de_bord,            name='tableau_de_bord'),
    path('tableau-de-bord/locataire/',           views.dashboard_locataire,        name='dashboard_locataire'),
    path('tableau-de-bord/bailleur/',            views.dashboard_bailleur,         name='dashboard_bailleur'),
    path('tableau-de-bord/admin/',               views.dashboard_admin,            name='dashboard_admin'),
    path('mes-favoris/',                         views.mes_favoris,                name='mes_favoris'),
    path('mes-reservations/',                    views.mes_reservations,           name='mes_reservations'),
    path('comparer/',                            views.comparer_logements,         name='comparer'),
    path('mes-annonces/',                        views.mes_annonces,               name='mes_annonces'),
    path('gerer-reservations/',                  views.gerer_reservations,         name='gerer_reservations'),
    path('reservations/<int:reservation_id>/repondre/', views.repondre_reservation,name='repondre_reservation'),
    path('admin/utilisateurs/',                        views.admin_utilisateurs,        name='admin_utilisateurs'),
path('admin/utilisateurs/<int:user_id>/toggle/',   views.admin_toggle_user,         name='admin_toggle_user'),
path('admin/logements/',                           views.admin_logements,           name='admin_logements'),
path('admin/signalements/',                        views.admin_signalements,        name='admin_signalements'),
path('admin/signalements/<int:signal_id>/traiter/',views.admin_traiter_signalement, name='admin_traiter_signalement'),
]