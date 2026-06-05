(function () {
  'use strict';

  const API_URL = '/chatbot/api/';

  // ------------- DOM helpers -------------
  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    if (attrs) {
      for (const k in attrs) {
        if (k === 'className') node.className = attrs[k];
        else if (k === 'dataset') Object.assign(node.dataset, attrs[k]);
        else if (k === 'html') node.innerHTML = attrs[k];
        else if (k.indexOf('on') === 0 && typeof attrs[k] === 'function') {
          node.addEventListener(k.slice(2), attrs[k]);
        } else {
          node.setAttribute(k, attrs[k]);
        }
      }
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach((c) => {
        if (c == null) return;
        node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
      });
    }
    return node;
  }

  function getCookie(name) {
    const parts = document.cookie.split('; ');
    for (const p of parts) {
      const [k, v] = p.split('=');
      if (k === name) return decodeURIComponent(v);
    }
    return '';
  }

  function csrfToken() {
    const fromCookie = getCookie('csrftoken');
    if (fromCookie) return fromCookie;
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') || '' : '';
  }

  // ------------- Render helpers -------------
  function escapeHtml(s) {
    return s
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function bubbleHtml(text, role) {
    const safe = escapeHtml(text)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
    return `<div class="chat-msg__bubble">${safe}</div>`;
  }

  function appendMessage(log, text, role) {
    const wrap = el('div', { className: 'chat-msg chat-msg--' + role, html: bubbleHtml(text, role) });
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
    return wrap;
  }

  function renderSuggestions(container, suggestions) {
    if (!suggestions || !suggestions.length) return;
    container.innerHTML = '';
    suggestions.forEach((msg) => {
      const btn = el('button', {
        type: 'button',
        className: 'chip',
        'data-msg': msg,
        onclick: function () { onSend(msg); },
      }, msg);
      container.appendChild(btn);
    });
  }

  // ------------- Send flow -------------
  function onSend(text) {
    text = (text || '').trim();
    if (!text) return;

    // Find the log & form on the active surface (full page or widget)
    const surface = currentSurface();
    if (!surface) return;
    const log = surface.querySelector('.chat-log');
    const form = surface.querySelector('.chat-form');
    const input = surface.querySelector('.chat-input');
    const sendBtn = surface.querySelector('.chat-form__send');
    const chipBox = surface.querySelector('.quick-replies');

    appendMessage(log, text, 'user');
    if (input) input.value = '';
    if (sendBtn) sendBtn.disabled = true;
    if (chipBox) chipBox.innerHTML = '';

    const typing = el('div', {
      className: 'chat-msg chat-msg--bot',
      html: '<div class="chat-msg__bubble"><span class="chat-typing"><span></span><span></span><span></span></span></div>',
    });
    log.appendChild(typing);
    log.scrollTop = log.scrollHeight;

    fetch(API_URL, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken(),
        'X-Requested-With': 'XMLHttpRequest',
      },
      body: JSON.stringify({ message: text }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (typing.parentNode) typing.parentNode.removeChild(typing);
        appendMessage(log, data.reply || '(no response)', 'bot');
        if (chipBox) renderSuggestions(chipBox, data.suggestions);
      })
      .catch((err) => {
        if (typing.parentNode) typing.parentNode.removeChild(typing);
        appendMessage(log, '⚠️ Network error — please try again.', 'bot');
      })
      .finally(() => {
        if (sendBtn) sendBtn.disabled = false;
        if (input) input.focus();
      });
  }

  // ------------- Surface detection -------------
  // We support two surfaces: a full chat page and a floating widget panel.
  function currentSurface() {
    const open = document.querySelector('.chat-panel.is-open');
    if (open) return open;
    const page = document.querySelector('.chat-page .chat-card');
    if (page) return page;
    return null;
  }

  // ------------- Wire up the full chat page -------------
  function initFullPage() {
    const card = document.querySelector('.chat-page .chat-card');
    if (!card) return;
    const form = card.querySelector('#chat-form');
    const input = card.querySelector('#chat-input');
    input.classList.add('chat-input');
    const chips = card.querySelectorAll('.chip');

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      onSend(input.value);
    });
    chips.forEach((c) => {
      c.addEventListener('click', function () {
        onSend(c.dataset.msg);
      });
    });

    // Auto-scroll to bottom of log on load
    const log = card.querySelector('.chat-log');
    if (log) log.scrollTop = log.scrollHeight;
  }

  // ------------- Floating widget -------------
  let widgetBooted = false;

  function buildWidget() {
    if (document.querySelector('.chat-fab')) return;

    const fab = el('button', {
      type: 'button',
      className: 'chat-fab',
      'aria-label': 'Open fitness coach',
      title: 'Ask the coach',
    }, '🤖');
    fab.addEventListener('click', toggleWidget);

    const panel = el('div', { className: 'chat-panel', role: 'dialog', 'aria-label': 'Fitness coach' });
    panel.innerHTML = `
      <div class="chat-panel__head">
        <span class="chat-panel__title"><span class="status-dot" aria-hidden="true"></span> Fitness Coach</span>
        <button type="button" class="chat-panel__close" aria-label="Close">×</button>
      </div>
      <div class="chat-log" role="log" aria-live="polite">
        <div class="chat-msg chat-msg--bot">
          <div class="chat-msg__bubble">Hey 👋 — ask me for exercises, app help, or nutrition basics.</div>
        </div>
      </div>
      <div class="quick-replies"></div>
      <form class="chat-form" autocomplete="off">
        <input class="chat-input" type="text" placeholder="Type your question…" maxlength="600" required>
        <button type="submit" class="btn chat-form__send" aria-label="Send">➤</button>
      </form>
      <p class="chat-foot">🛡️ Informational only — not medical advice.</p>
    `;
    document.body.appendChild(fab);
    document.body.appendChild(panel);

    panel.querySelector('.chat-panel__close').addEventListener('click', closeWidget);
    const form = panel.querySelector('.chat-form');
    const input = panel.querySelector('.chat-input');
    const chips = panel.querySelector('.quick-replies');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      onSend(input.value);
    });
    chips.addEventListener('click', function (e) {
      const t = e.target.closest('.chip');
      if (t) onSend(t.dataset.msg);
    });
    widgetBooted = true;
  }

  function openWidget() {
    buildWidget();
    const p = document.querySelector('.chat-panel');
    p.classList.add('is-open');
    const i = p.querySelector('.chat-input');
    if (i) setTimeout(() => i.focus(), 50);
  }
  function closeWidget() {
    const p = document.querySelector('.chat-panel');
    if (p) p.classList.remove('is-open');
  }
  function toggleWidget() {
    const p = document.querySelector('.chat-panel');
    if (!p) return openWidget();
    if (p.classList.contains('is-open')) closeWidget();
    else openWidget();
  }

  // Inject typing-indicator styles (kept here so chat.css stays clean)
  function injectTypingStyles() {
    if (document.getElementById('chat-typing-styles')) return;
    const style = document.createElement('style');
    style.id = 'chat-typing-styles';
    style.textContent = `
      .chat-typing { display: inline-flex; gap: 4px; align-items: center; }
      .chat-typing span {
        width: 6px; height: 6px; border-radius: 50%;
        background: #8b9bb1;
        display: inline-block;
        animation: typingBlink 1.2s infinite ease-in-out;
      }
      .chat-typing span:nth-child(2) { animation-delay: 0.15s; }
      .chat-typing span:nth-child(3) { animation-delay: 0.3s; }
      @keyframes typingBlink {
        0%, 80%, 100% { opacity: 0.25; transform: translateY(0); }
        40% { opacity: 1; transform: translateY(-2px); }
      }
    `;
    document.head.appendChild(style);
  }

  // ------------- Bootstrap -------------
  function boot() {
    injectTypingStyles();
    initFullPage();

    // Build widget only on pages that aren't the full chat page itself.
    if (!document.querySelector('.chat-page .chat-card')) {
      buildWidget();
    }

    // Expose for debugging
    window.__fitnessChat = { open: openWidget, close: closeWidget, send: onSend };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
