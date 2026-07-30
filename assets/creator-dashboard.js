(async () => {
  const root="../../", cms=await fetch(root+"assets/data/creator-cms.json").then(r=>r.json());
  const rec=await fetch(root+"assets/data/recommendations.json").then(r=>r.json());
  const set=(key,items)=>{const value=document.querySelector(`[data-dashboard="${key}"]`),list=document.querySelector(`[data-dashboard-list="${key}"]`);value.textContent=Array.isArray(items)?items.length:items; if(list&&Array.isArray(items))list.innerHTML=items.slice(0,8).map(x=>`<li>${x}</li>`).join("")};
  const releases=cms.releases, artists=cms.artists, newsSlugs=new Set(cms.news.map(x=>x.releaseSlug).filter(Boolean));
  set("published",releases.length); set("upcoming",cms.upcoming.length); set("scheduled",cms.upcoming.map(x=>x.title));
  set("mv",releases.filter(x=>!x.youtubeUrl).map(x=>x.title)); set("news",releases.filter(x=>!newsSlugs.has(x.slug)).map(x=>x.title));
  set("gallery",releases.filter(x=>!(x.galleryImages||[]).length).map(x=>x.title)); set("wiki",artists.filter(x=>!x.world).map(x=>x.name));
  set("universe",artists.filter(x=>!x.world||!x.music).map(x=>x.name)); set("image",releases.filter(x=>!x.coverImage).map(x=>x.title));
  set("seo",releases.filter(x=>!x.seo?.title||!x.seo?.description).map(x=>x.title)); set("jsonld",releases.filter(x=>x.seo?.jsonLdEnabled===false).map(x=>x.title));
  set("searchconsole",["/playlists/","/community/","/universe/","/en/"]); set("youtube",releases.filter(x=>!x.youtubeUrl).map(x=>x.title));
  set("instagram",artists.filter(x=>!x.instagramUrl).map(x=>x.name)); set("publishedat",releases.filter(x=>!x.publishedAt).map(x=>x.title));
  set("recommendations",releases.filter(x=>!rec.recommendations[x.slug]?.aiRecommended?.length).map(x=>x.title));
})().catch(error=>{document.body.dataset.dashboardError=error.message});
