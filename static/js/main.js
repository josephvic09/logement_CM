'use strict';

// ─── CSRF Token ───────────────────────────────────────
function getCsrf() {
  const c = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return c ? c.trim().split('=')[1] : '';
}

// ─── Bouton retour en haut ────────────────────────────
const btnTop = document.getElementById('btnTop');
if (btnTop) {
  window.addEventListener('scroll', () => {
    btnTop.style.display = window.scrollY > 400 ? 'flex' : 'none';
  });
  btnTop.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ─── Fermeture auto des alertes ───────────────────────
document.querySelectorAll('.alert').forEach(alert => {
  setTimeout(() => {
    const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
    if (bsAlert) bsAlert.close();
  }, 5000);
});

// ─── Toast notifications ──────────────────────────────
function showToast(message, type = 'success') {
  const colors = {
    success: 'bg-success',
    error:   'bg-danger',
    warning: 'bg-warning text-dark',
    info:    'bg-primary'
  };
  const icons = {
    success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️'
  };

  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    container.style.cssText = 'position:fixed;top:80px;right:1rem;z-index:9999';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast align-items-center text-white
                     ${colors[type]} border-0 show mb-2`;
  toast.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">
        ${icons[type]} ${message}
      </div>
      <button type="button"
              class="btn-close btn-close-white me-2 m-auto"
              onclick="this.closest('.toast').remove()">
      </button>
    </div>`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ─── Toggle Favori (AJAX) ────────────────────────────
document.addEventListener('click', async function(e) {
  const btn = e.target.closest('.btn-favori');
  if (!btn) return;
  e.preventDefault();

  const logementId = btn.dataset.logementId;
  if (!logementId) return;

  try {
    const res = await fetch(`/logements/${logementId}/favori/`, {
      method:  'POST',
      headers: { 'X-CSRFToken': getCsrf() },
    });
    const data = await res.json();

    const icon = btn.querySelector('i');
    if (data.status === 'added') {
      if (icon) {
        icon.className = 'bi bi-heart-fill text-danger';
      }
      showToast('Ajouté aux favoris ❤️');
    } else {
      if (icon) {
        icon.className = 'bi bi-heart';
      }
      showToast('Retiré des favoris', 'info');
    }
  } catch(e) {
    showToast('Erreur réseau', 'error');
  }
});

// ─── Galerie photos (page détail) ────────────────────
const mainImg = document.getElementById('galleryMain');
if (mainImg) {
  document.querySelectorAll('.thumb-img').forEach(thumb => {
    thumb.addEventListener('click', () => {
      mainImg.src = thumb.src;
    });
  });
}

// ─── Notifications count live ─────────────────────────
async function updateNotifCount() {
  try {
    const res  = await fetch('/notifications/count/');
    const data = await res.json();
    const badge = document.querySelector('.notif-badge');
    if (badge) {
      badge.textContent  = data.count;
      badge.style.display = data.count > 0 ? '' : 'none';
    }
  } catch(e) {}
}

// ─── Init ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {

  // Mettre à jour notifs toutes les 60s
  if (document.body.dataset.authenticated === 'true') {
    updateNotifCount();
    setInterval(updateNotifCount, 60000);
  }

  // Tooltips Bootstrap
  document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => {
    new bootstrap.Tooltip(el);
  });

  // Animation cartes au scroll
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity    = '1';
        e.target.style.transform  = 'translateY(0)';
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.card').forEach(card => {
    card.style.opacity    = '0';
    card.style.transform  = 'translateY(20px)';
    card.style.transition = 'opacity .4s ease, transform .4s ease';
    observer.observe(card);
  });

});

// ─── Export global ────────────────────────────────────
window.LCM = { showToast, getCsrf };

// ─── Système de notifications ─────────────────────────

