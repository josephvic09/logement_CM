import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import hrskills
from .hrskills import HRSkillsErreur
from .models import Paiement, Abonnement
from .services import demarrer_paiement, synchroniser
from logements.models import Reservation

METHODES = ('MTN_MOMO', 'ORANGE_MONEY')
FRAIS_RESERVATION = 1000  # FCFA — frais fixes, pas le loyer

PRIX_PLANS = {'STARTER': 5000, 'PRO': 10000, 'BUSINESS': 25000}


def _lancer_paiement(request, paiement, telephone_saisi):
    """Lance la demande Mobile Money ; renvoie True si le client doit valider."""
    telephone = hrskills.normaliser_telephone(telephone_saisi)
    if not telephone:
        paiement.delete()
        messages.error(request, "Numéro invalide : entrez un numéro Mobile Money camerounais (6XX XXX XXX).")
        return False
    paiement.telephone = telephone
    try:
        demarrer_paiement(paiement, telephone)
    except HRSkillsErreur as exc:
        paiement.statut = 'ECHOUE'
        paiement.message_operateur = str(exc)
        paiement.save(update_fields=['telephone', 'statut', 'message_operateur'])
        messages.error(request, str(exc))
        return False
    return True


# ─── Réservation ─────────────────────────────────────

@login_required
def initier_paiement(request, reservation_id):
    reservation = get_object_or_404(
        Reservation.objects.select_related('logement__ville', 'logement__quartier'),
        pk=reservation_id, locataire=request.user
    )
    if reservation.paye:
        messages.info(request, "Cette réservation a déjà été payée.")
        return redirect('accounts:mes_reservations')
    if reservation.type_demande != 'RESERVATION' or reservation.statut != 'EN_ATTENTE':
        messages.error(request, "Cette demande ne nécessite pas de paiement.")
        return redirect('accounts:mes_reservations')

    montant = reservation.montant or FRAIS_RESERVATION
    contexte = {'reservation': reservation, 'montant': montant}

    if request.method == 'POST':
        methode = request.POST.get('methode', 'MTN_MOMO')
        if methode not in METHODES:
            methode = 'MTN_MOMO'
        paiement = Paiement.objects.create(
            utilisateur=request.user, type_paiement='RESERVATION',
            methode=methode, montant=montant, reservation=reservation,
        )
        if _lancer_paiement(request, paiement, request.POST.get('telephone')):
            return redirect('paiements:confirmer', paiement_uuid=paiement.uuid)
    return render(request, 'paiements/paiement.html', contexte)


# ─── Suivi d'un paiement (réservation ou abonnement) ─

@login_required
def confirmer_paiement(request, paiement_uuid):
    """Page d'attente : le client valide sur son téléphone, la page se met à jour seule."""
    paiement = get_object_or_404(
        Paiement.objects.select_related('reservation__logement'),
        uuid=paiement_uuid, utilisateur=request.user
    )
    if paiement.est_reussi:
        return redirect('paiements:recu', paiement_uuid=paiement.uuid)
    return render(request, 'paiements/confirmer.html', {
        'paiement':         paiement,
        'telephone_masque': _masquer_telephone(paiement.telephone),
    })


@login_required
def statut_paiement(request, paiement_uuid):
    """État du paiement en JSON, utilisé par la page d'attente."""
    paiement = get_object_or_404(Paiement, uuid=paiement_uuid, utilisateur=request.user)
    erreur = ''
    if paiement.en_cours:
        try:
            synchroniser(paiement)
        except HRSkillsErreur as exc:
            erreur = str(exc)
    reponse = {'statut': paiement.statut, 'message': paiement.message_operateur or erreur}
    if paiement.est_reussi:
        reponse['url'] = reverse('paiements:recu', args=[paiement.uuid])
    return JsonResponse(reponse)


@csrf_exempt
@require_POST
def webhook_hrskills(request):
    """Notification signée de HR-Skills Pay. On ne se fie pas au contenu reçu : on
    revérifie l'état de la transaction directement auprès de HR-Skills Pay."""
    if not hrskills.signature_valide(request.body, request.headers.get('X-Hub-Signature')):
        return HttpResponse(status=403)
    try:
        reference = json.loads(request.body)['data']['reference']
    except (ValueError, KeyError, TypeError):
        return HttpResponse(status=400)
    paiement = Paiement.objects.filter(reference_externe=reference).first()
    if paiement:
        try:
            synchroniser(paiement)
        except HRSkillsErreur:
            return HttpResponse(status=502)
    return HttpResponse('ok')


