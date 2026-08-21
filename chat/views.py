import json
import re
from groq import Groq 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.conf import settings

from .models import Conversation, Message, ConversationChatbot, MessageChatbot
from logements.models import Logement, Ville, Quartier


# ─── Client Grok ────────────────────────────────────────────────────
def _get_client():
    return Groq(api_key=getattr(settings, 'GROQ_API_KEY', ''))

GROK_MODEL = getattr(settings, 'GROQ_MODEL', "openai/gpt-oss-120b")

# ─── Prompt agent immobilier ─────────────────────────────────────────
PROMPT_AGENT = (
    "Tu es joseph, agent immobilier virtuel chez LogementCM, une agence "
    "immobilière digitale au Cameroun. Tu es compétente, chaleureuse et "
    "précise. Tu réponds naturellement à toute question immobilière : "
    "recherche de logement, démarches de location, documents nécessaires, "
    "conseils de négociation, choix de quartier, droits et devoirs d'un "
    "locataire ou d'un bailleur au Cameroun, prix moyens, etc. "
    "Réponds TOUJOURS en français, de façon claire et concise "
    "(4 à 6 phrases maximum sauf si la question demande clairement plus de détail). "
    "Les prix sont en FCFA."
)


# ════════════════════════════════════════════════════════════════════
# Vues conversation locataire ↔ bailleur
# ════════════════════════════════════════════════════════════════════

@login_required
def liste_conversations(request):
    convs = (
        Conversation.objects.filter(locataire=request.user) |
        Conversation.objects.filter(bailleur=request.user)
    ).select_related(
        'locataire', 'bailleur', 'logement'
    ).order_by('-modifie_le')
    return render(request, 'chat/conversations.html', {
        'conversations': convs
    })


@login_required
def conversation_detail(request, conv_uuid):
    conv = get_object_or_404(Conversation, uuid=conv_uuid)
    if request.user not in [conv.locataire, conv.bailleur]:
        return redirect('chat:conversations')
    Message.objects.filter(
        conversation=conv, non_lu=True
    ).exclude(expediteur=request.user).update(
        non_lu=False, lu_le=timezone.now()
    )
    messages_list = conv.messages.filter(
        supprime=False
    ).select_related('expediteur')
    return render(request, 'chat/conversation.html', {
        'conversation': conv,
        'messages':     messages_list,
    })


@login_required
def poll_messages(request, conv_uuid):
    conv = get_object_or_404(Conversation, uuid=conv_uuid)
    if request.user not in [conv.locataire, conv.bailleur]:
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    Message.objects.filter(
        conversation=conv, non_lu=True
    ).exclude(expediteur=request.user).update(
        non_lu=False, lu_le=timezone.now()
    )
    qs = conv.messages.filter(supprime=False).order_by('-cree_le')[:30]
    data = []
    for m in reversed(list(qs)):
        data.append({
            'id':            m.pk,
            'contenu':       m.contenu,
            'expediteur_id': m.expediteur_id,
            'cree_le':       m.cree_le.strftime('%H:%M'),
            'lu':            not m.non_lu,
        })
    return JsonResponse({'messages': data})


@login_required
def demarrer_conversation(request, logement_id):
    logement = get_object_or_404(Logement, pk=logement_id, statut='PUBLIE')
    if request.user == logement.bailleur:
        return redirect('logements:detail', slug=logement.slug)
    conv, _ = Conversation.objects.get_or_create(
        locataire=request.user,
        bailleur=logement.bailleur,
        logement=logement,
    )
    return redirect('chat:detail', conv_uuid=str(conv.uuid))


@login_required
@require_POST
def envoyer_message(request, conv_uuid):
    conv = get_object_or_404(Conversation, uuid=conv_uuid)
    if request.user not in [conv.locataire, conv.bailleur]:
        return JsonResponse({'error': 'Accès refusé'}, status=403)
    data    = json.loads(request.body)
    contenu = data.get('contenu', '').strip()
    if not contenu:
        return JsonResponse({'error': 'Message vide'}, status=400)
    msg = Message.objects.create(
        conversation=conv,
        expediteur=request.user,
        contenu=contenu[:2000],
    )
    conv.save()
    try:
        from notifs.utils import notif_nouveau_message
        notif_nouveau_message(msg)
    except Exception:
        pass
    return JsonResponse({
        'id':         msg.pk,
        'contenu':    msg.contenu,
        'expediteur': request.user.get_full_name(),
        'cree_le':    msg.cree_le.strftime('%H:%M'),
    })


# ════════════════════════════════════════════════════════════════════
# Vues chatbot IA
# ════════════════════════════════════════════════════════════════════

def chatbot(request):
    if not request.session.session_key:
        request.session.create()
    conv = None
    if request.user.is_authenticated:
        conv = ConversationChatbot.objects.filter(
            utilisateur=request.user
        ).order_by('-modifie_le').first()
    return render(request, 'chat/chatbot.html', {
        'conversation': conv
    })


