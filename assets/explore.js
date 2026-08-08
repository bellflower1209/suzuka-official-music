(() => {
  const catalogUrl = document.documentElement.dataset.catalogUrl;
  if (!catalogUrl) return;
  const base = document.documentElement.dataset.siteBase || "/";
  const normalize = value => String(value || "").normalize("NFKC").toLocaleLowerCase("ja").replace(/\s+/g, "").trim();
  const esc = value => String(value || "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const link = path => `${base}${String(path || "").replace(/^\/+/, "")}`;
  const card = item => `<article class="explore-card"><img src="${link(item.coverImage)}" alt="${esc(item.coverAlt)}" width="1280" height="720" loading="lazy"><div class="explore-card-copy"><time datetime="${item.releaseDate}">${esc(item.releaseDate.replaceAll("-","."))}</time><h2>${esc(item.displayTitle)}</h2><p>${esc(item.artist)}</p><div class="explore-tags">${item.genres.map(g=>`<span class="explore-tag">${esc(g)}</span>`).join("")}</div><div class="explore-actions"><a href="${link(item.releaseUrl)}">作品ページ</a><a href="${esc(item.youtubeUrl)}" target="_blank" rel="noopener noreferrer">公式MV ↗</a>${item.newsUrl?`<a href="${link(item.newsUrl)}">News</a>`:""}</div></div></article>`;
  fetch(catalogUrl).then(r => {
    if (!r.ok) throw new Error(`catalog HTTP ${r.status}`);
    return r.json();
  }).then(data => {
    const published = data.releases.filter(item => item.status === "published");
    const weekly = document.querySelector("[data-weekly-pick]");
    if (weekly) {
      const eligible = published.filter(i => i.coverImage && i.youtubeUrl && i.recommendationWeight > 0);
      const now = new Date();
      const thursday = new Date(Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate()));
      thursday.setUTCDate(thursday.getUTCDate()+4-(thursday.getUTCDay()||7));
      const yearStart = new Date(Date.UTC(thursday.getUTCFullYear(),0,1));
      const week = Math.ceil((((thursday-yearStart)/86400000)+1)/7);
      const pool = [...eligible].sort((a,b)=>a.artistSlug.localeCompare(b.artistSlug)||a.slug.localeCompare(b.slug));
      const seed = `${thursday.getUTCFullYear()}-${week}`;
      let hash = 2166136261;
      for (const ch of seed) hash = Math.imul(hash ^ ch.charCodeAt(0), 16777619);
      const item = pool[Math.abs(hash) % pool.length];
      if (item) {
        weekly.querySelector("img").src=link(item.coverImage); weekly.querySelector("img").alt=item.coverAlt;
        weekly.querySelector("[data-pick-title]").textContent=item.displayTitle;
        weekly.querySelector("[data-pick-artist]").textContent=item.artist;
        weekly.querySelector("[data-pick-description]").textContent=item.description;
        weekly.querySelector("[data-pick-genres]").textContent=item.genres.join(" · ");
        weekly.querySelector("[data-pick-release]").href=link(item.releaseUrl);
        weekly.querySelector("[data-pick-youtube]").href=item.youtubeUrl;
        weekly.querySelector("[data-pick-artist-link]").href=link(`artists/${item.artistSlug}/`);
        weekly.querySelector("[data-pick-lyrics]").href=item.lyricsAvailable?link(`lyrics/${item.slug}/`):link("lyrics/");
        const news=weekly.querySelector("[data-pick-news]"); if(item.newsUrl){news.href=link(item.newsUrl)}else{news.hidden=true}
      }
    }
    const form = document.querySelector("[data-search-form]");
    if (!form) return;
    const q=form.elements.q, artist=form.elements.artist, genre=form.elements.genre, theme=form.elements.theme, year=form.elements.year, type=form.elements.type, sort=form.elements.sort;
    const result=document.querySelector("[data-search-results]"), count=document.querySelector("[data-search-count]"), empty=document.querySelector("[data-search-empty]");
    [...new Map(published.map(i=>[i.artistSlug,i.artist])).entries()].sort((a,b)=>a[1].localeCompare(b[1],"ja")).forEach(([value,label])=>artist.add(new Option(label,value)));
    [...new Set(published.flatMap(i=>i.genres))].sort((a,b)=>a.localeCompare(b,"ja")).forEach(value=>genre.add(new Option(value,value)));
    [...new Set(published.flatMap(i=>i.themes||[]))].sort((a,b)=>a.localeCompare(b,"ja")).forEach(value=>theme.add(new Option(value,value)));
    [...new Set(published.map(i=>String(i.releaseYear)))].sort().reverse().forEach(value=>year.add(new Option(value,value)));
    [...new Set(published.map(i=>i.releaseType||"single"))].sort().forEach(value=>type.add(new Option(value,value)));
    const params=new URLSearchParams(location.search); q.value=params.get("q")||""; artist.value=params.get("artist")||""; genre.value=params.get("genre")||""; theme.value=params.get("theme")||""; year.value=params.get("year")||""; type.value=params.get("type")||""; sort.value=params.get("sort")||"newest";
    const update=({push=false}={})=>{
      const needle=normalize(q.value);
      let items=published.filter(i=>(!needle||normalize([i.title,i.displayTitle,i.artist,...(i.genres||[]),...(i.moods||[]),...(i.themes||[]),...(i.tags||[]),...(i.searchKeywords||[]),i.lyrics,i.introduction,i.description,i.releaseYear,i.releaseType].join(" ")).includes(needle))&&(!artist.value||i.artistSlugs.includes(artist.value))&&(!genre.value||i.genres.includes(genre.value))&&(!theme.value||(i.themes||[]).includes(theme.value))&&(!year.value||String(i.releaseYear)===year.value)&&(!type.value||(i.releaseType||"single")===type.value));
      items.sort((a,b)=>(sort.value==="oldest"?a.releaseDate.localeCompare(b.releaseDate):sort.value==="title"?a.title.localeCompare(b.title,"ja"):b.releaseDate.localeCompare(a.releaseDate))||a.slug.localeCompare(b.slug));
      result.innerHTML=items.map(card).join(""); empty.hidden=items.length>0; count.textContent=String(items.length);
      const next=new URLSearchParams(); if(q.value)next.set("q",q.value);if(artist.value)next.set("artist",artist.value);if(genre.value)next.set("genre",genre.value);if(theme.value)next.set("theme",theme.value);if(year.value)next.set("year",year.value);if(type.value)next.set("type",type.value);if(sort.value!=="newest")next.set("sort",sort.value);
      history[push?"pushState":"replaceState"]({},"",`${location.pathname}${next.size?`?${next}`:""}`);
    };
    form.addEventListener("input",()=>update()); form.addEventListener("change",()=>update({push:true}));
    form.addEventListener("reset",()=>setTimeout(()=>update({push:true})));
    addEventListener("popstate",()=>{const p=new URLSearchParams(location.search);q.value=p.get("q")||"";artist.value=p.get("artist")||"";genre.value=p.get("genre")||"";theme.value=p.get("theme")||"";year.value=p.get("year")||"";type.value=p.get("type")||"";sort.value=p.get("sort")||"newest";update()});
    update();
  }).catch(error => console.error("SUZUKA explore:", error));
})();
