from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView


urlpatterns = [
    # Administration Django
    path('admin/', admin.site.urls),

    # Page d'accueil et logements
    path('', include('logements.urls', namespace='logements')),

    # Comptes utilisateurs
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Chat et chatbot
    path('chat/', include('chat.urls', namespace='chat')),

    # Notifications
    path('notifications/', include('notifs.urls', namespace='notifs')),

    # Paiements
    path('paiements/', include('paiements.urls', namespace='paiements')),

    # API REST
    path('api/v1/', include('api.urls', namespace='api')),
    path('api/', include('api.urls')),
    # PWA — Service Worker à la racine
    path('sw.js', TemplateView.as_view(
        template_name='sw.js',
        content_type='application/javascript'
    ), name='sw'),

    # PWA — Manifest
    path('manifest.json', TemplateView.as_view(
        template_name='manifest.json',
        content_type='application/json'
    ), name='manifest'),
]

# Servir les fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personnalisation admin
admin.site.site_header  = "LogementCM Administration"
admin.site.site_title   = "LogementCM"
admin.site.index_title  = "Panneau d'administration"


 