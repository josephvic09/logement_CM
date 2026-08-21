import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Paiement, Abonnement
from logements.models import Reservation


@login_required
def initier_paiement(request, reservation_id):
    reservation = get_object_or_404(
        Reservation, pk=reservation_id,
        locataire=request.user
    )
    if reservation.paye:
        messages.info(request, "Cette réservation a déjà été payée.")
        return redirect('accounts:mes_reservations')
 
    # ── Montant : frais fixes de réservation (1000 FCFA), pas le loyer ──
    montant = reservation.montant or 1000
 
    if request.method == 'POST':
        methode   = request.POST.get('methode', 'MTN_MOMO')
        telephone = request.POST.get('telephone', '').strip()
        if not telephone or len(telephone) < 9:
            messages.error(request, "Numéro de téléphone invalide.")
            return render(request, 'paiements/paiement.html', {
                'reservation': reservation,
                'montant':     montant,
            })
        paiement = Paiement.objects.create(
            utilisateur=request.user,
            type_paiement='RESERVATION',
            methode=methode,
            montant=montant,
            reservation=reservation,
            telephone=telephone,
            statut='TRAITEMENT',
        )
        return redirect('paiements:confirmer', paiement_uuid=str(paiement.uuid))
    return render(request, 'paiements/paiement.html', {
        'reservation': reservation,
        'montant':     montant,
    })
 
 


@login_required
def confirmer_paiement(request, paiement_uuid):
    paiement = get_object_or_404(
        Paiement, uuid=paiement_uuid,
        utilisateur=request.user
    )
    if paiement.est_reussi:
        return redirect('paiements:recu', paiement_uuid=paiement_uuid)
    erreur = None
    if request.method == 'POST':
        code_saisi = request.POST.get('code', '').strip()
        if code_saisi == paiement.code_confirmation:
            paiement.statut         = 'REUSSI'
            paiement.transaction_id = paiement.generer_transaction_id()
            paiement.traite_le      = timezone.now()
            paiement.message_operateur = (
                f"Transaction effectuée avec succès. "
                f"ID: {paiement.transaction_id}"
            )
            paiement.save()
            if paiement.reservation:
                paiement.reservation.paye   = True
                paiement.reservation.statut = 'CONFIRME'
                paiement.reservation.save()
 
                # ── Réservation (pas simple visite) payée : le logement ──
                # ── disparaît du fil puisqu'il est désormais pris.       ──
                if paiement.reservation.type_demande == 'RESERVATION':
                    logement = paiement.reservation.logement
                    logement.statut     = 'LOUE'
                    logement.disponible = False
                    logement.save()
 
            try:
                from notifs.utils import notif_paiement_reussi
                notif_paiement_reussi(paiement)
            except Exception:
                pass
            messages.success(
                request,
                f"Paiement de {paiement.montant_formate} effectué avec succès !"
            )
            return redirect('paiements:recu', paiement_uuid=paiement_uuid)
        else:
            erreur = "Code incorrect. Vérifiez le SMS reçu."
            paiement.statut = 'ECHOUE'
            paiement.save()
    return render(request, 'paiements/confirmer.html', {
        'paiement':          paiement,
        'erreur':            erreur,
        'telephone_masque':  _masquer_telephone(paiement.telephone),
    })


@login_required
def recu_paiement(request, paiement_uuid):
    paiement = get_object_or_404(
        Paiement, uuid=paiement_uuid,
        utilisateur=request.user
    )
    return render(request, 'paiements/recu.html', {
        'paiement': paiement,
    })


@login_required
def telecharger_recu(request, paiement_uuid):
    paiement = get_object_or_404(
        Paiement, uuid=paiement_uuid,
        utilisateur=request.user,
        statut='REUSSI'
    )
    html_content = _generer_html_recu(paiement)
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="recu-{paiement.reference}.pdf"'
        )
        return response
    except ImportError:
        return HttpResponse(html_content, content_type='text/html')


@login_required
def historique_paiements(request):
    paiements  = Paiement.objects.filter(
        utilisateur=request.user
    ).order_by('-cree_le')
    total_paye = sum(p.montant for p in paiements if p.statut == 'REUSSI')
    return render(request, 'paiements/historique.html', {
        'paiements':  paiements,
        'total_paye': total_paye,
        'nb_reussis': paiements.filter(statut='REUSSI').count(),
        'nb_echecs':  paiements.filter(statut='ECHOUE').count(),
    })


@login_required
def abonnements(request):
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')
    abonnement_actif = Abonnement.objects.filter(
        utilisateur=request.user,
        statut='ACTIF',
        fin__gt=timezone.now()
    ).first()
    plans = [
        {
            'code':        'BASIC',
            'nom':         'Basic',
            'prix':        0,
            'prix_affiche':'Gratuit',
            'annonces':    3,
            'couleur':     'var(--gray-400)',
            'recommande':  False,
            'avantages': [
                '3 annonces actives',
                '5 photos par annonce',
                'Messagerie standard',
                'Accès aux statistiques',
            ],
        },
        {
            'code':        'STARTER',
            'nom':         'Starter',
            'prix':        5000,
            'prix_affiche':'5 000 FCFA/mois',
            'annonces':    10,
            'couleur':     'var(--primary)',
            'recommande':  False,
            'avantages': [
                '10 annonces actives',
                '10 photos par annonce',
                '2 boosts gratuits/mois',
                'Badge bailleur vérifié',
                'Support prioritaire',
            ],
        },
        {
            'code':        'PRO',
            'nom':         'Pro',
            'prix':        10000,
            'prix_affiche':'10 000 FCFA/mois',
            'annonces':    30,
            'couleur':     '#8b5cf6',
            'recommande':  True,
            'avantages': [
                '30 annonces actives',
                '20 photos par annonce',
                '5 boosts gratuits/mois',
                'Annonces en vedette',
                'Statistiques avancées',
                'Support 24/7',
            ],
        },
        {
            'code':        'BUSINESS',
            'nom':         'Business',
            'prix':        25000,
            'prix_affiche':'25 000 FCFA/mois',
            'annonces':    100,
            'couleur':     '#f59e0b',
            'recommande':  False,
            'avantages': [
                'Annonces illimitées',
                '50 photos par annonce',
                '20 boosts gratuits/mois',
                'Toujours en vedette',
                'Page agence personnalisée',
                'Account manager dédié',
            ],
        },
    ]
    return render(request, 'paiements/abonnements.html', {
        'plans':            plans,
        'abonnement_actif': abonnement_actif,
    })


