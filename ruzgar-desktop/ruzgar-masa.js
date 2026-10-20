/* Ana Motor çalışma yüzeyi — tek sahne, çok yetenek. Sohbet ve motor listesine dokunmaz. */
(function () {
  const KEY = "ruzgarMasaDeskV1";
  const COLS = "ABCDEFGHIJKL".split("");
  const ROWS = 28;
  const BW = 1600;
  const BH = 1000;
  const YETENEK_AD = {
    sohbet: "Sohbet",
    belge: "Belge",
    tablo: "Tablo",
    cizim: "Çizim",
    sunum: "Sunum",
    medya: "Medya",
    foto: "Foto",
    notlar: "Notlar",
    kod: "Kod",
    ses: "Ses",
    okuma: "Okuma",
    web: "Web",
  };
  const IKINCIL = { notlar: 1, kod: 1, ses: 1, okuma: 1, web: 1 };

  const root = document.getElementById("ruzgar-masa");
  if (!root) return;

  const tools = document.getElementById("ruzgar-masa-tools");
  const statusEl = document.getElementById("ruzgar-masa-durum");
  const chipEl = document.getElementById("ruzgar-masa-chip");
  const belge = document.getElementById("ruzgar-masa-belge");
  const sheetWrap = document.getElementById("ruzgar-masa-sheet");
  const formulaInput = document.getElementById("ruzgar-masa-formula-input");
  const cellName = document.getElementById("ruzgar-masa-cell-name");
  const canvas = document.getElementById("ruzgar-masa-canvas");
  const slidesEl = document.getElementById("ruzgar-masa-slides");
  const slideTitle = document.getElementById("ruzgar-masa-slide-title");
  const slideBody = document.getElementById("ruzgar-masa-slide-body");
  const slidePreview = document.getElementById("ruzgar-masa-slide-preview");
  const slidePreviewTitle = document.getElementById("ruzgar-masa-slide-preview-title");
  const slidePreviewBody = document.getElementById("ruzgar-masa-slide-preview-body");
  const present = document.getElementById("ruzgar-masa-present");
  const presentTitle = document.getElementById("ruzgar-masa-present-title");
  const presentBody = document.getElementById("ruzgar-masa-present-body");
  const medyaRoot = document.getElementById("ruzgar-masa-medya");
  const medyaEmpty = document.getElementById("ruzgar-masa-medya-empty");
  const medyaView = document.getElementById("ruzgar-masa-medya-view");
  const medyaFile = document.getElementById("ruzgar-masa-medya-file");
  const notlarEl = document.getElementById("ruzgar-masa-notlar");
  const gorevlerEl = document.getElementById("ruzgar-masa-gorevler");
  const kodEl = document.getElementById("ruzgar-masa-kod");
  const kodDil = document.getElementById("ruzgar-masa-kod-dil");
  const kodSatir = document.getElementById("ruzgar-masa-kod-satir");
  const sesRoot = document.getElementById("ruzgar-masa-ses");
  const sesEmpty = document.getElementById("ruzgar-masa-ses-empty");
  const sesView = document.getElementById("ruzgar-masa-ses-view");
  const sesFile = document.getElementById("ruzgar-masa-ses-file");
  const sesPlayer = document.getElementById("ruzgar-masa-ses-player");
  const sesAd = document.getElementById("ruzgar-masa-ses-ad");
  const sesKayitBtn = document.getElementById("ruzgar-masa-ses-kayit");
  const okumaFile = document.getElementById("ruzgar-masa-okuma-file");
  const okumaAd = document.getElementById("ruzgar-masa-okuma-ad");
  const okumaText = document.getElementById("ruzgar-masa-okuma-text");
  const okumaPdf = document.getElementById("ruzgar-masa-okuma-pdf");
  const okumaEmpty = document.getElementById("ruzgar-masa-okuma-empty");
  const webForm = document.getElementById("ruzgar-masa-web-form");
  const webUrl = document.getElementById("ruzgar-masa-web-url");
  const webFrame = document.getElementById("ruzgar-masa-web-frame");
  const webPane = document.querySelector('.ruzgar-masa-pane[data-pane="web"] .ruzgar-masa-web');
  const webYenile = document.getElementById("ruzgar-masa-web-yenile");
  const fotoRoot = document.getElementById("ruzgar-masa-foto");
  const fotoRef = document.getElementById("ruzgar-masa-foto-ref");
  const fotoRefImg = document.getElementById("ruzgar-masa-foto-ref-img");
  const fotoRefEmpty = document.getElementById("ruzgar-masa-foto-ref-empty");
  const fotoRefFile = document.getElementById("ruzgar-masa-foto-ref-file");
  const fotoKok = document.getElementById("ruzgar-masa-foto-kok");
  const fotoTara = document.getElementById("ruzgar-masa-foto-tara");
  const fotoEsle = document.getElementById("ruzgar-masa-foto-esle");
  const fotoDurum = document.getElementById("ruzgar-masa-foto-durum");
  const fotoGrid = document.getElementById("ruzgar-masa-foto-grid");
  const fotoSayi = document.getElementById("ruzgar-masa-foto-sayi");
  const fotoEmpty = document.getElementById("ruzgar-masa-foto-empty");

  const state = {
    mode: "belge",
    belgeHtml: "",
    sheet: blankSheet(),
    sel: { r: 0, c: 0 },
    slides: [{ title: "Başlık", body: "Metin", bg: "#1c1a16", fg: "#f7f4ec" }],
    slideIndex: 0,
    draw: { tool: "kalem", color: "#1a1a1c", size: 4 },
    medya: { name: "", kind: "", url: "" },
    foto: { refName: "", refUrl: "", refFile: null, kok: "", sayi: 0, ornek: [], katman: {}, sonuclar: [] },
    notlar: "",
    gorevler: [],
    kod: "",
    kodDil: "text",
    ses: { name: "", url: "" },
    okuma: { name: "", kind: "", text: "", url: "" },
    web: "",
    sesRec: null,
  };

  let saveTimer = 0;
  let flashTimer = 0;
  let ctx = canvas.getContext("2d");
  let paperReady = false;
  let sayfa = "sohbet";
  let sahneTimer = 0;
  let drawing = false;
  let lastPt = null;
  let shapeStart = null;
  let snap = null;

  function blankSheet() {
    return Array.from({ length: ROWS }, function () {
      return Array.from({ length: COLS.length }, function () { return ""; });
    });
  }

  function setStatus(text, tone) {
    if (!statusEl) return;
    statusEl.textContent = text || "";
    statusEl.classList.toggle("is-ok", tone === "ok");
    statusEl.classList.toggle("is-busy", tone === "busy");
  }

  function setChip(kind) {
    if (!chipEl) return;
    const ad = YETENEK_AD[kind] || YETENEK_AD[state.mode] || "Yüzey";
    chipEl.textContent = ad;
  }

  function flashYuzey() {
    root.classList.add("is-flash");
    clearTimeout(flashTimer);
    flashTimer = setTimeout(function () {
      root.classList.remove("is-flash");
    }, 420);
  }

  function scheduleSave() {
    setStatus("Yazılıyor…", "busy");
    clearTimeout(saveTimer);
    saveTimer = setTimeout(persist, 350);
  }

  function persist() {
    const payload = {
      mode: state.mode,
      belgeHtml: belge.innerHTML,
      sheet: state.sheet,
      slides: state.slides,
      slideIndex: state.slideIndex,
      ink: !!state.ink,
      drawPng: "",
      notlar: notlarEl ? notlarEl.value : state.notlar,
      gorevler: state.gorevler,
      kod: kodEl ? kodEl.value : state.kod,
      kodDil: kodDil ? kodDil.value : state.kodDil,
      web: state.web,
      fotoKok: state.foto.kok || "",
      okumaText: state.okuma && state.okuma.kind === "text" ? state.okuma.text : "",
      okumaName: state.okuma && state.okuma.kind === "text" ? state.okuma.name : "",
    };
    try {
      if (state.ink && canvas.width) payload.drawPng = canvas.toDataURL("image/png");
    } catch (err) {
      payload.drawPng = "";
    }
    try {
      localStorage.setItem(KEY, JSON.stringify(payload));
      setStatus("Kaydedildi", "ok");
      syncChip();
    } catch (err) {
      payload.drawPng = "";
      try {
        localStorage.setItem(KEY, JSON.stringify(payload));
        setStatus("Kaydedildi (çizim büyük)");
      } catch (err2) {
        setStatus("Kayıt sığmadı");
      }
    }
    syncSahne();
  }

  function load() {
    let data = null;
    try {
      data = JSON.parse(localStorage.getItem(KEY) || "null");
    } catch (err) {
      data = null;
    }
    if (!data) return;
    if (typeof data.belgeHtml === "string") belge.innerHTML = data.belgeHtml;
    if (Array.isArray(data.sheet)) {
      state.sheet = blankSheet();
      data.sheet.forEach(function (row, r) {
        if (!state.sheet[r] || !Array.isArray(row)) return;
        row.forEach(function (cell, c) {
          if (state.sheet[r][c] !== undefined && typeof cell === "string") state.sheet[r][c] = cell;
        });
      });
    }
    if (Array.isArray(data.slides) && data.slides.length) {
      state.slides = data.slides.filter(function (s) { return s && typeof s.title === "string"; });
      if (!state.slides.length) state.slides = [{ title: "Başlık", body: "", bg: "#1c1a16", fg: "#f7f4ec" }];
    }
    state.slideIndex = Math.min(state.slides.length - 1, Math.max(0, data.slideIndex || 0));
    if (data.mode && YETENEK_AD[data.mode] && data.mode !== "sohbet") state.mode = data.mode;
    state.ink = data.ink === true;
    state._png = state.ink && typeof data.drawPng === "string" ? data.drawPng : "";
    if (typeof data.notlar === "string" && notlarEl) {
      state.notlar = data.notlar;
      notlarEl.value = data.notlar;
    }
    if (Array.isArray(data.gorevler)) {
      state.gorevler = data.gorevler
        .filter(function (g) { return g && typeof g.text === "string"; })
        .slice(0, 80)
        .map(function (g) { return { text: String(g.text).slice(0, 200), done: !!g.done }; });
    }
    if (typeof data.kod === "string" && kodEl) {
      state.kod = data.kod;
      kodEl.value = data.kod;
    }
    if (typeof data.kodDil === "string" && kodDil) {
      state.kodDil = data.kodDil;
      kodDil.value = data.kodDil;
    }
    if (typeof data.web === "string") state.web = data.web;
    if (typeof data.fotoKok === "string" && data.fotoKok) {
      state.foto.kok = data.fotoKok;
      if (fotoKok) fotoKok.value = data.fotoKok;
    }
    if (typeof data.okumaText === "string" && data.okumaText) {
      state.okuma = {
        name: String(data.okumaName || "not.txt").slice(0, 180),
        kind: "text",
        text: data.okumaText.slice(0, 200000),
        url: "",
      };
    }
  }

  function showMode(mode, opts) {
    state.mode = mode;
    root.dataset.yetenek = mode;
    root.classList.toggle("has-ikincil", !!IKINCIL[mode]);
    root.querySelectorAll("[data-masa]").forEach(function (btn) {
      const on = btn.getAttribute("data-masa") === mode;
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    root.querySelectorAll("[data-pane]").forEach(function (pane) {
      const on = pane.getAttribute("data-pane") === mode;
      pane.classList.toggle("is-on", on);
      if (on) pane.removeAttribute("hidden");
      else pane.setAttribute("hidden", "");
    });
    renderTools();
    if (mode === "cizim") requestAnimationFrame(ensurePaper);
    if (mode === "sunum") {
      renderSlides();
      syncSlidePreview();
    }
    if (mode === "medya") paintMedya();
    if (mode === "foto") {
      paintFoto();
      fotoDurumYenile();
    }
    if (mode === "notlar") paintGorevler();
    if (mode === "kod") syncKodSatir();
    if (mode === "ses") paintSes();
    if (mode === "okuma") paintOkuma();
    if (mode === "web") paintWeb();
    syncChip();
    if (!opts || !opts.keep) scheduleSave();
    focusYetenek(mode);
  }

  function focusYetenek(mode) {
    try {
      if (mode === "belge" && belge) belge.focus({ preventScroll: true });
      else if (mode === "tablo" && formulaInput) formulaInput.focus({ preventScroll: true });
      else if (mode === "cizim") {
        const wrap = document.getElementById("ruzgar-masa-canvas-wrap");
        if (wrap) wrap.focus({ preventScroll: true });
      } else if (mode === "sunum" && slideTitle) slideTitle.focus({ preventScroll: true });
      else if (mode === "medya" && medyaRoot) medyaRoot.focus({ preventScroll: true });
      else if (mode === "foto" && fotoKok) fotoKok.focus({ preventScroll: true });
      else if (mode === "notlar" && notlarEl) notlarEl.focus({ preventScroll: true });
      else if (mode === "kod" && kodEl) kodEl.focus({ preventScroll: true });
      else if (mode === "ses" && sesRoot) sesRoot.focus({ preventScroll: true });
      else if (mode === "web" && webUrl) webUrl.focus({ preventScroll: true });
    } catch (err) { /* odak zorunlu değil */ }
  }

  function syncChip() {
    const kind = sayfa === "sohbet" ? "sohbet" : state.mode;
    setChip(kind);
  }

  function syncSlidePreview() {
    const slide = currentSlide();
    if (!slidePreview || !slide) return;
    const bg = toHex(slide.bg, "#1c1a16");
    const fg = toHex(slide.fg, "#f7f4ec");
    slidePreview.style.background = bg;
    slidePreview.style.color = fg;
    if (slidePreviewTitle) slidePreviewTitle.textContent = slide.title || "Başlık";
    if (slidePreviewBody) slidePreviewBody.textContent = slide.body || "Metin";
  }

  function kopruAracHtml() {
    return (
      '<label class="ruzgar-masa-kopru-label">Gönder ' +
      '<select id="ruzgar-masa-kopru" aria-label="Motora gönder">' +
      '<option value="">—</option>' +
      '<option value="tercume">Tercüme</option>' +
      '<option value="programlama">Programlama</option>' +
      '<option value="ses">Ses</option>' +
      '<option value="video">Video</option>' +
      '<option value="hafiza">Hafıza</option>' +
      '<option value="okuma">Okuma</option>' +
      "</select></label>"
    );
  }

  function renderTools() {
    const mode = state.mode;
    if (mode === "belge") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Belge</span>' +
        '<button type="button" data-cmd="bold" title="Kalın"><b>B</b></button>' +
        '<button type="button" data-cmd="italic" title="İtalik"><i>I</i></button>' +
        '<button type="button" data-cmd="underline" title="Altı çizili"><u>U</u></button>' +
        '<button type="button" data-cmd="h2">Başlık</button>' +
        '<button type="button" data-cmd="insertUnorderedList">Madde</button>' +
        '<button type="button" data-cmd="insertOrderedList">Numara</button>' +
        '<button type="button" data-cmd="justifyLeft">Sola</button>' +
        '<button type="button" data-cmd="justifyCenter">Ortala</button>' +
        '<button type="button" data-cmd="justifyRight">Sağa</button>' +
        '<button type="button" id="ruzgar-masa-belge-img-btn" title="Resim ekle">Resim</button>' +
        '<button type="button" id="ruzgar-masa-belge-tablo-btn" title="Tablo ekle">Tablo</button>' +
        kopruAracHtml();
    } else if (mode === "tablo") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Tablo</span>' +
        '<span>=A1+B1 · =TOPLA(A1:A8) · =ORTALAMA · =MİN · =MAK</span>' +
        kopruAracHtml();
    } else if (mode === "cizim") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Çizim</span>' +
        '<button type="button" data-tool="kalem" class="is-on">Kalem</button>' +
        '<button type="button" data-tool="silgi">Silgi</button>' +
        '<button type="button" data-tool="cizgi">Çizgi</button>' +
        '<button type="button" data-tool="kutu">Kutu</button>' +
        '<button type="button" data-tool="daire">Daire</button>' +
        '<label>Renk <input id="ruzgar-masa-color" type="color" value="#1a1a1c"></label>' +
        '<label>Kalınlık <input id="ruzgar-masa-size" type="range" min="1" max="32" value="4"></label>' +
        '<button type="button" id="ruzgar-masa-undo">Geri al</button>' +
        '<button type="button" id="ruzgar-masa-clear">Temizle</button>';
      const color = document.getElementById("ruzgar-masa-color");
      const size = document.getElementById("ruzgar-masa-size");
      color.value = state.draw.color;
      size.value = String(state.draw.size);
      markTool(state.draw.tool);
    } else if (mode === "medya") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Medya</span>' +
        '<button type="button" id="ruzgar-masa-medya-pick">Dosya seç</button>' +
        '<button type="button" id="ruzgar-masa-medya-clear">Temizle</button>' +
        '<span>Önizleme · ağır kesim Video motorunda</span>' +
        kopruAracHtml();
    } else if (mode === "foto") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Foto</span>' +
        '<button type="button" id="ruzgar-masa-foto-ref-pick">Referans</button>' +
        '<button type="button" id="ruzgar-masa-foto-tara-tool">Katalog tara</button>' +
        '<button type="button" id="ruzgar-masa-foto-katman-tool">Katmanları kur</button>' +
        '<button type="button" id="ruzgar-masa-foto-esle-tool">Yüz ara</button>' +
        '<span>Yerel Haar · OpenCV</span>';
    } else if (mode === "notlar") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Notlar</span>' +
        '<button type="button" id="ruzgar-masa-gorev-ekle-tool">Görev ekle</button>' +
        '<button type="button" id="ruzgar-masa-notlar-temizle">Notları temizle</button>' +
        kopruAracHtml();
    } else if (mode === "kod") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Kod</span>' +
        '<button type="button" id="ruzgar-masa-kod-temizle">Temizle</button>' +
        '<span>Çalıştırma kapalı</span>' +
        kopruAracHtml();
    } else if (mode === "ses") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Ses</span>' +
        '<button type="button" id="ruzgar-masa-ses-pick">Dosya seç</button>' +
        '<button type="button" id="ruzgar-masa-ses-rec-tool">Kayıt</button>' +
        '<button type="button" id="ruzgar-masa-ses-clear">Temizle</button>' +
        '<span>Stüdyo Ses motorunda</span>' +
        kopruAracHtml();
    } else if (mode === "okuma") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Okuma</span>' +
        '<button type="button" id="ruzgar-masa-okuma-pick">Dosya aç</button>' +
        '<button type="button" id="ruzgar-masa-okuma-clear">Temizle</button>' +
        '<span>TXT · MD · PDF</span>' +
        kopruAracHtml();
    } else if (mode === "web") {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Web</span>' +
        '<button type="button" id="ruzgar-masa-web-go">Aç</button>' +
        '<button type="button" id="ruzgar-masa-web-external">Tarayıcıda aç</button>' +
        '<span>Önizleme · bazı siteler çerçeveyi engeller</span>' +
        kopruAracHtml();
    } else {
      tools.innerHTML =
        '<span class="ruzgar-masa-tools-hint">Sunum</span>' +
        '<button type="button" id="ruzgar-masa-add-slide">Slayt ekle</button>' +
        '<button type="button" id="ruzgar-masa-del-slide">Slaytı sil</button>' +
        '<label>Zemin <input id="ruzgar-masa-bg" type="color" value="#1c1a16"></label>' +
        '<label>Yazı <input id="ruzgar-masa-fg" type="color" value="#f7f4ec"></label>' +
        '<button type="button" id="ruzgar-masa-play" class="ruzgar-masa-btn-accent">Sun</button>' +
        kopruAracHtml();
      const slide = currentSlide();
      document.getElementById("ruzgar-masa-bg").value = toHex(slide.bg, "#1c1a16");
      document.getElementById("ruzgar-masa-fg").value = toHex(slide.fg, "#f7f4ec");
    }
    const kopruSel = document.getElementById("ruzgar-masa-kopru");
    if (kopruSel) {
      kopruSel.onchange = function () {
        const hedef = kopruSel.value;
        kopruSel.value = "";
        if (hedef) yuzeyMotorGonder(hedef);
      };
    }
  }

  function toHex(value, fallback) {
    return /^#[0-9a-fA-F]{6}$/.test(value || "") ? value : fallback;
  }

  function markTool(name) {
    tools.querySelectorAll("[data-tool]").forEach(function (btn) {
      btn.classList.toggle("is-on", btn.getAttribute("data-tool") === name);
    });
  }

  tools.addEventListener("mousedown", function (ev) {
    if (state.mode === "belge" && ev.target.closest("button")) ev.preventDefault();
  });

  tools.addEventListener("click", function (ev) {
    const cmdBtn = ev.target.closest("[data-cmd]");
    if (cmdBtn && state.mode === "belge") {
      belge.focus();
      const cmd = cmdBtn.getAttribute("data-cmd");
      if (cmd === "h2") document.execCommand("formatBlock", false, "h2");
      else document.execCommand(cmd, false, null);
      scheduleSave();
      return;
    }
    const toolBtn = ev.target.closest("[data-tool]");
    if (toolBtn) {
      state.draw.tool = toolBtn.getAttribute("data-tool");
      markTool(state.draw.tool);
      return;
    }
    if (ev.target.id === "ruzgar-masa-undo") undoDraw();
    if (ev.target.id === "ruzgar-masa-clear") clearPaper();
    if (ev.target.id === "ruzgar-masa-add-slide") addSlide();
    if (ev.target.id === "ruzgar-masa-del-slide") deleteSlide();
    if (ev.target.id === "ruzgar-masa-play") startPresent();
    if (ev.target.id === "ruzgar-masa-belge-img-btn") {
      const inp = document.getElementById("ruzgar-masa-belge-img");
      if (inp) inp.click();
      return;
    }
    if (ev.target.id === "ruzgar-masa-belge-tablo-btn") {
      belgeTabloEkle(3, 3);
      return;
    }
    if (ev.target.id === "ruzgar-masa-medya-pick" && medyaFile) medyaFile.click();
    if (ev.target.id === "ruzgar-masa-medya-clear") medyaTemizle();
    if (ev.target.id === "ruzgar-masa-foto-ref-pick") void fotoReferansSecDialog();
    if (ev.target.id === "ruzgar-masa-foto-tara-tool") fotoKatalogTara();
    if (ev.target.id === "ruzgar-masa-foto-katman-tool") void fotoKatmanKur();
    if (ev.target.id === "ruzgar-masa-foto-esle-tool") void fotoYuzAra();
    if (ev.target.id === "ruzgar-masa-gorev-ekle-tool") gorevEkle();
    if (ev.target.id === "ruzgar-masa-notlar-temizle") notlarTemizle();
    if (ev.target.id === "ruzgar-masa-kod-temizle") kodTemizle();
    if (ev.target.id === "ruzgar-masa-ses-pick" && sesFile) sesFile.click();
    if (ev.target.id === "ruzgar-masa-ses-rec-tool") sesKayitToggle();
    if (ev.target.id === "ruzgar-masa-ses-clear") sesTemizle();
    if (ev.target.id === "ruzgar-masa-okuma-pick" && okumaFile) okumaFile.click();
    if (ev.target.id === "ruzgar-masa-okuma-clear") okumaTemizle();
    if (ev.target.id === "ruzgar-masa-web-go") webAc(webUrl && webUrl.value);
    if (ev.target.id === "ruzgar-masa-web-external") webDisarida();
  });

  tools.addEventListener("input", function (ev) {
    if (ev.target.id === "ruzgar-masa-color") state.draw.color = ev.target.value;
    if (ev.target.id === "ruzgar-masa-size") state.draw.size = Number(ev.target.value) || 4;
    if (ev.target.id === "ruzgar-masa-bg" || ev.target.id === "ruzgar-masa-fg") {
      const slide = currentSlide();
      if (ev.target.id === "ruzgar-masa-bg") slide.bg = ev.target.value;
      else slide.fg = ev.target.value;
      renderSlides();
      syncSlidePreview();
      scheduleSave();
    }
  });

  root.querySelector(".ruzgar-masa-tabs").addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-masa]");
    if (!btn) return;
    masaSayfa(btn.getAttribute("data-masa"));
  });

  belge.addEventListener("input", scheduleSave);

  function belgeInsertNode(node) {
    belge.focus();
    const sel = window.getSelection();
    let range = null;
    if (sel && sel.rangeCount && belge.contains(sel.anchorNode)) {
      range = sel.getRangeAt(0);
      range.deleteContents();
      range.insertNode(node);
    } else {
      belge.appendChild(node);
      range = document.createRange();
      range.selectNodeContents(belge);
      range.collapse(false);
    }
    const after = document.createRange();
    after.setStartAfter(node);
    after.collapse(true);
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(after);
    }
    scheduleSave();
    flashYuzey();
  }

  function belgeResimEkle(file) {
    if (!file) return "Dosya yok.";
    if (String(file.type || "").indexOf("image/") !== 0) return "Yalnız resim.";
    if (file.size > 12 * 1024 * 1024) return "Belge resmi 12 MB üstü olamaz.";
    const reader = new FileReader();
    reader.onload = function () {
      const src = String(reader.result || "");
      if (!src || src.length > 2_500_000) {
        setStatus("Resim belgede çok büyük — küçültülüyor…", "busy");
      }
      const img = new Image();
      img.onload = function () {
        const maxW = 960;
        let w = img.naturalWidth || img.width;
        let h = img.naturalHeight || img.height;
        if (w > maxW) {
          h = Math.round((h * maxW) / w);
          w = maxW;
        }
        const canvas = document.createElement("canvas");
        canvas.width = Math.max(1, w);
        canvas.height = Math.max(1, h);
        const c = canvas.getContext("2d");
        c.drawImage(img, 0, 0, canvas.width, canvas.height);
        let dataUrl = "";
        try {
          dataUrl = canvas.toDataURL("image/jpeg", 0.82);
        } catch (err) {
          dataUrl = src.slice(0, 2_000_000);
        }
        if (dataUrl.length > 2_800_000) {
          setStatus("Resim sığmadı", "busy");
          return;
        }
        const el = document.createElement("img");
        el.className = "ruzgar-belge-img";
        el.src = dataUrl;
        el.alt = String(file.name || "resim").slice(0, 120);
        masaAc("belge");
        belgeInsertNode(el);
        setStatus("Resim eklendi", "ok");
      };
      img.onerror = function () { setStatus("Resim okunamadı", "busy"); };
      img.src = src;
    };
    reader.onerror = function () { setStatus("Resim okunamadı", "busy"); };
    reader.readAsDataURL(file);
    return "Resim ekleniyor…";
  }

  function belgeTabloEkle(rows, cols) {
    const r = Math.max(1, Math.min(12, Number(rows) || 3));
    const c = Math.max(1, Math.min(8, Number(cols) || 3));
    const table = document.createElement("table");
    table.className = "ruzgar-belge-tablo";
    for (let i = 0; i < r; i++) {
      const tr = document.createElement("tr");
      for (let j = 0; j < c; j++) {
        const cell = document.createElement(i === 0 ? "th" : "td");
        cell.textContent = i === 0 ? "Başlık " + (j + 1) : "";
        tr.appendChild(cell);
      }
      table.appendChild(tr);
    }
    masaAc("belge");
    belgeInsertNode(table);
    setStatus("Tablo eklendi", "ok");
    return "Belgeye " + r + "×" + c + " tablo eklendi.";
  }

  const KOPRU_AD = {
    tercume: "Tercüme",
    programlama: "Programlama",
    ses: "Ses",
    video: "Video",
    hafiza: "Hafıza",
    okuma: "Okuma",
    mimar: "Mimar",
  };

  function yuzeyPaketAl() {
    const mode = sayfa === "sohbet" ? "sohbet" : state.mode;
    if (mode === "belge") {
      return {
        tur: "belge",
        metin: String(belge.innerText || "").replace(/\u00a0/g, " ").trim().slice(0, 50000),
      };
    }
    if (mode === "kod") {
      const body = String(kodEl ? kodEl.value : state.kod || "");
      const dil = String(kodDil ? kodDil.value : state.kodDil || "text");
      const header = dil && dil !== "text" ? "// dil: " + dil + "\n" : "";
      return { tur: "kod", metin: (header + body).trim().slice(0, 50000) };
    }
    if (mode === "notlar") {
      const gorev = state.gorevler.map(function (g) {
        return (g.done ? "[x] " : "[ ] ") + g.text;
      }).join("\n");
      const not = notlarEl ? notlarEl.value : state.notlar;
      return { tur: "notlar", metin: (String(not || "") + (gorev ? "\n\n" + gorev : "")).trim().slice(0, 50000) };
    }
    if (mode === "tablo") {
      const satirlar = [];
      for (let r = 0; r < ROWS; r++) {
        for (let c = 0; c < COLS.length; c++) {
          const deger = String(state.sheet[r][c] || "").trim();
          if (deger) satirlar.push(COLS[c] + (r + 1) + "\t" + deger);
        }
      }
      return { tur: "tablo", metin: satirlar.join("\n").slice(0, 50000) };
    }
    if (mode === "sunum") {
      const metin = state.slides.map(function (sl, i) {
        return "Slayt " + (i + 1) + ": " + String(sl.title || "") + "\n" + String(sl.body || "");
      }).join("\n\n");
      return { tur: "sunum", metin: metin.trim().slice(0, 50000) };
    }
    if (mode === "okuma") {
      if (state.okuma.kind === "text") {
        return { tur: "okuma", metin: String(state.okuma.text || "").slice(0, 50000) };
      }
      return { tur: "okuma", metin: state.okuma.name ? ("PDF: " + state.okuma.name) : "" };
    }
    if (mode === "web") {
      return { tur: "web", metin: String(state.web || (webUrl && webUrl.value) || "").trim() };
    }
    if (mode === "medya") {
      return {
        tur: "medya",
        metin: state.medya.name
          ? ("Medya yüzeyde: " + state.medya.name + " (" + (state.medya.kind || "dosya") + "). Ağır işlem Video motorunda.")
          : "",
      };
    }
    if (mode === "ses") {
      return {
        tur: "ses",
        metin: state.ses.name ? ("Ses yüzeyde: " + state.ses.name) : "",
      };
    }
    if (mode === "foto") {
      return {
        tur: "foto",
        metin: [
          state.foto.refName ? "Referans: " + state.foto.refName : "",
          state.foto.kok ? "Kütüphane: " + state.foto.kok : "",
          state.foto.sayi ? "Katalog: " + state.foto.sayi + " foto" : "",
        ].filter(Boolean).join("\n"),
      };
    }
    return { tur: mode, metin: "" };
  }

  function yuzeyMotorGonder(motor) {
    const mid = String(motor || "")
      .toLowerCase()
      .replace(/ğ/g, "g")
      .replace(/ü/g, "u")
      .replace(/ş/g, "s")
      .replace(/ı/g, "i")
      .replace(/ö/g, "o")
      .replace(/ç/g, "c");
    const map = {
      tercume: "tercume",
      tercumeye: "tercume",
      ceviri: "tercume",
      programlama: "programlama",
      programlamaya: "programlama",
      koda: "programlama",
      kod: "programlama",
      ses: "ses",
      sese: "ses",
      video: "video",
      videoya: "video",
      hafiza: "hafiza",
      hafizaya: "hafiza",
      okuma: "okuma",
      okumaya: "okuma",
      mimar: "mimar",
      mimara: "mimar",
    };
    const hedef = map[mid] || mid;
    if (!KOPRU_AD[hedef]) {
      return "Bilinmeyen motor. Tercüme, Programlama, Ses, Video, Hafıza, Okuma.";
    }
    const paket = yuzeyPaketAl();
    let metin = paket.metin;
    if (!metin) {
      return "Gönderilecek içerik yok. Önce yüzeyde yaz / aç.";
    }
    if (hedef === "programlama") {
      if (paket.tur !== "kod") {
        metin =
          "# Yüzeyden görev (çalıştırma kapalı — güvenli atölye)\n" +
          "# Kaynak yetenek: " + paket.tur + "\n\n" +
          metin;
      } else {
        metin =
          "# Yüzey → Programlama (Faz85 güvenli yol; serbest çalıştırma kapalı)\n" +
          metin;
      }
    }
    if (typeof window.applyMotorHandoff !== "function") {
      return "Motor köprüsü henüz yüklenmedi. Sayfayı yenile.";
    }
    try {
      window.applyMotorHandoff(hedef, metin);
    } catch (err) {
      return "Köprü uygulanamadı.";
    }
    flashYuzey();
    setStatus("→ " + KOPRU_AD[hedef], "ok");
    const guven = hedef === "programlama"
      ? " Çalıştırma kapalı; Faz85 hızlı yol / onaylı yazım."
      : "";
    return "Yüzey (" + (YETENEK_AD[state.mode] || paket.tur) + ") → " + KOPRU_AD[hedef] + " aktarıldı." + guven;
  }

  function wireBelgeKarma() {
    const imgInp = document.getElementById("ruzgar-masa-belge-img");
    if (imgInp) {
      imgInp.addEventListener("change", function () {
        belgeResimEkle(imgInp.files && imgInp.files[0]);
        imgInp.value = "";
      });
    }
    belge.addEventListener("paste", function (ev) {
      const items = ev.clipboardData && ev.clipboardData.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].type && items[i].type.indexOf("image/") === 0) {
          const file = items[i].getAsFile();
          if (file) {
            ev.preventDefault();
            belgeResimEkle(file);
            return;
          }
        }
      }
    });
    belge.addEventListener("dragover", function (ev) {
      if (ev.dataTransfer && Array.prototype.some.call(ev.dataTransfer.types || [], function (t) {
        return t === "Files";
      })) {
        ev.preventDefault();
        belge.classList.add("is-drag-img");
      }
    });
    belge.addEventListener("dragleave", function () {
      belge.classList.remove("is-drag-img");
    });
    belge.addEventListener("drop", function (ev) {
      belge.classList.remove("is-drag-img");
      const file = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
      if (file && String(file.type || "").indexOf("image/") === 0) {
        ev.preventDefault();
        belgeResimEkle(file);
      }
    });
  }

  function belgeMetinNodunaYaz(eski, yeni) {
    const walker = document.createTreeWalker(belge, NodeFilter.SHOW_TEXT, null);
    let node = walker.nextNode();
    while (node) {
      const val = node.nodeValue || "";
      const yer = val.indexOf(eski);
      if (yer >= 0) {
        node.nodeValue = val.slice(0, yer) + yeni + val.slice(yer + eski.length);
        return true;
      }
      node = walker.nextNode();
    }
    return false;
  }

  function colLabel(c) { return COLS[c] || ""; }
  function addr(r, c) { return colLabel(c) + (r + 1); }

  function buildSheet() {
    const table = document.createElement("table");
    table.className = "ruzgar-masa-sheet";
    const head = document.createElement("tr");
    const corner = document.createElement("th");
    corner.className = "ruzgar-masa-corner";
    head.appendChild(corner);
    COLS.forEach(function (name) {
      const th = document.createElement("th");
      th.textContent = name;
      head.appendChild(th);
    });
    table.appendChild(head);
    for (let r = 0; r < ROWS; r++) {
      const tr = document.createElement("tr");
      const rh = document.createElement("th");
      rh.className = "ruzgar-masa-rowhead";
      rh.textContent = String(r + 1);
      tr.appendChild(rh);
      for (let c = 0; c < COLS.length; c++) {
        const td = document.createElement("td");
        const input = document.createElement("input");
        input.type = "text";
        input.spellcheck = false;
        input.dataset.r = String(r);
        input.dataset.c = String(c);
        input.setAttribute("aria-label", addr(r, c));
        td.appendChild(input);
        tr.appendChild(td);
      }
      table.appendChild(tr);
    }
    sheetWrap.replaceChildren(table);
    sheetWrap.addEventListener("focusin", onCellFocus);
    sheetWrap.addEventListener("focusout", function () { setTimeout(paintSheet, 0); });
    sheetWrap.addEventListener("input", onCellInput);
    sheetWrap.addEventListener("keydown", onCellKey);
    sheetWrap.addEventListener("paste", onCellPaste);
    paintSheet();
  }

  function cellInput(r, c) {
    return sheetWrap.querySelector('input[data-r="' + r + '"][data-c="' + c + '"]');
  }

  function paintSheet() {
    const stack = new Set();
    for (let r = 0; r < ROWS; r++) {
      for (let c = 0; c < COLS.length; c++) {
        const input = cellInput(r, c);
        if (!input || input === document.activeElement) continue;
        const raw = state.sheet[r][c];
        input.value = raw && raw.charAt(0) === "=" ? displayValue(evalFormula(raw, stack)) : raw;
      }
    }
    markSel();
  }

  function displayValue(value) {
    if (typeof value === "number" && isFinite(value)) {
      const rounded = Math.round(value * 1000000) / 1000000;
      return String(rounded);
    }
    return value == null ? "" : String(value);
  }

  function markSel() {
    sheetWrap.querySelectorAll("td.is-sel").forEach(function (td) { td.classList.remove("is-sel"); });
    const input = cellInput(state.sel.r, state.sel.c);
    if (input) input.parentElement.classList.add("is-sel");
    cellName.textContent = addr(state.sel.r, state.sel.c);
    if (document.activeElement !== formulaInput) {
      formulaInput.value = state.sheet[state.sel.r][state.sel.c];
    }
  }

  function onCellFocus(ev) {
    const input = ev.target.closest("input[data-r]");
    if (!input) return;
    const r = Number(input.dataset.r);
    const c = Number(input.dataset.c);
    state.sel = { r: r, c: c };
    input.value = state.sheet[r][c];
    formulaInput.value = state.sheet[r][c];
    markSel();
  }

  function commitCell(r, c, raw) {
    state.sheet[r][c] = raw;
    scheduleSave();
    paintSheet();
  }

  function onCellInput(ev) {
    const input = ev.target.closest("input[data-r]");
    if (!input) return;
    const r = Number(input.dataset.r);
    const c = Number(input.dataset.c);
    state.sheet[r][c] = input.value;
    formulaInput.value = input.value;
    scheduleSave();
  }

  sheetWrap && formulaInput.addEventListener("change", function () {
    commitCell(state.sel.r, state.sel.c, formulaInput.value);
    const input = cellInput(state.sel.r, state.sel.c);
    if (input) input.value = formulaInput.value.charAt(0) === "="
      ? displayValue(evalFormula(formulaInput.value, new Set()))
      : formulaInput.value;
  });

  function onCellKey(ev) {
    const input = ev.target.closest("input[data-r]");
    if (!input) return;
    let r = Number(input.dataset.r);
    let c = Number(input.dataset.c);
    let nr = r;
    let nc = c;
    if (ev.key === "Enter") nr = Math.min(ROWS - 1, r + 1);
    else if (ev.key === "ArrowDown") nr = Math.min(ROWS - 1, r + 1);
    else if (ev.key === "ArrowUp") nr = Math.max(0, r - 1);
    else if (ev.key === "Tab" && !ev.shiftKey) nc = Math.min(COLS.length - 1, c + 1);
    else if (ev.key === "Tab" && ev.shiftKey) nc = Math.max(0, c - 1);
    else if (ev.key === "ArrowRight" && input.selectionStart === input.value.length) nc = Math.min(COLS.length - 1, c + 1);
    else if (ev.key === "ArrowLeft" && input.selectionStart === 0) nc = Math.max(0, c - 1);
    else return;
    ev.preventDefault();
    state.sheet[r][c] = input.value;
    const next = cellInput(nr, nc);
    if (next) next.focus();
    paintSheet();
  }

  function onCellPaste(ev) {
    const input = ev.target.closest("input[data-r]");
    const text = (ev.clipboardData && ev.clipboardData.getData("text")) || "";
    if (!input || text.indexOf("\t") === -1 && text.indexOf("\n") === -1) return;
    ev.preventDefault();
    const startR = Number(input.dataset.r);
    const startC = Number(input.dataset.c);
    text.replace(/\r/g, "").split("\n").forEach(function (line, dr) {
      if (!line && dr === text.split("\n").length - 1) return;
      line.split("\t").forEach(function (part, dc) {
        const r = startR + dr;
        const c = startC + dc;
        if (state.sheet[r] && state.sheet[r][c] !== undefined) state.sheet[r][c] = part;
      });
    });
    paintSheet();
    scheduleSave();
  }

  function evalFormula(raw, stack) {
    try {
      const parser = new Parser(String(raw).slice(1), stack);
      const value = parser.parseExpr();
      parser.skip();
      if (parser.peek()) return "#HATA";
      return value;
    } catch (err) {
      return "#HATA";
    }
  }

  function Parser(src, stack) {
    this.s = src;
    this.i = 0;
    this.stack = stack;
  }
  Parser.prototype.peek = function () { return this.s.charAt(this.i); };
  Parser.prototype.skip = function () { while (this.peek() === " ") this.i += 1; };
  Parser.prototype.parseExpr = function () {
    this.skip();
    let value = this.parseTerm();
    for (;;) {
      this.skip();
      const op = this.peek();
      if (op !== "+" && op !== "-") break;
      this.i += 1;
      const right = this.parseTerm();
      value = op === "+" ? asNum(value) + asNum(right) : asNum(value) - asNum(right);
    }
    return value;
  };
  Parser.prototype.parseTerm = function () {
    this.skip();
    let value = this.parseFactor();
    for (;;) {
      this.skip();
      const op = this.peek();
      if (op !== "*" && op !== "/") break;
      this.i += 1;
      const right = this.parseFactor();
      if (op === "*") value = asNum(value) * asNum(right);
      else {
        const den = asNum(right);
        if (!den) return "#SIFIR";
        value = asNum(value) / den;
      }
    }
    return value;
  };
  Parser.prototype.parseFactor = function () {
    this.skip();
    const ch = this.peek();
    if (ch === "+") { this.i += 1; return this.parseFactor(); }
    if (ch === "-") { this.i += 1; return -asNum(this.parseFactor()); }
    if (ch === "(") {
      this.i += 1;
      const value = this.parseExpr();
      this.skip();
      if (this.peek() === ")") this.i += 1;
      return value;
    }
    if (/[0-9.]/.test(ch)) return this.parseNumber();
    if (/[A-Za-z]/.test(ch)) return this.parseIdent();
    throw new Error("token");
  };
  Parser.prototype.parseNumber = function () {
    const start = this.i;
    while (/[0-9.]/.test(this.peek())) this.i += 1;
    const n = Number(this.s.slice(start, this.i));
    if (!isFinite(n)) throw new Error("num");
    return n;
  };
  Parser.prototype.parseIdent = function () {
    const start = this.i;
    while (/[A-Za-z]/.test(this.peek())) this.i += 1;
    const word = this.s.slice(start, this.i).toUpperCase();
    this.skip();
    if (this.peek() === "(") return this.parseCall(word);
    let rowDigits = "";
    while (/[0-9]/.test(this.peek())) {
      rowDigits += this.peek();
      this.i += 1;
    }
    return readCell(word, rowDigits, this.stack);
  };
  Parser.prototype.parseCall = function (name) {
    this.i += 1;
    const values = [];
    this.skip();
    if (this.peek() !== ")") {
      for (;;) {
        this.parseArg().forEach(function (item) { values.push(item); });
        this.skip();
        if (this.peek() === ",") { this.i += 1; continue; }
        break;
      }
    }
    this.skip();
    if (this.peek() === ")") this.i += 1;
    const nums = values.map(asNum);
    if (name === "TOPLA" || name === "SUM") return nums.reduce(function (a, b) { return a + b; }, 0);
    if (name === "ORTALAMA" || name === "AVERAGE") return nums.length ? nums.reduce(function (a, b) { return a + b; }, 0) / nums.length : 0;
    if (name === "MIN" || name === "MİN") return nums.length ? Math.min.apply(null, nums) : 0;
    if (name === "MAK" || name === "MAX") return nums.length ? Math.max.apply(null, nums) : 0;
    throw new Error("fn");
  };
  Parser.prototype.parseArg = function () {
    const save = this.i;
    const ref = this.tryCell();
    if (ref) {
      this.skip();
      if (this.peek() === ":") {
        this.i += 1;
        const end = this.tryCell();
        if (!end) throw new Error("range");
        return expandRange(ref, end, this.stack);
      }
      return [readCell(COLS[ref.c], String(ref.r + 1), this.stack)];
    }
    this.i = save;
    return [this.parseExpr()];
  };
  Parser.prototype.tryCell = function () {
    const save = this.i;
    this.skip();
    const start = this.i;
    while (/[A-Za-z]/.test(this.peek())) this.i += 1;
    const letters = this.s.slice(start, this.i).toUpperCase();
    let rowDigits = "";
    while (/[0-9]/.test(this.peek())) {
      rowDigits += this.peek();
      this.i += 1;
    }
    if (!letters || !rowDigits || COLS.indexOf(letters) < 0) {
      this.i = save;
      return null;
    }
    return { c: COLS.indexOf(letters), r: Number(rowDigits) - 1 };
  };

  function readCell(letters, rowDigits, stack) {
    const c = COLS.indexOf(letters);
    const r = Number(rowDigits) - 1;
    if (c < 0 || r < 0 || r >= ROWS) return "#HATA";
    const key = r + "," + c;
    if (stack.has(key)) return "#DÖNGÜ";
    const raw = state.sheet[r][c] || "";
    if (!raw) return 0;
    if (raw.charAt(0) !== "=") return asNum(raw);
    stack.add(key);
    try {
      return evalFormula(raw, stack);
    } finally {
      stack.delete(key);
    }
  }

  function expandRange(a, b, stack) {
    const r1 = Math.min(a.r, b.r);
    const r2 = Math.max(a.r, b.r);
    const c1 = Math.min(a.c, b.c);
    const c2 = Math.max(a.c, b.c);
    const out = [];
    for (let r = r1; r <= r2; r++) {
      for (let c = c1; c <= c2; c++) out.push(readCell(COLS[c], String(r + 1), stack));
    }
    return out;
  }

  function asNum(value) {
    if (typeof value === "number") return value;
    if (value === "#HATA" || value === "#SIFIR" || value === "#DÖNGÜ") throw new Error(value);
    const n = Number(String(value).replace(",", "."));
    if (!isFinite(n)) throw new Error("nan");
    return n;
  }

  function ensurePaper() {
    if (paperReady) return;
    canvas.width = BW;
    canvas.height = BH;
    ctx = canvas.getContext("2d");
    ctx.fillStyle = "#f4f0e6";
    ctx.fillRect(0, 0, BW, BH);
    paperReady = true;
    if (state._png) {
      state.ink = true;
      const img = new Image();
      const src = state._png;
      state._png = "";
      img.onload = function () { ctx.drawImage(img, 0, 0, BW, BH); };
      img.src = src;
    }
  }

  function pointOf(ev) {
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((ev.clientX - rect.left) / rect.width) * BW,
      y: ((ev.clientY - rect.top) / rect.height) * BH,
    };
  }

  function takeSnap() {
    try { snap = ctx.getImageData(0, 0, BW, BH); } catch (err) { snap = null; }
  }

  function undoDraw() {
    if (!snap) return;
    ctx.putImageData(snap, 0, 0);
    snap = null;
    scheduleSave();
  }

  function clearPaper() {
    takeSnap();
    ctx.fillStyle = "#f4f0e6";
    ctx.fillRect(0, 0, BW, BH);
    state.ink = false;
    scheduleSave();
    syncSahne();
  }

  function strokeStyle() {
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.lineWidth = state.draw.tool === "silgi" ? state.draw.size * 4 : state.draw.size * 2;
    ctx.strokeStyle = state.draw.tool === "silgi" ? "#f4f0e6" : state.draw.color;
    ctx.fillStyle = state.draw.color;
  }

  canvas.addEventListener("pointerdown", function (ev) {
    if (state.mode !== "cizim" || ev.button !== 0) return;
    try { canvas.setPointerCapture(ev.pointerId); } catch (err) { /* sentetik işaret */ }
    if (canvas.parentElement) canvas.parentElement.focus();
    drawing = true;
    takeSnap();
    lastPt = pointOf(ev);
    shapeStart = lastPt;
    strokeStyle();
    if (state.draw.tool === "kalem" || state.draw.tool === "silgi") {
      ctx.beginPath();
      ctx.moveTo(lastPt.x, lastPt.y);
    }
  });

  canvas.addEventListener("pointermove", function (ev) {
    if (!drawing) return;
    const pt = pointOf(ev);
    if (state.draw.tool === "kalem" || state.draw.tool === "silgi") {
      ctx.lineTo(pt.x, pt.y);
      ctx.stroke();
      lastPt = pt;
      return;
    }
    if (snap) ctx.putImageData(snap, 0, 0);
    strokeStyle();
    ctx.beginPath();
    if (state.draw.tool === "cizgi") {
      ctx.moveTo(shapeStart.x, shapeStart.y);
      ctx.lineTo(pt.x, pt.y);
      ctx.stroke();
    } else if (state.draw.tool === "kutu") {
      ctx.strokeRect(shapeStart.x, shapeStart.y, pt.x - shapeStart.x, pt.y - shapeStart.y);
    } else if (state.draw.tool === "daire") {
      const rx = Math.abs(pt.x - shapeStart.x) / 2;
      const ry = Math.abs(pt.y - shapeStart.y) / 2;
      ctx.ellipse((shapeStart.x + pt.x) / 2, (shapeStart.y + pt.y) / 2, Math.max(rx, 1), Math.max(ry, 1), 0, 0, Math.PI * 2);
      ctx.stroke();
    }
  });

  function endDraw() {
    if (!drawing) return;
    drawing = false;
    state.ink = true;
    scheduleSave();
    syncSahne();
  }
  canvas.addEventListener("pointerup", endDraw);
  canvas.addEventListener("pointercancel", endDraw);

  function currentSlide() {
    return state.slides[state.slideIndex] || state.slides[0];
  }

  function renderSlides() {
    slidesEl.replaceChildren();
    state.slides.forEach(function (slide, index) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ruzgar-masa-slide-thumb" + (index === state.slideIndex ? " is-on" : "");
      btn.innerHTML = "<strong>" + (index + 1) + ". " + escapeText(slide.title || "Slayt") + "</strong><small>" + escapeText(slide.body || "") + "</small>";
      btn.addEventListener("click", function () {
        state.slideIndex = index;
        fillSlideForm();
        renderSlides();
      });
      slidesEl.appendChild(btn);
    });
    fillSlideForm();
  }

  function escapeText(text) {
    return String(text).replace(/[&<>]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[ch];
    });
  }

  function fillSlideForm() {
    const slide = currentSlide();
    if (document.activeElement !== slideTitle) slideTitle.value = slide.title || "";
    if (document.activeElement !== slideBody) slideBody.value = slide.body || "";
    syncSlidePreview();
  }

  function bindSlideField(el, key) {
    el.addEventListener("input", function () {
      currentSlide()[key] = el.value;
      scheduleSave();
      syncSlidePreview();
      slidesEl.querySelectorAll(".ruzgar-masa-slide-thumb").forEach(function (btn, index) {
        if (index !== state.slideIndex) return;
        const slide = currentSlide();
        btn.innerHTML = "<strong>" + (index + 1) + ". " + escapeText(slide.title || "Slayt") + "</strong><small>" + escapeText(slide.body || "") + "</small>";
      });
    });
  }
  bindSlideField(slideTitle, "title");
  bindSlideField(slideBody, "body");

  function addSlide() {
    state.slides.splice(state.slideIndex + 1, 0, { title: "Yeni slayt", body: "", bg: "#1c1a16", fg: "#f7f4ec" });
    state.slideIndex += 1;
    renderTools();
    renderSlides();
    scheduleSave();
  }

  function deleteSlide() {
    if (state.slides.length === 1) {
      state.slides[0] = { title: "", body: "", bg: "#1c1a16", fg: "#f7f4ec" };
    } else {
      state.slides.splice(state.slideIndex, 1);
      state.slideIndex = Math.max(0, state.slideIndex - 1);
    }
    renderTools();
    renderSlides();
    scheduleSave();
  }

  let presentIndex = 0;
  function startPresent() {
    presentIndex = state.slideIndex;
    paintPresent();
    present.hidden = false;
  }
  function paintPresent() {
    const slide = state.slides[presentIndex] || state.slides[0];
    present.style.background = slide.bg || "#1c1a16";
    present.style.color = slide.fg || "#f7f4ec";
    presentTitle.textContent = slide.title || "";
    presentBody.textContent = slide.body || "";
  }
  present.addEventListener("click", function () {
    presentIndex += 1;
    if (presentIndex >= state.slides.length) present.hidden = true;
    else paintPresent();
  });
  document.addEventListener("keydown", function (ev) {
    if (present.hidden) return;
    ev.preventDefault();
    if (ev.key === "Escape") present.hidden = true;
    else if (ev.key === "ArrowRight" || ev.key === " ") {
      presentIndex = Math.min(state.slides.length - 1, presentIndex + 1);
      paintPresent();
    } else if (ev.key === "ArrowLeft") {
      presentIndex = Math.max(0, presentIndex - 1);
      paintPresent();
    }
  });

  function download(filename, blob) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  }

  document.getElementById("ruzgar-masa-indir").addEventListener("click", function () {
    if (state.mode === "belge") {
      const html = "<!DOCTYPE html><meta charset=\"utf-8\"><title>Belge</title><body>" + belge.innerHTML + "</body>";
      download("ruzgar-belge.html", new Blob([html], { type: "text/html" }));
    } else if (state.mode === "tablo") {
      const lines = [COLS.join(",")];
      state.sheet.forEach(function (row) {
        lines.push(row.map(function (cell) {
          const text = String(cell).replace(/"/g, '""');
          return /[",\n]/.test(text) ? '"' + text + '"' : text;
        }).join(","));
      });
      download("ruzgar-tablo.csv", new Blob([lines.join("\n")], { type: "text/csv" }));
    } else if (state.mode === "cizim") {
      canvas.toBlob(function (blob) { if (blob) download("ruzgar-cizim.png", blob); });
    } else if (state.mode === "medya") {
      if (!state.medya.url) {
        setStatus("Medya boş", "busy");
        return;
      }
      const a = document.createElement("a");
      a.href = state.medya.url;
      a.download = state.medya.name || (state.medya.kind === "video" ? "ruzgar-medya.mp4" : "ruzgar-medya.png");
      a.click();
    } else if (state.mode === "foto") {
      if (state.foto.refUrl) {
        const a = document.createElement("a");
        a.href = state.foto.refUrl;
        a.download = state.foto.refName || "ruzgar-referans.jpg";
        a.click();
      } else {
        download(
          "ruzgar-foto-katalog.txt",
          new Blob(
            [(state.foto.kok || "") + "\n" + state.foto.sayi + " foto\n" + (state.foto.ornek || []).map(function (x) {
              return typeof x === "string" ? x : (x.rel || "");
            }).join("\n")],
            { type: "text/plain;charset=utf-8" },
          ),
        );
      }
    } else if (state.mode === "notlar") {
      const gorevMetin = state.gorevler.map(function (g) {
        return (g.done ? "[x] " : "[ ] ") + g.text;
      }).join("\n");
      const body = (notlarEl ? notlarEl.value : "") + (gorevMetin ? "\n\n---\n" + gorevMetin : "");
      download("ruzgar-notlar.txt", new Blob([body], { type: "text/plain;charset=utf-8" }));
    } else if (state.mode === "kod") {
      const ext = { javascript: "js", python: "py", html: "html", css: "css", json: "json", markdown: "md", text: "txt" }[state.kodDil] || "txt";
      download("ruzgar-kod." + ext, new Blob([kodEl ? kodEl.value : ""], { type: "text/plain;charset=utf-8" }));
    } else if (state.mode === "ses") {
      if (!state.ses.url) {
        setStatus("Ses boş", "busy");
        return;
      }
      const a = document.createElement("a");
      a.href = state.ses.url;
      a.download = state.ses.name || "ruzgar-ses.webm";
      a.click();
    } else if (state.mode === "okuma") {
      if (state.okuma.kind === "text") {
        download(state.okuma.name || "ruzgar-okuma.txt", new Blob([state.okuma.text || ""], { type: "text/plain;charset=utf-8" }));
      } else if (state.okuma.url) {
        const a = document.createElement("a");
        a.href = state.okuma.url;
        a.download = state.okuma.name || "ruzgar-okuma.pdf";
        a.click();
      } else setStatus("Okuma boş", "busy");
    } else if (state.mode === "web") {
      download("ruzgar-web-url.txt", new Blob([state.web || ""], { type: "text/plain;charset=utf-8" }));
    } else {
      const parts = state.slides.map(function (slide) {
        return "<section style=\"min-height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;background:" +
          escapeText(slide.bg) + ";color:" + escapeText(slide.fg) + ";padding:48px\"><h1>" +
          escapeText(slide.title) + "</h1><p style=\"white-space:pre-wrap;font-size:24px\">" + escapeText(slide.body) + "</p></section>";
      });
      download("ruzgar-sunum.html", new Blob(["<!DOCTYPE html><meta charset=\"utf-8\"><title>Sunum</title>" + parts.join("")], { type: "text/html" }));
    }
  });

  document.getElementById("ruzgar-masa-yeni").addEventListener("click", function () {
    const label = YETENEK_AD[state.mode] || "yüzeyi";
    if (!window.confirm(label + " temizlensin mi?")) return;
    if (state.mode === "belge") belge.innerHTML = "";
    else if (state.mode === "tablo") {
      state.sheet = blankSheet();
      paintSheet();
    } else if (state.mode === "cizim") clearPaper();
    else if (state.mode === "medya") medyaTemizle();
    else if (state.mode === "foto") {
      if (state.foto.refUrl) {
        try { URL.revokeObjectURL(state.foto.refUrl); } catch (err) { /* tarayıcı */ }
      }
      state.foto.refName = "";
      state.foto.refUrl = "";
      state.foto.refFile = null;
      state.foto.sonuclar = [];
      if (fotoRefImg) {
        fotoRefImg.removeAttribute("src");
        fotoRefImg.hidden = true;
      }
      if (fotoRefEmpty) fotoRefEmpty.hidden = false;
      paintFoto();
    } else if (state.mode === "notlar") notlarTemizle();
    else if (state.mode === "kod") kodTemizle();
    else if (state.mode === "ses") sesTemizle();
    else if (state.mode === "okuma") okumaTemizle();
    else if (state.mode === "web") {
      state.web = "";
      if (webUrl) webUrl.value = "";
      if (webFrame) {
        webFrame.removeAttribute("data-src");
        webFrame.src = "about:blank";
      }
      paintWeb();
    } else {
      state.slides = [{ title: "", body: "", bg: "#1c1a16", fg: "#f7f4ec" }];
      state.slideIndex = 0;
      renderSlides();
    }
    scheduleSave();
  });

  const masaMenu = document.createElement("div");
  masaMenu.id = "ruzgar-masa-menu";
  masaMenu.className = "ruzgar-masa-menu";
  masaMenu.hidden = true;
  masaMenu.setAttribute("role", "menu");
  masaMenu.innerHTML =
    '<button type="button" data-act="cut" role="menuitem">Kes</button>' +
    '<button type="button" data-act="copy" role="menuitem">Kopyala</button>' +
    '<button type="button" data-act="paste" role="menuitem">Yapıştır</button>' +
    '<button type="button" data-act="all" role="menuitem">Tümünü seç</button>';
  document.body.appendChild(masaMenu);
  let masaCtx = null;

  function hideMasaMenu() {
    masaMenu.hidden = true;
  }

  function showMasaMenu(x, y) {
    masaMenu.hidden = false;
    const cutBtn = masaMenu.querySelector('[data-act="cut"]');
    const copyBtn = masaMenu.querySelector('[data-act="copy"]');
    const allBtn = masaMenu.querySelector('[data-act="all"]');
    if (masaCtx && masaCtx.kind === "cizim") {
      cutBtn.disabled = false;
      copyBtn.disabled = false;
      allBtn.hidden = true;
    } else {
      allBtn.hidden = false;
      cutBtn.disabled = !(masaCtx && masaCtx.selected);
      copyBtn.disabled = !(masaCtx && (masaCtx.selected || masaCtx.whole));
    }
    const pad = 6;
    const w = 160;
    const h = 150;
    masaMenu.style.left = Math.min(Math.max(pad, x), window.innerWidth - w - pad) + "px";
    masaMenu.style.top = Math.min(Math.max(pad, y), window.innerHeight - h - pad) + "px";
  }

  function writeClipboardText(text) {
    try {
      if (window.ruzgarApi && typeof window.ruzgarApi.writeClipboardText === "function") {
        if (window.ruzgarApi.writeClipboardText(text)) return Promise.resolve();
      }
    } catch (err) { /* Electron panosu */ }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () { return copyWithBox(text); });
    }
    return copyWithBox(text);
  }

  function copyWithBox(text) {
    const box = document.createElement("textarea");
    box.value = text;
    box.setAttribute("readonly", "");
    box.style.position = "fixed";
    box.style.left = "-9999px";
    document.body.appendChild(box);
    box.select();
    const ok = document.execCommand("copy");
    box.remove();
    return ok ? Promise.resolve() : Promise.reject(new Error("copy"));
  }

  function readClipboardText() {
    try {
      if (window.ruzgarApi && typeof window.ruzgarApi.readClipboardText === "function") {
        const t = window.ruzgarApi.readClipboardText();
        return Promise.resolve(String(t || ""));
      }
    } catch (err) { /* Electron panosu */ }
    if (navigator.clipboard && navigator.clipboard.readText) return navigator.clipboard.readText();
    return Promise.reject(new Error("clipboard"));
  }

  function restoreRich() {
    belge.focus();
    if (!masaCtx || !masaCtx.range) return;
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(masaCtx.range);
  }

  function focusFieldSel(selectAllIfEmpty) {
    const el = masaCtx.el;
    el.focus();
    const start = masaCtx.start || 0;
    const end = masaCtx.end == null ? start : masaCtx.end;
    if (selectAllIfEmpty && start === end) el.select();
    else el.setSelectionRange(start, end);
  }

  function selectedFieldText() {
    const el = masaCtx.el;
    if (masaCtx.start !== masaCtx.end) return el.value.slice(masaCtx.start, masaCtx.end);
    return el.value;
  }

  function writeFieldText(text) {
    const el = masaCtx.el;
    el.focus();
    const start = masaCtx.start == null ? el.value.length : masaCtx.start;
    const end = masaCtx.end == null ? start : masaCtx.end;
    if (el.closest("#ruzgar-masa-sheet") && /[\t\n]/.test(text)) {
      const data = new DataTransfer();
      data.setData("text", text);
      el.dispatchEvent(new ClipboardEvent("paste", { bubbles: true, clipboardData: data }));
      return;
    }
    el.setRangeText(text, start, end, "end");
    el.dispatchEvent(new Event("input", { bubbles: true }));
    if (el.closest("#ruzgar-masa-sheet")) {
      el.dispatchEvent(new FocusEvent("focusout", { bubbles: true }));
    }
    if (el.id === "ruzgar-masa-slide-title" || el.id === "ruzgar-masa-slide-body") {
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }
    scheduleSave();
  }

  function copyCanvas() {
    return new Promise(function (resolve, reject) {
      canvas.toBlob(function (blob) {
        if (!blob || !navigator.clipboard || !navigator.clipboard.write || typeof ClipboardItem === "undefined") {
          reject(new Error("image"));
          return;
        }
        navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]).then(resolve).catch(reject);
      }, "image/png");
    });
  }

  function pasteCanvas() {
    if (!navigator.clipboard || !navigator.clipboard.read) return Promise.reject(new Error("image"));
    return navigator.clipboard.read().then(function (items) {
      let found = null;
      items.forEach(function (item) {
        const type = item.types.filter(function (name) { return name.indexOf("image/") === 0; })[0];
        if (type && !found) found = item.getType(type);
      });
      if (!found) return Promise.reject(new Error("no-image"));
      return found.then(function (blob) {
        return new Promise(function (resolve, reject) {
          const img = new Image();
          img.onload = function () {
            takeSnap();
            ctx.drawImage(img, 0, 0, BW, BH);
            URL.revokeObjectURL(img.src);
            scheduleSave();
            resolve();
          };
          img.onerror = reject;
          img.src = URL.createObjectURL(blob);
        });
      });
    });
  }

  function captureMasaCtx(target) {
    if (target.closest("#ruzgar-masa-canvas, #ruzgar-masa-canvas-wrap")) {
      return { kind: "cizim", selected: true, whole: true };
    }
    const cell = target.closest("#ruzgar-masa-sheet td");
    if (cell && cell.querySelector("input")) target = cell.querySelector("input");
    const rich = target.closest("#ruzgar-masa-belge");
    if (rich) {
      const sel = window.getSelection();
      const text = sel ? sel.toString() : "";
      let range = null;
      if (sel && sel.rangeCount) {
        const node = sel.anchorNode;
        if (node && (node === belge || belge.contains(node))) range = sel.getRangeAt(0).cloneRange();
      }
      return { kind: "rich", range: range, text: text, selected: text.length > 0, whole: (belge.innerText || "").trim().length > 0 };
    }
    const field = target.closest("input, textarea");
    if (!field || !root.contains(field) || field.type === "color" || field.type === "range") return null;
    const start = field.selectionStart || 0;
    const end = field.selectionEnd || 0;
    return {
      kind: "field",
      el: field,
      start: start,
      end: end,
      selected: start !== end,
      whole: field.value.length > 0,
    };
  }

  document.addEventListener("contextmenu", function (ev) {
    if (!root.contains(ev.target)) return;
    const next = captureMasaCtx(ev.target);
    if (!next) return;
    ev.preventDefault();
    ev.stopPropagation();
    masaCtx = next;
    showMasaMenu(ev.clientX, ev.clientY);
  }, true);

  masaMenu.addEventListener("mousedown", function (ev) { ev.preventDefault(); });
  masaMenu.addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-act]");
    if (!btn || btn.disabled || !masaCtx) return;
    const act = btn.getAttribute("data-act");
    hideMasaMenu();
    if (act === "all") {
      if (masaCtx.kind === "rich") {
        belge.focus();
        document.execCommand("selectAll");
      } else if (masaCtx.kind === "field") {
        masaCtx.el.focus();
        masaCtx.el.select();
      }
      return;
    }
    if (act === "copy") {
      if (masaCtx.kind === "cizim") {
        copyCanvas().then(function () { setStatus("Çizim kopyalandı"); }).catch(function () { setStatus("Kopyalanamadı"); });
        return;
      }
      if (masaCtx.kind === "rich") restoreRich();
      else focusFieldSel(true);
      if (document.execCommand("copy")) {
        setStatus("Kopyalandı");
        return;
      }
      const text = masaCtx.kind === "rich" ? (masaCtx.text || belge.innerText || "") : selectedFieldText();
      writeClipboardText(text).then(function () { setStatus("Kopyalandı"); }).catch(function () { setStatus("Kopyalanamadı"); });
      return;
    }
    if (act === "cut") {
      if (masaCtx.kind === "cizim") {
        copyCanvas().then(function () { clearPaper(); setStatus("Çizim kesildi"); }).catch(function () { setStatus("Kesilemedi"); });
        return;
      }
      if (masaCtx.kind === "rich") restoreRich();
      else focusFieldSel(false);
      if (document.execCommand("cut")) {
        if (masaCtx.kind === "field") masaCtx.el.dispatchEvent(new Event("input", { bubbles: true }));
        scheduleSave();
        setStatus("Kesildi");
        return;
      }
      const text = masaCtx.kind === "rich" ? (masaCtx.text || "") : masaCtx.el.value.slice(masaCtx.start, masaCtx.end);
      writeClipboardText(text).then(function () {
        if (masaCtx.kind === "rich") {
          restoreRich();
          document.execCommand("delete");
        } else {
          writeFieldText("");
        }
        scheduleSave();
        setStatus("Kesildi");
      }).catch(function () { setStatus("Kesilemedi"); });
      return;
    }
    if (act === "paste") {
      if (masaCtx.kind === "cizim") {
        pasteCanvas().then(function () { setStatus("Görsel yapıştırıldı"); }).catch(function () { setStatus("Panoda görsel yok"); });
        return;
      }
      if (masaCtx.kind === "rich") restoreRich();
      else focusFieldSel(false);
      if (document.execCommand("paste")) {
        if (masaCtx.kind === "field") masaCtx.el.dispatchEvent(new Event("input", { bubbles: true }));
        scheduleSave();
        setStatus("Yapıştırıldı");
        return;
      }
      readClipboardText().then(function (text) {
        if (masaCtx.kind === "rich") {
          restoreRich();
          document.execCommand("insertText", false, text);
          scheduleSave();
        } else {
          writeFieldText(text);
        }
        setStatus("Yapıştırıldı");
      }).catch(function () { setStatus("Yapıştırılamadı"); });
    }
  });

  document.addEventListener("pointerdown", function (ev) {
    if (masaMenu.hidden || masaMenu.contains(ev.target)) return;
    hideMasaMenu();
  }, true);
  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") hideMasaMenu();
    if (state.mode !== "cizim") return;
    if (ev.target.closest && ev.target.closest("input, textarea, #ruzgar-masa-belge")) return;
    if (!(ev.ctrlKey || ev.metaKey) || !root.contains(ev.target)) return;
    const key = ev.key.toLowerCase();
    if (key === "c") {
      ev.preventDefault();
      copyCanvas().then(function () { setStatus("Çizim kopyalandı"); }).catch(function () { setStatus("Kopyalanamadı"); });
    } else if (key === "x") {
      ev.preventDefault();
      copyCanvas().then(function () { clearPaper(); setStatus("Çizim kesildi"); }).catch(function () { setStatus("Kesilemedi"); });
    } else if (key === "v") {
      ev.preventDefault();
      pasteCanvas().then(function () { setStatus("Görsel yapıştırıldı"); }).catch(function () { setStatus("Panoda görsel yok"); });
    }
  });
  window.addEventListener("blur", hideMasaMenu);
  window.addEventListener("resize", hideMasaMenu);

  const MASA_RENK = {
    siyah: "#1a1a1c",
    kirmizi: "#8c2f2f",
    mavi: "#1e4d8c",
    yesil: "#1f6b45",
    altin: "#8a7844",
    beyaz: "#f4f0e6",
  };

  function masaTemizMetin(value, max) {
    return String(value || "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, "").slice(0, max);
  }

  function masaHarf(name) {
    return String(name || "")
      .toLowerCase()
      .replace(/ı/g, "i")
      .replace(/İ/g, "i")
      .replace(/ş/g, "s")
      .replace(/ğ/g, "g")
      .replace(/ü/g, "u")
      .replace(/ö/g, "o")
      .replace(/ç/g, "c");
  }

  function masaSayi(value, lo, hi) {
    const n = Number(value);
    if (!isFinite(n)) return null;
    return Math.max(lo, Math.min(hi, n));
  }

  function masaSayfa(kind) {
    if (!YETENEK_AD[kind]) return "";
    sayfa = kind;
    if (kind !== "sohbet") showMode(kind);
    syncSahne();
    syncChip();
    flashYuzey();
    return (YETENEK_AD[kind] || "Yüzey") + " açık.";
  }

  function medyaTemizle() {
    if (state.medya.url) {
      try { URL.revokeObjectURL(state.medya.url); } catch (err) { /* tarayıcı */ }
    }
    state.medya = { name: "", kind: "", url: "" };
    paintMedya();
    setStatus("Medya temizlendi", "ok");
    return "Medya temizlendi.";
  }

  function medyaYukle(file) {
    if (!file) return "Dosya yok.";
    const tip = String(file.type || "");
    const kind = tip.indexOf("video/") === 0 ? "video" : tip.indexOf("image/") === 0 ? "image" : "";
    if (!kind) return "Yalnız resim veya kısa video.";
    if (file.size > 80 * 1024 * 1024) return "Dosya 80 MB üstü olamaz.";
    if (state.medya.url) {
      try { URL.revokeObjectURL(state.medya.url); } catch (err) { /* tarayıcı */ }
    }
    state.medya = {
      name: String(file.name || "medya").slice(0, 180),
      kind: kind,
      url: URL.createObjectURL(file),
    };
    masaAc("medya");
    paintMedya();
    flashYuzey();
    setStatus(kind === "video" ? "Video hazır" : "Resim hazır", "ok");
    return (kind === "video" ? "Video" : "Resim") + " yüzeyde: " + state.medya.name;
  }

  function paintMedya() {
    if (!medyaEmpty || !medyaView) return;
    const varMi = !!(state.medya && state.medya.url);
    medyaEmpty.hidden = varMi;
    medyaView.hidden = !varMi;
    medyaView.replaceChildren();
    if (!varMi) return;
    if (state.medya.kind === "video") {
      const video = document.createElement("video");
      video.src = state.medya.url;
      video.controls = true;
      video.playsInline = true;
      medyaView.appendChild(video);
    } else {
      const img = document.createElement("img");
      img.src = state.medya.url;
      img.alt = state.medya.name || "Medya";
      medyaView.appendChild(img);
    }
  }

  function wireMedya() {
    if (medyaFile) {
      medyaFile.addEventListener("change", function () {
        const file = medyaFile.files && medyaFile.files[0];
        medyaYukle(file);
        medyaFile.value = "";
      });
    }
    if (!medyaRoot) return;
    medyaRoot.addEventListener("dragover", function (ev) {
      ev.preventDefault();
      medyaRoot.classList.add("is-drag");
    });
    medyaRoot.addEventListener("dragleave", function () {
      medyaRoot.classList.remove("is-drag");
    });
    medyaRoot.addEventListener("drop", function (ev) {
      ev.preventDefault();
      medyaRoot.classList.remove("is-drag");
      const file = ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0];
      medyaYukle(file);
    });
    medyaRoot.addEventListener("paste", function (ev) {
      const items = ev.clipboardData && ev.clipboardData.items;
      if (!items) return;
      for (let i = 0; i < items.length; i++) {
        if (items[i].kind === "file") {
          const file = items[i].getAsFile();
          if (file) {
            ev.preventDefault();
            medyaYukle(file);
            return;
          }
        }
      }
    });
  }

  function fotoRelOf(item) {
    if (typeof item === "string") return item;
    return String((item && item.rel) || "").trim();
  }

  function fotoOnizUrl(rel) {
    const r = String(rel || "").trim();
    if (!r) return "";
    return masaApiKok() + "/api/foto/dosya?rel=" + encodeURIComponent(r);
  }

  function paintFoto() {
    if (!fotoRoot) return;
    const sonuclar = state.foto.sonuclar || [];
    const has = state.foto.sayi > 0 || sonuclar.length > 0;
    fotoRoot.classList.toggle("has-catalog", has);
    if (fotoEmpty) fotoEmpty.hidden = has;
    if (fotoSayi) {
      fotoSayi.textContent = sonuclar.length
        ? sonuclar.length + " eşleşme"
        : state.foto.sayi + " foto";
    }
    if (fotoGrid) {
      fotoGrid.replaceChildren();
      const liste = sonuclar.length
        ? sonuclar.map(function (s) {
          return { rel: s.rel, bytes: 0, skor: s.skor };
        })
        : (state.foto.ornek || []).slice(0, 48);
      liste.forEach(function (item) {
        const card = document.createElement("button");
        card.type = "button";
        card.className = "ruzgar-masa-foto-card" + (item.skor != null ? " is-hit" : "");
        const rel = fotoRelOf(item);
        const ad = rel.split("/").pop() || rel;
        const bytes = item && item.bytes ? Math.round(item.bytes / 1024) + " KB" : "";
        const skor = item.skor != null ? "skor " + item.skor : "";
        const img = document.createElement("img");
        img.alt = ad;
        img.loading = "lazy";
        img.decoding = "async";
        const url = fotoOnizUrl(rel);
        if (url) img.src = url;
        img.addEventListener("error", function () {
          card.classList.add("is-broken");
        });
        const meta = document.createElement("span");
        meta.className = "ruzgar-masa-foto-card-meta";
        meta.innerHTML = "<strong>" + escapeText(ad) + "</strong><small>" +
          escapeText(rel) + (bytes ? " · " + bytes : "") + (skor ? " · " + skor : "") + "</small>";
        card.appendChild(img);
        card.appendChild(meta);
        card.title = "Tıkla: referans yap";
        card.addEventListener("click", function () {
          void fotoKartReferansYap(rel, ad);
        });
        fotoGrid.appendChild(card);
      });
    }
    const kat = state.foto.katman || {};
    root.querySelectorAll(".ruzgar-masa-foto-layers li").forEach(function (li) {
      const key = li.getAttribute("data-kat");
      li.classList.toggle("is-on", !!kat[key]);
      li.classList.toggle("is-next", false);
    });
    if (fotoKok && state.foto.kok && !fotoKok.value) fotoKok.value = state.foto.kok;
    if (fotoRefImg && state.foto.refUrl) {
      fotoRefImg.src = state.foto.refUrl;
      fotoRefImg.hidden = false;
      if (fotoRefEmpty) fotoRefEmpty.hidden = true;
    }
  }

  function fotoDosyaGecerli(file) {
    if (!file) return false;
    const tip = String(file.type || "").toLowerCase();
    if (tip.indexOf("image/") === 0) return true;
    // Windows sürükle-bırak bazen type boş bırakır — sunucu yine decode eder
    return /\.(jpe?g|jfif|png|webp|bmp|gif|tif{1,2}|heic|heif|avif)$/i.test(String(file.name || ""))
      || !tip; // uzantısız / type boş: sunucuya bırak
  }

  function fotoRefGoster(file, opts) {
    if (state.foto.refUrl && String(state.foto.refUrl).indexOf("blob:") === 0) {
      try { URL.revokeObjectURL(state.foto.refUrl); } catch (err) { /* tarayıcı */ }
    }
    state.foto.refName = String((file && file.name) || (opts && opts.name) || "referans.jpg").slice(0, 180);
    // Kutuda blob yerine sunucu önizlemesi — Electron/IPC yolunda daha güvenilir
    const serverUrl = (opts && opts.serverUrl) ||
      (masaApiKok() + "/api/foto/referans-oniz?t=" + Date.now());
    state.foto.refUrl = serverUrl;
    state.foto.refFile = file || null;
    masaAc("foto");
    if (fotoRefImg) {
      fotoRefImg.onload = function () {
        fotoDurumYaz("Referans kutuda: " + state.foto.refName + " — Yüz ara.");
      };
      fotoRefImg.onerror = function () {
        // Sunucu önizleme yoksa dosyadan blob dene
        if (file) {
          try {
            const blobUrl = URL.createObjectURL(file);
            state.foto.refUrl = blobUrl;
            fotoRefImg.onerror = function () {
              fotoDurumYaz("Önizleme görünmedi. Fotoğraf seç → Aç tekrar.");
            };
            fotoRefImg.src = blobUrl;
            return;
          } catch (err) { /* yedek */ }
        }
        fotoDurumYaz("Önizleme görünmedi. Fotoğraf seç → Aç tekrar.");
      };
      fotoRefImg.removeAttribute("hidden");
      fotoRefImg.hidden = false;
      fotoRefImg.style.display = "block";
      fotoRefImg.style.visibility = "visible";
      fotoRefImg.src = serverUrl;
    }
    if (fotoRefEmpty) {
      fotoRefEmpty.setAttribute("hidden", "");
      fotoRefEmpty.hidden = true;
      fotoRefEmpty.style.display = "none";
    }
    paintFoto();
    flashYuzey();
    fotoDurumYaz("Referans hazır: " + state.foto.refName + " — Yüz ara.");
    setStatus("Referans hazır", "ok");
    return "Referans foto: " + state.foto.refName;
  }

  function fotoRefYukle(file) {
    if (!file) {
      fotoDurumYaz("Dosya yok.");
      return "Dosya yok.";
    }
    // Yerel File → sunucuda normalize (boyut/uzantı fark etmez)
    void fotoReferansDosyaYukle(file);
    return "Yükleniyor…";
  }

  async function fotoReferansSunucudanCek(nameHint) {
    let hj = {};
    try {
      const haz = await fetch(masaApiKok() + "/api/foto/referans-hazirla", { method: "POST" });
      hj = await haz.json().catch(function () { return {}; });
      if (!haz.ok) {
        // Ham kopya duruyorsa yine de önizlemeyi dene
        fotoDurumYaz(hj.detail || "Normalize atlandı — önizleme deneniyor…");
      }
    } catch (err) {
      fotoDurumYaz("Sunucu hazırlık hatası — önizleme deneniyor…");
    }
    const url = masaApiKok() + "/api/foto/referans-oniz?t=" + Date.now();
    let res;
    try {
      res = await fetch(url);
    } catch (err) {
      fotoDurumYaz("Önizleme isteği gitmedi. Sunucu kapalı olabilir.");
      return false;
    }
    if (!res.ok) {
      fotoDurumYaz((hj && hj.detail) || "Önizleme gelmedi. Fotoğraf seç → Aç.");
      return false;
    }
    const blob = await res.blob();
    if (!blob || blob.size < 32) {
      fotoDurumYaz("Önizleme boş geldi.");
      return false;
    }
    const ad = (hj && hj.name) || nameHint || "referans.jpg";
    const file = new File([blob], ad, { type: blob.type || "image/jpeg" });
    fotoRefGoster(file, { name: ad, serverUrl: url });
    if (hj.w && hj.h) {
      fotoDurumYaz("Referans hazır (" + hj.w + "×" + hj.h + ") — Yüz ara.");
    }
    return true;
  }

  async function fotoReferansDosyaYukle(file) {
    masaAc("foto");
    fotoDurumYaz("Resim hazırlanıyor (boyut/uzantı uyarlanıyor)…");
    try {
      // 1) Electron yolu varsa diskten (sürükle-bırak)
      let abs = "";
      try {
        if (window.ruzgarApi && typeof window.ruzgarApi.getPathForFile === "function") {
          abs = String(window.ruzgarApi.getPathForFile(file) || "");
        }
      } catch (err) { abs = ""; }
      if (abs && window.ruzgarApi && typeof window.ruzgarApi.importImagePath === "function") {
        const ir = await window.ruzgarApi.importImagePath(abs);
        if (!ir || !ir.ok) {
          fotoDurumYaz((ir && ir.error) || "Dosya kopyalanamadı.");
          return;
        }
        await fotoReferansSunucudanCek(ir.name || file.name);
        return;
      }
      // 2) FormData yükle — dosya seç / sürükle (yol yoksa)
      const fd = new FormData();
      fd.append("file", file, file.name || "referans.bin");
      const res = await fetch(masaApiKok() + "/api/foto/referans-yukle", { method: "POST", body: fd });
      const data = await res.json().catch(function () { return {}; });
      if (!res.ok) {
        fotoDurumYaz(data.detail || "Yükleme başarısız.");
        return;
      }
      const url = masaApiKok() + "/api/foto/referans-oniz?t=" + Date.now();
      const imgRes = await fetch(url);
      if (!imgRes.ok) {
        fotoDurumYaz("Önizleme gelmedi.");
        return;
      }
      const blob = await imgRes.blob();
      const ad = (data && data.name) || file.name || "referans.jpg";
      fotoRefGoster(new File([blob], ad, { type: "image/jpeg" }), { name: ad, serverUrl: url });
      if (data.w && data.h) {
        fotoDurumYaz("Referans hazır (" + data.w + "×" + data.h + ") — Yüz ara.");
      }
    } catch (err) {
      fotoDurumYaz("Resim alınamadı. «Fotoğraf seç» ile Aç'a bas.");
    }
  }

  async function fotoReferansSecDialog() {
    masaAc("foto");
    fotoDurumYaz("Fotoğraf seç — pencerede Aç'a bas (sürükleme değil).");
    if (window.ruzgarApi && typeof window.ruzgarApi.pickImageFile === "function") {
      try {
        const r = await window.ruzgarApi.pickImageFile();
        if (!r || !r.ok) {
          fotoDurumYaz(r && r.error ? String(r.error) : "Fotoğraf seçilmedi.");
          return;
        }
        fotoDurumYaz("Resim hazırlanıyor…");
        const ok = await fotoReferansSunucudanCek(r.name);
        if (!ok) return;
        return;
      } catch (err) {
        fotoDurumYaz("Seçim hatası — tekrar dene.");
      }
    }
    if (fotoRefFile) fotoRefFile.click();
  }

  async function fotoKartReferansYap(rel, ad) {
    const url = fotoOnizUrl(rel);
    if (!url) return;
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("okunamadi");
      const blob = await res.blob();
      const tip = blob.type || "image/jpeg";
      const file = new File([blob], ad || "referans.jpg", { type: tip });
      fotoRefYukle(file);
      fotoDurumYaz("Referans seçildi: " + (ad || rel) + " — şimdi Yüz ara.");
    } catch (err) {
      fotoDurumYaz("Bu foto açılamadı (önizleme).");
    }
  }

  function fotoDurumYaz(text) {
    if (fotoDurum) fotoDurum.textContent = text || "";
  }

  async function fotoDurumYenile() {
    try {
      const res = await fetch(masaApiKok() + "/api/foto/durum");
      const data = await res.json();
      if (data && data.kok) state.foto.kok = data.kok;
      state.foto.sayi = Number(data.dosya_sayisi) || 0;
      state.foto.katman = data.katman || {};
      if (fotoKok && data.kok && !fotoKok.value) fotoKok.value = data.kok;
      fotoDurumYaz(data.not || "");
      paintFotoKatman(data.sonraki);
      if (state.foto.sayi && !(state.foto.ornek || []).length) {
        const or = await fetch(masaApiKok() + "/api/foto/ornek?limit=36");
        const oj = await or.json();
        state.foto.ornek = oj.ornek || [];
      }
      paintFoto();
    } catch (err) {
      fotoDurumYaz("Sunucu kapalıysa katalog bekler. ForceRestart sonrası tekrar dene.");
    }
  }

  function paintFotoKatman(sonraki) {
    root.querySelectorAll(".ruzgar-masa-foto-layers li").forEach(function (li) {
      const key = li.getAttribute("data-kat");
      const on = !!(state.foto.katman && state.foto.katman[key]);
      li.classList.toggle("is-on", on);
      li.classList.toggle("is-next", !on && key === sonraki);
    });
  }

  async function fotoKatalogTara() {
    const kok = String((fotoKok && fotoKok.value) || state.foto.kok || "").trim();
    if (!kok) {
      fotoDurumYaz("Klasör yolu yaz (ör. D:\\Fotoğraflar).");
      return "Klasör yolu yok.";
    }
    state.foto.kok = kok;
    masaAc("foto");
    fotoDurumYaz("Taranıyor…");
    setStatus("Katalog taranıyor…", "busy");
    try {
      const res = await fetch(masaApiKok() + "/api/foto/katalog", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kok: kok, limit: 20000 }),
      });
      const data = await res.json();
      if (!res.ok) {
        fotoDurumYaz(data.detail || "Tarama başarısız.");
        return data.detail || "Tarama başarısız.";
      }
      state.foto.sayi = Number(data.dosya_sayisi) || 0;
      state.foto.katman = data.katman || {};
      state.foto.ornek = (data.ornek || []).map(function (rel) { return { rel: rel }; });
      fotoDurumYaz(data.not || "");
      paintFotoKatman(data.sonraki);
      paintFoto();
      scheduleSave();
      flashYuzey();
      setStatus(state.foto.sayi + " foto katalog", "ok");
      return data.not || ("Katalog: " + state.foto.sayi);
    } catch (err) {
      fotoDurumYaz("Katalog isteği gitmedi. Sunucu açık mı?");
      return "Katalog isteği gitmedi.";
    }
  }

  async function fotoKatmanKur() {
    masaAc("foto");
    fotoDurumYaz("Yüz + gömme kuruluyor… (büyük arşivde sürebilir)");
    setStatus("Katmanlar…", "busy");
    try {
      const res = await fetch(masaApiKok() + "/api/foto/katman-kur", { method: "POST" });
      const data = await res.json();
      if (!res.ok) {
        fotoDurumYaz(data.detail || "Katman kurulamadı.");
        return data.detail || "Katman kurulamadı.";
      }
      state.foto.katman = data.katman || {};
      fotoDurumYaz(data.not || "");
      paintFotoKatman(data.sonraki);
      paintFoto();
      flashYuzey();
      setStatus(
        (data.yuz_sayisi || 0) + " yüz · " + (data.vektor_sayisi || 0) + " vektör",
        "ok",
      );
      return data.not || "Katmanlar hazır.";
    } catch (err) {
      fotoDurumYaz("Katman isteği gitmedi. OpenCV kurulu mu?");
      return "Katman isteği gitmedi.";
    }
  }

  async function fotoYuzAra() {
    masaAc("foto");
    if (!state.foto.refFile && !state.foto.refUrl) {
      fotoDurumYaz("Önce referans fotoğraf bırak.");
      return "Referans yok.";
    }
    try {
      let res;
      if (state.foto.refFile) {
        const fd = new FormData();
        fd.append("file", state.foto.refFile, state.foto.refName || "referans.jpg");
        fd.append("top_k", "24");
        res = await fetch(masaApiKok() + "/api/foto/eslestir-dosya", {
          method: "POST",
          body: fd,
        });
      } else {
        res = await fetch(masaApiKok() + "/api/foto/eslestir", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ referans_adi: state.foto.refName || "" }),
        });
      }
      const data = await res.json();
      if (!res.ok) {
        fotoDurumYaz(data.detail || data.reply || "Eşleştirme başarısız.");
        return data.detail || "Eşleştirme başarısız.";
      }
      state.foto.sonuclar = Array.isArray(data.sonuclar) ? data.sonuclar : [];
      fotoDurumYaz(data.reply || "");
      if (data.sonraki) paintFotoKatman(data.sonraki);
      await fotoDurumYenile();
      paintFoto();
      flashYuzey();
      setStatus(
        state.foto.sonuclar.length ? state.foto.sonuclar.length + " aday" : "Eşleşme yok",
        state.foto.sonuclar.length ? "ok" : "busy",
      );
      return data.reply || "Yüz araması bitti.";
    } catch (err) {
      fotoDurumYaz("Eşleştirme isteği gitmedi.");
      return "Eşleştirme isteği gitmedi.";
    }
  }

  function wireFoto() {
    if (fotoRef) {
      fotoRef.addEventListener("click", function () {
        void fotoReferansSecDialog();
      });
      fotoRef.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          void fotoReferansSecDialog();
        }
      });
      fotoRef.addEventListener("dragover", function (ev) {
        ev.preventDefault();
        if (ev.dataTransfer) ev.dataTransfer.dropEffect = "copy";
        fotoRef.classList.add("is-drag");
      });
      fotoRef.addEventListener("dragleave", function () {
        fotoRef.classList.remove("is-drag");
      });
      fotoRef.addEventListener("drop", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        fotoRef.classList.remove("is-drag");
        const files = ev.dataTransfer && ev.dataTransfer.files;
        let file = files && files[0];
        if (!file && ev.dataTransfer && ev.dataTransfer.items) {
          for (let i = 0; i < ev.dataTransfer.items.length; i++) {
            if (ev.dataTransfer.items[i].kind === "file") {
              file = ev.dataTransfer.items[i].getAsFile();
              if (file) break;
            }
          }
        }
        if (!file) {
          fotoDurumYaz("Bırakılan şey resim değil. Klasörden bir fotoğraf sürükle.");
          return;
        }
        void fotoReferansDosyaYukle(file);
      });
      fotoRef.addEventListener("paste", function (ev) {
        const items = ev.clipboardData && ev.clipboardData.items;
        if (!items) return;
        for (let i = 0; i < items.length; i++) {
          if (items[i].type && items[i].type.indexOf("image/") === 0) {
            ev.preventDefault();
            void fotoReferansDosyaYukle(items[i].getAsFile());
            return;
          }
        }
      });
    }
    const fotoRefSec = document.getElementById("ruzgar-masa-foto-ref-sec");
    if (fotoRefSec) {
      fotoRefSec.addEventListener("click", function () {
        void fotoReferansSecDialog();
      });
    }
    if (fotoRefFile) {
      fotoRefFile.addEventListener("change", function () {
        const f = fotoRefFile.files && fotoRefFile.files[0];
        fotoRefFile.value = "";
        if (f) void fotoReferansDosyaYukle(f);
      });
    }
    if (fotoTara) fotoTara.addEventListener("click", function () { void fotoKatalogTara(); });
    const fotoKatmanBtn = document.getElementById("ruzgar-masa-foto-katman");
    if (fotoKatmanBtn) fotoKatmanBtn.addEventListener("click", function () { void fotoKatmanKur(); });
    if (fotoEsle) fotoEsle.addEventListener("click", function () { void fotoYuzAra(); });
    if (fotoKok) {
      fotoKok.addEventListener("change", function () {
        state.foto.kok = fotoKok.value.trim();
        scheduleSave();
      });
      fotoKok.addEventListener("focus", function () {
        // Eski yolu kolay silmek için: odaklanınca seç
        try { fotoKok.select(); } catch (err) { /* tarayıcı */ }
      });
      fotoKok.addEventListener("paste", function (ev) {
        // Electron'da native yapıştır bazen susar — panodan elle yaz
        const clip = (ev.clipboardData && ev.clipboardData.getData("text")) || "";
        let text = clip;
        if (!text && window.ruzgarApi && typeof window.ruzgarApi.readClipboardText === "function") {
          text = window.ruzgarApi.readClipboardText() || "";
        }
        if (!text) return;
        ev.preventDefault();
        const start = fotoKok.selectionStart == null ? fotoKok.value.length : fotoKok.selectionStart;
        const end = fotoKok.selectionEnd == null ? start : fotoKok.selectionEnd;
        const clean = String(text).replace(/^["']+|["']+$/g, "").trim();
        fotoKok.setRangeText(clean, start, end, "end");
        state.foto.kok = fotoKok.value.trim();
        scheduleSave();
        setStatus("Yol yapıştırıldı", "ok");
      });
    }
    const fotoKokSec = document.getElementById("ruzgar-masa-foto-kok-sec");
    if (fotoKokSec) {
      fotoKokSec.addEventListener("click", function () {
        void fotoKlasorSec();
      });
    }
  }

  async function fotoKlasorSec() {
    masaAc("foto");
    if (!window.ruzgarApi || typeof window.ruzgarApi.pickSaveDirectory !== "function") {
      fotoDurumYaz("Klasör seçici yok. Kutuya yolu elle yaz veya Ctrl+V dene.");
      if (fotoKok) fotoKok.focus();
      return "Klasör seçici yok.";
    }
    try {
      const r = await window.ruzgarApi.pickSaveDirectory();
      if (!r || !r.ok || !r.abs) {
        fotoDurumYaz("Klasör seçilmedi.");
        return "Klasör seçilmedi.";
      }
      const yol = String(r.abs || "").trim();
      if (fotoKok) fotoKok.value = yol;
      state.foto.kok = yol;
      scheduleSave();
      fotoDurumYaz("Klasör seçildi. Şimdi «Katalog tara».");
      setStatus("Klasör hazır", "ok");
      return yol;
    } catch (err) {
      fotoDurumYaz("Klasör seçilemedi.");
      return "Klasör seçilemedi.";
    }
  }

  function paintGorevler() {
    if (!gorevlerEl) return;
    gorevlerEl.replaceChildren();
    state.gorevler.forEach(function (gorev, index) {
      const li = document.createElement("li");
      if (gorev.done) li.className = "is-done";
      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !!gorev.done;
      cb.addEventListener("change", function () {
        state.gorevler[index].done = cb.checked;
        paintGorevler();
        scheduleSave();
      });
      const span = document.createElement("span");
      span.textContent = gorev.text;
      const sil = document.createElement("button");
      sil.type = "button";
      sil.setAttribute("aria-label", "Sil");
      sil.textContent = "×";
      sil.addEventListener("click", function () {
        state.gorevler.splice(index, 1);
        paintGorevler();
        scheduleSave();
      });
      li.appendChild(cb);
      li.appendChild(span);
      li.appendChild(sil);
      gorevlerEl.appendChild(li);
    });
  }

  function gorevEkle(metin) {
    let text = String(metin || "").trim();
    if (!text) {
      text = window.prompt("Görev:", "");
      if (text == null) return "İptal.";
      text = String(text).trim();
    }
    if (!text) return "Görev boş.";
    if (state.gorevler.length >= 80) return "En fazla 80 görev.";
    state.gorevler.push({ text: text.slice(0, 200), done: false });
    masaAc("notlar");
    paintGorevler();
    scheduleSave();
    flashYuzey();
    return "Görev eklendi: " + text.slice(0, 80);
  }

  function notlarYaz(metin, ekle) {
    const clean = masaTemizMetin(metin, 20000).trim();
    if (!clean || !notlarEl) return "Yazılacak not yok.";
    if (ekle && notlarEl.value.trim()) {
      notlarEl.value = notlarEl.value.replace(/\s+$/, "") + "\n" + clean;
    } else {
      notlarEl.value = clean;
    }
    state.notlar = notlarEl.value;
    masaAc("notlar");
    scheduleSave();
    flashYuzey();
    return (ekle ? "Nota eklendi." : "Not yazıldı.") + "\n" + clean.slice(0, 400);
  }

  function notlarTemizle() {
    if (notlarEl) notlarEl.value = "";
    state.notlar = "";
    state.gorevler = [];
    paintGorevler();
    scheduleSave();
    setStatus("Notlar temizlendi", "ok");
    return "Notlar temizlendi.";
  }

  function syncKodSatir() {
    if (!kodEl || !kodSatir) return;
    const n = String(kodEl.value || "").split(/\n/).length;
    kodSatir.textContent = n + " satır";
  }

  function kodTemizle() {
    if (kodEl) kodEl.value = "";
    state.kod = "";
    syncKodSatir();
    scheduleSave();
    return "Kod temizlendi.";
  }

  function kodYaz(metin) {
    const clean = String(metin || "");
    if (!clean.trim() || !kodEl) return "Kod yok.";
    if (clean.length > 200000) return "Kod çok uzun.";
    kodEl.value = clean;
    state.kod = clean;
    masaAc("kod");
    syncKodSatir();
    scheduleSave();
    flashYuzey();
    return "Kod yazıldı (" + clean.split(/\n/).length + " satır).";
  }

  function paintSes() {
    if (!sesEmpty || !sesView) return;
    const varMi = !!(state.ses && state.ses.url);
    sesEmpty.hidden = varMi;
    sesView.hidden = !varMi;
    if (sesPlayer) sesPlayer.src = varMi ? state.ses.url : "";
    if (sesAd) sesAd.textContent = varMi ? state.ses.name : "";
    if (sesKayitBtn) {
      sesKayitBtn.textContent = state.sesRec ? "Durdur" : "Kayıt";
    }
  }

  function sesTemizle() {
    if (state.sesRec) {
      try { state.sesRec.stop(); } catch (err) { /* mikrofon */ }
      state.sesRec = null;
    }
    if (state.ses.url) {
      try { URL.revokeObjectURL(state.ses.url); } catch (err) { /* tarayıcı */ }
    }
    state.ses = { name: "", url: "" };
    paintSes();
    setStatus("Ses temizlendi", "ok");
    return "Ses temizlendi.";
  }

  function sesYukle(file) {
    if (!file) return "Dosya yok.";
    if (String(file.type || "").indexOf("audio/") !== 0 && !/\.(mp3|wav|ogg|m4a|webm)$/i.test(file.name || "")) {
      return "Yalnız ses dosyası.";
    }
    if (file.size > 60 * 1024 * 1024) return "Ses 60 MB üstü olamaz.";
    if (state.ses.url) {
      try { URL.revokeObjectURL(state.ses.url); } catch (err) { /* tarayıcı */ }
    }
    state.ses = {
      name: String(file.name || "ses").slice(0, 180),
      url: URL.createObjectURL(file),
    };
    masaAc("ses");
    paintSes();
    flashYuzey();
    setStatus("Ses hazır", "ok");
    return "Ses yüzeyde: " + state.ses.name;
  }

  function sesKayitToggle() {
    if (state.sesRec) {
      try { state.sesRec.stop(); } catch (err) { /* mikrofon */ }
      return "Kayıt duruyor…";
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || typeof MediaRecorder === "undefined") {
      return "Bu ortamda kayıt yok. Dosya seçebilirsin.";
    }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      const rec = new MediaRecorder(stream);
      const chunks = [];
      state.sesRec = rec;
      paintSes();
      rec.ondataavailable = function (ev) {
        if (ev.data && ev.data.size) chunks.push(ev.data);
      };
      rec.onstop = function () {
        stream.getTracks().forEach(function (t) { t.stop(); });
        state.sesRec = null;
        const blob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
        const file = new File([blob], "ruzgar-kayit.webm", { type: blob.type });
        sesYukle(file);
      };
      rec.start();
      masaAc("ses");
      setStatus("Kaydediliyor…", "busy");
    }).catch(function () {
      setStatus("Mikrofon izni yok", "busy");
    });
    return "Kayıt başladı.";
  }

  function paintOkuma() {
    if (!okumaEmpty || !okumaText || !okumaPdf) return;
    const o = state.okuma || {};
    const varMi = !!(o.kind && (o.text || o.url));
    okumaEmpty.hidden = varMi;
    okumaText.hidden = !(varMi && o.kind === "text");
    okumaPdf.hidden = !(varMi && o.kind === "pdf");
    if (okumaAd) okumaAd.textContent = varMi ? (o.name || "Dosya") : "Dosya yok";
    if (o.kind === "text") okumaText.textContent = o.text || "";
    if (o.kind === "pdf") okumaPdf.src = o.url || "about:blank";
    else if (okumaPdf.src && okumaPdf.src !== "about:blank") okumaPdf.src = "about:blank";
  }

  function okumaTemizle() {
    if (state.okuma && state.okuma.url) {
      try { URL.revokeObjectURL(state.okuma.url); } catch (err) { /* tarayıcı */ }
    }
    state.okuma = { name: "", kind: "", text: "", url: "" };
    paintOkuma();
    scheduleSave();
    return "Okuma temizlendi.";
  }

  function okumaYukle(file) {
    if (!file) return "Dosya yok.";
    const name = String(file.name || "dosya").slice(0, 180);
    const tip = String(file.type || "");
    const pdf = tip === "application/pdf" || /\.pdf$/i.test(name);
    if (pdf) {
      if (file.size > 40 * 1024 * 1024) return "PDF 40 MB üstü olamaz.";
      if (state.okuma.url) {
        try { URL.revokeObjectURL(state.okuma.url); } catch (err) { /* tarayıcı */ }
      }
      state.okuma = { name: name, kind: "pdf", text: "", url: URL.createObjectURL(file) };
      masaAc("okuma");
      paintOkuma();
      flashYuzey();
      return "PDF açık: " + name;
    }
    if (file.size > 4 * 1024 * 1024) return "Metin 4 MB üstü olamaz.";
    const reader = new FileReader();
    reader.onload = function () {
      state.okuma = {
        name: name,
        kind: "text",
        text: String(reader.result || "").slice(0, 200000),
        url: "",
      };
      masaAc("okuma");
      paintOkuma();
      scheduleSave();
      flashYuzey();
      setStatus("Okuma hazır", "ok");
    };
    reader.onerror = function () { setStatus("Okunamadı", "busy"); };
    reader.readAsText(file);
    return "Okunuyor: " + name;
  }

  function webNormalize(raw) {
    let u = String(raw || "").trim();
    if (!u) return "";
    if (!/^https?:\/\//i.test(u)) u = "https://" + u;
    try {
      const parsed = new URL(u);
      if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return "";
      return parsed.href;
    } catch (err) {
      return "";
    }
  }

  function paintWeb() {
    if (webUrl && state.web && webUrl.value !== state.web) webUrl.value = state.web;
    if (webPane) webPane.classList.toggle("has-url", !!state.web);
    if (webFrame && state.web && webFrame.getAttribute("data-src") !== state.web) {
      webFrame.setAttribute("data-src", state.web);
      webFrame.src = state.web;
    }
  }

  function webAc(raw) {
    const href = webNormalize(raw);
    if (!href) return "Geçerli bir https adresi yaz.";
    state.web = href;
    if (webUrl) webUrl.value = href;
    masaAc("web");
    paintWeb();
    scheduleSave();
    flashYuzey();
    return "Web açık: " + href;
  }

  function webDisarida() {
    const href = webNormalize((webUrl && webUrl.value) || state.web);
    if (!href) return "Adres yok.";
    if (window.ruzgarApi && typeof window.ruzgarApi.openExternalUrl === "function") {
      window.ruzgarApi.openExternalUrl(href);
    } else {
      window.open(href, "_blank", "noopener,noreferrer");
    }
    return "Tarayıcıda açılıyor.";
  }

  function wireYetenekler() {
    if (notlarEl) {
      notlarEl.addEventListener("input", function () {
        state.notlar = notlarEl.value;
        scheduleSave();
      });
    }
    const gorevBtn = document.getElementById("ruzgar-masa-gorev-ekle");
    if (gorevBtn) gorevBtn.addEventListener("click", function () { gorevEkle(); });
    if (kodEl) {
      kodEl.addEventListener("input", function () {
        state.kod = kodEl.value;
        syncKodSatir();
        scheduleSave();
      });
      kodEl.addEventListener("keydown", function (ev) {
        if (ev.key === "Tab") {
          ev.preventDefault();
          const start = kodEl.selectionStart;
          const end = kodEl.selectionEnd;
          const v = kodEl.value;
          kodEl.value = v.slice(0, start) + "  " + v.slice(end);
          kodEl.selectionStart = kodEl.selectionEnd = start + 2;
          state.kod = kodEl.value;
          scheduleSave();
        }
      });
    }
    if (kodDil) {
      kodDil.addEventListener("change", function () {
        state.kodDil = kodDil.value;
        scheduleSave();
      });
    }
    if (sesFile) {
      sesFile.addEventListener("change", function () {
        sesYukle(sesFile.files && sesFile.files[0]);
        sesFile.value = "";
      });
    }
    if (sesKayitBtn) sesKayitBtn.addEventListener("click", function () { sesKayitToggle(); });
    if (sesRoot) {
      sesRoot.addEventListener("dragover", function (ev) { ev.preventDefault(); });
      sesRoot.addEventListener("drop", function (ev) {
        ev.preventDefault();
        sesYukle(ev.dataTransfer && ev.dataTransfer.files && ev.dataTransfer.files[0]);
      });
    }
    if (okumaFile) {
      okumaFile.addEventListener("change", function () {
        okumaYukle(okumaFile.files && okumaFile.files[0]);
        okumaFile.value = "";
      });
    }
    if (webForm) {
      webForm.addEventListener("submit", function (ev) {
        ev.preventDefault();
        webAc(webUrl && webUrl.value);
      });
    }
    if (webYenile) {
      webYenile.addEventListener("click", function () {
        if (state.web && webFrame) {
          webFrame.src = state.web;
          setStatus("Yenilendi", "ok");
        }
      });
    }
  }

  function masaAc(mode) {
    masaSayfa(mode);
  }

  function masaFormulGuvenli(value) {
    return /^=[0-9A-Za-zÇĞİÖŞÜçğıöşü+\-*/().,:\s]+$/.test(value) && value.length <= 180;
  }

  function masaEylemGuvenli(action) {
    const izin = {
      "belge.yaz": ["metin"],
      "belge.ekle": ["metin"],
      "belge.yerine": ["eski", "yeni"],
      "belge.temizle": [],
      "belge.tablo": [],
      "notlar.yaz": ["metin"],
      "notlar.ekle": ["metin"],
      "notlar.gorev": ["metin"],
      "tablo.hucre": ["hucre", "deger"],
      "tablo.sil": ["hucre"],
      "tablo.topla": ["sutun"],
      "tablo.temizle": [],
      "cizim.renk": ["ad"],
      "cizim.cizgi": ["x1", "y1", "x2", "y2"],
      "cizim.kutu": ["x", "y", "w", "h"],
      "cizim.daire": ["x", "y", "rx", "ry"],
      "cizim.temizle": [],
      "sunum.ekle": ["baslik", "metin"],
      "sunum.baslik": ["baslik"],
      "sunum.metin": ["metin"],
      "sunum.temizle": [],
      "sunum.sun": [],
    };
    const renkli = { "cizim.cizgi": 1, "cizim.kutu": 1, "cizim.daire": 1 };
    if (!action || typeof action !== "object" || Array.isArray(action)) return false;
    const keys = Object.keys(action);
    const eylemAd = String(action.eylem || "");
    const need = izin[eylemAd];
    const renkVar = action.renk != null && renkli[eylemAd] ? 1 : 0;
    const ekstra = eylemAd === "belge.tablo" ? 2 : 0;
    if (!need || keys.length > need.length + 1 + renkVar + ekstra) return false;
    const yazi = { metin: 1, deger: 1, hucre: 1, ad: 1, baslik: 1, eski: 1, yeni: 1, sutun: 1 };
    for (let i = 0; i < keys.length; i++) {
      if (keys[i] === "eylem" || need.indexOf(keys[i]) >= 0) continue;
      if (keys[i] === "renk" && renkli[eylemAd]) continue;
      if (eylemAd === "belge.tablo" && (keys[i] === "satir" || keys[i] === "sutun")) {
        if (typeof action[keys[i]] !== "number" || !isFinite(action[keys[i]])) return false;
        continue;
      }
      return false;
    }
    if (action.renk != null) {
      const renkAd = masaHarf(action.renk);
      if (!/^(siyah|mavi|kirmizi|yesil)$/.test(renkAd) || !MASA_RENK[renkAd]) return false;
    }
    for (let i = 0; i < need.length; i++) {
      const key = need[i];
      const value = action[key];
      if (yazi[key]) {
        if (typeof value !== "string" || !value.trim()) return false;
      } else if (typeof value !== "number" || !isFinite(value)) {
        return false;
      }
    }
    return true;
  }

  function masaHucreYaz(letters, rowText, raw) {
    const c = COLS.indexOf(String(letters || "").toUpperCase());
    const r = Number(rowText) - 1;
    if (c < 0 || r < 0 || r >= ROWS) return "Hücre A1 ile L28 arasında olmalı.";
    const value = masaTemizMetin(raw, 180).trim();
    if (!value) return "Hücreye yazılacak değer yok.";
    if (value.charAt(0) === "=" && !masaFormulGuvenli(value)) {
      return "Formülde yalnız sayı, hücre ve TOPLA, ORTALAMA, MİN, MAK kullanılabilir.";
    }
    state.sheet[r][c] = value;
    paintSheet();
    scheduleSave();
    masaAc("tablo");
    return addr(r, c) + " yazıldı: " + value;
  }

  function masaBelgeYaz(text, append) {
    const clean = masaTemizMetin(text, 8000).trim();
    if (!clean) return "Yazılacak metin yok.";
    const p = document.createElement("p");
    p.textContent = clean;
    if (append && (belge.innerText || "").trim()) {
      belge.appendChild(p);
    } else if (append) {
      belge.appendChild(p);
    } else {
      belge.innerHTML = "";
      belge.appendChild(p);
    }
    scheduleSave();
    masaAc("belge");
    flashYuzey();
    return (append ? "Belgeye eklendi." : "Belge yazıldı.") + "\n" + clean;
  }

  function masaCizHazir() {
    ensurePaper();
    state.ink = true;
    strokeStyle();
    masaAc("cizim");
  }

  function masaSlaytEkle(title, body) {
    const baslik = masaTemizMetin(title, 120).trim();
    const metin = masaTemizMetin(body, 2000).trim();
    if (!baslik && !metin) return "Slayt boş olamaz.";
    if (state.slides.length >= 12) return "En fazla 12 slayt.";
    const only = state.slides.length === 1 ? state.slides[0] : null;
    const bosIlk = only && (!String(only.title || "").trim() && !String(only.body || "").trim()
      || (only.title === "Başlık" && only.body === "Metin"));
    const slide = { title: baslik, body: metin, bg: "#1c1a16", fg: "#f7f4ec" };
    if (bosIlk) state.slides[0] = slide;
    else state.slides.push(slide);
    state.slideIndex = state.slides.length - 1;
    renderTools();
    renderSlides();
    scheduleSave();
    masaAc("sunum");
    const satir = [baslik, metin].filter(Boolean).join("\n");
    return "Slayt hazır.\n" + satir;
  }

  function masaUygula(action) {
    if (!action || typeof action !== "object") return "Komut geçersiz.";
    const eylem = String(action.eylem || "");
    if (eylem === "belge.oku") {
      const yazi = String(belge.innerText || "").replace(/\u00a0/g, " ").trim();
      masaAc("belge");
      return yazi ? "Belgede: " + yazi : "Belge boş.";
    }
    if (eylem === "tablo.oku") {
      const hucre = String(action.hucre || "");
      const bak = hucre.match(/^([A-L])(\d{1,2})$/);
      if (!bak) return "Hücre A1 biçiminde olmalı.";
      const c = COLS.indexOf(bak[1]);
      const r = Number(bak[2]) - 1;
      if (c < 0 || r < 0 || r >= ROWS) return "Hücre A1 ile L28 arasında olmalı.";
      const deger = String(state.sheet[r][c] || "").trim();
      masaAc("tablo");
      return deger ? hucre + ": " + deger : hucre + " boş.";
    }
    if (eylem === "sunum.oku") {
      const slide = currentSlide();
      const baslik = String((slide && slide.title) || "").trim();
      masaAc("sunum");
      return baslik ? "Başlık: " + baslik : "Başlık yok.";
    }
    if (eylem === "cizim.oku") {
      masaAc("cizim");
      return state.ink ? "Çizimde iz var." : "Çizim boş.";
    }
    if (eylem === "belge.yaz") return masaBelgeYaz(action.metin, false);
    if (eylem === "belge.ekle") return masaBelgeYaz(action.metin, true);
    if (eylem === "notlar.yaz") return notlarYaz(action.metin, false);
    if (eylem === "notlar.ekle") return notlarYaz(action.metin, true);
    if (eylem === "notlar.gorev") return gorevEkle(action.metin);
    if (eylem === "belge.yerine") {
      const eski = masaTemizMetin(action.eski, 180).trim();
      const yeni = masaTemizMetin(action.yeni, 400).trim();
      if (!eski || !yeni) return "Metin belgede yok.";
      if (!belgeMetinNodunaYaz(eski, yeni)) return "Metin belgede yok.";
      const sonra = String(belge.innerText || "").replace(/\u00a0/g, " ").replace(/\s+$/, "");
      scheduleSave();
      masaAc("belge");
      flashYuzey();
      return "Belgede değişti.\n" + eski + " yerine " + yeni + "\n" + sonra;
    }
    if (eylem === "belge.temizle") {
      belge.innerHTML = "";
      scheduleSave();
      masaAc("belge");
      return "Belge temizlendi.";
    }
    if (eylem === "belge.tablo") {
      return belgeTabloEkle(action.satir || 3, action.sutun || 3);
    }
    if (eylem === "tablo.hucre") {
      const hucre = String(action.hucre || "");
      const m = hucre.match(/^([A-La-l])(\d{1,2})$/);
      if (!m) return "Hücre A1 biçiminde olmalı.";
      return masaHucreYaz(m[1], m[2], action.deger);
    }
    if (eylem === "tablo.sil") {
      const hucre = String(action.hucre || "");
      const silinen = hucre.match(/^([A-La-l])(\d{1,2})$/);
      if (!silinen) return "Hücre A1 biçiminde olmalı.";
      const c = COLS.indexOf(silinen[1].toUpperCase());
      const r = Number(silinen[2]) - 1;
      if (c < 0 || r < 0 || r >= ROWS) return "Hücre A1 ile L28 arasında olmalı.";
      state.sheet[r][c] = "";
      paintSheet();
      scheduleSave();
      masaAc("tablo");
      return silinen[1].toUpperCase() + silinen[2] + " silindi.";
    }
    if (eylem === "tablo.topla") {
      const c = COLS.indexOf(String(action.sutun || "").toUpperCase());
      if (c < 0) return "Sütun A ile L arasında olmalı.";
      let toplam = 0;
      for (let r = 0; r < ROWS; r++) {
        const raw = String(state.sheet[r][c] || "").trim().replace(",", ".");
        if (!raw) continue;
        const n = Number(raw);
        if (!isFinite(n)) continue;
        toplam += n;
      }
      const yazi = String(Math.round(toplam * 1000) / 1000);
      masaAc("tablo");
      return COLS[c] + " sütunu toplamı: " + yazi;
    }
    if (eylem === "tablo.temizle") {
      state.sheet = blankSheet();
      paintSheet();
      scheduleSave();
      masaAc("tablo");
      return "Tablo temizlendi.";
    }
    if (eylem === "cizim.renk") {
      const renk = MASA_RENK[masaHarf(action.ad)];
      if (!renk) return "Renk: siyah, kırmızı, mavi, yeşil, altın, beyaz.";
      state.draw.color = renk;
      return "Kalem rengi değişti.";
    }
    if (eylem === "cizim.cizgi" || eylem === "cizim.kutu" || eylem === "cizim.daire") {
      if (action.renk) {
        const renk = MASA_RENK[masaHarf(action.renk)];
        if (!renk) return "Renk: siyah, kırmızı, mavi, yeşil.";
        state.draw.color = renk;
        state.draw.tool = "kalem";
      }
      let ciz = null;
      if (eylem === "cizim.cizgi") {
        ciz = {
          x1: masaSayi(action.x1, 0, BW),
          y1: masaSayi(action.y1, 0, BH),
          x2: masaSayi(action.x2, 0, BW),
          y2: masaSayi(action.y2, 0, BH),
        };
        if (ciz.x1 == null || ciz.y1 == null || ciz.x2 == null || ciz.y2 == null) return "Çizgi koordinatı geçersiz.";
      } else if (eylem === "cizim.kutu") {
        ciz = {
          x: masaSayi(action.x, 0, BW),
          y: masaSayi(action.y, 0, BH),
          w: masaSayi(action.w, 1, BW),
          h: masaSayi(action.h, 1, BH),
        };
        if (ciz.x == null || ciz.y == null || ciz.w == null || ciz.h == null) return "Kutu ölçüsü geçersiz.";
      } else {
        ciz = {
          x: masaSayi(action.x, 0, BW),
          y: masaSayi(action.y, 0, BH),
          rx: masaSayi(action.rx, 1, 800),
          ry: masaSayi(action.ry, 1, 800),
        };
        if (ciz.x == null || ciz.y == null || ciz.rx == null || ciz.ry == null) return "Daire ölçüsü geçersiz.";
      }
      masaCizHazir();
      takeSnap();
      ctx.beginPath();
      if (eylem === "cizim.cizgi") {
        ctx.moveTo(ciz.x1, ciz.y1);
        ctx.lineTo(ciz.x2, ciz.y2);
        ctx.stroke();
      } else if (eylem === "cizim.kutu") {
        ctx.strokeRect(ciz.x, ciz.y, ciz.w, ciz.h);
      } else {
        ctx.ellipse(ciz.x, ciz.y, ciz.rx, ciz.ry, 0, 0, Math.PI * 2);
        ctx.stroke();
      }
      scheduleSave();
      if (eylem === "cizim.cizgi") return "Çizgi çizildi.";
      if (eylem === "cizim.kutu") return "Kutu çizildi.";
      return "Daire çizildi.";
    }
    if (eylem === "cizim.temizle") {
      ensurePaper();
      clearPaper();
      masaAc("cizim");
      return "Çizim temizlendi.";
    }
    if (eylem === "sunum.ekle") return masaSlaytEkle(action.baslik, action.metin);
    if (eylem === "sunum.baslik") {
      const baslik = masaTemizMetin(action.baslik, 120).trim();
      if (!baslik) return "Başlık boş.";
      if (!state.slides.length) return "Slayt yok.";
      const i = state.slideIndex >= 0 && state.slideIndex < state.slides.length ? state.slideIndex : 0;
      state.slides[i].title = baslik;
      renderTools();
      renderSlides();
      scheduleSave();
      masaAc("sunum");
      return "Slayt başlığı değişti.\n" + baslik;
    }
    if (eylem === "sunum.metin") {
      const metin = masaTemizMetin(action.metin, 2000).trim();
      if (!metin) return "Metin boş.";
      if (!state.slides.length) return "Slayt yok.";
      const i = state.slideIndex >= 0 && state.slideIndex < state.slides.length ? state.slideIndex : 0;
      state.slides[i].body = metin;
      renderTools();
      renderSlides();
      scheduleSave();
      masaAc("sunum");
      return "Slayt metni değişti.\n" + metin;
    }
    if (eylem === "sunum.temizle") {
      state.slides = [{ title: "", body: "", bg: "#1c1a16", fg: "#f7f4ec" }];
      state.slideIndex = 0;
      present.hidden = true;
      renderTools();
      renderSlides();
      scheduleSave();
      masaAc("sunum");
      return "Sunum temizlendi.";
    }
    if (eylem === "sunum.sun") {
      if (!state.slides.length) return "Slayt yok.";
      masaAc("sunum");
      startPresent();
      return "Sunum açıldı. Esc kapatır.";
    }
    return "";
  }

  function masaYardim() {
    return [
      "Çalışma yüzeyi — tek sahne, yetenekler:",
      "Birincil: sohbet · belge · tablo · çizim · sunum · medya · foto",
      "İkincil: notlar · kod · ses · okuma · web",
      "Foto: fotoyu aç · katalog tara · referans bırak · yüz ara (katmanlı)",
      "Köprü: bunu tercümeye gönder · kodu programlamaya gönder · belgeyi sese gönder",
      "Aç: belgeyi aç · notları aç · kodu aç · sesi aç · okumayı aç · web aç",
      "belgeye … yaz · belgeye tablo ekle · belgeye 4x2 tablo ekle · resim: bırak/yapıştır",
      "notlara … yaz · göreve … ekle · koda … yaz",
      "tabloda A1 e 10 yaz · çizime kutu çiz · sunuma … slaytı ekle: …",
      "web aç https://örnek.com · medya/ses/okuma: dosya bırak",
      "Derin iş: Video / Ses / Okuma / Programlama / Tercüme (köprü ile)",
    ].join("\n");
  }

  function masaOldu(cevap) {
    return /yazıldı|eklendi|işlendi|çizildi|cizildi|hazır|değişti|açıldı|temizlendi|silindi|toplamı|toplami|boş|Belgede:|Başlık|Çizim|yüzeyde|yuzeyde|Resim|Video|Medya|Not|Görev|Kod|Web|PDF|Ses|Okuma|tablo|seç|aktarıldı|aktarildi|Köprü|Kopru/.test(String(cevap || ""));
  }

  function masaAnlikAl() {
    let piksel = null;
    try {
      if (paperReady && canvas.width && ctx) piksel = ctx.getImageData(0, 0, canvas.width, canvas.height);
    } catch (err) {
      piksel = null;
    }
    return {
      belge: belge.innerHTML,
      sheet: JSON.parse(JSON.stringify(state.sheet)),
      slides: JSON.parse(JSON.stringify(state.slides)),
      slideIndex: state.slideIndex,
      ink: !!state.ink,
      piksel: piksel,
      color: state.draw.color,
      tool: state.draw.tool,
    };
  }

  function masaAnlikYaz(anlik) {
    belge.innerHTML = anlik.belge;
    state.sheet = anlik.sheet;
    paintSheet();
    state.slides = anlik.slides.length ? anlik.slides : state.slides;
    state.slideIndex = anlik.slideIndex;
    state.draw.color = anlik.color;
    state.draw.tool = anlik.tool;
    renderTools();
    renderSlides();
    if (anlik.piksel && ctx) {
      try { ctx.putImageData(anlik.piksel, 0, 0); } catch (err) { /* tuval eski kareyi tutamadı */ }
      state.ink = !!anlik.ink;
    } else if (!anlik.ink) {
      ensurePaper();
      ctx.fillStyle = "#f4f0e6";
      ctx.fillRect(0, 0, BW, BH);
      state.ink = false;
    }
    scheduleSave();
  }

  function masaListeUygula(liste) {
    const anlik = masaAnlikAl();
    const notlar = [];
    for (let i = 0; i < liste.length; i++) {
      const cevap = masaUygula(liste[i]);
      if (!masaOldu(cevap)) {
        if (notlar.length) masaAnlikYaz(anlik);
        const once = notlar.length ? "\nÖnceki parçalar geri alındı." : "";
        return (i + 1) + ". parça durdu. " + (cevap || "Masa değişmedi.") + once;
      }
      notlar.push(cevap);
    }
    return notlar.join("\n");
  }

  function masaKomutSonuc(reply) {
    const text = String(reply || "");
    if (masaOldu(text) || /açık\.|acik\./i.test(text)) {
      flashYuzey();
      setStatus("Uygulandı", "ok");
      syncChip();
    }
    return { handled: true, reply: text };
  }

  function masaKomutCoz(text) {
    const raw = String(text || "").trim();
    if (!raw || raw.length > 9000) return null;
    if (window.ruzgarMasaSoz && typeof window.ruzgarMasaSoz.coz === "function") {
      const duz = window.ruzgarMasaSoz.coz(raw);
      if (duz && duz.red) {
        return {
          handled: true,
          reply: "Bunu yapmadım. Yüzey değişmedi. Şöyle söyle: belgeye selam yaz, tabloda A1 e 10 yaz, çizime kutu çiz, sunuma Hoş geldin slaytı ekle: bugün.",
        };
      }
      if (duz && duz.bak) return null;
      if (duz && duz.liste) return masaKomutSonuc(masaListeUygula(duz.liste));
      if (duz && duz.eylem) return masaKomutSonuc(masaUygula(duz));
    }
    const sade = raw
      .replace(/^[Ll]ütfen\s+/, "")
      .replace(/\s+(mısın|misin|misiniz|mısınız|musun|musunuz)[.!?]*$/i, "")
      .replace(/\?+$/g, "")
      .trim();
    const low = typeof window.ruzgarKomutGovdesi === "function"
      ? window.ruzgarKomutGovdesi(sade)
      : masaHarf(sade);
    if (/^(masa yardim|calisma masasi yardim|masa komutlari|yuzey yardim|calisma yuzeyi yardim)$/.test(low)) {
      return { handled: true, reply: masaYardim() };
    }
    if (/^(sohbet|sohbeti goster|sohbeti ac|sahne|robota don)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("sohbet"));
    }
    if (/^(belgeyi ac|belgeyi goster|belge ac|belge goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("belge"));
    }
    if (/^(tabloyu ac|tabloyu goster|tablo ac|tablo goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("tablo"));
    }
    if (/^(cizimi ac|cizimi goster|cizim ac|cizim goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("cizim"));
    }
    if (/^(sunumu ac|sunumu goster|sunum ac|sunum goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("sunum"));
    }
    if (/^(medyayi ac|medyayi goster|medya ac|medya goster|resmi goster|videoyu goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("medya"));
    }
    if (/^(fotoyu ac|fotoyu goster|foto ac|foto goster|fotograf ac|fotografi ac)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("foto"));
    }
    m = sade.match(/^(?:bunu|belgeyi|kodu|notlari|notları|metni|yuzeyi|yüzeyi|tabloyu|sunumu|okumayi|okumayı)\s+(tercumeye|tercümeye|programlamaya|sese|videoya|hafizaya|hafızaya|okumaya|mimara)\s+g[öo]nder$/i);
    if (m) return masaKomutSonuc(yuzeyMotorGonder(m[1]));
    m = sade.match(/^(?:kopru|köprü)\s*[:\-]?\s*(tercume|tercüme|programlama|ses|video|hafiza|hafıza|okuma|mimar)$/i);
    if (m) return masaKomutSonuc(yuzeyMotorGonder(m[1]));
    if (/^(katalog tara|foto katalog|fotografi tara)$/.test(low)) {
      return { handled: true, reply: "Katalog taranıyor…", asyncFoto: "tara" };
    }
    if (/^(yuz ara|yuz eslestir|fotograf ara|yuzu bul)$/.test(low)) {
      return { handled: true, reply: "Yüz araması…", asyncFoto: "esle" };
    }
    if (/^(notlari ac|notlari goster|notlar ac|notlar goster|notu ac)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("notlar"));
    }
    if (/^(kodu ac|kodu goster|kod ac|kod goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("kod"));
    }
    if (/^(sesi ac|sesi goster|ses ac|ses goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("ses"));
    }
    if (/^(okumayi ac|okumayi goster|okuma ac|okuma goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("okuma"));
    }
    if (/^(web ac|web goster|webi ac|webi goster)$/.test(low)) {
      return masaKomutSonuc(masaSayfa("web"));
    }
    let m = sade.match(/^(?:web ac|site ac|sayfa ac)\s+(.+)$/i);
    if (m) return masaKomutSonuc(webAc(m[1]));
    m = sade.match(/^(?:notlara|nota)\s+(.+?)\s+yaz$/i);
    if (m) return masaKomutSonuc(notlarYaz(m[1], false));
    m = sade.match(/^(?:notlara|nota)\s+(.+?)\s+ekle$/i);
    if (m) return masaKomutSonuc(notlarYaz(m[1], true));
    m = sade.match(/^(?:goreve|göreve|gorev|görev)\s+(.+?)\s+ekle$/i);
    if (m) return masaKomutSonuc(gorevEkle(m[1]));
    m = sade.match(/^(?:koda|kode)\s+yaz\s*[:\-]?\s*([\s\S]+)$/i);
    if (m) return masaKomutSonuc(kodYaz(m[1]));
    m = sade.match(/^(belgeye yaz|belge yaz|belgeye ekle|belge ekle)\s*[:\-]?\s*([\s\S]+)$/i);
    if (m) return masaKomutSonuc(masaBelgeYaz(m[2], /ekle/i.test(m[1])));
    if (/^(belgeyi temizle|belge temizle)$/i.test(sade)) {
      return masaKomutSonuc(masaUygula({ eylem: "belge.temizle" }));
    }
    if (/^belgeye\s+tablo\s+ekle$/i.test(sade)) {
      return masaKomutSonuc(belgeTabloEkle(3, 3));
    }
    m = sade.match(/^belgeye\s+(\d{1,2})\s*[x×]\s*(\d{1,2})\s+tablo\s+ekle$/i);
    if (m) return masaKomutSonuc(belgeTabloEkle(m[1], m[2]));
    if (/^(belgeye\s+resim\s+ekle|belgeye\s+gorsel\s+ekle|belgeye\s+görsel\s+ekle)$/i.test(sade)) {
      masaAc("belge");
      const inp = document.getElementById("ruzgar-masa-belge-img");
      if (inp) inp.click();
      return masaKomutSonuc("Resim seç — dosya penceresi açıldı.");
    }
    if (/^tablo\s*:\s*\n/i.test(sade)) {
      const lines = sade.split(/\n/).slice(1);
      const notes = [];
      lines.forEach(function (line) {
        const cell = line.trim().match(/^([A-La-l])(\d{1,2})\s*(?:=|:)?\s*(.+)$/);
        if (cell) notes.push(masaHucreYaz(cell[1], cell[2], cell[3]));
      });
      if (!notes.length) return { handled: true, reply: "Tablo satırı A1 10 biçiminde olmalı." };
      return masaKomutSonuc(notes.join(" "));
    }
    m = sade.match(/^(?:tablo|hucre|hücre)\s+([A-La-l])(\d{1,2})\s*(?:=|:)?\s*([\s\S]+)$/i);
    if (m) return masaKomutSonuc(masaHucreYaz(m[1], m[2], m[3]));
    if (/^(tabloyu temizle|tablo temizle)$/i.test(sade)) {
      return masaKomutSonuc(masaUygula({ eylem: "tablo.temizle" }));
    }
    m = sade.match(/^(?:renk)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\s*$/i);
    if (m) return masaKomutSonuc(masaUygula({ eylem: "cizim.renk", ad: m[1] }));
    m = sade.match(/^(?:çizgi|cizgi)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$/i);
    if (m) return masaKomutSonuc(masaUygula({ eylem: "cizim.cizgi", x1: m[1], y1: m[2], x2: m[3], y2: m[4] }));
    m = sade.match(/^(?:kutu)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$/i);
    if (m) return masaKomutSonuc(masaUygula({ eylem: "cizim.kutu", x: m[1], y: m[2], w: m[3], h: m[4] }));
    m = sade.match(/^(?:daire)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$/i);
    if (m) return masaKomutSonuc(masaUygula({ eylem: "cizim.daire", x: m[1], y: m[2], rx: m[3], ry: m[4] }));
    if (/^(çizimi temizle|cizimi temizle|çizim temizle|cizim temizle)$/i.test(sade)) {
      return masaKomutSonuc(masaUygula({ eylem: "cizim.temizle" }));
    }
    m = sade.match(/^slayt ekle\s*[:\-]?\s*([\s\S]+?)\s*(?:\|\s*|\n)\s*([\s\S]+)$/i);
    if (m) return masaKomutSonuc(masaSlaytEkle(m[1], m[2]));
    if (/^(sunumu temizle|sunum temizle|slaytlari temizle|slaytları temizle)$/i.test(sade)) {
      return masaKomutSonuc(masaUygula({ eylem: "sunum.temizle" }));
    }
    if (/^(sun|sunumu aç|sunumu ac|sunumu başlat|sunumu baslat)$/i.test(sade)) {
      return masaKomutSonuc(masaUygula({ eylem: "sunum.sun" }));
    }
    if (/^(medyayi temizle|medya temizle)$/i.test(sade)) {
      return masaKomutSonuc(medyaTemizle());
    }
    if (/^(notlari temizle|notlar temizle)$/i.test(sade)) {
      return masaKomutSonuc(notlarTemizle());
    }
    if (/^(kodu temizle|kod temizle)$/i.test(sade)) {
      return masaKomutSonuc(kodTemizle());
    }
    if (/^(sesi temizle|ses temizle)$/i.test(sade)) {
      return masaKomutSonuc(sesTemizle());
    }
    if (/^(okumayi temizle|okuma temizle)$/i.test(sade)) {
      return masaKomutSonuc(okumaTemizle());
    }
    return null;
  }

  let masaBekleyen = null;
  const MASA_BEKLEYEN_ANAHTAR = "ruzgarMasaBekleyenV1";

  function masaBekleyenYaz(eylem) {
    masaBekleyen = eylem || null;
    try {
      if (masaBekleyen) localStorage.setItem(MASA_BEKLEYEN_ANAHTAR, JSON.stringify(masaBekleyen));
      else localStorage.removeItem(MASA_BEKLEYEN_ANAHTAR);
    } catch (err) { /* tarayıcı saklamazsa bu oturumda durur */ }
  }

  function masaBekleyenOku() {
    if (masaBekleyen) return masaBekleyen;
    try {
      const ham = localStorage.getItem(MASA_BEKLEYEN_ANAHTAR);
      if (ham) masaBekleyen = JSON.parse(ham);
    } catch (err) {
      masaBekleyen = null;
    }
    return masaBekleyen;
  }

  function masaApiKok() {
    const kok = typeof API === "string" ? API : "";
    return String(kok || "http://127.0.0.1:8779").replace(/\/$/, "");
  }

  function masaGorunen(masa) {
    if (masa === "belge") return String(belge.innerText || belge.textContent || "").replace(/\s+/g, " ").trim().slice(0, 1200);
    if (masa === "tablo") {
      const satirlar = [];
      for (let r = 0; r < ROWS && satirlar.length < 40; r++) {
        for (let c = 0; c < COLS.length; c++) {
          const deger = String(state.sheet[r][c] || "").trim();
          if (deger) satirlar.push(COLS[c] + (r + 1) + ": " + deger);
        }
      }
      return satirlar.join("\n").slice(0, 1200);
    }
    if (masa === "cizim") return masaCizimGor();
    return state.slides.map(function (slayt, i) {
      return "Slayt " + (i + 1) + ": " + String(slayt.title || "") + " | " + String(slayt.body || "");
    }).join("\n").slice(0, 1200);
  }

  function masaCizimGor() {
    ensurePaper();
    if (!state.ink || !ctx || !canvas.width) return "Çizim boş.";
    let kare = null;
    try { kare = ctx.getImageData(0, 0, canvas.width, canvas.height); } catch (err) { kare = null; }
    if (!kare || !window.ruzgarMasaGoz) return "Çizimde iz var.";
    return window.ruzgarMasaGoz.cizimSoz(kare.data, canvas.width, canvas.height);
  }

  async function masaBak(masa) {
    masaBekleyenYaz(null);
    if (masa === "cizim") {
      try {
        await fetch(masaApiKok() + "/api/programlama/bekleyen-birak", { method: "POST" });
      } catch (err) { /* klasör önerisi duruyorsa da çizime bakılır */ }
      const yazi = masaCizimGor();
      masaAc("cizim");
      return { handled: true, reply: "Gördüm: " + yazi + "\nÖneri çıkmadı. Çizim aynı." };
    }
    const yazi = masaGorunen(masa);
    try {
      await fetch(masaApiKok() + "/api/programlama/bekleyen-birak", { method: "POST" });
    } catch (err) { /* klasör önerisi duruyorsa da masa bakışı sürer */ }
    let data = {};
    try {
      const res = await fetch(masaApiKok() + "/api/programlama/masa-bak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ masa: masa, yazi: yazi }),
      });
      data = await res.json();
    } catch (err) {
      return { handled: true, reply: "Öneri çıkmadı. Masa aynı." };
    }
    if (data && data.eylem) masaBekleyenYaz(data.eylem);
    masaAc(masa);
    return { handled: true, reply: (data && data.reply) || "Masa aynı." };
  }

  window.ruzgarMasaBak = function (masa) {
    return masaBak(String(masa || ""));
  };

  window.ruzgarMasaBekleyenUygula = function () {
    const eylem = masaBekleyenOku();
    if (!eylem) return null;
    masaBekleyenYaz(null);
    return { handled: true, reply: masaUygula(eylem) || "Masa değişmedi." };
  };

  window.ruzgarMasaBekleyenSil = function () {
    masaBekleyenYaz(null);
  };

  window.ruzgarMasaSayfa = function (kind) {
    return masaSayfa(String(kind || ""));
  };

  window.ruzgarYuzey = {
    ac: function (kind) { return masaSayfa(String(kind || "")); },
    yetenek: function () { return sayfa === "sohbet" ? "sohbet" : state.mode; },
    paket: yuzeyPaketAl,
    gonder: yuzeyMotorGonder,
    medyaYukle: medyaYukle,
    medyaTemizle: medyaTemizle,
  };

  window.ruzgarMasaParcalari = function (cumleler) {
    const liste = Array.isArray(cumleler) ? cumleler : [];
    const anlik = masaAnlikAl();
    const notlar = [];
    for (let i = 0; i < liste.length; i++) {
      const duz = window.ruzgarMasaSoz && window.ruzgarMasaSoz.coz(liste[i]);
      if (!duz || duz.red || duz.bak) {
        masaAnlikYaz(anlik);
        return { ok: false, reply: (i + 1) + ". parça durdu. Masa değişmedi." };
      }
      const adimlar = duz.liste || [duz];
      for (let j = 0; j < adimlar.length; j++) {
        const cevap = masaUygula(adimlar[j]);
        if (!masaOldu(cevap)) {
          masaAnlikYaz(anlik);
          return { ok: false, reply: (i + 1) + ". parça durdu. " + (cevap || "Masa değişmedi.") };
        }
        notlar.push(cevap);
      }
    }
    return {
      ok: true,
      reply: notlar.join("\n"),
      geri: function () { masaAnlikYaz(anlik); },
    };
  };

  window.ruzgarMasaKomut = function (text) {
    try {
      const hit = masaKomutCoz(text);
      if (hit && hit.asyncFoto === "tara") {
        return fotoKatalogTara().then(function (reply) {
          return { handled: true, reply: reply };
        });
      }
      if (hit && hit.asyncFoto === "esle") {
        return fotoYuzAra().then(function (reply) {
          return { handled: true, reply: reply };
        });
      }
      return hit;
    } catch (err) {
      return { handled: true, reply: "Masa komutu uygulanamadı." };
    }
  };

  window.ruzgarMasaFence = function (text) {
    const found = String(text || "").match(/```ruzgar-masa\s*([\s\S]{2,6000}?)```/);
    if (!found) return null;
    let data = null;
    try {
      data = JSON.parse(found[1]);
    } catch (err) {
      return null;
    }
    const list = Array.isArray(data) ? data.slice(0, 8) : [data];
    if (!list.length || list.length > 8) return null;
    for (let i = 0; i < list.length; i++) {
      if (!masaEylemGuvenli(list[i])) return null;
    }
    const notes = [];
    for (let i = 0; i < list.length; i++) {
      const note = masaUygula(list[i]);
      if (!note) return null;
      notes.push(note);
    }
    const clean = String(text).replace(/```ruzgar-masa\s*[\s\S]*?```/g, "").trim();
    return { clean: (clean ? clean + "\n\n" : "") + "Masa: " + notes.join(" ") };
  };

  function paintSpeech() {
    const soz = document.getElementById("ruzgar-sahne-soz");
    const sahneFace = document.getElementById("ruzgar-sahne-face");
    if (!soz) return;
    const nodes = document.querySelectorAll("#chat-messages .bubble.assistant");
    let text = "";
    for (let i = nodes.length - 1; i >= 0; i--) {
      if (nodes[i].classList.contains("chat-welcome")) continue;
      text = (nodes[i].innerText || "").replace(/\s+\n/g, "\n").trim();
      if (text) break;
    }
    soz.textContent = text ? (text.length > 700 ? text.slice(0, 700) + "…" : text) : "Yaz. Cevabı ben buradan söyleyeyim.";
    if (!text || !sahneFace) return;
    sahneFace.classList.add("is-talking");
    clearTimeout(sahneTimer);
    sahneTimer = setTimeout(function () {
      const live = document.getElementById("ruzgar-face");
      if (!live || !live.classList.contains("is-talking")) sahneFace.classList.remove("is-talking");
    }, Math.min(9000, 1400 + text.length * 18));
  }

  function syncSahne() {
    const motor = document.body.dataset.motor || "genel";
    const on = motor === "genel" && sayfa === "sohbet";
    document.body.classList.toggle("ruzgar-sahne-on", on);
    const back = document.getElementById("ruzgar-masa-sahne");
    if (back) back.hidden = on;
    root.querySelectorAll("[data-masa]").forEach(function (btn) {
      const id = btn.getAttribute("data-masa");
      const active = on ? id === "sohbet" : id === state.mode;
      btn.classList.toggle("is-on", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });
    syncChip();
    if (on) paintSpeech();
  }

  function wireSahne() {
    const openDesk = document.getElementById("ruzgar-sahne-masa");
    const backStage = document.getElementById("ruzgar-masa-sahne");
    if (openDesk) {
      openDesk.addEventListener("click", function () {
        masaSayfa(state.mode === "sohbet" ? "belge" : state.mode);
      });
    }
    if (backStage) {
      backStage.addEventListener("click", function () {
        masaSayfa("sohbet");
      });
    }
    const chat = document.getElementById("chat-messages");
    if (chat && window.MutationObserver) {
      new MutationObserver(function () { paintSpeech(); }).observe(chat, { childList: true, subtree: true });
    }
    if (window.MutationObserver) {
      new MutationObserver(syncSahne).observe(document.body, { attributes: true, attributeFilter: ["data-motor"] });
    }
  }

  load();
  buildSheet();
  ensurePaper();
  showMode(YETENEK_AD[state.mode] && state.mode !== "sohbet" ? state.mode : "belge", { keep: true });
  renderSlides();
  paintMedya();
  paintFoto();
  paintGorevler();
  paintSes();
  paintOkuma();
  paintWeb();
  syncKodSatir();
  setStatus("Hazır", "ok");
  wireSahne();
  wireMedya();
  wireFoto();
  wireBelgeKarma();
  wireYetenekler();
  syncSahne();
  if (state.foto.kok) void fotoDurumYenile();
})();
