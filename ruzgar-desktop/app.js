/**
 * Bağlantı hattı: UI → Tünel → Colab API (aynı köke WebSocket/SSE/Fetch).
 * Beyin adresi önceliği: ruzgar_remote_api.txt ile yüklenen uç > ?api > localStorage > yalın yerel.
 */
function resolveRuzgarApiRoot() {
  try {
    const remote =
      typeof window !== "undefined" &&
      window.ruzgarApi?.getRemoteBrainEndpoint?.();
    if (remote) return String(remote).trim().replace(/\/$/, "");
  } catch (_) {
    /* yok say */
  }
  try {
    const qs = new URLSearchParams(window.location.search).get("api");
    if (qs) return String(qs).trim().replace(/\/$/, "");
  } catch (_) {
    /* yok say */
  }
  try {
    if (typeof localStorage !== "undefined") {
      const ls = localStorage.getItem("ruzgarApi");
      if (ls) return String(ls).trim().replace(/\/$/, "");
    }
  } catch (_) {
    /* yok say */
  }
  return "http://127.0.0.1:8777";
}

const API = resolveRuzgarApiRoot();
console.info("[RÜZGAR Connection Bridge] API kök:", API);

/** Connection Bridge — istemci üst süre (ms); 0 = süresiz (RUZGAR_BRIDGE_TIMEOUT_MS varsayılan 0) */
function bridgeTimeoutMsHardCap() {
  try {
    if (window.ruzgarApi?.getBridgeTimeoutMs) {
      const t = window.ruzgarApi.getBridgeTimeoutMs();
      if (typeof t === "number" && t >= 0) return t;
    }
  } catch (_) {
    /* yok say */
  }
  return 0;
}

const RUZGAR_CHAT_STREAM_HARD_CAP_MS = bridgeTimeoutMsHardCap();

/** Kesin Köprü WebSocket ilk açılış tavanı (ms); llm_ollama._BRIDGE_UI_WS_HANDSHAKE_MAX_MS ile aynı rakam */
const RUZGAR_WS_BRIDGE_HANDSHAKE_CEILING_MS = 2147483647;

function tunnelWsHandshakeDeadlineMs() {
  try {
    if (window.ruzgarApi?.getTunnelWsHandshakeMaxMs) {
      const v = window.ruzgarApi.getTunnelWsHandshakeMaxMs();
      if (typeof v === "number" && v >= 60000) return v;
    }
  } catch (_) {
    /* yok say */
  }
  return RUZGAR_WS_BRIDGE_HANDSHAKE_CEILING_MS;
}

const RUZGAR_WS_OPEN_WAIT_MS =
  bridgeTimeoutMsHardCap() <= 0
    ? tunnelWsHandshakeDeadlineMs()
    : Math.max(120000, bridgeTimeoutMsHardCap());

function mergeAggressiveStreamingFetchInit(init = {}) {
  const out = { ...init };
  const noCacheHdr = {
    "Cache-Control": "no-cache",
    Pragma: "no-cache",
  };
  if (!out.headers) out.headers = { ...noCacheHdr };
  else if (typeof Headers !== "undefined" && out.headers instanceof Headers) {
    const h = out.headers;
    for (const [k, v] of Object.entries(noCacheHdr)) {
      if (!h.has(k)) h.set(k, v);
    }
  } else out.headers = { ...noCacheHdr, ...out.headers };
  if (out.cache === undefined || out.cache === null) out.cache = "no-store";
  return out;
}

function ruzgarApiOriginPrefix() {
  try {
    return new URL(API).origin;
  } catch {
    return "";
  }
}

/** Yerel masaüstü API’ye giden çağrılarda ara belleği düşük tut (streaming / Colab Köprüsü — Buffer Management) */
const _nativeFetch = window.fetch.bind(window);
window.fetch = function ruzgarPatchedFetch(input, init) {
  let urlStr = "";
  try {
    urlStr =
      typeof input === "string"
        ? input
        : input && typeof input.url === "string"
          ? input.url
          : "";
  } catch (_) {
    urlStr = "";
  }
  const pref = ruzgarApiOriginPrefix();
  if (pref && urlStr.startsWith(pref)) {
    init = mergeAggressiveStreamingFetchInit(init || {});
  }
  return _nativeFetch(input, init);
};

/** HTTP(S) API kökünü WebSocket köküne çevirir — Işık Hızı (Ümit & Gökçenur). */
function apiToWsBase(api) {
  try {
    const u = new URL(api);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    return u.origin;
  } catch {
    return "ws://127.0.0.1:8777";
  }
}

/** Yerel `desktop_server` (8777): WebSocket Köprüsü olmadan doğrudan SSE — öğrenme merkezi her turda garanti */
function ruzgarLikelyLocalDesktopApi() {
  try {
    const u = new URL(API);
    const h = String(u.hostname || "").toLowerCase();
    if (h !== "127.0.0.1" && h !== "localhost") return false;
    const rawPort =
      u.port ||
      (u.protocol === "https:" ? "443" : u.protocol === "http:" ? "80" : "");
    return String(rawPort) === "8777";
  } catch {
    return false;
  }
}

(function startTunnelKeepAlive() {
  const intervalMs = (() => {
    try {
      if (window.ruzgarApi?.getKeepAliveIntervalMs) {
        const n = window.ruzgarApi.getKeepAliveIntervalMs();
        if (typeof n === "number" && n >= 0) return n;
      }
    } catch (_) {
      /* yok say */
    }
    return 30000;
  })();
  if (!intervalMs) return;
  const ping = () => {
    window
      .fetch(`${API}/api/health`, {
        method: "GET",
        cache: "no-store",
        keepalive: true,
        headers: { "X-Ruzgar-Bridge": "keep-alive", "Cache-Control": "no-cache" },
      })
      .catch(() => {});
  };
  ping();
  window.setInterval(ping, intervalMs);
})();

/** Sunucudaki prior_messages limitiyle uyumlu; gereksiz büyük JSON göndermez */
const MAX_CLIENT_HISTORY_MSGS = 32;

const MODE_QS = new URLSearchParams(window.location.search);
let currentMode = (MODE_QS.get("mode") || "genel").trim().toLowerCase();
const WINDOW_TITLE_BASE =
  "RÜZGAR — Mimarlar: Ümit & Gökçenur";

const MODE_LABELS = {
  genel: "ANA MOTOR",
  uretim: "RÜZGAR ÇEKİRDEĞİ",
  gelisim: "Gelişim",
  ses: "SES MOTORU",
  okuma: "İLİM MOTORU",
  video: "VİDEO MOTORU",
  programlama: "PROGRAMLAMA MOTORU",
  hafiza: "HAFIZA MOTORU",
  duzen: "Düzen",
  dosya: "Dosya",
  hizli: "Hızlı",
};

const el = {
  chat: document.getElementById("chat-messages"),
  input: document.getElementById("msg-input"),
  send: document.getElementById("btn-send"),
  stop: document.getElementById("btn-stop"),
  mic: document.getElementById("btn-mic"),
  web: document.getElementById("opt-web"),
  linkRead: document.getElementById("opt-link-read"),
  fetchN: document.getElementById("opt-fetch"),
  code: document.getElementById("opt-code"),
  voiceOut: document.getElementById("opt-voice-out"),
  voiceSend: document.getElementById("opt-voice-send"),
  optAutonom: document.getElementById("opt-autonom"),
  api: document.getElementById("api-status"),
  modeBadge: document.getElementById("mode-badge"),
  modeGenelHint: document.getElementById("mode-genel-hint"),
  statusR: document.getElementById("status-right"),
  statusL: document.getElementById("status-left"),
  tree: document.getElementById("file-tree"),
  navBack: document.getElementById("nav-back"),
  navForward: document.getElementById("nav-forward"),
  navRefresh: document.getElementById("nav-refresh"),
  navClearChat: document.getElementById("nav-clear-chat"),
  cpu: document.getElementById("cpu-indicator"),
  gpu: document.getElementById("gpu-indicator"),
  micLevelWrap: document.getElementById("mic-level-wrap"),
  micLevelBar: document.getElementById("mic-level-bar"),
  micLevelPct: document.getElementById("mic-level-pct"),
  micTestPill: document.getElementById("mic-test-pill"),
  sistemAyarlariOverlay: document.getElementById("sistem-ayarlari-overlay"),
  optMicMeterTest: document.getElementById("opt-mic-meter-test"),
  selMicDevice: document.getElementById("sel-mic-device"),
  btnMicRefresh: document.getElementById("btn-mic-refresh"),
  btnSistemAyarlariKapat: document.getElementById("btn-sistem-ayarlari-kapat"),
  panelMain: document.getElementById("panel-main"),
  thinkingOverlay: document.getElementById("thinking-center-overlay"),
  thinkingTitle: document.getElementById("thinking-center-title"),
  thinkingSub: document.getElementById("thinking-center-sub"),
  hafizaReminder: document.getElementById("hafiza-reminder"),
  hafizaReminderText: document.getElementById("hafiza-reminder-text"),
  btnHafizaReminderKapat: document.getElementById("btn-hafiza-reminder-kapat"),
  btnHafizaYonet: document.getElementById("btn-hafiza-yonet"),
  btnKisiselPanel: document.getElementById("btn-kisisel-panel"),
  hafizaYonetOverlay: document.getElementById("hafiza-yonet-overlay"),
  hafizaList: document.getElementById("hafiza-list"),
  hafizaListEmpty: document.getElementById("hafiza-list-empty"),
  btnHafizaYonetRefresh: document.getElementById("btn-hafiza-yonet-refresh"),
  btnHafizaYonetKapat: document.getElementById("btn-hafiza-yonet-kapat"),
  kisiselOverlay: document.getElementById("kisisel-panel-overlay"),
  kisiselUmit: document.getElementById("kisisel-umit"),
  kisiselGokcenur: document.getElementById("kisisel-gokcenur"),
  kisiselNotlar: document.getElementById("kisisel-notlar"),
  btnKisiselKaydet: document.getElementById("btn-kisisel-kaydet"),
  btnKisiselIptal: document.getElementById("btn-kisisel-iptal"),
  modeBtnGenel: document.getElementById("mode-btn-genel"),
  modeBtnVideo: document.getElementById("mode-btn-video"),
  modeBtnProgramlama: document.getElementById("mode-btn-programlama"),
  modeBtnHafiza: document.getElementById("mode-btn-hafiza"),
  modeBtnOkuma: document.getElementById("mode-btn-okuma"),
  modeBtnSes: document.getElementById("mode-btn-ses"),
  motorDeclarationHeader: document.getElementById("motor-declaration-header"),
  dynamicWorkbench: document.getElementById("dynamic-workbench"),
  pageGenel: document.getElementById("page-genel"),
  pageHafiza: document.getElementById("page-hafiza"),
  pageOkuma: document.getElementById("page-okuma"),
  pageVideo: document.getElementById("page-video"),
  pageProgramlama: document.getElementById("page-programlama"),
  pageSes: document.getElementById("page-ses"),
  btnLayoutFull: document.getElementById("btn-layout-full"),
  btnLayoutSplit2: document.getElementById("btn-layout-split2"),
  btnLayoutSplit4: document.getElementById("btn-layout-split4"),
  hafizaListView: document.getElementById("hafiza-list-view"),
  hafizaInput: document.getElementById("hafiza-input"),
  btnHafizaSave: document.getElementById("btn-hafiza-save"),
  btnHafizaSend: document.getElementById("btn-hafiza-send"),
  btnHafizaRefresh: document.getElementById("btn-hafiza-refresh"),
  hafizaAnalyzeActions: document.getElementById("hafiza-analyze-actions"),
  btnHafizaDeleteSelected: document.getElementById("btn-hafiza-delete-selected"),
  btnHafizaDeleteAll: document.getElementById("btn-hafiza-delete-all"),
  btnHafizaDeleteCancel: document.getElementById("btn-hafiza-delete-cancel"),
  ilimFileList: document.getElementById("ilim-file-list"),
  ilimFileContent: document.getElementById("ilim-file-content"),
  videoFileInput: document.getElementById("video-file-input"),
  videoPreview: document.getElementById("video-preview"),
  audioFileInput: document.getElementById("audio-file-input"),
  audioPreview: document.getElementById("audio-preview"),
  dashboardStatus: document.getElementById("dashboard-status"),
  dashboardLastSpeech: document.getElementById("dashboard-last-speech"),
  ctxMenu: document.getElementById("ctx-menu"),
};

let hafizaAnalyzeRows = [];
let hafizaLookup = {};
let selectedAnalyzeIndex = -1;

const TOP_MODE_BUTTONS = [
  "modeBtnGenel",
  "modeBtnVideo",
  "modeBtnProgramlama",
  "modeBtnHafiza",
  "modeBtnOkuma",
  "modeBtnSes",
];

function syncTopModeButtons() {
  for (const key of TOP_MODE_BUTTONS) {
    const btn = el[key];
    if (!btn) continue;
    const mode = String(btn.getAttribute("data-mode") || "").trim().toLowerCase();
    btn.classList.toggle("is-active", mode === currentMode);
    btn.setAttribute("aria-pressed", mode === currentMode ? "true" : "false");
  }
}

