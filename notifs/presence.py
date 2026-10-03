"""Présence en ligne : qui est connecté en ce moment (WebSocket ouvert).

Les locataires (et admins) voient les bailleurs en ligne ; les bailleurs voient les locataires.
Le comptage est tenu en mémoire du processus : il convient à une seule instance du serveur.
"""
from django.db.models import OuterRef, Subquery
from django.urls import reverse

from accounts.models import Utilisateur
from chat.models import Conversation
from logements.models import Logement

ROLES_SUIVIS = ('BAILLEUR', 'LOCATAIRE')

_connexions = {}  # id utilisateur -> nombre d'onglets connectés


def role_observe(role_observateur):
    """Le bailleur observe les locataires ; tous les autres observent les bailleurs."""
    return 'LOCATAIRE' if role_observateur == 'BAILLEUR' else 'BAILLEUR'


def groupe(role_cible):
    """Groupe de canaux qui reçoit les arrivées et départs des utilisateurs de ce rôle."""
    return f'presence_{role_cible.lower()}s'


def connecter(utilisateur_id):
    """Renvoie True si l'utilisateur vient de passer en ligne (premier onglet)."""
    nb = _connexions.get(utilisateur_id, 0)
    _connexions[utilisateur_id] = nb + 1
    return nb == 0


def deconnecter(utilisateur_id):
    """Renvoie True si l'utilisateur vient de passer hors ligne (dernier onglet fermé)."""
    nb = _connexions.get(utilisateur_id, 0) - 1
    if nb > 0:
        _connexions[utilisateur_id] = nb
        return False
    return _connexions.pop(utilisateur_id, None) is not None


def _fiche(utilisateur):
    lien = ''
    if utilisateur.role == 'BAILLEUR' and utilisateur.logement_pk:
        lien = reverse('chat:demarrer', args=[utilisateur.logement_pk])
    elif utilisateur.role == 'LOCATAIRE' and utilisateur.conversation_uuid:
        lien = reverse('chat:detail', args=[utilisateur.conversation_uuid])
    return {
        'id':     utilisateur.pk,
        'nom':    utilisateur.get_full_name(),
        'avatar': utilisateur.get_avatar_url(),
        'lien':   lien,
    }


def fiches(role_cible, observateur, ids=None):
    """Fiches des utilisateurs en ligne de ce rôle, avec le lien adapté à l'observateur.

    Bailleur observé : lien pour lui écrire à propos de sa dernière annonce publiée.
    Locataire observé : lien vers la conversation existante avec le bailleur observateur.
    """
    ids = list(_connexions) if ids is None else [i for i in ids if i in _connexions]
    derniere_annonce = Logement.objects.filter(
        bailleur=OuterRef('pk'), statut='PUBLIE', disponible=True
    ).order_by('-cree_le').values('pk')[:1]
    derniere_conversation = Conversation.objects.filter(
        locataire=OuterRef('pk'), bailleur=observateur
    ).order_by('-modifie_le').values('uuid')[:1]

    utilisateurs = Utilisateur.objects.filter(
        pk__in=ids, role=role_cible, is_active=True
    ).annotate(
        logement_pk=Subquery(derniere_annonce),
        conversation_uuid=Subquery(derniere_conversation),
    ).order_by('prenom', 'nom')
    return [_fiche(u) for u in utilisateurs]
