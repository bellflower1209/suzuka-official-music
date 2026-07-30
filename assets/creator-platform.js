(() => {
  const key = "suzuka-community-v1";
  const state = JSON.parse(localStorage.getItem(key) || '{"votes":{},"entries":[]}');
  const save = () => localStorage.setItem(key, JSON.stringify(state));
  const render = () => {
    const list = document.querySelector("[data-community-ranking]");
    if (!list) return;
    const rows = Object.entries(state.votes).sort((a,b)=>b[1]-a[1] || a[0].localeCompare(b[0]));
    list.innerHTML = rows.length ? rows.map(([slug,count],i)=>`<li><strong>${i+1}</strong> ${slug} <span>${count}票</span></li>`).join("") : "<li>この端末の投票はまだありません。</li>";
  };
  document.querySelectorAll("[data-community-form]").forEach(form => form.addEventListener("submit", event => {
    event.preventDefault();
    const type = form.dataset.communityForm;
    const data = Object.fromEntries(new FormData(form));
    if (type === "vote") state.votes[data.release] = (state.votes[data.release] || 0) + 1;
    state.entries.push({type, data, savedAt: new Date().toISOString()});
    save(); render();
    const output = document.querySelector(`[data-community-result="${type}"]`);
    if (output) output.textContent = "この端末に保存しました。";
    form.reset();
  }));
  render();
})();
