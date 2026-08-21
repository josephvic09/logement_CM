from django import template
from logements.models import Logement, Favori

register = template.Library()


@register.simple_tag
def recommandations_locataire(user):
    """Recommande des logements selon les favoris et l'historique."""
    if not user.is_authenticated:
        return Logement.objects.filter(
            statut='PUBLIE', disponible=True
        ).prefetch_related('photos').select_related('ville', 'quartier')[:4]

    # Villes et types préférés basés sur les favoris
    favoris = Favori.objects.filter(
        utilisateur=user
    ).select_related('logement__ville')[:10]

    if favoris.exists():
        villes = list(set([f.logement.ville_id for f in favoris]))
        types  = list(set([f.logement.type_logement for f in favoris]))

        logements = Logement.objects.filter(
            statut='PUBLIE',
            disponible=True,
            ville_id__in=villes,
        ).exclude(
            favoris_set__utilisateur=user
        ).prefetch_related('photos').select_related('ville', 'quartier')[:4]

        if logements.exists():
            return logements

    # Fallback : logements récents
    return Logement.objects.filter(
        statut='PUBLIE', disponible=True
    ).prefetch_related('photos').select_related(
        'ville', 'quartier'
    ).order_by('-cree_le')[:4]