"""Peuple la base : villes, quartiers, comptes de démonstration, annonces et avis.

Idempotent : peut être relancé à chaque déploiement sans créer de doublons.
Mot de passe des comptes : variable d'environnement SEED_MOT_DE_PASSE.
"""
import random

from decouple import config
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Utilisateur
from logements.models import Avis, Logement, Quartier, Ville

VILLES = [
    {'nom': 'Yaoundé', 'region': 'Centre', 'latitude': 3.8480, 'longitude': 11.5021},
    {'nom': 'Douala', 'region': 'Littoral', 'latitude': 4.0511, 'longitude': 9.7679},
    {'nom': 'Bafoussam', 'region': 'Ouest', 'latitude': 5.4767, 'longitude': 10.4214},
    {'nom': 'Garoua', 'region': 'Nord', 'latitude': 9.3019, 'longitude': 13.3969},
    {'nom': 'Bamenda', 'region': 'Nord-Ouest', 'latitude': 5.9527, 'longitude': 10.1467},
    {'nom': 'Ngaoundéré', 'region': 'Adamaoua', 'latitude': 7.3268, 'longitude': 13.5836},
    {'nom': 'Bertoua', 'region': 'Est', 'latitude': 4.5786, 'longitude': 13.6853},
]

# ville -> (quartiers, quartiers populaires)
QUARTIERS = {
    'Yaoundé': (
        ['Bastos', 'Nlongkak', 'Mvog-Ada', 'Nsam', 'Biyem-Assi', 'Melen', 'Essos',
         'Omnisport', 'Etoug-Ebe', 'Mendong', 'Ngousso', 'Ekié', 'Mvog-Mbi',
         'Briqueterie', 'Tsinga', 'Santa Barbara', 'Nkol-Eton', 'Messa', 'Obili',
         'Elig-Essono'],
        {'Bastos', 'Nlongkak', 'Biyem-Assi'},
    ),
    'Douala': (
        ['Akwa', 'Bonanjo', 'Deido', 'New-Bell', 'Makepe', 'Logpom', 'Ndokoti',
         'Bépanda', 'Bonabéri', 'Bonapriso', 'Kotto', 'Cité des Palmiers', 'Bali',
         'Bonamoussadi'],
        {'Akwa', 'Bonanjo', 'Bonapriso'},
    ),
}

ANNONCES = [
    {
        'titre': 'Bel appartement F3 meublé à Bastos',
        'type_logement': 'APPARTEMENT', 'standing': 'CONFORT', 'meuble': 'MEUBLE',
        'prix': 120000, 'nb_chambres': 2, 'ville': 'Yaoundé', 'quartier': 'Bastos',
        'description': (
            'Superbe appartement moderne avec vue panoramique. Entièrement meublé, '
            'cuisine équipée, WiFi haut débit inclus.'),
        'latitude': 3.8826, 'longitude': 11.5196,
        'options': ('internet', 'climatisation', 'parking', 'securite', 'est_vedette'),
    },
    {
        'titre': 'Studio moderne à Nlongkak',
        'type_logement': 'STUDIO', 'standing': 'STANDARD', 'meuble': 'SEMI_MEUBLE',
        'prix': 55000, 'nb_chambres': 1, 'ville': 'Yaoundé', 'quartier': 'Nlongkak',
        'description': (
            'Studio cosy idéal pour étudiant ou jeune professionnel. '
            'Proche universités et commerces.'),
        'latitude': 3.8754, 'longitude': 11.5089,
        'options': ('internet',),
    },
    {
        'titre': 'Villa luxueuse avec piscine à Bastos',
        'type_logement': 'VILLA', 'standing': 'LUXE', 'meuble': 'MEUBLE',
        'prix': 450000, 'nb_chambres': 4, 'ville': 'Yaoundé', 'quartier': 'Bastos',
        'description': (
            'Magnifique villa 4 chambres avec piscine privée, jardin paysager '
            'et garage double.'),
        'latitude': 3.8860, 'longitude': 11.5220,
        'options': ('internet', 'climatisation', 'parking', 'gardien', 'piscine',
                    'securite', 'est_vedette', 'est_booste'),
    },
    {
        'titre': 'Appartement F2 à louer à Akwa Douala',
        'type_logement': 'APPARTEMENT', 'standing': 'CONFORT', 'meuble': 'SEMI_MEUBLE',
        'prix': 95000, 'nb_chambres': 2, 'ville': 'Douala', 'quartier': 'Akwa',
        'description': (
            "Bel appartement au coeur d'Akwa. Proche du port, commerces "
            'et administrations.'),
        'latitude': 4.0504, 'longitude': 9.7081,
        'options': ('internet', 'climatisation'),
    },
    {
        'titre': 'Maison familiale F4 à Biyem-Assi',
        'type_logement': 'MAISON', 'standing': 'STANDARD', 'meuble': 'NON_MEUBLE',
        'prix': 85000, 'nb_chambres': 3, 'ville': 'Yaoundé', 'quartier': 'Biyem-Assi',
        'description': (
            'Grande maison familiale dans quartier calme. 3 chambres, salon spacieux.'),
        'latitude': 3.8219, 'longitude': 11.4983,
        'options': ('parking',),
    },
    {
        'titre': 'Duplex moderne à Bonanjo Douala',
        'type_logement': 'DUPLEX', 'standing': 'LUXE', 'meuble': 'MEUBLE',
        'prix': 250000, 'nb_chambres': 3, 'ville': 'Douala', 'quartier': 'Bonanjo',
        'description': (
            'Superbe duplex au coeur du quartier des affaires. '
            'Vue sur le fleuve Wouri.'),
        'latitude': 4.0450, 'longitude': 9.6950,
        'options': ('internet', 'climatisation', 'parking', 'est_vedette'),
    },
    {
        'titre': 'Chambre meublée à Melen Yaoundé',
        'type_logement': 'CHAMBRE', 'standing': 'ECONOMIQUE', 'meuble': 'MEUBLE',
        'prix': 25000, 'nb_chambres': 1, 'ville': 'Yaoundé', 'quartier': 'Melen',
        'description': (
            'Chambre meublée propre et sécurisée. Idéale pour étudiant. '
            'Eau et électricité incluses.'),
        'latitude': 3.8650, 'longitude': 11.5150,
        'options': (),
    },
    {
        'titre': 'Appartement neuf 3 chambres à Makepe Douala',
        'type_logement': 'APPARTEMENT', 'standing': 'CONFORT', 'meuble': 'SEMI_MEUBLE',
        'prix': 130000, 'nb_chambres': 3, 'ville': 'Douala', 'quartier': 'Makepe',
        'description': (
            'Appartement neuf dans résidence sécurisée. Gardien 24h/24, parking, '
            'groupe électrogène.'),
        'latitude': 4.0720, 'longitude': 9.7500,
        'options': ('internet', 'gardien', 'parking', 'generateur'),
    },
]

