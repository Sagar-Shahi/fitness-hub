/* FitHub: small helpers. No inline scripts are used anywhere, so the Content-Security-Policy stays strict. */
(function () {
  'use strict';

  // Copy buttons: <button data-copy="text to copy">
  function copyText(text, button) {
    var original = button.textContent;
    function done(ok) {
      button.textContent = ok ? 'Copied' : 'Press Ctrl+C';
      window.setTimeout(function () { button.textContent = original; }, 1800);
    }
    function fallback() {
      var area = document.createElement('textarea');
      area.value = text;
      area.setAttribute('readonly', '');
      area.className = 'visually-hidden';
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(area);
      done(ok);
    }
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () { done(true); }, fallback);
    } else {
      fallback();
    }
  }

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-copy]');
    if (button) {
      event.preventDefault();
      copyText(button.getAttribute('data-copy'), button);
      return;
    }
  });

  // Ask before destructive actions: <form data-confirm="Are you sure?">
  document.addEventListener('submit', function (event) {
    var message = event.target.getAttribute && event.target.getAttribute('data-confirm');
    if (message && !window.confirm(message)) {
      event.preventDefault();
    }
  });

  // Close the account menu when clicking elsewhere or pressing Escape.
  document.addEventListener('click', function (event) {
    document.querySelectorAll('details.account-menu[open]').forEach(function (menu) {
      if (!menu.contains(event.target)) { menu.removeAttribute('open'); }
    });
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      document.querySelectorAll('details.account-menu[open]').forEach(function (menu) { menu.removeAttribute('open'); });
    }
  });
})();
