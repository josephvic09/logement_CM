from django.urls import path
from . import views

app_name = 'notifs'

urlpatterns = [
    path('',
         views.liste_notifications,
         name='liste'),
    path('marquer-lues/',
         views.marquer_lues,
         name='marquer_lues'),
    path('<int:notif_id>/lue/',
         views.marquer_lue,
         name='marquer_lue'),
    path('<int:notif_id>/supprimer/',
         views.supprimer_notification,
         name='supprimer'),
    path('count/',
         views.compte_non_lues,
         name='count'),
    path('dernieres/',
         views.dernieres_notifications,
         name='dernieres'),
]