/* ============================================================
   CRANE Docs — shared chrome
   Injects sidebar + topbar + TOC, handles theme/search/nav.
   Each page sets window.CRANE_PAGE = "<filename>" before this loads.
   ============================================================ */
(function () {
  "use strict";

  var REPO = "https://github.com/cra-norm-engine/crane";
  var DEMO = "https://cra-compliance-tool-1.onrender.com";

  // ---- icons (stroke, 24 viewbox) ----
  var I = {
    overview: '<path d="M3 12 12 3l9 9"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/>',
    rocket:   '<path d="M4.5 16.5 3 21l4.5-1.5"/><path d="M14 4s4 0 6 2 2 6 2 6l-7 7-6-3-3-6Z"/><circle cx="14.5" cy="9.5" r="1.5"/>',
    concepts: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    features: '<path d="m9 11 3 3 8-8"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>',
    scenarios:'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    cra:      '<path d="M12 3 4 6v6c0 5 3.4 7.8 8 9 4.6-1.2 8-4 8-9V6Z"/><path d="m9 12 2 2 4-4"/>',
    config:   '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1Z"/>',
    api:      '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    faq:      '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12" y2="17"/>',
    contrib:  '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M6 9v6a3 3 0 0 0 3 3h6"/>',
    showcase: '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/><path d="m7 10 3 3 5-5"/>',
    install:  '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>'
  };

  // ---- nav model ----
  var NAV = [
    { label: "Getting Started", items: [
      { t: "Overview", f: "index.html", i: "overview" },
      { t: "Quick Start", f: "quickstart.html", i: "rocket" },
      { t: "Installation Guide", f: "installation.html", i: "install" }
    ]},
    { label: "Using CRANE", items: [
      { t: "Core Concepts", f: "concepts.html", i: "concepts" },
      { t: "Feature Reference", f: "features.html", i: "features" },
      { t: "Real-World Scenarios", f: "scenarios.html", i: "scenarios" },
      { t: "Product Showcase", f: "product-showcase.html", i: "showcase" }
    ]},
    { label: "Regulatory", items: [
      { t: "CRA Context", f: "cra-context.html", i: "cra" }
    ]},
    { label: "Operations", items: [
      { t: "Configuration & Deployment", f: "configuration.html", i: "config" },
      { t: "Database Implementation", f: "database.html", i: "api" },
      { t: "File Upload & Management", f: "file-upload.html", i: "api" },
      { t: "API Reference", f: "api.html", i: "api" }
    ]},
    { label: "Help", items: [
      { t: "FAQ & Troubleshooting", f: "faq.html", i: "faq" },
      { t: "Contributing & Roadmap", f: "contributing.html", i: "contrib" }
    ]}
  ];

  // flat order for pager
  var FLAT = [];
  NAV.forEach(function (g) { g.items.forEach(function (it) { FLAT.push(it); }); });

  var current = window.CRANE_PAGE || "index.html";

  function svg(paths, cls) {
    return '<svg class="' + (cls || "") + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + paths + "</svg>";
  }

  // ---- THEME (also set inline in <head> to avoid FOUC) ----
  function applyTheme(t) {
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("crane-theme", t); } catch (e) {}
  }
  function currentTheme() {
    return document.documentElement.getAttribute("data-theme") || "light";
  }

  // ---- build sidebar ----
  function buildSidebar() {
    var nav = NAV.map(function (g) {
      var links = g.items.map(function (it) {
        var active = it.f === current ? " active" : "";
        return '<a class="nav-link' + active + '" href="' + it.f + '" data-title="' + it.t.toLowerCase() + '">' +
          svg(I[it.i], "ni") + "<span>" + it.t + "</span></a>";
      }).join("");
      return '<div class="nav-group" data-group="' + g.label.toLowerCase() + '">' +
        '<div class="nav-group-label">' + g.label + "</div>" + links + "</div>";
    }).join("");

    return '' +
      '<aside class="sidebar" id="sidebar">' +
        '<a class="brand" href="index.html">' +
          '<span class="brand-logo">' +
            '<span class="brand-wordmark"><span class="brand-cra">CRA</span><span class="brand-ne">NE</span></span>' +
            '<span class="brand-motto">Conformity by design</span>' +
          '</span>' +
        '</a>' +
        '<div class="nav-search"><input type="search" id="navSearch" placeholder="Search docs\u2026" autocomplete="off" spellcheck="false"></div>' +
        '<nav class="nav" id="navList">' + nav + '<div class="nav-empty" id="navEmpty" hidden>No pages match.</div></nav>' +
      '</aside>';
  }

  // ---- build topbar ----
  function buildTopbar() {
    var cur = FLAT.filter(function (x) { return x.f === current; })[0] || { t: "Docs" };
    var group = "";
    NAV.forEach(function (g) { g.items.forEach(function (it) { if (it.f === current) group = g.label; }); });
    return '' +
      '<header class="topbar">' +
        '<button class="tb-btn tb-icon menu-btn" id="menuBtn" aria-label="Menu">' + svg('<line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>') + '</button>' +
        '<nav class="crumbs"><span class="crumb-hide">' + group + '</span><span class="sep crumb-hide">/</span><span class="here">' + cur.t + '</span></nav>' +
        '<div class="topbar-spacer"></div>' +
        '<div class="topbar-actions">' +
          '<a class="tb-btn" href="' + DEMO + '" target="_blank" rel="noopener">' + svg('<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>') + '<span class="lbl">Live demo</span></a>' +
          '<a class="tb-btn tb-icon" href="' + REPO + '" target="_blank" rel="noopener" aria-label="GitHub repository">' + svg('<path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>') + '</a>' +
          '<button class="tb-btn tb-icon theme-toggle" id="themeToggle" aria-label="Toggle theme">' +
            svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>', "sun") +
            svg('<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>', "moon") +
          '</button>' +
        '</div>' +
      '</header>';
  }

  // ---- build pager ----
  function buildPager() {
    var idx = -1;
    FLAT.forEach(function (x, k) { if (x.f === current) idx = k; });
    if (idx < 0) return "";
    var prev = FLAT[idx - 1], next = FLAT[idx + 1];
    var html = "";
    if (prev) html += '<a href="' + prev.f + '"><div class="dir">\u2190 Previous</div><div class="pg-title">' + prev.t + '</div></a>';
    if (next) html += '<a class="next" href="' + next.f + '"><div class="dir">Next \u2192</div><div class="pg-title">' + next.t + '</div></a>';
    return html ? '<nav class="pager">' + html + "</nav>" : "";
  }

  // ---- build TOC from headings ----
  function buildTOC() {
    var article = document.querySelector(".article");
    if (!article) return;
    var heads = article.querySelectorAll("h2, h3");
    var toc = document.getElementById("tocList");
    if (!toc) return;
    if (!heads.length) { toc.innerHTML = '<div class="toc-empty">\u2014</div>'; return; }
    heads.forEach(function (h) {
      if (!h.id) {
        h.id = h.textContent.trim().toLowerCase().replace(/[^\w\s-]/g, "").replace(/\s+/g, "-");
      }
      // anchor link on heading
      var a = document.createElement("a");
      a.href = "#" + h.id; a.className = "anchor"; a.textContent = "#";
      a.setAttribute("aria-label", "Link to section");
      h.appendChild(a);
    });
    var links = "";
    heads.forEach(function (h) {
      var sub = h.tagName === "H3" ? " sub" : "";
      var label = h.textContent.replace(/#$/, "").trim();
      links += '<a class="toc-item' + sub + '" href="#' + h.id + '" data-id="' + h.id + '">' + label + "</a>";
    });
    toc.innerHTML = links;

    // scroll spy
    var tocLinks = toc.querySelectorAll(".toc-item");
    var byId = {};
    tocLinks.forEach(function (l) { byId[l.getAttribute("data-id")] = l; });
    var spy = function () {
      var pos = window.scrollY + 110;
      var activeId = heads[0].id;
      heads.forEach(function (h) { if (h.offsetTop <= pos) activeId = h.id; });
      tocLinks.forEach(function (l) { l.classList.toggle("active", l.getAttribute("data-id") === activeId); });
    };
    window.addEventListener("scroll", spy, { passive: true });
    spy();
  }

  // ---- search filter ----
  function wireSearch() {
    var input = document.getElementById("navSearch");
    if (!input) return;
    var links = Array.prototype.slice.call(document.querySelectorAll(".nav-link"));
    var groups = Array.prototype.slice.call(document.querySelectorAll(".nav-group"));
    var empty = document.getElementById("navEmpty");
    input.addEventListener("input", function () {
      var q = input.value.trim().toLowerCase();
      var any = false;
      links.forEach(function (l) {
        var match = !q || l.getAttribute("data-title").indexOf(q) !== -1;
        l.style.display = match ? "" : "none";
        if (match) any = true;
      });
      groups.forEach(function (g) {
        var visible = g.querySelectorAll('.nav-link:not([style*="display: none"])').length;
        g.style.display = visible ? "" : "none";
      });
      if (empty) empty.hidden = any;
    });
    // keyboard "/" focus
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
        e.preventDefault(); input.focus();
      }
    });
  }

  // ---- copy buttons on code blocks ----
  function wireCopy() {
    var blocks = document.querySelectorAll(".content pre");
    blocks.forEach(function (pre) {
      var wrap = pre.closest(".code-block");
      if (!wrap) {
        wrap = document.createElement("div");
        wrap.className = "code-block";
        pre.parentNode.insertBefore(wrap, pre);
        wrap.appendChild(pre);
      }
      var btn = document.createElement("button");
      btn.className = "copy-btn";
      btn.setAttribute("aria-label", "Copy code");
      btn.innerHTML = svg('<rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>', "ic") +
                      svg('<polyline points="20 6 9 17 4 12"/>', "ok");
      btn.addEventListener("click", function () {
        var text = pre.querySelector("code") ? pre.querySelector("code").innerText : pre.innerText;
        navigator.clipboard.writeText(text).then(function () {
          btn.classList.add("copied");
          setTimeout(function () { btn.classList.remove("copied"); }, 1400);
        });
      });
      wrap.appendChild(btn);
    });
  }

  // ---- mobile nav ----
  function wireMobile() {
    var btn = document.getElementById("menuBtn");
    var scrim = document.querySelector(".scrim");
    if (btn) btn.addEventListener("click", function () { document.body.classList.toggle("nav-open"); });
    if (scrim) scrim.addEventListener("click", function () { document.body.classList.remove("nav-open"); });
    document.querySelectorAll(".nav-link").forEach(function (l) {
      l.addEventListener("click", function () { document.body.classList.remove("nav-open"); });
    });
  }

  // ---- re-apply URL fragment after the DOM is rebuilt ----
  // mount() replaces #doc-root's innerHTML, which destroys/recreates the
  // element the browser had scrolled to on load (and reflows everything as
  // the sidebar + topbar are inserted). The browser does not re-scroll to the
  // hash after a manual innerHTML change, so cross-page deep links such as
  // concepts.html#sbom would land at the wrong offset. Re-apply it here once
  // the layout is final. We re-run on window 'load' too, in case images above
  // the target shift layout as they finish loading.
  function applyHashScroll() {
    if (!location.hash) return;
    var id;
    try { id = decodeURIComponent(location.hash.slice(1)); }
    catch (e) { id = location.hash.slice(1); }
    var target = id && document.getElementById(id);
    if (!target) return;
    requestAnimationFrame(function () { target.scrollIntoView(); });
  }

  // ---- mount ----
  function mount() {
    var root = document.getElementById("doc-root");
    if (!root) return;

    var contentInner = root.innerHTML; // page-authored <main class="content"> markup
    root.innerHTML =
      buildSidebar() +
      '<div class="scrim"></div>' +
      '<div class="main">' +
        buildTopbar() +
        contentInner +
        '<aside class="toc"><div class="toc-label">On this page</div><div id="tocList"></div></aside>' +
      '</div>';

    // append pager + footer into the .content article
    var article = document.querySelector(".article");
    if (article) {
      var pager = buildPager();
      if (pager) article.insertAdjacentHTML("beforeend", pager);
      article.insertAdjacentHTML("beforeend",
        '<footer class="doc-footer">' +
          '<span>CRANE \u00b7 CRA Norm Engine \u00b7 AGPL-3.0</span>' +
          '<span><a href="' + REPO + '" target="_blank" rel="noopener">GitHub</a> \u00b7 ' +
          '<a href="' + REPO + '/blob/main/LICENSE" target="_blank" rel="noopener">License</a> \u00b7 ' +
          '<a href="mailto:amh1036@yahoo.com">Contact</a></span>' +
        '</footer>');
    }

    document.getElementById("themeToggle").addEventListener("click", function () {
      applyTheme(currentTheme() === "dark" ? "light" : "dark");
    });

    buildTOC();
    wireSearch();
    wireCopy();
    wireMobile();

    // The DOM has been rebuilt — restore the deep-link scroll position.
    applyHashScroll();
    window.addEventListener("load", applyHashScroll);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
