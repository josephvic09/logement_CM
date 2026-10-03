/* Fenêtre « en ligne » façon liste de contacts Facebook.
   Locataires et admins voient les bailleurs ; les bailleurs voient les locataires.
   Ordinateur : fenêtre ancrée en bas à droite. Mobile : pastille qui ouvre un volet en bas d'écran.
   Alimentée par le WebSocket de notifications.js via l'événement « lcm:ws ». */
(function () {
  'use strict';
  var body = document.body;
  if (body.dataset.authenticated !== 'true') return;

  var voitBailleurs = body.dataset.role !== 'BAILLEUR';
  var TITRE = voitBailleurs ? 'Bailleurs en ligne' : 'Locataires en ligne';
  var VIDE = voitBailleurs ? 'Aucun bailleur en ligne pour le moment.' : 'Aucun locataire en ligne pour le moment.';

  var mq = window.matchMedia('(max-width: 991.98px)');
  var mobile = mq.matches;
  var contacts = new Map();   // id -> fiche
  var ouvert = false;

  function lireEtatBureau() {
    try { return localStorage.getItem('lcm_presence_ouvert') !== '0'; } catch (e) { return true; }
  }
  ouvert = mobile ? false : lireEtatBureau();

  /* ── Styles ── */
  var style = document.createElement('style');
  style.textContent =
    '#lcmPresence{position:fixed;z-index:996;background:var(--bg-card,#fff);color:var(--text-primary,#1e1b3a);' +
      'border:1px solid var(--border-color,#e2e8f0);font-size:.85rem}' +
    '#lcmPresence .pr-tete{width:100%;display:flex;align-items:center;gap:.55rem;border:0;background:transparent;color:inherit;' +
      'font-weight:700;font-size:.86rem;cursor:pointer;text-align:left}' +
    '#lcmPresence .pr-tete:focus-visible{outline:2px solid #6d3fe8;outline-offset:-2px}' +
    '#lcmPresence .pr-point{width:10px;height:10px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 3px rgba(34,197,94,.25);flex-shrink:0}' +
    '#lcmPresence .pr-nb{margin-left:auto;min-width:22px;height:22px;padding:0 7px;border-radius:50px;background:rgba(109,63,232,.12);' +
      'color:#6d3fe8;font-size:.72rem;font-weight:800;display:inline-flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}' +
    '#lcmPresence .pr-court{display:none}' +
    '#lcmPresence .pr-fleche{transition:transform .2s;color:var(--text-muted,#94a3b8);flex-shrink:0;display:flex}' +
    '#lcmPresence .pr-corps{overflow-y:auto;border-top:1px solid var(--border-color,#e2e8f0);padding:.35rem;overscroll-behavior:contain}' +
    '#lcmPresence[data-ouvert="false"] .pr-corps{display:none}' +
    '#lcmPresence .pr-ligne{display:flex;align-items:center;gap:.65rem;padding:.5rem .55rem;border-radius:10px;color:inherit;text-decoration:none;min-height:48px}' +
    '#lcmPresence a.pr-ligne:hover,#lcmPresence a.pr-ligne:active{background:rgba(109,63,232,.08);color:inherit}' +
    '#lcmPresence a.pr-ligne:focus-visible{outline:2px solid #6d3fe8}' +
    '#lcmPresence .pr-avatar{position:relative;width:38px;height:38px;flex-shrink:0}' +
    '#lcmPresence .pr-avatar img{width:100%;height:100%;border-radius:50%;object-fit:cover;display:block;background:#e2e8f0}' +
    '#lcmPresence .pr-avatar i{position:absolute;right:-1px;bottom:-1px;width:12px;height:12px;border-radius:50%;background:#22c55e;border:2px solid var(--bg-card,#fff)}' +
    '#lcmPresence .pr-nom{font-weight:600;line-height:1.25;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}' +
    '#lcmPresence .pr-sous{font-size:.72rem;color:var(--text-muted,#94a3b8)}' +
    '#lcmPresence .pr-ecrire{margin-left:auto;color:#6d3fe8;flex-shrink:0}' +
    '#lcmPresence .pr-vide{padding:1rem .8rem;text-align:center;color:var(--text-muted,#94a3b8);font-size:.8rem}' +
    '#lcmPresence .pr-ligne.nouveau{animation:prApparition .5s ease-out}' +
    '@keyframes prApparition{from{background:rgba(34,197,94,.18)}to{background:transparent}}' +
    '#lcmPresenceFond{display:none}' +

    /* Ordinateur : fenêtre ancrée en bas à droite, à gauche du bouton du chatbot */
    '@media (min-width:992px){' +
      '#lcmPresence{bottom:0;right:96px;width:280px;border-bottom:0;border-radius:12px 12px 0 0;box-shadow:0 -4px 24px rgba(0,0,0,.14)}' +
      '#lcmPresence .pr-tete{padding:.7rem .9rem;border-radius:12px 12px 0 0}' +
      '#lcmPresence .pr-tete:hover{background:rgba(109,63,232,.06)}' +
      '#lcmPresence .pr-corps{max-height:min(340px,55vh)}' +
      '#lcmPresence[data-ouvert="false"] .pr-fleche{transform:rotate(180deg)}' +
    '}' +

    /* Mobile : pastille au-dessus de la barre du bas, volet plein écran en largeur une fois ouvert */
    '@media (max-width:991.98px){' +
      '#lcmPresence{left:12px;bottom:calc(76px + env(safe-area-inset-bottom,0px));border-radius:50px;box-shadow:0 6px 20px rgba(0,0,0,.18)}' +
      '#lcmPresence .pr-tete{padding:.55rem .95rem;min-height:44px}' +
      '#lcmPresence[data-ouvert="false"] .pr-titre,#lcmPresence[data-ouvert="false"] .pr-nb,#lcmPresence[data-ouvert="false"] .pr-fleche{display:none}' +
      '#lcmPresence[data-ouvert="false"] .pr-court{display:inline}' +
      '#lcmPresence[data-ouvert="true"]{z-index:1040;left:0;right:0;bottom:0;width:100%;border-radius:18px 18px 0 0;border-bottom:0;' +
        'box-shadow:0 -10px 40px rgba(0,0,0,.25);padding-bottom:env(safe-area-inset-bottom,0px)}' +
      '#lcmPresence[data-ouvert="true"] .pr-tete{padding:.9rem 1rem}' +
      '#lcmPresence[data-ouvert="true"] .pr-corps{max-height:min(60vh,420px);padding:.4rem .5rem .8rem}' +
      '#lcmPresence[data-ouvert="true"] .pr-fleche{transform:rotate(180deg)}' +
      '#lcmPresenceFond[data-visible="true"]{display:block;position:fixed;inset:0;z-index:1039;background:rgba(0,0,0,.4)}' +
    '}' +
    '@media (prefers-reduced-motion:reduce){#lcmPresence .pr-ligne.nouveau{animation:none}#lcmPresence .pr-fleche{transition:none}}';
  document.head.appendChild(style);

  /* ── Structure ── */
  var fond = document.createElement('div');
  fond.id = 'lcmPresenceFond';

  var fenetre = document.createElement('section');
  fenetre.id = 'lcmPresence';
  fenetre.setAttribute('aria-label', TITRE);

  var tete = document.createElement('button');
  tete.type = 'button';
  tete.className = 'pr-tete';
  tete.setAttribute('aria-controls', 'lcmPresenceListe');
  var point = document.createElement('span');
  point.className = 'pr-point';
  var titre = document.createElement('span');
  titre.className = 'pr-titre';
  titre.textContent = TITRE;
  var court = document.createElement('span');
  court.className = 'pr-court';
  var compteur = document.createElement('span');
  compteur.className = 'pr-nb';
  compteur.setAttribute('aria-live', 'polite');
  var fleche = document.createElement('span');
  fleche.className = 'pr-fleche';
  fleche.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m6 15 6-6 6 6"/></svg>';
  tete.append(point, titre, court, compteur, fleche);

  var corps = document.createElement('div');
  corps.className = 'pr-corps';
  corps.id = 'lcmPresenceListe';

  fenetre.append(tete, corps);
  document.body.append(fond, fenetre);

  function appliquerEtat() {
    fenetre.dataset.ouvert = String(ouvert);
    tete.setAttribute('aria-expanded', String(ouvert));
    fond.dataset.visible = String(mobile && ouvert);
  }

  function basculer(valeur) {
    ouvert = valeur;
    appliquerEtat();
    if (!mobile) {
      try { localStorage.setItem('lcm_presence_ouvert', ouvert ? '1' : '0'); } catch (e) { /* ignoré */ }
    }
  }

  tete.addEventListener('click', function () { basculer(!ouvert); });
  fond.addEventListener('click', function () { basculer(false); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && mobile && ouvert) basculer(false);
  });
  mq.addEventListener('change', function (e) {
    mobile = e.matches;
    ouvert = mobile ? false : lireEtatBureau();
    appliquerEtat();
  });

  /* ── Affichage ── */
  var ICONE_ECRIRE = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>';

  function sousTitre(c) {
    if (c.lien) return 'En ligne';
    return voitBailleurs ? 'En ligne · aucune annonce' : 'En ligne · pas encore de conversation';
  }

  function ligne(c, neuf) {
    var el = document.createElement(c.lien ? 'a' : 'div');
    el.className = 'pr-ligne' + (neuf ? ' nouveau' : '');
    if (c.lien) {
      el.href = c.lien;
      el.title = voitBailleurs ? 'Écrire à ' + c.nom : 'Ouvrir la conversation avec ' + c.nom;
    }

    var avatar = document.createElement('span');
    avatar.className = 'pr-avatar';
    var img = document.createElement('img');
    img.src = c.avatar;
    img.alt = '';
    img.loading = 'lazy';
    var indicateur = document.createElement('i');
    avatar.append(img, indicateur);

    var texte = document.createElement('span');
    texte.style.cssText = 'min-width:0;flex:1';
    var nom = document.createElement('div');
    nom.className = 'pr-nom';
    nom.textContent = c.nom;
    var sous = document.createElement('div');
    sous.className = 'pr-sous';
    sous.textContent = sousTitre(c);
    texte.append(nom, sous);

    el.append(avatar, texte);
    if (c.lien) {
      var ecrire = document.createElement('span');
      ecrire.className = 'pr-ecrire';
      ecrire.innerHTML = ICONE_ECRIRE;
      el.appendChild(ecrire);
    }
    return el;
  }

  function afficher(nouveauId) {
    var liste = Array.from(contacts.values()).sort(function (a, b) { return a.nom.localeCompare(b.nom, 'fr'); });
    compteur.textContent = liste.length;
    court.textContent = liste.length + ' en ligne';
    corps.replaceChildren();
    if (!liste.length) {
      var vide = document.createElement('div');
      vide.className = 'pr-vide';
      vide.textContent = VIDE;
      corps.appendChild(vide);
      return;
    }
    liste.forEach(function (c) { corps.appendChild(ligne(c, c.id === nouveauId)); });
  }

  /* ── Réception depuis le WebSocket ── */
  document.addEventListener('lcm:ws', function (e) {
    var d = e.detail;
    if (d.type === 'presence') {
      contacts.clear();
      d.utilisateurs.forEach(function (c) { contacts.set(c.id, c); });
      afficher();
    } else if (d.type === 'presence_changement') {
      if (d.en_ligne) contacts.set(d.utilisateur.id, d.utilisateur);
      else contacts.delete(d.utilisateur.id);
      afficher(d.en_ligne ? d.utilisateur.id : null);
    }
  });

  appliquerEtat();
  afficher();
})();
