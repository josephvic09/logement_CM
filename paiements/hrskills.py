"""Client minimal de l'API HR-Skills Pay (Mobile Money MTN / Orange, Cameroun)."""
import hashlib
import hmac
import re

import requests
from django.conf import settings
from django.core.cache import cache

DELAI = 20  # secondes
DUREE_JETON = 40 * 60  # le jeton de transaction expire après 45 min
CLE_CACHE_JETON = 'hrskills_jeton_transaction'

STATUT_REUSSI = 'SUCCESS'
STATUT_ECHOUE = 'FAILED'

OPERATEURS = {'MTN_MOMO': 'mtn', 'ORANGE_MONEY': 'orange'}


class HRSkillsErreur(Exception):
    """Erreur renvoyée par HR-Skills Pay ou service injoignable."""


def normaliser_telephone(saisie):
    """Renvoie 237XXXXXXXXX pour un numéro camerounais valide, sinon None."""
    chiffres = re.sub(r'\D', '', saisie or '')
    if len(chiffres) == 9:
        chiffres = '237' + chiffres
    return chiffres if re.fullmatch(r'2376\d{8}', chiffres) else None


def signature_valide(corps, signature):
    """Vérifie la signature HMAC-SHA256 (en-tête X-Hub-Signature) d'un webhook."""
    secret = settings.HRSKILLS_WEBHOOK_SECRET
    if not secret:
        return False
    attendue = 'sha256=' + hmac.new(secret.encode(), corps, hashlib.sha256).hexdigest()
    return hmac.compare_digest((signature or '').encode(), attendue.encode())


def _jeton_transaction():
    jeton = cache.get(CLE_CACHE_JETON)
    if jeton:
        return jeton
    if not (settings.HRSKILLS_CLE_PUBLIQUE and settings.HRSKILLS_CLE_SECRETE):
        raise HRSkillsErreur("Paiement indisponible : HR-Skills Pay n'est pas configuré.")
    try:
        rep = requests.post(
            f'{settings.HRSKILLS_BASE_URL}/v1/auth/transaction-token',
            headers={'Authorization': f'Bearer {settings.HRSKILLS_CLE_PUBLIQUE}'},
            json={'api_secret': settings.HRSKILLS_CLE_SECRETE},
            timeout=DELAI,
        )
        rep.raise_for_status()
        jeton = rep.json()['transaction_token']
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise HRSkillsErreur("Impossible de s'authentifier auprès de HR-Skills Pay.") from exc
    cache.set(CLE_CACHE_JETON, jeton, DUREE_JETON)
    return jeton


def _appeler(methode, chemin, cle_idempotence=None, **kwargs):
    entetes = {
        'Authorization': f'Bearer {settings.HRSKILLS_CLE_PUBLIQUE}',
        'X-Transaction-Token': _jeton_transaction(),
    }
    if cle_idempotence:
        entetes['Idempotency-Key'] = cle_idempotence
    try:
        rep = requests.request(
            methode, f'{settings.HRSKILLS_BASE_URL}{chemin}',
            headers=entetes, timeout=DELAI, **kwargs
        )
        donnees = rep.json()
    except (requests.RequestException, ValueError) as exc:
        raise HRSkillsErreur("Le service de paiement ne répond pas. Réessayez.") from exc
    if not rep.ok:
        detail = donnees.get('message') or 'Demande refusée.'
        raise HRSkillsErreur(f"HR-Skills Pay : {detail}")
    return donnees.get('data') or {}


def collecter(paiement, telephone):
    """Envoie la demande de paiement sur le téléphone du client.

    Renvoie les données de la transaction, dont 'reference' (à stocker pour le suivi).
    """
    donnees = _appeler(
        'POST', '/api/v1/payin/mobile-money', cle_idempotence=str(paiement.uuid),
        json={
            'operator': OPERATEURS[paiement.methode],
            'country': 'CM',
            'phone_number': telephone,
            'amount': paiement.montant,
            'currency': 'XAF',
            'description': f'LogementCM {paiement.get_type_paiement_display()}'[:100],
            'metadata': {'reference': paiement.reference},
        },
    )
    if not donnees.get('reference'):
        raise HRSkillsErreur("Réponse inattendue de HR-Skills Pay. Réessayez.")
    return donnees


def verifier(reference_externe):
    """Interroge HR-Skills Pay sur l'état réel d'une transaction."""
    return _appeler('GET', f'/v1/payments/{reference_externe}')
