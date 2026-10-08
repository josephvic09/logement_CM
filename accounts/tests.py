from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

from django.test import TestCase, override_settings
from django.urls import reverse

from .models import CompteSocial, Utilisateur

PROFIL = {
    'uid': '123', 'email': 'awa@example.com', 'email_verifie': True,
    'prenom': 'Awa', 'nom': 'Mbarga',
}


@override_settings(
    GOOGLE_CLIENT_ID='id-google', GOOGLE_CLIENT_SECRET='secret-google',
    FACEBOOK_APP_ID='id-facebook', FACEBOOK_APP_SECRET='secret-facebook',
)
class ConnexionSocialeTests(TestCase):

    def _retour(self, fournisseur, profil, role='', etat='attendu', code='abc'):
        session = self.client.session
        session['oauth_etat'] = 'attendu'
        session['oauth_role'] = role
        session.save()
        parametres = {'state': etat, **({'code': code} if code else {})}
        with patch('accounts.views.oauth.echanger_code', return_value='jeton'), \
                patch('accounts.views.oauth.lire_profil', return_value=profil):
            return self.client.get(
                reverse('accounts:oauth_retour', args=[fournisseur]), parametres
            )

    def _connecte(self):
        return '_auth_user_id' in self.client.session

    def test_demarrer_redirige_vers_google_avec_etat(self):
        reponse = self.client.get(reverse('accounts:oauth_demarrer', args=['google']))
        url = urlparse(reponse['Location'])
        self.assertEqual(url.netloc, 'accounts.google.com')
        etat = parse_qs(url.query)['state'][0]
        self.assertEqual(etat, self.client.session['oauth_etat'])

    @override_settings(GOOGLE_CLIENT_ID='')
    def test_demarrer_sans_configuration_renvoie_a_la_connexion(self):
        reponse = self.client.get(reverse('accounts:oauth_demarrer', args=['google']))
        self.assertRedirects(reponse, reverse('accounts:connexion'), fetch_redirect_response=False)

    def test_fournisseur_inconnu(self):
        self.assertEqual(self.client.get('/accounts/oauth/twitter/').status_code, 404)

    def test_etat_invalide_refuse(self):
        reponse = self._retour('google', PROFIL, etat='autre')
        self.assertRedirects(reponse, reverse('accounts:connexion'), fetch_redirect_response=False)
        self.assertFalse(self._connecte())
        self.assertFalse(Utilisateur.objects.exists())

    def test_acces_refuse_chez_le_fournisseur(self):
        reponse = self._retour('google', PROFIL, code='')
        self.assertRedirects(reponse, reverse('accounts:connexion'), fetch_redirect_response=False)
        self.assertFalse(self._connecte())

    def test_creation_compte_bailleur(self):
        reponse = self._retour('google', PROFIL, role='BAILLEUR')
        utilisateur = Utilisateur.objects.get(email='awa@example.com')
        self.assertEqual((utilisateur.role, utilisateur.is_active), ('BAILLEUR', True))
        self.assertFalse(utilisateur.has_usable_password())
        self.assertTrue(CompteSocial.objects.filter(utilisateur=utilisateur, uid='123').exists())
        self.assertTrue(self._connecte())
        self.assertRedirects(
            reponse, '/accounts/tableau-de-bord/bailleur/', fetch_redirect_response=False
        )

    def test_role_non_autorise_devient_locataire(self):
        self._retour('google', PROFIL, role='SUPER_ADMIN')
        self.assertEqual(Utilisateur.objects.get(email='awa@example.com').role, 'LOCATAIRE')

    def test_reconnexion_ne_cree_pas_de_doublon(self):
        self._retour('google', PROFIL)
        self.client.logout()
        self._retour('google', PROFIL)
        self.assertEqual(Utilisateur.objects.count(), 1)
        self.assertEqual(CompteSocial.objects.count(), 1)

    def test_google_rattache_un_compte_existant(self):
        existant = Utilisateur.objects.create_user(
            email='awa@example.com', password='x', nom='M', prenom='A', is_active=True
        )
        self._retour('google', PROFIL)
        self.assertEqual(Utilisateur.objects.count(), 1)
        self.assertEqual(CompteSocial.objects.get().utilisateur, existant)
        self.assertTrue(self._connecte())

    def test_facebook_ne_rattache_pas_un_compte_existant(self):
        Utilisateur.objects.create_user(
            email='awa@example.com', password='x', nom='M', prenom='A', is_active=True
        )
        self._retour('facebook', {**PROFIL, 'email_verifie': False})
        self.assertFalse(CompteSocial.objects.exists())
        self.assertFalse(self._connecte())

    def test_compte_desactive_refuse(self):
        inactif = Utilisateur.objects.create_user(
            email='awa@example.com', password='x', nom='M', prenom='A', is_active=False
        )
        CompteSocial.objects.create(utilisateur=inactif, fournisseur='google', uid='123')
        self._retour('google', PROFIL)
        self.assertFalse(self._connecte())
