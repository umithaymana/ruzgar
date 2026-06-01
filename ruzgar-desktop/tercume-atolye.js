/**
 * Tercüme Atölyesi v2 — yalnızca #page-tercume (diğer motorlara dokunmaz).
 */
(function initTercumeAtolyeModule(global) {
  const LS_WORK_ROOT = "ruzgar_tercume_work_root";
  const EBOOK_EXTS = [".epub", ".fb2", ".mobi", ".azw", ".azw3", ".kfx", ".djvu", ".djv", ".rtf"];
  const IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"];

  let deps = {};
  let openRel = null;
  let workRoot = "ilim-assistant/arsiv";
  let awaitingChatReply = false;
  let translateAbort = false;
  let lastDownloadDir = { abs: "", rel: "" };

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
      return String(j.text ?? "");
    }
    return readWorkspaceText(rel);
  }

  function defaultSaveRel() {
    const tgt = String($("tercume-tgt-lang")?.value || "tr").trim() || "tr";
    const fmt = String($("tercume-output-format")?.value || "txt").trim() || "txt";
    const ext = fmt === "md" ? ".md" : fmt === "html" ? ".html" : ".txt";
    if (openRel) {
      const leaf = String(openRel).split("/").pop() || "kaynak";
      const stem = leaf.replace(/\.[^.]+$/, "") || "kaynak";
      return `ilim-assistant/arsiv/tercume-output/${stem}_${tgt}${ext}`;
    }
    return `ilim-assistant/arsiv/tercume-output/ceviri_${tgt}_${Date.now()}${ext}`;
  }

  function syncSavePlaceholder() {
    const inp = $("tercume-save-rel");
    if (inp && !inp.value.trim()) inp.placeholder = defaultSaveRel();
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
    } catch (e) {
      openRel = rel;
      const msg = String(e.message || e);
      setSourceText(`(Dosya: ${rel}\n\nÖnizleme alınamadı: ${msg}\n\nBüyük PDF için OCR veya sayfa sayfa modunu deneyin.)`);
      updateActiveLabel();
      flash("Tam metin yüklenemedi; dosya yolu kayıtlı.");
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

  async function startBatchCilt() {
    if (batchPollTimer) {
      flash("Zaten bir cilt sırası işi çalışıyor.");
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

  function pollBatchJob(jobId) {
    if (batchPollTimer) clearInterval(batchPollTimer);
    batchPollTimer = setInterval(async () => {
      try {
        const res = await fetch(`${api()}/api/tercume/batch-status?job_id=${encodeURIComponent(jobId)}`);
        const j = await res.json().catch(() => ({}));
        if (!res.ok || !j.ok) return;
        const total = Number(j.total) || 0;
        const done = Number(j.done) || 0;
        const label = j.label || j.current_file || j.status || `${done}/${total}`;
        showProgress(done, total || 1, `Cilt sırası: ${label}`);
        if (j.status === "done" || j.status === "cancelled") {
          clearInterval(batchPollTimer);
          batchPollTimer = null;
          activeBatchJobId = null;
          const okN = Array.isArray(j.outputs) ? j.outputs.filter((o) => o.ok).length : done;
          flash(j.status === "done" ? `Cilt sırası bitti: ${okN}/${total} kaydedildi.` : "Cilt sırası iptal edildi.");
          setTimeout(hideProgress, 2500);
        }
      } catch {
        /* sessiz tekrar */
      }
    }, 2000);
  }

  async function cancelBatchJob() {
    if (!activeBatchJobId) return;
    const fd = new FormData();
    fd.append("job_id", activeBatchJobId);
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
    return String(j.text || "");
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
      pages = [{ index: 0, text: raw, label: "Tam metin" }];
    }
    if (!pages.length) {
      flash("Çevrilecek metin yok.");
      return;
    }
    setTargetText("");
    const delayMs = mode === "full" ? 400 : 120;
    const outParts = [];
    for (let i = 0; i < pages.length; i++) {
      if (translateAbort) break;
      const p = pages[i];
      showProgress(i + 1, pages.length, `Çevriliyor: ${p.label || i + 1}${p.quality === "low" ? " (zayıf)" : ""}`);
      try {
        const tr = await translateChunkApi(String(p.text || ""), p.index);
        outParts.push(tr);
        setTargetText(outParts.join("\n\n"));
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
    const copy = String($("tercume-copy-rel")?.value || "").trim();
    if (copy) fd.append("copy_rel", copy);
    const res = await fetch(`${api()}/api/tercume/save-target`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : "Kayıt başarısız");
    $("tercume-save-rel").value = j.rel || rel;
    flash(`Kaydedildi: ${j.rel}${j.copy_rel ? ` · kopya: ${j.copy_rel}` : ""}`);
    void refreshApprenticeLog();
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
      else if (mode === "page" || mode === "full" || mode === "range") void runPagedTranslation(mode);
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
    $("btn-tercume-clear")?.addEventListener("click", () => {
      setSourceText("");
      setTargetText("");
      openRel = null;
      awaitingChatReply = false;
      updateActiveLabel();
      syncSavePlaceholder();
      fetch(`${api()}/api/tercume/memory-clear`, { method: "POST" }).catch(() => {});
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
    $("tercume-tgt-lang")?.addEventListener("change", () => syncSavePlaceholder());
    $("tercume-output-format")?.addEventListener("change", () => syncSavePlaceholder());

    getSourceEl()?.addEventListener("input", () => updateStats());
    wireZoom();
    syncSavePlaceholder();
    void refreshTree();
    void refreshApprenticeLog();
    void refreshOcrWarning();
    void refreshReadiness();
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
