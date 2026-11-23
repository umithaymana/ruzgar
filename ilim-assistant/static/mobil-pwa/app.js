(() => {
  const LS = {
    base: "ruzgar_pwa_base",
    token: "ruzgar_pwa_token",
    who: "ruzgar_pwa_who",
    deviceId: "ruzgar_pwa_device_id",
    deviceKind: "ruzgar_pwa_device_kind",
    regDraft: "ruzgar_pwa_reg_draft",
    deviceName: "ruzgar_pwa_device_name",
    livePref: "ruzgar_pwa_live", // 1=sürekli sohbet açık (varsayılan)
  };

  const el = (id) => document.getElementById(id);
  const baseInput = el("baseUrl");
  const gateMsg = el("gateMsg");
  const chat = el("chat");
  const meta = el("meta");
  const SAHNE_PLACEHOLDER = "Yaz. Cevabı ben buradan söyleyeyim.";
  let history = [];
  let micBusy = false;
  /** STT duygu hattı → /api/tts emotion (masa lastVoiceEmotion ile aynı rol) */
  let lastVoiceEmotion = null;
  /** Son mic RMS (0–1) — /api/stt mic_energy → fuse_emotion (masa parity) */
  let lastMicEnergy01 = 0.45;

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

  /** Kullanıcı «sahneyi kapat» dedi — ACL açık kalsa da yüzü gizle; «aç» ile geri gelir */
  let sahneUiForcedOff = false;

  function openMobilSahneUi() {
    if (!sahneAllowed()) {
      return { ok: false, reason: "izin" };
    }
    sahneUiForcedOff = false;
    const who = readWho();
    applySahneGate(who);
    const stage = el("sahneStage");
    const view = el("chatView");
    if (stage) {
      stage.classList.remove("hidden");
      stage.setAttribute("aria-hidden", "false");
      try {
        stage.inert = false;
      } catch (_) {}
    }
    if (view) {
      view.classList.add("has-sahne");
      view.classList.remove("sheet-open");
      if (!view.getAttribute("data-sahne-abc")) {
        view.setAttribute("data-sahne-abc", "A");
      }
    }
    applySahneOrgan("yuz");
    setSahneState("hazir");
    syncSahneSheetBtn();
    return { ok: true };
  }

  function closeMobilSahneUi() {
    sahneUiForcedOff = true;
    const stage = el("sahneStage");
    const view = el("chatView");
    if (stage) {
      stage.classList.add("hidden");
      stage.setAttribute("aria-hidden", "true");
      try {
        stage.inert = true;
      } catch (_) {}
      stage.classList.remove("is-live", "is-dinle", "is-dusun", "is-yazi", "organ-on");
    }
    if (view) {
      view.classList.remove("has-sahne", "sheet-open", "sahne-busy");
    }
    try {
      document.body.classList.remove("mobil-sahne-organ-on");
    } catch (_) {}
    syncSahneSheetBtn();
    return { ok: true };
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
    const on = sahneAllowed(who) && !sahneUiForcedOff;
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
    zoom: 7,
    tip: "ulke",
    mode: "uydu",
    hedef: "Türkiye",
    label: "Türkiye",
    year: 2015,
  };

  function haritaPilotSehir(s) {
    // Açık sehir öncelikli; yoksa yerel bina dosyası için etiket/koordinat.
    const explicit = String(s.sehir || "").toLowerCase().trim();
    if (explicit) return explicit;
    const blob = [s.label, s.hedef, s.tour_place]
      .filter(Boolean)
      .join(" ")
      .toLowerCase()
      .replace(/i̇/g, "i");
    if (blob.indexOf("istanbu") >= 0) return "istanbul";
    if (blob.indexOf("ankara") >= 0) return "ankara";
    if (blob.indexOf("bursa") >= 0) return "bursa";
    if (blob.indexOf("izmir") >= 0) return "izmir";
    const lat = Number(s.lat);
    const lon = Number(s.lon);
    if (!isFinite(lat) || !isFinite(lon)) return "";
    const pilots = [
      { k: "istanbul", lat: 41.0082, lon: 28.9784 },
      { k: "ankara", lat: 39.9334, lon: 32.8597 },
      { k: "bursa", lat: 40.1885, lon: 29.061 },
      { k: "izmir", lat: 38.4192, lon: 27.1287 },
    ];
    let best = "";
    let bestD = 0.32 * 0.32;
    for (let i = 0; i < pilots.length; i++) {
      const c = pilots[i];
      const d =
        (lat - c.lat) * (lat - c.lat) + (lon - c.lon) * (lon - c.lon);
      if (d < bestD) {
        bestD = d;
        best = c.k;
      }
    }
    return best;
  }

  function haritaViewerUrl(st) {
    const s = st || mobilHaritaState;
    const root = (base() || "").replace(/\/$/, "");
    const label = encodeURIComponent(String(s.label || s.hedef || "Türkiye"));
    const sehir = haritaPilotSehir(s);
    const era = encodeURIComponent(String(s.era || "simdi"));
    let url =
      root +
      "/ui/harita-viewer.html?mode=" +
      encodeURIComponent(String(s.mode || "uydu")) +
      "&lat=" +
      Number(s.lat || 39).toFixed(5) +
      "&lon=" +
      Number(s.lon || 35.2).toFixed(5) +
      "&zoom=" +
      Math.max(2, Math.min(18, Number(s.zoom) || 7)) +
      "&label=" +
      label +
      "&year=" +
      (s.year != null ? Number(s.year) : 2015) +
      "&era=" +
      era +
      "&fly=1";
    if (s.tip) url += "&tip=" + encodeURIComponent(String(s.tip));
    if (s.terrain) url += "&terrain=1";
    if (s.tour_play || s.tour) {
      url += "&tour=1&terrain=1";
      const tp = encodeURIComponent(
        String(s.tour_place || s.label || s.hedef || "")
      );
      if (tp) url += "&tour_place=" + tp;
    }
    if (sehir) url += "&sehir=" + encodeURIComponent(sehir) + "&bina=1";
    const cam = s.camera;
    if (cam && isFinite(Number(cam.range_m))) {
      url +=
        "&cam_h=" +
        Number(cam.heading || 0).toFixed(1) +
        "&cam_p=" +
        Number(cam.pitch || -28).toFixed(1) +
        "&cam_r=" +
        Number(cam.range_m).toFixed(0);
    }
    if (s.bbox && s.bbox.length === 4) {
      url +=
        "&bbox=" +
        [s.bbox[0], s.bbox[1], s.bbox[2], s.bbox[3]]
          .map(function (n) {
            return Number(n).toFixed(5);
          })
          .join(",");
    }
    url += "&hv=kamera-rig-v20-fwd-fix&mobil=1&qos=mobil";
    return url;
  }

  function postMobilHaritaTourStart(ifr, tourPayload, st) {
    if (!ifr || !ifr.contentWindow) return false;
    try {
      ifr.contentWindow.postMessage(
        {
          type: "ruzgar-harita-tour",
          action: "start",
          tour: tourPayload || null,
          place: st.tour_place || st.label || st.hedef,
          tip: st.tip,
          lat: st.lat,
          lon: st.lon,
        },
        "*"
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  function scheduleMobilHaritaTourStart(tourPayload) {
    const st = mobilHaritaState;
    const payload = tourPayload || st.tour || null;
    let attempts = 0;
    function trySend() {
      attempts += 1;
      const frame = el("sahneOrganFrame");
      const ifr = frame && frame.querySelector("iframe[data-sahne-harita]");
      if (!ifr) {
        if (attempts < 25) setTimeout(trySend, 300);
        return;
      }
      if (!ifr.getAttribute("data-tour-listen")) {
        ifr.setAttribute("data-tour-listen", "1");
        ifr.addEventListener("load", function () {
          setTimeout(function () {
            postMobilHaritaTourStart(ifr, payload, st);
          }, 400);
        });
      }
      postMobilHaritaTourStart(ifr, payload, st);
      if (attempts < 8) setTimeout(trySend, 900);
    }
    setTimeout(trySend, 500);
  }

  function setMobilHaritaToolsMenuOpen(tools, open) {
    if (!tools) return;
    const more = tools.querySelector(".harita-tools-more");
    const menu = tools.querySelector(".harita-tools-menu");
    if (!more || !menu) return;
    const on = !!open;
    tools.classList.toggle("is-menu-open", on);
    more.setAttribute("aria-expanded", on ? "true" : "false");
    menu.hidden = !on;
  }

  function ensureMobilHaritaTools(frame) {
    let tools = frame.querySelector(".harita-tools");
    if (tools && !tools.querySelector(".harita-tools-menu")) {
      tools.remove();
      tools = null;
    }
    if (tools) return tools;
    tools = document.createElement("div");
    tools.className = "harita-tools";
    tools.setAttribute("role", "toolbar");
    tools.setAttribute("aria-label", "Harita kontrolleri");
    tools.innerHTML =
      '<button type="button" data-h="zoom_in" title="Yaklaştır">+</button>' +
      '<button type="button" data-h="zoom_out" title="Uzaklaştır">−</button>' +
      '<button type="button" class="harita-tools-more" aria-expanded="false" aria-haspopup="true" title="Diğer kontroller" aria-label="Diğer harita kontrolleri">' +
      '<span class="harita-tools-more-icon" aria-hidden="true"></span>' +
      "</button>" +
      '<div class="harita-tools-menu" hidden role="menu" aria-label="Harita modları">' +
      '<button type="button" role="menuitem" data-h="mode_2d">2D</button>' +
      '<button type="button" role="menuitem" data-h="mode_3d" title="3D Cesium">3D</button>' +
      '<button type="button" role="menuitem" data-h="mode_4d">4D</button>' +
      '<button type="button" role="menuitem" data-h="mode_uydu">Uydu</button>' +
      '<button type="button" role="menuitem" data-h="mode_tur">Tur</button>' +
      '<button type="button" role="menuitem" data-h="tour_start" title="Dünya Gezgini">Gezgin</button>' +
      '<button type="button" role="menuitem" data-h="tour_prev" title="Önceki bölüm">Geri</button>' +
      '<button type="button" role="menuitem" data-h="tour_next" title="Sonraki bölüm">İleri</button>' +
      '<button type="button" role="menuitem" data-h="tour_pause" title="Duraklat">Duraklat</button>' +
      '<button type="button" role="menuitem" data-h="tour_resume" title="Devam Et">Devam Et</button>' +
      '<button type="button" role="menuitem" data-h="tour_closer" title="Alçal">Alçal</button>' +
      '<button type="button" role="menuitem" data-h="tour_farther" title="Yüksel">Yüksel</button>' +
      '<button type="button" role="menuitem" data-h="tour_altitude_reset" title="Kuş irtifası">Kuş</button>' +
      '<button type="button" role="menuitem" data-h="tour_slower" title="Hız azalt">Yavaş</button>' +
      '<button type="button" role="menuitem" data-h="tour_faster" title="Hızlandır">Hızlı</button>' +
      '<button type="button" role="menuitem" data-h="tour_stop" title="Turu Bitir">Turu Bitir</button>' +
      '<button type="button" role="menuitem" data-h="tour_skip" title="Bölüm atla">Atla</button>' +
      '<button type="button" role="menuitem" data-h="mode_sentinel" title="Sentinel-2">S2</button>' +
      '<button type="button" role="menuitem" data-h="mode_pano" title="Mapillary">Pano</button>' +
      '<button type="button" role="menuitem" data-h="mode_f4" title="F4map yedek">F4</button>' +
      "</div>";
    tools.addEventListener("click", (ev) => {
      const more = ev.target && ev.target.closest(".harita-tools-more");
      if (more && tools.contains(more)) {
        setMobilHaritaToolsMenuOpen(tools, !tools.classList.contains("is-menu-open"));
        return;
      }
      const btn = ev.target && ev.target.closest("button[data-h]");
      if (!btn || !tools.contains(btn)) return;
      const act = btn.getAttribute("data-h");
      if (!act) return;
      if (String(act).indexOf("mode_") === 0 || String(act).indexOf("tour_") === 0) {
        setMobilHaritaToolsMenuOpen(tools, false);
      }
      applyMobilHaritaCommand({ action: act });
    });
    if (!window.__ruzgarMobilHaritaToolsDocClose) {
      window.__ruzgarMobilHaritaToolsDocClose = true;
      document.addEventListener(
        "pointerdown",
        (ev) => {
          document.querySelectorAll(".harita-tools.is-menu-open").forEach((t) => {
            if (t.contains(ev.target)) return;
            setMobilHaritaToolsMenuOpen(t, false);
          });
        },
        true,
      );
    }
    frame.appendChild(tools);
    return tools;
  }

  function formatMobilHaritaLive(st) {
    const s = st || mobilHaritaState || {};
    const center = s.centerLabel || s.label || s.hedef || "—";
    const z = Math.round(Number(s.zoom) || 7);
    const katman =
      s.baseLabel ||
      ({ esri: "Esri Uydu", osm: "OSM", gibs: "NASA GIBS" }[s.base] ||
        String(s.mode || "UYDU").toUpperCase());
    let t = "Merkez: " + center + " · Zoom: " + z + " · Katman: " + katman;
    if (s.buildings != null || s.roads != null) {
      t +=
        " · bina " +
        (s.buildings != null ? s.buildings : "—") +
        " · yol " +
        (s.roads != null ? s.roads : "—");
    }
    return t;
  }

  function paintMobilHaritaLiveLabels() {
    const live = formatMobilHaritaLive(mobilHaritaState);
    const meta = el("sahneOrganMeta");
    const soz = el("sahneSoz");
    if (meta) {
      meta.hidden = false;
      meta.textContent = live;
    }
    if (soz) soz.textContent = "Harita · " + live;
  }

  function applyMobilHaritaViewSync(msg) {
    if (!msg || msg.type !== "ruzgar-harita-view") return;
    const root = el("sahneOrgan");
    if (!root || root.getAttribute("data-organ") !== "harita") return;
    const st = mobilHaritaState;
    if (msg.lat != null) st.lat = Number(msg.lat);
    if (msg.lon != null) st.lon = Number(msg.lon);
    if (msg.zoom != null) st.zoom = Number(msg.zoom);
    if (msg.centerLabel || msg.label) {
      st.centerLabel = String(msg.centerLabel || msg.label);
      st.label = st.centerLabel;
    }
    if (msg.base) st.base = String(msg.base);
    if (msg.baseLabel) st.baseLabel = String(msg.baseLabel);
    if (msg.terrain != null) st.terrain = !!msg.terrain;
    if (msg.buildings != null) st.buildings = Number(msg.buildings);
    if (msg.roads != null) st.roads = Number(msg.roads);
    paintMobilHaritaLiveLabels();
  }

  function applyMobilHaritaCinema(msg) {
    if (!msg || msg.type !== "ruzgar-harita-cinema") return;
    const on = !!msg.on;
    document.body.classList.toggle("mobil-harita-cinema", on);
    const face = el("sahneFace");
    if (face) face.classList.toggle("is-cinema-hide", on);
  }

  function applyMobilHaritaReady(msg) {
    if (!msg || msg.type !== "ruzgar-harita-ready") return;
    if (!(mobilHaritaState.tour_play || mobilHaritaState.tour)) return;
    scheduleMobilHaritaTourStart(mobilHaritaState.tour || null);
  }

  if (!window.__ruzgarMobilHaritaViewListen) {
    window.__ruzgarMobilHaritaViewListen = true;
    window.addEventListener("message", function (ev) {
      try {
        applyMobilHaritaViewSync(ev && ev.data);
        applyMobilHaritaCinema(ev && ev.data);
        applyMobilHaritaReady(ev && ev.data);
      } catch (_) {}
    });
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
    const live = formatMobilHaritaLive(mobilHaritaState);
    if (meta) {
      meta.hidden = false;
      meta.textContent = live;
    }
    const soz = el("sahneSoz");
    if (soz) soz.textContent = "Harita · " + live;
  }

  function applyMobilHaritaCommand(cmd) {
    const c = cmd || {};
    const action = String(c.action || c.fiil || "show");
    const st = mobilHaritaState;
    const geo = c.geo || null;
    if (action === "mode_2d" || action === "2d") st.mode = "2d";
    if (action === "mode_3d" || action === "3d") {
      st.mode = "3d";
      const tip3 = String(st.tip || "");
      if (
        !/^(dag|gecit|kopru|bina|nokta)$/i.test(tip3) &&
        (Number(st.zoom) || 7) < 15
      ) {
        st.zoom = 16;
      }
    }
    if (action === "mode_4d" || action === "4d") st.mode = "4d";
    if (action === "mode_uydu" || action === "uydu") st.mode = "uydu";
    if (action === "mode_tur" || action === "tur") {
      st.mode = "tur";
      if ((Number(st.zoom) || 7) < 5) st.zoom = 5;
    }
    if (action === "mode_f4" || action === "f4") {
      st.mode = "f4";
      if ((Number(st.zoom) || 7) < 15) st.zoom = 16;
    }
    if (action === "mode_sentinel" || action === "sentinel") {
      st.mode = "sentinel";
      if ((Number(st.zoom) || 7) < 10) st.zoom = 11;
    }
    if (action === "mode_pano" || action === "pano") {
      st.mode = "pano";
      if ((Number(st.zoom) || 7) < 15) st.zoom = 17;
    }
    if (action === "era_gecmis") {
      st.era = "gecmis";
      st.mode = st.mode === "2d" ? "3d" : st.mode;
      if ((Number(st.zoom) || 7) < 14) st.zoom = 15;
    }
    if (action === "era_gelecek") {
      st.era = "gelecek";
      st.mode = st.mode === "2d" ? "3d" : st.mode;
      if ((Number(st.zoom) || 7) < 14) st.zoom = 15;
    }
    if (action === "show_buildings") {
      st.bina = 1;
      st.mode = "3d";
      if ((Number(st.zoom) || 7) < 15) st.zoom = 16;
      const sehirBina = haritaPilotSehir(st);
      if (sehirBina) st.sehir = sehirBina;
    }
    const isMode =
      /^mode_(2d|3d|4d|uydu|tur|f4|sentinel|pano)$/.test(action) ||
      /^(2d|3d|4d|uydu|tur|f4|sentinel|pano|era_gecmis|era_gelecek|show_buildings)$/.test(action);
    const hedefStr = c.hedef != null ? String(c.hedef).trim() : "";
    const hedefIsMode =
      /^(2d|3d|4d|uydu|tur|f4|f4map|sentinel|pano|mapillary|panorama|dunya\s*turu|tarihi|historical)$/i.test(hedefStr);
    if (!isMode || (geo && !hedefIsMode)) {
      if (geo && geo.lat != null && geo.lon != null && !hedefIsMode) {
        st.lat = Number(geo.lat);
        st.lon = Number(geo.lon);
        if (geo.zoom != null) st.zoom = Number(geo.zoom);
        else if (geo.tip) {
          const tipZ = {
            ulke: 7,
            il: 11,
            ilce: 13,
            mahalle: 15,
            dag: 14,
            gecit: 16,
            vadi: 13,
            kanyon: 14,
            nehir: 11,
            bogaz: 14,
            volkan: 14,
            kopru: 17,
            bina: 18,
            nokta: 18,
          };
          st.zoom = tipZ[String(geo.tip)] || 11;
        }
        if (geo.tip) st.tip = String(geo.tip);
        if (geo.bbox) st.bbox = geo.bbox;
        st.label = geo.label || hedefStr || st.label;
        st.centerLabel = geo.label || hedefStr || st.centerLabel || st.label;
        st.hedef = hedefStr || st.label;
        if (geo.camera && typeof geo.camera === "object") {
          st.camera = {
            lat: Number(geo.camera.lat != null ? geo.camera.lat : st.lat),
            lon: Number(geo.camera.lon != null ? geo.camera.lon : st.lon),
            heading: Number(geo.camera.heading) || 0,
            pitch: Number(geo.camera.pitch) || -28,
            range_m: Number(geo.camera.range_m) || 500,
          };
        } else {
          delete st.camera;
        }
        st.base = st.base || "esri";
        st.baseLabel = st.baseLabel || "Esri Uydu";
      } else if (hedefStr && !hedefIsMode) {
        st.hedef = hedefStr;
        st.label = st.hedef;
      }
    }
    let delta = Number(c.zoom_delta) || 0;
    if (action === "zoom_in" && !delta) delta = 1;
    if (action === "zoom_out" && !delta) delta = -1;
    if (delta) st.zoom = Math.max(2, Math.min(18, (Number(st.zoom) || 7) + delta));
    if ((action === "show" || action === "goster") && !geo && !hedefStr) {
      if (!st.hedef) {
        st.lat = 39;
        st.lon = 35.2;
        st.zoom = 7;
        st.tip = "ulke";
        st.hedef = "Türkiye";
        st.label = "Türkiye";
      }
    }
    // H10.6 Dünya Gezgini — sürekli uçuş (PC ile aynı)
    if (action === "tour_start") {
      st.mode = "3d";
      st.terrain = true;
      st.tour_play = 1;
      st.tour = c.tour || null;
      st.tour_place = c.hedef || (c.tour && c.tour.label) || st.label || st.hedef;
      if (c.tour && c.tour.tip) st.tip = String(c.tour.tip);
      if ((Number(st.zoom) || 7) < 11) st.zoom = 12;
      const sehirTour = haritaPilotSehir(st);
      if (sehirTour) {
        st.sehir = sehirTour;
        st.bina = 1;
      }
    }
    if (
      action === "tour_pause" ||
      action === "tour_resume" ||
      action === "tour_stop" ||
      action === "tour_next" ||
      action === "tour_prev" ||
      action === "tour_skip" ||
      action === "tour_faster" ||
      action === "tour_slower" ||
      action === "tour_closer" ||
      action === "tour_farther" ||
      action === "tour_altitude" ||
      action === "tour_altitude_reset" ||
      action === "tour_turn_left" ||
      action === "tour_turn_right" ||
      action === "tour_forward" ||
      action === "tour_back" ||
      action === "tour_strafe_left" ||
      action === "tour_strafe_right" ||
      action === "tour_walk" ||
      action === "tour_fly" ||
      action === "tour_labels_on" ||
      action === "tour_traffic" ||
      action === "tour_pano_near" ||
      action === "tour_follow_river" ||
      action === "tour_enter_city" ||
      action === "tour_follow_coast" ||
      action === "tour_enter_crater"
    ) {
      try {
        const frame = el("sahneOrganFrame");
        const ifr = frame && frame.querySelector("iframe[data-sahne-harita]");
        if (ifr && ifr.contentWindow) {
          const payload = {
            type: "ruzgar-harita-tour",
            action: String(action).replace(/^tour_/, ""),
          };
          const meters = c.tour_meters != null ? c.tour_meters : c.meters;
          if (meters != null && isFinite(Number(meters))) {
            payload.meters = Number(meters);
            payload.tour_meters = Number(meters);
          }
          ifr.contentWindow.postMessage(payload, "*");
        }
      } catch (_) {}
      if (action === "tour_stop") {
        st.tour_play = 0;
        st.tour = null;
        document.body.classList.remove("mobil-harita-cinema");
      }
      return { ok: true, organ: "harita", state: { ...st }, tour_ctrl: action };
    }
    paintMobilHarita(c.metaText);
    if (action === "tour_start") {
      scheduleMobilHaritaTourStart(c.tour || st.tour || null);
    }
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

  function shortSahneReply(res, reply) {
    bubble("bot", reply);
    history.push({ role: "assistant", content: reply });
    res._mobilShort = true;
    return res;
  }

  async function runSuperEl(text) {
    const stage = el("sahneStage");
    if (!stage) return null;
    // İstemci niyet kapısı — API'ye gereksiz gitme (desktop parity)
    if (!looksLikeSahneCmd(text)) {
      return { ok: false, skipped: "no_sahne_niyet" };
    }
    try {
      const res = await api("/api/sahne/super-el", {
        method: "POST",
        body: JSON.stringify({ text: String(text || "") }),
      });
      if (!res || !res.ok) return res;

      // Zayıf güven → yüzeyi değiştirme (desktop ruzgar-masa guven<0.72)
      const guven = Number(res.guven || 0);
      const act0 = String(res.action || "");
      const strongAct =
        /^(zoom_|mode_|tour_|cam_|stage_|era_|show_buildings)/.test(act0) ||
        act0 === "focus" ||
        act0 === "clear" ||
        res.canli_kamera;
      if (!strongAct && guven < 0.72) {
        res.applied = { ok: false, skipped: "low_guven_sohbet" };
        return res;
      }

      const action = act0;

      /* Gerçek UI — LLM «sahne açıldı» demesin, yüz gerçekten açılsın/kapansın */
      if (action === "stage_open") {
        const opened = openMobilSahneUi();
        if (!opened.ok) {
          return shortSahneReply(
            res,
            "Sahne motorun kapalı — Panelden bu kullanıcıya «Sahne» iznini aç."
          );
        }
        return shortSahneReply(res, "Sahne açıldı.");
      }
      if (action === "stage_close") {
        closeMobilSahneUi();
        return shortSahneReply(res, "Sahne kapandı · sohbet şeridi.");
      }

      /* Organ komutu gelince sahne kapalıysa aç (izin varsa) */
      if (stage.classList.contains("hidden") && sahneAllowed()) {
        openMobilSahneUi();
      }
      if (stage.classList.contains("hidden")) {
        /* İzin yok — organ komutunda yalan söyleme */
        if (res.organ && res.organ !== "yuz") {
          return shortSahneReply(
            res,
            "Sahne kapalı — önce «sahneyi aç» veya panelden sahne izni."
          );
        }
        return null;
      }

      if (res.fiil === "temizle" || action === "clear") {
        applySahneOrgan("yuz");
        return shortSahneReply(res, "Sahne temizlendi · yüz.");
      }
      const mapActs = {
        zoom_in: 1,
        zoom_out: 1,
        mode_2d: 1,
        mode_3d: 1,
        mode_4d: 1,
        mode_uydu: 1,
        mode_tur: 1,
        mode_f4: 1,
        mode_sentinel: 1,
        mode_pano: 1,
        era_gecmis: 1,
        era_gelecek: 1,
        show_buildings: 1,
        show: 1,
        focus: 1,
        tour_start: 1,
        tour_pause: 1,
        tour_resume: 1,
        tour_stop: 1,
        tour_next: 1,
        tour_prev: 1,
        tour_skip: 1,
        tour_faster: 1,
        tour_slower: 1,
        tour_closer: 1,
        tour_farther: 1,
        tour_altitude: 1,
        tour_altitude_reset: 1,
        tour_turn_left: 1,
        tour_turn_right: 1,
        tour_forward: 1,
        tour_back: 1,
        tour_strafe_left: 1,
        tour_strafe_right: 1,
        tour_walk: 1,
        tour_fly: 1,
        tour_labels_on: 1,
        tour_traffic: 1,
        tour_pano_near: 1,
        tour_follow_river: 1,
        tour_enter_city: 1,
        tour_follow_coast: 1,
        tour_enter_crater: 1,
      };
      const organ = res.organ || "yuz";
      /* show/focus yalnız organ=harita iken harita — «sahneyi aç» yüze kalsın */
      if (organ === "harita" || mapActs[action]) {
        const applied = applyMobilHaritaCommand({
          action: action || "show",
          fiil: res.fiil,
          hedef: res.hedef,
          zoom_delta: res.zoom_delta || 0,
          geo: res.geo || null,
          tour: res.tour || null,
          tour_meters: res.tour_meters != null ? res.tour_meters : res.meters,
          meters: res.meters != null ? res.meters : res.tour_meters,
          metaText:
            (res.fiil || action) +
            " · harita" +
            (res.hedef ? " · " + res.hedef : "") +
            (String(action).indexOf("tour_") === 0 ? " · Dünya Gezgini" : ""),
        });
        res.applied = applied;
        const view = el("chatView");
        if (view && view.classList.contains("has-sahne")) {
          view.classList.remove("sheet-open");
          syncSahneSheetBtn();
        }
        if (mapActs[action]) {
          const mode = String(mobilHaritaState.mode || "uydu").toUpperCase();
          let reply =
            "Harita: " +
            (mobilHaritaState.label || res.hedef || "Türkiye") +
            " · " +
            mode +
            " · zoom " +
            mobilHaritaState.zoom +
            ".";
          if (action === "tour_start") {
            reply =
              "Dünya Gezgini: " +
              (mobilHaritaState.label || res.hedef || "hedef") +
              " · 3D sahne.";
          } else if (action === "tour_walk") {
            reply = "Göz hizası · yürüyüş.";
          } else if (action === "mode_3d") reply = "3D moda aldım.";
          else if (action === "mode_4d") reply = "4D zamanlı uyduyu açtım.";
          else if (action === "mode_uydu") reply = "Uydu görüntüsünü açtım.";
          else if (action === "mode_tur") reply = "Dünya turunu başlattım.";
          else if (action === "mode_2d") reply = "2D moda aldım.";
          else if (action === "zoom_in") reply = "Yaklaştırdım · zoom " + mobilHaritaState.zoom;
          else if (action === "zoom_out") reply = "Uzaklaştırdım · zoom " + mobilHaritaState.zoom;
          else if (action === "show" || action === "focus") {
            reply =
              "Harita: " +
              (mobilHaritaState.label || res.hedef || "Türkiye") +
              " · " +
              mode +
              ".";
          } else if (String(action).indexOf("tour_") === 0) {
            reply = "Gezgin · " + String(action).replace(/^tour_/, "") + ".";
          }
          return shortSahneReply(res, reply);
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
        return shortSahneReply(res, (res.fiil || "goster") + " · " + organ + " açıldı.");
      }
      return res;
    } catch (_) {
      return null;
    }
  }

  function setSahneState(mode, sozText) {
    try {
      paintSadeDurum(mode); // sade yüz: sahne izni olmasa da durum görünür
    } catch (_) {}
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
    const haritaOn =
      document.body.classList.contains("mobil-sahne-organ-on") &&
      el("sahneOrgan") &&
      el("sahneOrgan").getAttribute("data-organ") === "harita";
    if (haritaOn) {
      paintMobilHaritaLiveLabels();
    } else if (soz && sozText != null) {
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
    // Sohbet açılınca sürekli sohbet varsayılan açık
    try {
      scheduleLiveAutoStart();
    } catch (_) {}
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
    try {
      sadeLogPush(role === "user" ? "user" : "bot", text);
    } catch (_) {}
  }

  /* ---- Madde 2.5 — Sade ses yüzü: balon yok · mikrofon + durum · isteğe bağlı sessiz kayıt ----
     Varsayılan KAPALI (mevcut yüz aynen). Aç/kapa: «Sade ses» düğmesi (localStorage ruzgar_pwa_sade_ses). */
  const SADE_KEY = "ruzgar_pwa_sade_ses";
  const SADE_LOG_KEY = "ruzgar_pwa_sade_log";
  const sadeLogRows = [];
  function sadeOn() {
    try {
      return localStorage.getItem(SADE_KEY) === "1";
    } catch (_) {
      return false;
    }
  }
  function sadeLogOn() {
    try {
      return localStorage.getItem(SADE_LOG_KEY) === "1";
    } catch (_) {
      return false;
    }
  }
  function paintSadeDurum(mode) {
    const box = el("sadeDurum");
    if (!box) return;
    const m = mode === "dinle" || mode === "konus" || mode === "dusun" ? mode : "hazir";
    box.setAttribute("data-durum", m);
    const mt = el("sadeDurumMetin");
    if (mt) {
      mt.textContent =
        m === "dinle" ? "Dinliyor" : m === "konus" ? "Konuşuyor" : m === "dusun" ? "Düşünüyor" : "Hazır";
    }
  }
  function paintSadeLog() {
    const box = el("sadeLog");
    if (!box) return;
    const show = sadeOn() && sadeLogOn();
    box.classList.toggle("hidden", !show);
    if (!show) return;
    box.textContent = "";
    sadeLogRows.forEach((r) => {
      const d = document.createElement("div");
      d.className = r.role === "user" ? "sl-u" : "sl-b";
      d.textContent = (r.role === "user" ? "Sen: " : "Rüzgar: ") + r.text;
      box.appendChild(d);
    });
    box.scrollTop = box.scrollHeight;
  }
  function sadeLogPush(role, text) {
    const t = String(text == null ? "" : text).trim();
    if (!t) return;
    sadeLogRows.push({ role, text: t.length > 600 ? t.slice(0, 600) + "…" : t });
    while (sadeLogRows.length > 24) sadeLogRows.shift();
    if (sadeOn() && sadeLogOn()) paintSadeLog();
  }
  function applySadeUi() {
    const on = sadeOn();
    const view = el("chatView");
    if (view) view.classList.toggle("sade-ses", on);
    const b = el("btnSade");
    if (b) {
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.textContent = on ? "Yazılı yüze dön" : "Sade ses";
    }
    const bl = el("btnSadeLog");
    if (bl) {
      bl.classList.toggle("hidden", !on);
      bl.setAttribute("aria-pressed", sadeLogOn() ? "true" : "false");
      bl.textContent = sadeLogOn() ? "Kaydı gizle" : "Kayıt";
    }
    const box = el("sadeDurum");
    if (box) box.classList.toggle("hidden", !on);
    paintSadeLog();
  }
  if (el("btnSade")) {
    el("btnSade").onclick = () => {
      try {
        localStorage.setItem(SADE_KEY, sadeOn() ? "0" : "1");
      } catch (_) {}
      applySadeUi();
    };
  }
  if (el("btnSadeLog")) {
    el("btnSadeLog").onclick = () => {
      try {
        localStorage.setItem(SADE_LOG_KEY, sadeLogOn() ? "0" : "1");
      } catch (_) {}
      applySadeUi();
    };
  }
  window.ruzgarSadeSes = {
    ac: () => {
      try {
        localStorage.setItem(SADE_KEY, "1");
      } catch (_) {}
      applySadeUi();
    },
    kapat: () => {
      try {
        localStorage.setItem(SADE_KEY, "0");
      } catch (_) {}
      applySadeUi();
    },
    acik: () => sadeOn(),
  };

  /* Yeni sohbet yüzü (ruzgar-yuz.js) için küçük kapı: cevabı oku / sustur.
     Mevcut mantığı değiştirmez; yalnız var olan işlevleri dışarı verir. */
  window.ruzgarMobil = {
    oku: (t) => speakReply(t),
    sustur: (r) => stopAllSpeech(r || "yuz-sustur"),
  };

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
    // Tam SW silme ekranı boşaltıyordu; yumuşak yenile + SW update (skipWaiting)
    try {
      const onPanel =
        el("panelView") && !el("panelView").classList.contains("hidden") &&
        el("chatWrap") && !el("chatWrap").classList.contains("hidden");
      sessionStorage.setItem("ruzgar_pwa_tab", onPanel ? "panel" : "chat");
      if ("serviceWorker" in navigator) {
        const regs = await navigator.serviceWorker.getRegistrations();
        for (const r of regs) {
          try {
            await r.update();
            if (r.waiting) {
              r.waiting.postMessage({ type: "SKIP_WAITING" });
            }
          } catch (_) {}
        }
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

  let _regPollTimer = null;
  let _regPollPass = "";
  function stopRegPoll() {
    if (_regPollTimer) {
      clearInterval(_regPollTimer);
      _regPollTimer = null;
    }
  }
  function paintRegWait(text, ok) {
    const w = el("regWait");
    if (!w) return;
    w.classList.remove("hidden");
    w.textContent = text || "";
    w.style.color = ok === false ? "#f87171" : "";
  }
  async function softLoginAfterApprove(kullanici, sifre) {
    if (el("user")) el("user").value = kullanici || "";
    if (el("pass") && sifre) el("pass").value = sifre;
    setTab("login");
    setMsg("Onaylandı — girişe geçiliyor…");
    paintRegWait("Onaylandı ✓ Giriş yapılıyor…", true);
    try {
      const kind = (el("deviceKind") && el("deviceKind").value) || "telefon";
      const dname = (el("device") && el("device").value.trim()) || kind;
      const j = await api("/api/mobil/login", {
        method: "POST",
        body: JSON.stringify({
          kullanici: kullanici,
          sifre: sifre,
          device_name: dname,
          device_id: deviceId(),
          device_kind: kind,
        }),
      });
      if (!j.ok) throw new Error(j.error || "giriş");
      localStorage.setItem(LS.token, j.token);
      localStorage.setItem(LS.who, JSON.stringify(j));
      setMsg("Onaylandı ve giriş tamam.");
      showChat(j);
    } catch (e) {
      setMsg("Onaylandı — şifrenizle Giriş’e basın. (" + String(e.message || e) + ")", true);
      paintRegWait("Onaylandı ✓ Giriş sekmesine geçin.", true);
    }
  }
  function startRegPoll(pendingId, kullanici, sifre) {
    stopRegPoll();
    _regPollPass = sifre || "";
    let ticks = 0;
    paintRegWait("Onay bekleniyor… Mimar panelden Onayla.", true);
    _regPollTimer = setInterval(async () => {
      ticks += 1;
      if (ticks > 180) {
        stopRegPoll();
        paintRegWait("Hâlâ bekleniyor — Mimar’a sorun veya sonra Giriş deneyin.", false);
        return;
      }
      try {
        const st = await api(
          `/api/mobil/register/status?pending_id=${encodeURIComponent(pendingId)}`,
        );
        if (!st || !st.ok) return;
        if (st.status === "approved" || st.login_ready) {
          stopRegPoll();
          void softLoginAfterApprove(st.kullanici || kullanici, _regPollPass);
          _regPollPass = "";
          return;
        }
        if (st.status === "rejected") {
          stopRegPoll();
          _regPollPass = "";
          paintRegWait("Kayıt reddedildi.", false);
          setMsg("Kayıt reddedildi.", false);
          return;
        }
        paintRegWait(`Onay bekleniyor… (${ticks * 2} sn)`, true);
      } catch (_) {}
    }, 2000);
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
      el("regCode").textContent = `Bekleyen kod: ${j.code}`;
      setMsg("Mimar panelinden onay bekleniyor — bu ekran otomatik yenilenir.");
      startRegPoll(j.pending_id, payload.kullanici, payload.sifre);
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

  function paintPanelInvite(suffix, erisim) {
    const box = el("panelInvite" + (suffix || ""));
    if (!box) return;
    const inv = (erisim && erisim.mimar_invite) || null;
    if (!inv) {
      box.classList.add("hidden");
      box.innerHTML = "";
      return;
    }
    box.classList.remove("hidden");
    const sticky = inv.sticky_url || (erisim && erisim.sticky_urls && erisim.sticky_urls[0]) || "";
    const adminUrl = inv.admin_users_url || "https://login.tailscale.com/admin/users";
    const steps = Array.isArray(inv.steps_tr) ? inv.steps_tr : [];
    box.innerHTML = `
      <strong>${esc(inv.title || "Tailscale davet")}</strong>
      <div class="invite-actions">
        <a class="primary tiny" href="${esc(adminUrl)}" target="_blank" rel="noopener">Davet / kullanıcı yönetimi</a>
        <button type="button" class="tiny" id="btnCopySticky${suffix || ""}">Sticky link kopyala</button>
        <button type="button" class="tiny" id="btnCopyAdmin${suffix || ""}">Admin URL kopyala</button>
      </div>
      <ol>${steps.map((t) => `<li>${esc(t)}</li>`).join("")}</ol>
      <p class="hint">Sertifika: ${esc((erisim && erisim.cert_kind) || "?")}${
        erisim && erisim.cert_warning ? " · self-signed ise arkadaş bir kez Devam basar" : " · LE — uyarı yok"
      }</p>`;
    const copySticky = el("btnCopySticky" + (suffix || ""));
    if (copySticky) {
      copySticky.onclick = async () => {
        try {
          await navigator.clipboard.writeText(sticky || "");
          setMsg("Sticky Rüzgar linki kopyalandı");
        } catch (_) {
          setMsg(sticky || "link yok", !!sticky);
        }
      };
    }
    const copyAdmin = el("btnCopyAdmin" + (suffix || ""));
    if (copyAdmin) {
      copyAdmin.onclick = async () => {
        try {
          await navigator.clipboard.writeText(adminUrl);
          setMsg("Tailscale admin URL kopyalandı");
        } catch (_) {
          setMsg(adminUrl, true);
        }
      };
    }
  }

  function paintFriendGuide(erisim) {
    const wrap = el("friendGuide");
    const list = el("friendGuideSteps");
    const certEl = el("friendGuideCert");
    if (!wrap || !list) return;
    const guide = erisim && erisim.friend_guide;
    const steps = guide && Array.isArray(guide.steps) ? guide.steps : [];
    if (!steps.length) {
      wrap.classList.add("hidden");
      return;
    }
    wrap.classList.remove("hidden");
    list.innerHTML = steps
      .map((s) => {
        const links = Array.isArray(s.links)
          ? s.links
              .map(
                (L) =>
                  `<a href="${esc(L.url)}" target="_blank" rel="noopener">${esc(L.label || L.url)}</a>`,
              )
              .join(" · ")
          : "";
        const urlBit = s.url
          ? ` <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a>`
          : "";
        return `<li><b>${esc(s.title || "")}</b> — ${esc(s.body || "")}${urlBit}${
          links ? `<br/>${links}` : ""
        }</li>`;
      })
      .join("");
    if (certEl) {
      if (erisim && erisim.cert_kind === "tailscale_le") {
        certEl.textContent = "Sertifika: Let’s Encrypt (Tailscale) — tarayıcı uyarısı beklenmez.";
      } else if (erisim && erisim.cert_warning) {
        certEl.textContent =
          "Sertifika self-signed: ilk açılışta Gelişmiş → Devam (tek ekran). Sonra Yenile yeterli.";
      } else {
        certEl.textContent = "";
      }
    }
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
      paintPanelInvite(s, st.erisim || null);
      paintFriendGuide(st.erisim || null);
      statusEl.innerHTML = [
        `v${esc(st.version)}`,
        `kullanıcı ${esc(st.users)}`,
        `oturum ${esc(st.sessions)}`,
        `bekleyen ${esc(st.pending)}`,
        `admin ${esc(st.admins)}`,
        st.enabled ? "açık" : "kapalı",
        st.erisim && st.erisim.cert_kind ? `cert ${esc(st.erisim.cert_kind)}` : "",
      ]
        .filter(Boolean)
        .join(" · ");

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
            const res = await api("/api/mobil/approve", {
              method: "POST",
              body: JSON.stringify({
                pending_id: p.pending_id,
                code: p.code,
                approve: true,
              }),
            });
            setMsg(
              res && res.login_ready
                ? `${p.kullanici} onaylandı — arkadaş otomatik girişe geçer`
                : `${p.kullanici} onaylandı`,
            );
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
     İlk dokunuşta HTMLAudio + AudioContext kilidini aç; TTS'i blob URL ile aynı player'da çal.
     Aşama B sabitleri = ilim_assistant.ses_v4_barge_in (PC↔mobil contract). */
  const RUZGAR_BARGE_IN = true;
  const RUZGAR_BARGE_SETTLE_MS = 40;
  /** Aşama C — text_ready→first_audio (A/B barge bozulmaz) */
  const RUZGAR_ASAMA_C_TTS_LAT = true;
  let _ttsTextReadyAt = 0;
  function markTtsTextReady(src) {
    _ttsTextReadyAt = performance.now();
    try {
      window.__ruzgarTtsTextReadyAt = _ttsTextReadyAt;
      window.__ruzgarTtsTextReadySrc = src || "";
    } catch (_) {}
  }
  function markTtsFirstAudio(src) {
    if (!_ttsTextReadyAt || !RUZGAR_ASAMA_C_TTS_LAT) return;
    const ms = Math.round(performance.now() - _ttsTextReadyAt);
    try {
      window.__ruzgarTtsTextToFirstAudioMs = ms;
      window.__ruzgarTtsLatLog = window.__ruzgarTtsLatLog || [];
      window.__ruzgarTtsLatLog.push({
        ms,
        src: src || "",
        under1s: ms < 1000,
        t: Date.now(),
      });
      if (window.__ruzgarTtsLatLog.length > 48) window.__ruzgarTtsLatLog.shift();
    } catch (_) {}
    _ttsTextReadyAt = 0;
  }
  const MOBIL_BARGE_RMS = 0.03;
  const MOBIL_BARGE_TICK_MS = 50;
  const MOBIL_BARGE_TICKS = 2;

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
    try {
      ttsPlayer.setAttribute("x-webkit-airplay", "allow");
    } catch (_) {}
    return ttsPlayer;
  }

  const SILENT_WAV =
    "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQAAAAA=";
  let ttsPlayGen = 0;

  /* ---- Madde 2 (Sprint E+F): ortak tur/ses mantığı — ruzgar-tur-ses.js ----
     SSE akışı + cümle çekici + TTS kuyruğu + tur kilidi (turn_id) + telemetri.
     Kapatma: localStorage ruzgar_pwa_tur_ses=0 → eski /api/chat/full yolu. */
  const TUR = typeof window !== "undefined" ? window.RuzgarTurSes || null : null;
  const turLock = TUR ? TUR.createTurnLock() : null;
  /** çalan sesin (playTtsBlob) hemen serbest bırakılması için */
  let _activePlayEnd = null;
  function turSesOn() {
    try {
      return !!TUR && !!turLock && localStorage.getItem("ruzgar_pwa_tur_ses") !== "0";
    } catch (_) {
      return !!TUR && !!turLock;
    }
  }
  function convId() {
    try {
      let c = sessionStorage.getItem("ruzgar_pwa_conv");
      if (!c) {
        c = "m" + Math.random().toString(36).slice(2, 10);
        sessionStorage.setItem("ruzgar_pwa_conv", c);
      }
      return c;
    } catch (_) {
      return "m-oturum";
    }
  }
  /** «ilk token» ve «duyulan ilk ses» ayrı telemetri (yalnız sayı; kişisel veri yok) */
  function postSesTelemetri(rec) {
    try {
      const r = rec || {};
      window.__ruzgarTurTelemetri = window.__ruzgarTurTelemetri || [];
      window.__ruzgarTurTelemetri.push({
        ilk_token_ms: r.ilk_token_ms,
        ilk_ses_ms: r.ilk_ses_ms,
        yol: r.ilk_ses_yolu,
        parca: r.parca,
        iptal: !!r.iptal,
      });
      if (window.__ruzgarTurTelemetri.length > 32) window.__ruzgarTurTelemetri.shift();
      void fetch(base() + "/api/ses/telemetri", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kanal: "mobil",
          turn_id: r.turn_id || null,
          ilk_token_ms: r.ilk_token_ms,
          ilk_ses_ms: r.ilk_ses_ms,
          ilk_ses_yolu: r.ilk_ses_yolu || null,
          parca: r.parca,
          iptal: !!r.iptal,
        }),
        keepalive: true,
      }).catch(() => {});
    } catch (_) {}
  }

  function isLikelyIos() {
    const ua = navigator.userAgent || "";
    if (/iPad|iPhone|iPod/i.test(ua)) return true;
    try {
      return navigator.platform === "MacIntel" && (navigator.maxTouchPoints || 0) > 1;
    } catch (_) {
      return false;
    }
  }

  function preferredRecorderMimes() {
    const base = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/aac",
      "audio/ogg",
    ];
    if (isLikelyIos()) {
      return ["audio/mp4", "audio/aac", "audio/wav", "audio/webm;codecs=opus", "audio/webm", "audio/ogg"];
    }
    return base;
  }

  function buildMicAudioConstraints() {
    // sampleRate zorlama yok — Android/iOS cihaz değişken; fallback getMicStream'te
    return {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    };
  }

  async function getMicStream() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("getUserMedia yok");
    }
    try {
      return await navigator.mediaDevices.getUserMedia({
        audio: buildMicAudioConstraints(),
      });
    } catch (e1) {
      // Android/eski WebView: kısıtlı constraint reddeder → sade audio:true
      try {
        return await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (e2) {
        throw e2 || e1;
      }
    }
  }

  async function probeMicPermission() {
    try {
      if (!navigator.permissions || !navigator.permissions.query) return null;
      const st = await navigator.permissions.query({ name: "microphone" });
      return st && st.state ? String(st.state) : null;
    } catch (_) {
      return null; // Safari çoğu sürümde Permissions API vermez
    }
  }

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

  /** Aşama A — Sus/Dur/Kes */
  function looksLikeVoiceStopCommand(text) {
    const t = String(text || "")
      .trim()
      .toLocaleLowerCase("tr-TR")
      .replace(/[!?.…,]+$/g, "")
      .trim();
    if (!t || t.length > 24) return false;
    return /^(sus|dur|kes|sessiz|sus\s*ol|kes\s*sesi|sus\s*lütfen|sus\s*lutfen)$/i.test(
      t,
    );
  }

  function notifyVoiceTurnListening(barge) {
    try {
      api("/api/ses/voice-turn", {
        method: "POST",
        body: JSON.stringify({
          state: "listening",
          barge_in: !!barge,
          note: barge ? "asama-a-barge" : "asama-a-listen",
        }),
      }).catch(() => ({}));
    } catch (_) {}
  }

  function notifyVoiceTurnIdle(note) {
    try {
      api("/api/ses/voice-turn", {
        method: "POST",
        body: JSON.stringify({
          state: "idle",
          note: String(note || "client-idle").slice(0, 80),
        }),
      }).catch(() => ({}));
    } catch (_) {}
  }

  let _voiceTurnQuietTimer = 0;
  function scheduleVoiceTurnIdleIfQuiet(ms, note) {
    const wait = Math.max(400, Number(ms) || 2200);
    if (_voiceTurnQuietTimer) {
      clearTimeout(_voiceTurnQuietTimer);
      _voiceTurnQuietTimer = 0;
    }
    _voiceTurnQuietTimer = window.setTimeout(() => {
      _voiceTurnQuietTimer = 0;
      try {
        if (liveMode || liveHoldRecord) return;
        try {
          const a = ensureTtsPlayer();
          if (a && !a.paused && !a.ended) return;
        } catch (_) {}
        notifyVoiceTurnIdle(note || "quiet-watchdog");
      } catch (_) {}
    }, wait);
  }

  // Aşama A — stopAllSpeech'ten önce declare (TDZ / ReferenceError yok)
  let liveHoldRecord = false;

  function stopAllSpeech(reason) {
    // F6.4 / Aşama A barge-in — YALNIZ TTS / yerel konuşma kesilir; sohbet abort yok
    const t0 = performance.now();
    ttsPlayGen += 1;
    /* Madde 2.4 — tur kilidi: aktif turun TTS kuyruğu (ve sunucudaki bekleyen parçaları) durur */
    let curTurnId = null;
    try {
      const curTurn = turLock && turLock.current();
      if (curTurn) {
        curTurnId = curTurn.id;
        curTurn.cancelTts(String(reason || "barge").slice(0, 40));
      }
    } catch (_) {}
    try {
      if (_activePlayEnd) _activePlayEnd(); // çalan parçanın söz'ü serbest kalsın (sızıntı yok)
    } catch (_) {}
    try {
      void fetch(base() + "/api/tts/cancel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          turn_id: curTurnId,
          device_id: deviceId(),
          sebep: String(reason || "barge").slice(0, 40),
        }),
      }).catch(() => {});
    } catch (_) {}
    try {
      const a = ensureTtsPlayer();
      a.pause();
      a.removeAttribute("src");
      a.load();
    } catch (_) {}
    try {
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    } catch (_) {}
    liveHoldRecord = false;
    // Canlı sohbet dışı: idle; canlıda kısa dinleme sonra quiet watchdog
    if (liveMode) {
      notifyVoiceTurnListening(true);
      scheduleVoiceTurnIdleIfQuiet(3500, "mobil-barge-quiet");
    } else {
      notifyVoiceTurnIdle(reason || "stop-speech");
    }
    const ms = Math.round(performance.now() - t0);
    try {
      window.__ruzgarLastBargeMs = ms;
    } catch (_) {}
    if (reason && meta) meta.textContent = String(reason) + ` (${ms} ms)`;
  }

  function playTtsBlob(blob, popts) {
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
      let bargeTimer = 0;
      try {
        audio.pause();
      } catch (_) {}
      let finished = false;
      const done = (note) => {
        if (bargeTimer) {
          clearInterval(bargeTimer);
          bargeTimer = 0;
        }
        if (finished) return resolve();
        finished = true;
        if (_activePlayEnd === endNow) _activePlayEnd = null;
        if (myGen !== ttsPlayGen) {
          try {
            URL.revokeObjectURL(url);
          } catch (_) {}
          return resolve();
        }
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
      const endNow = () => done();
      _activePlayEnd = endNow;
      audio.onended = () => done();
      audio.onerror = () => done("ses dosyası hatası");
      if (popts && typeof popts.onPlaying === "function") {
        // Madde 2.6 — «duyulan ilk ses» = tarayıcının gerçek 'playing' olayı (play() çağrısı değil)
        const onPlaying = () => {
          audio.removeEventListener("playing", onPlaying);
          if (myGen !== ttsPlayGen) return;
          try {
            popts.onPlaying();
          } catch (_) {}
        };
        audio.addEventListener("playing", onPlaying);
      }
      audio.src = url;
      try {
        audio.load();
      } catch (_) {}
      // Aşama A/B — TTS sırasında mic VAD açık; ticks×tick_ms ≈ kesilme (ses_v4)
      if (RUZGAR_BARGE_IN && liveMode && liveVad) {
        let speechTicks = 0;
        bargeTimer = setInterval(() => {
          if (myGen !== ttsPlayGen || !liveMode) {
            clearInterval(bargeTimer);
            bargeTimer = 0;
            return;
          }
          try {
            if (liveMuted) {
              speechTicks = 0;
              return;
            }
            if (liveVad.rms() >= MOBIL_BARGE_RMS) {
              speechTicks += 1;
              if (speechTicks >= MOBIL_BARGE_TICKS) {
                stopAllSpeech("sürekli: kesildi — dinliyorum");
                done("barge-in");
              }
            } else {
              speechTicks = 0;
            }
          } catch (_) {}
        }, MOBIL_BARGE_TICK_MS);
      }
      markTtsFirstAudio("playTtsBlob");
      const p = audio.play();
      if (p && typeof p.catch === "function") {
        p.catch((err) => {
          const name = String((err && err.name) || err || "");
          // Madde 2.4: kesilmiş (barge/yeni tur) parçanın play() reddi → sessizce bitir
          // (eski sürüm burada «Cevap hazır.» diye konuşup yeni cevaba biniyordu)
          if (myGen !== ttsPlayGen) {
            done();
            return;
          }
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
    return history.slice(-4).map((m) => ({
      role: m.role,
      content: String(m.content || "").slice(0, 280),
    }));
  }

  /** Desktop `_sahneNiyet` ile hizalı — sohbet cümlesinde süper-el çağırma */
  function looksLikeSahneCmd(t) {
    const s = String(t || "");
    return /\b(harita|sahne|gezgin|odaklan|odakla|yakla[sş]t[iı]r|uzakla[sş]t[iı]r|2d|3d|4d|uydu|cesium|kamera|iss|nasa|pinle|temizle|tur(u)?|duraklat|kuşbak|kusbak|üzerine|uzerine)\b|sahneye\s+(koy|yaz)|haritay[ıi]\s+(a[cç]|g[oö]ster)|(?:harita|sahne|gezgin).{0,24}g[oö]ster\b|g[oö]ster.{0,24}(?:harita|sahne)\b/i.test(
      s,
    );
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

  function splitTtsChunks(text, maxFirst) {
    // Aşama D — erken ilk parça + tüm metin cümle/noktalama sınırında; yarım kelime yok
    const t = String(text || "").replace(/\s+/g, " ").trim();
    if (!t) return [];
    const firstLim = maxFirst || (liveMode ? 110 : 150);
    const mergeLim = liveMode ? 280 : 380;
    const out = [];
    let rest = t;
    let first = true;
    while (rest) {
      const lim = first ? firstLim : mergeLim;
      if (rest.length <= lim) {
        out.push(rest);
        break;
      }
      if (first) {
        const m = rest.match(/^(.+?[.!?…])(\s+|$)/u);
        if (m && m[1].length >= 20 && m[1].length <= lim + 48) {
          out.push(m[1].trim());
          rest = rest.slice(m[0].length).trim();
          first = false;
          continue;
        }
      }
      const window = rest.slice(0, lim + 1);
      let cut = -1;
      let sepLen = 1;
      for (const sep of [". ", "! ", "? ", "… ", "; ", ": ", ", ", " — ", " - "]) {
        const i = window.lastIndexOf(sep);
        if (i >= 18 && i > cut) {
          cut = i;
          sepLen = sep.length;
        }
      }
      if (cut < 18) {
        const sp = window.lastIndexOf(" ");
        cut = sp > 18 ? sp : -1;
        sepLen = 1;
      }
      if (cut < 18) {
        out.push(rest);
        break;
      }
      const head = rest.slice(0, cut + (sepLen > 1 ? sepLen : 0)).trim();
      rest = rest.slice(cut + (sepLen > 1 ? sepLen : 1)).trim();
      if (head) out.push(head);
      first = false;
    }
    return out.filter((c) => c.length >= 2);
  }

  /** S1 tavan — masa normalizeKarakterForTts ile aynı alias */
  function normalizeKarakterForTts(k) {
    const s = String(k || "")
      .toLowerCase()
      .trim();
    if (s === "bilge" || s === "kari" || s === "âlim") return "alim";
    if (s === "sair") return "edip";
    if (s === "asistan" || s === "sohbet" || s === "gunluk" || s === "günlük")
      return "muhabbet";
    if (s === "kuran" || s === "tecvid") return "tilavet";
    if (s === "muhabbet" || s === "alim" || s === "tilavet" || s === "edip")
      return s;
    return "muhabbet";
  }

  async function fetchTtsBlob(say, ttsOpts) {
    const opts = ttsOpts && typeof ttsOpts === "object" ? ttsOpts : {};
    const token = localStorage.getItem(LS.token) || "";
    const headers = { "Content-Type": "application/json" };
    if (token) headers.Authorization = "Bearer " + token;
    let lastErr = "";
    const kar = normalizeKarakterForTts(
      opts.profil || opts.karakter || "muhabbet",
    );
    const hasEtiket =
      typeof say === "string" && /\[[^\]]{2,24}\]/.test(say);
    const be = String(opts.backend || "auto").trim().toLowerCase() || "auto";
    const softDeadlineMs =
      opts.softDeadlineMs != null
        ? Number(opts.softDeadlineMs)
        : be === "clone"
          ? 0
          : 8000;
    const buildPayload = (backendForce) => {
      const payload = {
        text: say,
        karakter: kar,
        profil: kar,
        backend: backendForce || be,
        prosody:
          opts.prosody != null ? !!opts.prosody : hasEtiket ? true : false,
      };
      const emo =
        (opts.emotion && String(opts.emotion)) ||
        (lastVoiceEmotion && String(lastVoiceEmotion)) ||
        "";
      if (emo && emo !== "notr") payload.emotion = emo;
      // Madde 2.4 — tur kimliği: sunucu iptal/eski turun parçasını sentezlemez (409)
      if (opts.turnId) {
        payload.turn_id = String(opts.turnId);
        payload.device_id = deviceId();
      }
      return payload;
    };
    const IPTAL_TTS = { iptal: true };
    const sigAborted = () => !!(opts.signal && opts.signal.aborted);
    const once = async (backendForce, deadlineMs) => {
      if (sigAborted()) return IPTAL_TTS;
      const payload = buildPayload(backendForce);
      const ctrl = new AbortController();
      let tid = 0;
      let unbindSig = null;
      if (opts.signal && typeof opts.signal.addEventListener === "function") {
        const onSigAbort = () => {
          try {
            ctrl.abort();
          } catch (_) {}
        };
        opts.signal.addEventListener("abort", onSigAbort, { once: true });
        unbindSig = () => {
          try {
            opts.signal.removeEventListener("abort", onSigAbort);
          } catch (_) {}
        };
      }
      if (deadlineMs > 0) {
        tid = window.setTimeout(() => {
          try {
            ctrl.abort();
          } catch (_) {}
        }, deadlineMs);
      }
      try {
        const res = await fetch(base() + "/api/tts", {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
          signal: ctrl.signal,
        });
        if (res.status === 409 && opts.turnId) {
          // Madde 2.4: sunucu «bu tur iptal/eski» dedi → çalma, yeniden deneme yok
          let jj = null;
          try {
            jj = await res.json();
          } catch (_) {}
          if (jj && jj.iptal) {
            lastErr = "tts_tur_iptal";
            return IPTAL_TTS;
          }
        }
        if (!res.ok) {
          lastErr = "tts_http_" + res.status;
          return null;
        }
        const blob = await res.blob();
        if (sigAborted()) return IPTAL_TTS;
        if (blob && blob.size > 32) return blob;
        lastErr = "tts_empty";
        return null;
      } catch (e) {
        if (sigAborted()) return IPTAL_TTS;
        if (e && e.name === "AbortError") {
          lastErr = "tts_deadline";
          throw e;
        }
        lastErr = String((e && e.message) || e || "tts_net").slice(0, 60);
        return null;
      } finally {
        if (tid) window.clearTimeout(tid);
        if (unbindSig) unbindSig();
      }
    };
    /* IPTAL_TTS → çağırana (kuyruk) iptal işareti; eski çağıranlar blob/null bekler */
    const retIptal = () => (opts.turnId && TUR ? TUR.IPTAL : null);
    try {
      const blob = await once(be, softDeadlineMs);
      if (blob === IPTAL_TTS) return retIptal();
      if (blob) return blob;
    } catch (e) {
      if (!(e && e.name === "AbortError")) {
        /* net */
      } else if (be !== "edge") {
        try {
          void fetch(base() + "/api/tts/cancel", { method: "POST" }).catch(
            () => {},
          );
        } catch (_) {}
        try {
          if (meta) meta.textContent = "Klon yavaş — Edge ile okuyorum…";
        } catch (_) {}
        try {
          const edgeBlob = await once("edge", 0);
          if (edgeBlob === IPTAL_TTS) return retIptal();
          if (edgeBlob) return edgeBlob;
        } catch (_) {}
      }
    }
    // Normal retry (deadline dışı)
    for (let attempt = 0; attempt < 2; attempt++) {
      if (sigAborted()) return retIptal();
      try {
        const blob = await once(be === "clone" ? "clone" : "edge", 0);
        if (blob === IPTAL_TTS) return retIptal();
        if (blob) return blob;
      } catch (_) {}
    }
    try {
      if (meta && lastErr) meta.textContent = "TTS: " + lastErr;
    } catch (_) {}
    return null;
  }

  /** S4 — raftan kısa pasaj (masa ile aynı /api/okuma/pasaj + /api/tts). */
  async function speakRaftanPasaj(query, opts) {
    const options = opts && typeof opts === "object" ? opts : {};
    const q = String(query || options.q || "").trim();
    const action = String(options.action || "oku").trim() || "oku";
    if (!q && !["devam", "tekrar", "yavas", "husulu"].includes(action)) {
      return { ok: false, error: "sorgu yok" };
    }
    const j = await api("/api/okuma/pasaj", {
      method: "POST",
      timeoutMs: 20000,
      body: JSON.stringify({ q, action, session_id: "mobil" }),
    });
    const pasaj = String((j && j.pasaj) || "").trim();
    if (!pasaj) return { ok: false, error: "pasaj boş" };
    const kar = String((j && j.karakter) || "alim");
    const title = j.baslik || j.eser_id || "Raftan";
    const reply = `📖 ${title}\n\n${pasaj}`;
    bubble("bot", reply);
    history.push({ role: "assistant", content: reply });
    setSahneState("konus", pasaj);
    await speakReplyWithKarakter(pasaj, kar);
    setSahneState("hazir", pasaj);
    return { ok: true, ...j };
  }

  async function speakReplyWithKarakter(reply, karakter) {
    const text = String(reply || "").trim();
    if (!text) return;
    unlockMobileAudio();
    const chunks = splitTtsChunks(text, liveMode ? 110 : 150);
    markTtsTextReady("speakRaftanPasaj");
    try {
      let prefetch = chunks[0]
        ? fetchTtsBlob(chunks[0], { karakter, prosody: true })
        : null;
      const genAtStart = ttsPlayGen;
      for (let i = 0; i < chunks.length; i++) {
        if (liveAbort || ttsPlayGen !== genAtStart) return;
        const blob = await prefetch;
        prefetch = null;
        if (i + 1 < chunks.length && !liveAbort && ttsPlayGen === genAtStart) {
          prefetch = fetchTtsBlob(chunks[i + 1], { karakter, prosody: true });
        }
        if (!blob) continue;
        if (liveAbort || ttsPlayGen !== genAtStart) return;
        await playTtsBlob(blob);
      }
    } catch (_) {
      await speakLocal(chunks[0] ? chunks[0].slice(0, 200) : text.slice(0, 200));
    }
  }

  function parseRaftanChatCmd(raw) {
    const t = String(raw || "").trim();
    if (!t) return null;
    const m = t.match(
      /^(?:raftan\s+(?:sesle\s+)?oku|kitaptan\s+(?:sesle\s+)?oku|kütüphaneden\s+(?:sesle\s+)?oku|kutuphaneden\s+(?:sesle\s+)?oku|sesle\s+oku\s+raftan|raf(?:tan)?\s+oku)\s*[:\-]?\s*(.+)$/i
    );
    if (m && String(m[1] || "").trim().length >= 2) {
      return { q: String(m[1]).trim(), action: "oku" };
    }
    const low = t.toLowerCase();
    if (/^(devam oku|okumaya devam|raftan devam|devam et oku)$/i.test(t)) {
      return { q: "", action: "devam" };
    }
    if (/^tekrar oku$/i.test(t)) return { q: "", action: "tekrar" };
    if (/^daha yava[sş] oku$/i.test(t)) return { q: "", action: "yavas" };
    if (/^daha hu[sşûu]+lu oku$/i.test(t) || low === "daha huşûlu oku") {
      return { q: "", action: "husulu" };
    }
    return null;
  }
  window.speakRaftanPasaj = speakRaftanPasaj;

  /**
   * V1.2 dublaj — masa ile aynı Form: mix_original / orig_duck_db / normalize.
   * Chat: «dublaj: yol/klip.mp4» veya «dublaj miks: yol/klip.mp4»
   */
  function parseDubChatCmd(raw) {
    const t = String(raw || "").trim();
    if (!t) return null;
    const m = t.match(
      /^dublaj(?:\s+(miks|mix))?\s*[:\-]?\s*(.+)$/i
    );
    if (!m) return null;
    const rel = String(m[2] || "").trim();
    if (rel.length < 3) return null;
    const mix = !!(m[1] && /miks|mix/i.test(m[1]));
    return {
      rel,
      mix_original: mix,
      orig_duck_db: "-16",
      normalize: true,
      voice: "auto",
      karakter: "asistan",
    };
  }

  async function runVideoDub(opts) {
    const o = opts && typeof opts === "object" ? opts : {};
    const rel = String(o.rel || "").trim();
    if (!rel) throw new Error("rel gerekli (göreli video yolu)");
    const token = localStorage.getItem(LS.token) || "";
    const fd = new FormData();
    fd.append("rel", rel);
    fd.append("src_lang", String(o.src_lang || "auto"));
    fd.append("tgt_lang", String(o.tgt_lang || "tr"));
    fd.append("voice", String(o.voice || "auto"));
    fd.append("karakter", String(o.karakter || "asistan"));
    fd.append("mix_original", o.mix_original ? "1" : "0");
    fd.append(
      "orig_duck_db",
      o.orig_duck_db != null && String(o.orig_duck_db).trim() !== ""
        ? String(o.orig_duck_db)
        : "-16"
    );
    fd.append("normalize", o.normalize === false ? "0" : "1");
    const headers = {};
    if (token) headers.Authorization = "Bearer " + token;
    const res = await fetch(base() + "/api/video/dub", {
      method: "POST",
      headers,
      body: fd,
    });
    const text = await res.text();
    let j = {};
    try {
      j = JSON.parse(text);
    } catch (_) {
      j = {};
    }
    if (!res.ok) {
      throw new Error(
        String(j.detail || j.error || text.slice(0, 160) || res.statusText)
      );
    }
    return j;
  }
  window.runVideoDub = runVideoDub;

  async function speakReply(reply) {
    const text = String(reply || "").trim();
    if (!text) return;
    unlockMobileAudio();
    const chunks = splitTtsChunks(text, liveMode ? 110 : 150);
    markTtsTextReady("speakReply");
    try {
      // Aşama D — uzun cevap: prefetch kuyruğu; barge gen değişince kes
      let prefetch = chunks[0] ? fetchTtsBlob(chunks[0]) : null;
      const genAtStart = ttsPlayGen;
      for (let i = 0; i < chunks.length; i++) {
        if (liveAbort || ttsPlayGen !== genAtStart) return;
        const blob = await prefetch;
        prefetch = null;
        if (i + 1 < chunks.length && !liveAbort && ttsPlayGen === genAtStart) {
          prefetch = fetchTtsBlob(chunks[i + 1]);
        }
        if (!blob) continue;
        if (liveAbort || ttsPlayGen !== genAtStart) return;
        await playTtsBlob(blob);
      }
      if (ttsPlayGen === genAtStart) return;
      return;
    } catch (_) {}
    await speakLocal(chunks[0].slice(0, 200));
  }

  /* ================= Madde 2.1/2.2/2.4 — akış + ortak TTS kuyruğu (mobil) =================
     Mantık `ruzgar-tur-ses.js`'te (masaüstü takeFirstTtsSentence/ttsSessionCounter ile hizalı).
     Burada yalnız DOM/ses bağları: balon, sahne durumu, playTtsBlob, fetchTtsBlob. */

  /** Tur için TTS kuyruğu kancaları: sentez (turn_id'li /api/tts) + çalma (tek paylaşılan Audio) */
  function ttsHooksFor(turn, ttsExtra) {
    return {
      ttsFetch: (text, o) =>
        fetchTtsBlob(text, Object.assign({}, ttsExtra || {}, { turnId: turn.id, signal: o && o.signal })),
      ttsPlay: (blob, text, idx, ctx) => {
        if (liveAbort) return Promise.resolve();
        return playTtsBlob(blob, {
          onPlaying: () => {
            try {
              ctx.markFirstAudio("blob");
            } catch (_) {}
          },
        });
      },
    };
  }

  /** Yedek yol (/api/chat/full) cevabı da aynı kuyruk + tur kilidiyle konuşulur */
  function speakWithTurn(reply, turn, onDone) {
    const text = String(reply || "").trim();
    if (!text || !TUR || !turn) return Promise.resolve();
    unlockMobileAudio();
    const hooks = ttsHooksFor(turn);
    const puller = TUR.createPuller();
    const q = TUR.createTtsQueue({
      turn,
      fetchChunk: hooks.ttsFetch,
      play: (blob, t, idx) => hooks.ttsPlay(blob, t, idx, { markFirstAudio: () => {} }),
    });
    markTtsTextReady("speakWithTurn");
    puller.push(text);
    puller.flush().forEach((c) => q.push(c));
    q.finish();
    return q.done.then(() => {
      if (typeof onDone === "function") onDone();
    });
  }

  /** (Yanıt yok) / boş cevap seslendirilmesin */
  function skipTtsChunk(chunk) {
    return /^\(?\s*yanıt yok\s*\)?\.?$/i.test(String(chunk || "").trim());
  }

  /**
   * SSE turu (metin akarken ses). Dönüş:
   *  { fallback:true, turn }  → akış açılamadı/boş: çağıran /api/chat/full yedeğine geçer
   *  { authError:true, message, code }
   *  { ok:true, reply, ttsDone, turn, stream, bubbleEl }
   */
  async function chatViaStream(t, o) {
    const opts = o || {};
    const token = localStorage.getItem(LS.token) || "";
    const turn = turLock.begin("yeni_tur");
    const t0 = opts.t0 != null ? opts.t0 : performance.now();
    let botEl = null;
    let raf = 0;
    let lastFull = "";
    const ensureBot = () => {
      if (botEl) return botEl;
      botEl = document.createElement("div");
      botEl.className = "bubble bot";
      chat.appendChild(botEl);
      return botEl;
    };
    const paint = () => {
      raf = 0;
      if (!botEl) return;
      botEl.textContent = lastFull;
      chat.scrollTop = chat.scrollHeight;
    };
    const hooks = ttsHooksFor(turn);
    const sess = TUR.createSession({
      turn,
      t0,
      url: base() + "/api/chat/stream",
      headers: token ? { Authorization: "Bearer " + token } : {},
      body: {
        message: t,
        history: opts.hist || [],
        mode: "genel",
        use_web: false,
        session_token: token,
        device_id: deviceId(),
        conversation_id: convId(),
        turn_id: turn.id,
      },
      ttsFetch: hooks.ttsFetch,
      ttsPlay: hooks.ttsPlay,
      skipChunk: skipTtsChunk,
      postTelemetry: postSesTelemetri,
      onToken: (txt, full) => {
        lastFull = full;
        if (!raf) raf = window.requestAnimationFrame(paint);
        ensureBot();
        if (opts.onToken) opts.onToken(txt, full);
      },
      onStatus: (ev) => {
        const s = String((ev && ev.text) || "").trim();
        if (s && !lastFull && meta) meta.textContent = s.slice(0, 120);
      },
      onFirstChunk: () => {
        markTtsTextReady("stream-ilk-parca");
        if (opts.onFirstChunk) opts.onFirstChunk();
      },
      onFirstAudio: (ms) => {
        if (opts.onFirstAudio) opts.onFirstAudio(ms);
      },
    });
    let r;
    try {
      r = await sess.run();
    } finally {
      if (raf) {
        window.cancelAnimationFrame(raf);
        raf = 0;
      }
    }
    const stream = r.stream || {};
    if (turn.streamAborted || stream.aborted) {
      // Yeni tur bu turun yerini aldı: kalan işi yeni tur yürütür; eski sesi/akışı hiçbir şey sürdürmez
      if (botEl && botEl.parentNode && !lastFull) botEl.parentNode.removeChild(botEl);
      else if (botEl) botEl.textContent = lastFull + " …";
      return { superseded: true, turn, partial: lastFull };
    }
    if (stream.authError) {
      if (botEl && botEl.parentNode) botEl.parentNode.removeChild(botEl);
      return {
        authError: true,
        message: String(stream.error || "Oturum geçersiz veya süresi dolmuş. PWA'dan tekrar giriş."),
        code: String(stream.code || ""),
        turn,
      };
    }
    if (stream.fallback || (!r.finalText && !stream.done)) {
      if (botEl && botEl.parentNode) botEl.parentNode.removeChild(botEl);
      return { fallback: true, turn, why: stream.networkError || "bos" };
    }
    const reply = String(r.finalText || "").trim();
    if (botEl) {
      if (reply) botEl.textContent = reply;
      else if (botEl.parentNode) botEl.parentNode.removeChild(botEl);
    } else if (reply && !skipTtsChunk(reply)) {
      botEl = ensureBot();
      botEl.textContent = reply;
    }
    chat.scrollTop = chat.scrollHeight;
    if (reply && !skipTtsChunk(reply)) sadeLogPush("bot", reply);
    return {
      ok: true,
      reply,
      ttsDone: r.ttsDone,
      turn,
      stream,
      broke: !!stream.broke,
      bubbleEl: botEl,
      session: sess,
    };
  }

  /**
   * Tek giriş: önce SSE akışı (token + ses aynı anda), olmazsa verilen yedek (fallbackFn).
   * Dönüş: {superseded} | {authError,message,code} | {kind:"stream",ok,reply,ttsDone,turn,bubbleShown,...}
   *        | {kind:"full", turn, fb}  (fb = fallbackFn sonucu; çağıran biçimler)
   */
  async function runChatTurn(t, o) {
    const opts = o || {};
    const t0 = opts.t0 != null ? opts.t0 : performance.now();
    let turn = null;
    if (turSesOn()) {
      let seen = "";
      let audioStarted = false;
      let sahneRaf = 0;
      const paintSahne = () => {
        sahneRaf = 0;
        setSahneState(audioStarted ? "konus" : "dusun", seen);
      };
      const sv = await chatViaStream(t, {
        hist: opts.hist,
        t0,
        onFirstChunk: opts.onFirstChunk,
        onToken: (txt, full) => {
          if (!seen && meta) meta.textContent = "yazıyor…";
          seen = full;
          if (!sahneRaf) sahneRaf = window.requestAnimationFrame(paintSahne);
        },
        onFirstAudio: (ms) => {
          audioStarted = true;
          setSahneState("konus", seen);
          if (meta) meta.textContent = `ilk ses ${ms} ms · konuşuyor…`;
        },
      });
      if (sahneRaf) {
        window.cancelAnimationFrame(sahneRaf);
        sahneRaf = 0;
      }
      if (sv.superseded) return { superseded: true };
      if (sv.authError) return { authError: true, message: sv.message, code: sv.code };
      if (sv.ok) {
        return {
          kind: "stream",
          ok: true,
          reply: sv.reply,
          ttsDone: sv.ttsDone,
          turn: sv.turn,
          bubbleShown: !!sv.bubbleEl,
          bubbleEl: sv.bubbleEl,
          stream: sv.stream,
          session: sv.session,
          broke: sv.broke,
          wallMs: Math.round(performance.now() - t0),
        };
      }
      turn = sv.turn || null; // akış açılamadı → yedek yol (aynı tur kimliğiyle)
    }
    const fb = await opts.fallbackFn(turn);
    return { kind: "full", turn, fb, wallMs: Math.round(performance.now() - t0) };
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
    // Aşama A: kısa uyarıda da barge duyulsun; sonra yankı penceresi
    if (liveMode) setLiveTtsListenMode(true);
    await speakLocal(msg);
    if (liveMode) setLiveTtsListenMode(false);
    if (liveMode && !liveAbort) await liveQuietGap(450);
  }

  let mobilChatInFlight = false;
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
    // Masa parity: önceki TTS'i kes (VRAM sıkışıklığı yok) — sohbet abort yok
    stopAllSpeech(opts.live ? "live-yeni-tur" : "yazı-yeni-tur");
    // Klavye/metin turu: eski mic duygusu sızmasın (canlı ses opts.live tutar)
    if (!opts.live) lastVoiceEmotion = null;
    if (mobilChatInFlight && !opts.live) {
      if (meta) meta.textContent = "Önceki yanıt bitene kadar bekleyin…";
      return;
    }
    const t0 = performance.now();
    bubble("user", t);
    history.push({ role: "user", content: t });
    meta.textContent = "düşünüyor…";
    setSahneState("dusun", t);
    if (!opts.live) mobilChatInFlight = true;
    try {
      /* Sohbet ≠ sahne: yalnız niyet varsa süper-el (desktop parity) */
      if (looksLikeSahneCmd(t)) {
        const se = await runSuperEl(t);
        if (se && se._mobilShort) {
          meta.textContent = "sahne";
          setSahneState("hazir");
          return;
        }
      }
      if (!opts.live || turSesOn()) {
        api("/api/ses/voice-turn", {
          method: "POST",
          body: JSON.stringify({ state: "thinking" }),
        }).catch(() => ({}));
      }
      const token = localStorage.getItem(LS.token) || "";
      /* F6.6 — with_tts politikası: sohbet turunda metin önce (false);
         ses ayrı /api/tts veya speakLocal. Tek canlı yol: ikisi de aynı reply. */
      const WITH_TTS_IN_CHAT = false;
      const turnTimeoutMs = opts.live
        ? /nedir|kimdir|anlat|hakkında|hakkinda|hadis|ayet|tarih|ilim/i.test(t)
          ? 55000
          : 38000
        : /nedir|kimdir|anlat|hakkında|hakkinda/i.test(t)
          ? 90000
          : 45000;
      const histForTurn = opts.live ? trimHistoryForVoice() : history.slice(-8);
      /* Madde 2.1 — önce SSE akışı (metin akarken ses); olmazsa eski /api/ses/sohbet-tur yedeği */
      const res = await runChatTurn(t, {
        hist: histForTurn,
        t0,
        onFirstChunk: () => {
          // Aşama A: TTS sırasında mic açık (barge VAD); kayıt tutulur (yankı→STT yok)
          if (liveMode) setLiveTtsListenMode(true);
        },
        fallbackFn: () =>
          api("/api/ses/sohbet-tur", {
            method: "POST",
            body: JSON.stringify({
              message: t,
              history: histForTurn,
              session_token: token,
              with_tts: WITH_TTS_IN_CHAT,
            }),
            /* F1.2 / F6.5 — canlı 22sn ilim turunu kesiyordu; ilim bütçesiyle hizalı */
            timeoutMs: turnTimeoutMs,
          }),
      });
      if (res.superseded) return;
      if (res.authError) {
        setSahneState("hazir");
        bubble("bot", `[Hata] ${res.message}`);
        meta.textContent = String(res.message || "oturum").slice(0, 80);
        history.pop();
        if (/oturum|süresi dol/i.test(String(res.message || "")) || /oturum/i.test(String(res.code || ""))) {
          localStorage.removeItem(LS.token);
          setMsg("Oturum düştü — tekrar giriş yap.", false);
        }
        notifyVoiceTurnIdle("mobil-auth-err");
        return;
      }
      const streamed = res.kind === "stream";
      const j = streamed ? null : res.fb;
      let reply = streamed ? String(res.reply || "").trim() : (j.full_reply || "").trim();
      if (!reply || reply === "(Yanıt yok)") {
        if (streamed) {
          try {
            res.turn.cancelTts("bos-cevap");
          } catch (_) {}
          if (res.bubbleEl && res.bubbleEl.parentNode) res.bubbleEl.parentNode.removeChild(res.bubbleEl);
          if (liveMode) setLiveTtsListenMode(false);
        }
        setSahneState("hazir");
        // F6.5 — F0 miss dili (öğret / boş)
        meta.textContent = "cevap yok (miss) — tekrar dene";
        await askRepeat("empty");
        history.pop();
        return;
      }
      if (!res.bubbleShown && !(streamed && res.bubbleShown)) bubble("bot", reply);
      history.push({ role: "assistant", content: reply });
      if (history.length > 24) history = history.slice(-16);
      // Metin bitti — sohbet kilidi kalksın; ses arka planda (masa parity)
      if (!opts.live) mobilChatInFlight = false;
      if (streamed) {
        const ft = res.stream && res.stream.firstTokenMs;
        meta.textContent = `cevap hazır${ft != null ? " · ilk token " + ft + " ms" : ""} · ses sürüyor…`;
        notifyVoiceTurnIdle("mobil-stream-metin"); // sohbet-tur ile aynı: metin bitince idle
        const afterTts = () => {
          if (liveMode) setLiveTtsListenMode(false);
          const wall = Math.round(performance.now() - t0);
          const fa = res.session && res.session.state ? res.session.state.firstAudioMs : null;
          const bits = [`${wall} ms`];
          if (ft != null) bits.push(`ilk token ${ft} ms`);
          bits.push(fa != null ? `ilk ses ${fa} ms` : "ses");
          meta.textContent = bits.join(" · ");
          setSahneState("hazir", reply);
          if (!liveMode) scheduleVoiceTurnIdleIfQuiet(400, "mobil-chat-done");
        };
        if (opts.live) {
          try {
            await res.ttsDone;
          } finally {
            afterTts();
          }
        } else {
          void res.ttsDone.then(afterTts, afterTts);
        }
        return;
      }
      meta.textContent = "cevap hazır · ses… (sohbet serbest)";
      setSahneState("konus", reply);
      const playVoice = async () => {
        // Aşama A: TTS sırasında mic açık (barge VAD); kayıt tutulur (yankı→STT yok)
        if (liveMode) setLiveTtsListenMode(true);
        try {
          await speakReply(reply);
        } catch (_) {
          try {
            await speakLocal(reply.slice(0, 160));
          } catch (__) {}
        }
        if (liveMode) setLiveTtsListenMode(false);
      };
      if (opts.live) {
        await playVoice();
      } else {
        void playVoice();
      }
      const wall = Math.round(performance.now() - t0);
      const bits = [`${wall} ms`];
      if (j.latency_ms != null) bits.push(`sunucu ${j.latency_ms} ms`);
      bits.push("metin önce");
      meta.textContent = bits.join(" · ");
      setSahneState("hazir", reply);
      if (!liveMode) scheduleVoiceTurnIdleIfQuiet(400, "mobil-chat-done");
    } catch (e) {
      const raw = String(e.message || e || "");
      // F6.5 — F0/F1 sınıflarıyla aynı dil
      let cls = "hata";
      if (/abort|timeout|süre|sure|timed?\s*out/i.test(raw)) cls = "timeout";
      else if (/öğretir|ogretir|bulamadım|bulamadim|miss/i.test(raw)) cls = "miss";
      else if (/stt|whisper|ses → metin/i.test(raw)) cls = "stt";
      const shown =
        cls === "timeout"
          ? "Ümit abi, süre yetmedi — biraz sonra tekrar dene."
          : cls === "miss"
            ? "Ümit abi, bu turda net cevap çıkmadı. Bana öğretir misin?"
            : `[Hata · ${cls}] ${raw}`;
      bubble("bot", shown);
      meta.textContent = cls === "timeout" ? "timeout (F1)" : cls === "miss" ? "miss (F0)" : raw;
      setSahneState("hazir");
      notifyVoiceTurnIdle("mobil-chat-err");
      if (opts.live) {
        history.pop();
        await askRepeat("error");
      }
    } finally {
      if (!opts.live) mobilChatInFlight = false;
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
    // Masa parity: önceki TTS kes — yeni sohbet sıkışmasın
    stopAllSpeech("btnSend-yeni-tur");
    el("input").value = "";
    bubble("user", t);
    history.push({ role: "user", content: t });
    meta.textContent = "düşünüyor…";
    setSahneState("dusun", t);
    try {
      const rafCmd = parseRaftanChatCmd(t);
      if (rafCmd) {
        meta.textContent = "raftan okuma…";
        try {
          const r = await speakRaftanPasaj(rafCmd.q, { action: rafCmd.action });
          meta.textContent = r && r.ok ? "raftan · ses" : "raftan hata";
          setSahneState("hazir");
          return;
        } catch (re) {
          bubble("bot", `[Raftan] ${re.message || re}`);
          meta.textContent = "raftan hata";
          setSahneState("hazir");
          return;
        }
      }
      const dubCmd = parseDubChatCmd(t);
      if (dubCmd) {
        meta.textContent = "dublaj V1.2…";
        try {
          const j = await runVideoDub(dubCmd);
          const qm = j.quality_mux || {};
          const line = [
            j.ok ? "Dublaj hazır" : "Dublaj",
            j.output_rel || j.audio_rel || "",
            j.srt_rel ? `SRT ${j.srt_rel}` : "",
            j.tavan ? `tavan ${j.tavan}` : "",
            j.voice_mode ? `ses ${j.voice_mode}` : "",
            dubCmd.mix_original ? "miks -16dB" : "",
            qm.normalized ? "loudnorm✓" : "",
            qm.mixed ? "mix✓" : "",
          ]
            .filter(Boolean)
            .join(" · ");
          bubble("bot", line);
          history.push({ role: "assistant", content: line });
          meta.textContent = j.ok ? "dublaj · ok" : "dublaj hata";
          setSahneState("hazir");
          return;
        } catch (de) {
          bubble("bot", `[Dublaj] ${de.message || de}`);
          meta.textContent = "dublaj hata";
          setSahneState("hazir");
          return;
        }
      }
      if (looksLikeSahneCmd(t)) {
        const se = await runSuperEl(t);
        if (se && se._mobilShort) {
          meta.textContent = "sahne";
          setSahneState("hazir");
          return;
        }
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
      /* Madde 2.1 — önce SSE akışı (metin akarken ses, PC ile aynı mantık);
         akış açılamazsa /api/chat/full yedeği (eski davranış) */
      const tSend = performance.now();
      const res = await runChatTurn(t, {
        hist,
        t0: tSend,
        fallbackFn: (turnFb) =>
          api("/api/chat/full", {
            method: "POST",
            /* F1.2 — bilgi turları 90sn sınırında kesilmesin */
            timeoutMs: /nedir|kimdir|anlat|hakkında|hakkinda|hadis|ayet|tarih|ilim|açıkla|acikla/i.test(
              t
            )
              ? 120000
              : 90000,
            body: JSON.stringify({
              message: t,
              history: hist,
              mode: "genel",
              use_web: false,
              session_token: token,
              device_id: deviceId(),
              conversation_id: convId(),
              turn_id: turnFb ? turnFb.id : undefined,
            }),
          }),
      });
      if (res.superseded) return;
      if (res.authError) {
        const err = String(res.message || "Oturum geçersiz").trim();
        bubble("bot", `[Hata] ${err}`);
        meta.textContent = err.slice(0, 80);
        setSahneState("hazir");
        if (/oturum|süresi dol/i.test(err) || /oturum/i.test(String(res.code || ""))) {
          localStorage.removeItem(LS.token);
          setMsg("Oturum düştü — tekrar giriş yap.", false);
        }
        return;
      }
      if (res.kind === "stream") {
        const reply = String(res.reply || "").trim();
        if (!reply) {
          try {
            res.turn.cancelTts("bos-cevap");
          } catch (_) {}
          bubble("bot", "[Hata] Sunucu boş döndü — Yenile deyip bir kez daha dene.");
          meta.textContent = "boş yanıt";
          setSahneState("hazir");
          return;
        }
        history.push({ role: "assistant", content: reply });
        const st = res.stream || {};
        const bits = [];
        if (st.firstTokenMs != null) bits.push(`ilk token ${st.firstTokenMs} ms`);
        if (res.wallMs != null) bits.push(`${res.wallMs} ms`);
        if (res.broke) bits.push("bağlantı koptu (kısmi)");
        meta.textContent =
          (bits.length ? bits.join(" · ") + " · " : "") + "ses… (sohbet serbest)";
        // Ses akış sırasında başladı; bitince durum güncellenir (Gönder kilitlenmez)
        const afterTts = () => {
          const fa = res.session && res.session.state ? res.session.state.firstAudioMs : null;
          if (fa != null) bits.push(`ilk ses ${fa} ms`);
          meta.textContent = bits.length ? bits.join(" · ") + " · ses" : "ses";
          setSahneState("hazir", reply);
        };
        void res.ttsDone.then(afterTts, afterTts);
        return;
      }
      const j = res.fb;
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
      meta.textContent =
        (bits.length ? bits.join(" · ") + " · " : "") + "ses… (sohbet serbest)";
      setSahneState("konus", reply);
      // Ses arka planda — Gönder kilitlenmesin (masa parity). Yedek yol da tur kilidine katılır.
      const afterSpeak = () => {
        meta.textContent = bits.length ? bits.join(" · ") + " · ses" : "ses";
        setSahneState("hazir", reply);
      };
      if (res.turn && turSesOn()) {
        void speakWithTurn(reply, res.turn).then(afterSpeak, afterSpeak);
      } else {
        void speakReply(reply).then(afterSpeak);
      }
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

  async function sttBlob(blob, opts) {
    const fast = !!(opts && opts.fast);
    const token = localStorage.getItem(LS.token) || "";
    let upload = blob;
    let name = "mobil.webm";
    // Canlı sohbet: telefonda OfflineAudio WAV dönüşümü çok yavaş — ham webm/mp4 gönder
    if (!fast) {
      try {
        const wav = await blobToWav16k(blob);
        if (wav && wav.size > 100) {
          upload = wav;
          name = "mobil.wav";
        }
      } catch (_) {
        const ext = (mediaMime || "").includes("mp4") ? "m4a" : "webm";
        name = `mobil.${ext}`;
      }
    } else {
      const t = String((blob && blob.type) || mediaMime || "");
      if (t.includes("mp4") || t.includes("m4a") || t.includes("aac")) name = "mobil.m4a";
      else if (t.includes("ogg")) name = "mobil.ogg";
      else if (t.includes("wav")) name = "mobil.wav";
      else name = "mobil.webm";
    }
    const fd = new FormData();
    fd.append("file", upload, name);
    try {
      if (liveVad && typeof liveVad.rms === "function") {
        const r = Number(liveVad.rms());
        if (Number.isFinite(r)) lastMicEnergy01 = Math.min(1, Math.max(0, r));
      }
      fd.append("mic_energy", String(lastMicEnergy01));
    } catch (_) {
      fd.append("mic_energy", String(lastMicEnergy01));
    }
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), fast ? 35000 : 90000);
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
      const out = String(j.text || j.transcript || "").trim();
      const emo = typeof j.emotion === "string" ? j.emotion : "notr";
      lastVoiceEmotion = emo && emo !== "notr" ? emo : null;
      return out;
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
      const text = await sttBlob(blob, { fast: true });
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
    const perm = await probeMicPermission();
    if (perm === "denied") {
      meta.textContent =
        "Mikrofon engelli — tarayıcı site ayarından izin ver" +
        (isLikelyIos() ? " (iOS: Ayarlar → Safari/Rüzgar → Mikrofon)." : ".");
      return;
    }
    // PC parity: mic basınca TTS kes + kısa settle (ses_v4)
    if (RUZGAR_BARGE_IN) {
      stopAllSpeech("basılı tut — dinliyorum");
      try {
        await sleep(RUZGAR_BARGE_SETTLE_MS);
      } catch (_) {}
    }
    micBusy = true;
    mediaChunks = [];
    if (el("btnMic")) el("btnMic").classList.add("listening");
    meta.textContent = "dinleniyor… basılı tut, bırakınca gönderilir";
    setSahneState("dinle");
    void requestWakeLock();
    notifyVoiceTurnListening(true);
    try {
      mediaStream = await getMicStream();
      const types = preferredRecorderMimes();
      mediaMime = types.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
      mediaRecorder = mediaMime
        ? new MediaRecorder(mediaStream, { mimeType: mediaMime })
        : new MediaRecorder(mediaStream);
      if (!mediaMime && mediaRecorder.mimeType) mediaMime = mediaRecorder.mimeType;
      mediaRecorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size) mediaChunks.push(ev.data);
      };
      // timeslice yok — tek parça (mobilde daha sağlam); bırakınca stop
      mediaRecorder.start();
    } catch (e) {
      micBusy = false;
      stopMediaTracks();
      if (el("btnMic")) el("btnMic").classList.remove("listening");
      const name = String((e && e.name) || "");
      const msg = String(e && e.message ? e.message : e);
      if (/NotAllowed|Permission|Denied|NotAllowedError/i.test(name + " " + msg)) {
        meta.textContent =
          "Mikrofon izni reddedildi — site ayarından izin ver" +
          (isLikelyIos() ? " (iOS: Ayarlar → Safari → Mikrofon)." : ".");
      } else if (/secure|Only secure|getUserMedia/i.test(msg) || !micSecureOk()) {
        paintMicBlocked();
      } else if (/NotFound|DevicesNotFound|NotReadable/i.test(name + " " + msg)) {
        meta.textContent = "Mikrofon bulunamadı / meşgul — başka uygulama kullanıyor olabilir.";
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
  let liveStartPending = false;

  function livePrefOn() {
    const v = localStorage.getItem(LS.livePref);
    // Yoksa veya 1 → açık (kullanıcı Durdur demedikçe)
    return v !== "0";
  }

  function setLivePref(on) {
    try {
      localStorage.setItem(LS.livePref, on ? "1" : "0");
    } catch (_) {}
  }

  function beginLiveSession() {
    unlockMobileAudio();
    if (liveMode) return;
    if (micBusy && !liveMode) {
      if (meta) meta.textContent = "Önce basılı tutmayı bırak / bekleyin.";
      return;
    }
    if (!micSecureOk()) {
      paintMicBlocked();
      if (meta) meta.textContent = "sürekli sohbet: HTTPS + mikrofon gerekli";
      return;
    }
    if (RUZGAR_BARGE_IN) stopAllSpeech("sürekli sohbet — dinliyorum");
    liveAbort = false;
    liveMode = true;
    liveStartPending = false;
    setLivePref(true);
    void liveLoop();
  }

  function scheduleLiveAutoStart() {
    if (!livePrefOn()) return;
    if (liveMode) return;
    liveStartPending = true;
    if (meta) meta.textContent = "sürekli sohbet açılıyor…";
    paintLiveBtn();
    // Jest gerekebilir — hemen dene; olmazsa ilk dokunuşta aç
    setTimeout(function () {
      if (!liveStartPending || liveMode || !livePrefOn()) return;
      beginLiveSession();
    }, 350);
  }
  let liveStream = null;
  let liveVad = null;
  let liveAbort = false;
  let liveMuted = false; // kısa sessizlik / yankı penceresi (track kapalı)
  let liveRestartN = 0;
  let wakeLock = null;

  function setLiveMicEnabled(on) {
    liveMuted = !on;
    try {
      if (!liveStream) return;
      liveStream.getAudioTracks().forEach(function (t) {
        try {
          t.enabled = !!on;
        } catch (_) {}
      });
    } catch (_) {}
  }

  /** Aşama A — TTS sırasında mic açık (barge), kayıt kapalı (yankıyı STT'ye alma) */
  function setLiveTtsListenMode(on) {
    liveHoldRecord = !!on;
    if (on) {
      setLiveMicEnabled(true);
    }
  }

  async function liveQuietGap(ms) {
    setLiveTtsListenMode(false);
    setLiveMicEnabled(false);
    await sleep(Math.max(200, ms || 900));
    if (liveMode && !liveAbort) setLiveMicEnabled(true);
  }

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
    } else if (livePrefOn() && localStorage.getItem(LS.token)) {
      scheduleLiveAutoStart();
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
    if (liveMuted || liveHoldRecord) {
      await sleep(200);
      return null;
    }
    if (!liveVad) liveVad = attachVad(stream);
    const SPEECH = 0.022;
    const SILENCE_MS = 520;
    const WAIT_SPEECH_MS = 25000;
    const MAX_REC_MS = 16000;
    const MIN_SPEECH_MS = 320;
    const tick = 50;
    meta.textContent = "sürekli: dinliyorum — konuşun";

    // 1) Önce konuşma gelsin (boşluğu kaydetme → STT daha hızlı/temiz)
    let waited = 0;
    while (!liveAbort && liveMode && waited < WAIT_SPEECH_MS) {
      await sleep(tick);
      waited += tick;
      if (liveMuted || liveHoldRecord) continue;
      if ((liveVad ? liveVad.rms() : 0) >= SPEECH) break;
    }
    if (liveAbort || !liveMode || liveMuted || liveHoldRecord) return null;
    if ((liveVad ? liveVad.rms() : 0) < SPEECH && waited >= WAIT_SPEECH_MS) return null;

    // 2) Kaydı konuşma başında aç
    const chunks = [];
    const types = preferredRecorderMimes();
    const mime = types.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
    let rec;
    try {
      rec = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
    } catch (e) {
      meta.textContent = "sürekli: kayıt açılamadı — yeniden…";
      await sleep(400);
      return null;
    }
    const useMime = mime || rec.mimeType || "audio/webm";
    rec.ondataavailable = (ev) => {
      if (ev.data && ev.data.size) chunks.push(ev.data);
    };
    try {
      rec.start(150);
    } catch (e) {
      meta.textContent = "sürekli: kayıt start hatası — yeniden…";
      await sleep(400);
      return null;
    }

    let speechMs = 0;
    let silenceMs = 0;
    let recMs = 0;
      meta.textContent = "sürekli: duyuyorum…";
    while (!liveAbort && liveMode && recMs < MAX_REC_MS) {
      await sleep(tick);
      recMs += tick;
      if (liveMuted || liveHoldRecord) break;
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
    if (liveMuted || speechMs < MIN_SPEECH_MS) return null;
    const blob = new Blob(chunks, { type: useMime });
    if (blob.size < 900) return null;
    return blob;
  }

  async function liveLoop() {
    micBusy = true;
    paintLiveBtn();
    let fatal = false;
    try {
      if (!micSecureOk()) {
        paintMicBlocked();
        liveMode = false;
        paintLiveBtn();
        return;
      }
      const woke = await requestWakeLock();
      // F7.5 — STT ısınma (soğuk ilk turu kes); beklemeden fire-and-forget
      try {
        const token = localStorage.getItem(LS.token) || "";
        const headers = {};
        if (token) headers.Authorization = "Bearer " + token;
        fetch(base() + "/api/stt/warmup", { method: "POST", headers }).catch(() => {});
      } catch (_) {}
      liveStream = await getMicStream();
      liveVad = attachVad(liveStream);
      liveMuted = false;
      liveHoldRecord = false;
      liveRestartN = 0;
      meta.textContent = woke
        ? "sürekli: dinliyorum — konuşun"
        : "sürekli: dinliyorum (ekranı açık tut) — konuşun";

      while (liveMode && !liveAbort) {
        let blob = null;
        try {
          blob = await recordUntilSilence(liveStream);
        } catch (e) {
          meta.textContent = "sürekli kayıt: " + String(e.message || e);
          await liveQuietGap(600);
          continue;
        }
        if (!liveMode || liveAbort) break;
        if (!blob) {
          meta.textContent = "sürekli: dinliyorum — konuşun";
          continue;
        }
        // STT / cevap sırasında mic kapalı — yankı ve kendini duyma yok
        setLiveMicEnabled(false);
        meta.textContent = "sürekli: ses → metin…";
        let text = "";
        try {
          mediaMime = blob.type || "audio/webm";
          text = await sttBlob(blob, { fast: true });
        } catch (e) {
          meta.textContent = "sürekli STT: " + String(e.message || e);
          await liveQuietGap(400);
          continue;
        }
        if (!text) {
          await askRepeat("short");
          if (!liveMode || liveAbort) break;
          await liveQuietGap(500);
          continue;
        }
        // Aşama A — Sus/Dur/Kes
        if (looksLikeVoiceStopCommand(text)) {
          stopAllSpeech("komut: susturuldu — dinliyorum");
          bubble("user", text);
          meta.textContent = "komut: sus/dur/kes";
          setSahneState("dinle");
          await liveQuietGap(350);
          continue;
        }
        meta.textContent = "algı: " + text.slice(0, 80);
        try {
          await voiceTurn(text, { live: true });
        } catch (e) {
          meta.textContent = "sürekli tur: " + String(e.message || e);
        }
        if (!liveMode || liveAbort) break;
        // Cevap bitti — kısa nefes, yine dinle
        meta.textContent = "sürekli: yine dinliyorum…";
        await liveQuietGap(450);
      }
    } catch (e) {
      fatal = true;
      const name = String((e && e.name) || "");
      const msg = String(e && e.message ? e.message : e);
      if (/NotAllowed|Permission|Denied/i.test(name + " " + msg)) {
        meta.textContent =
          "Sürekli sohbet: mikrofon izni yok" +
          (isLikelyIos() ? " — iOS Ayarlar → Safari/Rüzgar → Mikrofon." : " — site ayarından izin ver.");
      } else if (/secure|Only secure/i.test(msg) || !micSecureOk()) {
        paintMicBlocked();
        meta.textContent = "Sürekli sohbet: HTTPS + mikrofon gerekli";
      } else {
        meta.textContent = "Sürekli sohbet açılamadı: " + msg;
      }
    } finally {
      // Durdur: setLivePref(false). Düşme/hata: pref açık kalır → otomatik yeniden
      const autoRestart = livePrefOn();
      liveMode = false;
      liveAbort = false;
      liveMuted = false;
      liveHoldRecord = false;
      micBusy = false;
      stopLiveStream();
      await releaseWakeLock();
      paintLiveBtn();
      if (autoRestart) {
        liveRestartN += 1;
        if (liveRestartN <= 8) {
          liveStartPending = true;
          if (meta && !/açılamadı|HTTPS/i.test(String(meta.textContent || ""))) {
            meta.textContent = "sürekli: yeniden bağlanıyor…";
          }
          setTimeout(function () {
            if (!livePrefOn() || liveMode) return;
            beginLiveSession();
          }, fatal ? 1200 : 500);
        } else {
          liveRestartN = 0;
          liveStartPending = true;
          if (meta) meta.textContent = "sürekli: dokun → yeniden aç";
        }
      } else if (meta && !/açılamadı|STT|Hata/i.test(String(meta.textContent || ""))) {
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
        liveStartPending = false;
        setLivePref(false);
        void releaseWakeLock();
        meta.textContent = "sürekli: durduruluyor…";
        paintLiveBtn();
        return;
      }
      beginLiveSession();
    };
  }

  // İlk jest: ses kilidi + bekleyen sürekli sohbeti aç (iOS/Android)
  document.addEventListener(
    "pointerdown",
    () => {
      unlockMobileAudio();
      if (liveStartPending && livePrefOn() && !liveMode) {
        beginLiveSession();
      }
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
  applySadeUi(); // Madde 2.5 — kayıtlı sade ses tercihi

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

  // Aşama B — ilk jestte autoplay/AudioContext kilidini aç (iOS/Android)
  (function bindGestureAudioUnlock() {
    let once = false;
    const arm = () => {
      if (once) return;
      once = true;
      unlockMobileAudio();
      try {
        document.removeEventListener("pointerdown", arm, true);
        document.removeEventListener("touchstart", arm, true);
        document.removeEventListener("click", arm, true);
      } catch (_) {}
    };
    try {
      document.addEventListener("pointerdown", arm, { capture: true, passive: true });
      document.addEventListener("touchstart", arm, { capture: true, passive: true });
      document.addEventListener("click", arm, { capture: true, passive: true });
    } catch (_) {}
  })();

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker
      .getRegistrations()
      .then((regs) => Promise.all(regs.map((r) => r.update())))
      .catch(() => {});
    navigator.serviceWorker
      .register("./sw.js?v=20261118-onboard")
      .then((reg) => {
        const kick = () => {
          if (reg.waiting) reg.waiting.postMessage({ type: "SKIP_WAITING" });
        };
        if (reg.waiting) kick();
        reg.addEventListener("updatefound", () => {
          const nw = reg.installing;
          if (!nw) return;
          nw.addEventListener("statechange", () => {
            if (nw.state === "installed" && navigator.serviceWorker.controller) {
              nw.postMessage({ type: "SKIP_WAITING" });
            }
          });
        });
        navigator.serviceWorker.addEventListener("controllerchange", () => {
          /* Yenile sonrası yeni SW — softReload zaten sayfayı çeker */
        });
      })
      .catch(() => {});
  }

  // Kapı durumu — görünür sağlık satırı + LAN/Tailscale / HTTPS mic ipuçları
  api("/api/mobil/status")
    .then((st) => {
      if (st && st.ok) {
        const bits = [`kapı açık · ${st.version || "mobil"}`];
        if (st.users != null) bits.push(`${st.users} kullanıcı`);
        const er = st.erisim || null;
        paintFriendGuide(er);
        if (er && er.lan_open === false) {
          bits.push("LAN kapalı (PC’de 0.0.0.0 gerekir)");
          setMsg(bits.join(" · "), false);
          return;
        }
        // Aşama D+sabit: MagicDNS / sticky önce (LAN 103↔105 kırılmaz)
        const preferStickyHttps = (list, erObj) => {
          const sticky = Array.isArray(erObj && erObj.sticky_urls)
            ? erObj.sticky_urls.map(String)
            : [];
          const stickyHit = sticky.find((u) => u.startsWith("https:"));
          if (stickyHit) return stickyHit;
          if (erObj && erObj.sticky_host) {
            return `https://${erObj.sticky_host}:8443/mobil/`;
          }
          const arr = Array.isArray(list) ? list.map(String) : [];
          const https = arr.filter((u) => u.startsWith("https:"));
          return (
            https.find((u) => /\.ts\.net(?::|\b)/i.test(u)) ||
            https.find((u) => /:\/\/100\./.test(u)) ||
            https.find((u) => /:\/\/(192\.168\.|10\.|172\.(1[6-9]|2\d|3[0-1])\.)/.test(u)) ||
            https[0] ||
            arr[0] ||
            ""
          );
        };
        if (er && Array.isArray(er.https_urls) && er.https_urls.length) {
          httpsMicPrefer = preferStickyHttps(er.https_urls, er);
        } else if (er && Array.isArray(er.urls) && er.urls.length) {
          httpsMicPrefer = preferStickyHttps(er.urls, er);
        }
        paintHttpsMicBar();
        if (er && Array.isArray(er.urls) && er.urls.length && baseInput) {
          const prefer = preferStickyHttps(er.urls, er);
          const asBase = String(prefer).replace(/\/mobil\/?$/, "");
          if (
            !localStorage.getItem(LS.base) ||
            /127\.0\.0\.1:8779|localhost:8779|192\.168\.\d+\.\d+/i.test(baseInput.value || "")
          ) {
            baseInput.value = asBase;
            try {
              localStorage.setItem(LS.base, asBase);
            } catch (_) {}
          }
        }
        if (micSecureOk()) bits.push("tek kapı (yazı+ses)");
        else bits.push("HTTPS köprü gerekli");
        if (er && er.cert_kind) bits.push(`cert ${er.cert_kind}`);
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
