(() => {
  const slides = [...document.querySelectorAll('.slide')];
  const currentEl = document.querySelector('#current');
  const totalEl = document.querySelector('#total');
  const titleEl = document.querySelector('#slide-title');
  const progressEl = document.querySelector('#progress-bar');
  const prevButton = document.querySelector('#prev');
  const nextButton = document.querySelector('#next');
  const fullscreenButton = document.querySelector('#fullscreen');
  let current = 0;
  let touchStartX = null;

  const pad = value => String(value).padStart(2, '0');
  totalEl.textContent = pad(slides.length);

  function indexFromHash() {
    const match = location.hash.match(/^#slide-(\d+)$/);
    if (!match) return 0;
    return Math.min(Math.max(Number(match[1]) - 1, 0), slides.length - 1);
  }

  function show(index, updateHash = true) {
    current = Math.min(Math.max(index, 0), slides.length - 1);
    slides.forEach((slide, slideIndex) => {
      const active = slideIndex === current;
      slide.classList.toggle('is-active', active);
      slide.setAttribute('aria-hidden', String(!active));
      slide.toggleAttribute('inert', !active);
    });
    currentEl.textContent = pad(current + 1);
    titleEl.textContent = slides[current].dataset.title || '';
    progressEl.style.width = `${((current + 1) / slides.length) * 100}%`;
    prevButton.disabled = current === 0;
    nextButton.disabled = current === slides.length - 1;
    document.title = `${current + 1}/${slides.length} · ${slides[current].dataset.title}`;
    if (updateHash && location.hash !== `#slide-${current + 1}`) {
      history.replaceState(null, '', `#slide-${current + 1}`);
    }
  }

  function isInteractiveTarget(target) {
    return target instanceof Element && Boolean(target.closest('input, textarea, select, button, a, [contenteditable="true"]'));
  }

  function goNext() { show(current + 1); }
  function goPrev() { show(current - 1); }

  prevButton.addEventListener('click', goPrev);
  nextButton.addEventListener('click', goNext);
  fullscreenButton.addEventListener('click', toggleFullscreen);

  async function toggleFullscreen() {
    try {
      if (!document.fullscreenElement) await document.documentElement.requestFullscreen?.();
      else await document.exitFullscreen?.();
    } catch (_) {
      // Fullscreen is optional; presentation remains usable without it.
    }
  }

  document.addEventListener('keydown', event => {
    if (isInteractiveTarget(event.target)) return;
    if (event.key === ' ') { event.preventDefault(); document.body.classList.toggle('parrot-visible'); }
    if (['ArrowRight', 'PageDown'].includes(event.key)) { event.preventDefault(); goNext(); }
    if (['ArrowLeft', 'PageUp'].includes(event.key)) { event.preventDefault(); goPrev(); }
    if (event.key === 'Home') { event.preventDefault(); show(0); }
    if (event.key === 'End') { event.preventDefault(); show(slides.length - 1); }
    if (event.key.toLowerCase() === 'f') { event.preventDefault(); toggleFullscreen(); }
    if (event.key.toLowerCase() === 'd') { document.body.classList.toggle('chrome-hidden'); }
  });

  document.addEventListener('touchstart', event => {
    touchStartX = event.changedTouches[0]?.clientX ?? null;
  }, { passive: true });

  document.addEventListener('touchend', event => {
    if (touchStartX === null) return;
    const endX = event.changedTouches[0]?.clientX ?? touchStartX;
    const delta = endX - touchStartX;
    touchStartX = null;
    if (Math.abs(delta) < 60) return;
    if (delta < 0) goNext(); else goPrev();
  }, { passive: true });

  window.addEventListener('hashchange', () => show(indexFromHash(), false));
  show(indexFromHash(), false);
})();