/** Sistem paneli + kalıcı mikrofon testi — Ümit & Gökçenur */
const LS_MIC_METER_TEST = "ruzgar_mic_meter_test";
const LS_MIC_DEVICE_ID = "ruzgar_mic_device_id";

function micMeterTestModeEnabled() {
  try {
    return localStorage.getItem(LS_MIC_METER_TEST) === "1";
  } catch (_) {
    return false;
  }
}

function syncMicTestPill() {
  if (!el.micTestPill) return;
  el.micTestPill.hidden = !micMeterTestModeEnabled();
}

/**
 * Tarayıcı / Electron için seçili veya sistem varsayılanı mikrofon.
 * @returns {MediaStreamConstraints}
 */
function getMicAudioConstraints() {
  try {
    const id = localStorage.getItem(LS_MIC_DEVICE_ID);
    if (id && String(id).length > 0) {
      return { audio: { deviceId: { exact: id } } };
    }
  } catch (_) {
    /* ignore */
  }
  return { audio: true };
}

async function refreshMicDeviceList(requestPermission) {
  const sel = el.selMicDevice;
  if (!sel) return;
  if (requestPermission && navigator.mediaDevices?.getUserMedia) {
    try {
      const st = await navigator.mediaDevices.getUserMedia(getMicAudioConstraints());
      st.getTracks().forEach((t) => t.stop());
    } catch (err) {
      console.warn("[RÜZGAR] Mikrofon izni veya cihaz (Ümit & Gökçenur):", err);
    }
  }
  try {
    const list = await navigator.mediaDevices.enumerateDevices();
    const inputs = list.filter((d) => d.kind === "audioinput");
    let saved = "";
    try {
      saved = localStorage.getItem(LS_MIC_DEVICE_ID) || "";
    } catch (_) {
      /* ignore */
    }
    sel.innerHTML = "";
    const o0 = document.createElement("option");
    o0.value = "";
    o0.textContent = "Sistem varsayılanı (işletim sistemi)";
    sel.appendChild(o0);
    let found = false;
    for (const d of inputs) {
      const o = document.createElement("option");
      o.value = d.deviceId;
      const lab =
        d.label ||
        `Giriş (${String(d.deviceId).slice(0, 10)}…)`;
      o.textContent = lab;
      if (d.deviceId === saved) {
        o.selected = true;
        found = true;
      }
      sel.appendChild(o);
    }
    if (saved && !found) {
      const ox = document.createElement("option");
      ox.value = saved;
      ox.textContent = "(Kayıtlı cihaz listede yok — yeniden seçin)";
      ox.selected = true;
      sel.appendChild(ox);
    }
  } catch (e) {
    sel.innerHTML =
      "<option value=\"\">Cihaz listesi alınamadı</option>";
    console.warn("[RÜZGAR] enumerateDevices:", e);
  }
}

function openSistemAyarlariPanel() {
  if (el.optMicMeterTest) {
    el.optMicMeterTest.checked = micMeterTestModeEnabled();
  }
  if (el.sistemAyarlariOverlay) {
    el.sistemAyarlariOverlay.hidden = false;
    el.sistemAyarlariOverlay.removeAttribute("aria-hidden");
  }
  void refreshMicDeviceList(false);
}

function closeSistemAyarlariPanel() {
  if (!el.sistemAyarlariOverlay) return;
  el.sistemAyarlariOverlay.hidden = true;
  el.sistemAyarlariOverlay.setAttribute("aria-hidden", "true");
}

function wireSistemAyarlariPanel() {
  if (el.optMicMeterTest) {
    el.optMicMeterTest.addEventListener("change", () => {
      try {
        if (el.optMicMeterTest.checked) {
          localStorage.setItem(LS_MIC_METER_TEST, "1");
        } else {
          localStorage.removeItem(LS_MIC_METER_TEST);
        }
      } catch (_) {
        /* ignore */
      }
      syncMicTestPill();
      setStatus(
        el.optMicMeterTest.checked
          ? "Mic test açık (çubuk + % — Ümit & Gökçenur)"
          : "Mic test kapalı",
        "Rüzgar"
      );
    });
  }
  if (el.selMicDevice) {
    el.selMicDevice.addEventListener("change", () => {
      const v = el.selMicDevice.value;
      try {
        if (v) localStorage.setItem(LS_MIC_DEVICE_ID, v);
        else localStorage.removeItem(LS_MIC_DEVICE_ID);
      } catch (_) {
        /* ignore */
      }
      setStatus(
        v ? "Mikrofon cihazı kaydedildi" : "Sistem varsayılanı mikrofon",
        "Rüzgar"
      );
    });
  }
  if (el.btnMicRefresh) {
    el.btnMicRefresh.addEventListener("click", () => {
      void refreshMicDeviceList(true);
      setStatus("Mikrofon listesi yenilendi (izin gerekirse sorulur)", "Rüzgar");
    });
  }
  if (el.btnSistemAyarlariKapat) {
    el.btnSistemAyarlariKapat.addEventListener("click", () =>
      closeSistemAyarlariPanel()
    );
  }
  if (el.sistemAyarlariOverlay) {
    el.sistemAyarlariOverlay.addEventListener("click", (e) => {
      if (e.target === el.sistemAyarlariOverlay) closeSistemAyarlariPanel();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!el.sistemAyarlariOverlay || el.sistemAyarlariOverlay.hidden) return;
    closeSistemAyarlariPanel();
  });
}

syncMicTestPill();
wireSistemAyarlariPanel();

function syncWebFetchUi() {
  if (el.fetchN && el.web) el.fetchN.disabled = !el.web.checked;
}

function applyModeToUI() {
  const label = MODE_LABELS[currentMode] || currentMode;
  if (el.modeBadge) el.modeBadge.textContent = label;
  if (el.modeGenelHint)
    el.modeGenelHint.hidden = currentMode !== "genel";
  document.title = `${WINDOW_TITLE_BASE} — ${label}`;
  if (el.code) {
    if (currentMode === "programlama") el.code.checked = true;
    if (currentMode === "hafiza") el.code.checked = false;
  }
  if (el.web) {
    if (["ses", "okuma", "uretim", "hizli", "hafiza"].includes(currentMode)) {
      el.web.checked = false;
    } else {
      el.web.checked = true;
    }
  }
  syncWebFetchUi();
  if (currentMode === "okuma") {
    el.input.placeholder =
      "Kültür ve İlim Hazinesi: metni yapıştırın; arsiv/ altındaki dört külliyata PDF/TXT ekleyip indeks: python -m ilim_assistant.arsiv_indexle";
  } else {
    el.input.placeholder =
      "Soru yazın veya yapıştırın — Web açıkken arama + okuma; doğrudan https:// bağlantısı da okunur.";
  }
  syncTopModeButtons();
}
applyModeToUI();
if (el.web) el.web.addEventListener("change", syncWebFetchUi);
let perfBusy = false;
let latestMetrics = { cpu: null, gpu: null };

/** Edge-TTS: SSE ile cümle tamponu; üst üste istekleri önlemek için oturum sayacı */
let ttsSessionCounter = 0;
let ttsPendingChunks = "";
const ttsTextQueue = [];
let ttsPumping = false;
let ttsAbortController = null;
let ttsPlayingEl = null;
let ttsEdgeSpokeTurn = false;

/** TTS sentez — arka iş parçacığı (Web Worker); yoksa fetch ile düşme (Ümit & Gökçenur). */
let _ttsWorker = null;
let _ttsWorkerBroken = false;
let _ttsJobSeq = 0;

function getTtsWorker() {
  if (_ttsWorkerBroken) return null;
  if (_ttsWorker) return _ttsWorker;
  try {
    _ttsWorker = new Worker("tts-worker.js");
    _ttsWorker.addEventListener("error", () => {
      _ttsWorkerBroken = true;
    });
    return _ttsWorker;
  } catch {
    _ttsWorkerBroken = true;
    return null;
  }
}

/** Dinamit: son STT duygusu — TTS hız/ton (Ümit & Gökçenur) */
let lastVoiceEmotion = null;
/** 0..1 mikrofon ortalama (VAD çubuğu ile) */
let lastMicEnergy01 = 0.45;

function synthEdgeMp3ViaWorker(apiRoot, text, karakter, signal, emotion) {
  return new Promise((resolve, reject) => {
    const w = getTtsWorker();
    if (!w) {
      reject(new Error("no-tts-worker"));
      return;
    }
    const id = ++_ttsJobSeq;
    const onAbort = () => {
      w.removeEventListener("message", onMsg);
      reject(new DOMException("Aborted", "AbortError"));
    };
    if (signal.aborted) {
      onAbort();
      return;
    }
    signal.addEventListener("abort", onAbort, { once: true });
    const onMsg = (e) => {
      const data = e.data || {};
      if (data.id !== id) return;
      w.removeEventListener("message", onMsg);
      signal.removeEventListener("abort", onAbort);
      if (data.ok) resolve(new Blob([data.buf]));
      else reject(new Error(data.err || "tts-worker"));
    };
    w.addEventListener("message", onMsg);
    const payload = {
      id,
      api: apiRoot,
      text,
      karakter,
    };
    if (emotion && emotion !== "notr") payload.emotion = emotion;
    w.postMessage(payload);
  });
}

function showThinkingCenter(titleText) {
  if (el.thinkingTitle) {
    el.thinkingTitle.textContent =
      titleText ||
      (currentMode === "okuma"
        ? "İlim Hazinesi taranıyor…"
        : "Rüzgar düşünüyor…");
  }
  if (el.thinkingOverlay) {
    el.thinkingOverlay.hidden = false;
    el.thinkingOverlay.removeAttribute("aria-hidden");
  }
  if (el.panelMain) el.panelMain.classList.add("thinking-dim");
}

function hideThinkingCenter() {
  if (el.thinkingOverlay) {
    el.thinkingOverlay.hidden = true;
    el.thinkingOverlay.setAttribute("aria-hidden", "true");
  }
  if (el.panelMain) el.panelMain.classList.remove("thinking-dim");
}

function updatePerformanceIndicators(busy) {
  const core = currentMode === "uretim";
  const cpu = latestMetrics.cpu;
  const gpu = latestMetrics.gpu;
  const cpuTxt = Number.isFinite(cpu) ? `CPU: %${Math.round(cpu)}` : "CPU: -";
  const gpuTxt = Number.isFinite(gpu) ? `GPU: %${Math.round(gpu)}` : "GPU: -";
  if (el.cpu) el.cpu.textContent = cpuTxt;
  if (el.gpu) el.gpu.textContent = gpuTxt;
  document.body.classList.toggle("core-mode", core);
  document.body.classList.toggle("core-busy", core && !!busy);
}
updatePerformanceIndicators(false);
syncInterruptButton();

async function refreshPerformanceMetrics() {
  try {
    const r = await fetch(`${API}/api/system-metrics`, { method: "GET" });
    if (!r.ok) return;
    const j = await r.json();
    latestMetrics = {
      cpu: typeof j.cpu_percent === "number" ? j.cpu_percent : null,
      gpu: typeof j.gpu_percent === "number" ? j.gpu_percent : null,
    };
    updatePerformanceIndicators(perfBusy);
  } catch (_) {
    /* metrics optional */
  }
}

function scheduleMetricsPolling() {
  const periodMs = currentMode === "uretim" ? 700 : 2500;
  window.setTimeout(async () => {
    await refreshPerformanceMetrics();
    scheduleMetricsPolling();
  }, periodMs);
}

function switchMode(mode) {
  const next = String(mode || "").trim().toLowerCase();
  if (!next) return;
  if (perfBusy) {
    interruptRuzgar();
    if (el.send) el.send.disabled = false;
    perfBusy = false;
  }
  currentMode = next;
  applyModeToUI();
  setStatus(`Mod: ${MODE_LABELS[currentMode] || currentMode}`, "Rüzgar");
  updatePerformanceIndicators(perfBusy);
  updateDynamicWorkbench();
  const motorDeclarationByMode = {
    genel: "Şu anda ana motor tam güç ve tam kapasite çalışıyor.",
    okuma: "Kültür ve İlim Hazinesi okuma bölümü açıldı.",
    video: "Bu motorda sadece video oluşturabilirsiniz.",
    programlama: "Bu motorla sadece program yazabilirsiniz.",
    hafiza:
      "Hafıza motoru açıldı; bu motorla gelişim ve hafıza teknikleri üzerinde çalışabilirsiniz.",
    ses: "Ses motoru açıldı; bu motorla ses işleme ve seslendirme yapabilirsiniz.",
  };
  setHeaderMotorDeclaration(motorDeclarationByMode[currentMode] || "");
  clearMotorDeclarations();
}

function setWorkbenchLayout(kind) {
  if (!el.dynamicWorkbench) return;
  el.dynamicWorkbench.classList.remove("layout-full", "layout-split2", "layout-split4");
  el.dynamicWorkbench.classList.add(kind);
  document.body.classList.toggle("workbench-full", kind === "layout-full");
  setStatus(`Çalışma sayfası düzeni: ${kind.replace("layout-", "")}`, "Rüzgar");
}

