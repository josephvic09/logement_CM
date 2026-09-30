import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import Http404

from django.db.models import Avg

from django.contrib import messages

from .models import (
    Logement, Ville, Quartier, Favori,
    Reservation, Avis, Signalement, PhotoLogement
)
from .forms import (
    LogementForm, RechercheForm, AvisForm, ReservationForm, VisiteForm
)
from accounts.models import Utilisateur
FRAIS_RESERVATION = 1000  # FCFA — frais fixes pour confirmer une réservation



# ─── Accueil ─────────────────────────────────────────

def accueil(request):
    logements_vedette = Logement.objects.filter(
        statut='PUBLIE', disponible=True, est_vedette=True
    ).select_related(
        'ville', 'quartier'
    ).prefetch_related('photos').order_by('-est_booste', '-cree_le')[:6]

    logements_recents = Logement.objects.filter(
        statut='PUBLIE', disponible=True
    ).select_related(
        'ville', 'quartier'
    ).prefetch_related('photos').order_by('-cree_le')[:12]

    villes_populaires = Ville.objects.filter(actif=True).annotate(
        nb=Count(
            'logements',
            filter=Q(logements__statut='PUBLIE')
        )
    ).filter(nb__gt=0).order_by('-nb')[:8]

    nb_logements = Logement.objects.filter(statut='PUBLIE').count()
    nb_villes    = Ville.objects.filter(actif=True).count()
    nb_bailleurs = Utilisateur.objects.filter(role='BAILLEUR').count()

    avantages = [
        {
            'emoji':       '🔍',
            'titre':       'Recherche Intelligente',
            'description': 'Moteur IA qui comprend vos besoins en français naturel. Trouvez en secondes.',
        },
        {
            'emoji':       '📍',
            'titre':       'Carte Interactive',
            'description': 'Visualisez tous les logements sur une carte Leaflet en temps réel.',
        },
        {
            'emoji':       '🛡️',
            'titre':       'Annonces Vérifiées',
            'description': 'Chaque bailleur est contrôlé par notre équipe. Zéro arnaque garantie.',
        },
        {
            'emoji':       '💬',
            'titre':       'Chat Instantané',
            'description': 'Contactez le bailleur directement depuis la plateforme.',
        },
        {
            'emoji':       '📱',
            'titre':       '100% Mobile',
            'description': 'Interface optimisée pour smartphone, tablette et desktop.',
        },
        {
            'emoji':       '💳',
            'titre':       'Mobile Money',
            'description': 'MTN MoMo et Orange Money intégrés pour payer en toute sécurité.',
        },
    ]

    context = {
        'logements_vedette': logements_vedette,
        'logements_recents': logements_recents,
        'villes_populaires': villes_populaires,
        'form_recherche':    RechercheForm(),
        'avantages':         avantages,
        'stats': {
            'nb_logements': nb_logements,
            'nb_villes':    nb_villes,
            'nb_bailleurs': nb_bailleurs,
        }
    }
    return render(request, 'logements/accueil.html', context)


# ─── Recherche ────────────────────────────────────────

