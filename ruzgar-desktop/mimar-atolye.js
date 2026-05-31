/**
 * Mimar Atölyesi — 3 bağımsız sayfa: fotoğraf / sanat / tasarım.
 */
(function initMimarAtolyeModule(global) {
  let deps = {};
  let fotoItems = [];
  let sanatItems = [];
  let activeFotoId = null;
  let activeSanatId = null;

  function $(id) {
    return document.getElementById(id);
  }
  function flash(msg) {
    if (deps.flash) deps.flash(msg);
  }

  function normalizeTab(tab) {
    let t = String(tab || "fotograf").trim() || "fotograf";
    if (t === "sohbet" || t === "icerik") t = "fotograf";
    if (t === "kroki") t = "tasarim";
    return t;
  }

  function focusChatInput() {
    $("msg-input")?.focus();
  }

  function setMimarTab(tab) {
    const t = normalizeTab(tab);
    document.body.dataset.mimarTab = t;
    document.querySelectorAll(".mimar-view-tab").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.mimarTab === t);
    });
    const wb = $("mimar-workbench");
    if (wb) {
      wb.className = `mimar-workbench mimar-workbench--${t}`;
    }
    ["fotograf", "resim-sanat", "tasarim"].forEach((key) => {
      const node = $(`mimar-panel-${key}`);
      if (!node) return;
      node.hidden = t !== key;
    });
    if (t === "tasarim") initTasarimCanvas();
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
    const labels = {
      fotograf: "Fotoğraf",
      "resim-sanat": "Resim · Sanat",
      tasarim: "Tasarım",
    };
    bar.querySelectorAll(".mimar-view-tab").forEach((btn) => {
      btn.addEventListener("click", () => {
        setMimarTab(btn.dataset.mimarTab || "fotograf");
        flash(`Mimar: ${labels[btn.dataset.mimarTab] || btn.dataset.mimarTab}`);
      });
    });
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
          `<li class="mimar-foto-thumb${it.id === activeFotoId ? " is-active" : ""}" data-foto-id="${it.id}"><img src="${it.url}" alt="${it.name}" /></li>`,
      )
      .join("");
    ul.querySelectorAll(".mimar-foto-thumb").forEach((li) => {
      li.addEventListener("click", () => selectFoto(li.dataset.fotoId));
    });
  }

  function selectFoto(id) {
    activeFotoId = id;
    const item = fotoItems.find((x) => x.id === id);
    const img = $("mimar-foto-preview-img");
    const hint = document.querySelector(".mimar-foto-preview-hint");
    if (item && img) {
      img.src = item.url;
      img.hidden = false;
      if (hint) hint.hidden = true;
      $("mimar-foto-status").textContent = item.name;
    }
    renderFotoThumbs();
  }

  function addFotoFiles(fileList) {
    const files = [...(fileList || [])].filter((f) => f.type.startsWith("image/"));
    if (!files.length) {
      flash("Geçerli görsel seçilmedi.");
      return;
    }
    files.forEach((f) => {
      const url = URL.createObjectURL(f);
      fotoItems.push({ id: `f${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, name: f.name, url });
    });
    renderFotoThumbs();
    if (!activeFotoId && fotoItems.length) selectFoto(fotoItems[fotoItems.length - 1].id);
    flash(`${files.length} fotoğraf eklendi.`);
  }

  function renderSanatGallery() {
    const gal = $("mimar-sanat-gallery");
    if (!gal) return;
    const tiles = sanatItems
      .map(
        (it) =>
          `<button type="button" class="mimar-sanat-tile${it.id === activeSanatId ? " is-active" : ""}" data-sanat-id="${it.id}"><img src="${it.url}" alt="${it.name}" /></button>`,
      )
      .join("");
    gal.innerHTML = `${tiles}<label class="mimar-sanat-tile mimar-sanat-tile-add"><span>+ Eser ekle</span><input type="file" id="mimar-sanat-file" hidden accept="image/*,.pdf" /></label>`;
    gal.querySelectorAll(".mimar-sanat-tile[data-sanat-id]").forEach((btn) => {
      btn.addEventListener("click", () => selectSanat(btn.dataset.sanatId));
    });
    $("mimar-sanat-file")?.addEventListener("change", (ev) => {
      addSanatFiles(ev.target.files);
      ev.target.value = "";
    });
  }

  function selectSanat(id) {
    activeSanatId = id;
    const item = sanatItems.find((x) => x.id === id);
    const prev = $("mimar-sanat-preview");
    if (!prev || !item) return;
    prev.innerHTML = `<img src="${item.url}" alt="${item.name}" />`;
    renderSanatGallery();
  }

  function addSanatFiles(fileList) {
    const files = [...(fileList || [])];
    if (!files.length) return;
    files.forEach((f) => {
      const url = f.type.startsWith("image/") ? URL.createObjectURL(f) : "";
      sanatItems.push({ id: `s${Date.now()}-${Math.random().toString(36).slice(2, 7)}`, name: f.name, url });
    });
    renderSanatGallery();
    if (!activeSanatId && sanatItems.length) selectSanat(sanatItems[sanatItems.length - 1].id);
    flash(`${files.length} eser galeriye eklendi.`);
  }

  let canvasInited = false;
  function initTasarimCanvas() {
    if (canvasInited) return;
    const canvas = $("mimar-tasarim-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    canvasInited = true;
    ctx.fillStyle = "#1e1e1e";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = "#555";
    ctx.strokeRect(40, 40, canvas.width - 80, canvas.height - 80);
    ctx.fillStyle = "#666";
    ctx.font = "14px Segoe UI";
    ctx.fillText("Tasarım tuvali — Faz 4 çizim motoru", 52, 68);
  }

  function wireFotoPage() {
    $("mimar-foto-file")?.addEventListener("change", (ev) => {
      addFotoFiles(ev.target.files);
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
      addFotoFiles(ev.dataTransfer?.files);
    });
    ["btn-mimar-foto-moderasyon", "btn-mimar-foto-restore", "btn-mimar-foto-tts", "btn-mimar-foto-speak"].forEach(
      (id) => {
        $(id)?.addEventListener("click", () => flash("Faz 4 — bu araç henüz bağlanmadı."));
      },
    );
  }

  function wireSanatPage() {
    renderSanatGallery();
    ["btn-mimar-sanat-tani", "btn-mimar-sanat-ciz", "btn-mimar-sanat-kopya"].forEach((id) => {
      $(id)?.addEventListener("click", () => flash("Faz 4 — sanat aracı henüz bağlanmadı."));
    });
  }

  function wireTasarimPage() {
    ["btn-mimar-tasarim-from-image", "btn-mimar-tasarim-from-chat", "btn-mimar-tasarim-archives"].forEach((id) => {
      $(id)?.addEventListener("click", () => flash("Faz 4 — tasarım aracı henüz bağlanmadı."));
    });
    $("mimar-tasarim-ref-file")?.addEventListener("change", (ev) => {
      const f = ev.target.files?.[0];
      if (!f) return;
      flash(`Referans: ${f.name} — Faz 4 ile tuvalde kullanılacak.`);
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
      renderFotoThumbs();
      renderSanatGallery();
    },
  };
})(window);