function updateDynamicWorkbench() {
  const pages = [
    el.pageGenel,
    el.pageHafiza,
    el.pageOkuma,
    el.pageVideo,
    el.pageProgramlama,
    el.pageSes,
  ];
  pages.forEach((p) => {
    if (p) p.hidden = true;
  });
  const map = {
    genel: el.pageGenel,
    hafiza: el.pageHafiza,
    okuma: el.pageOkuma,
    video: el.pageVideo,
    programlama: el.pageProgramlama,
    ses: el.pageSes,
  };
  const active = map[currentMode] || el.pageGenel;
  if (active) active.hidden = false;
  if (currentMode === "hafiza") {
    setWorkbenchLayout("layout-split2");
  }
  if (el.dashboardStatus)
    el.dashboardStatus.textContent = `Aktif motor: ${MODE_LABELS[currentMode] || currentMode}`;
  if (el.dashboardLastSpeech) {
    const short = (lastAssistantReply || "").trim();
    el.dashboardLastSpeech.textContent = short
      ? `Son konuşma: ${short.slice(0, 280)}`
      : "Son konuşma: (bekleniyor)";
  }
  if (currentMode === "hafiza") void loadHafizaJsonView();
  if (currentMode === "okuma") void loadIlimFileList();
}

function wireTopModeButtons() {
  for (const key of TOP_MODE_BUTTONS) {
    const btn = el[key];
    if (!btn) continue;
    btn.addEventListener("click", () => {
      const mode = String(btn.getAttribute("data-mode") || "").trim().toLowerCase();
      if (!mode) return;
      switchMode(mode);
      el.input.focus();
    });
  }
}

function wireDynamicWorkbench() {
  if (el.btnLayoutFull) el.btnLayoutFull.addEventListener("click", () => setWorkbenchLayout("layout-full"));
  if (el.btnLayoutSplit2) el.btnLayoutSplit2.addEventListener("click", () => setWorkbenchLayout("layout-split2"));
  if (el.btnLayoutSplit4) el.btnLayoutSplit4.addEventListener("click", () => setWorkbenchLayout("layout-split4"));
  if (el.btnHafizaSave) {
    // Click event köprüsü: analiz satırlarını kalıcı hafızaya yazar.
    el.btnHafizaSave.addEventListener("click", (ev) => {
      ev.preventDefault();
      void saveHafizaAnalyzeRows();
    });
  }
  if (el.btnHafizaSend) {
    el.btnHafizaSend.onclick = () => {
      void sendToHafizaAnalyze();
    };
  }
  if (el.btnHafizaRefresh) {
    el.btnHafizaRefresh.addEventListener("click", () => {
      void updateTable();
    });
  }
  if (el.btnHafizaDeleteSelected) {
    el.btnHafizaDeleteSelected.addEventListener("click", () => {
      if (selectedAnalyzeIndex < 0 || selectedAnalyzeIndex >= hafizaAnalyzeRows.length) return;
      hafizaAnalyzeRows.splice(selectedAnalyzeIndex, 1);
      selectedAnalyzeIndex = -1;
      renderAnalyzeRowsImmediate();
      if (el.hafizaAnalyzeActions) el.hafizaAnalyzeActions.hidden = true;
    });
  }
  if (el.btnHafizaDeleteAll) {
    el.btnHafizaDeleteAll.addEventListener("click", () => {
      hafizaAnalyzeRows = [];
      selectedAnalyzeIndex = -1;
      void updateTable();
      if (el.hafizaAnalyzeActions) el.hafizaAnalyzeActions.hidden = true;
    });
  }
  if (el.btnHafizaDeleteCancel) {
    el.btnHafizaDeleteCancel.addEventListener("click", () => {
      selectedAnalyzeIndex = -1;
      if (el.hafizaAnalyzeActions) el.hafizaAnalyzeActions.hidden = true;
      if (el.hafizaListView) {
        el.hafizaListView
          .querySelectorAll(".hafiza-row-selected")
          .forEach((r) => r.classList.remove("hafiza-row-selected"));
      }
    });
  }
  if (el.hafizaInput) {
    if (el.hafizaInput.isContentEditable) {
      el.hafizaInput.addEventListener("input", () => syncHafizaEditorEmptyClass());
      el.hafizaInput.addEventListener("paste", (e) => {
        e.preventDefault();
        const t = e.clipboardData.getData("text/plain");
        document.execCommand("insertText", false, t);
        syncHafizaEditorEmptyClass();
      });
      document.querySelectorAll(".hafiza-rich-btn[data-rich]").forEach((btn) => {
        btn.addEventListener("click", (ev) => {
          ev.preventDefault();
          el.hafizaInput.focus();
          const a = btn.getAttribute("data-rich");
          if (a === "bold") document.execCommand("bold");
          if (a === "italic") document.execCommand("italic");
          if (a === "underline") document.execCommand("underline");
        });
      });
    }
    el.hafizaInput.addEventListener("keydown", (e) => {
      if (e.key !== "Enter") return;
      if (e.shiftKey) {
        if (el.hafizaInput.isContentEditable) {
          e.preventDefault();
          document.execCommand("insertLineBreak");
        }
        return;
      }
      e.preventDefault();
      void sendToHafizaAnalyze();
    });
  }
  if (el.videoFileInput && el.videoPreview) {
    el.videoFileInput.addEventListener("change", () => {
      const f = el.videoFileInput.files && el.videoFileInput.files[0];
      if (!f) return;
      el.videoPreview.src = URL.createObjectURL(f);
    });
  }
  if (el.audioFileInput && el.audioPreview) {
    el.audioFileInput.addEventListener("change", () => {
      const f = el.audioFileInput.files && el.audioFileInput.files[0];
      if (!f) return;
      el.audioPreview.src = URL.createObjectURL(f);
    });
  }
}

function wireContextMenu() {
  if (!el.ctxMenu) return;

  const hideMenu = () => {
    el.ctxMenu.hidden = true;
    el.ctxMenu.style.display = "none";
    el.ctxMenu.setAttribute("aria-hidden", "true");
  };

  const showMenu = (clientX, clientY) => {
    el.ctxMenu.hidden = false;
    el.ctxMenu.style.display = "flex";
    el.ctxMenu.removeAttribute("aria-hidden");
    requestAnimationFrame(() => {
      const pad = 6;
      const w = el.ctxMenu.offsetWidth || 140;
      const h = el.ctxMenu.offsetHeight || 96;
      const maxX = Math.max(pad, window.innerWidth - w - pad);
      const maxY = Math.max(pad, window.innerHeight - h - pad);
      el.ctxMenu.style.left = `${Math.min(Math.max(pad, clientX), maxX)}px`;
      el.ctxMenu.style.top = `${Math.min(Math.max(pad, clientY), maxY)}px`;
    });
  };

  /** Menü dışına her türlü etkileşimde kapat (click bazen gelmez; scroll iç alanda kabarcıklanmaz). */
  const closeIfOutside = (e) => {
    if (!el.ctxMenu || el.ctxMenu.hidden) return;
    const t = e.target;
    if (t instanceof Node && el.ctxMenu.contains(t)) return;
    hideMenu();
  };

  document.addEventListener("pointerdown", closeIfOutside, true);
  document.addEventListener("wheel", closeIfOutside, { capture: true, passive: true });
  document.addEventListener("scroll", hideMenu, true);
  window.addEventListener("blur", hideMenu);
  window.addEventListener("resize", hideMenu);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") hideMenu();
  });

  document.addEventListener("contextmenu", (e) => {
    const t = e.target;
    if (!(t instanceof HTMLElement)) return;
    // Yerel OS menüsü: düz metin alanları
    if (t.closest("textarea, input, [contenteditable='true']")) {
      hideMenu();
      return;
    }
    if (!t.closest("pre, .motor-page, .chat-scroll")) return;
    e.preventDefault();
    showMenu(e.clientX, e.clientY);
  });

  el.ctxMenu.querySelectorAll("button[data-act]").forEach((btn) => {
    btn.addEventListener(
      "click",
      async (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const act = btn.getAttribute("data-act");
        hideMenu();
        if (act === "cut") {
          try {
            document.execCommand("cut");
          } catch (_) {
            /* yok say */
          }
          return;
        }
        if (act === "copy") {
          try {
            document.execCommand("copy");
          } catch (_) {
            /* yok say */
          }
          return;
        }
        if (act === "paste") {
          try {
            const txt = await navigator.clipboard.readText();
            const a = document.activeElement;
            if (a && "value" in a) {
              a.value += txt;
              return;
            }
            if (a instanceof HTMLElement && a.isContentEditable) {
              a.focus();
              document.execCommand("insertText", false, txt);
            }
          } catch (_) {
            try {
              document.execCommand("paste");
            } catch (_2) {
              /* yok say */
            }
          }
        }
      },
      true
    );
  });
}

/** Akış kesintisi — WebSocket + SSE (Ümit & Gökçenur UX) */
let activeChatAbort = null;
/** @type {WebSocket | null} */
let activeChatWs = null;
let userRequestedChatStop = false;

const KEYS_VOICE_SILENCE_IGNORE = new Set([
  "Escape",
  "Tab",
  "ArrowUp",
  "ArrowDown",
  "ArrowLeft",
  "ArrowRight",
  "Home",
  "End",
  "PageUp",
  "PageDown",
  "CapsLock",
]);

/** @type {{role:string, content:string}[]} */
let chatHistory = [];
let sessionWakeUsed = false;
let lastAssistantReply = "";

function setStatus(right, left) {
  if (right != null) el.statusR.textContent = right;
  if (left != null) el.statusL.textContent = left;
}

/** Ses motoru (Edge + Web Speech) — yazarken veya yeni turda anında sustur */
function silenceVoiceOutputNow() {
  bumpTtsSession();
  try {
    window.speechSynthesis.cancel();
  } catch (_) {
    /* yok say */
  }
}

/** Yazmaya başlanınca: yalnızca ses/kuyruk gerçekten çalışıyorsa kes (gereksiz oturum sıfırlaması yok) */
function silenceVoiceOnUserEdit() {
  let synBusy = false;
  try {
    synBusy = window.speechSynthesis.speaking;
  } catch (_) {
    /* yok say */
  }
  const edgeBusy = !!(
    ttsPlayingEl ||
    ttsPumping ||
    (ttsTextQueue && ttsTextQueue.length > 0) ||
    (ttsPendingChunks && String(ttsPendingChunks).trim().length > 0)
  );
  if (!edgeBusy && !synBusy) return;
  silenceVoiceOutputNow();
}

/** Durdur görünürlüğü: yanıt beklerken veya TTS kuyruğu/çalma aktifken */
function syncInterruptButton() {
  if (!el.stop) return;
  const ttsBusy = !!(
    ttsPlayingEl ||
    ttsPumping ||
    (ttsTextQueue && ttsTextQueue.length > 0) ||
    (ttsPendingChunks && String(ttsPendingChunks).trim().length > 0)
  );
  el.stop.hidden = !perfBusy && !ttsBusy;
}

function interruptRuzgar() {
  if (activeChatAbort || activeChatWs) userRequestedChatStop = true;
  bumpTtsSession();
  try {
    window.speechSynthesis.cancel();
  } catch (_) {
    /* yok say */
  }
  try {
    activeChatWs?.close();
  } catch (_) {
    /* yok say */
  }
  try {
    activeChatAbort?.abort();
  } catch (_) {
    /* yok say */
  }
  hideThinkingCenter();
  setStatus("Durduruldu", "Rüzgar");
  syncInterruptButton();
}

/** Uygulamayı kapatmadan sohbet oturumunu sıfırla */
function clearChatSession() {
  chatHistory = [];
  sessionWakeUsed = false;
  lastAssistantReply = "";
  el.chat.innerHTML = "";
  el.input.value = "";
  setStatus("Sohbet temizlendi", "Rüzgar");
  window.setTimeout(() => setStatus("Hazır", "Rüzgar"), 1600);
}

function wireNavToolbar() {
  const api = window.ruzgarApi;
  if (el.navBack) {
    el.navBack.addEventListener("click", async () => {
      if (api?.navGoBack) {
        const ok = await api.navGoBack();
        if (!ok) setStatus("Geri gidilecek sayfa yok", null);
        else setStatus("Hazır", "Rüzgar");
      } else {
        try {
          if (window.history.length > 1) window.history.back();
        } catch {
          setStatus("Geri kullanılamıyor", null);
        }
      }
    });
  }
  if (el.navForward) {
    el.navForward.addEventListener("click", async () => {
      if (api?.navGoForward) {
        const ok = await api.navGoForward();
        if (!ok) setStatus("İleri gidilecek sayfa yok", null);
        else setStatus("Hazır", "Rüzgar");
      }
    });
  }
  if (el.navRefresh) {
    el.navRefresh.addEventListener("click", async () => {
      if (api?.navReload) await api.navReload();
      else window.location.reload();
    });
  }
  if (el.navClearChat) {
    el.navClearChat.addEventListener("click", () => clearChatSession());
  }
}