def recherche(request):
    form = RechercheForm(request.GET)
    qs   = Logement.objects.filter(
        statut='PUBLIE', disponible=True
    ).select_related('ville', 'quartier').prefetch_related('photos')

    if form.is_valid():
        q             = form.cleaned_data.get('q')
        ville         = form.cleaned_data.get('ville')
        quartier      = form.cleaned_data.get('quartier')
        type_logement = form.cleaned_data.get('type_logement')
        type_offre    = form.cleaned_data.get('type_offre')
        prix_min      = form.cleaned_data.get('prix_min')
        prix_max      = form.cleaned_data.get('prix_max')
        nb_chambres   = form.cleaned_data.get('nb_chambres')
        standing      = form.cleaned_data.get('standing')
        wifi          = form.cleaned_data.get('wifi')
        parking       = form.cleaned_data.get('parking')
        climatisation = form.cleaned_data.get('climatisation')
        gardien       = form.cleaned_data.get('gardien')
        piscine       = form.cleaned_data.get('piscine')

        if q:
            qs = qs.filter(
                Q(titre__icontains=q) |
                Q(description__icontains=q) |
                Q(adresse__icontains=q) |
                Q(ville__nom__icontains=q) |
                Q(quartier__nom__icontains=q)
            )
        if ville:
            qs = qs.filter(ville__nom__icontains=ville)
        if quartier:
            qs = qs.filter(quartier__nom__icontains=quartier)
        if type_logement:
            qs = qs.filter(type_logement=type_logement)
        if type_offre:
            qs = qs.filter(type_offre=type_offre)
        if prix_min:
            qs = qs.filter(prix__gte=prix_min)
        if prix_max:
            qs = qs.filter(prix__lte=prix_max)
        if nb_chambres:
            qs = qs.filter(nb_chambres__gte=nb_chambres)
        if standing:
            qs = qs.filter(standing=standing)
        if wifi:
            qs = qs.filter(internet=True)
        if parking:
            qs = qs.filter(parking=True)
        if climatisation:
            qs = qs.filter(climatisation=True)
        if gardien:
            qs = qs.filter(gardien=True)
        if piscine:
            qs = qs.filter(piscine=True)

    # Tri
    tri = request.GET.get('tri', 'recent')
    if tri == 'prix_asc':
        qs = qs.order_by('prix')
    elif tri == 'prix_desc':
        qs = qs.order_by('-prix')
    elif tri == 'vues':
        qs = qs.order_by('-nb_vues')
    else:
        qs = qs.order_by('-est_booste', '-cree_le')

    nb_resultats = qs.count()
    paginator    = Paginator(qs, 12)
    page         = request.GET.get('page', 1)
    logements    = paginator.get_page(page)

    return render(request, 'logements/recherche.html', {
        'form':         form,
        'logements':    logements,
        'nb_resultats': nb_resultats,
        'villes':       Ville.objects.filter(actif=True),
        'tri':          tri,
    })


# ─── Détail logement ─────────────────────────────────





def detail_logement(request, slug):
    logement = get_object_or_404(Logement, slug=slug)

    est_proprietaire = (
        request.user.is_authenticated and request.user == logement.bailleur
    )
    est_admin = (
        request.user.is_authenticated
        and request.user.role in ['ADMIN', 'SUPER_ADMIN']
    )

    if logement.statut != 'PUBLIE' and not (est_proprietaire or est_admin):
        raise Http404("Aucun logement ne correspond à la requête.")

    # ─── Soumission d'un avis ────────────────────────────────────
    if request.method == 'POST' and request.POST.get('avis'):
        if not request.user.is_authenticated:
            messages.error(request, "Connectez-vous pour laisser un avis.")
            return redirect(f"{reverse('accounts:connexion')}?next={request.path}")

        form_avis = AvisForm(request.POST)
        if form_avis.is_valid():
            avis          = form_avis.save(commit=False)
            avis.logement = logement
            avis.auteur   = request.user
            avis.save()
            messages.success(
                request,
                "Merci ! Votre avis a été enregistré et sera visible après validation."
            )
            return redirect('logements:detail', slug=logement.slug)
        else:
            messages.error(request, "Veuillez corriger les erreurs de votre avis.")
    else:
        form_avis = AvisForm()

    # ─── Incrémenter les vues ────────────────────────────────────
    if not est_proprietaire:
        Logement.objects.filter(pk=logement.pk).update(
            nb_vues=logement.nb_vues + 1
        )

    # ─── Vérifier visite + droit de réserver ────────────────────
    reservation_active = (
        request.user.is_authenticated and not est_proprietaire and not est_admin
        and _reservation_active(request.user, logement)
    )
    peut_reserver = not reservation_active

    # ─── Données de la page ──────────────────────────────────────
    photos    = logement.photos.order_by('ordre', '-principale')
    avis_list = logement.avis.filter(approuve=True).select_related('auteur')
    note_moy  = avis_list.aggregate(Avg('note'))['note__avg']
    if note_moy is not None:
        note_moy = round(note_moy, 1)

    similaires = Logement.objects.filter(
        statut='PUBLIE',
        disponible=True,
        ville=logement.ville,
        type_logement=logement.type_logement,
    ).exclude(pk=logement.pk).prefetch_related('photos')[:4]

    est_favori = False
    if request.user.is_authenticated:
        est_favori = Favori.objects.filter(
            utilisateur=request.user, logement=logement
        ).exists()

    return render(request, 'logements/detail.html', {
        'logement':          logement,
        'photos':            photos,
        'avis_list':         avis_list,
        'note_moy':          note_moy,
        'avis_form':         form_avis,
        'form_visite':       VisiteForm(auto_id='visite_%s'),
        'form_reservation':  ReservationForm(auto_id='resa_%s'),
        'similaires':        similaires,
        'est_favori':        est_favori,
        'reservation_active': reservation_active,
        'peut_reserver':     peut_reserver,
    })
