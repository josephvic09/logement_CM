import secrets
import hashlib
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.forms import PasswordChangeForm

from .models import Utilisateur, LogActivite
from .forms import (
    InscriptionForm, ConnexionForm, ProfilForm,
    ResetPasswordDemandeForm, ResetPasswordConfirmForm
)



# ─── Utilitaires ─────────────────────────────────────────

def get_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def log_activite(user, action, request, description=''):
    LogActivite.objects.create(
        utilisateur=user,
        action=action,
        description=description,
        ip_address=get_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
    )


def get_redirect_url(user):
    if user.est_admin:
        return '/accounts/tableau-de-bord/admin/'
    elif user.role == 'BAILLEUR':
        return '/accounts/tableau-de-bord/bailleur/'
    return '/accounts/tableau-de-bord/locataire/'


# ─── Inscription ─────────────────────────────────────────

def inscription(request):
    if request.user.is_authenticated:
        return redirect('logements:accueil')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active     = True
            user.email_verified = True
            user.save()

            # Notification de bienvenue
            from notifs.utils import notif_bienvenue
            notif_bienvenue(user)

            login(request, user)
            log_activite(user, 'INSCRIPTION', request)
            messages.success(
                request,
                f"Bienvenue {user.prenom} ! Votre compte a été créé."
            )
            return redirect(get_redirect_url(user))
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = InscriptionForm()

    return render(request, 'accounts/inscription.html', {'form': form})


# ─── Vérification email ───────────────────────────────────

