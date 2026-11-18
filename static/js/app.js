/* FitHub: small helpers. No inline scripts are used anywhere, so the Content-Security-Policy stays strict. */
(function () {
  'use strict';

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
    } else { fallback(); }
  }

  document.addEventListener('click', function (event) {
    var button = event.target.closest('[data-copy]');
    if (button) { event.preventDefault(); copyText(button.getAttribute('data-copy'), button); }
  });

  document.addEventListener('submit', function (event) {
    var message = event.target.getAttribute && event.target.getAttribute('data-confirm');
    if (message && !window.confirm(message)) event.preventDefault();
  });

  document.addEventListener('click', function (event) {
    document.querySelectorAll('details.account-menu[open]').forEach(function (menu) {
      if (!menu.contains(event.target)) menu.removeAttribute('open');
    });
  });
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      document.querySelectorAll('details.account-menu[open]').forEach(function (menu) { menu.removeAttribute('open'); });
      var dock = document.getElementById('focus-dock');
      if (dock) dock.removeAttribute('open');
    }
  });

  // Focus player deliberately plays direct audio URLs only. It never scrapes provider pages.
  var input = document.getElementById('focus-audio-url');
  if (!input) return;
  var audio = document.getElementById('focus-audio');
  var status = document.getElementById('focus-status');
  var openLink = document.getElementById('focus-open');
  var download = document.getElementById('focus-download');
  var load = document.getElementById('focus-load');
  var clear = document.getElementById('focus-clear');
  var localFile = document.getElementById('focus-local-file');
  var stopVoice = document.getElementById('focus-stop-speak');
  var activeObjectUrl = null;
  var storageKey = 'fithub.focusAudioUrl.v1';

  function clearAudioSource() {
    audio.pause();
    audio.removeAttribute('src');
    audio.load();
    if (activeObjectUrl) {
      URL.revokeObjectURL(activeObjectUrl);
      activeObjectUrl = null;
    }
  }

  function safeUrl(value) {
    try {
      var url = new URL(value.trim());
      return (url.protocol === 'https:' || url.protocol === 'http:') ? url : null;
    } catch (error) { return null; }
  }
  function providerName(url) {
    var host = url.hostname.toLowerCase().replace(/^www\./, '');
    if (host === 'youtube.com' || host === 'youtu.be' || host === 'music.youtube.com') return 'YouTube';
    if (host === 'spotify.com' || host.endsWith('.spotify.com')) return 'Spotify';
    return '';
  }
  function looksLikeAudio(url) {
    return /\.(mp3|m4a|aac|ogg|oga|opus|wav|flac|webm)(?:$|[?#])/i.test(url.pathname + url.search);
  }
  function showStatus(message) { status.textContent = message; }

  function loadUrl(value, save) {
    var url = safeUrl(value);
    if (!url) { showStatus('Enter a complete http or https link.'); return; }
    clearAudioSource();
    localFile.value = '';
    input.value = url.href;
    openLink.href = url.href;
    openLink.hidden = false;
    var provider = providerName(url);
    download.hidden = true;
    if (provider) {
      showStatus(provider + ' link detected. Open it on ' + provider + ' to listen; FitHub cannot extract or download protected streams.');
    } else if (looksLikeAudio(url)) {
      audio.src = url.href;
      audio.load();
      download.href = url.href;
      download.hidden = false;
      showStatus('Direct audio link loaded. Playback and downloading depend on the source server and its permissions.');
    } else {
      showStatus('This looks like a webpage, not a direct audio file. Open the link or paste a permitted direct audio-file URL.');
    }
    if (save) {
      try { window.localStorage.setItem(storageKey, url.href); } catch (error) { /* storage may be disabled */ }
    }
  }

  load.addEventListener('click', function () { loadUrl(input.value, true); });
  input.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') { event.preventDefault(); loadUrl(input.value, true); }
  });
  openLink.addEventListener('click', function (event) {
    if (openLink.hidden || !openLink.href || openLink.getAttribute('href') === '#') event.preventDefault();
  });
  localFile.addEventListener('change', function () {
    var file = localFile.files && localFile.files[0];
    if (!file) return;
    if (!(file.type && file.type.indexOf('audio/') === 0) &&
        !/\.(mp3|m4a|aac|ogg|oga|opus|wav|flac|webm)$/i.test(file.name)) {
      localFile.value = '';
      showStatus('Choose a recognised audio file (MP3, M4A, WAV, OGG, FLAC or WebM).');
      return;
    }
    clearAudioSource();
    input.value = '';
    openLink.hidden = true;
    download.hidden = true;
    try {
      activeObjectUrl = URL.createObjectURL(file);
      audio.src = activeObjectUrl;
      audio.load();
      showStatus('Local audio ready: ' + file.name + '. It stays on this device and is not uploaded.');
    } catch (error) {
      showStatus('This browser could not open the selected local file.');
    }
  });

  audio.addEventListener('error', function () {
    if (audio.src) showStatus('Could not play this audio source. It may be unavailable, blocked, or use an unsupported format.');
  });

  clear.addEventListener('click', function () {
    clearAudioSource();
    localFile.value = '';
    input.value = '';
    openLink.hidden = true;
    download.hidden = true;
    showStatus('Player cleared.');
    try { window.localStorage.removeItem(storageKey); } catch (error) { /* storage may be disabled */ }
  });

  document.getElementById('focus-speak').addEventListener('click', function () {
    if (!('speechSynthesis' in window) || !('SpeechSynthesisUtterance' in window)) {
      showStatus('Spoken cues are not supported by this browser.');
      return;
    }
    window.speechSynthesis.cancel();
    var cues = [
      'You showed up. That is the first win.',
      'Breathe, focus, and make this set count.',
      'Strong and steady. One rep at a time.',
      'Rest with purpose. You are building progress.'
    ];
    var cue = cues[Math.floor(Math.random() * cues.length)];
    var utterance = new SpeechSynthesisUtterance(cue);
    utterance.rate = 0.96;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
    showStatus('Coach voice is on. Use Stop voice whenever you want.');
  });
  stopVoice.addEventListener('click', function () {
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    showStatus('Coach voice stopped.');
  });

  try {
    var saved = window.localStorage.getItem(storageKey);
    if (saved) loadUrl(saved, false);
  } catch (error) { /* storage may be disabled */ }
})();
