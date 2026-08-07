// ---------------------------------------------------------------
// Small, plain JS. No build step, no dependencies.
// ---------------------------------------------------------------

// Keep the footer year current without editing it by hand.
document.addEventListener("DOMContentLoaded", () => {
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();
});

// The nav below the header spans exactly the width of the name
// above it. The name's font-size is fluid (vw-based), so measure it
// after fonts load and re-measure on resize.
document.addEventListener("DOMContentLoaded", () => {
  const wordmark = document.querySelector(".wordmark");
  if (!wordmark) return;

  const sync = () => {
    const w = Math.round(wordmark.getBoundingClientRect().width);
    if (w > 0) {
      document.documentElement.style.setProperty("--name-width", `${w}px`);
    }
  };

  sync();
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(sync);
  }
  window.addEventListener("resize", sync, { passive: true });

  // Re-measure once the compact/expand transition finishes. Not on
  // every frame of it (see the note on the sticky-header block below
  // for why watching an element's own size and writing that back into
  // layout-affecting CSS can loop) — just at the start and the end,
  // which is enough to keep the nav's width honest without the risk.
  wordmark.addEventListener("transitionend", sync);
});

// Sticky top bar: compacts once you've scrolled past the first
// stretch, and publishes its own height as --top-h so the table of
// contents and anchor links can offset themselves correctly instead
// of sliding underneath it.
document.addEventListener("DOMContentLoaded", () => {
  const top = document.getElementById("site-top");
  if (!top) return;

  // Deliberately NOT a ResizeObserver here. Observing #site-top's own
  // size and writing that size back into a CSS variable that other
  // elements' layout depends on (--top-h feeds the TOC's position and
  // heading scroll-margins) can cause the observer to re-trigger
  // itself — the resulting loop was the actual cause of a rapid
  // flicker right around the compact-header threshold. transitionend
  // fires exactly twice per state change (once per animated property)
  // and can't retrigger itself, so it's used here instead.
  const publishHeight = () => {
    document.documentElement.style.setProperty(
      "--top-h", `${Math.round(top.getBoundingClientRect().height)}px`);
  };
  publishHeight();
  top.addEventListener("transitionend", publishHeight);

  // Hysteresis: compacting shrinks the header by roughly 100px, which
  // moves page content up underneath a fixed scroll position. With a
  // single threshold that shift alone can cross back over the same
  // line and toggle the class again. But hysteresis alone isn't
  // enough — while the header is mid-transition, the browser fires
  // dozens of scroll events on its own as content shifts under it
  // (one scrollTo() call was measured firing 55 scroll events), and
  // scrollY's meaning is itself in flux during that window. Locking
  // the check out entirely until the transition finishes stops those
  // synthetic in-between events from ever being evaluated at all.
  let ticking = false;
  let transitioning = false;
  top.addEventListener("transitionstart", () => { transitioning = true; });
  top.addEventListener("transitionend", () => { transitioning = false; });

  const onScroll = () => {
    if (ticking || transitioning) return;
    ticking = true;
    requestAnimationFrame(() => {
      const scrolled = top.classList.contains("scrolled");
      if (!scrolled && window.scrollY > 160) {
        top.classList.add("scrolled");
      } else if (scrolled && window.scrollY < 40) {
        top.classList.remove("scrolled");
      }
      ticking = false;
    });
  };

  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
});

// Dark/light toggle. The no-flash inline script in <head> sets the
// initial state before paint; this just wires up the button and
// remembers the choice for next visit.
document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  const root = document.documentElement;

  const isLight = () => root.getAttribute("data-theme") === "light";
  const updateLabel = () => { btn.textContent = isLight() ? "Dark" : "Light"; };
  updateLabel();

  btn.addEventListener("click", () => {
    if (isLight()) {
      root.removeAttribute("data-theme");
      localStorage.setItem("theme", "dark");
    } else {
      root.setAttribute("data-theme", "light");
      localStorage.setItem("theme", "light");
    }
    updateLabel();
  });
});