# ─── Créer logement ───────────────────────────────────

@login_required
def creer_logement(request):
    if not request.user.est_bailleur:
        messages.error(request, "Seuls les bailleurs peuvent publier des annonces.")
        return redirect('logements:accueil')

    if request.method == 'POST':
        form   = LogementForm(request.POST)
        photos = request.FILES.getlist('photos')

        if form.is_valid():
            logement          = form.save(commit=False)
            logement.bailleur = request.user
            logement.statut   = 'PUBLIE'          # ← publication directe, plus de validation admin
            logement.save()

            # Sauvegarder les photos
            for i, photo in enumerate(photos[:10]):
                if photo.size > 5 * 1024 * 1024:
                    continue
                if photo.content_type not in [
                    'image/jpeg', 'image/png', 'image/webp'
                ]:
                    continue
                PhotoLogement.objects.create(
                    logement=logement,
                    image=photo,
                    principale=(i == 0),
                    ordre=i,
                )

            messages.success(
                request,
                "✅ Annonce publiée avec succès ! Elle est désormais visible par tous."
            )
            return redirect('accounts:dashboard_bailleur')
        else:
            messages.error(
                request,
                "Veuillez corriger les erreurs dans le formulaire."
            )
    else:
        form = LogementForm()

    villes = Ville.objects.filter(actif=True).order_by('nom')
    return render(request, 'logements/creer.html', {
        'form':   form,
        'villes': villes,
    })
# ─── Modifier logement ────────────────────────────────

@login_required
def modifier_logement(request, slug):
    logement = get_object_or_404(
        Logement, slug=slug, bailleur=request.user
    )

    if request.method == 'POST':
        form   = LogementForm(request.POST, instance=logement)
        photos = request.FILES.getlist('photos')

        if form.is_valid():
            logement = form.save()

            # Ajouter nouvelles photos
            nb_photos = logement.photos.count()
            for i, photo in enumerate(photos[:10 - nb_photos]):
                if photo.size > 5 * 1024 * 1024:
                    continue
                PhotoLogement.objects.create(
                    logement=logement,
                    image=photo,
                    principale=False,
                    ordre=nb_photos + i,
                )

            messages.success(request, "✅ Annonce mise à jour avec succès.")
            return redirect('logements:detail', slug=logement.slug)
        else:
            messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = LogementForm(instance=logement)

    return render(request, 'logements/modifier.html', {
        'form':     form,
        'logement': logement,
    })


# ─── Supprimer logement ───────────────────────────────

@login_required
@require_POST
def supprimer_logement(request, slug):
    logement = get_object_or_404(
        Logement, slug=slug, bailleur=request.user
    )
    logement.statut = 'ARCHIVE'
    logement.save()
    messages.success(request, f'Annonce "{logement.titre}" archivée.')
    return redirect('accounts:mes_annonces')


# ─── Toggle Favori ────────────────────────────────────

