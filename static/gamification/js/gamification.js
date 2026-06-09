/* Fitness Hub — Gamification client UI
 *
 *   - Level-up modal (auto-opens on /play/ when ?levelup=N is in the URL)
 *   - Achievement toasts (announce badges from server messages)
 *   - Confetti animation (used by level-up + claim button)
 *   - Floating "+XP" popups
 *
 * The page may include window.LEVEL_UP_DATA / window.BADGE_TOASTS as
 * pre-rendered JSON, or those values can come from a data-* attribute
 * on the body.
 */

(function () {
    'use strict';

    // -------------------------------------------------------------------
    // Confetti
    // -------------------------------------------------------------------
    const CONFETTI_COLORS = ['#22c55e', '#14b8a6', '#06b6d4', '#f59e0b',
                             '#ec4899', '#8b5cf6', '#fbbf24', '#fb7185'];

    function fireConfetti(count) {
        count = count || 80;
        const container = document.createElement('div');
        container.className = 'confetti-container';
        document.body.appendChild(container);
        for (let i = 0; i < count; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = Math.random() * 100 + 'vw';
            piece.style.background = CONFETTI_COLORS[i % CONFETTI_COLORS.length];
            piece.style.animationDelay = (Math.random() * 0.4) + 's';
            piece.style.animationDuration = (1.8 + Math.random() * 1.2) + 's';
            piece.style.transform = 'rotate(' + Math.random() * 360 + 'deg)';
            piece.style.width = (6 + Math.random() * 8) + 'px';
            piece.style.height = (8 + Math.random() * 8) + 'px';
            container.appendChild(piece);
        }
        setTimeout(function () { container.remove(); }, 3000);
    }

    // Expose globally so other components can trigger confetti.
    window.fireConfetti = fireConfetti;

    // -------------------------------------------------------------------
    // Floating "+XP" popup
    // -------------------------------------------------------------------
    function floatXP(text, x, y) {
        const el = document.createElement('div');
        el.className = 'xp-popup';
        el.textContent = text;
        el.style.left = (x || (window.innerWidth / 2)) + 'px';
        el.style.top  = (y || (window.innerHeight / 2)) + 'px';
        document.body.appendChild(el);
        setTimeout(function () { el.remove(); }, 1500);
    }
    window.floatXP = floatXP;

    // -------------------------------------------------------------------
    // Level-up modal
    // -------------------------------------------------------------------
    function showLevelUp(level, title, levelsGained) {
        const tmpl = document.getElementById('levelupTmpl');
        if (!tmpl) return;
        const root = tmpl.content.firstElementChild.cloneNode(true);
        root.querySelector('.level-big').textContent = level;
        root.querySelector('.new-title').textContent = title;
        if (levelsGained > 1) {
            root.querySelector('.levels-gained').textContent =
                '+' + levelsGained + ' levels at once!';
        }
        const close = function () {
            root.classList.remove('is-open');
            setTimeout(function () { root.remove(); }, 400);
            document.removeEventListener('keydown', onKey);
        };
        const onKey = function (e) { if (e.key === 'Escape') close(); };
        root.querySelector('.levelup-close').addEventListener('click', close);
        root.addEventListener('click', function (e) {
            if (e.target === root) close();
        });
        document.addEventListener('keydown', onKey);
        document.body.appendChild(root);
        requestAnimationFrame(function () {
            root.classList.add('is-open');
            fireConfetti(120);
            setTimeout(function () { fireConfetti(60); }, 800);
        });
    }
    window.showLevelUp = showLevelUp;

    // -------------------------------------------------------------------
    // Achievement toast
    // -------------------------------------------------------------------
    function showAchievementToast(icon, name, description) {
        const tmpl = document.getElementById('achievementTmpl');
        if (!tmpl) return;
        const root = tmpl.content.firstElementChild.cloneNode(true);
        root.querySelector('.a-icon').textContent = icon || '🏅';
        root.querySelector('.a-text strong').textContent = name || 'Achievement unlocked';
        root.querySelector('.a-text span').textContent = description || '';
        document.body.appendChild(root);
        requestAnimationFrame(function () {
            root.classList.add('is-open');
            fireConfetti(40);
        });
        setTimeout(function () {
            root.classList.remove('is-open');
            setTimeout(function () { root.remove(); }, 500);
        }, 5000);
    }
    window.showAchievementToast = showAchievementToast;

    // -------------------------------------------------------------------
    // Auto-trigger from body data attributes
    // -------------------------------------------------------------------
    document.addEventListener('DOMContentLoaded', function () {
        const body = document.body;
        if (!body) return;

        // Level-up
        if (body.dataset.levelup) {
            try {
                const data = JSON.parse(body.dataset.levelup);
                setTimeout(function () {
                    showLevelUp(data.level, data.title, data.levels_gained || 1);
                }, 350);
            } catch (e) { /* ignore */ }
        }

        // Multiple achievement toasts in a row
        if (body.dataset.badges) {
            try {
                const badges = JSON.parse(body.dataset.badges);
                badges.forEach(function (b, i) {
                    setTimeout(function () {
                        showAchievementToast(b.icon, b.name, b.description);
                    }, 600 + i * 1800);
                });
            } catch (e) { /* ignore */ }
        }
    });

    // -------------------------------------------------------------------
    // Wire claim buttons to fire confetti on success
    // -------------------------------------------------------------------
    document.addEventListener('submit', function (e) {
        if (e.target && e.target.matches && e.target.matches('form.quest-claim')) {
            // The page reloads after the claim; fire confetti right before.
            fireConfetti(60);
        }
    });

    // -------------------------------------------------------------------
    // Streak shield consume confirmation
    // -------------------------------------------------------------------
    document.addEventListener('click', function (e) {
        const btn = e.target.closest && e.target.closest('.use-shield-btn');
        if (btn) {
            e.preventDefault();
            if (window.confirm('Burn 1 streak shield to protect today\'s streak?')) {
                btn.closest('form').submit();
            }
        }
    });
})();