function esc(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

/** UTF-8 yanlışlıkla Latin-1 gibi okunmuşsa (Ãœ, Ä±) düzelt — birikmiş metin üzerinde */
/** Sunucu full_reply bazen UTF-8 iki kez yanlış okunmuş gibi gelir; akış metni düzgün kalır */
function looksLikeMojibake(s) {
  return /Ã[¼¤]|Ä±|ÄŸ|ÅŸ|nasÄ±l|Ã¼mit|TALÄ°MAT|Ã–NCEL/i.test(s || "");
}

function extractYerelFooter(s) {
  const m = (s || "").match(/\n\n\*\(Yerel bağlam:[\s\S]*?\)\*/);
  return m ? m[0] : "";
}

/** Eski sunucu hâlâ altbilgi gönderse bile sohbet balonunda gösterme */
function stripYerelFooter(s) {
  return (s || "")
    .replace(/\n\n\*\(Yerel bağlam:[\s\S]*?\)\*/g, "")
    .replace(/\n+\*\(Yerel bağlam:[\s\S]*?\)\*/g, "")
    .trimEnd();
}

function repairMojibake(s) {
  if (!s || s.length < 2) return s;
  if (!/[ÃÄÅÂ]/.test(s)) return s;
  const score = (t) =>
    ["Ã", "Ä", "Å", "Â"].reduce((n, ch) => n + t.split(ch).length - 1, 0);
  let best = s;
  let bestSc = score(s);
  try {
    const u8 = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      if (c > 255) return s;
      u8[i] = c;
    }
    const t = new TextDecoder("utf-8", { fatal: false }).decode(u8);
    const sc = score(t);
    if (sc < bestSc) {
      best = t;
      bestSc = sc;
    }
  } catch (_) {
    /* ignore */
  }
  return best;
}

function appendBubble(role, text) {
  const div = document.createElement("div");
  div.className = `bubble ${role}`;
  div.innerHTML = esc(text);
  el.chat.appendChild(div);
  el.chat.scrollTop = el.chat.scrollHeight;
}

function clearMotorDeclarations() {
  if (!el.chat) return;
  el.chat.querySelectorAll(".motor-declaration").forEach((n) => n.remove());
}

function appendMotorDeclaration(text) {
  if (!el.chat || !text) return;
  clearMotorDeclarations();
  const div = document.createElement("div");
  div.className = "bubble assistant motor-declaration";
  div.innerHTML = esc(text);
  el.chat.appendChild(div);
  el.chat.scrollTop = el.chat.scrollHeight;
}

function setHeaderMotorDeclaration(text) {
  if (!el.motorDeclarationHeader) return;
  el.motorDeclarationHeader.textContent = String(text || "").trim();
}

function wireHafizaAnalyzeTableInteractions() {
  if (!el.hafizaListView) return;
  selectedAnalyzeIndex = -1;
  const trs = el.hafizaListView.querySelectorAll("tbody tr");
  trs.forEach((tr) => {
    tr.addEventListener("click", () => {
      const idx = Number(tr.getAttribute("data-idx"));
      selectedAnalyzeIndex = Number.isFinite(idx) ? idx : -1;
      trs.forEach((x) => x.classList.remove("hafiza-row-selected"));
      tr.classList.add("hafiza-row-selected");
      if (el.hafizaAnalyzeActions) el.hafizaAnalyzeActions.hidden = false;
    });
  });
  el.hafizaListView.querySelectorAll(".hafiza-q-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const q = String(btn.getAttribute("data-q") || "").trim();
      if (!q) return;
      if (el.input) el.input.value = q;
      await sendMessageWithText(q);
    });
  });
}

async function loadHafizaJsonView() {
  if (!el.hafizaListView) return;
  try {
    const r = await fetch(`${API}/api/hafiza/arsiv?t=${Date.now()}`);
    const j = await r.json();
    // Tam sözlük sadece soru→cevap önizlemesi (Gönder / motor-read) için; analiz tablosunda gösterilmez.
    hafizaLookup = { ...(j.data || {}) };
    if (!hafizaAnalyzeRows.length) {
      el.hafizaListView.innerHTML =
        '<div class="mini-card">Analiz bekleyen satır yok. Soru girip Gönder ile ekleyin; Hafızaya Al ile kalıcı kaydedilir.</div>';
      return;
    }
    const body = hafizaAnalyzeRows
      .map(
        (x, idx) =>
          `<tr data-idx="${idx}"><td><button type="button" class="hafiza-q-btn" data-q="${esc(String(
            x.soru
          ))}">${esc(String(x.soru))}</button></td><td>${esc(String(x.cevap))}</td></tr>`
      )
      .join("");
    el.hafizaListView.innerHTML = `<table class="hafiza-table"><thead><tr><th>Soru</th><th>Cevap</th></tr></thead><tbody>${body}</tbody></table>`;
    wireHafizaAnalyzeTableInteractions();
  } catch (e) {
    console.error("[HAFIZA] Liste yükleme hatası:", e);
    // API okuma hatasında bile analiz satırlarını kaybetme.
    const localRows = hafizaAnalyzeRows.map(
      (x, idx) =>
        `<tr data-idx="${idx}"><td><button type="button" class="hafiza-q-btn" data-q="${esc(
          String(x.soru)
        )}">${esc(String(x.soru))}</button></td><td>${esc(String(x.cevap))}</td></tr>`
    );
    if (localRows.length) {
      el.hafizaListView.innerHTML = `<table class="hafiza-table"><thead><tr><th>Soru</th><th>Cevap</th></tr></thead><tbody>${localRows.join(
        ""
      )}</tbody></table>`;
      wireHafizaAnalyzeTableInteractions();
      return;
    }
    el.hafizaListView.innerHTML = '<div class="mini-card">Veri okunamadı.</div>';
  }
}

async function updateTable() {
  // Manuel tazeleme garantisi: clear -> dosyayı tekrar oku -> tabloya bas.
  if (el.hafizaListView) el.hafizaListView.innerHTML = "";
  await loadHafizaJsonView();
}

function getHafizaEditorText() {
  const n = el.hafizaInput;
  if (!n) return "";
  if (n.tagName === "TEXTAREA") return String(n.value || "");
  return String(n.innerText ?? n.textContent ?? "").replace(/\u00a0/g, " ");
}

function clearHafizaEditor() {
  const n = el.hafizaInput;
  if (!n) return;
  if (n.tagName === "TEXTAREA") n.value = "";
  else {
    n.textContent = "";
    n.classList.add("is-empty");
  }
}

function syncHafizaEditorEmptyClass() {
  const n = el.hafizaInput;
  if (!n || n.tagName === "TEXTAREA") return;
  const t = getHafizaEditorText().replace(/\s/g, "").length;
  n.classList.toggle("is-empty", !t);
}

/** Editörden gelen metni katı biçimde `soru = cevap` satırlarına çevirir. */
function parseHafizaEditorEntries(rawText) {
  const out = [];
  const src = String(rawText || "").replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const lines = src.split("\n");
  for (const line of lines) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const normalized = t.replace(/＝/g, "=");
    const idx = normalized.indexOf("=");
    if (idx <= 0) continue;
    const soru = normalized.slice(0, idx).trim();
    const cevap = normalized.slice(idx + 1).trim();
    if (!soru || !cevap) continue;
    out.push({ soru, cevap });
  }
  return out;
}

async function fetchHafizaImportBlok(raw) {
  // Önce yeni endpoint, olmazsa eski endpoint'e düş.
  try {
    const rr = await fetch(`${API}/api/hafiza/import-blok`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ raw }),
    });
    const jj = await rr.json();
    if (rr.ok && jj.ok) {
      return {
        added: Number(jj.added || 0),
        items: Array.isArray(jj.items) ? jj.items : [],
      };
    }
  } catch (_) {
    /* fallback */
  }

  // Eski sunucu sürümleri için arsiv/add: önce `soru = cevap` ham metin dene.
  const rr2 = await fetch(`${API}/api/hafiza/arsiv/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw }),
  });
  const jj2 = await rr2.json();
  if (rr2.ok && jj2.ok) {
    return {
      added: Number(jj2.added || 0),
      items: [],
    };
  }

  // Daha da eski parser sürümü: `Soru:\nCevap:` blok formatı.
  const legacyRows = String(raw || "")
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean)
    .map((line) => {
      const i = line.indexOf("=");
      if (i <= 0) return null;
      const q = line.slice(0, i).trim();
      const a = line.slice(i + 1).trim();
      if (!q || !a) return null;
      return `Soru: ${q}\nCevap: ${a}`;
    })
    .filter(Boolean)
    .join("\n\n");

  const rr3 = await fetch(`${API}/api/hafiza/arsiv/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw: legacyRows }),
  });
  const jj3 = await rr3.json();
  if (!rr3.ok || !jj3.ok) {
    throw new Error(jj3.detail || jj2.detail || "İçe aktarma başarısız");
  }
  return {
    added: Number(jj3.added || 0),
    items: [],
  };
}

function flashRuzgarDurum(mesaj, ms = 3200) {
  setStatus(mesaj, "Rüzgar");
  window.setTimeout(() => setStatus("Hazır", "Rüzgar"), ms);
}

/** Analiz tablosuna düşecek soru/cevap: metni ilk `=` işaretinden böler. */
function hafizaAnalizSoruCevap(raw, motorYanit) {
  const t = String(raw || "").trim();
  const eq = t.indexOf("=");
  if (eq === -1) {
    return { soru: t, cevap: motorYanit };
  }
  const soru = t.slice(0, eq).trim();
  const cevap = t.slice(eq + 1).trim();
  if (soru && cevap) {
    return { soru, cevap };
  }
  return { soru: t, cevap: motorYanit };
}

async function sendToHafizaAnalyze() {
  // Akış: Editör metni → SADECE analiz tablosuna eklenir.
  // Kalıcı `ruzgar_genel_hafiza.json` yazımı yalnızca "Hafızaya Al" tuşunda yapılır.
  const rawT = getHafizaEditorText();
  const raw = rawT.replace(/\u00a0/g, " ").trim();
  if (!raw) return;
  const entries = parseHafizaEditorEntries(raw);
  if (!entries.length) {
    flashRuzgarDurum("Lütfen yalnızca `Soru = Cevap` formatında giriş yapın.");
    return;
  }
  entries
    .slice()
    .reverse()
    .forEach((it) => {
      hafizaAnalyzeRows.unshift({
        soru: String(it.soru || ""),
        cevap: String(it.cevap || ""),
      });
    });
  renderAnalyzeRowsImmediate();
  clearHafizaEditor();
  flashRuzgarDurum(
    `${entries.length} satır analiz tablosuna eklendi — kaydetmek için "Hafızaya Al"a basın.`
  );
}

function renderAnalyzeRowsImmediate() {
  if (!el.hafizaListView) return;
  const rows = hafizaAnalyzeRows.map(
    (x, idx) =>
      `<tr data-idx="${idx}"><td><button type="button" class="hafiza-q-btn" data-q="${esc(
        String(x.soru)
      )}">${esc(String(x.soru))}</button></td><td>${esc(String(x.cevap))}</td></tr>`
  );
  if (!rows.length) return;
  el.hafizaListView.innerHTML = `<table class="hafiza-table"><thead><tr><th>Soru</th><th>Cevap</th></tr></thead><tbody>${rows.join(
    ""
  )}</tbody></table>`;
  wireHafizaAnalyzeTableInteractions();
}

function prependAnalyzeRowImmediate(soru, cevap) {
  if (!el.hafizaListView) return;
  const safeQ = esc(String(soru || ""));
  const safeA = esc(String(cevap || ""));
  const existingTable = el.hafizaListView.querySelector("table.hafiza-table");
  if (!existingTable) {
    el.hafizaListView.innerHTML =
      `<table class="hafiza-table"><thead><tr><th>Soru</th><th>Cevap</th></tr></thead><tbody>` +
      `<tr><td><button type="button" class="hafiza-q-btn" data-q="${safeQ}">${safeQ}</button></td><td>${safeA}</td></tr>` +
      `</tbody></table>`;
    return;
  }
  const tbody = existingTable.querySelector("tbody");
  if (!tbody) return;
  const tr = document.createElement("tr");
  tr.innerHTML = `<td><button type="button" class="hafiza-q-btn" data-q="${safeQ}">${safeQ}</button></td><td>${safeA}</td>`;
  tbody.prepend(tr);
}

function collectAnalyzeRowsFromDom() {
  if (!el.hafizaListView) return [];
  const rows = [];
  const trs = el.hafizaListView.querySelectorAll("tbody tr");
  trs.forEach((tr) => {
    const btn = tr.querySelector(".hafiza-q-btn");
    const q = String(btn?.textContent || "").trim();
    const tds = tr.querySelectorAll("td");
    const a = String(tds?.[1]?.textContent || "").trim();
    if (q && a) rows.push({ soru: q, cevap: a });
  });
  return rows;
}

async function saveHafizaAnalyzeRows() {
  let rowsToSave = Array.isArray(hafizaAnalyzeRows) ? [...hafizaAnalyzeRows] : [];
  if (!rowsToSave.length) {
    rowsToSave = collectAnalyzeRowsFromDom();
  }
  if (!rowsToSave.length) {
    flashRuzgarDurum("Kaydedilecek analiz satırı bulunamadı.");
    return;
  }
  try {
    const raw = rowsToSave
      .map((x) => `${x.soru} = ${x.cevap}`)
      .join("\n");
    const imp = await fetchHafizaImportBlok(raw);
    const eklenen = Number(imp?.added || rowsToSave.length);
    hafizaAnalyzeRows = [];
    await updateTable();
    void eklenen;
    const okText = "hafızama aldım";
    appendBubble("assistant", okText);
    flashRuzgarDurum(okText);
    try {
      speakTextImmediate(okText);
    } catch (_) {
      /* sessiz geç */
    }
  } catch (e) {
    console.error("Hafıza kaydedilemedi:", e);
    setStatus("Hafıza kaydedilemedi", "Rüzgar");
  }
}