@require_POST
def chatbot_message(request):
    try:
        data         = json.loads(request.body)
        message_user = data.get('message', '').strip()
        conv_id      = data.get('conv_id')
        if not message_user:
            return JsonResponse({'error': 'Message vide'}, status=400)

        session_id = request.session.session_key or 'anonymous'
        if conv_id:
            try:
                conv = ConversationChatbot.objects.get(pk=conv_id)
            except ConversationChatbot.DoesNotExist:
                conv = _creer_conv(request, session_id)
        else:
            conv = _creer_conv(request, session_id)

        MessageChatbot.objects.create(
            conversation=conv, role='USER', contenu=message_user
        )

        reponse, logements = _generer_reponse(message_user, conv)

        msg_bot = MessageChatbot.objects.create(
            conversation=conv, role='ASSISTANT', contenu=reponse
        )
        if logements:
            msg_bot.logements_sugeres.set(logements)

        logements_data = []
        for l in logements[:4]:
            photo = l.get_photo_principale()
            logements_data.append({
                'id':       l.pk,
                'titre':    l.titre,
                'prix':     l.prix_formate,
                'ville':    l.ville.nom,
                'quartier': l.quartier.nom if l.quartier else '',
                'chambres': l.nb_chambres,
                'type':     l.get_type_logement_display(),
                'photo':    photo.image.url if photo else '/static/images/no-image.jpg',
                'url':      f'/logements/{l.slug}/',
            })

        return JsonResponse({
            'reponse':   reponse,
            'conv_id':   conv.pk,
            'logements': logements_data,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def _creer_conv(request, session_id):
    return ConversationChatbot.objects.create(
        utilisateur=request.user if request.user.is_authenticated else None,
        session_id=session_id,
        titre='Nouvelle recherche',
    )


# ════════════════════════════════════════════════════════════════════
# Intégration Grok (xAI) — remplace Ollama
# ════════════════════════════════════════════════════════════════════

def _appeler_grok(system_prompt, messages_api, message_utilisateur):
    """
    Appelle l'API Grok (xAI).
    Retourne le texte de réponse ou None si erreur/clé manquante.
    """
    try:
        client = _get_client()
        msgs = [{"role": "system", "content": system_prompt}]
        if messages_api:
            msgs += messages_api
        msgs.append({"role": "user", "content": message_utilisateur})

        response = client.chat.completions.create(
            model=GROK_MODEL,
            messages=msgs,
            max_tokens=400,
            temperature=0.6,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Grok Error] {e}")
        return None


def _generer_reponse(message, conv):
    criteres   = _extraire_criteres(message)
    historique = list(
        conv.messages.order_by('cree_le').values('role', 'contenu')[:10]
    )
    messages_api = []
    for m in historique[-6:]:
        messages_api.append({
            'role':    'user' if m['role'] == 'USER' else 'assistant',
            'content': m['contenu']
        })

    # ── Cas 1 : aucun critère → question générale immobilière ─────
    if not criteres:
        system_prompt = (
            PROMPT_AGENT + "\n\n"
            "L'utilisateur n'a donné aucun critère de recherche précis. "
            "Réponds à sa question en tant qu'expert immobilier. "
            "Ne propose aucun logement précis et n'invente aucune annonce. "
            "Si tu sens qu'il cherche un logement, demande-lui la ville et le budget."
        )
        reponse_texte = _appeler_grok(system_prompt, messages_api, message)
        if reponse_texte is None:
            reponse_texte = (
                "Bonjour ! Je suis Sarah, votre agent immobilier LogementCM. 🏠 "
                "Posez-moi une question sur l'immobilier au Cameroun, ou "
                "indiquez-moi votre ville et votre budget pour que je recherche "
                "un logement adapté à vos besoins."
            )
        return reponse_texte, []

    # ── Cas 2 : critères détectés → recherche réelle en base ──────
    logements, est_elargi = _chercher_logements(criteres)

    if logements.exists() and not est_elargi:
        contexte = (
            "\n\nVoici les logements RÉELLEMENT disponibles dans la base de "
            "données qui correspondent EXACTEMENT à la demande :\n"
        )
        for l in logements[:5]:
            contexte += (
                f"- {l.titre} à {l.ville.nom}"
                f"{' (' + l.quartier.nom + ')' if l.quartier else ''}"
                f" : {l.prix_formate}/mois, {l.nb_chambres} chambre(s)\n"
            )
        contexte += "\nPrésente ces logements de façon engageante et professionnelle."

    elif logements.exists() and est_elargi:
        contexte = (
            "\n\nAucun logement ne correspond EXACTEMENT aux critères demandés. "
            "Voici des alternatives PROCHES (même ville et/ou budget légèrement "
            "élargi) réellement disponibles :\n"
        )
        for l in logements[:5]:
            contexte += (
                f"- {l.titre} à {l.ville.nom}"
                f"{' (' + l.quartier.nom + ')' if l.quartier else ''}"
                f" : {l.prix_formate}/mois, {l.nb_chambres} chambre(s)\n"
            )
        contexte += (
            "\nDis d'abord qu'il n'y a pas de correspondance exacte, "
            "puis présente ces alternatives."
        )
    else:
        contexte = (
            "\n\nAucun logement disponible dans la base, même en élargissant. "
            "Dis-le honnêtement sans inventer d'annonce, et propose de "
            "réessayer plus tard ou de modifier les critères."
        )

    system_prompt = (
        PROMPT_AGENT + "\n\n"
        "RÈGLE ABSOLUE : tu ne dois JAMAIS inventer un logement, un prix, "
        "un quartier ou une caractéristique qui n'est pas dans la liste "
        "ci-dessous. Si l'information n'y figure pas, dis-le honnêtement."
        + contexte
    )

    reponse_texte = _appeler_grok(system_prompt, messages_api, message)
    if reponse_texte is None:
        reponse_texte = _reponse_fallback(logements, criteres, est_elargi)

    return reponse_texte, list(logements[:4])


# ════════════════════════════════════════════════════════════════════
# Helpers : extraction de critères + recherche base de données
# ════════════════════════════════════════════════════════════════════

def _extraire_criteres(message):
    msg      = message.lower()
    criteres = {}

    for ville in Ville.objects.filter(actif=True).values_list('nom', flat=True):
        if ville.lower() in msg:
            criteres['ville'] = ville
            break

    for quartier in Quartier.objects.values_list('nom', flat=True):
        if quartier.lower() in msg:
            criteres['quartier'] = quartier
            break

    prix_matches = re.findall(r'(\d[\d\s]*)\s*(?:fcfa|francs?|f\b)?', msg)
    montants = []
    for p in prix_matches[:2]:
        try:
            val = int(p.replace(' ', ''))
            if val > 100:
                montants.append(val)
        except ValueError:
            pass
    if len(montants) >= 2:
        montants.sort()
        criteres['prix_min'] = montants[0]
        criteres['prix_max'] = montants[1]
    elif len(montants) == 1:
        criteres['prix_max'] = montants[0]

    types = {
        'studio':      'STUDIO',
        'appartement': 'APPARTEMENT',
        'villa':       'VILLA',
        'maison':      'MAISON',
        'chambre':     'CHAMBRE',
        'duplex':      'DUPLEX',
    }
    for k, v in types.items():
        if k in msg:
            criteres['type_logement'] = v
            break

    ch = re.search(r'(\d+)\s*chambre', msg)
    if ch:
        criteres['nb_chambres'] = int(ch.group(1))

    return criteres


def _appliquer_filtres(qs, criteres, avec_quartier=True):
    if criteres.get('ville'):
        qs = qs.filter(ville__nom__icontains=criteres['ville'])
    if avec_quartier and criteres.get('quartier'):
        qs = qs.filter(quartier__nom__icontains=criteres['quartier'])
    if criteres.get('type_logement'):
        qs = qs.filter(type_logement=criteres['type_logement'])
    if criteres.get('nb_chambres'):
        qs = qs.filter(nb_chambres__gte=criteres['nb_chambres'])
    return qs


def _chercher_logements(criteres):
    """Appelée UNIQUEMENT quand des critères ont été détectés."""
    base = Logement.objects.filter(
        statut='PUBLIE', disponible=True
    ).select_related('ville', 'quartier').prefetch_related('photos')

    # 1) Recherche exacte
    qs = _appliquer_filtres(base, criteres, avec_quartier=True)
    if criteres.get('prix_min'):
        qs = qs.filter(prix__gte=criteres['prix_min'])
    if criteres.get('prix_max'):
        qs = qs.filter(prix__lte=criteres['prix_max'])
    if qs.order_by('-est_booste', '-cree_le').exists():
        return qs.order_by('-est_booste', '-cree_le')[:5], False

    # 2) Élargi : sans quartier, budget +/- 30%
    qs_large = _appliquer_filtres(base, criteres, avec_quartier=False)
    if criteres.get('prix_max'):
        qs_large = qs_large.filter(prix__lte=int(criteres['prix_max'] * 1.3))
    if criteres.get('prix_min'):
        qs_large = qs_large.filter(prix__gte=int(criteres['prix_min'] * 0.7))
    if qs_large.order_by('-est_booste', '-cree_le').exists():
        return qs_large.order_by('-est_booste', '-cree_le')[:5], True

    # 3) Juste ville + type
    qs_ville = _appliquer_filtres(base, {
        'ville':         criteres.get('ville'),
        'type_logement': criteres.get('type_logement'),
    }, avec_quartier=False).order_by('-est_booste', '-cree_le')
    if criteres.get('ville') and qs_ville.exists():
        return qs_ville[:5], True

    return base.none(), True


def _reponse_fallback(logements, criteres, est_elargi=False):
    if logements.exists() and not est_elargi:
        return (
            f"J'ai trouvé **{logements.count()} logement(s)** correspondant "
            f"exactement à votre recherche ! Voici les meilleures options."
        )
    elif logements.exists() and est_elargi:
        return (
            "Je n'ai pas de correspondance exacte, mais voici des alternatives "
            "proches qui pourraient vous intéresser."
        )
    return (
        "Je n'ai trouvé aucun logement pour ces critères, même en élargissant. "
        "Voulez-vous essayer un autre quartier ou un autre budget ?"
    )