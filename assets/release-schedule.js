/* Calendar days are explicitly Asia/Tokyo; UTC methods only perform day arithmetic.
   Week starts Monday, matching the static schedule and ISO Weekly Pick. */
(() => {
  'use strict';
  const DAY = 86400000;
  const jstDay = instant => new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(instant);
  const dayNumber = value => Date.parse(`${value}T00:00:00Z`) / DAY;
  const classify = (scheduledAt, instant = new Date()) => {
    const today = jstDay(instant);
    const scheduled = jstDay(new Date(scheduledAt));
    const base = dayNumber(today), target = dayNumber(scheduled);
    const weekday = (new Date(`${today}T00:00:00Z`).getUTCDay() + 6) % 7;
    const end = base + 6 - weekday;
    if (target < base) return 'awaiting-confirmation';
    if (target === base) return 'today';
    if (target <= end) return 'this-week';
    if (target <= end + 7) return 'next-week';
    if (scheduled.slice(0, 7) === today.slice(0, 7)) return 'this-month';
    return 'later';
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = { jstDay, classify };
  if (typeof document === 'undefined') return;
  const update = () => {
    const cards = [...document.querySelectorAll('.v31-schedule-group [data-release-at][data-release-slug]')];
    const now = new Date();
    cards.sort((a, b) => a.dataset.releaseAt.localeCompare(b.dataset.releaseAt) || a.dataset.releaseSlug.localeCompare(b.dataset.releaseSlug));
    for (const card of cards) {
      const destination = document.querySelector(`#${classify(card.dataset.releaseAt, now)} .v31-schedule-list`);
      if (destination) destination.append(card);
    }
    for (const id of ['today', 'this-week', 'next-week', 'this-month', 'later', 'awaiting-confirmation']) {
      const list = document.querySelector(`#${id} .v31-schedule-list`);
      if (!list) continue;
      list.querySelectorAll('.v31-empty').forEach(node => node.remove());
      if (!list.querySelector('[data-release-slug]')) {
        const empty = document.createElement('p');
        empty.className = 'v31-empty';
        empty.textContent = '現在該当する公開予定はありません。';
        list.append(empty);
      }
    }
  };
  update();
  setInterval(update, 30000);
  document.addEventListener('visibilitychange', update);
})();