async function initialLoadHafiza() {
  try {
    await updateTable();
    console.log("[HAFIZA] initial_load tamamlandı.");
  } catch (e) {
    console.error("[HAFIZA] initial_load hatası:", e);
  }
}

async function loadIlimFileList() {
  if (!el.ilimFileList) return;
  try {
    const items = await window.ruzgarApi.listDir("ilim-assistant/arsiv");
    el.ilimFileList.innerHTML = "";
    for (const it of items) {
      const row = document.createElement("div");
      row.className = `tree-item ${it.isDir ? "folder" : "file"}`;
      row.textContent = (it.isDir ? "▸ " : "· ") + it.name;
      if (!it.isDir) {
        row.style.cursor = "pointer";
        row.addEventListener("click", async () => {
          if (!el.ilimFileContent) return;
          try {
            const rr = await fetch(
              `${API}/api/workspace/read-text?rel=${encodeURIComponent(it.rel)}`
            );
            const jj = await rr.json();
            el.ilimFileContent.value = jj.text || "(okunamadı)";
          } catch {
            el.ilimFileContent.value = "(okunamadı)";
          }
        });
      }
      el.ilimFileList.appendChild(row);
    }
  } catch {
    el.ilimFileList.innerHTML = "(kütüphane okunamadı)";
  }
}

async function checkApi() {
  try {
    const r = await fetch(`${API}/api/health`, { method: "GET" });
    const j = await r.json();
    if (j.ok) {
      el.api.textContent = j.stt ? "API ✓ STT" : "API ✓";
      el.api.title = j.stt
        ? "desktop_server — STT: Whisper ve/veya SpeechRecognition (Ümit & Gökçenur dinleme)"
        : "API açık — pip install faster-whisper ve/veya SpeechRecognition";
      el.api.className = "tech-chip ok";
      setStatus("Hazır", "Rüzgar");
      void tryShowHafizaReminder();
      return true;
    }
  } catch {
    el.api.textContent = "API kapalı";
    el.api.className = "tech-chip err";
    el.api.title = "";
    setStatus("Önce desktop_server.py çalıştır", "Rüzgar");
  }
  return false;
}

const LS_HAFIZA_REMINDER_SESSION = "ruzgar_hafiza_reminder_gone";

/** Kuvve-i Hafıza — açılış hatırlatması (Ümit & Gökçenur) */
async function tryShowHafizaReminder() {
  const bar = el.hafizaReminder;
  const txt = el.hafizaReminderText;
  if (!bar || !txt) return;
  try {
    if (sessionStorage.getItem(LS_HAFIZA_REMINDER_SESSION) === "1") return;
  } catch (_) {
    /* ignore */
  }
  try {
    const r = await fetch(`${API}/api/hafiza/reminder`);
    if (!r.ok) return;
    const j = await r.json();
    const t = (j.text || "").trim();
    if (!t) return;
    txt.textContent = t;
    bar.hidden = false;
    bar.removeAttribute("aria-hidden");
  } catch (_) {
    /* Eski sunucuda endpoint yok */
  }
}

function dismissHafizaReminderBar() {
  if (!el.hafizaReminder) return;
  try {
    sessionStorage.setItem(LS_HAFIZA_REMINDER_SESSION, "1");
  } catch (_) {
    /* ignore */
  }
  el.hafizaReminder.hidden = true;
  el.hafizaReminder.setAttribute("aria-hidden", "true");
}

function openHafizaYonetModal() {
  if (!el.hafizaYonetOverlay) return;
  el.hafizaYonetOverlay.hidden = false;
  el.hafizaYonetOverlay.removeAttribute("aria-hidden");
  void refreshHafizaListUi();
}

function closeHafizaYonetModal() {
  if (!el.hafizaYonetOverlay) return;
  el.hafizaYonetOverlay.hidden = true;
  el.hafizaYonetOverlay.setAttribute("aria-hidden", "true");
}

async function refreshHafizaListUi() {
  const list = el.hafizaList;
  const empty = el.hafizaListEmpty;
  if (!list) return;
  list.innerHTML = "";
  try {
    const r = await fetch(`${API}/api/hafiza/sohbet?limit=120`);
    const j = await r.json();
    const rows = j.rows || [];
    if (empty) empty.hidden = rows.length > 0;
    if (!rows.length) return;
    for (const row of rows) {
      const wrap = document.createElement("div");
      wrap.className =
        "hafiza-row" + (row.altin ? " hafiza-row-altin" : "");
      const preview = String(row.content || "");
      const short =
        preview.length > 360 ? `${preview.slice(0, 360)}…` : preview;
      const roleLab =
        row.role === "user" ? "Siz" : row.role === "assistant" ? "Rüzgar" : row.role;
      wrap.innerHTML = `
        <div class="hafiza-row-meta">
          <span class="hafiza-role">${esc(roleLab)}</span>
          <span class="hafiza-ts">${esc(row.ts || "")}</span>
          ${
            row.altin
              ? '<span class="hafiza-gold-badge" title="Altın hatırlat">Altın</span>'
              : ""
          }
        </div>
        <div class="hafiza-row-text">${esc(short)}</div>
        <div class="hafiza-row-actions">
          <button type="button" class="btn-secondary btn-compact btn-hafiza-sil" data-id="${row.id}">Sil</button>
          <button type="button" class="btn-secondary btn-compact btn-hafiza-altin" data-id="${row.id}" data-altin="${row.altin ? "1" : "0"}">${
        row.altin ? "Altını kaldır" : "Altınla"
      }</button>
        </div>`;
      list.appendChild(wrap);
    }
    list.querySelectorAll(".btn-hafiza-sil").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = Number(btn.getAttribute("data-id"));
        if (!Number.isFinite(id)) return;
        try {
          const rr = await fetch(`${API}/api/hafiza/sohbet/${id}`, {
            method: "DELETE",
          });
          if (rr.ok) {
            setStatus("Hafızadan silindi", "Rüzgar");
            void refreshHafizaListUi();
          } else setStatus("Silinemedi", "Rüzgar");
        } catch {
          setStatus("API hatası", "Rüzgar");
        }
      });
    });
    list.querySelectorAll(".btn-hafiza-altin").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const id = Number(btn.getAttribute("data-id"));
        const isGold = btn.getAttribute("data-altin") === "1";
        if (!Number.isFinite(id)) return;
        try {
          const rr = await fetch(`${API}/api/hafiza/sohbet/${id}/altin`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ altin: !isGold }),
          });
          if (rr.ok) {
            setStatus(isGold ? "Altın kaldırıldı" : "Altın — kalıcı hatırlat", "Rüzgar");
            void refreshHafizaListUi();
          } else setStatus("İşlem başarısız", "Rüzgar");
        } catch {
          setStatus("API hatası", "Rüzgar");
        }
      });
    });
  } catch {
    list.innerHTML =
      '<p class="hafiza-help">Liste alınamadı — sunucuyu güncelleyin.</p>';
    if (empty) empty.hidden = true;
  }
}

function openKisiselPanelModal() {
  if (!el.kisiselOverlay) return;
  el.kisiselOverlay.hidden = false;
  el.kisiselOverlay.removeAttribute("aria-hidden");
  void (async () => {
    try {
      const r = await fetch(`${API}/api/hafiza/kisisel`);
      const j = await r.json();
      const d = j.data || {};
      if (el.kisiselUmit) el.kisiselUmit.value = d.umit_arastirma || "";
      if (el.kisiselGokcenur) el.kisiselGokcenur.value = d.gokcenur_eserler || "";
      if (el.kisiselNotlar) el.kisiselNotlar.value = d.notlar || "";
    } catch {
      setStatus("Kişisel panel okunamadı", "Rüzgar");
    }
  })();
}

function closeKisiselPanelModal() {
  if (!el.kisiselOverlay) return;
  el.kisiselOverlay.hidden = true;
  el.kisiselOverlay.setAttribute("aria-hidden", "true");
}

async function saveKisiselPanel() {
  const body = {
    umit_arastirma: el.kisiselUmit ? el.kisiselUmit.value : "",
    gokcenur_eserler: el.kisiselGokcenur ? el.kisiselGokcenur.value : "",
    notlar: el.kisiselNotlar ? el.kisiselNotlar.value : "",
  };
  try {
    const r = await fetch(`${API}/api/hafiza/kisisel`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (r.ok) {
      setStatus("Kişisel veri kaydedildi — Kuvve-i Hafıza", "Rüzgar");
      closeKisiselPanelModal();
    } else setStatus("Kaydedilemedi", "Rüzgar");
  } catch {
    setStatus("API yok — kayıt atlanamadı", "Rüzgar");
  }
}

function wireKuvveHafizaUi() {
  if (el.btnHafizaReminderKapat) {
    el.btnHafizaReminderKapat.addEventListener("click", () =>
      dismissHafizaReminderBar()
    );
  }
  if (el.btnHafizaYonet) {
    el.btnHafizaYonet.addEventListener("click", () => {
      openHafizaYonetModal();
      setStatus("Hafızayı Yönet — Ümit & Gökçenur", "Rüzgar");
    });
  }
  if (el.btnKisiselPanel) {
    el.btnKisiselPanel.addEventListener("click", () => {
      openKisiselPanelModal();
      setStatus("Kişisel veri paneli", "Rüzgar");
    });
  }
  if (el.btnHafizaYonetKapat) {
    el.btnHafizaYonetKapat.addEventListener("click", () =>
      closeHafizaYonetModal()
    );
  }
  if (el.btnHafizaYonetRefresh) {
    el.btnHafizaYonetRefresh.addEventListener("click", () =>
      void refreshHafizaListUi()
    );
  }
  if (el.hafizaYonetOverlay) {
    el.hafizaYonetOverlay.addEventListener("click", (e) => {
      if (e.target === el.hafizaYonetOverlay) closeHafizaYonetModal();
    });
  }
  if (el.btnKisiselKaydet) {
    el.btnKisiselKaydet.addEventListener("click", () => void saveKisiselPanel());
  }
  if (el.btnKisiselIptal) {
    el.btnKisiselIptal.addEventListener("click", () => closeKisiselPanelModal());
  }
  if (el.kisiselOverlay) {
    el.kisiselOverlay.addEventListener("click", (e) => {
      if (e.target === el.kisiselOverlay) closeKisiselPanelModal();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (el.hafizaYonetOverlay && !el.hafizaYonetOverlay.hidden) {
      closeHafizaYonetModal();
      return;
    }
    if (el.kisiselOverlay && !el.kisiselOverlay.hidden) {
      closeKisiselPanelModal();
    }
  });
}

wireKuvveHafizaUi();
wireTopModeButtons();
wireDynamicWorkbench();
wireContextMenu();
updateDynamicWorkbench();
void initialLoadHafiza();

/** Dinamit — görsel sürükle-bırak + hatırlatıcı poll (Ümit & Gökçenur) */
function wireDinamitFeatures() {
  const panel = document.querySelector(".panel-chat");
  if (panel) {
    panel.addEventListener("dragover", (e) => {
      e.preventDefault();
      try {
        e.dataTransfer.dropEffect = "copy";
      } catch (_) {
        /* ignore */
      }
    });
    panel.addEventListener("drop", async (e) => {
      e.preventDefault();
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!f || !String(f.type || "").startsWith("image/")) {
        setStatus("Yalnızca görüntü dosyası (Dinamit)", "Rüzgar");
        return;
      }
      const fd = new FormData();
      fd.append("file", f, f.name || "ruzgar.png");
      setStatus("Görsel analiz (PIL/OpenCV)…", "Rüzgar");
      try {
        const r = await fetch(`${API}/api/vision/analyze`, {
          method: "POST",
          body: fd,
        });
        const j = await r.json();
        const s =
          (j && (j.summary || j.text)) ||
          (typeof j === "string" ? j : "");
        if (s) {
          appendBubble("assistant", s);
          const cur = el.input.value.trim();
          el.input.value = cur ? `${cur}\n\n${s}` : s;
        }
        setStatus("Hazır", "Rüzgar");
      } catch {
        setStatus("Görsel API hatası", "Rüzgar");
      }
    });
  }
  window.setInterval(() => {
    void (async () => {
      try {
        const r = await fetch(`${API}/api/reminders/pending`);
        if (!r.ok) return;
        const j = await r.json();
        const items = j.items || [];
        for (const it of items) {
          const line = `Mimar, hatırlatma — ${it.mesaj} (Dinamit — Ümit & Gökçenur)`;
          appendBubble("assistant", line);
          lastAssistantReply = line;
          try {
            await fetch(`${API}/api/reminders/ack`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ id: it.id }),
            });
          } catch (_) {
            /* ignore */
          }
          lastVoiceEmotion = "ciddi";
          window.setTimeout(() => void speakLast(), 500);
        }
      } catch (_) {
        /* API yok */
      }
    })();
  }, 24000);
}

