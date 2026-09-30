"""Client minimal de l'API Campay (Mobile Money MTN / Orange, Cameroun)."""
import re

import requests
from django.conf import settings

DELAI = 20  # secondes

STATUT_REUSSI = 'SUCCESSFUL'
STATUT_ECHOUE = 'FAILED'


class CampayErreur(Exception):
    """Erreur renvoyée par Campay ou réseau injoignable."""


def normaliser_telephone(saisie):
    """Renvoie 237XXXXXXXXX pour un numéro camerounais valide, sinon None."""
    chiffres = re.sub(r'\D', '', saisie or '')
    if len(chiffres) == 9:
        chiffres = '237' + chiffres
    return chiffres if re.fullmatch(r'2376\d{8}', chiffres) else None


def _entetes():
    if settings.CAMPAY_TOKEN:
        return {'Authorization': f'Token {settings.CAMPAY_TOKEN}'}
    if not (settings.CAMPAY_USERNAME and settings.CAMPAY_PASSWORD):
        raise CampayErreur("Paiement indisponible : Campay n'est pas configuré.")
    try:
        rep = requests.post(
            f'{settings.CAMPAY_BASE_URL}/token/',
            json={'username': settings.CAMPAY_USERNAME, 'password': settings.CAMPAY_PASSWORD},
            timeout=DELAI,
        )
        rep.raise_for_status()
        return {'Authorization': f'Token {rep.json()["token"]}'}
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise CampayErreur("Impossible de s'authentifier auprès de Campay.") from exc


def _appeler(methode, chemin, **kwargs):
    try:
        rep = requests.request(
            methode, f'{settings.CAMPAY_BASE_URL}{chemin}',
            headers=_entetes(), timeout=DELAI, **kwargs
        )
        donnees = rep.json()
    except (requests.RequestException, ValueError) as exc:
        raise CampayErreur("Le service de paiement ne répond pas. Réessayez.") from exc
    if not rep.ok:
        detail = donnees.get('message') or donnees.get('detail') or 'Demande refusée.'
        raise CampayErreur(f"Campay : {detail}")
    return donnees


def collecter(paiement, telephone):
    """Envoie la demande de paiement sur le téléphone du client.

    Renvoie {'reference': ..., 'ussd_code': ..., 'operator': ...}.
    """
    return _appeler('POST', '/collect/', json={
        'amount': str(paiement.montant),
        'currency': 'XAF',
        'from': telephone,
        'description': f'LogementCM {paiement.get_type_paiement_display()}'[:100],
        'external_reference': paiement.reference,
    })


def verifier(reference_campay):
    """Interroge Campay sur l'état réel d'une transaction."""
    return _appeler('GET', f'/transaction/{reference_campay}/')
