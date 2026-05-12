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
  okuma: "BİLİM MOTORU",
  video: "VİDEO MOTORU",
  programlama: "PROGRAMLAMA MOTORU",
  hafiza: "HAFIZA MOTORU",
  tercume: "TERCÜME MOTORU",
  duzen: "Düzen",
  dosya: "Dosya",
  hizli: "Hızlı",
};

const el = {
  chat: document.getElementById("chat-messages"),
  orchestraBridge: document.getElementById("orchestra-bridge"),
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
  pageTercume: document.getElementById("page-tercume"),
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
  btnIlimRefresh: document.getElementById("btn-ilim-refresh"),
  btnIlimToChat: document.getElementById("btn-ilim-to-chat"),
  btnIlimSummary: document.getElementById("btn-ilim-summary"),
  btnIlimComment: document.getElementById("btn-ilim-comment"),
  btnIlimOpenArchive: document.getElementById("btn-ilim-open-archive"),
  ilimStats: document.getElementById("ilim-stats"),
  ilimActiveFile: document.getElementById("ilim-active-file"),
  tercumeFileList: document.getElementById("tercume-file-list"),
  tercumeSource: document.getElementById("tercume-source"),
  tercumeTarget: document.getElementById("tercume-target"),
  tercumeSrcLang: document.getElementById("tercume-src-lang"),
  tercumeTgtLang: document.getElementById("tercume-tgt-lang"),
  btnTercumeRefresh: document.getElementById("btn-tercume-refresh"),
  btnTercumeOpenArchive: document.getElementById("btn-tercume-open-archive"),
  btnTercumeTranslate: document.getElementById("btn-tercume-translate"),
  btnTercumeLastToTarget: document.getElementById("btn-tercume-last-to-target"),
  btnTercumeSourceToChat: document.getElementById("btn-tercume-source-to-chat"),
  btnTercumeClear: document.getElementById("btn-tercume-clear"),
  tercumeStats: document.getElementById("tercume-stats"),
  tercumeActiveFile: document.getElementById("tercume-active-file"),
  sesSttLang: document.getElementById("ses-stt-lang"),
  btnSesStt: document.getElementById("btn-ses-stt"),
  sesSttHint: document.getElementById("ses-stt-hint"),
  sesTranscript: document.getElementById("ses-transcript"),
  btnSesToChat: document.getElementById("btn-ses-to-chat"),
  btnSesSpeak: document.getElementById("btn-ses-speak"),
  btnSesClear: document.getElementById("btn-ses-clear"),
  sesSttMeta: document.getElementById("ses-stt-meta"),
  videoFileInput: document.getElementById("video-file-input"),
  videoPreview: document.getElementById("video-preview"),
  btnVideoProbe: document.getElementById("btn-video-probe"),
  btnVideoClear: document.getElementById("btn-video-clear"),
  videoEngineHint: document.getElementById("video-engine-hint"),
  videoProbeJson: document.getElementById("video-probe-json"),
  videoRelWorkspace: document.getElementById("video-rel-workspace"),
  videoStartSec: document.getElementById("video-start-sec"),
  videoDurationSec: document.getElementById("video-duration-sec"),
  videoEndSec: document.getElementById("video-end-sec"),
  videoCopyStreams: document.getElementById("video-copy-streams"),
  btnVideoTrim: document.getElementById("btn-video-trim"),
  btnVideoTranscode: document.getElementById("btn-video-transcode"),
  btnVideoConcat: document.getElementById("btn-video-concat"),
  btnVideoOpenExport: document.getElementById("btn-video-open-export"),
  videoConcatA: document.getElementById("video-concat-a"),
  videoConcatB: document.getElementById("video-concat-b"),
  videoConcatCopy: document.getElementById("video-concat-copy"),
  videoRelBurnVideo: document.getElementById("video-rel-burn-video"),
  videoRelBurnSub: document.getElementById("video-rel-burn-sub"),
  btnVideoBurnSub: document.getElementById("btn-video-burn-sub"),
  videoRelMuxVideo: document.getElementById("video-rel-mux-video"),
  videoRelMuxAudio: document.getElementById("video-rel-mux-audio"),
  videoMuxShortest: document.getElementById("video-mux-shortest"),
  videoMuxCopyVideo: document.getElementById("video-mux-copy-video"),
  btnVideoMuxAudio: document.getElementById("btn-video-mux-audio"),
  videoTimelineLabel: document.getElementById("video-timeline-label"),
  videoTimelineTrack: document.getElementById("video-timeline-track"),
  videoTimelineProgress: document.getElementById("video-timeline-progress"),
  videoTimelineRange: document.getElementById("video-timeline-range"),
  videoTimelinePlayhead: document.getElementById("video-timeline-playhead"),
  btnVideoMarkIn: document.getElementById("btn-video-mark-in"),
  btnVideoMarkOut: document.getElementById("btn-video-mark-out"),
  btnVideoSyncTrim: document.getElementById("btn-video-sync-trim"),
  btnVideoClearRange: document.getElementById("btn-video-clear-range"),
  videoRelSubTranslate: document.getElementById("video-rel-sub-translate"),
  btnVideoSubToTercume: document.getElementById("btn-video-sub-to-tercume"),
  audioFileInput: document.getElementById("audio-file-input"),
  audioPreview: document.getElementById("audio-preview"),
  codeEditor: document.getElementById("code-editor"),
  codeLanguage: document.getElementById("code-language"),
  codeOutput: document.getElementById("code-output"),
  btnCodeNew: document.getElementById("btn-code-new"),
  btnCodeExplain: document.getElementById("btn-code-explain"),
  btnCodeFix: document.getElementById("btn-code-fix"),
  btnCodeRefactor: document.getElementById("btn-code-refactor"),
  btnCodeTest: document.getElementById("btn-code-test"),
  btnCodeRun: document.getElementById("btn-code-run"),
  btnCodeOutputClear: document.getElementById("btn-code-output-clear"),
  codeFileTree: document.getElementById("code-file-tree"),
  btnCodeRefresh: document.getElementById("btn-code-refresh"),
  btnCodeSave: document.getElementById("btn-code-save"),
  codeActiveFile: document.getElementById("code-active-file"),
  dashboardStatus: document.getElementById("dashboard-status"),
  dashboardLastSpeech: document.getElementById("dashboard-last-speech"),
  ctxMenu: document.getElementById("ctx-menu"),
};

let hafizaAnalyzeRows = [];
let hafizaLookup = {};
let selectedAnalyzeIndex = -1;

/** Programlama Atölyesi — Faz 1.2: açık dosya göreli yolu (proje köküne göre) */
let atolyeOpenRel = null;

/** Okuma Atölyesi — İlim arşivinde seçili dosya */
let ilimOpenRel = null;
/** Tercüme Atölyesi — kaynak dosya */
let tercumeOpenRel = null;
/** Ses önizleme blob URL — yeniden seçimde iptal */
let sesPreviewObjectUrl = null;
/** Video önizleme blob URL */
let videoPreviewObjectUrl = null;
/** Son ffprobe özeti (dosya seçili değilken süre için) */
let lastVideoProbeDurationSec = 0;
/** v4 zaman çizelgesi In/Out (saniye; null = işaret yok) */
let videoTimelineIn = null;
let videoTimelineOut = null;
const OKUMA_ARSIV_ROOT = "ilim-assistant/arsiv";

async function workspaceListDir(rel) {
  const r = String(rel ?? "");
  if (window.ruzgarApi?.listDir) {
    return window.ruzgarApi.listDir(r);
  }
  const res = await fetch(`${API}/api/workspace/list?rel=${encodeURIComponent(r)}`);
  const j = await res.json().catch(() => ({}));
  if (!res.ok || j.ok === false) {
    throw new Error(j.detail || j.error || `HTTP ${res.status}`);
  }
  return j.items || [];
}

async function readWorkspaceText(rel) {
  if (window.ruzgarApi?.readText) {
    const rr = await window.ruzgarApi.readText(rel);
    if (rr?.ok) return String(rr.text ?? "");
    throw new Error(rr?.error || "Dosya okunamadı.");
  }
  const res = await fetch(`${API}/api/workspace/read-text?rel=${encodeURIComponent(rel)}`);
  const j = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || {}) || `HTTP ${res.status}`
    );
  }
  return String(j.text ?? "");
}

