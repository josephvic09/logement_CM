/* Notifications instantanées : WebSocket + repli sur le rafraîchissement périodique de main.js */
(function () {
  'use strict';
  if (document.body.dataset.authenticated !== 'true' || !('WebSocket' in window)) return;

  var URL_WS = (location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws/notifications/';
  var titreOrigine = document.title;
  var ws = null;
  var tentative = 0;
  var battement = null;
  var contexteAudio = null;

  /* ── Compteur (pastille + titre de l'onglet) ── */
  function afficherCompteur(nb) {
    var badge = document.getElementById('notifBadge');
    var total = document.getElementById('notifCountBadge');
    if (badge) {
      badge.textContent = nb > 9 ? '9+' : nb;
      badge.style.display = nb > 0 ? 'flex' : 'none';
    }
    if (total) {
      total.textContent = nb;
      total.style.display = nb > 0 ? '' : 'none';
    }
    document.title = nb > 0 ? '(' + nb + ') ' + titreOrigine : titreOrigine;
  }

  /* ── Son discret ── */
  function jouerSon() {
    try {
      contexteAudio = contexteAudio || new (window.AudioContext || window.webkitAudioContext)();
      if (contexteAudio.state === 'suspended') contexteAudio.resume();
      var t = contexteAudio.currentTime;
      [[880, 0], [1175, 0.11]].forEach(function (n) {
        var osc = contexteAudio.createOscillator();
        var gain = contexteAudio.createGain();
        osc.type = 'sine';
        osc.frequency.value = n[0];
        gain.gain.setValueAtTime(0.0001, t + n[1]);
        gain.gain.exponentialRampToValueAtTime(0.12, t + n[1] + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.0001, t + n[1] + 0.25);
        osc.connect(gain).connect(contexteAudio.destination);
        osc.start(t + n[1]);
        osc.stop(t + n[1] + 0.26);
      });
    } catch (e) { /* son indisponible : sans importance */ }
  }

  /* ── Carte de notification à l'écran ── */
  function conteneur() {
    var c = document.getElementById('lcmNotifPile');
    if (!c) {
      c = document.createElement('div');
      c.id = 'lcmNotifPile';
      c.setAttribute('aria-live', 'polite');
      c.style.cssText = 'position:fixed;top:78px;right:16px;z-index:10000;display:flex;flex-direction:column;gap:10px;width:min(360px,calc(100vw - 32px));pointer-events:none';
      document.body.appendChild(c);
    }
    return c;
  }

  function ouvrir(n) {
    if (typeof marquerLue === 'function') marquerLue(n.id);
    if (n.lien) window.location.href = n.lien;
  }

  function afficherCarte(n) {
    var pile = conteneur();
    while (pile.children.length >= 4) pile.firstChild.remove();

    var carte = document.createElement('div');
    carte.setAttribute('role', 'status');
    carte.style.cssText = 'pointer-events:auto;cursor:pointer;display:flex;gap:12px;align-items:flex-start;padding:12px 14px;border-radius:14px;' +
      'background:var(--bg-card,#fff);color:var(--text-primary,#1e1b3a);border:1px solid var(--border-color,#e2e8f0);' +
      'box-shadow:0 14px 40px rgba(0,0,0,.18);transform:translateX(120%);opacity:0;transition:transform .35s cubic-bezier(.2,.8,.2,1),opacity .35s';

    var icone = document.createElement('div');
    icone.style.cssText = 'width:38px;height:38px;border-radius:12px;flex-shrink:0;display:flex;align-items:center;justify-content:center;background:' + n.couleur + '22;color:' + n.couleur;
    icone.innerHTML = '<svg data-lucide="' + n.icone + '" style="width:19px;height:19px"></svg>';

    var texte = document.createElement('div');
    texte.style.cssText = 'min-width:0;flex:1';
    var titre = document.createElement('div');
    titre.style.cssText = 'font-weight:700;font-size:.86rem;line-height:1.3';
    titre.textContent = n.titre;
    var message = document.createElement('div');
    message.style.cssText = 'font-size:.78rem;color:var(--text-secondary,#64748b);margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden';
    message.textContent = n.message;
    var temps = document.createElement('div');
    temps.style.cssText = 'font-size:.68rem;color:var(--text-muted,#94a3b8);margin-top:4px';
    temps.textContent = n.temps;
    texte.append(titre, message, temps);

    var fermer = document.createElement('button');
    fermer.type = 'button';
    fermer.setAttribute('aria-label', 'Fermer');
    fermer.style.cssText = 'border:0;background:transparent;color:var(--text-muted,#94a3b8);font-size:1.2rem;line-height:1;padding:0 2px;cursor:pointer';
    fermer.textContent = '×';

    carte.append(icone, texte, fermer);
    pile.appendChild(carte);
    if (window.lucide) lucide.createIcons();

    var minuteur;
    function retirer() {
      clearTimeout(minuteur);
      carte.style.transform = 'translateX(120%)';
      carte.style.opacity = '0';
      setTimeout(function () { carte.remove(); }, 350);
    }
    function armer() { minuteur = setTimeout(retirer, 7000); }

    carte.addEventListener('click', function (e) { if (e.target !== fermer) ouvrir(n); });
    fermer.addEventListener('click', function (e) { e.stopPropagation(); retirer(); });
    carte.addEventListener('mouseenter', function () { clearTimeout(minuteur); });
    carte.addEventListener('mouseleave', armer);

    requestAnimationFrame(function () {
      carte.style.transform = 'translateX(0)';
      carte.style.opacity = '1';
    });
    armer();
  }

  /* ── Notification du navigateur (onglet en arrière-plan) ── */
  function notificationSysteme(n) {
    if (!('Notification' in window) || Notification.permission !== 'granted' || !document.hidden) return;
    try {
      var sys = new Notification(n.titre, { body: n.message, tag: 'lcm-' + n.id });
      sys.onclick = function () { window.focus(); ouvrir(n); sys.close(); };
    } catch (e) { /* non supporté */ }
  }

  function demanderPermission() {
    if (!('Notification' in window) || Notification.permission !== 'default') return;
    try {
      if (localStorage.getItem('lcm_notif_permission')) return;
      localStorage.setItem('lcm_notif_permission', '1');
    } catch (e) { return; }
    Notification.requestPermission();
  }
  document.addEventListener('click', demanderPermission, { once: true });

  /* ── Réception ── */
  function menuOuvert() {
    var liste = document.getElementById('notifList');
    return liste && liste.closest('.dropdown-menu.show');
  }

  function recevoir(d) {
    if (d.type === 'compteur') {
      afficherCompteur(d.nb);
    } else if (d.type === 'nouvelle') {
      afficherCompteur(d.nb);
      afficherCarte(d);
      jouerSon();
      notificationSysteme(d);
      if (menuOuvert() && typeof chargerNotifications === 'function') chargerNotifications();
    }
  }

  /* ── Connexion avec reconnexion automatique ── */
  function connecter() {
    ws = new WebSocket(URL_WS);
    ws.onopen = function () {
      tentative = 0;
      clearInterval(battement);
      battement = setInterval(function () {
        if (ws.readyState === 1) ws.send(JSON.stringify({ type: 'ping' }));
      }, 25000);
    };
    ws.onmessage = function (e) {
      try { recevoir(JSON.parse(e.data)); } catch (err) { /* message illisible */ }
    };
    ws.onclose = function (e) {
      clearInterval(battement);
      if (e.code === 4401) return;  // non connecté : inutile de réessayer
      tentative += 1;
      setTimeout(connecter, Math.min(30000, 1000 * Math.pow(2, tentative)));
    };
    ws.onerror = function () { ws.close(); };
  }

  connecter();
})();
