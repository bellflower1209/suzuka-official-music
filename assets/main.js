document.querySelectorAll(".mobile-menu a").forEach((link) => {
  link.addEventListener("click", () => link.closest("details")?.removeAttribute("open"));
});

(() => {
  const mainScript = document.currentScript || [...document.scripts].find((script) => script.src.includes("/assets/main.js"));
  const siteRoot = mainScript?.src ? new URL("../", mainScript.src) : new URL("./", document.baseURI);
  const socialStyleUrl = new URL("assets/social.css", siteRoot).href;
  if (![...document.querySelectorAll('link[rel="stylesheet"]')].some((stylesheet) => stylesheet.href === socialStyleUrl)) {
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = socialStyleUrl;
    document.head.append(stylesheet);
  }
  if (!document.querySelector('script[data-suzuka-social]')) {
    const socialScript = document.createElement("script");
    socialScript.src = new URL("assets/social.js", siteRoot).href;
    socialScript.defer = true;
    socialScript.dataset.suzukaSocial = "true";
    document.head.append(socialScript);
  }
})();
