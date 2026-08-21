from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import Notification


@login_required
def liste_notifications(request):
    """Page des notifications."""
    notifs_toutes = request.user.notifications.all()
    notifs_non_lues = notifs_toutes.filter(lue=False)
    notifs_lues     = notifs_toutes.filter(lue=True)[:20]

    # Marquer comme lues auto si demandé
    if request.GET.get('tout_lire'):
        notifs_non_lues.update(lue=True, lue_le=timezone.now())
        return redirect('notifs:liste')

    return render(request, 'notifs/liste.html', {
        'notifs_non_lues': notifs_non_lues[:20],
        'notifs_lues':     notifs_lues,
        'nb_non_lues':     notifs_non_lues.count(),
    })


@login_required
@require_POST
def marquer_lue(request, notif_id):
    """Marquer une notification comme lue."""
    notif = get_object_or_404(
        Notification, pk=notif_id,
        destinataire=request.user
    )
    notif.lue    = True
    notif.lue_le = timezone.now()
    notif.save()
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def marquer_lues(request):
    """Marquer toutes les notifications comme lues."""
    request.user.notifications.filter(lue=False).update(
        lue=True, lue_le=timezone.now()
    )
    return JsonResponse({'status': 'ok'})


@login_required
def compte_non_lues(request):
    """Retourner le nombre de notifications non lues (API)."""
    count = request.user.notifications.filter(lue=False).count()
    return JsonResponse({'count': count})


@login_required
def dernieres_notifications(request):
    """Retourner les 5 dernières notifications (API)."""
    notifs = request.user.notifications.all()[:5]
    data = []
    for n in notifs:
        data.append({
            'id':       n.pk,
            'titre':    n.titre,
            'message':  n.message[:80],
            'icone':    n.icone,
            'couleur':  n.couleur,
            'lue':      n.lue,
            'lien':     n.lien,
            'temps':    _format_temps(n.cree_le),
        })
    return JsonResponse({
        'notifications': data,
        'nb_non_lues': request.user.notifications.filter(lue=False).count(),
    })


@login_required
@require_POST
def supprimer_notification(request, notif_id):
    """Supprimer une notification."""
    notif = get_object_or_404(
        Notification, pk=notif_id,
        destinataire=request.user
    )
    notif.delete()
    return JsonResponse({'status': 'ok'})


# ─── Helpers ─────────────────────────────────────────

def _format_temps(dt):
    """Formater un datetime en temps relatif."""
    from django.utils import timezone as tz
    now   = tz.now()
    diff  = now - dt
    secs  = int(diff.total_seconds())

    if secs < 60:
        return "À l'instant"
    elif secs < 3600:
        mins = secs // 60
        return f"Il y a {mins} min"
    elif secs < 86400:
        hrs = secs // 3600
        return f"Il y a {hrs}h"
    elif secs < 604800:
        days = secs // 86400
        return f"Il y a {days}j"
    else:
        return dt.strftime('%d/%m/%Y')