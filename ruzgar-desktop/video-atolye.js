/**
 * Video Atölyesi — düzen panelleri (Tercüme motoru ile aynı dock modeli)
 */
(function initRuzgarVideoAtolye(global) {
  function $(id) {
    return document.getElementById(id);
  }

  let flashFn = (msg) => {
    try {
      global.dispatchEvent(
        new CustomEvent("ruzgar-sidebar-notify", { detail: { message: String(msg || "") } }),
      );
    } catch {
      /* ignore */
    }
  };
  let openExportFn = null;
  let activeDuzenDock = "";

  const DUZEN_ORIGINS = new Map();

  const DUZEN_PANELS = {
    preview: {
      title: "Önizleme",
      focusOnly: true,
      onOpen: () => {
        window.setTimeout(() => {
          $("video-timeline-wrap")?.scrollIntoView?.({ behavior: "smooth", block: "nearest" });
        }, 60);
      },
    },
    meta: {
      title: "Teknik özet",
      placement: "right",
      host: true,
      collect: () => {
        const el = document.querySelector("#page-video .video-col-meta");
        return el ? [el] : [];
      },
    },
    download: {
      title: "URL indir",
      placement: "right",
      host: true,
      collect: () => {
        const el = $("video-anchor-download");
        return el ? [el] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-download-url")?.focus?.({ preventScroll: true }), 80);
      },
    },
    trim: {
      title: "Kes · Dönüştür · Birleştir",
      placement: "right",
      host: true,
      collect: () => {
        const el = $("video-anchor-v2");
        return el ? [el] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-start-sec")?.focus?.({ preventScroll: true }), 80);
      },
    },
    subtitle: {
      title: "Altyazı göm",
      placement: "right",
      host: true,
      collect: () => {
        const v3 = $("video-anchor-v3");
        const block = v3?.querySelector(".video-v3-block:not(.video-v3-block-spaced)");
        return block ? [block] : v3 ? [v3] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-rel-burn-sub")?.focus?.({ preventScroll: true }), 80);
      },
    },
    mux: {
      title: "Harici ses",
      placement: "right",
      host: true,
      collect: () => {
        const el = $("video-anchor-v3-mux");
        return el ? [el] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-rel-mux-video")?.focus?.({ preventScroll: true }), 80);
      },
    },
    edit: {
      title: "Görsel kurgu",
      placement: "center",
      host: true,
      collect: () => {
        const el = $("video-anchor-v5");
        return el ? [el] : [];
      },
    },
    create: {
      title: "Video oluştur",
      placement: "center",
      host: true,
      collect: () => {
        const el = $("video-anchor-create");
        return el ? [el] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-create-text")?.focus?.({ preventScroll: true }), 80);
      },
    },
    tercume: {
      title: "Altyazı → Tercüme",
      placement: "right",
      host: true,
      collect: () => {
        const el = $("video-anchor-v4");
        return el ? [el] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-rel-sub-translate")?.focus?.({ preventScroll: true }), 80);
      },
    },
    dub: {
      title: "Dublaj (S6)",
      placement: "right",
      host: true,
      collect: () => {
        const el = $("video-anchor-dub");
        return el ? [el] : [];
      },
      onOpen: () => {
        window.setTimeout(() => $("video-rel-dub")?.focus?.({ preventScroll: true }), 80);
      },
    },
  };

  function stashDuzenNode(node) {
    if (!node || DUZEN_ORIGINS.has(node)) return;
    DUZEN_ORIGINS.set(node, { parent: node.parentNode, next: node.nextSibling });
  }

  function restoreDuzenNode(node) {
    const o = DUZEN_ORIGINS.get(node);
    if (!o?.parent) return;
    try {
      o.parent.insertBefore(node, o.next);
    } catch {
      o.parent.appendChild(node);
    }
  }

  function restoreAllDuzenNodes() {
    [...DUZEN_ORIGINS.keys()].forEach(restoreDuzenNode);
  }

  function makeDuzenCloseBtn() {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "video-duzen-close";
    btn.setAttribute("aria-label", "Paneli kapat");
    btn.title = "Kapat";
    btn.textContent = "×";
    btn.addEventListener("click", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      closeDuzenDock();
    });
    return btn;
  }

  function ensureDuzenCloseChrome(el, title) {
    if (!el) return;
    let head = el.querySelector(":scope > .video-duzen-chrome");
    if (!head) {
      head = document.createElement("header");
      head.className = "video-duzen-chrome";
      el.insertBefore(head, el.firstChild);
    }
    let tit = head.querySelector(".video-duzen-chrome-title");
    if (!tit) {
      tit = document.createElement("span");
      tit.className = "video-duzen-chrome-title";
      head.insertBefore(tit, head.firstChild);
    }
    tit.textContent = title;
    if (!head.querySelector(".video-duzen-close")) head.appendChild(makeDuzenCloseBtn());
  }

  function ensureDuzenFloatHost() {
    let host = $("video-duzen-float-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "video-duzen-float-host";
      host.className = "video-duzen-float-host";
      host.hidden = true;
      host.setAttribute("aria-hidden", "true");
    }
    if (host.parentElement !== document.body) {
      document.body.appendChild(host);
    }
    return host;
  }

  function ensureDuzenBackdrop() {
    let backdrop = $("video-duzen-backdrop");
    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.id = "video-duzen-backdrop";
      backdrop.className = "video-duzen-backdrop";
      backdrop.hidden = true;
      backdrop.setAttribute("aria-hidden", "true");
      backdrop.addEventListener("click", () => closeDuzenDock());
    }
    if (backdrop.parentElement !== document.body) {
      document.body.appendChild(backdrop);
    }
    return backdrop;
  }

  function unhideDuzenNode(node) {
    if (!node) return;
    node.hidden = false;
    node.style.removeProperty("display");
    node.classList.remove("video-ops-parked");
  }

  function parkDuzenNode(node) {
    if (!node) return;
    node.classList.add("video-ops-parked");
    node.style.setProperty("display", "none", "important");
  }

  function isVideoPageVisible() {
    const page = $("page-video");
    return !!(page && !page.hidden);
  }

  /** Sağ sütun panellerini park et — dock açıkken taşınan düğümlere dokunma */
  function parkVideoOpsColumn() {
    const page = $("page-video");
    if (!page) return;
    const ops = page.querySelector(".video-split-ops");
    if (ops) ops.style.setProperty("display", "none", "important");
    page.querySelectorAll(".video-ops-scroll > *").forEach((el) => {
      if (el.closest("#video-duzen-float-host")) return;
      parkDuzenNode(el);
    });
  }

  function hideAllDuzenPanels() {
    document.querySelectorAll("#page-video .video-duzen-open, #video-duzen-float-host .video-duzen-open").forEach((el) => {
      el.classList.remove("video-duzen-open");
      el.removeAttribute("data-duzen-place");
      el.style.removeProperty("display");
      el.querySelector(":scope > .video-duzen-chrome")?.remove();
      if (el.dataset.duzenWasHidden === "1") {
        el.hidden = true;
        delete el.dataset.duzenWasHidden;
      }
    });
    restoreAllDuzenNodes();
    const host = $("video-duzen-float-host");
    if (host) {
      host.textContent = "";
      host.hidden = true;
      host.setAttribute("aria-hidden", "true");
    }
    parkVideoOpsColumn();
  }

  function mountDuzenHostPanel(cfg) {
    const nodes = cfg.collect?.() || [];
    if (!nodes.length) return false;
    const host = ensureDuzenFloatHost();
    host.innerHTML = "";
    const shell = document.createElement("aside");
    shell.className = "video-duzen-panel video-duzen-open";
    shell.dataset.duzenPlace = cfg.placement || "right";
    ensureDuzenCloseChrome(shell, cfg.title);
    const body = document.createElement("div");
    body.className = "video-duzen-host-body";
    nodes.forEach((node) => {
      stashDuzenNode(node);
      unhideDuzenNode(node);
      body.appendChild(node);
    });
    shell.appendChild(body);
    host.appendChild(shell);
    host.hidden = false;
    host.setAttribute("aria-hidden", "false");
    return true;
  }

  function showDuzenRoots(cfg) {
    const roots = (cfg.roots?.() || []).filter(Boolean);
    if (!roots.length) return false;
    const disp = cfg.display || "flex";
    roots.forEach((el) => {
      if (el.hidden) {
        el.dataset.duzenWasHidden = "1";
        el.hidden = false;
      }
      ensureDuzenCloseChrome(el, cfg.title);
      el.classList.add("video-duzen-open");
      el.dataset.duzenPlace = cfg.placement || "left";
      el.style.setProperty("display", disp, "important");
    });
    return true;
  }

  function syncQuickBtnActive() {
    document.querySelectorAll(".video-quick-btn[data-video-dock]").forEach((btn) => {
      const dock = btn.getAttribute("data-video-dock") || "";
      btn.classList.toggle("is-active", !!dock && dock === activeDuzenDock);
    });
  }

  function syncDuzenDockDisplay() {
    const dock = String(activeDuzenDock || "").trim();
    hideAllDuzenPanels();
    if (!dock) return;
    const cfg = DUZEN_PANELS[dock];
    if (!cfg) return;
    if (cfg.focusOnly) {
      cfg.onOpen?.();
      syncQuickBtnActive();
      return;
    }
    cfg.onOpen?.();
    let ok = false;
    if (cfg.host) ok = mountDuzenHostPanel(cfg);
    else ok = showDuzenRoots(cfg);
    if (!ok) {
      flashFn(`Panel açılamadı: ${cfg.title}`);
      activeDuzenDock = "";
      delete document.body.dataset.videoDock;
      const backdrop = $("video-duzen-backdrop");
      if (backdrop) backdrop.hidden = true;
    }
    syncQuickBtnActive();
  }

  function openDuzenDock(name) {
    const n = String(name || "").trim();
    if (!n) return;
    const cfg = DUZEN_PANELS[n];
    if (document.body.dataset.motor !== "video") {
      document.body.dataset.motor = "video";
    }
    activeDuzenDock = n;
    document.body.dataset.videoDock = n;
    const backdrop = ensureDuzenBackdrop();
    if (cfg?.focusOnly) {
      backdrop.hidden = true;
    } else {
      backdrop.hidden = false;
      backdrop.setAttribute("aria-hidden", "false");
    }
    syncDuzenDockDisplay();
    syncQuickBtnActive();
  }

  function toggleDuzenDock(name) {
    const n = String(name || "").trim();
    if (activeDuzenDock === n) closeDuzenDock();
    else openDuzenDock(n);
  }

  function closeDuzenDock() {
    activeDuzenDock = "";
    delete document.body.dataset.videoDock;
    const backdrop = $("video-duzen-backdrop");
    if (backdrop) backdrop.hidden = true;
    hideAllDuzenPanels();
    syncQuickBtnActive();
  }

  function syncVideoLayout(active, opts = {}) {
    if (!active) {
      closeDuzenDock();
      document.body.classList.remove("video-motor-active", "video-cinema-mode");
      document.getElementById("panel-main")?.classList.remove("video-cinema-main");
      document.getElementById("dynamic-workbench")?.classList.remove("video-cinema-workbench");
      if (document.body.dataset.motor === "video") {
        delete document.body.dataset.motor;
      }
      return;
    }
    document.body.dataset.motor = "video";
    document.body.classList.add("video-motor-active", "video-cinema-mode");
    document.getElementById("panel-main")?.classList.add("video-cinema-main");
    document.getElementById("dynamic-workbench")?.classList.add("video-cinema-workbench");
    parkVideoOpsColumn();
    ensureDuzenFloatHost();
    const backdrop = ensureDuzenBackdrop();
    if (!opts.soft) {
      hideAllDuzenPanels();
    } else {
      parkVideoOpsColumn();
      if (activeDuzenDock) syncDuzenDockDisplay();
    }
    syncQuickBtnActive();
  }

  /** Motor paneli daralt/genişlet — dock kapanmadan kabuk yenile */
  function relayoutShell() {
    if (!isVideoPageVisible()) return;
    document.body.dataset.motor = "video";
    document.body.classList.add("video-motor-active", "video-cinema-mode");
    document.getElementById("panel-main")?.classList.add("video-cinema-main");
    document.getElementById("dynamic-workbench")?.classList.add("video-cinema-workbench");
    parkVideoOpsColumn();
    if (activeDuzenDock) syncDuzenDockDisplay();
    syncQuickBtnActive();
  }

  function runPanelAction(action) {
    const a = String(action || "").trim();
    const dockMap = {
      "video:preview": "preview",
      "video:timeline": "preview",
      "video:meta": "meta",
      "video:download": "download",
      "video:youtube": "download",
      "video:trim": "trim",
      "video:subtitle": "subtitle",
      "video:subtitles": "subtitle",
      "video:mux": "mux",
      "video:export-audio": "mux",
      "video:create": "create",
      "video:edit": "edit",
      "video:tercume": "tercume",
      "video:sub-tercume": "tercume",
      "video:dub": "dub",
    };
    if (dockMap[a]) {
      openDuzenDock(dockMap[a]);
      return true;
    }
    if (a === "video:mark-in") {
      openDuzenDock("preview");
      window.setTimeout(() => {
        $("btn-video-mark-in")?.click?.();
      }, 120);
      return true;
    }
    if (a === "video:export") {
      if (typeof openExportFn === "function") openExportFn();
      else $("btn-video-open-export")?.click?.();
      return true;
    }
    return false;
  }

  function wire() {
    $("video-duzen-backdrop")?.addEventListener("click", () => closeDuzenDock());
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && activeDuzenDock && document.body.dataset.motor === "video") {
        closeDuzenDock();
      }
    });
  }

  function init(options = {}) {
    if (options.flash) flashFn = options.flash;
    if (options.openVideoExportFolder) openExportFn = options.openVideoExportFolder;
    wire();
    ensureDuzenFloatHost();
    ensureDuzenBackdrop();
    syncVideoLayout(document.body.dataset.motor === "video");
    const motors = document.querySelector(".panel-motors");
    if (motors && motors.dataset.videoRelayoutObs !== "1" && typeof ResizeObserver !== "undefined") {
      motors.dataset.videoRelayoutObs = "1";
      new ResizeObserver(() => {
        if (document.body.dataset.motor !== "video") return;
        parkVideoOpsColumn();
      }).observe(motors);
    }
  }

  global.RuzgarVideoAtolye = {
    DUZEN_PANELS,
    init,
    wire,
    openDuzenDock,
    closeDuzenDock,
    toggleDuzenDock,
    syncVideoLayout,
    relayoutShell,
    syncDuzenDockDisplay,
    runPanelAction,
    getActiveDock: () => activeDuzenDock,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", wire, { once: true });
  } else {
    wire();
  }
})(typeof window !== "undefined" ? window : globalThis);