@login_required
@require_POST
def toggle_favori(request, logement_id):
    logement = get_object_or_404(Logement, pk=logement_id)
    fav, cree = Favori.objects.get_or_create(
        utilisateur=request.user,
        logement=logement
    )
    if not cree:
        fav.delete()
        return JsonResponse({'status': 'removed'})

    try:
        from notifs.utils import notif_nouveau_favori
        notif_nouveau_favori(logement, request.user)
    except Exception:
        pass

    return JsonResponse({'status': 'added'})


# ─── Faire une réservation ────────────────────────────



def _reservation_active(utilisateur, logement):
    """Ce locataire a-t-il déjà une réservation en cours sur ce logement ?"""
    return Reservation.objects.filter(
        locataire=utilisateur, logement=logement,
        type_demande='RESERVATION', statut__in=['EN_ATTENTE', 'CONFIRME'],
    ).exists()


def _enregistrer_demande(request, logement, form_class, type_demande, montant):
    """Valide et enregistre une demande ; renvoie la réservation ou None."""
    form = form_class(request.POST)
    if not form.is_valid():
        erreurs = " ".join(e for liste in form.errors.values() for e in liste)
        messages.error(request, f"Demande non enregistrée. {erreurs}")
        return None

    res              = form.save(commit=False)
    res.locataire    = request.user
    res.logement     = logement
    res.type_demande = type_demande
    res.montant      = montant
    if type_demande == 'VISITE' and not res.lieu_rencontre:
        res.lieu_rencontre = f"{logement.adresse}, {logement.ville.nom}"
    res.save()

    try:
        from notifs.utils import notif_nouvelle_reservation
        notif_nouvelle_reservation(res)
    except Exception:
        pass
    return res


@login_required
@require_POST
def demander_visite(request, logement_id):
    logement = get_object_or_404(Logement, pk=logement_id, statut='PUBLIE')

    if request.user == logement.bailleur:
        messages.error(request, "Vous ne pouvez pas visiter votre propre logement.")
        return redirect('logements:detail', slug=logement.slug)

    res = _enregistrer_demande(request, logement, VisiteForm, 'VISITE', 0)
    if res is None:
        return redirect('logements:detail', slug=logement.slug)

    messages.success(
        request,
        "✅ Demande de visite envoyée ! Le bailleur vous répondra sous 24h."
    )
    return redirect('accounts:mes_reservations')


@login_required
@require_POST
def faire_reservation(request, logement_id):
    logement = get_object_or_404(Logement, pk=logement_id, statut='PUBLIE')

    if request.user == logement.bailleur:
        messages.error(request, "Vous ne pouvez pas réserver votre propre logement.")
        return redirect('logements:detail', slug=logement.slug)

    if _reservation_active(request.user, logement):
        messages.error(request, "Vous avez déjà une réservation en cours pour ce logement.")
        return redirect('logements:detail', slug=logement.slug)

    res = _enregistrer_demande(
        request, logement, ReservationForm, 'RESERVATION', FRAIS_RESERVATION
    )
    if res is None:
        return redirect('logements:detail', slug=logement.slug)

    messages.success(
        request,
        f"Demande de réservation envoyée. Réglez les {FRAIS_RESERVATION} FCFA "
        f"de frais de réservation pour la confirmer."
    )
    return redirect('paiements:payer', reservation_id=res.pk)
# ─── Signaler un logement ─────────────────────────────

@login_required
def signaler_logement(request, logement_id):
    logement = get_object_or_404(Logement, pk=logement_id)

    if request.method == 'POST':
        motif       = request.POST.get('motif', 'AUTRE')
        description = request.POST.get('description', '')

        Signalement.objects.create(
            logement=logement,
            auteur=request.user,
            motif=motif,
            description=description,
        )
        messages.success(
            request,
            "Signalement envoyé. Notre équipe va examiner cette annonce."
        )
        return redirect('logements:detail', slug=logement.slug)

    return render(request, 'logements/signaler.html', {
        'logement': logement
    })


# ─── Admin — Valider logement ─────────────────────────

