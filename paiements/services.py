from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from . import campay
from .models import Abonnement, Paiement

DUREE_ABONNEMENT = timedelta(days=30)


def _methode_depuis_operateur(operateur, defaut):
    operateur = (operateur or '').upper()
    if 'MTN' in operateur:
        return 'MTN_MOMO'
    if 'ORANGE' in operateur:
        return 'ORANGE_MONEY'
    return defaut


def demarrer_paiement(paiement, telephone):
    """Envoie la demande de paiement sur le téléphone du client."""
    donnees = campay.collecter(paiement, telephone)
    paiement.campay_reference = donnees.get('reference', '')
    paiement.ussd_code = donnees.get('ussd_code', '')
    paiement.methode = _methode_depuis_operateur(donnees.get('operator'), paiement.methode)
    paiement.statut = 'TRAITEMENT'
    paiement.save(update_fields=['campay_reference', 'ussd_code', 'methode', 'statut'])


def synchroniser(paiement):
    """Aligne le paiement sur l'état réel chez Campay (peut lever CampayErreur)."""
    if paiement.est_reussi or not paiement.campay_reference:
        return paiement

    donnees = campay.verifier(paiement.campay_reference)
    statut = donnees.get('status')

    if statut == campay.STATUT_REUSSI:
        _finaliser_succes(paiement.pk, donnees)
    elif statut == campay.STATUT_ECHOUE and paiement.en_cours:
        paiement.statut = 'ECHOUE'
        paiement.message_operateur = 'Le paiement a été refusé ou a expiré.'
        paiement.traite_le = timezone.now()
        paiement.save(update_fields=['statut', 'message_operateur', 'traite_le'])
    paiement.refresh_from_db()
    return paiement


def _finaliser_succes(paiement_pk, donnees):
    """Enregistre un paiement encaissé et applique ses effets, une seule fois."""
    with transaction.atomic():
        paiement = Paiement.objects.select_for_update().select_related(
            'utilisateur', 'reservation__logement'
        ).get(pk=paiement_pk)
        if paiement.est_reussi:
            return

        paiement.statut = 'REUSSI'
        paiement.transaction_id = donnees.get('operator_reference') or paiement.campay_reference
        paiement.methode = _methode_depuis_operateur(donnees.get('operator'), paiement.methode)
        paiement.traite_le = timezone.now()
        paiement.message_operateur = f'Transaction effectuée. ID : {paiement.transaction_id}'
        paiement.save()

        if paiement.type_paiement == 'RESERVATION' and paiement.reservation:
            _appliquer_reservation(paiement.reservation)
        elif paiement.type_paiement == 'ABONNEMENT':
            _activer_abonnement(paiement)

        transaction.on_commit(lambda: _notifier(paiement))


def _appliquer_reservation(reservation):
    reservation.paye = True
    champs = ['paye']
    if reservation.statut == 'EN_ATTENTE':
        reservation.statut = 'CONFIRME'
        champs.append('statut')
        if reservation.type_demande == 'RESERVATION':
            logement = reservation.logement
            logement.statut = 'LOUE'
            logement.disponible = False
            logement.save(update_fields=['statut', 'disponible'])
    reservation.save(update_fields=champs)


def _activer_abonnement(paiement):
    utilisateur = paiement.utilisateur
    debut = timezone.now()
    Abonnement.objects.filter(utilisateur=utilisateur, statut='ACTIF').update(statut='ANNULE')
    abonnement = Abonnement.objects.create(
        utilisateur=utilisateur, plan=paiement.plan, statut='ACTIF',
        debut=debut, fin=debut + DUREE_ABONNEMENT, paiement=paiement,
    )
    utilisateur.is_premium = True
    utilisateur.premium_debut = abonnement.debut
    utilisateur.premium_fin = abonnement.fin
    utilisateur.save(update_fields=['is_premium', 'premium_debut', 'premium_fin'])


def _notifier(paiement):
    try:
        from notifs.utils import notif_paiement_reussi
        notif_paiement_reussi(paiement)
    except Exception:
        pass
