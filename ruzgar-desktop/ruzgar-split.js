/**
 * Rüzgar — sürüklenebilir dikey bölme ayırıcıları (Cursor tarzı).
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

  function applySavedCssVars() {
    const st = loadState();
    const root = document.documentElement;
    if (typeof st.motors === "number") root.style.setProperty("--ruzgar-motors-w", `${st.motors}px`);
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
      this.defaultWidth = opts.defaultWidth ?? 280;
      this.mode = opts.mode ?? "flex";
      this.cssVar = opts.cssVar || "";
      this.cssTarget = opts.cssTarget || document.documentElement;
      this.visible = opts.visible ?? (() => true);
      this.onResize = opts.onResize;
      this._handle = null;
      this._reposition = null;
    }

    getWidth() {
      const saved = loadState()[this.key];
      if (typeof saved === "number" && saved > 0) return saved;
      if (this.mode === "cssVar" && this.cssVar) {
        const raw = getComputedStyle(this.cssTarget).getPropertyValue(this.cssVar).trim();
        const n = parseFloat(raw);
        if (Number.isFinite(n) && n > 0) return n;
      }
      const rect = this.beforeEl.getBoundingClientRect();
      if (rect.width > 0) return rect.width;
      return this.defaultWidth;
    }

    applyWidth(px) {
      const w = clamp(px, this.min, this.max);
      if (this.mode === "cssVar" && this.cssVar) {
        this.cssTarget.style.setProperty(this.cssVar, `${w}px`);
      } else if (this.mode === "overlay") {
        if (this.onResize) this.onResize(w);
      } else {
        this.beforeEl.style.flex = `0 0 ${w}px`;
        this.beforeEl.style.width = `${w}px`;
        this.beforeEl.style.minWidth = `${w}px`;
        this.beforeEl.style.maxWidth = `${w}px`;
      }
      saveStateKey(this.key, w);
      if (this._reposition) this._reposition();
      return w;
    }

    mount() {
      if (!this.root || !this.beforeEl || this.beforeEl.dataset.splitMounted === "1") return;
      this.beforeEl.dataset.splitMounted = "1";
      this.applyWidth(this.getWidth());

      const handle = document.createElement("div");
      handle.className = "ruzgar-split-handle";
      if (this.mode === "overlay") handle.classList.add("ruzgar-split-handle--overlay");
      handle.dataset.splitKey = this.key;
      handle.setAttribute("role", "separator");
      handle.setAttribute("aria-orientation", "vertical");
      handle.setAttribute("aria-label", "Bölme genişliğini ayarla");
      handle.tabIndex = 0;
      this._handle = handle;

      if (this.mode === "overlay") {
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
          handle.style.left = `${Math.round(r.right - rootR.left - 2)}px`;
          handle.style.top = "0";
          handle.style.height = `${Math.round(rootR.height)}px`;
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
      if (ev.key === "ArrowLeft") step = -12;
      else if (ev.key === "ArrowRight") step = 12;
      else return;
      ev.preventDefault();
      this.applyWidth(this.getWidth() + step);
    }

    _onDown(ev) {
      if (!this.visible()) return;
      if (ev.button !== 0) return;
      ev.preventDefault();
      const handle = this._handle;
      handle.classList.add("is-active");
      document.body.classList.add("ruzgar-split-dragging");
      const startX = ev.clientX;
      const startW = this.getWidth();

      const onMove = (e) => {
        this.applyWidth(startW + (e.clientX - startX));
      };
      const onUp = () => {
        handle.classList.remove("is-active");
        document.body.classList.remove("ruzgar-split-dragging");
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        window.removeEventListener("pointercancel", onUp);
      };

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    }
  }

  function applyWorkbenchGridFromState() {
    const wb = document.getElementById("tercume-workbench");
    if (!wb) return;
    const tab = document.body.dataset.tercumeTab || "calisma";
    const state = loadState();
    const c1 = state["tercume-sidebar"] || 190;
    const c2 = state["tercume-ara"] || 240;
    if (tab === "ara") wb.style.gridTemplateColumns = `${c1}px ${c2}px minmax(0, 1fr)`;
    else if (tab === "calisma") wb.style.gridTemplateColumns = `${c1}px minmax(0, 1fr)`;
    global.RuzgarSplit?._splits?.forEach((s) => s._reposition?.());
  }

  const mounted = [];

  function initRuzgarSplits() {
    applySavedCssVars();
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
        defaultWidth: 232,
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
        defaultWidth: 320,
        min: 220,
        max: 560,
        visible: () => getComputedStyle(chat).display !== "none",
      });
      sp.mount();
      mounted.push(sp);
    }

    const wb = document.getElementById("tercume-workbench");
    const sidebar = wb?.querySelector(".tercume-sidebar");
    if (wb && sidebar && sidebar.dataset.splitMounted !== "1") {
      const sp = new PaneSplit({
        key: "tercume-sidebar",
        root: wb,
        before: sidebar,
        mode: "overlay",
        defaultWidth: 190,
        min: 120,
        max: 340,
        visible: () => {
          const tab = document.body.dataset.tercumeTab || "calisma";
          return tab === "calisma" || tab === "ara";
        },
        onResize: (w) => {
          const tab = document.body.dataset.tercumeTab || "calisma";
          const c2 = loadState()["tercume-ara"] || 240;
          if (tab === "ara") wb.style.gridTemplateColumns = `${w}px ${c2}px minmax(0, 1fr)`;
          else wb.style.gridTemplateColumns = `${w}px minmax(0, 1fr)`;
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
        mode: "overlay",
        defaultWidth: 240,
        min: 160,
        max: 420,
        visible: () => document.body.dataset.tercumeTab === "ara",
        onResize: (w) => {
          const c1 = loadState()["tercume-sidebar"] || 190;
          wb.style.gridTemplateColumns = `${c1}px ${w}px minmax(0, 1fr)`;
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
        mode: "overlay",
        defaultWidth: 400,
        min: 200,
        max: 900,
        visible: () => {
          const tab = document.body.dataset.tercumeTab || "calisma";
          return tab === "calisma" || tab === "ara";
        },
        onResize: (w) => {
          panels.style.gridTemplateColumns = `${w}px minmax(0, 1fr)`;
        },
      });
      sp.mount();
      mounted.push(sp);
      const saved = loadState()["tercume-source"];
      if (typeof saved === "number" && saved >= 200) {
        panels.style.gridTemplateColumns = `${saved}px minmax(0, 1fr)`;
      }
    }

    applyWorkbenchGridFromState();
  }

  global.RuzgarSplit = {
    init: initRuzgarSplits,
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
