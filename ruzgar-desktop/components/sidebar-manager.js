/**
 * SidebarManager — motor manifest'lerine göre dinamik yan panel + slide-in
 */
(function initSidebarManager(global) {
  const MANIFEST_BASE = "modules";
  const manifestCache = new Map();

  function $(id) {
    return document.getElementById(id);
  }

  function clickEl(id) {
    const el = $(id);
    if (el && typeof el.click === "function") el.click();
    return !!el;
  }

  function scrollToEl(id) {
    const el = $(id);
    if (!el) return false;
    el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    try {
      el.focus({ preventScroll: true });
    } catch {
      el.focus?.();
    }
    return true;
  }

  function setMimarTab(tab) {
    const btn = document.querySelector(`.mimar-view-tab[data-mimar-tab="${tab}"]`);
    if (btn) btn.click();
    else global.RuzgarMimarAtolye?.setMimarTab?.(tab);
  }

  const PAGE_BY_MOTOR = [
    ["genel", "page-genel"],
    ["hafiza", "page-hafiza"],
    ["hizir", "page-hizir"],
    ["mimar", "page-mimar"],
    ["tercume", "page-tercume"],
    ["video", "page-video"],
    ["programlama", "page-programlama"],
    ["ses", "page-ses"],
  ];

  function getActiveMotorFromDom() {
    for (const [mode, id] of PAGE_BY_MOTOR) {
      const el = document.getElementById(id);
      if (el && !el.hidden) return mode;
    }
    const cm = String(global.currentMode || "").trim().toLowerCase();
    return cm === "okuma" ? "mimar" : cm || "genel";
  }

  function motorForAction(action) {
    const a = String(action || "");
    if (a.startsWith("tercume")) return "tercume";
    if (a.startsWith("video")) return "video";
    if (a.startsWith("mimar")) return "mimar";
    if (a.startsWith("ses")) return "ses";
    if (a.startsWith("prog")) return "programlama";
    if (a.startsWith("genel")) return "genel";
    return null;
  }

  function panelActionNeedsVisibleMotor(action) {
    const need = motorForAction(action);
    if (!need) return true;
    const vis = getActiveMotorFromDom();
    if (vis === need) return true;
    const labels = {
      tercume: "Tercüme",
      video: "Video",
      mimar: "Mimar",
      ses: "Ses",
      programlama: "Programlama",
      genel: "Ana motor",
    };
    const msg = `Bu panel yalnızca «${labels[need] || need}» sayfasındayken açılır.`;
    try {
      global.dispatchEvent(
        new CustomEvent("ruzgar-sidebar-notify", { detail: { message: msg } }),
      );
    } catch {
      /* ignore */
    }
    return false;
  }

  function runTercumeDock(dock) {
    const t = global.RuzgarTercumeAtolye;
    if (!t) return;
    t.syncTercumeLayout?.(true);
    if (dock === "files" || dock === "ara") t.setTercumeTab?.(dock === "ara" ? "ara" : "calisma");
    if (typeof t.openDuzenDock === "function") t.openDuzenDock(dock);
    else t.toggleDuzenDock?.(dock);
  }

  /** Merkezi eylem kaydı — panel-manager'dan taşındı ve genişletildi */
  function runPanelAction(action) {
    const a = String(action || "").trim();
    if (!a) return;
    if (!panelActionNeedsVisibleMotor(a)) return;

    if (a.startsWith("tercume-ui:")) {
      const mode = a.slice("tercume-ui:".length);
      global.RuzgarTercumeAtolye?.syncTercumeLayout?.(true);
      global.RuzgarTercumeAtolye?.setTercumeUiMode?.(mode);
      return;
    }

    if (a.startsWith("tercume:")) {
      const t = global.RuzgarTercumeAtolye;
      const dockMap = {
        "tercume:flow": "flow",
        "tercume:files": "files",
        "tercume:tools": "tools",
        "tercume:status": "status",
        "tercume:ara": "ara",
        "tercume:review": "review",
      };
      if (dockMap[a]) {
        runTercumeDock(dockMap[a]);
        return;
      }
      if (a === "tercume:glossary") {
        runTercumeDock("tools");
        const fold = $("tercume-user-glossary-fold");
        if (fold) {
          fold.hidden = false;
          fold.open = true;
        }
        return;
      }
      if (a === "tercume:history") {
        runTercumeDock("status");
        const fold = $("tercume-apprentice-fold");
        if (fold) {
          fold.hidden = false;
          fold.open = true;
        }
        return;
      }
      if (a === "tercume:page-output") {
        runTercumeDock("page-output");
        return;
      }
    }

    if (a.startsWith("video:")) {
      if (global.RuzgarVideoAtolye?.runPanelAction?.(a)) return;
      if (a === "video:mark-in") clickEl("btn-video-mark-in") || clickEl("video-quick-create");
      else if (a === "video:subtitles") scrollToEl("video-rel-burn-sub");
      else if (a === "video:export-audio" || a === "video:export")
        clickEl("video-quick-audio") || clickEl("btn-video-open-export");
      else if (a === "video:trim") clickEl("video-quick-trim");
      else if (a === "video:timeline") scrollToEl("video-timeline-wrap");
      else if (a === "video:youtube") clickEl("video-quick-youtube");
      else if (a === "video:sub-tercume") clickEl("btn-video-sub-to-tercume");
      return;
    }

    if (a.startsWith("mimar:")) {
      if (a === "mimar:photo") setMimarTab("fotograf");
      else if (a === "mimar:art") setMimarTab("resim-sanat");
      else if (a === "mimar:design") setMimarTab("tasarim");
      else if (a === "mimar:archive") clickEl("btn-mimar-open-archive");
      return;
    }

    if (a.startsWith("ses:")) {
      if (a === "ses:open") clickEl("audio-file-input");
      else if (a === "ses:transcript") clickEl("btn-ses-stt");
      else if (a === "ses:to-chat") clickEl("btn-ses-to-chat");
      else if (a === "ses:speak") clickEl("btn-ses-speak");
      else if (a === "ses:dub") {
        scrollToEl("ses-dub-panel");
        window.setTimeout(() => $("ses-dub-rel")?.focus?.({ preventScroll: true }), 120);
      }
      else if (a === "ses:clear") clickEl("btn-ses-clear");
      return;
    }

    if (a.startsWith("prog:")) {
      if (a === "prog:root") scrollToEl("code-work-root");
      else if (a === "prog:kpi") scrollToEl("programlama-kpi-strip");
      else if (a === "prog:onay") scrollToEl("programlama-umit-onay-card");
      else if (a === "prog:editor") scrollToEl("code-editor");
      else if (a === "prog:tree") scrollToEl("code-file-tree");
      else if (a === "prog:refactor") clickEl("btn-code-refactor");
      else if (a === "prog:test") clickEl("btn-code-run-tests");
      return;
    }

    if (a === "genel:clear-chat") clickEl("nav-clear-chat");
    else if (a === "genel:help") clickEl("btn-faz7-help");
    else if (a === "genel:focus-chat") $("msg-input")?.focus();
    else if (a === "genel:devtools") global.ruzgarApi?.openDevTools?.();
    else if (a === "genel:refresh-manifest") {
      if (typeof global.refreshUiManifest === "function") void global.refreshUiManifest();
    }
  }

  class SidebarManager {
    constructor(options = {}) {
      this.sidebarEl = options.sidebarEl || $("main-sidebar");
      this.listEl = options.listEl || $("main-sidebar-list");
      this.titleEl = options.titleEl || $("main-sidebar-title");
      this.slideHost = options.slideHost || $("ruzgar-slide-host");
      this.slideTitle = options.slideTitle || $("ruzgar-slide-title");
      this.slideBody = options.slideBody || $("ruzgar-slide-body");
      this.motor = "genel";
      this.menuGroup = "default";
      this.manifest = null;
    }

    async loadManifest(motorId) {
      const id = String(motorId || "genel").trim().toLowerCase();
      const key = id === "okuma" ? "mimar" : id;
      if (manifestCache.has(key)) {
        this.manifest = manifestCache.get(key);
        return this.manifest;
      }
      const url = `${MANIFEST_BASE}/${key}/manifest.json`;
      try {
        const res = await fetch(url, { cache: "no-cache" });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        manifestCache.set(key, data);
        this.manifest = data;
        return data;
      } catch (e) {
        console.warn("[SidebarManager] manifest yüklenemedi:", key, e);
        const fallback = manifestCache.get("genel") || {
          id: key,
          title: key,
          sidebar: { default: [] },
        };
        this.manifest = fallback;
        return fallback;
      }
    }

    async setMotor(motorId) {
      this.motor = String(motorId || "genel").trim().toLowerCase();
      if (this.motor === "okuma") this.motor = "mimar";
      global.RuzgarContext?.setMotor?.(this.motor);
      await this.loadManifest(this.motor);
      return this.renderSidebar(this.menuGroup);
    }

    /** Düz liste veya { group, items }[] → gruplu yapı */
    normalizePanelGroups(raw) {
      if (!Array.isArray(raw) || !raw.length) return [];
      if (raw[0]?.items && Array.isArray(raw[0].items)) {
        return raw.map((g) => ({
          group: String(g.group || "").trim() || "Diğer",
          items: Array.isArray(g.items) ? g.items : [],
        }));
      }
      return [{ group: "", items: raw }];
    }

    getPanelGroups(group) {
      const g = group || this.menuGroup || "default";
      const side = this.manifest?.sidebar || {};
      const raw = Array.isArray(side[g]) ? side[g] : side.default || [];
      return this.normalizePanelGroups(raw);
    }

    getPanelList(group) {
      return this.getPanelGroups(group).flatMap((gr) => gr.items);
    }

    renderItemHtml(item) {
      if (item.type === "control" && item.control === "system_level") {
        const lvl = global.RuzgarContext?.get("system_level") || "akademik";
        const hint = String(item.title || "").replace(/"/g, "&quot;");
        return `<li class="ruzgar-sidebar-control">
              <label class="ruzgar-sidebar-control-label" title="${hint}">${item.icon || ""} ${item.label}</label>
              <select class="ruzgar-sidebar-level-select" data-context-key="system_level" aria-label="Çeviri seviyesi" title="${hint}">
                <option value="akademik"${lvl === "akademik" ? " selected" : ""}>Akademik</option>
                <option value="lise"${lvl === "lise" ? " selected" : ""}>Lise</option>
                <option value="ilkokul"${lvl === "ilkokul" ? " selected" : ""}>İlkokul</option>
              </select>
            </li>`;
      }
      const act = String(item.action || item.id || "");
      const lab = String(item.label || "").replace(/</g, "&lt;");
      const hint = String(item.title || lab).replace(/"/g, "&quot;");
      const ic = item.icon ? `${item.icon} ` : "";
      return `<li><button type="button" class="ruzgar-motor-tool-btn" data-panel-id="${item.id || ""}" data-panel-action="${act.replace(/"/g, "&quot;")}" title="${hint}">${ic}${lab}</button></li>`;
    }

    renderSidebar(group = "default") {
      this.menuGroup = group;
      const sidebar = this.sidebarEl;
      const list = this.listEl;
      const title = this.titleEl;
      if (!sidebar || !list) return;

      const panelGroups = this.getPanelGroups(group);
      const items = this.getPanelList(group);
      const motorTitle = this.manifest?.title || this.motor;
      const groupLabel =
        group === "duzen" ? "Düzen" : group === "gelisim" ? "Gelişim" : "Araçlar";

      if (title) title.textContent = `${motorTitle} · ${groupLabel}`;

      if (!items.length) {
        sidebar.classList.remove("active");
        sidebar.hidden = true;
        return;
      }
      if (document.body.classList.contains("ui-motors-compact")) {
        sidebar.classList.remove("active");
        sidebar.hidden = true;
        return;
      }

      list.innerHTML = panelGroups
        .map((gr) => {
          const head =
            gr.group ?
              `<li class="ruzgar-sidebar-group-title" aria-hidden="false">${String(gr.group).replace(/</g, "&lt;")}</li>`
            : "";
          const body = (gr.items || []).map((item) => this.renderItemHtml(item)).join("");
          return `${head}${body}`;
        })
        .join("");

      list.querySelectorAll("[data-panel-action]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const act = btn.getAttribute("data-panel-action");
          const item = items.find(
            (i) => i.action === act || i.id === btn.getAttribute("data-panel-id"),
          );
          this.openSlidePanel(item || { label: act, action: act, title: btn.title });
        });
      });

      list.querySelectorAll(".ruzgar-sidebar-level-select").forEach((sel) => {
        sel.addEventListener("change", () => {
          global.RuzgarContext?.setSystemLevel?.(sel.value);
          const top = $("tercume-read-level");
          if (top) top.value = sel.value;
        });
      });

      sidebar.hidden = false;
      requestAnimationFrame(() => sidebar.classList.add("active"));
    }

    openSlidePanel(item) {
      const label = item?.label || "Panel";
      const action = item?.action;
      const host = this.slideHost;
      if (!host) {
        if (action) runPanelAction(action);
        return;
      }
      if (this.slideTitle) this.slideTitle.textContent = label;
      if (this.slideBody) {
        const hint = item?.title ? `<br><span class="ruzgar-slide-hint">${String(item.title).replace(/</g, "&lt;")}</span>` : "";
        if (item?.type === "control") {
          this.slideBody.innerHTML =
            `<p class="ruzgar-slide-desc">Seviye soldaki listeden seçilir; her çeviri isteğine <code>system_level</code> eklenir.${hint}</p>`;
        } else {
          this.slideBody.innerHTML =
            `<p class="ruzgar-slide-desc"><strong>${label.replace(/</g, "&lt;")}</strong> açılıyor…${hint}</p>`;
        }
      }
      host.hidden = false;
      requestAnimationFrame(() => host.classList.add("is-open"));
      if (action) runPanelAction(action);
    }

    closeSlidePanel() {
      const host = this.slideHost;
      if (!host) return;
      host.classList.remove("is-open");
      window.setTimeout(() => {
        if (!host.classList.contains("is-open")) host.hidden = true;
      }, 280);
    }

    _notify(msg) {
      try {
        global.dispatchEvent(
          new CustomEvent("ruzgar-sidebar-notify", { detail: { message: String(msg || "") } }),
        );
      } catch {
        /* ignore */
      }
    }

    _wireDrawerActions(container, items) {
      if (!container) return;
      container.querySelectorAll("[data-panel-action]").forEach((btn) => {
        btn.addEventListener("click", () => {
          const act = btn.getAttribute("data-panel-action");
          const item = items.find(
            (i) => i.action === act || i.id === btn.getAttribute("data-panel-id"),
          );
          if (item?.type === "control") return;
          if (!act) return;
          this.closeSlidePanel();
          window.setTimeout(() => runPanelAction(act), 48);
        });
      });
      container.querySelectorAll(".ruzgar-drawer-level-select").forEach((sel) => {
        sel.addEventListener("change", () => {
          global.RuzgarContext?.setSystemLevel?.(sel.value);
          const top = $("tercume-read-level");
          if (top) top.value = sel.value;
          this._notify(`Seviye: ${sel.options[sel.selectedIndex]?.text || sel.value}`);
        });
      });
    }

    /** Menü «Paneller…» — ikon modunda da çalışır; sağdan slide-in liste */
    openPanelsDrawer(group = "duzen") {
      const panelGroups = this.getPanelGroups(group);
      const items = this.getPanelList(group);
      const host = this.slideHost;
      const motorTitle = this.manifest?.title || this.motor;
      const groupLabel =
        group === "duzen" ? "Düzen" : group === "gelisim" ? "Gelişim" : "Araçlar";

      if (!items.length) {
        this._notify("Panel listesi yüklenemedi — üst «Yenile» veya Ctrl+R.");
        return;
      }

      if (!host || !this.slideBody) {
        this._notify(`${motorTitle}: ${items.length} panel`);
        return;
      }

      if (this.slideTitle) {
        this.slideTitle.textContent = `${motorTitle} · ${groupLabel}`;
      }

      const html = panelGroups
        .map((gr) => {
          const head = gr.group
            ? `<div class="ruzgar-drawer-group-title">${String(gr.group).replace(/</g, "&lt;")}</div>`
            : "";
          const body = (gr.items || [])
            .map((item) => {
              if (item.type === "control" && item.control === "system_level") {
                const lvl = global.RuzgarContext?.get("system_level") || "akademik";
                const hint = String(item.title || "").replace(/"/g, "&quot;");
                return `<div class="ruzgar-drawer-control">
                  <label class="ruzgar-drawer-control-label" title="${hint}">${item.icon || ""} ${item.label}</label>
                  <select class="ruzgar-drawer-level-select" aria-label="Çeviri seviyesi">
                    <option value="akademik"${lvl === "akademik" ? " selected" : ""}>Akademik</option>
                    <option value="lise"${lvl === "lise" ? " selected" : ""}>Lise</option>
                    <option value="ilkokul"${lvl === "ilkokul" ? " selected" : ""}>İlkokul</option>
                  </select>
                </div>`;
              }
              const act = String(item.action || item.id || "");
              const lab = String(item.label || "").replace(/</g, "&lt;");
              const hint = String(item.title || lab).replace(/"/g, "&quot;");
              const ic = item.icon ? `<span class="ruzgar-drawer-icon">${item.icon}</span>` : "";
              return `<button type="button" class="ruzgar-drawer-btn" data-panel-id="${item.id || ""}" data-panel-action="${act.replace(/"/g, "&quot;")}" title="${hint}">${ic}<span class="ruzgar-drawer-btn-text">${lab}</span></button>`;
            })
            .join("");
          return `${head}<div class="ruzgar-drawer-group">${body}</div>`;
        })
        .join("");

      this.slideBody.innerHTML = `<div class="ruzgar-drawer-panel-list">${html}</div>`;
      this._wireDrawerActions(this.slideBody, items);

      host.hidden = false;
      requestAnimationFrame(() => host.classList.add("is-open"));
      this._notify(`${motorTitle} panelleri`);
    }

    async renderFromMenu(menuKind) {
      const kind = menuKind === "duzen" || menuKind === "gelisim" ? menuKind : "default";
      const motor = getActiveMotorFromDom();
      this.motor = motor;
      global.RuzgarContext?.setMotor?.(motor);
      await this.loadManifest(motor);
      const items = this.getPanelList(kind);
      if (!items.length) {
        this._notify("Panel manifest yüklenemedi.");
        return;
      }
      this.openPanelsDrawer(kind);
      if (!document.body.classList.contains("ui-motors-compact")) {
        this.renderSidebar(kind);
      }
    }

    wire() {
      $("btn-main-sidebar-close")?.addEventListener("click", () => {
        this.sidebarEl?.classList.remove("active");
      });
      $("ruzgar-slide-backdrop")?.addEventListener("click", () => this.closeSlidePanel());
      $("btn-ruzgar-slide-close")?.addEventListener("click", () => this.closeSlidePanel());
      document.addEventListener("keydown", (ev) => {
        if (ev.key === "Escape") this.closeSlidePanel();
      });
      document.addEventListener("ruzgar-sidebar-notify", (ev) => {
        const msg = ev.detail?.message;
        if (msg && typeof global.setStatus === "function") {
          global.setStatus(msg, "Rüzgar");
        }
      });
    }
  }

  const manager = new SidebarManager();
  manager.wire();

  global.RuzgarSidebarManager = manager;
  global.getActiveMotorFromDom = getActiveMotorFromDom;
  global.RuzgarPanelActions = { run: runPanelAction };

  /** panel-manager.js uyumluluğu */
  global.RuzgarPanelManager = {
    openPanel: (motor) => manager.setMotor(motor),
    closePanel: () => manager.sidebarEl?.classList.remove("active"),
    runToolAction: runPanelAction,
    wire: () => {},
    getCurrentMotor: () => manager.motor,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => manager.loadManifest("genel"), { once: true });
  }
})(typeof window !== "undefined" ? window : globalThis);