async function chargerNotifications() {
  try {
    const res  = await fetch('/notifications/dernieres/');
    const data = await res.json();

    const list  = document.getElementById('notifList');
    const badge = document.getElementById('notifBadge');
    const count = document.getElementById('notifCountBadge');

    if (!list) return;

    // Mettre à jour le badge
    if (data.nb_non_lues > 0) {
      badge.textContent    = data.nb_non_lues > 9 ? '9+' : data.nb_non_lues;
      badge.style.display  = 'flex';
      count.textContent    = data.nb_non_lues;
      count.style.display  = '';
    } else {
      badge.style.display  = 'none';
      count.style.display  = 'none';
    }

    // Afficher les notifications
    if (data.notifications.length === 0) {
      list.innerHTML = `
        <div class="text-center py-4 text-muted small">
          <svg data-lucide="bell-off"
               style="width:28px;height:28px;color:var(--gray-200);
                      display:block;margin:0 auto .75rem">
          </svg>
          Aucune notification
        </div>`;
    } else {
      list.innerHTML = data.notifications.map(n => `
        <a href="${n.lien || '#'}"
           onclick="marquerLue(${n.id})"
           class="d-flex gap-3 p-3 text-decoration-none text-dark border-bottom"
           style="background:${n.lue ? 'white' : 'var(--primary-light)'};
                  transition:.15s"
           onmouseover="this.style.background='var(--gray-50)'"
           onmouseout="this.style.background='${n.lue ? 'white' : 'var(--primary-light)'}'">
          <div style="width:36px;height:36px;border-radius:10px;
                      background:${n.couleur}20;
                      display:flex;align-items:center;
                      justify-content:center;flex-shrink:0">
            <svg data-lucide="${n.icone}"
                 style="width:17px;height:17px;color:${n.couleur}">
            </svg>
          </div>
          <div class="flex-grow-1 overflow-hidden">
            <div style="font-weight:${n.lue ? '500' : '700'};
                        font-size:.82rem;white-space:nowrap;
                        overflow:hidden;text-overflow:ellipsis">
              ${n.titre}
            </div>
            <div style="font-size:.73rem;color:var(--text-muted);
                        overflow:hidden;text-overflow:ellipsis;
                        white-space:nowrap;margin-top:1px">
              ${n.message}
            </div>
            <div style="font-size:.68rem;color:var(--text-muted);margin-top:2px">
              ${n.temps}
            </div>
          </div>
          ${!n.lue ? `<div style="width:7px;height:7px;border-radius:50%;
                                   background:var(--primary);flex-shrink:0;
                                   margin-top:6px"></div>` : ''}
        </a>`).join('');
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();

  } catch(e) {
    console.error('Erreur notifications:', e);
  }
}

async function marquerLue(notifId) {
  try {
    await fetch(`/notifications/${notifId}/lue/`, {
      method:  'POST',
      headers: { 'X-CSRFToken': getCsrf() },
    });
    // Mettre à jour visuellement
    const el = document.getElementById(`notif-${notifId}`);
    if (el) {
      el.style.background  = 'white';
      el.style.borderColor = 'var(--border)';
      const point = el.querySelector('[style*="border-radius:50%"]');
      if (point) point.remove();
    }
    updateNotifCount();
  } catch(e) {}
}

async function toutMarquerLu() {
  try {
    await fetch('/notifications/marquer-lues/', {
      method:  'POST',
      headers: { 'X-CSRFToken': getCsrf() },
    });
    chargerNotifications();
    LCM.showToast('Toutes les notifications sont lues', 'success');
  } catch(e) {}
}

async function supprimerNotif(notifId) {
  try {
    await fetch(`/notifications/${notifId}/supprimer/`, {
      method:  'POST',
      headers: { 'X-CSRFToken': getCsrf() },
    });
    const el = document.getElementById(`notif-${notifId}`);
    if (el) {
      el.style.transition = 'opacity .3s, transform .3s';
      el.style.opacity    = '0';
      el.style.transform  = 'translateX(20px)';
      setTimeout(() => el.remove(), 300);
    }
    updateNotifCount();
  } catch(e) {}
}

// ─── Mise à jour count en temps réel ──────────────────

async function updateNotifCount() {
  try {
    const res  = await fetch('/notifications/count/');
    const data = await res.json();
    const badge = document.getElementById('notifBadge');
    const count = document.getElementById('notifCountBadge');
    if (badge) {
      if (data.count > 0) {
        badge.textContent   = data.count > 9 ? '9+' : data.count;
        badge.style.display = 'flex';
        if (count) {
          count.textContent   = data.count;
          count.style.display = '';
        }
      } else {
        badge.style.display = 'none';
        if (count) count.style.display = 'none';
      }
    }
  } catch(e) {}
}

// Charger au démarrage et toutes les 30s
document.addEventListener('DOMContentLoaded', () => {
  const isAuth = document.body.dataset.authenticated === 'true';
  if (isAuth) {
    updateNotifCount();
    setInterval(updateNotifCount, 30000);
  }
});