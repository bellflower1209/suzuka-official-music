document.querySelectorAll(".mobile-menu a").forEach((link) => {
  link.addEventListener("click", () => link.closest("details")?.removeAttribute("open"));
});

(() => {
  const VIDEO_ID = "WzcXyuAI_FM";
  const YOUTUBE_URL = `https://www.youtube.com/watch?v=${VIDEO_ID}`;
  const STORAGE_KEY = "suzuka-mia-player-position";
  const DEFAULT_DURATION = 5 * 60 + 28;
  const currentScript = document.currentScript || [...document.scripts].find((script) => script.src.includes("/assets/main.js"));
  const siteRoot = currentScript?.src ? new URL("../", currentScript.src) : new URL("./", document.baseURI);
  const imageUrl = new URL("images/mv-mia.jpg", siteRoot).href;
  const styleUrl = new URL("assets/player.css", siteRoot).href;

  if (!document.querySelector(`link[href="${styleUrl}"]`)) {
    const stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = styleUrl;
    document.head.append(stylesheet);
  }

  const playerShell = document.createElement("aside");
  playerShell.className = "suzuka-music-player";
  playerShell.setAttribute("aria-label", "SUZUKA ミュージックプレイヤー");
  playerShell.innerHTML = `
    <div class="suzuka-player-video" aria-label="M・I・A YouTube動画">
      <div id="suzuka-youtube-player"></div>
    </div>
    <div class="suzuka-player-panel">
      <img class="suzuka-player-cover" src="${imageUrl}" alt="榎本魅愛 M・I・A ジャケット" width="72" height="72">
      <button class="suzuka-player-toggle" type="button" aria-label="M・I・Aを再生" aria-pressed="false">
        <span class="suzuka-player-play" aria-hidden="true"></span>
      </button>
      <div class="suzuka-player-details">
        <span class="suzuka-player-kicker">NOW PLAYING · SUZUKA</span>
        <strong>M・I・A</strong>
        <small>榎本魅愛 · ENOMOTO MIA</small>
        <div class="suzuka-player-progress">
          <span class="suzuka-player-current">0:00</span>
          <input class="suzuka-player-seek" type="range" min="0" max="${DEFAULT_DURATION}" value="0" step="1" aria-label="再生位置">
          <span class="suzuka-player-duration">5:28</span>
        </div>
      </div>
      <a class="suzuka-player-youtube" href="${YOUTUBE_URL}" target="_blank" rel="noreferrer" aria-label="M・I・AをYouTubeで開く">YouTube <span aria-hidden="true">↗</span></a>
      <span class="suzuka-player-status" role="status" aria-live="polite"></span>
    </div>`;
  document.body.append(playerShell);

  const toggle = playerShell.querySelector(".suzuka-player-toggle");
  const seek = playerShell.querySelector(".suzuka-player-seek");
  const currentLabel = playerShell.querySelector(".suzuka-player-current");
  const durationLabel = playerShell.querySelector(".suzuka-player-duration");
  const status = playerShell.querySelector(".suzuka-player-status");
  let player;
  let playerReady = false;
  let pendingPlay = false;
  const readStoredPosition = () => {
    try {
      return Number(sessionStorage.getItem(STORAGE_KEY)) || 0;
    } catch {
      return 0;
    }
  };
  const storePosition = (position) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, String(position));
    } catch {
      // Playback remains available when storage is restricted.
    }
  };
  const clearStoredPosition = () => {
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // Nothing to clear when storage is restricted.
    }
  };
  let pendingSeek = readStoredPosition();
  let progressTimer;

  const formatTime = (seconds) => {
    const safeSeconds = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;
    return `${Math.floor(safeSeconds / 60)}:${String(safeSeconds % 60).padStart(2, "0")}`;
  };

  if (pendingSeek > 0) {
    seek.value = String(Math.min(pendingSeek, DEFAULT_DURATION));
    currentLabel.textContent = formatTime(pendingSeek);
    toggle.setAttribute("aria-label", `M・I・Aを${formatTime(pendingSeek)}から再生`);
  }

  const setPlayingState = (isPlaying) => {
    playerShell.classList.toggle("is-playing", isPlaying);
    toggle.setAttribute("aria-pressed", String(isPlaying));
    toggle.setAttribute("aria-label", isPlaying ? "M・I・Aを一時停止" : "M・I・Aを再生");
    toggle.innerHTML = isPlaying
      ? '<span class="suzuka-player-pause" aria-hidden="true"></span>'
      : '<span class="suzuka-player-play" aria-hidden="true"></span>';
  };

  const updateProgress = () => {
    if (!playerReady || typeof player?.getCurrentTime !== "function") return;
    const currentTime = player.getCurrentTime() || 0;
    const duration = player.getDuration() || DEFAULT_DURATION;
    seek.max = String(Math.max(1, Math.floor(duration)));
    seek.value = String(Math.min(currentTime, duration));
    currentLabel.textContent = formatTime(currentTime);
    durationLabel.textContent = formatTime(duration);
    storePosition(currentTime);
  };

  const onPlayerStateChange = ({ data }) => {
    playerShell.dataset.playerState = String(data);
    const states = window.YT?.PlayerState;
    const isPlaying = data === states?.PLAYING;
    if (isPlaying) status.textContent = "";
    setPlayingState(isPlaying);
    clearInterval(progressTimer);
    if (isPlaying) progressTimer = window.setInterval(updateProgress, 500);
    if (data === states?.ENDED) {
      clearStoredPosition();
      seek.value = "0";
      currentLabel.textContent = "0:00";
    }
  };

  const createPlayer = () => {
    if (player || !window.YT?.Player) return;
    player = new window.YT.Player("suzuka-youtube-player", {
      width: 200,
      height: 200,
      videoId: VIDEO_ID,
      playerVars: {
        autoplay: pendingPlay ? 1 : 0,
        controls: 1,
        playsinline: 1,
        rel: 0,
      },
      events: {
        onReady: () => {
          playerReady = true;
          playerShell.dataset.ready = "true";
          status.textContent = "";
          const duration = player.getDuration() || DEFAULT_DURATION;
          seek.max = String(Math.floor(duration));
          durationLabel.textContent = formatTime(duration);
          if (pendingSeek > 0 && pendingSeek < duration - 2) player.seekTo(pendingSeek, true);
          if (pendingPlay) {
            pendingPlay = false;
            player.playVideo();
          }
        },
        onStateChange: onPlayerStateChange,
        onError: () => {
          status.textContent = "再生できない場合はYouTubeでお聴きください。";
          setPlayingState(false);
        },
      },
    });
  };

  const loadYouTubeApi = (createWhenReady = true) => {
    if (window.YT?.Player) {
      if (createWhenReady) createPlayer();
      return;
    }
    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const apiScript = document.createElement("script");
      apiScript.src = "https://www.youtube.com/iframe_api";
      apiScript.async = true;
      apiScript.addEventListener("error", () => {
        status.textContent = "再生できない場合はYouTubeでお聴きください。";
        pendingPlay = false;
      });
      document.head.append(apiScript);
    }
    const previousCallback = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      if (typeof previousCallback === "function") previousCallback();
      if (pendingPlay || createWhenReady) createPlayer();
    };
  };

  toggle.addEventListener("click", () => {
    playerShell.classList.add("is-expanded");
    if (!playerReady) {
      pendingPlay = true;
      status.textContent = "プレイヤーを読み込んでいます…";
      loadYouTubeApi(true);
      window.setTimeout(() => {
        if (playerShell.dataset.playerState !== String(window.YT?.PlayerState?.PLAYING)) {
          status.textContent = "Safariでは動画内の再生ボタンをタップしてください。";
        }
      }, 1400);
      return;
    }
    const isPlaying = player.getPlayerState() === window.YT.PlayerState.PLAYING;
    if (isPlaying) player.pauseVideo();
    else player.playVideo();
  });

  seek.addEventListener("input", () => {
    currentLabel.textContent = formatTime(Number(seek.value));
  });

  seek.addEventListener("change", () => {
    pendingSeek = Number(seek.value);
    storePosition(pendingSeek);
    if (playerReady) player.seekTo(pendingSeek, true);
  });

  window.addEventListener("pagehide", updateProgress);
  loadYouTubeApi(false);
})();
