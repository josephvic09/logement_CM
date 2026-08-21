import os
import sys
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logement_cm.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from logements.models import Ville, Quartier, Logement
from accounts.models import Utilisateur

print("Création des données de test...")

# ─── Villes ──────────────────────────────────────────
villes_data = [
    {'nom':'Yaoundé',    'region':'Centre',     'latitude':3.8480, 'longitude':11.5021},
    {'nom':'Douala',     'region':'Littoral',   'latitude':4.0511, 'longitude':9.7679},
    {'nom':'Bafoussam',  'region':'Ouest',      'latitude':5.4767, 'longitude':10.4214},
    {'nom':'Garoua',     'region':'Nord',       'latitude':9.3019, 'longitude':13.3969},
    {'nom':'Bamenda',    'region':'Nord-Ouest', 'latitude':5.9527, 'longitude':10.1467},
    {'nom':'Ngaoundéré', 'region':'Adamaoua',   'latitude':7.3268, 'longitude':13.5836},
    {'nom':'Bertoua',    'region':'Est',        'latitude':4.5786, 'longitude':13.6853},
]
for v in villes_data:
    obj, c = Ville.objects.get_or_create(nom=v['nom'], defaults=v)
    if c:
        print(f"  Ville créée : {obj.nom}")

# ─── Quartiers Yaoundé ───────────────────────────────
yde = Ville.objects.get(nom='Yaoundé')
quartiers_yde = [
    'Bastos', 'Nlongkak', 'Mvog-Ada', 'Nsam', 'Biyem-Assi',
    'Melen', 'Essos', 'Omnisport', 'Etoug-Ebe', 'Mendong',
    'Ngousso', 'Ekié', 'Mvog-Mbi', 'Briqueterie', 'Tsinga',
    'Santa Barbara', 'Nkol-Eton', 'Messa', 'Obili', 'Elig-Essono',
]
for nom in quartiers_yde:
    Quartier.objects.get_or_create(
        ville=yde, nom=nom,
        defaults={'populaire': nom in ['Bastos', 'Nlongkak', 'Biyem-Assi']}
    )

# ─── Quartiers Douala ────────────────────────────────
dla = Ville.objects.get(nom='Douala')
quartiers_dla = [
    'Akwa', 'Bonanjo', 'Deido', 'New-Bell', 'Makepe',
    'Logpom', 'Ndokoti', 'Bépanda', 'Bonabéri', 'Bonapriso',
    'Kotto', 'Cité des Palmiers', 'Bali', 'Bonamoussadi',
]
for nom in quartiers_dla:
    Quartier.objects.get_or_create(
        ville=dla, nom=nom,
        defaults={'populaire': nom in ['Akwa', 'Bonanjo', 'Bonapriso']}
    )

print(f"Villes    : {Ville.objects.count()}")
print(f"Quartiers : {Quartier.objects.count()}")

# ─── Super Admin ─────────────────────────────────────
if not Utilisateur.objects.filter(email='admin@logementcm.cm').exists():
    Utilisateur.objects.create_superuser(
        email='admin@logementcm.cm',
        password='Admin2024!',
        nom='Ngoua',
        prenom='Jean-Pierre',
    )
    print("Admin créé : admin@logementcm.cm / Admin2024!")

# ─── Bailleur test ───────────────────────────────────
if not Utilisateur.objects.filter(email='bailleur@test.cm').exists():
    bailleur = Utilisateur.objects.create_user(
        email='bailleur@test.cm',
        password='Test2024!',
        nom='Tchamda',
        prenom='Marie',
        role='BAILLEUR',
        is_active=True,
        email_verified=True,
        ville='Yaoundé',
    )
    print("Bailleur créé : bailleur@test.cm / Test2024!")
else:
    bailleur = Utilisateur.objects.get(email='bailleur@test.cm')

# ─── Locataire test ──────────────────────────────────
if not Utilisateur.objects.filter(email='locataire@test.cm').exists():
    Utilisateur.objects.create_user(
        email='locataire@test.cm',
        password='Test2024!',
        nom='Kamdem',
        prenom='Paul',
        role='LOCATAIRE',
        is_active=True,
        email_verified=True,
        ville='Yaoundé',
    )
    print("Locataire créé : locataire@test.cm / Test2024!")