@login_required
@require_POST
def souscrire_abonnement(request):
    if not request.user.est_bailleur:
        return redirect('accounts:tableau_de_bord')
    plan      = request.POST.get('plan')
    methode   = request.POST.get('methode', 'MTN_MOMO')
    telephone = request.POST.get('telephone', '').strip()
    prix_plans = {
        'STARTER': 5000,
        'PRO':     10000,
        'BUSINESS':25000,
    }
    if plan not in prix_plans:
        messages.error(request, "Plan invalide.")
        return redirect('paiements:abonnements')
    montant = prix_plans[plan]
    if not telephone or len(telephone) < 9:
        messages.error(request, "Numéro de téléphone invalide.")
        return redirect('paiements:abonnements')
    paiement = Paiement.objects.create(
        utilisateur=request.user,
        type_paiement='ABONNEMENT',
        methode=methode,
        montant=montant,
        telephone=telephone,
        statut='TRAITEMENT',
    )
    return redirect(
        'paiements:confirmer_abonnement',
        paiement_uuid=str(paiement.uuid),
        plan=plan
    )


@login_required
def confirmer_abonnement(request, paiement_uuid, plan):
    paiement = get_object_or_404(
        Paiement, uuid=paiement_uuid,
        utilisateur=request.user
    )
    erreur = None
    if request.method == 'POST':
        code_saisi = request.POST.get('code', '').strip()
        if code_saisi == paiement.code_confirmation:
            from datetime import timedelta
            paiement.statut         = 'REUSSI'
            paiement.transaction_id = paiement.generer_transaction_id()
            paiement.traite_le      = timezone.now()
            paiement.save()
            Abonnement.objects.filter(
                utilisateur=request.user,
                statut='ACTIF'
            ).update(statut='ANNULE')
            abonnement = Abonnement.objects.create(
                utilisateur=request.user,
                plan=plan,
                statut='ACTIF',
                debut=timezone.now(),
                fin=timezone.now() + timedelta(days=30),
                paiement=paiement,
            )
            request.user.is_premium    = True
            request.user.premium_debut = abonnement.debut
            request.user.premium_fin   = abonnement.fin
            request.user.save()
            messages.success(
                request,
                f"Abonnement {abonnement.get_plan_display()} activé !"
            )
            return redirect('accounts:dashboard_bailleur')
        else:
            erreur = "Code incorrect. Vérifiez le SMS reçu."
    return render(request, 'paiements/confirmer_abonnement.html', {
        'paiement':         paiement,
        'plan':             plan,
        'erreur':           erreur,
        'telephone_masque': _masquer_telephone(paiement.telephone),
    })


@login_required
@require_POST
def annuler_paiement(request, paiement_uuid):
    paiement = get_object_or_404(
        Paiement, uuid=paiement_uuid,
        utilisateur=request.user,
        statut__in=['EN_ATTENTE', 'TRAITEMENT']
    )
    paiement.statut = 'ANNULE'
    paiement.save()
    messages.info(request, "Paiement annulé.")
    return redirect('paiements:historique')


# ─── Helpers ─────────────────────────────────────────

def _masquer_telephone(telephone):
    if len(telephone) >= 6:
        return telephone[:3] + '****' + telephone[-3:]
    return telephone


def _generer_html_recu(paiement):
    logement_info = ''
    if paiement.reservation and paiement.reservation.logement:
        l = paiement.reservation.logement
        logement_info = f"""
        <tr>
          <td><strong>Logement</strong></td>
          <td>{l.titre}</td>
        </tr>
        <tr>
          <td><strong>Localisation</strong></td>
          <td>{l.ville.nom}</td>
        </tr>"""
    date_str = ''
    if paiement.traite_le:
        date_str = paiement.traite_le.strftime('%d/%m/%Y à %H:%M')
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
      <div class="montant">{paiement.montant_formate}</div>
      <table>
        <tr><td><strong>Référence</strong></td><td><strong>{paiement.reference}</strong></td></tr>
        <tr><td><strong>Date</strong></td><td>{date_str}</td></tr>
        <tr><td><strong>Méthode</strong></td><td>{paiement.get_methode_display()}</td></tr>
        <tr><td><strong>Numéro</strong></td><td>{_masquer_telephone(paiement.telephone)}</td></tr>
        <tr><td><strong>ID Transaction</strong></td><td>{paiement.transaction_id}</td></tr>
        <tr><td><strong>Client</strong></td><td>{paiement.utilisateur.get_full_name()}</td></tr>
        {logement_info}
        <tr><td><strong>Statut</strong></td><td style="color:#065f46;font-weight:700">Réussi</td></tr>
      </table>
      <div class="footer">
        <p>Merci d'utiliser LogementCM</p>
        <p>© 2024 LogementCM — contact@logementcm.cm</p>
      </div>
    </body>
    </html>"""