// ---------------------------------------------------------------
// Scroll reveal. Applied automatically to page titles, section
// headings, list rows, and gallery figures — no class="reveal"
// needed in the HTML itself, so it works on every essay/poem/photo
// page without editing each one by hand. Each element fades and
// rises into place the first time it scrolls into view, then stays
// put. Skipped entirely under reduced motion.
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const selector = ".home-intro, .list-header, .article-head, .content h2, .entry-list li, .gallery figure";
  const targets = document.querySelectorAll(selector);
  if (!targets.length) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Photographs dissolve; everything else fades and rises. The
  // .no-anim class hides them instantly for one frame — otherwise the
  // browser would animate opacity 1 -> 0 over the full duration and the
  // element would never actually reach 0 before being revealed.
  targets.forEach((el) => {
    el.classList.add(el.matches(".gallery figure") ? "reveal-fade" : "reveal", "no-anim");
  });

  if (reduceMotion) {
    targets.forEach((el) => el.classList.add("visible"));
    return;
  }

  // Cascade: rows within a given list reveal one after another, top to
  // bottom. The counter resets per container, so each list (and the
  // gallery) starts its own cascade from zero rather than inheriting a
  // running total from earlier lists on the page.
  document.querySelectorAll(".entry-list, .gallery").forEach((container) => {
    const step = container.matches(".gallery") ? 260 : 200;
    const rows = container.querySelectorAll(":scope > li, :scope > figure");
    rows.forEach((row, i) => {
      row.style.transitionDelay = `${Math.min(i * step, 1600)}ms`;
    });
  });

  const remaining = new Set(targets);

  const show = (el) => {
    el.classList.add("visible");
    remaining.delete(el);
  };

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          show(entry.target);
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  targets.forEach((el) => observer.observe(el));

  // IntersectionObserver alone misses anything the viewport jumps
  // straight past — a fast flick, a TOC anchor link, or a reload
  // partway down the page — leaving those elements stuck invisible.
  // This sweep catches anything at or above the fold and reveals it.
  const sweep = () => {
    if (!remaining.size) return;
    [...remaining].forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight) {
        show(el);
        observer.unobserve(el);
      }
    });
  };

  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      sweep();
      ticking = false;
    });
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });

  // Sequence matters: the hidden state must actually paint before the
  // transition is armed, and the transition must be armed before
  // anything is revealed. Otherwise no fade is ever seen.
  requestAnimationFrame(() => {
    void document.body.offsetHeight;             // hidden state painted
    targets.forEach((el) => el.classList.remove("no-anim")); // arm fade
    void document.body.offsetHeight;
    requestAnimationFrame(sweep);                // now reveal
  });
});

// Faint background rhomboid grid drifts slower than the page scrolls —
// a small parallax touch, purely decorative. No-ops if the element
// isn't on the page, and does nothing under reduced motion.
document.addEventListener("DOMContentLoaded", () => {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  let ticking = false;
  window.addEventListener(
    "scroll",
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const shift = window.scrollY * 0.12;
        document.documentElement.style.setProperty("--monogram-shift", `${shift}px`);
        ticking = false;
      });
    },
    { passive: true }
  );
});

// Photograph lightbox: click a thumbnail on the Photographs page
// to see it full-size; click again (or press Escape) to close.
document.addEventListener("DOMContentLoaded", () => {
  const lightbox = document.getElementById("lightbox");
  const lightboxImg = document.getElementById("lightbox-img");
  if (!lightbox || !lightboxImg) return; // not on the photographs page

  document.querySelectorAll(".gallery-link").forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      lightboxImg.src = link.getAttribute("href");
      lightboxImg.alt = link.querySelector("img")?.alt || "";
      lightbox.classList.add("open");
    });
  });

  lightbox.addEventListener("click", () => {
    lightbox.classList.remove("open");
    lightboxImg.src = "";
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      lightbox.classList.remove("open");
      lightboxImg.src = "";
    }
  });
});

// ---------------------------------------------------------------
// Long-form reading aids. All of this only runs on a page that has
// an <article class="essay"> with a .content block inside — i.e.
// essay and poem pages. Nothing here needs configuring per-post.
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const article = document.querySelector("article.essay");
  const content = article?.querySelector(".content");
  if (!article || !content) return;

  // --- auto reading time, written into <span id="reading-time"> if present ---
  const words = content.textContent.trim().split(/\s+/).filter(Boolean).length;
  const minutes = Math.max(1, Math.round(words / 200)); // ~200 wpm
  const timeEl = document.getElementById("reading-time");
  if (timeEl) timeEl.textContent = `${minutes} min read`;

  // --- table of contents, only when there's enough structure to need one ---
  const headings = content.querySelectorAll("h2");
  if (headings.length >= 3) {
    const toc = document.createElement("nav");
    toc.className = "toc";
    toc.setAttribute("aria-label", "Table of contents");

    const label = document.createElement("p");
    label.className = "toc-label";
    label.textContent = "In this essay";
    toc.appendChild(label);

    const list = document.createElement("ol");
    headings.forEach((h, i) => {
      if (!h.id) h.id = `section-${i + 1}`;
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#${h.id}`;
      a.textContent = h.textContent;
      li.appendChild(a);
      list.appendChild(li);
    });
    toc.appendChild(list);

    content.parentNode.insertBefore(toc, content);
    article.classList.add("has-toc");
  }

  // --- reading progress bar, fills as you scroll through the article ---
  const bar = document.createElement("div");
  bar.className = "reading-progress";
  document.body.appendChild(bar);

  const updateProgress = () => {
    const rect = article.getBoundingClientRect();
    const total = article.offsetHeight - window.innerHeight;
    const scrolled = Math.min(Math.max(-rect.top, 0), total);
    const pct = total > 0 ? (scrolled / total) * 100 : 0;
    bar.style.width = `${pct}%`;
  };
  document.addEventListener("scroll", updateProgress, { passive: true });
  updateProgress();

  // --- back to top, only worth showing once the piece is reasonably long ---
  if (words > 600) {
    const back = document.createElement("a");
    back.href = "#top";
    back.className = "back-to-top";
    back.textContent = "↑ Back to top";
    article.appendChild(back);
  }
});
