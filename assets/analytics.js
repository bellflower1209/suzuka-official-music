(() => {
  const safePageUrl = window.location.origin + window.location.pathname;
  const send = (name, parameters = {}) => {
    if (typeof window.gtag !== "function") return;
    window.gtag("event", name, {...parameters, page_location: safePageUrl});
  };
  const clean = value => String(value || "").replace(/\s+/g, " ").trim().slice(0, 300);
  const safeLink = value => {
    const url = new URL(value, location.href);
    if (url.origin === location.origin) return url.origin + url.pathname;
    return url.href;
  };
  const pageRelease = location.pathname.match(/\/releases\/([^/]+)\/?$/)?.[1] || "";
  const pageArtist = location.pathname.match(/\/artists\/([^/]+)\/?$/)?.[1] || "";
  const schemas = [];
  document.querySelectorAll('script[type="application/ld+json"]').forEach(node => {
    try {
      const walk = value => {
        if (!value || typeof value !== "object") return;
        if (Array.isArray(value)) return value.forEach(walk);
        schemas.push(value);
        Object.values(value).forEach(walk);
      };
      walk(JSON.parse(node.textContent));
    } catch (_) {}
  });
  const recording = schemas.find(item => {
    const type = item["@type"];
    return type === "MusicRecording" || (Array.isArray(type) && type.includes("MusicRecording"));
  }) || {};
  const schemaArtist = clean(recording.byArtist?.name || recording.byArtist?.[0]?.name);
  const schemaTitle = clean(recording.name);
  const contextFor = anchor => anchor.closest(
    "[data-weekly-pick],.explorer-release-card,.explore-card,.release-card,.timeline-item,.gallery-card,article,section"
  ) || document;
  const detailsFor = anchor => {
    const context = contextFor(anchor);
    const linkedPath = new URL(anchor.href, location.href).pathname;
    const releaseLink = context.querySelector('a[href*="/releases/"]');
    const releaseUrl = new URL(releaseLink?.href || location.href, location.href);
    const slug = releaseUrl.pathname.match(/\/releases\/([^/]+)\/?/)?.[1] || pageRelease;
    const title = clean(
      context.querySelector("[data-pick-title],h1,h2,h3")?.textContent || schemaTitle || document.querySelector("h1")?.textContent
    );
    const artist = clean(
      context.querySelector("[data-pick-artist],.release-card-artist,.artist-name")?.textContent ||
      schemaArtist || (pageArtist ? document.querySelector("h1")?.textContent : "")
    );
    return {
      work_title: title,
      release_slug: clean(slug),
      artist_name: artist,
      link_url: safeLink(anchor.href),
      content_type: clean(
        anchor.closest("[data-weekly-pick]") ? "weekly_pick" :
        linkedPath.includes("/releases/") ? "release" :
        linkedPath.includes("/news/") ? "news" :
        linkedPath.includes("/gallery/") ? "gallery" :
        linkedPath.includes("/wiki/") ? "wiki" :
        linkedPath.includes("/universe/") ? "universe" :
        linkedPath.includes("/community/") ? "community" :
        linkedPath.includes("/playlists/") ? "playlist" : "link"
      ),
    };
  };
  document.addEventListener("click", event => {
    const anchor = event.target.closest("a[href]");
    if (!anchor) return;
    const url = new URL(anchor.href, location.href);
    const path = url.pathname;
    const host = url.hostname.replace(/^www\./, "");
    const isYoutube = host === "youtube.com" || host === "youtu.be";
    const youtubeChannel = isYoutube &&
      (path.includes("/@suzuka1209") || path.includes("/channel/UCVde75yhByGQMu3SkO-fzrA"));
    const youtubeVideo = isYoutube && !youtubeChannel &&
      (path === "/watch" || host === "youtu.be" || path.includes("/shorts/"));
    const details = detailsFor(anchor);
    if (anchor.closest("[data-weekly-pick]")) send("weekly_pick_click", details);
    if (youtubeChannel) send("youtube_click", details);
    else if (youtubeVideo && path.includes("/shorts/")) send("shorts_click", details);
    else if (youtubeVideo) send("official_mv_click", details);
    if (url.hostname.includes("instagram.com")) send("instagram_click", details);
    if (url.origin === location.origin && /\/releases\/[^/]+\/?$/.test(path)) send("release_click", details);
    if (url.origin === location.origin && /\/playlists\/(?:[^/]+\/?)?$/.test(path)) send("playlist_click", details);
    if (url.origin === location.origin && /\/artists\/[^/]+\/?$/.test(path)) send("artist_click", details);
    if (url.origin === location.origin && /\/news\/[^/]+\/?$/.test(path)) send("news_click", details);
    if (url.origin === location.origin && /\/gallery\/(?:[^/]+\/?)?$/.test(path)) send("gallery_click", details);
    if (url.origin === location.origin && /\/wiki\/(?:[^/]+\/?)?$/.test(path)) send("wiki_click", details);
    if (url.origin === location.origin && /\/universe\/?$/.test(path)) send("universe_click", details);
    if (url.origin === location.origin && /\/community\/?$/.test(path)) send("community_click", details);
    if (url.origin !== location.origin) send("outbound_click", details);
  });
  const form = document.querySelector("[data-search-form]");
  if (form) {
    let timer = 0, lastSignature = "";
    const reportSearch = () => {
      clearTimeout(timer);
      timer = window.setTimeout(() => {
        const data = Object.fromEntries(new FormData(form));
        const active = Object.values(data).filter(Boolean).length;
        const signature = Object.keys(data).filter(key => data[key]).sort().join("|") + ":" + active;
        if (!active || signature === lastSignature) return;
        lastSignature = signature;
        send("search_use", {
          has_search_query: Boolean(data.q),
          active_filter_count: active,
          result_count: Number(document.querySelector("[data-search-count]")?.textContent || 0),
        });
      }, 800);
    };
    form.addEventListener("input", reportSearch);
    form.addEventListener("change", reportSearch);
    form.addEventListener("submit", reportSearch);
  }
})();
