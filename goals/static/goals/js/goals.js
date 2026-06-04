document.addEventListener('DOMContentLoaded', () => {

  /* Animate progress bars on scroll */
  const progressFills = document.querySelectorAll('.goal-progress-fill');
  if (progressFills.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const width = entry.target.dataset.pct || entry.target.style.width || '0%';
          entry.target.style.width = '0%';
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              entry.target.style.width = width;
            });
          });
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });

    progressFills.forEach(el => {
      el.dataset.pct = el.style.width;
      el.style.width = '0%';
      observer.observe(el);
    });
  }

  /* Goal card menu dropdown */
  document.addEventListener('click', (e) => {
    const menuBtn = e.target.closest('.goal-card-menu');
    if (menuBtn) {
      e.stopPropagation();
      const card = menuBtn.closest('.goal-card');
      if (!card) return;
      const existing = card.querySelector('.dropdown-menu');
      if (existing) {
        existing.remove();
        return;
      }
      document.querySelectorAll('.dropdown-menu').forEach(el => el.remove());
      const menu = document.createElement('div');
      menu.className = 'dropdown-menu';
      menu.innerHTML = `
        <button class="dropdown-item" data-action="view">👁️ View Details</button>
        <button class="dropdown-item" data-action="edit">✏️ Edit Goal</button>
        <button class="dropdown-item danger" data-action="delete">🗑️ Delete</button>
      `;
      menu.style.cssText = `
        position: absolute; top: 100%; right: 0; z-index: 100;
        min-width: 160px; background: #1e293b; border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 0.35rem; box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      `;
      card.style.position = 'relative';
      card.appendChild(menu);

      const style = document.createElement('style');
      style.id = 'dropdown-styles';
      if (!document.getElementById('dropdown-styles')) {
        style.textContent = `
          .dropdown-item {
            display: flex; align-items: center; gap: 0.5rem;
            width: 100%; padding: 0.6rem 0.8rem;
            border: none; border-radius: 8px;
            background: transparent; color: #f8fafc;
            font-size: 0.82rem; font-family: inherit;
            cursor: pointer; transition: background 0.15s ease;
            text-align: left;
          }
          .dropdown-item:hover { background: rgba(255,255,255,0.06); }
          .dropdown-item.danger { color: #fb7185; }
          .dropdown-item.danger:hover { background: rgba(244,63,94,0.1); }
        `;
        document.head.appendChild(style);
      }
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.goal-card-menu') && !e.target.closest('.dropdown-menu')) {
      document.querySelectorAll('.dropdown-menu').forEach(el => el.remove());
    }
  });

  /* Delete confirmation */
  document.addEventListener('click', (e) => {
    const deleteBtn = e.target.closest('.btn-danger');
    if (deleteBtn && !deleteBtn.closest('.dropdown-item')) {
      const card = deleteBtn.closest('.goal-card');
      if (card) {
        card.style.transform = 'scale(0.95)';
        card.style.opacity = '0.5';
        card.style.transition = 'all 0.3s ease';
      }
    }
  });
});
