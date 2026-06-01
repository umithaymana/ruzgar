/**
 * Tercüme Atölyesi v2 — yalnızca #page-tercume (diğer motorlara dokunmaz).
 */
(function initTercumeAtolyeModule(global) {
  const LS_WORK_ROOT = "ruzgar_tercume_work_root";
  const LS_PAGE_JOB = "ruzgar_tercume_page_job_id";
  const LS_LAST_SAVE_DIR = "ruzgar_tercume_last_save_dir";
  const QUALITY_PASS = 55;
  const QUALITY_WARN = 75;

  let lastTranslateContext = null;
  const EBOOK_EXTS = [".epub", ".fb2", ".mobi", ".azw", ".azw3", ".kfx", ".djvu", ".djv", ".rtf"];
  const IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"];

  let deps = {};
  let openRel = null;
  let workRoot = "ilim-assistant/arsiv";
  let awaitingChatReply = false;
  let translateAbort = false;
  let lastDownloadDir = { abs: "", rel: "" };
  let lastSaveDir = "ilim-assistant/arsiv/tercume-output";

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
  function getSourceText() {
    const el = getSourceEl();
    return el ? String(el.innerText || "").trim() : "";
  }
  function setSourceText(t) {
    const el = getSourceEl();
    if (el) el.innerText = t || "";
    updateStats();
  }
  function getTargetText() {
    const el = getTargetEl();
    return el ? String(el.innerText || "").trim() : "";
  }
  function setTargetText(t) {
    const el = getTargetEl();
    if (el) el.innerText = t || "";
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
      el.textContent = `Kaynak: ${openRel}`;
      el.classList.add("has-file");
      el.title = openRel;
    } else {
      el.textContent = "Kaynak: sol listeden dosya seçin";
      el.classList.remove("has-file");
      el.title = "Sol listeden dosya seçin (tıklayınca listeye gider)";
    }
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
    list.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
    try {
      const items = deps.workspaceListDir
        ? await deps.workspaceListDir(workRoot)
        : [];
      list.innerHTML = "";
      for (const it of items) {
        if (deps.createCodeTreeBranch) {
          list.appendChild(deps.createCodeTreeBranch(it, 0));
        }
      }
      if (!items.length) {
        list.innerHTML = `<div class="code-file-placeholder">Klasör boş: <code>${esc(workRoot)}</code></div>`;
      }
    } catch (e) {
      list.innerHTML = `<div class="code-file-placeholder">Liste hatası: ${esc(e.message || e)}</div>`;
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
    setSourceText("Dosya yükleniyor…");
    updateActiveLabel();
    try {
      const text = await readFileForTercume(rel);
      openRel = rel;
      setSourceText(text);
      updateActiveLabel();
      syncSavePlaceholder();
      flash(`Kaynak panele yüklendi: ${rel.split("/").pop()}`);
      getSourceEl()?.focus();
      void refreshApprenticeLog();
      void refreshMemoryStatus();
    } catch (e) {
      openRel = rel;
      const msg = String(e.message || e);
      setSourceText(`(Dosya: ${rel}\n\nÖnizleme alınamadı: ${msg}\n\nBüyük PDF için OCR veya sayfa sayfa modunu deneyin.)`);
      updateActiveLabel();
      flash("Tam metin yüklenemedi; dosya yolu kayıtlı.");
      void refreshMemoryStatus();
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

  function renderAlignedDiff(payload) {
    const fold = $("tercume-aligned-fold");
    const tbody = $("tercume-aligned-tbody");
    const statsEl = $("tercume-aligned-stats");
    if (!fold || !tbody) return;
    const rows = Array.isArray(payload?.segments) ? payload.segments : [];
    if (!rows.length) {
      fold.hidden = true;
      tbody.innerHTML = "";
      return;
    }
    fold.hidden = false;
    const st = payload.stats || {};
    const warn = (st.missing_target || 0) + (st.extra_target || 0);
    if (statsEl) {
      statsEl.textContent = payload.aligned
        ? `${rows.length} segment · hizalı`
        : `${rows.length} segment · ${warn} uyarı`;
    }
    tbody.innerHTML = "";
    for (const r of rows) {
      const tr = document.createElement("tr");
      const idx = document.createElement("td");
      idx.textContent = String(r.page || r.index + 1);
      const tdSrc = document.createElement("td");
      tdSrc.className = "col-src";
      tdSrc.textContent = (r.source || "").slice(0, 320) || "—";
      const tdTgt = document.createElement("td");
      tdTgt.className = "col-tgt";
      tdTgt.textContent = (r.target || "").slice(0, 320) || "—";
      const tdSt = document.createElement("td");
      const code = String(r.status || "paired");
      tdSt.className = `st-${code}`;
      tdSt.textContent = ALIGNED_STATUS_TR[code] || code;
      tr.appendChild(idx);
      tr.appendChild(tdSrc);
      tr.appendChild(tdTgt);
      tr.appendChild(tdSt);
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
    renderAlignedDiff(j);
    if (!j.aligned) flash("Segment sayıları tam hizalı değil — tabloya bakın.");
    else flash("Kaynak ve hedef segmentler hizalı görünüyor.");
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
    } catch {
      el.hidden = true;
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
            if (deps.createCodeTreeBranch) kids.appendChild(deps.createCodeTreeBranch(x, depth + 1));
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
    flash(
      (j.ready ? "Hazırlık tamam — " : "Eksik var — ") +
        lines.slice(0, 4).join(" · ") +
        (hints[0] ? ` · ${hints[0]}` : ""),
    );
    void refreshReadiness();
    return j;
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
    if (panel) panel.hidden = !show;
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
    const score = Number(quality.score);
    const tier = qualityTier(score);
    strip.hidden = false;
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
    flash(
      String(j.label || `Arka plan çevirisi bitti: ${okN}/${okN + errN}`) +
        (lowN ? ` — ${lowN} sayfa düşük kalite.` : ""),
    );
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
        showJobPanel(true);
        flash("Devam eden arka plan çevirisi bağlandı — sekme kapansa da sürer.");
        pollBatchJob(jid, { pageRange: true });
      } else if (j.status === "done") {
        await finishPageRangeJob(j);
      } else {
        clearPageJobStorage();
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
    const body = {
      rel: openRel,
      tgt_lang: String($("tercume-tgt-lang")?.value || "tr"),
      src_lang: String($("tercume-src-lang")?.value || "auto"),
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
    setTargetText("");
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
      body: JSON.stringify({
        folder_rel: folder,
        tgt_lang: String($("tercume-tgt-lang")?.value || "tr"),
        src_lang: String($("tercume-src-lang")?.value || "auto"),
      }),
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
            renderPageJobLog(j.outputs || [], String(j.error || j.label || j.status));
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
    if (!wrap) return;
    wrap.hidden = false;
    const pct = total > 0 ? Math.round((current / total) * 100) : 0;
    if (fill) fill.style.width = `${pct}%`;
    if (lab) lab.textContent = label || `${current}/${total}`;
  }
  function hideProgress() {
    const wrap = $("tercume-progress-wrap");
    if (wrap) wrap.hidden = true;
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
          flash(`Düşük kalite skoru (${hit.quality.score}) — «Yeniden çevir» veya metni düzeltin.`);
        }
      } catch (e) {
        outParts.push(`[HATA ${p.label || i + 1}: ${e.message || e}]`);
        setTargetText(outParts.join("\n\n"));
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
    flash("İndiriliyor (büyük dosyalar uzun sürebilir)…");
    const res = await fetch(`${api()}/api/tercume/import-url`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : "İndirme hatası");
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
        await refreshTree();
        flash(`Çalışma klasörü: ${workRoot}`);
      }
      return;
    }
    const v = String($("tercume-work-root")?.value || "").trim();
    if (v) {
      workRoot = v.replace(/\\/g, "/").replace(/^\/+/, "");
      try {
        localStorage.setItem(LS_WORK_ROOT, workRoot);
      } catch (_) {
        /* ignore */
      }
      await refreshTree();
    }
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
    if (global.RuzgarSplit?.onTercumeTabChange) {
      requestAnimationFrame(() => global.RuzgarSplit.onTercumeTabChange());
    }
  }

  function syncTercumeLayout(isTercume) {
    const tabs = $("tercume-view-tabs");
    if (tabs) tabs.hidden = !isTercume;
    if (isTercume) {
      document.body.dataset.motor = "tercume";
      const cur = normalizeTercumeTab(document.body.dataset.tercumeTab || "calisma");
      setTercumeTab(cur);
      void refreshOcrWarning();
      void refreshReadiness();
    } else {
      delete document.body.dataset.motor;
      delete document.body.dataset.tercumeTab;
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

  function wireAll() {
    if ($("page-tercume")?.dataset.tercumeV2Wired === "1") return;
    $("page-tercume").dataset.tercumeV2Wired = "1";
    wireTercumeViewTabs();

    try {
      workRoot = localStorage.getItem(LS_WORK_ROOT) || workRoot;
    } catch (_) {
      /* ignore */
    }
    const rootInp = $("tercume-work-root");
    if (rootInp) rootInp.value = workRoot;

    $("tercume-file-list")?.addEventListener("click", (ev) => void onTreeClick(ev));
    $("btn-tercume-refresh")?.addEventListener("click", () => void refreshTree());
    $("btn-tercume-pick-folder")?.addEventListener("click", () => void pickWorkFolder());
    $("tercume-work-root")?.addEventListener("change", () => void pickWorkFolder());
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
      if (ev.target.open && !$("tercume-arsiv-download-list")?.dataset.loaded) {
        $("tercume-arsiv-download-list").dataset.loaded = "1";
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
    $("btn-tercume-ocr")?.addEventListener("click", async () => {
      if (!openRel) {
        flash("Önce görsel dosyası seçin.");
        return;
      }
      await refreshOcrWarning();
      if (!$("tercume-ocr-warn")?.hidden) {
        flash("OCR kurulu değil — sarı uyarıdaki adımları uygulayın.");
        return;
      }
      try {
        setSourceText(await readFileForTercume(openRel, { forceOcr: true }));
        flash("OCR tamam.");
      } catch (e) {
        flash(e.message || "OCR hatası");
      }
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
    $("btn-tercume-term-add")?.addEventListener("click", () => {
      void addUserTerm().catch((e) => flash(e.message || String(e)));
    });
    $("tercume-user-glossary-fold")?.addEventListener("toggle", (ev) => {
      if (ev.target.open) void refreshUserGlossary();
    });
    $("btn-tercume-clear")?.addEventListener("click", () => {
      setSourceText("");
      setTargetText("");
      openRel = null;
      awaitingChatReply = false;
      hideEbookMeta();
      hideQualityStrip();
      updateActiveLabel();
      syncSavePlaceholder();
      const fd = new FormData();
      if (openRel) fd.append("source_file", openRel);
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
    void resumeActivePageJobIfAny();
    void refreshBatchJobsList();
    void refreshMemoryStatus();
    void refreshSavePrefs();
    void refreshUserGlossary();
    $("tercume-tgt-lang")?.addEventListener("change", () => {
      syncSavePlaceholder();
      void refreshMemoryStatus();
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
      void refreshTree();
      void refreshApprenticeLog();
      const fold = $("tercume-arsiv-download-fold");
      if (fold?.open) void refreshArsivCatalog();
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
      if (rel) openRel = rel;
      setSourceText(text);
      updateActiveLabel();
      syncSavePlaceholder();
      if (deps.switchMode) deps.switchMode("tercume");
    },
    getOpenRel: () => openRel,
    runSearch: (text) => runEserSearch(text).then((ok) => ok),
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
