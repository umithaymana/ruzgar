/**
 * Rüzgar — sürüklenebilir bölme ayırıcıları (motor, sohbet, tüm atölye sayfaları).
 */
(function initRuzgarSplitModule(global) {
  const STORAGE_KEY = "ruzgarSplit.v1";

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  function saveStateKey(key, value) {
    const state = loadState();
    state[key] = Math.round(value);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* ignore */
    }
  }

  function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
  }

  function pageVisible(pageSel) {
    if (!pageSel) return true;
    const el = document.querySelector(pageSel);
    return Boolean(el && !el.hidden);
  }

  function applySavedCssVars() {
    const st = loadState();
    const root = document.documentElement;
    if (document.body.classList.contains("ui-motors-compact")) {
      root.style.setProperty("--ruzgar-motors-w", "52px");
    } else if (typeof st.motors === "number") {
      root.style.setProperty("--ruzgar-motors-w", `${st.motors}px`);
    }
    if (typeof st.chat === "number") root.style.setProperty("--ruzgar-chat-w", `${st.chat}px`);
  }

  function chatMainSplitRoot() {
    const row = document.getElementById("tercume-center-row");
    if (!row) return document.querySelector(".layout.layout-v2");
    if (getComputedStyle(row).display === "contents") return document.querySelector(".layout.layout-v2");
    return row;
  }

  class PaneSplit {
    constructor(opts) {
      this.key = opts.key;
      this.root = opts.root;
      this.beforeEl = opts.before;
      this.min = opts.min ?? 120;
      this.max = opts.max ?? 720;
      this.defaultSize = opts.defaultSize ?? opts.defaultWidth ?? 280;
      this.axis = opts.axis === "vertical" ? "vertical" : "horizontal";
      this.mode = opts.mode ?? (this.axis === "vertical" ? "overlay-v" : "overlay");
      this.cssVar = opts.cssVar || "";
      this.cssTarget = opts.cssTarget || document.documentElement;
      this.visible = opts.visible ?? (() => true);
      this.onResize = opts.onResize;
      this._handle = null;
      this._reposition = null;
    }

    getSize() {
      const saved = loadState()[this.key];
      if (typeof saved === "number" && saved > 0) return saved;
      if (this.mode === "cssVar" && this.cssVar) {
        const raw = getComputedStyle(this.cssTarget).getPropertyValue(this.cssVar).trim();
        const n = parseFloat(raw);
        if (Number.isFinite(n) && n > 0) return n;
      }
      const rect = this.beforeEl.getBoundingClientRect();
      const n = this.axis === "vertical" ? rect.height : rect.width;
      if (n > 0) return n;
      return this.defaultSize;
    }

    applySize(px) {
      const size = clamp(px, this.min, this.max);
      if (this.mode === "cssVar" && this.cssVar) {
        this.cssTarget.style.setProperty(this.cssVar, `${size}px`);
      } else if (this.onResize) {
        this.onResize(size);
      } else if (this.axis === "vertical") {
        this.beforeEl.style.flex = `0 0 ${size}px`;
        this.beforeEl.style.height = `${size}px`;
        this.beforeEl.style.minHeight = `${size}px`;
        this.beforeEl.style.maxHeight = `${size}px`;
      } else {
        this.beforeEl.style.flex = `0 0 ${size}px`;
        this.beforeEl.style.width = `${size}px`;
        this.beforeEl.style.minWidth = `${size}px`;
        this.beforeEl.style.maxWidth = `${size}px`;
      }
      saveStateKey(this.key, size);
      if (this._reposition) this._reposition();
      return size;
    }

    mount() {
      if (!this.root || !this.beforeEl || this.beforeEl.dataset.splitMounted === "1") return;
      this.beforeEl.dataset.splitMounted = "1";
      this.applySize(this.getSize());

      const handle = document.createElement("div");
      handle.className = "ruzgar-split-handle";
      if (this.mode.startsWith("overlay")) {
        handle.classList.add(
          this.axis === "vertical" ? "ruzgar-split-handle--overlay-v" : "ruzgar-split-handle--overlay",
        );
      }
      handle.dataset.splitKey = this.key;
      handle.setAttribute("role", "separator");
      handle.setAttribute("aria-orientation", this.axis === "vertical" ? "horizontal" : "vertical");
      handle.setAttribute("aria-label", "Bölme boyutunu ayarla");
      handle.tabIndex = 0;
      this._handle = handle;

      if (this.mode.startsWith("overlay")) {
        if (getComputedStyle(this.root).position === "static") {
          this.root.style.position = "relative";
        }
        this.root.appendChild(handle);
        this._reposition = () => {
          if (!this.visible()) {
            handle.hidden = true;
            return;
          }
          handle.hidden = false;
          const r = this.beforeEl.getBoundingClientRect();
          const rootR = this.root.getBoundingClientRect();
          if (this.axis === "vertical") {
            handle.style.left = `${Math.round(r.left - rootR.left)}px`;
            handle.style.top = `${Math.round(r.bottom - rootR.top - 2)}px`;
            handle.style.width = `${Math.round(r.width)}px`;
            handle.style.height = "";
          } else {
            handle.style.left = `${Math.round(r.right - rootR.left - 2)}px`;
            handle.style.top = "0";
            handle.style.width = "";
            handle.style.height = `${Math.round(rootR.height)}px`;
          }
        };
        this._reposition();
        window.addEventListener("resize", this._reposition);
      } else {
        this.beforeEl.insertAdjacentElement("afterend", handle);
      }

      handle.addEventListener("pointerdown", (ev) => this._onDown(ev));
      handle.addEventListener("keydown", (ev) => this._onKey(ev));
    }

    _onKey(ev) {
      if (!this.visible()) return;
      let step = 0;
      if (this.axis === "vertical") {
        if (ev.key === "ArrowUp") step = -12;
        else if (ev.key === "ArrowDown") step = 12;
        else return;
      } else if (ev.key === "ArrowLeft") step = -12;
      else if (ev.key === "ArrowRight") step = 12;
      else return;
      ev.preventDefault();
      this.applySize(this.getSize() + step);
    }

    _onDown(ev) {
      if (!this.visible()) return;
      if (ev.button !== 0) return;
      ev.preventDefault();
      const handle = this._handle;
      handle.classList.add("is-active");
      document.body.classList.add("ruzgar-split-dragging");
      if (this.axis === "vertical") document.body.classList.add("ruzgar-split-dragging--v");
      const start = this.axis === "vertical" ? ev.clientY : ev.clientX;
      const startSize = this.getSize();

      const onMove = (e) => {
        const delta = (this.axis === "vertical" ? e.clientY : e.clientX) - start;
        this.applySize(startSize + delta);
      };
      const onUp = () => {
        handle.classList.remove("is-active");
        document.body.classList.remove("ruzgar-split-dragging", "ruzgar-split-dragging--v");
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
      };

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    }
  }

  function mountGridSplit(def) {
    document.querySelectorAll(def.root).forEach((root) => {
      const before = root.querySelector(def.before);
      if (!before) return;
      const key = def.keyUnique ? `${def.key}-${root.id || root.className}` : def.key;
      const visible = () => {
        if (def.page && !pageVisible(def.page)) return false;
        if (typeof def.visible === "function") return def.visible(root, before);
        return root.offsetParent !== null && getComputedStyle(root).display !== "none";
      };
      const sp = new PaneSplit({
        key,
        root,
        before,
        axis: def.axis || "horizontal",
        defaultSize: def.defaultSize,
        min: def.min,
        max: def.max,
        visible,
        onResize: def.onResize
          ? (size) => def.onResize(root, before, size)
          : (size) => {
              if (def.axis === "vertical") {
                root.style.gridTemplateRows = `${size}px minmax(0, 1fr)`;
              } else {
                root.style.gridTemplateColumns = `${size}px minmax(0, 1fr)`;
              }
            },
      });
      sp.mount();
      mounted.push(sp);
      const saved = loadState()[key];
      if (typeof saved === "number" && saved > 0 && def.onResize) {
        def.onResize(root, before, saved);
      } else if (typeof saved === "number" && saved > 0) {
        if (def.axis === "vertical") root.style.gridTemplateRows = `${saved}px minmax(0, 1fr)`;
        else root.style.gridTemplateColumns = `${saved}px minmax(0, 1fr)`;
      }
    });
  }

  const WORKBENCH_SPLITS = [
    {
      root: ".code-workbench",
      before: ".code-sidebar",
      key: "code-sidebar",
      page: "#page-programlama",
      defaultSize: 240,
      min: 160,
      max: 480,
    },
    {
      root: ".okuma-workbench",
      before: ".okuma-sidebar",
      key: "okuma-sidebar",
      defaultSize: 260,
      min: 140,
      max: 420,
      visible: (root) => getComputedStyle(root).display !== "none",
    },
    {
      root: ".mimar-foto-layout",
      before: ".mimar-foto-strip",
      key: "mimar-foto-strip",
      page: "#page-mimar",
      defaultSize: 150,
      min: 100,
      max: 280,
      visible: () => document.body.dataset.mimarTab === "fotograf",
    },
    {
      root: ".mimar-sanat-layout",
      before: ".mimar-sanat-gallery",
      key: "mimar-sanat-gallery",
      page: "#page-mimar",
      defaultSize: 0,
      min: 200,
      max: 900,
      visible: () => document.body.dataset.mimarTab === "resim-sanat",
      onResize: (root, _before, w) => {
        root.style.gridTemplateColumns = `${w}px minmax(220px, 1fr)`;
      },
    },
    {
      root: ".mimar-tasarim-layout",
      before: ".mimar-tasarim-stage",
      key: "mimar-tasarim-stage",
      page: "#page-mimar",
      defaultSize: 0,
      min: 280,
      max: 1200,
      visible: () => document.body.dataset.mimarTab === "tasarim",
      onResize: (root, _before, w) => {
        root.style.gridTemplateColumns = `minmax(0, ${w}px) minmax(160px, 1fr)`;
      },
    },
    {
      root: ".ses-workbench",
      before: ".ses-col-file",
      key: "ses-file-col",
      page: "#page-ses",
      defaultSize: 300,
      min: 200,
      max: 520,
    },
    {
      root: ".hizir-split--vitrin",
      before: ".hizir-col-vitrin",
      key: "hizir-vitrin",
      page: "#page-hizir",
      defaultSize: 0,
      min: 280,
      max: 1200,
      onResize: (root, _before, w) => {
        root.style.gridTemplateColumns = `${w}px minmax(240px, 1fr)`;
      },
    },
    {
      root: "#page-hafiza .hafiza-split",
      before: ".hafiza-analyze-column",
      key: "hafiza-analyze",
      page: "#page-hafiza",
      axis: "vertical",
      defaultSize: 320,
      min: 160,
      max: 700,
      visible: () => {
        const wb = document.getElementById("dynamic-workbench");
        return pageVisible("#page-hafiza") && !wb?.classList.contains("layout-split2");
      },
      onResize: (_root, before, h) => {
        before.style.flex = `0 0 ${h}px`;
        before.style.minHeight = `${h}px`;
        before.style.maxHeight = `${h}px`;
      },
    },
    {
      root: ".code-main",
      before: ".code-editor",
      key: "code-editor-h",
      page: "#page-programlama",
      axis: "vertical",
      defaultSize: 360,
      min: 160,
      max: 900,
      onResize: (root, _before, h) => {
        root.style.gridTemplateRows = `auto auto ${h}px minmax(100px, 1fr)`;
      },
    },
  ];

  function applyWorkbenchGridFromState() {
    const wb = document.getElementById("tercume-workbench");
    if (!wb) return;
    if (document.body.dataset.tercumeUi === "reader") {
      wb.style.setProperty("grid-template-columns", "minmax(0, 1fr)", "important");
      const main = wb.querySelector(".tercume-main");
      if (main) main.style.setProperty("grid-column", "1 / -1", "important");
      return;
    }
    const tab = document.body.dataset.tercumeTab || "calisma";
    const state = loadState();
    const c1 = state["tercume-sidebar"] || 190;
    const c2 = state["tercume-ara"] || 240;
    if (tab === "ara") wb.style.gridTemplateColumns = `${c1}px ${c2}px minmax(0, 1fr)`;
    else if (tab === "calisma") wb.style.gridTemplateColumns = `${c1}px minmax(0, 1fr)`;
  }

  const mounted = [];

  function initCoreSplits() {
    const layout = document.querySelector(".layout.layout-v2");
    if (!layout) return;

    const motors = layout.querySelector(".panel-motors");
    if (motors && motors.dataset.splitMounted !== "1") {
      const sp = new PaneSplit({
        key: "motors",
        root: layout,
        before: motors,
        mode: "cssVar",
        cssVar: "--ruzgar-motors-w",
        defaultSize: 232,
        min: 52,
        max: 400,
        visible: () => !document.body.classList.contains("ui-motors-compact"),
      });
      sp.mount();
      mounted.push(sp);
    }

    const chat = layout.querySelector(".panel-chat");
    const chatRoot = chatMainSplitRoot();
    if (chat && chatRoot && chat.dataset.splitMounted !== "1") {
      const sp = new PaneSplit({
        key: "chat",
        root: chatRoot,
        before: chat,
        mode: "cssVar",
        cssVar: "--ruzgar-chat-w",
        defaultSize: 320,
        min: 220,
        max: 560,
        visible: () => getComputedStyle(chat).display !== "none",
      });
      sp.mount();
      mounted.push(sp);
    }
  }

  function initTercumeSplits() {
    const wb = document.getElementById("tercume-workbench");
    const sidebar = wb?.querySelector(".tercume-sidebar");
    if (wb && sidebar && sidebar.dataset.splitMounted !== "1") {
      const sp = new PaneSplit({
        key: "tercume-sidebar",
        root: wb,
        before: sidebar,
        defaultSize: 190,
        min: 120,
        max: 340,
        visible: () => {
          if (document.body.dataset.tercumeUi === "reader") return false;
          const tab = document.body.dataset.tercumeTab || "calisma";
          return tab === "calisma" || tab === "ara";
        },
        onResize: (size) => {
          if (document.body.dataset.tercumeUi === "reader") return;
          const tab = document.body.dataset.tercumeTab || "calisma";
          const c2 = loadState()["tercume-ara"] || 240;
          if (tab === "ara") wb.style.gridTemplateColumns = `${size}px ${c2}px minmax(0, 1fr)`;
          else wb.style.gridTemplateColumns = `${size}px minmax(0, 1fr)`;
        },
      });
      sp.mount();
      mounted.push(sp);
    }

    const araPanel = document.getElementById("tercume-ara-panel");
    if (wb && araPanel && araPanel.dataset.splitMounted !== "1") {
      const sp = new PaneSplit({
        key: "tercume-ara",
        root: wb,
        before: araPanel,
        defaultSize: 240,
        min: 160,
        max: 420,
        visible: () => document.body.dataset.tercumeTab === "ara",
        onResize: (size) => {
          const c1 = loadState()["tercume-sidebar"] || 190;
          wb.style.gridTemplateColumns = `${c1}px ${size}px minmax(0, 1fr)`;
        },
      });
      sp.mount();
      mounted.push(sp);
    }

    const panels = document.querySelector("#page-tercume .tercume-panels");
    const srcPanel = panels?.querySelector(".tercume-panel:first-child");
    if (panels && srcPanel && srcPanel.dataset.splitMounted !== "1") {
      const sp = new PaneSplit({
        key: "tercume-source",
        root: panels,
        before: srcPanel,
        defaultSize: 400,
        min: 200,
        max: 900,
        visible: () => {
          const tab = document.body.dataset.tercumeTab || "calisma";
          return tab === "calisma" || tab === "ara";
        },
        onResize: (size) => {
          panels.style.gridTemplateColumns = `${size}px minmax(0, 1fr)`;
        },
      });
      sp.mount();
      mounted.push(sp);
      const saved = loadState()["tercume-source"];
      if (typeof saved === "number" && saved >= 200) {
        panels.style.gridTemplateColumns = `${saved}px minmax(0, 1fr)`;
      }
    }
  }

  function initWorkbenchSplits() {
    WORKBENCH_SPLITS.forEach((def) => mountGridSplit(def));
  }

  function refreshAll() {
    applySavedCssVars();
    mounted.forEach((s) => s._reposition?.());
    applyWorkbenchGridFromState();
    WORKBENCH_SPLITS.forEach((def) => {
      const saved = loadState()[def.key];
      if (typeof saved !== "number" || saved <= 0) return;
      document.querySelectorAll(def.root).forEach((root) => {
        if (def.onResize) def.onResize(root, root.querySelector(def.before), saved);
      });
    });
  }

  function initRuzgarSplits() {
    applySavedCssVars();
    initCoreSplits();
    initTercumeSplits();
    initWorkbenchSplits();
    applyWorkbenchGridFromState();
  }

  global.RuzgarSplit = {
    init: initRuzgarSplits,
    refresh: refreshAll,
    applyWorkbenchGridFromState,
    onTercumeTabChange: applyWorkbenchGridFromState,
    loadState,
    _splits: mounted,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => initRuzgarSplits());
  } else {
    initRuzgarSplits();
  }
})(window);
