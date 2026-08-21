from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import Utilisateur
import uuid


class Ville(models.Model):

    nom       = models.CharField(max_length=100, unique=True)
    slug      = models.SlugField(unique=True, blank=True)
    region    = models.CharField(max_length=100, blank=True)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    actif     = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Ville'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class Quartier(models.Model):

    ville     = models.ForeignKey(Ville, on_delete=models.CASCADE, related_name='quartiers')
    nom       = models.CharField(max_length=100)
    slug      = models.SlugField(blank=True)
    latitude  = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    populaire = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Quartier'
        unique_together = [('ville', 'nom')]
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.ville})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)


class Logement(models.Model):

    TYPE_CHOICES = [
        ('STUDIO',      'Studio'),
        ('APPARTEMENT', 'Appartement'),
        ('VILLA',       'Villa'),
        ('MAISON',      'Maison'),
        ('CHAMBRE',     'Chambre'),
        ('DUPLEX',      'Duplex'),
        ('BUREAU',      'Bureau'),
        ('TERRAIN',     'Terrain'),
    ]
    OFFRE_CHOICES = [
        ('LOCATION',     'À louer'),
        ('VENTE',        'À vendre'),
        ('COLOCATION',   'Colocation'),
        ('COURTE_DUREE', 'Courte durée'),
    ]
    STANDING_CHOICES = [
        ('ECONOMIQUE', 'Économique'),
        ('STANDARD',   'Standard'),
        ('CONFORT',    'Confort'),
        ('LUXE',       'Luxe'),
    ]
    STATUT_CHOICES = [
        ('BROUILLON',  'Brouillon'),
        ('EN_ATTENTE', 'En attente'),
        ('PUBLIE',     'Publié'),
        ('SUSPENDU',   'Suspendu'),
        ('ARCHIVE',    'Archivé'),
        ('LOUE',       'Loué / Vendu'),
    ]
    MEUBLE_CHOICES = [
        ('NON_MEUBLE',  'Non meublé'),
        ('SEMI_MEUBLE', 'Semi-meublé'),
        ('MEUBLE',      'Meublé'),
    ]

    uuid          = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug          = models.SlugField(max_length=250, unique=True, blank=True)
    bailleur      = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='logements')

    # Informations
    titre         = models.CharField(max_length=200)
    description   = models.TextField()
    type_logement = models.CharField(max_length=20, choices=TYPE_CHOICES)
    type_offre    = models.CharField(max_length=20, choices=OFFRE_CHOICES, default='LOCATION')
    standing      = models.CharField(max_length=20, choices=STANDING_CHOICES, default='STANDARD')
    meuble        = models.CharField(max_length=20, choices=MEUBLE_CHOICES, default='NON_MEUBLE')

    # Localisation
    ville         = models.ForeignKey(Ville, on_delete=models.PROTECT, related_name='logements')
    quartier      = models.ForeignKey(Quartier, on_delete=models.PROTECT,
                                      related_name='logements', null=True, blank=True)
    adresse       = models.CharField(max_length=255)
    latitude      = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude     = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Caractéristiques
    surface        = models.PositiveIntegerField(null=True, blank=True)
    nb_chambres    = models.PositiveIntegerField(default=1)
    nb_salles_bain = models.PositiveIntegerField(default=1)
    nb_toilettes   = models.PositiveIntegerField(default=1)
    etage          = models.SmallIntegerField(default=0)

    # Prix
    prix            = models.PositiveBigIntegerField()
    prix_negociable = models.BooleanField(default=False)
    charges         = models.PositiveBigIntegerField(default=0)
    caution         = models.PositiveBigIntegerField(default=0)

    # Équipements
    eau_courante    = models.BooleanField(default=True)
    electricite     = models.BooleanField(default=True)
    internet        = models.BooleanField(default=False)
    climatisation   = models.BooleanField(default=False)
    parking         = models.BooleanField(default=False)
    gardien         = models.BooleanField(default=False)
    generateur      = models.BooleanField(default=False)
    piscine         = models.BooleanField(default=False)
    cuisine_equipee = models.BooleanField(default=False)
    balcon          = models.BooleanField(default=False)
    securite        = models.BooleanField(default=False)

    # Statut
    statut             = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    disponible         = models.BooleanField(default=True)
    date_disponibilite = models.DateField(null=True, blank=True)

    # Boost
    est_booste  = models.BooleanField(default=False)
    est_vedette = models.BooleanField(default=False)

    # Stats
    nb_vues     = models.PositiveIntegerField(default=0)
    nb_favoris  = models.PositiveIntegerField(default=0)
    nb_contacts = models.PositiveIntegerField(default=0)

    # Dates
    cree_le    = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Logement'
        ordering = ['-est_booste', '-est_vedette', '-cree_le']

    def __str__(self):
        return f"{self.titre} - {self.ville}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.titre}-{self.ville}")
            self.slug = f"{base}-{str(self.uuid)[:8]}"
        super().save(*args, **kwargs)

    def get_photo_principale(self):
        photo = self.photos.filter(principale=True).first()
        if not photo:
            photo = self.photos.first()
        return photo

    @property
    def note_moyenne(self):
        avis = self.avis.filter(approuve=True)
        if not avis.exists():
            return 0
        return round(sum(a.note for a in avis) / avis.count(), 1)

    @property
    def prix_formate(self):
        return f"{self.prix:,} FCFA".replace(',', ' ')

    def incrementer_vues(self):
        Logement.objects.filter(pk=self.pk).update(
            nb_vues=models.F('nb_vues') + 1
        )


