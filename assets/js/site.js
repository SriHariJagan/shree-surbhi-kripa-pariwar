/* ==========================================================================
   SHREE SURBHI KRIPA PARIWAR — SITE BEHAVIOUR
   Progressive enhancement only. Every page remains readable without this file.
   ========================================================================== */
(function () {
  "use strict";

  document.documentElement.classList.remove("no-js");

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---- Sticky header -------------------------------------------------- */
  var header = document.querySelector("[data-header]");
  function onScroll() {
    if (!header) return;
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---- Mobile menu ---------------------------------------------------- */
  var menu = document.getElementById("site-menu");
  var openBtn = document.querySelector("[data-menu-open]");
  var closeBtn = document.querySelector("[data-menu-close]");
  var lastFocus = null;

  function setMenu(open) {
    if (!menu) return;
    menu.classList.toggle("is-open", open);
    menu.setAttribute("aria-hidden", String(!open));
    document.body.classList.toggle("is-locked", open);
    if (openBtn) openBtn.setAttribute("aria-expanded", String(open));
    if (open) {
      lastFocus = document.activeElement;
      if (closeBtn) closeBtn.focus();
    } else if (lastFocus) {
      lastFocus.focus();
    }
  }

  if (openBtn) openBtn.addEventListener("click", function () { setMenu(true); });
  if (closeBtn) closeBtn.addEventListener("click", function () { setMenu(false); });
  if (menu) {
    menu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () { setMenu(false); });
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      if (menu && menu.classList.contains("is-open")) setMenu(false);
      closeLightbox();
    }
  });

  /* ---- Reveal on scroll ----------------------------------------------- */
  var revealItems = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (!("IntersectionObserver" in window) || reduced) {
    revealItems.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
    );
    revealItems.forEach(function (el) { observer.observe(el); });
    // Safety: if something goes wrong, never leave content invisible.
    window.setTimeout(function () {
      revealItems.forEach(function (el) {
        var box = el.getBoundingClientRect();
        if (box.top < window.innerHeight * 1.2) el.classList.add("is-visible");
      });
    }, 2200);
  }

  /* ---- Seva pillars: image follows the active item -------------------- */
  var pillars = Array.prototype.slice.call(document.querySelectorAll(".pillar"));
  var pillarImages = Array.prototype.slice.call(document.querySelectorAll(".pillar__img"));
  function activatePillar(index) {
    pillarImages.forEach(function (image, i) {
      image.classList.toggle("is-active", i === index);
    });
  }
  pillars.forEach(function (pillar, index) {
    ["mouseenter", "focusin", "click"].forEach(function (type) {
      pillar.addEventListener(type, function () { activatePillar(index); });
    });
  });

  /* ---- Gallery filter ------------------------------------------------- */
  var gallery = document.querySelector("[data-gallery]");
  var filterBar = document.querySelector("[data-filters]");
  var emptyState = document.querySelector("[data-gallery-empty]");

  function visibleGalleryItems() {
    if (!gallery) return [];
    return Array.prototype.slice
      .call(gallery.querySelectorAll(".gallery-item"))
      .filter(function (item) { return !item.hidden; });
  }

  if (filterBar && gallery) {
    filterBar.addEventListener("click", function (event) {
      var button = event.target.closest("[data-filter]");
      if (!button) return;
      var filter = button.getAttribute("data-filter");
      filterBar.querySelectorAll("[data-filter]").forEach(function (item) {
        item.classList.toggle("is-active", item === button);
      });
      var shown = 0;
      gallery.querySelectorAll(".gallery-item").forEach(function (item) {
        var match = filter === "all" || item.getAttribute("data-cat") === filter;
        item.hidden = !match;
        if (match) shown += 1;
      });
      if (emptyState) emptyState.hidden = shown !== 0;
    });
  }

  /* ---- Lightbox ------------------------------------------------------- */
  var lightbox = document.getElementById("lightbox");
  var lbImage = lightbox ? lightbox.querySelector("[data-lb-img]") : null;
  var lbCaption = lightbox ? lightbox.querySelector("[data-lb-caption]") : null;
  var lbCat = lightbox ? lightbox.querySelector("[data-lb-cat]") : null;
  var lbCount = lightbox ? lightbox.querySelector("[data-lb-count]") : null;
  var lbItems = [];
  var lbIndex = 0;
  var lbReturnFocus = null;

  function renderLightbox() {
    if (!lbItems.length) return;
    var item = lbItems[lbIndex];
    var source = item.getAttribute("data-full");
    var caption = item.getAttribute("data-caption") || "";
    var category = item.getAttribute("data-cat") || "";
    if (lbImage) {
      lbImage.src = source;
      lbImage.alt = caption;
    }
    if (lbCaption) lbCaption.textContent = caption;
    if (lbCat) lbCat.textContent = category.replace("-", " ");
    if (lbCount) lbCount.textContent = (lbIndex + 1) + " / " + lbItems.length;
  }

  function openLightbox(item) {
    if (!lightbox) return;
    lbItems = visibleGalleryItems();
    lbIndex = Math.max(0, lbItems.indexOf(item));
    lbReturnFocus = document.activeElement;
    renderLightbox();
    lightbox.classList.add("is-open");
    lightbox.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-locked");
    var close = lightbox.querySelector("[data-lb-close]");
    if (close) close.focus();
  }

  function closeLightbox() {
    if (!lightbox || !lightbox.classList.contains("is-open")) return;
    lightbox.classList.remove("is-open");
    lightbox.setAttribute("aria-hidden", "true");
    document.body.classList.remove("is-locked");
    if (lbReturnFocus) lbReturnFocus.focus();
  }

  function stepLightbox(direction) {
    if (!lbItems.length) return;
    lbIndex = (lbIndex + direction + lbItems.length) % lbItems.length;
    renderLightbox();
  }

  if (gallery && lightbox) {
    gallery.addEventListener("click", function (event) {
      var item = event.target.closest(".gallery-item");
      if (item) openLightbox(item);
    });
    gallery.addEventListener("keydown", function (event) {
      if (event.key !== "Enter" && event.key !== " ") return;
      var item = event.target.closest(".gallery-item");
      if (!item) return;
      event.preventDefault();
      openLightbox(item);
    });

    lightbox.querySelector("[data-lb-close]").addEventListener("click", closeLightbox);
    lightbox.querySelector("[data-lb-prev]").addEventListener("click", function () { stepLightbox(-1); });
    lightbox.querySelector("[data-lb-next]").addEventListener("click", function () { stepLightbox(1); });

    lightbox.addEventListener("click", function (event) {
      if (event.target === lightbox) closeLightbox();
    });

    document.addEventListener("keydown", function (event) {
      if (!lightbox.classList.contains("is-open")) return;
      if (event.key === "ArrowLeft") stepLightbox(-1);
      if (event.key === "ArrowRight") stepLightbox(1);
    });

    var touchStart = null;
    lightbox.addEventListener("touchstart", function (event) {
      touchStart = event.changedTouches[0].clientX;
    }, { passive: true });
    lightbox.addEventListener("touchend", function (event) {
      if (touchStart === null) return;
      var delta = event.changedTouches[0].clientX - touchStart;
      if (Math.abs(delta) > 48) stepLightbox(delta > 0 ? -1 : 1);
      touchStart = null;
    }, { passive: true });
  }

  /* ---- Copy to clipboard ---------------------------------------------- */
  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    try { document.execCommand("copy"); } catch (error) { /* ignore */ }
    document.body.removeChild(area);
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-copy]");
    if (!button) return;
    var value = button.getAttribute("data-copy");
    var original = button.getAttribute("data-copy-label") || button.textContent;
    var copied = button.getAttribute("data-copied-label") || "Copied";
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(value).catch(function () { fallbackCopy(value); });
    } else {
      fallbackCopy(value);
    }
    button.textContent = copied;
    button.classList.add("is-copied");
    window.setTimeout(function () {
      button.textContent = original;
      button.classList.remove("is-copied");
    }, 1800);
  });

  /* ---- Forms: deliver by email without a server of our own ------------ */
  document.addEventListener("submit", function (event) {
    var form = event.target.closest("form[data-form]");
    if (!form) return;
    event.preventDefault();

    var data = new FormData(form);
    var lines = [];
    data.forEach(function (value, key) {
      if (key.charAt(0) === "_") return;
      var text = String(value).trim();
      if (text) lines.push(key.replace(/([A-Z])/g, " $1").replace(/^./, function (c) { return c.toUpperCase(); }) + ": " + text);
    });

    var email = form.getAttribute("data-email") || "";
    var subject = form.getAttribute("data-subject") || "Website enquiry";
    var endpoint = form.getAttribute("data-ajax") || "";
    var success = form.querySelector("[data-success]");
    var error = form.querySelector("[data-error]");
    var button = form.querySelector('button[type="submit"]');

    function openMailApp() {
      if (!email) return;
      window.location.href = "mailto:" + email +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(lines.join("\n\n"));
    }

    function show(el) {
      if (success) success.classList.remove("is-visible");
      if (error) error.classList.remove("is-visible");
      if (!el) return;
      el.classList.add("is-visible");
      el.setAttribute("tabindex", "-1");
      el.focus({ preventScroll: true });
    }

    if (!/^https?:/i.test(endpoint)) {
      openMailApp();
      show(success);
      form.reset();
      return;
    }

    if (button) button.disabled = true;
    fetch(endpoint, {
      method: "POST",
      body: data,
      headers: { Accept: "application/json" }
    })
      .then(function (response) {
        return response.json().then(function (payload) {
          if (!response.ok || payload.success === "false") throw new Error("Delivery failed");
          return payload;
        });
      })
      .then(function () {
        show(success);
        form.reset();
      })
      .catch(function () {
        openMailApp();
        show(error);
      })
      .then(function () {
        if (button) button.disabled = false;
      });
  });

  /* ---- Open a linked accordion ---------------------------------------- */
  if (window.location.hash) {
    var target = document.querySelector(window.location.hash);
    if (target && target.tagName === "DETAILS") target.open = true;
  }
})();