@login_required
@require_POST
def annuler_paiement(request, paiement_uuid):
    paiement = get_object_or_404(Paiement, uuid=paiement_uuid, utilisateur=request.user)
    try:
        synchroniser(paiement)
    except HRSkillsErreur:
        pass
    if paiement.est_reussi:
        messages.info(request, "Ce paiement vient d'être validé, il ne peut plus être annulé.")
        return redirect('paiements:recu', paiement_uuid=paiement.uuid)
    if paiement.en_cours:
        paiement.statut = 'ANNULE'
        paiement.save(update_fields=['statut'])
        messages.info(request, "Paiement annulé.")
    return redirect('paiements:historique')


@login_required
def recu_paiement(request, paiement_uuid):
    paiement = get_object_or_404(
        Paiement.objects.select_related('reservation__logement__ville'),
        uuid=paiement_uuid, utilisateur=request.user
    )
    return render(request, 'paiements/recu.html', {'paiement': paiement})


@login_required
def telecharger_recu(request, paiement_uuid):
    paiement = get_object_or_404(
        Paiement.objects.select_related('utilisateur', 'reservation__logement__ville'),
        uuid=paiement_uuid, utilisateur=request.user, statut='REUSSI'
    )
    html_content = _generer_html_recu(paiement)
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="recu-{paiement.reference}.pdf"'
        return response
    except ImportError:
        return HttpResponse(html_content, content_type='text/html')


@login_required
def historique_paiements(request):
    paiements = Paiement.objects.filter(utilisateur=request.user).order_by('-cree_le')
    total_paye = paiements.filter(statut='REUSSI').aggregate(t=Sum('montant'))['t'] or 0
    return render(request, 'paiements/historique.html', {
        'paiements':  paiements,
        'total_paye': total_paye,
        'nb_reussis': paiements.filter(statut='REUSSI').count(),
        'nb_echecs':  paiements.filter(statut='ECHOUE').count(),
    })


# ─── Abonnements ─────────────────────────────────────

@login_required
def abonnements(request):
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')
    abonnement_actif = Abonnement.objects.filter(
        utilisateur=request.user, statut='ACTIF', fin__gt=timezone.now()
    ).first()
    plans = [
        {
            'code': 'BASIC', 'nom': 'Basic', 'prix': 0, 'prix_affiche': 'Gratuit',
            'annonces': 3, 'couleur': 'var(--gray-400)', 'recommande': False,
            'avantages': [
                '3 annonces actives', '5 photos par annonce',
                'Messagerie standard', 'Accès aux statistiques',
            ],
        },
        {
            'code': 'STARTER', 'nom': 'Starter', 'prix': 5000, 'prix_affiche': '5 000 FCFA/mois',
            'annonces': 10, 'couleur': 'var(--primary)', 'recommande': False,
            'avantages': [
                '10 annonces actives', '10 photos par annonce', '2 boosts gratuits/mois',
                'Badge bailleur vérifié', 'Support prioritaire',
            ],
        },
        {
            'code': 'PRO', 'nom': 'Pro', 'prix': 10000, 'prix_affiche': '10 000 FCFA/mois',
            'annonces': 30, 'couleur': '#8b5cf6', 'recommande': True,
            'avantages': [
                '30 annonces actives', '20 photos par annonce', '5 boosts gratuits/mois',
                'Annonces en vedette', 'Statistiques avancées', 'Support 24/7',
            ],
        },
        {
            'code': 'BUSINESS', 'nom': 'Business', 'prix': 25000, 'prix_affiche': '25 000 FCFA/mois',
            'annonces': 100, 'couleur': '#f59e0b', 'recommande': False,
            'avantages': [
                'Annonces illimitées', '50 photos par annonce', '20 boosts gratuits/mois',
                'Toujours en vedette', 'Page agence personnalisée', 'Account manager dédié',
            ],
        },
    ]
    return render(request, 'paiements/abonnements.html', {
        'plans': plans, 'abonnement_actif': abonnement_actif,
    })


