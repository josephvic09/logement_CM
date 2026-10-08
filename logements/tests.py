from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import Utilisateur
from .models import Logement, Quartier, Ville
from .views import MAX_PHOTOS, TAILLE_MAX_PHOTO, _ajouter_photos, _retirer_photos

STOCKAGE_MEMOIRE = {
    'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


def photo(nom='photo.jpg', type_contenu='image/jpeg', taille=100):
    return SimpleUploadedFile(nom, b'x' * taille, content_type=type_contenu)


@override_settings(STORAGES=STOCKAGE_MEMOIRE)
class PhotosAnnonceTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.ville = Ville.objects.create(nom='Yaoundé')
        cls.quartier = Quartier.objects.create(ville=cls.ville, nom='Bastos')

    def _logement(self, email='bailleur@test.cm'):
        bailleur = Utilisateur.objects.create_user(
            email=email, password='x', nom='B', prenom='B', role='BAILLEUR', is_active=True
        )
        return Logement.objects.create(
            bailleur=bailleur, ville=self.ville, quartier=self.quartier, titre='Studio',
            description='Studio', type_logement='STUDIO', adresse='Bastos', prix=50000,
        )

    def setUp(self):
        self.logement = self._logement()

    def test_ajout_de_plusieurs_photos_la_premiere_est_principale(self):
        refusees = _ajouter_photos(self.logement, [photo('a.jpg'), photo('b.png', 'image/png')])
        self.assertEqual(refusees, 0)
        principales = [p.principale for p in self.logement.photos.order_by('ordre')]
        self.assertEqual(principales, [True, False])

    def test_format_ou_taille_non_acceptes(self):
        refusees = _ajouter_photos(self.logement, [
            photo('a.gif', 'image/gif'), photo('b.jpg', taille=TAILLE_MAX_PHOTO + 1),
        ])
        self.assertEqual((refusees, self.logement.photos.count()), (2, 0))

    def test_limite_de_photos(self):
        _ajouter_photos(self.logement, [photo(f'{i}.jpg') for i in range(MAX_PHOTOS)])
        self.assertEqual(_ajouter_photos(self.logement, [photo('trop.jpg')]), 1)
        self.assertEqual(self.logement.photos.count(), MAX_PHOTOS)

    def test_retirer_la_principale_en_designe_une_autre(self):
        _ajouter_photos(self.logement, [photo('a.jpg'), photo('b.jpg')])
        principale = self.logement.photos.get(principale=True)
        _retirer_photos(self.logement, [str(principale.pk)])
        restante = self.logement.photos.get()
        self.assertNotEqual(restante.pk, principale.pk)
        self.assertTrue(restante.principale)

    def test_impossible_de_retirer_la_photo_d_une_autre_annonce(self):
        autre = self._logement(email='autre@test.cm')
        _ajouter_photos(autre, [photo()])
        _retirer_photos(self.logement, [str(autre.photos.get().pk), 'pas-un-id'])
        self.assertEqual(autre.photos.count(), 1)
