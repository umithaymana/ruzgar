/**
 * Mimar Atölyesi — 3 bağımsız sayfa: fotoğraf / sanat / tasarım.
 * Faz 4F foto · 4S sanat · 4T tasarım (4S-4, 4T-2, 4T-3 dahil).
 */
(function initMimarAtolyeModule(global) {
  let deps = {};
  let fotoItems = [];
  let sanatItems = [];
  let activeFotoId = null;
  let activeSanatId = null;
  let fotoBusy = false;
  let modPanelOpen = false;
  let restorePanelOpen = false;
  let pendingRestoreOp = null;
  let previewingRestore = false;
  let lastVoiceText = "";
  let sanatBusy = false;
  let sanatShowingCopy = false;

  function api() {
    return deps.api || global.API || "";
  }
  function $(id) {
    return document.getElementById(id);
  }
  function flash(msg) {
    if (deps.flash) deps.flash(msg);
  }

  function mimarDrawCommand(ctx, cmd) {
    if (!cmd || !ctx) return;
    const t = cmd.type;
    ctx.strokeStyle = cmd.color || "#cccccc";
    ctx.fillStyle = cmd.color || "#cccccc";
    ctx.lineWidth = cmd.width || 1;
    if (t === "line") {
      ctx.beginPath();
      ctx.moveTo(cmd.x1, cmd.y1);
      ctx.lineTo(cmd.x2, cmd.y2);
      ctx.stroke();
    } else if (t === "rect") {
      if (cmd.fill) ctx.fillRect(cmd.x, cmd.y, cmd.w, cmd.h);
      else ctx.strokeRect(cmd.x, cmd.y, cmd.w, cmd.h);
    } else if (t === "circle") {
      ctx.beginPath();
      ctx.arc(cmd.cx, cmd.cy, cmd.r, 0, Math.PI * 2);
      if (cmd.fill) ctx.fill();
      else ctx.stroke();
    } else if (t === "polyline" && Array.isArray(cmd.points) && cmd.points.length >= 2) {
      ctx.beginPath();
      ctx.moveTo(cmd.points[0][0], cmd.points[0][1]);
      for (let i = 1; i < cmd.points.length; i++) ctx.lineTo(cmd.points[i][0], cmd.points[i][1]);
      ctx.stroke();
    } else if (t === "text" && cmd.text) {
      ctx.font = `${cmd.size || 14}px Segoe UI, sans-serif`;
      ctx.fillStyle = cmd.color || "#e0e0e0";
      ctx.fillText(cmd.text, cmd.x, cmd.y);
    }
  }

  function normalizeTab(tab) {
    let t = String(tab || "fotograf").trim() || "fotograf";
    if (t === "sohbet" || t === "icerik") t = "fotograf";
    if (t === "kroki") t = "tasarim";
    return t;
  }

  function fotoPreviewUrl(rel) {
    if (!rel) return "";
    return `${api()}/api/mimar/fotograf/file?rel=${encodeURIComponent(rel)}&t=${Date.now()}`;
  }

  function setMimarTab(tab) {
    const t = normalizeTab(tab);
    document.body.dataset.mimarTab = t;
    document.querySelectorAll(".mimar-view-tab").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.mimarTab === t);
    });
    const wb = $("mimar-workbench");
    if (wb) wb.className = `mimar-workbench mimar-workbench--${t}`;
    ["fotograf", "resim-sanat", "tasarim"].forEach((key) => {
      const node = $(`mimar-panel-${key}`);
      if (node) node.hidden = t !== key;
    });
    if (t === "tasarim") initTasarimCanvas();
    if (t === "fotograf") void refreshFotoList();
    if (t === "resim-sanat") void refreshSanatList();
    if (t === "tasarim") void refreshTasarimProjectSelect();
  }

  function syncMimarLayout(isMimar) {
    const tabs = $("mimar-view-tabs");
    if (tabs) tabs.hidden = !isMimar;
    if (isMimar) {
      document.body.dataset.motor = "mimar";
      setMimarTab(document.body.dataset.mimarTab || "fotograf");
    } else if (document.body.dataset.motor === "mimar") {
      delete document.body.dataset.motor;
      delete document.body.dataset.mimarTab;
    }
  }

  function wireMimarViewTabs() {
    const bar = $("mimar-view-tabs");
    if (!bar || bar.dataset.wired === "1") return;
    bar.dataset.wired = "1";
    const labels = { fotograf: "Fotoğraf", "resim-sanat": "Resim · Sanat", tasarim: "Tasarım" };
    bar.querySelectorAll(".mimar-view-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        setMimarTab(btn.dataset.mimarTab || "fotograf");
        flash(`Mimar: ${labels[btn.dataset.mimarTab] || btn.dataset.mimarTab}`);
      });
    });
  }

  function activeFotoItem() {
    return fotoItems.find((x) => x.id === activeFotoId) || null;
  }

  function updateFotoStatus(text) {
    const el = $("mimar-foto-status");
    if (el) el.textContent = text || "";
  }

  function renderFotoThumbs() {
    const ul = $("mimar-foto-thumbs");
    if (!ul) return;
    if (!fotoItems.length) {
      ul.innerHTML =
        '<li class="mimar-foto-thumb-empty">Henüz fotoğraf yok — «Ekle» ile yükleyin.</li>';
      return;
    }
    ul.innerHTML = fotoItems
      .map(
        (it) =>
          `<li class="mimar-foto-thumb${it.id === activeFotoId ? " is-active" : ""}" data-foto-id="${it.id}"><img src="${fotoPreviewUrl(it.rel)}" alt="${it.name || ""}" /></li>`,
      )
      .join("");
    ul.querySelectorAll(".mimar-foto-thumb").forEach((li) => {
      li.addEventListener("click", () => selectFoto(li.dataset.fotoId));
    });
  }

  function selectFoto(id) {
    activeFotoId = id;
    const item = activeFotoItem();
    const img = $("mimar-foto-preview-img");
    const hint = document.querySelector(".mimar-foto-preview-hint");
    if (item && img) {
      img.src = fotoPreviewUrl(item.rel);
      img.hidden = false;
      if (hint) hint.hidden = true;
      const wh = item.width && item.height ? ` · ${item.width}×${item.height}` : "";
      updateFotoStatus(`${item.name || item.rel}${wh}`);
      $("btn-mimar-foto-moderasyon")?.removeAttribute("disabled");
      $("btn-mimar-foto-restore")?.removeAttribute("disabled");
      $("btn-mimar-foto-tts")?.removeAttribute("disabled");
      $("btn-mimar-foto-speak")?.removeAttribute("disabled");
    } else {
      $("btn-mimar-foto-moderasyon")?.setAttribute("disabled", "disabled");
      $("btn-mimar-foto-restore")?.setAttribute("disabled", "disabled");
      $("btn-mimar-foto-tts")?.setAttribute("disabled", "disabled");
      $("btn-mimar-foto-speak")?.setAttribute("disabled", "disabled");
    }
    renderFotoThumbs();
  }

  async function refreshFotoList() {
    try {
      const res = await fetch(`${api()}/api/mimar/fotograf/list`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      fotoItems = (j.items || []).map((it) => ({
        id: it.id || it.rel,
        rel: it.rel,
        name: it.name,
        width: it.width,
        height: it.height,
      }));
      if (activeFotoId && !fotoItems.some((x) => x.id === activeFotoId)) {
        activeFotoId = fotoItems[0]?.id || null;
      }
      if (!activeFotoId && fotoItems.length) activeFotoId = fotoItems[0].id;
      renderFotoThumbs();
      if (activeFotoId) selectFoto(activeFotoId);
      else {
        const img = $("mimar-foto-preview-img");
        if (img) {
          img.hidden = true;
          img.removeAttribute("src");
        }
        const hint = document.querySelector(".mimar-foto-preview-hint");
        if (hint) hint.hidden = false;
        updateFotoStatus(j.pillow === false ? "Pillow yok: pip install pillow" : "Fotoğraf seçin veya ekleyin");
      }
    } catch (e) {
      updateFotoStatus(`Liste alınamadı: ${e.message || e}`);
    }
  }

  async function uploadFotoFile(file) {
    const fd = new FormData();
    fd.append("file", file, file.name);
    const res = await fetch(`${api()}/api/mimar/fotograf/upload`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
    return j.item || j;
  }

  async function addFotoFiles(fileList) {
    const files = [...(fileList || [])].filter((f) => f.type.startsWith("image/"));
    if (!files.length) {
      flash("Geçerli görsel seçilmedi.");
      return;
    }
    if (fotoBusy) return;
    fotoBusy = true;
    updateFotoStatus("Yükleniyor…");
    try {
      for (const f of files) {
        const item = await uploadFotoFile(f);
        if (item?.rel) {
          fotoItems.unshift({
            id: item.id || item.rel,
            rel: item.rel,
            name: item.name || f.name,
            width: item.width,
            height: item.height,
          });
          activeFotoId = item.id || item.rel;
        }
      }
      renderFotoThumbs();
      if (activeFotoId) selectFoto(activeFotoId);
      flash(`${files.length} fotoğraf arşive kaydedildi.`);
    } catch (e) {
      flash(`Yükleme hatası: ${e.message || e}`);
      updateFotoStatus(String(e.message || e));
    } finally {
      fotoBusy = false;
    }
  }

  async function applyFotoOp(op) {
    const item = activeFotoItem();
    if (!item?.rel || fotoBusy) {
      flash("Önce bir fotoğraf seçin.");
      return;
    }
    fotoBusy = true;
    updateFotoStatus("İşleniyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/fotograf/moderate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel, op }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      item.rel = j.rel || item.rel;
      item.width = j.width;
      item.height = j.height;
      selectFoto(activeFotoId);
      flash(j.label_tr || "Moderasyon uygulandı.");
    } catch (e) {
      flash(`Moderasyon: ${e.message || e}`);
      updateFotoStatus(String(e.message || e));
    } finally {
      fotoBusy = false;
    }
  }

  async function restoreFotoOriginal() {
    const item = activeFotoItem();
    if (!item?.rel || fotoBusy) return;
    fotoBusy = true;
    try {
      const res = await fetch(`${api()}/api/mimar/fotograf/restore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      item.width = j.width;
      item.height = j.height;
      cancelRestorePreview();
      selectFoto(activeFotoId);
      flash(j.label_tr || "Orijinal geri yüklendi.");
    } catch (e) {
      flash(String(e.message || e));
    } finally {
      fotoBusy = false;
    }
  }

  function cancelRestorePreview() {
    pendingRestoreOp = null;
    previewingRestore = false;
    $("btn-mimar-foto-restore-apply")?.setAttribute("disabled", "disabled");
    const item = activeFotoItem();
    const img = $("mimar-foto-preview-img");
    if (item && img) {
      img.src = fotoPreviewUrl(item.rel);
    }
  }

  async function previewRestoreOp(op) {
    const item = activeFotoItem();
    if (!item?.rel || fotoBusy) {
      flash("Önce fotoğraf seçin.");
      return;
    }
    fotoBusy = true;
    updateFotoStatus("Restorasyon önizleniyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/fotograf/restoration/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel, op }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      pendingRestoreOp = op;
      previewingRestore = true;
      const img = $("mimar-foto-preview-img");
      if (img && j.preview_b64) {
        img.src = `data:image/jpeg;base64,${j.preview_b64}`;
        img.hidden = false;
      }
      $("btn-mimar-foto-restore-apply")?.removeAttribute("disabled");
      const cv = j.opencv_used ? " · OpenCV" : "";
      updateFotoStatus(`Önizleme: ${j.label_tr || op}${cv} — «Uygula» ile kaydet`);
    } catch (e) {
      flash(`Önizleme: ${e.message || e}`);
      updateFotoStatus(String(e.message || e));
    } finally {
      fotoBusy = false;
    }
  }

  async function applyPendingRestore() {
    const item = activeFotoItem();
    const op = pendingRestoreOp;
    if (!item?.rel || !op || fotoBusy) {
      flash("Önce bir restorasyon önizleyin.");
      return;
    }
    fotoBusy = true;
    updateFotoStatus("Kaydediliyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/fotograf/restoration/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel, op }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      item.rel = j.rel || item.rel;
      item.width = j.width;
      item.height = j.height;
      pendingRestoreOp = null;
      previewingRestore = false;
      $("btn-mimar-foto-restore-apply")?.setAttribute("disabled", "disabled");
      selectFoto(activeFotoId);
      flash(j.label_tr || "Restorasyon kaydedildi.");
    } catch (e) {
      flash(`Kayıt: ${e.message || e}`);
      updateFotoStatus(String(e.message || e));
    } finally {
      fotoBusy = false;
    }
  }

  function toggleModPanel(force) {
    modPanelOpen = typeof force === "boolean" ? force : !modPanelOpen;
    const panel = $("mimar-foto-moderasyon");
    if (panel) panel.hidden = !modPanelOpen;
    const btn = $("btn-mimar-foto-moderasyon");
    if (btn) btn.classList.toggle("is-active", modPanelOpen);
    if (modPanelOpen) toggleRestorePanel(false);
    if (modPanelOpen) toggleVoicePanel(false);
  }

  function toggleRestorePanel(force) {
    restorePanelOpen = typeof force === "boolean" ? force : !restorePanelOpen;
    const panel = $("mimar-foto-restoration");
    if (panel) panel.hidden = !restorePanelOpen;
    const btn = $("btn-mimar-foto-restore");
    if (btn) btn.classList.toggle("is-active", restorePanelOpen);
    if (restorePanelOpen) {
      toggleModPanel(false);
      toggleVoicePanel(false);
    } else {
      cancelRestorePreview();
    }
  }

  function toggleVoicePanel(force) {
    const open = typeof force === "boolean" ? force : !($("mimar-foto-voice")?.hidden === false);
    const panel = $("mimar-foto-voice");
    if (panel) panel.hidden = !open;
    if (open) {
      toggleModPanel(false);
      toggleRestorePanel(false);
    }
  }

  async function fetchVoiceText(mode) {
    const item = activeFotoItem();
    if (!item?.rel || fotoBusy) {
      flash("Önce fotoğraf seçin.");
      return null;
    }
    fotoBusy = true;
    updateFotoStatus(mode === "speak" ? "Konuşturma metni hazırlanıyor…" : "Metin çıkarılıyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/fotograf/voice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel, mode }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      lastVoiceText = String(j.text || "");
      const ta = $("mimar-foto-voice-text");
      if (ta) ta.value = lastVoiceText;
      toggleVoicePanel(true);
      const src = j.source === "ocr" ? "OCR" : j.source === "vision" ? "görsel betimleme" : "";
      const note = src ? ` (${src})` : "";
      updateFotoStatus(`${j.label_tr || "Metin hazır"}${note}`);
      flash(j.label_tr || "Metin hazır.");
      return lastVoiceText;
    } catch (e) {
      flash(String(e.message || e));
      updateFotoStatus(String(e.message || e));
      return null;
    } finally {
      fotoBusy = false;
    }
  }

  async function runFotoVoice(mode) {
    const text = await fetchVoiceText(mode);
    if (!text) return;
    if (deps.speakText) {
      await deps.speakText(text);
    } else {
      flash("Seslendirme köprüsü yok — metin panelde.");
    }
  }

  async function replayFotoVoice() {
    if (!lastVoiceText) {
      flash("Önce «Metin oku» veya «Konuştur» ile metin üretin.");
      return;
    }
    if (deps.speakText) {
      await deps.speakText(lastVoiceText);
    } else {
      flash("Seslendirme köprüsü yok.");
    }
  }

  function wireFotoPage() {
    $("mimar-foto-file")?.addEventListener("change", (ev) => {
      void addFotoFiles(ev.target.files);
      ev.target.value = "";
    });
    const preview = $("mimar-foto-preview");
    preview?.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      preview.classList.add("is-drag");
    });
    preview?.addEventListener("dragleave", () => preview.classList.remove("is-drag"));
    preview?.addEventListener("drop", (ev) => {
      ev.preventDefault();
      preview.classList.remove("is-drag");
      void addFotoFiles(ev.dataTransfer?.files);
    });

    $("btn-mimar-foto-moderasyon")?.addEventListener("click", () => {
      if (!activeFotoItem()) {
        flash("Önce fotoğraf seçin.");
        return;
      }
      toggleModPanel();
    });

    document.querySelectorAll("[data-foto-op]").forEach((btn) => {
      btn.addEventListener("click", () => void applyFotoOp(btn.getAttribute("data-foto-op")));
    });
    $("btn-mimar-foto-undo")?.addEventListener("click", () => void restoreFotoOriginal());

    $("btn-mimar-foto-restore")?.addEventListener("click", () => {
      if (!activeFotoItem()) {
        flash("Önce fotoğraf seçin.");
        return;
      }
      toggleRestorePanel();
    });
    document.querySelectorAll("[data-restore-op]").forEach((btn) => {
      btn.addEventListener("click", () => void previewRestoreOp(btn.getAttribute("data-restore-op")));
    });
    $("btn-mimar-foto-restore-apply")?.addEventListener("click", () => void applyPendingRestore());
    $("btn-mimar-foto-restore-cancel")?.addEventListener("click", () => {
      cancelRestorePreview();
      flash("Önizleme iptal — kayıtlı sürüm gösteriliyor.");
    });
    $("btn-mimar-foto-tts")?.addEventListener("click", () => void runFotoVoice("read"));
    $("btn-mimar-foto-speak")?.addEventListener("click", () => void runFotoVoice("speak"));
    $("btn-mimar-foto-voice-speak")?.addEventListener("click", () => void replayFotoVoice());
    $("btn-mimar-foto-voice-hide")?.addEventListener("click", () => toggleVoicePanel(false));
  }

  function sanatPreviewUrl(rel) {
    if (!rel) return "";
    return `${api()}/api/mimar/sanat/file?rel=${encodeURIComponent(rel)}&t=${Date.now()}`;
  }

  function activeSanatItem() {
    return sanatItems.find((x) => x.id === activeSanatId) || null;
  }

  function updateSanatStatus(text) {
    const el = $("mimar-sanat-status");
    if (el) el.textContent = text || "";
  }

  function escHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderSanatReport(report) {
    const box = $("mimar-sanat-report");
    if (!box) return;
    const r = report && typeof report === "object" ? report : {};
    const has =
      r.summary ||
      r.style ||
      r.composition ||
      r.historical_context ||
      r.subject;
    if (!has) {
      box.hidden = true;
      box.innerHTML = "";
      return;
    }
    const conf = r.confidence ? `<span class="mimar-sanat-conf mimar-sanat-conf--${escHtml(r.confidence)}">${escHtml(r.confidence)}</span>` : "";
    const rows = [
      ["Stil", r.style],
      ["Akım", r.movement],
      ["Konu", r.subject],
      ["Kompozisyon", r.composition],
      ["Renk", r.color_palette],
      ["Tarihsel bağlam", r.historical_context],
    ]
      .filter(([, v]) => v)
      .map(([k, v]) => `<dt>${escHtml(k)}</dt><dd>${escHtml(v)}</dd>`)
      .join("");
    const sim = (r.similar_artists || []).length
      ? `<p class="mimar-sanat-report-sim"><strong>Benzer:</strong> ${escHtml(r.similar_artists.join(", "))}</p>`
      : "";
    const tips = r.viewing_tips
      ? `<p class="mimar-sanat-report-tips">${escHtml(r.viewing_tips)}</p>`
      : "";
    box.innerHTML = `<div class="mimar-sanat-report-head">Eser raporu ${conf}</div>${
      r.summary ? `<p class="mimar-sanat-report-sum">${escHtml(r.summary)}</p>` : ""
    }${rows ? `<dl class="mimar-sanat-report-dl">${rows}</dl>` : ""}${sim}${tips}`;
    box.hidden = false;
  }

  function fillSanatMeta(item) {
    if ($("mimar-sanat-title")) $("mimar-sanat-title").value = item?.title || "";
    if ($("mimar-sanat-artist")) $("mimar-sanat-artist").value = item?.artist || "";
    if ($("mimar-sanat-period")) $("mimar-sanat-period").value = item?.period || "";
    if ($("mimar-sanat-technique")) $("mimar-sanat-technique").value = item?.technique || "";
    if ($("mimar-sanat-notes")) $("mimar-sanat-notes").value = item?.notes || "";
    renderSanatReport(item?.identify_report);
  }

  function readSanatMetaFromForm() {
    return {
      title: $("mimar-sanat-title")?.value?.trim() || "",
      artist: $("mimar-sanat-artist")?.value?.trim() || "",
      period: $("mimar-sanat-period")?.value?.trim() || "",
      technique: $("mimar-sanat-technique")?.value?.trim() || "",
      notes: $("mimar-sanat-notes")?.value?.trim() || "",
    };
  }

  function renderSanatGallery() {
    const gal = $("mimar-sanat-gallery");
    if (!gal) return;
    const tiles = sanatItems
      .map((it) => {
        const cap = it.title || it.name || "";
        return `<button type="button" class="mimar-sanat-tile${it.id === activeSanatId ? " is-active" : ""}" data-sanat-id="${it.id}" title="${cap}"><img src="${sanatPreviewUrl(it.rel)}" alt="${cap}" /></button>`;
      })
      .join("");
    const empty =
      sanatItems.length === 0
        ? '<div class="mimar-sanat-gallery-empty">Henüz eser yok — «Eser ekle» ile yükleyin.</div>'
        : "";
    gal.innerHTML = `${empty}${tiles}<label class="mimar-sanat-tile mimar-sanat-tile-add"><span>+ Eser ekle</span><input type="file" id="mimar-sanat-file" hidden accept="image/*" multiple /></label>`;
    gal.querySelectorAll(".mimar-sanat-tile[data-sanat-id]").forEach((btn) => {
      btn.addEventListener("click", () => selectSanat(btn.dataset.sanatId));
    });
    $("mimar-sanat-file")?.addEventListener("change", (ev) => {
      void addSanatFiles(ev.target.files);
      ev.target.value = "";
    });
  }

  function setupSanatPreview(item) {
    const prev = $("mimar-sanat-preview");
    if (!prev || !item) return;
    const showCopy = sanatShowingCopy && item.copy_rel;
    const src = showCopy ? sanatPreviewUrl(item.copy_rel) : sanatPreviewUrl(item.rel);
    prev.innerHTML = `<img class="mimar-sanat-preview-img" src="${src}" alt="${escHtml(item.title || item.name || "")}" /><canvas class="mimar-sanat-sketch-layer" id="mimar-sanat-sketch-canvas" aria-hidden="true"></canvas>`;
    const img = prev.querySelector(".mimar-sanat-preview-img");
    if (img) {
      img.onload = () => renderSanatSketch(item);
      if (img.complete) renderSanatSketch(item);
    }
  }

  function renderSanatSketch(item) {
    const canvas = $("mimar-sanat-sketch-canvas");
    if (!canvas) return;
    const cmds = item?.sketch_commands;
    if (!cmds?.length) {
      canvas.hidden = true;
      return;
    }
    const w = item.sketch_width || item.width || 960;
    const h = item.sketch_height || item.height || 540;
    canvas.width = w;
    canvas.height = h;
    canvas.hidden = false;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, w, h);
    cmds.forEach((cmd) => mimarDrawCommand(ctx, cmd));
    $("btn-mimar-sanat-sketch-dl")?.removeAttribute("disabled");
  }

  function selectSanat(id) {
    activeSanatId = id;
    sanatShowingCopy = false;
    const item = activeSanatItem();
    const hint = document.querySelector(".mimar-sanat-preview-hint");
    if (item) {
      setupSanatPreview(item);
      if (hint) hint.hidden = true;
      fillSanatMeta(item);
      const wh = item.width && item.height ? ` · ${item.width}×${item.height}` : "";
      updateSanatStatus(`${item.title || item.name || item.rel}${wh}`);
      $("btn-mimar-sanat-tani")?.removeAttribute("disabled");
      $("btn-mimar-sanat-analyze")?.removeAttribute("disabled");
      $("btn-mimar-sanat-save-meta")?.removeAttribute("disabled");
      $("btn-mimar-sanat-ciz")?.removeAttribute("disabled");
      if (item.sketch_svg_rel) $("btn-mimar-sanat-sketch-dl")?.removeAttribute("disabled");
      else $("btn-mimar-sanat-sketch-dl")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-kopya")?.removeAttribute("disabled");
      if (item.copy_rel) $("btn-mimar-sanat-copy-view")?.removeAttribute("disabled");
      else $("btn-mimar-sanat-copy-view")?.setAttribute("disabled", "disabled");
    } else {
      const prev = $("mimar-sanat-preview");
      if (prev) prev.innerHTML = '<span class="mimar-sanat-preview-hint">Galeriden eser seçin</span>';
      $("btn-mimar-sanat-tani")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-analyze")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-save-meta")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-ciz")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-sketch-dl")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-kopya")?.setAttribute("disabled", "disabled");
      $("btn-mimar-sanat-copy-view")?.setAttribute("disabled", "disabled");
    }
    renderSanatGallery();
  }

  async function refreshSanatList() {
    try {
      const res = await fetch(`${api()}/api/mimar/sanat/list`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      sanatItems = (j.items || []).map((it) => ({
        id: it.id || it.rel,
        rel: it.rel,
        name: it.name,
        title: it.title,
        artist: it.artist,
        period: it.period,
        technique: it.technique,
        notes: it.notes,
        identify_summary: it.identify_summary,
        identify_source: it.identify_source,
        identify_report: it.identify_report,
        identify_confidence: it.identify_confidence,
        sketch_commands: it.sketch_commands,
        sketch_svg_rel: it.sketch_svg_rel,
        sketch_source: it.sketch_source,
        sketch_width: it.sketch_width,
        sketch_height: it.sketch_height,
        copy_rel: it.copy_rel,
        copy_mode: it.copy_mode,
        width: it.width,
        height: it.height,
      }));
      if (activeSanatId && !sanatItems.some((x) => x.id === activeSanatId)) {
        activeSanatId = sanatItems[0]?.id || null;
      }
      if (!activeSanatId && sanatItems.length) activeSanatId = sanatItems[0].id;
      renderSanatGallery();
      if (activeSanatId) selectSanat(activeSanatId);
      else {
        const prev = $("mimar-sanat-preview");
        if (prev) {
          prev.innerHTML = '<span class="mimar-sanat-preview-hint">Galeriden eser seçin</span>';
        }
        fillSanatMeta(null);
        updateSanatStatus(j.pillow === false ? "Pillow yok: pip install pillow" : "Eser seçin veya ekleyin");
      }
    } catch (e) {
      updateSanatStatus(`Liste alınamadı: ${e.message || e}`);
    }
  }

  async function uploadSanatFile(file) {
    const fd = new FormData();
    fd.append("file", file, file.name);
    const res = await fetch(`${api()}/api/mimar/sanat/upload`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
    return j.item || j;
  }

  async function addSanatFiles(fileList) {
    const files = [...(fileList || [])].filter((f) => f.type.startsWith("image/"));
    if (!files.length) {
      flash("Geçerli görsel seçilmedi.");
      return;
    }
    if (sanatBusy) return;
    sanatBusy = true;
    updateSanatStatus("Yükleniyor…");
    try {
      for (const f of files) {
        const item = await uploadSanatFile(f);
        if (item?.rel) {
          sanatItems.unshift({
            id: item.id || item.rel,
            rel: item.rel,
            name: item.name || f.name,
            title: item.title,
            artist: item.artist,
            period: item.period,
            technique: item.technique,
            notes: item.notes,
            width: item.width,
            height: item.height,
          });
          activeSanatId = item.id || item.rel;
        }
      }
      renderSanatGallery();
      if (activeSanatId) selectSanat(activeSanatId);
      flash(`${files.length} eser galeriye kaydedildi.`);
    } catch (e) {
      flash(`Yükleme hatası: ${e.message || e}`);
      updateSanatStatus(String(e.message || e));
    } finally {
      sanatBusy = false;
    }
  }

  async function saveSanatMeta() {
    const item = activeSanatItem();
    if (!item?.rel || sanatBusy) {
      flash("Önce bir eser seçin.");
      return;
    }
    sanatBusy = true;
    updateSanatStatus("Kaydediliyor…");
    const meta = readSanatMetaFromForm();
    try {
      const res = await fetch(`${api()}/api/mimar/sanat/meta`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel, ...meta }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      const saved = j.item || {};
      Object.assign(item, saved);
      selectSanat(activeSanatId);
      flash(j.label_tr || "Eser bilgisi kaydedildi.");
    } catch (e) {
      flash(String(e.message || e));
      updateSanatStatus(String(e.message || e));
    } finally {
      sanatBusy = false;
    }
  }

  async function runSanatAnalyze(depth) {
    const item = activeSanatItem();
    if (!item?.rel || sanatBusy) {
      flash("Önce bir eser seçin.");
      return;
    }
    sanatBusy = true;
    updateSanatStatus(depth === "deep" ? "Detaylı rapor hazırlanıyor…" : "Eser tanınıyor…");
    $("btn-mimar-sanat-tani")?.setAttribute("disabled", "disabled");
    $("btn-mimar-sanat-analyze")?.setAttribute("disabled", "disabled");
    try {
      const url =
        depth === "deep"
          ? `${api()}/api/mimar/sanat/analyze`
          : `${api()}/api/mimar/sanat/identify`;
      const body =
        depth === "deep"
          ? { rel: item.rel, depth: "deep" }
          : { rel: item.rel };
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      const saved = j.item || {};
      Object.assign(item, saved);
      fillSanatMeta(item);
      if (j.report) renderSanatReport(j.report);
      const src = j.source === "gemini" ? "Gemini" : "Yapısal özet";
      updateSanatStatus(`${j.label_tr || "Tamam"} (${src})`);
      flash(j.label_tr || (depth === "deep" ? "Detaylı rapor hazır." : "Eser tanındı."));
    } catch (e) {
      flash(String(e.message || e));
      updateSanatStatus(String(e.message || e));
    } finally {
      sanatBusy = false;
      if (activeSanatItem()) {
        $("btn-mimar-sanat-tani")?.removeAttribute("disabled");
        $("btn-mimar-sanat-analyze")?.removeAttribute("disabled");
      }
    }
  }

  async function sketchSanatWork() {
    const item = activeSanatItem();
    if (!item?.rel || sanatBusy) {
      flash("Önce bir eser seçin.");
      return;
    }
    sanatBusy = true;
    updateSanatStatus("Eskiz üretiliyor…");
    $("btn-mimar-sanat-ciz")?.setAttribute("disabled", "disabled");
    try {
      const res = await fetch(`${api()}/api/mimar/sanat/sketch`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      Object.assign(item, j.item || {});
      if (j.commands) item.sketch_commands = j.commands;
      renderSanatSketch(item);
      const src = j.source === "gemini" ? "Gemini" : "Kenar";
      flash(`${j.label_tr || "Eskiz hazır"} (${src})`);
      updateSanatStatus(`${j.label_tr || "Eskiz"} · ${src}`);
    } catch (e) {
      flash(String(e.message || e));
      updateSanatStatus(String(e.message || e));
    } finally {
      sanatBusy = false;
      if (activeSanatItem()) $("btn-mimar-sanat-ciz")?.removeAttribute("disabled");
    }
  }

  function downloadSanatSketchSvg() {
    const item = activeSanatItem();
    if (!item?.sketch_svg_rel) {
      flash("Önce «Çiz / eskiz» ile katman üretin.");
      return;
    }
    const a = document.createElement("a");
    a.href = `${api()}/api/mimar/sanat/file?rel=${encodeURIComponent(item.sketch_svg_rel)}&t=${Date.now()}`;
    a.download = `${item.title || item.name || "eskiz"}.svg`;
    a.click();
    flash("SVG indiriliyor…");
  }

  async function copySanatWork(mode) {
    const item = activeSanatItem();
    if (!item?.rel || sanatBusy) {
      flash("Önce bir eser seçin.");
      return;
    }
    sanatBusy = true;
    updateSanatStatus("Kopya üretiliyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/sanat/copy`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: item.rel, mode: mode || "trace" }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      Object.assign(item, j.item || {});
      sanatShowingCopy = true;
      setupSanatPreview(item);
      $("btn-mimar-sanat-copy-view")?.removeAttribute("disabled");
      flash(j.label_tr || "Kopya hazır.");
      updateSanatStatus(`${j.label_tr || "Kopya"} · ${j.mode || mode}`);
    } catch (e) {
      flash(String(e.message || e));
      updateSanatStatus(String(e.message || e));
    } finally {
      sanatBusy = false;
    }
  }

  function toggleSanatCopyView() {
    const item = activeSanatItem();
    if (!item?.copy_rel) {
      flash("Önce «Kopya çıkar» ile kopya üretin.");
      return;
    }
    sanatShowingCopy = !sanatShowingCopy;
    setupSanatPreview(item);
    flash(sanatShowingCopy ? "Kopya görünümü." : "Orijinal eser.");
  }

  function wireSanatPage() {
    $("btn-mimar-sanat-tani")?.addEventListener("click", () => void runSanatAnalyze("quick"));
    $("btn-mimar-sanat-analyze")?.addEventListener("click", () => void runSanatAnalyze("deep"));
    $("btn-mimar-sanat-save-meta")?.addEventListener("click", () => void saveSanatMeta());
    $("btn-mimar-sanat-ciz")?.addEventListener("click", () => void sketchSanatWork());
    $("btn-mimar-sanat-sketch-dl")?.addEventListener("click", () => downloadSanatSketchSvg());
    $("btn-mimar-sanat-kopya")?.addEventListener("click", () => void copySanatWork("trace"));
    $("btn-mimar-sanat-copy-view")?.addEventListener("click", () => toggleSanatCopyView());
  }

  let canvasInited = false;
  let tasarimProject = null;
  let tasarimRefRel = "";
  let tasarimRefImage = null;
  let tasarimBusy = false;
  let tasarimPenDown = false;
  let tasarimPenLast = null;

  function updateTasarimStatus(text) {
    const el = $("mimar-tasarim-status");
    if (el) el.textContent = text || "";
  }

  function tasarimRefUrl(rel) {
    if (!rel) return "";
    return `${api()}/api/mimar/tasarim/reference/file?rel=${encodeURIComponent(rel)}&t=${Date.now()}`;
  }

  function defaultTasarimProject() {
    return {
      id: "",
      name: "Yeni plan",
      width: 960,
      height: 540,
      notes: "",
      reference_rel: "",
      layers: [
        { id: "eskiz", name: "Eskiz", visible: true, kind: "vector", commands: [] },
        { id: "el", name: "El çizimi", visible: true, kind: "vector", commands: [] },
      ],
    };
  }

  function getTasarimLayer(id) {
    const layers = tasarimProject?.layers || [];
    return layers.find((l) => l.id === id) || null;
  }

  function canvasPoint(canvas, ev) {
    const r = canvas.getBoundingClientRect();
    const sx = canvas.width / (r.width || 1);
    const sy = canvas.height / (r.height || 1);
    return { x: (ev.clientX - r.left) * sx, y: (ev.clientY - r.top) * sy };
  }

  function renderTasarimCanvas() {
    const canvas = $("mimar-tasarim-canvas");
    if (!canvas || !tasarimProject) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const w = tasarimProject.width || 960;
    const h = tasarimProject.height || 540;
    if (canvas.width !== w) canvas.width = w;
    if (canvas.height !== h) canvas.height = h;
    ctx.fillStyle = "#1a1a1a";
    ctx.fillRect(0, 0, w, h);
    if (tasarimRefImage) {
      ctx.globalAlpha = 0.35;
      const iw = tasarimRefImage.width;
      const ih = tasarimRefImage.height;
      const scale = Math.min(w / iw, h / ih);
      const dw = iw * scale;
      const dh = ih * scale;
      ctx.drawImage(tasarimRefImage, (w - dw) / 2, (h - dh) / 2, dw, dh);
      ctx.globalAlpha = 1;
    }
    (tasarimProject.layers || []).forEach((layer) => {
      if (layer.visible === false) return;
      (layer.commands || []).forEach((cmd) => mimarDrawCommand(ctx, cmd));
    });
  }

  function renderTasarimLayers() {
    const ul = $("mimar-tasarim-layers");
    if (!ul || !tasarimProject) return;
    const layers = tasarimProject.layers || [];
    if (!layers.length) {
      ul.innerHTML = '<li class="mimar-layer-empty">Henüz katman yok</li>';
      return;
    }
    ul.innerHTML = layers
      .map(
        (l) =>
          `<li class="mimar-layer-item${l.visible === false ? " is-hidden" : ""}" data-layer-id="${l.id}"><span>${l.name || l.id}</span><small>${(l.commands || []).length} çizgi</small></li>`,
      )
      .join("");
    ul.querySelectorAll(".mimar-layer-item").forEach((li) => {
      li.addEventListener("click", () => {
        const layer = getTasarimLayer(li.dataset.layerId);
        if (layer) {
          layer.visible = layer.visible === false;
          renderTasarimLayers();
          renderTasarimCanvas();
        }
      });
    });
  }

  function applySketchToLayer(commands, layerId = "eskiz") {
    const layer = getTasarimLayer(layerId);
    if (!layer) return;
    layer.commands = [...(layer.commands || []), ...(commands || [])];
    renderTasarimLayers();
    renderTasarimCanvas();
  }

  function syncTasarimNotesFromProject() {
    const notes = $("mimar-tasarim-notes");
    if (notes && tasarimProject) notes.value = tasarimProject.notes || "";
  }

  function syncTasarimProjectFromNotes() {
    if (tasarimProject && $("mimar-tasarim-notes")) {
      tasarimProject.notes = $("mimar-tasarim-notes").value || "";
    }
  }

  function setTasarimProject(project) {
    tasarimProject = project || defaultTasarimProject();
    tasarimRefRel = tasarimProject.reference_rel || "";
    syncTasarimNotesFromProject();
    renderTasarimLayers();
    if (tasarimRefRel) {
      const img = new Image();
      img.onload = () => {
        tasarimRefImage = img;
        renderTasarimCanvas();
      };
      img.onerror = () => {
        tasarimRefImage = null;
        renderTasarimCanvas();
      };
      img.src = tasarimRefUrl(tasarimRefRel);
    } else {
      tasarimRefImage = null;
      renderTasarimCanvas();
    }
  }

  async function ensureTasarimProject() {
    if (tasarimProject?.id) return tasarimProject;
    const res = await fetch(`${api()}/api/mimar/tasarim/project/new`, { method: "POST" });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
    setTasarimProject(j.project);
    void refreshTasarimProjectSelect();
    return tasarimProject;
  }

  async function refreshTasarimProjectSelect() {
    const sel = $("mimar-tasarim-project-select");
    if (!sel) return;
    try {
      const res = await fetch(`${api()}/api/mimar/tasarim/project/list`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      const cur = tasarimProject?.id || "";
      sel.innerHTML =
        '<option value="">— Proje seç —</option>' +
        (j.items || [])
          .map((it) => `<option value="${it.id}"${it.id === cur ? " selected" : ""}>${it.name || it.id}</option>`)
          .join("");
    } catch (_) {
      /* ignore */
    }
  }

  async function saveTasarimProject() {
    if (tasarimBusy) return;
    tasarimBusy = true;
    updateTasarimStatus("Kaydediliyor…");
    try {
      await ensureTasarimProject();
      syncTasarimProjectFromNotes();
      tasarimProject.reference_rel = tasarimRefRel || "";
      const res = await fetch(`${api()}/api/mimar/tasarim/project/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project: tasarimProject }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      setTasarimProject(j.project || tasarimProject);
      void refreshTasarimProjectSelect();
      flash(j.label_tr || "Proje kaydedildi.");
      updateTasarimStatus(j.label_tr || "Kaydedildi");
    } catch (e) {
      flash(String(e.message || e));
      updateTasarimStatus(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  async function loadTasarimProject(projectId) {
    const pid = (projectId || $("mimar-tasarim-project-select")?.value || "").trim();
    if (!pid) {
      flash("Proje seçin.");
      return;
    }
    if (tasarimBusy) return;
    tasarimBusy = true;
    updateTasarimStatus("Proje açılıyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/tasarim/project/load`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: pid }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      setTasarimProject(j.project);
      flash(`Proje açıldı: ${j.project?.name || pid}`);
      updateTasarimStatus(j.project?.name || pid);
    } catch (e) {
      flash(String(e.message || e));
      updateTasarimStatus(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  async function uploadTasarimReference(file) {
    if (!file || tasarimBusy) return;
    tasarimBusy = true;
    updateTasarimStatus("Referans yükleniyor…");
    try {
      await ensureTasarimProject();
      const fd = new FormData();
      fd.append("file", file, file.name);
      const res = await fetch(`${api()}/api/mimar/tasarim/reference/upload`, { method: "POST", body: fd });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      tasarimRefRel = j.rel || "";
      tasarimProject.reference_rel = tasarimRefRel;
      const img = new Image();
      img.onload = () => {
        tasarimRefImage = img;
        renderTasarimCanvas();
      };
      img.src = tasarimRefUrl(tasarimRefRel);
      flash("Referans yüklendi — «Resimden çiz» ile eskiz üretin.");
      updateTasarimStatus("Referans hazır");
    } catch (e) {
      flash(String(e.message || e));
      updateTasarimStatus(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  async function sketchFromReference() {
    if (!tasarimRefRel) {
      flash("Önce referans görsel yükleyin.");
      return;
    }
    if (tasarimBusy) return;
    tasarimBusy = true;
    updateTasarimStatus("Eskiz üretiliyor…");
    try {
      await ensureTasarimProject();
      const w = tasarimProject.width || 960;
      const h = tasarimProject.height || 540;
      const res = await fetch(`${api()}/api/mimar/tasarim/sketch/from-image`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: tasarimRefRel, width: w, height: h }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      const layer = getTasarimLayer("eskiz");
      if (layer) layer.commands = j.commands || [];
      renderTasarimLayers();
      renderTasarimCanvas();
      const src = j.source === "gemini" ? "Gemini" : "Kenar";
      flash(`${j.label_tr || "Eskiz hazır"} (${src})`);
      updateTasarimStatus(`${j.label_tr || "Eskiz"} · ${src}`);
    } catch (e) {
      flash(String(e.message || e));
      updateTasarimStatus(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  async function sketchFromChat() {
    if (tasarimBusy) return;
    const notes = $("mimar-tasarim-notes")?.value?.trim() || "";
    const handoff = deps.getChatHandoff?.() || {};
    const user = handoff.user || "";
    const assistant = handoff.assistant || deps.lastAssistantReply?.()?.trim() || "";
    if (!notes && !user && !assistant) {
      flash("Not alanına betimleme yazın veya önce sohbet edin.");
      return;
    }
    tasarimBusy = true;
    updateTasarimStatus("Sohbet handoff → tuval…");
    try {
      await ensureTasarimProject();
      const w = tasarimProject.width || 960;
      const h = tasarimProject.height || 540;
      const res = await fetch(`${api()}/api/mimar/tasarim/sketch/from-chat-handoff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user,
          assistant,
          notes,
          width: w,
          height: h,
          project_id: tasarimProject.id || "",
        }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      if (j.project) setTasarimProject(j.project);
      else {
        const layer = getTasarimLayer("eskiz");
        if (layer) layer.commands = j.commands || [];
        renderTasarimLayers();
        renderTasarimCanvas();
      }
      const src = j.source === "gemini" ? "Gemini" : "Temel şekil";
      flash(j.label_tr || "Sohbetten çizim hazır.");
      updateTasarimStatus(`${j.label_tr || "Handoff"} · ${src}`);
    } catch (e) {
      flash(String(e.message || e));
      updateTasarimStatus(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  async function regenerateTasarimProject() {
    const pid = tasarimProject?.id || $("mimar-tasarim-project-select")?.value?.trim();
    if (!pid) {
      flash("Önce proje kaydedin veya listeden seçin.");
      return;
    }
    if (tasarimBusy) return;
    tasarimBusy = true;
    updateTasarimStatus("Kayıtlı mimari yenileniyor…");
    try {
      const res = await fetch(`${api()}/api/mimar/tasarim/project/regenerate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: pid }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      setTasarimProject(j.project);
      flash(j.label_tr || "Proje yenilendi.");
      updateTasarimStatus(j.label_tr || "Yeniden üretildi");
    } catch (e) {
      flash(String(e.message || e));
      updateTasarimStatus(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  async function duplicateTasarimProject() {
    const pid = tasarimProject?.id || $("mimar-tasarim-project-select")?.value?.trim();
    if (!pid) {
      flash("Kopyalanacak proje seçin.");
      return;
    }
    if (tasarimBusy) return;
    tasarimBusy = true;
    try {
      const res = await fetch(`${api()}/api/mimar/tasarim/project/duplicate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_id: pid }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(typeof j.detail === "string" ? j.detail : `HTTP ${res.status}`);
      setTasarimProject(j.project);
      void refreshTasarimProjectSelect();
      flash(j.label_tr || "Proje kopyalandı.");
      updateTasarimStatus(j.project?.name || "Kopya");
    } catch (e) {
      flash(String(e.message || e));
    } finally {
      tasarimBusy = false;
    }
  }

  function exportTasarimPng() {
    const pid = tasarimProject?.id || $("mimar-tasarim-project-select")?.value?.trim();
    if (!pid) {
      flash("Önce projeyi kaydedin.");
      return;
    }
    const a = document.createElement("a");
    a.href = `${api()}/api/mimar/tasarim/project/export-png?project_id=${encodeURIComponent(pid)}&t=${Date.now()}`;
    a.download = `mimar-${pid}.png`;
    a.click();
    flash("PNG indiriliyor…");
  }

  function wireTasarimPen() {
    const canvas = $("mimar-tasarim-canvas");
    if (!canvas || canvas.dataset.penWired === "1") return;
    canvas.dataset.penWired = "1";
    canvas.addEventListener("mousedown", (ev) => {
      if (!tasarimProject) return;
      tasarimPenDown = true;
      tasarimPenLast = canvasPoint(canvas, ev);
    });
    canvas.addEventListener("mousemove", (ev) => {
      if (!tasarimPenDown || !tasarimPenLast) return;
      const p = canvasPoint(canvas, ev);
      const layer = getTasarimLayer("el");
      if (layer) {
        layer.commands.push({
          type: "line",
          x1: tasarimPenLast.x,
          y1: tasarimPenLast.y,
          x2: p.x,
          y2: p.y,
          color: "#3794ff",
          width: 2,
        });
      }
      tasarimPenLast = p;
      renderTasarimCanvas();
    });
    const stopPen = () => {
      if (tasarimPenDown) renderTasarimLayers();
      tasarimPenDown = false;
      tasarimPenLast = null;
    };
    canvas.addEventListener("mouseup", stopPen);
    canvas.addEventListener("mouseleave", stopPen);
  }

  function initTasarimCanvas() {
    if (canvasInited) {
      renderTasarimCanvas();
      return;
    }
    canvasInited = true;
    if (!tasarimProject) setTasarimProject(defaultTasarimProject());
    wireTasarimPen();
    renderTasarimCanvas();
    void refreshTasarimProjectSelect();
  }

  function wireTasarimPage() {
    $("btn-mimar-tasarim-from-image")?.addEventListener("click", () => void sketchFromReference());
    $("btn-mimar-tasarim-from-chat")?.addEventListener("click", () => void sketchFromChat());
    $("btn-mimar-tasarim-save")?.addEventListener("click", () => void saveTasarimProject());
    $("btn-mimar-tasarim-regenerate")?.addEventListener("click", () => void regenerateTasarimProject());
    $("btn-mimar-tasarim-duplicate")?.addEventListener("click", () => void duplicateTasarimProject());
    $("btn-mimar-tasarim-export")?.addEventListener("click", () => exportTasarimPng());
    $("btn-mimar-tasarim-new")?.addEventListener("click", () => {
      setTasarimProject(defaultTasarimProject());
      tasarimRefRel = "";
      tasarimRefImage = null;
      void ensureTasarimProject();
      flash("Yeni tuval — referans veya betimleme ile başlayın.");
      updateTasarimStatus("Yeni proje");
    });
    $("btn-mimar-tasarim-load")?.addEventListener("click", () => void loadTasarimProject());
    $("mimar-tasarim-ref-file")?.addEventListener("change", (ev) => {
      const f = ev.target.files?.[0];
      if (f) void uploadTasarimReference(f);
      ev.target.value = "";
    });
  }

  function wireAll() {
    if ($("page-mimar")?.dataset.mimarWired === "1") return;
    if ($("page-mimar")) $("page-mimar").dataset.mimarWired = "1";
    wireMimarViewTabs();
    wireFotoPage();
    wireSanatPage();
    wireTasarimPage();
    setMimarTab("fotograf");
  }

  global.RuzgarMimarAtolye = {
    init(d) {
      deps = d || {};
      wireAll();
      if (deps.getCurrentMode?.() === "mimar" || deps.getCurrentMode?.() === "okuma") syncMimarLayout(true);
    },
    setMimarTab,
    syncMimarLayout,
    load() {
      void refreshFotoList();
      void refreshSanatList();
    },
  };
})(window);
