(() => {
  'use strict';
  const button = document.getElementById('mp-copy-email');
  const status = document.getElementById('mp-copy-status');
  if (!button || !status) return;

  button.addEventListener('click', async () => {
    const address = button.dataset.email;
    if (!address) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard API unavailable');
      await navigator.clipboard.writeText(address);
      status.textContent = 'コピーしました';
    } catch (_) {
      // Some email-app browsers deny clipboard access. The visible address remains selectable.
      status.textContent = 'コピーできませんでした。表示中のアドレスを選択してください';
    }
  });
})();
