(() => {
  const LS = {
    base: "ruzgar_pwa_base",
    token: "ruzgar_pwa_token",
    who: "ruzgar_pwa_who",
    deviceId: "ruzgar_pwa_device_id",
    deviceKind: "ruzgar_pwa_device_kind",
    regDraft: "ruzgar_pwa_reg_draft",
    deviceName: "ruzgar_pwa_device_name",
  };

  const el = (id) => document.getElementById(id);
  const baseInput = el("baseUrl");
  const gateMsg = el("gateMsg");
  const chat = el("chat");
  const meta = el("meta");
  const SAHNE_PLACEHOLDER = "Yaz. Cevabı ben buradan söyleyeyim.";
  let history = [];
  let micBusy = false;

  /* Tek ikon kuralı: yazı+mikrofon aynı PWA. HTTP'de mic ölür → HTTPS:8443'e at. */
  (function forceHttpsSingleDoor() {
    try {
      if (window.isSecureContext) return;
      if ((location.protocol || "") !== "http:") return;
      const h = (location.hostname || "").toLowerCase();
      if (!h) return;
      if (h === "localhost" || h === "127.0.0.1") {
        /* PC kısayolu da HTTPS; localhost http ise yine 8443 */
      }
      const path = location.pathname || "/mobil/";
      const dest = `https://${location.hostname}:8443${path}${location.search || ""}${location.hash || ""}`;
      location.replace(dest);
    } catch (_) {}
  })();

  function defaultBase() {
    // HTTPS köprüde origin zaten https://host:8443 — API de aynı kapıdan
    return window.location.origin || "https://127.0.0.1:8443";
  }

  function deviceId() {
    let id = localStorage.getItem(LS.deviceId);
    if (!id) {
      id = "dev_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(LS.deviceId, id);
    }
    return id;
  }

  baseInput.value = localStorage.getItem(LS.base) || defaultBase();
  const savedKind = localStorage.getItem(LS.deviceKind);
  if (savedKind && el("deviceKind")) {
    el("deviceKind").value = savedKind === "pc" ? "pc" : savedKind;
  } else if (el("deviceKind")) {
    // Masaüstü / app penceresi → varsayılan PC
    const desk =
      window.matchMedia("(display-mode: standalone)").matches ||
      window.matchMedia("(min-width: 900px)").matches ||
      !/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent || "");
    if (desk) el("deviceKind").value = "pc";
  }
  if (el("device") && !el("device").value && el("deviceKind") && el("deviceKind").value === "pc") {
    el("device").placeholder = "örn. Ümit PC";
  }
  const savedDeviceName = localStorage.getItem(LS.deviceName);
  if (savedDeviceName && el("device") && !el("device").value) el("device").value = savedDeviceName;

  // Kayıt formu otomatik doldurma (son taslak + tarayıcı autocomplete)
  try {
    const draft = JSON.parse(localStorage.getItem(LS.regDraft) || "null");
    if (draft && typeof draft === "object") {
      if (draft.ad && el("ad")) el("ad").value = draft.ad;
      if (draft.soyad && el("soyad")) el("soyad").value = draft.soyad;
      if (draft.telefon && el("tel")) el("tel").value = draft.telefon;
      if (draft.kullanici && el("regUser")) el("regUser").value = draft.kullanici;
    }
  } catch (_) {}

  function base() {
    return (baseInput.value || defaultBase()).replace(/\/$/, "");
  }

  function setMsg(t, ok = true) {
    gateMsg.textContent = t || "";
    gateMsg.style.color = ok ? "#38bdf8" : "#f43f5e";
  }

  function readWho() {
    try {
      return JSON.parse(localStorage.getItem(LS.who) || "null");
    } catch (_) {
      return null;
    }
  }

  function sahneAllowed(who) {
    const w = who || readWho();
    if (!w) return false;
    const motors = w.motors || {};
    return motors.sahne === true;
  }

  function ensureMobilSahneA11y() {
    const stage = el("sahneStage");
    const soz = el("sahneSoz");
    const durum = el("sahneDurum");
    if (stage && !stage.getAttribute("aria-label")) {
      stage.setAttribute("aria-label", "Rüzgar sahne");
    }
    if (soz && !soz.hasAttribute("tabindex")) soz.setAttribute("tabindex", "-1");
    if (soz) {
      soz.setAttribute("aria-live", "polite");
      if (!soz.getAttribute("lang")) soz.setAttribute("lang", "tr");
    }
    if (durum) {
      durum.setAttribute("aria-live", "polite");
      durum.setAttribute("aria-atomic", "true");
      if (!durum.getAttribute("role")) durum.setAttribute("role", "status");
      if (!durum.getAttribute("lang")) durum.setAttribute("lang", "tr");
    }
  }

  function applySahneGate(who) {
    const stage = el("sahneStage");
    if (!stage) return;
    ensureMobilSahneA11y();
    const on = sahneAllowed(who);
    stage.classList.toggle("hidden", !on);
    stage.setAttribute("aria-hidden", on ? "false" : "true");
    try {
      stage.inert = !on;
    } catch (_) {}
    if (!on) {
      stage.setAttribute("data-sahne-mode", "hazir");
      stage.setAttribute("aria-busy", "false");
      stage.title = "Rüzgar sahne · hazir";
      const sozOff = el("sahneSoz");
      if (sozOff) sozOff.textContent = SAHNE_PLACEHOLDER;
      const durumOff = el("sahneDurum");
      if (durumOff) {
        durumOff.textContent = "Hazır";
        durumOff.title = "Durum: hazir";
      }
      const faceOff = el("sahneFace");
      if (faceOff) faceOff.classList.remove("is-thinking-sahne");
      const dalgaOff = el("sahneDalga");
      if (dalgaOff) dalgaOff.classList.remove("is-on", "is-dinle", "is-dusun");
      stage.classList.remove("is-live", "is-dinle", "is-dusun", "is-yazi");
      if (el("chatView")) {
        el("chatView").classList.remove("sahne-busy", "has-sahne", "sheet-open");
      }
    } else if (el("chatView")) {
      el("chatView").classList.add("has-sahne");
      /* Sıra 32: mobil A/B/C — varsayılan A (tam sahne) */
      if (!el("chatView").getAttribute("data-sahne-abc")) {
        el("chatView").setAttribute("data-sahne-abc", "A");
      }
    }
    const hint = stage.querySelector(".sahne-gate-hint");
    const admin = !!(who && (who.is_admin || who.role === "mimar" || who.role === "admin"));
    if (hint) hint.classList.toggle("hidden", !admin);
    if (on) setSahneState("hazir");
    syncSahneSheetBtn();
  }

  function syncSahneSheetBtn() {
    const btn = el("btnSahneSheet");
    const view = el("chatView");
    if (!btn || !view) return;
    const open = view.classList.contains("sheet-open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.textContent = open ? "Şeridi kapat" : "Sohbet şeridi";
  }

  function toggleSahneSheet(force) {
    const view = el("chatView");
    if (!view || !view.classList.contains("has-sahne")) return;
    const next = typeof force === "boolean" ? force : !view.classList.contains("sheet-open");
    view.classList.toggle("sheet-open", next);
    syncSahneSheetBtn();
    if (next) {
      const chat = el("chat");
      if (chat) chat.scrollTop = chat.scrollHeight;
    }
  }

  const mobilHaritaState = {
    lat: 39.0,
    lon: 35.2,
    zoom: 6,
    mode: "2d",
    hedef: "Türkiye",
    label: "Türkiye",
    year: 2015,
  };

  function haritaViewerUrl(st) {
    const s = st || mobilHaritaState;
    const root = (base() || "").replace(/\/$/, "");
    const label = encodeURIComponent(String(s.label || s.hedef || "Türkiye"));
    return (
      root +
      "/ui/harita-viewer.html?mode=" +
      encodeURIComponent(String(s.mode || "2d")) +
      "&lat=" +
      Number(s.lat || 39).toFixed(5) +
      "&lon=" +
      Number(s.lon || 35.2).toFixed(5) +
      "&zoom=" +
      Math.max(2, Math.min(18, Number(s.zoom) || 6)) +
      "&label=" +
      label +
      "&year=" +
      (s.year != null ? Number(s.year) : 2015)
    );
  }

  function ensureMobilHaritaTools(frame) {
    let tools = frame.querySelector(".harita-tools");
    if (tools) return tools;
    tools = document.createElement("div");
    tools.className = "harita-tools";
    tools.setAttribute("role", "toolbar");
    tools.innerHTML =
      '<button type="button" data-h="zoom_in">+</button>' +
      '<button type="button" data-h="zoom_out">−</button>' +
      '<button type="button" data-h="mode_2d">2D</button>' +
      '<button type="button" data-h="mode_3d" title="3D Cesium">3D</button>' +
      '<button type="button" data-h="mode_4d">4D</button>' +
      '<button type="button" data-h="mode_uydu">Uydu</button>' +
      '<button type="button" data-h="mode_tur">Tur</button>' +
      '<button type="button" data-h="mode_f4" title="F4map yedek">F4</button>';
    tools.addEventListener("click", (ev) => {
      const btn = ev.target && ev.target.closest("button[data-h]");
      if (!btn) return;
      applyMobilHaritaCommand({ action: btn.getAttribute("data-h") });
    });
    frame.appendChild(tools);
    return tools;
  }

  function paintMobilHarita(metaText) {
    const root = el("sahneOrgan");
    const frame = el("sahneOrganFrame");
    const meta = el("sahneOrganMeta");
    const face = el("sahneFace");
    const stage = el("sahneStage");
    if (!root || !frame) return;
    root.setAttribute("data-organ", "harita");
    root.className = "sahne-organ is-harita";
    if (stage) stage.classList.add("organ-on");
    document.body.classList.add("mobil-sahne-organ-on");
    if (face) face.classList.add("is-organ-dim");
    const tools = ensureMobilHaritaTools(frame);
    let iframe = frame.querySelector("iframe[data-sahne-harita]");
    if (!iframe) {
      iframe = document.createElement("iframe");
      iframe.title = "Harita";
      iframe.loading = "eager";
      iframe.referrerPolicy = "no-referrer";
      iframe.allow = "fullscreen";
      iframe.setAttribute("data-sahne-harita", "1");
      frame.insertBefore(iframe, tools);
    }
    frame.hidden = false;
    const src = haritaViewerUrl(mobilHaritaState);
    if (iframe.getAttribute("data-src") !== src) {
      iframe.setAttribute("data-src", src);
      iframe.src = src;
    }
    tools.querySelectorAll("button[data-h]").forEach((b) => {
      const a = b.getAttribute("data-h");
      b.classList.toggle("is-on", a === "mode_" + mobilHaritaState.mode);
    });
    const modeLabel = String(mobilHaritaState.mode || "2d").toUpperCase();
    if (meta) {
      meta.hidden = false;
      meta.textContent =
        metaText ||
        [
          "Harita",
          mobilHaritaState.label || mobilHaritaState.hedef || "Türkiye",
          "zoom " + mobilHaritaState.zoom,
          modeLabel,
        ].join(" · ");
    }
    const soz = el("sahneSoz");
    if (soz) {
      soz.textContent =
        "Harita " +
        modeLabel +
        ": " +
        (mobilHaritaState.label || "Türkiye") +
        " · zoom " +
        mobilHaritaState.zoom;
    }
  }

  function applyMobilHaritaCommand(cmd) {
    const c = cmd || {};
    const action = String(c.action || c.fiil || "show");
    const st = mobilHaritaState;
    const geo = c.geo || null;
    if (action === "mode_2d" || action === "2d") st.mode = "2d";
    if (action === "mode_3d" || action === "3d") {
      st.mode = "3d";
      if ((Number(st.zoom) || 6) < 15) st.zoom = 16;
    }
    if (action === "mode_4d" || action === "4d") st.mode = "4d";
    if (action === "mode_uydu" || action === "uydu") st.mode = "uydu";
    if (action === "mode_tur" || action === "tur") {
      st.mode = "tur";
      if ((Number(st.zoom) || 6) < 5) st.zoom = 5;
    }
    if (action === "mode_f4" || action === "f4") {
      st.mode = "f4";
      if ((Number(st.zoom) || 6) < 15) st.zoom = 16;
    }
    const isMode =
      /^mode_(2d|3d|4d|uydu|tur|f4)$/.test(action) ||
      /^(2d|3d|4d|uydu|tur|f4)$/.test(action);
    const hedefStr = c.hedef != null ? String(c.hedef).trim() : "";
    const hedefIsMode =
      /^(2d|3d|4d|uydu|tur|f4|f4map|panorama|dunya\s*turu|tarihi|historical)$/i.test(hedefStr);
    if (!isMode || (geo && !hedefIsMode)) {
      if (geo && geo.lat != null && geo.lon != null && !hedefIsMode) {
        st.lat = Number(geo.lat);
        st.lon = Number(geo.lon);
        if (geo.zoom != null) st.zoom = Number(geo.zoom);
        st.label = geo.label || hedefStr || st.label;
        st.hedef = hedefStr || st.label;
      } else if (hedefStr && !hedefIsMode) {
        st.hedef = hedefStr;
        st.label = st.hedef;
      }
    }
    let delta = Number(c.zoom_delta) || 0;
    if (action === "zoom_in" && !delta) delta = 1;
    if (action === "zoom_out" && !delta) delta = -1;
    if (delta) st.zoom = Math.max(2, Math.min(18, (Number(st.zoom) || 6) + delta));
    if ((action === "show" || action === "goster") && !geo && !hedefStr) {
      if (!st.hedef) {
        st.lat = 39;
        st.lon = 35.2;
        st.zoom = 6;
        st.hedef = "Türkiye";
        st.label = "Türkiye";
      }
    }
    paintMobilHarita(c.metaText);
    return { ok: true, organ: "harita", state: { ...st } };
  }

  function applySahneOrgan(organ, hedef, metaText) {
    const root = el("sahneOrgan");
    const frame = el("sahneOrganFrame");
    const meta = el("sahneOrganMeta");
    const face = el("sahneFace");
    const stage = el("sahneStage");
    if (!root || !frame) return;
    const o = organ || "yuz";
    root.setAttribute("data-organ", o);
    root.className = "sahne-organ is-" + o;
    if (o === "yuz") {
      frame.replaceChildren();
      frame.hidden = true;
      if (meta) {
        meta.hidden = true;
        meta.textContent = "";
      }
      if (face) face.classList.remove("is-organ-dim");
      if (stage) stage.classList.remove("organ-on");
      document.body.classList.remove("mobil-sahne-organ-on");
      return;
    }
    if (face) face.classList.add("is-organ-dim");
    if (o === "harita") {
      if (hedef) {
        mobilHaritaState.hedef = String(hedef);
        mobilHaritaState.label = String(hedef);
      }
      paintMobilHarita(metaText);
      return;
    }
    if (stage) stage.classList.add("organ-on");
    document.body.classList.add("mobil-sahne-organ-on");
    frame.replaceChildren();
    frame.hidden = false;
    if (o === "uzay") {
      const iframe = document.createElement("iframe");
      iframe.title = "Uzay";
      iframe.loading = "lazy";
      iframe.src = "https://images.nasa.gov/";
      frame.appendChild(iframe);
      if (meta) {
        meta.hidden = false;
        meta.textContent = metaText || "Uzay · NASA";
      }
    } else {
      const p = document.createElement("p");
      p.className = "hint";
      p.style.padding = "12px";
      p.textContent = metaText || o + " organı";
      frame.appendChild(p);
      if (meta) {
        meta.hidden = false;
        meta.textContent = metaText || o;
      }
    }
  }

  async function runSuperEl(text) {
    const stage = el("sahneStage");
    if (!stage) return null;
    /* Organ komutu gelince sahne kapalıysa aç (izin varsa) */
    if (stage.classList.contains("hidden") && sahneAllowed()) {
      stage.classList.remove("hidden");
      const view = el("chatView");
      if (view) view.classList.add("has-sahne");
    }
    if (stage.classList.contains("hidden")) return null;
    try {
      const res = await api("/api/sahne/super-el", {
        method: "POST",
        body: JSON.stringify({ text: String(text || "") }),
      });
      if (!res || !res.ok) return res;
      if (res.fiil === "temizle" || res.action === "clear") {
        applySahneOrgan("yuz");
        return res;
      }
      const action = String(res.action || "");
      const mapActs = {
        zoom_in: 1,
        zoom_out: 1,
        mode_2d: 1,
        mode_3d: 1,
        mode_4d: 1,
        mode_uydu: 1,
        mode_tur: 1,
        mode_f4: 1,
        show: 1,
        focus: 1,
      };
      const organ = res.organ || "yuz";
      if (organ === "harita" || mapActs[action]) {
        const applied = applyMobilHaritaCommand({
          action: action || "show",
          fiil: res.fiil,
          hedef: res.hedef,
          zoom_delta: res.zoom_delta || 0,
          geo: res.geo || null,
          metaText:
            (res.fiil || action) +
            " · harita" +
            (res.hedef ? " · " + res.hedef : ""),
        });
        res.applied = applied;
        const view = el("chatView");
        if (view && view.classList.contains("has-sahne")) {
          view.classList.remove("sheet-open");
          syncSahneSheetBtn();
        }
        /* Kısa onay — LLM «gösteremiyorum» demesin */
        if (mapActs[action]) {
          const mode = String(mobilHaritaState.mode || "2d").toUpperCase();
          let reply =
            "Harita: " +
            (mobilHaritaState.label || res.hedef || "Türkiye") +
            " · " +
            mode +
            " · zoom " +
            mobilHaritaState.zoom +
            ".";
          if (action === "mode_3d") reply = "3D moda aldım.";
          else if (action === "mode_4d") reply = "4D zamanlı uyduyu açtım.";
          else if (action === "mode_uydu") reply = "Uydu görüntüsünü açtım.";
          else if (action === "mode_tur") reply = "Dünya turunu başlattım.";
          else if (action === "mode_2d") reply = "2D moda aldım.";
          else if (action === "zoom_in") reply = "Yaklaştırdım · zoom " + mobilHaritaState.zoom;
          else if (action === "zoom_out") reply = "Uzaklaştırdım · zoom " + mobilHaritaState.zoom;
          bubble("bot", reply);
          history.push({ role: "assistant", content: reply });
          res._mobilShort = true;
        }
        return res;
      }
      if (organ && organ !== "yuz") {
        applySahneOrgan(organ, res.hedef, (res.fiil || "") + " · " + organ);
        const view = el("chatView");
        if (view && view.classList.contains("has-sahne")) {
          view.classList.remove("sheet-open");
          syncSahneSheetBtn();
        }
      }
      return res;
    } catch (_) {
      return null;
    }
  }

  function setSahneState(mode, sozText) {
    const stage = el("sahneStage");
    if (!stage || stage.classList.contains("hidden")) return;
    ensureMobilSahneA11y();
    const durum = el("sahneDurum");
    const dalga = el("sahneDalga");
    const soz = el("sahneSoz");
    const face = el("sahneFace");
    stage.classList.remove("is-live", "is-dinle", "is-dusun", "is-yazi");
    if (dalga) dalga.classList.remove("is-on", "is-dinle", "is-dusun");
    if (face) face.classList.remove("is-thinking-sahne");
    const m = mode || "hazir";
    stage.setAttribute("data-sahne-mode", m);
    const busy = m !== "hazir" && m !== "yazi";
    stage.setAttribute("aria-busy", busy ? "true" : "false");
    if (el("chatView")) {
      el("chatView").classList.toggle("sahne-busy", busy);
    }
    if (durum) durum.title = "Durum: " + m;
    stage.title = "Rüzgar sahne · " + m;
    if (m === "konus") {
      stage.classList.add("is-live");
      if (dalga) dalga.classList.add("is-on");
      if (durum) durum.textContent = "Konuşuyor";
    } else if (m === "dinle") {
      stage.classList.add("is-dinle");
      /* PC hiza: is-dinle tek başına görünür; is-on yalnız konuşurken */
      if (dalga) dalga.classList.add("is-dinle");
      if (durum) durum.textContent = "Dinliyor";
    } else if (m === "dusun") {
      stage.classList.add("is-dusun");
      if (dalga) dalga.classList.add("is-dusun");
      if (face) face.classList.add("is-thinking-sahne");
      if (durum) durum.textContent = "Düşünüyor";
    } else if (m === "yazi") {
      stage.classList.add("is-yazi");
      if (durum) durum.textContent = "Yazıyorsun";
    } else if (durum) {
      durum.textContent = "Hazır";
    }
    if (soz && sozText != null) {
      const t = String(sozText);
      const shown = t.length > 640 ? t.slice(0, 640) + "…" : t;
      const prev = soz.textContent || "";
      /* PC paintSpeech hiza: stream büyürken is-fresh spam yok */
      const sameStream =
        !!t &&
        !!prev &&
        prev !== SAHNE_PLACEHOLDER &&
        shown.length >= prev.length &&
        shown.indexOf(prev.replace(/…$/, "")) === 0;
      const fresh = shown !== prev && !sameStream;
      soz.textContent = shown;
      if (fresh || sameStream) soz.scrollTop = soz.scrollHeight;
      if (fresh) {
        soz.classList.remove("is-fresh");
        void soz.offsetWidth;
        soz.classList.add("is-fresh");
        try {
          soz.focus({ preventScroll: true });
        } catch (_) {}
      }
    } else if (soz && m === "hazir" && !String(soz.textContent || "").trim()) {
      soz.textContent = SAHNE_PLACEHOLDER;
    }
  }

  function paintWhoLine(who) {
    el("who").textContent = who
      ? `${who.kullanici} · ${who.role || "user"}${who.is_admin ? " · yönetici" : ""}${
          who.device_kind ? " · " + who.device_kind : ""
        }${sahneAllowed(who) ? " · sahne" : ""}`
      : "";
  }

  async function refreshWhoMotors() {
    const token = localStorage.getItem(LS.token);
    if (!token) return readWho();
    try {
      const j = await api("/api/mobil/me", { timeoutMs: 8000 });
      if (!j || !j.ok) return readWho();
      const prev = readWho() || {};
      const next = {
        ...prev,
        ...j,
        token: prev.token || token,
        ok: true,
      };
      localStorage.setItem(LS.who, JSON.stringify(next));
      paintWhoLine(next);
      applySahneGate(next);
      return next;
    } catch (_) {
      return readWho();
    }
  }

  function showChat(who) {
    el("gate").classList.add("hidden");
    el("chatWrap").classList.remove("hidden");
    paintWhoLine(who);
    const admin = !!(who && (who.is_admin || who.role === "mimar" || who.role === "admin"));
    if (el("btnNavPanel")) el("btnNavPanel").style.display = admin ? "" : "none";
    applySahneGate(who);
    void refreshWhoMotors();
    const prefer = sessionStorage.getItem("ruzgar_pwa_tab");
    sessionStorage.removeItem("ruzgar_pwa_tab");
    showChatTab(prefer === "panel" && admin ? "panel" : "chat");
  }

  function showGate() {
    el("gate").classList.remove("hidden");
    el("chatWrap").classList.add("hidden");
  }

  function showChatTab(which) {
    const chatOn = which === "chat";
    if (el("chatView")) el("chatView").classList.toggle("hidden", !chatOn);
    if (el("panelView")) el("panelView").classList.toggle("hidden", chatOn);
    if (el("btnNavChat")) el("btnNavChat").classList.toggle("on", chatOn);
    if (el("btnNavPanel")) el("btnNavPanel").classList.toggle("on", !chatOn);
    if (!chatOn) refreshPanel("2");
  }

  async function api(path, opts = {}) {
    const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
    const token = localStorage.getItem(LS.token);
    if (token) headers.Authorization = `Bearer ${token}`;
    const ctrl = new AbortController();
    const ms = opts.timeoutMs != null ? opts.timeoutMs : 12000;
    const timer = setTimeout(() => ctrl.abort(), ms);
    let res;
    try {
      res = await fetch(`${base()}${path}`, { ...opts, headers, signal: ctrl.signal });
    } catch (e) {
      if (e && e.name === "AbortError") throw new Error("zaman aşımı — Yenile veya kapıyı kontrol et");
      throw e;
    } finally {
      clearTimeout(timer);
    }
    const text = await res.text();
    let j = {};
    try {
      j = JSON.parse(text);
    } catch {
      throw new Error(text.slice(0, 240) || res.statusText);
    }
    if (!res.ok) throw new Error(j.detail || j.error || text.slice(0, 240));
    return j;
  }

  function bubble(role, text) {
    const d = document.createElement("div");
    d.className = `bubble ${role === "user" ? "user" : "bot"}`;
    d.textContent = text;
    chat.appendChild(d);
    chat.scrollTop = chat.scrollHeight;
  }

  function setTab(which) {
    const map = {
      login: ["loginBox", "tabLogin"],
      reg: ["regBox", "tabReg"],
      panel: ["panelBox", "tabPanel"],
    };
    ["loginBox", "regBox", "panelBox"].forEach((id) => el(id).classList.add("hidden"));
    ["tabLogin", "tabReg", "tabPanel"].forEach((id) => el(id).classList.remove("on"));
    const [box, tab] = map[which];
    el(box).classList.remove("hidden");
    el(tab).classList.add("on");
  }

  el("tabLogin").onclick = () => setTab("login");
  el("tabReg").onclick = () => setTab("reg");
  el("tabPanel").onclick = () => {
    setTab("panel");
    refreshPanel("");
  };

  if (el("btnNavChat")) el("btnNavChat").onclick = () => showChatTab("chat");
  if (el("btnNavPanel")) el("btnNavPanel").onclick = () => showChatTab("panel");
  if (el("btnNavLogout")) {
    el("btnNavLogout").onclick = () => {
      if (el("btnLogout")) el("btnLogout").click();
      else void doLogout();
    };
  }
  if (el("btnSahneSheet")) {
    el("btnSahneSheet").onclick = () => toggleSahneSheet();
  }
  if (el("input")) {
    el("input").addEventListener("focus", () => {
      const view = el("chatView");
      if (view && view.classList.contains("has-sahne") && !view.classList.contains("sheet-open")) {
        /* yazıya girince şerit açılmaz — yalnız geçmiş istenirse düğme; sahne birincil */
      }
    });
  }

  async function softReload() {
    // Tam SW silme ekranı boşaltıyordu; yumuşak yenile + SW update
    try {
      const onPanel =
        el("panelView") && !el("panelView").classList.contains("hidden") &&
        el("chatWrap") && !el("chatWrap").classList.contains("hidden");
      sessionStorage.setItem("ruzgar_pwa_tab", onPanel ? "panel" : "chat");
      if ("serviceWorker" in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations();
        await Promise.all(regs.map((r) => r.update().catch(() => {})));
      }
    } catch (_) {}
    const u = new URL(window.location.href);
    u.searchParams.set("v", String(Date.now()));
    window.location.replace(u.toString());
  }
  if (el("btnReload")) el("btnReload").onclick = () => void softReload();
  if (el("btnNavReload")) el("btnNavReload").onclick = () => void softReload();

  async function doLogin(ev) {
    if (ev) ev.preventDefault();
    localStorage.setItem(LS.base, base());
    const kind = el("deviceKind").value || "telefon";
    localStorage.setItem(LS.deviceKind, kind);
    const dname = el("device").value.trim() || kind;
    localStorage.setItem(LS.deviceName, dname);
    try {
      const j = await api("/api/mobil/login", {
        method: "POST",
        body: JSON.stringify({
          kullanici: el("user").value.trim(),
          sifre: el("pass").value,
          device_name: dname,
          device_id: deviceId(),
          device_kind: kind,
        }),
      });
      if (!j.ok) throw new Error(j.error || "giriş başarısız");
      localStorage.setItem(LS.token, j.token);
      localStorage.setItem(LS.who, JSON.stringify(j));
      setMsg("Giriş tamam — oturum bu cihazda kalır.");
      showChat(j);
    } catch (e) {
      setMsg(String(e.message || e), false);
    }
  }

  async function doRegister(ev) {
    if (ev) ev.preventDefault();
    localStorage.setItem(LS.base, base());
    const payload = {
      ad: el("ad").value.trim(),
      soyad: el("soyad").value.trim(),
      telefon: el("tel").value.trim(),
      kullanici: el("regUser").value.trim(),
      sifre: el("regPass").value,
    };
    localStorage.setItem(
      LS.regDraft,
      JSON.stringify({
        ad: payload.ad,
        soyad: payload.soyad,
        telefon: payload.telefon,
        kullanici: payload.kullanici,
      }),
    );
    try {
      const j = await api("/api/mobil/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (!j.ok) throw new Error(j.error || "kayıt başarısız");
      el("regCode").textContent = `Kod: ${j.code}  (pending: ${j.pending_id})`;
      setMsg("Mimar panelinden onay bekleniyor.");
    } catch (e) {
      setMsg(String(e.message || e), false);
    }
  }

  if (el("loginForm")) el("loginForm").onsubmit = (ev) => void doLogin(ev);
  else if (el("btnLogin")) el("btnLogin").onclick = () => void doLogin();
  if (el("regForm")) el("regForm").onsubmit = (ev) => void doRegister(ev);
  else if (el("btnReg")) el("btnReg").onclick = () => void doRegister();

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  let _panelBusy = false;
  async function refreshPanel(suffix) {
    const s = suffix || "";
    const statusEl = el("panelStatus" + s);
    const pendEl = el("panelPending" + s);
    const sessEl = el("panelSessions" + s);
    const usersEl = el("panelUsers" + s);
    const devEl = el("panelDevices" + s);
    if (!statusEl || !pendEl || !sessEl || !usersEl || !devEl) return;
    if (_panelBusy) return;
    _panelBusy = true;
    statusEl.textContent = "yükleniyor…";
    pendEl.innerHTML = "";
    sessEl.innerHTML = "";
    usersEl.innerHTML = "";
    devEl.innerHTML = "";
    const again = () => refreshPanel(s);
    try {
      const [st, pend, sess, users, devices] = await Promise.all([
        api("/api/mobil/status"),
        api("/api/mobil/pending"),
        api("/api/mobil/sessions"),
        api("/api/mobil/users"),
        api("/api/mobil/devices").catch(() => ({ devices: [] })),
      ]);
      statusEl.innerHTML = [
        `v${esc(st.version)}`,
        `kullanıcı ${esc(st.users)}`,
        `oturum ${esc(st.sessions)}`,
        `bekleyen ${esc(st.pending)}`,
        `admin ${esc(st.admins)}`,
        st.enabled ? "açık" : "kapalı",
      ].join(" · ");

      (devices.devices || []).forEach((d) => {
        const card = document.createElement("div");
        card.className = "device-card" + (d.filled ? " filled" : "");
        card.innerHTML = `<strong>${esc(d.slot || d.device_kind)}</strong><span>${
          d.filled
            ? esc(d.device_name || d.kullanici || d.device_id || "kayıtlı")
            : "boş slot"
        }</span>`;
        devEl.appendChild(card);
      });

      (pend.pending || []).forEach((p) => {
        const row = document.createElement("div");
        row.className = "panel-row";
        row.innerHTML = `<div><b>${esc(p.kullanici)}</b> · ${esc(p.ad)} ${esc(p.soyad)}<br/><small>kod ${esc(
          p.code
        )} · ${esc(p.pending_id)}</small></div>`;
        const actions = document.createElement("div");
        actions.className = "row-actions";
        const ok = document.createElement("button");
        ok.type = "button";
        ok.className = "primary tiny";
        ok.textContent = "Onayla";
        ok.onclick = async () => {
          try {
            await api("/api/mobil/approve", {
              method: "POST",
              body: JSON.stringify({
                pending_id: p.pending_id,
                code: p.code,
                approve: true,
              }),
            });
            setMsg(`${p.kullanici} onaylandı`);
            again();
          } catch (e) {
            setMsg(String(e.message || e), false);
          }
        };
        const no = document.createElement("button");
        no.type = "button";
        no.className = "tiny";
        no.textContent = "Red";
        no.onclick = async () => {
          try {
            await api("/api/mobil/approve", {
              method: "POST",
              body: JSON.stringify({
                pending_id: p.pending_id,
                code: p.code,
                approve: false,
              }),
            });
            setMsg(`${p.kullanici} reddedildi`);
            again();
          } catch (e) {
            setMsg(String(e.message || e), false);
          }
        };
        actions.appendChild(ok);
        actions.appendChild(no);
        row.appendChild(actions);
        pendEl.appendChild(row);
      });
      if (!(pend.pending || []).length) {
        pendEl.innerHTML = `<p class="hint">Bekleyen yok</p>`;
      }

      (sess.sessions || []).forEach((sessRow) => {
        const row = document.createElement("div");
        row.className = "panel-row";
        row.innerHTML = `<div><b>${esc(sessRow.kullanici)}</b> · ${esc(sessRow.device_kind || "")} ${esc(
          sessRow.device_name || ""
        )}<br/><small>${esc(sessRow.token_prefix)}…</small></div>`;
        const kick = document.createElement("button");
        kick.type = "button";
        kick.className = "tiny";
        kick.textContent = "Düşür";
        kick.onclick = async () => {
          try {
            await api("/api/mobil/kick", {
              method: "POST",
              body: JSON.stringify({ token_prefix: sessRow.token_prefix, actor: "mimar" }),
            });
            setMsg("oturum düşürüldü");
            again();
          } catch (e) {
            setMsg(String(e.message || e), false);
          }
        };
        const actions = document.createElement("div");
        actions.className = "row-actions";
        actions.appendChild(kick);
        row.appendChild(actions);
        sessEl.appendChild(row);
      });
      if (!(sess.sessions || []).length) {
        sessEl.innerHTML = `<p class="hint">Oturum yok</p>`;
      }

      const motorKeys = [
        "sohbet",
        "hafiza",
        "ses",
        "sahne",
        "video",
        "mimar",
        "tercume",
        "programlama",
        "okuma",
      ];
      const motorLabels = {
        sohbet: "Sohbet",
        hafiza: "Hafıza",
        ses: "Ses",
        sahne: "Sahne",
        video: "Video",
        mimar: "Mimar",
        tercume: "Tercüme",
        programlama: "Programlama",
        okuma: "Okuma",
      };
      (users.users || []).forEach((u) => {
        const motors = u.motors || {};
        const openCount = motorKeys.filter((m) => motors[m]).length;
        const row = document.createElement("div");
        row.className = "panel-row user-row";

        const head = document.createElement("button");
        head.type = "button";
        head.className = "user-head";
        head.innerHTML = `<span class="user-head-main"><b>${esc(u.kullanici)}</b> · ${esc(
          u.role || "user"
        )}</span><span class="user-head-meta">${openCount}/${motorKeys.length} açık · dokun</span><span class="user-chev">▾</span>`;

        const body = document.createElement("div");
        body.className = "user-body hidden";
        body.innerHTML = `<p class="hint user-body-hint">Bu kullanıcı için motor izinleri — işaretle, Kaydet. <b>Sahne</b>: sohbet yüzü (varsayılan kapalı).</p>
          <div class="motor-grid">${motorKeys
            .map(
              (m) =>
                `<label class="chk" title="${
                  m === "sahne" ? "Sohbet sahne yüzü — kullanıcıya aç/kapa" : esc(motorLabels[m] || m)
                }"><input type="checkbox" data-motor="${m}" ${
                  motors[m] ? "checked" : ""
                }/> ${esc(motorLabels[m] || m)}</label>`
            )
            .join("")}</div>`;

        const save = document.createElement("button");
        save.type = "button";
        save.className = "primary tiny";
        save.textContent = "İzinleri kaydet";
        save.onclick = async (ev) => {
          ev.stopPropagation();
          const payload = {};
          body.querySelectorAll("input[type=checkbox]").forEach((inp) => {
            payload[inp.dataset.motor] = inp.checked;
          });
          if (payload.sahne) {
            payload.sohbet = true;
            const sohbetInp = body.querySelector('input[data-motor="sohbet"]');
            if (sohbetInp) sohbetInp.checked = true;
          }
          try {
            await api("/api/mobil/acl", {
              method: "POST",
              body: JSON.stringify({ kullanici: u.kullanici, motors: payload, actor: "mimar" }),
            });
            setMsg(`${u.kullanici} izinleri kaydedildi`);
            const n = motorKeys.filter((m) => payload[m]).length;
            head.querySelector(".user-head-meta").textContent = `${n}/${motorKeys.length} açık · dokun`;
            const me = readWho();
            if (me && me.kullanici === u.kullanici) {
              me.motors = { ...(me.motors || {}), ...payload };
              localStorage.setItem(LS.who, JSON.stringify(me));
              applySahneGate(me);
              if (el("who")) {
                el("who").textContent = `${me.kullanici} · ${me.role || "user"}${
                  me.is_admin ? " · yönetici" : ""
                }${me.device_kind ? " · " + me.device_kind : ""}${
                  sahneAllowed(me) ? " · sahne" : ""
                }`;
              }
            }
          } catch (e) {
            setMsg(String(e.message || e), false);
          }
        };
        body.appendChild(save);

        head.onclick = () => {
          const open = body.classList.contains("hidden");
          // Aynı anda tek kullanıcı açık kalsın
          usersEl.querySelectorAll(".user-body").forEach((b) => b.classList.add("hidden"));
          usersEl.querySelectorAll(".user-row").forEach((r) => r.classList.remove("open"));
          usersEl.querySelectorAll(".user-chev").forEach((c) => {
            c.textContent = "▾";
          });
          if (open) {
            body.classList.remove("hidden");
            row.classList.add("open");
            head.querySelector(".user-chev").textContent = "▴";
          }
        };

        row.appendChild(head);
        row.appendChild(body);
        usersEl.appendChild(row);
      });
      if (!(users.users || []).length) {
        usersEl.innerHTML = `<p class="hint">Kullanıcı yok</p>`;
      }
    } catch (e) {
      statusEl.textContent = "Panel yüklenemedi: " + String(e.message || e);
      pendEl.innerHTML = `<p class="hint">Tekrar Yenile (panel içi) dene</p>`;
    } finally {
      _panelBusy = false;
    }
  }
  el("btnRefreshPanel").onclick = () => refreshPanel("");
  if (el("btnRefreshPanel2")) el("btnRefreshPanel2").onclick = () => refreshPanel("2");

  async function doWol() {
    try {
      const j = await api("/api/mobil/wol", { method: "POST", body: JSON.stringify({}) });
      setMsg(j.ok ? `WoL: ${j.message || "gönderildi"}` : j.error || "WoL başarısız", !!j.ok);
    } catch (e) {
      setMsg(String(e.message || e), false);
    }
  }
  el("btnWol").onclick = doWol;
  if (el("btnWol2")) el("btnWol2").onclick = doWol;

  /* Mobil (iOS/Android): async fetch sonrası Audio.play() NotAllowedError yutar.
     İlk dokunuşta HTMLAudio + AudioContext kilidini aç; TTS'i blob URL ile aynı player'da çal. */
  let ttsPlayer = null;
  let audioUnlocked = false;
  let sharedAudioCtx = null;

  function ensureTtsPlayer() {
    if (ttsPlayer) return ttsPlayer;
    ttsPlayer = new Audio();
    ttsPlayer.setAttribute("playsinline", "");
    ttsPlayer.setAttribute("webkit-playsinline", "");
    ttsPlayer.playsInline = true;
    ttsPlayer.preload = "auto";
    return ttsPlayer;
  }

  const SILENT_WAV =
    "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=";
  let ttsPlayGen = 0;

  function unlockMobileAudio() {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (Ctx) {
        if (!sharedAudioCtx) sharedAudioCtx = new Ctx();
        if (sharedAudioCtx.state === "suspended") void sharedAudioCtx.resume();
      }
    } catch (_) {}
    if (audioUnlocked) return;
    audioUnlocked = true;
    const unlockGen = ttsPlayGen;
    try {
      if (sharedAudioCtx) {
        const buf = sharedAudioCtx.createBuffer(1, 1, 22050);
        const src = sharedAudioCtx.createBufferSource();
        src.buffer = buf;
        src.connect(sharedAudioCtx.destination);
        src.start(0);
      }
    } catch (_) {}
    try {
      // iOS: kilidi açılan element = TTS çalan element (aynı Audio)
      const a = ensureTtsPlayer();
      a.src = SILENT_WAV;
      const p = a.play();
      if (p && typeof p.then === "function") {
        p.then(() => {
          // Gerçek TTS başladıysa (gen arttı) sessiz warm-up'ı kesme
          if (unlockGen !== ttsPlayGen) return;
          try {
            if ((a.currentSrc || a.src || "").indexOf("data:audio/wav") === 0) {
              a.pause();
              a.currentTime = 0;
            }
          } catch (_) {}
        }).catch(() => {});
      }
    } catch (_) {}
    try {
      if (window.speechSynthesis) {
        window.speechSynthesis.resume();
        const u = new SpeechSynthesisUtterance(" ");
        u.volume = 0;
        window.speechSynthesis.speak(u);
        window.speechSynthesis.cancel();
      }
    } catch (_) {}
  }

  function b64ToBlob(b64, mime) {
    const bin = atob(b64);
    const n = bin.length;
    const bytes = new Uint8Array(n);
    for (let i = 0; i < n; i++) bytes[i] = bin.charCodeAt(i);
    return new Blob([bytes], { type: mime || "audio/mpeg" });
  }

  function playTtsBlob(blob) {
    return new Promise((resolve) => {
      if (!blob || !blob.size) return resolve();
      unlockMobileAudio();
      let url = "";
      try {
        url = URL.createObjectURL(blob);
      } catch (_) {
        if (meta) meta.textContent = "ses blob açılamadı";
        return resolve();
      }
      const audio = ensureTtsPlayer();
      const myGen = ++ttsPlayGen;
      try {
        audio.pause();
      } catch (_) {}
      const done = (note) => {
        if (myGen !== ttsPlayGen) return resolve();
        try {
          URL.revokeObjectURL(url);
        } catch (_) {}
        audio.onended = null;
        audio.onerror = null;
        if (note && meta) {
          const cur = String(meta.textContent || "");
          if (!cur.includes(note)) meta.textContent = (cur ? cur + " · " : "") + note;
        }
        resolve();
      };
      audio.onended = () => done();
      audio.onerror = () => done("ses dosyası hatası");
      audio.src = url;
      try {
        audio.load();
      } catch (_) {}
      const p = audio.play();
      if (p && typeof p.catch === "function") {
        p.catch((err) => {
          const name = String((err && err.name) || err || "");
          void speakLocal("Cevap hazır.").finally(() =>
            done(
              /NotAllowed|NotSupported|AbortError/i.test(name)
                ? "tarayıcı sesi engelledi — bir kez dokunup tekrar dene"
                : "ses çalınamadı",
            ),
          );
        });
      }
    });
  }

  function playTtsBase64(b64, mime) {
    if (!b64) return Promise.resolve();
    try {
      return playTtsBlob(b64ToBlob(b64, mime || "audio/mpeg"));
    } catch (_) {
      if (meta) meta.textContent = "ses verisi okunamadı";
      return Promise.resolve();
    }
  }

  function trimHistoryForVoice() {
    // Kısa bağlam = daha hızlı + az sapma
    return history.slice(-6).map((m) => ({
      role: m.role,
      content: String(m.content || "").slice(0, 500),
    }));
  }

  function speakLocal(text) {
    return new Promise((resolve) => {
      let settled = false;
      const finish = () => {
        if (settled) return;
        settled = true;
        resolve();
      };
      try {
        if (!window.speechSynthesis) return finish();
        unlockMobileAudio();
        window.speechSynthesis.cancel();
        window.speechSynthesis.resume();
        const u = new SpeechSynthesisUtterance(String(text || "").slice(0, 160));
        u.lang = "tr-TR";
        u.rate = 1.05;
        u.onend = finish;
        u.onerror = finish;
        window.speechSynthesis.speak(u);
        // iOS bazen onend vermez
        window.setTimeout(finish, Math.min(12000, 800 + String(text || "").length * 60));
      } catch (_) {
        finish();
      }
    });
  }

  async function speakReply(reply) {
    const text = String(reply || "").trim();
    if (!text) return;
    unlockMobileAudio();
    try {
      const token = localStorage.getItem(LS.token) || "";
      const headers = { "Content-Type": "application/json" };
      if (token) headers.Authorization = "Bearer " + token;
      const res = await fetch(base() + "/api/tts", {
        method: "POST",
        headers,
        body: JSON.stringify({ text: text.slice(0, 3000), prosody: false }),
      });
      if (res.ok) {
        const blob = await res.blob();
        if (blob && blob.size > 32) {
          await playTtsBlob(blob);
          return;
        }
      }
    } catch (_) {}
    await speakLocal(text.slice(0, 200));
  }

  function sttLooksBad(text) {
    const t = (text || "").trim();
    if (t.length < 2) return "short";
    if (/^(uh+|ı+|mm+|ee+|aa+|hmm+|şey+|e+|a+)$/i.test(t)) return "filler";
    // Çöp: Türkçe harf yok / aşırı anlamsız
    const letters = (t.match(/[a-zA-ZçğıöşüÇĞİÖŞÜ]/g) || []).length;
    if (letters < Math.max(2, t.length * 0.35)) return "garbage";
    if (/^[^a-zA-ZçğıöşüÇĞİÖŞÜ0-9]+$/.test(t)) return "garbage";
    const lastBot = [...history].reverse().find((m) => m.role === "assistant");
    if (lastBot) {
      const bot = String(lastBot.content || "");
      if (t.length >= 10 && bot.includes(t)) return "echo";
      if (t.length >= 18 && bot.length > 24 && t.includes(bot.slice(0, 24))) return "echo";
    }
    const lastUser = [...history].reverse().find((m) => m.role === "user");
    if (lastUser && String(lastUser.content || "").trim() === t) return "dup";
    return "";
  }

  async function askRepeat(reason) {
    const msg =
      reason === "echo"
        ? "Yankı oldu, tekrar eder misin?"
        : reason === "garbage" || reason === "filler" || reason === "short"
          ? "Seni net duyamadım, tekrar eder misin?"
          : "Anlayamadım, bir daha söyler misin?";
    meta.textContent = msg;
    bubble("bot", msg);
    await speakLocal(msg);
  }

  async function voiceTurn(text, opts = {}) {
    const t = (text || "").trim();
    if (!t) {
      if (opts.live) await askRepeat("short");
      return;
    }
    const bad = sttLooksBad(t);
    if (opts.live && bad) {
      await askRepeat(bad);
      return;
    }
    const t0 = performance.now();
    bubble("user", t);
    history.push({ role: "user", content: t });
    meta.textContent = "düşünüyor…";
    setSahneState("dusun", t);
    try {
      if (!opts.live) {
        api("/api/ses/voice-turn", {
          method: "POST",
          body: JSON.stringify({ state: "thinking" }),
        }).catch(() => ({}));
      }
      const token = localStorage.getItem(LS.token) || "";
      const j = await api("/api/ses/sohbet-tur", {
        method: "POST",
        body: JSON.stringify({
          message: t,
          history: opts.live ? trimHistoryForVoice() : history.slice(-12),
          session_token: token,
          with_tts: true,
        }),
        timeoutMs: 45000,
      });
      let reply = (j.full_reply || "").trim();
      if (!reply || reply === "(Yanıt yok)") {
        setSahneState("hazir");
        await askRepeat("empty");
        // Boş cevabı geçmişe gömme
        history.pop();
        return;
      }
      bubble("bot", reply);
      history.push({ role: "assistant", content: reply });
      if (history.length > 24) history = history.slice(-16);
      meta.textContent = "Rüzgar konuşuyor…";
      setSahneState("konus", reply);
      if (j.tts_base64) await playTtsBase64(j.tts_base64, j.tts_mime);
      else await speakLocal(reply.slice(0, 200));
      const wall = Math.round(performance.now() - t0);
      const bits = [`${wall} ms`];
      if (j.latency_ms != null) bits.push(`sunucu ${j.latency_ms} ms`);
      if (j.tts_error) bits.push(`tts: ${j.tts_error}`);
      else if (j.tts_base64) bits.push("ses çaldı");
      meta.textContent = bits.join(" · ");
      setSahneState("hazir", reply);
    } catch (e) {
      bubble("bot", `[Hata] ${e.message || e}`);
      meta.textContent = String(e.message || e);
      setSahneState("hazir");
      if (opts.live) {
        history.pop();
        await askRepeat("error");
      }
    }
  }

  let sahneYaziTimer = 0;
  if (el("input")) {
    el("input").addEventListener("input", () => {
      clearTimeout(sahneYaziTimer);
      /* PC schedulePaintSpeech(60) hiza — yazı modunu spam etme */
      sahneYaziTimer = window.setTimeout(() => {
        const stage = el("sahneStage");
        if (!stage || stage.classList.contains("hidden")) return;
        if (
          stage.classList.contains("is-live") ||
          stage.classList.contains("is-dinle") ||
          stage.classList.contains("is-dusun")
        ) {
          return;
        }
        const has = !!(el("input").value || "").trim();
        const next = has ? "yazi" : "hazir";
        if (stage.getAttribute("data-sahne-mode") === next) return;
        setSahneState(next);
      }, 60);
    });
  }

  el("btnSend").onclick = async () => {
    unlockMobileAudio();
    const t = el("input").value.trim();
    if (!t) return;
    el("input").value = "";
    bubble("user", t);
    history.push({ role: "user", content: t });
    meta.textContent = "düşünüyor…";
    setSahneState("dusun", t);
    try {
      const se = await runSuperEl(t);
      if (se && se._mobilShort) {
        meta.textContent = "sahne";
        setSahneState("hazir");
        return;
      }
      const token = localStorage.getItem(LS.token) || "";
      if (!token) {
        bubble("bot", "[Hata] Oturum yok — Çıkış yapıp tekrar giriş yap.");
        meta.textContent = "oturum yok";
        setSahneState("hazir");
        return;
      }
      /* Boş «(Yanıt yok)» geçmişi modeli/anı kirletmesin */
      const hist = history
        .slice(-12)
        .filter((m) => !(m.role === "assistant" && String(m.content || "").trim() === "(Yanıt yok)"));
      const j = await api("/api/chat/full", {
        method: "POST",
        timeoutMs: 90000,
        body: JSON.stringify({
          message: t,
          history: hist,
          mode: "genel",
          use_web: false,
          session_token: token,
        }),
      });
      if (j && j.ok === false) {
        const err = (j.error || j.full_reply || "Sohbet reddedildi").trim();
        bubble("bot", `[Hata] ${err}`);
        meta.textContent = err.slice(0, 80);
        setSahneState("hazir");
        if (/oturum|süresi dol/i.test(err)) {
          localStorage.removeItem(LS.token);
          setMsg("Oturum düştü — tekrar giriş yap.", false);
        }
        return;
      }
      const reply = (j.full_reply || j.error || "").trim();
      if (!reply) {
        bubble("bot", "[Hata] Sunucu boş döndü — Yenile deyip bir kez daha dene.");
        meta.textContent = "boş yanıt";
        setSahneState("hazir");
        return;
      }
      bubble("bot", reply);
      history.push({ role: "assistant", content: reply });
      const bits = [];
      if (j.latency_ms != null) bits.push(`${j.latency_ms} ms`);
      if (j.sohbet_onay && j.sohbet_onay.pending) bits.push("onay bekliyor");
      meta.textContent = (bits.length ? bits.join(" · ") + " · " : "") + "Rüzgar konuşuyor…";
      setSahneState("konus", reply);
      await speakReply(reply);
      meta.textContent = bits.length ? bits.join(" · ") + " · ses" : "ses";
      setSahneState("hazir", reply);
    } catch (e) {
      bubble("bot", `[Hata] ${e.message || e}`);
      meta.textContent = String(e.message || e).slice(0, 80);
      setSahneState("hazir");
    }
  };

  el("btnVoiceSend").onclick = async () => {
    unlockMobileAudio();
    const t = el("input").value.trim();
    if (!t) return;
    el("input").value = "";
    await voiceTurn(t);
  };

  let holdPointer = null;
  let mediaStream = null;
  let mediaRecorder = null;
  let mediaChunks = [];
  let mediaMime = "audio/webm";

  function micSecureOk() {
    // localhost güvenli; http://100.x / http://192.168.x telefonda mikrofonu keser
    if (window.isSecureContext) return true;
    const h = (location.hostname || "").toLowerCase();
    return h === "localhost" || h === "127.0.0.1";
  }

  let httpsMicPrefer = "";

  function httpsMicCandidates() {
    const host = (location.hostname || "").trim();
    const out = [];
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      out.push(`https://${host}:8443/mobil/`);
    }
    if (httpsMicPrefer && !out.includes(httpsMicPrefer)) out.unshift(httpsMicPrefer);
    return out;
  }

  function paintHttpsMicBar() {
    const bar = el("httpsMicBar");
    const link = el("httpsMicLink");
    const text = el("httpsMicText");
    if (!bar) return;
    if (micSecureOk()) {
      bar.classList.add("hidden");
      return;
    }
    // Yönlendirme olmadıysa (proxy kapalı) tek kapı linki göster — ikinci ikon değil
    const href = httpsMicCandidates()[0] || "https://127.0.0.1:8443/mobil/";
    if (text) {
      text.textContent =
        "Tek kapı HTTPS hazır değil (PC’de 8443 köprü). Aynı Rüzgar Mobil adresini HTTPS ile aç — yazı+ses birlikte:";
    }
    if (link) {
      link.href = href;
      link.textContent = "Tek kapıyı aç";
    }
    bar.classList.remove("hidden");
  }

  function paintMicBlocked() {
    paintHttpsMicBar();
    const href = httpsMicCandidates()[0] || "https://127.0.0.1:8443/mobil/";
    meta.textContent =
      "Mikrofon için güvenli bağlam yok. Tek adres: " + href + " (Gelişmiş → Devam). Ayrı ikon yok.";
  }

  function _writeWav(samples, sampleRate) {
    const n = samples.length;
    const buf = new ArrayBuffer(44 + n * 2);
    const v = new DataView(buf);
    const w = (o, s) => {
      for (let i = 0; i < s.length; i++) v.setUint8(o + i, s.charCodeAt(i));
    };
    w(0, "RIFF");
    v.setUint32(4, 36 + n * 2, true);
    w(8, "WAVE");
    w(12, "fmt ");
    v.setUint32(16, 16, true);
    v.setUint16(20, 1, true);
    v.setUint16(22, 1, true);
    v.setUint32(24, sampleRate, true);
    v.setUint32(28, sampleRate * 2, true);
    v.setUint16(32, 2, true);
    v.setUint16(34, 16, true);
    w(36, "data");
    v.setUint32(40, n * 2, true);
    let o = 44;
    for (let i = 0; i < n; i++, o += 2) {
      const s = Math.max(-1, Math.min(1, samples[i]));
      v.setInt16(o, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return new Blob([buf], { type: "audio/wav" });
  }

  async function blobToWav16k(blob) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    if (!Ctx) return null;
    const ctx = new Ctx();
    try {
      const ab = await blob.arrayBuffer();
      const decoded = await ctx.decodeAudioData(ab.slice(0));
      const rate = 16000;
      const offline = new OfflineAudioContext(1, Math.ceil(decoded.duration * rate), rate);
      const src = offline.createBufferSource();
      // mono mix
      const ch0 = decoded.getChannelData(0);
      const mono = offline.createBuffer(1, decoded.length, decoded.sampleRate);
      const out = mono.getChannelData(0);
      if (decoded.numberOfChannels > 1) {
        const ch1 = decoded.getChannelData(1);
        for (let i = 0; i < decoded.length; i++) out[i] = (ch0[i] + ch1[i]) * 0.5;
      } else {
        out.set(ch0);
      }
      src.buffer = mono;
      src.connect(offline.destination);
      src.start(0);
      const rendered = await offline.startRendering();
      return _writeWav(rendered.getChannelData(0), rate);
    } finally {
      try {
        await ctx.close();
      } catch (_) {}
    }
  }

  async function sttBlob(blob) {
    const token = localStorage.getItem(LS.token) || "";
    let upload = blob;
    let name = "mobil.webm";
    try {
      const wav = await blobToWav16k(blob);
      if (wav && wav.size > 100) {
        upload = wav;
        name = "mobil.wav";
      }
    } catch (_) {
      // webm yedek
      const ext = (mediaMime || "").includes("mp4") ? "m4a" : "webm";
      name = `mobil.${ext}`;
    }
    const fd = new FormData();
    fd.append("file", upload, name);
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 90000);
    try {
      const res = await fetch(`${base()}/api/stt?lang=tr`, {
        method: "POST",
        headers,
        body: fd,
        signal: ctrl.signal,
      });
      const text = await res.text();
      let j = {};
      try {
        j = JSON.parse(text);
      } catch {
        throw new Error(text.slice(0, 200) || res.statusText);
      }
      if (!res.ok) throw new Error(j.detail || j.error || text.slice(0, 200));
      return String(j.text || j.transcript || "").trim();
    } finally {
      clearTimeout(timer);
    }
  }

  function stopMediaTracks() {
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => {
        try {
          t.stop();
        } catch (_) {}
      });
    }
    mediaStream = null;
  }

  async function stopHoldMic(send) {
    const btn = el("btnMic");
    if (btn) btn.classList.remove("listening");
    if (!send) setSahneState("hazir");
    holdPointer = null;
    const rec = mediaRecorder;
    mediaRecorder = null;
    if (!rec) {
      micBusy = false;
      stopMediaTracks();
      if (send) paintMicBlocked();
      return;
    }
    const done = new Promise((resolve) => {
      rec.onstop = () => resolve();
      try {
        if (rec.state !== "inactive") rec.stop();
        else resolve();
      } catch (_) {
        resolve();
      }
    });
    await done;
    stopMediaTracks();
    micBusy = false;
    if (!liveMode) await releaseWakeLock();
    const chunks = mediaChunks.slice();
    mediaChunks = [];
    if (!send) return;
    if (!chunks.length) {
      meta.textContent = "Ses kaydı boş — basılı tutup konuş.";
      return;
    }
    const blob = new Blob(chunks, { type: mediaMime || "audio/webm" });
    if (blob.size < 800) {
      meta.textContent = "Çok kısa — bir saniye basılı tutup konuş.";
      return;
    }
    meta.textContent = "ses → metin (PC Whisper)…";
    try {
      const text = await sttBlob(blob);
      if (!text) {
        meta.textContent = "Algılanamadı — daha net / biraz daha uzun konuş.";
        return;
      }
      meta.textContent = `algılandı: ${text}`;
      await voiceTurn(text);
    } catch (e) {
      meta.textContent = "STT hata: " + String(e.message || e);
    }
  }

  async function startHoldMic() {
    unlockMobileAudio();
    if (micBusy) {
      meta.textContent = "mikrofon zaten dinliyor…";
      return;
    }
    if (!micSecureOk()) {
      paintMicBlocked();
      return;
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      meta.textContent = "Bu tarayıcıda mikrofon yok.";
      return;
    }
    micBusy = true;
    mediaChunks = [];
    if (el("btnMic")) el("btnMic").classList.add("listening");
    meta.textContent = "dinleniyor… basılı tut, bırakınca gönderilir";
    setSahneState("dinle");
    void requestWakeLock();
    api("/api/ses/voice-turn", {
      method: "POST",
      body: JSON.stringify({ state: "listening" }),
    }).catch(() => ({}));
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
      });
      const types = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg",
      ];
      mediaMime = types.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
      mediaRecorder = mediaMime
        ? new MediaRecorder(mediaStream, { mimeType: mediaMime })
        : new MediaRecorder(mediaStream);
      if (!mediaMime && mediaRecorder.mimeType) mediaMime = mediaRecorder.mimeType;
      mediaRecorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size) mediaChunks.push(ev.data);
      };
      // timeslice yok — tek parça webm (mobilde daha sağlam); bırakınca stop
      mediaRecorder.start();
    } catch (e) {
      micBusy = false;
      stopMediaTracks();
      if (el("btnMic")) el("btnMic").classList.remove("listening");
      const msg = String(e && e.message ? e.message : e);
      if (/NotAllowed|Permission|Denied/i.test(msg)) {
        meta.textContent = "Mikrofon izni reddedildi — site ayarından izin ver.";
      } else if (/secure|Only secure|getUserMedia/i.test(msg) || !micSecureOk()) {
        paintMicBlocked();
      } else {
        meta.textContent = "Mikrofon açılamadı: " + msg;
      }
    }
  }

  const micBtn = el("btnMic");
  if (micBtn) {
    micBtn.addEventListener(
      "pointerdown",
      (ev) => {
        if (ev.button != null && ev.button !== 0) return;
        ev.preventDefault();
        try {
          micBtn.setPointerCapture(ev.pointerId);
        } catch (_) {}
        holdPointer = ev.pointerId;
        void startHoldMic();
      },
      { passive: false },
    );
    const endHold = (ev) => {
      if (holdPointer != null && ev.pointerId !== holdPointer) return;
      ev.preventDefault();
      void stopHoldMic(true);
    };
    micBtn.addEventListener("pointerup", endHold, { passive: false });
    micBtn.addEventListener("pointercancel", endHold, { passive: false });
    micBtn.addEventListener("lostpointercapture", () => {
      if (mediaRecorder) void stopHoldMic(true);
    });
    micBtn.addEventListener("contextmenu", (ev) => ev.preventDefault());
  }

  // Açılışta http uyarısı + HTTPS şerit
  paintHttpsMicBar();
  if (!micSecureOk() && meta) {
    paintMicBlocked();
  }

  // --- Sürekli sohbet: konuş → sus → cevap → yine dinle (aynı kapı) ---
  let liveMode = false;
  let liveStream = null;
  let liveVad = null;
  let liveAbort = false;
  let wakeLock = null;

  async function requestWakeLock() {
    try {
      if (!navigator.wakeLock || !navigator.wakeLock.request) return false;
      wakeLock = await navigator.wakeLock.request("screen");
      wakeLock.addEventListener("release", () => {
        wakeLock = null;
      });
      return true;
    } catch (_) {
      wakeLock = null;
      return false;
    }
  }

  async function releaseWakeLock() {
    try {
      if (wakeLock) await wakeLock.release();
    } catch (_) {}
    wakeLock = null;
  }

  // Sekme / bfcache geri gelince: sahne izin yenile + canlı durum + sürekli sohbet kilidi
  function onSahneResume() {
    if (localStorage.getItem(LS.token)) void refreshWhoMotors();
    if (liveMode) {
      void requestWakeLock();
      setSahneState("dinle");
    }
  }
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState !== "visible") return;
    onSahneResume();
  });
  window.addEventListener("pageshow", (ev) => {
    if (ev.persisted) onSahneResume();
  });
  window.addEventListener("online", () => {
    onSahneResume();
  });

  function paintLiveBtn() {
    const b = el("btnLive");
    if (!b) return;
    b.classList.toggle("listening", liveMode);
    b.textContent = liveMode ? "⏹ Durdur" : "Sürekli sohbet";
    if (liveMode) setSahneState("dinle");
    else setSahneState("hazir");
  }

  function stopLiveVad() {
    if (liveVad) {
      try {
        liveVad.close();
      } catch (_) {}
    }
    liveVad = null;
  }

  function stopLiveStream() {
    stopLiveVad();
    if (liveStream) {
      liveStream.getTracks().forEach((t) => {
        try {
          t.stop();
        } catch (_) {}
      });
    }
    liveStream = null;
  }

  function attachVad(stream) {
    const Ctx = window.AudioContext || window.webkitAudioContext;
    const ctx = new Ctx();
    const src = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 2048;
    src.connect(analyser);
    const data = new Uint8Array(analyser.fftSize);
    return {
      rms() {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        return Math.sqrt(sum / data.length);
      },
      async close() {
        try {
          await ctx.close();
        } catch (_) {}
      },
    };
  }

  function sleep(ms) {
    return new Promise((r) => setTimeout(r, ms));
  }

  async function recordUntilSilence(stream) {
    if (!liveVad) liveVad = attachVad(stream);
    const SPEECH = 0.03;
    const SILENCE_MS = 750;
    const WAIT_SPEECH_MS = 20000;
    const MAX_REC_MS = 18000;
    const MIN_SPEECH_MS = 350;
    const tick = 50;
    meta.textContent = "sürekli: dinliyorum — konuşun";

    // 1) Önce konuşma gelsin (boşluğu kaydetme → STT daha hızlı/temiz)
    let waited = 0;
    while (!liveAbort && liveMode && waited < WAIT_SPEECH_MS) {
      await sleep(tick);
      waited += tick;
      if ((liveVad ? liveVad.rms() : 0) >= SPEECH) break;
    }
    if (liveAbort || !liveMode) return null;
    if ((liveVad ? liveVad.rms() : 0) < SPEECH && waited >= WAIT_SPEECH_MS) return null;

    // 2) Kaydı konuşma başında aç
    const chunks = [];
    const types = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
    const mime = types.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
    const rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
    const useMime = mime || rec.mimeType || "audio/webm";
    rec.ondataavailable = (ev) => {
      if (ev.data && ev.data.size) chunks.push(ev.data);
    };
    rec.start(150);

    let speechMs = 0;
    let silenceMs = 0;
    let recMs = 0;
    meta.textContent = "sürekli: duyuyorum…";
    while (!liveAbort && liveMode && recMs < MAX_REC_MS) {
      await sleep(tick);
      recMs += tick;
      const level = liveVad ? liveVad.rms() : 0;
      if (level >= SPEECH) {
        speechMs += tick;
        silenceMs = 0;
      } else {
        silenceMs += tick;
        if (speechMs >= MIN_SPEECH_MS && silenceMs >= SILENCE_MS) break;
      }
    }

    const stopped = new Promise((resolve) => {
      rec.onstop = () => resolve();
      try {
        if (rec.state !== "inactive") rec.stop();
        else resolve();
      } catch (_) {
        resolve();
      }
    });
    await stopped;
    if (speechMs < MIN_SPEECH_MS) return null;
    const blob = new Blob(chunks, { type: useMime });
    if (blob.size < 700) return null;
    return blob;
  }

  async function liveLoop() {
    micBusy = true;
    paintLiveBtn();
    try {
      if (!micSecureOk()) {
        paintMicBlocked();
        liveMode = false;
        paintLiveBtn();
        return;
      }
      const woke = await requestWakeLock();
      liveStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      liveVad = attachVad(liveStream);
      meta.textContent = woke
        ? "sürekli: ekran açık tutulacak — konuşun"
        : "sürekli: dinliyorum (ekran kilidi desteklenmiyor — ekranı elle açık tut)";

      while (liveMode && !liveAbort) {
        const blob = await recordUntilSilence(liveStream);
        if (!liveMode || liveAbort) break;
        if (!blob) {
          meta.textContent = "sürekli: ses yok — yine dinliyorum";
          continue;
        }
        meta.textContent = "sürekli: ses → metin…";
        let text = "";
        try {
          mediaMime = blob.type || "audio/webm";
          text = await sttBlob(blob);
        } catch (e) {
          meta.textContent = "sürekli STT: " + String(e.message || e);
          await sleep(400);
          continue;
        }
        if (!text) {
          await askRepeat("short");
          if (!liveMode || liveAbort) break;
          await sleep(500);
          continue;
        }
        // Algılananı göster — saçma olsa bile kullanıcı görsün
        meta.textContent = "algı: " + text.slice(0, 80);
        await voiceTurn(text, { live: true });
        if (!liveMode || liveAbort) break;
        // TTS / yerel ses yankısı karışmasın
        meta.textContent = "sürekli: kısa bekleme…";
        await sleep(1000);
        meta.textContent = "sürekli: yine dinliyorum…";
      }
    } catch (e) {
      meta.textContent = "Sürekli sohbet açılamadı: " + String(e.message || e);
    } finally {
      liveMode = false;
      liveAbort = false;
      micBusy = false;
      stopLiveStream();
      await releaseWakeLock();
      paintLiveBtn();
      if (meta && !/açılamadı|STT|Hata/i.test(String(meta.textContent || ""))) {
        meta.textContent = "sürekli sohbet kapalı";
      }
    }
  }

  if (el("btnLive")) {
    el("btnLive").onclick = () => {
      unlockMobileAudio();
      if (liveMode) {
        liveAbort = true;
        liveMode = false;
        void releaseWakeLock();
        meta.textContent = "sürekli: durduruluyor…";
        paintLiveBtn();
        return;
      }
      if (micBusy) {
        meta.textContent = "Önce basılı tutmayı bırak / bekleyin.";
        return;
      }
      liveAbort = false;
      liveMode = true;
      void liveLoop();
    };
  }

  // İlk jest: ses kilidini aç (iOS/Android autoplay)
  document.addEventListener(
    "pointerdown",
    () => {
      unlockMobileAudio();
    },
    { passive: true, once: false },
  );

  async function doLogout() {
    liveAbort = true;
    liveMode = false;
    stopLiveStream();
    await releaseWakeLock();
    const token = localStorage.getItem(LS.token);
    try {
      if (token) await api("/api/mobil/logout", { method: "POST", body: JSON.stringify({ token }) });
    } catch (_) {}
    localStorage.removeItem(LS.token);
    localStorage.removeItem(LS.who);
    history = [];
    chat.innerHTML = "";
    showGate();
    setMsg("Çıkış yapıldı.");
  }
  if (el("btnLogout")) el("btnLogout").onclick = doLogout;

  const tok = localStorage.getItem(LS.token);
  const whoRaw = localStorage.getItem(LS.who);
  if (tok && whoRaw) {
    try {
      showChat(JSON.parse(whoRaw));
    } catch {
      showGate();
    }
  }

  // PWA kur / ana ekrana ekle (Chrome/Edge beforeinstallprompt)
  let deferredInstall = null;
  const installBar = el("installBar");
  const installHint = el("installHint");
  const standAlone =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.navigator.standalone === true;

  function paintInstallHint() {
    if (!installHint) return;
    if (standAlone) {
      installHint.textContent = "Uygulama modunda açık.";
      return;
    }
    const isDesktop = window.matchMedia("(min-width: 900px)").matches;
    installHint.textContent = isDesktop
      ? "Masaüstü: «Kur» veya masaüstündeki «Rüzgar Mobil» ikonu · Edge/Chrome → Yükle."
      : "Telefon: tarayıcı menüsü → Ana ekrana ekle / Uygulamayı yükle.";
  }
  paintInstallHint();

  window.addEventListener("beforeinstallprompt", (ev) => {
    ev.preventDefault();
    deferredInstall = ev;
    if (installBar && !standAlone && localStorage.getItem("ruzgar_pwa_install_dismiss") !== "1") {
      installBar.classList.remove("hidden");
    }
  });

  if (el("btnInstall")) {
    el("btnInstall").onclick = async () => {
      if (!deferredInstall) {
        setMsg("Tarayıcı kur önerisini göstermiyor — menüden «Uygulamayı yükle / Ana ekrana ekle» kullanın.", false);
        return;
      }
      deferredInstall.prompt();
      try {
        await deferredInstall.userChoice;
      } catch (_) {}
      deferredInstall = null;
      if (installBar) installBar.classList.add("hidden");
    };
  }
  if (el("btnInstallDismiss")) {
    el("btnInstallDismiss").onclick = () => {
      localStorage.setItem("ruzgar_pwa_install_dismiss", "1");
      if (installBar) installBar.classList.add("hidden");
    };
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .getRegistrations()
      .then((regs) => Promise.all(regs.map((r) => r.update())))
      .catch(() => {});
    navigator.serviceWorker.register("./sw.js?v=23").catch(() => {});
  }

  // Kapı durumu — görünür sağlık satırı + LAN/Tailscale / HTTPS mic ipuçları
  api("/api/mobil/status")
    .then((st) => {
      if (st && st.ok) {
        const bits = [`kapı açık · ${st.version || "mobil"}`];
        if (st.users != null) bits.push(`${st.users} kullanıcı`);
        const er = st.erisim || null;
        if (er && er.lan_open === false) {
          bits.push("LAN kapalı (PC’de 0.0.0.0 gerekir)");
          setMsg(bits.join(" · "), false);
          return;
        }
        if (er && Array.isArray(er.https_urls) && er.https_urls.length) {
          httpsMicPrefer =
            er.https_urls.find((u) => String(u).includes("100.")) || er.https_urls[0];
        } else if (er && Array.isArray(er.urls) && er.urls.length) {
          httpsMicPrefer = er.urls.find((u) => String(u).startsWith("https:")) || er.urls[0];
        }
        paintHttpsMicBar();
        if (er && Array.isArray(er.urls) && er.urls.length && baseInput) {
          const prefer =
            er.urls.find((u) => String(u).includes("100.")) ||
            er.urls.find((u) => String(u).startsWith("https:")) ||
            er.urls[0];
          const asBase = String(prefer).replace(/\/mobil\/?$/, "");
          if (
            !localStorage.getItem(LS.base) ||
            /127\.0\.0\.1:8779|localhost:8779/i.test(baseInput.value || "")
          ) {
            baseInput.value = asBase;
            try {
              localStorage.setItem(LS.base, asBase);
            } catch (_) {}
          }
        }
        if (micSecureOk()) bits.push("tek kapı (yazı+ses)");
        else bits.push("HTTPS köprü gerekli");
        setMsg(bits.join(" · "), micSecureOk());
        if (!micSecureOk()) paintMicBlocked();
      }
    })
    .catch(() =>
      setMsg(
        "Kapıya ulaşılamadı — PC’de Rüzgar + HTTPS 8443 açık mı? Tek adres: https://<PC-IP>:8443/mobil/",
        false,
      ),
    );
})();
