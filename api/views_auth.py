from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Utilisateur


@csrf_exempt
def inscription(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Méthode non autorisée'}, status=405)
    try:
        data      = json.loads(request.body)
        email     = data.get('email', '').strip().lower()
        password  = data.get('password', '')
        prenom    = data.get('prenom', '').strip()
        nom       = data.get('nom', '').strip()
        role      = data.get('role', 'LOCATAIRE')
        telephone = data.get('telephone', '')

        if not email or not password or not prenom or not nom:
            return JsonResponse({'detail': 'Tous les champs obligatoires doivent être remplis.'}, status=400)

        if Utilisateur.objects.filter(email=email).exists():
            return JsonResponse({'detail': 'Un compte avec cet email existe déjà.'}, status=400)

        user = Utilisateur.objects.create_user(
            username=email, email=email, password=password,
            prenom=prenom, nom=nom, role=role, telephone=telephone
        )
        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id':     user.id,
                'prenom': user.prenom,
                'nom':    user.nom,
                'email':  user.email,
                'role':   user.role,
            }
        }, status=201)
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=500)


@csrf_exempt
def connexion(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Méthode non autorisée'}, status=405)
    try:
        data     = json.loads(request.body)
        email    = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = authenticate(request, username=email, password=password)
        if user is None:
            return JsonResponse({'detail': 'Email ou mot de passe incorrect.'}, status=401)

        refresh = RefreshToken.for_user(user)
        return JsonResponse({
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id':     user.id,
                'prenom': user.prenom,
                'nom':    user.nom,
                'email':  user.email,
                'role':   user.role,
            }
        })
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=500)


def profil(request):
    from rest_framework_simplejwt.authentication import JWTAuthentication
    try:
        auth = JWTAuthentication()
        user, _ = auth.authenticate(request)
        return JsonResponse({
            'id':        user.id,
            'prenom':    user.prenom,
            'nom':       user.nom,
            'email':     user.email,
            'role':      user.role,
            'telephone': user.telephone or '',
        })
    except Exception:
        return JsonResponse({'detail': 'Non authentifié'}, status=401)