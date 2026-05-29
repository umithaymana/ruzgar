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
    const v = String($("tercume-src-lang")?.value || "auto").trim();
    const map = { tr: "tur", en: "eng", ar: "ara", de: "deu", fr: "fra", fa: "fas", ru: "rus" };
    if (v === "auto") return "tur+eng";
    return map[v] ? `${map[v]}+eng` : "tur+eng";
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
        `${api()}/api/workspace/read-image-ocr?rel=${encodeURIComponent(rel)}&lang=${encodeURIComponent(ocrLangFromUi())}`,
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
    const el = $("tercume-active-file");
    if (!el) return;
    el.textContent = openRel ? `Kaynak: ${openRel}` : "Kaynak: (listeden dosya seçin)";
  }

  function updateStats() {
    const el = $("tercume-stats");
    if (!el) return;
    const t = getSourceText();
    const words = t.replace(/\s+/g, " ").trim() ? t.trim().split(/\s+/).length : 0;
    el.textContent = `${t.length.toLocaleString("tr-TR")} karakter · ${words.toLocaleString("tr-TR")} kelime`;
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

  async function openFile(rel) {
    try {
      const text = await readFileForTercume(rel);
      openRel = rel;
      setSourceText(text);
      updateActiveLabel();
      syncSavePlaceholder();
      flash(`Yüklendi: ${rel}`);
      getSourceEl()?.focus();
      void refreshApprenticeLog();
    } catch (e) {
      setSourceText(`(okunamadı: ${e.message || e})`);
      flash("Dosya açılamadı.");
    }
  }

  async function onTreeClick(ev) {
    const row = ev.target.closest(".code-tree-file");
    if (!row || !row.dataset?.rel) return;
    ev.preventDefault();
    await openFile(row.dataset.rel);
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
    if (!j.ok) throw new Error(j.error || j.detail || `HTTP ${res.status}`);
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
    if (mode === "page" || mode === "full") {
      if (!openRel) {
        flash("Sayfa sayfa için önce dosyayı listeden açın.");
        return;
      }
      const res = await fetch(`${api()}/api/tercume/source-pages?rel=${encodeURIComponent(openRel)}`);
      const j = await res.json().catch(() => ({}));
      if (!j.ok || !Array.isArray(j.pages)) throw new Error("Sayfa listesi alınamadı");
      pages = j.pages.filter((p) => String(p.text || "").trim());
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
      showProgress(i + 1, pages.length, `Çevriliyor: ${p.label || i + 1}`);
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

  async function importUrl() {
    const url = String($("tercume-import-url")?.value || "").trim();
    if (!url) {
      flash("URL girin.");
      return;
    }
    const fd = new FormData();
    fd.append("url", url);
    const res = await fetch(`${api()}/api/tercume/import-url`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : "İndirme hatası");
    $("tercume-import-url").value = "";
    await refreshTree();
    if (j.rel) await openFile(j.rel);
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

  function wireAll() {
    if ($("page-tercume")?.dataset.tercumeV2Wired === "1") return;
    $("page-tercume").dataset.tercumeV2Wired = "1";

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
    $("btn-tercume-translate")?.addEventListener("click", () => {
      const mode = String($("tercume-translate-mode")?.value || "single");
      if (mode === "chat") void translateViaChat();
      else if (mode === "page" || mode === "full") void runPagedTranslation(mode);
      else void runPagedTranslation("single");
    });
    $("btn-tercume-stop")?.addEventListener("click", () => {
      translateAbort = true;
      flash("Durdurma istendi…");
    });
    $("btn-tercume-save-target")?.addEventListener("click", () => void saveTarget().catch((e) => flash(e.message)));
    $("btn-tercume-import-url")?.addEventListener("click", () => void importUrl().catch((e) => flash(e.message)));
    $("tercume-import-file")?.addEventListener("change", (ev) => {
      const f = ev.target.files?.[0];
      void importFile(f).catch((e) => flash(e.message));
      ev.target.value = "";
    });
    $("btn-tercume-ocr")?.addEventListener("click", async () => {
      if (!openRel) {
        flash("Önce görsel dosyası seçin.");
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
    });
    $("btn-tercume-last-to-target")?.addEventListener("click", () => {
      const t = String(deps.lastAssistantReply?.() || "").trim();
      if (!t) {
        flash("Sohbette yanıt yok.");
        return;
      }
      setTargetText(t);
    });
    $("tercume-tgt-lang")?.addEventListener("change", () => syncSavePlaceholder());
    $("tercume-output-format")?.addEventListener("change", () => syncSavePlaceholder());

    getSourceEl()?.addEventListener("input", () => updateStats());
    wireZoom();
    syncSavePlaceholder();
    void refreshTree();
    void refreshApprenticeLog();
  }

  global.RuzgarTercumeAtolye = {
    init(d) {
      deps = d || {};
      wireAll();
    },
    load() {
      updateActiveLabel();
      updateStats();
      syncSavePlaceholder();
      void refreshTree();
      void refreshApprenticeLog();
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
  };
})(window);
