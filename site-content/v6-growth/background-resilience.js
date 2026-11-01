/* Preview-only recovery for existing decorative images. No audio or animation changes. */
(() => {
  'use strict';
  if (window.__suzukaV6BackgroundRecoveryInstalled) return;
  window.__suzukaV6BackgroundRecoveryInstalled = true;
  const pending = new Map();
  const deadline = 6500;
  const selector = 'picture.scene > img';
  const relevant = img => img.matches(selector) && img.closest('.hero, .voyage-destination, [data-selection-scene]');
  const visible = img => {
    const box = img.getBoundingClientRect();
    return box.width > 0 && box.height > 0 && box.bottom > -200 && box.top < innerHeight + 200;
  };
  const clear = state => { clearTimeout(state.timer); state.timer = 0; };
  const assetURL = value => {
    try {
      const url = new URL(value, document.baseURI);
      return url.origin === location.origin && /^\/assets\/(cinema|baba-nova)\/[a-z0-9-]+\.(avif|webp)$/.test(url.pathname) ? url : null;
    } catch { return null; }
  };
  const retryURL = value => {
    const url = assetURL(value);
    if (!url) return value;
    url.searchParams.set('v6-background-retry', '1');
    return url.href;
  };
  function arm(img, state) {
    if (!state) return;
    clear(state);
    if (!img.isConnected || document.hidden || !visible(img) || img.complete && img.naturalWidth) return;
    if (state.finished) return;
    state.timer = setTimeout(() => recover(img, state), deadline);
  }
  function recover(img, state) {
    clear(state);
    if (!img.isConnected || document.hidden || !visible(img) || img.complete && img.naturalWidth) return;
    if (navigator.onLine === false) { img.dataset.v6BackgroundState = 'offline'; return; }
    const picture = img.parentElement;
    const avif = [...picture.querySelectorAll('source[type="image/avif"]')];
    const webp = [...picture.querySelectorAll('source[type="image/webp"]')];
    const selected = assetURL(img.currentSrc);
    // Keep the same responsive sources, orientation, dimensions and existing WebP bytes.
    // An AVIF-only request may stall even though the existing WebP is available.
    if (!state.fallback && avif.length && webp.length && (!selected || selected.pathname.endsWith('.avif'))) {
      state.fallback = true;
      img.dataset.v6BackgroundState = 'webp';
      avif.forEach(source => source.media = 'not all');
    } else if (!state.retried) {
      state.retried = true;
      img.dataset.v6BackgroundState = 'retry';
      webp.forEach(source => {
        source.srcset = source.srcset.split(',').map(item => {
          const [url, descriptor] = item.trim().split(/\s+/);
          return retryURL(url) + (descriptor ? ' ' + descriptor : '');
        }).join(', ');
      });
      img.src = retryURL(img.getAttribute('src'));
    } else {
      state.finished = true;
      img.dataset.v6BackgroundState = 'unavailable';
      return; // Never loop or reload the page. Text, links and controls remain usable.
    }
    arm(img, state);
  }
  function watch(img) {
    if (pending.has(img) || !relevant(img) || !assetURL(img.getAttribute('src'))) return;
    const state = {timer: 0, fallback: false, retried: false, finished: false};
    state.loaded = () => {
      clear(state);
      img.dataset.v6BackgroundState = img.naturalWidth ? 'ready' : 'unavailable';
    };
    state.failed = () => recover(img, state);
    img.addEventListener('load', state.loaded);
    img.addEventListener('error', state.failed);
    // Only the hero and the open destination get high priority; never preload all worlds.
    if (img.closest('.hero, dialog[open] .voyage-destination')) {
      img.loading = 'eager'; img.fetchPriority = 'high';
    }
    pending.set(img, state);
    observer?.observe(img);
    arm(img, state);
    if (img.complete && !img.naturalWidth && visible(img)) recover(img, state);
  }
  const observer = typeof IntersectionObserver === 'function' ? new IntersectionObserver(entries => {
    entries.forEach(entry => { if (entry.isIntersecting) arm(entry.target, pending.get(entry.target)); });
  }, {rootMargin: '200px'}) : null;
  function scan() {
    pending.forEach((state, img) => {
      if (img.isConnected) return;
      clear(state); observer?.unobserve(img);
      img.removeEventListener('load', state.loaded); img.removeEventListener('error', state.failed);
      pending.delete(img);
    });
    document.querySelectorAll(selector).forEach(watch);
  }
  scan();
  new MutationObserver(scan).observe(document.documentElement, {childList: true, subtree: true});
  const resume = () => { scan(); pending.forEach((state, img) => arm(img, state)); };
  window.addEventListener('online', resume);
  window.addEventListener('resize', resume);
  window.addEventListener('pageshow', resume);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) pending.forEach(clear); else resume();
  });
  window.addEventListener('pagehide', () => pending.forEach(clear));
})();