wireDinamitFeatures();

function normalizeKarakterForTts(k) {
  const s = String(k || "")
    .toLowerCase()
    .trim();
  if (s === "bilge" || s === "kari") return "alim";
  if (s === "sair") return "edip";
  if (s === "alim" || s === "edip" || s === "asistan") return s;
  return "asistan";
}

function ttsPlainForSpeech(t) {
  return String(t)
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/^#+\s*/gm, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * İlk cümle / erken kesit — seslendirme metin tamamlanmadan başlasın (Ümit & Gökçenur).
 */
function takeFirstTtsSentence(s) {
  const t = String(s);
  if (!t.trim()) return null;
  const m = t.match(/^([\s\S]+?)([.!?…])(\s+|$)/);
  if (m && m[0]) {
    const head = (m[1] + m[2]).trim();
    const rest = t.slice(m[0].length);
    if (head.length >= 3) return { head, rest };
  }
  if (t.length >= 32) {
    const cut = t.lastIndexOf(" ", 34);
    if (cut > 10) {
      return {
        head: t.slice(0, cut).trim(),
        rest: t.slice(cut + 1),
      };
    }
  }
  if (t.length >= 420) {
    const cut = t.lastIndexOf(" ", 420);
    if (cut > 50) return { head: t.slice(0, cut).trim(), rest: t.slice(cut) };
  }
  return null;
}

function bumpTtsSession() {
  ttsSessionCounter += 1;
  ttsPendingChunks = "";
  ttsTextQueue.length = 0;
  ttsPumping = false;
  ttsEdgeSpokeTurn = false;
  try {
    if (ttsAbortController) ttsAbortController.abort();
  } catch (_) {
    /* yok say */
  }
  ttsAbortController = null;
  try {
    if (ttsPlayingEl) {
      ttsPlayingEl.pause();
      ttsPlayingEl.removeAttribute("src");
      ttsPlayingEl = null;
    }
  } catch (_) {
    /* yok say */
  }
  syncInterruptButton();
  return ttsSessionCounter;
}

/** Ses yankısını azaltmak: çalma öncesi kısa tampon ve parçalar arası nefes (CPU yükünde daha temiz çıkış). */
const RUZGAR_TTS_PLAY_PREROLL_MS = 420;
const RUZGAR_TTS_CHUNK_GAP_MS = 520;

function playTtsBlob(blob) {
  return new Promise((resolve) => {
    try {
      const url = URL.createObjectURL(blob);
      const a = new Audio();
      ttsPlayingEl = a;
      a.src = url;
      a.preload = "auto";
      a.onended = () => {
        try {
          URL.revokeObjectURL(url);
        } catch (_) {
          /* yok say */
        }
        ttsPlayingEl = null;
        syncInterruptButton();
        resolve();
      };
      a.onerror = () => {
        try {
          URL.revokeObjectURL(url);
        } catch (_) {
          /* yok say */
        }
        ttsPlayingEl = null;
        syncInterruptButton();
        resolve();
      };
      window.setTimeout(() => {
        try {
          if (ttsPlayingEl !== a) {
            try {
              URL.revokeObjectURL(url);
            } catch (_) {
              /* yok say */
            }
            resolve();
            return;
          }
          void a.play();
        } catch (_) {
          try {
            URL.revokeObjectURL(url);
          } catch (_2) {
            /* yok say */
          }
          resolve();
        }
      }, RUZGAR_TTS_PLAY_PREROLL_MS);
      setStatus("Sesli okuma…");
      syncInterruptButton();
    } catch (_) {
      resolve();
    }
  });
}

/**
 * Edge-TTS kuyruğu — Hızlı Yanıt Kuyruğu (Işık Hızı): ilk cümle hemen sentezlenir,
 * kuyruk dolarken sonraki MP3 prefetch ile hazırlanır; tam yanıtı beklemeden çalma başlar.
 * Ümit & Gökçenur performans hattı.
 */
async function runTtsPump(ttsSess, karakter, signal) {
  if (ttsPumping) return;
  ttsPumping = true;
  try {
    /** @type {Promise<Blob | null> | null} */
    let prefetch = null;

    const synthOne = async (chunk) => {
      const k = normalizeKarakterForTts(karakter);
      try {
        const b = await synthEdgeMp3ViaWorker(
          API,
          chunk,
          k,
          signal,
          lastVoiceEmotion
        );
        if (ttsSess !== ttsSessionCounter) return null;
        return b;
      } catch (wErr) {
        if (wErr && wErr.name === "AbortError") throw wErr;
        const res = await fetch(`${API}/api/tts`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text: chunk,
            karakter: k,
            backend: "edge",
            ...(lastVoiceEmotion && lastVoiceEmotion !== "notr"
              ? { emotion: lastVoiceEmotion }
              : {}),
          }),
          signal,
        });
        if (!res.ok || ttsSess !== ttsSessionCounter) return null;
        return res.blob();
      }
    };

    const fillPrefetch = () => {
      if (prefetch != null) return;
      while (ttsTextQueue.length > 0) {
        const raw = ttsTextQueue.shift();
        const chunk = ttsPlainForSpeech(raw);
        if (!chunk || chunk.length < 2) continue;
        prefetch = synthOne(chunk);
        return;
      }
    };

    fillPrefetch();
    while (ttsSess === ttsSessionCounter && prefetch != null) {
      const blob = await prefetch;
      prefetch = null;
      fillPrefetch();
      if (!blob || blob.size <= 80) continue;
      ttsEdgeSpokeTurn = true;
      await playTtsBlob(blob);
      await new Promise((r) =>
        window.setTimeout(r, RUZGAR_TTS_CHUNK_GAP_MS)
      );
    }
  } catch (_) {
    /* iptal veya ağ */
  } finally {
    ttsPumping = false;
    syncInterruptButton();
  }
}

async function waitTtsIdle(ttsSess) {
  for (let i = 0; i < 2400; i++) {
    if (ttsSess !== ttsSessionCounter) return;
    if (!ttsPumping && ttsTextQueue.length === 0) return;
    await new Promise((r) => setTimeout(r, 40));
  }
}

/**
 * Ollama/OpenAI/LM Studio — Işık Hızı: önce WebSocket (/ws/chat), olmazsa SSE fallback.
 * Düşünme balonu + anlık token (Ümit & Gökçenur).
 */
