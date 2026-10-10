/* Cinematic static-site portal. Formal audio and unadopted candidate stay separate. */
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
  const save = (key,value) => { try { localStorage.setItem(`suzuka.cg.${key}`,String(value)); } catch { /* Storage is optional. */ } };
  const audioPath = config.doorAudio || config.candidatePlaybackAudio || config.candidateAudio;
  const isCandidate = !config.doorAudio && Boolean(config.candidateAudio);
  let sound = Boolean(audioPath) && read('sound') === 'on';
  let short = read('short') === 'true';
  // Fixed safe gain; legacy slider preferences cannot raise the sound level.
  const volume = Math.max(0,Math.min(.24,Number(config.defaultVolume) || 0));
  let audioContext = null, audioSource = null, gainNode = null, envelopeNode = null, loadController = null;
  let active = null, dialog = null, toneFilter = null;
  function stopSound() {
    loadController?.abort(); loadController = null;
    if (audioSource) { try { audioSource.stop(); } catch { /* Already ended. */ } audioSource.disconnect(); audioSource = null; }
    toneFilter?.disconnect(); toneFilter = null; gainNode?.disconnect(); gainNode = null; envelopeNode?.disconnect(); envelopeNode = null;
  }
  const soundButton = document.querySelector('[data-cg-sound]');
  function reflect() {
    if (soundButton) {
      soundButton.disabled = !audioPath;
      soundButton.textContent = audioPath ? `効果音 ${sound ? 'ON' : 'OFF'}` : '効果音 OFF';
      soundButton.setAttribute('aria-pressed',String(sound));
    }
    if (dialog) {
      const mute = dialog.querySelector('[data-cg-dialog-sound]');
      mute.disabled = !audioPath; mute.textContent = audioPath ? `効果音 ${sound ? 'ON' : 'OFF'}` : '効果音 OFF'; mute.setAttribute('aria-pressed',String(sound));
    }
  }
  reflect();
  function imageFallback(image) {
    if (!(image instanceof HTMLImageElement) || !image.closest('.cg-scene,.cg-door-beyond,.cg-official-inset,.cg-arrival')) return;
    if (!image.dataset.cgFallback) {
      image.dataset.cgFallback = 'true';
      image.closest('picture')?.querySelectorAll('source').forEach(source => source.remove());
      image.removeAttribute('srcset');
      if (image.getAttribute('src')) image.src = image.getAttribute('src');
    } else image.style.opacity = '0';
  }
  document.addEventListener('error',event => imageFallback(event.target),true);
  document.querySelectorAll('.cg-scene img,.cg-official-inset img').forEach(image => { if (image.complete && !image.naturalWidth) imageFallback(image); });
  function toggleSound() {
    if (!audioPath) return;
    sound = !sound; save('sound',sound ? 'on' : 'off');
    if (!sound) stopSound();
    if (active?.started) dialog.querySelector('#cg-door-description').textContent = sound ? '音声ONは次の扉から適用します。' : '効果音OFF。扉は無音で進みます。';
    reflect();
  }
  soundButton?.addEventListener('click',toggleSound);
  addEventListener('storage',event => {
    if (!event.key?.startsWith('suzuka.cg.')) return;
    sound = Boolean(audioPath) && read('sound') === 'on'; short = read('short') === 'true';
    if (!sound) stopSound(); reflect();
  });
  const musicIsActive = () => [...document.querySelectorAll('audio,video')].some(media => !media.paused && !media.ended)
    || Boolean(document.querySelector('iframe[src*="youtube"],iframe[src*="vimeo"],[data-player-state="playing"],[data-music-playing="true"]'));
  const imageUrl = (name,extension) => new URL(`assets/cinema/${name}.${extension}`,root).href;
  function setWorld(picture,background) {
    const source = picture.querySelector('source');
    const image = picture.querySelector('img');
    // Same art direction and responsive selection as the destination hero.
    picture.querySelectorAll('source').forEach(item => item.remove());
    for (const format of ['avif','webp']) {
      const mobile = document.createElement('source'); mobile.media = '(max-width:640px)'; mobile.type = `image/${format}`;
      mobile.srcset = imageUrl(`${background}-mobile`,format); picture.insertBefore(mobile,image);
    }
    const wide = source || document.createElement('source'); wide.removeAttribute('media'); wide.type = 'image/avif'; wide.sizes = '100vw';
    wide.srcset = [768,1280,1600].map(size => `${imageUrl(`${background}-${size}`,'avif')} ${size}w`).join(',');
    picture.insertBefore(wide,image); image.src = imageUrl(`${background}-1600`,'webp');
    image.removeAttribute('data-cg-fallback'); image.style.opacity = ''; image.fetchPriority = 'high';
  }
  // A consumed, path-bound, short-lived arrival record bridges two static documents.
  // Content remains visible if storage or either image fails.
  function arrival() {
    const record = window.__cgArrival; delete window.__cgArrival;
    if (!record) return;
    const valid = record.background === config.cinema.home || Object.values(config.artists).some(a => a.background === record.background && a.realm === record.realm);
    if (!valid) { delete document.documentElement.dataset.cgArrival; return; }
    const cover = document.createElement('div'); cover.className = `cg-arrival${record.realm === 'infernal' ? ' cg-infernal' : ''}`;
    cover.style.setProperty('--gate-paper',Object.values(config.artists).find(a => a.background === record.background)?.tint || '#fcf9ef');
    cover.setAttribute('aria-hidden','true'); cover.innerHTML = '<picture><img alt=""></picture><div class="cg-door-distance"></div><div class="cg-arrival-mist cg-atmospheric-veil"></div>';
    cover.style.setProperty('--cg-arrival-ms',`${config.arrivalMs}ms`);
    setWorld(cover.querySelector('picture'),record.background); document.body.append(cover);
    const hero = document.querySelector('.explorer-hero .cg-scene img,.cg-home-hero .cg-scene img');
    const decode = img => img?.decode?.().catch(() => {}) || Promise.resolve();
    let done = false;
    const reveal = () => {
      if (done) return; done = true;
      delete document.documentElement.dataset.cgArrival;
      if (reduced.matches || record.fast) { cover.remove(); return; }
      cover.classList.add('cg-arrival-reveal');
      setTimeout(() => cover.remove(),config.arrivalMs + 80);
    };
    Promise.all([decode(hero),decode(cover.querySelector('img'))]).then(reveal);
    setTimeout(reveal,1200);
    addEventListener('pagehide',() => cover.remove(),{once:true});
  }
  arrival();

  function getDialog() {
    if (dialog) return dialog;
    dialog = document.createElement('dialog');
    if (typeof dialog.showModal !== 'function') return null;
    dialog.className = 'cg-door-dialog'; dialog.setAttribute('aria-labelledby','cg-door-title'); dialog.setAttribute('aria-describedby','cg-door-description');
    dialog.innerHTML = '<div class="cg-door-view" aria-hidden="true"><picture class="cg-door-beyond"><source type="image/avif"><img alt="" decoding="async"></picture><div class="cg-door-distance"></div><div class="cg-door-portal"><div class="cg-door-leaves"><div class="cg-door-leaf cg-door-left"></div><div class="cg-door-leaf cg-door-right"></div></div><img class="cg-door-frame" alt="" decoding="async"><div class="cg-door-sigil"></div><div class="cg-door-spill"></div></div><div class="cg-door-near-mist cg-mist-left"></div><div class="cg-door-near-mist cg-mist-right"></div><div class="cg-door-wash cg-atmospheric-veil"></div></div><div class="cg-door-status"><p data-cg-door-realm></p><h2 id="cg-door-title"></h2><small id="cg-door-description" aria-live="polite"></small></div><button class="cg-door-skip" type="button">スキップして進む ↗</button><button class="cg-door-cancel" type="button">キャンセル / Esc</button><button class="cg-door-mute" type="button" data-cg-dialog-sound aria-pressed="false"></button>';
    document.body.append(dialog);
    dialog.querySelector('[data-cg-dialog-sound]').addEventListener('click',toggleSound);
    reflect();
    dialog.querySelector('.cg-door-skip').addEventListener('click',() => finish(true,true));
    dialog.querySelector('.cg-door-cancel').addEventListener('click',() => finish(false));
    dialog.addEventListener('cancel',event => { event.preventDefault(); finish(false); });
    return dialog;
  }
  function later(callback,ms,state) {
    const id = setTimeout(() => { if (active === state) callback(); },ms); state.timers.push(id);
  }
  function cleanup(state) {
    state.timers.forEach(clearTimeout); cancelAnimationFrame(state.raf); stopSound(); state.navigation.abort();
    dialog?.close(); dialog?.classList.remove('cg-door-opening'); document.body.style.overflow = state.overflow;
    state.trigger?.focus({preventScroll:true});
  }
  function navigationError(state) {
    if (active !== state) return;
    active = null; cleanup(state);
    try { sessionStorage.removeItem('suzuka.cg.arrival'); } catch { /* Optional. */ }
    document.querySelector('.cg-nav-error')?.remove();
    const alert = document.createElement('div'); alert.className = 'cg-nav-error'; alert.setAttribute('role','alert');
    alert.innerHTML = '<p>移動先を読み込めませんでした。接続を確認して、もう一度扉を選択してください。</p><button type="button">閉じる</button>';
    alert.querySelector('button').addEventListener('click',() => { alert.remove(); state.trigger?.focus({preventScroll:true}); });
    document.body.append(alert); alert.querySelector('button').focus();
  }
  async function finish(navigate,skipped = false) {
    const state = active; if (!state) return;
    if (!navigate) { active = null; cleanup(state); return; }
    if (state.navigating) return;
    state.navigating = true; cancelAnimationFrame(state.raf); stopSound();
    dialog.querySelector('#cg-door-description').textContent = '移動先を確認しています。';
    const ready = await state.ready;
    if (active !== state) return;
    if (!ready) { navigationError(state); return; }
    try {
      sessionStorage.setItem('suzuka.cg.arrival',JSON.stringify({path:state.destination.pathname,background:state.background,realm:state.realm,time:Date.now(),fast:state.fast || skipped}));
    } catch { /* Static hero still renders normally. */ }
    try {
      // Keep the last mist frame on screen until pagehide; never expose the source.
      location.assign(state.destination.href);
      later(() => navigationError(state),3500,state);
    } catch { navigationError(state); }
  }
  const clamp = value => Math.max(0,Math.min(1,value));
  const smooth = value => { const t=clamp(value); return t*t*(3-2*t); };
  const inertia = value => { const t=clamp(value); return t*t*t*(10+t*(-15+6*t)); };
  function animate(state) {
    const phase = config.timeline, total = config.durationMs;
    const frame = now => {
      if (active !== state || state.navigating) return;
      const t = now - state.epoch;
      const approach = smooth(t/phase.approachMs);
      const glow = smooth((t-phase.approachMs)/(phase.glowMs-phase.approachMs));
      const opening = inertia((t-phase.glowMs)/(phase.openMs-phase.glowMs));
      const reveal = smooth((t-phase.openMs)/(phase.revealMs-phase.openMs));
      // The camera starts with a measured drift, then crosses the near plane with increasing velocity.
      const entry = clamp((t-phase.revealMs)/(phase.entryMs-phase.revealMs));
      const flight = .08*entry + .92*entry*entry*entry;
      const wash = smooth((t-phase.entryMs)/(total-phase.entryMs));
      const set = (name,value) => dialog.style.setProperty(`--cg-${name}`,String(value));
      set('approach',approach); set('glow',glow); set('open',opening); set('reveal',reveal); set('flight',flight); set('travel',entry); set('wash',wash);
      dialog.dataset.phase = t < phase.approachMs ? 'approach' : t < phase.glowMs ? 'glow' : t < phase.openMs ? 'opening' : t < phase.revealMs ? 'world' : t < phase.entryMs ? 'entry' : 'mist';
      if (t >= phase.glowMs) dialog.classList.add('cg-door-opening');
      if (t >= total) { finish(true); return; }
      state.raf = requestAnimationFrame(frame);
    };
    state.raf = requestAnimationFrame(frame);
  }
  function start(destination,artist,trigger,returning) {
    if (active) return;
    const panel = getDialog(); if (!panel) { location.assign(destination.href); return; }
    document.querySelector('.cg-nav-error')?.remove();
    const fast = Boolean(returning || short || reduced.matches || navigator.connection?.saveData);
    const realm = artist?.realm === 'infernal' ? 'infernal' : 'celestial';
    const background = returning ? config.cinema.home : artist.background;
    const state = {destination,trigger,background,realm,fast,timers:[],overflow:document.body.style.overflow,started:false,navigating:false,navigation:new AbortController()};
    active = state;
    // Check the real target before leaving. Failure does not strand the user in a modal.
    state.ready = new Promise(resolve => {
      const timeout = setTimeout(() => { state.navigation.abort(); resolve(false); },5000); state.timers.push(timeout);
      fetch(destination.href,{signal:state.navigation.signal,headers:{Accept:'text/html'}})
        .then(response => response.ok && /text\/html/i.test(response.headers.get('content-type') || '') ? response.text() : '')
        .then(text => { clearTimeout(timeout); resolve(/<body[\s>]/i.test(text)); })
        .catch(() => { clearTimeout(timeout); resolve(false); });
    });
    panel.className = `cg-door-dialog${realm === 'infernal' ? ' cg-infernal' : ''}${fast ? ' cg-door-fast' : ''}${returning ? ' cg-returning' : ''}`;
    for (const name of ['approach','glow','open','reveal','flight','travel','wash']) panel.style.setProperty(`--cg-${name}`,'0');
    panel.dataset.phase = 'loading';
    const emblem = document.createElementNS('http://www.w3.org/2000/svg','svg'); emblem.setAttribute('viewBox','0 0 64 64'); emblem.setAttribute('aria-hidden','true');
    const use = document.createElementNS('http://www.w3.org/2000/svg','use'); use.setAttribute('href',new URL(`assets/celestial-emblems.svg#${artist?.emblem || 'asteria'}`,root).href); emblem.append(use); panel.querySelector('.cg-door-sigil').replaceChildren(emblem);
    panel.style.setProperty('--gate-accent',realm === 'infernal' ? '#ed3c44' : (artist?.accent || '#806432'));
    panel.style.setProperty('--gate-paper',realm === 'infernal' ? '#19080d' : (artist?.tint || '#fcf9ef'));
    const kind = realm === 'infernal' ? 'infernal' : 'celestial';
    setWorld(panel.querySelector('.cg-door-beyond'),background);
    panel.querySelector('.cg-door-frame').src = imageUrl(`frame-${kind}-${fast ? 480 : 960}`,'webp');
    const textureUrl = imageUrl(`door-${kind}-${fast ? 480 : 960}`,'webp');
    panel.style.setProperty('--gate-texture',`url("${textureUrl}")`);
    const texture = new Image(); texture.src = textureUrl;
    state.assetsReady = fast ? Promise.resolve() : Promise.race([
      Promise.all([panel.querySelector('.cg-door-beyond img'),panel.querySelector('.cg-door-frame'),texture].map(img => img.decode().catch(() => {}))),
      new Promise(resolve => later(resolve,400,state))
    ]);
    panel.querySelector('#cg-door-title').textContent = returning ? '天界へ' : artist.name;
    panel.querySelector('[data-cg-door-realm]').textContent = returning ? 'CELESTIAL GATE' : `${artist.label} / ${realm === 'infernal' ? 'INFERNAL' : 'CELESTIAL'} REALM`;
    const description = panel.querySelector('#cg-door-description'); description.textContent = fast ? 'まもなく移動します。' : '扉の奥へ、音楽の世界へ。';
    document.body.style.overflow = 'hidden'; panel.showModal(); panel.querySelector('.cg-door-skip').focus();
    const begin = async buffer => {
      if (active !== state || state.started) return;
      state.started = true; await state.assetsReady;
      if (active !== state || state.navigating) return;
      state.epoch = performance.now(); panel.dataset.phase = 'approach';
      if (buffer && sound && !musicIsActive()) {
        try {
          gainNode = audioContext.createGain(); gainNode.gain.value = volume;
          audioSource = audioContext.createBufferSource(); audioSource.buffer = buffer; envelopeNode = audioContext.createGain(); audioSource.connect(envelopeNode);
          // Reuse the exact V4 candidate. NOX receives gentle darkening, never a replacement or adopted label.
          if (realm === 'infernal' && isCandidate && typeof audioContext.createBiquadFilter === 'function') {
            toneFilter = audioContext.createBiquadFilter(); toneFilter.type = 'lowpass'; toneFilter.frequency.value = 720; toneFilter.Q.value = .45;
            envelopeNode.connect(toneFilter); toneFilter.connect(gainNode);
          } else envelopeNode.connect(gainNode); gainNode.connect(audioContext.destination);
          const when = audioContext.currentTime + config.timeline.glowMs/1000;
          // Independent envelope preserves the fixed safe gain and softens any formal file's attack/tail.
          const envelope = envelopeNode.gain; envelope.value = 0;
          if (typeof envelope.setValueAtTime === 'function') {
            envelope.setValueAtTime(0,when); envelope.linearRampToValueAtTime(1,when+.08);
            const end = when + Math.min(buffer.duration,(config.durationMs-config.timeline.glowMs)/1000);
            envelope.setValueAtTime(1,Math.max(when+.08,end-.15)); envelope.linearRampToValueAtTime(0,end);
          } else envelope.value = 1;
          audioSource.start(when);
          description.textContent = '効果音とともに扉を開きます。';
        } catch { stopSound(); description.textContent = '効果音を再生できないため、無音で移動します。'; }
      }
      if (fast) { panel.dataset.phase = 'short'; later(() => finish(true),config.shortDurationMs,state); }
      else animate(state);
    };
    const blocked = musicIsActive();
    if (!sound || !audioPath || fast || blocked) {
      if (blocked && sound) description.textContent = '楽曲再生との重複を避け、無音で移動します。';
      begin(null); return;
    }
    // Resume synchronously in the user gesture; bounded decode shares the animation clock.
    let expired = false;
    const fallback = () => {
      if (active !== state || state.started) return;
      expired = true; stopSound(); description.textContent = '効果音を読み込めないため、無音で移動します。'; begin(null);
    };
    later(fallback,500,state);
    try {
      const Context = window.AudioContext || window.webkitAudioContext;
      if (!Context) { fallback(); return; }
      audioContext ||= new Context(); const resumed = audioContext.resume();
      loadController = new AbortController();
      Promise.all([resumed,fetch(new URL(audioPath,root),{signal:loadController.signal})
        .then(response => { if (!response.ok) throw new Error('SFX unavailable'); return response.arrayBuffer(); })
        .then(bytes => audioContext.decodeAudioData(bytes))])
        .then(([,buffer]) => {
          if (active !== state || expired || state.started) return;
          if (audioContext.state !== 'running') { fallback(); return; }
          loadController = null; begin(buffer);
        }).catch(fallback);
    } catch { fallback(); }
  }
  const artistPaths = new Map(Object.entries(config.artists).map(([slug,artist]) => [new URL(`artists/${slug}/`,root).pathname,artist]));
  document.addEventListener('click',event => {
    const link = event.target.closest?.('a[href]');
    if (!link || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;
    let destination; try { destination = new URL(link.href); } catch { return; }
    if (destination.origin !== location.origin || destination.pathname === location.pathname) return;
    const returning = link.hasAttribute('data-cg-return');
    const artist = artistPaths.get(destination.pathname.replace(/index\.html$/,'').replace(/\/?$/,'/'));
    if (!artist && !returning) return;
    event.preventDefault(); start(destination,artist,link,returning);
  });
  addEventListener('pagehide',() => finish(false)); addEventListener('pageshow',() => finish(false));
  addEventListener('keydown',event => {
    if (event.key === 'Escape') {
      document.querySelector('.cg-settings[open]')?.removeAttribute('open');
      const menu = document.querySelector('.mobile-menu[open]'); if (menu) { menu.removeAttribute('open'); menu.querySelector('summary')?.focus(); }
    }
  });
  document.addEventListener('play',stopSound,true);
})();
