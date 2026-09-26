/* Local-only product demo. No analytics, external embeds, or dependencies. */
(() => {
  const video = document.getElementById('product-demo');
  const button = document.querySelector('.demo-toggle');
  if (!video || !button) return;
  const source = video.querySelector('source');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const connection = navigator.connection;
  let inView = false;
  let userPaused = false;
  let userRequested = false;
  let loaded = false;
  let blocked = false;

  function syncButton() {
    button.textContent = video.paused ? button.dataset.play : button.dataset.pause;
  }
  function load() {
    if (loaded) return;
    loaded = true;
    source.src = source.dataset.src;
    video.load();
  }
  function mayPlay() {
    return inView && !document.hidden && !userPaused && !blocked &&
      (userRequested || (!reducedMotion.matches && !connection?.saveData));
  }
  function update() {
    if (!mayPlay()) { video.pause(); return; }
    load();
    const attempt = video.play();
    if (attempt) attempt.then(() => {
      // A slow load must not restart playback after leaving the viewport.
      if (!mayPlay()) video.pause();
    }).catch((error) => {
      if (error.name !== 'AbortError') blocked = true;
      syncButton();
    });
  }
  video.muted = true;
  video.controls = false;
  button.hidden = false;
  video.addEventListener('play', syncButton);
  video.addEventListener('pause', syncButton);
  video.addEventListener('error', () => { blocked = true; video.controls = true; syncButton(); });
  button.addEventListener('click', () => {
    if (!video.paused) {
      userPaused = true;
      video.pause();
    } else {
      userPaused = false;
      userRequested = true;
      blocked = false;
      update();
    }
  });
  document.addEventListener('visibilitychange', update);
  reducedMotion.addEventListener('change', () => { userRequested = false; update(); });
  connection?.addEventListener?.('change', update);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(([entry]) => {
      inView = entry.isIntersecting && entry.intersectionRatio >= 0.2;
      update();
    }, { threshold: [0, 0.2] }).observe(video);
  } else {
    // Older browsers get explicit playback rather than unbounded autoplay.
    inView = true;
    userPaused = true;
  }
})();