async function streamChat(userText) {
  bumpTtsSession();
  const ttsSess = ttsSessionCounter;
  ttsAbortController = new AbortController();

  let workspaceRoot = null;
  try {
    if (window.ruzgarApi?.getRoot) {
      workspaceRoot = await window.ruzgarApi.getRoot();
    }
  } catch {
    workspaceRoot = null;
  }

  let sesVoice = "asistan";
  const wantEdge =
    el.voiceOut != null &&
    el.voiceOut.checked &&
    typeof fetch !== "undefined";
  if (wantEdge) {
    try {
      const rs = await fetch(`${API}/api/ses/settings`);
      if (rs.ok) {
        const j = await rs.json();
        sesVoice = normalizeKarakterForTts(j.karakter);
      }
    } catch (_) {
      /* API yok */
    }
  }

  const body = {
    message: userText,
    history: chatHistory,
    use_web: el.web ? !!el.web.checked : !["ses", "okuma", "hafiza", "hizli"].includes(currentMode),
    read_message_links:
      el.linkRead == null ? true : !!el.linkRead.checked,
    fetch_pages: Number.parseInt(String(el.fetchN?.value ?? "0"), 10) || 0,
    coding_mode: el.code ? !!el.code.checked : currentMode === "programlama",
    session_wake_used: sessionWakeUsed,
    mode: currentMode,
    workspace_root: workspaceRoot || undefined,
    autonom_research: !!(el.optAutonom && el.optAutonom.checked),
  };

  const dec = new TextDecoder("utf-8");
  let buf = "";
  let full = "";
  let responseBubble = null;

  function ensureReplyBubble() {
    if (responseBubble) return;
    hideThinkingCenter();
    responseBubble = document.createElement("div");
    responseBubble.className = "bubble assistant";
    el.chat.appendChild(responseBubble);
  }

  /** Genel hafıza anında cevaplarda gereksiz "düşünüyor"; SSE gelene kadar ertelenir. */
  const RUZGAR_DEFER_THINKING_MS = 175;
  let deferThinkingUntil = null;
  function clearDeferThinking() {
    if (deferThinkingUntil != null) {
      window.clearTimeout(deferThinkingUntil);
      deferThinkingUntil = null;
    }
  }
  function scheduleDeferThinkingOverlay() {
    clearDeferThinking();
    if (currentMode === "hafiza") return;
    deferThinkingUntil = window.setTimeout(() => {
      deferThinkingUntil = null;
      showThinkingCenter(null);
    }, RUZGAR_DEFER_THINKING_MS);
  }

  /** Token/done/error/status — zorunlu akış + hazırlık durumu (Ümit & Gökçenur Işık Hızı). */
  function processChatEvent(ev) {
    if (ev.type === "meta" && ev.instant_memory) {
      clearDeferThinking();
      hideThinkingCenter();
      return;
    }
    clearDeferThinking();
    if (ev.type === "status") {
      const t = (ev.text || "").trim();
      if (t) {
        showThinkingCenter(t);
        setStatus(t, "Rüzgar");
      } else {
        showThinkingCenter(null);
      }
      return;
    }
    if (ev.type === "token" && ev.text) {
      hideThinkingCenter();
      ensureReplyBubble();
      full += ev.text;
      responseBubble.innerHTML = esc(repairMojibake(full));
      el.chat.scrollTop = el.chat.scrollHeight;
      setStatus("Yazıyor…");
      if (
        wantEdge &&
        ttsSess === ttsSessionCounter &&
        ttsAbortController
      ) {
        ttsPendingChunks += ev.text;
        while (ttsSess === ttsSessionCounter) {
          const sp = takeFirstTtsSentence(ttsPendingChunks);
          if (!sp) break;
          ttsPendingChunks = sp.rest;
          ttsTextQueue.push(sp.head);
          queueMicrotask(() => {
            void runTtsPump(
              ttsSess,
              sesVoice,
              ttsAbortController.signal
            );
          });
        }
      }
    } else if (ev.type === "done") {
      const streamed = repairMojibake(full);
      const srv = repairMojibake(ev.full_reply || "");
      let merged = srv || streamed;
      if (looksLikeMojibake(srv) && streamed.length > 0 && !looksLikeMojibake(streamed)) {
        merged = streamed + extractYerelFooter(srv);
      }
      full = stripYerelFooter(merged);
      sessionWakeUsed = !!ev.new_wake_used;
      hideThinkingCenter();
      if (!responseBubble) {
        responseBubble = document.createElement("div");
        responseBubble.className = "bubble assistant";
        el.chat.appendChild(responseBubble);
      }
      responseBubble.innerHTML = esc(full);
      lastAssistantReply = full;
      updateDynamicWorkbench();
      chatHistory.push({ role: "user", content: ev.user_message || userText });
      chatHistory.push({ role: "assistant", content: full });
      setStatus("Hazır");
      if (wantEdge && ttsSess === ttsSessionCounter && ttsAbortController) {
        const tail = ttsPlainForSpeech(ttsPendingChunks);
        ttsPendingChunks = "";
        if (tail.length >= 2) {
          ttsTextQueue.push(tail);
          queueMicrotask(() => {
            void runTtsPump(
              ttsSess,
              sesVoice,
              ttsAbortController.signal
            );
          });
        }
        void waitTtsIdle(ttsSess);
      }
      if (el.voiceOut == null || el.voiceOut.checked) {
        if (currentMode === "hafiza") {
          speakTextImmediate(full);
        } else if (!wantEdge || !ttsEdgeSpokeTurn) {
          window.setTimeout(() => void speakLast(), 80);
        }
      }
      if (chatHistory.length > MAX_CLIENT_HISTORY_MSGS) {
        chatHistory = chatHistory.slice(-MAX_CLIENT_HISTORY_MSGS);
      }
      window.setTimeout(() => {
        lastVoiceEmotion = null;
      }, 90000);
    } else if (ev.type === "error") {
      hideThinkingCenter();
      ensureReplyBubble();
      responseBubble.innerHTML = esc(ev.text || "Hata");
      setStatus("Hata");
    }
  }

  function handleSseJson(jsonStr) {
    try {
      processChatEvent(JSON.parse(jsonStr));
    } catch {
      /* kesik JSON */
    }
  }

  const streamViaWebSocket = () =>
    new Promise((resolve, reject) => {
      const wsBase = apiToWsBase(API);
      const ws = new WebSocket(`${wsBase}/ws/chat`);
      const tid = window.setTimeout(() => {
        try {
          ws.close();
        } catch (_) {
          /* ignore */
        }
        reject(new Error("ws-open-timeout"));
      }, RUZGAR_WS_OPEN_WAIT_MS);
      ws.onopen = () => {
        clearTimeout(tid);
        activeChatWs = ws;
        try {
          ws.send(JSON.stringify(body));
        } catch (e) {
          reject(e);
          return;
        }
        const onAbort = () => {
          try {
            ws.close();
          } catch (_) {
            /* ignore */
          }
          const err = new Error("aborted");
          err.name = "AbortError";
          reject(err);
        };
        streamCtrl.signal.addEventListener("abort", onAbort);
        ws.onmessage = (e) => {
          try {
            const ev = JSON.parse(e.data);
            processChatEvent(ev);
            if (ev.type === "done" || ev.type === "error") {
              streamCtrl.signal.removeEventListener("abort", onAbort);
              try {
                ws.close();
              } catch (_) {
                /* ignore */
              }
              resolve();
            }
          } catch (_) {
            /* tek çerçeve */
          }
        };
        ws.onerror = () => {
          clearTimeout(tid);
          streamCtrl.signal.removeEventListener("abort", onAbort);
          reject(new Error("ws-error"));
        };
      };
      ws.onerror = () => {
        clearTimeout(tid);
        reject(new Error("ws-connect-error"));
      };
    });

  try {
    const gr = await fetch(`${API}/api/hafiza/genel-bak`, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify({ message: userText }),
      cache: "no-store",
    });
    if (gr.ok) {
      const gj = await gr.json();
      if (gj && gj.hit === true && gj.answer) {
        const txt = repairMojibake(String(gj.answer));
        const nw =
          sessionWakeUsed ||
          /\br[uü]zgar\b/i.test(userText) ||
          /\bruzgar\b/i.test(userText);
        hideThinkingCenter();
        clearDeferThinking();
        processChatEvent({ type: "token", text: txt });
        processChatEvent({
          type: "done",
          full_reply: txt,
          user_message: userText,
          new_wake_used: nw,
        });
        activeChatAbort = null;
        activeChatWs = null;
        syncInterruptButton();
        return;
      }
    }
  } catch (_) {
    /* Köprü yoksa normal akış */
  }

  const streamCtrl = new AbortController();
  activeChatAbort = streamCtrl;
  activeChatWs = null;
  let timedOutAbort = false;
  /** Tarayıcı setTimeout üst sınırı (yaklaşık 24,8 gün) — MAX_SAFE_INTEGER hemen tetiklenebilir */
  const STREAM_ABORT_MAX_DELAY_MS = 2147483647;
  /** @type {ReturnType<typeof setTimeout> | null} */
  let streamDeadline = null;
  if (RUZGAR_CHAT_STREAM_HARD_CAP_MS > 0) {
    streamDeadline = window.setTimeout(
      () => {
        timedOutAbort = true;
        streamCtrl.abort();
      },
      Math.min(RUZGAR_CHAT_STREAM_HARD_CAP_MS, STREAM_ABORT_MAX_DELAY_MS),
    );
  }

  if (currentMode !== "hafiza") {
    scheduleDeferThinkingOverlay();
  }
  try {
    let usedHttp = false;
    if (ruzgarLikelyLocalDesktopApi()) {
      usedHttp = true;
    } else {
      try {
        await streamViaWebSocket();
      } catch (wsErr) {
        if (wsErr && wsErr.name === "AbortError") {
          throw wsErr;
        }
        usedHttp = true;
      }
    }
    if (usedHttp) {
    const res = await fetch(`${API}/api/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        Accept: "text/event-stream",
        "Accept-Charset": "utf-8",
        "X-Ruzgar-Buffer-Mode": "stream-aggressive",
        "X-Accel-Buffering": "no",
      },
      body: JSON.stringify(body),
      signal: streamCtrl.signal,
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const reader = res.body.getReader();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let nl;
      while ((nl = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, nl);
        buf = buf.slice(nl + 1);
        const trimmed = line.replace(/\r$/, "").trim();
        if (!trimmed.startsWith("data:")) continue;
        const payload = trimmed.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        handleSseJson(payload);
      }
    }
    const tailLine = buf.replace(/\r$/, "").trim();
    if (tailLine.startsWith("data:")) {
      const payload = tailLine.slice(5).trim();
      if (payload && payload !== "[DONE]") handleSseJson(payload);
    }
    }
  } catch (e) {
    hideThinkingCenter();
    if (userRequestedChatStop) {
      userRequestedChatStop = false;
      timedOutAbort = false;
      return;
    }
    if (e && e.name === "AbortError") {
      if (timedOutAbort) {
        timedOutAbort = false;
        throw new Error(
          RUZGAR_CHAT_STREAM_HARD_CAP_MS <= 0
            ? "Yanıt kesildi — istek iptali. Ümit & Gökçenur Connection Bridge."
            : `Yanıt zaman aşımı (${Math.round(
                RUZGAR_CHAT_STREAM_HARD_CAP_MS / 1000,
              )} sn) — Colab / Ollama / Köprü. Ümit & Gökçenur.`
        );
      }
      timedOutAbort = false;
      return;
    }
    timedOutAbort = false;
    throw e;
  } finally {
    if (streamDeadline != null) clearTimeout(streamDeadline);
    clearDeferThinking();
    hideThinkingCenter();
    activeChatAbort = null;
    activeChatWs = null;
    syncInterruptButton();
  }
}

/**
 * @param {{ skipUserBubble?: boolean }} opts Ses metni zaten gösterildiyse Yıldırım: çift balon yok.
 */
async function sendMessageWithText(t, opts = {}) {
  const skipUser = !!opts.skipUserBubble;
  const text = (t || "").trim();
  if (!text) return;
  silenceVoiceOutputNow();
  const ok = await checkApi();
  if (!ok) return;

  el.input.value = "";
  if (!skipUser) {
    appendBubble("user", text);
  }
  if (el.send) el.send.disabled = true;
  setStatus("İstek…", "Rüzgar");
  perfBusy = true;
  updatePerformanceIndicators(perfBusy);
  syncInterruptButton();

  try {
    await streamChat(text);
  } catch (e) {
    appendBubble("assistant", String(e));
    setStatus("Hata");
  } finally {
    if (el.send) el.send.disabled = false;
    perfBusy = false;
    updatePerformanceIndicators(perfBusy);
    syncInterruptButton();
  }
}

async function sendMessage() {
  const t = el.input.value.trim();
  if (!t) return;
  await sendMessageWithText(t);
}

/** Yerel STT: MediaRecorder → /api/stt (Whisper veya SpeechRecognition). Ümit & Gökçenur dinleme modülü. */
let recState = null;
/** Basılı tutunca kayıt */
let micPressed = false;
/** Bırakınca Konuşunca gönder */
let pushSessionSend = false;
/** ses → Mikrofon menü oturumu (zamanlayıcı iptali) */
let menuMicToken = 0;
/** getUserMedia + MediaRecorder asenkron başlarken pointerup yarışını çözer */
let micBootPromise = null;

/** Web Audio: giriş sinyali çubuğu (Ümit & Gökçenur dinleme göstergesi) */
let micLevelRaf = 0;
let micLevelCtx = null;
let micLevelSrc = null;
let micLevelAnalyser = null;

/** Yıldırım: sessizlikte kaydı kapat (ms) — Ümit & Gökçenur VAD */
const RUZGAR_SILENCE_END_MS = 800;
const RUZGAR_SILENCE_MIN_REC_MS = 1200;
let vadSilentMs = 0;
let silenceAutoStopBusy = false;

function stopMicLevelMeter() {
  if (micLevelRaf) {
    cancelAnimationFrame(micLevelRaf);
    micLevelRaf = 0;
  }
  try {
    micLevelSrc?.disconnect();
  } catch (_) {
    /* ignore */
  }
  micLevelSrc = null;
  try {
    micLevelAnalyser?.disconnect();
  } catch (_) {
    /* ignore */
  }
  micLevelAnalyser = null;
  try {
    if (micLevelCtx && micLevelCtx.state !== "closed") micLevelCtx.close();
  } catch (_) {
    /* ignore */
  }
  micLevelCtx = null;
  const wrap = el.micLevelWrap;
  const bar = el.micLevelBar;
  if (wrap) {
    wrap.hidden = true;
    wrap.setAttribute("aria-hidden", "true");
  }
  if (bar) bar.style.width = "4%";
  const pctEl = el.micLevelPct;
  if (pctEl) {
    pctEl.hidden = true;
    pctEl.setAttribute("aria-hidden", "true");
    pctEl.textContent = "—";
  }
  vadSilentMs = 0;
}

async function maybeEndRecordingOnSilence() {
  if (silenceAutoStopBusy) return;
  const s = recState;
  if (!s || (s.kind !== "btn" && s.kind !== "menu")) return;
  if (!s.startedAt || Date.now() - s.startedAt < RUZGAR_SILENCE_MIN_REC_MS) {
    return;
  }
  silenceAutoStopBusy = true;
  try {
    if (s.kind === "menu" && s.timer) {
      clearTimeout(s.timer);
      s.timer = null;
    }
    micPressed = false;
    const st = recState;
    recState = null;
    if (st) await finalizeRecording(st);
  } finally {
    silenceAutoStopBusy = false;
  }
}

/**
 * @param {MediaStream} stream
 */
function startMicLevelMeter(stream) {
  stopMicLevelMeter();
  const wrap = el.micLevelWrap;
  const bar = el.micLevelBar;
  if (!wrap || !bar || !stream) return;
  const Ctx = window.AudioContext || window.webkitAudioContext;
  if (!Ctx) return;

  wrap.hidden = false;
  wrap.removeAttribute("aria-hidden");

  micLevelCtx = new Ctx();
  micLevelSrc = micLevelCtx.createMediaStreamSource(stream);
  micLevelAnalyser = micLevelCtx.createAnalyser();
  micLevelAnalyser.fftSize = 256;
  micLevelAnalyser.smoothingTimeConstant = 0.65;
  micLevelSrc.connect(micLevelAnalyser);

  const data = new Uint8Array(micLevelAnalyser.frequencyBinCount);
  let micTestFrames = 0;

  function tick() {
    if (!micLevelAnalyser || !bar) return;
    micLevelAnalyser.getByteFrequencyData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i += 1) sum += data[i];
    const avg = data.length ? sum / data.length : 0;
    const pct = Math.min(100, Math.max(5, (avg / 72) * 100));
    lastMicEnergy01 = Math.min(1, Math.max(0, pct / 100));
    bar.style.width = `${pct}%`;
    if (recState && (recState.kind === "btn" || recState.kind === "menu")) {
      const quiet = avg < 8;
      if (quiet) vadSilentMs += 1000 / 58;
      else vadSilentMs = 0;
      if (
        vadSilentMs >= RUZGAR_SILENCE_END_MS &&
        recState.startedAt &&
        Date.now() - recState.startedAt >= RUZGAR_SILENCE_MIN_REC_MS
      ) {
        vadSilentMs = 0;
        void maybeEndRecordingOnSilence();
      }
    }
    const pctEl = el.micLevelPct;
    if (pctEl) {
      if (micMeterTestModeEnabled()) {
        pctEl.hidden = false;
        pctEl.removeAttribute("aria-hidden");
        pctEl.textContent = `${Math.round(pct)}%`;
        micTestFrames += 1;
        if (micTestFrames % 20 === 0) {
          console.log(
            "[RÜZGAR Mic test — Ümit & Gökçenur] seviye %",
            Math.round(pct)
          );
        }
      } else {
        pctEl.hidden = true;
        pctEl.setAttribute("aria-hidden", "true");
      }
    }
    micLevelRaf = requestAnimationFrame(tick);
  }

  if (micLevelCtx.state === "suspended") {
    void micLevelCtx.resume().catch(() => {});
  }
  micLevelRaf = requestAnimationFrame(tick);
}

function pickRecorderMime() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
  ];
  for (const m of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(m)) {
      return m;
    }
  }
  return "";
}

async function discardActiveRecording() {
  stopMicLevelMeter();
  const s = recState;
  if (!s) return;
  recState = null;
  if (s.timer) {
    clearTimeout(s.timer);
    s.timer = null;
  }
  try {
    if (s.recorder && s.recorder.state === "recording") {
      await new Promise((resolve) => {
        s.recorder.onstop = resolve;
        s.recorder.stop();
      });
    }
  } catch (_) {
    /* ignore */
  }
  try {
    s.stream?.getTracks()?.forEach((t) => t.stop());
  } catch (_) {
    /* ignore */
  }
  el.mic.classList.remove("recording");
  el.mic.classList.remove("listening");
}

function blobFromStoppedRecorder(state) {
  const { recorder, stream, chunks, mime } = state;
  return new Promise((resolve, reject) => {
    recorder.onstop = () => {
      try {
        stream.getTracks().forEach((t) => t.stop());
      } catch (_) {
        /* ignore */
      }
      resolve(new Blob(chunks, { type: mime || "audio/webm" }));
    };
    recorder.onerror = () => reject(new Error("MediaRecorder hatası"));
    try {
      if (recorder.state === "recording") recorder.stop();
      else {
        stream.getTracks().forEach((t) => t.stop());
        resolve(new Blob(chunks, { type: mime || "audio/webm" }));
      }
    } catch (err) {
      reject(err);
    }
  });
}

async function postSttBlob(blob) {
  const ext = blob.type.includes("ogg") ? "ogg" : "webm";
  const fd = new FormData();
  fd.append("file", blob, `ruzgar.${ext}`);
  try {
    fd.append("mic_energy", String(lastMicEnergy01));
  } catch (_) {
    /* ignore */
  }
  const r = await fetch(`${API}/api/stt?lang=tr`, {
    method: "POST",
    body: fd,
  });
  const raw = await r.text();
  if (!r.ok) {
    let detail = raw;
    try {
      const j = JSON.parse(raw);
      const d = j.detail;
      if (Array.isArray(d)) {
        detail = d.map((x) => (x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (d != null) {
        detail = String(d);
      }
    } catch (_) {
      /* raw string */
    }
    throw new Error(detail || r.statusText);
  }
  const j = JSON.parse(raw);
  return {
    text: typeof j.text === "string" ? j.text : "",
    emotion: typeof j.emotion === "string" ? j.emotion : "notr",
  };
}

async function finalizeRecording(state) {
  stopMicLevelMeter();
  if (state.timer) {
    clearTimeout(state.timer);
    state.timer = null;
  }
  el.mic.classList.remove("recording");
  el.mic.classList.remove("listening");
  setStatus("Metne çevriliyor…", "Rüzgar");
  let blob;
  try {
    blob = await blobFromStoppedRecorder(state);
  } catch (e) {
    el.mic.classList.remove("recording");
    el.mic.classList.remove("listening");
    setStatus(String(e && e.message ? e.message : e), "Rüzgar");
    pushSessionSend = false;
    return;
  }
  if (!blob || blob.size < 64) {
    el.mic.classList.remove("recording");
    el.mic.classList.remove("listening");
    setStatus("Ses kaydı çok kısa", "Rüzgar");
    pushSessionSend = false;
    return;
  }
  let text = "";
  let emo = "notr";
  try {
    const st = await postSttBlob(blob);
    text = st.text || "";
    emo = st.emotion || "notr";
    lastVoiceEmotion = emo !== "notr" ? emo : null;
  } catch (e) {
    el.mic.classList.remove("recording");
    el.mic.classList.remove("listening");
    setStatus("STT: " + (e && e.message ? e.message : e), "Rüzgar");
    pushSessionSend = false;
    return;
  }
  text = (text || "").trim();
  if (text) {
    const prev = el.input.value.trim();
    el.input.value = prev ? `${prev} ${text}`.trim() : text;
  }
  const chain = el.voiceSend == null || !!el.voiceSend.checked;
  const full = el.input.value.trim();
  if (pushSessionSend && chain && full) {
    appendBubble("user", full);
    void sendMessageWithText(full, { skipUserBubble: true });
  }
  pushSessionSend = false;
  setStatus("Hazır", "Rüzgar");
}

async function startBtnRecording() {
  await discardActiveRecording();
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Bu ortamda mikrofon API yok.");
  }
  const stream = await navigator.mediaDevices.getUserMedia(
    getMicAudioConstraints()
  );
  window.__ruzgarMicOk = true;
  startMicLevelMeter(stream);
  const mime = pickRecorderMime();
  let recorder;
  const chunks = [];
  try {
    recorder = new MediaRecorder(
      stream,
      mime ? { mimeType: mime } : undefined
    );
    recorder.ondataavailable = (ev) => {
      if (ev.data && ev.data.size) chunks.push(ev.data);
    };
    recorder.start(120);
  } catch (e) {
    stopMicLevelMeter();
    try {
      stream.getTracks().forEach((t) => t.stop());
    } catch (_) {
      /* ignore */
    }
    throw e;
  }
  recState = {
    kind: "btn",
    stream,
    recorder,
    chunks,
    mime,
    startedAt: Date.now(),
  };
  el.mic.classList.add("recording");
  el.mic.classList.add("listening");
  setStatus("Dinliyorum… (bırakınca metne)", "Rüzgar");
}

function micPointerDown(e) {
  if (e.pointerType === "mouse" && e.button !== 0) return;
  e.preventDefault();
  try {
    el.mic.setPointerCapture(e.pointerId);
  } catch (_) {}
  if (micPressed) return;
  micPressed = true;
  pushSessionSend = true;
  micBootPromise = (async () => {
    try {
      await startBtnRecording();
    } catch (err) {
      micPressed = false;
      pushSessionSend = false;
      stopMicLevelMeter();
      el.mic.classList.remove("recording");
      el.mic.classList.remove("listening");
      setStatus(err && err.message ? err.message : String(err), "Rüzgar");
    }
  })();
}

async function micPointerUp(e) {
  if (micBootPromise) {
    try {
      await micBootPromise;
    } catch (_) {
      /* startBtnRecording hata verdiyse */
    }
    micBootPromise = null;
  }
  const wasHeld = micPressed;
  micPressed = false;
  try {
    el.mic.releasePointerCapture(e.pointerId);
  } catch (_) {}
  if (wasHeld) {
    const s = recState;
    if (s && s.kind === "btn") {
      recState = null;
      await finalizeRecording(s);
    } else {
      await discardActiveRecording();
    }
    return;
  }
  await discardActiveRecording();
}

/** Menüden mikrofon: basılı tutmadan max ~12 sn dinle */
async function menuOpenMic() {
  if (micPressed) return;
  const sessionId = ++menuMicToken;
  pushSessionSend = true;
  try {
    await discardActiveRecording();
    if (!navigator.mediaDevices?.getUserMedia) {
      throw new Error("Mikrofon API yok.");
    }
    const stream = await navigator.mediaDevices.getUserMedia(
      getMicAudioConstraints()
    );
    window.__ruzgarMicOk = true;
    startMicLevelMeter(stream);
    const mime = pickRecorderMime();
    let recorder;
    const chunks = [];
    try {
      recorder = new MediaRecorder(
        stream,
        mime ? { mimeType: mime } : undefined
      );
      recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size) chunks.push(ev.data);
      };
      recorder.start(120);
    } catch (e) {
      stopMicLevelMeter();
      try {
        stream.getTracks().forEach((t) => t.stop());
      } catch (_) {
        /* ignore */
      }
      throw e;
    }
    const timer = window.setTimeout(async () => {
      const s = recState;
      if (!s || s.kind !== "menu" || s.menuSessionId !== sessionId) return;
      recState = null;
      if (s.timer) clearTimeout(s.timer);
      await finalizeRecording(s);
    }, 12000);
    recState = {
      kind: "menu",
      menuSessionId: sessionId,
      stream,
      recorder,
      chunks,
      mime,
      timer,
      startedAt: Date.now(),
    };
    el.mic.classList.add("recording");
    el.mic.classList.add("listening");
    setStatus("Dinliyorum… (en fazla 12 sn)", "Rüzgar");
  } catch (err) {
    pushSessionSend = false;
    stopMicLevelMeter();
    el.mic.classList.remove("recording");
    el.mic.classList.remove("listening");
    setStatus(err && err.message ? err.message : String(err), "Rüzgar");
  }
}

async function speakLast() {
  const text = ttsPlainForSpeech(lastAssistantReply || "");
  if (!text) return;
  if (el.voiceOut != null && !el.voiceOut.checked) return;
  let kar = "asistan";
  try {
    const rs = await fetch(`${API}/api/ses/settings`);
    if (rs.ok) {
      const j = await rs.json();
      kar = normalizeKarakterForTts(j.karakter);
    }
  } catch (_) {
    /* yok say */
  }
  try {
    const res = await fetch(`${API}/api/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        karakter: kar,
        backend: "edge",
        ...(lastVoiceEmotion && lastVoiceEmotion !== "notr"
          ? { emotion: lastVoiceEmotion }
          : {}),
      }),
    });
    if (res.ok) {
      const blob = await res.blob();
      await playTtsBlob(blob);
      setStatus("Hazır");
      return;
    }
  } catch (_) {
    /* Edge yok */
  }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "tr-TR";
  window.speechSynthesis.speak(u);
  setStatus("Sesli okuma…");
  syncInterruptButton();
  u.onend = () => {
    setStatus("Hazır");
    syncInterruptButton();
  };
}

