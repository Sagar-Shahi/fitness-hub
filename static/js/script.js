const menuToggle = document.getElementById('menuToggle');
const mainNav = document.getElementById('mainNav');

if (menuToggle && mainNav) {
    menuToggle.addEventListener('click', () => {
        mainNav.classList.toggle('open');
        menuToggle.classList.toggle('active');
    });
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
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', expanded ? 'false' : 'true');
    if (guide) {
        if (guide.hasAttribute('hidden')) {
            guide.removeAttribute('hidden');
        } else {
            guide.setAttribute('hidden', '');
        }
    }
});