# ─── Logements de test ───────────────────────────────
if Logement.objects.count() < 3:

    annonces = [
        {
            'titre': 'Bel appartement F3 meublé à Bastos',
            'type_logement': 'APPARTEMENT',
            'type_offre': 'LOCATION',
            'standing': 'CONFORT',
            'meuble': 'MEUBLE',
            'prix': 120000,
            'nb_chambres': 2,
            'quartier': 'Bastos',
            'ville': yde,
            'description': 'Superbe appartement moderne avec vue panoramique. Entièrement meublé, cuisine équipée, WiFi haut débit inclus.',
            'internet': True,
            'climatisation': True,
            'parking': True,
            'securite': True,
            'latitude': 3.8826,
            'longitude': 11.5196,
            'statut': 'PUBLIE',
            'est_vedette': True,
        },
        {
            'titre': 'Studio moderne à Nlongkak',
            'type_logement': 'STUDIO',
            'type_offre': 'LOCATION',
            'standing': 'STANDARD',
            'meuble': 'SEMI_MEUBLE',
            'prix': 55000,
            'nb_chambres': 1,
            'quartier': 'Nlongkak',
            'ville': yde,
            'description': 'Studio cosy idéal pour étudiant ou jeune professionnel. Proche universités et commerces.',
            'internet': True,
            'latitude': 3.8754,
            'longitude': 11.5089,
            'statut': 'PUBLIE',
        },
        {
            'titre': 'Villa luxueuse avec piscine à Bastos',
            'type_logement': 'VILLA',
            'type_offre': 'LOCATION',
            'standing': 'LUXE',
            'meuble': 'MEUBLE',
            'prix': 450000,
            'nb_chambres': 4,
            'quartier': 'Bastos',
            'ville': yde,
            'description': 'Magnifique villa 4 chambres avec piscine privée, jardin paysager et garage double.',
            'internet': True,
            'climatisation': True,
            'parking': True,
            'gardien': True,
            'piscine': True,
            'securite': True,
            'latitude': 3.8860,
            'longitude': 11.5220,
            'statut': 'PUBLIE',
            'est_vedette': True,
            'est_booste': True,
        },
        {
            'titre': 'Appartement F2 à louer à Akwa Douala',
            'type_logement': 'APPARTEMENT',
            'type_offre': 'LOCATION',
            'standing': 'CONFORT',
            'meuble': 'SEMI_MEUBLE',
            'prix': 95000,
            'nb_chambres': 2,
            'quartier': 'Akwa',
            'ville': dla,
            'description': "Bel appartement au coeur d'Akwa. Proche du port, commerces et administrations.",
            'internet': True,
            'climatisation': True,
            'latitude': 4.0504,
            'longitude': 9.7081,
            'statut': 'PUBLIE',
        },
        {
            'titre': 'Maison familiale F4 à Biyem-Assi',
            'type_logement': 'MAISON',
            'type_offre': 'LOCATION',
            'standing': 'STANDARD',
            'meuble': 'NON_MEUBLE',
            'prix': 85000,
            'nb_chambres': 3,
            'quartier': 'Biyem-Assi',
            'ville': yde,
            'description': 'Grande maison familiale dans quartier calme. 3 chambres, salon spacieux.',
            'parking': True,
            'latitude': 3.8219,
            'longitude': 11.4983,
            'statut': 'PUBLIE',
        },
        {
            'titre': 'Duplex moderne à Bonanjo Douala',
            'type_logement': 'DUPLEX',
            'type_offre': 'LOCATION',
            'standing': 'LUXE',
            'meuble': 'MEUBLE',
            'prix': 250000,
            'nb_chambres': 3,
            'quartier': 'Bonanjo',
            'ville': dla,
            'description': 'Superbe duplex au coeur du quartier des affaires. Vue sur le fleuve Wouri.',
            'internet': True,
            'climatisation': True,
            'parking': True,
            'latitude': 4.0450,
            'longitude': 9.6950,
            'statut': 'PUBLIE',
            'est_vedette': True,
        },
        {
            'titre': 'Chambre meublée à Melen Yaoundé',
            'type_logement': 'CHAMBRE',
            'type_offre': 'LOCATION',
            'standing': 'ECONOMIQUE',
            'meuble': 'MEUBLE',
            'prix': 25000,
            'nb_chambres': 1,
            'quartier': 'Melen',
            'ville': yde,
            'description': 'Chambre meublée propre et sécurisée. Idéale pour étudiant. Eau et électricité incluses.',
            'internet': False,
            'latitude': 3.8650,
            'longitude': 11.5150,
            'statut': 'PUBLIE',
        },
        {
            'titre': 'Appartement neuf 3 chambres à Makepe Douala',
            'type_logement': 'APPARTEMENT',
            'type_offre': 'LOCATION',
            'standing': 'CONFORT',
            'meuble': 'SEMI_MEUBLE',
            'prix': 130000,
            'nb_chambres': 3,
            'quartier': 'Makepe',
            'ville': dla,
            'description': 'Appartement neuf dans résidence sécurisée. Gardien 24h/24, parking, groupe électrogène.',
            'internet': True,
            'gardien': True,
            'parking': True,
            'generateur': True,
            'latitude': 4.0720,
            'longitude': 9.7500,
            'statut': 'PUBLIE',
        },
    ]

    for data in annonces:
        quartier = Quartier.objects.filter(
            ville=data['ville'],
            nom=data.get('quartier', '')
        ).first()

        Logement.objects.create(
            bailleur=bailleur,
            titre=data['titre'],
            description=data['description'],
            type_logement=data['type_logement'],
            type_offre=data['type_offre'],
            standing=data['standing'],
            meuble=data['meuble'],
            prix=data['prix'],
            nb_chambres=data['nb_chambres'],
            ville=data['ville'],
            quartier=quartier,
            adresse=f"{data.get('quartier', '')}, {data['ville'].nom}",
            statut=data.get('statut', 'PUBLIE'),
            disponible=True,
            internet=data.get('internet', False),
            climatisation=data.get('climatisation', False),
            parking=data.get('parking', False),
            gardien=data.get('gardien', False),
            piscine=data.get('piscine', False),
            securite=data.get('securite', False),
            generateur=data.get('generateur', False),
            eau_courante=True,
            electricite=True,
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            est_vedette=data.get('est_vedette', False),
            est_booste=data.get('est_booste', False),
            nb_vues=random.randint(50, 500),
        )
        print(f"  Logement créé : {data['titre']}")

# ─── Résumé ──────────────────────────────────────────
print("\n" + "="*50)
print("DONNÉES CRÉÉES AVEC SUCCÈS !")
print("="*50)
print(f"  Villes    : {Ville.objects.count()}")
print(f"  Quartiers : {Quartier.objects.count()}")
print(f"  Logements : {Logement.objects.count()}")
print(f"  Utilisateurs : {Utilisateur.objects.count()}")
print("\nComptes de test :")
print("  admin@logementcm.cm    / Admin2024!")
print("  bailleur@test.cm       / Test2024!")
print("  locataire@test.cm      / Test2024!")
print("="*50)