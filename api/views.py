from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from logements.models import Logement, Quartier, Ville
from django.db.models import Count, Q


class LogementsAPIView(APIView):

    def get(self, request):
        qs    = Logement.objects.filter(statut='PUBLIE', disponible=True)
        ville = request.GET.get('ville')
        q     = request.GET.get('q')

        if ville:
            qs = qs.filter(ville__nom__icontains=ville)
        if q:
            qs = qs.filter(
                Q(titre__icontains=q) |
                Q(description__icontains=q)
            )

        data = list(qs.values(
            'id', 'titre', 'prix', 'nb_chambres',
            'type_logement', 'ville__nom',
            'quartier__nom', 'latitude', 'longitude'
        )[:50])

        return Response({
            'results': data,
            'count':   qs.count()
        })


@api_view(['GET'])
def quartiers_api(request):
    ville_id = request.GET.get('ville_id')
    qs = Quartier.objects.all()
    if ville_id:
        qs = qs.filter(ville_id=ville_id)
    data = list(qs.values('id', 'nom', 'ville__nom'))
    return Response(data)


@api_view(['GET'])
def villes_api(request):
    q  = request.GET.get('q', '')
    qs = Ville.objects.filter(actif=True)
    if q:
        qs = qs.filter(nom__icontains=q)
    data = list(qs.values('id', 'nom', 'slug'))
    return Response(data)


@api_view(['GET'])
def stats_api(request):
    return Response({
        'nb_logements': Logement.objects.filter(statut='PUBLIE').count(),
        'nb_villes':    Ville.objects.filter(actif=True).count(),
        'nb_quartiers': Quartier.objects.count(),
    })