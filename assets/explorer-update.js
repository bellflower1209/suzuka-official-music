(() => {
  document.querySelectorAll("[data-lightbox-src]").forEach((trigger) => {
    const dialog = trigger.closest("main")?.querySelector(".explorer-lightbox");
    if (!dialog) return;
    trigger.addEventListener("click", () => {
      const image = dialog.querySelector("img");
      image.src = trigger.dataset.lightboxSrc || "";
      image.alt = trigger.dataset.lightboxAlt || "";
      dialog.showModal();
    });
    dialog.querySelector("[data-lightbox-close]")?.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });
  document.querySelectorAll("[data-wiki-filter]").forEach((input) => {
    const root = input.closest("main")?.querySelector("[data-wiki-list]");
    if (!root) return;
    input.addEventListener("input", () => {
      const query = input.value.normalize("NFKC").toLowerCase().trim();
      root.querySelectorAll("[data-wiki-entry], .explorer-wiki-card").forEach((entry) => {
        entry.hidden = query && !entry.textContent.normalize("NFKC").toLowerCase().includes(query);
      });
    });
  });
})();