class PhotoLogement(models.Model):

    logement   = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='photos')
    image      = models.ImageField(upload_to='logements/%Y/%m/')
    legende    = models.CharField(max_length=200, blank=True)
    principale = models.BooleanField(default=False)
    ordre      = models.PositiveSmallIntegerField(default=0)
    cree_le    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Photo'
        ordering = ['ordre', 'cree_le']

    def __str__(self):
        return f"Photo de {self.logement.titre}"


class Favori(models.Model):

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='favoris')
    logement    = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='favoris_set')
    cree_le     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Favori'
        unique_together = [('utilisateur', 'logement')]
        ordering = ['-cree_le']


class Avis(models.Model):

    logement    = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='avis')
    auteur      = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='avis_donnes')
    note        = models.PositiveSmallIntegerField(
                    validators=[MinValueValidator(1), MaxValueValidator(5)])
    commentaire = models.TextField()
    approuve    = models.BooleanField(default=False)
    cree_le     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Avis'
        unique_together = [('logement', 'auteur')]
        ordering = ['-cree_le']

    def __str__(self):
        return f"Avis de {self.auteur} — {self.note}/5"


class Reservation(models.Model):

    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRME',   'Confirmé'),
        ('REFUSE',     'Refusé'),
        ('ANNULE',     'Annulé'),
        ('TERMINE',    'Terminé'),
    ]
    TYPE_CHOICES = [
        ('VISITE',      'Demande de visite'),
        ('RESERVATION', 'Réservation'),
    ]

    uuid         = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    logement     = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='reservations')
    locataire    = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='reservations')
    type_demande = models.CharField(max_length=20, choices=TYPE_CHOICES, default='VISITE')
    statut       = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    date_debut   = models.DateField()
    date_fin     = models.DateField(null=True, blank=True)
    message      = models.TextField(blank=True)
    montant      = models.PositiveBigIntegerField(default=0)
    paye         = models.BooleanField(default=False)
    cree_le      = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Réservation'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.locataire} — {self.logement}"


class Signalement(models.Model):

    MOTIF_CHOICES = [
        ('FRAUDE',       'Fraude / Arnaque'),
        ('FAUX_PHOTOS',  'Photos fausses'),
        ('PRIX_ABUSIF',  'Prix abusif'),
        ('INEXISTANT',   'Logement inexistant'),
        ('INAPPROPRIE',  'Contenu inapproprié'),
        ('AUTRE',        'Autre'),
    ]

    logement    = models.ForeignKey(Logement, on_delete=models.CASCADE, related_name='signalements')
    auteur      = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    motif       = models.CharField(max_length=20, choices=MOTIF_CHOICES)
    description = models.TextField()
    traite      = models.BooleanField(default=False)
    cree_le     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Signalement'
        ordering = ['-cree_le']
        
class RechercheHistorique(models.Model):
    utilisateur   = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='historique_recherches'
    )
    requete       = models.CharField(max_length=500)
    ville         = models.CharField(max_length=100, blank=True)
    quartier      = models.CharField(max_length=100, blank=True)
    type_logement = models.CharField(max_length=20, blank=True)
    prix_min      = models.PositiveBigIntegerField(null=True, blank=True)
    prix_max      = models.PositiveBigIntegerField(null=True, blank=True)
    nb_resultats  = models.PositiveIntegerField(default=0)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    cree_le       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Recherche historique'
        ordering = ['-cree_le']

    def __str__(self):
        return f"{self.utilisateur} — {self.requete}"