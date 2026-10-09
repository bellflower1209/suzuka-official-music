/* Native static-site transitions. No autoplay, dependencies or content fetches. */
(() => {
  'use strict';
  const element = document.getElementById('cg-config');
  if (!element) return;
  let config;
  try { config = JSON.parse(element.textContent); } catch { return; }
  const script = [...document.scripts].find(item => /\/assets\/celestial-gate\.js(?:\?|$)/.test(item.src));
  if (!script) return;
  const root = new URL('../', script.src);
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const read = key => { try { return localStorage.getItem(`suzuka.cg.${key}`); } catch { return null; } };
  const save = (key, value) => { try { localStorage.setItem(`suzuka.cg.${key}`, String(value)); } catch { /* Private browsing still works. */ } };
  let sound = Boolean(config.doorAudio) && read('sound') === 'on';
  let short = read('short') === 'true';
  const storedVolume = read('volume');
  let volume = storedVolume !== null && Number.isFinite(Number(storedVolume)) ? Math.max(0, Math.min(.5, Number(storedVolume))) : config.defaultVolume;
  let audioContext = null;
  let audioSource = null;
  let gainNode = null;
  let loadController = null;
  function stopSound() {
    loadController?.abort(); loadController = null;
    if (audioSource) { try { audioSource.stop(); } catch { /* Already ended. */ } audioSource.disconnect(); audioSource = null; }
    gainNode?.disconnect(); gainNode = null;
  }
  let active = null;
  let dialog = null;
  const soundButton = document.querySelector('[data-cg-sound]');
  const shortInput = document.querySelector('[data-cg-short]');
  const volumeInput = document.querySelector('[data-cg-volume]');
  function reflect() {
    if (soundButton) {
      soundButton.disabled = !config.doorAudio;
      soundButton.textContent = config.doorAudio ? `音声 ${sound ? 'ON' : 'OFF'}` : '音源未登録';
      soundButton.setAttribute('aria-pressed', String(sound));
    }
    if (shortInput) shortInput.checked = short;
    if (volumeInput) volumeInput.value = String(volume);
  }
  reflect();
  // A failed AVIF/source-set must not hide navigation or canonical copy.
  // Retry the existing WebP fallback; official thumbnails retry their untouched source.
  function imageFallback(image) {
    if (!(image instanceof HTMLImageElement) || !image.closest('.cg-scene,.cg-door-beyond,.cg-official-inset')) return;
    if (!image.dataset.cgFallback) {
      image.dataset.cgFallback = 'true';
      image.closest('picture')?.querySelectorAll('source').forEach(source => source.remove());
      image.removeAttribute('srcset');
      if (image.getAttribute('src')) image.src = image.getAttribute('src');
    } else if (image.closest('.cg-scene,.cg-door-beyond')) image.style.opacity = '0';
  }
  document.addEventListener('error', event => imageFallback(event.target), true);
  // A priority image can fail before this deferred script has installed listeners.
  document.querySelectorAll('.cg-scene img,.cg-official-inset img').forEach(image => {
    if (image.complete && !image.naturalWidth) imageFallback(image);
  });
  soundButton?.addEventListener('click', () => {
    if (!config.doorAudio) return;
    sound = !sound;
    save('sound', sound ? 'on' : 'off');
    if (!sound) stopSound();
    reflect();
  });
  shortInput?.addEventListener('change', () => { short = shortInput.checked; save('short', short); });
  volumeInput?.addEventListener('input', () => { volume = Math.max(0, Math.min(.5, Number(volumeInput.value))); save('volume', volume); if (gainNode) gainNode.gain.value = volume; });
  addEventListener('storage', event => {
    if (!event.key?.startsWith('suzuka.cg.')) return;
    sound = Boolean(config.doorAudio) && read('sound') === 'on';
    short = read('short') === 'true';
    const next = Number(read('volume'));
    if (read('volume') !== null && Number.isFinite(next)) volume = Math.max(0, Math.min(.5, next));
    if (!sound) stopSound();
    reflect();
  });

  // Cross-origin iframe playback is unknowable without cooperation: silence the SFX.
  const musicIsActive = () => [...document.querySelectorAll('audio,video')].some(media => !media.paused && !media.ended)
    || Boolean(document.querySelector('iframe[src*="youtube"],iframe[src*="vimeo"],[data-player-state="playing"],[data-music-playing="true"]'));

  function getDialog() {
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    if (typeof dialog.showModal !== 'function') return null;
    dialog.className = 'cg-door-dialog';
    dialog.setAttribute('aria-labelledby', 'cg-door-title');
    dialog.setAttribute('aria-describedby', 'cg-door-description');
    dialog.innerHTML = '<div class="cg-door-view" aria-hidden="true"><picture class="cg-door-beyond"><source type="image/avif"><img alt="" decoding="async"></picture><div class="cg-door-portal"><div class="cg-door-leaves"><div class="cg-door-leaf cg-door-left"></div><div class="cg-door-leaf cg-door-right"></div></div><img class="cg-door-frame" alt="" decoding="async"><div class="cg-door-sigil"><span>✧</span></div></div></div><div class="cg-door-status"><p data-cg-door-realm></p><h2 id="cg-door-title"></h2><small id="cg-door-description" aria-live="polite"></small></div><button class="cg-door-skip" type="button">スキップして進む ↗</button><button class="cg-door-cancel" type="button">キャンセル / Esc</button>';
    document.body.append(dialog);
    dialog.querySelector('.cg-door-skip').addEventListener('click', () => finish(true));
    dialog.querySelector('.cg-door-cancel').addEventListener('click', () => finish(false));
    dialog.addEventListener('cancel', event => { event.preventDefault(); finish(false); });
    return dialog;
  }

  function later(callback, ms, state) {
    const id = setTimeout(() => { if (active === state) callback(); }, ms);
    state.timers.push(id);
  }
  function finish(navigate) {
    const state = active;
    if (!state) return;
    active = null;
    state.timers.forEach(clearTimeout);
    stopSound();
    dialog?.close();
    dialog?.classList.remove('cg-door-opening');
    document.body.style.overflow = state.overflow;
    state.trigger?.focus({preventScroll:true});
    if (navigate) location.assign(state.destination.href);
  }
  function start(destination, artist, trigger, returning) {
    if (active) return;
    const panel = getDialog();
    if (!panel) { location.assign(destination.href); return; }
    const fast = returning || short || reduced.matches || navigator.connection?.saveData;
    const state = {destination, trigger, timers:[], overflow:document.body.style.overflow, started:false};
    active = state;
    panel.className = `cg-door-dialog${artist?.realm === 'infernal' ? ' cg-infernal' : ''}${returning ? ' cg-returning' : ''}`;
    const emblem = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    emblem.setAttribute('viewBox', '0 0 64 64'); emblem.setAttribute('aria-hidden', 'true');
    const use = document.createElementNS('http://www.w3.org/2000/svg', 'use');
    use.setAttribute('href', new URL(`assets/celestial-emblems.svg#${artist?.emblem || 'asteria'}`, root).href);
    emblem.append(use); panel.querySelector('.cg-door-sigil').replaceChildren(emblem);
    panel.style.setProperty('--gate-accent', artist?.accent || '#806432');
    panel.style.setProperty('--gate-paper', artist?.realm === 'infernal' ? '#19141f' : (artist?.tint || '#fcf9ef'));
    const kind = artist?.realm === 'infernal' ? 'infernal' : 'celestial';
    const backdrop = returning ? config.cinema.home : artist.background;
    const size = matchMedia('(max-width:640px)').matches ? 'mobile' : '1280';
    const imageUrl = (name, extension) => new URL(`assets/cinema/${name}.${extension}`, root).href;
    panel.querySelector('.cg-door-beyond source').srcset = imageUrl(`${backdrop}-${size}`, 'avif');
    panel.querySelector('.cg-door-beyond img').src = imageUrl(`${backdrop}-${size}`, 'webp');
    panel.querySelector('.cg-door-frame').src = imageUrl(`frame-${kind}-${fast ? 480 : 960}`, 'webp');
    panel.style.setProperty('--gate-texture', `url("${imageUrl(`door-${kind}-${fast ? 480 : 960}`, 'webp')}")`);
    panel.querySelector('#cg-door-title').textContent = returning ? '天界へ' : artist.name;
    panel.querySelector('[data-cg-door-realm]').textContent = returning ? 'CELESTIAL GATE' : `${artist.label} / ${artist.realm === 'infernal' ? 'INFERNAL' : 'CELESTIAL'} REALM`;
    const description = panel.querySelector('#cg-door-description');
    description.textContent = fast ? 'まもなく移動します。' : '扉の向こうの世界へ。無音でも移動できます。';
    panel.style.setProperty('--cg-door-duration', fast ? '0ms' : `${config.durationMs - 600}ms`);
    document.body.style.overflow = 'hidden';
    panel.showModal();
    panel.querySelector('.cg-door-skip').focus();
    const reveal = () => {
      if (active !== state || state.started) return;
      state.started = true;
      // Force a closed-door frame before transition; this works after BFCache too.
      void panel.offsetWidth;
      later(() => panel.classList.add('cg-door-opening'), fast ? 0 : 160, state);
      later(() => finish(true), fast ? config.shortDurationMs : config.durationMs, state);
    };
    const blockedByMusic = musicIsActive();
    const shouldPlay = sound && config.doorAudio && !fast && !blockedByMusic;
    if (!shouldPlay) {
      if (blockedByMusic && sound) description.textContent = '楽曲再生との重複を避け、扉を無音で開きます。';
      reveal(); return;
    }
    // Web Audio plays only this approved SFX. Existing music hooks stay untouched.
    // Resume is invoked synchronously inside the user gesture (including Safari).
    let expired = false;
    const fallback = message => {
      if (active !== state || state.started) return;
      expired = true; stopSound();
      state.timers.forEach(clearTimeout); state.timers = [];
      description.textContent = message; reveal();
    };
    later(() => fallback('音源の読み込みを待たず、無音で移動します。'), 500, state);
    try {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) { fallback('効果音に対応していないため、無音で移動します。'); return; }
      audioContext ||= new Context();
      const resumed = audioContext.resume();
      loadController = new AbortController();
      const sourceUrl = new URL(config.doorAudio, root);
      Promise.all([
        resumed,
        fetch(sourceUrl, {signal:loadController.signal})
          .then(response => { if (!response.ok) throw new Error('SFX unavailable'); return response.arrayBuffer(); })
          .then(bytes => audioContext.decodeAudioData(bytes))
      ]).then(([,buffer]) => {
        if (active !== state || expired) return;
        if (audioContext.state !== 'running') { fallback('効果音を再生できないため、無音で移動します。'); return; }
        if (musicIsActive() || !sound) { fallback('楽曲と重ならないよう、扉を無音で開きます。'); return; }
        loadController = null;
        gainNode = audioContext.createGain(); gainNode.gain.value = volume;
        audioSource = audioContext.createBufferSource(); audioSource.buffer = buffer;
        audioSource.connect(gainNode); gainNode.connect(audioContext.destination);
        state.timers.forEach(clearTimeout); state.timers = [];
        // Sound and the door share this start point; visual opening begins 160ms later.
        audioSource.start(audioContext.currentTime);
        description.textContent = '重低音Ver.2とともに、扉を開いています。';
        reveal();
      }).catch(() => fallback('効果音を再生できないため、無音で移動します。'));
    } catch { fallback('効果音を再生できないため、無音で移動します。'); }
  }

  const artistPaths = new Map(Object.entries(config.artists).map(([slug, artist]) => [new URL(`artists/${slug}/`,root).pathname,artist]));
  document.addEventListener('click', event => {
    const link = event.target.closest?.('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    let destination;
    try { destination = new URL(link.href); } catch { return; }
    if (destination.origin !== location.origin || destination.pathname === location.pathname) return;
    const returning = link.hasAttribute('data-cg-return');
    const artist = artistPaths.get(destination.pathname.replace(/index\.html$/, '').replace(/\/?$/, '/'));
    if (!artist && !returning) return;
    event.preventDefault();
    start(destination,artist,link,returning);
  });
  addEventListener('pagehide', () => finish(false));
  addEventListener('pageshow', () => finish(false));
  addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      document.querySelector('.cg-settings[open]')?.removeAttribute('open');
      const menu = document.querySelector('.mobile-menu[open]');
      if (menu) { menu.removeAttribute('open'); menu.querySelector('summary')?.focus(); }
    }
  });
  // Suppress interference even if media starts after the gate click.
  document.addEventListener('play', () => stopSound(), true);
})();
