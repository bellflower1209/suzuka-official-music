(() => {
  'use strict';
  const todayInTokyo = (now) => new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Asia/Tokyo', year: 'numeric', month: '2-digit', day: '2-digit'
  }).format(now);
  const update = () => {
    const today = todayInTokyo(new Date());
    document.querySelectorAll('[data-streaming-date]').forEach(node => {
      const release = node.dataset.streamingDate;
      const previousDay = new Date(`${release}T00:00:00+09:00`);
      previousDay.setTime(previousDay.getTime() - 86400000);
      node.textContent = today >= release ? 'NOW STREAMING'
        : today === todayInTokyo(previousDay) ? '明日リリース' : 'COMING SOON';
    });
  };
  update();
  setInterval(update, 30000);
  document.addEventListener('visibilitychange', update);
})();
