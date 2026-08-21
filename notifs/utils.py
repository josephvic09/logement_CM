"""
Utilitaires pour créer des notifications automatiques.
Appelé depuis toutes les apps du projet.
"""
from .models import Notification


def notifier(destinataire, type_notif, titre, message, lien=''):
    """Créer une notification."""
    try:
        Notification.objects.create(
            destinataire=destinataire,
            type_notif=type_notif,
            titre=titre,
            message=message,
            lien=lien,
        )
    except Exception:
        pass


# ─── Notifications Logements ─────────────────────────

def notif_annonce_validee(logement):
    """Notifier le bailleur que son annonce a été validée."""
    notifier(
        destinataire=logement.bailleur,
        type_notif='VALIDATION',
        titre='Annonce publiée !',
        message=(
            f'Votre annonce "{logement.titre}" a été validée '
            f'et est maintenant visible par tous les visiteurs.'
        ),
        lien=f'/logements/{logement.slug}/',
    )


def notif_annonce_rejetee(logement, motif=''):
    """Notifier le bailleur que son annonce a été rejetée."""
    notifier(
        destinataire=logement.bailleur,
        type_notif='REJET',
        titre='Annonce non publiée',
        message=(
            f'Votre annonce "{logement.titre}" n\'a pas été validée. '
            f'{motif}'
        ),
        lien='/accounts/mes-annonces/',
    )


def notif_nouveau_favori(logement, utilisateur):
    """Notifier le bailleur qu'un utilisateur a mis en favori."""
    notifier(
        destinataire=logement.bailleur,
        type_notif='FAVORI',
        titre='Nouveau favori',
        message=(
            f'{utilisateur.get_full_name()} a ajouté votre annonce '
            f'"{logement.titre}" à ses favoris.'
        ),
        lien=f'/logements/{logement.slug}/',
    )


# ─── Notifications Réservations ──────────────────────

def notif_nouvelle_reservation(reservation):
    """Notifier le bailleur d'une nouvelle demande."""
    notifier(
        destinataire=reservation.logement.bailleur,
        type_notif='RESERVATION',
        titre='Nouvelle demande de visite',
        message=(
            f'{reservation.locataire.get_full_name()} souhaite '
            f'visiter votre logement "{reservation.logement.titre}" '
            f'le {reservation.date_debut.strftime("%d/%m/%Y")}.'
        ),
        lien='/accounts/gerer-reservations/',
    )


def notif_reservation_confirmee(reservation):
    """Notifier le locataire que sa réservation est confirmée."""
    notifier(
        destinataire=reservation.locataire,
        type_notif='RESERVATION',
        titre='Visite confirmée !',
        message=(
            f'Votre demande de visite pour "{reservation.logement.titre}" '
            f'a été confirmée par le bailleur.'
        ),
        lien='/accounts/mes-reservations/',
    )


def notif_reservation_refusee(reservation):
    """Notifier le locataire que sa réservation est refusée."""
    notifier(
        destinataire=reservation.locataire,
        type_notif='REJET',
        titre='Demande refusée',
        message=(
            f'Votre demande pour "{reservation.logement.titre}" '
            f'n\'a pas pu être acceptée par le bailleur.'
        ),
        lien='/accounts/mes-reservations/',
    )


# ─── Notifications Messages ───────────────────────────

def notif_nouveau_message(message):
    """Notifier le destinataire d'un nouveau message."""
    conv = message.conversation
    if message.expediteur == conv.locataire:
        destinataire = conv.bailleur
    else:
        destinataire = conv.locataire

    notifier(
        destinataire=destinataire,
        type_notif='MESSAGE',
        titre=f'Message de {message.expediteur.get_full_name()}',
        message=(
            f'{message.contenu[:100]}...'
            if len(message.contenu) > 100
            else message.contenu
        ),
        lien=f'/chat/{conv.uuid}/',
    )


# ─── Notifications Paiements ─────────────────────────

def notif_paiement_reussi(paiement):
    """Notifier l'utilisateur que son paiement est réussi."""
    notifier(
        destinataire=paiement.utilisateur,
        type_notif='PAIEMENT',
        titre='Paiement confirmé',
        message=(
            f'Votre paiement de {paiement.montant_formate} '
            f'a été effectué avec succès. '
            f'Référence : {paiement.reference}'
        ),
        lien='/paiements/historique/',
    )


# ─── Notifications Avis ───────────────────────────────

def notif_nouvel_avis(avis):
    """Notifier le bailleur d'un nouvel avis."""
    notifier(
        destinataire=avis.logement.bailleur,
        type_notif='AVIS',
        titre='Nouvel avis sur votre logement',
        message=(
            f'{avis.auteur.get_full_name()} a laissé un avis '
            f'{avis.note}/5 sur "{avis.logement.titre}".'
        ),
        lien=f'/logements/{avis.logement.slug}/',
    )


# ─── Notification de bienvenue ────────────────────────

def notif_bienvenue(utilisateur):
    """Envoyer une notification de bienvenue."""
    notifier(
        destinataire=utilisateur,
        type_notif='SYSTEME',
        titre=f'Bienvenue sur LogementCM, {utilisateur.prenom} !',
        message=(
            'Votre compte est créé avec succès. '
            'Explorez des milliers de logements au Cameroun '
            'ou publiez vos annonces dès maintenant.'
        ),
        lien='/',
    )