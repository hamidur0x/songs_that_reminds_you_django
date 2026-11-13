(() => {
  "use strict";

  const TOTAL = parseInt(document.getElementById("book-config").dataset.total, 10);
  const SONGS = JSON.parse(document.getElementById("songs-data").textContent);
  const FLIP_URL = document.getElementById("book-config").dataset.flipSound;

  const $ = (id) => document.getElementById(id);
  const bookEl = $("book"), startBtn = $("start-btn"), startup = $("startup-screen"),
        ui = $("ui-layer"), main = $("main-content"), counter = $("page-counter"),
        prevBtn = $("prev-btn"), nextBtn = $("next-btn"), indicator = $("music-indicator"),
        titleEl = $("song-title"), muteBtn = $("toggle-mute"), pauseBtn = $("toggle-pause"),
        bars = $("music-bars"), audio = $("song-audio");

  let pageFlip, started = false, muted = false, userPaused = false, currentPage = 1,
      token = 0, fadeRaf = 0, audioCtx = null, flipBuffer = null;

  // ---------- Page images: load the current page ±4 only ----------
  function loadNear(p) {
    const imgs = bookEl.querySelectorAll("img[data-src]");
    imgs.forEach((img, i) => {
      if (Math.abs(i + 1 - p) <= 4) { img.src = img.dataset.src; img.removeAttribute("data-src"); }
    });
  }

  // ---------- Page-turn sound: real file (decoded once), synthesised noise only as a fallback ----------
  function loadFlipSound() {
    if (!audioCtx || !FLIP_URL || flipBuffer) return;
    fetch(FLIP_URL)
      .then((r) => r.arrayBuffer())
      .then((data) => new Promise((ok, fail) => audioCtx.decodeAudioData(data, ok, fail)))
      .then((buf) => { flipBuffer = buf; })
      .catch(() => {});
  }

  function synthFlip() {
    const dur = 0.35, rate = audioCtx.sampleRate;
    const buf = audioCtx.createBuffer(1, Math.floor(rate * dur), rate), d = buf.getChannelData(0);
    for (let i = 0; i < d.length; i++) {
      const t = i / d.length;
      d[i] = (Math.random() * 2 - 1) * Math.pow(1 - t, 2.2) * Math.sin(Math.min(t * 12, 1) * Math.PI / 2);
    }
    const bp = audioCtx.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 2600; bp.Q.value = 0.6;
    return { buf, node: bp };
  }

  function playFlipSound() {
    if (muted || !audioCtx) return;
    if (audioCtx.state === "suspended") audioCtx.resume();
    const src = audioCtx.createBufferSource();
    const g = audioCtx.createGain();
    if (flipBuffer) {
      src.buffer = flipBuffer; g.gain.value = 0.9;
      src.connect(g).connect(audioCtx.destination);
    } else {
      const f = synthFlip(); src.buffer = f.buf; g.gain.value = 0.35;
      src.connect(f.node).connect(g).connect(audioCtx.destination);
    }
    src.start();
  }

  // ---------- Music: HTML5 audio first (ad-free), YouTube only as a fallback ----------
  let yt = null, ytReady = false, ytPending = null, ytLoading = false;

  function fadeIn(ms = 800) {
    cancelAnimationFrame(fadeRaf);
    audio.volume = 0;
    const t0 = performance.now();
    const step = (t) => {
      const k = Math.max(0, Math.min((t - t0) / ms, 1));
      audio.volume = k;
      if (k < 1) fadeRaf = requestAnimationFrame(step);
    };
    fadeRaf = requestAnimationFrame(step);
  }

  function stopAll() {
    cancelAnimationFrame(fadeRaf);
    audio.pause();
    if (yt && ytReady) { try { yt.stopVideo(); } catch (_) {} }
    ytPending = null;
  }

  function setIndicator(song) {
    if (!song) { indicator.classList.add("hidden-ui"); return; }
    titleEl.textContent = song.title;
    indicator.classList.remove("hidden-ui");
    syncPauseUi();
    updateMediaSession(song);
  }

  function playMusic(page) {
    const my = ++token;
    const song = SONGS[page];
    stopAll();
    if (!song) { setIndicator(null); return; }
    setIndicator(song);
    if (userPaused) return;

    if (song.src) {                       // ----- ad-free path -----
      audio.src = song.src;
      audio.muted = muted;
      const seek = () => {
        if (my !== token) return;
        if (song.start && song.start < (audio.duration || Infinity)) audio.currentTime = song.start;
        fadeIn();
        audio.play().catch(() => {});
      };
      audio.addEventListener("loadedmetadata", seek, { once: true });
      audio.load();
    } else if (song.videoId) {            // ----- YouTube fallback -----
      playYouTube(song, my);
    }
  }

  function playYouTube(song, my) {
    ytPending = { song, my };
    if (yt && ytReady) return flushYouTube();
    loadYouTube();
  }

  function loadYouTube() {
    if (yt || ytLoading) return;
    ytLoading = true;
    window.onYouTubeIframeAPIReady = () => {
      yt = new YT.Player("yt-player-container", {
        width: "1", height: "1",
        playerVars: { autoplay: 0, controls: 0, rel: 0, modestbranding: 1, playsinline: 1, iv_load_policy: 3, disablekb: 1 },
        events: {
          onReady: () => { ytReady = true; flushYouTube(); },
          onError: (e) => {                             // show why YouTube refused (101/150 = embedding blocked, 153 = no referrer)
            console.error("YouTube error", e.data);
            const s = SONGS[currentPage];
            if (s) titleEl.textContent = `${s.title} (YouTube error ${e.data})`;
          },
          onStateChange: (e) => {                       // loop current song from its start second
            if (e.data === YT.PlayerState.ENDED) {
              const s = SONGS[currentPage]; if (s && !s.src) { yt.seekTo(s.start || 0, true); yt.playVideo(); }
            }
          },
        },
      });
    };
    const s = document.createElement("script");
    s.src = "https://www.youtube.com/iframe_api"; s.async = true;
    document.body.appendChild(s);
  }

  function flushYouTube() {
    if (!ytPending || ytPending.my !== token) return;
    const { song } = ytPending; ytPending = null;
    yt.loadVideoById({ videoId: song.videoId, startSeconds: song.start || 0 });
    muted ? yt.mute() : yt.unMute();
    yt.setVolume(100);
    if (!userPaused) yt.playVideo();
  }

  // ---------- Controls ----------
  function isYT() { const s = SONGS[currentPage]; return s && !s.src; }

  function syncPauseUi() {
    $("ico-pause").classList.toggle("hide", userPaused);
    $("ico-play").classList.toggle("hide", !userPaused);
    bars.classList.toggle("paused", userPaused);
    pauseBtn.setAttribute("aria-label", userPaused ? "Play music" : "Pause music");
    if ("mediaSession" in navigator) navigator.mediaSession.playbackState = userPaused ? "paused" : "playing";
  }

  function setPaused(v) {
    userPaused = v;
    if (v) { audio.pause(); if (yt && ytReady) try { yt.pauseVideo(); } catch (_) {} }
    else if (SONGS[currentPage]) {
      if (isYT()) { yt && ytReady ? yt.playVideo() : playMusic(currentPage); }
      else if (audio.src) { audio.play().catch(() => {}); } else { playMusic(currentPage); }
    }
    syncPauseUi();
  }

  pauseBtn.addEventListener("click", () => setPaused(!userPaused));

  muteBtn.addEventListener("click", () => {
    muted = !muted;
    $("ico-vol").classList.toggle("hide", muted);
    $("ico-mute").classList.toggle("hide", !muted);
    audio.muted = muted;
    if (yt && ytReady) { muted ? yt.mute() : (yt.unMute(), yt.setVolume(100)); }
  });

  // Lock-screen / headphone controls on phones
  function updateMediaSession(song) {
    if (!("mediaSession" in navigator)) return;
    const art = bookEl.querySelector("img")?.src;
    navigator.mediaSession.metadata = new MediaMetadata({
      title: song.title, artist: "For My Love", album: "Songs that remind me of you",
      artwork: art ? [{ src: art, sizes: "530x770", type: "image/jpeg" }] : [],
    });
  }
  if ("mediaSession" in navigator) {
    const ms = navigator.mediaSession;
    ms.setActionHandler("play", () => setPaused(false));
    ms.setActionHandler("pause", () => setPaused(true));
    ms.setActionHandler("nexttrack", () => pageFlip && pageFlip.flipNext());
    ms.setActionHandler("previoustrack", () => pageFlip && pageFlip.flipPrev());
  }

  // ---------- Book ----------
  function updateUI(p) { counter.textContent = p === 1 ? "Cover" : p === TOTAL ? "End" : `Page ${p}`; }

  function initBook() {
    const mobile = innerWidth < 768;
    let width, height;
    if (mobile) {
      width = innerWidth * 0.92; height = width * 1.45;
      if (height > innerHeight * 0.82) { height = innerHeight * 0.82; width = height / 1.45; }
    } else { height = innerHeight * 0.82; width = height / 1.45; }

    pageFlip = new St.PageFlip(bookEl, {
      width, height, size: "fixed", minWidth: 300, maxWidth: 1200, minHeight: 400, maxHeight: 1600,
      showCover: true, usePortrait: true, mobileScrollSupport: false, flippingTime: 900,
      drawShadow: true, swipeDistance: 20,
    });
    pageFlip.loadFromHTML(document.querySelectorAll(".page"));
    pageFlip.on("changeState", (e) => {            // page starts turning (button, key or swipe)
      if (e.data === "flipping") playFlipSound();
    });
    pageFlip.on("flip", (e) => {                   // page has landed -> that page's song starts
      currentPage = e.data + 1;
      updateUI(currentPage); loadNear(currentPage); playMusic(currentPage);
    });
  }

  // A 0.1 s silent WAV used to "unlock" the audio element inside the user's tap (required by iOS/Android)
  function silentWav() {
    const n = 800, b = new DataView(new ArrayBuffer(44 + n * 2));
    const w = (o, s) => [...s].forEach((c, i) => b.setUint8(o + i, c.charCodeAt(0)));
    w(0, "RIFF"); b.setUint32(4, 36 + n * 2, true); w(8, "WAVEfmt "); b.setUint32(16, 16, true);
    b.setUint16(20, 1, true); b.setUint16(22, 1, true); b.setUint32(24, 8000, true); b.setUint32(28, 16000, true);
    b.setUint16(32, 2, true); b.setUint16(34, 16, true); w(36, "data"); b.setUint32(40, n * 2, true);
    return URL.createObjectURL(new Blob([b], { type: "audio/wav" }));
  }

  startBtn.addEventListener("click", () => {
    if (started) return; started = true;
    try { audioCtx = new (window.AudioContext || window.webkitAudioContext)(); audioCtx.resume(); } catch (_) {}
    try { audio.src = silentWav(); audio.loop = false; audio.play().catch(() => {}); } catch (_) {}
    audio.loop = true;
    loadFlipSound();
    if (Object.values(SONGS).some((x) => !x.src && x.videoId)) loadYouTube();

    startup.style.opacity = "0";
    setTimeout(() => { startup.style.display = "none"; }, 1000);
    ui.style.opacity = "1"; main.style.opacity = "1";
    loadNear(1);
    initBook();
    setTimeout(() => playMusic(1), 1200);
  });

  nextBtn.addEventListener("click", () => pageFlip && pageFlip.flipNext());
  prevBtn.addEventListener("click", () => pageFlip && pageFlip.flipPrev());
  document.addEventListener("keydown", (e) => {
    if (!pageFlip) return;
    if (e.key === "ArrowRight") pageFlip.flipNext();
    if (e.key === "ArrowLeft") pageFlip.flipPrev();
  });
})();
