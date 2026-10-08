"""Connexion et inscription via Google et Facebook (OAuth 2.0, code d'autorisation)."""
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db import transaction

from .models import CompteSocial, Utilisateur

DELAI = 15  # secondes
ROLES_AUTORISES = ('LOCATAIRE', 'BAILLEUR')


class OAuthErreur(Exception):
    """Erreur dont le message peut être affiché à l'utilisateur."""


def _profil_google(donnees):
    return {
        'uid': str(donnees['sub']),
        'email': donnees.get('email', '').lower(),
        'email_verifie': bool(donnees.get('email_verified')),
        'prenom': donnees.get('given_name', ''),
        'nom': donnees.get('family_name', ''),
    }


def _profil_facebook(donnees):
    # Facebook ne garantit pas que l'adresse e-mail a été vérifiée.
    return {
        'uid': str(donnees['id']),
        'email': donnees.get('email', '').lower(),
        'email_verifie': False,
        'prenom': donnees.get('first_name', ''),
        'nom': donnees.get('last_name', ''),
    }


def fournisseur(code):
    """Configuration du fournisseur, ou None s'il est inconnu."""
    version = settings.FACEBOOK_API_VERSION
    return {
        'google': {
            'code': 'google',
            'nom': 'Google',
            'url_autorisation': 'https://accounts.google.com/o/oauth2/v2/auth',
            'url_jeton': 'https://oauth2.googleapis.com/token',
            'methode_jeton': 'POST',
            'url_profil': 'https://openidconnect.googleapis.com/v1/userinfo',
            'params_profil': {},
            'jeton_en_entete': True,
            'scope': 'openid email profile',
            'params_autorisation': {'prompt': 'select_account'},
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'normaliser': _profil_google,
        },
        'facebook': {
            'code': 'facebook',
            'nom': 'Facebook',
            'url_autorisation': f'https://www.facebook.com/{version}/dialog/oauth',
            'url_jeton': f'https://graph.facebook.com/{version}/oauth/access_token',
            'methode_jeton': 'GET',
            'url_profil': f'https://graph.facebook.com/{version}/me',
            'params_profil': {'fields': 'id,first_name,last_name,email'},
            'jeton_en_entete': False,
            'scope': 'email,public_profile',
            'params_autorisation': {},
            'client_id': settings.FACEBOOK_APP_ID,
            'client_secret': settings.FACEBOOK_APP_SECRET,
            'normaliser': _profil_facebook,
        },
    }.get(code)


def est_configure(config):
    return bool(config['client_id'] and config['client_secret'])


def url_autorisation(config, url_retour, etat):
    params = {
        'client_id': config['client_id'],
        'redirect_uri': url_retour,
        'response_type': 'code',
        'scope': config['scope'],
        'state': etat,
        **config['params_autorisation'],
    }
    return f"{config['url_autorisation']}?{urlencode(params)}"


def echanger_code(config, url_retour, code):
    """Échange le code d'autorisation contre un jeton d'accès."""
    donnees = {
        'client_id': config['client_id'],
        'client_secret': config['client_secret'],
        'code': code,
        'redirect_uri': url_retour,
        'grant_type': 'authorization_code',
    }
    cle = 'params' if config['methode_jeton'] == 'GET' else 'data'
    try:
        rep = requests.request(
            config['methode_jeton'], config['url_jeton'], timeout=DELAI, **{cle: donnees}
        )
        rep.raise_for_status()
        return rep.json()['access_token']
    except (requests.RequestException, KeyError, ValueError) as exc:
        raise OAuthErreur(
            f"Impossible de valider la connexion avec {config['nom']}. Réessayez."
        ) from exc


def lire_profil(config, jeton):
    """Renvoie le profil normalisé : uid, email, email_verifie, prenom, nom."""
    entetes = {}
    params = dict(config['params_profil'])
    if config['jeton_en_entete']:
        entetes['Authorization'] = f'Bearer {jeton}'
    else:
        params['access_token'] = jeton
    try:
        rep = requests.get(
            config['url_profil'], headers=entetes, params=params, timeout=DELAI
        )
        rep.raise_for_status()
        return config['normaliser'](rep.json())
    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        raise OAuthErreur(
            f"Impossible de lire votre profil {config['nom']}. Réessayez."
        ) from exc


def _verifier_actif(utilisateur):
    if not utilisateur.is_active:
        raise OAuthErreur("Ce compte est désactivé. Contactez l'administration.")
    return utilisateur


@transaction.atomic
def identifier_ou_creer(config, profil, role):
    """Renvoie (utilisateur, cree) pour un profil social.

    Un compte existant n'est rattaché par e-mail que si le fournisseur certifie
    cette adresse ; sinon n'importe qui pourrait prendre un compte en s'inscrivant
    chez le fournisseur avec l'e-mail d'autrui.
    """
    lien = CompteSocial.objects.select_related('utilisateur').filter(
        fournisseur=config['code'], uid=profil['uid']
    ).first()
    if lien:
        return _verifier_actif(lien.utilisateur), False

    if not profil['email']:
        raise OAuthErreur(
            f"{config['nom']} ne nous a pas communiqué votre adresse e-mail : "
            "inscrivez-vous avec le formulaire."
        )

    utilisateur = Utilisateur.objects.filter(email__iexact=profil['email']).first()
    cree = utilisateur is None
    if cree:
        prenom = (profil['prenom'] or profil['email'].split('@')[0])[:100]
        utilisateur = Utilisateur.objects.create_user(
            email=profil['email'], password=None, prenom=prenom,
            nom=(profil['nom'] or prenom)[:100],
            role=role if role in ROLES_AUTORISES else 'LOCATAIRE',
            is_active=True, email_verified=True,
        )
    elif not profil['email_verifie']:
        raise OAuthErreur(
            "Un compte existe déjà avec cette adresse e-mail : "
            "connectez-vous avec votre mot de passe."
        )

    CompteSocial.objects.create(
        utilisateur=utilisateur, fournisseur=config['code'], uid=profil['uid']
    )
    return _verifier_actif(utilisateur), cree
