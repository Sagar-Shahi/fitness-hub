// Site-wide interactions
(function () {
    const menuToggle = document.getElementById('menuToggle');
    const mainNav = document.getElementById('mainNav');
    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            const open = mainNav.classList.toggle('open');
            menuToggle.classList.toggle('active', open);
            menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
        });
    }

    const header = document.getElementById('siteHeader');
    if (header) {
        const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 8);
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll();
    }

    window.addEventListener('load', () => {
        document.body.dataset.loaded = 'true';
    });

    // Toggle inline form guide for exercises
    document.addEventListener('click', (e) => {
        const toggle = e.target.closest('.form-toggle');
        if (!toggle) return;
        const card = toggle.closest('.exercise-card');
        if (!card) return;
        const guide = card.querySelector('.form-guide');
        if (!guide) return;
        const expanded = toggle.getAttribute('aria-expanded') === 'true';
        toggle.setAttribute('aria-expanded', expanded ? 'false' : 'true');
        if (guide.hasAttribute('hidden')) {
            guide.removeAttribute('hidden');
        } else {
            guide.setAttribute('hidden', '');
        }
    });
})();
