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

  // Animate real dashboard charts once when they enter view; keep the data and SVG geometry unchanged.
  var charts = document.querySelectorAll('[data-animate-chart]');
  function revealChart(chart) {
    if (chart.classList.contains('is-visible')) return;
    chart.classList.add('is-visible');
    chart.querySelectorAll('.chart-bar:not(.is-empty)').forEach(function (bar, index) { bar.style.setProperty('--bar-index', index); });
    chart.querySelectorAll('.chart-line').forEach(function (path) {
      try {
        var length = path.getTotalLength();
        path.style.strokeDasharray = length;
        path.style.strokeDashoffset = length;
        window.requestAnimationFrame(function () { path.style.strokeDashoffset = '0'; });
      } catch (error) { /* retain the static chart if SVG measurement is unavailable */ }
    });
  }
  if ('IntersectionObserver' in window) {
    var chartObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          revealChart(entry.target);
          chartObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.18 });
    charts.forEach(function (chart) { chartObserver.observe(chart); });
  } else {
    charts.forEach(revealChart);
  }


  // Homepage demo: let visitors complete sample sets and feel the UI respond.
  var demoSets = document.querySelectorAll('[data-demo-set]');
  var demoCount = document.querySelector('[data-demo-completed]');
  function updateDemoCount() {
    if (!demoCount) return;
    var completed = document.querySelectorAll('[data-demo-set][aria-pressed="true"]').length;
    demoCount.textContent = String(completed);
  }
  demoSets.forEach(function (set) {
    set.addEventListener('click', function () {
      var done = set.getAttribute('aria-pressed') === 'true';
      set.setAttribute('aria-pressed', done ? 'false' : 'true');
      updateDemoCount();
    });
  });

  // Subtle pointer tilt on the training preview. Touch and reduced-motion users get a static card.
  var tiltCard = document.querySelector('.athletic-preview');
  var reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (tiltCard && !reduceMotion && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    tiltCard.addEventListener('pointermove', function (event) {
      var bounds = tiltCard.getBoundingClientRect();
      var x = (event.clientX - bounds.left) / bounds.width;
      var y = (event.clientY - bounds.top) / bounds.height;
      var rotateY = (x - 0.5) * 8;
      var rotateX = (0.5 - y) * 6;
      tiltCard.style.transform = 'perspective(1100px) rotateX(' + rotateX.toFixed(2) + 'deg) rotateY(' + rotateY.toFixed(2) + 'deg) translateY(-4px)';
    });
    tiltCard.addEventListener('pointerleave', function () {
      tiltCard.style.transform = '';
    });
  }

  // Live session progress and built-in rest timer.
  var sessionSets = document.querySelectorAll('[data-workout-set]');
  var progressBar = document.querySelector('[data-progress-bar]');
  var progressLabel = document.querySelector('[data-progress-label]');
  var completedCount = document.querySelector('[data-completed-count]');
  if (progressBar) progressBar.style.width = (progressBar.getAttribute('data-progress-value') || '0') + '%';
  function refreshSessionProgress() {
    if (!sessionSets.length) return;
    var done = document.querySelectorAll('[data-workout-set].is-complete').length;
    var percent = Math.round(done * 100 / sessionSets.length);
    if (completedCount) completedCount.textContent = String(done);
    if (progressLabel) progressLabel.textContent = percent + '%';
    if (progressBar) progressBar.style.width = percent + '%';
  }
  document.querySelectorAll('[data-set-form]').forEach(function (form) {
    var checkbox = form.querySelector('input[type="checkbox"][name$="-is_completed"]');
    if (checkbox) checkbox.addEventListener('change', function () {
      var card = form.closest('[data-workout-set]');
      if (card) card.classList.toggle('is-complete', checkbox.checked);
      refreshSessionProgress();
    });
  });
  var restDisplay = document.querySelector('[data-rest-display]');
  var restStart = document.querySelector('[data-rest-start]');
  var restReset = document.querySelector('[data-rest-reset]');
  if (restDisplay && restStart) {
    var restSeconds = 90, restInterval = null;
    function paintRest() {
      restDisplay.textContent = String(Math.floor(restSeconds / 60)).padStart(2, '0') + ':' + String(restSeconds % 60).padStart(2, '0');
    }
    function stopRest() { if (restInterval) window.clearInterval(restInterval); restInterval = null; }
    restStart.addEventListener('click', function () {
      if (restInterval) { stopRest(); restStart.textContent = 'Resume'; return; }
      restStart.textContent = 'Pause';
      if (restReset) restReset.hidden = false;
      restInterval = window.setInterval(function () {
        restSeconds = Math.max(0, restSeconds - 1); paintRest();
        if (!restSeconds) { stopRest(); restStart.textContent = 'Again'; }
      }, 1000);
    });
    if (restReset) restReset.addEventListener('click', function () {
      stopRest(); restSeconds = 90; paintRest(); restStart.textContent = 'Start rest'; restReset.hidden = true;
    });
    paintRest();
  }

  // Shared YouTube player lives in the existing Focus Audio panel.
  function showFocusVideo(id, title) {
    id = String(id || '');
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return false;
    var dock = document.getElementById('focus-dock');
    var stage = document.getElementById('focus-video-stage');
    var frame = document.getElementById('focus-video-frame');
    var heading = document.getElementById('focus-video-title');
    var videoStatus = document.getElementById('focus-video-status');
    var audio = document.getElementById('focus-audio');
    if (!dock || !stage || !frame) return false;
    if (audio) audio.pause();
    dock.classList.add('has-video');
    dock.open = true;
    stage.hidden = false;
    if (heading) heading.textContent = title || 'Now playing';
    if (videoStatus) videoStatus.textContent = 'Starting video… Use the YouTube controls to pause or turn sound on.';
    frame.src = 'https://www.youtube-nocookie.com/embed/' + encodeURIComponent(id) + '?rel=0&autoplay=1&mute=1&controls=1&playsinline=1';
    window.setTimeout(function () {
      stage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 80);
    return true;
  }

  function closeFocusVideo() {
    var dock = document.getElementById('focus-dock');
    var stage = document.getElementById('focus-video-stage');
    var frame = document.getElementById('focus-video-frame');
    if (frame) frame.removeAttribute('src');
    if (stage) stage.hidden = true;
    if (dock) dock.classList.remove('has-video');
  }

  var focusVideoClose = document.getElementById('focus-video-close');
  var focusVideoFrame = document.getElementById('focus-video-frame');
  var focusVideoStatus = document.getElementById('focus-video-status');
  if (focusVideoClose) focusVideoClose.addEventListener('click', closeFocusVideo);
  if (focusVideoFrame) focusVideoFrame.addEventListener('load', function () {
    var stage = document.getElementById('focus-video-stage');
    if (stage && !stage.hidden && focusVideoFrame.getAttribute('src') && focusVideoStatus) {
      focusVideoStatus.textContent = 'Player ready. Use the YouTube controls to pause or turn sound on.';
    }
  });

  // Exercise tutorials reuse Focus Audio instead of creating a second player.
  document.querySelectorAll('[data-exercise-tutorial]').forEach(function (panel) {
    var searchButton = panel.querySelector('[data-tutorial-search]');
    var results = panel.querySelector('[data-tutorial-results]');
    var status = panel.querySelector('[data-video-status]');
    var endpoint = panel.getAttribute('data-tutorial-url');

    function playVideo(id, title) {
      if (!showFocusVideo(id, title)) {
        status.textContent = 'The video could not be opened. Please try another tutorial.';
        return;
      }
      status.textContent = 'Playing in the Focus Audio player below.';
    }

    results.addEventListener('click', function (event) {
      var card = event.target.closest('.tutorial-result[data-video-id]');
      if (!card || !results.contains(card)) return;
      event.preventDefault();
      playVideo(card.getAttribute('data-video-id'), card.getAttribute('data-title') || 'Exercise tutorial');
    });

    function renderVideos(videos) {
      results.textContent = '';
      if (!videos.length) {
        status.textContent = 'No suitable video found. Try again later.';
        return;
      }
      var video = videos[0];
      var recommendation = document.createElement('p');
      recommendation.className = 'tutorial-recommendation';
      recommendation.textContent = 'Recommended tutorial: ' + video.title + (video.channel ? ' · ' + video.channel : '');
      results.appendChild(recommendation);
      playVideo(video.id, video.title || 'Exercise tutorial');
    }
    searchButton.addEventListener('click', function () {
      searchButton.disabled = true;
      status.textContent = 'Finding exercise tutorials…';
      results.textContent = '';
      fetch(endpoint, { credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
        .then(function (response) {
          return response.json().then(function (data) {
            if (!response.ok) throw new Error(data.error || 'Could not load tutorials.');
            return data;
          });
        })
        .then(function (data) { renderVideos(data.videos || []); })
        .catch(function (error) { status.textContent = error.message || 'Could not load tutorials. Please try again.'; })
        .finally(function () { searchButton.disabled = false; });
    });
  });

  // Workout quick controls: adjust reps/weight with taps; completing a set saves it immediately.
  document.querySelectorAll('[data-set-form]').forEach(function (form) {
    form.querySelectorAll('[data-step]').forEach(function (button) {
      button.addEventListener('click', function () {
        var input = button.parentElement.querySelector('input[type="number"]');
        if (!input) return;
        var step = Number(button.getAttribute('data-step'));
        var current = Number(input.value || 0);
        var min = Number(input.min || 0);
        var max = Number(input.max || 999999);
        var decimals = (input.step || '1').indexOf('.') >= 0 ? 1 : 0;
        input.value = String(Math.min(max, Math.max(min, current + step)).toFixed(decimals));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    });
    var completed = form.querySelector('input[type="checkbox"][name$="-is_completed"]');
    if (completed) completed.addEventListener('change', function () {
      if (form.requestSubmit) form.requestSubmit();
      else form.submit();
    });
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
    var youtubeId = '';
    if (provider === 'YouTube') {
      if (url.hostname.toLowerCase().replace(/^www\\./, '') === 'youtu.be') {
        youtubeId = url.pathname.split('/').filter(Boolean)[0] || '';
      } else {
        youtubeId = url.searchParams.get('v') || '';
        if (!youtubeId) {
          var parts = url.pathname.split('/').filter(Boolean);
          var marker = parts.findIndex(function (part) { return part === 'embed' || part === 'shorts' || part === 'live'; });
          if (marker >= 0) youtubeId = parts[marker + 1] || '';
        }
      }
      if (youtubeId && showFocusVideo(youtubeId, 'YouTube video')) {
        showStatus('YouTube video is playing in this Focus Audio panel.');
      } else {
        showStatus('YouTube link detected, but its video ID could not be read. Paste a standard YouTube video link.');
      }
    } else if (provider === 'Spotify') {
      showStatus('Spotify links open on Spotify. FitHub does not extract or download protected streams.');
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
    closeFocusVideo();
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
