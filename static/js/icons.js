/* ============================================================
   LOGEMENT CM — Système d'icônes 100% JavaScript (Lucide)
   ============================================================ */

// ─── Initialiser Lucide après chargement DOM ──────────────
document.addEventListener('DOMContentLoaded', () => {
  lucide.createIcons();
  remplacerBootstrapIcons();
});

// ─── Remplacer tous les bi bi-* par Lucide ────────────────
function remplacerBootstrapIcons() {
  // Correspondance bi bi-* → lucide
  const iconMap = {
    // Navigation
    'bi-house':              'home',
    'bi-house-fill':         'home',
    'bi-house-heart-fill':   'heart',
    'bi-search':             'search',
    'bi-bell':               'bell',
    'bi-bell-fill':          'bell',
    'bi-chat-dots':          'message-circle',
    'bi-chat-dots-fill':     'message-circle',
    'bi-person':             'user',
    'bi-person-fill':        'user',
    'bi-person-circle':      'user-circle',
    'bi-box-arrow-in-right': 'log-in',
    'bi-box-arrow-right':    'log-out',
    'bi-person-plus':        'user-plus',
    'bi-speedometer2':       'layout-dashboard',
    'bi-gear':               'settings',
    'bi-gear-fill':          'settings',

    // Logements
    'bi-building':           'building',
    'bi-building-add':       'building-2',
    'bi-building-fill':      'building',
    'bi-geo-alt':            'map-pin',
    'bi-geo-alt-fill':       'map-pin',
    'bi-map':                'map',
    'bi-pin-map':            'map-pin',
    'bi-door-open':          'door-open',
    'bi-droplet':            'droplets',
    'bi-droplet-half':       'droplets',
    'bi-droplet-fill':       'droplets',
    'bi-arrows-fullscreen':  'maximize-2',
    'bi-sofa':               'armchair',
    'bi-car-front':          'car',
    'bi-wifi':               'wifi',
    'bi-lightning':          'zap',
    'bi-lightning-fill':     'zap',
    'bi-thermometer-snow':   'snowflake',
    'bi-shield-check':       'shield-check',
    'bi-shield-lock':        'shield',
    'bi-shield-lock-fill':   'shield',
    'bi-fuel-pump':          'fuel',
    'bi-water':              'waves',
    'bi-house-up':           'home',
    'bi-lock':               'lock',
    'bi-lock-fill':          'lock',
    'bi-layers':             'layers',

    // Actions
    'bi-heart':              'heart',
    'bi-heart-fill':         'heart',
    'bi-star':               'star',
    'bi-star-fill':          'star',
    'bi-plus':               'plus',
    'bi-plus-lg':            'plus',
    'bi-plus-circle':        'plus-circle',
    'bi-plus-circle-fill':   'plus-circle',
    'bi-pencil':             'pencil',
    'bi-pencil-fill':        'pencil',
    'bi-trash':              'trash-2',
    'bi-trash-fill':         'trash-2',
    'bi-eye':                'eye',
    'bi-eye-fill':           'eye',
    'bi-send':               'send',
    'bi-send-fill':          'send',
    'bi-arrow-up-short':     'arrow-up',
    'bi-arrow-up':           'arrow-up',
    'bi-arrow-left':         'arrow-left',
    'bi-arrow-right':        'arrow-right',
    'bi-chevron-left':       'chevron-left',
    'bi-chevron-right':      'chevron-right',
    'bi-check-circle':       'check-circle',
    'bi-check-circle-fill':  'check-circle',
    'bi-x-circle':           'x-circle',
    'bi-x-circle-fill':      'x-circle',

    // UI
    'bi-robot':              'bot',
    'bi-images':             'images',
    'bi-image':              'image',
    'bi-camera':             'camera',
    'bi-printer':            'printer',
    'bi-flag':               'flag',
    'bi-flag-fill':          'flag',
    'bi-info-circle':        'info',
    'bi-exclamation-triangle':'alert-triangle',
    'bi-patch-check':        'badge-check',
    'bi-patch-check-fill':   'badge-check',
    'bi-stars':              'sparkles',
    'bi-lightbulb':          'lightbulb',
    'bi-list-check':         'list-checks',
    'bi-list-ul':            'list',
    'bi-grid':               'grid-3x3',
    'bi-tools':              'wrench',
    'bi-currency-dollar':    'dollar-sign',
    'bi-calendar3':          'calendar',
    'bi-calendar-check':     'calendar-check',
    'bi-calendar-check-fill':'calendar-check',
    'bi-clock':              'clock',
    'bi-clock-history':      'history',
    'bi-telephone':          'phone',
    'bi-telephone-fill':     'phone',
    'bi-envelope':           'mail',
    'bi-envelope-fill':      'mail',
    'bi-people':             'users',
    'bi-people-fill':        'users',
    'bi-person-gear':        'user-cog',
    'bi-key':                'key',
    'bi-key-fill':           'key',
    'bi-facebook':           'facebook',
    'bi-twitter-x':          'twitter',
    'bi-whatsapp':           'message-circle',
    'bi-instagram':          'instagram',
    'bi-layout-dashboard':   'layout-dashboard',
  };

  document.querySelectorAll('i[class*="bi-"]').forEach(el => {
    const classes = Array.from(el.classList);
    const biClass = classes.find(c => c.startsWith('bi-'));
    if (biClass && iconMap[biClass]) {
      const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      svg.setAttribute('data-lucide', iconMap[biClass]);

      // Copier les classes de style importantes
      const keepClasses = classes.filter(c =>
        !c.startsWith('bi') &&
        (c.startsWith('text-') || c.startsWith('me-') || c.startsWith('ms-') ||
         c.startsWith('fs-') || c === 'd-block' || c === 'd-inline')
      );
      keepClasses.forEach(c => svg.classList.add(c));

      // Style par défaut
      svg.style.width  = '1em';
      svg.style.height = '1em';
      svg.style.verticalAlign = '-0.125em';
      svg.style.display = 'inline-block';
      svg.style.flexShrink = '0';

      el.replaceWith(svg);
    }
  });

  // Relancer lucide pour les nouveaux svg
  lucide.createIcons();
}