(() => {
  const script = document.currentScript;
  const siteRoot = script?.src ? new URL("../", script.src) : new URL("./", document.baseURI);
  const socialDataUrl = new URL("assets/data/social-links.json", siteRoot);
  const releaseDataUrl = new URL("assets/data/release-links.json", siteRoot);
  const route = decodeURIComponent(location.pathname.slice(siteRoot.pathname.length)).replace(/^\/+|\/+$/g, "");

  const siteUrl = (path = "") => new URL(path, siteRoot).href;
  const externalAttributes = (anchor) => {
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
  };
  const makeLink = (label, href, className = "social-action", external = false) => {
    const anchor = document.createElement("a");
    anchor.className = className;
    anchor.href = href;
    anchor.textContent = label;
    if (external) externalAttributes(anchor);
    return anchor;
  };

  document.querySelectorAll('a[target="_blank"]').forEach((anchor) => {
    const rel = new Set((anchor.rel || "").split(/\s+/).filter(Boolean));
    rel.add("noopener");
    rel.add("noreferrer");
    anchor.rel = [...rel].join(" ");
  });

  const addNavigationLinks = () => {
    document.querySelectorAll(".desktop-nav, .mobile-menu nav, .site-footer-nav").forEach((nav) => {
      if ([...nav.querySelectorAll("a")].some((anchor) => anchor.href === siteUrl("social/"))) return;
      const anchor = makeLink("Official Links", siteUrl("social/"));
      anchor.dataset.socialHubLink = "true";
      anchor.setAttribute("aria-label", "SUZUKA公式SNS・作品リンク一覧");
      nav.append(anchor);
    });
  };

  const addHomeLink = () => {
    if (route || document.querySelector("[data-home-social-link]")) return;
    const heroActions = document.querySelector(".hero-release-actions");
    if (heroActions) {
      const link = makeLink("公式リンク一覧", siteUrl("social/"), "button button-ghost");
      link.dataset.homeSocialLink = "true";
      link.setAttribute("aria-label", "YouTube・楽曲・Newsをまとめた公式リンク一覧を見る");
      heroActions.append(link);
    }
  };

  const buildShareButtons = (title, url) => {
    const block = document.createElement("div");
    block.className = "social-share";
    block.setAttribute("aria-label", "このページを共有");
    const encodedUrl = encodeURIComponent(url);
    const encodedText = encodeURIComponent(`${title}｜SUZUKA`);
    block.append(
      makeLink("Xでシェア", `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`, "social-share-button", true),
      makeLink("LINEで送る", `https://social-plugins.line.me/lineit/share?url=${encodedUrl}`, "social-share-button", true),
    );

    const nativeButton = document.createElement("button");
    nativeButton.type = "button";
    nativeButton.className = "social-share-button";
    nativeButton.textContent = "共有";
    nativeButton.addEventListener("click", async () => {
      if (navigator.share) {
        try {
          await navigator.share({ title, text: `${title}｜SUZUKA`, url });
          return;
        } catch (error) {
          if (error?.name === "AbortError") return;
        }
      }
      await copyUrl(url, status);
    });

    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.className = "social-share-button";
    copyButton.textContent = "URLをコピー";
    const status = document.createElement("span");
    status.className = "social-copy-status";
    status.setAttribute("role", "status");
    status.setAttribute("aria-live", "polite");
    copyButton.addEventListener("click", () => copyUrl(url, status));
    block.append(nativeButton, copyButton, status);
    return block;
  };

  const copyUrl = async (url, status) => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(url);
      } else {
        const field = document.createElement("textarea");
        field.value = url;
        field.setAttribute("readonly", "");
        field.style.position = "fixed";
        field.style.opacity = "0";
        document.body.append(field);
        field.select();
        document.execCommand("copy");
        field.remove();
      }
      status.textContent = "URLをコピーしました。";
    } catch {
      status.textContent = "コピーできませんでした。アドレスバーのURLをご利用ください。";
    }
  };

  const createContextSection = (release, heading, intro) => {
    const section = document.createElement("section");
    section.className = "social-context-section";
    section.setAttribute("aria-labelledby", `social-actions-${release.slug}`);
    section.innerHTML = `<div><p>OFFICIAL LINKS</p><h2 id="social-actions-${release.slug}">${heading}</h2><span>${intro}</span></div>`;
    const actions = document.createElement("div");
    actions.className = "social-context-actions";
    if (release.youtubeStatus === "published" && release.youtubeUrl) {
      actions.append(makeLink("公式MVを見る ↗", release.youtubeUrl, "social-action social-action-primary", true));
    }
    if (release.shortsStatus === "published" && release.shortsUrl) {
      actions.append(makeLink("YouTube Shortsを見る ↗", release.shortsUrl, "social-action", true));
    }
    if (release.newsStatus === "published" && release.newsPage && route !== release.newsPage.replace(/\/$/, "")) {
      actions.append(makeLink("楽曲の物語を読む", siteUrl(release.newsPage)));
    }
    if (route !== release.releasePage.replace(/\/$/, "")) {
      actions.append(makeLink("公式リリースページ", siteUrl(release.releasePage)));
    }
    actions.append(
      makeLink("アーティストプロフィール", siteUrl(`artists/${release.artistSlug}/`)),
      makeLink("全作品を見る", siteUrl("releases/")),
      makeLink("News一覧", siteUrl("news/")),
      makeLink("公式リンク一覧", siteUrl("social/")),
    );
    section.append(actions, buildShareButtons(document.querySelector("h1")?.textContent.trim() || release.title, location.href.split("?")[0].split("#")[0]));
    return section;
  };

  const insertBeforeFooter = (section) => {
    const footer = document.querySelector(".artist-profile-footer, .site-footer");
    if (footer && !document.querySelector(".social-context-section")) footer.before(section);
  };

  const enhanceCurrentPage = (releases) => {
    if (route.startsWith("releases/")) {
      const slug = route.split("/")[1];
      const release = releases.find((item) => item.slug === slug);
      if (release) insertBeforeFooter(createContextSection(release, `${release.title}を、次の場所へ。`, "公式MV、作品の物語、アーティスト情報をひとつにまとめています。"));
      return;
    }
    if (route.startsWith("news/") && route !== "news") {
      const release = releases.find((item) => item.newsPage?.replace(/\/$/, "") === route)
        || (route === "news/shadow-code-announcement" ? releases.find((item) => item.slug === "shadow-code") : null)
        || (route === "news/eclypse-joins-suzuka" ? releases.find((item) => item.slug === "shadow-code") : null);
      if (release) insertBeforeFooter(createContextSection(release, "記事から、音楽とアーティストへ。", "関連する公式ページだけを厳選して案内します。"));
    }
  };

  Promise.all([
    fetch(socialDataUrl, { cache: "no-cache" }).then((response) => {
      if (!response.ok) throw new Error(`social links HTTP ${response.status}`);
      return response.json();
    }),
    fetch(releaseDataUrl, { cache: "no-cache" }).then((response) => {
      if (!response.ok) throw new Error(`release links HTTP ${response.status}`);
      return response.json();
    }),
  ]).then(([, releaseData]) => {
    addNavigationLinks();
    addHomeLink();
    enhanceCurrentPage(releaseData.releases || []);
  }).catch((error) => {
    console.warn("SUZUKA official-link enhancements are unavailable.", error);
    addNavigationLinks();
    addHomeLink();
  });
})();