@login_required
def admin_valider_logement(request, logement_id):
    if not request.user.est_admin:
        messages.error(request, "Accès refusé.")
        return redirect('logements:accueil')

    logement = get_object_or_404(Logement, pk=logement_id)
    action   = request.POST.get('action')

    if action == 'valider':
        logement.statut = 'PUBLIE'
        logement.save()
        try:
            from notifs.utils import notif_annonce_validee
            notif_annonce_validee(logement)
        except Exception:
            pass
        messages.success(
            request,
            f'✅ Annonce "{logement.titre}" publiée.'
        )
    elif action == 'rejeter':
        logement.statut = 'SUSPENDU'
        logement.save()
        try:
            from notifs.utils import notif_annonce_rejetee
            motif = request.POST.get('motif', '')
            notif_annonce_rejetee(logement, motif)
        except Exception:
            pass
        messages.warning(
            request,
            f'Annonce "{logement.titre}" rejetée.'
        )

    return redirect('accounts:admin_logements')


# ─── Carte Leaflet ────────────────────────────────────

def carte(request):
    villes    = Ville.objects.filter(actif=True)
    quartiers = Quartier.objects.select_related('ville').all()

    qs = Logement.objects.filter(
        statut='PUBLIE',
        disponible=True,
        latitude__isnull=False,
        longitude__isnull=False,
    ).select_related('ville', 'quartier').prefetch_related('photos')

    # Filtres
    ville_id   = request.GET.get('ville')
    type_offre = request.GET.get('type_offre', '')
    prix_max   = request.GET.get('prix_max', '')
    type_log   = request.GET.get('type_logement', '')

    if ville_id:
        qs = qs.filter(ville_id=ville_id)
    if type_offre:
        qs = qs.filter(type_offre=type_offre)
    if prix_max:
        qs = qs.filter(prix__lte=prix_max)
    if type_log:
        qs = qs.filter(type_logement=type_log)

    logements_data = []
    for l in qs[:300]:
        photo = l.get_photo_principale()
        logements_data.append({
            'id':           l.pk,
            'titre':        l.titre,
            'prix':         l.prix,
            'prix_formate': l.prix_formate,
            'ville':        l.ville.nom,
            'quartier':     l.quartier.nom if l.quartier else '',
            'type':         l.get_type_logement_display(),
            'offre':        l.get_type_offre_display(),
            'chambres':     l.nb_chambres,
            'surface':      l.surface or '',
            'lat':          float(l.latitude),
            'lng':          float(l.longitude),
            'photo':        photo.image.url if photo else '/static/images/no-image.jpg',
            'url':          f'/logements/{l.slug}/',
            'booste':       l.est_booste,
            'vedette':      l.est_vedette,
            'wifi':         l.internet,
            'parking':      l.parking,
            'piscine':      l.piscine,
            'gardien':      l.gardien,
        })

    context = {
        'logements_json': json.dumps(logements_data),
        'nb_logements':   len(logements_data),
        'villes':         villes,
        'quartiers':      quartiers,
        'type_choices':   Logement.TYPE_CHOICES,
        'offre_choices':  Logement.OFFRE_CHOICES,
    }
    return render(request, 'logements/carte.html', context)


# ─── API Logements Carte ──────────────────────────────

def api_logements_carte(request):
    qs = Logement.objects.filter(
        statut='PUBLIE',
        disponible=True,
        latitude__isnull=False,
        longitude__isnull=False,
    ).select_related('ville', 'quartier')[:300]

    data = []
    for l in qs:
        photo = l.get_photo_principale()
        data.append({
            'id':       l.pk,
            'titre':    l.titre,
            'prix':     l.prix,
            'lat':      float(l.latitude),
            'lng':      float(l.longitude),
            'photo':    photo.image.url if photo else '',
            'url':      f'/logements/{l.slug}/',
        })
    return JsonResponse({'logements': data})


# ─── API Quartiers par ville ──────────────────────────

def api_quartiers_par_ville(request):
    ville_id = request.GET.get('ville_id')
    if not ville_id:
        return JsonResponse({'quartiers': []})
    quartiers = Quartier.objects.filter(
        ville_id=ville_id
    ).order_by('nom').values('id', 'nom')
    return JsonResponse({'quartiers': list(quartiers)})
