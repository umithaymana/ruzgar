/* Ana Motor çalışma masası. Sohbet ve motor listesine dokunmaz. */
(function () {
  const KEY = "ruzgarMasaDeskV1";
  const COLS = "ABCDEFGHIJKL".split("");
  const ROWS = 28;
  const BW = 1600;
  const BH = 1000;

  const root = document.getElementById("ruzgar-masa");
  if (!root) return;

  const tools = document.getElementById("ruzgar-masa-tools");
  const statusEl = document.getElementById("ruzgar-masa-durum");
  const belge = document.getElementById("ruzgar-masa-belge");
  const sheetWrap = document.getElementById("ruzgar-masa-sheet");
  const formulaInput = document.getElementById("ruzgar-masa-formula-input");
  const cellName = document.getElementById("ruzgar-masa-cell-name");
  const canvas = document.getElementById("ruzgar-masa-canvas");
  const slidesEl = document.getElementById("ruzgar-masa-slides");
  const slideTitle = document.getElementById("ruzgar-masa-slide-title");
  const slideBody = document.getElementById("ruzgar-masa-slide-body");
  const present = document.getElementById("ruzgar-masa-present");
  const presentTitle = document.getElementById("ruzgar-masa-present-title");
  const presentBody = document.getElementById("ruzgar-masa-present-body");

  const state = {
    mode: "belge",
    belgeHtml: "",
    sheet: blankSheet(),
    sel: { r: 0, c: 0 },
    slides: [{ title: "Başlık", body: "Metin", bg: "#1c1a16", fg: "#f7f4ec" }],
    slideIndex: 0,
    draw: { tool: "kalem", color: "#1a1a1c", size: 4 },
  };

  let saveTimer = 0;
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

  function setStatus(text) {
    if (statusEl) statusEl.textContent = text || "";
  }

  function scheduleSave() {
    setStatus("Yazılıyor…");
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
    };
    try {
      if (state.ink && canvas.width) payload.drawPng = canvas.toDataURL("image/png");
    } catch (err) {
      payload.drawPng = "";
    }
    try {
      localStorage.setItem(KEY, JSON.stringify(payload));
      setStatus("Kaydedildi");
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
    if (data.mode) state.mode = data.mode;
    state.ink = data.ink === true;
    state._png = state.ink && typeof data.drawPng === "string" ? data.drawPng : "";
  }

  function showMode(mode, opts) {
    state.mode = mode;
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
    if (mode === "sunum") renderSlides();
    if (!opts || !opts.keep) scheduleSave();
  }

  function renderTools() {
    const mode = state.mode;
    if (mode === "belge") {
      tools.innerHTML =
        '<button type="button" data-cmd="bold" title="Kalın"><b>B</b></button>' +
        '<button type="button" data-cmd="italic" title="İtalik"><i>I</i></button>' +
        '<button type="button" data-cmd="underline" title="Altı çizili"><u>U</u></button>' +
        '<button type="button" data-cmd="h2">Başlık</button>' +
        '<button type="button" data-cmd="insertUnorderedList">Madde</button>' +
        '<button type="button" data-cmd="insertOrderedList">Numara</button>' +
        '<button type="button" data-cmd="justifyLeft">Sola</button>' +
        '<button type="button" data-cmd="justifyCenter">Ortala</button>' +
        '<button type="button" data-cmd="justifyRight">Sağa</button>';
    } else if (mode === "tablo") {
      tools.innerHTML =
        '<span>Formül: =A1+B1 · =TOPLA(A1:A8) · =ORTALAMA · =MİN · =MAK</span>';
    } else if (mode === "cizim") {
      tools.innerHTML =
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
    } else {
      tools.innerHTML =
        '<button type="button" id="ruzgar-masa-add-slide">Slayt ekle</button>' +
        '<button type="button" id="ruzgar-masa-del-slide">Slaytı sil</button>' +
        '<label>Zemin <input id="ruzgar-masa-bg" type="color" value="#1c1a16"></label>' +
        '<label>Yazı <input id="ruzgar-masa-fg" type="color" value="#f7f4ec"></label>' +
        '<button type="button" id="ruzgar-masa-play" class="ruzgar-masa-btn-accent">Sun</button>';
      const slide = currentSlide();
      document.getElementById("ruzgar-masa-bg").value = toHex(slide.bg, "#1c1a16");
      document.getElementById("ruzgar-masa-fg").value = toHex(slide.fg, "#f7f4ec");
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
  });

  tools.addEventListener("input", function (ev) {
    if (ev.target.id === "ruzgar-masa-color") state.draw.color = ev.target.value;
    if (ev.target.id === "ruzgar-masa-size") state.draw.size = Number(ev.target.value) || 4;
    if (ev.target.id === "ruzgar-masa-bg" || ev.target.id === "ruzgar-masa-fg") {
      const slide = currentSlide();
      if (ev.target.id === "ruzgar-masa-bg") slide.bg = ev.target.value;
      else slide.fg = ev.target.value;
      renderSlides();
      scheduleSave();
    }
  });

  root.querySelector(".ruzgar-masa-tabs").addEventListener("click", function (ev) {
    const btn = ev.target.closest("[data-masa]");
    if (!btn) return;
    masaSayfa(btn.getAttribute("data-masa"));
  });

  belge.addEventListener("input", scheduleSave);

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
  }

  function bindSlideField(el, key) {
    el.addEventListener("input", function () {
      currentSlide()[key] = el.value;
      scheduleSave();
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
    const label = { belge: "belgeyi", tablo: "tabloyu", cizim: "çizimi", sunum: "sunumu" }[state.mode];
    if (!window.confirm("Bu " + label + " temizlensin mi?")) return;
    if (state.mode === "belge") belge.innerHTML = "";
    else if (state.mode === "tablo") {
      state.sheet = blankSheet();
      paintSheet();
    } else if (state.mode === "cizim") clearPaper();
    else {
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
    const izin = { sohbet: 1, belge: 1, tablo: 1, cizim: 1, sunum: 1 };
    if (!izin[kind]) return "";
    sayfa = kind;
    if (kind !== "sohbet") showMode(kind);
    syncSahne();
    return {
      sohbet: "Sohbet açık.",
      belge: "Belge açık.",
      tablo: "Tablo açık.",
      cizim: "Çizim açık.",
      sunum: "Sunum açık.",
    }[kind];
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
      "belge.temizle": [],
      "tablo.hucre": ["hucre", "deger"],
      "tablo.temizle": [],
      "cizim.renk": ["ad"],
      "cizim.cizgi": ["x1", "y1", "x2", "y2"],
      "cizim.kutu": ["x", "y", "w", "h"],
      "cizim.daire": ["x", "y", "rx", "ry"],
      "cizim.temizle": [],
      "sunum.ekle": ["baslik", "metin"],
      "sunum.temizle": [],
      "sunum.sun": [],
    };
    if (!action || typeof action !== "object" || Array.isArray(action)) return false;
    const keys = Object.keys(action);
    const need = izin[String(action.eylem || "")];
    if (!need || keys.length > need.length + 1) return false;
    const yazi = { metin: 1, deger: 1, hucre: 1, ad: 1, baslik: 1 };
    for (let i = 0; i < keys.length; i++) {
      if (keys[i] !== "eylem" && need.indexOf(keys[i]) < 0) return false;
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
    return addr(r, c) + " yazıldı.";
  }

  function masaBelgeYaz(text, append) {
    const clean = masaTemizMetin(text, 8000).trim();
    if (!clean) return "Yazılacak metin yok.";
    if (append && (belge.textContent || "").trim()) {
      belge.textContent = belge.textContent.replace(/\s+$/, "") + "\n" + clean;
    } else {
      belge.textContent = clean;
    }
    scheduleSave();
    masaAc("belge");
    return append ? "Belgeye eklendi." : "Belge yazıldı.";
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
    return "Slayt hazır.";
  }

  function masaUygula(action) {
    if (!action || typeof action !== "object") return "Komut geçersiz.";
    const eylem = String(action.eylem || "");
    if (eylem === "belge.yaz") return masaBelgeYaz(action.metin, false);
    if (eylem === "belge.ekle") return masaBelgeYaz(action.metin, true);
    if (eylem === "belge.temizle") {
      belge.textContent = "";
      scheduleSave();
      masaAc("belge");
      return "Belge temizlendi.";
    }
    if (eylem === "tablo.hucre") {
      const hucre = String(action.hucre || "");
      const m = hucre.match(/^([A-La-l])(\d{1,2})$/);
      if (!m) return "Hücre A1 biçiminde olmalı.";
      return masaHucreYaz(m[1], m[2], action.deger);
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
      return "Çizim işlendi.";
    }
    if (eylem === "cizim.temizle") {
      ensurePaper();
      clearPaper();
      masaAc("cizim");
      return "Çizim temizlendi.";
    }
    if (eylem === "sunum.ekle") return masaSlaytEkle(action.baslik, action.metin);
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
      "Çalışma masası komutları:",
      "sohbet",
      "belgeyi aç",
      "tabloyu göster",
      "çizimi aç",
      "sunumu aç",
      "belgeye yaz: metin",
      "belgeye ekle: metin",
      "belgeyi temizle",
      "tablo A1 = 10",
      "tablo A3 = =TOPLA(A1:A2)",
      "tabloyu temizle",
      "çizgi 40 40 400 200",
      "kutu 80 80 240 140",
      "daire 300 220 80 60",
      "renk kırmızı",
      "çizimi temizle",
      "slayt ekle: Başlık | metin",
      "sunumu temizle",
      "sun",
    ].join("\n");
  }

  function masaKomutCoz(text) {
    const raw = String(text || "").trim();
    if (!raw || raw.length > 9000) return null;
    const sade = raw
      .replace(/^[Ll]ütfen\s+/, "")
      .replace(/\s+(mısın|misin|misiniz|mısınız|musun|musunuz)[.!?]*$/i, "")
      .replace(/\?+$/g, "")
      .trim();
    const low = typeof window.ruzgarKomutGovdesi === "function"
      ? window.ruzgarKomutGovdesi(sade)
      : masaHarf(sade);
    if (/^(masa yardim|calisma masasi yardim|masa komutlari)$/.test(low)) {
      return { handled: true, reply: masaYardim() };
    }
    if (/^(sohbet|sohbeti goster|sohbeti ac|sahne|robota don)$/.test(low)) {
      return { handled: true, reply: masaSayfa("sohbet") };
    }
    if (/^(belgeyi ac|belgeyi goster|belge ac|belge goster)$/.test(low)) {
      return { handled: true, reply: masaSayfa("belge") };
    }
    if (/^(tabloyu ac|tabloyu goster|tablo ac|tablo goster)$/.test(low)) {
      return { handled: true, reply: masaSayfa("tablo") };
    }
    if (/^(cizimi ac|cizimi goster|cizim ac|cizim goster)$/.test(low)) {
      return { handled: true, reply: masaSayfa("cizim") };
    }
    if (/^(sunumu ac|sunumu goster|sunum ac|sunum goster)$/.test(low)) {
      return { handled: true, reply: masaSayfa("sunum") };
    }
    let m = sade.match(/^(belgeye yaz|belge yaz|belgeye ekle|belge ekle)\s*[:\-]?\s*([\s\S]+)$/i);
    if (m) return { handled: true, reply: masaBelgeYaz(m[2], /ekle/i.test(m[1])) };
    if (/^(belgeyi temizle|belge temizle)$/i.test(sade)) {
      return { handled: true, reply: masaUygula({ eylem: "belge.temizle" }) };
    }
    if (/^tablo\s*:\s*\n/i.test(sade)) {
      const lines = sade.split(/\n/).slice(1);
      const notes = [];
      lines.forEach(function (line) {
        const cell = line.trim().match(/^([A-La-l])(\d{1,2})\s*(?:=|:)?\s*(.+)$/);
        if (cell) notes.push(masaHucreYaz(cell[1], cell[2], cell[3]));
      });
      if (!notes.length) return { handled: true, reply: "Tablo satırı A1 10 biçiminde olmalı." };
      return { handled: true, reply: notes.join(" ") };
    }
    m = sade.match(/^(?:tablo|hucre|hücre)\s+([A-La-l])(\d{1,2})\s*(?:=|:)?\s*([\s\S]+)$/i);
    if (m) return { handled: true, reply: masaHucreYaz(m[1], m[2], m[3]) };
    if (/^(tabloyu temizle|tablo temizle)$/i.test(sade)) {
      return { handled: true, reply: masaUygula({ eylem: "tablo.temizle" }) };
    }
    m = sade.match(/^(?:renk)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ]+)\s*$/i);
    if (m) return { handled: true, reply: masaUygula({ eylem: "cizim.renk", ad: m[1] }) };
    m = sade.match(/^(?:çizgi|cizgi)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$/i);
    if (m) return { handled: true, reply: masaUygula({ eylem: "cizim.cizgi", x1: m[1], y1: m[2], x2: m[3], y2: m[4] }) };
    m = sade.match(/^(?:kutu)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$/i);
    if (m) return { handled: true, reply: masaUygula({ eylem: "cizim.kutu", x: m[1], y: m[2], w: m[3], h: m[4] }) };
    m = sade.match(/^(?:daire)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s*$/i);
    if (m) return { handled: true, reply: masaUygula({ eylem: "cizim.daire", x: m[1], y: m[2], rx: m[3], ry: m[4] }) };
    if (/^(çizimi temizle|cizimi temizle|çizim temizle|cizim temizle)$/i.test(sade)) {
      return { handled: true, reply: masaUygula({ eylem: "cizim.temizle" }) };
    }
    m = sade.match(/^slayt ekle\s*[:\-]?\s*([\s\S]+?)\s*(?:\|\s*|\n)\s*([\s\S]+)$/i);
    if (m) return { handled: true, reply: masaSlaytEkle(m[1], m[2]) };
    if (/^(sunumu temizle|sunum temizle|slaytlari temizle|slaytları temizle)$/i.test(sade)) {
      return { handled: true, reply: masaUygula({ eylem: "sunum.temizle" }) };
    }
    if (/^(sun|sunumu aç|sunumu ac|sunumu başlat|sunumu baslat)$/i.test(sade)) {
      return { handled: true, reply: masaUygula({ eylem: "sunum.sun" }) };
    }
    return null;
  }

  window.ruzgarMasaSayfa = function (kind) {
    return masaSayfa(String(kind || ""));
  };

  window.ruzgarMasaKomut = function (text) {
    try {
      return masaKomutCoz(text);
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
  showMode(state.mode === "tablo" || state.mode === "cizim" || state.mode === "sunum" ? state.mode : "belge", { keep: true });
  renderSlides();
  setStatus("Hazır");
  wireSahne();
  syncSahne();
})();