def verifier_email(request, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        user = Utilisateur.objects.get(
            email_verify_token=token_hash,
            is_active=False
        )
        user.is_active = True
        user.email_verified = True
        user.email_verify_token = ''
        user.save()
        messages.success(request, "✅ Email vérifié ! Vous pouvez vous connecter.")
        return redirect('accounts:connexion')
    except Utilisateur.DoesNotExist:
        messages.error(request, "Lien invalide ou expiré.")
        return redirect('accounts:inscription')


def verification_email_envoyee(request):
    return render(request, 'accounts/verification_email_envoyee.html')


# ─── Connexion ────────────────────────────────────────────

def connexion(request):
    if request.user.is_authenticated:
        return redirect(get_redirect_url(request.user))

    if request.method == 'POST':
        form = ConnexionForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            if not form.cleaned_data.get('se_souvenir'):
                request.session.set_expiry(0)
            login(request, user)
            Utilisateur.objects.filter(pk=user.pk).update(
                nb_connexions=user.nb_connexions + 1,
                derniere_connexion_ip=get_ip(request)
            )
            log_activite(user, 'CONNEXION', request)
            messages.success(request, f"Bienvenue {user.prenom} !")
            next_url = request.GET.get('next', get_redirect_url(user))
            return redirect(next_url)
        else:
            messages.error(request, "Email ou mot de passe incorrect.")
    else:
        form = ConnexionForm()

    return render(request, 'accounts/connexion.html', {'form': form})


# ─── Déconnexion ──────────────────────────────────────────

def deconnexion(request):
    if request.user.is_authenticated:
        log_activite(request.user, 'DECONNEXION', request)
        logout(request)
    messages.info(request, "Vous avez été déconnecté(e).")
    return redirect('accounts:connexion')


# ─── Reset mot de passe ───────────────────────────────────

def reset_password_demande(request):
    if request.method == 'POST':
        form = ResetPasswordDemandeForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user  = Utilisateur.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            user.reset_password_token   = hashlib.sha256(token.encode()).hexdigest()
            user.reset_password_expires = timezone.now() + timedelta(hours=2)
            user.save()

            lien = request.build_absolute_uri(
                f'/accounts/reset-password/{token}/'
            )
            send_mail(
                subject='🔑 Réinitialisation mot de passe — LogementCM',
                message=f'Bonjour {user.prenom},\n\nCliquez ici :\n{lien}\n\nLien valable 2h.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=True,
            )
            messages.success(request, "Lien de réinitialisation envoyé à votre email.")
            return redirect('accounts:connexion')
    else:
        form = ResetPasswordDemandeForm()

    return render(request, 'accounts/reset_password_demande.html', {'form': form})


def reset_password_confirmer(request, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    try:
        user = Utilisateur.objects.get(
            reset_password_token=token_hash,
            reset_password_expires__gt=timezone.now()
        )
    except Utilisateur.DoesNotExist:
        messages.error(request, "Lien invalide ou expiré.")
        return redirect('accounts:reset_password_demande')

    if request.method == 'POST':
        form = ResetPasswordConfirmForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['password1'])
            user.reset_password_token   = ''
            user.reset_password_expires = None
            user.save()
            messages.success(request, "Mot de passe réinitialisé ! Connectez-vous.")
            return redirect('accounts:connexion')
    else:
        form = ResetPasswordConfirmForm()

    return render(request, 'accounts/reset_password_confirmer.html', {'form': form})


# ─── Profil ───────────────────────────────────────────────

@login_required
def profil(request):
    if request.method == 'POST':
        form = ProfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_activite(request.user, 'MODIF_PROFIL', request)
            messages.success(request, "Profil mis à jour !")
            return redirect('accounts:profil')
    else:
        form = ProfilForm(instance=request.user)

    return render(request, 'accounts/profil.html', {'form': form})


@login_required
def changer_mot_de_passe(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_activite(user, 'MODIF_MDP', request)
            messages.success(request, "Mot de passe changé !")
            return redirect('accounts:profil')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/changer_mdp.html', {'form': form})


# ─── Tableaux de bord ─────────────────────────────────────

@login_required
def tableau_de_bord(request):
    if request.user.est_admin:
        return redirect('accounts:dashboard_admin')
    elif request.user.role == 'BAILLEUR':
        return redirect('accounts:dashboard_bailleur')
    return redirect('accounts:dashboard_locataire')


@login_required
def dashboard_locataire(request):
    from logements.models import Favori, Reservation, RechercheHistorique
    from chat.models import Conversation

    favoris = Favori.objects.filter(
        utilisateur=request.user
    ).select_related('logement__ville', 'logement__quartier').prefetch_related(
        'logement__photos'
    ).order_by('-cree_le')[:6]

    reservations = Reservation.objects.filter(
        locataire=request.user
    ).select_related('logement__ville').order_by('-cree_le')[:5]

    nb_messages = (
        Conversation.objects.filter(locataire=request.user) |
        Conversation.objects.filter(bailleur=request.user)
    ).count()

    context = {
        'favoris':      favoris,
        'reservations': reservations,
        'nb_favoris':   Favori.objects.filter(utilisateur=request.user).count(),
        'nb_reservations': Reservation.objects.filter(locataire=request.user).count(),
        'nb_messages':  nb_messages,
    }
    return render(request, 'accounts/dashboard_locataire.html', context)

@login_required
def dashboard_bailleur(request):
    if not request.user.est_bailleur:
        messages.error(request, "Accès refusé.")
        return redirect('accounts:dashboard_locataire')

    from logements.models import Logement, Reservation

    # ✅ Queryset de base sans slice
    logements_qs = Logement.objects.filter(
        bailleur=request.user
    ).select_related('ville', 'quartier').prefetch_related('photos')

    # ✅ Statistiques calculées AVANT le slice
    nb_total      = logements_qs.count()
    nb_publie     = logements_qs.filter(statut='PUBLIE').count()
    nb_en_attente = logements_qs.filter(statut='EN_ATTENTE').count()
    nb_loue       = logements_qs.filter(statut='LOUE').count()
    total_vues    = sum(l.nb_vues for l in logements_qs)
    total_favoris = sum(l.nb_favoris for l in logements_qs)

    # ✅ Réservations
    reservations = Reservation.objects.filter(
        logement__bailleur=request.user
    ).select_related('logement', 'locataire').order_by('-cree_le')

    reservations_attente = reservations.filter(statut='EN_ATTENTE').count()

    # ✅ Slice uniquement pour l'affichage, à la fin
    logements_affichage = logements_qs.order_by('-cree_le')[:8]

    context = {
        'logements':            logements_affichage,
        'reservations':         reservations[:10],
        'nb_total':             nb_total,
        'nb_publie':            nb_publie,
        'nb_en_attente':        nb_en_attente,
        'nb_loue':              nb_loue,
        'total_vues':           total_vues,
        'total_favoris':        total_favoris,
        'reservations_attente': reservations_attente,
    }
    return render(request, 'accounts/dashboard_bailleur.html', context)


@login_required
def dashboard_admin(request):
    if not request.user.est_admin:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('accounts:tableau_de_bord')

    from logements.models import Logement, Signalement, Reservation
    from chat.models import Conversation

    # Statistiques globales
    nb_utilisateurs  = Utilisateur.objects.filter(is_active=True).count()
    nb_bailleurs     = Utilisateur.objects.filter(role='BAILLEUR').count()
    nb_locataires    = Utilisateur.objects.filter(role='LOCATAIRE').count()
    nb_logements     = Logement.objects.filter(statut='PUBLIE').count()
    nb_en_attente    = Logement.objects.filter(statut='EN_ATTENTE').count()
    nb_signalements  = Signalement.objects.filter(traite=False).count()
    nb_reservations  = Reservation.objects.filter(statut='EN_ATTENTE').count()
    nb_conversations = Conversation.objects.count()

    # Derniers inscrits
    derniers_users = Utilisateur.objects.order_by('-date_inscription')[:8]

    # Dernières annonces
    derniers_logements = Logement.objects.select_related(
        'ville', 'quartier', 'bailleur'
    ).prefetch_related('photos').order_by('-cree_le')[:8]

    # Annonces en attente de validation
    annonces_attente = Logement.objects.filter(
        statut='EN_ATTENTE'
    ).select_related('ville', 'bailleur').prefetch_related('photos').order_by('-cree_le')[:5]

    # Signalements non traités
    signalements = Signalement.objects.filter(
        traite=False
    ).select_related('logement', 'auteur').order_by('-cree_le')[:5]

    context = {
        'nb_utilisateurs':  nb_utilisateurs,
        'nb_bailleurs':     nb_bailleurs,
        'nb_locataires':    nb_locataires,
        'nb_logements':     nb_logements,
        'nb_en_attente':    nb_en_attente,
        'nb_signalements':  nb_signalements,
        'nb_reservations':  nb_reservations,
        'nb_conversations': nb_conversations,
        'derniers_users':   derniers_users,
        'derniers_logements': derniers_logements,
        'annonces_attente': annonces_attente,
        'signalements':     signalements,
    }
    return render(request, 'accounts/dashboard_admin.html', context)
@login_required
def mes_favoris(request):
    from logements.models import Favori
    favoris = Favori.objects.filter(
        utilisateur=request.user
    ).select_related(
        'logement__ville', 'logement__quartier'
    ).prefetch_related('logement__photos').order_by('-cree_le')

    return render(request, 'accounts/mes_favoris.html', {
        'favoris': favoris,
        'nb_favoris': favoris.count(),
    })


@login_required
def mes_reservations(request):
    from logements.models import Reservation
    reservations = Reservation.objects.filter(
        locataire=request.user
    ).select_related('logement__ville', 'logement__quartier').order_by('-cree_le')

    return render(request, 'accounts/mes_reservations.html', {
        'reservations': reservations,
    })


@login_required
def comparer_logements(request):
    from logements.models import Logement
    ids = request.GET.getlist('ids')
    logements = []
    if ids:
        logements = Logement.objects.filter(
            pk__in=ids[:4], statut='PUBLIE'
        ).select_related('ville', 'quartier').prefetch_related('photos')

    return render(request, 'accounts/comparer.html', {
        'logements': logements,
    })
    

@login_required
def gerer_reservations(request):
    """Gestion des réservations par le bailleur."""
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')

    from logements.models import Reservation
    statut = request.GET.get('statut', '')

    reservations = Reservation.objects.filter(
        logement__bailleur=request.user
    ).select_related('logement', 'locataire').order_by('-cree_le')

    if statut:
        reservations = reservations.filter(statut=statut)

    return render(request, 'accounts/gerer_reservations.html', {
        'reservations': reservations,
        'statut_actuel': statut,
    })


@login_required
def repondre_reservation(request, reservation_id):
    """Confirmer ou refuser une réservation."""
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')

    from logements.models import Reservation
    from notifs.utils import notif_reservation_confirmee, notif_reservation_refusee

    res    = get_object_or_404(
        Reservation, pk=reservation_id,
        logement__bailleur=request.user
    )
    action = request.POST.get('action')

    if action == 'confirmer':
        res.statut = 'CONFIRME'
        res.save()
        notif_reservation_confirmee(res)
        messages.success(
            request,
            f"✅ Réservation de {res.locataire.get_full_name()} confirmée."
        )
    elif action == 'refuser':
        res.statut = 'REFUSE'
        res.save()
        notif_reservation_refusee(res)
        messages.warning(
            request,
            f"Réservation de {res.locataire.get_full_name()} refusée."
        )

    return redirect('accounts:gerer_reservations')


@login_required
def mes_annonces(request):
    """Liste complète des annonces du bailleur."""
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')

    from logements.models import Logement
    statut = request.GET.get('statut', '')

    logements = Logement.objects.filter(
        bailleur=request.user
    ).select_related('ville', 'quartier').prefetch_related('photos')

    if statut:
        logements = logements.filter(statut=statut)

    logements = logements.order_by('-cree_le')

    return render(request, 'accounts/mes_annonces.html', {
        'logements':     logements,
        'statut_actuel': statut,
        'nb_total':      logements.count(),
    })
    
    
@login_required
def admin_utilisateurs(request):
    """Gestion des utilisateurs."""
    if not request.user.est_admin:
        return redirect('accounts:tableau_de_bord')

    role   = request.GET.get('role', '')
    search = request.GET.get('q', '')

    users = Utilisateur.objects.order_by('-date_inscription')

    if role:
        users = users.filter(role=role)
    if search:
        from django.db.models import Q
        users = users.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(email__icontains=search)
        )

    from django.core.paginator import Paginator
    paginator = Paginator(users, 15)
    page      = request.GET.get('page', 1)
    users     = paginator.get_page(page)

    return render(request, 'accounts/admin_utilisateurs.html', {
        'users':      users,
        'role_actuel': role,
        'search':     search,
    })


@login_required
def admin_toggle_user(request, user_id):
    """Activer / désactiver un utilisateur."""
    if not request.user.est_admin:
        from django.http import JsonResponse
        return JsonResponse({'error': 'Accès refusé'}, status=403)

    user = get_object_or_404(Utilisateur, pk=user_id)
    if user == request.user:
        messages.error(request, "Vous ne pouvez pas modifier votre propre compte.")
        return redirect('accounts:admin_utilisateurs')

    user.is_active = not user.is_active
    user.save()

    if user.is_active:
        messages.success(request, f"Compte de {user.get_full_name()} activé.")
    else:
        messages.warning(request, f"Compte de {user.get_full_name()} désactivé.")

    return redirect('accounts:admin_utilisateurs')


@login_required
def admin_logements(request):
    """Gestion des logements."""
    if not request.user.est_admin:
        return redirect('accounts:tableau_de_bord')

    from logements.models import Logement
    statut = request.GET.get('statut', '')
    search = request.GET.get('q', '')

    logements = Logement.objects.select_related(
        'ville', 'quartier', 'bailleur'
    ).prefetch_related('photos').order_by('-cree_le')

    if statut:
        logements = logements.filter(statut=statut)
    if search:
        from django.db.models import Q
        logements = logements.filter(
            Q(titre__icontains=search) |
            Q(bailleur__email__icontains=search) |
            Q(ville__nom__icontains=search)
        )

    from django.core.paginator import Paginator
    paginator = Paginator(logements, 15)
    page      = request.GET.get('page', 1)
    logements = paginator.get_page(page)

    return render(request, 'accounts/admin_logements.html', {
        'logements':     logements,
        'statut_actuel': statut,
        'search':        search,
    })


@login_required
def admin_signalements(request):
    """Gestion des signalements."""
    if not request.user.est_admin:
        return redirect('accounts:tableau_de_bord')

    from logements.models import Signalement
    signalements = Signalement.objects.filter(
        traite=False
    ).select_related('logement', 'auteur').order_by('-cree_le')

    return render(request, 'accounts/admin_signalements.html', {
        'signalements': signalements,
    })


@login_required
def admin_traiter_signalement(request, signal_id):
    """Traiter un signalement."""
    if not request.user.est_admin:
        return redirect('accounts:tableau_de_bord')

    from logements.models import Signalement
    signal = get_object_or_404(Signalement, pk=signal_id)
    action = request.POST.get('action')

    if action == 'traiter':
        signal.traite = True
        signal.save()
        messages.success(request, "Signalement marqué comme traité.")
    elif action == 'suspendre':
        signal.logement.statut = 'SUSPENDU'
        signal.logement.save()
        signal.traite = True
        signal.save()
        messages.warning(request, f"Logement suspendu et signalement traité.")

    return redirect('accounts:admin_signalements')