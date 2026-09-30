from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .realtime import groupe_utilisateur


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Canal personnel : chaque utilisateur connecté reçoit ses notifications en direct."""

    groupe = None

    async def connect(self):
        utilisateur = self.scope['user']
        if not utilisateur.is_authenticated:
            await self.close(code=4401)
            return
        self.groupe = groupe_utilisateur(utilisateur.pk)
        await self.channel_layer.group_add(self.groupe, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'compteur', 'nb': await self._nb_non_lues(utilisateur)})

    async def disconnect(self, code):
        if self.groupe:
            await self.channel_layer.group_discard(self.groupe, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})

    # Messages envoyés par notifs.realtime via la couche de canaux
    async def notification_nouvelle(self, event):
        await self.send_json(event['donnees'])

    async def notification_compteur(self, event):
        await self.send_json({'type': 'compteur', 'nb': event['nb']})

    @database_sync_to_async
    def _nb_non_lues(self, utilisateur):
        return utilisateur.notifications.filter(lue=False).count()