@login_required
@require_POST
def souscrire_abonnement(request):
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')
    plan = request.POST.get('plan')
    methode = request.POST.get('methode', 'MTN_MOMO')
    if plan not in PRIX_PLANS:
        messages.error(request, "Plan invalide.")
        return redirect('paiements:abonnements')
    if methode not in METHODES:
        methode = 'MTN_MOMO'

    paiement = Paiement.objects.create(
        utilisateur=request.user, type_paiement='ABONNEMENT',
        methode=methode, montant=PRIX_PLANS[plan], plan=plan,
    )
    if not _lancer_paiement(request, paiement, request.POST.get('telephone')):
        return redirect('paiements:abonnements')
    return redirect('paiements:confirmer', paiement_uuid=paiement.uuid)


# ─── Helpers ─────────────────────────────────────────

def _masquer_telephone(telephone):
    if len(telephone) >= 6:
        return telephone[:5] + '****' + telephone[-3:]
    return telephone


def _generer_html_recu(paiement):
    logement_info = ''
    if paiement.reservation and paiement.reservation.logement:
        logement = paiement.reservation.logement
        logement_info = f"""
        <tr><td><strong>Logement</strong></td><td>{escape(logement.titre)}</td></tr>
        <tr><td><strong>Localisation</strong></td><td>{escape(logement.ville.nom)}</td></tr>"""
    elif paiement.type_paiement == 'ABONNEMENT':
        logement_info = (
            f'<tr><td><strong>Abonnement</strong></td><td>{escape(paiement.plan)}</td></tr>'
        )
    date_str = paiement.traite_le.strftime('%d/%m/%Y à %H:%M') if paiement.traite_le else ''
    return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:2rem;color:#0f172a }}
        .header {{ text-align:center;border-bottom:3px solid #6366f1;padding-bottom:1.5rem;margin-bottom:2rem }}
        .logo {{ font-size:1.8rem;font-weight:900;color:#6366f1 }}
        .montant {{ font-size:2.5rem;font-weight:900;color:#6366f1;text-align:center;margin:1.5rem 0 }}
        table {{ width:100%;border-collapse:collapse }}
        td {{ padding:.75rem;border-bottom:1px solid #e2e8f0;font-size:.9rem }}
        td:first-child {{ color:#64748b;width:45% }}
        .footer {{ text-align:center;margin-top:2rem;color:#94a3b8;font-size:.8rem;
                   border-top:1px solid #e2e8f0;padding-top:1rem }}
      </style>
    </head>
    <body>
      <div class="header">
        <div class="logo">LogementCM</div>
        <p style="color:#64748b;margin:.5rem 0">Institut Africain d'Informatique — Cameroun</p>
        <span style="background:#d1fae5;color:#065f46;padding:.5rem 1.5rem;
                     border-radius:50px;font-weight:700">Paiement Confirmé</span>
      </div>
      <div class="montant">{escape(paiement.montant_formate)}</div>
      <table>
        <tr><td><strong>Référence</strong></td><td><strong>{escape(paiement.reference)}</strong></td></tr>
        <tr><td><strong>Date</strong></td><td>{date_str}</td></tr>
        <tr><td><strong>Méthode</strong></td><td>{escape(paiement.get_methode_display())}</td></tr>
        <tr><td><strong>Numéro</strong></td><td>{escape(_masquer_telephone(paiement.telephone))}</td></tr>
        <tr><td><strong>ID Transaction</strong></td><td>{escape(paiement.transaction_id)}</td></tr>
        <tr><td><strong>Client</strong></td><td>{escape(paiement.utilisateur.get_full_name())}</td></tr>
        {logement_info}
        <tr><td><strong>Statut</strong></td><td style="color:#065f46;font-weight:700">Réussi</td></tr>
      </table>
      <div class="footer">
        <p>Merci d'utiliser LogementCM</p>
        <p>© {timezone.now().year} LogementCM — contact@logementcm.cm</p>
      </div>
    </body>
    </html>"""
