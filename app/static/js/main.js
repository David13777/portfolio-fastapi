const menuButton = document.querySelector('.menu-button');
const navigation = document.querySelector('.main-nav');
const body = document.body;

const closeMenu = () => {
  if (!menuButton || !navigation) return;
  menuButton.setAttribute('aria-expanded', 'false');
  navigation.classList.remove('is-open');
  body.classList.remove('menu-open');
};

if (menuButton && navigation) {
  menuButton.addEventListener('click', () => {
    const isOpen = menuButton.getAttribute('aria-expanded') === 'true';
    menuButton.setAttribute('aria-expanded', String(!isOpen));
    navigation.classList.toggle('is-open', !isOpen);
    body.classList.toggle('menu-open', !isOpen);
  });
  navigation.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', closeMenu);
  });
}

document.querySelectorAll('[data-year]').forEach((node) => {
  node.textContent = new Date().getFullYear();
});

const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.12 }
);

document.querySelectorAll('.reveal').forEach((element) => revealObserver.observe(element));

const progressBar = document.querySelector('.scroll-progress span');
const parallaxLayer = document.querySelector('[data-parallax]');
const header = document.querySelector('.site-header');

const updateScrollEffects = () => {
  const scrollable = document.documentElement.scrollHeight - window.innerHeight;
  const progress = scrollable > 0 ? window.scrollY / scrollable : 0;
  if (progressBar) progressBar.style.transform = `scaleX(${progress})`;
  if (parallaxLayer) parallaxLayer.style.transform = `translate3d(0, ${window.scrollY * 0.12}px, 0) scale(1.04)`;
  if (header) header.classList.toggle('is-solid', window.scrollY > 24);
};

window.addEventListener('scroll', updateScrollEffects, { passive: true });
updateScrollEffects();

const cursor = document.querySelector('.cursor');
if (cursor && window.matchMedia('(pointer: fine)').matches) {
  window.addEventListener('mousemove', (event) => {
    cursor.style.transform = `translate3d(${event.clientX}px, ${event.clientY}px, 0)`;
  });
  document.querySelectorAll('[data-cursor]').forEach((element) => {
    element.addEventListener('mouseenter', () => cursor.classList.add('is-active'));
    element.addEventListener('mouseleave', () => cursor.classList.remove('is-active'));
  });
}

document.querySelectorAll('a[href^="/"]').forEach((link) => {
  link.addEventListener('click', (event) => {
    if (event.metaKey || event.ctrlKey || link.pathname === window.location.pathname) return;
    event.preventDefault();
    body.classList.add('is-leaving');
    window.setTimeout(() => { window.location.href = link.href; }, 280);
  });
});

window.addEventListener('pageshow', () => body.classList.remove('is-leaving'));

document.querySelectorAll('[data-ratio]').forEach((slide) => {
  const ratio = Number(slide.dataset.ratio);
  if (ratio > 0 && ratio <= 100) slide.style.setProperty('--ratio', String(ratio));
});

const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

