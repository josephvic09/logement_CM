// ═══════════════════════════════════════════════════════════════
// LogementCM — Service Worker
// Cache les ressources statiques pour un chargement rapide
// et un fonctionnement partiel hors ligne.
// ═══════════════════════════════════════════════════════════════

const CACHE_NAME    = 'logementcm-v1';
const OFFLINE_URL   = '/offline/';

// Ressources à mettre en cache immédiatement à l'installation
const PRECACHE_URLS = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/static/js/icons.js',
  '/static/images/logo.png',
  '/static/images/icon-192.png',
  '/static/images/icon-512.png',
  '/static/images/no-image.jpg',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
  'https://unpkg.com/lucide@latest/dist/umd/lucide.min.js',
];

// ── Installation : précache ───────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
      .catch(err => console.warn('[SW] Précache partiel :', err))
  );
});

// ── Activation : nettoyage des anciens caches ─────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch : stratégie Network First avec fallback cache ───────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorer les requêtes non-GET et les API externes
  if (request.method !== 'GET') return;
  if (!url.origin.includes(self.location.hostname) &&
      !url.hostname.includes('cdn.jsdelivr.net') &&
      !url.hostname.includes('unpkg.com')) return;

  // Fichiers statiques → Cache First (rapide)
  if (url.pathname.startsWith('/static/') || url.pathname.startsWith('/media/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(c => c.put(request, clone));
          }
          return response;
        });
      })
    );
    return;
  }

  // Pages HTML → Network First avec fallback cache
  event.respondWith(
    fetch(request)
      .then(response => {
        if (response.ok && request.headers.get('Accept').includes('text/html')) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, clone));
        }
        return response;
      })
      .catch(() => {
        // Hors ligne → chercher en cache, sinon page offline
        return caches.match(request).then(cached => {
          if (cached) return cached;
          if (request.headers.get('Accept') &&
              request.headers.get('Accept').includes('text/html')) {
            return caches.match('/') || new Response(
              '<h1>Hors ligne</h1><p>LogementCM nécessite une connexion internet.</p>',
              { headers: { 'Content-Type': 'text/html; charset=utf-8' } }
            );
          }
        });
      })
  );
});
