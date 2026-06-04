/**
 * Tercüme Atölyesi v2 — yalnızca #page-tercume (diğer motorlara dokunmaz).
 */
(function initTercumeAtolyeModule(global) {
  const LS_WORK_ROOT = "ruzgar_tercume_work_root";
  const LS_PAGE_JOB = "ruzgar_tercume_page_job_id";
  const LS_LAST_SAVE_DIR = "ruzgar_tercume_last_save_dir";
  const LS_RECENT_FILES = "ruzgar_tercume_recent_files";
  const LS_TERCUME_UI = "ruzgar_tercume_ui_mode";
  const LS_TERCUME_READ_LEVEL = "ruzgar_tercume_read_level";
  const QUALITY_PASS = 55;
  const QUALITY_WARN = 75;

  let reviewMode = false;
  let currentSegmentIndex = 0;
  let lastQualityScore = null;
  let userGlossaryTerms = [];
  let pdfMeta = null;
  let pdfPreviewPage = 1;
  let pdfPreviewAvailable = null;
  let preflightStatus = { ok: null, label: "…" };
  let jobStatusLabel = "—";
  let tmHighlightTimer = null;
  let activeDuzenDock = "";

  let lastTranslateContext = null;
  let lastAlignedPayload = null;
  const approvedAlignedRows = new Set();
  const alignedRowNotes = new Map();
  let focusedAlignedRowKey = "";
  let alignedNotesSaveTimer = null;
  const EBOOK_EXTS = [".epub", ".fb2", ".mobi", ".azw", ".azw3", ".kfx", ".djvu", ".djv", ".rtf"];
  const IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"];
  const TERCUME_OPEN_EXTS = [
    ".pdf",
    ".docx",
    ".epub",
    ".txt",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".html",
    ".rtf",
    ".fb2",
    ".mobi",
    ".djvu",
    ".djv",
  ];

  let fileFilterQuery = "";
  let fileSearchTimer = null;
  let fileSearchToken = 0;

  function fileTypeBadge(name) {
    const low = String(name || "").toLowerCase();
    if (low.endsWith(".pdf")) return { label: "PDF", kind: "pdf" };
    if (low.endsWith(".docx")) return { label: "DOC", kind: "doc" };
    if (low.endsWith(".epub") || low.endsWith(".mobi") || low.endsWith(".fb2")) return { label: "EP", kind: "ebook" };
    if (low.endsWith(".djvu") || low.endsWith(".djv")) return { label: "Dj", kind: "ebook" };
    if (IMAGE_EXTS.some((e) => low.endsWith(e))) return { label: "IMG", kind: "img" };
    if (low.endsWith(".html") || low.endsWith(".htm")) return { label: "HT", kind: "web" };
    if (low.endsWith(".txt") || low.endsWith(".md")) return { label: "TXT", kind: "text" };
    return { label: "·", kind: "other" };
  }

  function createTercumeTreeBranch(it, depth) {
    const branch = document.createElement("div");
    branch.className = "code-tree-branch";
    const pad = 4 + depth * 12;
    if (it.isDir) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "code-tree-row folder";
      btn.dataset.rel = it.rel;
      btn.dataset.depth = String(depth);
      btn.style.paddingLeft = `${pad}px`;
      btn.innerHTML =
        `<span class="code-tree-chev" aria-hidden="true">▸</span>` +
        `<span class="code-tree-file-ico tercume-tree-ico tercume-tree-ico--dir" aria-hidden="true">KL</span>` +
        `<span class="code-tree-name">${esc(it.name)}</span>`;
      const kids = document.createElement("div");
      kids.className = "code-tree-children";
      kids.hidden = true;
      branch.appendChild(btn);
      branch.appendChild(kids);
    } else {
      const badge = fileTypeBadge(it.name);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "code-tree-row file";
      btn.dataset.rel = it.rel;
      btn.dataset.depth = String(depth);
      btn.dataset.extKind = badge.kind;
      btn.style.paddingLeft = `${pad}px`;
      btn.innerHTML =
        `<span class="code-tree-file-ico tercume-tree-ico tercume-tree-ico--${esc(badge.kind)}" aria-hidden="true">${esc(badge.label)}</span>` +
        `<span class="code-tree-name">${esc(it.name)}</span>`;
      branch.appendChild(btn);
    }
    return branch;
  }

  function renderPathCrumb() {
    const nav = $("tercume-path-crumb");
    if (!nav) return;
    const root = String(workRoot || "").replace(/\\/g, "/").replace(/\/$/, "");
    const parts = root.split("/").filter(Boolean);
    nav.innerHTML = "";
    if (!parts.length) return;
    let acc = "";
    parts.forEach((seg, i) => {
      acc = acc ? `${acc}/${seg}` : seg;
      const path = acc;
      if (i > 0) {
        const sep = document.createElement("span");
        sep.className = "tercume-crumb-sep";
        sep.textContent = "/";
        sep.setAttribute("aria-hidden", "true");
        nav.appendChild(sep);
      }
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tercume-crumb-btn";
      btn.textContent = seg;
      btn.title = path;
      btn.addEventListener("click", () => {
        workRoot = path;
        const inp = $("tercume-work-root");
        if (inp) inp.value = workRoot;
        try {
          localStorage.setItem(LS_WORK_ROOT, workRoot);
        } catch {
          /* ignore */
        }
        fileFilterQuery = "";
        const filterInp = $("tercume-file-filter");
        if (filterInp) filterInp.value = "";
        void refreshTree();
      });
      nav.appendChild(btn);
    });
  }

  function updateFileCountLabel(n, mode) {
    const el = $("tercume-file-count");
    if (!el) return;
    if (mode === "search") {
      el.textContent = n === 1 ? "1 sonuç" : `${n} sonuç`;
      return;
    }
    if (n === 0) el.textContent = "Boş";
    else if (n === 1) el.textContent = "1 öğe";
    else el.textContent = `${n} öğe`;
  }

  function updateSidebarActiveFile() {
    const el = $("tercume-sidebar-active");
    if (!el) return;
    if (openRel) {
      const name = openRel.split("/").pop() || openRel;
      el.textContent = name;
      el.title = openRel;
      el.hidden = false;
      el.classList.add("has-file");
    } else {
      el.textContent = "Dosya seçilmedi";
      el.title = "Listedan dosya seçin veya Dosya aç";
      el.hidden = false;
      el.classList.remove("has-file");
    }
  }

  function triggerOpenFileDialog() {
    $("tercume-import-file")?.click();
  }

  async function searchFilesUnderRoot(root, query, max = 180) {
    const q = String(query || "").trim().toLowerCase();
    if (!q || q.length < 2) return [];
    const out = [];
    async function walk(rel, depth) {
      if (out.length >= max || depth > 10) return;
      const items = deps.workspaceListDir ? await deps.workspaceListDir(rel) : [];
      for (const it of items) {
        if (out.length >= max) break;
        if (it.isDir) await walk(it.rel, depth + 1);
        else if (String(it.name || "").toLowerCase().includes(q)) out.push(it);
      }
    }
    await walk(root, 0);
    return out;
  }

  function renderSearchResults(items) {
    const list = $("tercume-file-list");
    if (!list) return;
    list.innerHTML = "";
    list.classList.add("tercume-file-tree--search");
    if (!items.length) {
      list.innerHTML = `<div class="code-file-placeholder">«${esc(fileFilterQuery)}» için sonuç yok.</div>`;
      updateFileCountLabel(0, "search");
      return;
    }
    for (const it of items) {
      const row = createTercumeTreeBranch(it, 0);
      const btn = row.querySelector(".code-tree-row.file");
      if (btn) {
        const sub = document.createElement("span");
        sub.className = "tercume-search-path";
        const parent = String(it.rel || "").replace(/\\/g, "/").split("/").slice(0, -1).join("/");
        sub.textContent = parent.length > 52 ? `…${parent.slice(-48)}` : parent;
        btn.appendChild(sub);
      }
      list.appendChild(row);
    }
    updateFileCountLabel(items.length, "search");
  }

  async function expandFolderByRel(rel) {
    const list = $("tercume-file-list");
    if (!list) return false;
    const norm = String(rel || "").replace(/\\/g, "/");
    for (const row of list.querySelectorAll(".code-tree-row.folder")) {
      if (String(row.dataset.rel || "").replace(/\\/g, "/") !== norm) continue;
      const branch = row.closest(".code-tree-branch");
      const kids = branch?.querySelector(":scope > .code-tree-children");
      if (!kids) return false;
      const depth = Number.parseInt(row.dataset.depth || "0", 10);
      if (kids.dataset.loaded !== "1") {
        kids.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
        kids.hidden = false;
        try {
          const items = deps.workspaceListDir ? await deps.workspaceListDir(norm) : [];
          kids.innerHTML = "";
          for (const x of items) {
            kids.appendChild(createTercumeTreeBranch(x, depth + 1));
          }
          kids.dataset.loaded = "1";
        } catch {
          kids.innerHTML = `<div class="code-tree-err">${esc("Liste okunamadı.")}</div>`;
          return false;
        }
      }
      kids.hidden = false;
      row.classList.add("is-expanded");
      const chev = row.querySelector(".code-tree-chev");
      if (chev) chev.textContent = "▾";
      return true;
    }
    return false;
  }

  async function expandTreeToRel(rel) {
    const norm = String(rel || "").replace(/\\/g, "/");
    const root = String(workRoot || "").replace(/\\/g, "/").replace(/\/$/, "");
    if (!norm.startsWith(root)) return;
    let sub = norm.slice(root.length).replace(/^\//, "");
    const parts = sub.split("/").filter(Boolean);
    if (parts.length <= 1) {
      markTreeActive(norm);
      return;
    }
    let acc = root;
    for (let i = 0; i < parts.length - 1; i += 1) {
      acc = `${acc}/${parts[i]}`.replace(/\/+/g, "/");
      await expandFolderByRel(acc);
    }
    markTreeActive(norm);
    const active = listActiveTreeRow(norm);
    active?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  function listActiveTreeRow(rel) {
    const list = $("tercume-file-list");
    if (!list) return null;
    const norm = String(rel || "").replace(/\\/g, "/");
    for (const row of list.querySelectorAll(".code-tree-row.file")) {
      if (String(row.dataset.rel || "").replace(/\\/g, "/") === norm) return row;
    }
    return null;
  }

  async function applyWorkRootFromInput() {
    const v = String($("tercume-work-root")?.value || "").trim();
    if (!v) {
      flash("Çalışma klasörü boş olamaz.");
      return;
    }
    workRoot = v.replace(/\\/g, "/").replace(/^\/+/, "").replace(/\/$/, "");
    try {
      localStorage.setItem(LS_WORK_ROOT, workRoot);
    } catch {
      /* ignore */
    }
    $("tercume-work-root").value = workRoot;
    fileFilterQuery = "";
    const filterInp = $("tercume-file-filter");
    if (filterInp) filterInp.value = "";
    renderPathCrumb();
    await refreshTree();
    flash(`Çalışma klasörü: ${workRoot}`);
  }

  function scheduleFileSearch() {
    if (fileSearchTimer) clearTimeout(fileSearchTimer);
    fileSearchTimer = setTimeout(() => void runFileSearch(), 280);
  }

  async function runFileSearch() {
    const q = String($("tercume-file-filter")?.value || "").trim();
    fileFilterQuery = q;
    const token = ++fileSearchToken;
    if (q.length < 2) {
      await refreshTree();
      return;
    }
    const list = $("tercume-file-list");
    if (list) {
      list.innerHTML = `<div class="code-tree-loading">${esc("Aranıyor…")}</div>`;
    }
    try {
      const items = await searchFilesUnderRoot(workRoot, q);
      if (token !== fileSearchToken) return;
      renderSearchResults(items);
    } catch (e) {
      if (token !== fileSearchToken) return;
      if (list) list.innerHTML = `<div class="code-file-placeholder">Arama hatası: ${esc(e.message || e)}</div>`;
    }
  }

  function wireFilePanelDnD() {
    const wrap = $("tercume-file-tree-wrap");
    const drop = $("tercume-file-dropzone");
    if (!wrap || wrap.dataset.dndWired === "1") return;
    wrap.dataset.dndWired = "1";
    let dragDepth = 0;
    const showDrop = () => {
      if (drop) drop.hidden = false;
      wrap.classList.add("is-dragover");
    };
    const hideDrop = () => {
      dragDepth = 0;
      if (drop) drop.hidden = true;
      wrap.classList.remove("is-dragover");
    };
    wrap.addEventListener("dragenter", (ev) => {
      if (!ev.dataTransfer?.types?.includes("Files")) return;
      ev.preventDefault();
      dragDepth += 1;
      showDrop();
    });
    wrap.addEventListener("dragover", (ev) => {
      if (!ev.dataTransfer?.types?.includes("Files")) return;
      ev.preventDefault();
      ev.dataTransfer.dropEffect = "copy";
    });
    wrap.addEventListener("dragleave", () => {
      dragDepth = Math.max(0, dragDepth - 1);
      if (dragDepth === 0) hideDrop();
    });
    wrap.addEventListener("drop", (ev) => {
      ev.preventDefault();
      hideDrop();
      const f = ev.dataTransfer?.files?.[0];
      if (f) void importFile(f).catch((e) => flash(e.message || String(e)));
    });
    const src = getSourceEl();
    if (src && src.dataset.tercumeDropWired !== "1") {
      src.dataset.tercumeDropWired = "1";
      src.addEventListener("dragover", (ev) => {
        if (!ev.dataTransfer?.types?.includes("Files")) return;
        ev.preventDefault();
      });
      src.addEventListener("drop", (ev) => {
        ev.preventDefault();
        const f = ev.dataTransfer?.files?.[0];
        if (f) void importFile(f).catch((e) => flash(e.message || String(e)));
      });
    }
  }

  let deps = {};
  let openRel = null;
  let fullSourceDoc = "";
  let fullTargetDoc = "";
  let sourcePageMeta = [];
  let sourceUnreadable = false;
  let ocrBusy = false;
  let workRoot = "ilim-assistant/arsiv";
  let awaitingChatReply = false;
  let translateAbort = false;
  let lastDownloadDir = { abs: "", rel: "" };
  let lastSaveDir = "ilim-assistant/arsiv/tercume-output";
  let lastIntentUndo = null;
  let lastIntentRawText = "";
  let lastBookSearchQuery = "";

  function api() {
    return deps.api || global.API || "";
  }
  function $(id) {
    return document.getElementById(id);
  }
  function flash(msg) {
    if (deps.flash) deps.flash(msg);
  }
  function esc(s) {
    return deps.esc ? deps.esc(s) : String(s);
  }

  function getSourceEl() {
    return $("tercume-source-editor");
  }
  function getTargetEl() {
    return $("tercume-target-editor");
  }
  function stripPdfBanner(text) {
    return String(text || "")
      .replace(/^\[PDF:[^\]]+\]\s*\n+/i, "")
      .trim();
  }

  function isPdfExtractGarbage(text) {
    const sample = String(text || "").slice(0, 12000);
    if (!sample) return false;
    const cid = sample.match(/\/G\d{2,}/g);
    if (cid && cid.length >= 6) return true;
    const chunks = sample.match(/\/[A-Z]\d{2,}\//g);
    if (chunks && chunks.length >= 8) return true;
    const words = sample.replace(/\s+/g, " ").trim().split(/\s+/).filter(Boolean);
    const readable = words.filter((w) => /^[\w\u0600-\u06FF\u0400-\u04FF.,;:!?'"()-]+$/u.test(w)).length;
    if (words.length > 40 && readable / words.length < 0.35) return true;
    return false;
  }

  function splitDocSegments(text) {
    const t = stripPdfBanner(text);
    if (!t) return [];
    return t.split(/\n\n+/).map((s) => s.trim()).filter(Boolean);
  }

  function showReadQualityWarn(msg) {
    const wrap = $("tercume-read-quality-warn");
    const txt = $("tercume-read-quality-warn-text");
    if (!wrap || !txt) return;
    if (!msg) {
      wrap.hidden = true;
      return;
    }
    txt.textContent = msg;
    if (getTercumeUiMode() === "reader") {
      wrap.hidden = true;
      flash(String(msg).slice(0, 140));
      return;
    }
    wrap.hidden = false;
  }

  function updatePanelHeadMeta(idx, total, pageLabel) {
    const srcMeta = $("tercume-source-head-meta");
    const tgtMeta = $("tercume-target-head-meta");
    if (!srcMeta || !tgtMeta) return;
    if (idx == null || total <= 1) {
      srcMeta.textContent = "";
      tgtMeta.textContent = "";
      return;
    }
    const page = pageLabel || `segment ${idx + 1}`;
    const label = `Sayfa/parça ${idx + 1} / ${total}${page ? ` · ${page}` : ""}`;
    srcMeta.textContent = label;
    tgtMeta.textContent = "↔ eşleşen hedef";
  }

  function shouldUseSegmentFocusView() {
    if (reviewMode) return false;
    const aligned = lastAlignedPayload?.segments;
    if (aligned?.length > 1) return true;
    return splitDocSegments(fullSourceDoc).length > 1;
  }

  function refreshSegmentPanelView() {
    const srcEl = getSourceEl();
    const tgtEl = getTargetEl();
    if (!srcEl || !tgtEl) return;
    const segs = splitDocSegments(fullSourceDoc);
    const tgts = splitDocSegments(fullTargetDoc);
    const aligned = lastAlignedPayload?.segments;
    const total = aligned?.length || segs.length || 1;
    if (shouldUseSegmentFocusView()) {
      const idx = Math.max(0, Math.min(total - 1, currentSegmentIndex));
      currentSegmentIndex = idx;
      let src = "";
      let tgt = "";
      let pageLabel = "";
      if (aligned?.[idx]) {
        src = String(aligned[idx].source || "");
        tgt = String(aligned[idx].target || "");
        pageLabel = aligned[idx].page ? `sayfa ${aligned[idx].page}` : "";
      } else {
        src = segs[idx] || "";
        tgt = tgts[idx] || "";
        const pm = sourcePageMeta[idx];
        pageLabel = pm?.label || (pm?.index != null ? `sayfa ${Number(pm.index) + 1}` : "");
      }
      srcEl.innerText = src;
      tgtEl.innerText = tgt;
      updatePanelHeadMeta(idx, total, pageLabel);
    } else {
      srcEl.innerText = fullSourceDoc;
      tgtEl.innerText = fullTargetDoc;
      updatePanelHeadMeta(null);
    }
    updateStats();
    applyEditorDirection();
    updateSegmentStrip();
    syncSegmentEditors();
    updateStatusBar();
    syncBookReaderView();
  }

  function setTercumeUiMode(mode) {
    closeDuzenDock();
    const m = mode === "classic" ? "classic" : "reader";
    document.body.dataset.tercumeUi = m;
    try {
      localStorage.setItem(LS_TERCUME_UI, m);
    } catch {
      /* ignore */
    }
    applyReaderWorkbenchGrid();
    if (global.RuzgarSplit?.applyWorkbenchGridFromState) {
      global.RuzgarSplit.applyWorkbenchGridFromState();
    }
    applyReaderWorkbenchGrid();
    syncBookReaderView();
  }

  const DUZEN_ORIGINS = new Map();

  const DUZEN_PANELS = {
    flow: {
      title: "Dil akışı",
      placement: "left",
      roots: () => [$("tercume-flow-panel")],
    },
    files: {
      title: "Dosyalar",
      placement: "left",
      roots: () => [document.querySelector("#page-tercume .tercume-file-panel")],
    },
    ara: {
      title: "Eser ara",
      placement: "right",
      roots: () => [$("tercume-ara-panel")],
      onOpen: () => {
        const ara = $("tercume-ara-panel");
        if (ara) ara.hidden = false;
        setTercumeTab("ara");
        setTimeout(() => {
          $("tercume-eser-input")?.focus();
          $("tercume-eser-input")?.select?.();
        }, 80);
      },
    },
    tools: {
      title: "Araçlar",
      placement: "right",
      host: true,
      collect: () => {
        const nodes = [];
        const tb = document.querySelector("#page-tercume .tercume-toolbar");
        if (tb) nodes.push(tb);
        ["tercume-user-glossary-fold", "tercume-capability-strip", "tercume-ocr-warn", "tercume-pdf-hint"].forEach(
          (id) => {
            const el = $(id);
            if (el) nodes.push(el);
          },
        );
        return nodes;
      },
    },
    status: {
      title: "Durum",
      placement: "right",
      host: true,
      collect: () => {
        const nodes = [];
        const hw = $("tercume-header-workbench");
        if (hw) nodes.push(hw);
        [
          "tercume-readiness-warn",
          "tercume-job-panel",
          "tercume-progress-wrap",
          "tercume-read-quality-warn",
          "tercume-quality-strip",
        ].forEach((id) => {
          const el = $(id);
          if (el) nodes.push(el);
        });
        return nodes;
      },
    },
    review: {
      title: "İnceleme",
      placement: "center",
      host: true,
      onOpen: () => {
        setWorkbenchReviewMode(true);
        const fold = $("tercume-aligned-fold");
        if (fold) {
          fold.hidden = false;
          fold.open = true;
        }
      },
      collect: () =>
        ["tercume-panels-row", "tercume-segment-strip", "tercume-segment-edit", "tercume-aligned-fold"]
          .map((id) => $(id))
          .filter(Boolean),
    },
    "page-output": {
      title: "Sayfa ve çıktı",
      placement: "right",
      host: true,
      collect: () => {
        const el = document.querySelector(".tercume-header-page-output");
        return el ? [el] : [];
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
    btn.className = "tercume-duzen-close";
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
    if (el.classList.contains("tercume-file-panel")) {
      const row = el.querySelector(".tercume-file-panel-title-row");
      if (row && !row.querySelector(".tercume-duzen-close")) row.appendChild(makeDuzenCloseBtn());
      return;
    }
    let head = el.querySelector(":scope > .tercume-duzen-chrome, :scope > .tercume-duzen-float-head");
    if (!head) {
      head = document.createElement("header");
      head.className = "tercume-duzen-chrome";
      el.insertBefore(head, el.firstChild);
    } else {
      head.classList.add("tercume-duzen-chrome");
    }
    let tit = head.querySelector(".tercume-duzen-chrome-title");
    if (!tit) {
      tit = document.createElement("span");
      tit.className = "tercume-duzen-chrome-title";
      head.insertBefore(tit, head.firstChild);
    }
    tit.textContent = title;
    head.querySelectorAll(".tercume-duzen-float-close").forEach((b) => b.remove());
    if (!head.querySelector(".tercume-duzen-close")) head.appendChild(makeDuzenCloseBtn());
  }

  function ensureDuzenFloatHost() {
    let host = $("tercume-duzen-float-host");
    if (!host) {
      host = document.createElement("div");
      host.id = "tercume-duzen-float-host";
      host.className = "tercume-duzen-float-host";
      host.hidden = true;
      $("page-tercume")?.appendChild(host);
    }
    return host;
  }

  function hideAllDuzenPanels() {
    document.querySelectorAll(".tercume-duzen-open").forEach((el) => {
      el.classList.remove("tercume-duzen-open");
      el.removeAttribute("data-duzen-place");
      el.style.removeProperty("display");
      if (el.dataset.duzenWasHidden === "1") {
        el.hidden = true;
        delete el.dataset.duzenWasHidden;
      }
    });
    const flow = $("tercume-flow-panel");
    if (flow) flow.hidden = true;

    const host = $("tercume-duzen-float-host");
    if (host) {
      host.hidden = true;
      host.innerHTML = "";
    }
    restoreAllDuzenNodes();

    const reader = getTercumeUiMode() === "reader";
    const fp = document.querySelector("#page-tercume .tercume-file-panel");
    document.querySelectorAll("#page-tercume .tercume-sidebar").forEach((el) => {
      el.style.setProperty("display", "none", "important");
    });
    if (fp) fp.style.setProperty("display", "none", "important");
    const ara = $("tercume-ara-panel");
    if (ara) {
      ara.classList.remove("tercume-duzen-open");
      ara.hidden = true;
      ara.style.setProperty("display", "none", "important");
    }
    const titleRow = $("title-row-tercume-controls");
    if (titleRow && reader) titleRow.hidden = true;
  }

  function mountDuzenHostPanel(cfg) {
    const nodes = cfg.collect?.() || [];
    if (!nodes.length) return false;
    const host = ensureDuzenFloatHost();
    host.innerHTML = "";
    const shell = document.createElement("aside");
    shell.className = "tercume-duzen-panel tercume-duzen-open";
    shell.dataset.duzenPlace = cfg.placement || "right";
    ensureDuzenCloseChrome(shell, cfg.title);
    const body = document.createElement("div");
    body.className = "tercume-duzen-host-body";
    nodes.forEach((node) => {
      stashDuzenNode(node);
      body.appendChild(node);
    });
    shell.appendChild(body);
    host.appendChild(shell);
    host.hidden = false;
    const titleRow = $("title-row-tercume-controls");
    if (titleRow) titleRow.hidden = false;
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
      el.classList.add("tercume-duzen-open");
      el.dataset.duzenPlace = cfg.placement || "left";
      el.style.setProperty("display", disp, "important");
    });
    return true;
  }

  function syncDuzenDockDisplay() {
    const dock = String(activeDuzenDock || "").trim();
    hideAllDuzenPanels();
    if (!dock) return;
    const cfg = DUZEN_PANELS[dock];
    if (!cfg) return;
    cfg.onOpen?.();
    let ok = false;
    if (cfg.host) ok = mountDuzenHostPanel(cfg);
    else ok = showDuzenRoots(cfg);
    if (!ok) {
      flash(`Panel açılamadı: ${cfg.title}`);
      activeDuzenDock = "";
      delete document.body.dataset.tercumeDock;
      $("tercume-duzen-backdrop").hidden = true;
      return;
    }
    if (dock === "files") {
      document.querySelectorAll("#page-tercume .tercume-sidebar").forEach((el) => {
        if (!el.classList.contains("tercume-file-panel")) el.style.setProperty("display", "none", "important");
      });
    }
  }

  function applyReaderWorkbenchGrid() {
    const wb = $("tercume-workbench");
    if (!wb || getTercumeUiMode() !== "reader") return;
    wb.style.setProperty("grid-template-columns", "minmax(0, 1fr)", "important");
    const main = wb.querySelector(".tercume-main");
    if (main) {
      main.style.setProperty("grid-column", "1 / -1", "important");
      main.style.width = "100%";
    }
    syncDuzenDockDisplay();
  }

  function getTercumeUiMode() {
    try {
      const s = localStorage.getItem(LS_TERCUME_UI);
      if (s === "classic") return "classic";
    } catch {
      /* ignore */
    }
    return "reader";
  }

  function getReadLevel() {
    const ctx = global.RuzgarContext?.get?.("system_level");
    if (ctx === "ilkokul" || ctx === "lise" || ctx === "akademik") return ctx;
    const el = $("tercume-read-level");
    const v = String(el?.value || "").trim().toLowerCase();
    if (v === "ilkokul" || v === "lise" || v === "akademik") {
      global.RuzgarContext?.setSystemLevel?.(v);
      return v;
    }
    try {
      const saved = localStorage.getItem(LS_TERCUME_READ_LEVEL);
      if (saved === "ilkokul" || saved === "lise" || saved === "akademik") {
        global.RuzgarContext?.setSystemLevel?.(saved);
        return saved;
      }
    } catch {
      /* ignore */
    }
    return "akademik";
  }

  function wireReadLevelSelect() {
    const el = $("tercume-read-level");
    if (!el || el.dataset.wired === "1") return;
    el.dataset.wired = "1";
    try {
      const saved = localStorage.getItem(LS_TERCUME_READ_LEVEL);
      if (saved === "ilkokul" || saved === "lise" || saved === "akademik") el.value = saved;
    } catch {
      /* ignore */
    }
    el.addEventListener("change", () => {
      const lvl = String(el.value || "akademik");
      global.RuzgarContext?.setSystemLevel?.(lvl);
      try {
        localStorage.setItem(LS_TERCUME_READ_LEVEL, lvl);
      } catch {
        /* ignore */
      }
      document.querySelectorAll(".ruzgar-sidebar-level-select").forEach((s) => {
        if (s.value !== lvl) s.value = lvl;
      });
      flash(`Çeviri seviyesi: ${el.options[el.selectedIndex]?.text || el.value}`);
    });
    global.RuzgarContext?.subscribe?.((snap) => {
      if (snap.system_level && el.value !== snap.system_level) el.value = snap.system_level;
    });
  }

  function openDuzenDock(name) {
    const n = String(name || "").trim();
    if (!n) return;
    if (document.body.dataset.motor !== "tercume") {
      document.body.dataset.motor = "tercume";
    }
    activeDuzenDock = n;
    document.body.dataset.tercumeDock = n;
    const backdrop = $("tercume-duzen-backdrop");
    if (backdrop) backdrop.hidden = false;
    document.querySelectorAll(".tercume-duzen-btn").forEach((b) => {
      b.classList.toggle("is-active", b.dataset.tercumeDock === activeDuzenDock);
    });
    if (activeDuzenDock !== "review" && getTercumeUiMode() === "reader") {
      setWorkbenchReviewMode(false);
    }
    syncDuzenDockDisplay();
  }

  function toggleDuzenDock(name) {
    const n = String(name || "").trim();
    if (activeDuzenDock === n) closeDuzenDock();
    else openDuzenDock(n);
  }

  function closeDuzenDock() {
    const had = !!activeDuzenDock;
    activeDuzenDock = "";
    delete document.body.dataset.tercumeDock;
    const backdrop = $("tercume-duzen-backdrop");
    if (backdrop) backdrop.hidden = true;
    document.querySelectorAll(".tercume-duzen-btn").forEach((b) => b.classList.remove("is-active"));
    if (had && getTercumeUiMode() === "reader") setWorkbenchReviewMode(false);
    hideAllDuzenPanels();
  }

  function syncBookReaderView() {
    if (document.body.dataset.tercumeUi !== "reader") return;
    const empty = $("tercume-book-empty");
    const spread = $("tercume-book-spread");
    const title = $("tercume-reader-title");
    const pageLab = $("tercume-reader-page-label");
    const bookSrc = $("tercume-book-source");
    const bookTgt = $("tercume-book-target");
    const bookImg = $("tercume-book-page-img");
    const bookText = $("tercume-book-page-text");
    const bookLoad = $("tercume-book-page-loading");
    const pageInput = $("tercume-book-page-input");
    const pageTotal = $("tercume-book-page-total");
    const hasFile = !!openRel || !!String(fullSourceDoc || "").trim();
    if (empty) empty.hidden = hasFile;
    if (spread) spread.hidden = !hasFile;
    if (title) {
      title.textContent = openRel ? openRel.split("/").pop() || "Kitap" : "Kitap";
      title.title = openRel || "";
    }
    const isPdf = !!(openRel && String(openRel).toLowerCase().endsWith(".pdf"));
    const total = Number(pdfMeta?.pages_total) || 0;
    const page = pdfPreviewPage || 1;
    if (pageLab) {
      const jobHint =
        batchPollTimer || activeBatchJobId ? jobStatusLabel : "";
      pageLab.textContent =
        jobHint && jobHint !== "—"
          ? jobHint
          : isPdf && total
            ? `Sayfa ${page} / ${total}`
            : hasFile
              ? "Metin belgesi"
              : "—";
    }
    if (pageInput) {
      pageInput.value = isPdf ? String(page) : "";
      pageInput.disabled = !isPdf;
    }
    if (pageTotal) pageTotal.textContent = isPdf && total ? `/ ${total}` : "/ ?";

    const srcEl = getSourceEl();
    const tgtEl = getTargetEl();
    const srcTxt = srcEl ? String(srcEl.innerText || "").trim() : String(fullSourceDoc || "").trim();
    const tgtTxt = tgtEl ? String(tgtEl.innerText || "").trim() : String(fullTargetDoc || "").trim();
    if (bookSrc) bookSrc.textContent = srcTxt || "—";
    if (bookTgt) {
      bookTgt.textContent = tgtTxt;
      bookTgt.classList.toggle("is-empty", !tgtTxt);
    }

    const prevImg = $("tercume-pdf-preview-img");
    const prevFallback = $("tercume-pdf-preview-fallback");
    if (isPdf && prevImg && !prevImg.hidden && prevImg.src) {
      if (bookImg) {
        bookImg.src = prevImg.src;
        bookImg.alt = prevImg.alt || `Sayfa ${page}`;
        bookImg.hidden = false;
      }
      if (bookText) bookText.hidden = true;
      if (bookLoad) bookLoad.hidden = true;
    } else if (isPdf && prevFallback && !prevFallback.hidden) {
      if (bookImg) bookImg.hidden = true;
      if (bookText) bookText.hidden = true;
      if (bookLoad) {
        bookLoad.hidden = false;
        bookLoad.textContent = prevFallback.textContent || "Sayfa yükleniyor…";
      }
    } else if (hasFile && !isPdf) {
      if (bookImg) bookImg.hidden = true;
      if (bookLoad) bookLoad.hidden = true;
      if (bookText) {
        bookText.hidden = false;
        bookText.textContent = srcTxt.slice(0, 12000) || "—";
      }
    } else if (isPdf) {
      if (bookImg) bookImg.hidden = true;
      if (bookText) bookText.hidden = true;
      if (bookLoad) {
        bookLoad.hidden = false;
        bookLoad.textContent = "Sayfa yükleniyor…";
      }
    }
    applyReaderWorkbenchGrid();
  }

  async function goToBookPage(pageNum) {
    const page = Math.max(1, Number(pageNum) || 1);
    const fromEl = $("tercume-page-from");
    const toEl = $("tercume-page-to");
    if (fromEl) fromEl.value = String(page);
    if (toEl) toEl.value = String(page);
    if (openRel && String(openRel).toLowerCase().endsWith(".pdf")) {
      await loadPdfPagesIntoSource(openRel, { capWideRange: false });
      currentSegmentIndex = 0;
      refreshSegmentPanelView();
      await loadPdfPreviewPage(page);
      syncBookReaderView();
      return page;
    }
    focusSegment(Math.max(0, page - 1), { syncPdf: false });
    syncBookReaderView();
    return page;
  }

  function extractFileHintFromText(text) {
    const raw = String(text || "").trim();
    const fileMatch = raw.match(/[\w\u0080-\uFFFF.-]+\.(pdf|epub|docx|txt|md|html|rtf)\b/i);
    if (fileMatch) return fileMatch[0];
    let t = raw
      .replace(/\b(lütfen|lutfen|abi|hocam|ruzgar|bana|benim|için|icin|şu|su|bu|the|please)\b/gi, " ")
      .replace(/\b(aç|ac|açar|misın|mısın|göster|goster|yükle|yukle|open|load|kitap|dosya|pdf|file|getir)\b/gi, " ")
      .replace(/['"]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return t.length >= 2 ? t : "";
  }

  function normalizeBookKey(s) {
    return String(s || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/\p{M}/gu, "")
      .replace(/ı/g, "i")
      .replace(/[\s._\-–—]+/g, " ")
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function bookSearchTokens(hint) {
    const stop = new Set([
      "var",
      "yok",
      "evet",
      "hayir",
      "tamam",
      "iste",
      "the",
      "and",
      "pdf",
      "dosya",
      "kitap",
      "ornek",
      "sample",
    ]);
    const parts = normalizeBookKey(hint).split(" ").filter((w) => w.length >= 3 && !stop.has(w));
    return parts.length ? parts : normalizeBookKey(hint).split(" ").filter((w) => w.length >= 2 && !stop.has(w));
  }

  function fileNameMatchesTokens(name, tokens) {
    const hay = normalizeBookKey(name);
    if (!tokens.length) return 0;
    let score = 0;
    for (const t of tokens) {
      if (hay.includes(t)) {
        score += 2;
        continue;
      }
      const stem = t.length >= 5 ? t.slice(0, 5) : t;
      if (hay.split(" ").some((w) => w.startsWith(stem) || stem.startsWith(w.slice(0, Math.min(w.length, stem.length))))) {
        score += 1;
      }
    }
    return score;
  }

  async function searchFilesUnderRootFuzzy(root, hint, max = 32) {
    const tokens = bookSearchTokens(hint);
    if (!tokens.length) return [];
    const minScore = tokens.length >= 2 ? 2 : 1;
    const out = [];
    async function walk(rel, depth) {
      if (out.length >= max * 3 || depth > 12) return;
      const items = deps.workspaceListDir ? await deps.workspaceListDir(rel) : [];
      for (const it of items) {
        if (out.length >= max * 3) break;
        if (it.isDir) await walk(it.rel, depth + 1);
        else {
          const score = fileNameMatchesTokens(String(it.name || it.rel || ""), tokens);
          if (score >= minScore) out.push({ ...it, _score: score });
        }
      }
    }
    await walk(root, 0);
    out.sort((a, b) => (b._score || 0) - (a._score || 0));
    return out.slice(0, max);
  }

  async function resolveFileByHint(hint) {
    const h = String(hint || "").trim();
    if (!h || h.length < 2) return "";

    let recent = [];
    try {
      recent = JSON.parse(localStorage.getItem(LS_RECENT_FILES) || "[]");
      if (!Array.isArray(recent)) recent = [];
    } catch {
      recent = [];
    }
    const tokens = bookSearchTokens(h);
    for (const rel of recent) {
      const leaf = String(rel.split("/").pop() || "");
      if (fileNameMatchesTokens(leaf, tokens) >= (tokens.length >= 2 ? 2 : 1)) return rel;
    }

    try {
      const res = await fetch(`${api()}/api/tercume/local-find?q=${encodeURIComponent(h)}&limit=8`);
      const j = await res.json().catch(() => ({}));
      if (res.ok && j.ok) {
        if (j.best?.rel) return String(j.best.rel);
        const items = Array.isArray(j.items) ? j.items : [];
        if (items[0]?.rel) return String(items[0].rel);
      }
    } catch {
      /* sunucu fuzzy yoksa istemci yedek */
    }

    try {
      const files = await searchFilesUnderRootFuzzy(workRoot, h, 12);
      if (files.length) return String(files[0].rel);
    } catch {
      /* ignore */
    }
    return "";
  }

  function extractBookQueryFromText(text) {
    const raw = String(text || "").trim();
    const fileMatch = raw.match(/[\w\u0080-\uFFFF.-]+\.(pdf|epub|docx|txt|md)\b/i);
    if (fileMatch) return fileMatch[0].replace(/\.[^.]+$/i, "");
    let t = raw
      .replace(/\?/g, " ")
      .replace(/\b(lütfen|lutfen|abi|hocam|ruzgar|bana|benim|için|icin|şu|su|bu|the|please)\b/gi, " ")
      .replace(
        /\b(aç|ac|açar|göster|goster|yükle|yukle|open|load|getir|çevir|cevir|translate|kaydet|indir|ara)\b/gi,
        " ",
      )
      .replace(/\b(arşivde|arsivde|arşiv|arsiv|var mı|var mi|mevcut mu|buluyor musun)\b/gi, " ")
      .replace(/\b(var|yok|evet|hayır|hayir|tamam|işte|iste|zaten|orada|mevcut)\b/gi, " ")
      .replace(/['"]/g, " ")
      .replace(/\s*[-–—]\s*/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    return t.length >= 2 ? t : "";
  }

  function rememberBookSearchQuery(q) {
    const s = String(q || "").trim();
    if (s.length >= 3) lastBookSearchQuery = s;
  }

  function pickBookQueryFromContext(raw, low) {
    const fromMsg = extractBookQueryFromText(raw);
    if (fromMsg.length >= 3) return fromMsg;
    if (lastBookSearchQuery.length >= 3) return lastBookSearchQuery;
    if (lastIntentRawText) {
      const prev = extractBookQueryFromText(lastIntentRawText);
      if (prev.length >= 3) return prev;
    }
    return "";
  }

  function isArchiveAffirmation(low, raw) {
    const t = String(raw || "").trim();
    if (t.length > 80) return false;
    if (/^(evet|tamam|aç|ac|aç artık|aç hadi|getir|göster|goster|orada|mevcut)\b/i.test(t)) return true;
    return /\b(arşivde|arsivde)\s+var\b/i.test(low) || /\bvar\s+(işte|zaten|orada)\b/i.test(low);
  }

  async function buildTercumeLocalReply(raw, low) {
    if (/^(selam|sa|slm|merhaba|hey|günaydın|gunaydin|iyi akşamlar|iyi aksamlar|naber|nasılsın|nasilsin)\b/i.test(low)) {
      return {
        reply: buildIntentReply(
          "Aleyküm selam Ümit abi. Bir kitap açalım mı? «Sahih Bukhari aç» yazmanız yeterli — sayfalar ortada kitap gibi açılır.",
          ["sohbet karşılama"],
          0.97,
        ),
      };
    }
    if (/\b(yardım|help|nasıl kullan|nasil kullan|ne yapabilir)\b/i.test(low)) {
      return {
        reply: buildIntentReply(
          "Dosya adı yazın («Sahih Bukhari»), sayfa gezin, «bu sayfayı çevir» deyin. Arka plan işi için «durdur» yeter. Gelişmiş paneller: üst menü → düzen.",
          ["yardım"],
          0.95,
        ),
      };
    }

    const wantsArchiveCheck = /\b(arşivde|arsivde|arşiv|arsiv|var mı|var mi|mevcut mu|buluyor musun)\b/i.test(low);
    const wantsOpenImplicit = /\b(aç|ac|göster|goster|getir|yükle|yukle|open)\b/i.test(low);

    if (isArchiveAffirmation(low, raw)) {
      const query = pickBookQueryFromContext(raw, low);
      if (query) {
        rememberBookSearchQuery(query);
        const rel = await resolveFileByHint(query);
        if (rel) {
          setTercumeTab("calisma");
          await openFile(rel);
          const leaf = rel.split("/").pop() || rel;
          return {
            reply: buildIntentReply(
              `Haklısınız — «${leaf}» arşivdeydi, şimdi açtım.`,
              ["önceki arama hatırlandi", "dosya açıldı"],
              0.95,
            ),
          };
        }
      }
      return {
        reply: buildIntentReply(
          "Hangi eseri kastettiniz? Tam adını yazın — örneğin «Sahih Bukhari aç».",
          ["bağlam eksik"],
          0.82,
        ),
      };
    }

    const query = pickBookQueryFromContext(raw, low);
    if (query.length >= 3) {
      rememberBookSearchQuery(query);
      const rel = await resolveFileByHint(query);
      if (rel) {
        const leaf = rel.split("/").pop() || rel;
        if (wantsArchiveCheck && !wantsOpenImplicit) {
          return {
            reply: buildIntentReply(
              `Evet, arşivde var: «${leaf}». Açmamı isterseniz «aç» deyin — hemen önünüze getiririm.`,
              ["arşiv taraması", "dosya bulundu"],
              0.94,
            ),
          };
        }
        setTercumeTab("calisma");
        await openFile(rel);
        return {
          reply: buildIntentReply(
            `Tamam, «${leaf}» açıldı. Sayfa numarasıyla gezebilir veya «bu sayfayı çevir» diyebilirsiniz.`,
            ["dosya bulundu", "kitap açıldı"],
            0.95,
          ),
        };
      }
      if (wantsArchiveCheck || query.length >= 4) {
        return {
          reply: buildIntentReply(
            `«${query}» için arşivde eşleşme bulamadım. Dosya farklı adla kayıtlı olabilir — «Dosyalar» panelinden bakın veya tam dosya adını yazın.`,
            ["arşiv taraması", "sonuç yok"],
            0.86,
          ),
        };
      }
    }

    if (raw.length <= 160) {
      return {
        reply: buildIntentReply(
          "Anladım. Bir eser adı yazarsanız arşivden açarım — örneğin «Sahih Bukhari» veya «Sahih Bukhari aç». Sayfa çevirisi için «bu sayfayı çevir» yeter.",
          ["yerel yanıt", "LLM gerekmedi"],
          0.72,
        ),
      };
    }
    return null;
  }

  function commitVisiblePanelsToFullDoc() {
    const srcEl = getSourceEl();
    const tgtEl = getTargetEl();
    if (!srcEl || !tgtEl) return;
    if (!shouldUseSegmentFocusView()) {
      fullSourceDoc = stripPdfBanner(String(srcEl.innerText || ""));
      fullTargetDoc = String(tgtEl.innerText || "");
      return;
    }
    const segs = splitDocSegments(fullSourceDoc);
    const tgts = splitDocSegments(fullTargetDoc);
    const idx = currentSegmentIndex;
    const src = String(srcEl.innerText || "").trim();
    const tgt = String(tgtEl.innerText || "").trim();
    if (idx < segs.length) segs[idx] = src;
    else if (src) segs.push(src);
    if (idx < tgts.length) tgts[idx] = tgt;
    else if (tgt) tgts.push(tgt);
    fullSourceDoc = segs.join("\n\n");
    fullTargetDoc = tgts.join("\n\n");
  }

  function getSourceText() {
    if (fullSourceDoc) return fullSourceDoc;
    const el = getSourceEl();
    return el ? stripPdfBanner(String(el.innerText || "").trim()) : "";
  }
  function setSourceText(t) {
    fullSourceDoc = stripPdfBanner(t || "");
    refreshSegmentPanelView();
    scheduleTmHighlight();
  }
  function getTargetText() {
    if (fullTargetDoc || fullSourceDoc) return fullTargetDoc;
    const el = getTargetEl();
    return el ? String(el.innerText || "").trim() : "";
  }
  function setTargetText(t) {
    fullTargetDoc = t || "";
    refreshSegmentPanelView();
  }

  function getSourceSegments() {
    return splitDocSegments(getSourceText());
  }

  function getTargetSegments() {
    return splitDocSegments(getTargetText());
  }

  function escRegex(s) {
    return String(s || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function setSourceReadability(readable, message) {
    sourceUnreadable = !readable;
    const row = $("tercume-panels-row");
    const simple = $("tercume-simple-state");
    const txt = $("tercume-simple-state-text");
    if (row) row.classList.toggle("tercume-panels-row--blocked", sourceUnreadable);
    if (simple) simple.hidden = !sourceUnreadable;
    if (txt) {
      txt.textContent =
        message ||
        "Bu PDF'den okunabilir metin çıkmadı. Önce OCR ile okuyun; sonra üstteki «Çevir» düğmesine basın.";
    }
    if (sourceUnreadable) {
      fullSourceDoc = "";
      fullTargetDoc = "";
      lastAlignedPayload = null;
      currentSegmentIndex = 0;
      setWorkbenchReviewMode(false);
      const fold = $("tercume-aligned-fold");
      if (fold) {
        fold.hidden = true;
        fold.open = false;
      }
      showReadQualityWarn("");
      const strip = $("tercume-segment-strip");
      if (strip) strip.hidden = true;
      const segEdit = $("tercume-segment-edit");
      if (segEdit) segEdit.hidden = true;
    }
    refreshSegmentPanelView();
  }

  function applySourcePagesPayload(j) {
    const pages = Array.isArray(j.pages) ? j.pages : [];
    sourcePageMeta = pages.map((p) => ({
      index: p.index,
      label: p.label || (p.index != null ? `Sayfa ${Number(p.index) + 1}` : ""),
      quality: p.quality,
      quality_hint: p.quality_hint,
    }));
    if (j.pages_total != null || j.meta?.pages_total != null) {
      pdfMeta = pdfMeta || {};
      pdfMeta.pages_total = j.pages_total ?? j.meta?.pages_total;
      pdfMeta.pages_read = pages.length;
      pdfMeta.truncated = false;
    }
    const texts = pages.map((p) => String(p.text || "").trim());
    const firstText = texts.find(Boolean) || "";
    lastAlignedPayload = null;
    currentSegmentIndex = 0;

    if (isPdfExtractGarbage(firstText)) {
      setSourceReadability(
        false,
        "Bu PDF taranmış veya bozuk metin katmanlı — kaynak kutusunda anlamsız kodlar görünmez. «OCR ile oku» deyin; metin gelince «Çevir».",
      );
      updatePdfHint();
      return;
    }

    setSourceReadability(true);
    fullSourceDoc = texts.filter(Boolean).join("\n\n");
    showReadQualityWarn("");

    refreshSegmentPanelView();
    updatePdfHint();
  }

  async function loadPdfPagesIntoSource(rel, opts = {}) {
    const range = pageRangeParams();
    let pf = range.label_from ?? 1;
    let pt = range.label_to ?? pf;
    if (opts.capWideRange && pt - pf > 8) {
      pt = pf;
      flash(`PDF: önce yalnızca sayfa ${pf} yüklendi. Tek sayfa çeviri için üst şeritte «1» – «1» girin.`);
    }
    const apiFrom = range.page_from != null ? range.page_from : pf - 1;
    const apiTo = range.page_to != null ? range.page_to : pt - 1;
    const qs = new URLSearchParams({ rel });
    qs.set("page_from", String(apiFrom));
    qs.set("page_to", String(apiTo));
    const res = await fetch(`${api()}/api/tercume/source-pages?${qs.toString()}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Sayfalar alınamadı");
    const pages = Array.isArray(j.pages) ? j.pages : [];
    if (!pages.length || !pages.some((p) => String(p.text || "").trim())) {
      throw new Error("Seçilen aralıkta metin yok (taranmış sayfa — OCR deneyin).");
    }
    applySourcePagesPayload(j);
    flash(`${pages.length} sayfa kaynak olarak yüklendi (${pf}–${pt}). Segment ${currentSegmentIndex + 1} panelde.`);
    if (pf != null) void loadPdfPreviewPage(pf);
    return j;
  }

  function setOcrBusy(on, label) {
    ocrBusy = !!on;
    const btns = [
      $("btn-tercume-simple-ocr"),
      $("btn-tercume-read-quality-ocr"),
      $("btn-tercume-ocr"),
    ];
    for (const b of btns) {
      if (!b) continue;
      b.disabled = ocrBusy;
      if (ocrBusy && b.id === "btn-tercume-simple-ocr") {
        b.dataset.prevLabel = b.textContent || "OCR ile oku";
        b.textContent = label || "OCR çalışıyor…";
      } else if (!ocrBusy && b.dataset.prevLabel) {
        b.textContent = b.dataset.prevLabel;
        delete b.dataset.prevLabel;
      }
    }
  }

  async function ocrPdfPageText(rel, pageNum) {
    const qs = new URLSearchParams({
      rel,
      page: String(pageNum),
      src_lang: String($("tercume-src-lang")?.value || "auto"),
      ocr_preset: ocrLangFromUi(),
    });
    const res = await fetch(`${api()}/api/tercume/pdf-page-ocr?${qs.toString()}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      const d = j.detail;
      throw new Error(typeof d === "string" ? d : j.error || `HTTP ${res.status}`);
    }
    return j;
  }

  async function runSimpleOcr() {
    if (!openRel) {
      flash("Önce dosya açın.");
      return;
    }
    if (ocrBusy) return;
    const low = String(openRel).toLowerCase();
    try {
      setOcrBusy(true, "OCR çalışıyor…");
      flash("OCR çalışıyor — sayfa taranıyor, lütfen bekleyin…");
      let text = "";
      if (low.endsWith(".pdf")) {
        const page = pageRangeParams().label_from ?? pdfPreviewPage ?? 1;
        const j = await ocrPdfPageText(openRel, page);
        text = String(j.text || "").trim();
        if (!text || text === "[OCR boş sonuç verdi]") {
          throw new Error("OCR boş sonuç verdi — sayfa görseli okunaksız olabilir.");
        }
      } else {
        text = stripPdfBanner(await readFileForTercume(openRel, { forceOcr: true }));
      }
      if (isPdfExtractGarbage(text)) {
        setSourceReadability(
          false,
          "OCR sonrası da metin zayıf. Başka sayfa veya daha net PDF deneyin.",
        );
        flash("OCR metni hâlâ okunaksız görünüyor.");
        return;
      }
      setSourceReadability(true);
      fullSourceDoc = text;
      fullTargetDoc = "";
      lastAlignedPayload = null;
      currentSegmentIndex = 0;
      refreshSegmentPanelView();
      flash("Metin hazır — üstte «Çevir» düğmesine basın.");
    } catch (e) {
      const msg = e.message || String(e);
      flash(msg);
      if (/tesseract|pytesseract|503/i.test(msg)) {
        setSourceReadability(
          false,
          "Tesseract kurulu değil veya Arapça dil paketi eksik. Ruzgar_OCR_Kur.bat çalıştırın, sonra tekrar «OCR ile oku».",
        );
      }
    } finally {
      setOcrBusy(false);
    }
  }

  function translateModeLabel() {
    const m = String($("tercume-translate-mode")?.value || "single");
    const map = {
      single: "tek parça",
      page: "sayfa sayfa",
      range: "sayfa aralığı",
      full: "tamamı",
      chat: "sohbet",
    };
    return map[m] || m;
  }

  function setWorkbenchReviewMode(on) {
    reviewMode = !!on;
    const wb = $("tercume-workbench");
    if (wb) wb.classList.toggle("tercume-workbench--review", reviewMode);
    document.querySelectorAll(".tercume-wb-mode").forEach((btn) => {
      const isRev = btn.dataset.tercumeWbMode === "review";
      btn.classList.toggle("is-active", reviewMode ? isRev : !isRev);
      btn.setAttribute("aria-selected", reviewMode ? (isRev ? "true" : "false") : isRev ? "false" : "true");
    });
    if (!reviewMode) {
      const fold = $("tercume-aligned-fold");
      if (fold) {
        fold.hidden = true;
        fold.open = false;
      }
    }
    refreshSegmentPanelView();
    updateStatusBar();
  }

  function maybeEnterReviewMode(score) {
    if (sourceUnreadable) return;
    if (score == null || !Number.isFinite(Number(score))) return;
    lastQualityScore = Number(score);
    if (Number(score) >= QUALITY_PASS) return;
    setWorkbenchReviewMode(true);
    const onlyIssues = $("tercume-aligned-only-issues");
    if (onlyIssues) onlyIssues.checked = true;
    if (getSourceText() || getTargetText()) {
      void runAlignedDiff().catch(() => {});
    }
  }

  function applyEditorDirection() {
    const srcEl = getSourceEl();
    const tgtEl = getTargetEl();
    if (!srcEl || !tgtEl) return;
    const srcLang = String($("tercume-src-lang")?.value || "auto").toLowerCase();
    const relLow = String(openRel || "").toLowerCase();
    const rtlSrc =
      srcLang === "ar" ||
      srcLang === "fa" ||
      /farsi|fars[iı]|_fa\.|arab|عرب|\.ar\./i.test(relLow) ||
      /mantik|attar|mesnevi|divan/i.test(relLow) && srcLang === "auto";
    const tgtLang = String($("tercume-tgt-lang")?.value || "tr").toLowerCase();
    const rtlTgt = tgtLang === "ar" || tgtLang === "fa";
    srcEl.classList.toggle("tercume-editor-rtl", rtlSrc);
    srcEl.classList.toggle("tercume-editor-ltr", !rtlSrc);
    tgtEl.classList.toggle("tercume-editor-rtl", rtlTgt);
    tgtEl.classList.toggle("tercume-editor-ltr", !rtlTgt);
  }

  function suggestLangFromPath(rel) {
    const low = String(rel || "").toLowerCase();
    const srcSel = $("tercume-src-lang");
    if (!srcSel) return;
    if (/farsi|fars[iı]|_fa\.pdf|mantik.*tayr/i.test(low)) {
      srcSel.value = "fa";
      const ocr = $("tercume-ocr-lang");
      if (ocr && ocr.value === "auto") ocr.value = "ara";
    } else if (/arab|arabi|\.ar\.|quran|kur'an/i.test(low)) {
      srcSel.value = "ar";
    }
    applyEditorDirection();
  }

  function scheduleTmHighlight() {
    if (tmHighlightTimer) clearTimeout(tmHighlightTimer);
    tmHighlightTimer = setTimeout(() => {
      tmHighlightTimer = null;
      void applyTmHighlight();
    }, 450);
  }

  function stripTmMarks(el) {
    if (!el) return;
    const t = String(el.innerText || "");
    el.innerText = t;
  }

  async function loadTmTermsForHighlight() {
    const terms = [];
    try {
      const res = await fetch(`${api()}/api/tercume/user-glossary?limit=120`);
      const j = await res.json().catch(() => ({}));
      if (res.ok && j.ok && Array.isArray(j.entries)) {
        for (const e of j.entries) {
          const src = String(e.src || "").trim();
          if (src.length >= 2) terms.push({ src });
        }
      }
    } catch {
      /* sessiz */
    }
    const seen = new Set();
    userGlossaryTerms = terms.filter((t) => {
      const k = t.src.toLowerCase();
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }

  async function applyTmHighlight() {
    const el = getSourceEl();
    if (!el || document.activeElement === el) return;
    await loadTmTermsForHighlight();
    const raw = getSourceText();
    if (!raw || !userGlossaryTerms.length) return;
    let html = esc(raw);
    const sorted = [...userGlossaryTerms].sort((a, b) => b.src.length - a.src.length);
    for (const t of sorted) {
      const src = String(t.src || "").trim();
      if (src.length < 2) continue;
      const re = new RegExp(escRegex(src), "gi");
      html = html.replace(re, (m) => `<mark class="tercume-tm-hit" title="Terim belleği">${m}</mark>`);
    }
    if (html !== esc(raw)) el.innerHTML = html;
    const stats = $("tercume-stats");
    if (stats && userGlossaryTerms.length) {
      const hint = stats.querySelector(".tercume-tm-hint");
      if (hint) hint.textContent = ` · TM: ${userGlossaryTerms.length} terim vurgulu`;
      else {
        const span = document.createElement("span");
        span.className = "tercume-tm-hint";
        span.textContent = ` · TM: ${userGlossaryTerms.length} terim vurgulu`;
        stats.appendChild(span);
      }
    }
    updateStatusBar();
  }

  function pushRecentFile(rel) {
    const r = String(rel || "").trim().replace(/\\/g, "/");
    if (!r) return;
    let list = [];
    try {
      list = JSON.parse(localStorage.getItem(LS_RECENT_FILES) || "[]");
      if (!Array.isArray(list)) list = [];
    } catch {
      list = [];
    }
    list = [r, ...list.filter((x) => x !== r)].slice(0, 5);
    try {
      localStorage.setItem(LS_RECENT_FILES, JSON.stringify(list));
    } catch {
      /* ignore */
    }
    renderRecentFiles();
  }

  function renderRecentFiles() {
    const ul = $("tercume-recent-list");
    if (!ul) return;
    let list = [];
    try {
      list = JSON.parse(localStorage.getItem(LS_RECENT_FILES) || "[]");
      if (!Array.isArray(list)) list = [];
    } catch {
      list = [];
    }
    ul.innerHTML = "";
    if (!list.length) {
      const li = document.createElement("li");
      li.textContent = "Henüz dosya açılmadı.";
      ul.appendChild(li);
      return;
    }
    for (const rel of list) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tercume-recent-btn";
      btn.textContent = rel.split("/").pop() || rel;
      btn.title = rel;
      btn.addEventListener("click", () => void openFile(rel));
      li.appendChild(btn);
      ul.appendChild(li);
    }
  }

  function updatePdfHint() {
    const wrap = $("tercume-pdf-hint");
    const txt = $("tercume-pdf-hint-text");
    if (!wrap || !txt) return;
    if (!openRel || !String(openRel).toLowerCase().endsWith(".pdf") || !pdfMeta) {
      wrap.hidden = true;
      return;
    }
    const total = pdfMeta.pages_total ?? "?";
    const read = pdfMeta.pages_read ?? "?";
    const trunc = pdfMeta.truncated ? ` (önizleme: ilk ${read} sayfa)` : "";
    const range = pageRangeParams();
    const rangeHint =
      range.label_from != null
        ? `Seçili aralık: ${range.label_from}–${range.label_to || range.label_from}`
        : "Üst şeritte sayfa aralığı girin (ör. 1–5)";
    txt.textContent = `PDF · ${total} sayfa${trunc}. ${rangeHint}.`;
    wrap.hidden = false;
  }

  async function loadPdfPageRange() {
    if (!openRel || !String(openRel).toLowerCase().endsWith(".pdf")) {
      flash("Sayfa aralığı yalnızca PDF için.");
      return;
    }
    const range = pageRangeParams();
    if (range.page_from == null) {
      flash("Başlangıç sayfası girin (üst şerit, örn. 1).");
      return;
    }
    flash(`PDF sayfaları yükleniyor: ${range.label_from}–${range.label_to || range.label_from}…`);
    await loadPdfPagesIntoSource(openRel, { capWideRange: false });
  }

  function segmentCount() {
    const aligned = lastAlignedPayload?.segments;
    if (aligned?.length) return aligned.length;
    return getSourceSegments().length;
  }

  function parsePageNumFromHint(hint) {
    const m = String(hint || "").match(/(\d+)/);
    return m ? Math.max(1, parseInt(m[1], 10) || 1) : null;
  }

  function replaceSourceSegment(outputIndex, newText) {
    const parts = splitDocSegments(fullSourceDoc || getSourceText());
    const idx = Number(outputIndex);
    if (!Number.isFinite(idx) || idx < 0) return false;
    if (idx < parts.length) {
      parts[idx] = newText;
      fullSourceDoc = parts.join("\n\n");
      refreshSegmentPanelView();
      scheduleTmHighlight();
      return true;
    }
    return false;
  }

  function updateSegmentEditVisibility() {
    const wrap = $("tercume-segment-edit");
    if (!wrap) return;
    wrap.hidden = segmentCount() <= 1;
  }

  function syncSegmentEditors() {
    const srcTa = $("tercume-segment-src");
    const tgtTa = $("tercume-segment-tgt");
    const lbl = $("tercume-seg-edit-label");
    if (!srcTa || !tgtTa) return;
    const aligned = lastAlignedPayload?.segments;
    const segs = getSourceSegments();
    const tgts = getTargetSegments();
    const total = aligned?.length || segs.length || 1;
    const idx = Math.max(0, Math.min(total - 1, currentSegmentIndex));
    currentSegmentIndex = idx;
    let src = "";
    let tgt = "";
    let pageHint = "";
    if (aligned?.[idx]) {
      src = String(aligned[idx].source || "");
      tgt = String(aligned[idx].target || "");
      pageHint = aligned[idx].page ? ` · sayfa ${aligned[idx].page}` : "";
    } else {
      src = segs[idx] || "";
      tgt = tgts[idx] || "";
    }
    srcTa.value = src;
    tgtTa.value = tgt;
    const rtl =
      getSourceEl()?.classList.contains("tercume-editor-rtl") ||
      String($("tercume-src-lang")?.value || "") === "fa" ||
      String($("tercume-src-lang")?.value || "") === "ar";
    srcTa.classList.toggle("tercume-editor-rtl", rtl);
    tgtTa.classList.toggle(
      "tercume-editor-rtl",
      String($("tercume-tgt-lang")?.value || "") === "fa" ||
        String($("tercume-tgt-lang")?.value || "") === "ar",
    );
    if (lbl) lbl.textContent = `Segment ${idx + 1} / ${total}${pageHint}`;
    const wrap = $("tercume-segment-edit");
    if (wrap) wrap.hidden = total <= 1;
  }

  function applySegmentEditorsToPanels(silent) {
    const src = String($("tercume-segment-src")?.value || "");
    const tgt = String($("tercume-segment-tgt")?.value || "");
    const aligned = lastAlignedPayload?.segments;
    const idx = currentSegmentIndex;
    if (aligned?.[idx]) {
      aligned[idx].source = src;
      aligned[idx].target = tgt;
      applyAlignedSegmentToTarget(aligned[idx], tgt);
      const parts = getSourceText().split(/\n\n+/);
      if (idx < parts.length) replaceSourceSegment(idx, src);
      else if (src) setSourceText(getSourceText() ? `${getSourceText()}\n\n${src}` : src);
      if (lastAlignedPayload) renderAlignedDiff(lastAlignedPayload);
    } else {
      replaceSourceSegment(idx, src);
      if (getTargetSegments().length > idx) replaceTargetSegment(idx, tgt);
      else if (tgt) {
        const parts = getTargetText().split(/\n\n+/);
        if (idx < parts.length) replaceTargetSegment(idx, tgt);
        else setTargetText(getTargetText() ? `${getTargetText()}\n\n${tgt}` : tgt);
      }
    }
    if (!silent) flash(`Segment ${idx + 1} panellere uygulandı.`);
    updateSegmentStrip();
  }

  function setPdfPreviewPanelVisible(show) {
    const panel = $("tercume-pdf-preview");
    const row = $("tercume-panels-row");
    const isPdf = openRel && String(openRel).toLowerCase().endsWith(".pdf");
    const reader = getTercumeUiMode() === "reader";
    const on = !!show && isPdf && !reader;
    if (panel) panel.hidden = !on;
    if (row) row.classList.toggle("tercume-panels-row--has-pdf", on);
  }

  async function refreshPdfPreviewCapability() {
    try {
      const res = await fetch(`${api()}/api/tercume/capabilities`);
      const j = await res.json().catch(() => ({}));
      pdfPreviewAvailable = !!(res.ok && j.capabilities?.pdf_preview);
    } catch {
      pdfPreviewAvailable = null;
    }
  }

  async function loadPdfPreviewPage(pageNum) {
    const panel = $("tercume-pdf-preview");
    const img = $("tercume-pdf-preview-img");
    const fallback = $("tercume-pdf-preview-fallback");
    const label = $("tercume-pdf-page-label");
    if (!openRel || !String(openRel).toLowerCase().endsWith(".pdf")) {
      setPdfPreviewPanelVisible(false);
      return;
    }
    setPdfPreviewPanelVisible(true);
    const total = Number(pdfMeta?.pages_total) || 9999;
    const page = Math.max(1, Math.min(total, Number(pageNum) || 1));
    pdfPreviewPage = page;
    if (label) label.textContent = `Sayfa ${page}${pdfMeta?.pages_total ? ` / ${pdfMeta.pages_total}` : ""}`;
    if (img) img.hidden = true;
    if (fallback) {
      fallback.hidden = false;
      fallback.textContent = "Sayfa yükleniyor…";
    }
    try {
      const qs = new URLSearchParams({ rel: openRel, page: String(page), dpi: "110" });
      const res = await fetch(`${api()}/api/tercume/pdf-page-preview?${qs.toString()}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) {
        const msg =
          typeof j.detail === "string"
            ? j.detail
            : res.status === 503
              ? "PyMuPDF kurulu değil: pip install pymupdf"
              : "Önizleme alınamadı";
        if (fallback) fallback.textContent = msg;
        return;
      }
      if (j.pages_total != null) {
        pdfMeta = pdfMeta || {};
        pdfMeta.pages_total = j.pages_total;
      }
      if (img && j.image_base64) {
        img.src = `data:image/png;base64,${j.image_base64}`;
        img.alt = `PDF sayfa ${page}`;
        img.hidden = false;
        if (fallback) fallback.hidden = true;
      }
      if (label) label.textContent = `Sayfa ${j.page || page} / ${j.pages_total || pdfMeta?.pages_total || "?"}`;
      updatePdfHint();
      updateStatusBar();
      syncBookReaderView();
    } catch (e) {
      if (fallback) {
        fallback.hidden = false;
        fallback.textContent = e.message || String(e);
      }
    }
  }

  function syncPdfPreviewFromSegment() {
    if (!openRel || !String(openRel).toLowerCase().endsWith(".pdf")) return;
    const aligned = lastAlignedPayload?.segments?.[currentSegmentIndex];
    let page = parsePageNumFromHint(aligned?.page);
    if (page == null) {
      const range = pageRangeParams();
      if (range.label_from != null) page = range.label_from + currentSegmentIndex;
      else page = pdfPreviewPage || 1;
    }
    void loadPdfPreviewPage(page);
  }

  function updateSegmentStrip() {
    const strip = $("tercume-segment-strip");
    const label = $("tercume-segment-label");
    if (!strip || !label) return;
    const segs = getSourceSegments();
    const n = segs.length;
    const total = lastAlignedPayload?.segments?.length || n;
    if (total <= 1) {
      strip.hidden = true;
      updateSegmentEditVisibility();
      return;
    }
    if (currentSegmentIndex >= total) currentSegmentIndex = Math.max(0, total - 1);
    if (currentSegmentIndex < 0) currentSegmentIndex = 0;
    strip.hidden = false;
    const pageHint =
      lastAlignedPayload?.segments?.[currentSegmentIndex]?.page ||
      sourcePageMeta[currentSegmentIndex]?.label ||
      (n > 1 ? `${currentSegmentIndex + 1}/${n}` : "");
    label.textContent = `Segment ${currentSegmentIndex + 1} / ${total}${pageHint ? ` · ${pageHint}` : ""}`;
    updateSegmentEditVisibility();
  }

  function focusSegment(index, opts = {}) {
    commitVisiblePanelsToFullDoc();
    const segs = getSourceSegments();
    const aligned = lastAlignedPayload?.segments;
    const total = aligned?.length || segs.length || 1;
    const idx = Math.max(0, Math.min(total - 1, Number(index) || 0));
    currentSegmentIndex = idx;
    if (aligned?.[idx]) {
      focusedAlignedRowKey = alignedRowKey(aligned[idx]);
      if (opts.renderTable !== false && lastAlignedPayload) renderAlignedDiff(lastAlignedPayload);
    }
    updateSegmentStrip();
    const fold = $("tercume-aligned-fold");
    if (opts.openTable && fold) {
      fold.hidden = false;
      fold.open = true;
    }
    const row = document.querySelector(`#tercume-aligned-tbody tr.focused-row`);
    row?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    refreshSegmentPanelView();
    if (opts.syncPdf !== false) syncPdfPreviewFromSegment();
  }

  async function translateCurrentSegment() {
    if (sourceUnreadable) {
      flash("Önce «OCR ile oku» — okunabilir metin olmadan çeviri yapılamaz.");
      return;
    }
    const segs = getSourceSegments();
    const aligned = lastAlignedPayload?.segments;
    let source = "";
    let pageIndex = currentSegmentIndex;
    const segEditOpen = !$("tercume-segment-edit")?.hidden;
    const inlineSrc = String($("tercume-segment-src")?.value || "").trim();
    if (segEditOpen && inlineSrc) {
      source = inlineSrc;
      pageIndex = aligned?.[currentSegmentIndex]
        ? Number(aligned[currentSegmentIndex].index)
        : currentSegmentIndex;
    } else if (aligned?.[currentSegmentIndex]) {
      source = String(aligned[currentSegmentIndex].source || "");
      pageIndex = Number(aligned[currentSegmentIndex].index);
    } else if (segs[currentSegmentIndex]) {
      source = segs[currentSegmentIndex];
    } else {
      source = getSourceText();
      pageIndex = 0;
    }
    if (!source.trim()) {
      flash("Segment boş.");
      return;
    }
    flash(`Segment ${currentSegmentIndex + 1} çevriliyor…`);
    const hit = await translateChunkApi(source, pageIndex);
    const out = String(hit.text || "").trim();
    if (aligned?.[currentSegmentIndex]) {
      aligned[currentSegmentIndex].target = out;
    }
    replaceTargetSegment(currentSegmentIndex, out);
    const tgtTa = $("tercume-segment-tgt");
    if (tgtTa) tgtTa.value = out;
    refreshSegmentPanelView();
    updateQualityStrip(hit.quality, `Segment ${currentSegmentIndex + 1}`);
    maybeEnterReviewMode(hit.quality?.score);
    if (reviewMode) void runAlignedDiff().catch(() => {});
  }

  function updateStatusBar() {
    const fileChip = $("tercume-status-file");
    const pageChip = $("tercume-status-page");
    const modeChip = $("tercume-status-mode");
    const qualChip = $("tercume-status-quality");
    const jobChip = $("tercume-status-job");
    const tmChip = $("tercume-status-tm");
    const pfChip = $("tercume-status-preflight");
    if (!fileChip) return;
    if (openRel) {
      const leaf = openRel.split("/").pop() || openRel;
      fileChip.textContent = `Dosya: ${leaf}`;
      fileChip.title = openRel;
    } else {
      fileChip.textContent = "Dosya: —";
      fileChip.title = "Sol listeden dosya seçin";
    }
    const range = pageRangeParams();
    pageChip.textContent =
      range.label_from != null
        ? `Sayfa: ${range.label_from}–${range.label_to || range.label_from}`
        : pdfMeta?.pages_total
          ? `Sayfa: 1–${pdfMeta.pages_total}`
          : "Sayfa: —";
    modeChip.textContent = `Mod: ${translateModeLabel()}`;
    if (lastQualityScore != null && Number.isFinite(lastQualityScore)) {
      qualChip.textContent = `Kalite: ${Math.round(lastQualityScore * 10) / 10}`;
      qualChip.classList.remove("is-warn", "is-bad", "is-ok");
      const tier = qualityTier(lastQualityScore);
      qualChip.classList.add(tier === "good" ? "is-ok" : tier === "bad" ? "is-bad" : "is-warn");
    } else {
      qualChip.textContent = "Kalite: —";
      qualChip.classList.remove("is-warn", "is-bad", "is-ok");
    }
    jobChip.textContent = `İş: ${jobStatusLabel}`;
    const memEl = $("tercume-memory-status");
    tmChip.textContent = memEl && !memEl.hidden ? memEl.textContent.replace(/^TM:\s*/i, "TM: ") : "TM: —";
    if (pfChip) {
      pfChip.textContent = `Hazırlık: ${preflightStatus.label}`;
      pfChip.classList.remove("is-ok", "is-bad");
      if (preflightStatus.ok === true) pfChip.classList.add("is-ok");
      else if (preflightStatus.ok === false) pfChip.classList.add("is-bad");
    }
  }

  function ocrLangFromUi() {
    return String($("tercume-ocr-lang")?.value || "auto").trim() || "auto";
  }

  function ocrQueryParams() {
    const preset = ocrLangFromUi();
    const src = String($("tercume-src-lang")?.value || "auto").trim();
    return `ocr_preset=${encodeURIComponent(preset)}&src_lang=${encodeURIComponent(src)}&tercume=1`;
  }

  async function readWorkspaceText(rel) {
    if (global.ruzgarApi?.readText) {
      const rr = await global.ruzgarApi.readText(rel);
      if (rr?.ok) return String(rr.text ?? "");
      throw new Error(rr?.error || "okunamadı");
    }
    const res = await fetch(`${api()}/api/workspace/read-text?rel=${encodeURIComponent(rel)}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
    return String(j.text ?? "");
  }

  async function readFileForTercume(rel, opts = {}) {
    const low = String(rel || "").toLowerCase();
    if (opts.forceOcr && low.endsWith(".pdf")) {
      const page = pageRangeParams().label_from ?? 1;
      const j = await ocrPdfPageText(rel, page);
      return String(j.text || "");
    }
    if (opts.forceOcr || IMAGE_EXTS.some((e) => low.endsWith(e))) {
      const res = await fetch(
        `${api()}/api/workspace/read-image-ocr?rel=${encodeURIComponent(rel)}&${ocrQueryParams()}`,
      );
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      return String(j.text ?? "");
    }
    if (low.endsWith(".pdf")) {
      const res = await fetch(`${api()}/api/workspace/read-pdf?rel=${encodeURIComponent(rel)}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      pdfMeta = {
        pages_total: j.pages_total,
        pages_read: j.pages_read,
        truncated: !!j.truncated_pages,
      };
      updatePdfHint();
      return String(j.text ?? "");
    }
    if (low.endsWith(".docx")) {
      const res = await fetch(`${api()}/api/workspace/read-docx?rel=${encodeURIComponent(rel)}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      return String(j.text ?? "");
    }
    if (EBOOK_EXTS.some((e) => low.endsWith(e))) {
      const res = await fetch(`${api()}/api/workspace/read-ebook?rel=${encodeURIComponent(rel)}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      showEbookMeta({
        title: j.title || j.meta?.title || j.meta?.ebook_title,
        author: j.author || j.meta?.author || j.meta?.ebook_author,
        chapters_read: j.chapters_read ?? j.meta?.chapters_read,
      });
      return String(j.text ?? "");
    }
    return readWorkspaceText(rel);
  }

  function defaultSaveDir() {
    const d = String(lastSaveDir || "").trim().replace(/\\/g, "/").replace(/\/$/, "");
    if (d && d.includes("arsiv")) return d;
    try {
      const ls = localStorage.getItem(LS_LAST_SAVE_DIR);
      if (ls && String(ls).includes("arsiv")) return String(ls).replace(/\\/g, "/").replace(/\/$/, "");
    } catch {
      /* ignore */
    }
    return "ilim-assistant/arsiv/tercume-output";
  }

  function rememberSaveDirFromRel(rel) {
    const raw = String(rel || "").trim().replace(/\\/g, "/");
    if (!raw) return;
    const idx = raw.lastIndexOf("/");
    if (idx <= 0) return;
    const dir = raw.slice(0, idx);
    lastSaveDir = dir;
    try {
      localStorage.setItem(LS_LAST_SAVE_DIR, dir);
    } catch {
      /* ignore */
    }
  }

  function defaultSaveRel() {
    const tgt = String($("tercume-tgt-lang")?.value || "tr").trim() || "tr";
    const fmt = String($("tercume-output-format")?.value || "txt").trim() || "txt";
    const ext = fmt === "md" ? ".md" : fmt === "html" ? ".html" : ".txt";
    const dir = defaultSaveDir();
    if (openRel) {
      const leaf = String(openRel).split("/").pop() || "kaynak";
      const stem = leaf.replace(/\.[^.]+$/, "") || "kaynak";
      return `${dir}/${stem}_${tgt}${ext}`;
    }
    return `${dir}/ceviri_${tgt}_${Date.now()}${ext}`;
  }

  function syncSavePlaceholder() {
    const inp = $("tercume-save-rel");
    if (inp && !inp.value.trim()) inp.placeholder = defaultSaveRel();
  }

  async function refreshSavePrefs() {
    try {
      const res = await fetch(`${api()}/api/tercume/save-prefs`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok) return;
      const dir = String(j.last_save_dir || "").trim().replace(/\\/g, "/");
      if (dir && dir.includes("arsiv")) {
        lastSaveDir = dir;
        try {
          localStorage.setItem(LS_LAST_SAVE_DIR, dir);
        } catch {
          /* ignore */
        }
        syncSavePlaceholder();
      }
    } catch {
      /* sessiz */
    }
  }

  function updateActiveLabel() {
    const el = $("btn-tercume-active-file") || $("tercume-active-file");
    if (!el) return;
    if (openRel) {
      const name = openRel.split("/").pop() || openRel;
      el.textContent = `Kaynak: ${name}`;
      el.classList.add("has-file");
      el.title = openRel;
    } else {
      el.textContent = "Kaynak: dosya seçilmedi";
      el.classList.remove("has-file");
      el.title = "Dosya panelinden seçin veya Dosya aç (Ctrl+O)";
    }
    updateSidebarActiveFile();
  }

  function updateStats() {
    const el = $("tercume-stats");
    if (!el) return;
    const t = getSourceText();
    const words = t.replace(/\s+/g, " ").trim() ? t.trim().split(/\s+/).length : 0;
    el.textContent = `${t.length.toLocaleString("tr-TR")} karakter · ${words.toLocaleString("tr-TR")} kelime`;
  }

  async function refreshArsivCatalog() {
    const ul = $("tercume-arsiv-download-list");
    if (!ul) return;
    ul.innerHTML = `<li class="code-tree-loading">${esc("Yükleniyor…")}</li>`;
    try {
      const res = await fetch(`${api()}/api/arsiv/download-catalog`);
      const j = await res.json().catch(() => ({}));
      if (!j.ok) throw new Error(j.error || j.detail || `HTTP ${res.status}`);
      ul.innerHTML = "";
      const items = Array.isArray(j.items) ? j.items : [];
      if (!items.length) {
        ul.innerHTML = `<li class="code-file-placeholder">${esc("Manifest boş")}</li>`;
        return;
      }
      for (const it of items) {
        const li = document.createElement("li");
        const done = !!it.downloaded;
        const badge = done ? "✓ var" : "bekliyor";
        const btn = done
          ? ""
          : `<button type="button" class="btn-secondary btn-compact arsiv-dl-btn" data-id="${esc(it.id)}">İndir</button>`;
        li.innerHTML = `<span class="arsiv-dl-title" title="${esc(it.folder || "")}">${esc(it.title || it.id)}</span><span class="arsiv-dl-badge ${done ? "ok" : "pending"}">${badge}</span>${btn}`;
        ul.appendChild(li);
      }
      ul.querySelectorAll(".arsiv-dl-btn").forEach((b) => {
        b.addEventListener("click", () => void downloadArsivItem(b.dataset.id));
      });
      const pending = Number(j.pending_count) || 0;
      flash(`Arşiv kataloğu: ${items.length - pending}/${items.length} indirildi`);
    } catch (e) {
      ul.innerHTML = `<li class="code-file-placeholder">${esc(e.message || e)}</li>`;
    }
  }

  async function downloadArsivItem(itemId) {
    if (!itemId) return;
    flash(`İndiriliyor: ${itemId}…`);
    const fd = new FormData();
    fd.append("item_id", itemId);
    const res = await fetch(`${api()}/api/arsiv/download-item`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!j.ok) throw new Error(j.error || j.detail || `HTTP ${res.status}`);
    if (j.skipped) flash(`Zaten var: ${j.rel || itemId}`);
    else flash(`İndirildi: ${j.rel || itemId} (${Math.round((j.bytes || 0) / 1024)} KB)`);
    await refreshArsivCatalog();
    await refreshTree();
    if (j.rel) await openFile(j.rel);
  }

  async function downloadArsivNext() {
    flash("Sıradaki indiriliyor…");
    const fd = new FormData();
    fd.append("limit", "1");
    const res = await fetch(`${api()}/api/arsiv/download-next`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!j.ok) throw new Error(j.error || j.detail || `HTTP ${res.status}`);
    const results = Array.isArray(j.results) ? j.results : [];
    const last = results[results.length - 1];
    if (!last) {
      flash("Bekleyen kayıt yok.");
      return;
    }
    if (!last.ok) throw new Error(last.error || "İndirme başarısız");
    if (last.skipped) flash(`Zaten var: ${last.rel || ""}`);
    else flash(`İndirildi: ${last.rel || ""}`);
    await refreshArsivCatalog();
    await refreshTree();
    if (last.rel) await openFile(last.rel);
  }

  async function refreshTree() {
    const list = $("tercume-file-list");
    if (!list) return;
    if (fileFilterQuery.length >= 2) {
      await runFileSearch();
      return;
    }
    list.classList.remove("tercume-file-tree--search");
    list.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
    renderPathCrumb();
    try {
      const items = deps.workspaceListDir ? await deps.workspaceListDir(workRoot) : [];
      list.innerHTML = "";
      for (const it of items) {
        list.appendChild(createTercumeTreeBranch(it, 0));
      }
      if (!items.length) {
        list.innerHTML = `<div class="code-file-placeholder">Klasör boş: <code>${esc(workRoot)}</code><br/>«Dosya aç» ile yükleyin veya alt klasör seçin.</div>`;
        updateFileCountLabel(0);
      } else {
        updateFileCountLabel(items.length);
      }
      if (openRel) void expandTreeToRel(openRel);
    } catch (e) {
      list.innerHTML = `<div class="code-file-placeholder">Liste hatası: ${esc(e.message || e)}</div>`;
      updateFileCountLabel(0);
    }
  }

  function markTreeActive(rel) {
    const list = $("tercume-file-list");
    if (!list) return;
    list.querySelectorAll(".code-tree-row.file.is-active").forEach((r) => r.classList.remove("is-active"));
    if (!rel) return;
    const norm = String(rel).replace(/\\/g, "/");
    for (const row of list.querySelectorAll(".code-tree-row.file")) {
      const r = String(row.dataset.rel || "").replace(/\\/g, "/");
      if (r === norm) row.classList.add("is-active");
    }
  }

  async function openFile(rel) {
    if (!rel) return;
    markTreeActive(rel);
    updateSidebarActiveFile();
    pdfMeta = null;
    sourcePageMeta = [];
    lastAlignedPayload = null;
    fullSourceDoc = "";
    fullTargetDoc = "";
    showReadQualityWarn("");
    updatePdfHint();
    setSourceText("Dosya yükleniyor…");
    updateActiveLabel();
    suggestLangFromPath(rel);
    try {
      openRel = rel;
      const low = String(rel).toLowerCase();
      setSourceReadability(true);
      if (low.endsWith(".pdf")) {
        await loadPdfPagesIntoSource(rel, { capWideRange: true });
      } else {
        const text = await readFileForTercume(rel);
        if (isPdfExtractGarbage(text)) {
          setSourceReadability(false);
        } else {
          fullSourceDoc = stripPdfBanner(text);
          fullTargetDoc = "";
          refreshSegmentPanelView();
        }
      }
      pushRecentFile(rel);
      updateActiveLabel();
      syncSavePlaceholder();
      flash(`Kaynak yüklendi: ${rel.split("/").pop()}`);
      getSourceEl()?.focus();
      void refreshApprenticeLog();
      void refreshMemoryStatus();
      void refreshCapabilities(rel);
      void loadTmTermsForHighlight().then(() => scheduleTmHighlight());
      await loadAlignedNotesForRel(rel);
      currentSegmentIndex = 0;
      if (low.endsWith(".pdf")) {
        pdfPreviewPage = pageRangeParams().label_from || 1;
        void loadPdfPreviewPage(pdfPreviewPage);
      } else {
        setPdfPreviewPanelVisible(false);
      }
      syncBookReaderView();
    } catch (e) {
      openRel = rel;
      pushRecentFile(rel);
      const msg = String(e.message || e);
      fullSourceDoc = `(Dosya: ${rel}\n\nÖnizleme alınamadı: ${msg}\n\nBüyük PDF için OCR veya sayfa aralığı deneyin.)`;
      fullTargetDoc = "";
      refreshSegmentPanelView();
      updateActiveLabel();
      flash("Tam metin yüklenemedi; dosya yolu kayıtlı.");
      void refreshMemoryStatus();
      void refreshCapabilities(rel);
      await loadAlignedNotesForRel(rel);
      if (String(rel).toLowerCase().endsWith(".pdf")) {
        pdfPreviewPage = pageRangeParams().label_from || 1;
        void loadPdfPreviewPage(pdfPreviewPage);
      }
    }
  }

  function showEbookMeta(meta) {
    const wrap = $("tercume-ebook-meta");
    const txt = $("tercume-ebook-meta-text");
    if (!wrap || !txt) return;
    const title = String(meta?.title || "").trim();
    const author = String(meta?.author || "").trim();
    const ch = meta?.chapters_read;
    if (!title && !author && ch == null) {
      wrap.hidden = true;
      return;
    }
    const parts = [];
    if (title) parts.push(title);
    if (author) parts.push(author);
    if (ch != null && Number(ch) > 0) parts.push(`${ch} bölüm`);
    txt.textContent = parts.join(" · ") || "—";
    wrap.hidden = false;
  }

  function hideEbookMeta() {
    const wrap = $("tercume-ebook-meta");
    if (wrap) wrap.hidden = true;
  }

  async function refreshUserGlossary() {
    const ul = $("tercume-user-glossary-list");
    if (!ul) return;
    try {
      const res = await fetch(`${api()}/api/tercume/user-glossary?limit=40`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok) return;
      ul.innerHTML = "";
      const rows = Array.isArray(j.entries) ? j.entries : [];
      if (!rows.length) {
        const li = document.createElement("li");
        li.textContent = "Henüz terim yok — kaynak ve hedef yazıp Ekle deyin.";
        ul.appendChild(li);
        return;
      }
      for (const e of rows) {
        const li = document.createElement("li");
        const main = document.createElement("span");
        main.className = "term-main";
        const scope = e.scope ? ` [${e.scope}]` : "";
        main.textContent = `«${e.src}» → ${e.tr || e.en || "?"}${scope}`;
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn-secondary btn-compact";
        btn.textContent = "Sil";
        btn.addEventListener("click", () => {
          void deleteUserTerm(String(e.id || ""));
        });
        li.appendChild(main);
        li.appendChild(btn);
        ul.appendChild(li);
      }
    } catch {
      /* sessiz */
    }
  }

  async function addUserTerm() {
    const src = String($("tercume-term-src")?.value || "").trim();
    const tgt = String($("tercume-term-tgt")?.value || "").trim();
    const scope = String($("tercume-term-scope")?.value || "").trim();
    if (!src || !tgt) {
      flash("Kaynak terim ve hedef çeviri gerekli.");
      return;
    }
    const fd = new FormData();
    const tgtLang = String($("tercume-tgt-lang")?.value || "tr");
    fd.append("src", src);
    if (tgtLang === "en") fd.append("en", tgt);
    else if (tgtLang === "ar") fd.append("ar", tgt);
    else fd.append("tr", tgt);
    if (scope) fd.append("scope", scope);
    else if (openRel) fd.append("scope", openRel);
    const res = await fetch(`${api()}/api/tercume/user-glossary/add`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "Eklenemedi");
    $("tercume-term-src").value = "";
    $("tercume-term-tgt").value = "";
    flash(`Terim eklendi: «${src}» → ${tgt}`);
    void refreshUserGlossary();
    void loadTmTermsForHighlight().then(() => scheduleTmHighlight());
  }

  async function deleteUserTerm(id) {
    const fd = new FormData();
    fd.append("entry_id", id);
    const res = await fetch(`${api()}/api/tercume/user-glossary/delete`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Silinemedi");
    void refreshUserGlossary();
  }

  async function importGlossaryFile(file) {
    if (!file) return;
    const text = await file.text();
    const name = String(file.name || "").toLowerCase();
    const fmt = name.endsWith(".json") ? "json" : "csv";
    const fd = new FormData();
    fd.append("text", text);
    fd.append("fmt", fmt);
    fd.append("merge", "1");
    const res = await fetch(`${api()}/api/tercume/user-glossary/import`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "İçe aktarılamadı");
    flash(`Terim içe aktarıldı: +${j.added || 0} (toplam ${j.total || "?"})`);
    void refreshUserGlossary();
  }

  async function exportTmxFile() {
    const fd = new FormData();
    if (openRel) fd.append("rel", openRel);
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    fd.append("src_lang", String($("tercume-src-lang")?.value || "auto"));
    const res = await fetch(`${api()}/api/tercume/tmx/export`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "TMX dışa aktarılamadı");
    const blob = new Blob([String(j.tmx || "")], { type: "application/xml;charset=utf-8" });
    const a = document.createElement("a");
    const stem = openRel ? openRel.replace(/^.*[/\\]/, "").replace(/\.[^.]+$/, "") : "terimler";
    a.href = URL.createObjectURL(blob);
    a.download = `${stem || "terimler"}.tmx`;
    a.click();
    URL.revokeObjectURL(a.href);
    flash(`TMX indirildi (${j.units || "?"} birim).`);
  }

  async function importTmxFile(file) {
    if (!file) return;
    const text = await file.text();
    const fd = new FormData();
    fd.append("text", text);
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    fd.append("merge", "1");
    const res = await fetch(`${api()}/api/tercume/tmx/import`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "TMX içe aktarılamadı");
    flash(`TMX içe aktarıldı: +${j.added || 0} terim`);
    void refreshUserGlossary();
  }

  const ALIGNED_STATUS_TR = {
    paired: "Eşleşti",
    missing_target: "Hedef eksik",
    extra_target: "Fazla hedef",
    empty: "—",
  };

  function alignedRowKey(row) {
    const idx = Number(row?.index);
    const page = String(row?.page || "");
    return `${page}#${Number.isFinite(idx) ? idx : "?"}`;
  }

  function alignedNotesToObject() {
    const out = {};
    for (const [k, v] of alignedRowNotes.entries()) {
      const kk = String(k || "").trim();
      const vv = String(v || "").trim();
      if (kk && vv) out[kk] = vv;
    }
    return out;
  }

  async function loadAlignedNotesForRel(rel) {
    alignedRowNotes.clear();
    const raw = String(rel || "").trim();
    if (!raw) return;
    try {
      const res = await fetch(`${api()}/api/tercume/aligned-notes?rel=${encodeURIComponent(raw)}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok || typeof j.notes !== "object") return;
      for (const [k, v] of Object.entries(j.notes || {})) {
        const kk = String(k || "").trim();
        const vv = String(v || "").trim();
        if (kk && vv) alignedRowNotes.set(kk, vv);
      }
    } catch {
      /* sessiz */
    }
  }

  function scheduleSaveAlignedNotes() {
    if (!openRel) return;
    if (alignedNotesSaveTimer) clearTimeout(alignedNotesSaveTimer);
    alignedNotesSaveTimer = setTimeout(() => {
      alignedNotesSaveTimer = null;
      const fd = new FormData();
      fd.append("rel", String(openRel || ""));
      fd.append("notes_json", JSON.stringify(alignedNotesToObject()));
      void fetch(`${api()}/api/tercume/aligned-notes/save`, { method: "POST", body: fd }).catch(() => {});
    }, 350);
  }

  async function scoreSegmentQuality(sourceText, targetText) {
    const fd = new FormData();
    fd.append("source_text", String(sourceText || ""));
    fd.append("target_text", String(targetText || ""));
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    const res = await fetch(`${api()}/api/tercume/quality-score`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Kalite ölçülemedi");
    return j.quality || null;
  }

  function applyAlignedSegmentToTarget(row, text) {
    const idx = Number(row?.index);
    if (!Number.isFinite(idx) || idx < 0) return false;
    return replaceTargetSegment(idx, String(text || ""));
  }

  async function retryAlignedSegment(row, textarea, qEl) {
    const source = String(row?.source || "");
    if (!source.trim()) {
      flash("Kaynak segment boş; yeniden çeviri yapılamadı.");
      return;
    }
    flash(`Segment yeniden çevriliyor: ${row.page || row.index + 1}`);
    const hit = await translateChunkApi(source, Number(row?.index));
    const out = String(hit.text || "").trim();
    textarea.value = out;
    applyAlignedSegmentToTarget(row, out);
    if (qEl) {
      const sc = hit?.quality?.score;
      qEl.textContent = sc != null ? `Skor: ${sc}` : "Skor: ?";
    }
    if (lastAlignedPayload) {
      const key = alignedRowKey(row);
      approvedAlignedRows.delete(key);
    }
    void runAlignedDiff();
  }

  function isProblemRow(row) {
    return String(row?.status || "") !== "paired";
  }

  async function retryUnapprovedAlignedRows() {
    if (!lastAlignedPayload || !Array.isArray(lastAlignedPayload.segments)) {
      flash("Önce hizalı diff çalıştırın.");
      return;
    }
    const rows = lastAlignedPayload.segments.filter((r) => {
      const key = alignedRowKey(r);
      return !approvedAlignedRows.has(key) && String(r.source || "").trim();
    });
    if (!rows.length) {
      flash("Yeniden çevrilecek onaysız satır yok.");
      return;
    }
    const maxN = Math.min(rows.length, 8);
    flash(`Onaysız satırlar yeniden çevriliyor (${maxN})…`);
    for (let i = 0; i < maxN; i++) {
      const r = rows[i];
      try {
        const hit = await translateChunkApi(String(r.source || ""), Number(r.index));
        const out = String(hit.text || "").trim();
        applyAlignedSegmentToTarget(r, out);
      } catch {
        /* bir satır hatası diğerlerini durdurmasın */
      }
    }
    flash(`Toplu yeniden çeviri bitti: ${maxN} satır`);
    void runAlignedDiff();
  }

  async function exportApprovedAlignedToTmx() {
    if (!lastAlignedPayload || !Array.isArray(lastAlignedPayload.segments)) {
      flash("Önce hizalı diff çalıştırın.");
      return;
    }
    const rows = lastAlignedPayload.segments
      .filter((r) => approvedAlignedRows.has(alignedRowKey(r)))
      .map((r) => ({
        source: String(r.source || "").trim(),
        target: String(r.target || "").trim(),
      }))
      .filter((r) => r.source && r.target);
    if (!rows.length) {
      flash("TMX için en az bir onaylı satır gerekli.");
      return;
    }
    const fd = new FormData();
    fd.append("segments_json", JSON.stringify(rows));
    fd.append("src_lang", String($("tercume-src-lang")?.value || "auto"));
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    const res = await fetch(`${api()}/api/tercume/tmx/export-segments`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) throw new Error(typeof j.detail === "string" ? j.detail : "TMX üretilemedi");
    const blob = new Blob([String(j.tmx || "")], { type: "application/xml;charset=utf-8" });
    const a = document.createElement("a");
    const stem = openRel ? openRel.replace(/^.*[/\\]/, "").replace(/\.[^.]+$/, "") : "cat-lite";
    a.href = URL.createObjectURL(blob);
    a.download = `${stem || "cat-lite"}_approved.tmx`;
    a.click();
    URL.revokeObjectURL(a.href);
    flash(`Onaylı TMX indirildi (${j.units || rows.length} satır).`);
  }

  function renderAlignedDiff(payload) {
    const fold = $("tercume-aligned-fold");
    const tbody = $("tercume-aligned-tbody");
    const statsEl = $("tercume-aligned-stats");
    if (!fold || !tbody) return;
    const allRows = Array.isArray(payload?.segments) ? payload.segments : [];
    if (!reviewMode || sourceUnreadable) {
      fold.hidden = true;
      fold.open = false;
      return;
    }
    const onlyIssues = !!$("tercume-aligned-only-issues")?.checked;
    const rows = onlyIssues ? allRows.filter((r) => isProblemRow(r)) : allRows;
    if (!allRows.length) {
      fold.hidden = true;
      tbody.innerHTML = "";
      return;
    }
    fold.hidden = false;
    const st = payload.stats || {};
    const warn = (st.missing_target || 0) + (st.extra_target || 0);
    const approvedN = allRows.filter((r) => approvedAlignedRows.has(alignedRowKey(r))).length;
    if (statsEl) {
      statsEl.textContent = payload.aligned
        ? `${rows.length}/${allRows.length} segment · hizalı · onay ${approvedN}`
        : `${rows.length}/${allRows.length} segment · ${warn} uyarı · onay ${approvedN}`;
    }
    tbody.innerHTML = "";
    if (!rows.length) {
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 5;
      td.textContent = "Filtrede gösterilecek sorunlu satır yok.";
      tr.appendChild(td);
      tbody.appendChild(tr);
      fold.open = true;
      return;
    }
    for (const r of rows) {
      const tr = document.createElement("tr");
      const rowKey = alignedRowKey(r);
      if (approvedAlignedRows.has(rowKey)) tr.classList.add("approved-row");
      if (focusedAlignedRowKey === rowKey) tr.classList.add("focused-row");
      tr.addEventListener("click", () => {
        focusedAlignedRowKey = rowKey;
        const idx = Number(r.index);
        if (Number.isFinite(idx)) focusSegment(idx, { renderTable: true, openTable: false });
        else renderAlignedDiff(lastAlignedPayload || payload);
      });
      const idx = document.createElement("td");
      idx.textContent = String(r.page || r.index + 1);
      const tdSrc = document.createElement("td");
      tdSrc.className = "col-src";
      tdSrc.textContent = (r.source || "").slice(0, 320) || "—";
      const tdTgt = document.createElement("td");
      tdTgt.className = "col-tgt";
      const ta = document.createElement("textarea");
      ta.className = "tercume-aligned-edit";
      ta.value = String(r.target || "");
      ta.placeholder = "Hedef segment";
      tdTgt.appendChild(ta);
      const tdSt = document.createElement("td");
      const code = String(r.status || "paired");
      tdSt.className = `st-${code}`;
      tdSt.textContent = ALIGNED_STATUS_TR[code] || code;
      const tdAct = document.createElement("td");
      tdAct.className = "col-actions";
      const actions = document.createElement("div");
      actions.className = "tercume-aligned-actions";
      const btnApply = document.createElement("button");
      btnApply.type = "button";
      btnApply.className = "btn-secondary btn-compact";
      btnApply.textContent = "Hedefe uygula";
      const btnRetry = document.createElement("button");
      btnRetry.type = "button";
      btnRetry.className = "btn-secondary btn-compact";
      btnRetry.textContent = "Yeniden çevir";
      const btnQ = document.createElement("button");
      btnQ.type = "button";
      btnQ.className = "btn-secondary btn-compact";
      btnQ.textContent = "Skor";
      const btnApprove = document.createElement("button");
      btnApprove.type = "button";
      btnApprove.className = "btn-secondary btn-compact";
      btnApprove.textContent = approvedAlignedRows.has(rowKey) ? "Onayı kaldır" : "Onayla";
      const note = document.createElement("input");
      note.type = "text";
      note.className = "tercume-aligned-note";
      note.placeholder = "Satır notu (editoryal)";
      note.value = alignedRowNotes.get(rowKey) || "";
      const q = document.createElement("small");
      q.className = "tercume-aligned-q";
      q.textContent = note.value ? `Not: ${note.value.slice(0, 80)}` : "";
      btnApply.addEventListener("click", () => {
        const ok = applyAlignedSegmentToTarget(r, ta.value);
        if (!ok) {
          flash(`Segment uygulanamadı: #${r.index + 1}`);
          return;
        }
        flash(`Segment hedefe uygulandı: #${r.index + 1}`);
      });
      btnRetry.addEventListener("click", () => {
        void retryAlignedSegment(r, ta, q).catch((e) => flash(e.message || String(e)));
      });
      btnApprove.addEventListener("click", () => {
        if (approvedAlignedRows.has(rowKey)) approvedAlignedRows.delete(rowKey);
        else approvedAlignedRows.add(rowKey);
        renderAlignedDiff(lastAlignedPayload || payload);
      });
      note.addEventListener("input", () => {
        const v = String(note.value || "").trim();
        if (v) alignedRowNotes.set(rowKey, v);
        else alignedRowNotes.delete(rowKey);
        q.textContent = v ? `Not: ${v.slice(0, 80)}` : "";
        scheduleSaveAlignedNotes();
      });
      btnQ.addEventListener("click", () => {
        void scoreSegmentQuality(r.source, ta.value)
          .then((qual) => {
            const sc = qual?.score;
            const issues = Array.isArray(qual?.issues) ? qual.issues : [];
            const noteTxt = alignedRowNotes.get(rowKey);
            q.textContent = sc != null ? `Skor: ${sc}${issues[0] ? ` · ${issues[0]}` : ""}` : "Skor: ?";
            if (noteTxt) q.textContent += ` · Not: ${String(noteTxt).slice(0, 60)}`;
          })
          .catch((e) => flash(e.message || String(e)));
      });
      actions.appendChild(btnApply);
      actions.appendChild(btnRetry);
      actions.appendChild(btnApprove);
      actions.appendChild(btnQ);
      tdAct.appendChild(actions);
      tdAct.appendChild(note);
      tdAct.appendChild(q);
      tr.appendChild(idx);
      tr.appendChild(tdSrc);
      tr.appendChild(tdTgt);
      tr.appendChild(tdSt);
      tr.appendChild(tdAct);
      tbody.appendChild(tr);
    }
    fold.open = true;
  }

  async function runAlignedDiff() {
    const tgt = getTargetText();
    const src = getSourceText();
    if (!tgt && !src) {
      flash("Önce kaynak veya hedef metin olsun.");
      return;
    }
    const fd = new FormData();
    fd.append("source_text", src);
    fd.append("target_text", tgt);
    if (openRel) fd.append("rel", openRel);
    flash("Hizalı karşılaştırma hazırlanıyor…");
    const res = await fetch(`${api()}/api/tercume/aligned-diff`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "Diff başarısız");
    lastAlignedPayload = j;
    renderAlignedDiff(j);
    refreshSegmentPanelView();
    updateSegmentStrip();
    syncSegmentEditors();
    if (!j.aligned) flash("Segment sayıları tam hizalı değil — tabloya bakın.");
    else flash("Kaynak ve hedef segmentler hizalı görünüyor.");
  }

  function renderAcademicCheck(payload) {
    const fold = $("tercume-academic-fold");
    const ul = $("tercume-academic-list");
    const stats = $("tercume-academic-stats");
    if (!fold || !ul) return;
    const rows = Array.isArray(payload?.claim_rows) ? payload.claim_rows : [];
    const risk = String(payload?.risk || "unknown");
    const uncited = Number(payload?.uncited_claims || 0);
    const coverage = Number(payload?.citation_coverage || 0);
    if (stats) stats.textContent = `risk:${risk} · atıf kapsama:${coverage}% · eksik:${uncited}`;
    ul.innerHTML = "";
    const hints = Array.isArray(payload?.hints) ? payload.hints : [];
    if (hints.length) {
      for (const h of hints.slice(0, 4)) {
        const li = document.createElement("li");
        li.textContent = `Öneri: ${String(h)}`;
        ul.appendChild(li);
      }
    }
    for (const r of rows.slice(0, 20)) {
      if (!r.claim_like) continue;
      const li = document.createElement("li");
      const has = r.has_citation ? "✓" : "✗";
      li.textContent = `${has} ${String(r.excerpt || "").slice(0, 170)}`;
      ul.appendChild(li);
    }
    if (!ul.children.length) {
      const li = document.createElement("li");
      li.textContent = "İddia/atıf satırı bulunamadı.";
      ul.appendChild(li);
    }
    fold.hidden = false;
    fold.open = true;
  }

  async function runAcademicCheck() {
    const src = getSourceText();
    const tgt = getTargetText();
    if (!src && !tgt) {
      flash("Önce kaynak veya hedef metin olsun.");
      return;
    }
    flash("Akademik kaynak izi kontrolü yapılıyor…");
    const fd = new FormData();
    fd.append("source_text", src);
    fd.append("target_text", tgt);
    const res = await fetch(`${api()}/api/tercume/academic-check`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Akademik kontrol başarısız");
    renderAcademicCheck(j);
    flash(`Akademik kontrol: risk=${j.risk}, atıf kapsama=${j.citation_coverage}%`);
  }

  async function refreshMemoryStatus() {
    const el = $("tercume-memory-status");
    if (!el) return;
    if (!openRel) {
      el.hidden = true;
      return;
    }
    const tgt = String($("tercume-tgt-lang")?.value || "tr").trim() || "tr";
    try {
      const res = await fetch(
        `${api()}/api/tercume/memory-status?rel=${encodeURIComponent(openRel)}&tgt_lang=${encodeURIComponent(tgt)}`,
      );
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok || j.enabled === false) {
        el.hidden = true;
        return;
      }
      const n = Number(j.pairs) || 0;
      const disk = j.persisted_on_disk ? " · diskte" : "";
      const tail = j.has_tail ? " · üslup" : "";
      el.hidden = false;
      el.textContent = n > 0 ? `TM: ${n} terim${disk}${tail}` : `TM: boş${disk}`;
      updateStatusBar();
    } catch {
      el.hidden = true;
      updateStatusBar();
    }
  }

  async function onTreeClick(ev) {
    const list = $("tercume-file-list");
    const row = ev.target.closest(".code-tree-row");
    if (!row || !list?.contains(row)) return;
    ev.preventDefault();
    const rel = row.dataset.rel;
    if (!rel) return;

    if (row.classList.contains("folder")) {
      const branch = row.closest(".code-tree-branch");
      const kids = branch?.querySelector(":scope > .code-tree-children");
      if (!kids) return;
      const depth = Number.parseInt(row.dataset.depth || "0", 10);
      if (kids.dataset.loaded !== "1") {
        kids.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
        kids.hidden = false;
        try {
          const items = deps.workspaceListDir ? await deps.workspaceListDir(rel) : [];
          kids.innerHTML = "";
          for (const x of items) {
            kids.appendChild(createTercumeTreeBranch(x, depth + 1));
          }
          kids.dataset.loaded = "1";
        } catch {
          kids.innerHTML = `<div class="code-tree-err">${esc("Liste okunamadı.")}</div>`;
          return;
        }
        row.classList.add("is-expanded");
        const chevOpen = row.querySelector(".code-tree-chev");
        if (chevOpen) chevOpen.textContent = "▾";
        return;
      }
      kids.hidden = !kids.hidden;
      row.classList.toggle("is-expanded", !kids.hidden);
      const chev = row.querySelector(".code-tree-chev");
      if (chev) chev.textContent = kids.hidden ? "▸" : "▾";
      return;
    }

    if (row.classList.contains("file")) {
      await openFile(rel);
    }
  }

  function extractEserSearchQuery(text) {
    const t = String(text || "").trim();
    if (!t) return "";
    const m = t.match(/^(?:ara|arat|bul|eser|kitap|yazar)\s*[:：]\s*(.+)$/im);
    if (m) return m[1].trim().slice(0, 200);
    if (/^https?:\/\//i.test(t)) return "";
    if (t.length > 220) return t.slice(0, 200);
    return t;
  }

  function openGoogleScholar(query) {
    const q = extractEserSearchQuery(query);
    const url = q
      ? `https://scholar.google.com/scholar?q=${encodeURIComponent(q)}&hl=tr`
      : "https://scholar.google.com/?hl=tr";
    if (global.ruzgarApi?.openExternalUrl) void global.ruzgarApi.openExternalUrl(url);
    else window.open(url, "_blank", "noopener");
    flash(q ? `Google Scholar: «${q}»` : "Google Scholar açıldı.");
  }

  function renderEserSearchEmpty(message) {
    const ul = $("tercume-work-eser-sites");
    const hint = $("tercume-eser-hint");
    if (hint) hint.textContent = message || "Arama henüz yapılmadı — yukarıdaki kutuya yazın.";
    const fallback = "Sonuç yok. Yukarıdaki arama kutusuna yazıp Ara düğmesine basın.";
    if (ul) ul.innerHTML = `<li class="code-file-placeholder">${esc(message || fallback)}</li>`;
  }

  async function pollTercumeJob(jobId, onTick) {
    const id = String(jobId || "").trim();
    if (!id) throw new Error("job_id yok");
    for (let i = 0; i < 480; i += 1) {
      const res = await fetch(`${api()}/api/tercume/jobs/${encodeURIComponent(id)}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
      if (onTick) onTick(j);
      const st = String(j.status || "");
      if (st === "awaiting_approval") {
        const msg = String(j.checkpoint_message || j.label || "Okuma bitti — çeviriye devam edilsin mi?");
        const choice = window.confirm(`${msg}\n\nTamam = Çevir · İptal = menüden Atla/İptal`);
        const fd = new FormData();
        fd.append("job_id", id);
        fd.append("action", choice ? "continue" : "skip");
        const rr = await fetch(`${api()}/api/tercume/super-resume`, { method: "POST", body: fd });
        const rj = await rr.json().catch(() => ({}));
        if (!rr.ok) throw new Error(typeof rj.detail === "string" ? rj.detail : rj.error || "Devam hatası");
        flash(choice ? "Çeviri devam ediyor…" : "Çeviri atlandı — rapor kaydediliyor…");
        continue;
      }
      if (st === "done") return j;
      if (st === "failed" || st === "cancelled") {
        throw new Error(String(j.error || j.label || st));
      }
      await new Promise((r) => setTimeout(r, 1500));
    }
    throw new Error("İndirme zaman aşımı");
  }

  function pageRangeParams() {
    const fromEl = $("tercume-page-from");
    const toEl = $("tercume-page-to");
    const pfRaw = String(fromEl?.value || "").trim();
    const ptRaw = String(toEl?.value || "").trim();
    const pf = pfRaw ? Math.max(1, parseInt(pfRaw, 10) || 1) : null;
    const pt = ptRaw ? Math.max(1, parseInt(ptRaw, 10) || 1) : pf;
    const page_from = pf != null ? pf - 1 : null;
    const page_to = pt != null ? pt - 1 : null;
    return { page_from, page_to, label_from: pf, label_to: pt };
  }

  async function importFromSearch(item, query) {
    const localRel = String(item?.local_rel || "").trim();
    if (localRel) {
      setTercumeTab("calisma");
      await openFile(localRel);
      flash("Arşivdeki dosya açıldı.");
      return;
    }
    const fd = new FormData();
    fd.append("q", String(query || "").trim());
    fd.append("download_url", String(item?.download_url || item?.url || "").trim());
    fd.append("title", String(item?.title || "").trim());
    flash("Arşive alınıyor (arka planda)…");
    const res = await fetch(`${api()}/api/tercume/import-from-search`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
    if (j.mode === "local" && j.rel) {
      setTercumeTab("calisma");
      await openFile(String(j.rel));
      flash(String(j.message || "Yerel dosya açıldı."));
      return;
    }
    const jobId = String(j.job_id || "").trim();
    if (!jobId) throw new Error("İş kuyruğa alınamadı");
    const final = await pollTercumeJob(jobId, (tick) => {
      const msg = String(tick.label || tick.step || tick.status || "İndiriliyor…");
      flash(msg);
    });
    const rel = String(final.rel || "").trim();
    if (rel) {
      setTercumeTab("calisma");
      await openFile(rel);
      flash("Arşive alındı — dosya açıldı.");
      return;
    }
    flash("İş bitti; dosya yolu bulunamadı.");
  }

  function renderEserSearchResults(data) {
    const ul = $("tercume-work-eser-sites");
    const hint = $("tercume-eser-hint");
    const inp = $("tercume-eser-input");
    if (!ul) return;
    const q = String(data?.query || "").trim();
    if (inp && q) inp.value = q;
    const items = Array.isArray(data?.items) ? data.items : [];
    if (hint) {
      const weak =
        data?.quality === "weak"
          ? " ⚠ Sonuçlar zayıf — soldaki yerel dosyalar veya Scholar."
          : "";
      const local =
        Array.isArray(data?.local_archive_matches) && data.local_archive_matches.length
          ? ` Yerel: ${data.local_archive_matches
              .slice(0, 2)
              .map((m) => m.name)
              .join(", ")}.`
          : "";
      const localFirst = data?.web_search_skipped
        ? " ✓ Arşivde var — internet aranmadı; soldan dosyayı açın."
        : data?.local_archive_matches?.length
          ? " Yerel + internet birleşik."
          : "";
      const expanded =
        data?.expanded_query && String(data.expanded_query).trim() !== q
          ? ` Alias: «${String(data.expanded_query).slice(0, 80)}».`
          : "";
      const sb = data?.search_backend;
      const ddgNote =
        sb && sb.ok === false
          ? ` ⚠ ${(Array.isArray(data.search_hints) && data.search_hints[0]) || sb.detail || "DDG kapalı"}.`
          : "";
      hint.textContent = q
        ? `«${q}» — ${items.length} sonuç.${localFirst}${weak}${local}${expanded}${ddgNote} Aç → site · Arşive al → indirme kuyruğu.`
        : "Arama henüz yapılmadı.";
    }
    if (!items.length) {
      ul.innerHTML = `<li class="code-file-placeholder">${esc("Sonuç bulunamadı. Farklı yazım veya daha kısa ad deneyin.")}</li>`;
      return;
    }
    ul.innerHTML = "";
    items.forEach((it, idx) => {
      const url = String(it.url || "");
      const localRel = String(it.local_rel || "").trim();
      const li = document.createElement("li");
      li.className = "tercume-eser-result-row";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "tercume-eser-result-btn";
      const src = esc(String(it.source || ""));
      const scoreTag =
        it.score != null ? ` · ${esc(String(it.confidence || ""))} ${Number(it.score).toFixed(0)}` : "";
      const title = esc(String(it.title || url).slice(0, 120));
      const snip = esc(String(it.snippet || "").slice(0, 160));
      btn.innerHTML =
        `<span class="tercume-eser-result-main">` +
        `<span class="tercume-eser-result-title">${idx + 1}. ${title}</span>` +
        (snip ? `<span class="tercume-eser-result-snippet">${snip}</span>` : "") +
        `</span>` +
        `<span class="tercume-eser-result-meta"><span class="tercume-eser-result-src">${src}${scoreTag}</span><span class="tercume-eser-site-go">Aç →</span></span>`;
      btn.addEventListener("click", () => {
        if (localRel) {
          setTercumeTab("calisma");
          void openFile(localRel).catch((e) => flash(e.message));
          return;
        }
        const dl = String(it.download_url || url || "");
        if (!dl && !url) return;
        if (url && global.ruzgarApi?.openExternalUrl) void global.ruzgarApi.openExternalUrl(url);
        else if (url) window.open(url, "_blank", "noopener");
        const urlInp = $("tercume-import-url");
        if (urlInp) urlInp.value = dl || url;
        flash("Site açıldı; URL indirme kutusuna yazıldı.");
      });
      const importBtn = document.createElement("button");
      importBtn.type = "button";
      importBtn.className = "btn-secondary btn-compact tercume-eser-import-btn";
      importBtn.textContent = localRel ? "Aç" : "Arşive al";
      importBtn.title = localRel
        ? "Yerel arşivde — Çalışma sekmesinde aç"
        : "Arka planda indir → tercume-imports";
      importBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const q = String($("tercume-eser-input")?.value || data?.query || "").trim();
        void importFromSearch(it, q).catch((e) => flash(e.message || String(e)));
      });
      li.appendChild(btn);
      li.appendChild(importBtn);
      ul.appendChild(li);
    });
  }

  async function runPreflight() {
    const qs = new URLSearchParams();
    if (openRel) qs.set("rel", openRel);
    const res = await fetch(`${api()}/api/tercume/preflight?${qs.toString()}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
    const checks = Array.isArray(j.checks) ? j.checks : [];
    const lines = checks.map((c) => `${c.ok ? "✓" : "✗"} ${c.label}${c.detail ? `: ${c.detail}` : ""}`);
    const hints = Array.isArray(j.hints) ? j.hints : [];
    preflightStatus = { ok: !!j.ready, label: j.ready ? "tamam" : "eksik" };
    updateStatusBar();
    flash(
      (j.ready ? "Hazırlık tamam — " : "Eksik var — ") +
        lines.slice(0, 4).join(" · ") +
        (hints[0] ? ` · ${hints[0]}` : ""),
    );
    void refreshReadiness();
    return j;
  }

  async function refreshPreflightChip() {
    try {
      const qs = new URLSearchParams();
      if (openRel) qs.set("rel", openRel);
      const res = await fetch(`${api()}/api/tercume/preflight?${qs.toString()}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) return;
      preflightStatus = { ok: !!j.ready, label: j.ready ? "tamam" : "eksik" };
      updateStatusBar();
    } catch {
      /* sessiz */
    }
  }

  async function runSuperAnalyst() {
    const q = String($("tercume-eser-input")?.value || "").trim();
    const rel = String(openRel || "").trim();
    if (!q && !rel) {
      flash("Arama kutusuna eser yazın veya Çalışmada dosya açın.");
      return;
    }
    flash("Tam analist zinciri başladı (uzun sürebilir)…");
    const fd = new FormData();
    fd.append("q", q);
    fd.append("rel", rel);
    fd.append("read_pages", "5");
    fd.append("translate", "1");
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    fd.append("src_lang", String($("tercume-src-lang")?.value || "auto"));
    const res = await fetch(`${api()}/api/tercume/super-start`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
    const jobId = String(j.job_id || "").trim();
    if (!jobId) throw new Error("İş başlatılamadı");
    const final = await pollTercumeJob(jobId, (tick) => {
      flash(String(tick.label || tick.step || "Tam analist…"));
    });
    const fileRel = String(final.rel || "").trim();
    if (fileRel) {
      setTercumeTab("calisma");
      await openFile(fileRel);
    }
    const reportRel = String(final.report_rel || "").trim();
    flash(
      reportRel
        ? `Tam analist bitti — rapor: ${reportRel}`
        : String(final.label || "Tam analist bitti")
    );
  }

  async function runAnalystReport() {
    const q = String($("tercume-eser-input")?.value || "").trim();
    const rel = String(openRel || "").trim();
    if (!q && !rel) {
      flash("Arama kutusuna eser yazın veya Çalışmada dosya açın.");
      return;
    }
    flash("Analist raporu hazırlanıyor…");
    const fd = new FormData();
    fd.append("q", q);
    fd.append("rel", rel);
    fd.append("read_pages", "5");
    fd.append("auto_import", rel ? "0" : "1");
    const res = await fetch(`${api()}/api/tercume/report-start`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
    const jobId = String(j.job_id || "").trim();
    if (!jobId) throw new Error("Rapor işi başlatılamadı");
    const final = await pollTercumeJob(jobId, (tick) => {
      flash(String(tick.label || tick.step || "Rapor…"));
    });
    const reportRel = String(final.report_rel || "").trim();
    const steps = Array.isArray(final.next_steps) ? final.next_steps.join(" · ") : "";
    if (reportRel) {
      flash(`Rapor kaydedildi: ${reportRel}${steps ? ` — ${steps.slice(0, 120)}` : ""}`);
    } else {
      flash(steps || "Rapor tamamlandı.");
    }
    const hint = $("tercume-eser-hint");
    if (hint && final.markdown_preview) {
      hint.textContent = String(final.markdown_preview).replace(/\s+/g, " ").slice(0, 280);
    }
  }

  async function runEserSearch(query) {
    const q = extractEserSearchQuery(query);
    if (!q) {
      flash("Arama metni boş.");
      return false;
    }
    const ul = $("tercume-work-eser-sites");
    const inp = $("tercume-eser-input");
    if (inp) inp.value = q;
    if (ul) ul.innerHTML = `<li class="code-tree-loading">${esc("Aranıyor (birkaç kaynak taranıyor)…")}</li>`;
    const hint = $("tercume-eser-hint");
    if (hint) hint.textContent = `«${q}» aranıyor…`;
    flash("İnternet araması başladı…");
    try {
      const res = await fetch(`${api()}/api/tercume/eser-search?q=${encodeURIComponent(q)}&web=1`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
      if (!j.ok) throw new Error(j.error || "Arama başarısız");
      renderEserSearchResults(j);
      flash(`${j.total || 0} sonuç listelendi.`);
      setTercumeTab("ara");
      return true;
    } catch (e) {
      renderEserSearchEmpty(`Arama hatası: ${e.message || e}`);
      flash(e.message || "Arama hatası");
      return false;
    }
  }

  function guessTargetLangFromText(text) {
    const t = String(text || "").toLowerCase();
    const hits = [
      { code: "tr", re: /\b(türkçe|turkce|turkish)\b/i },
      { code: "en", re: /\b(ingilizce|english)\b/i },
      { code: "ar", re: /\b(arapça|arapca|arabic)\b/i },
      { code: "de", re: /\b(almanca|german|deutsch)\b/i },
      { code: "fr", re: /\b(fransızca|fransizca|french)\b/i },
      { code: "fa", re: /\b(farsça|farsca|persian)\b/i },
      { code: "ru", re: /\b(rusça|rusca|russian)\b/i },
    ];
    for (const h of hits) {
      if (h.re.test(t)) return h.code;
    }
    return "";
  }

  function parseSaveRelFromText(text) {
    const t = String(text || "");
    const quoted = t.match(/(?:kaydet|yaz)[^"'“”]*["“]([^"”]+)["”]/i);
    if (quoted?.[1]) return quoted[1].trim();
    const pathy = t.match(/(?:kaydet|yaz)[^\n]*\s((?:ilim-assistant|arsiv|output|outputs)[^\s]+)/i);
    if (pathy?.[1]) return pathy[1].trim();
    return "";
  }

  function parseUrlFromText(text) {
    const m = String(text || "").match(/https?:\/\/[^\s<>"']+/i);
    return m ? m[0] : "";
  }

  function parsePageRangeFromText(text) {
    const t = String(text || "");
    const m = t.match(/(?:sayfa|pages?)\s*(\d{1,5})\s*[-–—]\s*(\d{1,5})/i);
    if (m) {
      const a = Number(m[1]);
      const b = Number(m[2]);
      if (Number.isFinite(a) && Number.isFinite(b) && a > 0 && b > 0) {
        return { from: Math.min(a, b), to: Math.max(a, b) };
      }
    }
    const single = t.match(/(?:sayfa|page)\s*(\d{1,5})\b/i);
    if (single) {
      const n = Number(single[1]);
      if (Number.isFinite(n) && n > 0) return { from: n, to: n };
    }
    return null;
  }

  function extractSearchQueryFromText(text) {
    const raw = String(text || "").trim();
    if (!raw) return "";
    const cleaned = raw
      .replace(/\b(lütfen|lutfen|rica etsem|abi|hocam)\b/gi, " ")
      .replace(/\b(indir|download|çevir|cevir|tercüme et|translate|kaydet|yaz)\b/gi, " ")
      .replace(/\b(bunu|şunu|sunu|şu|bu|dosyaya|dile|sayfaları|sayfalari|sayfa)\b/gi, " ")
      .replace(/https?:\/\/[^\s<>"']+/gi, " ")
      .replace(/\d+\s*[-–—]\s*\d+/g, " ")
      .replace(/[^\p{L}\p{N}\s.'-]+/gu, " ")
      .replace(/\s+/g, " ")
      .trim();
    return cleaned.length >= 3 ? cleaned : "";
  }

  function buildIntentReply(main, steps = [], confidence = 0.8) {
    const safeMain = String(main || "Tamam.").trim();
    const list = Array.isArray(steps) ? steps.filter(Boolean) : [];
    const conf = Math.max(0, Math.min(1, Number(confidence) || 0));
    const confTag = conf >= 0.86 ? "yüksek" : conf >= 0.65 ? "orta" : "düşük";
    const stepTxt = list.length ? `\nAdımlar: ${list.join(" → ")}` : "";
    return `${safeMain}${stepTxt}\nGüven: ${confTag} (${Math.round(conf * 100)}%)`;
  }

  async function pickDownloadFolder() {
    if (global.ruzgarApi?.pickSaveDirectory) {
      const r = await global.ruzgarApi.pickSaveDirectory();
      if (r?.ok) {
        lastDownloadDir = { abs: r.abs || "", rel: r.rel || "" };
        return r;
      }
      return { ok: false };
    }
    if (global.ruzgarApi?.pickWorkspaceDirectory) {
      const r = await global.ruzgarApi.pickWorkspaceDirectory();
      if (r?.ok) {
        lastDownloadDir = { abs: "", rel: r.rel || workRoot };
        return { ok: true, rel: r.rel };
      }
    }
    lastDownloadDir = { abs: "", rel: workRoot };
    return { ok: true, rel: workRoot };
  }

  let readPollTimer = null;
  let activeReadJobId = null;

  async function startReadAnalyze() {
    if (!openRel) {
      flash("Önce listeden bir dosya seçin.");
      return;
    }
    if (readPollTimer) {
      flash("Okuma analizi zaten çalışıyor.");
      return;
    }
    showProgress(0, 1, "Okuma analizi başlıyor…");
    const res = await fetch(`${api()}/api/tercume/read-start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rel: openRel }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
    if (!j.job_id) throw new Error("İş başlatılamadı");
    activeReadJobId = j.job_id;
    pollReadJob(j.job_id);
  }

  function pollReadJob(jobId) {
    if (readPollTimer) clearInterval(readPollTimer);
    readPollTimer = setInterval(async () => {
      try {
        const res = await fetch(`${api()}/api/tercume/read-status?job_id=${encodeURIComponent(jobId)}`);
        const j = await res.json().catch(() => ({}));
        if (!res.ok || !j.ok) return;
        showProgress(1, 1, j.label || j.status || "Okunuyor…");
        if (j.status === "done" || j.status === "failed" || j.status === "cancelled") {
          clearInterval(readPollTimer);
          readPollTimer = null;
          activeReadJobId = null;
          hideProgress();
          if (j.status === "done") {
            const msg =
              j.read_hint ||
              `Okuma: ${j.ok_pages || 0} iyi, ${j.low_pages || 0} zayıf, ${j.empty_pages || 0} boş sayfa.`;
            flash(msg);
            if (j.ocr_recommended) flash("⚠ Taranmış kitap olabilir — OCR dili seçip tekrar deneyin.");
          } else {
            flash(j.error || "Okuma analizi tamamlanamadı.");
          }
        }
      } catch {
        /* tekrar dene */
      }
    }, 1500);
  }

  let batchPollTimer = null;
  let activeBatchJobId = null;
  let lastJobOutputs = [];

  function clearPageJobStorage() {
    try {
      localStorage.removeItem(LS_PAGE_JOB);
    } catch {
      /* ignore */
    }
  }

  function setPageJobStorage(jobId) {
    try {
      if (jobId) localStorage.setItem(LS_PAGE_JOB, String(jobId));
    } catch {
      /* ignore */
    }
  }

  function showJobPanel(show) {
    const panel = $("tercume-job-panel");
    if (!panel) return;
    if (getTercumeUiMode() === "reader" && activeDuzenDock !== "status") {
      panel.hidden = true;
      return;
    }
    panel.hidden = !show;
  }

  function qualityTier(score) {
    if (score == null || !Number.isFinite(Number(score))) return "unknown";
    const s = Number(score);
    if (s >= QUALITY_WARN) return "good";
    if (s >= QUALITY_PASS) return "warn";
    return "bad";
  }

  function hideQualityStrip() {
    const strip = $("tercume-quality-strip");
    const retryBtn = $("btn-tercume-retry-quality");
    if (strip) strip.hidden = true;
    if (retryBtn) retryBtn.hidden = true;
    lastTranslateContext = null;
    lastQualityScore = null;
    updateStatusBar();
  }

  function updateQualityStrip(quality, contextLabel) {
    const strip = $("tercume-quality-strip");
    const badge = $("tercume-quality-badge");
    const detail = $("tercume-quality-detail");
    const issuesEl = $("tercume-quality-issues");
    const retryBtn = $("btn-tercume-retry-quality");
    if (!strip || !badge) return;
    if (!quality || quality.score == null || !Number.isFinite(Number(quality.score))) {
      strip.hidden = true;
      if (retryBtn) retryBtn.hidden = true;
      return;
    }
    if (getTercumeUiMode() === "reader" && activeDuzenDock !== "status") {
      strip.hidden = true;
      if (retryBtn) retryBtn.hidden = true;
      lastQualityScore = Number(quality.score);
      updateStatusBar();
      return;
    }
    const score = Number(quality.score);
    lastQualityScore = score;
    const tier = qualityTier(score);
    strip.hidden = false;
    updateStatusBar();
    if (tier === "bad") maybeEnterReviewMode(score);
    badge.textContent = String(Math.round(score * 10) / 10);
    badge.className = `tercume-quality-badge tercume-quality-${tier}`;
    const label = String(contextLabel || "Son parça").trim();
    const pass = quality.ok !== false && tier !== "bad";
    if (detail) {
      detail.textContent = pass
        ? `${label} — kalite uygun`
        : `${label} — düşük kalite, kontrol edin`;
    }
    const issues = Array.isArray(quality.issues) ? quality.issues.filter(Boolean) : [];
    if (issuesEl) {
      issuesEl.textContent = issues.length
        ? issues.join(" · ")
        : tier === "good"
          ? "Belirgin sorun yok."
          : "Skor düşük — metni gözden geçirin.";
    }
    if (retryBtn) {
      retryBtn.hidden = !lastTranslateContext || tier === "good";
    }
  }

  function updateQualityStripFromJob(j) {
    const qs = j?.quality_summary;
    if (qs && qs.avg_score != null && Number.isFinite(Number(qs.avg_score))) {
      const low = Number(qs.low_count) || 0;
      const issues = [];
      if (low > 0) {
        issues.push(`${low} sayfa skor < ${QUALITY_PASS}`);
        const lp = Array.isArray(qs.low_pages) ? qs.low_pages : [];
        if (lp.length) issues.push(lp.slice(0, 4).join(", "));
      }
      if (qs.min_score != null && Number(qs.min_score) < QUALITY_PASS) {
        issues.push(`en düşük: ${qs.min_score}`);
      }
      updateQualityStrip(
        {
          score: Number(qs.avg_score),
          ok: low === 0,
          issues,
        },
        `Ortalama (${qs.pages_scored || "?"} sayfa)`,
      );
      if ($("btn-tercume-retry-quality")) $("btn-tercume-retry-quality").hidden = true;
      return;
    }
    const outs = Array.isArray(j?.outputs) ? j.outputs : [];
    const scored = outs.filter((o) => o.ok && o.quality_score != null);
    if (!scored.length) {
      hideQualityStrip();
      return;
    }
    const scores = scored.map((o) => Number(o.quality_score));
    const avg = Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10;
    const low = scores.filter((s) => s < QUALITY_PASS).length;
    updateQualityStrip(
      {
        score: avg,
        ok: low === 0,
        issues: low ? [`${low} düşük skorlu parça`] : [],
      },
      `Ortalama (${scores.length} parça)`,
    );
    if ($("btn-tercume-retry-quality")) $("btn-tercume-retry-quality").hidden = true;
  }

  async function retryLastChunkQuality() {
    const ctx = lastTranslateContext;
    if (!ctx?.sourceText) {
      flash("Yeniden çevrilecek parça yok — önce Tek parça ile çevirin.");
      return;
    }
    flash(`Yeniden çevriliyor: ${ctx.label || "parça"}…`);
    try {
      const hit = await translateChunkApi(String(ctx.sourceText), ctx.pageIndex);
      if (ctx.mode === "single") {
        setTargetText(hit.text);
      }
      updateQualityStrip(hit.quality, ctx.label || "Yeniden çeviri");
      flash(
        hit.quality?.ok === false
          ? "Yeniden çevrildi — kalite hâlâ düşük, metni kontrol edin."
          : "Yeniden çeviri tamamlandı.",
      );
      void refreshApprenticeLog();
      void refreshMemoryStatus();
    } catch (e) {
      flash(e.message || String(e));
    }
  }

  function renderReviewQueue(items) {
    const fold = $("tercume-review-fold");
    const ul = $("tercume-review-list");
    const cnt = $("tercume-review-count");
    if (!fold || !ul) return;
    const rows = Array.isArray(items) ? items : [];
    if (cnt) cnt.textContent = String(rows.length);
    if (!rows.length) {
      fold.hidden = true;
      ul.innerHTML = "";
      return;
    }
    fold.hidden = false;
    ul.innerHTML = "";
    for (const it of rows) {
      const li = document.createElement("li");
      const main = document.createElement("span");
      main.className =
        it.kind === "error" ? "review-main review-err" : "review-main review-warn";
      const sc =
        it.quality_score != null ? ` skor ${it.quality_score}` : it.error ? ` — ${it.error}` : "";
      main.textContent = `${it.page}${sc}`;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-secondary btn-compact";
      btn.textContent = "Yeniden çevir";
      btn.addEventListener("click", () => {
        void retranslateReviewItem(it).catch((e) => flash(e.message || String(e)));
      });
      li.appendChild(main);
      li.appendChild(btn);
      ul.appendChild(li);
    }
  }

  async function refreshReviewQueue(jobId) {
    if (!jobId) {
      renderReviewQueue([]);
      return;
    }
    try {
      const res = await fetch(
        `${api()}/api/tercume/review-queue?job_id=${encodeURIComponent(jobId)}`,
      );
      const j = await res.json().catch(() => ({}));
      if (res.ok && j.ok) {
        renderReviewQueue(j.items || []);
        return;
      }
    } catch {
      /* fallback */
    }
    const items = [];
    for (let i = 0; i < lastJobOutputs.length; i++) {
      const o = lastJobOutputs[i];
      if (!o || typeof o !== "object") continue;
      if (o.ok === false) {
        items.push({
          kind: "error",
          page: o.page,
          page_index: o.page_index,
          output_index: i,
          error: o.error,
        });
      } else if (o.quality_score != null && Number(o.quality_score) < QUALITY_PASS) {
        items.push({
          kind: "low_quality",
          page: o.page,
          page_index: o.page_index,
          output_index: i,
          quality_score: o.quality_score,
        });
      }
    }
    renderReviewQueue(items);
  }

  function replaceTargetSegment(outputIndex, newText) {
    const parts = getTargetText().split(/\n\n+/);
    const idx = Number(outputIndex);
    if (!Number.isFinite(idx) || idx < 0) return false;
    if (idx < parts.length) {
      parts[idx] = newText;
      setTargetText(parts.join("\n\n"));
      return true;
    }
    return false;
  }

  async function retranslateReviewItem(item) {
    if (!openRel) {
      flash("Önce kaynak dosyayı açın.");
      return;
    }
    const res = await fetch(`${api()}/api/tercume/source-pages?rel=${encodeURIComponent(openRel)}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok || !Array.isArray(j.pages)) {
      throw new Error("Kaynak sayfa listesi alınamadı");
    }
    let page = null;
    if (item.page_index != null) {
      page = j.pages.find((p) => p.index === item.page_index);
    }
    if (!page && item.page) {
      page = j.pages.find((p) => String(p.label) === String(item.page));
    }
    if (!page) {
      throw new Error(`Sayfa bulunamadı: ${item.page}`);
    }
    flash(`Yeniden çevriliyor: ${item.page}…`);
    const hit = await translateChunkApi(String(page.text || ""), page.index);
    const escPage = String(item.page || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const errRe = new RegExp(`\\[HATA sayfa ${escPage}:[^\\]]*\\]`, "i");
    let updated = false;
    const tgt = getTargetText();
    if (errRe.test(tgt)) {
      setTargetText(tgt.replace(errRe, hit.text));
      updated = true;
    } else if (item.output_index != null) {
      updated = replaceTargetSegment(item.output_index, hit.text);
    }
    if (!updated) {
      setTargetText(`${tgt}\n\n${hit.text}`);
      flash("Parça hedef sonuna eklendi (konum eşleşmedi).");
    } else {
      flash(`Güncellendi: ${item.page} (skor ${hit.quality?.score ?? "?"})`);
    }
    updateQualityStrip(hit.quality, item.page);
    void refreshApprenticeLog();
    if (activeBatchJobId) void refreshReviewQueue(activeBatchJobId);
  }

  function renderPageJobLog(outputs, summary) {
    const ul = $("tercume-job-log");
    const sum = $("tercume-job-summary");
    if (!ul) return;
    ul.innerHTML = "";
    const rows = Array.isArray(outputs) ? outputs : [];
    const tail = rows.length > 48 ? rows.slice(-48) : rows;
    for (const o of tail) {
      const li = document.createElement("li");
      li.className = o.ok ? "tercume-job-log-ok" : "tercume-job-log-err";
      const page = String(o.page || "?");
      if (o.ok) {
        const scNum = o.quality_score != null ? Number(o.quality_score) : null;
        const sc = scNum != null ? ` · skor ${scNum}` : "";
        if (scNum != null && scNum < QUALITY_PASS) {
          li.className = "tercume-job-log-warn";
          const iss = Array.isArray(o.quality_issues) ? o.quality_issues[0] : "";
          li.textContent = `⚠ ${page}${sc}${iss ? ` — ${iss}` : ""}`;
        } else {
          li.textContent = `✓ ${page}${sc}`;
        }
      } else {
        li.textContent = `✗ ${page}: ${String(o.error || "?").slice(0, 80)}`;
      }
      ul.appendChild(li);
    }
    if (sum && summary != null) sum.textContent = String(summary);
    if (tail.length) ul.scrollTop = ul.scrollHeight;
    lastJobOutputs = rows;
    if (activeBatchJobId) void refreshReviewQueue(activeBatchJobId);
  }

  function countJobOutputs(outputs) {
    const rows = Array.isArray(outputs) ? outputs : [];
    let okN = 0;
    let errN = 0;
    for (const o of rows) {
      if (o.ok) okN += 1;
      else errN += 1;
    }
    return { okN, errN };
  }

  async function finishPageRangeJob(j) {
    hideProgress();
    const outs = Array.isArray(j.outputs) ? j.outputs : [];
    let okN = Number(j.ok_count);
    let errN = Number(j.error_count);
    if (!Number.isFinite(okN) || !Number.isFinite(errN)) {
      const c = countJobOutputs(outs);
      okN = c.okN;
      errN = c.errN;
    }
    const partial = String(j.partial_text || "").trim();
    if (partial) setTargetText(partial);
    else if (j.output_rel) {
      try {
        setTargetText(await readWorkspaceText(String(j.output_rel)));
      } catch (e) {
        flash(`Dosyaya kaydedildi (${j.output_rel}); panel: ${e.message || e}`);
      }
    }
    const saveInp = $("tercume-save-rel");
    if (saveInp && j.output_rel) {
      saveInp.value = String(j.output_rel);
      rememberSaveDirFromRel(j.output_rel);
    }
    syncSavePlaceholder();
    clearPageJobStorage();
    activeBatchJobId = null;
    const qHint =
      j.quality_summary?.low_count > 0
        ? ` · ${j.quality_summary.low_count} düşük skor`
        : j.quality_summary?.avg_score != null
          ? ` · ort. ${j.quality_summary.avg_score}`
          : "";
    renderPageJobLog(outs, `${okN} başarılı · ${errN} hatalı${qHint}`);
    updateQualityStripFromJob(j);
    const lowN = Number(j.quality_summary?.low_count) || 0;
    if (lowN > 0) {
      setWorkbenchReviewMode(true);
      const onlyIssues = $("tercume-aligned-only-issues");
      if (onlyIssues) onlyIssues.checked = true;
      void runAlignedDiff().catch(() => {});
    }
    flash(
      String(j.label || `Arka plan çevirisi bitti: ${okN}/${okN + errN}`) +
        (lowN ? ` — ${lowN} sayfa düşük kalite.` : ""),
    );
    jobStatusLabel = "bitti";
    updateStatusBar();
    void refreshApprenticeLog();
    void refreshBatchJobsList();
    void refreshMemoryStatus();
  }

  async function refreshBatchJobsList() {
    const ul = $("tercume-job-recent-list");
    if (!ul) return;
    try {
      const res = await fetch(`${api()}/api/tercume/batch-jobs?limit=10`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok || !Array.isArray(j.items)) return;
      ul.innerHTML = "";
      for (const it of j.items) {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "tercume-job-recent-btn";
        const relLeaf = String(it.rel || "").split("/").pop() || "dosya";
        const st = String(it.status || "?");
        const prog =
          it.total != null && Number(it.total) > 0
            ? `${it.done ?? 0}/${it.total}`
            : String(it.label || "").slice(0, 40);
        btn.textContent = `${st} · ${relLeaf} · ${prog}`;
        btn.title = String(it.job_id || "");
        btn.addEventListener("click", () => {
          const jid = String(it.job_id || "").trim();
          if (!jid) return;
          if (st === "running" || st === "queued") {
            if (batchPollTimer) {
              flash("Zaten izlenen bir iş var.");
              return;
            }
            activeBatchJobId = jid;
            setPageJobStorage(jid);
            showJobPanel(true);
            flash("İşe yeniden bağlanıldı.");
            pollBatchJob(jid, { pageRange: it.job_type === "page_range" });
            return;
          }
          if (st === "done" && it.output_rel) {
            void (async () => {
              try {
                const stRes = await fetch(
                  `${api()}/api/tercume/batch-status?job_id=${encodeURIComponent(jid)}`,
                );
                const stJ = await stRes.json().catch(() => ({}));
                if (stRes.ok && stJ.ok) await finishPageRangeJob(stJ);
                else {
                  setTargetText(await readWorkspaceText(String(it.output_rel)));
                  const saveInp = $("tercume-save-rel");
                  if (saveInp) saveInp.value = String(it.output_rel);
                  flash(`Çıktı yüklendi: ${it.output_rel}`);
                }
              } catch (e) {
                flash(e.message || String(e));
              }
            })();
          }
        });
        li.appendChild(btn);
        ul.appendChild(li);
      }
    } catch {
      /* sessiz */
    }
  }

  async function resumeActivePageJobIfAny() {
    let jid = "";
    try {
      jid = localStorage.getItem(LS_PAGE_JOB) || "";
    } catch {
      return;
    }
    if (!jid || batchPollTimer) return;
    try {
      const res = await fetch(`${api()}/api/tercume/batch-status?job_id=${encodeURIComponent(jid)}`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok) {
        clearPageJobStorage();
        return;
      }
      if (j.job_type !== "page_range") {
        clearPageJobStorage();
        return;
      }
      if (j.status === "running" || j.status === "queued") {
        activeBatchJobId = jid;
        if (getTercumeUiMode() !== "reader") showJobPanel(true);
        flash("Devam eden arka plan çevirisi — «durdur» ile kesebilirsiniz.");
        pollBatchJob(jid, { pageRange: true });
      } else if (j.status === "done") {
        await finishPageRangeJob(j);
      } else {
        clearPageJobStorage();
        if (j.status === "cancelled" || j.status === "failed") dismissBatchUi();
      }
    } catch {
      clearPageJobStorage();
    }
  }

  async function startPageRangeJob(mode) {
    if (!openRel) {
      flash("Önce sol listeden dosya açın (PDF, TXT veya DOCX).");
      return;
    }
    if (batchPollTimer) {
      flash("Zaten bir arka plan işi çalışıyor — Durdur ile iptal edebilirsiniz.");
      return;
    }
    const range = pageRangeParams();
    if (mode === "range") {
      if (range.page_from == null) {
        flash("Başlangıç sayfası girin (ör. 1).");
        return;
      }
      const span =
        (range.label_to ?? range.label_from ?? 1) - (range.label_from ?? 1) + 1;
      if (span > 30) {
        flash(
          `${span} sayfa arka planda çevrilecek — uzun sürer. Tek sayfa için aralığı 1–1 yapın; «Bu segmenti çevir» daha net.`,
        );
      }
    }
    if (isPdfExtractGarbage(getSourceText())) {
      flash("Kaynak metin bozuk — önce «Sayfa aralığını yükle» veya OCR deneyin.");
      return;
    }
    const body = global.RuzgarContext?.appendToJsonBody
      ? global.RuzgarContext.appendToJsonBody({
          rel: openRel,
          tgt_lang: String($("tercume-tgt-lang")?.value || "tr"),
          src_lang: String($("tercume-src-lang")?.value || "auto"),
          skip_empty: true,
        })
      : {
          rel: openRel,
          tgt_lang: String($("tercume-tgt-lang")?.value || "tr"),
          src_lang: String($("tercume-src-lang")?.value || "auto"),
          read_level: getReadLevel(),
          system_level: getReadLevel(),
          skip_empty: true,
        };
    if (mode === "range") {
      if (range.page_from == null) {
        flash("Başlangıç sayfası girin (ör. 1).");
        return;
      }
      body.page_from = range.page_from;
      body.page_to = range.page_to;
    }
    translateAbort = false;
    fullTargetDoc = "";
    refreshSegmentPanelView();
    showJobPanel(true);
    renderPageJobLog([], "Kuyruğa alınıyor…");
    showProgress(0, 1, "Arka plan çevirisi başlatılıyor…");
    const res = await fetch(`${api()}/api/tercume/batch-start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
    if (!j.ok || !j.job_id) throw new Error(j.error || "İş başlatılamadı");
    activeBatchJobId = j.job_id;
    setPageJobStorage(j.job_id);
    const modeHint =
      mode === "range"
        ? `sayfa ${range.label_from || "?"}–${range.label_to || "?"}`
        : mode === "full"
          ? "tamamı"
          : "sayfa sayfa";
    flash(`Arka planda çevriliyor (${modeHint}) — pencere kapansa da devam eder.`);
    pollBatchJob(j.job_id, { pageRange: true });
    void refreshBatchJobsList();
  }

  async function startBatchCilt() {
    if (batchPollTimer) {
      flash("Zaten bir arka plan işi çalışıyor (çeviri veya cilt sırası).");
      return;
    }
    const folder = String(workRoot || "ilim-assistant/arsiv").trim();
    showProgress(0, 1, "Sıra hazırlanıyor…");
    const res = await fetch(`${api()}/api/tercume/batch-start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(
        global.RuzgarContext?.appendToJsonBody
          ? global.RuzgarContext.appendToJsonBody({
              folder_rel: folder,
              tgt_lang: String($("tercume-tgt-lang")?.value || "tr"),
              src_lang: String($("tercume-src-lang")?.value || "auto"),
            })
          : {
              folder_rel: folder,
              tgt_lang: String($("tercume-tgt-lang")?.value || "tr"),
              src_lang: String($("tercume-src-lang")?.value || "auto"),
              read_level: getReadLevel(),
              system_level: getReadLevel(),
            },
      ),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || `HTTP ${res.status}`);
    if (!j.ok || !j.job_id) throw new Error(j.error || "İş başlatılamadı");
    activeBatchJobId = j.job_id;
    flash(`Cilt sırası: ${j.total} dosya — arka planda çevriliyor.`);
    pollBatchJob(j.job_id);
  }

  function pollBatchJob(jobId, opts = {}) {
    if (batchPollTimer) clearInterval(batchPollTimer);
    const pageRange = opts.pageRange === true;
    const pollMs = pageRange ? 1200 : 2000;
    batchPollTimer = setInterval(async () => {
      try {
        const res = await fetch(`${api()}/api/tercume/batch-status?job_id=${encodeURIComponent(jobId)}`);
        const j = await res.json().catch(() => ({}));
        if (!res.ok || !j.ok) return;
        const total = Number(j.total) || 0;
        const done = Number(j.done) || 0;
        const label = j.label || j.current_file || j.status || `${done}/${total}`;
        const isPage = pageRange || j.job_type === "page_range";

        if (isPage) {
          showJobPanel(true);
          showProgress(done, total || 1, label);
          if (j.partial_text) setTargetText(String(j.partial_text));
          const outs = Array.isArray(j.outputs) ? j.outputs : [];
          lastJobOutputs = outs;
          let okN = Number(j.ok_count);
          let errN = Number(j.error_count);
          if (!Number.isFinite(okN) || !Number.isFinite(errN)) {
            const c = countJobOutputs(outs);
            okN = c.okN;
            errN = c.errN;
          }
          renderPageJobLog(outs, `${okN} ✓ · ${errN} ✗ · ${done}/${total || "?"}`);
          void refreshReviewQueue(jobId);
          if (j.quality_summary) updateQualityStripFromJob(j);
        } else {
          showProgress(done, total || 1, `Cilt sırası: ${label}`);
        }

        if (j.status === "done") {
          clearInterval(batchPollTimer);
          batchPollTimer = null;
          activeBatchJobId = null;
          if (isPage) {
            await finishPageRangeJob(j);
          } else {
            const okN = Array.isArray(j.outputs) ? j.outputs.filter((o) => o.ok).length : done;
            flash(`Cilt sırası bitti: ${okN}/${total} kaydedildi.`);
            setTimeout(hideProgress, 2500);
            void refreshBatchJobsList();
          }
          return;
        }
        if (j.status === "failed" || j.status === "cancelled") {
          clearInterval(batchPollTimer);
          batchPollTimer = null;
          activeBatchJobId = null;
          if (isPage) {
            clearPageJobStorage();
            if (j.partial_text) setTargetText(String(j.partial_text));
            if (getTercumeUiMode() === "reader" && j.status === "cancelled") {
              dismissBatchUi();
            } else {
              renderPageJobLog(j.outputs || [], String(j.error || j.label || j.status));
            }
            flash(String(j.error || j.label || (j.status === "cancelled" ? "İptal edildi." : "İş başarısız.")));
          } else {
            flash(j.status === "cancelled" ? "Cilt sırası iptal edildi." : String(j.error || "Cilt hatası"));
            setTimeout(hideProgress, 2500);
          }
          void refreshBatchJobsList();
        }
      } catch {
        /* sessiz tekrar */
      }
    }, pollMs);
  }

  function dismissBatchUi() {
    if (batchPollTimer) {
      clearInterval(batchPollTimer);
      batchPollTimer = null;
    }
    activeBatchJobId = null;
    clearPageJobStorage();
    hideProgress();
    showJobPanel(false);
    renderPageJobLog([], "");
    jobStatusLabel = "—";
    updateStatusBar();
    syncBookReaderView();
  }

  async function cancelBatchJob() {
    let jid = activeBatchJobId;
    if (!jid) {
      try {
        jid = localStorage.getItem(LS_PAGE_JOB) || "";
      } catch {
        jid = "";
      }
    }
    if (!jid) return;
    const fd = new FormData();
    fd.append("job_id", jid);
    await fetch(`${api()}/api/tercume/batch-cancel`, { method: "POST", body: fd });
  }

  function showProgress(current, total, label) {
    const wrap = $("tercume-progress-wrap");
    const fill = $("tercume-progress-fill");
    const lab = $("tercume-progress-label");
    const labTxt = label || `${current}/${total}`;
    const pct = total > 0 ? Math.round((current / total) * 100) : 0;
    jobStatusLabel = total > 0 ? `${labTxt} (%${pct})` : labTxt;
    updateStatusBar();
    syncBookReaderView();
    if (getTercumeUiMode() === "reader" && activeDuzenDock !== "status") {
      if (wrap) wrap.hidden = true;
      return;
    }
    if (!wrap) return;
    wrap.hidden = false;
    if (fill) fill.style.width = `${pct}%`;
    if (lab) lab.textContent = labTxt;
  }
  function hideProgress() {
    const wrap = $("tercume-progress-wrap");
    if (wrap) wrap.hidden = true;
    if (!activeBatchJobId && !batchPollTimer) {
      jobStatusLabel = "—";
      updateStatusBar();
    }
  }

  function isLocalApi() {
    try {
      const u = new URL(api() || "http://127.0.0.1:8779");
      return u.hostname === "127.0.0.1" || u.hostname === "localhost";
    } catch {
      return true;
    }
  }

  async function refreshReadiness() {
    const box = $("tercume-readiness-warn");
    const txt = $("tercume-readiness-warn-text");
    if (!box || !txt) return;
    try {
      const res = await fetch(`${api()}/api/tercume/readiness`);
      const j = await res.json().catch(() => ({}));
      if (!j.ok || j.ready) {
        box.hidden = true;
        return;
      }
      const blockers = Array.isArray(j.blockers) ? j.blockers.filter(Boolean) : [];
      const hints = Array.isArray(j.hints) ? j.hints.filter(Boolean) : [];
      const brain = j.brain || {};
      const chain = Array.isArray(brain.chain) ? brain.chain.join(" + ") : "";
      box.hidden = false;
      txt.textContent =
        blockers[0] ||
        hints[0] ||
        (brain.ollama_only
          ? `Ollama-only — ${brain.ollama_model || "ollama serve gerekli"}`
          : chain
            ? `Çeviri beyni: ${chain}`
            : "Hazırlık eksik — «Hazırlık» düğmesine basın.");
    } catch {
      box.hidden = true;
    }
  }

  async function refreshCapabilities(rel = "") {
    const box = $("tercume-capability-strip");
    const txt = $("tercume-capability-text");
    if (!box || !txt) return;
    try {
      const res = await fetch(`${api()}/api/tercume/capabilities`);
      const j = await res.json().catch(() => ({}));
      const caps = j?.capabilities || {};
      if (!j.ok || typeof caps !== "object") {
        box.hidden = true;
        return;
      }
      const hasCal = !!caps.calibre;
      const hasDjvu = !!caps.djvu;
      const hasDocx = !!caps.docx_export;
      const hasOcr = !!caps.ocr;
      const hasPdfPrev = !!caps.pdf_preview;
      pdfPreviewAvailable = hasPdfPrev;
      const ext = String(rel || "").toLowerCase();
      let warn = "";
      if (ext.endsWith(".mobi") || ext.endsWith(".azw") || ext.endsWith(".azw3") || ext.endsWith(".kfx")) {
        if (!hasCal) warn = "Bu dosya için Calibre (ebook-convert) gerekir.";
      } else if (ext.endsWith(".djvu") || ext.endsWith(".djv")) {
        if (!hasDjvu) warn = "Bu dosya için DjVuLibre (djvutxt) gerekir.";
      } else if (ext.endsWith(".pdf") && !hasPdfPrev) {
        warn = "PDF sayfa önizlemesi için: pip install pymupdf (metin çeviri yine çalışır).";
      } else if (
        (ext.endsWith(".png") ||
          ext.endsWith(".jpg") ||
          ext.endsWith(".jpeg") ||
          ext.endsWith(".webp") ||
          ext.endsWith(".tif") ||
          ext.endsWith(".tiff")) &&
        !hasOcr
      ) {
        warn = "Görsel/OCR için Tesseract (Arapça/Osmanlıca paketi) kurulu olmalı.";
      }
      if (warn) {
        txt.textContent = warn;
        box.hidden = false;
      } else {
        txt.textContent = "";
        box.hidden = true;
      }
    } catch {
      box.hidden = true;
    }
  }

  async function refreshOcrWarning() {
    const box = $("tercume-ocr-warn");
    const txt = $("tercume-ocr-warn-text");
    if (!box || !txt) return;
    try {
      const res = await fetch(`${api()}/api/health`);
      const j = await res.json().catch(() => ({}));
      const ocr = j.ocr || {};
      if (ocr.cloud_ready) {
        box.hidden = true;
        return;
      }
      const local = isLocalApi();
      if (!ocr.available) {
        box.hidden = false;
        txt.textContent = local
          ? "Taranmış sayfa, fotoğraf ve taranmış PDF için Tesseract kurulu olmalı. Proje kökündeki Ruzgar_OCR_Kur.bat dosyasını bir kez çalıştırın (Arapça OCR — Osmanlıca metinler için). Metinli PDF'lerde OCR gerekmez. Bulut sürümünde kurulum sunucuda otomatik yapılır; kullanıcı bir şey kurmaz."
          : "Bu sunucuda OCR henüz hazır değil; taranmış kitap ve görseller okunmayabilir. Sunucu yöneticisinden Tesseract (Arapça paketi) kurulumunu isteyin.";
        return;
      }
      const missing = Array.isArray(ocr.missing_langs) ? ocr.missing_langs.filter(Boolean) : [];
      if (missing.length) {
        box.hidden = false;
        txt.textContent = local
          ? `Eksik OCR dil paketi: ${missing.join(", ")}. Ruzgar_OCR_Kur.bat ile tamamlayın (Osmanlıca için Arapça ara paketi yeterli).`
          : `Sunucuda eksik OCR dil paketi: ${missing.join(", ")}. Yöneticiye bildirin.`;
        return;
      }
      box.hidden = true;
    } catch {
      box.hidden = true;
    }
  }

  async function translateChunkApi(text, pageIndex) {
    const fd = new FormData();
    fd.append("text", text);
    fd.append("src_lang", String($("tercume-src-lang")?.value || "auto"));
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "en"));
    const level = getReadLevel();
    fd.append("read_level", level);
    fd.append("system_level", level);
    if (global.RuzgarContext?.appendToFormData) global.RuzgarContext.appendToFormData(fd);
    fd.append("source_file", openRel || "");
    if (pageIndex != null) fd.append("page_index", String(pageIndex));
    const wr = deps.getWorkspaceRoot ? await deps.getWorkspaceRoot() : "";
    if (wr) fd.append("workspace_root", wr);
    const res = await fetch(`${api()}/api/tercume/translate-chunk`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!j.ok) {
      const msg = String(j.hint_tr || j.error || j.detail || `HTTP ${res.status}`).trim();
      const err = new Error(msg);
      if (j.error_code) err.errorCode = j.error_code;
      throw err;
    }
    const quality =
      j.quality && typeof j.quality === "object"
        ? j.quality
        : j.quality_score != null
          ? { score: j.quality_score, ok: true, issues: [] }
          : null;
    return { text: String(j.text || ""), quality };
  }

  async function runPagedTranslation(mode) {
    if (sourceUnreadable) {
      flash("Önce «OCR ile oku» — kaynak metin hazır değil.");
      return;
    }
    const raw = getSourceText();
    if (!raw && !openRel) {
      flash("Kaynak metin veya dosya gerekli.");
      return;
    }
    translateAbort = false;
    let pages = [];
    const range = pageRangeParams();
    if (mode === "range") {
      if (!openRel) {
        flash("Sayfa aralığı için önce dosyayı listeden açın.");
        return;
      }
      if (range.page_from == null) {
        flash("Başlangıç sayfası girin (ör. 1).");
        return;
      }
      const qs = new URLSearchParams({ rel: openRel });
      qs.set("page_from", String(range.page_from));
      if (range.page_to != null) qs.set("page_to", String(range.page_to));
      const res = await fetch(`${api()}/api/tercume/source-pages?${qs.toString()}`);
      const j = await res.json().catch(() => ({}));
      if (!j.ok || !Array.isArray(j.pages)) throw new Error("Sayfa listesi alınamadı");
      pages = j.pages.filter((p) => String(p.text || "").trim() && p.quality !== "empty");
      if (!pages.length) pages = j.pages.filter((p) => String(p.text || "").trim());
      flash(`Sayfa ${range.label_from || "?"}–${range.label_to || "?"}: ${pages.length} parça`);
    } else if (mode === "page" || mode === "full") {
      if (!openRel) {
        flash("Sayfa sayfa için önce dosyayı listeden açın.");
        return;
      }
      const res = await fetch(`${api()}/api/tercume/source-pages?rel=${encodeURIComponent(openRel)}`);
      const j = await res.json().catch(() => ({}));
      if (!j.ok || !Array.isArray(j.pages)) throw new Error("Sayfa listesi alınamadı");
      const qs = j.meta?.quality_summary;
      if (j.meta?.read_hint) flash(j.meta.read_hint);
      else if (qs?.ocr_recommended) {
        flash(
          `${qs.low + qs.empty}/${qs.total} sayfa zayıf — taranmış PDF olabilir; OCR veya metinli PDF deneyin.`,
        );
      }
      pages = j.pages.filter((p) => String(p.text || "").trim() && p.quality !== "empty");
      if (!pages.length && Array.isArray(j.pages)) {
        pages = j.pages.filter((p) => String(p.text || "").trim());
      }
    } else {
      pages = [{ index: 0, text: raw, label: "Tek parça" }];
    }
    if (!pages.length) {
      flash("Çevrilecek metin yok.");
      return;
    }
    setTargetText("");
    const delayMs = mode === "full" ? 400 : 120;
    const outParts = [];
    const isSingle = mode !== "page" && mode !== "full" && mode !== "range";
    for (let i = 0; i < pages.length; i++) {
      if (translateAbort) break;
      const p = pages[i];
      showProgress(i + 1, pages.length, `Çevriliyor: ${p.label || i + 1}${p.quality === "low" ? " (zayıf)" : ""}`);
      const srcText = String(p.text || "");
      lastTranslateContext = {
        sourceText: srcText,
        pageIndex: p.index,
        label: p.label || (isSingle ? "Tek parça" : `Parça ${i + 1}`),
        mode: isSingle ? "single" : mode,
      };
      try {
        const hit = await translateChunkApi(srcText, p.index);
        outParts.push(hit.text);
        setTargetText(outParts.join("\n\n"));
        updateQualityStrip(hit.quality, lastTranslateContext.label);
        if (hit.quality && hit.quality.ok === false) {
          flash(`Düşük kalite skoru (${hit.quality.score}) — metni kontrol edin.`);
        }
      } catch (e) {
        flash(`Çeviri hatası (${p.label || i + 1}): ${e.message || e}`);
        if (mode === "full") break;
      }
      await new Promise((r) => setTimeout(r, delayMs));
    }
    hideProgress();
    syncSavePlaceholder();
    flash(translateAbort ? "Çeviri durduruldu." : "Çeviri tamamlandı.");
    void refreshApprenticeLog();
    void refreshMemoryStatus();
  }

  async function translateViaChat() {
    const raw = getSourceText();
    if (!raw) {
      flash("Kaynak metin boş.");
      return;
    }
    const chunk = raw.length > 28000 ? `${raw.slice(0, 28000)}\n\n… (kısaltıldı)` : raw;
    const srcLabel = $("tercume-src-lang")?.selectedOptions?.[0]?.textContent?.trim() || "Otomatik";
    const tgtLabel = $("tercume-tgt-lang")?.selectedOptions?.[0]?.textContent?.trim() || "İngilizce";
    const msg = `${openRel ? `[Kaynak: ${openRel}]\n` : ""}Ümit abi, tercüme atölyesinden.

Kaynak: ${srcLabel} → Hedef: ${tgtLabel}
Hedef dilin imla ve dil bilgisi kurallarına bire bir uy. Yalnızca çeviri metni.

---

${chunk}`;
    awaitingChatReply = true;
    flash("Sohbet üzerinden çevriliyor…");
    if (deps.sendMessage) await deps.sendMessage(msg, { skipUserBubble: false });
  }

  async function saveTarget() {
    const body = getTargetText();
    if (!body) {
      flash("Hedef metin boş.");
      return;
    }
    let rel = String($("tercume-save-rel")?.value || "").trim() || defaultSaveRel();
    const fmt = String($("tercume-output-format")?.value || "txt");
    if (!rel.toLowerCase().endsWith(`.${fmt}`)) {
      rel = rel.replace(/\.[^.]+$/, "") + `.${fmt}`;
    }
    const fd = new FormData();
    fd.append("rel", rel);
    fd.append("text", body);
    fd.append("avoid_collision", "1");
    fd.append("export_format", fmt);
    if (openRel) fd.append("source_file", openRel);
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    const copy = String($("tercume-copy-rel")?.value || "").trim();
    if (copy) fd.append("copy_rel", copy);
    const res = await fetch(`${api()}/api/tercume/save-target`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "Kayıt başarısız");
    const savedRel = j.rel || rel;
    $("tercume-save-rel").value = savedRel;
    rememberSaveDirFromRel(savedRel);
    syncSavePlaceholder();
    let msg = `Kaydedildi: ${savedRel}`;
    if (j.versioned) {
      msg = String(j.hint_tr || `Dosya vardı — ${savedRel} olarak kaydedildi.`);
    }
    if (j.copy_rel) msg += ` · kopya: ${j.copy_rel}`;
    if (j.copy_versioned) msg += " (kopya sürümlendi)";
    flash(msg);
    void refreshApprenticeLog();
    void refreshSavePrefs();
  }

  async function saveBridgeToHafiza() {
    const src = getSourceText();
    const tr = getTargetText();
    if (!tr || tr.length < 12) {
      flash("Önce çeviri yapın (hedef en az 12 karakter).");
      return;
    }
    const fdPreview = new FormData();
    fdPreview.append("source_text", src);
    fdPreview.append("translated_text", tr);
    fdPreview.append("source_file", openRel || "");
    fdPreview.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    fdPreview.append("src_lang", String($("tercume-src-lang")?.value || "auto"));
    const prevRes = await fetch(`${api()}/api/tercume/bridge-preview`, { method: "POST", body: fdPreview });
    const prev = await prevRes.json().catch(() => ({}));
    if (!prevRes.ok) {
      throw new Error(typeof prev.detail === "string" ? prev.detail : prev.error || "Önizleme başarısız");
    }
    const soru = String(prev.soru || "").slice(0, 160);
    const ok = global.confirm(
      `Ana hafızaya kaydedilsin mi?\n\nAnahtar:\n${soru}\n\n(${prev.target_chars || tr.length} karakter çeviri)`
    );
    if (!ok) {
      flash("Hafıza kaydı iptal.");
      return;
    }
    const fd = new FormData();
    fd.append("source_text", src);
    fd.append("translated_text", tr);
    fd.append("source_file", openRel || "");
    fd.append("tgt_lang", String($("tercume-tgt-lang")?.value || "tr"));
    fd.append("src_lang", String($("tercume-src-lang")?.value || "auto"));
    fd.append("approved", "1");
    fd.append("save_knowledge", "1");
    const res = await fetch(`${api()}/api/tercume/bridge-save`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : j.error || "Kayıt başarısız");
    flash(j.message || "Ana hafızaya kaydedildi.");
    void refreshApprenticeLog();
  }

  async function importUrl() {
    const url = String($("tercume-import-url")?.value || "").trim();
    if (!url) {
      flash("URL girin.");
      return;
    }
    flash("İndirilecek klasörü seçin (Farklı kaydet)…");
    const dir = await pickDownloadFolder();
    if (!dir?.ok) {
      flash("İndirme iptal edildi.");
      return;
    }
    const fd = new FormData();
    fd.append("url", url);
    if (dir.abs) fd.append("target_abs", dir.abs);
    else if (dir.rel) fd.append("target_dir_rel", dir.rel.startsWith("ilim-assistant/") ? dir.rel : `ilim-assistant/arsiv/${dir.rel}`);
    const targetRel = dir.rel?.startsWith("ilim-assistant/")
      ? dir.rel
      : dir.rel
        ? `ilim-assistant/arsiv/${dir.rel}`
        : "";
    const finishImport = async (j) => {
      $("tercume-import-url").value = "";
      const rel = String(j.rel || "");
      if (rel.startsWith("ilim-assistant/")) {
        workRoot = rel.split("/").slice(0, -1).join("/") || workRoot;
        const rootInp = $("tercume-work-root");
        if (rootInp) rootInp.value = workRoot;
        try {
          localStorage.setItem(LS_WORK_ROOT, workRoot);
        } catch (_) {
          /* ignore */
        }
        await refreshTree();
        await openFile(rel);
      } else {
        flash(`İndirildi: ${j.abs || rel} (${Math.round((j.bytes || 0) / 1024 / 1024)} MB)`);
      }
    };
    if (window.RuzgarVirusGuard?.runUrlDownload) {
      await window.RuzgarVirusGuard.runUrlDownload({
        apiBase: api(),
        url,
        targetAbs: dir.abs || "",
        targetDirRel: targetRel,
        speak: window.ruzgarSpeak,
        flash,
        onSuccess: (j) => finishImport(j),
      });
      return;
    }
    flash("İndiriliyor (büyük dosyalar uzun sürebilir)…");
    const res = await fetch(`${api()}/api/tercume/import-url`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : "İndirme hatası");
    await finishImport(j);
  }

  async function importFile(file) {
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file, file.name);
    const res = await fetch(`${api()}/api/tercume/import-file`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Yükleme hatası");
    await refreshTree();
    if (j.rel) await openFile(j.rel);
  }

  async function tryAtolyeFromMessage(text) {
    const raw = String(text || "").trim();
    const low = raw.toLowerCase();
    if (!raw || raw.length > 420) return { handled: false };

    const wantsResume = /\b(devam et|kald(ı|i)ğ(ı|i)m(ı|i)z yerden|resume|şuradan devam)\b/i.test(low);
    const hasUrl = /https?:\/\//i.test(raw);
    const wantsDownload = /\b(indir|download|url)\b/i.test(low);
    const wantsTranslate = /\b(çevir|tercüme et|cevir|translate)\b/i.test(low);
    const wantsSave = /\b(kaydet|yaz)\b/i.test(low) && /\b(dosya|file|çıktı|cikti)\b/i.test(low);
    const wantsCancel = /\b(iptal|durdur|stop|vazgeç|vazgec)\b/i.test(low);
    const wantsUndo = /\b(geri al|undo|son işlemi geri al|son islemi geri al)\b/i.test(low);
    const wantsOpen =
      /\b(aç|ac|açar|göster|goster|yükle|yukle|open|getir)\b/i.test(low) &&
      !wantsTranslate &&
      !hasUrl &&
      !wantsCancel;
    const wantsFullTranslate = /\b(tamamını|tamamini|hepsini|tümünü|tumunu|tüm kitap|full)\b/i.test(low);
    const wantsPageByPage = /\b(sayfa sayfa|page by page)\b/i.test(low);
    const wantsThisPage = /\b(bu sayfa|bu sayfayı|bu sayfayi|şu sayfa|su sayfa|mevcut sayfa)\b/i.test(low);
    const wantsGotoPage =
      /\b(sayfa|page)\b/i.test(low) &&
      /\b(git|geç|gec|gidelim|aç|ac|göster|goster|getir)\b/i.test(low) &&
      !wantsTranslate;
    const intentCount = [wantsResume, wantsDownload, wantsTranslate, wantsSave].filter(Boolean).length;

    if (wantsCancel) {
      lastIntentRawText = raw;
      if (batchPollTimer || activeBatchJobId) {
        await cancelBatchJob();
        dismissBatchUi();
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("Tamam, arka plan çevirisini durdurdum. Ekranı temizledim — tek sayfa için «bu sayfayı çevir» deyin.", ["iş durduruldu"], 0.96),
        };
      }
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply("Şu an iptal edilecek aktif bir iş yok.", ["aktif iş kontrol edildi"], 0.95),
      };
    }

    if (wantsUndo) {
      lastIntentRawText = raw;
      if (lastIntentUndo?.type === "target_replace") {
        setTargetText(String(lastIntentUndo.prevTarget || ""));
        lastIntentUndo = null;
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("Tamam, son hedef metin değişikliğini geri aldım.", ["hedef metin geri yüklendi"], 0.92),
        };
      }
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply("Geri alınacak bir işlem bulamadım.", ["undo geçmişi kontrol edildi"], 0.93),
      };
    }

    if (wantsOpen) {
      lastIntentRawText = raw;
      setTercumeTab("calisma");
      const hint = extractBookQueryFromText(raw) || extractFileHintFromText(raw);
      if (hint.length >= 2) {
        rememberBookSearchQuery(hint);
        const rel = await resolveFileByHint(hint);
        if (rel) {
          await openFile(rel);
          const leaf = rel.split("/").pop() || rel;
          return {
            handled: true,
            instant: true,
            reply: buildIntentReply(
              `Tamam, «${leaf}» önünüze açıldı. Sayfalar arasında gezinip «bu sayfayı çevir» diyebilirsiniz.`,
              ["dosya bulundu", "kitap görünümü açıldı"],
              0.94,
            ),
          };
        }
      }
      toggleDuzenDock("files");
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply(
          hint.length >= 2
            ? `«${hint}» için arşivde net eşleşme bulamadım — «Dosyalar» panelini açtım. Sunucuyu yeniden başlattıysanız tekrar «${hint} aç» deneyin.`
            : "Hangi eseri açalım? «Sahih Bukhari aç» yazmanız yeterli.",
          ["dosya paneli açıldı"],
          0.86,
        ),
      };
    }

    if (wantsGotoPage) {
      lastIntentRawText = raw;
      const range = parsePageRangeFromText(raw);
      if (range && (openRel || getSourceText())) {
        await goToBookPage(range.from);
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply(`Tamam, sayfa ${range.from} açıldı.`, ["sayfa yüklendi"], 0.93),
        };
      }
      if (!openRel) {
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("Önce bir kitap açalım — adını yazmanız yeterli.", ["dosya gerekli"], 0.86),
        };
      }
    }

    if (intentCount >= 2 && !hasUrl && !wantsThisPage) {
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply(
          "Birden fazla adım var gibi — önce hangisini yapalım: açayım mı, çevireyim mi, kaydedeyim mi?",
          ["niyetler ayrıştırıldı"],
          0.61,
        ),
      };
    }

    if (wantsResume) {
      lastIntentRawText = raw;
      await resumeActivePageJobIfAny();
      if (batchPollTimer || activeBatchJobId) {
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("Tamam, aktif çeviri işine yeniden bağlandım.", ["iş bulundu", "izleme başlatıldı"], 0.96),
        };
      }
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply("Devam eden bir iş bulamadım. İsterseniz yeni çeviri başlatayım.", ["aktif iş kontrol edildi"], 0.92),
      };
    }

    if (wantsDownload && hasUrl) {
      lastIntentRawText = raw;
      const url = parseUrlFromText(raw);
      if (!url) return { handled: false };
      const inp = $("tercume-import-url");
      if (inp) inp.value = url;
      await importUrl();
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply(
          "Tamam, bağlantıyı indirip çalışma paneline aldım. Dili söyleyin, çevireyim.",
          ["URL alındı", "dosya indirildi", "çalışma paneli açıldı"],
          0.95,
        ),
      };
    }

    if (wantsDownload && !hasUrl) {
      lastIntentRawText = raw;
      const q = extractSearchQueryFromText(raw);
      if (q.length < 3) {
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("İndirebilmem için bağlantı (URL) verin ya da kitap adını daha net yazın.", ["indir niyeti bulundu"], 0.84),
        };
      }
      const ok = await runEserSearch(q);
      return {
        handled: true,
        instant: true,
        reply: ok
          ? buildIntentReply(
              "Kaynağı aradım, sonuçları «Eser ara» sekmesine getirdim. Uygun sonucu seçip indiriyorum.",
              ["arama sorgusu çıkarıldı", "eser arama çalıştırıldı"],
              0.86,
            )
          : buildIntentReply("Bu isimle sonuç bulamadım; farklı yazımla tekrar deneyelim.", ["arama çalıştırıldı", "sonuç bulunamadı"], 0.83),
      };
    }

    if (wantsTranslate) {
      lastIntentRawText = raw;
      setTercumeTab("calisma");
      const code = guessTargetLangFromText(raw);
      if (code) {
        const sel = $("tercume-tgt-lang");
        if (sel) {
          const has = Array.from(sel.options || []).some((o) => String(o.value) === code);
          if (has) sel.value = code;
        }
      }
      const range = parsePageRangeFromText(raw);
      const modeSel = $("tercume-translate-mode");

      if (openRel || getSourceText()) {
        if (wantsThisPage || (range && range.from === range.to && !wantsFullTranslate && !wantsPageByPage)) {
          const pg = wantsThisPage ? pdfPreviewPage || 1 : range.from;
          if (range || wantsThisPage) await goToBookPage(pg);
          if (modeSel) modeSel.value = "single";
          lastIntentUndo = { type: "target_replace", prevTarget: getTargetText() };
          await translateCurrentSegment();
          return {
            handled: true,
            instant: true,
            reply: buildIntentReply(
              `Tamam, sayfa ${pg} çevrildi — altta görebilirsiniz.`,
              ["sayfa yüklendi", "tek sayfa çeviri tamamlandı"],
              0.94,
            ),
          };
        }
        if (range && range.from !== range.to) {
          const fromEl = $("tercume-page-from");
          const toEl = $("tercume-page-to");
          if (fromEl) fromEl.value = String(range.from);
          if (toEl) toEl.value = String(range.to);
          lastIntentUndo = { type: "target_replace", prevTarget: getTargetText() };
          await startPageRangeJob("range");
          return {
            handled: true,
            instant: true,
            reply: buildIntentReply(
              `Tamam, ${range.from}–${range.to} arası arka planda çevriliyor — ilerlemeyi alttaki çubuktan izleyebilirsiniz.`,
              ["sayfa aralığı", "arka plan işi"],
              0.93,
            ),
          };
        }
        if (wantsPageByPage) {
          lastIntentUndo = { type: "target_replace", prevTarget: getTargetText() };
          await startPageRangeJob("page");
          return {
            handled: true,
            instant: true,
            reply: buildIntentReply(
              "Sayfa sayfa arka planda çeviri başladı. Tek tek okumak isterseniz «bu sayfayı çevir» deyin.",
              ["mod: sayfa sayfa"],
              0.91,
            ),
          };
        }
        if (wantsFullTranslate) {
          lastIntentUndo = { type: "target_replace", prevTarget: getTargetText() };
          await startPageRangeJob("full");
          return {
            handled: true,
            instant: true,
            reply: buildIntentReply(
              "Tam kitap arka planda çevriliyor — bu uzun sürebilir. İsterseniz «durdur» diyebilirsiniz.",
              ["mod: tamamı"],
              0.9,
            ),
          };
        }
        if (modeSel && modeSel.value === "single" && (getSourceSegments().length > 1 || lastAlignedPayload?.segments?.length)) {
          lastIntentUndo = { type: "target_replace", prevTarget: getTargetText() };
          await translateCurrentSegment();
          return {
            handled: true,
            instant: true,
            reply: buildIntentReply("Bu sayfayı çevirdim — altta okuyabilirsiniz.", ["segment çeviri"], 0.92),
          };
        }
        lastIntentUndo = { type: "target_replace", prevTarget: getTargetText() };
        await runPagedTranslation("single");
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("Mevcut metni çevirdim.", ["tek parça çeviri"], 0.91),
        };
      }
      const q = extractSearchQueryFromText(raw);
      if (q.length >= 3 && /\b(kitap|eser|mektubat|tefsir|risale|hadis)\b/i.test(low)) {
        const ok = await runEserSearch(q);
        return {
          handled: true,
          instant: true,
          reply: ok
            ? buildIntentReply(
                "Önce kitabı aradım. Sonuçtan dosyayı açınca çeviriyi otomatik başlatabilirim.",
                ["kitap adı çıkarıldı", "eser arama yapıldı"],
                0.82,
              )
            : buildIntentReply("Çevirecek dosya bulamadım. URL veya dosya verin, hemen başlatayım.", ["arama yapıldı", "dosya bulunamadı"], 0.8),
        };
      }
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply("Çevirmem için önce dosya açın veya kaynak metin yapıştırın.", ["çeviri niyeti bulundu", "girdi eksik"], 0.86),
      };
    }

    if (wantsSave) {
      lastIntentRawText = raw;
      if (!getTargetText()) {
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply("Kaydedecek hedef metin yok. Önce çeviri yapalım, sonra kaydedeyim.", ["kaydet niyeti bulundu", "hedef metin kontrolü"], 0.95),
        };
      }
      const rel = parseSaveRelFromText(raw);
      if (rel) {
        const saveInp = $("tercume-save-rel");
        if (saveInp) saveInp.value = rel;
        const ext = rel.toLowerCase().match(/\.(txt|md|html|docx)$/)?.[1] || "";
        if (ext) {
          const fmt = $("tercume-output-format");
          if (fmt) fmt.value = ext;
        }
      } else if (!String($("tercume-save-rel")?.value || "").trim()) {
        return {
          handled: true,
          instant: true,
          reply: buildIntentReply(
            "Nereye kaydedeyim? Örn: ilim-assistant/arsiv/tercume-output/kitap_tr.md",
            ["kaydet yolu isteniyor"],
            0.9,
          ),
        };
      }
      await saveTarget();
      return {
        handled: true,
        instant: true,
        reply: buildIntentReply("Tamam, çıktıyı dosyaya kaydettim.", ["kayıt yolu belirlendi", "dosya yazıldı"], 0.95),
      };
    }

    const local = await buildTercumeLocalReply(raw, low);
    if (local?.reply) {
      lastIntentRawText = raw;
      return { handled: true, instant: true, reply: local.reply };
    }

    return { handled: false };
  }

  async function runActionCardCommand(cmd) {
    const c = String(cmd || "").trim().toLowerCase();
    if (!c) return { ok: false, message: "Komut boş." };
    if (c === "undo") {
      const hit = await tryAtolyeFromMessage("geri al");
      return { ok: !!hit?.handled, message: hit?.reply || "Geri alma çalıştırıldı." };
    }
    if (c === "repeat") {
      if (!String(lastIntentRawText || "").trim()) {
        return { ok: false, message: "Tekrarlanacak son işlem yok." };
      }
      const hit = await tryAtolyeFromMessage(lastIntentRawText);
      return { ok: !!hit?.handled, message: hit?.reply || "Son işlem tekrarlandı." };
    }
    if (c === "details") {
      const open = String(openRel || "(dosya yok)");
      const job = String(activeBatchJobId || "");
      const undo = lastIntentUndo?.type ? "var" : "yok";
      const last = String(lastIntentRawText || "").trim() || "(yok)";
      return {
        ok: true,
        message:
          `Detay:\n` +
          `- Açık dosya: ${open}\n` +
          `- Aktif iş: ${job || "yok"}\n` +
          `- Undo tamponu: ${undo}\n` +
          `- Son niyet cümlesi: ${last}`,
      };
    }
    return { ok: false, message: `Bilinmeyen komut: ${cmd}` };
  }

  async function refreshApprenticeLog() {
    const list = $("tercume-apprentice-list");
    if (!list) return;
    try {
      const wr = deps.getWorkspaceRoot ? await deps.getWorkspaceRoot() : "";
      const qs = wr ? `?workspace_root=${encodeURIComponent(wr)}&limit=8` : "?limit=8";
      const res = await fetch(`${api()}/api/tercume/apprentice-log${qs}`);
      const j = await res.json().catch(() => ({}));
      const items = Array.isArray(j.items) ? j.items : [];
      list.innerHTML = items
        .map((it) => {
          const note = esc(String(it.note || it.lesson || "").slice(0, 120));
          const f = esc(String(it.source_file || "").split("/").pop() || "");
          return `<li>${note}${f ? ` · ${f}` : ""}</li>`;
        })
        .join("");
      if (!items.length) list.innerHTML = "<li>Henüz kayıt yok — çeviri/kaydet sonrası programlama motoru okuyabilir.</li>";
    } catch {
      list.innerHTML = "<li>Günlük yüklenemedi.</li>";
    }
  }

  async function pickWorkFolder() {
    if (global.ruzgarApi?.pickWorkspaceDirectory) {
      const r = await global.ruzgarApi.pickWorkspaceDirectory();
      if (r?.ok && r.rel) {
        workRoot = r.rel;
        try {
          localStorage.setItem(LS_WORK_ROOT, workRoot);
        } catch (_) {
          /* ignore */
        }
        $("tercume-work-root").value = workRoot;
        fileFilterQuery = "";
        const filterInp = $("tercume-file-filter");
        if (filterInp) filterInp.value = "";
        renderPathCrumb();
        await refreshTree();
        flash(`Çalışma klasörü: ${workRoot}`);
      }
      return;
    }
    await applyWorkRootFromInput();
  }

  function wireZoom() {
    const page = $("page-tercume");
    if (!page || page.dataset.tercumeZoomWired === "1") return;
    page.dataset.tercumeZoomWired = "1";
    page.addEventListener(
      "wheel",
      (ev) => {
        if (!ev.ctrlKey) return;
        ev.preventDefault();
        const cur = parseFloat(getComputedStyle(page).getPropertyValue("--tercume-font-size")) || 14;
        const next = Math.min(22, Math.max(10, cur + (ev.deltaY < 0 ? 1 : -1)));
        page.style.setProperty("--tercume-font-size", `${next}px`);
      },
      { passive: false },
    );
  }

  function normalizeTercumeTab(tab) {
    const t = String(tab || "calisma").trim() || "calisma";
    if (t === "sohbet") return "calisma";
    return t;
  }

  function setTercumeTab(tab) {
    const t = normalizeTercumeTab(tab);
    document.body.dataset.tercumeTab = t;
    document.querySelectorAll(".tercume-view-tab").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.tercumeTab === t);
    });
    const wb = $("tercume-workbench");
    const pasifSlot = $("tercume-pasif-slot");
    if (pasifSlot) pasifSlot.hidden = t !== "pasif";
    if (wb) {
      wb.hidden = t === "pasif";
      wb.classList.remove("tercume-workbench--ara", "tercume-workbench--calisma", "tercume-workbench--okuma");
      if (t === "ara") wb.classList.add("tercume-workbench--ara");
      else if (t === "okuma") wb.classList.add("tercume-workbench--okuma");
      else if (t === "calisma") wb.classList.add("tercume-workbench--calisma");
    }
    const ara = $("tercume-ara-panel");
    const okuma = $("tercume-okuma-panel");
    if (ara) ara.hidden = t !== "ara";
    if (okuma) okuma.hidden = t !== "okuma";
    if (t === "ara") {
      setTimeout(() => {
        const inp = $("tercume-eser-input");
        inp?.focus();
        inp?.select?.();
      }, 60);
    }
    if (t === "okuma") {
      if (global.okumaAtolyeRefreshTree) void global.okumaAtolyeRefreshTree();
      else if (deps.loadIlimFileList) void deps.loadIlimFileList();
    }
    if (t === "calisma" || t === "ara") {
      void refreshTree();
    }
    if (t === "calisma") {
      void refreshPreflightChip();
      renderRecentFiles();
      renderPathCrumb();
      updateSidebarActiveFile();
      applyEditorDirection();
      updateStatusBar();
      updateSegmentStrip();
    }
    if (global.RuzgarSplit?.onTercumeTabChange) {
      requestAnimationFrame(() => {
        global.RuzgarSplit.onTercumeTabChange();
        applyReaderWorkbenchGrid();
      });
    } else {
      applyReaderWorkbenchGrid();
    }
  }

  function syncTercumeLayout(isTercume) {
    const tabs = $("tercume-view-tabs");
    if (tabs) tabs.hidden = !isTercume;
    if (isTercume) {
      document.body.dataset.motor = "tercume";
      setTercumeUiMode(getTercumeUiMode());
      const cur = normalizeTercumeTab(document.body.dataset.tercumeTab || "calisma");
      setTercumeTab(cur);
      void refreshOcrWarning();
      void refreshReadiness();
      void refreshCapabilities(openRel || "");
      if (deps.showTercumeChatWelcome) deps.showTercumeChatWelcome();
    } else {
      closeDuzenDock();
      delete document.body.dataset.motor;
      delete document.body.dataset.tercumeTab;
      delete document.body.dataset.tercumeUi;
    }
  }

  function wireTercumeViewTabs() {
    const bar = $("tercume-view-tabs");
    if (!bar || bar.dataset.wired === "1") return;
    bar.dataset.wired = "1";
    bar.querySelectorAll(".tercume-view-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        const raw = btn.dataset.tercumeTab || "calisma";
        setTercumeTab(raw);
        const labels = { pasif: "Yakında (pasif)", calisma: "Çalışma", ara: "Eser ara", okuma: "Okuma" };
        flash(`Görünüm: ${labels[raw] || raw}`);
      });
    });
  }

  function onTercumeKeydown(ev) {
    if (document.body.dataset.motor !== "tercume") return;
    if (normalizeTercumeTab(document.body.dataset.tercumeTab || "calisma") !== "calisma") return;
    const ae = document.activeElement;
    const inField =
      ae &&
      (ae.tagName === "INPUT" || ae.tagName === "TEXTAREA" || ae.tagName === "SELECT") &&
      !ae.classList?.contains("tercume-doc-editor");
    if (inField && !(ev.ctrlKey && ev.key === "Enter") && !(ev.ctrlKey && ev.key === "s")) return;
    if (ev.ctrlKey && ev.key === "Enter") {
      ev.preventDefault();
      const mode = String($("tercume-translate-mode")?.value || "single");
      if (mode === "single" && (getSourceSegments().length > 1 || lastAlignedPayload?.segments?.length)) {
        void translateCurrentSegment().catch((e) => flash(e.message || String(e)));
      } else {
        $("btn-tercume-translate")?.click();
      }
      return;
    }
    if (ev.ctrlKey && (ev.key === "s" || ev.key === "S")) {
      ev.preventDefault();
      void saveTarget().catch((e) => flash(e.message || String(e)));
      return;
    }
    if (ev.ctrlKey && (ev.key === "o" || ev.key === "O")) {
      ev.preventDefault();
      triggerOpenFileDialog();
      return;
    }
    if (ev.altKey && ev.key === "ArrowDown") {
      ev.preventDefault();
      focusSegment(currentSegmentIndex + 1, { openTable: reviewMode });
      return;
    }
    if (ev.altKey && ev.key === "ArrowUp") {
      ev.preventDefault();
      focusSegment(currentSegmentIndex - 1, { openTable: reviewMode });
    }
  }

  function wireTercumeProfessional() {
    const page = $("page-tercume");
    if (!page || page.dataset.tercumeProWired === "1") return;
    page.dataset.tercumeProWired = "1";

    $("btn-tercume-wb-edit")?.addEventListener("click", () => setWorkbenchReviewMode(false));
    $("btn-tercume-wb-review")?.addEventListener("click", () => {
      setWorkbenchReviewMode(true);
      if (getSourceText() || getTargetText()) {
        void runAlignedDiff().catch((e) => flash(e.message || String(e)));
      }
    });
    $("btn-tercume-seg-prev")?.addEventListener("click", () =>
      focusSegment(currentSegmentIndex - 1, { openTable: reviewMode }),
    );
    $("btn-tercume-seg-next")?.addEventListener("click", () =>
      focusSegment(currentSegmentIndex + 1, { openTable: reviewMode }),
    );
    $("btn-tercume-seg-translate")?.addEventListener("click", () => {
      void translateCurrentSegment().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-seg-to-aligned")?.addEventListener("click", () => {
      focusSegment(currentSegmentIndex, { openTable: true });
      const fold = $("tercume-aligned-fold");
      if (fold) {
        fold.hidden = false;
        fold.open = true;
      }
    });
    $("btn-tercume-pdf-apply-range")?.addEventListener("click", () => {
      void loadPdfPageRange().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-read-quality-reload")?.addEventListener("click", () => {
      void loadPdfPageRange().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-read-quality-ocr")?.addEventListener("click", () => {
      void runSimpleOcr();
    });
    $("btn-tercume-simple-ocr")?.addEventListener("click", () => {
      void runSimpleOcr();
    });
    $("btn-tercume-simple-reload")?.addEventListener("click", () => {
      void loadPdfPageRange().catch((e) => flash(e.message || String(e)));
    });
    getSourceEl()?.addEventListener("blur", () => commitVisiblePanelsToFullDoc());
    getTargetEl()?.addEventListener("blur", () => commitVisiblePanelsToFullDoc());
    $("btn-tercume-pdf-open-folder")?.addEventListener("click", () => {
      if (openRel && global.ruzgarApi?.openWorkspaceRel) {
        const dir = openRel.replace(/[/\\][^/\\]+$/, "");
        void global.ruzgarApi.openWorkspaceRel(dir || workRoot);
      }
    });
    $("btn-tercume-pdf-prev-page")?.addEventListener("click", () => {
      void loadPdfPreviewPage(Math.max(1, pdfPreviewPage - 1));
    });
    $("btn-tercume-pdf-next-page")?.addEventListener("click", () => {
      const max = Number(pdfMeta?.pages_total) || pdfPreviewPage + 1;
      void loadPdfPreviewPage(Math.min(max, pdfPreviewPage + 1));
    });
    $("btn-tercume-seg-apply-both")?.addEventListener("click", () => applySegmentEditorsToPanels());
    $("btn-tercume-seg-translate-inline")?.addEventListener("click", () => {
      void translateCurrentSegment().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-segment-src")?.addEventListener("blur", () => applySegmentEditorsToPanels(true));
    $("tercume-segment-tgt")?.addEventListener("blur", () => applySegmentEditorsToPanels(true));
    $("tercume-status-file")?.addEventListener("click", () => {
      if (getTercumeUiMode() === "reader") {
        toggleDuzenDock("files");
        return;
      }
      $("tercume-file-list")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    $("tercume-status-page")?.addEventListener("click", () => {
      $("tercume-page-from")?.focus();
      flash("Sayfa aralığı üst şeritte (Sayfa ve çıktı).");
    });
    $("tercume-status-mode")?.addEventListener("click", () => {
      $("tercume-translate-mode")?.focus();
    });
    $("tercume-status-quality")?.addEventListener("click", () => {
      const strip = $("tercume-quality-strip");
      if (strip) strip.hidden = false;
    });
    $("tercume-status-job")?.addEventListener("click", () => {
      showJobPanel(true);
      $("tercume-job-panel")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    $("tercume-status-tm")?.addEventListener("click", () => {
      const fold = $("tercume-user-glossary-fold");
      if (fold) {
        fold.open = true;
        void refreshUserGlossary();
      }
    });
    $("tercume-status-preflight")?.addEventListener("click", () => {
      void runPreflight().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-page-from")?.addEventListener("change", () => {
      updatePdfHint();
      updateStatusBar();
    });
    $("tercume-page-to")?.addEventListener("change", () => {
      updatePdfHint();
      updateStatusBar();
    });
    $("tercume-src-lang")?.addEventListener("change", () => applyEditorDirection());
    $("tercume-tgt-lang")?.addEventListener("change", () => applyEditorDirection());
    getSourceEl()?.addEventListener("focus", () => stripTmMarks(getSourceEl()));
    getSourceEl()?.addEventListener("blur", () => scheduleTmHighlight());
    document.addEventListener("keydown", onTercumeKeydown);
    renderRecentFiles();
    void refreshPreflightChip();
    void refreshPdfPreviewCapability();
    applyEditorDirection();
    updateStatusBar();
    wireReaderUi();
  }

  function wireReaderUi() {
    const page = $("page-tercume");
    if (!page || page.dataset.readerUiWired === "1") return;
    page.dataset.readerUiWired = "1";

    document.querySelectorAll(".tercume-duzen-btn").forEach((btn) => {
      btn.addEventListener("click", () => toggleDuzenDock(btn.dataset.tercumeDock || ""));
    });
    $("tercume-duzen-backdrop")?.addEventListener("click", () => closeDuzenDock());
    document.addEventListener(
      "keydown",
      (ev) => {
        if (ev.key !== "Escape" || !activeDuzenDock) return;
        closeDuzenDock();
      },
      true,
    );

    $("btn-tercume-book-prev")?.addEventListener("click", () => {
      void goToBookPage(Math.max(1, pdfPreviewPage - 1));
    });
    $("btn-tercume-book-next")?.addEventListener("click", () => {
      const max = Number(pdfMeta?.pages_total) || pdfPreviewPage + 1;
      void goToBookPage(Math.min(max, pdfPreviewPage + 1));
    });
    $("btn-tercume-book-translate-page")?.addEventListener("click", () => {
      const modeSel = $("tercume-translate-mode");
      if (modeSel) modeSel.value = "single";
      void translateCurrentSegment().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-book-page-input")?.addEventListener("change", (ev) => {
      const n = Number(ev.target?.value);
      if (Number.isFinite(n) && n > 0) void goToBookPage(n);
    });
    $("tercume-book-page-input")?.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        const n = Number(ev.target?.value);
        if (Number.isFinite(n) && n > 0) void goToBookPage(n);
      }
    });
  }

  function wireAll() {
    const page = $("page-tercume");
    if (!page) {
      if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", () => wireAll(), { once: true });
      }
      return;
    }
    if (page.dataset.tercumeV2Wired === "1") {
      wireTercumeProfessional();
      wireReadLevelSelect();
      return;
    }
    page.dataset.tercumeV2Wired = "1";
    wireTercumeViewTabs();
    wireTercumeProfessional();
    wireReadLevelSelect();

    try {
      workRoot = localStorage.getItem(LS_WORK_ROOT) || workRoot;
    } catch (_) {
      /* ignore */
    }
    const rootInp = $("tercume-work-root");
    if (rootInp) rootInp.value = workRoot;
    renderPathCrumb();
    updateSidebarActiveFile();
    wireFilePanelDnD();

    $("tercume-file-list")?.addEventListener("click", (ev) => void onTreeClick(ev));
    $("btn-tercume-refresh")?.addEventListener("click", () => void refreshTree());
    $("btn-tercume-pick-folder")?.addEventListener("click", () => void pickWorkFolder());
    $("btn-tercume-path-apply")?.addEventListener("click", () => void applyWorkRootFromInput());
    $("tercume-work-root")?.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        void applyWorkRootFromInput();
      }
    });
    $("btn-tercume-open-file")?.addEventListener("click", () => triggerOpenFileDialog());
    $("btn-tercume-io-open-file")?.addEventListener("click", () => triggerOpenFileDialog());
    $("tercume-file-filter")?.addEventListener("input", () => scheduleFileSearch());
    $("tercume-file-filter")?.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        ev.preventDefault();
        fileFilterQuery = "";
        ev.target.value = "";
        void refreshTree();
      }
    });
    $("btn-tercume-open-archive")?.addEventListener("click", () => {
      if (global.ruzgarApi?.openWorkspaceRel) void global.ruzgarApi.openWorkspaceRel(workRoot);
    });
    $("btn-arsiv-download-refresh")?.addEventListener("click", () =>
      void refreshArsivCatalog().catch((e) => flash(e.message)),
    );
    $("btn-arsiv-download-next")?.addEventListener("click", () =>
      void downloadArsivNext().catch((e) => flash(e.message)),
    );
    $("btn-tercume-eser-ara")?.addEventListener("click", () => {
      void runEserSearch(String($("tercume-eser-input")?.value || ""));
    });
    $("btn-tercume-eser-rapor")?.addEventListener("click", () => {
      void runAnalystReport().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-super")?.addEventListener("click", () => {
      void runSuperAnalyst().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-scholar-open")?.addEventListener("click", () => {
      openGoogleScholar(String($("tercume-eser-input")?.value || ""));
    });
    $("tercume-eser-input")?.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        void runEserSearch(String($("tercume-eser-input")?.value || ""));
      }
    });
    $("tercume-arsiv-download-fold")?.addEventListener("toggle", (ev) => {
      const list = $("tercume-arsiv-download-list");
      if (ev.target.open && list && !list.dataset.loaded) {
        list.dataset.loaded = "1";
        void refreshArsivCatalog();
      }
    });
    $("btn-tercume-translate")?.addEventListener("click", () => {
      const mode = String($("tercume-translate-mode")?.value || "single");
      if (mode === "chat") void translateViaChat();
      else if (mode === "page" || mode === "full" || mode === "range")
        void startPageRangeJob(mode).catch((e) => {
          hideProgress();
          showJobPanel(false);
          flash(e.message || "Arka plan çevirisi başlatılamadı");
        });
      else void runPagedTranslation("single");
    });
    $("btn-tercume-stop")?.addEventListener("click", () => {
      translateAbort = true;
      void cancelBatchJob();
      flash("Durdurma istendi…");
    });
    $("btn-tercume-save-target")?.addEventListener("click", () => void saveTarget().catch((e) => flash(e.message)));
    $("btn-tercume-bridge-save")?.addEventListener("click", () =>
      void saveBridgeToHafiza().catch((e) => flash(e.message || String(e)))
    );
    $("btn-tercume-import-url")?.addEventListener("click", () => void importUrl().catch((e) => flash(e.message)));
    $("tercume-import-file")?.addEventListener("change", (ev) => {
      const f = ev.target.files?.[0];
      void importFile(f).catch((e) => flash(e.message));
      ev.target.value = "";
    });
    $("btn-tercume-batch-cilt")?.addEventListener("click", () => {
      void startBatchCilt().catch((e) => {
        hideProgress();
        flash(e.message || "Cilt sırası hatası");
      });
    });
    $("btn-tercume-preflight")?.addEventListener("click", () => {
      void runPreflight().catch((e) => flash(e.message || "Hazırlık kontrolü hatası"));
    });
    $("btn-tercume-okuma-to-source")?.addEventListener("click", () => {
      const t = String($("ilim-file-content")?.value || "").trim();
      if (!t) {
        flash("Önce Okuma sekmesinde bir dosya açın.");
        return;
      }
      setSourceText(t);
      setTercumeTab("calisma");
      flash("Metin kaynak panele aktarıldı — Çevir deyin.");
    });
    $("btn-tercume-read-analyze")?.addEventListener("click", () => {
      void startReadAnalyze().catch((e) => {
        hideProgress();
        flash(e.message || "Okuma analizi hatası");
      });
    });
    $("btn-tercume-ocr")?.addEventListener("click", () => {
      void runSimpleOcr();
    });
    $("tercume-glossary-import-file")?.addEventListener("change", (ev) => {
      const f = ev.target?.files?.[0];
      if (f) void importGlossaryFile(f).catch((e) => flash(e.message || String(e)));
      ev.target.value = "";
    });
    $("btn-tercume-tmx-export")?.addEventListener("click", () => {
      void exportTmxFile().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-tmx-import-file")?.addEventListener("change", (ev) => {
      const f = ev.target?.files?.[0];
      if (f) void importTmxFile(f).catch((e) => flash(e.message || String(e)));
      ev.target.value = "";
    });
    $("btn-tercume-aligned-diff")?.addEventListener("click", () => {
      void runAlignedDiff().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-academic-check")?.addEventListener("click", () => {
      void runAcademicCheck().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-aligned-only-issues")?.addEventListener("change", () => {
      if (lastAlignedPayload) renderAlignedDiff(lastAlignedPayload);
    });
    $("btn-tercume-aligned-retry-unapproved")?.addEventListener("click", () => {
      void retryUnapprovedAlignedRows().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-aligned-export-approved")?.addEventListener("click", () => {
      void exportApprovedAlignedToTmx().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-term-add")?.addEventListener("click", () => {
      void addUserTerm().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-user-glossary-fold")?.addEventListener("toggle", (ev) => {
      if (ev.target.open) void refreshUserGlossary();
    });
    $("btn-tercume-clear")?.addEventListener("click", () => {
      const prevRel = openRel;
      fullSourceDoc = "";
      fullTargetDoc = "";
      sourcePageMeta = [];
      sourceUnreadable = false;
      showReadQualityWarn("");
      setSourceText("");
      setTargetText("");
      openRel = null;
      pdfMeta = null;
      lastAlignedPayload = null;
      currentSegmentIndex = 0;
      awaitingChatReply = false;
      hideEbookMeta();
      hideQualityStrip();
      updatePdfHint();
      updateSegmentStrip();
      const acad = $("tercume-academic-fold");
      if (acad) acad.hidden = true;
      const aligned = $("tercume-aligned-fold");
      if (aligned) aligned.hidden = true;
      setPdfPreviewPanelVisible(false);
      updateActiveLabel();
      syncSavePlaceholder();
      const fd = new FormData();
      if (prevRel) fd.append("source_file", prevRel);
      fetch(`${api()}/api/tercume/memory-clear`, { method: "POST", body: fd }).catch(() => {});
      void refreshMemoryStatus();
    });
    $("btn-tercume-retry-quality")?.addEventListener("click", () => {
      void retryLastChunkQuality().catch((e) => flash(e.message || String(e)));
    });
    $("btn-tercume-last-to-target")?.addEventListener("click", () => {
      const t = String(deps.lastAssistantReply?.() || "").trim();
      if (!t) {
        flash("Sohbette yanıt yok — önce Sohbet sekmesinde bir şey sorun veya Kaynak paneline yapıştırın.");
        getSourceEl()?.focus();
        return;
      }
      setTargetText(t);
      flash("Son sohbet yanıtı hedef panele yazıldı.");
    });
    $("btn-tercume-active-file")?.addEventListener("click", () => {
      if (openRel) {
        flash(`Açık dosya: ${openRel}`);
        getSourceEl()?.focus();
        return;
      }
      setTercumeTab("calisma");
      flash("Sol listeden bir dosyaya tıklayın — veya Kaynak paneline metin yapıştırın.");
      $("tercume-file-list")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    $("tercume-output-format")?.addEventListener("change", () => syncSavePlaceholder());

    getSourceEl()?.addEventListener("input", () => updateStats());
    wireZoom();
    syncSavePlaceholder();
    void refreshTree();
    void refreshApprenticeLog();
    void refreshOcrWarning();
    void refreshReadiness();
    void refreshCapabilities(openRel || "");
    void resumeActivePageJobIfAny();
    void refreshBatchJobsList();
    void refreshMemoryStatus();
    void refreshSavePrefs();
    void refreshUserGlossary();
    void loadTmTermsForHighlight();
    $("tercume-tgt-lang")?.addEventListener("change", () => {
      syncSavePlaceholder();
      void refreshMemoryStatus();
      applyEditorDirection();
    });
  }

  global.RuzgarTercumeAtolye = {
    init(d) {
      deps = d || {};
      wireAll();
      renderEserSearchEmpty();
      if (deps.getCurrentMode?.() === "tercume") syncTercumeLayout(true);
    },
    setTercumeTab,
    syncTercumeLayout,
    load() {
      updateActiveLabel();
      updateStats();
      syncSavePlaceholder();
      renderRecentFiles();
      applyEditorDirection();
      updateSegmentStrip();
      updateStatusBar();
      void refreshPreflightChip();
      void refreshTree();
      void refreshApprenticeLog();
      const fold = $("tercume-arsiv-download-fold");
      if (fold?.open) void refreshArsivCatalog();
      void refreshCapabilities(openRel || "");
      void resumeActivePageJobIfAny();
      void refreshBatchJobsList();
      void refreshMemoryStatus();
      void refreshSavePrefs();
    },
    onAssistantReply(text) {
      if (!awaitingChatReply) return;
      awaitingChatReply = false;
      if (text?.trim()) {
        setTargetText(text);
        flash("Sohbet çevirisi hedef panele yazıldı.");
      }
    },
    importText(text, rel) {
      if (rel) {
        openRel = rel;
        suggestLangFromPath(rel);
        pushRecentFile(rel);
      }
      setSourceText(text);
      updateActiveLabel();
      syncSavePlaceholder();
      if (deps.switchMode) deps.switchMode("tercume");
    },
    getOpenRel: () => openRel,
    runSearch: (text) => runEserSearch(text).then((ok) => ok),
    tryAtolyeFromMessage,
    runActionCardCommand,
    setTercumeUiMode,
    getTercumeUiMode,
    toggleDuzenDock,
    openDuzenDock,
    closeDuzenDock,
    goToBookPage,
    openFileByHint: async (hint) => {
      const rel = await resolveFileByHint(hint);
      if (!rel) return { ok: false, message: "Dosya bulunamadı." };
      await openFile(rel);
      return { ok: true, rel, message: rel.split("/").pop() || rel };
    },
    isSearchIntent(text) {
      const t = String(text || "").trim().toLowerCase();
      if (!t || t.length > 280) return false;
      if (/^https?:\/\//i.test(t)) return false;
      if (/^(ara|arat|bul)\b/.test(t)) return true;
      if (/\b(eser|kitap|yazar).{0,40}\bara\b/.test(t)) return true;
      if (/\bara\b.{0,30}\b(eser|kitap|mektubat|kur'an|kuran|hadis|tefsir)\b/.test(t)) return true;
      if (/\b(eserlerini|kitaplarını)\s+ara\b/.test(t)) return true;
      return false;
    },
  };
})(window);