# Avis approuvés posés sur les premières annonces (note, commentaire)
AVIS = [
    (5, 'Appartement conforme aux photos, bailleur très réactif. Je recommande.'),
    (4, 'Studio bien situé, proche des commerces. Quelques bruits en journée.'),
    (5, 'Villa magnifique, piscine bien entretenue. Visite parfaitement organisée.'),
]


class Command(BaseCommand):
    help = "Peuple la base avec des villes, des comptes de démonstration et des annonces."

    def handle(self, *args, **options):
        mot_de_passe = config('SEED_MOT_DE_PASSE', default='')
        if not mot_de_passe:
            raise CommandError(
                "12345678"
            )

        with transaction.atomic():
            villes, quartiers = self._creer_villes_et_quartiers()
            self._creer_compte(
                config('SEED_ADMIN_EMAIL', default='admin@logementcm.cm'), mot_de_passe,
                superuser=True, nom='Ngoua', prenom='Jean-Pierre', email_verified=True,
            )
            bailleur = self._creer_compte(
                'bailleur@test.cm', mot_de_passe, nom='Tchamda', prenom='Marie',
                role='BAILLEUR', is_active=True, is_verified=True, email_verified=True,
                ville='Yaoundé',
            )
            locataire = self._creer_compte(
                'locataire@test.cm', mot_de_passe, nom='Kamdem', prenom='Paul',
                role='LOCATAIRE', is_active=True, email_verified=True, ville='Yaoundé',
            )
            self._creer_annonces(bailleur, locataire, villes, quartiers)

        self.stdout.write(self.style.SUCCESS(
            f'Base peuplée : {Ville.objects.count()} villes, '
            f'{Quartier.objects.count()} quartiers, {Logement.objects.count()} logements, '
            f'{Utilisateur.objects.count()} utilisateurs.'
        ))

    def _creer_villes_et_quartiers(self):
        villes = {
            v['nom']: Ville.objects.get_or_create(nom=v['nom'], defaults=v)[0]
            for v in VILLES
        }
        quartiers = {}
        for nom_ville, (noms, populaires) in QUARTIERS.items():
            for nom in noms:
                quartiers[(nom_ville, nom)] = Quartier.objects.get_or_create(
                    ville=villes[nom_ville], nom=nom,
                    defaults={'populaire': nom in populaires},
                )[0]
        return villes, quartiers

    def _creer_compte(self, email, mot_de_passe, superuser=False, **champs):
        """Crée le compte de test s'il n'existe pas, sinon lui réapplique le mot de passe."""
        utilisateur = Utilisateur.objects.filter(email=email).first()
        if utilisateur is None:
            gestionnaire = Utilisateur.objects
            creer = gestionnaire.create_superuser if superuser else gestionnaire.create_user
            return creer(email=email, password=mot_de_passe, **champs)
        if not utilisateur.check_password(mot_de_passe):
            utilisateur.set_password(mot_de_passe)
            utilisateur.save(update_fields=['password'])
        return utilisateur

    def _creer_annonces(self, bailleur, locataire, villes, quartiers):
        """Crée les annonces et leurs avis uniquement si le site n'a encore aucune annonce."""
        if Logement.objects.exists():
            return
        logements = []
        for annonce in ANNONCES:
            champs = dict(annonce)
            nom_ville = champs.pop('ville')
            nom_quartier = champs.pop('quartier')
            options = dict.fromkeys(champs.pop('options'), True)
            logements.append(Logement.objects.create(
                bailleur=bailleur, ville=villes[nom_ville],
                quartier=quartiers[(nom_ville, nom_quartier)],
                adresse=f'{nom_quartier}, {nom_ville}', statut='PUBLIE', disponible=True,
                nb_vues=random.randint(50, 500), **champs, **options,
            ))
        for logement, (note, commentaire) in zip(logements, AVIS):
            Avis.objects.create(
                logement=logement, auteur=locataire, note=note,
                commentaire=commentaire, approuve=True,
            )
