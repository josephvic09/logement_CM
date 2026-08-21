from django.urls import path
from . import views
from . import views_auth, views_logements

app_name = 'api'

urlpatterns = [
    path('logements/',  views.LogementsAPIView.as_view(), name='logements'),
    path('quartiers/',  views.quartiers_api,               name='quartiers'),
    path('villes/',     views.villes_api,                  name='villes'),
    path('stats/',      views.stats_api,    name='stats'), 
    path('auth/inscription/', views_auth.inscription, name='api_inscription'),
    path('auth/connexion/',   views_auth.connexion,   name='api_connexion'),
    path('auth/profil/',      views_auth.profil,      name='api_profil'),

    # Logements
    path('logements/',        views_logements.liste_logements, name='api_logements'),
    path('logements/<int:pk>/', views_logements.detail_logement, name='api_detail_logement'),
]               
