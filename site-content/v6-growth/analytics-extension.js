  // Growth actions are counted once here, before the legacy generic listener.
  // Never send email addresses, email bodies, free text or full destination URLs.
  const reportGrowth = anchor => {
    const action = anchor.dataset.growthAction;
    const names = {
      streaming: "streaming_click", sticker: "line_sticker_click",
      "production-contact": "music_production_click", "production-visit": "music_production_click",
    };
    if (!Object.hasOwn(names, action)) return false;
    const cleanId = value => /^[a-z0-9_-]{1,100}$/.test(value || "") ? value : "";
    send(names[action], {
      release_slug: cleanId(anchor.dataset.releaseSlug),
      artist_slug: cleanId(anchor.dataset.artistSlug),
      service: cleanId(anchor.dataset.service),
      product_id: cleanId(anchor.dataset.productId),
      interaction: action === "production-contact" ? "consultation" : action === "production-visit" ? "visit" : "outbound",
      source_section: cleanId(anchor.closest("[data-source-section]")?.dataset.sourceSection) || "page",
    });
    return true;
  };