function speakTextImmediate(text) {
  const plain = ttsPlainForSpeech(text || "");
  if (!plain) return;
  try {
    window.speechSynthesis.cancel();
  } catch (_) {
    /* yok say */
  }
  try {
    const u = new SpeechSynthesisUtterance(plain);
    u.lang = "tr-TR";
    window.speechSynthesis.speak(u);
    setStatus("Sesli okuma…");
    syncInterruptButton();
    u.onend = () => {
      setStatus("Hazır");
      syncInterruptButton();
    };
  } catch (_) {
    /* yok say */
  }
}

async function loadFileTree() {
  try {
    const items = await window.ruzgarApi.listDir("");
    el.tree.innerHTML = "";
    for (const it of items) {
      const row = document.createElement("div");
      row.className = `tree-item ${it.isDir ? "folder" : "file"}`;
      row.textContent = (it.isDir ? "▸ " : "· ") + it.name;
      el.tree.appendChild(row);
    }
  } catch {
    el.tree.textContent = "(klasör okunamadı)";
  }
}

if (el.send) el.send.addEventListener("click", sendMessage);
if (el.stop) {
  el.stop.addEventListener("click", () => interruptRuzgar());
}
el.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    void sendMessage();
    return;
  }
  if (e.isComposing) return;
  if (e.altKey || e.ctrlKey || e.metaKey) return;
  if (KEYS_VOICE_SILENCE_IGNORE.has(e.key)) return;
  silenceVoiceOnUserEdit();
});
/** IME commit, dokunmatik klavye, sürükleyip bırakma metin — ses varsayılanı kes */
el.input.addEventListener("input", () => silenceVoiceOnUserEdit());
el.input.addEventListener("paste", () => silenceVoiceOutputNow());
if (el.mic) {
  el.mic.addEventListener("pointerdown", (e) => {
    void micPointerDown(e);
  });
  el.mic.addEventListener("pointerup", micPointerUp);
  el.mic.addEventListener("pointercancel", micPointerUp);
  el.mic.addEventListener("lostpointercapture", micPointerUp);
}
/* pointerleave kaldırıldı: kenarda milimetrelik hareket “bırakıldı” sanıp tanımayı kesiyor + Windows’ta çok sayıda erişim kaydı */

if (window.ruzgarApi?.onMenu) {
  window.ruzgarApi.onMenu((action) => {
    if (action === "focus-chat") el.input.focus();
    if (action === "mic") void menuOpenMic();
    if (action === "speak") speakLast();
    if (action === "menu:disa-aktar") {
      console.log("[RÜZGAR] Hazırlanıyor... (Dışa Aktar — içerik)");
      let body = (lastAssistantReply || "").trim();
      if (!body && chatHistory.length) {
        body = chatHistory
          .map((m) => `${m.role}: ${m.content}`)
          .join("\n\n");
      }
      if (!body) {
        setStatus("Dışa aktarılacak metin yok", "Rüzgar");
        return;
      }
      void window.ruzgarApi.exportSonuc(body).then((r) => {
        if (r?.ok) setStatus("Dışa aktarıldı", "Rüzgar");
        else setStatus("Dışa aktarma iptal veya hata", "Rüzgar");
      });
    }
    if (action === "menu:bellek-temizle") {
      console.log("[RÜZGAR] Hazırlanıyor... (Bellek temizliği)");
      clearChatSession();
    }
    if (action === "menu:kaynak-eklendi") {
      console.log("[RÜZGAR] Mimar, yeni eser kütüphaneye eklendi");
      setStatus("Mimar, yeni eser kütüphaneye eklendi", "Rüzgar");
    }
    if (action === "menu:sistem-ayarlari") {
      openSistemAyarlariPanel();
      setStatus("Sistem Ayarları — Ümit & Gökçenur", "Rüzgar");
    }
    if (action === "ses:ayar-hiz-huzur") {
      console.log("[RÜZGAR] Hazırlanıyor... (Okuma hızı ve huzur)");
      const defH = "0.92";
      const defZ = "0.88";
      const hRaw = window.prompt(
        "Okuma hızı çarpanı (0.45–1.0, yüksek = daha akıcı)",
        defH
      );
      if (hRaw == null) return;
      const zRaw = window.prompt(
        "Huzur çarpanı (0.45–1.0, düşük = daha yavaş/sakin — Deep & Calm)",
        defZ
      );
      if (zRaw == null) return;
      let hiz = Number.parseFloat(hRaw.replace(",", "."));
      let huzur = Number.parseFloat(zRaw.replace(",", "."));
      if (!Number.isFinite(hiz)) hiz = 0.92;
      if (!Number.isFinite(huzur)) huzur = 0.88;
      hiz = Math.min(1, Math.max(0.45, hiz));
      huzur = Math.min(1, Math.max(0.45, huzur));
      void fetch(`${API}/api/ses/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hiz,
          huzur,
          mimarlar: "Ümit & Gökçenur",
        }),
      })
        .then((r) => {
          if (r.ok) setStatus(`Ses ayarı: hız ${hiz} · huzur ${huzur}`, "Rüzgar");
          else setStatus("Ses ayarı kaydedilemedi", "Rüzgar");
        })
        .catch(() => setStatus("API yok — ses ayarı yazılamadı", "Rüzgar"));
    }
    if (typeof action === "string" && action.startsWith("mode:")) {
      switchMode(action.slice(5));
      el.input.focus();
    }
  });
}

wireNavToolbar();
checkApi();
setInterval(checkApi, 15000);
refreshPerformanceMetrics();
scheduleMetricsPolling();
loadFileTree();
globalThis.__ruzgarSpeak = speakLast;
