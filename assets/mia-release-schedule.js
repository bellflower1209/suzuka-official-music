(() => {
  'use strict';
  const today = () => new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(new Date());
  const update = () => document.querySelectorAll('[data-activity-date]').forEach(item => {
    const status = item.querySelector('[data-activity-status]');
    const date = item.dataset.activityDate;
    const kind = item.dataset.activityKind;
    if (!status || !date) return;
    if (kind === 'KARAOKE / JOYSOUND') status.textContent = today() >= date ? kind : `${kind} · COMING ${date.slice(5).replace('-', '.')}`;
    else if (kind === 'NEW RELEASE') status.textContent = today() >= date ? 'NOW STREAMING' : `${kind} · COMING ${date.slice(5).replace('-', '.')}`;
    else status.textContent = kind;
  });
  update();
  setInterval(update, 30000);
  document.addEventListener('visibilitychange', update);
})();
