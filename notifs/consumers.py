from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from . import presence
from .realtime import groupe_utilisateur


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """Canal personnel : notifications en direct et présence en ligne."""

    groupe = None
    groupe_presence = None   # arrivées/départs des utilisateurs que cet utilisateur observe
    role_observe = None
    est_suivi = False        # bailleurs et locataires sont visibles par l'autre côté

    async def connect(self):
        utilisateur = self.scope['user']
        if not utilisateur.is_authenticated:
            await self.close(code=4401)
            return
        self.groupe = groupe_utilisateur(utilisateur.pk)
        self.role_observe = presence.role_observe(utilisateur.role)
        self.groupe_presence = presence.groupe(self.role_observe)
        self.est_suivi = utilisateur.role in presence.ROLES_SUIVIS

        await self.channel_layer.group_add(self.groupe, self.channel_name)
        await self.channel_layer.group_add(self.groupe_presence, self.channel_name)
        await self.accept()

        await self.send_json({'type': 'compteur', 'nb': await self._nb_non_lues(utilisateur)})
        await self.send_json({
            'type': 'presence',
            'cible': self.role_observe,
            'utilisateurs': await self._fiches(),
        })
        if self.est_suivi and presence.connecter(utilisateur.pk):
            await self._annoncer(utilisateur, en_ligne=True)

    async def disconnect(self, code):
        if self.groupe:
            await self.channel_layer.group_discard(self.groupe, self.channel_name)
        if self.groupe_presence:
            await self.channel_layer.group_discard(self.groupe_presence, self.channel_name)
        utilisateur = self.scope['user']
        if self.est_suivi and presence.deconnecter(utilisateur.pk):
            await self._annoncer(utilisateur, en_ligne=False)

    async def receive_json(self, content, **kwargs):
        if content.get('type') == 'ping':
            await self.send_json({'type': 'pong'})

    async def _annoncer(self, utilisateur, en_ligne):
        await self.channel_layer.group_send(presence.groupe(utilisateur.role), {
            'type': 'presence.changement', 'en_ligne': en_ligne, 'utilisateur_id': utilisateur.pk,
        })

    # Messages envoyés via la couche de canaux
    async def notification_nouvelle(self, event):
        await self.send_json(event['donnees'])

    async def notification_compteur(self, event):
        await self.send_json({'type': 'compteur', 'nb': event['nb']})

    async def presence_changement(self, event):
        if event['en_ligne']:
            fiches = await self._fiches(ids=[event['utilisateur_id']])
            if not fiches:
                return
            utilisateur = fiches[0]
        else:
            utilisateur = {'id': event['utilisateur_id']}
        await self.send_json({
            'type': 'presence_changement',
            'en_ligne': event['en_ligne'],
            'utilisateur': utilisateur,
        })

    @database_sync_to_async
    def _fiches(self, ids=None):
        return presence.fiches(self.role_observe, self.scope['user'], ids)

    @database_sync_to_async
    def _nb_non_lues(self, utilisateur):
        return utilisateur.notifications.filter(lue=False).count()
