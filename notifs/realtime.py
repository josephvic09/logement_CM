"""Envoi en direct des notifications aux navigateurs connectés (Channels)."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


def groupe_utilisateur(utilisateur_id):
    return f'notifs_{utilisateur_id}'


def _envoyer(utilisateur_id, message):
    couche = get_channel_layer()
    if couche is None:
        return
    try:
        async_to_sync(couche.group_send)(groupe_utilisateur(utilisateur_id), message)
    except Exception:
        # Le temps réel est un bonus : la notification reste en base et visible au rechargement.
        pass


def pousser_notification(notif):
    """Envoie une notification toute neuve au(x) navigateur(s) du destinataire."""
    utilisateur_id = notif.destinataire_id
    nb = notif.destinataire.notifications.filter(lue=False).count()
    donnees = {
        'type':    'nouvelle',
        'id':      notif.pk,
        'titre':   notif.titre,
        'message': notif.message,
        'icone':   notif.icone,
        'couleur': notif.couleur,
        'lien':    notif.lien,
        'temps':   "À l'instant",
        'nb':      nb,
    }
    transaction.on_commit(lambda: _envoyer(
        utilisateur_id, {'type': 'notification.nouvelle', 'donnees': donnees}
    ))


def pousser_compteur(utilisateur):
    """Synchronise le badge de tous les onglets ouverts (lecture, suppression…)."""
    nb = utilisateur.notifications.filter(lue=False).count()
    transaction.on_commit(lambda: _envoyer(
        utilisateur.pk, {'type': 'notification.compteur', 'nb': nb}
    ))
