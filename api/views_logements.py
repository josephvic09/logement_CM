from django.http import JsonResponse
from logements.models import Logement


def liste_logements(request):
    qs = Logement.objects.filter(
        statut='PUBLIE', disponible=True
    ).select_related('ville', 'quartier').prefetch_related('photos')[:20]

    data = []
    for l in qs:
        photo = l.get_photo_principale()
        data.append({
            'id':           l.pk,
            'titre':        l.titre,
            'prix':         l.prix,
            'prix_formate': l.prix_formate,
            'ville':        l.ville.nom,
            'quartier':     l.quartier.nom if l.quartier else '',
            'type':         l.get_type_logement_display(),
            'chambres':     l.nb_chambres,
            'surface':      l.surface,
            'photo':        request.build_absolute_uri(photo.image.url) if photo else None,
            'slug':         l.slug,
            'disponible':   l.disponible,
        })
    return JsonResponse({'logements': data})


def detail_logement(request, pk):
    try:
        l = Logement.objects.select_related(
            'ville', 'quartier', 'bailleur'
        ).prefetch_related('photos').get(pk=pk, statut='PUBLIE')
    except Logement.DoesNotExist:
        return JsonResponse({'detail': 'Logement introuvable'}, status=404)

    photos = [
        request.build_absolute_uri(p.image.url)
        for p in l.photos.all()
    ]
    return JsonResponse({
        'id':           l.pk,
        'titre':        l.titre,
        'description':  l.description,
        'prix':         l.prix,
        'prix_formate': l.prix_formate,
        'ville':        l.ville.nom,
        'quartier':     l.quartier.nom if l.quartier else '',
        'adresse':      l.adresse,
        'latitude':     float(l.latitude) if l.latitude else None,
        'longitude':    float(l.longitude) if l.longitude else None,
        'type':         l.get_type_logement_display(),
        'chambres':     l.nb_chambres,
        'surface':      l.surface,
        'meuble':       l.get_meuble_display(),
        'photos':       photos,
        'bailleur':     l.bailleur.get_full_name(),
        'telephone':    l.bailleur.telephone or '',
        'eau_courante':   l.eau_courante,
        'electricite':    l.electricite,
        'internet':       l.internet,
        'climatisation':  l.climatisation,
        'parking':        l.parking,
        'gardien':        l.gardien,
    })