document.querySelectorAll('[data-gallery-block]').forEach((block) => {
  const carousel = block.querySelector('[data-carousel]');
  const previous = block.querySelector('[data-carousel-prev]');
  const next = block.querySelector('[data-carousel-next]');
  const bar = block.querySelector('.carousel-progress span');
  if (!carousel || !previous || !next) return;

  const update = () => {
    const maxScroll = carousel.scrollWidth - carousel.clientWidth;
    previous.disabled = carousel.scrollLeft <= 2;
    next.disabled = maxScroll <= 2 || carousel.scrollLeft >= maxScroll - 2;
    if (bar) bar.style.transform = `scaleX(${maxScroll <= 2 ? 1 : carousel.scrollLeft / maxScroll})`;
  };

  const step = () => Math.max(280, carousel.clientWidth * 0.72);
  const scrollByStep = (direction) => {
    carousel.scrollBy({
      left: step() * direction,
      behavior: motionQuery.matches ? 'auto' : 'smooth',
    });
  };

  previous.addEventListener('click', () => scrollByStep(-1));
  next.addEventListener('click', () => scrollByStep(1));
  carousel.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update);
  carousel.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      scrollByStep(1);
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      scrollByStep(-1);
    }
  });

  if (window.matchMedia('(pointer: fine)').matches) {
    let startX = 0;
    let startScroll = 0;
    let dragging = false;
    let moved = false;

    carousel.addEventListener('pointerdown', (event) => {
      if (event.pointerType !== 'mouse' || event.button !== 0) return;
      dragging = true;
      moved = false;
      startX = event.clientX;
      startScroll = carousel.scrollLeft;
      carousel.classList.add('is-dragging');
      carousel.setPointerCapture(event.pointerId);
    });

    carousel.addEventListener('pointermove', (event) => {
      if (!dragging) return;
      const delta = event.clientX - startX;
      if (Math.abs(delta) > 6) moved = true;
      carousel.scrollLeft = startScroll - delta;
    });

    const stopDragging = () => {
      dragging = false;
      carousel.classList.remove('is-dragging');
    };

    carousel.addEventListener('pointerup', stopDragging);
    carousel.addEventListener('pointercancel', stopDragging);
    carousel.addEventListener('click', (event) => {
      if (!moved) return;
      event.preventDefault();
      event.stopPropagation();
      moved = false;
    }, true);
  }

  update();
});

const lightbox = document.querySelector('[data-lightbox]');
if (lightbox) {
  const image = lightbox.querySelector('[data-lightbox-image]');
  const caption = lightbox.querySelector('[data-lightbox-label]');
  const closeButton = lightbox.querySelector('[data-lightbox-close]');
  const previousButton = lightbox.querySelector('[data-lightbox-prev]');
  const nextButton = lightbox.querySelector('[data-lightbox-next]');
  let items = [];
  let index = 0;
  let returnFocus = null;

  const render = () => {
    const item = items[index];
    if (!item) return;
    if (!item.src.startsWith('/static/images/') || item.src.includes('..') || item.src.includes('\\')) return;
    image.src = item.src;
    image.alt = item.alt;
    caption.textContent = `${item.label}  ·  ${String(index + 1).padStart(2, '0')} / ${String(items.length).padStart(2, '0')}`;
    const single = items.length < 2;
    previousButton.disabled = single;
    nextButton.disabled = single;
  };

  const open = (group, start, opener) => {
    items = group;
    index = start;
    returnFocus = opener;
    render();
    lightbox.hidden = false;
    body.classList.add('lightbox-open');
    closeButton.focus();
  };

  const close = () => {
    lightbox.hidden = true;
    image.removeAttribute('src');
    body.classList.remove('lightbox-open');
    returnFocus?.focus();
  };

  const shift = (direction) => {
    if (items.length < 2) return;
    index = (index + direction + items.length) % items.length;
    render();
  };

  document.querySelectorAll('.slide-open').forEach((button) => {
    button.addEventListener('click', () => {
      const group = [...document.querySelectorAll(`.slide-open[data-gallery="${CSS.escape(button.dataset.gallery)}"]`)].map((slide) => ({
        src: slide.dataset.src,
        alt: slide.dataset.alt,
        label: slide.dataset.label,
      }));
      open(group, Number(button.dataset.index), button);
    });
  });

  closeButton.addEventListener('click', close);
  previousButton.addEventListener('click', () => shift(-1));
  nextButton.addEventListener('click', () => shift(1));
  lightbox.addEventListener('click', (event) => {
    if (event.target === lightbox) close();
  });

  document.addEventListener('keydown', (event) => {
    if (lightbox.hidden) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      close();
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      shift(1);
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      shift(-1);
    }
  });

  let touchStartX = 0;
  lightbox.addEventListener('touchstart', (event) => {
    touchStartX = event.changedTouches[0].clientX;
  }, { passive: true });
  lightbox.addEventListener('touchend', (event) => {
    const delta = event.changedTouches[0].clientX - touchStartX;
    if (Math.abs(delta) < 40) return;
    shift(delta > 0 ? -1 : 1);
  }, { passive: true });
}
