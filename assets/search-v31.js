(() => {
  const form=document.querySelector('[data-search-form]'), root=document.querySelector('[data-v31-search-results]');
  if(!form||!root)return;
  const norm=v=>String(v||'').normalize('NFKC').toLocaleLowerCase('ja').replace(/\s+/g,'').trim();
  const esc=v=>String(v||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  fetch('../assets/data/search-v31.json').then(r=>r.json()).then(data=>{
    const render=()=>{const q=norm(form.elements.q.value);const docs=q?data.documents.filter(d=>norm([d.title,d.description,...d.keywords].join(' ')).includes(q)):[];
      root.innerHTML=docs.map(d=>`<article class="v31-search-document"><small>${esc(d.type)}</small><h3><a href="../${esc(d.url)}">${esc(d.title)}</a></h3><p>${esc(d.description)}</p></article>`).join('')||(q?'<p>該当するNews・Wiki・公式歌詞はありません。</p>':'<p>検索語を入力すると関連コンテンツを表示します。</p>');};
    form.addEventListener('input',render);form.addEventListener('change',render);render();
  }).catch(()=>{root.textContent='検索データを読み込めませんでした。';});
})();