/** Okuma atölyesi: PDF/DOCX sunucuda; diğerleri düz metin (UTF-8). */
async function readArchiveFileForOkuma(rel) {
  const low = String(rel || "").toLowerCase();
  if (low.endsWith(".pdf")) {
    const res = await fetch(`${API}/api/workspace/read-pdf?rel=${encodeURIComponent(rel)}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      const d = j.detail;
      throw new Error(typeof d === "string" ? d : JSON.stringify(d || {}) || `HTTP ${res.status}`);
    }
    let out = String(j.text ?? "");
    if (j.truncated_pages || j.truncated_length) {
      out += "\n\n— PDF: sayfa/metin sınırı nedeniyle kısaltılmış olabilir.";
    }
    return out;
  }
  if (low.endsWith(".docx")) {
    const res = await fetch(`${API}/api/workspace/read-docx?rel=${encodeURIComponent(rel)}`);
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      const d = j.detail;
      throw new Error(typeof d === "string" ? d : JSON.stringify(d || {}) || `HTTP ${res.status}`);
    }
    let out = String(j.text ?? "");
    if (j.truncated_length) {
      out += "\n\n— DOCX: uzunluk sınırı nedeniyle kısaltılmış olabilir.";
    }
    return out;
  }
  return readWorkspaceText(rel);
}

const TOP_MODE_BUTTONS = [
  "modeBtnGenel",
  "modeBtnVideo",
  "modeBtnProgramlama",
  "modeBtnHafiza",
  "modeBtnOkuma",
  "modeBtnSes",
];

function syncTopModeButtons() {
  // Hem üst topbar (eski) hem sol motor menüsü (Faz 0) aynı `data-mode` ile çalışır.
  const allModeButtons = document.querySelectorAll("[data-mode]");
  allModeButtons.forEach((btn) => {
    const mode = String(btn.getAttribute("data-mode") || "").trim().toLowerCase();
    if (!mode) return;
    const isActive = mode === currentMode;
    btn.classList.toggle("is-active", isActive);
    btn.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
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
    if (["ses", "okuma", "tercume", "uretim", "hizli", "hafiza"].includes(currentMode)) {
      el.web.checked = false;
    } else {
      el.web.checked = true;
    }
  }
  syncWebFetchUi();
  if (currentMode === "okuma") {
    el.input.placeholder =
      "Kültür ve İlim Hazinesi: metni yapıştırın; arsiv/ altındaki dört külliyata PDF/TXT ekleyip indeks: python -m ilim_assistant.arsiv_indexle";
  } else if (currentMode === "tercume") {
    el.input.placeholder =
      "İsterseniz çeviriyi buradan da yazın; sol panel «Çevir» ile daha yapılandırılmış gönderir.";
  } else if (currentMode === "ses") {
    el.input.placeholder =
      "Ses motorunda transkripti panelden sohbete aktarabilir veya doğrudan soru yazabilirsiniz.";
  } else if (currentMode === "video") {
    el.input.placeholder =
      "Video motorunda FFmpeg, kesme veya altyazı hakkında soru yazın; dosya özeti soldaki panelde.";
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
        : currentMode === "tercume"
          ? "Çeviri için düşünülüyor…"
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
    okuma:
      "Bilim motoru — İlim, tabiat ve tarih: arşiv + derin okuma; ana motorla köprülü çalışır.",
    video:
      "Video motoru — v4: kesim çizelgesi (başlangıç/bitiş), altyazı gömme, ses birleştirme, altyazıyı Tercüme atölyesine aktarma; çıktı .ruzgar-video-export.",
    programlama:
      "Programlama motoru açıldı; Faz 1.3 — proje köküne göre çalıştırma, kod yardımcısı üretim modu.",
    hafiza:
      "Hafıza motoru açıldı; bu motorla gelişim ve hafıza teknikleri üzerinde çalışabilirsiniz.",
    ses:
      "Ses motoru — Stüdyo: dosya + konuşmayı metne dökme, transkript; tarayıcıdan seslendirme.",
    tercume:
      "Tercüme motoru — Ofis paneli: arşiv + iki kolon; Çevir ile Rüzgar’a yapılandırılmış istek.",
  };
  setHeaderMotorDeclaration(motorDeclarationByMode[currentMode] || "");
  clearMotorDeclarations();
}

function clearOrchestraBridge() {
  const wrap = el.orchestraBridge;
  if (!wrap) return;
  wrap.hidden = true;
  wrap.innerHTML = "";
}

function applyMotorHandoff(modeId, handoffText) {
  const t = String(handoffText || "").trim();
  const mid = String(modeId || "").trim().toLowerCase();
  switch (mid) {
    case "tercume":
      switchMode("tercume");
      if (el.tercumeSource) el.tercumeSource.value = t;
      updateTercumeTextStats();
      el.tercumeSource?.focus();
      break;
    case "video":
      switchMode("video");
      flashRuzgarDurum("Video motoru: metin panoya kopyalandı.");
      void navigator.clipboard?.writeText(t);
      break;
    case "ses":
      switchMode("ses");
      if (el.sesTranscript) el.sesTranscript.value = t;
      el.sesTranscript?.focus();
      break;
    case "programlama":
      switchMode("programlama");
      if (el.codeEditor) el.codeEditor.value = t;
      updateProgramlamaActiveFileLabel();
      break;
    case "okuma":
      switchMode("okuma");
      if (el.input) el.input.value = t;
      el.input?.focus();
      break;
    case "hafiza":
      switchMode("hafiza");
      if (el.hafizaInput) el.hafizaInput.value = t.slice(0, 8000);
      break;
    default:
      switchMode("genel");
      if (el.input) el.input.value = t;
      el.input?.focus();
  }
  setStatus(`Köprü: ${mid}`, "Rüzgar");
}

function renderOrchestraBridge(orch) {
  const wrap = el.orchestraBridge;
  if (!wrap || !orch || !Array.isArray(orch.motors) || orch.motors.length === 0) {
    clearOrchestraBridge();
    return;
  }
  wrap.hidden = false;
  wrap.innerHTML = "";
  const title = document.createElement("div");
  title.className = "orchestra-bridge-title";
  title.textContent = "Ana motor — çalışma sayfası köprüleri";
  wrap.appendChild(title);
  const row = document.createElement("div");
  row.className = "orchestra-bridge-actions";
  for (const m of orch.motors) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "btn-orchestra-bridge";
    b.textContent = m.label || m.id || "Motor";
    const id = String(m.id || "").trim().toLowerCase();
    const ho = String(m.handoff || "").trim();
    b.addEventListener("click", () => applyMotorHandoff(id, ho));
    row.appendChild(b);
  }
  wrap.appendChild(row);
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
    el.pageTercume,
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
    tercume: el.pageTercume,
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
  if (currentMode === "tercume") void loadTercumeFileList();
  if (currentMode === "ses") void refreshSesSttHint();
  if (currentMode === "video") void refreshVideoEngineHint();
  if (currentMode === "programlama") {
    updateProgramlamaActiveFileLabel();
    void programlamaAtolyeRefreshRoot();
  }
}

function wireTopModeButtons() {
  // Tek bir handler hem eski üst topbar hem yeni sol motor menüsü için çalışır.
  // Idempotent: aynı butona iki kez bağlamayalım diye işaretliyoruz.
  const allModeButtons = document.querySelectorAll("[data-mode]");
  allModeButtons.forEach((btn) => {
    if (btn.dataset.modeWired === "1") return;
    btn.dataset.modeWired = "1";
    btn.addEventListener("click", () => {
      const mode = String(btn.getAttribute("data-mode") || "").trim().toLowerCase();
      if (!mode) return;
      switchMode(mode);
      if (el.input) el.input.focus();
    });
  });
}

function selectedCodeLanguageLabel() {
  const value = String(el.codeLanguage?.value || "python").trim();
  const opt = el.codeLanguage?.selectedOptions?.[0];
  return opt?.textContent?.trim() || value || "Python";
}

function getCodeEditorText() {
  return String(el.codeEditor?.value || "").trim();
}

function setCodeOutput(text) {
  if (!el.codeOutput) return;
  el.codeOutput.textContent = String(text || "");
}

function sendCodeAssistantPrompt(action) {
  const code = getCodeEditorText();
  if (!code) {
    setCodeOutput("Önce editöre kod yazın; sonra Rüzgar yardımcısını çağırın.");
    flashRuzgarDurum("Programlama Atölyesi: editörde kod yok.");
    return;
  }
  const lang = selectedCodeLanguageLabel();
  const actionPrompts = {
    explain: "Aşağıdaki kodu mimara sade ve net şekilde açıkla. Hatalı veya riskli yerleri ayrıca belirt.",
    fix: "Aşağıdaki kodu incele. Olası hataları, bug risklerini ve düzeltme önerilerini sırayla ver.",
    refactor:
      "Aşağıdaki kodu daha temiz, okunabilir ve sürdürülebilir hale getirmek için yeniden düzenleme önerisi hazırla.",
    test: "Aşağıdaki kod için uygun test senaryoları ve mümkünse örnek test kodu yaz.",
  };
  const instruction = actionPrompts[action] || actionPrompts.explain;
  const proEdge =
    "Üretim kalitesinde yanıt ver: gereksiz önsöz yok; doğrudan çözüm; güvenlik ve sürdürülebilirlik notları kısa.";
  const prompt = `${proEdge}\n\n${instruction}\n\nDil: ${lang}\n\n\`\`\`${String(el.codeLanguage?.value || "python")}\n${code}\n\`\`\``;
  switchMode("programlama");
  setCodeOutput("Rüzgar kod yardımcısı çağrıldı. Yanıt sağ sohbet panelinde akacak.");
  void sendMessageWithText(prompt, { skipUserBubble: false });
}

function deriveCodeRunCwdRelFromOpenFile(rel) {
  const s = String(rel || "").replace(/\\/g, "/");
  const i = s.lastIndexOf("/");
  return i > 0 ? s.slice(0, i) : "";
}

async function runCodeFromWorkbench() {
  const code = getCodeEditorText();
  if (!code) {
    setCodeOutput("Önce editöre kod yazın.");
    return;
  }
  const language = String(el.codeLanguage?.value || "python").trim().toLowerCase();
  setCodeOutput("Çalıştırılıyor...");
  let workspaceRoot = null;
  try {
    if (window.ruzgarApi?.getRoot) {
      workspaceRoot = await window.ruzgarApi.getRoot();
    }
  } catch (_) {
    workspaceRoot = null;
  }
  const payload = {
    code,
    language,
    timeout_sec: 8,
  };
  if (workspaceRoot && atolyeOpenRel) {
    payload.workspace_root = workspaceRoot;
    payload.cwd_rel = deriveCodeRunCwdRelFromOpenFile(atolyeOpenRel);
  }
  try {
    const res = await fetch(`${API}/api/code/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data?.detail || `HTTP ${res.status}`);
    }
    const parts = [];
    parts.push(`Durum: ${data.ok ? "başarılı" : "hata"}${data.exit_code != null ? ` (exit ${data.exit_code})` : ""}`);
    if (Object.prototype.hasOwnProperty.call(data, "cwd_used_rel") && data.cwd_used_rel != null) {
      const cr = data.cwd_used_rel;
      parts.push(
        cr === "" || cr === "."
          ? "\nÇalışma dizini: proje kökü (kayıtlı dosya — göreli import/dosya yolu aktif)."
          : `\nÇalışma dizini (proje içi): ${cr.replace(/\\/g, "/")}`
      );
    } else if (!atolyeOpenRel) {
      parts.push("\nÇalışma dizini: izole geçici klasör (kayıtlı dosya yok — projeye göre yol için önce Kaydet veya ağaçtan dosya aç).");
    }
    if (data.timeout) parts.push("Zaman aşımı: kod belirtilen sürede bitmedi.");
    if (data.stdout) parts.push(`\n--- stdout ---\n${data.stdout}`);
    if (data.stderr) parts.push(`\n--- stderr ---\n${data.stderr}`);
    if (!data.stdout && !data.stderr) parts.push("\nÇıktı yok.");
    setCodeOutput(parts.join("\n"));
  } catch (e) {
    setCodeOutput(`Çalıştırma hatası: ${e && e.message ? e.message : e}`);
  }
}

// ---------- Programlama Atölyesi — Faz 1.2 (proje ağacı + dosya oku/yaz) ----------
function updateProgramlamaActiveFileLabel() {
  if (!el.codeActiveFile) return;
  el.codeActiveFile.textContent = atolyeOpenRel
    ? `Dosya: ${atolyeOpenRel}`
    : "Dosya: (yeni — Kaydet ile göreli yol verilir)";
}

function applyLanguageFromFilename(rel) {
  const low = String(rel || "").toLowerCase();
  const pairs = [
    [/\.pyw?$/, "python"],
    [/\.(js|mjs|cjs)$/, "javascript"],
    [/\.ts$/, "typescript"],
    [/\.(tsx|jsx)$/, "typescript"],
    [/\.(html|htm)$/, "html"],
    [/\.css$/, "css"],
    [/\.(json|jsonc)$/, "json"],
  ];
  if (!el.codeLanguage) return;
  for (const [re, val] of pairs) {
    if (re.test(low)) {
      const opts = Array.from(el.codeLanguage.options || []);
      if (opts.some((o) => o.value === val)) el.codeLanguage.value = val;
      return;
    }
  }
}

function createCodeTreeBranch(it, depth) {
  const branch = document.createElement("div");
  branch.className = "code-tree-branch";
  const pad = 4 + depth * 12;
  if (it.isDir) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "code-tree-row folder";
    btn.dataset.rel = it.rel;
    btn.dataset.depth = String(depth);
    btn.style.paddingLeft = `${pad}px`;
    btn.innerHTML =
      `<span class="code-tree-chev" aria-hidden="true">▸</span>` +
      `<span class="code-tree-name">${esc(it.name)}</span>`;
    const kids = document.createElement("div");
    kids.className = "code-tree-children";
    kids.hidden = true;
    branch.appendChild(btn);
    branch.appendChild(kids);
  } else {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "code-tree-row file";
    btn.dataset.rel = it.rel;
    btn.dataset.depth = String(depth);
    btn.style.paddingLeft = `${pad}px`;
    btn.innerHTML =
      `<span class="code-tree-file-ico" aria-hidden="true">·</span>` +
      `<span class="code-tree-name">${esc(it.name)}</span>`;
    branch.appendChild(btn);
  }
  return branch;
}

async function handleCodeTreeClick(ev) {
  const row = ev.target.closest(".code-tree-row");
  if (!row || !el.codeFileTree || !el.codeFileTree.contains(row)) return;
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
        const items = await workspaceListDir(rel);
        kids.innerHTML = "";
        for (const x of items) {
          kids.appendChild(createCodeTreeBranch(x, depth + 1));
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
    if (chev)
      chev.textContent = kids.hidden ? "▸" : "▾";
    return;
  }

  if (row.classList.contains("file")) {
    void openProgramlamaWorkspaceFile(rel);
  }
}

async function openProgramlamaWorkspaceFile(rel) {
  try {
    const text = await readWorkspaceText(rel);
    atolyeOpenRel = rel;
    if (el.codeEditor) el.codeEditor.value = text;
    applyLanguageFromFilename(rel);
    updateProgramlamaActiveFileLabel();
    setCodeOutput(`Açıldı: ${rel}`);
    flashRuzgarDurum(`Dosya açıldı: ${rel}`);
    el.codeEditor?.focus();
  } catch (e) {
    setCodeOutput(`Dosya hatası: ${e && e.message ? e.message : e}`);
  }
}

async function programlamaAtolyeRefreshRoot() {
  if (!el.codeFileTree) return;
  el.codeFileTree.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
  try {
    const items = await workspaceListDir("");
    el.codeFileTree.innerHTML = "";
    for (const it of items) {
      el.codeFileTree.appendChild(createCodeTreeBranch(it, 0));
    }
    if (!items.length) {
      el.codeFileTree.innerHTML =
        `<div class="code-file-placeholder">Kök klasör boş veya erişilemiyor.</div>`;
    }
  } catch (e) {
    el.codeFileTree.innerHTML =
      `<div class="code-file-placeholder">Kök liste okunamadı: ${esc(String(e && e.message ? e.message : e))}. Yerel sunucu (ilim-assistant) veya masaüstü köprüsü gerekir.</div>`;
  }
}

// ---------- Okuma Atölyesi — Faz 2.1 (İlim arşivi ağacı + metin + sohbete aktar) ----------
function updateIlimActiveFileLabel() {
  if (!el.ilimActiveFile) return;
  el.ilimActiveFile.textContent = ilimOpenRel
    ? `Metin: ${ilimOpenRel}`
    : "Metin: (sol listeden dosya seçin)";
}

function updateIlimTextStats() {
  if (!el.ilimStats) return;
  const t = String(el.ilimFileContent?.value || "");
  const chars = t.length;
  const words = t.replace(/\s+/g, " ").trim() ? t.trim().split(/\s+/).length : 0;
  el.ilimStats.textContent = `${chars.toLocaleString("tr-TR")} karakter · ${words.toLocaleString("tr-TR")} kelime`;
}

async function handleArsivTreeClick(ev, listEl, onOpenFile) {
  const row = ev.target.closest(".code-tree-row");
  if (!row || !listEl || !listEl.contains(row)) return;
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
        const items = await workspaceListDir(rel);
        kids.innerHTML = "";
        for (const x of items) {
          kids.appendChild(createCodeTreeBranch(x, depth + 1));
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
    void onOpenFile(rel);
  }
}

async function openOkumaArsivFile(rel) {
  try {
    const text = await readArchiveFileForOkuma(rel);
    ilimOpenRel = rel;
    if (el.ilimFileContent) el.ilimFileContent.value = text;
    updateIlimActiveFileLabel();
    updateIlimTextStats();
    flashRuzgarDurum(`Okundu: ${rel}`);
    el.ilimFileContent?.focus();
  } catch (e) {
    if (el.ilimFileContent) {
      el.ilimFileContent.value = `(okunamadı: ${e && e.message ? e.message : String(e)})`;
    }
    flashRuzgarDurum("Dosya okunamadı.");
  }
}

async function openTercumeArsivFile(rel) {
  try {
    const text = await readArchiveFileForOkuma(rel);
    tercumeOpenRel = rel;
    if (el.tercumeSource) el.tercumeSource.value = text;
    updateTercumeActiveFileLabel();
    updateTercumeTextStats();
    flashRuzgarDurum(`Kaynak yüklendi: ${rel}`);
    el.tercumeSource?.focus();
  } catch (e) {
    if (el.tercumeSource) {
      el.tercumeSource.value = `(okunamadı: ${e && e.message ? e.message : String(e)})`;
    }
    flashRuzgarDurum("Dosya okunamadı.");
  }
}

function updateTercumeActiveFileLabel() {
  if (!el.tercumeActiveFile) return;
  el.tercumeActiveFile.textContent = tercumeOpenRel
    ? `Kaynak: ${tercumeOpenRel}`
    : "Kaynak: (sol listeden dosya seçin)";
}

function updateTercumeTextStats() {
  if (!el.tercumeStats) return;
  const t = String(el.tercumeSource?.value || "");
  const chars = t.length;
  const words = t.replace(/\s+/g, " ").trim() ? t.trim().split(/\s+/).length : 0;
  el.tercumeStats.textContent = `${chars.toLocaleString("tr-TR")} karakter · ${words.toLocaleString("tr-TR")} kelime (kaynak)`;
}

async function tercumeAtolyeRefreshTree() {
  await refreshArsivTreeInto(el.tercumeFileList);
}

async function loadTercumeFileList() {
  updateTercumeActiveFileLabel();
  updateTercumeTextStats();
  await tercumeAtolyeRefreshTree();
}

async function sendTercumeTranslatePrompt() {
  const raw = String(el.tercumeSource?.value || "").trim();
  if (!raw) {
    flashRuzgarDurum("Önce kaynak metin girin veya soldan dosya açın.");
    return;
  }
  const chunk =
    raw.length > 28000 ? `${raw.slice(0, 28000)}\n\n… (mimar için kısaltıldı)` : raw;
  const srcLabel = el.tercumeSrcLang?.selectedOptions?.[0]?.textContent?.trim() || "Otomatik";
  const tgtLabel = el.tercumeTgtLang?.selectedOptions?.[0]?.textContent?.trim() || "İngilizce";
  const fileNote = tercumeOpenRel ? `\n[Kaynak dosya: ${tercumeOpenRel}]\n` : "";
  const msg = `${fileNote}Ümit abi, tercüme atölyesinden iletiyorum.

Kaynak dil: ${srcLabel}
Hedef dil: ${tgtLabel}

Yalnızca hedef dilde tam çeviriyi ver; uzun giriş veya genel özet yazma. Gerekirse hassas terimler için çok kısa dipnot kullan.

---

${chunk}`;
  flashRuzgarDurum("Rüzgar’a iletiliyor…");
  await sendMessageWithText(msg, { skipUserBubble: false });
}

function wireTercumeAtolye() {
  if (el.tercumeFileList && el.tercumeFileList.dataset.tercumeWired !== "1") {
    el.tercumeFileList.dataset.tercumeWired = "1";
    el.tercumeFileList.addEventListener("click", (ev) => {
      void handleArsivTreeClick(ev, el.tercumeFileList, openTercumeArsivFile);
    });
  }
  if (el.btnTercumeRefresh) {
    el.btnTercumeRefresh.addEventListener("click", () => {
      void tercumeAtolyeRefreshTree();
      flashRuzgarDurum("Kaynak listesi yenilendi.");
    });
  }
  if (el.btnTercumeOpenArchive) {
    el.btnTercumeOpenArchive.addEventListener("click", () => {
      if (window.ruzgarApi?.openWorkspaceRel) {
        void window.ruzgarApi.openWorkspaceRel("ilim-assistant/arsiv");
        flashRuzgarDurum("Arşiv klasörü açılıyor…");
      } else {
        flashRuzgarDurum("Klasörü açmak için masaüstü Rüzgar kullanın.");
      }
    });
  }
  if (el.btnTercumeTranslate) {
    el.btnTercumeTranslate.addEventListener("click", () => {
      void sendTercumeTranslatePrompt();
    });
  }
  if (el.btnTercumeLastToTarget) {
    el.btnTercumeLastToTarget.addEventListener("click", () => {
      const t = String(lastAssistantReply || "").trim();
      if (!t) {
        flashRuzgarDurum("Henüz sohbette bir Rüzgar yanıtı yok.");
        return;
      }
      if (el.tercumeTarget) el.tercumeTarget.value = t;
      flashRuzgarDurum("Son yanıt hedef panele yazıldı.");
      el.tercumeTarget?.focus();
    });
  }
  if (el.btnTercumeSourceToChat) {
    el.btnTercumeSourceToChat.addEventListener("click", () => {
      const t = String(el.tercumeSource?.value || "").trim();
      if (!t) {
        flashRuzgarDurum("Kaynak metin boş.");
        return;
      }
      const chunk = t.length > 12000 ? `${t.slice(0, 12000)}\n\n… (kısaltıldı)` : t;
      if (el.input) {
        el.input.value = chunk;
        el.input.focus();
        flashRuzgarDurum("Kaynak sohbet kutusuna aktarıldı.");
      }
    });
  }
  if (el.btnTercumeClear) {
    el.btnTercumeClear.addEventListener("click", () => {
      if (el.tercumeSource) el.tercumeSource.value = "";
      if (el.tercumeTarget) el.tercumeTarget.value = "";
      tercumeOpenRel = null;
      updateTercumeActiveFileLabel();
      updateTercumeTextStats();
      flashRuzgarDurum("Paneller temizlendi.");
    });
  }
  if (el.tercumeSource) {
    el.tercumeSource.addEventListener("input", () => updateTercumeTextStats());
  }
}

async function refreshSesSttHint() {
  if (!el.sesSttHint) return;
  try {
    const r = await fetch(`${API}/api/health`, { method: "GET" });
    if (!r.ok) throw new Error("no-health");
    const j = await r.json();
    if (j.stt) {
      el.sesSttHint.textContent =
        "Konuşmayı metne dökme hazır. Dosya seçip «Metne dök» deyin; gerekirse: pip install faster-whisper.";
    } else {
      el.sesSttHint.textContent =
        "Metne döküm kapalı. Kurulum: pip install faster-whisper — ardından yerel sunucuyu yeniden başlatın.";
    }
  } catch {
    el.sesSttHint.textContent =
      "Sunucu yok — «Metne dök» için ilim-assistant klasöründe yerel sunucuyu çalıştırın.";
  }
}

async function runSesSttFromFile() {
  const f = el.audioFileInput?.files?.[0];
  if (!f) {
    flashRuzgarDurum("Önce bir ses dosyası seçin.");
    return;
  }
  const langRaw = String(el.sesSttLang?.value || "tr").trim();
  const fd = new FormData();
  fd.append("file", f, f.name || "audio.webm");
  flashRuzgarDurum("Metne dökülüyor…");
  setStatus("STT…", "Rüzgar");
  try {
    const q = langRaw === "auto" ? "auto" : encodeURIComponent(langRaw);
    const res = await fetch(`${API}/api/stt?lang=${q}`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      flashRuzgarDurum(String(detail || res.statusText || "Metne döküm başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const text = String(j.text ?? "").trim();
    if (el.sesTranscript) el.sesTranscript.value = text;
    if (el.sesSttMeta) {
      el.sesSttMeta.textContent =
        j.language != null && String(j.language).length ? `Algılanan dil: ${j.language}` : "";
    }
    flashRuzgarDurum(text ? "Metin dökümü hazır." : "Boş sonuç döndü.");
    setStatus("Hazır", "Rüzgar");
    el.sesTranscript?.focus();
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

function wireSesAtolye() {
  if (el.audioFileInput && el.audioPreview && el.audioFileInput.dataset.sesWired !== "1") {
    el.audioFileInput.dataset.sesWired = "1";
    el.audioFileInput.addEventListener("change", () => {
      const f = el.audioFileInput.files && el.audioFileInput.files[0];
      if (!f) return;
      try {
        if (sesPreviewObjectUrl) URL.revokeObjectURL(sesPreviewObjectUrl);
      } catch (_) {
        /* ignore */
      }
      sesPreviewObjectUrl = URL.createObjectURL(f);
      el.audioPreview.src = sesPreviewObjectUrl;
      if (el.sesSttMeta) el.sesSttMeta.textContent = "";
    });
  }
  if (el.btnSesStt) {
    el.btnSesStt.addEventListener("click", () => {
      void runSesSttFromFile();
    });
  }
  if (el.btnSesToChat) {
    el.btnSesToChat.addEventListener("click", () => {
      const t = String(el.sesTranscript?.value || "").trim();
      if (!t) {
        flashRuzgarDurum("Metin dökümü boş.");
        return;
      }
      const chunk = t.length > 12000 ? `${t.slice(0, 12000)}\n\n… (kısaltıldı)` : t;
      if (el.input) {
        el.input.value = chunk;
        el.input.focus();
        flashRuzgarDurum("Metin sohbet kutusuna aktarıldı.");
      }
    });
  }
  if (el.btnSesSpeak) {
    el.btnSesSpeak.addEventListener("click", () => {
      void speakStudioTranscript(el.sesTranscript?.value || "");
    });
  }
  if (el.btnSesClear) {
    el.btnSesClear.addEventListener("click", () => {
      if (el.sesTranscript) el.sesTranscript.value = "";
      if (el.sesSttMeta) el.sesSttMeta.textContent = "";
      flashRuzgarDurum("Metin dökümü temizlendi.");
    });
  }
}

function formatDurationSec(sec) {
  if (sec == null || Number.isNaN(Number(sec))) return "—";
  const s = Math.max(0, Math.floor(Number(sec)));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
  return `${m}:${String(r).padStart(2, "0")}`;
}

function formatVideoSummaryHuman(summary) {
  if (!summary || typeof summary !== "object") return "(özet yok)";
  const lines = [];
  lines.push(
    `Süre: ${formatDurationSec(summary.duration_sec)} (${Number(summary.duration_sec || 0).toFixed(2)} sn)`
  );
  if (summary.size_bytes != null) {
    const mb = Number(summary.size_bytes) / (1024 * 1024);
    lines.push(`Boyut: ${mb.toFixed(2)} MB`);
  }
  if (summary.format_name) lines.push(`Konteyner / format: ${summary.format_name}`);
  lines.push(`Akış sayısı: ${summary.stream_count ?? "—"}`);
  lines.push(`Video: ${summary.has_video ? "var" : "yok"} · Ses: ${summary.has_audio ? "var" : "yok"}`);
  if (summary.video) {
    const v = summary.video;
    lines.push(
      `Görüntü — kodek: ${v.codec || "?"} · ${v.width || "?"}×${v.height || "?"} · ${v.avg_frame_rate || "?"} kare/sn · ${v.pix_fmt || ""}`
    );
  }
  if (summary.audio) {
    const a = summary.audio;
    lines.push(`Ses — kodek: ${a.codec || "?"} · ${a.sample_rate || "?"} Hz · ${a.channels || "?"} kanal`);
  }
  return lines.join("\n");
}

function getVideoEffectiveDurationSec() {
  const v = el.videoPreview;
  if (v && Number.isFinite(v.duration) && v.duration > 0) return v.duration;
  if (lastVideoProbeDurationSec > 0) return lastVideoProbeDurationSec;
  return 0;
}

function updateVideoTimelineUI() {
  const d = getVideoEffectiveDurationSec();
  const v = el.videoPreview;
  const cur =
    v && Number.isFinite(v.currentTime) && v.currentTime >= 0 ? v.currentTime : 0;
  const safeD = d > 0 ? d : 0.001;
  const pctPlay = Math.min(100, Math.max(0, (cur / safeD) * 100));
  if (el.videoTimelineProgress) el.videoTimelineProgress.style.width = `${pctPlay}%`;
  if (el.videoTimelinePlayhead) el.videoTimelinePlayhead.style.left = `${pctPlay}%`;

  const rangeEl = el.videoTimelineRange;
  if (rangeEl) {
    if (videoTimelineIn != null && videoTimelineOut != null) {
      let a = videoTimelineIn;
      let b = videoTimelineOut;
      if (b < a) [a, b] = [b, a];
      const left = (a / safeD) * 100;
      const w = ((b - a) / safeD) * 100;
      rangeEl.hidden = false;
      rangeEl.style.left = `${Math.min(100, Math.max(0, left))}%`;
      rangeEl.style.width = `${Math.min(100 - left, Math.max(0, w))}%`;
    } else {
      rangeEl.hidden = true;
    }
  }

  if (el.videoTimelineLabel) {
    let cutInfo = "—";
    if (videoTimelineIn != null && videoTimelineOut != null) {
      let a = videoTimelineIn;
      let b = videoTimelineOut;
      if (b < a) [a, b] = [b, a];
      cutInfo = `${a.toFixed(1)}–${b.toFixed(1)} sn (${(b - a).toFixed(1)} sn)`;
    } else if (videoTimelineIn != null) {
      cutInfo = `Başlangıç ${videoTimelineIn.toFixed(1)} sn`;
    } else if (videoTimelineOut != null) {
      cutInfo = `Bitiş ${videoTimelineOut.toFixed(1)} sn`;
    }
    const totalStr = d > 0 ? `${d.toFixed(1)} sn` : "— (dosya veya «Medya bilgisi»)";
    el.videoTimelineLabel.textContent = `Süre: ${totalStr} · İmleç: ${cur.toFixed(1)} sn · Kesim: ${cutInfo}`;
  }
}

function resetVideoTimelineMarks() {
  videoTimelineIn = null;
  videoTimelineOut = null;
  updateVideoTimelineUI();
}

function resetVideoTimelineProbeDuration() {
  lastVideoProbeDurationSec = 0;
  updateVideoTimelineUI();
}

function syncVideoMarksToTrimFields() {
  if (videoTimelineIn == null || videoTimelineOut == null) {
    flashRuzgarDurum("Önce oynatıcıda konum seçip başlangıç ve bitiş işaretleyin.");
    return;
  }
  let a = videoTimelineIn;
  let b = videoTimelineOut;
  if (b < a) [a, b] = [b, a];
  if (el.videoStartSec) el.videoStartSec.value = String(Math.max(0, a).toFixed(2));
  const dur = Math.max(0, b - a);
  if (el.videoDurationSec) el.videoDurationSec.value = dur > 0.001 ? String(dur.toFixed(2)) : "";
  if (el.videoEndSec) el.videoEndSec.value = "";
  flashRuzgarDurum("Kesim alanları güncellendi (v2).");
}

function seekVideoFromTimelineClientX(clientX) {
  const track = el.videoTimelineTrack;
  const v = el.videoPreview;
  if (!track || !v) return;
  const rect = track.getBoundingClientRect();
  const x = (clientX - rect.left) / Math.max(rect.width, 1);
  const d = getVideoEffectiveDurationSec();
  if (d <= 0) {
    flashRuzgarDurum("Önce dosya seçin veya «Medya bilgisi» ile süre alın.");
    return;
  }
  const sec = Math.max(0, Math.min(d, x * d));
  v.currentTime = sec;
  updateVideoTimelineUI();
}

function wireVideoTimeline() {
  const wrap = document.getElementById("video-timeline-wrap");
  if (!wrap || wrap.dataset.timelineWired === "1") return;
  wrap.dataset.timelineWired = "1";
  if (el.videoPreview) {
    el.videoPreview.addEventListener("timeupdate", () => updateVideoTimelineUI());
    el.videoPreview.addEventListener("loadedmetadata", () => updateVideoTimelineUI());
  }
  if (el.videoTimelineTrack) {
    el.videoTimelineTrack.addEventListener("click", (ev) => {
      seekVideoFromTimelineClientX(ev.clientX);
    });
  }
  if (el.btnVideoMarkIn) {
    el.btnVideoMarkIn.addEventListener("click", () => {
      const v = el.videoPreview;
      if (!v || getVideoEffectiveDurationSec() <= 0) {
        flashRuzgarDurum("Önce oynatılabilir dosya veya süre bilgisi gerekli.");
        return;
      }
      videoTimelineIn = v.currentTime;
      updateVideoTimelineUI();
      flashRuzgarDurum(`Başlangıç işareti: ${videoTimelineIn.toFixed(2)} sn`);
    });
  }
  if (el.btnVideoMarkOut) {
    el.btnVideoMarkOut.addEventListener("click", () => {
      const v = el.videoPreview;
      if (!v || getVideoEffectiveDurationSec() <= 0) {
        flashRuzgarDurum("Önce oynatılabilir dosya veya süre bilgisi gerekli.");
        return;
      }
      videoTimelineOut = v.currentTime;
      updateVideoTimelineUI();
      flashRuzgarDurum(`Bitiş işareti: ${videoTimelineOut.toFixed(2)} sn`);
    });
  }
  if (el.btnVideoSyncTrim) {
    el.btnVideoSyncTrim.addEventListener("click", () => {
      syncVideoMarksToTrimFields();
    });
  }
  if (el.btnVideoClearRange) {
    el.btnVideoClearRange.addEventListener("click", () => {
      videoTimelineIn = null;
      videoTimelineOut = null;
      updateVideoTimelineUI();
      flashRuzgarDurum("Başlangıç ve bitiş işaretleri sıfırlandı.");
    });
  }
  if (el.btnVideoSubToTercume) {
    el.btnVideoSubToTercume.addEventListener("click", () => {
      void sendSubtitleFileToTercumeAtolye();
    });
  }
}

async function sendSubtitleFileToTercumeAtolye() {
  const rel = String(el.videoRelSubTranslate?.value || "").trim();
  if (!rel) {
    flashRuzgarDurum("Altyazı dosyası için göreli yol girin.");
    return;
  }
  const low = rel.toLowerCase();
  if (!low.endsWith(".srt") && !low.endsWith(".vtt") && !low.endsWith(".txt")) {
    flashRuzgarDurum("Önerilen uzantılar: .srt, .vtt veya düz .txt");
  }
  flashRuzgarDurum("Altyazı okunuyor…");
  setStatus("Dosya okunuyor…", "Rüzgar");
  try {
    const text = await readWorkspaceText(rel);
    if (!text.trim()) {
      flashRuzgarDurum("Dosya boş.");
      setStatus("Hazır", "Rüzgar");
      return;
    }
    if (el.tercumeSource) el.tercumeSource.value = text;
    switchMode("tercume");
    flashRuzgarDurum("Kaynak metin Tercüme atölyesine aktarıldı.");
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

async function refreshVideoEngineHint() {
  if (!el.videoEngineHint) return;
  try {
    const r = await fetch(`${API}/api/health`, { method: "GET" });
    if (!r.ok) throw new Error("no-health");
    const j = await r.json();
    if (j.ffprobe) {
      el.videoEngineHint.textContent =
        "Ortam inceleme hazır — «Medya bilgisi». v2 kesim; v3 altyazı/ses; v4 çizelge + altyazıyı Tercüme’ye gönder. Yerel araçlar sistem yolunda olmalı; çıktı .ruzgar-video-export/.";
    } else {
      el.videoEngineHint.textContent =
        "Ortam inceleme aracı yok — FFmpeg paketini kurup sistem yoluna ekleyin; ardından yerel sunucuyu yeniden başlatın.";
    }
  } catch {
    el.videoEngineHint.textContent =
      "Sunucu yok — video işlemleri için ilim-assistant yerel sunucusu çalışır olmalıdır.";
  }
}

async function runVideoProbeFromFile() {
  const f = el.videoFileInput?.files?.[0];
  if (!f) {
    flashRuzgarDurum("Önce bir dosya seçin.");
    return;
  }
  flashRuzgarDurum("Ortam inceleniyor…");
  setStatus("Medya özeti…", "Rüzgar");
  try {
    const fd = new FormData();
    fd.append("file", f, f.name || "media.bin");
    const res = await fetch(`${API}/api/video/probe`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      if (el.videoProbeJson) el.videoProbeJson.textContent = String(detail || res.statusText || "Hata");
      flashRuzgarDurum(String(detail || "Medya özeti alınamadı"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const sum = j.summary;
    if (sum && typeof sum.duration_sec === "number" && Number.isFinite(sum.duration_sec)) {
      lastVideoProbeDurationSec = Math.max(0, sum.duration_sec);
    }
    if (el.videoProbeJson) el.videoProbeJson.textContent = formatVideoSummaryHuman(sum);
    updateVideoTimelineUI();
    flashRuzgarDurum("Medya özeti hazır.");
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    if (el.videoProbeJson) el.videoProbeJson.textContent = String(e && e.message ? e.message : e);
    flashRuzgarDurum("Medya özeti isteği başarısız.");
    setStatus("Hazır", "Rüzgar");
  }
}

function appendVideoJobNote(rel) {
  const line = `\n\n— Son çıktı —\n${rel}\n`;
  if (el.videoProbeJson) {
    el.videoProbeJson.textContent = `${String(el.videoProbeJson.textContent || "").trimEnd()}${line}`;
  }
  flashRuzgarDurum(`Kaydedildi: ${rel}`);
}

function openVideoExportFolder() {
  if (window.ruzgarApi?.openWorkspaceRel) {
    void window.ruzgarApi.openWorkspaceRel(".ruzgar-video-export");
    flashRuzgarDurum("Çıktı klasörü açılıyor…");
  } else {
    flashRuzgarDurum("Klasörü açmak için masaüstü Rüzgar kullanın.");
  }
}

async function runVideoTrimJob() {
  const rel = String(el.videoRelWorkspace?.value || "").trim();
  const fd = new FormData();
  fd.append("start_sec", String(el.videoStartSec?.value ?? "0"));
  const du = String(el.videoDurationSec?.value || "").trim();
  const en = String(el.videoEndSec?.value || "").trim();
  if (du) fd.append("duration_sec", du);
  else if (en) fd.append("end_sec", en);
  else {
    flashRuzgarDurum("Süre veya bitiş süresi girin.");
    return;
  }
  fd.append("copy_streams", el.videoCopyStreams?.checked ? "true" : "false");
  if (rel) {
    fd.append("rel", rel);
  } else {
    const f = el.videoFileInput?.files?.[0];
    if (!f) {
      flashRuzgarDurum("Göreli yol yazın veya dosya seçin.");
      return;
    }
    fd.append("file", f, f.name);
  }
  flashRuzgarDurum("Kesim işleniyor…");
  setStatus("Kesim işleniyor…", "Rüzgar");
  try {
    const res = await fetch(`${API}/api/video/trim`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      flashRuzgarDurum(String(detail || res.statusText || "Kesim başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoTranscodeJob() {
  const rel = String(el.videoRelWorkspace?.value || "").trim();
  const fd = new FormData();
  if (rel) {
    fd.append("rel", rel);
  } else {
    const f = el.videoFileInput?.files?.[0];
    if (!f) {
      flashRuzgarDurum("Göreli yol yazın veya dosya seçin.");
      return;
    }
    fd.append("file", f, f.name);
  }
  flashRuzgarDurum("Dönüştürme…");
  setStatus("Dönüştürülüyor…", "Rüzgar");
  try {
    const res = await fetch(`${API}/api/video/transcode`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      flashRuzgarDurum(String(detail || res.statusText || "Dönüştürme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoConcatJob() {
  const a = String(el.videoConcatA?.value || "").trim();
  const b = String(el.videoConcatB?.value || "").trim();
  if (!a || !b) {
    flashRuzgarDurum("İki göreli yol girin.");
    return;
  }
  flashRuzgarDurum("Birleştiriliyor…");
  setStatus("Dosyalar birleştiriliyor…", "Rüzgar");
  try {
    const res = await fetch(`${API}/api/video/concat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        rel_a: a,
        rel_b: b,
        copy_streams: !!(el.videoConcatCopy && el.videoConcatCopy.checked),
      }),
    });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      flashRuzgarDurum(String(detail || res.statusText || "Birleştirme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoBurnSubJob() {
  const v = String(el.videoRelBurnVideo?.value || "").trim();
  const s = String(el.videoRelBurnSub?.value || "").trim();
  if (!v || !s) {
    flashRuzgarDurum("Video ve altyazı için göreli yol girin.");
    return;
  }
  const fd = new FormData();
  fd.append("rel_video", v);
  fd.append("rel_sub", s);
  flashRuzgarDurum("Altyazı görüntüye gömülüyor…");
  setStatus("Altyazı işleniyor…", "Rüzgar");
  try {
    const res = await fetch(`${API}/api/video/burn-subtitles`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      flashRuzgarDurum(String(detail || res.statusText || "Altyazı gömme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoMuxAudioJob() {
  const v = String(el.videoRelMuxVideo?.value || "").trim();
  const a = String(el.videoRelMuxAudio?.value || "").trim();
  if (!v || !a) {
    flashRuzgarDurum("Video ve ses dosyası için göreli yol girin.");
    return;
  }
  const fd = new FormData();
  fd.append("rel_video", v);
  fd.append("rel_audio", a);
  fd.append("copy_video", el.videoMuxCopyVideo?.checked ? "true" : "false");
  fd.append("shortest", el.videoMuxShortest?.checked ? "true" : "false");
  flashRuzgarDurum("Ses birleştiriliyor…");
  setStatus("Ses ekleniyor…", "Rüzgar");
  try {
    const res = await fetch(`${API}/api/video/mux-audio`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      } else if (detail != null && typeof detail !== "string") {
        detail = JSON.stringify(detail);
      }
      flashRuzgarDurum(String(detail || res.statusText || "Ses birleştirme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  }
}

function wireVideoAtolye() {
  if (el.videoFileInput && el.videoPreview && el.videoFileInput.dataset.videoWired !== "1") {
    el.videoFileInput.dataset.videoWired = "1";
    el.videoFileInput.addEventListener("change", () => {
      const f = el.videoFileInput.files && el.videoFileInput.files[0];
      if (!f) return;
      try {
        if (videoPreviewObjectUrl) URL.revokeObjectURL(videoPreviewObjectUrl);
      } catch (_) {
        /* ignore */
      }
      videoPreviewObjectUrl = URL.createObjectURL(f);
      el.videoPreview.src = videoPreviewObjectUrl;
      videoTimelineIn = null;
      videoTimelineOut = null;
      lastVideoProbeDurationSec = 0;
      if (el.videoProbeJson) {
        el.videoProbeJson.textContent =
          "Dosya değişti. «Medya bilgisi» ile teknik özeti güncelleyin.";
      }
    });
  }
  if (el.btnVideoProbe) {
    el.btnVideoProbe.addEventListener("click", () => {
      void runVideoProbeFromFile();
    });
  }
  if (el.btnVideoClear) {
    el.btnVideoClear.addEventListener("click", () => {
      try {
        if (videoPreviewObjectUrl) URL.revokeObjectURL(videoPreviewObjectUrl);
      } catch (_) {
        /* ignore */
      }
      videoPreviewObjectUrl = null;
      if (el.videoFileInput) el.videoFileInput.value = "";
      if (el.videoPreview) {
        el.videoPreview.removeAttribute("src");
        el.videoPreview.load();
      }
      if (el.videoProbeJson) {
        el.videoProbeJson.textContent =
          "Sıfırlandı. Yeni dosya seçip «Medya bilgisi» ile devam edin.";
      }
      if (el.videoRelWorkspace) el.videoRelWorkspace.value = "";
      if (el.videoRelBurnVideo) el.videoRelBurnVideo.value = "";
      if (el.videoRelBurnSub) el.videoRelBurnSub.value = "";
      if (el.videoRelMuxVideo) el.videoRelMuxVideo.value = "";
      if (el.videoRelMuxAudio) el.videoRelMuxAudio.value = "";
      if (el.videoRelSubTranslate) el.videoRelSubTranslate.value = "";
      resetVideoTimelineMarks();
      resetVideoTimelineProbeDuration();
      flashRuzgarDurum("Video paneli sıfırlandı.");
    });
  }
  if (el.btnVideoTrim) {
    el.btnVideoTrim.addEventListener("click", () => {
      void runVideoTrimJob();
    });
  }
  if (el.btnVideoTranscode) {
    el.btnVideoTranscode.addEventListener("click", () => {
      void runVideoTranscodeJob();
    });
  }
  if (el.btnVideoConcat) {
    el.btnVideoConcat.addEventListener("click", () => {
      void runVideoConcatJob();
    });
  }
  if (el.btnVideoOpenExport) {
    el.btnVideoOpenExport.addEventListener("click", () => {
      openVideoExportFolder();
    });
  }
  if (el.btnVideoBurnSub) {
    el.btnVideoBurnSub.addEventListener("click", () => {
      void runVideoBurnSubJob();
    });
  }
  if (el.btnVideoMuxAudio) {
    el.btnVideoMuxAudio.addEventListener("click", () => {
      void runVideoMuxAudioJob();
    });
  }
  wireVideoTimeline();
}

async function refreshArsivTreeInto(containerEl) {
  if (!containerEl) return;
  containerEl.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
  try {
    const items = await workspaceListDir(OKUMA_ARSIV_ROOT);
    containerEl.innerHTML = "";
    for (const it of items) {
      containerEl.appendChild(createCodeTreeBranch(it, 0));
    }
    if (!items.length) {
      containerEl.innerHTML =
        `<div class="code-file-placeholder">Arşiv boş veya klasör yok. Klasörü oluşturun: <code>ilim-assistant/arsiv</code> — içine .md / .txt ekleyin.</div>`;
    }
  } catch (e) {
    containerEl.innerHTML =
      `<div class="code-file-placeholder">Arşiv listelenemedi: ${esc(String(e && e.message ? e.message : e))}</div>`;
  }
}

async function okumaAtolyeRefreshTree() {
  await refreshArsivTreeInto(el.ilimFileList);
}

function wireOkumaAtolye() {
  if (el.ilimFileList && el.ilimFileList.dataset.okumaWired !== "1") {
    el.ilimFileList.dataset.okumaWired = "1";
    el.ilimFileList.addEventListener("click", (ev) => {
      void handleArsivTreeClick(ev, el.ilimFileList, openOkumaArsivFile);
    });
  }
  if (el.btnIlimRefresh) {
    el.btnIlimRefresh.addEventListener("click", () => {
      void okumaAtolyeRefreshTree();
      flashRuzgarDurum("İlim arşivi yenilendi.");
    });
  }
  if (el.btnIlimToChat) {
    el.btnIlimToChat.addEventListener("click", () => {
      const t = String(el.ilimFileContent?.value || "").trim();
      if (!t) {
        flashRuzgarDurum("Önce sol listeden bir dosya açın veya metin girin.");
        return;
      }
      const chunk = t.length > 12000 ? `${t.slice(0, 12000)}\n\n… (kısaltıldı)` : t;
      if (el.input) {
        el.input.value = chunk;
        el.input.focus();
        flashRuzgarDurum("Metin sohbet kutusuna aktarıldı.");
      }
    });
  }
  if (el.btnIlimSummary) {
    el.btnIlimSummary.addEventListener("click", () => {
      void ilimSendPreparedPrompt("summary");
    });
  }
  if (el.btnIlimComment) {
    el.btnIlimComment.addEventListener("click", () => {
      void ilimSendPreparedPrompt("comment");
    });
  }
  if (el.ilimFileContent) {
    el.ilimFileContent.addEventListener("input", () => updateIlimTextStats());
  }
  if (el.btnIlimOpenArchive) {
    el.btnIlimOpenArchive.addEventListener("click", () => {
      if (window.ruzgarApi?.openWorkspaceRel) {
        void window.ruzgarApi.openWorkspaceRel("ilim-assistant/arsiv");
        flashRuzgarDurum("Arşiv klasörü açılıyor…");
      } else {
        flashRuzgarDurum("Klasörü açmak için masaüstü Rüzgar kullanın.");
      }
    });
  }
}

async function ilimSendPreparedPrompt(kind) {
  const t = String(el.ilimFileContent?.value || "").trim();
  if (!t) {
    flashRuzgarDurum("Önce bir dosya açın veya metin girin.");
    return;
  }
  const chunk = t.length > 24000 ? `${t.slice(0, 24000)}\n\n… (mimar için kısaltıldı)` : t;
  const src = ilimOpenRel ? `\n[Kaynak dosya: ${ilimOpenRel}]\n` : "";
  const prompts = {
    summary: `${src}Ümit abi, aşağıdaki metni okuma atölyesinden iletiyorum. Kısa ve net bir özet çıkar; gerekiyorsa madde işaretleri kullan. Uzun giriş yazma.\n\n---\n\n${chunk}`,
    comment: `${src}Ümit abi, aşağıdaki metni okuma atölyesinden iletiyorum. Ana fikirleri, güçlü/zayıf yanları ve open questions (varsa) ile birlikte dengeli bir okuma notu yaz; gereksiz tekrar yapma.\n\n---\n\n${chunk}`,
  };
  const msg = prompts[kind] || prompts.summary;
  flashRuzgarDurum("Rüzgar’a iletiliyor…");
  await sendMessageWithText(msg, { skipUserBubble: false });
}

async function saveProgramlamaAtolyeBuffer() {
  const code = String(el.codeEditor?.value ?? "");
  let rel = atolyeOpenRel;
  if (!rel) {
    const suggested = window.prompt(
      "Kaydetmek için proje köküne göre göreli yol yazın (örn. ruzgar-desktop/ornek.py):",
      "ruzgar-desktop/ornek.py"
    );
    if (suggested == null) return;
    rel = suggested.trim().replace(/^[/\\]+/, "");
    if (!rel) return;
  }
  if (!window.ruzgarApi?.writeText) {
    flashRuzgarDurum("Kaydetme yalnızca masaüstü Rüzgar’da (Electron).");
    return;
  }
  try {
    const w = await window.ruzgarApi.writeText(rel, code);
    if (!w?.ok) {
      setCodeOutput(w?.error || "Yazılamadı.");
      flashRuzgarDurum("Kaydetme başarısız.");
      return;
    }
    atolyeOpenRel = rel;
    updateProgramlamaActiveFileLabel();
    flashRuzgarDurum("Kaydedildi.");
    setCodeOutput(`Kaydedildi: ${rel}`);
    void programlamaAtolyeRefreshRoot();
  } catch (e) {
    setCodeOutput(`Kayıt hatası: ${e && e.message ? e.message : e}`);
  }
}

function wireProgrammingWorkbench() {
  if (el.codeFileTree && el.codeFileTree.dataset.treeWired !== "1") {
    el.codeFileTree.dataset.treeWired = "1";
    el.codeFileTree.addEventListener("click", (ev) => {
      void handleCodeTreeClick(ev);
    });
  }
  if (el.btnCodeRefresh) {
    el.btnCodeRefresh.addEventListener("click", () => {
      void programlamaAtolyeRefreshRoot();
      flashRuzgarDurum("Proje ağacı yenilendi.");
    });
  }
  if (el.btnCodeSave) {
    el.btnCodeSave.addEventListener("click", () => {
      void saveProgramlamaAtolyeBuffer();
    });
  }
  if (el.codeEditor) {
    el.codeEditor.addEventListener("keydown", (e) => {
      if (!e.ctrlKey && !e.metaKey) return;
      if (e.key === "s" || e.key === "S") {
        e.preventDefault();
        void saveProgramlamaAtolyeBuffer();
      }
    });
  }
  if (el.btnCodeNew) {
    el.btnCodeNew.addEventListener("click", () => {
      if (el.codeEditor) el.codeEditor.value = "";
      atolyeOpenRel = null;
      updateProgramlamaActiveFileLabel();
      setCodeOutput("Yeni çalışma alanı hazır.");
      el.codeEditor?.focus();
    });
  }
  if (el.btnCodeExplain) {
    el.btnCodeExplain.addEventListener("click", () => sendCodeAssistantPrompt("explain"));
  }
  if (el.btnCodeFix) {
    el.btnCodeFix.addEventListener("click", () => sendCodeAssistantPrompt("fix"));
  }
  if (el.btnCodeRefactor) {
    el.btnCodeRefactor.addEventListener("click", () => sendCodeAssistantPrompt("refactor"));
  }
  if (el.btnCodeTest) {
    el.btnCodeTest.addEventListener("click", () => sendCodeAssistantPrompt("test"));
  }
  if (el.btnCodeRun) {
    el.btnCodeRun.addEventListener("click", () => {
      void runCodeFromWorkbench();
    });
  }
  if (el.btnCodeOutputClear) {
    el.btnCodeOutputClear.addEventListener("click", () => setCodeOutput(""));
  }
}

function wireDynamicWorkbench() {
  if (el.btnLayoutFull) el.btnLayoutFull.addEventListener("click", () => setWorkbenchLayout("layout-full"));
  if (el.btnLayoutSplit2) el.btnLayoutSplit2.addEventListener("click", () => setWorkbenchLayout("layout-split2"));
  if (el.btnLayoutSplit4) el.btnLayoutSplit4.addEventListener("click", () => setWorkbenchLayout("layout-split4"));
  wireProgrammingWorkbench();
  wireOkumaAtolye();
  wireTercumeAtolye();
  wireSesAtolye();
  wireVideoAtolye();
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

// ---------- Asistan yanıtında kod bloklarını "akıllı kart" olarak render ----------
// Programlama Atölyesi'nin DNA'sı: Rüzgar kod yazınca kullanıcı kopyala-yapıştırla
// uğraşmasın; tek tık ile editöre koysun, çalıştırsın.

const CODE_LANG_NORMALIZE = {
  py: "python",
  python: "python",
  python3: "python",
  js: "javascript",
  javascript: "javascript",
  node: "javascript",
  nodejs: "javascript",
  ts: "typescript",
  typescript: "typescript",
  rs: "rust",
  rust: "rust",
  go: "go",
  golang: "go",
  cs: "csharp",
  csharp: "csharp",
  "c#": "csharp",
  kotlin: "kotlin",
  kt: "kotlin",
  swift: "swift",
  dart: "dart",
  vue: "vue",
  jsx: "jsx",
  tsx: "tsx",
  java: "java",
  cpp: "cpp",
  cxx: "cpp",
  cc: "cpp",
  c: "c",
  sqlite: "sql",
  sql: "sql",
  yaml: "yaml",
  yml: "yaml",
  md: "markdown",
  markdown: "markdown",
  html: "html",
  htm: "html",
  css: "css",
  json: "json",
  bash: "bash",
  sh: "bash",
  shell: "bash",
  pwsh: "powershell",
  ps1: "powershell",
  powershell: "powershell",
  text: "text",
  txt: "text",
  "": "text",
};

function normalizeCodeLang(raw) {
  const t = String(raw || "").trim().toLowerCase();
  return CODE_LANG_NORMALIZE[t] || t || "text";
}

function codeLangIsRunnable(lang) {
  const v = normalizeCodeLang(lang);
  return v === "python" || v === "javascript";
}

let _codeCardCounter = 0;
function renderCodeCard(rawCode, lang) {
  const code = String(rawCode || "").replace(/\n+$/, "");
  const norm = normalizeCodeLang(lang);
  const id = `rc-code-${Date.now().toString(36)}-${++_codeCardCounter}`;
  const safe = esc(code);
  const safeLang = esc(norm);
  const runnable = codeLangIsRunnable(norm);
  const runBtn = runnable
    ? `<button type="button" class="btn-primary btn-compact code-card-run" data-card="${id}" data-lang="${safeLang}" title="Programlama Atölyesi'nde çalıştır">Çalıştır</button>`
    : "";
  return (
    `<div class="code-card" id="${id}" data-lang="${safeLang}">` +
    `<div class="code-card-head">` +
    `<span class="code-card-lang">${safeLang}</span>` +
    `<span class="code-card-spacer"></span>` +
    `<button type="button" class="btn-secondary btn-compact code-card-copy" data-card="${id}" title="Kodu panoya kopyala">Kopyala</button>` +
    `<button type="button" class="btn-secondary btn-compact code-card-paste" data-card="${id}" data-lang="${safeLang}" title="Programlama Atölyesi editörüne ekle">Editöre Ekle</button>` +
    runBtn +
    `</div>` +
    `<pre class="code-card-body"><code>${safe}</code></pre>` +
    `</div>`
  );
}

/** Asistan metnini güvenli HTML'e çevir; ```fenced``` blokları kart olur. */
function renderAssistantRichHtml(text) {
  const src = String(text || "");
  /** SYNC: doğruluk testi `ruzgar-desktop/tools/phase11_code_cards_checks.mjs` */
  /** Açılış: isteğe bağlı dil etiketi etrafında boşluk; içerikten sonra isteğe bağlı newline + kapanış ``` */
  const fence =
    /```[ \t]*([a-zA-Z0-9_+#.-]*)[ \t]*\r?\n([\s\S]*?)\n?[ \t]*```/g;
  let out = "";
  let last = 0;
  let m;
  while ((m = fence.exec(src)) !== null) {
    const before = src.slice(last, m.index);
    if (before) out += esc(before).replace(/\n/g, "<br>");
    out += renderCodeCard(m[2], m[1]);
    last = m.index + m[0].length;
  }
  const tail = src.slice(last);
  if (tail) out += esc(tail).replace(/\n/g, "<br>");
  return out || esc(src);
}

/** Yanıt balonundaki kod kartı butonlarını canlandır. */
function wireAssistantCodeButtons(scope) {
  const root = scope || document;
  root.querySelectorAll(".code-card-copy").forEach((btn) => {
    if (btn.dataset.wired === "1") return;
    btn.dataset.wired = "1";
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-card");
      const card = id ? document.getElementById(id) : null;
      const codeEl = card ? card.querySelector("code") : null;
      const code = codeEl ? codeEl.textContent || "" : "";
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          void navigator.clipboard.writeText(code);
        } else {
          const ta = document.createElement("textarea");
          ta.value = code;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          ta.remove();
        }
        flashRuzgarDurum("Kod panoya kopyalandı.");
      } catch (_) {
        flashRuzgarDurum("Kopyalama başarısız.");
      }
    });
  });
  root.querySelectorAll(".code-card-paste").forEach((btn) => {
    if (btn.dataset.wired === "1") return;
    btn.dataset.wired = "1";
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-card");
      const lang = btn.getAttribute("data-lang") || "text";
      const card = id ? document.getElementById(id) : null;
      const codeEl = card ? card.querySelector("code") : null;
      const code = codeEl ? codeEl.textContent || "" : "";
      pasteCodeIntoProgramlamaAtolye(code, lang, false);
    });
  });
  root.querySelectorAll(".code-card-run").forEach((btn) => {
    if (btn.dataset.wired === "1") return;
    btn.dataset.wired = "1";
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-card");
      const lang = btn.getAttribute("data-lang") || "python";
      const card = id ? document.getElementById(id) : null;
      const codeEl = card ? card.querySelector("code") : null;
      const code = codeEl ? codeEl.textContent || "" : "";
      pasteCodeIntoProgramlamaAtolye(code, lang, true);
    });
  });
}

/** Kod kartından gelen kodu Programlama Atölyesi editörüne koy; istenirse hemen çalıştır. */
function pasteCodeIntoProgramlamaAtolye(code, lang, alsoRun) {
  if (currentMode !== "programlama") {
    switchMode("programlama");
  }
  atolyeOpenRel = null;
  updateProgramlamaActiveFileLabel();
  const norm = normalizeCodeLang(lang);
  if (el.codeLanguage) {
    const opts = Array.from(el.codeLanguage.options || []);
    const match = opts.find((o) => o.value === norm);
    if (match) el.codeLanguage.value = norm;
  }
  if (el.codeEditor) {
    el.codeEditor.value = String(code || "");
    el.codeEditor.focus();
    try {
      el.codeEditor.setSelectionRange(0, 0);
      el.codeEditor.scrollTop = 0;
    } catch (_) {
      /* ignore */
    }
  }
  if (alsoRun && codeLangIsRunnable(norm)) {
    flashRuzgarDurum("Kod editöre eklendi, çalıştırılıyor…");
    void runCodeFromWorkbench();
  } else if (alsoRun) {
    flashRuzgarDurum(`${norm} dili henüz çalıştırılamıyor; editöre eklendi.`);
  } else {
    flashRuzgarDurum("Kod editöre eklendi.");
  }
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
  updateIlimActiveFileLabel();
  updateIlimTextStats();
  await okumaAtolyeRefreshTree();
}

async function checkApi() {
  try {
    const r = await fetch(`${API}/api/health`, { method: "GET" });
    const j = await r.json();
    if (j.ok) {
      el.api.textContent = j.stt ? "Sunucu ✓ metne döküm" : "Sunucu ✓";
      let apiTitle = j.stt
        ? "Yerel sunucu — konuşmayı metne düşürme (yerel model veya tarayıcı tanıma)"
        : "Sunucu bağlı — konuşmayı metne düşürmek için: pip install faster-whisper ve/veya SpeechRecognition";
      if (j.pdf_text === false) {
        apiTitle += " | PDF için: pip install pypdf";
      }
      if (j.docx_text === false) {
        apiTitle += " | DOCX için: pip install python-docx";
      }
      if (j.ffprobe === false) {
        apiTitle += " | Video: FFmpeg sistem yolunda olmalı (inceleme aracı)";
      }
      if (j.ffmpeg === false) {
        apiTitle += " | FFmpeg ikilisi bulunamadı";
      }
      el.api.title = apiTitle;
      el.api.className = "tech-chip ok";
      setStatus("Hazır", "Rüzgar");
      void tryShowHafizaReminder();
      return true;
    }
  } catch {
    el.api.textContent = "Sunucu kapalı";
    el.api.className = "tech-chip err";
    el.api.title = "";
    setStatus("Önce yerel sunucuyu başlatın (ilim-assistant)", "Rüzgar");
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
          setStatus("Sunucu hatası", "Rüzgar");
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
          setStatus("Sunucu hatası", "Rüzgar");
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
    setStatus("Sunucu yok — kayıt atlanamadı", "Rüzgar");
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
        setStatus("Görsel üretim hatası", "Rüzgar");
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
    use_web: el.web ? !!el.web.checked : !["ses", "okuma", "tercume", "hafiza", "hizli"].includes(currentMode),
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
  let streamAssistHtmlRaf = null;

  /** Akış sırasında: kapalı fenced blok oluşunca kod kartları; değilse satır sonlarıyla düzgün metin */
  function paintStreamingAssistantBubble() {
    streamAssistHtmlRaf = null;
    if (!responseBubble) return;
    const repaired = repairMojibake(full);
    if (repaired.includes("```")) {
      responseBubble.innerHTML = renderAssistantRichHtml(repaired);
      wireAssistantCodeButtons(responseBubble);
    } else {
      responseBubble.innerHTML = esc(repaired).replace(/\n/g, "<br>");
    }
    el.chat.scrollTop = el.chat.scrollHeight;
  }

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
      if (streamAssistHtmlRaf != null) {
        cancelAnimationFrame(streamAssistHtmlRaf);
        streamAssistHtmlRaf = null;
      }
      streamAssistHtmlRaf = window.requestAnimationFrame(() => {
        paintStreamingAssistantBubble();
      });
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
      if (streamAssistHtmlRaf != null) {
        cancelAnimationFrame(streamAssistHtmlRaf);
        streamAssistHtmlRaf = null;
      }
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
      // Streaming bittikten sonra zenginleştirilmiş render: ```fenced``` kod blokları
      // Programlama Atölyesi'ne tek tıkla atılabilir kart hâline gelir.
      if (full.includes("```")) {
        responseBubble.innerHTML = renderAssistantRichHtml(full);
        wireAssistantCodeButtons(responseBubble);
      } else {
        responseBubble.innerHTML = esc(full).replace(/\n/g, "<br>");
      }
      lastAssistantReply = full;
      updateDynamicWorkbench();
      renderOrchestraBridge(ev.orchestra);
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
    const genelBakCtrl = new AbortController();
    const genelBakTo = window.setTimeout(() => genelBakCtrl.abort(), 6000);
    let gr;
    try {
      gr = await fetch(`${API}/api/hafiza/genel-bak`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ message: userText }),
        cache: "no-store",
        signal: genelBakCtrl.signal,
      });
    } finally {
      window.clearTimeout(genelBakTo);
    }
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
  clearOrchestraBridge();
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

/** Ses atölyesi transkriptini Edge TTS ile (varsa) veya Web Speech ile okur. */
async function speakStudioTranscript(raw) {
  const plain = ttsPlainForSpeech(raw || "");
  if (!plain) {
    flashRuzgarDurum("Seslendirilecek metin yok.");
    return;
  }
  let kar = "asistan";
  try {
    const rs = await fetch(`${API}/api/ses/settings`);
    if (rs.ok) {
      const j = await rs.json();
      kar = normalizeKarakterForTts(j.karakter);
    }
  } catch (_) {
    /* ignore */
  }
  try {
    const res = await fetch(`${API}/api/tts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: plain,
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
  speakTextImmediate(plain);
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
        .catch(() => setStatus("Sunucu yok — ses ayarı yazılamadı", "Rüzgar"));
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
