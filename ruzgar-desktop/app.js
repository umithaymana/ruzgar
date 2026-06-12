/**
 * Bağlantı hattı: UI → Tünel → Colab API (aynı köke WebSocket/SSE/Fetch).
 * Beyin adresi önceliği: preload + ruzgar_remote_api.txt > ?api > localStorage > yalın yerel.
 * Kök sonda `/api` ise kırpılır — aksi halde fetch `.../api/api/merkezi-bellek` ile 404 verir.
 */
const RUZGAR_LOCAL_API_PORT = 8779;
const RUZGAR_EXPECTED_BUILD_REV = "2026-05-27-ruzgar-faz98-v107";
const RUZGAR_LOCAL_API_FALLBACK = `http://127.0.0.1:${RUZGAR_LOCAL_API_PORT}`;

function migrateLegacyApiUrl(raw) {
  const s = String(raw || "").trim();
  if (!s) return s;
  return s
    .replace(/127\.0\.0\.1:8777/gi, `127.0.0.1:${RUZGAR_LOCAL_API_PORT}`)
    .replace(/localhost:8777/gi, `localhost:${RUZGAR_LOCAL_API_PORT}`);
}

function normalizeRuzgarApiRootTail(raw) {
  let s = migrateLegacyApiUrl(String(raw || "").trim()).replace(/\/+$/, "");
  if (!s) return "";
  if (/\/api$/i.test(s)) {
    s = s.replace(/\/api$/i, "").replace(/\/+$/, "");
  }
  return s;
}

function resolveRuzgarApiRoot() {
  const fallback = RUZGAR_LOCAL_API_FALLBACK;
  try {
    if (typeof window !== "undefined") {
      const injected = window.__RUZGAR_API_ROOT__;
      if (injected) {
        const n = normalizeRuzgarApiRootTail(String(injected).trim());
        if (n) return n;
      }
      if (window.location?.pathname?.startsWith("/ui")) {
        const origin = normalizeRuzgarApiRootTail(window.location.origin);
        if (origin) return origin;
      }
    }
  } catch (_) {
    /* yok say */
  }
  try {
    const remote =
      typeof window !== "undefined" &&
      window.ruzgarApi?.getRemoteBrainEndpoint?.();
    if (remote) {
      const n = normalizeRuzgarApiRootTail(String(remote).trim());
      if (n) return n;
    }
  } catch (_) {
    /* yok say */
  }
  try {
    const qs = new URLSearchParams(window.location.search).get("api");
    if (qs) {
      const n = normalizeRuzgarApiRootTail(String(qs).trim());
      if (n) return n;
    }
  } catch (_) {
    /* yok say */
  }
  try {
    if (typeof localStorage !== "undefined") {
      const ls = localStorage.getItem("ruzgarApi");
      if (ls) {
        const migrated = migrateLegacyApiUrl(ls);
        if (migrated !== ls) {
          try {
            localStorage.setItem("ruzgarApi", migrated);
          } catch (_) {
            /* yok say */
          }
        }
        const n = normalizeRuzgarApiRootTail(migrated);
        if (n) return n;
      }
    }
  } catch (_) {
    /* yok say */
  }
  return normalizeRuzgarApiRootTail(fallback) || fallback;
}

const API = resolveRuzgarApiRoot();
/** Faz F1/G3 — dosya bağlamı + oturum paketi */
const anaMotorUploadQueue = [];
let anaMotorUploadSessionId = null;
let anaMotorLastUserTopic = "";
let anaMotorLastNebulaCard = null;
let anaMotorNebulaApplyPoll = null;
let anaMotorPaketAutoPoll = null;
let anaMotorLastPaketOzetCard = null;
let anaMotorLastReminders = [];
let anaMotorRemindNotifyPoll = null;
const anaMotorNotifiedHintKeys = new Set();
console.info("[RÜZGAR Connection Bridge] API kök:", API);
const RUZGAR_CHAT_FULL_TIMEOUT_MS = 180000;
/** Kısa selam / nasılsın — Ollama yavaşken 12 sn yetmiyordu */
const RUZGAR_CHAT_CASUAL_TIMEOUT_MS = 25000;
/** Video indirme — /api/video/download; sohbet 180sn sınırından bağımsız */
const RUZGAR_VIDEO_DOWNLOAD_TIMEOUT_MS = 600000;
/** Metinden video oluşturma — plan + TTS + FFmpeg (uzun sürebilir) */
const RUZGAR_VIDEO_CREATE_TIMEOUT_MS = 900000;
/** Otonom görev (görev: / kod modu) — çok tur + verify; 180 sn yetmez */
const RUZGAR_CHAT_PROGRAMMING_AGENT_TIMEOUT_MS = 900000;
const RUZGAR_DISABLE_STREAMING = true;

const RUZGAR_VIDEO_URL_RE = /https?:\/\/[^\s<>\"{}|\\^`\[\]]+/gi;
const RUZGAR_VIDEO_DL_HINT_RE =
  /(?:\bindir\b|\bindirme\b|download|youtube|youtu\.be|dailymotion|dai\.ly|vimeo|tiktok|twitch|\boynat\b|\baç\b|\bac\b|\bizle\b|videoyu|filmi|sinema|burada\s+oynat|linki?\b)/i;
const RUZGAR_VIDEO_HOST_RE =
  /(?:youtube\.com|youtu\.be|youtube-nocookie\.com|vimeo\.com|dailymotion\.com|dai\.ly|tiktok\.com|twitch\.tv|twitter\.com|x\.com|facebook\.com|fb\.watch|instagram\.com|bilibili\.com)/i;
const RUZGAR_WEB_CINEMA_HOST_RE =
  /(?:^|\.)dailymotion\.com$|^dai\.ly$|(?:^|\.)facebook\.com$|(?:^|\.)fb\.watch$|(?:^|\.)instagram\.com$/i;

/** Konuşma hattı teşhisi — varsayılan kapalı; yalnızca konsol (?debug=1). Sohbette mavi JSON paneli yok. */
function isRuzgarUiDebugEnabled() {
  try {
    if (new URLSearchParams(window.location.search).get("debug") === "1") return true;
    if (localStorage.getItem("ruzgarUiDebug") === "1") return true;
  } catch (_) {
    /* yok say */
  }
  return false;
}
const RUZGAR_UI_DEBUG = isRuzgarUiDebugEnabled();

function ruzgarDebugLog(label, detail) {
  if (!RUZGAR_UI_DEBUG) return;
  console.info("[RÜZGAR]", label, detail ?? "");
}

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
    return `ws://127.0.0.1:${RUZGAR_LOCAL_API_PORT}`;
  }
}

/** Yerel `desktop_server` (8779): WebSocket Köprüsü olmadan doğrudan SSE — öğrenme merkezi her turda garanti */
function ruzgarLikelyLocalDesktopApi() {
  try {
    const u = new URL(API);
    const h = String(u.hostname || "").toLowerCase();
    if (h !== "127.0.0.1" && h !== "localhost") return false;
    const rawPort =
      u.port ||
      (u.protocol === "https:" ? "443" : u.protocol === "http:" ? "80" : "");
    return String(rawPort) === String(RUZGAR_LOCAL_API_PORT);
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
const UI_MANIFEST_POLL_MS = 3000;

const MODE_QS = new URLSearchParams(window.location.search);

function normalizeMotorMode(mode) {
  let m = String(mode || "").trim().toLowerCase();
  if (m === "okuma") m = "mimar";
  return m || "genel";
}

function persistMotorSession() {
  const mode = normalizeMotorMode(currentMode);
  try {
    sessionStorage.setItem("ruzgar_last_motor", mode);
    sessionStorage.setItem("ruzgar_motor_nav_stack", JSON.stringify(motorNavStack));
    sessionStorage.setItem("ruzgar_motor_nav_index", String(motorNavIndex));
  } catch {
    /* ignore */
  }
  return mode;
}

function restoreMotorNavStack() {
  try {
    const raw = sessionStorage.getItem("ruzgar_motor_nav_stack");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || !parsed.length) return null;
    return parsed.map(normalizeMotorMode).filter(Boolean);
  } catch {
    return null;
  }
}

let currentMode = normalizeMotorMode(MODE_QS.get("mode") || "");
/** Ana Motor hub: genel sohbet kalır, motor paneli arka planda (Faz B) */
let hubQuietMotor = null;
if (!MODE_QS.get("mode")) {
  try {
    const saved = sessionStorage.getItem("ruzgar_last_motor");
    if (saved) currentMode = normalizeMotorMode(saved);
  } catch {
    /* ignore */
  }
}
if (!currentMode) currentMode = "genel";

/** Sol motor menüsü geçmişi — geri/ileri (tüm motorlar, sınırsız) */
const motorNavStack = restoreMotorNavStack() || [currentMode];
let motorNavIndex = 0;
try {
  const idx = parseInt(sessionStorage.getItem("ruzgar_motor_nav_index") || "", 10);
  if (Number.isFinite(idx)) {
    motorNavIndex = Math.max(0, Math.min(idx, motorNavStack.length - 1));
  } else {
    motorNavIndex = Math.max(0, motorNavStack.lastIndexOf(currentMode));
  }
} catch {
  motorNavIndex = Math.max(0, motorNavStack.lastIndexOf(currentMode));
}
if (motorNavIndex < 0) motorNavIndex = motorNavStack.length - 1;
if (!motorNavStack.includes(currentMode)) {
  motorNavStack.push(currentMode);
  motorNavIndex = motorNavStack.length - 1;
} else if (MODE_QS.get("mode")) {
  const at = motorNavStack.lastIndexOf(currentMode);
  if (at >= 0) motorNavIndex = at;
}
let motorNavFromHistory = false;

function updateMotorNavButtons() {
  if (el.navBack) el.navBack.disabled = motorNavIndex <= 0;
  if (el.navForward) el.navForward.disabled = motorNavIndex >= motorNavStack.length - 1;
}

function recordMotorNav(mode) {
  const m = normalizeMotorMode(mode);
  if (!m || motorNavFromHistory) return;
  if (motorNavStack[motorNavIndex] === m) return;
  motorNavStack.splice(motorNavIndex + 1);
  motorNavStack.push(m);
  motorNavIndex = motorNavStack.length - 1;
  updateMotorNavButtons();
  persistMotorSession();
}

function motorNavGo(delta) {
  const next = motorNavIndex + (delta < 0 ? -1 : 1);
  if (next < 0 || next >= motorNavStack.length) return false;
  motorNavIndex = next;
  motorNavFromHistory = true;
  switchMode(motorNavStack[motorNavIndex]);
  motorNavFromHistory = false;
  updateMotorNavButtons();
  persistMotorSession();
  return true;
}

const WINDOW_TITLE_BASE =
  "RÜZGAR — Mimarlar: Ümit & Gökçenur";

const MODE_LABELS = {
  genel: "ANA MOTOR",
  uretim: "RÜZGAR ÇEKİRDEĞİ",
  gelisim: "Gelişim",
  ses: "SES MOTORU",
  mimar: "MIMAR MOTORU",
  okuma: "MIMAR MOTORU",
  video: "VİDEO MOTORU",
  programlama: "PROGRAMLAMA MOTORU",
  hafiza: "HAFIZA MOTORU",
  tercume: "TERCÜME MOTORU",
  duzen: "Düzen",
  dosya: "Dosya",
  hizli: "Hızlı",
  hizir: "HIZIR — Ekonomik avcı",
};

const el = {
  chat: document.getElementById("chat-messages"),
  orchestraBridge: document.getElementById("orchestra-bridge"),
  input: document.getElementById("msg-input"),
  send: document.getElementById("btn-send"),
  stop: document.getElementById("btn-stop"),
  ttsPause: document.getElementById("btn-tts-pause"),
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
  cpu: null,
  gpu: null,
  workbenchLayoutTools: document.getElementById("workbench-layout-tools"),
  workbenchHizirTools: document.getElementById("workbench-hizir-tools"),
  btnHizirScanHistory: document.getElementById("btn-hizir-scan-history"),
  hizirScanHistoryMenu: document.getElementById("hizir-scan-history-menu"),
  btnHizirSayfaTemizleWb: document.getElementById("btn-hizir-sayfa-temizle-wb"),
  btnHizirHizliYenileWb: document.getElementById("btn-hizir-hizli-yenile-wb"),
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
  thinkingElapsed: document.getElementById("thinking-center-elapsed"),
  ttsStatusPill: document.getElementById("tts-status-pill"),
  faz7HelpBtn: document.getElementById("btn-faz7-help"),
  faz7HelpOverlay: document.getElementById("faz7-help-overlay"),
  faz7HelpClose: document.getElementById("btn-faz7-help-close"),
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
  modeBtnMimar: document.getElementById("mode-btn-mimar"),
  modeBtnSes: document.getElementById("mode-btn-ses"),
  modeBtnHizir: document.getElementById("mode-btn-hizir"),
  motorDeclarationHeader: document.getElementById("motor-declaration-header"),
  dynamicWorkbench: document.getElementById("dynamic-workbench"),
  pageGenel: document.getElementById("page-genel"),
  pageHafiza: document.getElementById("page-hafiza"),
  pageMimar: document.getElementById("page-mimar"),
  pageTercume: document.getElementById("page-tercume"),
  pageVideo: document.getElementById("page-video"),
  pageProgramlama: document.getElementById("page-programlama"),
  pageSes: document.getElementById("page-ses"),
  pageHizir: document.getElementById("page-hizir"),
  btnOpenHizirPanel: document.getElementById("btn-open-hizir-panel"),
  btnHizirRefresh: document.getElementById("btn-hizir-refresh"),
  btnHizirTara: document.getElementById("btn-hizir-tara"),
  btnHizirPazarlar: document.getElementById("btn-hizir-pazarlar"),
  hizirPazarlarPanel: document.getElementById("hizir-pazarlar-panel"),
  hizirPazarlarWrap: document.getElementById("hizir-pazarlar-wrap"),
  hizirAktifKanallar: document.getElementById("hizir-aktif-kanallar"),
  hizirTaraQuery: document.getElementById("hizir-tara-query"),
  hizirInlineStatus: document.getElementById("hizir-inline-status"),
  hizirWorkbenchStrip: document.getElementById("hizir-workbench-strip"),
  hizirWbServer: document.getElementById("hizir-wb-server"),
  hizirFirsatlarWrap: document.getElementById("hizir-firsatlar-wrap"),
  /** UI Fix — HIZIR vitrin iç kaydırma kabı (yükseklik zinciri) */
  hizirFirsatlarScroll: document.getElementById("hizir-firsatlar-scroll"),
  hizirOnbellekWrap: document.getElementById("hizir-onbellek-wrap"),
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
  btnTercumeOcr: document.getElementById("btn-tercume-ocr"),
  btnTercumeSaveTarget: document.getElementById("btn-tercume-save-target"),
  btnTercumeImportUrl: document.getElementById("btn-tercume-import-url"),
  tercumeSaveRel: document.getElementById("tercume-save-rel"),
  tercumeImportUrl: document.getElementById("tercume-import-url"),
  tercumeStats: document.getElementById("tercume-stats"),
  tercumeActiveFile: document.getElementById("btn-tercume-active-file"),
  sesSttLang: document.getElementById("ses-stt-lang"),
  btnSesStt: document.getElementById("btn-ses-stt"),
  sesSttHint: document.getElementById("ses-stt-hint"),
  sesTranscript: document.getElementById("ses-transcript"),
  btnSesToChat: document.getElementById("btn-ses-to-chat"),
  btnSesSpeak: document.getElementById("btn-ses-speak"),
  btnSesTilavet: document.getElementById("btn-ses-tilavet"),
  btnSesClear: document.getElementById("btn-ses-clear"),
  sesSttMeta: document.getElementById("ses-stt-meta"),
  sesCloneRefInput: document.getElementById("ses-clone-ref-input"),
  sesCloneKarakter: document.getElementById("ses-clone-karakter"),
  btnSesCloneUpload: document.getElementById("btn-ses-clone-upload"),
  sesUseClone: document.getElementById("ses-use-clone"),
  sesCloneHint: document.getElementById("ses-clone-hint"),
  sesDubRel: document.getElementById("ses-dub-rel"),
  sesDubFileInput: document.getElementById("ses-dub-file-input"),
  sesDubSrcLang: document.getElementById("ses-dub-src-lang"),
  sesDubTgtLang: document.getElementById("ses-dub-tgt-lang"),
  sesDubVoice: document.getElementById("ses-dub-voice"),
  btnSesDub: document.getElementById("btn-ses-dub"),
  btnSesDubVideoPanel: document.getElementById("btn-ses-dub-video-panel"),
  sesDubMeta: document.getElementById("ses-dub-meta"),
  videoFileInput: document.getElementById("video-file-input"),
  videoPreview: document.getElementById("video-preview"),
  videoCinemaUrl: document.getElementById("video-cinema-url"),
  btnCinemaOpenUrl: document.getElementById("btn-cinema-open-url"),
  btnCinemaOpenWeb: document.getElementById("btn-cinema-open-web"),
  videoCinemaNowPlaying: document.getElementById("video-cinema-now-playing"),
  videoSearchResults: document.getElementById("video-search-results"),
  btnCinemaWatchDownload: document.getElementById("btn-cinema-watch-download"),
  btnCinemaTrimReady: document.getElementById("btn-cinema-trim-ready"),
  btnCinemaEditBin: document.getElementById("btn-cinema-edit-bin"),
  videoJobProgress: document.getElementById("video-job-progress"),
  videoJobProgressLabel: document.getElementById("video-job-progress-label"),
  videoJobProgressBar: document.getElementById("video-job-progress-bar"),
  btnVideoProbe: document.getElementById("btn-video-probe"),
  btnVideoClear: document.getElementById("btn-video-clear"),
  videoEngineHint: document.getElementById("video-engine-hint"),
  videoProbeJson: document.getElementById("video-probe-json"),
  videoDownloadUrl: document.getElementById("video-download-url"),
  btnVideoDownload: document.getElementById("btn-video-download"),
  videoDownloadStatus: document.getElementById("video-download-status"),
  videoDownloadRecent: document.getElementById("video-download-recent"),
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
  videoTimelineHandleIn: document.getElementById("video-timeline-handle-in"),
  videoTimelineHandleOut: document.getElementById("video-timeline-handle-out"),
  videoEditBin: document.getElementById("video-edit-bin"),
  videoEditBinEmpty: document.getElementById("video-edit-bin-empty"),
  videoEditProjectName: document.getElementById("video-edit-project-name"),
  videoEditInsertRel: document.getElementById("video-edit-insert-rel"),
  videoEditInsertStart: document.getElementById("video-edit-insert-start"),
  videoEditInsertEnd: document.getElementById("video-edit-insert-end"),
  videoEditCopyStreams: document.getElementById("video-edit-copy-streams"),
  btnVideoAddClip: document.getElementById("btn-video-add-clip"),
  btnVideoInsertClip: document.getElementById("btn-video-insert-clip"),
  btnVideoClearBin: document.getElementById("btn-video-clear-bin"),
  btnVideoEditMix: document.getElementById("btn-video-edit-mix"),
  videoRelSubTranslate: document.getElementById("video-rel-sub-translate"),
  videoSubSrcLang: document.getElementById("video-sub-src-lang"),
  videoSubTgtLang: document.getElementById("video-sub-tgt-lang"),
  videoSubTemplate: document.getElementById("video-sub-template"),
  btnVideoSubProcess: document.getElementById("btn-video-sub-process"),
  btnVideoSubPipeline: document.getElementById("btn-video-sub-pipeline"),
  videoSubFactoryMeta: document.getElementById("video-sub-factory-meta"),
  videoRelDub: document.getElementById("video-rel-dub"),
  videoDubSrcLang: document.getElementById("video-dub-src-lang"),
  videoDubTgtLang: document.getElementById("video-dub-tgt-lang"),
  videoDubVoice: document.getElementById("video-dub-voice"),
  btnVideoDub: document.getElementById("btn-video-dub"),
  videoDubMeta: document.getElementById("video-dub-meta"),
  videoRelTranscribe: document.getElementById("video-rel-transcribe"),
  videoSttLang: document.getElementById("video-stt-lang"),
  btnVideoTranscribe: document.getElementById("btn-video-transcribe"),
  btnVideoTranscriptToSes: document.getElementById("btn-video-transcript-to-ses"),
  videoTranscriptOut: document.getElementById("video-transcript-out"),
  videoTranscriptMeta: document.getElementById("video-transcript-meta"),
  btnVideoSubToTercume: document.getElementById("btn-video-sub-to-tercume"),
  videoCreateTitle: document.getElementById("video-create-title"),
  videoCreateTheme: document.getElementById("video-create-theme"),
  videoCreateText: document.getElementById("video-create-text"),
  videoCreatePreset: document.getElementById("video-create-preset"),
  videoCreateQuality: document.getElementById("video-create-quality"),
  videoCreateRenderMode: document.getElementById("video-create-render-mode"),
  videoCreateKarakter: document.getElementById("video-create-karakter"),
  videoCreateBg: document.getElementById("video-create-bg"),
  videoCreateImagesDir: document.getElementById("video-create-images-dir"),
  videoCreatePlanPreview: document.getElementById("video-create-plan-preview"),
  btnVideoCreatePlan: document.getElementById("btn-video-create-plan"),
  btnVideoCreateLoadProje: document.getElementById("btn-video-create-load-proje"),
  btnVideoCreateStoryboard: document.getElementById("btn-video-create-storyboard"),
  btnVideoCreateRender: document.getElementById("btn-video-create-render"),
  videoQuickCreate: document.getElementById("video-quick-create"),
  videoQuickYoutube: document.getElementById("video-quick-youtube"),
  videoQuickTrim: document.getElementById("video-quick-trim"),
  videoQuickAudio: document.getElementById("video-quick-audio"),
  videoQuickExport: document.getElementById("video-quick-export"),
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
  btnUmitOnayApply: document.getElementById("btn-umit-onay-apply"),
  btnUmitOnayCancel: document.getElementById("btn-umit-onay-cancel"),
  codeFileTree: document.getElementById("code-file-tree"),
  progProjectSelect: document.getElementById("prog-project-select"),
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
/** Ses önizleme blob URL — yeniden seçimde iptal */
let sesPreviewObjectUrl = null;
/** Video önizleme blob URL */
let videoPreviewObjectUrl = null;
let youtubeBrowserViewResizeHandler = null;
let videoHlsInstance = null;
let cinemaNowPlaying = {
  url: "",
  title: "",
  site: "",
  token: "",
  streamType: "",
  localRel: "",
};
let lastVideoSearchResults = [];
/** @type {HTMLIFrameElement|null} */
let videoYoutubeEmbedEl = null;
/** Son ffprobe özeti (dosya seçili değilken süre için) */
let lastVideoProbeDurationSec = 0;
/** v4/v5 zaman çizelgesi In/Out (saniye; null = işaret yok) */
let videoTimelineIn = null;
let videoTimelineOut = null;
/** v5 kurgu parça listesi */
let videoEditBin = [];
/** Timeline sürükleme: in | out | scrub | null */
let videoTimelineDrag = null;
let lastUiManifest = null;
const VIDEO_EDIT_MAX_CLIP_SEC = 300;
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
  "modeBtnMimar",
  "modeBtnSes",
  "modeBtnHizir",
];

function syncTopModeButtons() {
  // Hem üst topbar (eski) hem sol motor menüsü (Faz 0) aynı `data-mode` ile çalışır.
  const allModeButtons = document.querySelectorAll("[data-mode]");
  allModeButtons.forEach((btn) => {
    const mode = String(btn.getAttribute("data-mode") || "").trim().toLowerCase();
    if (!mode) return;
    const isActive =
      mode === currentMode || (mode === "mimar" && currentMode === "okuma");
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
    if (["ses", "mimar", "okuma", "tercume", "uretim", "hizli", "hafiza", "hizir"].includes(currentMode)) {
      el.web.checked = false;
    } else {
      el.web.checked = true;
    }
  }
  syncWebFetchUi();
  if (currentMode === "mimar" || currentMode === "okuma") {
    el.input.placeholder =
      "Mimar: fotoğraf, resim·sanat, tasarım — sohbet solda; her sekme ayrı sayfa.";
  } else if (currentMode === "tercume") {
    el.input.placeholder =
      "«imam-ı rabbani eserlerini ara» → Eser ara · Okuma sekmesi → arşiv · Çevir ile çeviri";
  } else if (currentMode === "ses") {
    el.input.placeholder =
      "Ses motorunda transkripti panelden sohbete aktarabilir veya doğrudan soru yazabilirsiniz.";
  } else if (currentMode === "video") {
    el.input.placeholder =
      "Sohbetle söyle — link indir/oynat, kes 0:30-1:00, medya bilgisi, kurgu, panel aç… «yardım»";
  } else if (currentMode === "hizir") {
    el.input.placeholder =
      "Örn: «Pazar yerini tara», «Hava durumuna bak», Trendyol fiyat. Yanıt sohbette; veri HIZIR sekmesinde güncellenir.";
  } else {
    el.input.placeholder =
      "Ana Motor — video, tercüme, kod, mimar… Tek sohbet; «hub yardım» ile motor listesi.";
  }
  syncTopModeButtons();
  syncHizirWorkbenchStripVisibility();
  syncWorkbenchHizirToolbar();
  if (el.navRefresh) {
    const tips = {
      genel: "Arayüzü yeniden yükle (Shift: yalnızca ana motor verisi)",
      hafiza: "Arayüzü yeniden yükle (Shift: yalnızca hafıza JSON)",
      hizir: "Arayüzü yeniden yükle (Shift: yalnızca HIZIR paneli)",
      mimar: "Arayüzü yeniden yükle (Shift: yalnızca mimar atölyesi)",
      okuma: "Arayüzü yeniden yükle (Shift: yalnızca mimar atölyesi)",
      tercume: "Arayüzü yeniden yükle (Shift: yalnızca tercüme listesi)",
      ses: "Arayüzü yeniden yükle (Shift: yalnızca ses motoru)",
      video: "Arayüzü yeniden yükle (Shift: yalnızca video özeti)",
      programlama: "Arayüzü yeniden yükle (Shift: yalnızca kod kökü)",
    };
    el.navRefresh.title = tips[currentMode] || "Arayüzü yeniden yükle (kod değişiklikleri dahil)";
  }
  updateMotorNavButtons();
  if (window.RuzgarSidebarManager?.setMotor) {
    void window.RuzgarSidebarManager.setMotor(currentMode);
  } else if (window.RuzgarPanelManager?.openPanel) {
    window.RuzgarPanelManager.openPanel(currentMode);
  }
}
window.switchMode = switchMode;
window.currentMode = currentMode;
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
let ttsPaused = false;
let ttsWebUtterance = null;
/** Ses sentezi isteği giderken de duraklat düğmesi görünsün */
let ttsArmed = false;

const RUZGAR_TTS_MAX_SPEECH_CHARS = 420;
const RUZGAR_TTS_MAX_SENTENCES = 3;

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

/** Faz 7 — düşünme süresi ve plan alt satırı */
let thinkingShownAt = 0;
let thinkingElapsedTimer = null;
let lastThinkingPlanHint = "";
const FAZ7_THINKING_SUB_DEFAULT = "Ümit & Gökçenur — Işık Hızı";
const LS_FAZ7_DEFER_MS = "ruzgarFaz7DeferMs";
const LS_FAZ7_REDUCED_MOTION = "ruzgarFaz7ReducedMotion";
let faz7HealthStripEl = null;
let apiWasOffline = false;
let lastHealthSnapshot = null;

function isHubSseFazDEnabled() {
  const b = lastHealthSnapshot?.build;
  if (!b || typeof b !== "object") return true;
  if (b.hub_sse_faz_d === false) return false;
  const hs = b.hub_sse;
  if (hs && typeof hs === "object" && hs.enabled === false) return false;
  return b.hub_sse_faz_d !== false;
}

function isHubSseFazEEnabled() {
  const b = lastHealthSnapshot?.build;
  if (!b || typeof b !== "object") return true;
  if (b.hub_sse_faz_e === false) return false;
  const hse = b.hub_sse_e;
  if (hse && typeof hse === "object" && hse.enabled === false) return false;
  return b.hub_sse_faz_e !== false;
}

function isUnifiedFaceEnabled() {
  const b = lastHealthSnapshot?.build;
  if (!b || typeof b !== "object") return true;
  return b.unified_face !== false;
}

function getFaz7DeferThinkingMs() {
  try {
    const v = parseInt(localStorage.getItem(LS_FAZ7_DEFER_MS) || "175", 10);
    return Number.isFinite(v) ? Math.max(0, Math.min(v, 900)) : 175;
  } catch {
    return 175;
  }
}

function isFaz7ReducedMotion() {
  try {
    return localStorage.getItem(LS_FAZ7_REDUCED_MOTION) === "1";
  } catch {
    return false;
  }
}

function applyFaz7MotionPrefs() {
  document.body.classList.toggle("faz7-reduced-motion", isFaz7ReducedMotion());
}

function formatClientChatError(exc) {
  const raw = String(exc?.message || exc || "").trim();
  if (raw === "ws-open-timeout") {
    return (
      "WebSocket açılamadı (zaman aşımı). Sunucu yanıt vermiyor olabilir; " +
      "SSE denenir veya Start-Ruzgar.ps1 ile API’yi yeniden başlatın."
    );
  }
  if (exc?.name === "AbortError" || /abort/i.test(raw)) {
    return "İstek iptal edildi (Durdur tuşu veya yeni soru).";
  }
  if (/failed to fetch|networkerror|load failed/i.test(raw)) {
    return `Ağ hatası: yerel sunucu (${RUZGAR_LOCAL_API_PORT}) erişilemiyor. Ruzgar.ps1 veya Start-Ruzgar.ps1 çalışıyor mu?`;
  }
  if (/rate_limit|too large for model|tokens per minute|TPM|413/i.test(raw)) {
    return (
      "Groq istek sınırı aşıldı (bağlam çok büyük). Video motorunda «selam» gibi kısa mesajlar artık yerel yanıtlanır; " +
      "uzun sohbet geçmişini temizleyin veya Ollama/Gemini zincirini kullanın (RUZGAR_GENEL_LOCAL_FIRST=1)."
    );
  }
  return raw || "Bilinmeyen istemci hatası";
}

function ensureFaz7HealthStrip() {
  if (faz7HealthStripEl || !el.dashboardStatus?.parentElement) return;
  const strip = document.createElement("div");
  strip.id = "faz7-health-strip";
  strip.className = "faz7-health-strip mini-card";
  strip.hidden = true;
  el.dashboardStatus.insertAdjacentElement("afterend", strip);
  faz7HealthStripEl = strip;
}

function updateFaz7HealthStrip(j) {
  if (!j || !j.ok) return;
  ensureFaz7HealthStrip();
  if (!faz7HealthStripEl) return;
  const am = j.ana_motor || {};
  faz7HealthStripEl.hidden = false;
  faz7HealthStripEl.classList.toggle("faz7-health-warn", !!am.main_only_genel_hafiza);
  if (am.main_only_genel_hafiza) {
    faz7HealthStripEl.textContent =
      "⚠ Genel mod: yalnızca hafıza JSON — LLM/RAG/web kapalı (RUZGAR_MAIN_ONLY_GENEL_HAFIZA=0)";
    return;
  }
  const sb = j.super_brain || {};
  const bits = [];
  if (sb.gemini_configured && sb.gemini_daemon?.ok) {
    bits.push(`Gemini ✓ ${sb.gemini_model_default || "gemini-2.0-flash"} (daemon)`);
  } else if (sb.gemini_configured) {
    bits.push(`Gemini ✓ ${sb.gemini_model_default || "gemini-2.0-flash"}`);
  } else if (sb.global_api_key_set === false) {
    bits.push("Gemini: .env GLOBAL_API_KEY yok");
  }
  const model = am.ollama_chat_model || "—";
  bits.push(`Ollama: ${model}`);
  if (am.question_plan_enabled) bits.push("soru planı");
  if (am.ana_motor_agent_enabled) bits.push("mini ajan");
  if (am.clarify_enabled) bits.push("netleştirme");
  const build = j.build || {};
  if (build.rev) bits.push(`build ${build.rev}`);
  if (build.nebula_kitap) bits.push("Nebula kitap ✓");
  else if (build.rev && !String(build.rev).includes("nebula")) {
    bits.push("Nebula yok — API eski");
  }
  if (String(build.rev || "").includes("tarih-fast")) bits.push("Tarih hızlı ✓");
  faz7HealthStripEl.textContent = bits.join(" · ");
}

function updateDashboardLastSpeech() {
  if (!el.dashboardLastSpeech) return;
  const short = (lastAssistantReply || "").trim();
  el.dashboardLastSpeech.textContent = short
    ? `Son konuşma: ${short.slice(0, 280)}${short.length > 280 ? "…" : ""}`
    : "Son konuşma: (bekleniyor)";
}

function syncTtsStatusPill() {
  if (!el.ttsStatusPill) return;
  const busy = isTtsActive();
  el.ttsStatusPill.hidden = !busy;
  if (busy) {
    if (ttsPaused) el.ttsStatusPill.textContent = "Duraklatıldı";
    else if (ttsPlayingEl) el.ttsStatusPill.textContent = "Sesli okuma…";
    else el.ttsStatusPill.textContent = "Ses hazırlanıyor…";
  }
}

function tickThinkingElapsed() {
  if (!el.thinkingElapsed || thinkingShownAt <= 0) return;
  const sec = Math.max(0, Math.floor((Date.now() - thinkingShownAt) / 1000));
  el.thinkingElapsed.textContent = sec > 0 ? `${sec} sn` : "";
  el.thinkingElapsed.hidden = sec <= 0;
}

function startThinkingElapsed() {
  thinkingShownAt = Date.now();
  if (el.thinkingElapsed) {
    el.thinkingElapsed.hidden = false;
    el.thinkingElapsed.textContent = "";
  }
  if (thinkingElapsedTimer != null) window.clearInterval(thinkingElapsedTimer);
  thinkingElapsedTimer = window.setInterval(tickThinkingElapsed, 1000);
  tickThinkingElapsed();
}

function stopThinkingElapsed() {
  if (thinkingElapsedTimer != null) {
    window.clearInterval(thinkingElapsedTimer);
    thinkingElapsedTimer = null;
  }
  thinkingShownAt = 0;
  if (el.thinkingElapsed) {
    el.thinkingElapsed.hidden = true;
    el.thinkingElapsed.textContent = "";
  }
}

function setThinkingPlanHint(plan) {
  if (!plan || !plan.primary) {
    lastThinkingPlanHint = "";
    return;
  }
  const lab = plan.label_tr || plan.primary;
  const src = plan.sources || "";
  lastThinkingPlanHint = src ? `${lab} · ${src}` : lab;
  if (el.thinkingSub && el.thinkingOverlay && !el.thinkingOverlay.hidden) {
    el.thinkingSub.textContent = lastThinkingPlanHint;
  }
}

function showThinkingCenter(titleText) {
  if (el.thinkingTitle) {
    el.thinkingTitle.textContent =
      titleText ||
      (currentMode === "mimar" || currentMode === "okuma"
        ? "Mimar atölyesi düşünülüyor…"
        : currentMode === "tercume"
          ? "Çeviri için düşünülüyor…"
          : "Rüzgar düşünüyor…");
  }
  if (el.thinkingSub) {
    el.thinkingSub.textContent = lastThinkingPlanHint || FAZ7_THINKING_SUB_DEFAULT;
  }
  if (el.thinkingOverlay) {
    el.thinkingOverlay.hidden = false;
    el.thinkingOverlay.removeAttribute("aria-hidden");
  }
  if (el.panelMain) el.panelMain.classList.add("thinking-dim");
  startThinkingElapsed();
}

function hideThinkingCenter() {
  stopThinkingElapsed();
  lastThinkingPlanHint = "";
  if (el.thinkingSub) el.thinkingSub.textContent = FAZ7_THINKING_SUB_DEFAULT;
  if (el.thinkingOverlay) {
    el.thinkingOverlay.hidden = true;
    el.thinkingOverlay.setAttribute("aria-hidden", "true");
  }
  if (el.panelMain) el.panelMain.classList.remove("thinking-dim");
}

function classifyChatError(errText) {
  const body = String(errText || "").trim();
  const low = body.toLowerCase();
  let kind = "generic";
  let title = "Yanıt üretilemedi";
  const hints = [];
  if (/zaman aşımı|timed out|timeout/i.test(body) && !/ollama/i.test(body)) {
    kind = "timeout";
    title = "Yanıt zaman aşımı";
    hints.push(
      "Ana Motor RAG + Gemini bazen 60–120 sn sürebilir; tekrar deneyin veya soruyu kısaltın."
    );
    hints.push("Health şeridinde «Gemini ✓ … (daemon)» görünmeli; yoksa Ruzgar.ps1 ile yeniden başlatın.");
  } else if (/ollama.*yanıt vermedi|ollama.*zaman aşımı/i.test(body)) {
    kind = "timeout";
    title = "Ollama yanıt vermedi";
    hints.push("GLOBAL_API_KEY (.env) varken Gemini kullanılmalı — API'yi yeniden başlatın.");
    hints.push("Ollama isteğe bağlı: `ollama serve` veya `ollama pull llama3.2:3b`");
  } else if (/bağlanılamadı|connection|refused|10061|actively refused/i.test(body)) {
    kind = "connection";
    title = "Bağlantı kurulamadı";
    hints.push(`Start-Ruzgar.ps1 veya Ruzgar.ps1 ile API (${RUZGAR_LOCAL_API_PORT}) ve Ollama birlikte başlatılır.`);
    hints.push("Sunucu çipi kırmızıysa `desktop_server.py` penceresini kontrol edin.");
  } else if (/model bulunamadı|not found|does not exist/i.test(body)) {
    kind = "model";
    title = "Model bulunamadı";
    hints.push("Kurulum: `ollama pull` ile health’te görünen modeli indirin.");
    hints.push("Ortam: OLLAMA_CHAT_MODEL değişkenini kontrol edin.");
  } else if (/hafıza-only|yalnızca hafıza|MAIN_ONLY/i.test(body)) {
    kind = "main_only";
    title = "Genel mod — yalnızca hafıza";
    hints.push("RUZGAR_MAIN_ONLY_GENEL_HAFIZA=0 yapın ve API’yi yeniden başlatın.");
  } else if (/gemini|global_api_key|google_gemini/i.test(body)) {
    kind = "gemini";
    title = "Gemini bağlantısı";
    hints.push("Anahtar kalıcı: ilim-assistant/.env → GLOBAL_API_KEY (tekrar girmeniz gerekmez).");
    hints.push("Ruzgar.ps1 ile başlatın; health’te «Gemini ✓ … (daemon)» görünmeli.");
  } else {
    hints.push("Sunucu ve Ollama günlüklerine bakın; ? ile yardım panelini açın.");
  }
  return { kind, title, body, hints };
}

function renderChatErrorHtml(errText) {
  const c = classifyChatError(errText);
  const hintsHtml = c.hints.map((h) => `<li>${esc(h)}</li>`).join("");
  return (
    `<div class="chat-error-card" data-error-kind="${esc(c.kind)}">` +
    `<p class="chat-error-lead"><strong>${esc(c.title)}</strong></p>` +
    `<p class="chat-error-body">${esc(c.body)}</p>` +
    (hintsHtml ? `<ul class="chat-error-hints">${hintsHtml}</ul>` : "") +
    `<div class="chat-error-actions">` +
    `<button type="button" class="btn-secondary btn-compact" data-faz7-copy-error>Kopyala</button>` +
    `</div></div>`
  );
}

function scrollFaz7HelpToMotor(mode) {
  const norm = String(mode || currentMode || "genel").trim().toLowerCase();
  const map = { okuma: "mimar" };
  const target = map[norm] || norm;
  const node =
    document.getElementById(`faz7-help-motor-${target}`) ||
    document.querySelector(`[data-motor="${target}"]`);
  if (!node) return;
  node.classList.add("faz7-help-motor-active");
  const body = el.faz7HelpOverlay?.querySelector(".faz7-help-body");
  if (body) {
    const top = node.offsetTop - 12;
    body.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }
  window.setTimeout(() => node.classList.remove("faz7-help-motor-active"), 2400);
}

let anaMotorLastResearchCard = null;

function syncAnaMotorKaynakPanel() {
  const fold = document.getElementById("ana-motor-kaynak-panel-fold");
  const hintEl = document.getElementById("ana-motor-kaynak-panel-hint");
  const research = document.getElementById("ana-motor-research-card");
  const nebula = document.getElementById("ana-motor-nebula-oneri-card");
  const hasR = research && !research.hidden;
  const hasN = nebula && !nebula.hidden;
  if (!fold) return;
  fold.classList.toggle("has-kaynak-content", !!(hasR || hasN));
  if (hasR || hasN) {
    const parts = [];
    if (hasR && anaMotorLastResearchCard?.primary) {
      parts.push(String(anaMotorLastResearchCard.primary));
    }
    if (hasN && anaMotorLastNebulaCard?.collection_title) {
      parts.push(`Nebula: ${anaMotorLastNebulaCard.collection_title}`);
    } else if (hasN) {
      parts.push("Nebula öneri");
    }
    if (hintEl) hintEl.textContent = parts.join(" · ") || "Kaynak verisi";
  } else if (hintEl) {
    hintEl.textContent = "Henüz veri yok — genişlet";
  }
}

function clearChatHistorySearch() {
  const input = document.getElementById("chat-history-search");
  const hint = document.getElementById("chat-history-search-hint");
  if (input) input.value = "";
  if (hint) hint.textContent = "";
  el.chat?.querySelectorAll(".bubble").forEach((b) => {
    b.classList.remove("chat-search-hit", "chat-search-dim");
  });
}

function highlightChatBubbles(query) {
  const q = String(query || "").trim().toLowerCase();
  if (!el.chat) return 0;
  let hits = 0;
  el.chat.querySelectorAll(".bubble:not(.chat-welcome)").forEach((bubble) => {
    const text = (bubble.textContent || "").toLowerCase();
    const match = q.length >= 2 && text.includes(q);
    bubble.classList.toggle("chat-search-hit", match);
    bubble.classList.toggle("chat-search-dim", q.length >= 2 && !match);
    if (match) hits += 1;
  });
  if (hits) {
    const first = el.chat.querySelector(".bubble.chat-search-hit");
    first?.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  return hits;
}

async function runChatHistorySearch(query) {
  const hint = document.getElementById("chat-history-search-hint");
  const q = String(query || "").trim();
  const localHits = highlightChatBubbles(q);
  if (q.length < 2) {
    clearChatHistorySearch();
    return;
  }
  if (hint) hint.textContent = localHits ? `${localHits} eşleşme (ekran)` : "Ekranda yok…";
  try {
    const mode = currentMode === "genel" ? "" : currentMode;
    const url =
      `${API}/api/ana-motor/chat-history/search?q=${encodeURIComponent(q)}&limit=12` +
      (mode ? `&mode=${encodeURIComponent(mode)}` : "");
    const res = await fetch(url, { cache: "no-store" });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) return;
    const remote = Number(j.count || 0);
    if (hint) {
      const bits = [];
      if (localHits) bits.push(`${localHits} ekran`);
      if (remote) bits.push(`${remote} arşiv`);
      hint.textContent = bits.length ? bits.join(" · ") : "Sonuç yok";
    }
  } catch {
    /* yok say */
  }
}

function wireFazAaChatSearch() {
  const input = document.getElementById("chat-history-search");
  const clearBtn = document.getElementById("btn-chat-history-clear");
  let debounce = null;
  if (input) {
    input.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => runChatHistorySearch(input.value), 220);
    });
    input.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape") {
        ev.preventDefault();
        clearChatHistorySearch();
        input.blur();
      }
    });
  }
  if (clearBtn) clearBtn.addEventListener("click", () => clearChatHistorySearch());
  const kaynakFold = document.getElementById("ana-motor-kaynak-panel-fold");
  if (kaynakFold) {
    const saved = localStorage.getItem("ruzgar_kaynak_panel_open");
    if (saved === "1") kaynakFold.open = true;
    kaynakFold.addEventListener("toggle", () => {
      localStorage.setItem("ruzgar_kaynak_panel_open", kaynakFold.open ? "1" : "0");
    });
  }
}

function initFazZUx() {
  const lsKeyArchive = "ruzgar_archive_fold_open";
  const lsKeyComposer = "ruzgar_composer_advanced_open";
  const archiveFold = document.getElementById("ana-motor-archive-fold");
  if (archiveFold) {
    const saved = localStorage.getItem(lsKeyArchive);
    const defaultOpen = saved === "1";
    archiveFold.open = defaultOpen;
    archiveFold.addEventListener("toggle", () => {
      localStorage.setItem(lsKeyArchive, archiveFold.open ? "1" : "0");
      const hint = document.getElementById("ana-motor-archive-summary");
      if (hint && !archiveFold.open) {
        const n = document.getElementById("ana-motor-archive-select")?.options?.length || 0;
        hint.textContent =
          n > 1 ? `${n - 1} arşiv oturumu — genişlet` : "Kalıcı arşiv oturumları — genişlet";
      }
    });
  }
  const composerFold = document.getElementById("composer-advanced-fold");
  if (composerFold) {
    const savedC = localStorage.getItem(lsKeyComposer);
    if (savedC === "1") composerFold.open = true;
    composerFold.addEventListener("toggle", () => {
      localStorage.setItem(lsKeyComposer, composerFold.open ? "1" : "0");
    });
  }
  const chatSimple =
    localStorage.getItem("ruzgar_chat_simple") !== "0" &&
    (lastHealthSnapshot?.ana_motor?.chat_simple !== false);
  document.body.classList.toggle("faz-z-chat-simple", !!chatSimple);
  document.body.classList.toggle(
    "ruzgar-unified-face",
    isUnifiedFaceEnabled() && currentMode === "genel",
  );
}

function openFaz7Help() {
  if (!el.faz7HelpOverlay) return;
  el.faz7HelpOverlay.hidden = false;
  el.faz7HelpOverlay.removeAttribute("aria-hidden");
  el.faz7HelpClose?.focus();
  window.requestAnimationFrame(() => scrollFaz7HelpToMotor(currentMode));
}

function closeFaz7Help() {
  if (!el.faz7HelpOverlay) return;
  el.faz7HelpOverlay.hidden = true;
  el.faz7HelpOverlay.setAttribute("aria-hidden", "true");
}

function showTercumeChatWelcome() {
  if (!el.chat || currentMode !== "tercume") return;
  if (!isChatVisuallyEmpty()) return;
  dismissChatWelcome();
  const foot = lastUiManifest?.dashboard?.welcome_foot || "Tercüme · Ümit & Gökçenur";
  const w = document.createElement("div");
  w.className = "bubble assistant chat-welcome chat-welcome-tercume";
  w.setAttribute("role", "note");
  w.innerHTML =
    `<p class="chat-welcome-lead"><strong>Merhaba — birlikte okuyalım.</strong></p>` +
    `<p class="chat-welcome-tercume-intro">Komut değil, sohbet: ne yapmak istediğinizi doğal yazın; kitap ortada açılır, çeviri altta birikir.</p>` +
    `<ul class="chat-welcome-list">` +
    `<li>«Sahih Bukhari'yi aç» — dosyayı bulup kitap gibi gösteririm</li>` +
    `<li>«14. sayfaya git» — sayfayı önünüze getiririm</li>` +
    `<li>«Bu sayfayı çevir» — yalnız o sayfayı çeviririm</li>` +
    `<li>«Tamamını çevir» — arka planda (uzun sürer; «durdur» diyebilirsiniz)</li>` +
    `<li>Üstte <strong>Çevir · Durdur · Kaydet</strong> — sık kullanılanlar</li>` +
    `<li><strong>Düzen</strong> menüsü veya Dosyalar/Araçlar — nadir paneller</li>` +
    `</ul>` +
    `<p class="chat-welcome-foot">${esc(foot)}</p>`;
  el.chat.appendChild(w);
  el.chat.scrollTop = 0;
}

function dismissChatWelcome() {
  el.chat?.querySelectorAll(".chat-welcome").forEach((n) => n.remove());
}

function isChatVisuallyEmpty() {
  if (!el.chat) return true;
  return el.chat.querySelectorAll(".bubble:not(.chat-welcome)").length === 0;
}

function showChatWelcomeIfEmpty() {
  if (!el.chat || !isChatVisuallyEmpty()) return;
  if (currentMode === "tercume") {
    showTercumeChatWelcome();
    return;
  }
  if (currentMode === "video" && window.RuzgarVideoChatBrain?.showChatWelcome) {
    dismissChatWelcome();
    window.RuzgarVideoChatBrain.showChatWelcome(el.chat);
    el.chat.scrollTop = 0;
    return;
  }
  if (currentMode === "genel" && window.RuzgarAnaMotorHub?.showChatWelcome) {
    dismissChatWelcome();
    window.RuzgarAnaMotorHub.showChatWelcome(el.chat);
    el.chat.scrollTop = 0;
    return;
  }
  dismissChatWelcome();
  const foot = lastUiManifest?.dashboard?.welcome_foot || "Faz 68–77 · Ümit & Gökçenur";
  const w = document.createElement("div");
  w.className = "bubble assistant chat-welcome";
  w.setAttribute("role", "note");
  w.innerHTML =
    `<p class="chat-welcome-lead"><strong>Merhaba — Rüzgar hazır.</strong></p>` +
    `<ul class="chat-welcome-list">` +
    `<li>Genel soru yazın; <strong>soru planı</strong> dashboard’da görünür.</li>` +
    `<li><strong>Web ara</strong> + sayfa okuma ile güncel bilgi.</li>` +
    `<li><code>@@ruzgar-desktop/app.js</code> — workspace dosyası okuma.</li>` +
    `<li><kbd>?</kbd> veya <kbd>Ctrl+/</kbd> — kısayol yardımı.</li>` +
    `</ul>` +
    `<p class="chat-welcome-actions"><button type="button" class="btn-secondary btn-compact" data-faz7-open-help>Yardımı aç</button></p>` +
    `<p class="chat-welcome-foot">${esc(foot)}</p>`;
  el.chat.appendChild(w);
  el.chat.scrollTop = 0;
}

function renderRecentVideoDownloads(items) {
  if (!el.videoDownloadRecent) return;
  const rows = Array.isArray(items) ? items.filter((x) => x && typeof x === "object") : [];
  el.videoDownloadRecent.innerHTML = "";
  if (!rows.length) {
    const li = document.createElement("li");
    li.className = "video-edit-bin-empty";
    li.textContent = "Henüz indirme kaydı yok.";
    el.videoDownloadRecent.appendChild(li);
    return;
  }
  rows.slice(0, 8).forEach((row) => {
    const li = document.createElement("li");
    li.className = "video-edit-bin-item video-download-recent-item";
    li.setAttribute("role", "button");
    li.tabIndex = 0;
    const title = String(row.title || row.url || "video").slice(0, 90);
    const filePath = String(row.file_path || row.rel || "").trim();
    li.title = filePath
      ? `Tıkla: göreli yolu doldur (${filePath})`
      : "Tıkla: indirme bilgisini forma aktar";
    li.innerHTML = `
      <span class="video-edit-bin-meta">
        <strong>${esc(title)}</strong>
        ${filePath ? `<br><span class="video-download-recent-path">${esc(filePath)}</span>` : ""}
      </span>
      <span class="video-download-recent-use" aria-hidden="true">Kullan</span>
    `;
    const activate = () => applyRecentVideoDownload(row);
    li.addEventListener("click", activate);
    li.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        activate();
      }
    });
    el.videoDownloadRecent.appendChild(li);
  });
}

function applyRecentVideoDownload(row) {
  if (!row || typeof row !== "object") return;
  const rel = String(row.file_path || row.rel || "").trim();
  const url = String(row.url || "").trim();
  if (rel) {
    if (el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
    if (el.videoRelBurnVideo) el.videoRelBurnVideo.value = rel;
    if (el.videoRelMuxVideo) el.videoRelMuxVideo.value = rel;
    if (el.videoRelTranscribe) el.videoRelTranscribe.value = rel;
    if (el.videoRelDub) el.videoRelDub.value = rel;
    if (el.sesDubRel) el.sesDubRel.value = rel;
    if (el.videoRelSubTranslate) el.videoRelSubTranslate.value = "";
  }
  if (url && el.videoDownloadUrl) el.videoDownloadUrl.value = url;
  if (rel) void loadVideoPreviewFromRel(rel, { flash: false });
  flashRuzgarDurum(rel ? `Proje yolu dolduruldu: ${rel}` : "İndirme kaydı forma aktarıldı.");
  window.RuzgarVideoAtolye?.openDuzenDock?.("trim");
}

function setAnaMotorInfoStripState(state) {
  const strip = document.getElementById("ana-motor-info-strip");
  if (!strip) return;
  strip.classList.remove(
    "atelier-info-strip-ana--loading",
    "atelier-info-strip-ana--ready",
    "atelier-info-strip-ana--err"
  );
  if (state) strip.classList.add(`atelier-info-strip-ana--${state}`);
}

function applyUiManifest(manifest) {
  if (!manifest || manifest.ok === false) return;
  lastUiManifest = manifest;
  setAnaMotorInfoStripState("ready");

  const dash = manifest.dashboard || {};
  const badge =
    document.getElementById("ana-motor-phase-badge") ||
    document.querySelector(".atelier-info-strip-ana .phase-badge-ana");
  if (badge && dash.badge) badge.textContent = dash.badge;
  const promise =
    document.getElementById("ana-motor-promise") ||
    document.querySelector(".atelier-info-strip-ana .atelier-promise");
  if (promise && dash.promise) promise.textContent = dash.promise;
  if (el.dashboardStatus && dash.badge) {
    const phaseLabel = manifest.current_phase_label || dash.badge;
    const ts = manifest.generated_at
      ? new Date(Number(manifest.generated_at) * 1000).toLocaleTimeString("tr-TR")
      : "";
    el.dashboardStatus.textContent = ts
      ? `Aktif motor: ANA MOTOR · ${phaseLabel} · manifest ${ts}`
      : `Aktif motor: ANA MOTOR · ${phaseLabel}`;
  }

  const grid = document.getElementById("motors-overview-grid");
  const phases = Array.isArray(manifest.phases) ? manifest.phases : [];
  if (grid && phases.length) {
    grid.innerHTML = "";
    const current = Number(manifest.current_phase || 0);
    phases.forEach((p) => {
      const card = document.createElement("div");
      card.className = "motors-overview-card";
      const ph = document.createElement("span");
      ph.className = "ovx-phase";
      ph.textContent = String(p.phase || "");
      const nm = document.createElement("span");
      nm.className = "ovx-name";
      nm.textContent = String(p.name || "");
      const st = document.createElement("span");
      const n = parseInt(String(p.phase || "").replace(/\D+/g, ""), 10);
      st.className = `ovx-status ${Number.isFinite(n) && n >= current ? "ovx-now" : "ovx-done"}`;
      st.textContent = String(p.status || "tamam");
      card.append(ph, nm, st);
      grid.appendChild(card);
    });
  }

  const motors = manifest.motors || {};
  Object.entries(motors).forEach(([mode, meta]) => {
    const safeMode =
      window.CSS && typeof CSS.escape === "function"
        ? CSS.escape(mode)
        : String(mode).replace(/[^a-z0-9_-]/gi, "");
    const tag = document.querySelector(`#motor-side-${safeMode} .motor-tag`);
    if (tag && meta?.tag) tag.textContent = String(meta.tag);
    if (mode === "programlama" && meta?.tag) {
      const pb = document.getElementById("programlama-phase-badge");
      const tagStr = String(meta.tag);
      if (pb) pb.textContent = tagStr.split("·")[0].trim() || "Faz 3";
      window.__ruzgarManifestProgTag = tagStr;
      if (!/handoff|faz\s*79|programlama/i.test(tagStr)) {
        console.warn("RUZGAR manifest programlama tag beklenmeyen biçim:", tagStr);
      }
    }
  });

  if (dash.help_title) {
    const title = document.getElementById("faz7-help-title");
    if (title) title.textContent = dash.help_title;
  }
  const caps = Array.isArray(manifest.capabilities) ? manifest.capabilities : [];
  const done = document.querySelector(".faz7-help-done");
  if (done && caps.length) {
    done.innerHTML = "";
    caps.forEach((cap) => {
      const li = document.createElement("li");
      li.textContent = String(cap);
      done.appendChild(li);
    });
  }

  const existingFoot = el.chat?.querySelector(".chat-welcome-foot");
  if (existingFoot && dash.welcome_foot) existingFoot.textContent = dash.welcome_foot;
  renderRecentVideoDownloads(manifest.video?.recent_downloads || []);
}

window.refreshUiManifest = refreshUiManifest;
async function refreshUiManifest() {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 8000);
  try {
    const r = await fetch(`${API}/api/ui/manifest`, {
      method: "GET",
      cache: "no-store",
      signal: ac.signal,
    });
    const j = await r.json();
    if (!r.ok || j.ok === false) throw new Error(j.detail || `HTTP ${r.status}`);
    applyUiManifest(j);
    return j;
  } catch (e) {
    console.warn("[RÜZGAR] UI manifest okunamadı:", e);
    if (lastHealthSnapshot?.ok) {
      setAnaMotorInfoStripState("ready");
      const badge = document.getElementById("ana-motor-phase-badge");
      const promise = document.getElementById("ana-motor-promise");
      if (badge) badge.textContent = "Ana Motor · sunucu bağlı";
      if (promise) {
        promise.textContent =
          "Manifest yüklenemedi ama yerel API çalışıyor — sohbet kullanılabilir.";
      }
    }
    return null;
  } finally {
    clearTimeout(timer);
  }
}

function wireFaz7PrefsUi() {
  const rm = document.getElementById("faz7-opt-reduced-motion");
  const defer = document.getElementById("faz7-opt-defer-ms");
  if (rm) {
    rm.checked = isFaz7ReducedMotion();
    rm.addEventListener("change", () => {
      try {
        if (rm.checked) localStorage.setItem(LS_FAZ7_REDUCED_MOTION, "1");
        else localStorage.removeItem(LS_FAZ7_REDUCED_MOTION);
      } catch {
        /* yok say */
      }
      applyFaz7MotionPrefs();
    });
  }
  if (defer) {
    defer.value = String(getFaz7DeferThinkingMs());
    defer.addEventListener("change", () => {
      try {
        const v = Math.max(0, Math.min(900, parseInt(defer.value, 10) || 175));
        defer.value = String(v);
        localStorage.setItem(LS_FAZ7_DEFER_MS, String(v));
      } catch {
        /* yok say */
      }
    });
  }
  applyFaz7MotionPrefs();
}

function wireFaz7Cila() {
  wireFaz7PrefsUi();
  initFazZUx();
  wireFazAaChatSearch();
  if (el.faz7HelpBtn) el.faz7HelpBtn.addEventListener("click", () => openFaz7Help());
  if (el.faz7HelpClose) el.faz7HelpClose.addEventListener("click", () => closeFaz7Help());
  el.faz7HelpOverlay?.querySelectorAll("[data-faz7-close]").forEach((node) => {
    node.addEventListener("click", () => closeFaz7Help());
  });
  if (el.chat) {
    el.chat.addEventListener("click", (e) => {
      const helpBtn =
        e.target instanceof HTMLElement ? e.target.closest("[data-faz7-open-help]") : null;
      if (helpBtn) {
        openFaz7Help();
        return;
      }
      const btn = e.target instanceof HTMLElement ? e.target.closest("[data-faz7-copy-error]") : null;
      if (!btn) return;
      const card = btn.closest(".chat-error-card");
      const body = card?.querySelector(".chat-error-body");
      const text = body?.textContent?.trim() || "";
      if (!text) return;
      void navigator.clipboard?.writeText(text).then(
        () => setStatus("Hata metni kopyalandı", "Rüzgar"),
        () => setStatus("Kopyalanamadı", "Rüzgar")
      );
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "?" && !e.ctrlKey && !e.metaKey && !e.altKey) {
      const t = e.target;
      if (t instanceof HTMLElement && t.closest("textarea, input, [contenteditable='true']")) return;
      e.preventDefault();
      openFaz7Help();
      return;
    }
    if (e.key === "F1") {
      e.preventDefault();
      openFaz7Help();
      return;
    }
    if (e.key === "/" && (e.ctrlKey || e.metaKey)) {
      const t = e.target;
      if (t instanceof HTMLElement && t.closest("textarea, input, [contenteditable='true']")) return;
      e.preventDefault();
      openFaz7Help();
      return;
    }
    if (e.key === "Escape" && el.faz7HelpOverlay && !el.faz7HelpOverlay.hidden) {
      closeFaz7Help();
    }
  });
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

function getWorkbenchMode() {
  if (currentMode === "genel" && hubQuietMotor) return hubQuietMotor;
  return currentMode;
}

function openMotorWorkbenchQuiet(mode) {
  let m = String(mode || "").trim().toLowerCase();
  if (m === "okuma") m = "mimar";
  if (!m || m === "genel") return;
  hubQuietMotor = m;
  if (window.RuzgarSidebarManager?.setMotor) {
    void window.RuzgarSidebarManager.setMotor(m);
  }
  updateDynamicWorkbench();
}

function clearHubQuietMotor() {
  if (!hubQuietMotor) return;
  hubQuietMotor = null;
  if (currentMode === "genel") updateDynamicWorkbench();
}

function switchMode(mode) {
  let next = String(mode || "").trim().toLowerCase();
  if (next === "okuma") next = "mimar";
  if (!next) return;
  hubQuietMotor = null;
  if (perfBusy) {
    interruptRuzgar();
    if (el.send) el.send.disabled = false;
    perfBusy = false;
  }
  currentMode = next;
  window.currentMode = currentMode;
  applyModeToUI();
  if (window.RuzgarSidebarManager?.setMotor) {
    void window.RuzgarSidebarManager.setMotor(next);
  } else if (window.RuzgarPanelManager?.openPanel) {
    window.RuzgarPanelManager.openPanel(next);
  }
  renderMotorChatFromSession(next);
  setStatus(`Mod: ${MODE_LABELS[currentMode] || currentMode}`, "Rüzgar");
  updatePerformanceIndicators(perfBusy);
  updateDynamicWorkbench();
  if (window.RuzgarSplit?.refresh) {
    requestAnimationFrame(() => window.RuzgarSplit.refresh());
  }
  if (next === "programlama") {
    void refreshProgramlamaUmitOnay();
    void refreshProgramlamaKpiDashboard();
  }
  if (next === "genel") {
    void refreshProgramlamaHandoffWorkbench();
  }
  if (next === "tercume") {
    showTercumeChatWelcome();
  }
  recordMotorNav(next);
  updateMotorNavButtons();
  const motorDeclarationByMode = {
    genel: "Ana Motor — Tek sohbetten video, tercüme, kod, mimar, ses… «hub yardım» ile motor listesi.",
    mimar:
      "Mimar motoru — Fotoğraf, sanat galerisi ve tasarım; üç bağımsız sayfa, yan sohbet.",
    okuma:
      "Mimar motoru — Fotoğraf, sanat galerisi ve tasarım; üç bağımsız sayfa, yan sohbet.",
    video:
      "Video motoru — Sohbetle yönet: link indir/oynat, kes, kurgu, medya bilgisi; sinema paneli talimatları yansıtır.",
    programlama:
      "Programlama motoru açıldı; Faz 6 — şablon projeler, oturum bağlamı, onaylı düzeltme.",
    hafiza:
      "Hafıza motoru açıldı; bu motorla gelişim ve hafıza teknikleri üzerinde çalışabilirsiniz.",
    ses:
      "Ses motoru — Stüdyo: dosya + konuşmayı metne dökme, transkript; tarayıcıdan seslendirme.",
    tercume:
      "Tercüme — Sohbetle kitap açın, sayfa sayfa çevirin; karmaşık paneller Düzen menüsünde.",
    hizir:
      "HIZIR — Merkezi Bellek v3: ticari fırsatlar ve genel keşif önbelleği; sunucu API ile canlı yenilenir.",
  };
  setHeaderMotorDeclaration(motorDeclarationByMode[currentMode] || "");
  clearMotorDeclarations();
  document.body.classList.toggle(
    "ruzgar-unified-face",
    isUnifiedFaceEnabled() && currentMode === "genel",
  );
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
      if (window.RuzgarTercumeAtolye) window.RuzgarTercumeAtolye.importText(t, null);
      break;
    case "video":
      switchMode("video");
      flashRuzgarDurum("Video motoru: metin panoya kopyalandı.");
      void navigator.clipboard?.writeText(t);
      break;
    case "ses":
      switchMode("ses");
      if (window.RuzgarAnaMotorHub?.parseTilavetReadCommand) {
        const tr = window.RuzgarAnaMotorHub.parseTilavetReadCommand(t);
        if (tr?.text) {
          if (el.sesTranscript) el.sesTranscript.value = tr.text;
          el.sesTranscript?.focus();
          break;
        }
      }
      if (el.sesTranscript) el.sesTranscript.value = t;
      el.sesTranscript?.focus();
      break;
    case "programlama":
      switchMode("programlama");
      if (el.codeEditor) el.codeEditor.value = t;
      updateProgramlamaActiveFileLabel();
      break;
    case "mimar":
    case "okuma":
      switchMode("mimar");
      if (el.input) el.input.value = t;
      window.RuzgarMimarAtolye?.setMimarTab?.("tasarim");
      el.input?.focus();
      break;
    case "hafiza":
      switchMode("hafiza");
      if (el.hafizaInput) el.hafizaInput.value = t.slice(0, 8000);
      break;
    case "hizir":
      switchMode("hizir");
      if (el.input) el.input.value = t;
      el.input?.focus();
      void HIZIR_MODU.refreshPanel();
      flashRuzgarDurum("HIZIR paneli: merkezi bellek sunucudan yenilendi.");
      break;
    default:
      switchMode("genel");
      if (el.input) el.input.value = t;
      el.input?.focus();
  }
  setStatus(`Köprü: ${mid}`, "Rüzgar");
}

let dashboardAgentWrapEl = null;
let dashboardAgentListEl = null;

function ensureDashboardAgentUi() {
  if (dashboardAgentWrapEl) return;
  if (!el.dashboardStatus?.parentElement) return;
  const wrap = document.createElement("div");
  wrap.id = "dashboard-agent-steps";
  wrap.className = "dashboard-agent-steps mini-card";
  wrap.hidden = true;
  const title = document.createElement("strong");
  title.className = "dashboard-agent-title";
  title.textContent = "Ajan adımları";
  const ol = document.createElement("ol");
  ol.id = "dashboard-agent-list";
  ol.className = "dashboard-agent-list";
  wrap.append(title, ol);
  el.dashboardStatus.insertAdjacentElement("afterend", wrap);
  dashboardAgentWrapEl = wrap;
  dashboardAgentListEl = ol;
}

function renderProgramlamaCompliance(compliance) {
  const wrap = document.getElementById("programlama-compliance-card");
  const scoreEl = document.getElementById("programlama-compliance-score");
  const gradeEl = document.getElementById("programlama-compliance-grade");
  const detailEl = document.getElementById("programlama-compliance-detail");
  if (!wrap || !scoreEl || !gradeEl) return;
  const c = compliance && typeof compliance === "object" ? compliance : null;
  if (!c || c.score === undefined) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const score = Number(c.score || 0);
  const grade = String(c.grade || "—");
  const target = Number(c.target_score || 85);
  const parityP = c.parity_passed;
  const parityT = c.parity_total;
  const parityBit =
    parityP !== undefined && parityT !== undefined
      ? ` · parity ${parityP}/${parityT}`
      : "";
  scoreEl.textContent = `${score}/100`;
  gradeEl.textContent =
    c.overall_kpi_ok === true
      ? `KPI OK ≥${target}`
      : c.meets_target
        ? `Not ${grade}`
        : `Hedef ≥${target}`;
  if (detailEl) {
    const scope = String(c.last_scope || "").trim();
    const turns = Number(c.turn_count || 0);
    detailEl.textContent =
      (scope ? `${scope} · ` : "") +
      (turns > 0 ? `${turns} tur` : "—") +
      parityBit;
  }
}

function renderProgramlamaTaskStats(stats, liveKpi) {
  const wrap = document.getElementById("programlama-task-stats-card");
  const rateEl = document.getElementById("programlama-task-stats-rate");
  const countEl = document.getElementById("programlama-task-stats-count");
  const detailEl = document.getElementById("programlama-task-stats-detail");
  if (!wrap || !rateEl || !countEl) return;
  const live = liveKpi && typeof liveKpi === "object" ? liveKpi : null;
  const w7 = live?.window_7d && live.window_7d.total ? live.window_7d : null;
  const s =
    w7 ||
    (stats && typeof stats === "object" && stats.total ? stats : null);
  if (!s || !s.total) {
    if (live && !live.sample_sufficient && live.window_7d) {
      wrap.hidden = false;
      rateEl.textContent = "—";
      countEl.textContent = `Canlı · ${live.window_7d.total || 0} görev`;
      if (detailEl) {
        detailEl.textContent = live.headline || `≥${live.min_sample || 5} görev gerekli`;
      }
      return;
    }
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const pct = Math.round(Number(s.success_rate || 0) * 100);
  const tgt = Math.round(Number(s.target_rate || live?.target_rate || 0.7) * 100);
  const trend = live?.trend;
  const arrow =
    trend === "up" ? " ↑" : trend === "down" ? " ↓" : trend === "flat" ? " →" : "";
  rateEl.textContent = `${pct}%${arrow}`;
  const meets = live?.meets_target_live ?? s.meets_target;
  countEl.textContent = meets ? `Canlı OK ≥${tgt}%` : `Canlı ≥${tgt}%`;
  if (detailEl) {
    const w30 = live?.window_30d;
    const statsE1 = stats && typeof stats === "object" ? stats : {};
    let line = `${s.success_count}/${s.total} görev (7g) · ort ${s.avg_turns || 0} tur`;
    if (w30 && w30.total) {
      line += ` · 30g: ${Math.round(Number(w30.success_rate || 0) * 100)}%`;
    }
    const e1 = statsE1.e1 || s.e1;
    if (e1 && e1.total) {
      const ep = Math.round(Number(e1.success_rate || 0) * 100);
      const et = Math.round(Number(statsE1.e1_target_rate || s.e1_target_rate || 0.9) * 100);
      line += ` · E1: ${ep}% (hedef ≥${et}%)`;
    }
    const roll = statsE1.rolling_20 || s.rolling_20;
    if (roll && roll.total) {
      line += ` · son${roll.window || 20}: ${Math.round(Number(roll.success_rate || 0) * 100)}%`;
    }
    const tops = statsE1.root_cause_top || s.root_cause_top;
    if (Array.isArray(tops) && tops[0]) {
      line += ` · kök: ${tops[0].cause}×${tops[0].count}`;
    }
    if (live?.headline) {
      line = `${live.headline} · ${line}`;
    }
    detailEl.textContent = line;
    detailEl.title = (live?.recent || [])
      .map((r) => `${r.success ? "OK" : "X"} ${r.scope_rel || "?"}`)
      .join("\n");
  }
}

function renderProgramlamaP89Kpi(build) {
  const wrap = document.getElementById("programlama-p89-kpi-card");
  const cacheEl = document.getElementById("programlama-p89-cache");
  const chainEl = document.getElementById("programlama-p89-chain");
  const detailEl = document.getElementById("programlama-p89-detail");
  if (!wrap || !cacheEl || !chainEl || !detailEl) return;
  const b = build || {};
  const c = b.prompt_cache_v98 || {};
  const p9 = b.p9_v99 || {};
  const winRate = Number(c.window_hit_rate || 0);
  const pct = Number.isFinite(winRate) ? Math.round(winRate * 100) : 0;
  const hits = Number(c.window_hits || 0);
  const misses = Number(c.window_misses || 0);
  const chain = Array.isArray(p9.programlama_chain) ? p9.programlama_chain : [];
  const first = chain.length ? String(chain[0]) : "—";
  const localFirst = Boolean(p9.local_first_active);
  const strict = Boolean(p9.strict_local_first);
  wrap.hidden = false;
  cacheEl.textContent = `%${pct}`;
  chainEl.textContent = `${first} · ${localFirst ? "yerel-öncelik ✓" : "yerel-öncelik ×"}`;
  detailEl.textContent =
    `Cache 5dk: ${hits}/${hits + misses} · strict=${strict ? "on" : "off"} · zincir: ${chain.slice(0, 5).join("→") || "—"}`;
}

function programlamaScopeFromContext() {
  const rel = String(atolyeOpenRel || "").replace(/\\/g, "/");
  if (rel.startsWith("projects/")) {
    const parts = rel.split("/").filter(Boolean);
    if (parts.length >= 2) return `${parts[0]}/${parts[1]}`;
  }
  const sel = document.getElementById("prog-project-select");
  if (sel && sel.value) return String(sel.value).trim();
  return "projects";
}

function renderProgramlamaWeeklyKpi(payload) {
  const wrap = document.getElementById("programlama-weekly-kpi-card");
  const weekEl = document.getElementById("programlama-weekly-kpi-week");
  const rateEl = document.getElementById("programlama-weekly-kpi-rate");
  const detailEl = document.getElementById("programlama-weekly-kpi-detail");
  if (!wrap || !weekEl || !rateEl || !detailEl) return;
  if (!payload || !payload.ok) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const ts = payload.task_stats || {};
  const to = payload.text_only_stats || {};
  const parity = payload.parity_last || {};
  const rate = Math.round(Number(ts.success_rate || 0) * 100);
  weekEl.textContent = String(payload.week || "hafta");
  rateEl.textContent = `görev %${rate}`;
  const pPass = parity.passed != null ? `${parity.passed}/${parity.total || 8}` : "—";
  detailEl.textContent =
    `metin-only %${Math.round(Number(to.text_only_rate || 0) * 100)} · parity ${pPass}` +
    (payload.saved_path ? ` · ${String(payload.saved_path).split(/[/\\]/).pop()}` : "");
}

function renderProgramlamaPrPlan(payload) {
  const wrap = document.getElementById("programlama-pr-plan-card");
  const branchEl = document.getElementById("programlama-pr-branch");
  const ghEl = document.getElementById("programlama-pr-gh");
  const stepsEl = document.getElementById("programlama-pr-steps");
  if (!wrap || !branchEl || !ghEl || !stepsEl) return;
  const plan = payload && payload.plan ? payload.plan : null;
  if (!payload || !payload.ok || !plan) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  branchEl.textContent = `dal: ${plan.branch || "?"} → öneri: ${plan.branch_suggest || "?"}`;
  ghEl.textContent = plan.gh_available ? "gh ✓ (komutu kopyala)" : "gh yok — web PR";
  ghEl.title = String(plan.gh_command || "");
  const steps = Array.isArray(plan.steps) ? plan.steps : [];
  stepsEl.textContent = steps.slice(0, 5).join("\n");
}

function renderProgramlamaGitChanges(payload) {
  const wrap = document.getElementById("programlama-git-changes-card");
  const branchEl = document.getElementById("programlama-git-branch");
  const summaryEl = document.getElementById("programlama-git-summary");
  const branchSuggestEl = document.getElementById("programlama-git-branch-suggest");
  const filesEl = document.getElementById("programlama-git-files");
  const commitEl = document.getElementById("programlama-git-commit-suggest");
  const diffPre = document.getElementById("programlama-git-diff-preview");
  if (!wrap || !branchEl || !summaryEl) return;
  const strip = payload && payload.strip ? payload.strip : null;
  if (!payload || !payload.ok || !strip) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  branchEl.textContent = strip.branch ? `dal: ${strip.branch}` : "git";
  summaryEl.textContent = strip.summary || (strip.has_changes ? "değişiklik var" : "temiz");
  if (branchSuggestEl) {
    const sug = payload.branch_suggest || payload.pr_branch_suggest;
    branchSuggestEl.textContent = sug ? `dal önerisi: ${sug}` : "";
  }
  if (filesEl) {
    const lines = Array.isArray(strip.file_lines) ? strip.file_lines : [];
    filesEl.textContent = lines.length ? lines.slice(0, 4).join(" · ") : "";
  }
  if (commitEl) {
    const pending = payload.pending_commit || payload.commit_suggest;
    const msg = pending && pending.message ? String(pending.message).trim() : "";
    if (msg) {
      const src = pending.source ? ` (${pending.source})` : "";
      commitEl.textContent = `Commit önerisi${src}: ${msg.slice(0, 100)}`;
      commitEl.title = msg;
    } else {
      commitEl.textContent = "";
      commitEl.title = "";
    }
  }
  const snap = payload.snapshot || {};
  const diffTxt = String(snap.diff_stat_preview || "").trim();
  if (diffPre) {
    if (diffTxt && !diffPre.dataset.pinned) {
      diffPre.hidden = false;
      diffPre.textContent = diffTxt.slice(0, 600);
    } else if (!diffPre.dataset.pinned) {
      diffPre.hidden = true;
      diffPre.textContent = "";
    }
  }
}

function renderProgramlamaUmitOnay(payload) {
  const wrap = document.getElementById("programlama-umit-onay-card");
  const stateEl = document.getElementById("programlama-umit-onay-state");
  const kindEl = document.getElementById("programlama-umit-onay-kind");
  const detailEl = document.getElementById("programlama-umit-onay-detail");
  const applyBtn = el.btnUmitOnayApply || document.getElementById("btn-umit-onay-apply");
  const cancelBtn = el.btnUmitOnayCancel || document.getElementById("btn-umit-onay-cancel");
  if (!wrap || !stateEl || !kindEl || !detailEl) return;
  wrap.hidden = false;
  wrap.classList.remove("programlama-umit-onay-pending");
  if (!payload || payload.ok === false) {
    const http = payload && payload.http_status ? ` (HTTP ${payload.http_status})` : "";
    stateEl.textContent = "API bağlantısı yok";
    kindEl.textContent = "Faz 98 endpoint";
    detailEl.textContent =
      `Ruzgar_TemizBaslat.bat çalıştır, Electron'da Ctrl+Shift+R${http}.`;
    if (applyBtn) applyBtn.disabled = true;
    if (cancelBtn) cancelBtn.disabled = true;
    return;
  }
  if (!payload.has_pending) {
    stateEl.textContent = "Bekleyen işlem yok";
    kindEl.textContent = "Sistem sakin";
    detailEl.textContent =
      "Sohbette: işlem iste: mkdir projects/onay-test → önizleme → Tamam yap.";
    if (applyBtn) applyBtn.disabled = true;
    if (cancelBtn) cancelBtn.disabled = true;
    return;
  }
  const op = payload.operation && typeof payload.operation === "object" ? payload.operation : {};
  const label = String(op.label || op.kind || "işlem");
  const riskCount = Number(op.risk_count || 0);
  wrap.classList.add("programlama-umit-onay-pending");
  stateEl.textContent = "Onay bekliyor";
  kindEl.textContent = label;
  const src = op.src ? `Kaynak: ${op.src}` : "";
  const dst = op.dst ? `Hedef: ${op.dst}` : "";
  const cmd = op.command ? `Komut: ${op.command}` : "";
  const pkg = op.package ? `Paket: ${op.package}` : "";
  const risk =
    riskCount > 0 ? `Risk(${riskCount}): ${String(op.risk_head || "").slice(0, 90)}` : "Risk: düşük";
  detailEl.textContent = [src, dst, cmd, pkg, risk].filter(Boolean).join(" · ");
  if (applyBtn) applyBtn.disabled = false;
  if (cancelBtn) cancelBtn.disabled = false;
}

async function refreshProgramlamaUmitOnay() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) {
    renderProgramlamaUmitOnay({ ok: false });
    return;
  }
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/umit-onay${qs}`, { cache: "no-store" });
    if (!res.ok) {
      renderProgramlamaUmitOnay({ ok: false, http_status: res.status });
      return;
    }
    const onay = await res.json().catch(() => ({}));
    renderProgramlamaUmitOnay(onay);
  } catch (_) {
    renderProgramlamaUmitOnay({ ok: false });
  }
}

async function refreshProgramlamaGitChanges(scopeRel) {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  const scope = String(scopeRel || programlamaScopeFromContext() || "").trim();
  if (!scope) return;
  try {
    const qs = new URLSearchParams({
      workspace_root: workspaceRoot,
      scope_rel: scope,
    });
    if (atolyeOpenRel) qs.set("active_file", atolyeOpenRel);
    const res = await fetch(`${API}/api/programlama/git-changes?${qs}`);
    const data = await res.json().catch(() => ({}));
    renderProgramlamaGitChanges(data);
  } catch (_) {
    /* ignore */
  }
}

function renderProgramlamaMegaWorkbench(payload) {
  const megaCard = document.getElementById("programlama-mega-workbench-card");
  const turnEl = document.getElementById("programlama-mega-turn");
  const filesEl = document.getElementById("programlama-mega-files");
  const e2El = document.getElementById("programlama-mega-e2");
  const resumeBtn = document.getElementById("btn-mega-resume");
  const touchCard = document.getElementById("programlama-touched-files-card");
  const touchCount = document.getElementById("programlama-touched-count");
  const touchList = document.getElementById("programlama-touched-list");
  const planCard = document.getElementById("programlama-patch-plan-card");
  const planCount = document.getElementById("programlama-patch-plan-count");
  const planList = document.getElementById("programlama-patch-plan-list");
  const verifyCard = document.getElementById("programlama-verify-unified-card");
  const verifyStatus = document.getElementById("programlama-verify-status");
  const verifyDetail = document.getElementById("programlama-verify-detail");
  if (!payload || !payload.ok) {
    if (megaCard) megaCard.hidden = true;
    return;
  }
  const lim = payload.mega?.limits || {};
  const ag = payload.agent || {};
  const e2 = payload.e2 || {};
  const maxT = intOr(lim.max_turns, ag.max_turns, 12);
  const maxF = intOr(lim.max_files_per_turn, 16);
  const budget = intOr(lim.budget_sec, 900);
  if (megaCard && turnEl && filesEl) {
    megaCard.hidden = false;
    turnEl.textContent = `tur ${ag.turn || 0}/${maxT}`;
    filesEl.textContent = payload.mega?.active
      ? `mega · ${maxF} dosya/tur · ${budget}s`
      : `standart · ${maxF} dosya/tur`;
    if (e2El) {
      const pct = Math.round(Number(e2.current_rate || 0) * 100);
      const tgt = Math.round(Number(e2.target_rate || 0.9) * 100);
      e2El.textContent = `E2: %${pct} (hedef ≥${tgt}%) · ${e2.sample_total || 0} örnek`;
    }
    if (resumeBtn) {
      resumeBtn.disabled = !ag.can_resume;
      resumeBtn.dataset.resumeHint = ag.resume_hint || "";
    }
  }
  const touched = Array.isArray(payload.touched_files) ? payload.touched_files : [];
  if (touchCard && touchCount && touchList) {
    touchCard.hidden = touched.length === 0;
    touchCount.textContent = String(payload.touched_count || touched.length);
    touchList.textContent = touched.slice(0, 12).join("\n");
  }
  const plan = payload.patch_plan || {};
  const ppaths = Array.isArray(plan.paths_preview) ? plan.paths_preview : [];
  if (planCard && planCount && planList) {
    planCard.hidden = !ppaths.length && !plan.count;
    planCount.textContent = `bekleyen ${plan.pending || 0} / ${plan.count || 0}`;
    planList.textContent = ppaths.join("\n") || "—";
  }
  const ver = payload.verify || {};
  if (verifyCard && verifyStatus && verifyDetail) {
    if (ver.ok === null || ver.ok === undefined) {
      verifyCard.hidden = true;
    } else {
      verifyCard.hidden = false;
      verifyStatus.textContent = ver.ok ? "verify OK" : "verify kırmızı";
      verifyDetail.textContent = String(ver.detail || "").slice(0, 200);
    }
  }
}

function intOr(...vals) {
  for (const v of vals) {
    const n = Number(v);
    if (Number.isFinite(n) && n > 0) return n;
  }
  return 0;
}

async function refreshProgramlamaMegaWorkbench() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/mega-workbench${qs}`);
    const data = await res.json().catch(() => ({}));
    renderProgramlamaMegaWorkbench(data);
    window.__ruzgarMegaWorkbench = data;
  } catch (_) {
    /* ignore */
  }
}

function renderProgramlamaLocalWorkbench(payload) {
  const wrap = document.getElementById("programlama-local-workbench-card");
  const modeEl = document.getElementById("programlama-local-mode");
  const chainEl = document.getElementById("programlama-local-chain");
  const e3El = document.getElementById("programlama-local-e3");
  const ruralEl = document.getElementById("programlama-local-rural");
  if (!wrap || !modeEl) return;
  if (!payload || !payload.ok) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const modes = payload.modes || {};
  const parts = [];
  if (modes.ollama_only) parts.push("ollama-only");
  if (modes.prog_local_first) parts.push("yerel öncelik");
  if (modes.groq_disabled) parts.push("groq kapalı");
  if (modes.gemini_disabled) parts.push("gemini kapalı");
  modeEl.textContent = parts.length
    ? parts.join(" · ")
    : modes.ollama_available
      ? "Ollama ✓"
      : "Ollama yok";
  const chain = (payload.chain?.effective || []).join(" → ");
  if (chainEl) {
    chainEl.textContent = chain || "—";
  }
  const e3 = payload.e3 || {};
  if (e3El) {
    const pct = Math.round(Number(e3.current_rate || 0) * 1000) / 10;
    const tgt = Math.round(Number(e3.target_text_only_rate || 0.01) * 1000) / 10;
    const ok = e3.meets_target ? "✓" : "⚠";
    e3El.textContent = `metin-only ${ok} %${pct} (hedef ≤%${tgt}) · ${e3.sample_total || 0} tur`;
  }
  if (ruralEl) {
    ruralEl.textContent = (payload.rural || {}).fallback_message || "";
  }
  window.__ruzgarLocalWorkbench = payload;
}

async function refreshProgramlamaLocalWorkbench() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/local-workbench${qs}`);
    const data = await res.json().catch(() => ({}));
    renderProgramlamaLocalWorkbench(data);
  } catch (_) {
    /* ignore */
  }
}

function renderProgramlamaHandoff(payload) {
  const wrap = document.getElementById("programlama-handoff-card");
  const scopeEl = document.getElementById("programlama-handoff-scope");
  const pytestEl = document.getElementById("programlama-handoff-pytest");
  const chainEl = document.getElementById("programlama-handoff-chain");
  const logEl = document.getElementById("programlama-handoff-log");
  if (!wrap || !scopeEl) return;
  if (!payload || !payload.ok) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const ho = payload.handoff || {};
  const e4 = payload.e4 || {};
  scopeEl.textContent = ho.scope_rel ? `kapsam: ${ho.scope_rel}` : "handoff hazır";
  if (pytestEl) {
    pytestEl.textContent = (payload.delegation || {}).pytest_footer || "pytest: —";
  }
  if (chainEl) {
    const chain = (payload.motor_chain || []).map((m) => m.id).join(" → ");
    const e4pct = Math.round(Number(e4.recent_success_rate || 0) * 100);
    const e4tgt = Math.round(Number(e4.target_rate || 0.85) * 100);
    chainEl.textContent = `${chain} · E4 delege %${e4pct} (≥${e4tgt}%)`;
  }
  if (logEl) {
    const rows = (payload.context_log || []).map(
      (r) =>
        `${r.success ? "✓" : "×"} ${r.scope_rel || "?"} · ${r.goal || ""} · ${r.verify_ok === true ? "pytest ok" : r.verify_ok === false ? "pytest fail" : ""}`,
    );
    logEl.textContent = rows.slice(-4).join("\n") || "—";
  }
  window.__ruzgarHandoffWorkbench = payload;
}

async function refreshProgramlamaHandoffWorkbench() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = new URLSearchParams({ workspace_root: workspaceRoot });
    if (atolyeOpenRel) qs.set("active_file", atolyeOpenRel);
    const res = await fetch(`${API}/api/programlama/handoff-workbench?${qs}`);
    const data = await res.json().catch(() => ({}));
    renderProgramlamaHandoff(data);
  } catch (_) {
    /* ignore */
  }
}

async function refreshProgramlamaWeeklyKpi() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/weekly-kpi${qs}`);
    const data = await res.json().catch(() => ({}));
    renderProgramlamaWeeklyKpi(data);
  } catch (_) {
    /* ignore */
  }
}

async function refreshProgramlamaKpiDashboard() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/kpi-dashboard${qs}`);
    const data = await res.json().catch(() => ({}));
    if (data.ok && data.compliance) {
      renderProgramlamaCompliance(data.compliance);
    }
    if (data.task_stats || data.live_kpi) {
      renderProgramlamaTaskStats(data.task_stats, data.live_kpi);
    }
    await refreshProgramlamaGitChanges(programlamaScopeFromContext());
    await refreshProgramlamaWeeklyKpi();
    await refreshProgramlamaMegaWorkbench();
    await refreshProgramlamaHandoffWorkbench();
    await refreshProgramlamaLocalWorkbench();
  } catch (_) {
    /* ignore */
  }
  await refreshProgramlamaUmitOnay();
}

function renderProgramlamaAgentSteps(steps) {
  const wrap = document.getElementById("programlama-agent-steps");
  const list = document.getElementById("programlama-agent-list");
  if (!wrap || !list) return;
  const rows = Array.isArray(steps) ? steps : [];
  if (!rows.length) {
    wrap.hidden = true;
    list.innerHTML = "";
    return;
  }
  wrap.hidden = false;
  list.innerHTML = "";
  const reduced = isFaz7ReducedMotion();
  rows.forEach((s, idx) => {
    const li = document.createElement("li");
    const st = String(s.status || "skip");
    li.className = `agent-step agent-step-${st}${reduced ? "" : " agent-step-enter"}`;
    if (!reduced) li.style.animationDelay = `${Math.min(idx * 55, 330)}ms`;
    const lab = esc(String(s.label || s.id || ""));
    const det = esc(String(s.detail || ""));
    const dot =
      st === "active"
        ? `<span class="agent-step-dot" aria-hidden="true"></span>`
        : st === "done"
          ? `<span class="agent-step-check" aria-hidden="true">✓</span>`
          : "";
    li.innerHTML =
      `${dot}<span class="agent-step-label">${lab}</span><span class="agent-step-detail">${det}</span>`;
    list.appendChild(li);
  });
}

function renderProgramlamaPatchCounts(counts) {
  const elCounts = document.getElementById("programlama-patch-counts");
  if (!elCounts || !counts) return;
  const p = Number(counts.pending || 0);
  const a = Number(counts.accepted || 0);
  const r = Number(counts.rejected || 0);
  elCounts.textContent = `bekleyen ${p} · kabul ${a} · red ${r}`;
}

let programlamaPatchTabsCache = [];

function hideProgramlamaInlineDiff() {
  const panel = document.getElementById("programlama-inline-diff");
  if (panel) panel.hidden = true;
}

function renderInlineDiffV2(data) {
  const preOld = document.getElementById("inline-diff-old");
  const preNew = document.getElementById("inline-diff-new");
  const htmlOld = document.getElementById("inline-diff-old-html");
  const htmlNew = document.getElementById("inline-diff-new-html");
  const unified = document.getElementById("inline-diff-unified");
  const cols = document.getElementById("inline-diff-cols");
  const statsEl = document.getElementById("inline-diff-stats");
  const v2 = Boolean(data.editor_v2 || data.editor_v2_default);
  if (!v2) {
    if (unified) unified.hidden = true;
    if (htmlOld) htmlOld.hidden = true;
    if (htmlNew) htmlNew.hidden = true;
    if (preOld) preOld.hidden = false;
    if (preNew) preNew.hidden = false;
    if (cols) cols.hidden = false;
    if (preOld) preOld.textContent = data.old_text || "(yeni dosya)";
    if (preNew) preNew.textContent = data.new_text || "";
    if (statsEl) statsEl.textContent = "";
    return;
  }
  if (preOld) preOld.hidden = true;
  if (preNew) preNew.hidden = true;
  if (htmlOld) {
    htmlOld.hidden = false;
    htmlOld.innerHTML = data.html_old || "";
  }
  if (htmlNew) {
    htmlNew.hidden = false;
    htmlNew.innerHTML = data.html_new || "";
  }
  if (unified && data.html_unified) {
    unified.hidden = false;
    unified.innerHTML = data.html_unified;
  } else if (unified) {
    unified.hidden = true;
  }
  if (cols) cols.hidden = Boolean(data.html_unified);
  const st = data.stats || {};
  if (statsEl) {
    statsEl.textContent = `+${st.add || 0} −${st.del || 0} · ${data.lang || ""}`;
  }
}

function renderProgramlamaPatchTabs(tabs, activePath) {
  const bar = document.getElementById("programlama-patch-tabs");
  if (!bar) return;
  programlamaPatchTabsCache = Array.isArray(tabs) ? tabs : [];
  if (!programlamaPatchTabsCache.length) {
    bar.hidden = true;
    bar.innerHTML = "";
    return;
  }
  bar.hidden = false;
  bar.innerHTML = "";
  for (const tab of programlamaPatchTabsCache) {
    const path = String(tab.path || "");
    if (!path) continue;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `programlama-patch-tab status-${escAttr(String(tab.status || "pending"))}${path === activePath ? " active" : ""}`;
    btn.textContent = String(tab.basename || path);
    btn.title = path;
    btn.addEventListener("click", () => {
      for (const b of bar.querySelectorAll(".programlama-patch-tab")) {
        b.classList.toggle("active", b === btn);
      }
      void showProgramlamaInlineDiff(path);
    });
    bar.appendChild(btn);
  }
}

async function refreshProgramlamaPatchUx() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  const hintEl = document.getElementById("programlama-patch-ux-hint");
  if (!workspaceRoot || !hintEl) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/patch/ux${qs}`);
    const data = await res.json().catch(() => ({}));
    if (!data.ok) {
      hintEl.hidden = true;
      return;
    }
    const tabs = data.tabs || [];
    renderProgramlamaPatchTabs(tabs, tabs[0]?.path);
    if (data.hint) {
      hintEl.hidden = false;
      hintEl.textContent = data.hint;
    } else {
      hintEl.hidden = true;
    }
  } catch (_) {
    hintEl.hidden = true;
  }
}

(function wireAnaMotorPatchButtons() {
  const refreshBtn = document.getElementById("btn-ana-patch-refresh");
  const applyBtn = document.getElementById("btn-ana-patch-apply");
  if (refreshBtn && !refreshBtn.dataset.wired) {
    refreshBtn.dataset.wired = "1";
    refreshBtn.addEventListener("click", () => {
      void refreshProgramlamaPatchFromServer();
      flashRuzgarDurum("Patch listesi yenilendi.");
    });
  }
  if (applyBtn && !applyBtn.dataset.wired) {
    applyBtn.dataset.wired = "1";
    applyBtn.addEventListener("click", () => void patchUnifiedApplyFromAtolye());
  }
})();

async function patchUnifiedApplyFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const res = await fetch(`${API}/api/programlama/patch/unified-apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_root: workspaceRoot, run_verify: true }),
    });
    const data = await res.json().catch(() => ({}));
    setCodeOutput(data.report || data.apply?.report || "Birleşik uygulama bitti.");
    if (data.bundle) {
      showProgramlamaPatchStrip({
        action: "applied",
        applied: data.apply?.applied || [],
        errors: data.apply?.errors || [],
        items: data.bundle.items || [],
        counts: data.bundle.counts || {},
      });
    } else {
      await refreshProgramlamaPatchFromServer();
    }
    hideProgramlamaInlineDiff();
    const tabsBar = document.getElementById("programlama-patch-tabs");
    if (tabsBar) tabsBar.hidden = true;
  } catch (e) {
    setCodeOutput(`Birleşik uygulama: ${e && e.message ? e.message : e}`);
  }
}

async function showProgramlamaInlineDiff(relPath) {
  const rel = String(relPath || "").replace(/\\/g, "/");
  if (!rel) return;
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) {
    setCodeOutput("Editör diff için workspace kökü gerekli.");
    return;
  }
  const panel = document.getElementById("programlama-inline-diff");
  const preOld = document.getElementById("inline-diff-old");
  const preNew = document.getElementById("inline-diff-new");
  const title = document.getElementById("programlama-inline-diff-title");
  if (!panel || !preOld || !preNew) return;
  try {
    const qs = new URLSearchParams({
      workspace_root: workspaceRoot,
      path: rel,
    });
    const res = await fetch(`${API}/api/programlama/patch/inline-diff?${qs}`);
    const data = await res.json().catch(() => ({}));
    if (!data.ok) {
      setCodeOutput(data.error || "Inline diff alınamadı.");
      return;
    }
    if (title) title.textContent = `Editör diff — ${rel}`;
    renderInlineDiffV2(data);
    panel.hidden = false;
    void openProgramlamaWorkspaceFile(rel);
    if (data.new_text && el.codeEditor) {
      el.codeEditor.value = data.new_text;
    }
    const bar = document.getElementById("programlama-patch-tabs");
    if (bar && programlamaPatchTabsCache.length) {
      for (const b of bar.querySelectorAll(".programlama-patch-tab")) {
        b.classList.toggle("active", b.title === rel);
      }
    }
    flashRuzgarDurum(
      data.editor_v2 || data.editor_v2_default
        ? "Faz 53: renkli çok dosya diff"
        : "Faz 27: eski/yeni"
    );
  } catch (e) {
    setCodeOutput(`Inline diff: ${e && e.message ? e.message : e}`);
  }
}

function showProgramlamaPatchStrip(codePatch) {
  const strip = document.getElementById("programlama-patch-strip");
  const list = document.getElementById("programlama-patch-list");
  if (!strip || !list || !codePatch) return;
  const applied = Array.isArray(codePatch.applied) ? codePatch.applied : [];
  const errors = Array.isArray(codePatch.errors) ? codePatch.errors : [];
  const items = Array.isArray(codePatch.items) ? codePatch.items : [];
  const counts = codePatch.counts || {};
  const action = String(codePatch.action || "");
  if (!applied.length && !errors.length && !items.length && action !== "staged") {
    strip.hidden = true;
    return;
  }
  strip.hidden = false;
  renderProgramlamaPatchCounts(counts);
  list.innerHTML = "";

  const renderItem = (it, opts = {}) => {
    const path = String(it.path || "");
    if (!path) return;
    const li = document.createElement("li");
    li.className = "programlama-patch-item";
    const head = document.createElement("div");
    head.className = "programlama-patch-item-head";
    const st = String(it.status || opts.status || "pending");
    const mark = opts.done ? "✓" : st === "rejected" ? "✗" : "○";
    head.innerHTML = `${mark} <code>${esc(path)}</code> <span class="programlama-patch-status ${escAttr(st)}">${esc(st)}</span>`;
    const actions = document.createElement("div");
    actions.className = "programlama-patch-actions";
    const btnOpen = document.createElement("button");
    btnOpen.type = "button";
    btnOpen.className = "btn-secondary btn-compact";
    btnOpen.textContent = "Aç";
    btnOpen.addEventListener("click", () => void openProgramlamaWorkspaceFile(path));
    const btnDiff = document.createElement("button");
    btnDiff.type = "button";
    btnDiff.className = "btn-secondary btn-compact";
    btnDiff.textContent = "Editör diff";
    btnDiff.addEventListener("click", () => void showProgramlamaInlineDiff(path));
    actions.appendChild(btnOpen);
    actions.appendChild(btnDiff);
    if (action === "staged" && st !== "applied" && st !== "rejected") {
      const btnOk = document.createElement("button");
      btnOk.type = "button";
      btnOk.className = "btn-secondary btn-compact";
      btnOk.textContent = "Kabul";
      btnOk.addEventListener("click", () =>
        void patchItemStatus(path, "accepted"),
      );
      const btnNo = document.createElement("button");
      btnNo.type = "button";
      btnNo.className = "btn-secondary btn-compact";
      btnNo.textContent = "Red";
      btnNo.addEventListener("click", () =>
        void patchItemStatus(path, "rejected"),
      );
      actions.appendChild(btnOk);
      actions.appendChild(btnNo);
    }
    head.appendChild(actions);
    li.appendChild(head);
    const diff = String(it.diff || "");
    if (diff.trim()) {
      const pre = document.createElement("pre");
      pre.className = "programlama-patch-diff";
      pre.textContent = diff;
      li.appendChild(pre);
    }
    list.appendChild(li);
  };

  if (action === "staged" && items.length) {
    for (const it of items) renderItem(it);
  } else {
    const diffByPath = new Map(
      items.filter((x) => x && x.path).map((x) => [String(x.path), x]),
    );
    for (const p of applied) {
      const meta = diffByPath.get(p) || { path: p };
      renderItem({ ...meta, path: p }, { done: true, status: "applied" });
    }
    for (const it of items) {
      if (!applied.includes(it.path)) renderItem(it);
    }
  }
  for (const e of errors) {
    const li = document.createElement("li");
    li.textContent = `✗ ${e}`;
    list.appendChild(li);
  }
}

async function getProgramlamaWorkspaceRoot() {
  try {
    if (window.ruzgarApi?.getRoot) return await window.ruzgarApi.getRoot();
  } catch (_) {
    /* ignore */
  }
  return null;
}

async function refreshProgramlamaProjectSelect() {
  const sel = el.progProjectSelect;
  if (!sel) return;
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/workspace-projects${qs}`);
    const data = await res.json().catch(() => ({}));
    if (!data.ok) return;
    const active = String(data.active_project || "").trim();
    const projects = Array.isArray(data.projects) ? data.projects : [];
    sel.innerHTML = "";
    const ph = document.createElement("option");
    ph.value = "";
    ph.textContent = projects.length ? "Proje seç…" : "Proje yok";
    sel.appendChild(ph);
    for (const p of projects) {
      const slug = String(p.slug || "").trim();
      if (!slug) continue;
      const opt = document.createElement("option");
      opt.value = slug;
      opt.textContent = slug + (p.has_git ? " · git" : "");
      if (slug === active) opt.selected = true;
      sel.appendChild(opt);
    }
  } catch (_) {
    /* ignore */
  }
}

async function switchProgramlamaProject(slug) {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot || !slug) return;
  try {
    const res = await fetch(`${API}/api/programlama/workspace/switch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_root: workspaceRoot, project_slug: slug }),
    });
    const data = await res.json().catch(() => ({}));
    if (!data.ok) {
      setCodeOutput(data.detail || data.error || "Proje geçişi başarısız.");
      return;
    }
    if (data.focus_rel) {
      await applyProgramlamaFocusFromChat({
        programlama_focus_rel: data.focus_rel,
        programlama_project_rel: data.project_rel,
        programlama_expand_tree: true,
      });
    } else {
      await programlamaAtolyeRefreshRoot();
    }
    flashRuzgarDurum(`Aktif proje: ${slug}`);
  } catch (e) {
    setCodeOutput(`Proje geçişi: ${e && e.message ? e.message : e}`);
  }
}

async function refreshProgramlamaPatchFromServer() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = `?workspace_root=${encodeURIComponent(workspaceRoot)}`;
    const res = await fetch(`${API}/api/programlama/patch/pending${qs}`);
    const data = await res.json().catch(() => ({}));
    if (!data.ok || !data.count) {
      const strip = document.getElementById("programlama-patch-strip");
      if (strip) strip.hidden = true;
      return;
    }
    showProgramlamaPatchStrip({
      action: "staged",
      items: data.items || [],
      counts: data.counts || {},
      count: data.count,
    });
    const tabs = (data.items || []).map((it) => ({
      path: it.path,
      status: it.status,
      basename: String(it.path || "").split("/").pop(),
    }));
    const firstPath = tabs[0]?.path;
    renderProgramlamaPatchTabs(tabs, firstPath);
    void refreshProgramlamaPatchUx();
    if (data.multi_file_preview_default && firstPath) {
      await showProgramlamaInlineDiff(firstPath);
    }
  } catch (_) {
    /* ignore */
  }
}

async function patchItemStatus(path, status) {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const res = await fetch(`${API}/api/programlama/patch/item`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_root: workspaceRoot, path, status }),
    });
    const data = await res.json().catch(() => ({}));
    if (data.bundle) {
      showProgramlamaPatchStrip({
        action: "staged",
        items: data.bundle.items || [],
        counts: data.bundle.counts || {},
      });
    } else {
      await refreshProgramlamaPatchFromServer();
    }
  } catch (e) {
    setCodeOutput(`Patch durum: ${e && e.message ? e.message : e}`);
  }
}

async function patchAcceptAllFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    await fetch(`${API}/api/programlama/patch/accept-all`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_root: workspaceRoot }),
    });
    await refreshProgramlamaPatchFromServer();
  } catch (e) {
    setCodeOutput(`Kabul hatası: ${e && e.message ? e.message : e}`);
  }
}

function closeProjeUretModal() {
  const modal = document.getElementById("proje-uret-modal");
  if (modal) modal.hidden = true;
}

function openProjeUretModal() {
  const modal = document.getElementById("proje-uret-modal");
  if (!modal) return;
  modal.hidden = false;
  void loadProjeUretTemplates();
}

async function loadProjeUretTemplates() {
  const sel = document.getElementById("proje-uret-template");
  if (!sel || sel.dataset.loaded === "1") return;
  try {
    const res = await fetch(`${API}/api/programlama/proje-uret/templates`);
    const data = await res.json().catch(() => ({}));
    const rows = Array.isArray(data.templates) ? data.templates : [];
    sel.innerHTML = "";
    for (const t of rows) {
      const opt = document.createElement("option");
      opt.value = String(t.id || "");
      opt.textContent = `${t.label || t.id} — ${t.desc || ""}`.slice(0, 72);
      sel.appendChild(opt);
    }
    if (!rows.length) {
      const opt = document.createElement("option");
      opt.value = "fastapi_api";
      opt.textContent = "FastAPI REST API";
      sel.appendChild(opt);
    }
    sel.dataset.loaded = "1";
  } catch (_) {
    sel.innerHTML = '<option value="fastapi_api">FastAPI REST API</option>';
  }
}

async function runProjeUretFromUi() {
  const templateId = String(document.getElementById("proje-uret-template")?.value || "fastapi_api");
  const name = String(document.getElementById("proje-uret-name")?.value || "").trim();
  const goal = String(document.getElementById("proje-uret-goal")?.value || "").trim();
  const features = String(document.getElementById("proje-uret-features")?.value || "").trim();
  if (!name) {
    setCodeOutput("Proje adı gerekli.");
    return;
  }
  let workspaceRoot = null;
  try {
    if (window.ruzgarApi?.getRoot) workspaceRoot = await window.ruzgarApi.getRoot();
  } catch (_) {
    workspaceRoot = null;
  }
  if (!workspaceRoot) {
    setCodeOutput("Proje üret için workspace kökü gerekli (Electron).");
    return;
  }
  closeProjeUretModal();
  setCodeOutput(`Proje üretiliyor: ${templateId} / ${name}…`);
  const enc = encodeURIComponent(workspaceRoot);
  const g = encodeURIComponent(goal || "health version pytest geçir");
  const f = encodeURIComponent(features);
  try {
    const res = await fetch(
      `${API}/api/programlama/proje-uret?workspace_root=${enc}` +
        `&template_id=${encodeURIComponent(templateId)}` +
        `&project_name=${encodeURIComponent(name)}` +
        `&goal=${g}` +
        (features ? `&features=${f}` : "")
    );
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error(data.detail || data.error || `HTTP ${res.status}`);
    }
    setCodeOutput(data.report || "Proje üret raporu.");
    const scope = data.data?.scope_rel || `projects/${name}`;
    let focusRel = `${scope}/index.html`;
    if (templateId === "fastapi_api") focusRel = `${scope}/app/main.py`;
    else if (templateId === "react_vite") focusRel = `${scope}/src/App.jsx`;
    else if (templateId === "mobile_expo") focusRel = `${scope}/App.js`;
    else if (templateId === "cli_python") focusRel = `${scope}/main.py`;
    await applyProgramlamaFocusFromChat({
      programlama_focus_rel: focusRel,
      programlama_project_rel: scope,
      programlama_expand_tree: true,
    });
    flashRuzgarDurum(
      data.ready_without_agent
        ? `Proje hazır (pytest OK): ${name}`
        : `Scaffold OK — ajan başlatılıyor: ${name}`
    );
    if (data.agent_required && data.agent_message) {
      switchMode("programlama");
      if (el.code) el.code.checked = true;
      setCodeOutput("Ajan görevi sohbet panelinde başlatıldı.");
      void sendMessageWithText(String(data.agent_message), { skipUserBubble: false });
    }
  } catch (e) {
    setCodeOutput(`Proje üret hatası: ${e && e.message ? e.message : e}`);
  }
}

async function runQuickScaffold(templateId, defaultName) {
  let workspaceRoot = null;
  try {
    if (window.ruzgarApi?.getRoot) workspaceRoot = await window.ruzgarApi.getRoot();
  } catch (_) {
    workspaceRoot = null;
  }
  if (!workspaceRoot) {
    setCodeOutput("Şablon için workspace kökü gerekli (Electron).");
    return;
  }
  const name =
    window.prompt("Proje adı (projects/ altına yazılır):", defaultName) || defaultName;
  if (!name.trim()) return;
  setCodeOutput(`Şablon oluşturuluyor: ${templateId} / ${name}…`);
  try {
    const res = await fetch(`${API}/api/programlama/scaffold`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_root: workspaceRoot,
        template_id: templateId,
        project_name: name.trim(),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      throw new Error(data.error || data.detail || `HTTP ${res.status}`);
    }
    setCodeOutput(data.report || "Şablon hazır.");
    const focus = data.focus?.focus_rel;
    if (focus) {
      await applyProgramlamaFocusFromChat({
        programlama_focus_rel: focus,
        programlama_project_rel: data.focus?.project_rel,
        programlama_expand_tree: true,
      });
    } else {
      await programlamaAtolyeRefreshRoot();
    }
    flashRuzgarDurum(`Şablon: ${data.base_dir || name}`);
  } catch (e) {
    setCodeOutput(`Şablon hatası: ${e && e.message ? e.message : e}`);
  }
}

async function applyPendingPatchFromAtolye(mode = "accepted") {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) {
    setCodeOutput("Workspace kökü yok — Electron köprüsü gerekli.");
    return;
  }
  try {
    const res = await fetch(`${API}/api/programlama/patch/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_root: workspaceRoot,
        rel: atolyeOpenRel || undefined,
        run_verify: true,
        mode,
      }),
    });
    const data = await res.json().catch(() => ({}));
    setCodeOutput(data.report || data.error || "Patch uygulandı.");
    if (data.applied?.length) {
      showProgramlamaPatchStrip({
        action: "applied",
        applied: data.applied,
        errors: data.errors || [],
        items: data.items || [],
      });
      void openProgramlamaWorkspaceFile(data.applied[0]);
    } else if (!data.ok) {
      await refreshProgramlamaPatchFromServer();
    } else {
      const strip = document.getElementById("programlama-patch-strip");
      if (strip) strip.hidden = true;
    }
  } catch (e) {
    setCodeOutput(`Patch hatası: ${e && e.message ? e.message : e}`);
  }
}

async function gitStatusFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = new URLSearchParams({
      workspace_root: workspaceRoot,
    });
    if (atolyeOpenRel) qs.set("active_file", atolyeOpenRel);
    const res = await fetch(`${API}/api/programlama/git/status?${qs}`);
    const data = await res.json().catch(() => ({}));
    setCodeOutput(data.report || data.snapshot?.error || "Git durum bitti.");
  } catch (e) {
    setCodeOutput(`Git: ${e && e.message ? e.message : e}`);
  }
}

async function gitSuggestCommitFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const res = await fetch(`${API}/api/programlama/git/suggest-commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_root: workspaceRoot,
        rel: atolyeOpenRel || undefined,
      }),
    });
    const data = await res.json().catch(() => ({}));
    setCodeOutput(data.report || data.error || "Commit önerisi hazır.");
  } catch (e) {
    setCodeOutput(`Commit öner: ${e && e.message ? e.message : e}`);
  }
}

async function gitPrStatusFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const qs = new URLSearchParams({ workspace_root: workspaceRoot });
    if (atolyeOpenRel) qs.set("active_file", atolyeOpenRel);
    const res = await fetch(`${API}/api/programlama/git/pr-status?${qs}`);
    const data = await res.json().catch(() => ({}));
    setCodeOutput(data.report || data.snapshot?.error || "PR durum bitti.");
  } catch (e) {
    setCodeOutput(`PR durum: ${e && e.message ? e.message : e}`);
  }
}

async function gitPrCreateFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  const title =
    window.prompt("PR başlığı (boş = son commit mesajı):", "") || "";
  if (title === null) return;
  try {
    const res = await fetch(`${API}/api/programlama/git/pr-create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        workspace_root: workspaceRoot,
        rel: atolyeOpenRel || undefined,
        title: title.trim(),
        push_first: true,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setCodeOutput(data.detail || data.error || data.report || "PR açılamadı.");
      return;
    }
    setCodeOutput(data.report || data.url || "PR oluşturuldu.");
  } catch (e) {
    setCodeOutput(`PR: ${e && e.message ? e.message : e}`);
  }
}

async function gitCommitFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const res = await fetch(`${API}/api/programlama/git/commit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_root: workspaceRoot, rel: atolyeOpenRel || undefined }),
    });
    const data = await res.json().catch(() => ({}));
    setCodeOutput(data.report || data.error || "Commit tamam.");
    if (data.ok) void programlamaAtolyeRefreshRoot();
  } catch (e) {
    setCodeOutput(`Commit: ${e && e.message ? e.message : e}`);
  }
}

async function prPrepareFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  const title =
    window.prompt("PR başlık ipucu (boş = otomatik):", "") ?? "";
  if (title === null) return;
  const scope = programlamaScopeFromContext();
  try {
    const qs = new URLSearchParams({
      workspace_root: workspaceRoot,
      scope_rel: scope,
    });
    if (title.trim()) qs.set("title", title.trim());
    const res = await fetch(`${API}/api/programlama/pr-plan?${qs}`);
    const data = await res.json().catch(() => ({}));
    const plan = data.plan || {};
    if (data.ok && plan.branch_suggest) {
      const enriched = {
        ok: true,
        strip: { branch: plan.branch, summary: "PR planı", has_changes: true, file_lines: [] },
        snapshot: { diff_stat_preview: plan.diff_stat || "" },
        branch_suggest: plan.branch_suggest,
        commit_suggest: { message: (plan.commit_message || "").split("\n")[0] },
      };
      renderProgramlamaGitChanges(enriched);
    }
    renderProgramlamaPrPlan(data);
    setCodeOutput(data.report || "PR planı hazır — otomatik PR açılmadı.");
  } catch (e) {
    setCodeOutput(`PR hazırla: ${e && e.message ? e.message : e}`);
  }
}

async function megaRefactorFromAtolye() {
  const scope = programlamaScopeFromContext();
  const hint =
    window.prompt("Mega refactor hedefi (kısa):", "tüm modülleri pytest geçir") || "";
  if (hint === null) return;
  const msg = `mega refactor ${scope}: ${hint.trim() || "10+ dosya düzenle"}`;
  void sendMessageWithText(msg);
  setCodeOutput(`Mega görev başlatılıyor: ${msg.slice(0, 120)}…`);
  void refreshProgramlamaMegaWorkbench();
}

async function megaResumeFromAtolye() {
  const wb = window.__ruzgarMegaWorkbench;
  const hint =
    (wb && wb.agent && wb.agent.resume_hint) ||
    document.getElementById("btn-mega-resume")?.dataset?.resumeHint ||
    "";
  if (!hint) {
    setCodeOutput("Devam edilecek yarım görev yok.");
    return;
  }
  void sendMessageWithText(hint);
  setCodeOutput(`Görev devam: ${hint.slice(0, 120)}`);
}

async function gitDiffPreviewFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  const scope = programlamaScopeFromContext();
  try {
    const qs = new URLSearchParams({
      workspace_root: workspaceRoot,
      scope_rel: scope,
    });
    if (atolyeOpenRel) qs.set("active_file", atolyeOpenRel);
    const res = await fetch(`${API}/api/programlama/git-changes?${qs}`);
    const data = await res.json().catch(() => ({}));
    renderProgramlamaGitChanges(data);
    const diffTxt = String((data.snapshot || {}).diff_stat_preview || "").trim();
    const diffPre = document.getElementById("programlama-git-diff-preview");
    if (diffPre) {
      diffPre.dataset.pinned = "1";
      diffPre.hidden = !diffTxt;
      diffPre.textContent = diffTxt || "(diff boş — çalışma ağacı temiz)";
    }
    setCodeOutput(diffTxt || data.strip?.summary || "Diff önizleme — değişiklik yok.");
  } catch (e) {
    setCodeOutput(`Diff: ${e && e.message ? e.message : e}`);
  }
}

async function rollbackPatchFromAtolye() {
  const workspaceRoot = await getProgramlamaWorkspaceRoot();
  if (!workspaceRoot) return;
  try {
    const res = await fetch(`${API}/api/programlama/patch/rollback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ workspace_root: workspaceRoot }),
    });
    const data = await res.json().catch(() => ({}));
    setCodeOutput(
      data.restored?.length
        ? `Geri alındı: ${data.restored.join(", ")}`
        : data.error || data.errors?.join("; ") || "Geri alma bitti.",
    );
    await programlamaAtolyeRefreshRoot();
  } catch (e) {
    setCodeOutput(`Geri alma: ${e && e.message ? e.message : e}`);
  }
}

function renderDashboardAgentSteps(steps) {
  ensureDashboardAgentUi();
  if (!dashboardAgentListEl || !dashboardAgentWrapEl) return;
  const list = Array.isArray(steps) ? steps : [];
  if (!list.length) {
    dashboardAgentWrapEl.hidden = true;
    dashboardAgentListEl.innerHTML = "";
    return;
  }
  dashboardAgentWrapEl.hidden = false;
  dashboardAgentListEl.innerHTML = "";
  const reduced = isFaz7ReducedMotion();
  list.forEach((s, idx) => {
    const li = document.createElement("li");
    const st = String(s.status || "skip");
    li.className = `agent-step agent-step-${st}${reduced ? "" : " agent-step-enter"}`;
    if (!reduced) li.style.animationDelay = `${Math.min(idx * 55, 330)}ms`;
    const lab = esc(String(s.label || s.id || ""));
    const det = esc(String(s.detail || ""));
    const dot =
      st === "active"
        ? `<span class="agent-step-dot" aria-hidden="true"></span>`
        : st === "done"
          ? `<span class="agent-step-check" aria-hidden="true">✓</span>`
          : "";
    li.innerHTML =
      `${dot}<span class="agent-step-label">${lab}</span><span class="agent-step-detail">${det}</span>`;
    dashboardAgentListEl.appendChild(li);
  });
}

function renderOrchestraBridge(orch) {
  const wrap = el.orchestraBridge;
  if (!orch) {
    clearOrchestraBridge();
    renderDashboardAgentSteps([]);
    return;
  }
  if (Array.isArray(orch.agent_steps) && orch.agent_steps.length) {
    renderDashboardAgentSteps(orch.agent_steps);
    if (currentMode === "programlama" || orch.programlama_faz11) {
      renderProgramlamaAgentSteps(orch.agent_steps);
    }
  }
  const motors = Array.isArray(orch.motors) ? orch.motors : [];
  const plan = orch.plan && typeof orch.plan === "object" ? orch.plan : null;
  if (!wrap) return;
  if (!plan && motors.length === 0) {
    clearOrchestraBridge();
    return;
  }
  wrap.hidden = false;
  wrap.innerHTML = "";
  if (plan && plan.primary) {
    const hint = document.createElement("div");
    hint.className = "orchestra-plan-hint";
    const sec =
      Array.isArray(plan.secondary) && plan.secondary.length
        ? ` · ${plan.secondary.slice(0, 2).join(", ")}`
        : "";
    const lab = plan.label_tr || plan.primary;
    const src = plan.sources ? ` · ${plan.sources}` : "";
    hint.textContent = `Soru planı: ${lab}${src}${sec}`;
    wrap.appendChild(hint);
  }
  if (motors.length === 0) return;
  const title = document.createElement("div");
  title.className = "orchestra-bridge-title";
  title.textContent = "Ana motor — çalışma sayfası köprüleri";
  wrap.appendChild(title);
  const hoWb = window.__ruzgarHandoffWorkbench;
  if (hoWb && hoWb.delegation && hoWb.delegation.pytest_footer) {
    const pf = document.createElement("div");
    pf.className = "orchestra-plan-hint";
    pf.textContent = `Son delege: ${hoWb.delegation.pytest_footer}`;
    wrap.appendChild(pf);
  }
  const row = document.createElement("div");
  row.className = "orchestra-bridge-actions";
  for (const m of motors) {
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
  if (window.RuzgarSplit?.refresh) {
    requestAnimationFrame(() => window.RuzgarSplit.refresh());
  }
}

/**
 * HIZIR — çalışma başlığı şeridi (yalnızca hizir modunda).
 */
function syncHizirWorkbenchStripVisibility() {
  if (!el.hizirWorkbenchStrip) return;
  const show = currentMode === "hizir";
  el.hizirWorkbenchStrip.hidden = !show;
  if (!show) return;
  const apiChipOk = !!(el.api && el.api.classList.contains("ok"));
  setHizirWorkbenchServerPill(apiChipOk, el.api?.title || "");
}

/** HIZIR modunda düzen seçicileri gizle; HIZIR araç çubuğunu göster. */
function syncWorkbenchHizirToolbar() {
  const layout = el.workbenchLayoutTools || document.getElementById("workbench-layout-tools");
  const hiz = el.workbenchHizirTools || document.getElementById("workbench-hizir-tools");
  if (!layout || !hiz) return;
  const isH = currentMode === "hizir";
  /* UI Fix — HIZIR sayfasında «sayfayı böl» araçlarını akıştan tamamen çıkar */
  layout.hidden = isH;
  layout.style.display = isH ? "none" : "";
  const wbCtl = document.querySelector(".workbench-controls");
  if (wbCtl) wbCtl.classList.toggle("workbench-controls--hizir", isH);
  if (isH) {
    hiz.removeAttribute("hidden");
    hiz.style.removeProperty("display");
  } else {
    hiz.setAttribute("hidden", "");
    hiz.style.display = "none";
  }
  document.body.classList.toggle("workbench-hizir-active", isH);
}

async function triggerRuzgarApiRestart() {
  if (window.ruzgarApi && typeof window.ruzgarApi.restartApi === "function") {
    return window.ruzgarApi.restartApi();
  }
  flashRuzgarDurum("Ruzgar_YenidenBaslat.bat dosyasını proje kökünden çalıştırın.");
  return { ok: false };
}

async function waitForExpectedBuildRev(maxSec = 120) {
  const deadline = Date.now() + maxSec * 1000;
  while (Date.now() < deadline) {
    try {
      const r = await fetch(`${API}/api/health`, { method: "GET" });
      if (r.ok) {
        const j = await r.json();
        const rev = String(j?.build?.rev || "").trim();
        if (rev === RUZGAR_EXPECTED_BUILD_REV) {
          return { ok: true, rev };
        }
      }
    } catch (_) {
      /* API henüz ayakta değil */
    }
    await new Promise((resolve) => setTimeout(resolve, 800));
  }
  return { ok: false };
}

function showStaleBuildBanner(rev, healthPayload) {
  const hp = healthPayload && typeof healthPayload === "object" ? healthPayload : {};
  const expected =
    String(hp?.build?.expected_rev || RUZGAR_EXPECTED_BUILD_REV).trim() ||
    RUZGAR_EXPECTED_BUILD_REV;
  const stale = Boolean(
    rev && (hp?.build?.build_mismatch === true || rev !== expected),
  );
  let box = document.getElementById("ruzgar-stale-build-banner");
  if (!stale) {
    if (box) box.remove();
    window.__ruzgarApiRestartBusy = false;
    return;
  }
  if (!box) {
    box = document.createElement("div");
    box.id = "ruzgar-stale-build-banner";
    box.setAttribute("role", "alert");
    box.style.cssText =
      "margin:8px 12px;padding:10px 14px;background:#fef2f2;border:1px solid #f87171;" +
      "color:#991b1b;border-radius:8px;font-size:13px;line-height:1.45;";
    const host =
      document.getElementById("page-programlama") ||
      document.querySelector(".panel-chat") ||
      document.body;
    host.prepend(box);
  }
  box.innerHTML =
    `<strong>Eski API</strong> <code>${escAttr(rev)}</code> → <code>${escAttr(expected)}</code> ` +
    `<button type="button" id="ruzgar-stale-restart-btn" style="margin-left:6px;padding:4px 10px;cursor:pointer;">Yeniden başlat</button>` +
    `<span id="ruzgar-stale-restart-status" style="margin-left:6px;font-size:11px;opacity:.9;"></span>`;
  const btn = document.getElementById("ruzgar-stale-restart-btn");
  const statusEl = document.getElementById("ruzgar-stale-restart-status");
  if (btn && !btn.dataset.wired) {
    btn.dataset.wired = "1";
    btn.addEventListener("click", async () => {
      if (window.__ruzgarApiRestartBusy) return;
      window.__ruzgarApiRestartBusy = true;
      btn.disabled = true;
      if (statusEl) statusEl.textContent = "Yeniden başlatılıyor…";
      try {
        const res = await triggerRuzgarApiRestart();
        if (res && res.ok) {
          if (statusEl) statusEl.textContent = "Güncel API bekleniyor…";
          flashRuzgarDurum("API yeniden başlatılıyor…");
          const ready = await waitForExpectedBuildRev(120);
          if (ready.ok) {
            if (statusEl) statusEl.textContent = "Güncel — sayfa yenileniyor…";
            window.location.reload();
          } else {
            if (statusEl) {
              statusEl.textContent =
                "Hâlâ eski sürüm — proje kökünden Ruzgar_YenidenBaslat.bat çalıştırın";
            }
            btn.disabled = false;
            window.__ruzgarApiRestartBusy = false;
          }
        } else {
          if (statusEl) statusEl.textContent = "Başarısız — Ruzgar_YenidenBaslat.bat";
          btn.disabled = false;
          window.__ruzgarApiRestartBusy = false;
        }
      } catch (e) {
        if (statusEl) statusEl.textContent = String(e?.message || e).slice(0, 80);
        btn.disabled = false;
        window.__ruzgarApiRestartBusy = false;
      }
    });
  }
}

function setHizirWorkbenchServerPill(connected, tooltipDetail) {
  const pill = el.hizirWbServer;
  if (!pill) return;
  pill.classList.remove("hizir-wb-server-ok", "hizir-wb-server-err", "hizir-wb-server-unknown");
  if (connected) {
    pill.textContent = "Sunucu: Bağlı";
    pill.classList.add("hizir-wb-server-ok");
    pill.title = tooltipDetail ? String(tooltipDetail) : "Yerel masaüstü API yanıt veriyor.";
  } else {
    pill.textContent = "Sunucu: Kopuk";
    pill.classList.add("hizir-wb-server-err");
    pill.title = tooltipDetail ? String(tooltipDetail) : "Önce ilim-assistant içinde desktop_server başlatın.";
  }
}

function setHizirWorkbenchServerPillUnknown() {
  const pill = el.hizirWbServer;
  if (!pill) return;
  pill.classList.remove("hizir-wb-server-ok", "hizir-wb-server-err");
  pill.classList.add("hizir-wb-server-unknown");
  pill.textContent = "Sunucu: …";
  pill.title = "";
}

function escAttr(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;");
}

async function openHizirProductUrl(url) {
  const u = String(url || "").trim();
  if (!u || !/^https?:\/\//i.test(u)) return false;
  try {
    if (typeof window !== "undefined" && window.ruzgarApi?.openExternalUrl) {
      const ok = await window.ruzgarApi.openExternalUrl(u);
      if (ok) return true;
    }
  } catch (_) {
    /* preload yok */
  }
  try {
    if (typeof window !== "undefined" && window.ruzgarApi?.openLocalhostUrl) {
      const ok2 = await window.ruzgarApi.openLocalhostUrl(u);
      if (ok2) return true;
    }
  } catch (_) {
    /* */
  }
  try {
    window.open(u, "_blank", "noopener,noreferrer");
    return true;
  } catch (_) {
    return false;
  }
}

/** Ürün görseli yüklenene kadar iskelet / spinner gösterir. */
function wireHizirImagePlaceholders(rootEl) {
  if (!rootEl) return;
  rootEl.querySelectorAll(".hizir-vitrin-card__img-wrap .hizir-vitrin-card__img--contain").forEach((img) => {
    const sk = img.previousElementSibling;
    if (!sk || !sk.classList.contains("hizir-img-skel")) return;
    const done = () => {
      sk.hidden = true;
      img.classList.add("is-loaded");
    };
    if (img.complete && img.naturalWidth > 0) done();
    else {
      img.addEventListener("load", done, { once: true });
    }
  });
}

/** Kırık görsel URL → yer tutucu ikon (HIZIR vitrin) */
function wireHizirImageErrorFallback(rootEl) {
  if (!rootEl) return;
  const ph =
    '<span class="hizir-ph-glyph hizir-ph-glyph--sm" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.4"/><path d="M20.5 16.5l-4.2-4.2-3.3 3.2-2.8-2.8-5.2 5.2"/></svg></span>';
  rootEl.querySelectorAll(".hizir-vitrin-card__img-wrap .hizir-vitrin-card__img--contain").forEach((img) => {
    if (img.dataset.hizirImgErr) return;
    img.dataset.hizirImgErr = "1";
    img.addEventListener(
      "error",
      () => {
        const sk = img.previousElementSibling;
        if (sk && sk.classList.contains("hizir-img-skel")) {
          sk.hidden = false;
          sk.classList.add("hizir-img-skel--fallback");
          sk.innerHTML = ph;
        }
        img.classList.remove("is-loaded");
        img.style.display = "none";
      },
      { once: true },
    );
  });
}

/** HIZIR vitrin — pazar logosu sınıfı (CSS ile renk). */
function hizirMpClass(platform) {
  const s = String(platform || "").toLowerCase();
  if (s.includes("trendyol")) return "hizir-mp hizir-mp--ty";
  if (s.includes("hepsiburada") || s.includes("hepsi")) return "hizir-mp hizir-mp--hb";
  if (s.includes("amazon")) return "hizir-mp hizir-mp--amz";
  if (s.includes("ebay")) return "hizir-mp hizir-mp--ebay";
  if (s.includes("aliexpress")) return "hizir-mp hizir-mp--ae";
  return "hizir-mp hizir-mp--gen";
}

function hizirMpInitials(platform) {
  const s = String(platform || "").trim();
  if (!s) return "?";
  const parts = s.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase().slice(0, 3);
  return s.slice(0, 2).toUpperCase();
}

function hizirFmtPrice(val, cur) {
  const c = String(cur || "TRY").toUpperCase();
  const n = Number(val);
  if (!Number.isFinite(n)) return "—";
  if (c === "TRY") {
    const t = n.toLocaleString("tr-TR", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
    return `${t} TL`;
  }
  return `${n.toFixed(2)} ${c}`;
}

function hizirRenderArbitrajVitrin(r) {
  const rawImg = String(r.gorsel_url || "").trim();
  const phIcon = `<span class="hizir-ph-glyph" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.4"/><path d="M20.5 16.5l-4.2-4.2-3.3 3.2-2.8-2.8-5.2 5.2"/></svg></span>`;
  const skel = `<div class="hizir-img-skel" aria-hidden="true"><span class="hizir-img-spin"></span></div>`;
  const mediaInner = rawImg
    ? `<div class="hizir-vitrin-card__img-wrap">${skel}<img class="hizir-vitrin-card__img hizir-vitrin-card__img--contain" src="${esc(rawImg)}" alt="" loading="lazy" width="128" height="128" decoding="async" referrerpolicy="no-referrer" /></div>`
    : `<div class="hizir-vitrin-card__img-wrap"><div class="hizir-vitrin-card__img hizir-vitrin-card__img--ph" role="img" aria-label="Ürün görseli">${phIcon}</div></div>`;
  const title = esc(String(r.urun_adi || "Ürün"));
  const bolge = esc(String(r.bolge || ""));
  const pb = String(r.para_birimi || "TRY").toUpperCase();
  const cheapPlRaw = String(r.ucuz_platform || "Kaynak");
  const expPlRaw = String(r.pahali_platform || "Hedef");
  const cheapPl = esc(cheapPlRaw);
  const expPl = esc(expPlRaw);
  const cheapName = esc(String(r.kaynak_urun_adi || r.urun_adi || ""));
  const expName = esc(String(r.hedef_urun_adi || r.urun_adi || ""));
  const kf = esc(hizirFmtPrice(r.kaynak_fiyat, pb));
  const hf = esc(hizirFmtPrice(r.hedef_fiyat, pb));
  const pkRaw = hizirFmtPrice(r.potansiyel_kar, pb);
  const pk = esc(pkRaw);
  const nm =
    r.net_marj_yuzde != null && Number.isFinite(Number(r.net_marj_yuzde))
      ? esc(`${Number(r.net_marj_yuzde).toFixed(1)}%`)
      : "—";
  const dt = esc(String(r.tarih || "").slice(0, 19).replace("T", " "));
  const clsCheap = hizirMpClass(cheapPlRaw);
  const clsExp = hizirMpClass(expPlRaw);
  const iniC = esc(hizirMpInitials(cheapPlRaw));
  const iniE = esc(hizirMpInitials(expPlRaw));
  const kid = esc(String(r.kart_id || ""));
  const satRaw = String(r.satinal_url || "").trim();
  const satDis = satRaw ? "" : "disabled";
  const pasDis = kid ? "" : "disabled";
  return `<article class="hizir-vitrin-card hizir-vitrin-card--arb" role="listitem">
  <div class="hizir-vitrin-card__media">
    ${mediaInner}
  </div>
  <div class="hizir-vitrin-card__body">
    <header class="hizir-vitrin-card__head">
      <span class="hizir-vitrin-card__bolge">${bolge}</span>
      <h4 class="hizir-vitrin-card__title">${title}</h4>
    </header>
    <div class="hizir-vitrin-cmp">
      <div class="hizir-vitrin-cmp__row hizir-vitrin-cmp__row--kaynak">
        <span class="${clsCheap}" title="${cheapPl}">${iniC}</span>
        <div class="hizir-vitrin-cmp__txt">
          <span class="hizir-vitrin-cmp__label">Kaynak · ${cheapPl}</span>
          <span class="hizir-vitrin-cmp__name">${cheapName}</span>
          <span class="hizir-vitrin-cmp__price hizir-vitrin-cmp__price--low">${kf}</span>
        </div>
      </div>
      <div class="hizir-vitrin-badge-wrap">
        <div class="hizir-vitrin-badge" aria-label="Tahmini net kâr">
          <span class="hizir-vitrin-badge__profit">+${pk}</span>
          <span class="hizir-vitrin-badge__pct">${nm}</span>
        </div>
      </div>
      <div class="hizir-vitrin-cmp__row hizir-vitrin-cmp__row--hedef">
        <span class="${clsExp}" title="${expPl}">${iniE}</span>
        <div class="hizir-vitrin-cmp__txt">
          <span class="hizir-vitrin-cmp__label">Hedef · ${expPl}</span>
          <span class="hizir-vitrin-cmp__name">${expName}</span>
          <span class="hizir-vitrin-cmp__price">${hf}</span>
        </div>
      </div>
    </div>
    <footer class="hizir-vitrin-card__foot hizir-vitrin-card__foot--arb">
      <span class="hizir-vitrin-card__dt">${dt}</span>
      <div class="hizir-vitrin-card__actions">
        <button type="button" class="hizir-vitrin-btn hizir-vitrin-btn--buy" data-hizir="satinal" data-url="${escAttr(satRaw)}" ${satDis}>AVLA / SATIN AL</button>
        <button type="button" class="hizir-vitrin-btn hizir-vitrin-btn--skip" data-hizir="pas" data-kart-id="${kid}" ${pasDis}>PAS GEÇ</button>
      </div>
    </footer>
  </div>
</article>`;
}

function hizirRenderDealVitrin(r) {
  const rawImg = String(r.gorsel_url || "").trim();
  const phIcon = `<span class="hizir-ph-glyph" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.4"/><path d="M20.5 16.5l-4.2-4.2-3.3 3.2-2.8-2.8-5.2 5.2"/></svg></span>`;
  const skel = `<div class="hizir-img-skel" aria-hidden="true"><span class="hizir-img-spin"></span></div>`;
  const mediaInner = rawImg
    ? `<div class="hizir-vitrin-card__img-wrap">${skel}<img class="hizir-vitrin-card__img hizir-vitrin-card__img--contain" src="${esc(rawImg)}" alt="" loading="lazy" width="88" height="88" decoding="async" referrerpolicy="no-referrer" /></div>`
    : `<div class="hizir-vitrin-card__img-wrap"><div class="hizir-vitrin-card__img hizir-vitrin-card__img--ph" role="img" aria-label="Ürün görseli">${phIcon}</div></div>`;
  const title = esc(String(r.urun_adi || "Ürün"));
  const bolge = esc(String(r.bolge || ""));
  const pb = String(r.para_birimi || "TRY").toUpperCase();
  const plRaw = String(r.platform || "");
  const pl = esc(plRaw);
  const price = esc(hizirFmtPrice(r.kaynak_fiyat, pb));
  const ozet = esc(String(r.ozet_metin || "").slice(0, 220));
  const cls = hizirMpClass(plRaw);
  const ini = esc(hizirMpInitials(plRaw));
  return `<article class="hizir-vitrin-card hizir-vitrin-card--deal" role="listitem">
    <div class="hizir-vitrin-card__media hizir-vitrin-card__media--sm">
      ${mediaInner}
    </div>
    <div class="hizir-vitrin-card__body">
      <span class="hizir-vitrin-card__bolge">${bolge}</span>
      <div class="hizir-vitrin-deal-row">
        <span class="${cls}" title="${pl}">${ini}</span>
        <div>
          <h4 class="hizir-vitrin-card__title hizir-vitrin-card__title--sm">${title}</h4>
          <p class="hizir-vitrin-deal__price">${price}</p>
        </div>
      </div>
      <p class="hizir-vitrin-deal__hint">${ozet}</p>
    </div>
  </article>`;
}

/** Search & Compare — Fiyat Dedektifi vitrin kartı (pazar yeri, kargo notu, AVLA). */
function hizirRenderFiyatListesiVitrin(r) {
  const rawImg = String(r.gorsel_url || "").trim();
  const phIcon = `<span class="hizir-ph-glyph" aria-hidden="true"><svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="8.5" cy="10" r="1.4"/><path d="M20.5 16.5l-4.2-4.2-3.3 3.2-2.8-2.8-5.2 5.2"/></svg></span>`;
  const skel = `<div class="hizir-img-skel" aria-hidden="true"><span class="hizir-img-spin"></span></div>`;
  const mediaInner = rawImg
    ? `<div class="hizir-vitrin-card__img-wrap">${skel}<img class="hizir-vitrin-card__img hizir-vitrin-card__img--contain" src="${esc(rawImg)}" alt="" loading="lazy" width="88" height="88" decoding="async" referrerpolicy="no-referrer" /></div>`
    : `<div class="hizir-vitrin-card__img-wrap"><div class="hizir-vitrin-card__img hizir-vitrin-card__img--ph" role="img" aria-label="Ürün görseli">${phIcon}</div></div>`;
  const title = esc(String(r.urun_adi || "Ürün"));
  const bolge = esc(String(r.bolge || ""));
  const plRaw = String(r.pazar_yeri || r.platform || "");
  const pl = esc(plRaw);
  const pb = String(r.para_birimi || "TRY").toUpperCase();
  const price = esc(hizirFmtPrice(r.kaynak_fiyat, pb));
  const kargo = esc(String(r.kargo_notu || "").slice(0, 180));
  const grp = String(r.grup_etiketi || "").trim();
  const grpHdr =
    r.yeni_grup && grp
      ? `<div class="hizir-vitrin-grup-hdr" role="separator" aria-label="Grup"><span>${esc(grp)}</span></div>`
      : "";
  const lider = r.lider_fiyat
    ? `<span class="hizir-vitrin-badge hizir-vitrin-badge--lider">LİDER FİYAT</span>`
    : "";
  const cls = hizirMpClass(plRaw);
  const ini = esc(hizirMpInitials(plRaw));
  const kid = esc(String(r.kart_id || ""));
  const satRaw = String(r.satinal_url || "").trim();
  const satDis = satRaw ? "" : "disabled";
  const pasDis = kid ? "" : "disabled";
  const dt = esc(String(r.tarih || "").slice(0, 19).replace("T", " "));
  return `${grpHdr}<article class="hizir-vitrin-card hizir-vitrin-card--cmp" role="listitem">
    <div class="hizir-vitrin-card__media hizir-vitrin-card__media--sm">${mediaInner}</div>
    <div class="hizir-vitrin-card__body">
      <div class="hizir-vitrin-cmp__rowbar">
        <span class="${cls}" title="${pl}">${ini}</span>
        ${lider}
        <span class="hizir-vitrin-card__bolge hizir-vitrin-card__bolge--tr">${bolge}</span>
      </div>
      <h4 class="hizir-vitrin-card__title hizir-vitrin-card__title--sm">${title}</h4>
      <p class="hizir-vitrin-cmp__plprice"><strong>${pl}</strong> · <span class="hizir-vitrin-deal__price">${price}</span></p>
      <p class="hizir-vitrin-deal__hint">${kargo}</p>
      <footer class="hizir-vitrin-card__foot hizir-vitrin-card__foot--arb">
        <span class="hizir-vitrin-card__dt">${dt}</span>
        <div class="hizir-vitrin-card__actions">
          <button type="button" class="hizir-vitrin-btn hizir-vitrin-btn--buy" data-hizir="satinal" data-url="${escAttr(satRaw)}" ${satDis}>AVLA</button>
          <button type="button" class="hizir-vitrin-btn hizir-vitrin-btn--skip" data-hizir="pas" data-kart-id="${kid}" ${pasDis}>PAS GEÇ</button>
        </div>
      </footer>
    </div>
  </article>`;
}

/** pazar_keşif girdisinden arama metnini çıkarır (tarama geçmişi menüsü). */
function hizirExtractPazarQuery(g) {
  if (!g || g.tip !== "pazar_keşif") return "";
    const inner = g.veri && g.veri.data && g.veri.data.result;
    if (inner && inner.query != null && String(inner.query).trim()) {
      let q = String(inner.query).trim();
      q = q.replace(/^pazar\s+yerini\s+tara\s*:?\s*/i, "").trim();
      return q || String(inner.query).trim();
    }
  const k = String(g.anahtar || "");
  const idx = k.indexOf(":");
  if (idx >= 0) {
    const tail = k.slice(idx + 1).trim().replace(/_/g, " ");
    if (tail) return tail;
  }
  return "";
}

const HIZIR_PAZAR_CH_STORAGE = "ruzgar:hizir:pazar-kanallari";

function hizirCollectPazarCheckboxIds() {
  const panel = el.hizirPazarlarPanel || document.getElementById("hizir-pazarlar-panel");
  if (!panel) return null;
  const out = [];
  panel.querySelectorAll("input[data-hizir-ch]").forEach((inp) => {
    if (inp.checked) {
      const id = String(inp.getAttribute("data-hizir-ch") || "").trim();
      if (id) out.push(id);
    }
  });
  return out.length ? out : null;
}

function hizirPersistPazarChecks() {
  try {
    localStorage.setItem(HIZIR_PAZAR_CH_STORAGE, JSON.stringify(hizirCollectPazarCheckboxIds()));
  } catch (_) {}
}

function hizirLoadPazarChecksFromStorage() {
  const panel = el.hizirPazarlarPanel;
  if (!panel) return;
  let raw = null;
  try {
    raw = localStorage.getItem(HIZIR_PAZAR_CH_STORAGE);
  } catch (_) {}
  if (!raw) return;
  let arr = null;
  try {
    arr = JSON.parse(raw);
  } catch (_) {
    return;
  }
  if (!Array.isArray(arr) || !arr.length) return;
  const want = new Set(arr);
  panel.querySelectorAll("input[data-hizir-ch]").forEach((inp) => {
    const id = String(inp.getAttribute("data-hizir-ch") || "");
    inp.checked = want.has(id);
  });
}

function hizirSetAllPazarChecks(on) {
  const panel = el.hizirPazarlarPanel;
  if (!panel) return;
  panel.querySelectorAll("input[data-hizir-ch]").forEach((inp) => {
    inp.checked = !!on;
  });
  hizirPersistPazarChecks();
}

function hizirRenderAktifKanallarStripFromGirdiler(girdiler) {
  const wrap = el.hizirAktifKanallar;
  if (!wrap) return;
  const scans = Array.isArray(girdiler) ? girdiler.filter((x) => x && x.tip === "pazar_keşif") : [];
  const last = scans.length ? scans[scans.length - 1] : null;
  const inner = last && last.veri && last.veri.data && last.veri.data.result;
  const meta = inner && Array.isArray(inner.aktif_kanallar) ? inner.aktif_kanallar : [];
  if (!meta.length) {
    wrap.innerHTML = "";
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const chips = meta
    .map((x) => {
      const lab = esc(String((x && x.label) || (x && x.id) || ""));
      const cls = hizirMpClass(String((x && x.label) || ""));
      const ini = esc(hizirMpInitials(String((x && x.label) || (x && x.id) || "")));
      return `<span class="hizir-ak-chip ${cls}" title="${lab}"><span class="hizir-ak-chip__ini" aria-hidden="true">${ini}</span><span class="hizir-ak-chip__txt">${lab}</span></span>`;
    })
    .join("");
  wrap.innerHTML = `<span class="hizir-ak-lead">Aktif kanallar</span>${chips}`;
}

/**
 * HIZIR — merkezi bellek (GET) + pazar taraması (POST); desktop_server ile uyumlu.
 * Tek giriş noktası: wire(), refreshPanel(), pazarTara().
 */
const HIZIR_MODU = {
  _wired: false,
  _cardDeckBound: false,
  _historyMenuWired: false,
  _pazarlarWired: false,
  _scanPopoverHtml: "",
  _pazarTaraDetail: "",
  _lastScanShort: "",
  /** Son render edilen girdiler (tarama geçmişi menüsü için). */
  _lastGirdilerSnapshot: [],
  /** Yeniden → eskiye; öğe: { girdi } */
  _pazarHistory: [],

  merkeziBellekUrl() {
    return `${API}/api/merkezi-bellek?t=${Date.now()}`;
  },

  pazarTaraUrl() {
    return `${API}/api/hizir/pazar-tara`;
  },

  firsatKaldirUrl() {
    return `${API}/api/hizir/firsat-kaldir`;
  },

  lastPazarScanSummary(girdiler) {
    const arr = Array.isArray(girdiler) ? girdiler.slice().reverse() : [];
    const g = arr.find((x) => x && x.tip === "pazar_keşif");
    if (!g || !g.veri || !g.veri.data) {
      return { shortLine: "", popoverHtml: "", errorCount: 0 };
    }
    const inner = g.veri.data.result;
    if (!inner || typeof inner !== "object") {
      return { shortLine: "", popoverHtml: "", errorCount: 0 };
    }
    const mode =
      inner.live === true ? "Canlı motor" : inner.data_mode === "mock" ? "Geliştirici" : "Veri";
    const scanM = inner.scan_mode === "fiyat_dedektifi" ? " · Fiyat Dedektifi" : "";
    const er = inner.errors && typeof inner.errors === "object" ? inner.errors : {};
    const keys = Object.keys(er);
    const errLines = keys.map((k) => `<div class="hizir-pop-err"><strong>${esc(k)}</strong><p>${esc(String(er[k]))}</p></div>`);
    const errCount = keys.length;
    const shortLine =
      errCount > 0
        ? `${mode}${scanM} · ${errCount} kanal notu`
        : `${mode}${scanM} · tarama temiz`;
    const q = inner.query != null ? esc(String(inner.query)) : "—";
    const popoverHtml = [
      `<p class="hizir-pop-lead">Son pazar keşfi · <code>${q}</code></p>`,
      errLines.length ? errLines.join("") : "<p>Şu an kayıtlı hata satırı yok.</p>",
    ].join("");
    return { shortLine, popoverHtml, errorCount: errCount };
  },

  _closeScanPopover() {
    const pop = document.getElementById("hizir-scan-popover");
    const btn = document.getElementById("hizir-scan-info-btn");
    if (pop) pop.hidden = true;
    if (btn) btn.setAttribute("aria-expanded", "false");
  },

  _toggleScanPopover() {
    const pop = document.getElementById("hizir-scan-popover");
    const btn = document.getElementById("hizir-scan-info-btn");
    if (!pop || !btn) return;
    const open = pop.hidden;
    pop.hidden = !open;
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      const parts = [this._scanPopoverHtml, this._pazarTaraDetail].filter(Boolean);
      const body =
        parts.length > 0
          ? parts.join('<hr class="hizir-pop-hr" />')
          : '<p class="hizir-pop-lead">Henüz kayıtlı tarama özeti yok. <strong>Tara</strong> veya <strong>Yenile</strong> deneyin.</p>';
      pop.innerHTML = `<div class="hizir-scan-popover__inner">${body}</div>`;
    }
  },

  _scanHistoryTitle(g) {
    const when = g && g.tarih ? String(g.tarih).slice(0, 16).replace("T", " ") : "—";
    const q = hizirExtractPazarQuery(g) || "Sorgu yok";
    return `${when} · ${q}`;
  },

  _buildScanHistoryMenu(girdiler) {
    const menu = el.hizirScanHistoryMenu;
    const trig = el.btnHizirScanHistory;
    if (!menu) return;
    const arr = Array.isArray(girdiler) ? girdiler : [];
    const scans = arr.filter((x) => x && x.tip === "pazar_keşif");
    const last20 = scans.slice(-20).reverse();
    this._pazarHistory = last20.map((g) => ({ girdi: g }));
    if (!last20.length) {
      menu.innerHTML = `<div class="hizir-wb-dd-empty" role="presentation">Henüz kayıtlı tarama yok</div>`;
    } else {
      menu.innerHTML = last20
        .map((g, i) => {
          const title = this._scanHistoryTitle(g);
          return `<button type="button" class="hizir-wb-dd-item" role="menuitem" data-hizir-scan-idx="${i}">${esc(title)}</button>`;
        })
        .join("");
    }
    if (trig) {
      if (!last20.length) trig.setAttribute("data-empty", "true");
      else trig.removeAttribute("data-empty");
    }
  },

  _closeScanHistoryMenu() {
    const menu = el.hizirScanHistoryMenu;
    const trig = el.btnHizirScanHistory;
    if (menu) menu.hidden = true;
    if (trig) trig.setAttribute("aria-expanded", "false");
  },

  _toggleScanHistoryMenu() {
    const menu = el.hizirScanHistoryMenu;
    const trig = el.btnHizirScanHistory;
    if (!menu || !trig) return;
    const open = menu.hidden;
    menu.hidden = !open;
    trig.setAttribute("aria-expanded", open ? "true" : "false");
  },

  _applyScanHistoryIndex(i) {
    const row = Array.isArray(this._pazarHistory) ? this._pazarHistory[i] : null;
    if (!row || !row.girdi) return;
    const g = row.girdi;
    const q = hizirExtractPazarQuery(g);
    if (el.hizirTaraQuery) el.hizirTaraQuery.value = q;
    const scan = this.lastPazarScanSummary([g]);
    this._scanPopoverHtml = scan.popoverHtml || "";
    this._lastScanShort = scan.shortLine || "";
    this._pazarTaraDetail = `<div class="hizir-pop-block"><strong>Geçmiş tarama</strong><p>Sorgu: <code>${esc(q || "(boş)")}</code></p></div>`;
    this._closeScanHistoryMenu();
    void this.pazarTara();
  },

  _wireScanHistoryMenuOnce() {
    if (this._historyMenuWired) return;
    this._historyMenuWired = true;
    const trig = el.btnHizirScanHistory;
    const menu = el.hizirScanHistoryMenu;
    if (trig) {
      trig.addEventListener("click", (ev) => {
        ev.stopPropagation();
        this._buildScanHistoryMenu(this._lastGirdilerSnapshot || []);
        this._toggleScanHistoryMenu();
      });
    }
    if (menu) {
      menu.addEventListener("click", (ev) => {
        const btn = ev.target && ev.target.closest ? ev.target.closest("[data-hizir-scan-idx]") : null;
        if (!btn || !menu.contains(btn)) return;
        ev.stopPropagation();
        const idx = Number(btn.getAttribute("data-hizir-scan-idx"));
        if (!Number.isFinite(idx)) return;
        this._applyScanHistoryIndex(idx);
      });
    }
    document.addEventListener("click", () => {
      const m = el.hizirScanHistoryMenu;
      if (m && !m.hidden) this._closeScanHistoryMenu();
    });
  },

  renderMerkeziBellek(root) {
    const oldStrip = document.getElementById("hizir-live-strip");
    if (oldStrip) oldStrip.remove();

    const kat = root.kategoriler || {};
    const ht = kat.hizir_ticaret || {};
    const rows = Array.isArray(ht.firsatlar) ? ht.firsatlar : [];
    const gen = kat.genel_onbellek || {};
    const girdiler = Array.isArray(gen.girdiler) ? gen.girdiler : [];
    this._lastGirdilerSnapshot = girdiler;
    hizirRenderAktifKanallarStripFromGirdiler(girdiler);
    if (el.hizirFirsatlarWrap) {
      if (!rows.length) {
        el.hizirFirsatlarWrap.innerHTML =
          '<div class="hizir-firsatlar-hint faz7-empty-hint">Arama yapın veya <strong>Yenile</strong> ile vitrini güncelleyin.</div>';
      } else {
        const sorted = rows.slice().sort((a, b) => {
          const rank = (r) => {
            const t = String(r.tur || "");
            if (t === "FIYAT_LISTESI") return 4;
            if (t === "ARBITRAJ") return 3;
            if (r.otomatik) return 2;
            return 1;
          };
          const d = rank(b) - rank(a);
          if (d !== 0) return d;
          const ta = String(a.tur || "");
          const tb = String(b.tur || "");
          if (ta === "FIYAT_LISTESI" && tb === "FIYAT_LISTESI") {
            const sa = Number(a.vitrin_sira);
            const sb = Number(b.vitrin_sira);
            if (Number.isFinite(sa) && Number.isFinite(sb) && sa !== sb) return sa - sb;
            const ea = Number(a.potansiyel_kar);
            const eb = Number(b.potansiyel_kar);
            if (Number.isFinite(ea) && Number.isFinite(eb) && ea !== eb) return ea - eb;
            return 0;
          }
          const pa = Number(a.potansiyel_kar);
          const pb = Number(b.potansiyel_kar);
          if (Number.isFinite(pa) && Number.isFinite(pb) && pa !== pb) return pb - pa;
          return 0;
        });
        const slice = sorted.slice(0, 80);
        const html = slice
          .map((r) => {
            const tur = String(r.tur || "").trim();
            if (tur === "FIYAT_LISTESI") return hizirRenderFiyatListesiVitrin(r);
            if (tur === "ARBITRAJ") return hizirRenderArbitrajVitrin(r);
            const otm = Boolean(r.otomatik);
            if (otm && r.gorsel_url) return hizirRenderDealVitrin(r);
            const ozet = String(r.ozet_metin || "").trim();
            const mod = otm ? "hizir-vitrin-card hizir-vitrin-card--plain" : "hizir-vitrin-card hizir-vitrin-card--manual";
            const metaDt = esc(String(r.tarih || "").slice(0, 19).replace("T", " "));
            const bolge = r.bolge != null ? esc(String(r.bolge)) : "";
            const body = ozet
              ? `<p class="hizir-vitrin-plain__text">${esc(ozet)}</p>`
              : `<p class="hizir-vitrin-plain__text">${esc(String(r.urun_adi || ""))}</p>`;
            return `<article class="${mod}" role="listitem">${body}<footer class="hizir-vitrin-card__foot">${bolge ? `${bolge} · ` : ""}${metaDt}</footer></article>`;
          })
          .join("");
        el.hizirFirsatlarWrap.innerHTML = `<div class="hizir-firsatlar-grid hizir-firsatlar-grid--vitrin" role="list">${html}</div>`;
        wireHizirImageErrorFallback(el.hizirFirsatlarWrap);
        wireHizirImagePlaceholders(el.hizirFirsatlarWrap);
      }
      /* UI Fix — HIZIR: yenileme sonrası vitrin kabının boyutu sıfırlanmasın; liste üstten görünsün */
      try {
        const sc = el.hizirFirsatlarScroll || document.getElementById("hizir-firsatlar-scroll");
        if (sc) sc.scrollTop = 0;
      } catch (_) {
        /* ignore */
      }
    }
    if (el.hizirOnbellekWrap) {
      const slice = girdiler.slice(-20);
      try {
        window.__ruzgarHizirOnbellek = slice;
      } catch (_) {
        /* ignore */
      }
      const last = slice.length ? slice[slice.length - 1] : null;
      const tip = last && last.tip ? esc(String(last.tip)) : "—";
      const when =
        last && last.tarih ? esc(String(last.tarih).slice(0, 19).replace("T", " ")) : "—";
      el.hizirOnbellekWrap.innerHTML = `<div class="hizir-cache-vitrin">
        <p class="hizir-cache-vitrin__sub">Son kayıt: <em>${tip}</em> · ${when}</p>
        <p class="hizir-cache-vitrin__note">Özet; tam veri arka planda işlenir.</p>
      </div>`;
    }
    const scan = this.lastPazarScanSummary(girdiler);
    this._scanPopoverHtml = scan.popoverHtml || "";
    this._lastScanShort = scan.shortLine || "";
    this._buildScanHistoryMenu(girdiler);
    this._closeScanPopover();
  },

  async refreshPanel() {
    if (!el.pageHizir) return;
    if (el.hizirInlineStatus) {
      el.hizirInlineStatus.textContent = "Yükleniyor…";
      el.hizirInlineStatus.removeAttribute("title");
    }
    if (currentMode === "hizir") setHizirWorkbenchServerPillUnknown();
    try {
      const url = this.merkeziBellekUrl();
      const res = await fetch(url);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok) {
        const d = j.detail;
        const base = typeof d === "string" ? d : `HTTP ${res.status}`;
        if (res.status === 404) {
          throw new Error(
            `${base} — ${url} (Kök: ${API}). Kökte sondaki /api varsa kaldırın; ilim-assistant içinde güncel desktop_server çalıştırın.`
          );
        }
        throw new Error(typeof d === "string" ? d : `HTTP ${res.status}`);
      }
      this.renderMerkeziBellek(j.data || {});
      const rawPath = String(j.path || "");
      if (el.hizirInlineStatus) {
        const v = esc(String(j.version ?? ""));
        el.hizirInlineStatus.textContent = `Bellek hazır · sürüm ${v}`;
        if (rawPath) el.hizirInlineStatus.title = rawPath;
        else el.hizirInlineStatus.removeAttribute("title");
      }
      if (el.hizirInlineStatus && this._lastScanShort) {
        el.hizirInlineStatus.textContent += ` · ${this._lastScanShort}`;
      }
      try {
        const kat = (j.data && j.data.kategoriler) || {};
        const gen = kat.genel_onbellek || {};
        const girdiler = Array.isArray(gen.girdiler) ? gen.girdiler : [];
        const pz = [...girdiler].reverse().find((x) => x && x.tip === "pazar_keşif");
        const inner = pz && pz.veri && pz.veri.data && pz.veri.data.result;
        if (el.hizirInlineStatus && inner && inner.mock_marketplace) {
          el.hizirInlineStatus.textContent += " · Geliştirici mock (HIZIR_MOCK_MARKETPLACE=0 önerilir)";
        }
      } catch (_) {
        /* ignore */
      }
      if (currentMode === "hizir") {
        setHizirWorkbenchServerPill(true, rawPath || el.api?.title || "");
      }
    } catch (e) {
      const msg = e && e.message ? String(e.message) : String(e);
      this._pazarTaraDetail = `<div class="hizir-pop-err"><strong>Yükleme</strong><p>${esc(msg)}</p></div>`;
      this._lastScanShort = "";
      if (el.hizirInlineStatus) {
        el.hizirInlineStatus.textContent = "Bellek yüklenemedi";
        el.hizirInlineStatus.title = msg.length > 200 ? msg.slice(0, 200) : msg;
      }
      if (currentMode === "hizir") setHizirWorkbenchServerPill(false, msg);
    }
  },

  async pazarTara() {
    const q = el.hizirTaraQuery ? String(el.hizirTaraQuery.value || "").trim() : "";
    if (el.hizirInlineStatus) {
      el.hizirInlineStatus.textContent = "Taranıyor…";
      el.hizirInlineStatus.removeAttribute("title");
    }
    try {
      const res = await fetch(this.pazarTaraUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, channels: hizirCollectPazarCheckboxIds() }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok) {
        const d = j.detail;
        throw new Error(typeof d === "string" ? d : `HTTP ${res.status}`);
      }
      const ch = j.tool_context_chars || 0;
      this._pazarTaraDetail = `<div class="hizir-pop-block"><strong>Son tarama</strong><p>Araç bağlamı <code>${esc(String(ch))}</code> karakter · sorgu: <code>${esc(q || "(boş)")}</code></p></div>`;
      if (el.hizirInlineStatus) {
        el.hizirInlineStatus.textContent = "Tarama tamamlandı";
        el.hizirInlineStatus.removeAttribute("title");
      }
      await this.refreshPanel();
    } catch (e) {
      const msg = e && e.message ? String(e.message) : String(e);
      this._pazarTaraDetail = `<div class="hizir-pop-err"><strong>Tarama hatası</strong><p>${esc(msg)}</p></div>`;
      if (el.hizirInlineStatus) {
        el.hizirInlineStatus.textContent = "Tarama başarısız";
        el.hizirInlineStatus.title = msg;
      }
    }
  },

  _sayfaTemizleUiOnly() {
    if (el.hizirFirsatlarWrap) {
      el.hizirFirsatlarWrap.innerHTML =
        '<div class="hizir-firsatlar-hint faz7-empty-hint">Vitrin temiz. <strong>Yenile</strong> veya <strong>Tara</strong> ile merkezi bellekten tekrar yükleyebilirsiniz.</div>';
    }
    this._lastGirdilerSnapshot = [];
    this._pazarHistory = [];
    this._scanPopoverHtml = "";
    this._pazarTaraDetail = "";
    this._lastScanShort = "";
  },

  async sayfaTemizle() {
    this._closeScanHistoryMenu();
    const btn = el.btnHizirSayfaTemizleWb;
    if (btn) btn.disabled = true;
    if (el.hizirInlineStatus) {
      el.hizirInlineStatus.textContent = "Merkezi bellek temizleniyor…";
    }
    try {
      const res = await fetch(`${API}/api/hizir/temizle`, { method: "POST" });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.ok) {
        const d = j.detail;
        throw new Error(typeof d === "string" ? d : `HTTP ${res.status}`);
      }
      this._sayfaTemizleUiOnly();
      if (el.hizirInlineStatus) {
        el.hizirInlineStatus.textContent = "Merkezi bellek vitrin temizlendi";
        el.hizirInlineStatus.removeAttribute("title");
      }
      setStatus("HIZIR vitrin temizlendi", "Rüzgar");
      await this.refreshPanel();
    } catch (e) {
      const msg = e && e.message ? String(e.message) : String(e);
      this._sayfaTemizleUiOnly();
      if (el.hizirInlineStatus) {
        el.hizirInlineStatus.textContent = "API hatası — ekran temizlendi";
        el.hizirInlineStatus.title = msg;
      }
      setStatus("HIZIR temizle: sunucu yanıt vermedi", "Rüzgar");
      flashRuzgarDurum(msg.slice(0, 100));
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  async hizliYenile() {
    await this.pazarTara();
  },

  async pasGecKart(kartId) {
    const kid = String(kartId || "").trim();
    if (!kid) return;
    try {
      const res = await fetch(this.firsatKaldirUrl(), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kart_id: kid }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) {
        const d = j.detail;
        throw new Error(typeof d === "string" ? d : `HTTP ${res.status}`);
      }
      await this.refreshPanel();
    } catch (e) {
      const msg = e && e.message ? String(e.message) : String(e);
      this._pazarTaraDetail = `<div class="hizir-pop-err"><strong>PAS GEÇ</strong><p>${esc(msg)}</p></div>`;
    }
  },

  _wireCardActionsOnce() {
    if (this._cardDeckBound) return;
    this._cardDeckBound = true;
    const deck = el.hizirFirsatlarWrap;
    if (!deck) return;
    deck.addEventListener("click", (ev) => {
      const t = ev.target;
      const btn = t && t.closest ? t.closest("[data-hizir]") : null;
      if (!btn || !deck.contains(btn)) return;
      const act = btn.getAttribute("data-hizir");
      if (act === "satinal") {
        const u = btn.getAttribute("data-url");
        if (u) void openHizirProductUrl(u);
        return;
      }
      if (act === "pas") {
        const id = btn.getAttribute("data-kart-id");
        if (id) void this.pasGecKart(id);
      }
    });
  },

  shouldRefreshAfterChat(userText) {
    const utLow = String(userText || "").toLowerCase();
    return (
      currentMode === "hizir" ||
      /\b(pazar\s+yerini|pazarı\s+tara|pazar\s+tara|hava\s+durumuna\s+bak|hemen\s+şimdi)\b/i.test(
        utLow
      ) ||
      utLow.includes("trendyol") ||
      utLow.includes("amazon") ||
      /\bavla\b/i.test(utLow)
    );
  },

  bootStatusIfEmpty() {
    if (!el.hizirInlineStatus) return;
    const t = (el.hizirInlineStatus.textContent || "").trim();
    if (!t) {
      el.hizirInlineStatus.textContent = "Yenile · Tara";
      el.hizirInlineStatus.removeAttribute("title");
    }
  },

  wire() {
    if (this._wired) return;
    this._wired = true;
    this.bootStatusIfEmpty();
    if (el.btnHizirRefresh) {
      el.btnHizirRefresh.addEventListener("click", () => {
        void this.refreshPanel();
      });
    }
    if (el.btnHizirTara) {
      el.btnHizirTara.addEventListener("click", () => {
        void this.pazarTara();
      });
    }
    if (el.hizirTaraQuery) {
      el.hizirTaraQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
          e.preventDefault();
          void this.pazarTara();
        }
      });
    }
    if (el.btnOpenHizirPanel) {
      el.btnOpenHizirPanel.addEventListener("click", () => {
        switchMode("hizir");
        void this.refreshPanel();
      });
    }
    const infoBtn = document.getElementById("hizir-scan-info-btn");
    const pop = document.getElementById("hizir-scan-popover");
    if (infoBtn) {
      infoBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        this._toggleScanPopover();
      });
    }
    if (pop) {
      pop.addEventListener("click", (ev) => ev.stopPropagation());
    }
    document.addEventListener("click", (ev) => {
      const btn = document.getElementById("hizir-scan-info-btn");
      const p = document.getElementById("hizir-scan-popover");
      if (!p || p.hidden) return;
      if (btn && (ev.target === btn || btn.contains(ev.target))) return;
      if (ev.target === p || p.contains(ev.target)) return;
      this._closeScanPopover();
    });
    if (el.btnHizirSayfaTemizleWb) {
      el.btnHizirSayfaTemizleWb.addEventListener("click", () => {
        void this.sayfaTemizle();
      });
    }
    if (el.btnHizirHizliYenileWb) {
      el.btnHizirHizliYenileWb.addEventListener("click", () => {
        void this.hizliYenile();
      });
    }
    this._wireScanHistoryMenuOnce();
    this._wireCardActionsOnce();
    this._wirePazarlarOnce();
  },

  _closePazarlarPanel() {
    const p = el.hizirPazarlarPanel;
    const b = el.btnHizirPazarlar;
    if (p) p.hidden = true;
    if (b) b.setAttribute("aria-expanded", "false");
  },

  _togglePazarlarPanel() {
    const p = el.hizirPazarlarPanel;
    const b = el.btnHizirPazarlar;
    if (!p || !b) return;
    const open = !!p.hidden;
    p.hidden = !open;
    b.setAttribute("aria-expanded", open ? "true" : "false");
  },

  _wirePazarlarOnce() {
    if (this._pazarlarWired) return;
    this._pazarlarWired = true;
    hizirLoadPazarChecksFromStorage();
    if (el.btnHizirPazarlar && el.hizirPazarlarPanel) {
      el.btnHizirPazarlar.addEventListener("click", (ev) => {
        ev.stopPropagation();
        this._togglePazarlarPanel();
      });
    }
    const panel = el.hizirPazarlarPanel;
    if (panel) {
      panel.addEventListener("click", (ev) => ev.stopPropagation());
      const allB = panel.querySelector("[data-hizir-ch-all]");
      const noneB = panel.querySelector("[data-hizir-ch-none]");
      if (allB)
        allB.addEventListener("click", (e) => {
          e.stopPropagation();
          hizirSetAllPazarChecks(true);
        });
      if (noneB)
        noneB.addEventListener("click", (e) => {
          e.stopPropagation();
          hizirSetAllPazarChecks(false);
        });
      panel.querySelectorAll("input[data-hizir-ch]").forEach((inp) => {
        inp.addEventListener("change", () => hizirPersistPazarChecks());
      });
    }
    document.addEventListener("click", (ev) => {
      const wrap = el.hizirPazarlarWrap;
      if (wrap && (ev.target === wrap || wrap.contains(ev.target))) return;
      this._closePazarlarPanel();
    });
  },
};

async function refreshHizirOperasyonPanel() {
  return HIZIR_MODU.refreshPanel();
}

/** Aktif motor sayfası görünür olduktan sonra kabuk + data-motor senkronu (video/tercüme/mimar). */
function syncActiveMotorShell() {
  const wb = getWorkbenchMode();
  if (window.RuzgarTercumeAtolye?.syncTercumeLayout) {
    window.RuzgarTercumeAtolye.syncTercumeLayout(wb === "tercume");
  }
  if (window.RuzgarMimarAtolye?.syncMimarLayout) {
    window.RuzgarMimarAtolye.syncMimarLayout(wb === "mimar" || wb === "okuma");
  }
  if (window.RuzgarVideoAtolye?.syncVideoLayout) {
    window.RuzgarVideoAtolye.syncVideoLayout(wb === "video");
  }
  /* Electron BrowserView sinema — video sayfası gizlense de pencerede kalır; motor değişince kapat */
  if (wb !== "video") {
    clearYoutubeEmbedPreview();
  }
}

function updateDynamicWorkbench() {
  const wb = getWorkbenchMode();
  const pages = [
    el.pageGenel,
    el.pageHafiza,
    el.pageHizir,
    el.pageMimar,
    el.pageTercume,
    el.pageVideo,
    el.pageProgramlama,
    el.pageSes,
  ];
  /* hidden + display:flex çakışması / önbellek: yalnızca aktif sayfa görünsün */
  pages.forEach((p) => {
    if (!p) return;
    p.hidden = true;
    p.style.display = "none";
  });
  const map = {
    genel: el.pageGenel,
    hafiza: el.pageHafiza,
    hizir: el.pageHizir,
    mimar: el.pageMimar,
    okuma: el.pageMimar,
    tercume: el.pageTercume,
    video: el.pageVideo,
    programlama: el.pageProgramlama,
    ses: el.pageSes,
  };
  const active = map[wb] || el.pageGenel;
  if (active) {
    active.hidden = false;
    active.style.display = "";
  }
  if (wb === "hafiza") {
    setWorkbenchLayout("layout-split2");
  } else if (wb === "video") {
    if (el.dynamicWorkbench) {
      el.dynamicWorkbench.classList.remove("layout-split2", "layout-split4");
      el.dynamicWorkbench.classList.add("layout-full");
      document.body.classList.add("workbench-full");
    }
  } else if (el.dynamicWorkbench?.classList.contains("layout-split2")) {
    setWorkbenchLayout("layout-full");
  }
  if (el.dashboardStatus) {
    el.dashboardStatus.textContent =
      hubQuietMotor && currentMode === "genel"
        ? `Ana Motor · panel: ${MODE_LABELS[hubQuietMotor] || hubQuietMotor}`
        : `Aktif motor: ${MODE_LABELS[currentMode] || currentMode}`;
  }
  updateDashboardLastSpeech();
  if (wb === "hafiza") void loadHafizaJsonView();
  if (wb === "mimar" || wb === "okuma") {
    if (window.RuzgarMimarAtolye) window.RuzgarMimarAtolye.load();
  }
  if (wb === "tercume") void loadTercumeFileList();
  /* tercüme: tercume-atolye.js */
  if (wb === "ses") {
    void refreshSesSttHint();
    void refreshSesDubHint();
  }
  if (wb === "video") void refreshVideoEngineHint();
  if (wb === "programlama") {
    updateProgramlamaActiveFileLabel();
    void programlamaAtolyeRefreshRoot();
  }
  if (wb === "hizir") void refreshHizirOperasyonPanel();
  syncWorkbenchHizirToolbar();
  syncActiveMotorShell();
  relayoutAppShell();
  if (wb === "video") {
    requestAnimationFrame(() => {
      syncActiveMotorShell();
      relayoutAppShell();
      window.RuzgarVideoAtolye?.relayoutShell?.();
    });
  }
}

const LS_MOTORS_COMPACT = "ruzgarMotorsCompact";

function hideMotorHoverTip() {
  const tip = document.getElementById("motor-hover-tip");
  if (tip) tip.hidden = true;
}

function ensureMotorHoverTip() {
  let tip = document.getElementById("motor-hover-tip");
  if (!tip) {
    tip = document.createElement("div");
    tip.id = "motor-hover-tip";
    tip.className = "motor-hover-tip";
    tip.hidden = true;
    tip.setAttribute("role", "tooltip");
    document.body.appendChild(tip);
  }
  return tip;
}

function motorHoverLabel(btn) {
  const name = btn.querySelector(".motor-name")?.textContent?.trim() || "";
  const tag = btn.querySelector(".motor-tag")?.textContent?.trim() || "";
  return { name, tag };
}

function positionMotorHoverTip(btn, tip) {
  const r = btn.getBoundingClientRect();
  tip.style.left = `${Math.round(r.right + 10)}px`;
  tip.style.top = `${Math.round(r.top + r.height / 2)}px`;
  tip.style.transform = "translateY(-50%)";
}

function showMotorHoverTip(btn) {
  const { name, tag } = motorHoverLabel(btn);
  if (!name) return;
  const tip = ensureMotorHoverTip();
  tip.innerHTML = tag
    ? `${name}<span class="motor-hover-tip-sub">${tag}</span>`
    : name;
  positionMotorHoverTip(btn, tip);
  tip.hidden = false;
}

function wireMotorHoverTips() {
  document.querySelectorAll(".panel-motors .motor-item[data-mode]").forEach((btn) => {
    if (btn.dataset.motorTipWired === "1") return;
    btn.dataset.motorTipWired = "1";
    btn.addEventListener("mouseenter", () => {
      if (!document.body.classList.contains("ui-motors-compact")) return;
      showMotorHoverTip(btn);
    });
    btn.addEventListener("mousemove", () => {
      if (!document.body.classList.contains("ui-motors-compact")) return;
      const tip = document.getElementById("motor-hover-tip");
      if (tip && !tip.hidden) positionMotorHoverTip(btn, tip);
    });
    btn.addEventListener("mouseleave", hideMotorHoverTip);
    btn.addEventListener("blur", hideMotorHoverTip);
  });
}

function isMotorsCompact() {
  return document.body.classList.contains("ui-motors-compact");
}

function getMotorsShellWidthPx() {
  if (isMotorsCompact()) return 52;
  const st = window.RuzgarSplit?.loadState?.() || {};
  if (typeof st.motors === "number" && st.motors > 80) return st.motors;
  const raw = getComputedStyle(document.documentElement).getPropertyValue("--ruzgar-motors-w").trim();
  const n = parseFloat(raw);
  return Number.isFinite(n) && n > 80 ? n : 232;
}

/** Motor paneli daralt/genişlet ve mod değişiminde ızgarayı yeniden kur (display:contents kırılmasını önler). */
function relayoutAppShell() {
  const mode = String(currentMode || window.currentMode || "genel").trim().toLowerCase();
  const layout = document.querySelector(".layout.layout-v2");
  const center = document.getElementById("tercume-center-row");
  const pageVideo = document.getElementById("page-video");
  const videoOn = mode === "video" && pageVideo && !pageVideo.hidden;
  const mimarOn = mode === "mimar" || mode === "okuma";
  const tercumeOn = mode === "tercume";

  window.RuzgarSplit?.refresh?.();
  window.RuzgarSplit?._splits?.forEach((s) => s._reposition?.());

  const mw = getMotorsShellWidthPx();
  document.documentElement.style.setProperty("--ruzgar-motors-w", `${mw}px`);

  if (layout && (videoOn || mimarOn || tercumeOn)) {
    layout.style.display = "grid";
    layout.style.gridTemplateColumns = `${mw}px minmax(0, 1fr)`;
    if (tercumeOn) layout.style.gridTemplateRows = "46px minmax(0, 1fr)";
    else if (mimarOn) layout.style.gridTemplateRows = "38px minmax(0, 1fr)";
    else layout.style.gridTemplateRows = "minmax(0, 1fr)";
  } else if (layout) {
    layout.style.removeProperty("display");
    layout.style.removeProperty("grid-template-columns");
    layout.style.removeProperty("grid-template-rows");
  }

  if (center && (videoOn || mimarOn || tercumeOn)) {
    center.style.setProperty("display", "flex", "important");
    center.style.flexDirection = "row";
    center.style.gridColumn = videoOn || mimarOn || tercumeOn ? "2" : "";
    center.style.gridRow = tercumeOn || mimarOn ? "2" : videoOn ? "1" : "";
    center.style.minWidth = "0";
    center.style.minHeight = "0";
    center.style.overflow = "hidden";
  } else if (center) {
    center.style.removeProperty("display");
    center.style.removeProperty("flex-direction");
    center.style.removeProperty("min-width");
    center.style.removeProperty("min-height");
    center.style.removeProperty("overflow");
  }

  const motorsSplit = window.RuzgarSplit?._splits?.find((s) => s.key === "motors");
  if (motorsSplit && !isMotorsCompact()) {
    motorsSplit.applySize(motorsSplit.getSize());
  }

  if (videoOn) {
    document.body.dataset.motor = "video";
    document.body.classList.add("video-cinema-mode");
    center?.classList.add("video-cinema-center");
    window.RuzgarVideoAtolye?.relayoutShell?.();
  } else {
    document.body.classList.remove("video-motor-active", "video-cinema-mode");
    center?.classList.remove("video-cinema-center");
  }
}

function applyMotorsCompact(compact, opts) {
  const on = Boolean(compact);
  const persist = opts?.persist !== false;
  document.body.classList.toggle("ui-motors-compact", on);
  if (on) {
    document.documentElement.style.setProperty("--ruzgar-motors-w", "52px");
  } else {
    document.documentElement.style.setProperty("--ruzgar-motors-w", `${getMotorsShellWidthPx()}px`);
  }
  relayoutAppShell();
  requestAnimationFrame(() => {
    relayoutAppShell();
    if (String(currentMode || "").trim().toLowerCase() === "video") {
      window.RuzgarVideoAtolye?.relayoutShell?.();
    }
  });
  if (!on) hideMotorHoverTip();
  if (persist) {
    try {
      localStorage.setItem(LS_MOTORS_COMPACT, on ? "1" : "0");
    } catch (_) {
      /* ignore */
    }
  }
  const syncBtn = (btn, expanded) => {
    if (!btn) return;
    btn.classList.toggle("is-active", on);
    btn.setAttribute("aria-pressed", on ? "true" : "false");
    if (btn.id === "btn-motors-panel-collapse") {
      btn.textContent = on ? "»" : "«";
      btn.title = on ? "Motor adlarını göster (genişlet)" : "İkon modu — daralt";
      btn.setAttribute("aria-label", on ? "Motor panelini genişlet" : "Motor panelini daralt");
      btn.setAttribute("aria-expanded", expanded ? "true" : "false");
      return;
    }
    btn.title = on ? "Motor adlarını göster" : "Motor adlarını gizle (yalnızca ikonlar)";
    btn.setAttribute(
      "aria-label",
      on ? "Motor panelini genişlet" : "Motor panelini daralt (yalnızca ikonlar)",
    );
  };
  syncBtn(document.getElementById("btn-motors-compact"), !on);
  syncBtn(document.getElementById("btn-motors-panel-collapse"), !on);
}

/** Sol motor ikonuna tıklanınca panel otomatik ikon şeridine küçülür. */
function autoCompactMotorsOnMotorPick() {
  if (isMotorsCompact()) return;
  applyMotorsCompact(true, { persist: true });
}

function toggleMotorsCompact() {
  applyMotorsCompact(!isMotorsCompact(), { persist: true });
}

function wireMotorsCompactToggle() {
  const headerBtn = document.getElementById("btn-motors-compact");
  const panelBtn = document.getElementById("btn-motors-panel-collapse");
  let compact = true;
  try {
    const stored = localStorage.getItem(LS_MOTORS_COMPACT);
    compact = stored === null || stored === "1";
  } catch (_) {
    compact = true;
  }
  applyMotorsCompact(compact, { persist: false });

  const wire = (btn) => {
    if (!btn || btn.dataset.wired === "1") return;
    btn.dataset.wired = "1";
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      toggleMotorsCompact();
    });
  };
  wire(headerBtn);
  wire(panelBtn);
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
      if (btn.classList.contains("motor-item")) {
        autoCompactMotorsOnMotorPick();
      }
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
  setCodeOutput("Çalıştırılıyor...");
  let workspaceRoot = null;
  try {
    if (window.ruzgarApi?.getRoot) {
      workspaceRoot = await window.ruzgarApi.getRoot();
    }
  } catch (_) {
    workspaceRoot = null;
  }
  const relNorm = String(atolyeOpenRel || "").replace(/\\/g, "/");
  if (workspaceRoot && relNorm.startsWith("projects/")) {
    try {
      const res = await fetch(`${API}/api/programlama/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_root: workspaceRoot,
          rel: relNorm,
          smoke_only: false,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.report) {
        setCodeOutput(data.report);
        return;
      }
    } catch (_) {
      /* code/run yedek */
    }
  }
  const code = getCodeEditorText();
  if (!code) {
    setCodeOutput("Önce editöre kod yazın veya projects/ altında kayıtlı dosya açın.");
    return;
  }
  const language = String(el.codeLanguage?.value || "python").trim().toLowerCase();
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
    void refreshProgramlamaGitChanges(programlamaScopeFromContext());
    setCodeOutput(`Açıldı: ${rel}`);
    flashRuzgarDurum(`Dosya açıldı: ${rel}`);
    el.codeEditor?.focus();
  } catch (e) {
    setCodeOutput(`Dosya hatası: ${e && e.message ? e.message : e}`);
  }
}

function findCodeTreeRowByRel(rel) {
  const norm = String(rel || "").replace(/\\/g, "/").replace(/^\/+/, "");
  if (!norm || !el.codeFileTree) return null;
  const rows = el.codeFileTree.querySelectorAll(".code-tree-row");
  for (const row of rows) {
    const r = String(row.dataset.rel || "").replace(/\\/g, "/").replace(/^\/+/, "");
    if (r === norm) return row;
  }
  return null;
}

async function expandCodeTreeFolderRow(row) {
  if (!row?.classList.contains("folder")) return;
  const branch = row.closest(".code-tree-branch");
  const kids = branch?.querySelector(":scope > .code-tree-children");
  if (!kids) return;
  if (kids.dataset.loaded !== "1") {
    const depth = Number.parseInt(row.dataset.depth || "0", 10);
    kids.innerHTML = `<div class="code-tree-loading">${esc("Yükleniyor…")}</div>`;
    kids.hidden = false;
    try {
      const items = await workspaceListDir(row.dataset.rel || "");
      kids.innerHTML = "";
      for (const x of items) {
        kids.appendChild(createCodeTreeBranch(x, depth + 1));
      }
      kids.dataset.loaded = "1";
    } catch {
      kids.innerHTML = `<div class="code-tree-err">${esc("Liste okunamadı.")}</div>`;
      return;
    }
  } else if (kids.hidden) {
    kids.hidden = false;
  }
  row.classList.add("is-expanded");
  const chev = row.querySelector(".code-tree-chev");
  if (chev) chev.textContent = "▾";
}

async function expandCodeTreeToRel(targetRel) {
  const norm = String(targetRel || "").replace(/\\/g, "/").replace(/^\/+/, "");
  const parts = norm.split("/").filter(Boolean);
  if (parts.length < 2) return;
  for (let i = 1; i < parts.length; i++) {
    const folderRel = parts.slice(0, i).join("/");
    let row = findCodeTreeRowByRel(folderRel);
    if (!row) {
      await programlamaAtolyeRefreshRoot();
      row = findCodeTreeRowByRel(folderRel);
    }
    if (row) await expandCodeTreeFolderRow(row);
  }
}

async function applyProgramlamaFocusFromChat(ev) {
  const focus = String(ev?.programlama_focus_rel || "").trim();
  const project = String(ev?.programlama_project_rel || "").trim();
  if (!focus && !project) return;
  switchMode("programlama");
  await programlamaAtolyeRefreshRoot();
  if (ev?.programlama_expand_tree) {
    await expandCodeTreeToRel(focus || project);
  }
  if (focus) {
    await openProgramlamaWorkspaceFile(focus);
  }
}

let programlamaBriefingShown = false;

async function programlamaAtolyeShowBriefing() {
  if (programlamaBriefingShown || !el.codeOutput) return;
  try {
    let root = workspaceRoot;
    if (!root && window.ruzgarApi?.getRoot) {
      root = await window.ruzgarApi.getRoot();
    }
    const qs = root ? `?workspace_root=${encodeURIComponent(root)}` : "";
    const [br, sr] = await Promise.all([
      fetch(`${API}/api/programlama/briefing${qs}`, { method: "GET" }),
      fetch(`${API}/api/programlama/session${qs}`, { method: "GET" }),
    ]);
    if (!br.ok) return;
    const j = await br.json();
    let text = String(j.text || "").trim();
    if (sr.ok) {
      const sj = await sr.json().catch(() => ({}));
      const ctx = String(sj.context_text || "").trim();
      if (ctx) text += `\n\n---\n${ctx}`;
    }
    if (!text) return;
    el.codeOutput.textContent = text;
    programlamaBriefingShown = true;
  } catch (_) {
    /* sunucu yoksa sessiz */
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
    void programlamaAtolyeShowBriefing();
    void refreshProgramlamaPatchFromServer();
    void refreshProgramlamaProjectSelect();
    void refreshProgramlamaKpiDashboard();
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

function loadTercumeFileList() {
  if (window.RuzgarTercumeAtolye) window.RuzgarTercumeAtolye.load();
}

function wireMimarAtolye() {
  if (!window.RuzgarMimarAtolye) return;
  window.RuzgarMimarAtolye.init({
    api: API,
    flash: flashRuzgarDurum,
    getCurrentMode: () => currentMode,
    speakText: speakStudioTranscript,
    lastAssistantReply: () => lastAssistantReply,
    getChatHandoff: () => {
      const mode = currentMode === "okuma" ? "mimar" : currentMode;
      const h = getSharedChatHistory();
      let user = "";
      let assistant = String(lastAssistantReply || "").trim();
      for (let i = h.length - 1; i >= 0; i--) {
        const m = h[i];
        if (!assistant && m.role === "assistant") assistant = String(m.content || "").trim();
        if (m.role === "user") {
          user = String(m.content || "").trim();
          break;
        }
      }
      return { user, assistant };
    },
  });
}

function wireTercumeAtolye() {
  if (!window.RuzgarTercumeAtolye) return;
  window.RuzgarTercumeAtolye.init({
    api: API,
    esc,
    flash: flashRuzgarDurum,
    sendMessage: sendMessageWithText,
    switchMode,
    getCurrentMode: () => currentMode,
    loadIlimFileList,
    workspaceListDir,
    createCodeTreeBranch,
    lastAssistantReply: () => lastAssistantReply,
    getWorkspaceRoot: async () => {
      if (window.ruzgarApi?.getRoot) {
        const r = await window.ruzgarApi.getRoot();
        return r?.root || r?.path || "";
      }
      return "";
    },
    showTercumeChatWelcome,
  });
}

async function refreshSesCloneHint() {
  if (!el.sesCloneHint) return;
  try {
    const r = await fetch(`${API}/api/tts/clone/status`, { method: "GET" });
    if (!r.ok) throw new Error("no-clone-status");
    const j = await r.json();
    const parts = [];
    if (j.xtts) parts.push("XTTS kurulu");
    else parts.push("XTTS yok — pip install TTS torch");
    if (j.cuda) parts.push("GPU");
    else parts.push("CPU (yavaş)");
    const refs = j.referans || {};
    const okRefs = Object.entries(refs)
      .filter(([, v]) => v)
      .map(([k]) => k);
    if (okRefs.length) parts.push(`referans: ${okRefs.join(", ")}`);
    else parts.push("referans bekleniyor");
    el.sesCloneHint.textContent = j.hint_tr || parts.join(" · ");
    } catch {
    el.sesCloneHint.textContent =
      "Klon durumu okunamadı — sunucu çalışıyor mu?";
  }
}
window.refreshSesCloneHint = refreshSesCloneHint;

async function refreshSesDubHint() {
  if (!el.sesDubMeta) return;
  try {
    const r = await fetch(`${API}/api/video/dub/status`, { method: "GET" });
    if (!r.ok) throw new Error("no-dub-status");
    const j = await r.json();
    if (!j.enabled) {
      el.sesDubMeta.textContent = "Dublaj kapalı — RUZGAR_VIDEO_DUB=1 ile açın.";
      return;
    }
    el.sesDubMeta.textContent = [
      "Dublaj hazır",
      j.max_segments ? `max ${j.max_segments} segment` : "",
      j.max_duration_sec ? `max ${Math.round(j.max_duration_sec / 60)} dk` : "",
    ]
      .filter(Boolean)
      .join(" · ");
  } catch {
    el.sesDubMeta.textContent = "Dublaj durumu okunamadı — sunucu çalışıyor mu?";
  }
}

async function uploadSesCloneReferans() {
  const f = el.sesCloneRefInput?.files?.[0];
  if (!f) {
    flashRuzgarDurum("Referans ses dosyası seçin (30–120 sn).");
    return;
  }
  const kar = String(el.sesCloneKarakter?.value || "asistan").trim();
  const fd = new FormData();
  fd.append("file", f, f.name || "referans.wav");
  fd.append("karakter", kar);
  flashRuzgarDurum("Referans ses kaydediliyor…");
  setStatus("Klon referans…", "Rüzgar");
  try {
    const res = await fetch(`${API}/api/tts/clone/referans`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      let detail = j.detail;
      if (typeof detail !== "string") detail = res.statusText;
      flashRuzgarDurum(String(detail || "Referans kaydedilemedi"));
      return;
    }
    flashRuzgarDurum(`Referans kaydedildi (${kar}): ${j.referans_rel || ""}`);
    void refreshSesCloneHint();
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
  } finally {
    setStatus("Hazır", "Rüzgar");
  }
}

function sesTtsBackendPreference() {
  if (el.sesUseClone && !el.sesUseClone.checked) return "edge";
  return "auto";
}

async function refreshSesSttHint() {
  if (!el.sesSttHint) return;
  try {
    const r = await fetch(`${API}/api/health`, { method: "GET" });
    if (!r.ok) throw new Error("no-health");
    const j = await r.json();
    if (j.stt) {
      const model = j.whisper_model ? ` (${j.whisper_model})` : "";
      el.sesSttHint.textContent =
        `Konuşmayı metne dökme hazır${model}. Ses ve video (.mp4, .mkv…) desteklenir; video uzun sürer — ilerleme çubuğuna bakın.`;
    } else {
      el.sesSttHint.textContent =
        "Metne döküm kapalı. Kurulum: pip install faster-whisper — ardından yerel sunucuyu yeniden başlatın.";
    }
  } catch {
    el.sesSttHint.textContent =
      "Sunucu yok — «Metne dök» için ilim-assistant klasöründe yerel sunucuyu çalıştırın.";
  }
}

function sesFileIsVideo(name) {
  return /\.(mp4|mkv|webm|mov|m4v|avi|ts|flv|wmv|mpeg|mpg)$/i.test(String(name || ""));
}

function sesFileKindHint(file) {
  if (!file) return "";
  const mb = (file.size / (1024 * 1024)).toFixed(1);
  if (sesFileIsVideo(file.name)) {
    return `${file.name} (${mb} MB) — video; «Metne dök» sesi çıkarıp Whisper ile yazar.`;
  }
  return `${file.name} (${mb} MB)`;
}

async function runSesSttFromFile() {
  const f = el.audioFileInput?.files?.[0];
  if (!f) {
    flashRuzgarDurum("Önce bir ses veya video dosyası seçin.");
    return;
  }
  const isVideo = sesFileIsVideo(f.name);
  const langRaw = String(el.sesSttLang?.value || "tr").trim();
  const fd = new FormData();
  fd.append("file", f, f.name || (isVideo ? "media.mp4" : "audio.webm"));
  flashRuzgarDurum(
    isVideo
      ? `Video STT: ${f.name} — ses çıkarılıyor + Whisper (uzun sürebilir)…`
      : "Metne dökülüyor…",
  );
  setStatus(isVideo ? "Video → metin…" : "STT…", "Rüzgar");
  setVideoJobProgress(true, isVideo ? "Video → metin (STT)…" : "Metne dökülüyor…");
  if (el.sesSttMeta) {
    el.sesSttMeta.textContent = isVideo
      ? "Video STT çalışıyor — ffmpeg + Whisper (dakikalar sürebilir)…"
      : "STT çalışıyor…";
  }
  try {
    const q = langRaw === "auto" ? "auto" : encodeURIComponent(langRaw);
    const res = await fetch(`${API}/api/stt?lang=${q}&segments=1`, { method: "POST", body: fd });
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
      const parts = [];
      if (j.language != null && String(j.language).length) {
        parts.push(`Algılanan dil: ${j.language}`);
      }
      if (Array.isArray(j.segments) && j.segments.length) {
        parts.push(`${j.segments.length} segment`);
      }
      if (j.srt) parts.push("SRT hazır");
      el.sesSttMeta.textContent = parts.join(" · ");
    }
    flashRuzgarDurum(text ? "Metin dökümü hazır." : "Boş sonuç döndü.");
    setStatus("Hazır", "Rüzgar");
    el.sesTranscript?.focus();
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
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
      if (el.sesSttHint) el.sesSttHint.textContent = sesFileKindHint(f);
      if (el.sesSttMeta) el.sesSttMeta.textContent = "";
    });
  }
  if (el.btnSesStt) {
    el.btnSesStt.addEventListener("click", () => {
      void runSesSttFromFile();
    });
  }
  if (el.btnSesCloneUpload) {
    el.btnSesCloneUpload.addEventListener("click", () => {
      void uploadSesCloneReferans();
    });
  }
  void refreshSesCloneHint();
  if (window.ruzgarSesKolonlar?.refresh) {
    void window.ruzgarSesKolonlar.refresh();
  }
  if (window.ruzgarKlonSesStudio?.refresh) {
    void window.ruzgarKlonSesStudio.refresh();
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
  if (el.btnSesTilavet) {
    el.btnSesTilavet.addEventListener("click", () => {
      void speakStudioTilavet(el.sesTranscript?.value || "");
    });
  }
  if (el.btnSesClear) {
    el.btnSesClear.addEventListener("click", () => {
      if (el.sesTranscript) el.sesTranscript.value = "";
      if (el.sesSttMeta) el.sesSttMeta.textContent = "";
      flashRuzgarDurum("Metin dökümü temizlendi.");
    });
  }
  if (el.btnSesDub) {
    el.btnSesDub.addEventListener("click", () => {
      void runSesDubJob();
    });
  }
  if (el.btnSesDubVideoPanel) {
    el.btnSesDubVideoPanel.addEventListener("click", () => {
      if (el.sesDubRel?.value && el.videoRelDub) {
        el.videoRelDub.value = String(el.sesDubRel.value).trim();
      }
      switchMode("video");
      window.setTimeout(() => {
        window.RuzgarVideoAtolye?.openDuzenDock?.("dub");
        el.videoRelDub?.focus?.({ preventScroll: true });
      }, 120);
    });
  }
  if (el.sesDubFileInput && el.sesDubFileInput.dataset.sesDubWired !== "1") {
    el.sesDubFileInput.dataset.sesDubWired = "1";
    el.sesDubFileInput.addEventListener("change", () => {
      const f = el.sesDubFileInput.files && el.sesDubFileInput.files[0];
      if (!f) return;
      if (el.sesDubRel) el.sesDubRel.value = f.name;
      if (el.sesDubMeta) {
        el.sesDubMeta.textContent = `${f.name} — «Dublaj yap» ile yuklenir (max 30 MB).`;
      }
    });
  }
  void refreshSesDubHint();
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

function workspaceMediaUrl(rel) {
  const r = String(rel || "").trim().replace(/\\/g, "/");
  if (!r) return "";
  return `${API}/api/workspace/media?rel=${encodeURIComponent(r)}`;
}

function parseVideoTimeSec(raw) {
  const s = String(raw || "").trim().replace(",", ".");
  if (!s) return NaN;
  if (/^\d+(\.\d+)?$/.test(s)) return parseFloat(s);
  const parts = s.split(":").map((x) => parseFloat(x));
  if (parts.some((n) => !Number.isFinite(n))) return NaN;
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return NaN;
}

function formatVideoApiError(detail, res, fallback) {
  let msg = detail;
  if (Array.isArray(msg)) {
    msg = msg.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
  } else if (msg != null && typeof msg !== "string") {
    msg = JSON.stringify(msg);
  }
  msg = String(msg || res?.statusText || fallback || "İşlem başarısız");
  if (/ffmpeg bulunamad/i.test(msg)) {
    return `${msg} · İpucu: https://ffmpeg.org/download.html — kurulumdan sonra Rüzgar'ı yeniden başlatın.`;
  }
  if (/ffprobe/i.test(msg) && /bulunamad|yok|not found/i.test(msg)) {
    return `${msg} · İpucu: tam FFmpeg paketi (ffmpeg + ffprobe) PATH'te olmalı.`;
  }
  if (/yt-dlp|ytdlp/i.test(msg)) {
    return `${msg} · İpucu: pip install yt-dlp veya requirements.txt.`;
  }
  if (res?.status === 503) {
    return `${msg} · Sunucu hazır değil; Start-Ruzgar.ps1 ile API'yi kontrol edin.`;
  }
  return msg;
}

function setVideoJobProgress(active, label, pct) {
  const wrap = el.videoJobProgress;
  if (!wrap) return;
  if (!active) {
    wrap.hidden = true;
    wrap.setAttribute("aria-hidden", "true");
    wrap.style.display = "none";
    return;
  }
  wrap.hidden = false;
  wrap.removeAttribute("aria-hidden");
  wrap.style.display = "";
  if (el.videoJobProgressLabel) {
    el.videoJobProgressLabel.textContent = label || "İşleniyor…";
  }
  const bar = el.videoJobProgressBar;
  const track = wrap.querySelector(".video-job-progress-track");
  if (!bar) return;
  if (pct == null || !Number.isFinite(pct)) {
    bar.classList.add("is-indeterminate");
    bar.style.width = "";
    if (track) track.removeAttribute("aria-valuenow");
  } else {
    bar.classList.remove("is-indeterminate");
    const v = Math.min(100, Math.max(0, pct));
    bar.style.width = `${v}%`;
    if (track) track.setAttribute("aria-valuenow", String(Math.round(v)));
  }
}

async function loadVideoPreviewFromRel(rel, opts = {}) {
  const r = String(rel || "").trim();
  if (!r || !el.videoPreview) return false;
  clearYoutubeEmbedPreview();
  try {
    if (videoPreviewObjectUrl) {
      URL.revokeObjectURL(videoPreviewObjectUrl);
      videoPreviewObjectUrl = null;
    }
  } catch (_) {
    /* ignore */
  }
  const url = workspaceMediaUrl(r);
  el.videoPreview.src = url;
  el.videoPreview.load();
  if (el.videoRelWorkspace) el.videoRelWorkspace.value = r;
  if (el.videoRelDub) el.videoRelDub.value = r;
  if (el.sesDubRel) el.sesDubRel.value = r;
  videoTimelineIn = null;
  videoTimelineOut = null;
  lastVideoProbeDurationSec = 0;
  el.videoPreview.classList.add("video-preview-flash");
  window.setTimeout(() => el.videoPreview?.classList.remove("video-preview-flash"), 1400);
  if (opts.flash !== false) flashRuzgarDurum(`Önizleme yüklendi: ${r}`);
  return new Promise((resolve) => {
    const v = el.videoPreview;
    if (!v) {
      resolve(false);
      return;
    }
    const done = (ok) => {
      v.removeEventListener("loadeddata", onOk);
      v.removeEventListener("error", onErr);
      resolve(ok);
    };
    const onOk = () => done(true);
    const onErr = () => {
      flashRuzgarDurum(
        `Önizleme açılamadı (${r}). Sunucuyu yeniden başlatın; /api/workspace/media gerekir.`,
      );
      done(false);
    };
    if (v.readyState >= 2) {
      done(true);
      return;
    }
    v.addEventListener("loadeddata", onOk, { once: true });
    v.addEventListener("error", onErr, { once: true });
  });
}

function getNormalizedTimelineRange() {
  const d = getVideoEffectiveDurationSec();
  if (videoTimelineIn == null && videoTimelineOut == null) return null;
  let a = videoTimelineIn != null ? videoTimelineIn : 0;
  let b = videoTimelineOut != null ? videoTimelineOut : d > 0 ? d : 0;
  if (b < a) [a, b] = [b, a];
  if (d > 0) {
    a = Math.max(0, Math.min(d, a));
    b = Math.max(0, Math.min(d, b));
  }
  if (b - a > VIDEO_EDIT_MAX_CLIP_SEC) b = a + VIDEO_EDIT_MAX_CLIP_SEC;
  if (b <= a + 0.01) return null;
  return { start: a, end: b, duration: b - a };
}

function timelineSecFromClientX(clientX) {
  const track = el.videoTimelineTrack;
  if (!track) return 0;
  const rect = track.getBoundingClientRect();
  const x = (clientX - rect.left) / Math.max(rect.width, 1);
  const d = getVideoEffectiveDurationSec();
  if (d <= 0) return 0;
  return Math.max(0, Math.min(d, x * d));
}

function stopVideoTimelineDrag() {
  videoTimelineDrag = null;
  if (el.videoTimelineTrack) el.videoTimelineTrack.classList.remove("is-dragging");
}

function onVideoTimelinePointerMove(ev) {
  if (!videoTimelineDrag) return;
  const sec = timelineSecFromClientX(ev.clientX);
  const d = getVideoEffectiveDurationSec();
  if (videoTimelineDrag === "in") {
    videoTimelineIn = sec;
    if (videoTimelineOut != null && videoTimelineOut < videoTimelineIn) {
      videoTimelineOut = videoTimelineIn;
    }
    if (videoTimelineOut != null && videoTimelineOut - videoTimelineIn > VIDEO_EDIT_MAX_CLIP_SEC) {
      videoTimelineOut = Math.min(d, videoTimelineIn + VIDEO_EDIT_MAX_CLIP_SEC);
    }
  } else if (videoTimelineDrag === "out") {
    videoTimelineOut = sec;
    if (videoTimelineIn != null && videoTimelineOut < videoTimelineIn) {
      videoTimelineIn = videoTimelineOut;
    }
    if (videoTimelineIn != null && videoTimelineOut - videoTimelineIn > VIDEO_EDIT_MAX_CLIP_SEC) {
      videoTimelineIn = Math.max(0, videoTimelineOut - VIDEO_EDIT_MAX_CLIP_SEC);
    }
  } else if (videoTimelineDrag === "scrub") {
    const v = el.videoPreview;
    if (v && d > 0) v.currentTime = sec;
  }
  updateVideoTimelineUI();
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
  const norm = getNormalizedTimelineRange();
  if (rangeEl) {
    if (norm) {
      const left = (norm.start / safeD) * 100;
      const w = ((norm.end - norm.start) / safeD) * 100;
      rangeEl.hidden = false;
      rangeEl.style.left = `${Math.min(100, Math.max(0, left))}%`;
      rangeEl.style.width = `${Math.min(100 - left, Math.max(0, w))}%`;
    } else {
      rangeEl.hidden = true;
    }
  }

  const showHandles = d > 0;
  const inPos =
    videoTimelineIn != null ? videoTimelineIn : norm ? norm.start : 0;
  const outPos =
    videoTimelineOut != null
      ? videoTimelineOut
      : norm
        ? norm.end
        : Math.min(d, VIDEO_EDIT_MAX_CLIP_SEC);
  if (el.videoTimelineHandleIn) {
    el.videoTimelineHandleIn.hidden = !showHandles;
    if (showHandles) {
      el.videoTimelineHandleIn.style.left = `${(inPos / safeD) * 100}%`;
    }
  }
  if (el.videoTimelineHandleOut) {
    el.videoTimelineHandleOut.hidden = !showHandles;
    if (showHandles) {
      el.videoTimelineHandleOut.style.left = `${(outPos / safeD) * 100}%`;
    }
  }

  if (el.videoTimelineLabel) {
    let cutInfo = "—";
    if (norm) {
      const capped =
        norm.duration >= VIDEO_EDIT_MAX_CLIP_SEC - 0.05
          ? ` (max ${VIDEO_EDIT_MAX_CLIP_SEC / 60} dk)`
          : "";
      cutInfo = `${norm.start.toFixed(1)}–${norm.end.toFixed(1)} sn (${norm.duration.toFixed(1)} sn)${capped}`;
    } else if (videoTimelineIn != null) {
      cutInfo = `Başlangıç ${videoTimelineIn.toFixed(1)} sn`;
    } else if (videoTimelineOut != null) {
      cutInfo = `Bitiş ${videoTimelineOut.toFixed(1)} sn`;
    }
    const totalStr = d > 0 ? `${d.toFixed(1)} sn` : "— (dosya veya «Medya bilgisi»)";
    el.videoTimelineLabel.textContent = `Süre: ${totalStr} · İmleç: ${cur.toFixed(1)} sn · Kesim: ${cutInfo}`;
  }
}

function newVideoEditClipId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `clip_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function renderVideoEditBin() {
  const list = el.videoEditBin;
  if (!list) return;
  list.innerHTML = "";
  if (el.videoEditBinEmpty) el.videoEditBinEmpty.hidden = videoEditBin.length > 0;
  videoEditBin.forEach((clip, idx) => {
    const li = document.createElement("li");
    li.className = "video-edit-bin-item";
    li.draggable = true;
    li.dataset.clipId = clip.id;
    const dur = Math.max(0, (clip.end_sec ?? 0) - (clip.start_sec ?? 0));
    li.innerHTML = `
      <span class="video-edit-bin-grip" title="Sürükleyerek sırala">⋮⋮</span>
      <span class="video-edit-bin-meta">
        <strong>${idx + 1}.</strong> ${esc(clip.label || "Parça")}
        · ${esc(clip.rel)} · ${Number(clip.start_sec || 0).toFixed(1)}–${Number(clip.end_sec || 0).toFixed(1)} sn (${dur.toFixed(1)} sn)
      </span>
      <button type="button" class="btn-secondary btn-compact video-edit-bin-remove" data-remove-id="${esc(clip.id)}">Sil</button>
    `;
    li.addEventListener("dragstart", (ev) => {
      li.classList.add("is-dragging");
      ev.dataTransfer.setData("text/plain", clip.id);
      ev.dataTransfer.effectAllowed = "move";
    });
    li.addEventListener("dragend", () => li.classList.remove("is-dragging"));
    li.addEventListener("dragover", (ev) => {
      ev.preventDefault();
      ev.dataTransfer.dropEffect = "move";
    });
    li.addEventListener("drop", (ev) => {
      ev.preventDefault();
      const fromId = ev.dataTransfer.getData("text/plain");
      if (!fromId || fromId === clip.id) return;
      const fromIdx = videoEditBin.findIndex((c) => c.id === fromId);
      const toIdx = videoEditBin.findIndex((c) => c.id === clip.id);
      if (fromIdx < 0 || toIdx < 0) return;
      const [moved] = videoEditBin.splice(fromIdx, 1);
      videoEditBin.splice(toIdx, 0, moved);
      renderVideoEditBin();
    });
    li.querySelector("[data-remove-id]")?.addEventListener("click", () => {
      videoEditBin = videoEditBin.filter((c) => c.id !== clip.id);
      renderVideoEditBin();
    });
    list.appendChild(li);
  });
}

function addClipToVideoEditBin(rel, startSec, endSec, label) {
  const relTrim = String(rel || "").trim();
  if (!relTrim) {
    flashRuzgarDurum("Proje içi göreli yol gerekli (üstteki alan).");
    return false;
  }
  let a = Math.max(0, Number(startSec) || 0);
  let b = endSec != null && String(endSec).trim() !== "" ? Number(endSec) : null;
  const d = getVideoEffectiveDurationSec();
  if (b == null || !Number.isFinite(b)) {
    b = d > 0 ? d : a + VIDEO_EDIT_MAX_CLIP_SEC;
  }
  if (!Number.isFinite(b)) b = a + VIDEO_EDIT_MAX_CLIP_SEC;
  if (b < a) [a, b] = [b, a];
  if (b - a > VIDEO_EDIT_MAX_CLIP_SEC) b = a + VIDEO_EDIT_MAX_CLIP_SEC;
  if (b <= a + 0.01) {
    flashRuzgarDurum("Geçersiz aralık.");
    return false;
  }
  videoEditBin.push({
    id: newVideoEditClipId(),
    rel: relTrim,
    start_sec: a,
    end_sec: b,
    label: label || `Parça ${videoEditBin.length + 1}`,
  });
  renderVideoEditBin();
  return true;
}

function addCurrentTimelineSelectionToBin() {
  const rel = String(el.videoRelWorkspace?.value || "").trim();
  const norm = getNormalizedTimelineRange();
  if (!norm) {
    flashRuzgarDurum("Zaman çizelgesinde başlangıç ve bitiş seçin (tutamaçları sürükleyin veya işaretleyin).");
    return;
  }
  if (addClipToVideoEditBin(rel, norm.start, norm.end, "")) {
    flashRuzgarDurum(`Listeye eklendi: ${norm.duration.toFixed(1)} sn`);
  }
}

function addInsertRelClipToBin() {
  const rel = String(el.videoEditInsertRel?.value || el.videoRelWorkspace?.value || "").trim();
  const start = Number(el.videoEditInsertStart?.value || 0);
  let endRaw = String(el.videoEditInsertEnd?.value || "").trim();
  let end = endRaw ? Number(endRaw) : null;
  if (end == null || !Number.isFinite(end)) {
    end = start + VIDEO_EDIT_MAX_CLIP_SEC;
  }
  if (addClipToVideoEditBin(rel, start, end, "Ara parça")) {
    flashRuzgarDurum("Dosya kurgu listesine eklendi.");
  }
}

async function runVideoEditMixJob() {
  if (!videoEditBin.length) {
    flashRuzgarDurum("Önce kurgu listesine en az bir parça ekleyin.");
    return;
  }
  flashRuzgarDurum("Kurgu birleştiriliyor (FFmpeg)…");
  setStatus("Video kurgu…", "Rüzgar");
  setVideoJobProgress(true, "Kurgu birleştiriliyor…");
  const body = {
    clips: videoEditBin.map((c) => ({
      rel: c.rel,
      start_sec: c.start_sec,
      end_sec: c.end_sec,
      label: c.label || "",
    })),
    copy_streams: el.videoEditCopyStreams?.checked !== false,
    project_name: String(el.videoEditProjectName?.value || "").trim(),
  };
  try {
    const res = await fetch(`${API}/api/video/edit/mix`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok || !j.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail || j.error, res, "Kurgu başarısız."));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    if (j.output_rel) {
      appendVideoJobNote(j.output_rel);
      if (el.videoRelWorkspace) el.videoRelWorkspace.value = j.output_rel;
    }
    flashRuzgarDurum(
      `Kurgu hazır · ${Number(j.total_duration_sec || 0).toFixed(1)} sn · havuz: ${j.project_id || "—"}`
    );
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
  }
}

function resetVideoTimelineMarks() {
  videoTimelineIn = null;
  videoTimelineOut = null;
  stopVideoTimelineDrag();
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

/** Video oluştur (V5) — son plan JSON */
let videoCreatePendingPlan = null;
const VIDEO_CREATE_DEFAULT_IMAGES_DIR = "ilim-assistant/arsiv/video_gorseller";

function readVideoCreateForm() {
  return {
    title: String(el.videoCreateTitle?.value || "").trim(),
    theme: String(el.videoCreateTheme?.value || "genel anlatım").trim(),
    text: String(el.videoCreateText?.value || "").trim(),
    preset: String(el.videoCreatePreset?.value || "16:9").trim(),
    quality: String(el.videoCreateQuality?.value || "high").trim(),
    render_mode: String(el.videoCreateRenderMode?.value || "motion").trim(),
    karakter: String(el.videoCreateKarakter?.value || "asistan").trim(),
    rel_background: String(el.videoCreateBg?.value || "").trim(),
    rel_images_dir: String(el.videoCreateImagesDir?.value || "").trim(),
  };
}

const VIDEO_CREATE_PROJE_REL = "ilim-assistant/arsiv/video_projeler/umit_anilar.json";

function applyVideoCreateProject(proje) {
  if (!proje || typeof proje !== "object") return;
  if (el.videoCreateTitle) el.videoCreateTitle.value = String(proje.title || "");
  if (el.videoCreateTheme) el.videoCreateTheme.value = String(proje.theme || "");
  if (el.videoCreateText) el.videoCreateText.value = String(proje.text || "");
  if (el.videoCreatePreset && proje.preset) el.videoCreatePreset.value = String(proje.preset);
  if (el.videoCreateQuality && proje.quality) el.videoCreateQuality.value = String(proje.quality);
  if (el.videoCreateRenderMode && proje.render_mode) {
    el.videoCreateRenderMode.value = String(proje.render_mode);
  }
  if (el.videoCreateKarakter && proje.karakter) el.videoCreateKarakter.value = String(proje.karakter);
  if (el.videoCreateImagesDir) {
    el.videoCreateImagesDir.value = String(proje.rel_images_dir || "ilim-assistant/arsiv/video_gorseller");
  }
  if (proje.plan?.scenes?.length) {
    videoCreatePendingPlan = proje.plan;
    if (proje.plan.rel_images_dir && el.videoCreateImagesDir) {
      el.videoCreateImagesDir.value = String(proje.plan.rel_images_dir);
    }
    if (proje.plan.render_mode && el.videoCreateRenderMode) {
      el.videoCreateRenderMode.value = String(proje.plan.render_mode);
    }
    showVideoCreatePlanPreview(proje.plan, "");
  }
}

function applyStoryboardApiResult(j) {
  if (!j || typeof j !== "object") return;
  videoCreatePendingPlan = j.plan || null;
  if (j.rel_images_dir && el.videoCreateImagesDir) {
    el.videoCreateImagesDir.value = String(j.rel_images_dir);
  }
  if (j.render_mode && el.videoCreateRenderMode) {
    el.videoCreateRenderMode.value = String(j.render_mode);
  }
  showVideoCreatePlanPreview(j.plan, j.plan_rel, j.storyboard, j.storyboard_rel);
}

async function loadVideoCreateProjeAnilar() {
  flashRuzgarDurum("Anılar projesi yükleniyor…");
  try {
    const res = await fetch(
      `${API}/api/workspace/read-text?rel=${encodeURIComponent(VIDEO_CREATE_PROJE_REL)}`,
    );
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(j.detail || res.statusText);
    const proje = JSON.parse(String(j.text || ""));
    applyVideoCreateProject(proje);
    flashRuzgarDurum("Proje yüklendi — «Videoyu oluştur» ile Rüzgar üretsin.");
  } catch (e) {
    flashRuzgarDurum(`Proje yüklenemedi: ${e.message || e}`);
  }
}

function showVideoCreatePlanPreview(plan, planRel, board, storyboardRel) {
  if (!el.videoCreatePlanPreview) return;
  const scenes = plan?.scenes || [];
  const chars = board?.characters || plan?.characters || [];
  const lines = scenes.map(
    (s, i) =>
      `${i + 1}. [${s.mood || "?"}] ${String(s.narration || "").slice(0, 120)}${String(s.narration || "").length > 120 ? "…" : ""}`,
  );
  const metaParts = [`${scenes.length} sahne`];
  if (planRel) metaParts.push(`plan: ${planRel}`);
  if (storyboardRel) metaParts.push(`storyboard: ${storyboardRel}`);
  el.videoCreatePlanPreview.hidden = false;
  el.videoCreatePlanPreview.textContent = [
    plan?.title ? `Başlık: ${plan.title}` : "",
    board?.synopsis ? `Özet: ${board.synopsis}` : plan?.synopsis ? `Özet: ${plan.synopsis}` : "",
    chars.length ? `Kahramanlar: ${chars.map((c) => c.name || c.id).join(", ")}` : "",
    metaParts.join(" · "),
    plan?.rel_images_dir ? `Görseller: ${plan.rel_images_dir}` : "",
    plan?.render_mode ? `Mod: ${plan.render_mode}` : "",
    board?.render_recommendation
      ? `Önerilen mod: ${board.render_recommendation} (${board?.capability_note || ""})`
      : "",
    "",
    ...lines,
  ]
    .filter(Boolean)
    .join("\n");
}

async function runVideoCreateStoryboardJob() {
  const form = readVideoCreateForm();
  if (form.text.length < 20) {
    flashRuzgarDurum("Hikâye metni en az 20 karakter olmalı.");
    return;
  }
  const imagesDir = form.rel_images_dir || VIDEO_CREATE_DEFAULT_IMAGES_DIR;
  if (!form.rel_images_dir && el.videoCreateImagesDir) {
    el.videoCreateImagesDir.value = imagesDir;
  }
  flashRuzgarDurum("Hikâye canlandırılıyor — kahramanlar ve sahneler planlanıyor…");
  setVideoJobProgress(true, "Storyboard (Ollama)…");
  const ctrl = new AbortController();
  const to = window.setTimeout(() => ctrl.abort(), RUZGAR_VIDEO_CREATE_TIMEOUT_MS);
  try {
    const res = await fetch(`${API}/api/video/storyboard`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: form.text,
        theme: form.theme,
        title: form.title,
        max_scenes: 12,
        rel_images_dir: imagesDir,
      }),
      signal: ctrl.signal,
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(j.detail || res.statusText);
    applyStoryboardApiResult(j);
    const assetNote =
      Number(j.asset_count) > 0 ? ` · ${j.asset_count} görsel eşlendi` : " · görsel klasörü boş";
    const saveNote = j.plan_rel ? ` Plan: ${j.plan_rel}` : "";
    const rec = String(j.render_recommendation || "motion");
    if (rec === "generative") {
      flashRuzgarDurum(
        `Storyboard hazır (${j.scene_count} sahne${assetNote}).${saveNote} V8 Runway modu API anahtarı ister; yoksa hareket yedeği kullanılır.`,
      );
    } else if ((j.render_mode || form.render_mode) === "portrait") {
      flashRuzgarDurum(
        `${j.scene_count} sahneli storyboard hazır${assetNote}.${saveNote} V7.2 portre için SadTalker gerekir; yoksa hareket yedeği.`,
      );
    } else if ((j.render_mode || form.render_mode) === "motion") {
      flashRuzgarDurum(
        `${j.scene_count} sahneli storyboard hazır${assetNote}.${saveNote} «Videoyu oluştur» — ses + fotoğraf + sinematik hareket (V7.1).`,
      );
    } else {
      flashRuzgarDurum(`${j.scene_count} sahneli storyboard hazır${assetNote}.${saveNote} «Videoyu oluştur» de.`);
    }
  } catch (e) {
    flashRuzgarDurum(`Storyboard hatası: ${e.message || e}`);
  } finally {
    window.clearTimeout(to);
    setVideoJobProgress(false);
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoCreatePlanJob() {
  const form = readVideoCreateForm();
  if (form.text.length < 20) {
    flashRuzgarDurum("Anlatım metni en az 20 karakter olmalı.");
    return;
  }
  flashRuzgarDurum("Sahne planı hazırlanıyor (Ollama)…");
  setStatus("Sahne planı…", "Rüzgar");
  setVideoJobProgress(true, "Sahne planı hazırlanıyor…");
  const ctrl = new AbortController();
  const to = window.setTimeout(() => ctrl.abort(), RUZGAR_VIDEO_CREATE_TIMEOUT_MS);
  try {
    const res = await fetch(`${API}/api/video/plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: form.text,
        theme: form.theme,
        title: form.title,
        max_scenes: 24,
      }),
      signal: ctrl.signal,
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(j.detail || res.statusText || "Plan hatası");
    videoCreatePendingPlan = j.plan || null;
    showVideoCreatePlanPreview(j.plan, j.plan_rel);
    flashRuzgarDurum(`${j.scene_count || 0} sahneli plan hazır. «Videoyu oluştur» ile devam edin.`);
  } catch (e) {
    flashRuzgarDurum(`Plan hatası: ${e.message || e}`);
  } finally {
    window.clearTimeout(to);
    setVideoJobProgress(false);
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoCreateRenderJob() {
  const form = readVideoCreateForm();
  if (form.text.length < 20 && !videoCreatePendingPlan) {
    flashRuzgarDurum("Metin girin veya önce sahne planı oluşturun.");
    return;
  }
  flashRuzgarDurum("Video oluşturuluyor — seslendirme ve kurgu birkaç dakika sürebilir…");
  setStatus("Video oluşturuluyor…", "Rüzgar");
  setVideoJobProgress(true, "Video oluşturuluyor (TTS + FFmpeg)…");
  const ctrl = new AbortController();
  const to = window.setTimeout(() => ctrl.abort(), RUZGAR_VIDEO_CREATE_TIMEOUT_MS);
  try {
    const body = {
      ...form,
      intro_title: form.title,
      max_scenes: 24,
    };
    if (!body.rel_images_dir && videoCreatePendingPlan?.rel_images_dir) {
      body.rel_images_dir = String(videoCreatePendingPlan.rel_images_dir);
    }
    if (videoCreatePendingPlan?.render_mode) {
      body.render_mode = String(videoCreatePendingPlan.render_mode);
    }
    if (videoCreatePendingPlan) body.plan = videoCreatePendingPlan;
    const res = await fetch(`${API}/api/video/create`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(j.detail || res.statusText || "Oluşturma hatası");
    if (j.plan) {
      videoCreatePendingPlan = j.plan;
      showVideoCreatePlanPreview(j.plan, j.plan_rel);
    }
    const out = String(j.output_rel || "").trim();
    const dur = Number(j.total_duration_sec);
    const durTxt = Number.isFinite(dur) && dur > 0 ? ` · ${Math.round(dur)} sn` : "";
    const notes = Array.isArray(j.render_notes) ? j.render_notes.filter(Boolean) : [];
    const noteTxt = notes.length ? ` · ${notes[0]}` : "";
    if (out) appendVideoJobNote(out);
    flashRuzgarDurum(
      `Video hazır${durTxt}: ${j.scene_count || "?"} sahne → ${out || "çıktı klasörü"}${noteTxt}`,
    );
  } catch (e) {
    flashRuzgarDurum(`Video oluşturma hatası: ${e.message || e}`);
  } finally {
    window.clearTimeout(to);
    setVideoJobProgress(false);
    setStatus("Hazır", "Rüzgar");
  }
}

function wireVideoCreatePanel() {
  const panel = document.getElementById("video-anchor-create");
  if (!panel || panel.dataset.createWired === "1") return;
  panel.dataset.createWired = "1";
  if (el.btnVideoCreateStoryboard) {
    el.btnVideoCreateStoryboard.addEventListener("click", () => {
      void runVideoCreateStoryboardJob();
    });
  }
  if (el.btnVideoCreateLoadProje) {
    el.btnVideoCreateLoadProje.addEventListener("click", () => {
      void loadVideoCreateProjeAnilar();
    });
  }
  if (el.btnVideoCreatePlan) {
    el.btnVideoCreatePlan.addEventListener("click", () => {
      void runVideoCreatePlanJob();
    });
  }
  if (el.btnVideoCreateRender) {
    el.btnVideoCreateRender.addEventListener("click", () => {
      void runVideoCreateRenderJob();
    });
  }
}

function wireVideoEditPanel() {
  const panel = document.getElementById("video-anchor-v5");
  if (!panel || panel.dataset.editWired === "1") return;
  panel.dataset.editWired = "1";
  if (el.btnVideoAddClip) {
    el.btnVideoAddClip.addEventListener("click", () => addCurrentTimelineSelectionToBin());
  }
  if (el.btnVideoInsertClip) {
    el.btnVideoInsertClip.addEventListener("click", () => addInsertRelClipToBin());
  }
  if (el.btnVideoClearBin) {
    el.btnVideoClearBin.addEventListener("click", () => {
      videoEditBin = [];
      renderVideoEditBin();
      flashRuzgarDurum("Kurgu listesi temizlendi.");
    });
  }
  if (el.btnVideoEditMix) {
    el.btnVideoEditMix.addEventListener("click", () => {
      void runVideoEditMixJob();
    });
  }
  renderVideoEditBin();
}

function wireVideoTimeline() {
  const wrap = document.getElementById("video-timeline-wrap");
  if (!wrap || wrap.dataset.timelineWired === "1") return;
  wrap.dataset.timelineWired = "1";
  if (el.videoPreview) {
    el.videoPreview.addEventListener("timeupdate", () => updateVideoTimelineUI());
    el.videoPreview.addEventListener("loadedmetadata", () => {
      const d = getVideoEffectiveDurationSec();
      if (d > 0 && videoTimelineIn == null && videoTimelineOut == null) {
        videoTimelineIn = 0;
        videoTimelineOut = Math.min(d, VIDEO_EDIT_MAX_CLIP_SEC);
      }
      updateVideoTimelineUI();
    });
  }
  const bindHandle = (handleEl, role) => {
    if (!handleEl) return;
    handleEl.addEventListener("pointerdown", (ev) => {
      ev.preventDefault();
      ev.stopPropagation();
      const d = getVideoEffectiveDurationSec();
      if (d <= 0) {
        flashRuzgarDurum("Önce dosya veya süre bilgisi gerekli.");
        return;
      }
      if (role === "in" && videoTimelineIn == null) videoTimelineIn = timelineSecFromClientX(ev.clientX);
      if (role === "out" && videoTimelineOut == null) videoTimelineOut = timelineSecFromClientX(ev.clientX);
      videoTimelineDrag = role;
      if (el.videoTimelineTrack) el.videoTimelineTrack.classList.add("is-dragging");
      handleEl.setPointerCapture(ev.pointerId);
    });
    handleEl.addEventListener("pointermove", (ev) => {
      if (videoTimelineDrag === role) onVideoTimelinePointerMove(ev);
    });
    handleEl.addEventListener("pointerup", (ev) => {
      if (videoTimelineDrag === role) {
        stopVideoTimelineDrag();
        try {
          handleEl.releasePointerCapture(ev.pointerId);
        } catch (_) {
          /* ignore */
        }
        updateVideoTimelineUI();
      }
    });
    handleEl.addEventListener("pointercancel", () => stopVideoTimelineDrag());
  };
  bindHandle(el.videoTimelineHandleIn, "in");
  bindHandle(el.videoTimelineHandleOut, "out");
  if (el.videoTimelineTrack) {
    el.videoTimelineTrack.addEventListener("pointerdown", (ev) => {
      if (ev.target.closest(".video-timeline-handle")) return;
      const d = getVideoEffectiveDurationSec();
      if (d <= 0) return;
      videoTimelineDrag = "scrub";
      el.videoTimelineTrack.classList.add("is-dragging");
      seekVideoFromTimelineClientX(ev.clientX);
    });
    el.videoTimelineTrack.addEventListener("pointermove", (ev) => {
      if (videoTimelineDrag === "scrub") onVideoTimelinePointerMove(ev);
    });
    el.videoTimelineTrack.addEventListener("pointerup", stopVideoTimelineDrag);
    el.videoTimelineTrack.addEventListener("pointercancel", stopVideoTimelineDrag);
    el.videoTimelineTrack.addEventListener("click", (ev) => {
      if (ev.target.closest(".video-timeline-handle")) return;
      seekVideoFromTimelineClientX(ev.clientX);
    });
  }
  window.addEventListener("pointerup", stopVideoTimelineDrag);
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
  if (el.btnVideoSubProcess) {
    el.btnVideoSubProcess.addEventListener("click", () => {
      void runVideoSubProcessJob();
    });
  }
  if (el.btnVideoSubPipeline) {
    el.btnVideoSubPipeline.addEventListener("click", () => {
      void runVideoSubPipelineJob();
    });
  }
  if (el.btnVideoDub) {
    el.btnVideoDub.addEventListener("click", () => {
      void runVideoDubJob();
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
    switchMode("tercume");
    if (window.RuzgarTercumeAtolye) window.RuzgarTercumeAtolye.importText(text, rel);
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
    const parts = [];
    if (j.ffmpeg && j.ffprobe) {
      parts.push("FFmpeg hazır — kes, dönüştür, altyazı, mux, kurgu");
    } else if (j.ffmpeg) {
      parts.push("ffmpeg var; ffprobe eksik — tam FFmpeg paketi kurun");
    } else {
      parts.push("FFmpeg yok — kurup PATH'e ekleyin, sunucuyu yeniden başlatın");
    }
    if (j.ytdlp) {
      parts.push("yt-dlp hazır — indir + YouTube arama");
    } else {
      parts.push("yt-dlp yok — pip install yt-dlp veya PATH'e yt-dlp");
    }
    const vc = j.video_create || {};
    const createBits = ["motion ✓"];
    if (vc.portrait) createBits.push("portre ✓");
    else createBits.push("portre (SadTalker kur)");
    if (vc.generative) createBits.push("Runway ✓");
    else createBits.push("Runway (API anahtarı)");
    parts.push(`Video oluştur: ${createBits.join(", ")}`);
    const vd = j.video_dub || {};
    if (vd.enabled) {
      parts.push(`Dublaj S6 ✓ (max ${vd.max_segments || "?"} seg)`);
    }
    el.videoEngineHint.textContent = `${parts.join(" · ")} · Çıktı: .ruzgar-video-export/ · Paneller: üst düğmeler veya Düzen menüsü`;
  } catch {
    el.videoEngineHint.textContent =
      "Sunucu kapalı — video işlemleri için ilim-assistant yerel sunucusu (127.0.0.1:8779) çalışır olmalıdır.";
  }
}

async function runVideoProbeWithForm(fd) {
  flashRuzgarDurum("Ortam inceleniyor…");
  setStatus("Medya özeti…", "Rüzgar");
  setVideoJobProgress(true, "Medya bilgisi alınıyor…");
  try {
    const res = await fetch(`${API}/api/video/probe`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      const msg = formatVideoApiError(j.detail, res, "Medya özeti alınamadı");
      if (el.videoProbeJson) el.videoProbeJson.textContent = msg;
      flashRuzgarDurum(msg);
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const sum = j.summary;
    if (sum && typeof sum.duration_sec === "number" && Number.isFinite(sum.duration_sec)) {
      lastVideoProbeDurationSec = Math.max(0, sum.duration_sec);
    }
    if (el.videoProbeJson) {
      const relNote = j.rel ? `\nKaynak: ${j.rel}\n` : "";
      el.videoProbeJson.textContent = `${relNote}${formatVideoSummaryHuman(sum)}`.trim();
    }
    updateVideoTimelineUI();
    flashRuzgarDurum(j.rel ? `Medya özeti hazır (${j.rel})` : "Medya özeti hazır.");
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    if (el.videoProbeJson) el.videoProbeJson.textContent = String(e && e.message ? e.message : e);
    flashRuzgarDurum("Medya özeti isteği başarısız.");
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
  }
}

async function runVideoProbeFromFile() {
  const f = el.videoFileInput?.files?.[0];
  const rel = String(el.videoRelWorkspace?.value || "").trim();
  if (f) {
    const fd = new FormData();
    fd.append("file", f, f.name || "media.bin");
    await runVideoProbeWithForm(fd);
    return;
  }
  if (rel) {
    const fd = new FormData();
    fd.append("rel", rel);
    await runVideoProbeWithForm(fd);
    return;
  }
  if (canStreamEditCinema()) {
    await runVideoProbeFromStream();
    return;
  }
  flashRuzgarDurum("Dosya seçin, sinemada video açın veya göreli yol yazın.");
}

function appendVideoJobNote(rel) {
  const line = `\n\n— Son çıktı —\n${rel}\n`;
  if (el.videoProbeJson) {
    el.videoProbeJson.textContent = `${String(el.videoProbeJson.textContent || "").trimEnd()}${line}`;
  }
  void loadVideoPreviewFromRel(rel, { flash: false });
  flashRuzgarDurum(`Kaydedildi ve önizlemeye yüklendi: ${rel}`);
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
  const rel = String(el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || "").trim();
  const startRaw = String(el.videoStartSec?.value ?? "0");
  const du = String(el.videoDurationSec?.value || "").trim();
  const en = String(el.videoEndSec?.value || "").trim();
  let start = parseFloat(startRaw);
  let duration = du ? parseFloat(du) : en ? parseFloat(en) - start : NaN;
  if (
    !rel &&
    canStreamEditCinema() &&
    Number.isFinite(start) &&
    Number.isFinite(duration) &&
    duration > 0
  ) {
    await runVideoTrimFromCinema({ start, end: start + duration }, { forceLocal: false });
    return;
  }

  const fd = new FormData();
  fd.append("start_sec", startRaw);
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
  setVideoJobProgress(true, "Kesim işleniyor…");
  try {
    const res = await fetch(`${API}/api/video/trim`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Kesim başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
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
  setVideoJobProgress(true, "Dönüştürülüyor…");
  try {
    const res = await fetch(`${API}/api/video/transcode`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Dönüştürme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
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
  setVideoJobProgress(true, "Dosyalar birleştiriliyor…");
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
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Birleştirme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
  }
}

async function runVideoTranscribeJob() {
  const rel = String(
    el.videoRelTranscribe?.value || el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || ""
  ).trim();
  if (!rel) {
    flashRuzgarDurum("Video/ses için göreli yol girin veya dosya açın.");
    return;
  }
  const langRaw = String(el.videoSttLang?.value || "auto").trim();
  const fd = new FormData();
  fd.append("rel", rel);
  fd.append("lang", langRaw);
  fd.append("save_srt", "true");
  flashRuzgarDurum("Konuşma metne dökülüyor… (Whisper, CPU'da uzun sürebilir)");
  setStatus("Transkript…", "Rüzgar");
  setVideoJobProgress(true, "Whisper transkript…");
  try {
    const res = await fetch(`${API}/api/video/transcribe`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Transkript başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const text = String(j.text ?? "").trim();
    if (el.videoTranscriptOut) el.videoTranscriptOut.value = text;
    if (el.videoTranscriptMeta) {
      const meta = [];
      if (j.language) meta.push(`Dil: ${j.language}`);
      if (Array.isArray(j.segments)) meta.push(`${j.segments.length} segment`);
      if (j.duration_sec != null) meta.push(`~${Math.round(j.duration_sec)} sn`);
      if (j.srt_rel) {
        meta.push(`SRT: ${j.srt_rel}`);
        if (el.videoRelBurnSub) el.videoRelBurnSub.value = j.srt_rel;
        if (el.videoRelSubTranslate) el.videoRelSubTranslate.value = j.srt_rel;
        if (el.videoRelBurnVideo && !el.videoRelBurnVideo.value) {
          el.videoRelBurnVideo.value = rel;
        }
      }
      el.videoTranscriptMeta.textContent = meta.join(" · ");
    }
    if (j.srt_rel) appendVideoJobNote(j.srt_rel);
    flashRuzgarDurum(text ? "Transkript hazır." : "Boş transkript döndü.");
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
  }
}

function copyVideoTranscriptToSes() {
  const text = String(el.videoTranscriptOut?.value || "").trim();
  if (!text) {
    flashRuzgarDurum("Önce transkript alın.");
    return;
  }
  if (el.sesTranscript) el.sesTranscript.value = text;
  switchMode("ses");
  flashRuzgarDurum("Transkript ses atölyesine aktarıldı.");
}

async function runVideoSubProcessJob() {
  const rel = String(el.videoRelSubTranslate?.value || el.videoRelBurnSub?.value || "").trim();
  if (!rel) {
    flashRuzgarDurum("Kaynak altyazı yolu girin (SRT/VTT).");
    return;
  }
  const fd = new FormData();
  fd.append("rel_sub", rel);
  fd.append("src_lang", String(el.videoSubSrcLang?.value || "auto"));
  fd.append("tgt_lang", String(el.videoSubTgtLang?.value || "tr"));
  fd.append("template", String(el.videoSubTemplate?.value || "sinema"));
  fd.append("output_format", "ass");
  flashRuzgarDurum("Altyazı çevriliyor ve ASS oluşturuluyor…");
  setStatus("Altyazı fabrikası…", "Rüzgar");
  setVideoJobProgress(true, "Altyazı S3…");
  try {
    const res = await fetch(`${API}/api/video/subtitles/process`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Altyazı işlemi başarısız"));
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) {
      if (el.videoRelBurnSub) el.videoRelBurnSub.value = out;
      appendVideoJobNote(out);
    }
    if (el.videoSubFactoryMeta) {
      el.videoSubFactoryMeta.textContent = [
        j.cue_count != null ? `${j.cue_count} satır` : "",
        j.template ? `şablon: ${j.template}` : "",
        j.target_lang ? `hedef: ${j.target_lang}` : "",
        out ? `çıktı: ${out}` : "",
      ]
        .filter(Boolean)
        .join(" · ");
    }
    flashRuzgarDurum(out ? `ASS hazır: ${out}` : "Altyazı işlendi.");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
  } finally {
    setVideoJobProgress(false);
    setStatus("Hazır", "Rüzgar");
  }
}

async function stageMediaRelFromLocalFile(file) {
  if (!file) return "";
  const fd = new FormData();
  fd.append("file", file, file.name || "media.bin");
  const res = await fetch(`${API}/api/tercume/import-file`, { method: "POST", body: fd });
  let j = {};
  try {
    j = await res.json();
  } catch {
    j = {};
  }
  if (!res.ok) {
    throw new Error(formatVideoApiError(j.detail, res, "Dosya yuklenemedi"));
  }
  return String(j.rel || "").trim();
}

async function runDubbingJob(options = {}) {
  const relInput = options.relInput || el.videoRelDub;
  const srcSelect = options.srcSelect || el.videoDubSrcLang;
  const tgtSelect = options.tgtSelect || el.videoDubTgtLang;
  const voiceSelect = options.voiceSelect || el.videoDubVoice;
  const metaEl = options.metaEl || el.videoDubMeta;
  const fileInput = options.fileInput || null;
  let rel = String(
    relInput?.value || el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || ""
  ).trim();
  if (!rel && fileInput?.files?.[0]) {
    try {
      flashRuzgarDurum("Video yukleniyor…");
      rel = await stageMediaRelFromLocalFile(fileInput.files[0]);
      if (relInput) relInput.value = rel;
    } catch (e) {
      flashRuzgarDurum(e && e.message ? e.message : String(e));
      return;
    }
  }
  if (!rel) {
    flashRuzgarDurum("Dublaj icin video goreli yolu girin veya dosya secin.");
    return;
  }
  const fd = new FormData();
  fd.append("rel", rel);
  fd.append("src_lang", String(srcSelect?.value || "auto"));
  fd.append("tgt_lang", String(tgtSelect?.value || "tr"));
  fd.append("voice", String(voiceSelect?.value || "auto"));
  fd.append("karakter", "asistan");
  flashRuzgarDurum("Dublaj basladi — STT + ceviri + TTS (uzun surebilir)…");
  setStatus("Dublaj S6…", "Rüzgar");
  setVideoJobProgress(true, "Dublaj pipeline…");
  try {
    const res = await fetch(`${API}/api/video/dub`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Dublaj basarisiz"));
      return;
    }
    const metaLine = [
      j.segment_count != null ? `${j.segment_count} segment` : "",
      j.voice_mode ? `ses: ${j.voice_mode}` : "",
      j.detected_language ? `kaynak: ${j.detected_language}` : "",
      j.target_language ? `hedef: ${j.target_language}` : "",
      j.srt_rel ? `SRT: ${j.srt_rel}` : "",
    ]
      .filter(Boolean)
      .join(" · ");
    if (metaEl) metaEl.textContent = metaLine;
    if (el.videoDubMeta && metaEl !== el.videoDubMeta) el.videoDubMeta.textContent = metaLine;
    if (el.sesDubMeta && metaEl !== el.sesDubMeta) el.sesDubMeta.textContent = metaLine;
    if (j.srt_rel && el.videoRelSubTranslate) el.videoRelSubTranslate.value = j.srt_rel;
    const out = String(j.output_rel || "").trim();
    if (out) {
      appendVideoJobNote(out);
      flashRuzgarDurum(`Dublaj hazir: ${out}`);
    } else {
      flashRuzgarDurum("Dublaj tamamlandi.");
    }
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
  } finally {
    setVideoJobProgress(false);
    setStatus("Hazır", "Rüzgar");
  }
}

async function runVideoDubJob() {
  await runDubbingJob({
    relInput: el.videoRelDub,
    srcSelect: el.videoDubSrcLang,
    tgtSelect: el.videoDubTgtLang,
    voiceSelect: el.videoDubVoice,
    metaEl: el.videoDubMeta,
  });
}

async function runSesDubJob() {
  await runDubbingJob({
    relInput: el.sesDubRel,
    srcSelect: el.sesDubSrcLang,
    tgtSelect: el.sesDubTgtLang,
    voiceSelect: el.sesDubVoice,
    metaEl: el.sesDubMeta,
    fileInput: el.sesDubFileInput,
  });
}

async function runVideoSubPipelineJob() {
  const sub = String(el.videoRelSubTranslate?.value || el.videoRelBurnSub?.value || "").trim();
  const video = String(
    el.videoRelBurnVideo?.value || el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || ""
  ).trim();
  if (!sub || !video) {
    flashRuzgarDurum("Video ve kaynak altyazı yolu gerekli.");
    return;
  }
  const fd = new FormData();
  fd.append("rel_video", video);
  fd.append("rel_sub", sub);
  fd.append("src_lang", String(el.videoSubSrcLang?.value || "auto"));
  fd.append("tgt_lang", String(el.videoSubTgtLang?.value || "tr"));
  fd.append("template", String(el.videoSubTemplate?.value || "sinema"));
  fd.append("burn", "true");
  flashRuzgarDurum("Çeviri + ASS + videoya gömme… (uzun sürebilir)");
  setStatus("Altyazı pipeline…", "Rüzgar");
  setVideoJobProgress(true, "S3 pipeline…");
  try {
    const res = await fetch(`${API}/api/video/subtitles/pipeline`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Pipeline başarısız"));
      return;
    }
    if (j.ass_rel && el.videoRelBurnSub) el.videoRelBurnSub.value = j.ass_rel;
    if (el.videoSubFactoryMeta) {
      el.videoSubFactoryMeta.textContent = [
        j.cue_count != null ? `${j.cue_count} satır` : "",
        j.ass_rel ? `ASS: ${j.ass_rel}` : "",
        j.burned_rel ? `video: ${j.burned_rel}` : "",
      ]
        .filter(Boolean)
        .join(" · ");
    }
    if (j.burned_rel) {
      appendVideoJobNote(j.burned_rel);
      flashRuzgarDurum(`Altyazılı video hazır: ${j.burned_rel}`);
    } else if (j.ass_rel) {
      appendVideoJobNote(j.ass_rel);
      flashRuzgarDurum(`ASS hazır: ${j.ass_rel}`);
    }
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
  } finally {
    setVideoJobProgress(false);
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
  setVideoJobProgress(true, "Altyazı gömülüyor…");
  try {
    const res = await fetch(`${API}/api/video/burn-subtitles`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Altyazı gömme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
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
  setVideoJobProgress(true, "Ses birleştiriliyor…");
  try {
    const res = await fetch(`${API}/api/video/mux-audio`, { method: "POST", body: fd });
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    if (!res.ok) {
      flashRuzgarDurum(formatVideoApiError(j.detail, res, "Ses birleştirme başarısız"));
      setStatus("Hazır", "Rüzgar");
      return;
    }
    const out = String(j.output_rel || "").trim();
    if (out) appendVideoJobNote(out);
    setStatus("Hazır", "Rüzgar");
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    setStatus("Hazır", "Rüzgar");
  } finally {
    setVideoJobProgress(false);
  }
}

function parseYoutubeVideoId(url) {
  const raw = normalizeYoutubeWatchUrl(url);
  if (!raw) return null;
  try {
    const parsed = new URL(raw);
    const host = parsed.hostname.replace(/^www\./i, "").toLowerCase();
    if (host === "youtu.be") {
      const id = parsed.pathname.replace(/^\//, "").split("/")[0];
      return id || null;
    }
    if (host.includes("youtube.com") || host.includes("youtube-nocookie.com")) {
      if (parsed.pathname.startsWith("/shorts/")) {
        return parsed.pathname.split("/")[2] || null;
      }
      if (parsed.pathname.startsWith("/embed/")) {
        return parsed.pathname.split("/")[2] || null;
      }
      const v = parsed.searchParams.get("v");
      if (v) return v;
    }
  } catch (_) {
    /* ignore */
  }
  const m = raw.match(/(?:[?&]v=|youtu\.be\/|\/embed\/|\/shorts\/)([a-zA-Z0-9_-]{6,})/);
  return m ? m[1] : null;
}

function normalizeYoutubeWatchUrl(url) {
  let u = String(url || "").trim().replace(/[.,);]+$/, "");
  u = u.replace(/([?&])v-([a-zA-Z0-9_-]{6,})/i, "$1v=$2");
  return u;
}

function videoPageHost(url) {
  try {
    return new URL(normalizeYoutubeWatchUrl(url)).hostname.replace(/^www\./i, "").toLowerCase();
  } catch (_) {
    return "";
  }
}

function isKnownVideoPageUrl(url) {
  const host = videoPageHost(url);
  if (host && RUZGAR_VIDEO_HOST_RE.test(host)) return true;
  try {
    const path = new URL(normalizeYoutubeWatchUrl(url)).pathname || "";
    return /\.(mp4|mkv|webm|mov|m4v|m3u8)(\?|$)/i.test(path);
  } catch (_) {
    return false;
  }
}

function prefersWebCinemaForUrl(url) {
  const host = videoPageHost(url);
  return !!(host && RUZGAR_WEB_CINEMA_HOST_RE.test(host));
}

function isRuzgarElectronShell() {
  if (window.ruzgarApi?.openExternalUrl) return true;
  return /\belectron\b/i.test(String(navigator.userAgent || ""));
}

async function openYoutubeWatchExternal(watchUrl) {
  const u = normalizeYoutubeWatchUrl(watchUrl);
  if (!u) return false;
  try {
    if (window.ruzgarApi?.openExternalUrl) {
      return !!(await window.ruzgarApi.openExternalUrl(u));
    }
  } catch (_) {
    /* ignore */
  }
  try {
    window.open(u, "_blank", "noopener,noreferrer");
    return true;
  } catch (_) {
    return false;
  }
}

function isVideoDownloadCommand(text) {
  const low = String(text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("tr-TR");
  return /\b(?:indir|download|indirme)\b/.test(low);
}

function isVideoStreamOpenCommand(text) {
  if (isVideoDownloadCommand(text)) return false;
  const url = extractVideoDownloadUrl(text) || extractVideoPageUrl(text);
  return !!url;
}

function getVideoYoutubeEmbedEl() {
  const wrap = el.videoPreview?.parentElement;
  if (!wrap) return null;
  if (!videoYoutubeEmbedEl) {
    const iframe = document.createElement("iframe");
    iframe.id = "video-youtube-embed";
    iframe.className = "video-youtube-embed";
    iframe.title = "YouTube önizleme";
    iframe.setAttribute("allowfullscreen", "");
    iframe.setAttribute(
      "allow",
      "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
    );
    iframe.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
    iframe.hidden = true;
    wrap.appendChild(iframe);
    videoYoutubeEmbedEl = iframe;
  }
  return videoYoutubeEmbedEl;
}

/** @type {HTMLDivElement|null} */
let videoYoutubeCinemaEl = null;

function getVideoYoutubeCinemaEl() {
  const wrap = el.videoPreview?.parentElement;
  if (!wrap) return null;
  if (!videoYoutubeCinemaEl) {
    const box = document.createElement("div");
    box.id = "video-youtube-cinema";
    box.className = "video-youtube-cinema";
    box.hidden = true;
    wrap.appendChild(box);
    videoYoutubeCinemaEl = box;
  }
  return videoYoutubeCinemaEl;
}

function clearYoutubeEmbedPreview() {
  if (window.ruzgarApi?.hideYoutubeCinema) {
    void window.ruzgarApi.hideYoutubeCinema();
  }
  if (youtubeBrowserViewResizeHandler) {
    window.removeEventListener("resize", youtubeBrowserViewResizeHandler);
    youtubeBrowserViewResizeHandler = null;
  }
  const iframe =
    videoYoutubeEmbedEl || document.getElementById("video-youtube-embed");
  if (iframe) {
    iframe.hidden = true;
    iframe.removeAttribute("src");
    iframe.style.display = "none";
  }
  const cinema = videoYoutubeCinemaEl || document.getElementById("video-youtube-cinema");
  if (cinema) {
    cinema.hidden = true;
    cinema.style.display = "none";
    cinema.replaceChildren();
  }
  if (el.videoPreview) {
    el.videoPreview.hidden = false;
    el.videoPreview.style.display = "";
  }
}

function hideNativeVideoPreviewForYoutube() {
  if (!el.videoPreview) return;
  try {
    if (videoPreviewObjectUrl) URL.revokeObjectURL(videoPreviewObjectUrl);
  } catch (_) {
    /* ignore */
  }
  videoPreviewObjectUrl = null;
  el.videoPreview.pause?.();
  el.videoPreview.removeAttribute("src");
  el.videoPreview.load();
  el.videoPreview.hidden = true;
  el.videoPreview.style.display = "none";
}

function loadYoutubeEmbedInPanel(watchUrl, vid, opts = {}) {
  const iframe = getVideoYoutubeEmbedEl();
  if (!iframe) return false;
  hideNativeVideoPreviewForYoutube();
  const cinema = videoYoutubeCinemaEl || document.getElementById("video-youtube-cinema");
  if (cinema) {
    cinema.hidden = true;
    cinema.style.display = "none";
  }

  const autoplay = opts.autoplay !== false ? "1" : "0";
  const origin = youtubeEmbedPageOrigin();
  const params = new URLSearchParams({
    autoplay,
    rel: "0",
    modestbranding: "1",
    playsinline: "1",
    enablejsapi: "1",
    origin,
  });
  iframe.src = `https://www.youtube.com/embed/${encodeURIComponent(vid)}?${params.toString()}`;
  iframe.hidden = false;
  iframe.style.display = "block";
  iframe.classList.add("video-preview-flash");
  window.setTimeout(() => iframe.classList.remove("video-preview-flash"), 1400);
  return true;
}

async function loadYoutubeCinemaPanel(watchUrl, vid, opts = {}) {
  const cinema = getVideoYoutubeCinemaEl();
  if (!cinema) return false;
  hideNativeVideoPreviewForYoutube();
  const iframe =
    videoYoutubeEmbedEl || document.getElementById("video-youtube-embed");
  if (iframe) {
    iframe.hidden = true;
    iframe.removeAttribute("src");
    iframe.style.display = "none";
  }

  const cleanUrl = normalizeYoutubeWatchUrl(watchUrl);
  const thumb = `https://i.ytimg.com/vi/${encodeURIComponent(vid)}/hqdefault.jpg`;
  const streamErr = String(opts.streamError || "").trim();
  const errHint = streamErr
    ? `<p class="video-youtube-cinema-hint video-youtube-cinema-err">Akış: ${streamErr.replace(/</g, "&lt;")}</p>`
    : "";
  cinema.replaceChildren();
  cinema.innerHTML =
    `<div class="video-youtube-cinema-inner">` +
    `<img class="video-youtube-cinema-thumb" src="${thumb}" alt="" loading="lazy" />` +
    `<div class="video-youtube-cinema-overlay">` +
    `<p class="video-youtube-cinema-lead">YouTube sinema</p>` +
    `<p class="video-youtube-cinema-hint">Canlı akış açılamadı. Aşağıdaki yöntemlerden birini dene.</p>` +
    errHint +
    `<div class="video-youtube-cinema-actions">` +
    `<button type="button" class="btn-primary btn-compact" data-yt-retry-stream>Akışı tekrar dene</button>` +
    `<button type="button" class="btn-secondary btn-compact" data-yt-open-browserview>Panelde gömülü aç</button>` +
    `<button type="button" class="btn-secondary btn-compact" data-yt-open-browser>Tarayıcıda izle</button>` +
    `</div>` +
    `<p class="video-youtube-cinema-foot">Kesim / yerel dosya: sohbete «<strong>indir</strong>» ekle.</p>` +
    `</div></div>`;
  cinema.hidden = false;
  cinema.style.display = "flex";
  cinema.classList.add("video-preview-flash");
  window.setTimeout(() => cinema.classList.remove("video-preview-flash"), 1400);

  cinema.querySelector("[data-yt-retry-stream]")?.addEventListener("click", () => {
    void loadPreviewInPanel(cleanUrl, { ...opts, flash: true });
  });
  cinema.querySelector("[data-yt-open-browserview]")?.addEventListener("click", () => {
    void loadWebCinemaInPanel(cleanUrl, opts);
  });
  cinema.querySelector("[data-yt-open-browser]")?.addEventListener("click", () => {
    void openYoutubeWatchExternal(cleanUrl);
  });

  if (el.videoDownloadUrl) el.videoDownloadUrl.value = cleanUrl;
  if (opts.flash !== false) {
    flashRuzgarDurum(`YouTube sinema: alternatif yöntemler (${vid})`);
  }
  return true;
}

function youtubeEmbedPageOrigin() {
  try {
    const loc = window.location;
    if (loc?.protocol && !/^file:$/i.test(loc.protocol) && loc.origin && loc.origin !== "null") {
      return loc.origin;
    }
  } catch (_) {
    /* ignore */
  }
  try {
    const root = String(window.__RUZGAR_API_ROOT__ || API || "")
      .trim()
      .replace(/\/+$/, "");
    if (root.startsWith("http")) return root;
  } catch (_) {
    /* ignore */
  }
  return "http://127.0.0.1:8779";
}

function getVideoPreviewBoundsForCinema() {
  const node =
    el.videoPreview?.closest(".video-preview-wrap") ||
    el.videoPreview?.parentElement ||
    el.videoPreview;
  if (!node) return null;
  const r = node.getBoundingClientRect();
  if (r.width < 40 || r.height < 40) return null;
  return {
    x: Math.round(r.left),
    y: Math.round(r.top),
    width: Math.round(r.width),
    height: Math.round(r.height),
  };
}

function destroyVideoHls() {
  if (videoHlsInstance) {
    try {
      videoHlsInstance.destroy();
    } catch (_) {
      /* ignore */
    }
    videoHlsInstance = null;
  }
}

async function ensureHlsJs() {
  if (window.Hls) return window.Hls;
  await new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/hls.js@1.5.17/dist/hls.min.js";
    s.onload = resolve;
    s.onerror = () => reject(new Error("hls.js yüklenemedi"));
    document.head.appendChild(s);
  });
  return window.Hls;
}

function updateCinemaNowPlaying(meta = {}) {
  cinemaNowPlaying = {
    url: String(meta.url || meta.watch_url || "").trim(),
    title: String(meta.title || "video").trim(),
    site: String(meta.site || "").trim(),
    token: String(meta.token || "").trim(),
    streamType: String(meta.streamType || meta.stream_type || "video").trim(),
    localRel: String(meta.localRel || meta.local_rel || "").trim(),
  };
  renderCinemaNowPlayingBar();
}

function renderCinemaNowPlayingBar() {
  const bar = el.videoCinemaNowPlaying;
  if (!bar) return;
  const { url, title, site, streamType, localRel } = cinemaNowPlaying;
  if (!url && !localRel) {
    bar.hidden = true;
    bar.replaceChildren();
    return;
  }
  const siteLabel = site || (url.includes("youtube") ? "YouTube" : "web");
  const modeLabel =
    streamType === "hls" ? "HLS" : localRel ? "yerel dosya" : "canlı akış";
  bar.hidden = false;
  bar.innerHTML =
    `<span class="video-cinema-now-site">${siteLabel.replace(/</g, "&lt;")}</span>` +
    `<span class="video-cinema-now-title">${title.replace(/</g, "&lt;")}</span>` +
    `<span class="video-cinema-now-mode">${modeLabel}</span>`;
}

function clearVideoSearchResults() {
  lastVideoSearchResults = [];
  const box = el.videoSearchResults;
  if (!box) return;
  box.hidden = true;
  box.replaceChildren();
}

function renderVideoSearchResults(data) {
  const box = el.videoSearchResults;
  if (!box || !data?.ok) return;
  const rows = Array.isArray(data.results) ? data.results : [];
  lastVideoSearchResults = rows;
  if (!rows.length) {
    clearVideoSearchResults();
    return;
  }
  box.hidden = false;
  box.replaceChildren();
  const lead = document.createElement("p");
  lead.className = "video-search-results-lead";
  lead.textContent = `«${data.query || "arama"}» — ${rows.length} sonuç · tıkla veya «N oynat» de`;
  box.appendChild(lead);
  rows.forEach((row, idx) => {
    const n = idx + 1;
    const card = document.createElement("article");
    card.className = "video-search-card";
    const dur =
      row.duration_sec != null && Number.isFinite(Number(row.duration_sec))
        ? `${Math.round(Number(row.duration_sec))} sn`
        : "";
    const ch = row.channel ? ` · ${row.channel}` : "";
    card.innerHTML =
      `<div class="video-search-card-main">` +
      `<span class="video-search-card-num">${n}</span>` +
      `<div class="video-search-card-text">` +
      `<strong>${String(row.title || "?").replace(/</g, "&lt;")}</strong>` +
      `<span class="video-search-card-meta">${dur}${ch.replace(/</g, "&lt;")}</span>` +
      `</div></div>` +
      `<div class="video-search-card-actions">` +
      `<button type="button" class="btn-primary btn-compact" data-watch>İzle</button>` +
      `<button type="button" class="btn-secondary btn-compact" data-dl>İndir</button>` +
      `<button type="button" class="btn-secondary btn-compact" data-trim>Kes</button>` +
      `</div>`;
    const url = String(row.url || "").trim();
    card.querySelector("[data-watch]")?.addEventListener("click", () => {
      void loadPreviewInPanel(url, { flash: true });
    });
    card.querySelector("[data-dl]")?.addEventListener("click", () => {
      if (el.videoDownloadUrl) el.videoDownloadUrl.value = url;
      void runVideoDownloadFromUrl(url, { announceChat: true });
    });
    card.querySelector("[data-trim]")?.addEventListener("click", () => {
      if (el.videoDownloadUrl) el.videoDownloadUrl.value = url;
      flashRuzgarDurum("Kesim için önce indiriliyor…");
      void runVideoDownloadFromUrl(url, { announceChat: true });
    });
    box.appendChild(card);
  });
}

async function playStreamOnVideo(streamUrl, streamType, opts = {}) {
  if (!el.videoPreview) return false;
  destroyVideoHls();
  try {
    if (videoPreviewObjectUrl) URL.revokeObjectURL(videoPreviewObjectUrl);
  } catch (_) {
    /* ignore */
  }
  videoPreviewObjectUrl = null;

  el.videoPreview.hidden = false;
  el.videoPreview.style.display = "";

  if (streamType === "hls") {
    const Hls = await ensureHlsJs();
    if (Hls.isSupported()) {
      videoHlsInstance = new Hls({ enableWorker: true });
      videoHlsInstance.loadSource(streamUrl);
      videoHlsInstance.attachMedia(el.videoPreview);
    } else if (el.videoPreview.canPlayType("application/vnd.apple.mpegurl")) {
      el.videoPreview.src = streamUrl;
      el.videoPreview.load();
    } else {
      return false;
    }
  } else {
    el.videoPreview.removeAttribute("src");
    el.videoPreview.src = streamUrl;
    el.videoPreview.load();
  }

  if (opts.autoplay !== false) {
    try {
      await el.videoPreview.play();
    } catch (_) {
      /* autoplay */
    }
  }
  el.videoPreview.classList.add("video-preview-flash");
  window.setTimeout(() => el.videoPreview.classList.remove("video-preview-flash"), 1400);
  return true;
}

async function loadStreamInPanel(watchUrl, opts = {}) {
  const cleanUrl = normalizeYoutubeWatchUrl(watchUrl);
  if (!cleanUrl || !el.videoPreview) {
    return { ok: false, error: "Oynatıcı yok" };
  }

  if (window.ruzgarApi?.hideYoutubeCinema) {
    void window.ruzgarApi.hideYoutubeCinema();
  }
  if (youtubeBrowserViewResizeHandler) {
    window.removeEventListener("resize", youtubeBrowserViewResizeHandler);
    youtubeBrowserViewResizeHandler = null;
  }

  const iframe =
    videoYoutubeEmbedEl || document.getElementById("video-youtube-embed");
  if (iframe) {
    iframe.hidden = true;
    iframe.removeAttribute("src");
    iframe.style.display = "none";
  }
  const cinema = videoYoutubeCinemaEl || document.getElementById("video-youtube-cinema");
  if (cinema) {
    cinema.hidden = true;
    cinema.style.display = "none";
    cinema.replaceChildren();
  }

  if (opts.flash !== false) {
    flashRuzgarDurum("Sinema akışı hazırlanıyor…");
  }

  const ctrl = new AbortController();
  const to = window.setTimeout(() => ctrl.abort(), 90000);
  try {
    const res = await fetch(`${API}/api/video/stream/prepare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: cleanUrl }),
      signal: ctrl.signal,
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || j.ok === false) {
      const detail = j.detail || j.error || `HTTP ${res.status}`;
      return { ok: false, error: String(detail) };
    }
    const streamPath = String(j.stream_path || "").trim();
    if (!streamPath) return { ok: false, error: "Akış yolu yok" };
    const apiRoot = String(API || "").trim().replace(/\/+$/, "");
    const streamUrl = streamPath.startsWith("http")
      ? streamPath
      : `${apiRoot}${streamPath.startsWith("/") ? streamPath : `/${streamPath}`}`;
    const streamType = String(j.stream_type || "video").trim();

    const played = await playStreamOnVideo(streamUrl, streamType, opts);
    if (!played) {
      return { ok: false, error: "Oynatıcı bu akış türünü desteklemiyor." };
    }

    if (el.videoDownloadUrl) el.videoDownloadUrl.value = cleanUrl;
    if (el.videoCinemaUrl) el.videoCinemaUrl.value = cleanUrl;
    const title = String(j.title || "video").trim();
    const site = String(j.site || "").trim();
    if (el.videoProbeJson) {
      const dur =
        j.duration_sec != null && Number.isFinite(Number(j.duration_sec))
          ? ` · ${Math.round(Number(j.duration_sec))} sn`
          : "";
      el.videoProbeJson.textContent = `Sinema akışı · ${site || "web"} · ${title}${dur}`;
    }
    updateCinemaNowPlaying({
      url: cleanUrl,
      title,
      site,
      token: j.token,
      streamType,
    });
    if (opts.flash !== false) {
      flashRuzgarDurum(`Sinema oynatıcıda: ${title}`);
    }
    return { ok: true, title, video_id: j.video_id, streamUrl, site, streamType };
  } catch (e) {
    const msg =
      e && e.name === "AbortError"
        ? "Akış hazırlama zaman aşımı"
        : String(e && e.message ? e.message : e);
    return { ok: false, error: msg };
  } finally {
    window.clearTimeout(to);
  }
}

async function loadYoutubeStreamInPanel(watchUrl, opts = {}) {
  return loadStreamInPanel(watchUrl, opts);
}

async function loadWebCinemaInPanel(pageUrl, opts = {}) {
  if (!window.ruzgarApi?.showYoutubeCinema) return false;
  const bounds = getVideoPreviewBoundsForCinema();
  if (!bounds) return false;
  const cleanUrl = normalizeYoutubeWatchUrl(pageUrl);
  if (!cleanUrl) return false;

  clearYoutubeEmbedPreview();
  hideNativeVideoPreviewForYoutube();
  destroyVideoHls();

  try {
    const out = await window.ruzgarApi.showYoutubeCinema({ url: cleanUrl, bounds });
    if (!out?.ok) return false;

    const cinema = getVideoYoutubeCinemaEl();
    if (cinema) {
      cinema.hidden = false;
      cinema.style.display = "flex";
      cinema.replaceChildren();
      cinema.innerHTML =
        `<div class="video-youtube-cinema-inner video-youtube-cinema-browserview">` +
        `<p class="video-youtube-cinema-lead">Web sinema</p>` +
        `<p class="video-youtube-cinema-hint">${cleanUrl.replace(/</g, "&lt;")}</p>` +
        `<button type="button" class="btn-secondary btn-compact" data-yt-hide-bv>Sinemayı kapat</button>` +
        `</div>`;
      cinema.querySelector("[data-yt-hide-bv]")?.addEventListener("click", () => {
        clearYoutubeEmbedPreview();
      });
    }

    if (youtubeBrowserViewResizeHandler) {
      window.removeEventListener("resize", youtubeBrowserViewResizeHandler);
    }
    youtubeBrowserViewResizeHandler = () => {
      const b = getVideoPreviewBoundsForCinema();
      if (b && window.ruzgarApi?.setYoutubeCinemaBounds) {
        void window.ruzgarApi.setYoutubeCinemaBounds(b);
      }
    };
    window.addEventListener("resize", youtubeBrowserViewResizeHandler);

    if (el.videoDownloadUrl) el.videoDownloadUrl.value = cleanUrl;
    if (el.videoCinemaUrl) el.videoCinemaUrl.value = cleanUrl;
    updateCinemaNowPlaying({ url: cleanUrl, title: cleanUrl, site: "web", streamType: "browserview" });
    void fetch(`${API}/api/video/stream/prepare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: cleanUrl }),
    })
      .then((r) => r.json())
      .then((j) => {
        if (j && j.ok && j.token) {
          updateCinemaNowPlaying({
            url: cleanUrl,
            title: String(j.title || cleanUrl),
            site: String(j.site || "web"),
            token: j.token,
            streamType: "browserview",
          });
        }
      })
      .catch(() => {});
    if (opts.flash !== false) {
      flashRuzgarDurum("Web sayfası sinema alanında.");
    }
    return true;
  } catch (_) {
    return false;
  }
}

async function loadYoutubeBrowserViewInPanel(watchUrl, vid, opts = {}) {
  return loadWebCinemaInPanel(watchUrl, opts);
}

async function loadPreviewInPanel(watchUrl, opts = {}) {
  const cleanUrl = normalizeYoutubeWatchUrl(watchUrl);
  if (!cleanUrl || !el.videoPreview) return false;
  if (/^file:/i.test(window.location.protocol)) {
    flashRuzgarDurum(
      "Sinema oynatıcı file:// ile çalışmaz — Rüzgarı kapatıp yeniden açın (http://127.0.0.1:8779/ui).",
    );
    return false;
  }

  clearVideoSearchResults();

  if (
    isRuzgarElectronShell() &&
    window.ruzgarApi?.showYoutubeCinema &&
    prefersWebCinemaForUrl(cleanUrl) &&
    opts.forceEmbed !== true &&
    opts.preferStream !== true
  ) {
    const webFirst = await loadWebCinemaInPanel(cleanUrl, { ...opts, flash: false });
    if (webFirst) {
      if (opts.flash !== false) {
        flashRuzgarDurum("Web sinema — site panelde açıldı.");
      }
      return true;
    }
  }

  const stream = await loadStreamInPanel(cleanUrl, { ...opts, flash: false });
  if (stream.ok) {
    if (opts.flash !== false) {
      flashRuzgarDurum(`Sinema oynatıcıda: ${stream.title || cleanUrl}`);
    }
    return true;
  }

  if (isRuzgarElectronShell() && window.ruzgarApi?.showYoutubeCinema && opts.forceEmbed !== true) {
    const bv = await loadWebCinemaInPanel(cleanUrl, { ...opts, flash: false });
    if (bv) {
      if (opts.flash !== false) {
        flashRuzgarDurum("Sinema panelde (gömülü web).");
      }
      return true;
    }
  }

  const vid = parseYoutubeVideoId(cleanUrl);
  if (vid && (!isRuzgarElectronShell() || opts.forceEmbed === true)) {
    clearYoutubeEmbedPreview();
    const ok = loadYoutubeEmbedInPanel(cleanUrl, vid, opts);
    if (ok) {
      if (el.videoDownloadUrl) el.videoDownloadUrl.value = cleanUrl;
      if (opts.flash !== false) {
        flashRuzgarDurum(`Gömülü oynatıcı (${vid}). Kesim için «indir» deyin.`);
      }
      return true;
    }
  }

  if (isRuzgarElectronShell()) {
    return loadYoutubeCinemaPanel(cleanUrl, vid || "web", {
      ...opts,
      streamError: stream.error,
    });
  }

  if (opts.flash !== false && stream.error) {
    flashRuzgarDurum(`Akış açılamadı: ${stream.error}`);
  }
  return false;
}

async function loadYoutubePreviewInPanel(watchUrl, opts = {}) {
  return loadPreviewInPanel(watchUrl, opts);
}

function extractVideoPageUrl(text) {
  const raw = String(text || "").trim();
  if (!raw) return null;
  const m = raw.match(RUZGAR_VIDEO_URL_RE);
  if (!m || !m[0]) return null;
  try {
    const u = new URL(m[0].replace(/[.,);]+$/, ""));
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return normalizeYoutubeWatchUrl(u.href);
  } catch (_) {
    return null;
  }
}

function extractVideoDownloadUrl(text) {
  const raw = String(text || "").trim();
  if (!raw || !RUZGAR_VIDEO_DL_HINT_RE.test(raw)) return null;
  return extractVideoPageUrl(raw);
}

async function runCinemaDownloadCurrent(opts = {}) {
  const announceChat = opts.announceChat !== false;
  const url = String(cinemaNowPlaying.url || el.videoDownloadUrl?.value || "").trim();
  const token = String(cinemaNowPlaying.token || "").trim();
  if (!url && !token) {
    const msg = "İndirilecek kaynak yok — önce sinemada bir video açın.";
    flashRuzgarDurum(msg);
    if (announceChat) appendBubble("assistant", msg, { error: true });
    return null;
  }
  setVideoJobProgress(true, "Sinema kaynağı indiriliyor… (yt-dlp)");
  if (announceChat) {
    appendBubble(
      "assistant",
      `Ümit abi, indirme başladı — **${url || "sinema kaynağı"}**\n\nBu birkaç dakika sürebilir; alttaki ilerleme çubuğunu izle.`,
    );
  }
  try {
    const res = await fetch(`${API}/api/video/stream/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, token }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || j.ok === false) {
      throw new Error(j.detail || j.result?.error || `HTTP ${res.status}`);
    }
    const result = j.result || j;
    const rel = String(result.file_path || "").trim();
    if (rel) {
      if (el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
      await loadVideoPreviewFromRel(rel);
      updateCinemaNowPlaying({
        url,
        title: result.title || cinemaNowPlaying.title,
        localRel: rel,
        streamType: "local",
      });
    }
    const okMsg = rel
      ? `Video indirildi — sinemada yerel dosya.\n\`${rel}\``
      : "İndirme tamamlandı.";
    flashRuzgarDurum(rel ? "Video indirildi — sinemada yerel dosya." : "İndirme tamamlandı.");
    if (announceChat) appendBubble("assistant", okMsg, { actionCard: true });
    return result;
  } catch (e) {
    const errText = formatClientChatError(e);
    if (url && opts.fallbackUrl !== false) {
      if (announceChat) {
        appendBubble(
          "assistant",
          `Sinema indirme başarısız (${errText}). **Doğrudan URL** ile tekrar deniyorum…`,
        );
      }
      setVideoJobProgress(true, "URL ile video indiriliyor…");
      try {
        const result = await runVideoDownloadFromUrl(url, { announceChat: false });
        const rel = String(result?.file_path || "").trim();
        if (rel) {
          if (el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
          await loadVideoPreviewFromRel(rel);
          updateCinemaNowPlaying({
            url,
            title: result.title || cinemaNowPlaying.title,
            localRel: rel,
            streamType: "local",
          });
        }
        if (announceChat) {
          appendBubble(
            "assistant",
            rel
              ? `Ümit abi, ikinci yöntemle indirildi.\n\`${rel}\``
              : "İndirme tamamlandı (yedek yol).",
            { actionCard: true },
          );
        }
        flashRuzgarDurum("Video indirildi (yedek yol).");
        return result;
      } catch (e2) {
        const msg =
          `Video indirilemedi: ${formatClientChatError(e2)}\n\n` +
          "Dailymotion bazen yt-dlp ile zor — **Web sinemada izle** veya «videodaki sesi kuran sesi yap» de (yalnızca ses referansı).";
        if (announceChat) appendBubble("assistant", msg, { error: true });
        flashRuzgarDurum("İndirme başarısız.");
        throw e2;
      }
    }
    if (announceChat) appendBubble("assistant", `İndirme başarısız: ${errText}`, { error: true });
    throw e;
  } finally {
    setVideoJobProgress(false);
  }
}

function wireCinemaHubControls() {
  if (el.btnCinemaOpenUrl?.dataset.cinemaWired === "1") return;
  if (el.btnCinemaOpenUrl) el.btnCinemaOpenUrl.dataset.cinemaWired = "1";
  if (el.btnCinemaOpenUrl) {
    el.btnCinemaOpenUrl.addEventListener("click", () => {
      const u = String(el.videoCinemaUrl?.value || el.videoDownloadUrl?.value || "").trim();
      if (!u) {
        flashRuzgarDurum("Sinema URL alanına bir adres yazın.");
        el.videoCinemaUrl?.focus();
        return;
      }
      void loadPreviewInPanel(u, { flash: true });
    });
  }
  if (el.videoCinemaUrl) {
    el.videoCinemaUrl.addEventListener("keydown", (ev) => {
      if (ev.key === "Enter") {
        ev.preventDefault();
        el.btnCinemaOpenUrl?.click();
      }
    });
  }
  if (el.btnCinemaOpenWeb) {
    el.btnCinemaOpenWeb.addEventListener("click", () => {
      const u = String(el.videoCinemaUrl?.value || el.videoDownloadUrl?.value || "").trim();
      if (!u) {
        flashRuzgarDurum("Web sinema için URL girin.");
        return;
      }
      if (!isRuzgarElectronShell()) {
        void loadPreviewInPanel(u, { flash: true });
        return;
      }
      void loadWebCinemaInPanel(u, { flash: true });
    });
  }
  if (el.btnCinemaWatchDownload) {
    el.btnCinemaWatchDownload.addEventListener("click", () => {
      void runCinemaDownloadCurrent();
    });
  }
  if (el.btnCinemaTrimReady) {
    el.btnCinemaTrimReady.addEventListener("click", () => {
      if (typeof window.RuzgarVideoAtolye?.openDock === "function") {
        window.RuzgarVideoAtolye.openDock("trim");
      }
      flashRuzgarDurum("Kesim paneli — timeline işaretlerini kullanın.");
    });
  }
  if (el.btnCinemaEditBin) {
    el.btnCinemaEditBin.addEventListener("click", () => {
      const rel = String(el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || "").trim();
      if (!rel) {
        flashRuzgarDurum("Kurgu binine eklemek için önce yerel dosya (indir veya seç).");
        return;
      }
      if (el.videoEditInsertRel) el.videoEditInsertRel.value = rel;
      if (typeof window.RuzgarVideoAtolye?.openDock === "function") {
        window.RuzgarVideoAtolye.openDock("edit");
      }
      flashRuzgarDurum("Kurgu paneli — «listeye ekle» ile devam edin.");
    });
  }
}

function isMostlyVideoDownloadCommand(text) {
  const raw = String(text || "").trim();
  if (!isVideoDownloadCommand(raw)) return false;
  const url = extractVideoDownloadUrl(raw);
  if (!url) return false;
  const rest = raw.replace(url, "").replace(RUZGAR_VIDEO_URL_RE, "").trim();
  return rest.length < 160;
}

const RUZGAR_VIDEO_SEARCH_RE =
  /(?:şu\s+filmi\s+ara|filmi\s+ara|video\s+ara|youtube\s+ara|video\s+bul|youtube\s+bul|klip\s+ara|\b(?:ara|bul)\b.*\b(?:film|video|youtube|klip)\b)/i;
const RUZGAR_VIDEO_PICK_RE =
  /(?:indir|download)\s*(?:#|no|numara)?\s*(\d{1,2})\b|(\d{1,2})\s*(?:numarayı|numarayi|nolu)\s*indir/i;
const RUZGAR_VIDEO_PICK_OPEN_RE =
  /(?:oynat|izle|aç|ac|panelde\s+aç|panelde\s+ac)\s*(?:#|no|numara)?\s*(\d{1,2})\b|(\d{1,2})\s*(?:numarayı|numarayi|nolu)\s*(?:oynat|izle|aç|ac|panelde\s+aç|panelde\s+ac)|(\d{1,2})\s*(?:numarayı|numarayi)\s*(?:panelde|sinemada)/i;

function isVideoSearchOrPickCommand(text) {
  const raw = String(text || "").trim();
  if (!raw || extractVideoDownloadUrl(raw)) return false;
  if (RUZGAR_VIDEO_PICK_RE.test(raw)) return true;
  if (RUZGAR_VIDEO_PICK_OPEN_RE.test(raw)) return true;
  return RUZGAR_VIDEO_SEARCH_RE.test(raw);
}

async function runVideoDownloadFromUrl(url, opts = {}) {
  const u = String(url || "").trim();
  if (!u) {
    throw new Error("Video URL yok.");
  }
  const announceChat = opts.announceChat !== false;
  setVideoJobProgress(true, "Video indiriliyor…");
  try {
    if (window.RuzgarVirusGuard?.runVideoDownload) {
      if (announceChat) {
        flashRuzgarDurum("Rüzgar virüs koruması: video taranıyor…");
      }
      const out = await window.RuzgarVirusGuard.runVideoDownload({
        apiBase: API,
        url: u,
        speak: speakTextImmediate,
        flash: (msg) => {
          if (announceChat) flashRuzgarDurum(msg);
        },
      });
      const raw = out.result || out;
      const rel = String(raw.file_path || out.rel || "").trim();
      return {
        ...raw,
        file_path: rel,
        title: raw.title || out.filename || "",
        ok: raw.ok !== false && out.ok !== false,
      };
    }
    const ctrl = new AbortController();
    const to = window.setTimeout(() => ctrl.abort(), RUZGAR_VIDEO_DOWNLOAD_TIMEOUT_MS);
    if (announceChat) {
      flashRuzgarDurum("Video indiriliyor… (doğrudan API)");
    }
    try {
      const res = await fetch(`${API}/api/video/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: u }),
        signal: ctrl.signal,
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || j.ok === false) {
        const detail = j.detail || j.result?.error || `HTTP ${res.status}`;
        throw new Error(formatVideoApiError(detail, res, "İndirme başarısız"));
      }
      return j.result || {};
    } finally {
      window.clearTimeout(to);
    }
  } finally {
    setVideoJobProgress(false);
  }
}

async function runVideoDownloadJob() {
  const url = String(el.videoDownloadUrl?.value || "").trim();
  if (!url) {
    flashRuzgarDurum("İndirmek için önce video URL girin.");
    el.videoDownloadUrl?.focus();
    return;
  }
  const btn = el.btnVideoDownload;
  if (btn) btn.disabled = true;
  if (el.videoDownloadStatus) {
    el.videoDownloadStatus.textContent =
      "İndiriliyor… Bu işlem video boyutuna göre sürebilir.";
  }
  try {
    const result = await runVideoDownloadFromUrl(url, { announceChat: true });
    const rel = String(result.file_path || "").trim();
    const title = String(result.title || "video").trim();
    if (el.videoDownloadStatus) {
      el.videoDownloadStatus.textContent = rel
        ? `İndirildi: ${title} · ${rel}`
        : `İndirildi: ${title}`;
    }
    if (rel) {
      if (el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
      if (el.videoEditInsertRel) el.videoEditInsertRel.value = rel;
      void loadVideoPreviewFromRel(rel);
    }
    flashRuzgarDurum("Video indirildi ve merkezi havuza kaydedildi.");
    await refreshUiManifest();
  } catch (e) {
    const msg = String(e && e.message ? e.message : e);
    if (el.videoDownloadStatus) {
      el.videoDownloadStatus.textContent = `İndirme başarısız: ${msg}`;
    }
    flashRuzgarDurum("Video indirme başarısız.");
    throw e;
  } finally {
    if (btn) btn.disabled = false;
  }
}

function clearVideoPreview() {
  clearYoutubeEmbedPreview();
  destroyVideoHls();
  clearVideoSearchResults();
  updateCinemaNowPlaying({});
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
      "Sıfırlandı. Sohbetten link verin veya «medya bilgisi» ile devam edin.";
  }
  if (el.videoRelWorkspace) el.videoRelWorkspace.value = "";
  if (el.videoRelBurnVideo) el.videoRelBurnVideo.value = "";
  if (el.videoRelBurnSub) el.videoRelBurnSub.value = "";
  if (el.videoRelMuxVideo) el.videoRelMuxVideo.value = "";
  if (el.videoRelMuxAudio) el.videoRelMuxAudio.value = "";
  if (el.videoRelSubTranslate) el.videoRelSubTranslate.value = "";
  if (el.videoRelTranscribe) el.videoRelTranscribe.value = "";
  if (el.videoRelDub) el.videoRelDub.value = "";
  if (el.videoTranscriptOut) el.videoTranscriptOut.value = "";
  if (el.videoTranscriptMeta) el.videoTranscriptMeta.textContent = "";
  if (el.videoSubFactoryMeta) el.videoSubFactoryMeta.textContent = "";
  if (el.videoDubMeta) el.videoDubMeta.textContent = "";
  resetVideoTimelineMarks();
  resetVideoTimelineProbeDuration();
  flashRuzgarDurum("Video paneli sıfırlandı.");
}

function markVideoTimelineIn() {
  el.btnVideoMarkIn?.click?.();
}

function markVideoTimelineOut() {
  el.btnVideoMarkOut?.click?.();
}

/** Sinema oturumu — sohbet süper beyin için (kopya). */
function getCinemaNowPlaying() {
  return { ...cinemaNowPlaying };
}

function hasActiveCinemaSession() {
  const c = cinemaNowPlaying;
  return !!(String(c.url || "").trim() || String(c.localRel || "").trim());
}

function getVideoPlayerCurrentTimeSec() {
  const v = el.videoPreview;
  if (!v?.src) return null;
  const t = v.currentTime;
  return Number.isFinite(t) && t >= 0 ? t : null;
}

/** HLS / yerel `<video>` — gömülü web sinemada konum okunamaz. */
function canSeekVideoPlayer() {
  if (cinemaNowPlaying.streamType === "browserview") return false;
  return getVideoPlayerCurrentTimeSec() != null;
}

/** Kesim / probe için sinemada akış oturumu var mı? */
function canStreamEditCinema() {
  const c = cinemaNowPlaying;
  return !!(String(c.token || "").trim() || String(c.url || "").trim());
}

/** Oynatılan akıştan yalnızca aralık kes — tam indirme yok. */
async function runVideoTrimFromCinema(range, opts = {}) {
  const start = Number(range?.start);
  const end = Number(range?.end);
  const duration =
    Number.isFinite(start) && Number.isFinite(end) && end > start
      ? end - start
      : Number(range?.duration);
  if (!Number.isFinite(start) || !Number.isFinite(duration) || duration <= 0) {
    flashRuzgarDurum("Geçersiz kesim aralığı.");
    return false;
  }

  const token = String(cinemaNowPlaying.token || "").trim();
  const url = String(cinemaNowPlaying.url || el.videoDownloadUrl?.value || "").trim();
  const localRel = String(el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || "").trim();

  if (canStreamEditCinema() && opts.forceLocal !== true) {
    setVideoJobProgress(true, "Akıştan kesiliyor (yalnızca seçilen bölüm)…");
    setStatus("Akış kesimi…", "Rüzgar");
    try {
      const res = await fetch(`${API}/api/video/stream/trim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: token || undefined,
          url: token ? undefined : url,
          start_sec: start,
          duration_sec: duration,
          copy_streams: false,
        }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || j.ok === false) {
        throw new Error(formatVideoApiError(j.detail, res, "Akış kesimi başarısız"));
      }
      const out = String(j.output_rel || "").trim();
      if (out) {
        if (el.videoRelWorkspace) el.videoRelWorkspace.value = out;
        if (el.videoEditInsertRel) el.videoEditInsertRel.value = out;
        appendVideoJobNote(out);
        updateCinemaNowPlaying({
          ...cinemaNowPlaying,
          localRel: out,
        });
      }
      flashRuzgarDurum("Kesim hazır — tam video indirilmedi, yalnızca istenen bölüm alındı.");
      setStatus("Hazır", "Rüzgar");
      return true;
    } catch (e) {
      flashRuzgarDurum(e && e.message ? e.message : String(e));
      setStatus("Hazır", "Rüzgar");
      return false;
    } finally {
      setVideoJobProgress(false);
    }
  }

  if (localRel) {
    if (el.videoStartSec) el.videoStartSec.value = String(start.toFixed(2));
    if (el.videoDurationSec) el.videoDurationSec.value = String(duration.toFixed(2));
    if (el.videoEndSec) el.videoEndSec.value = "";
    await runVideoTrimJob();
    return true;
  }

  flashRuzgarDurum("Sinemada video yok — önce link aç.");
  return false;
}

async function runVideoProbeFromStream() {
  const token = String(cinemaNowPlaying.token || "").trim();
  const url = String(cinemaNowPlaying.url || el.videoDownloadUrl?.value || "").trim();
  if (!token && !url) {
    flashRuzgarDurum("Sinemada akış yok.");
    return false;
  }
  setVideoJobProgress(true, "Akış analiz ediliyor…");
  try {
    const res = await fetch(`${API}/api/video/stream/probe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: token || undefined, url: token ? undefined : url }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || j.ok === false) {
      throw new Error(formatVideoApiError(j.detail, res, "Akış analizi başarısız"));
    }
    const summary = j.summary || {};
    if (el.videoProbeJson) {
      el.videoProbeJson.textContent = JSON.stringify(summary, null, 2);
    }
    const dur = summary.duration_sec != null ? Number(summary.duration_sec) : 0;
    if (dur > 0) lastVideoProbeDurationSec = dur;
    flashRuzgarDurum("Medya bilgisi — akıştan (indirme yok).");
    return true;
  } catch (e) {
    flashRuzgarDurum(e && e.message ? e.message : String(e));
    return false;
  } finally {
    setVideoJobProgress(false);
  }
}

/** Kesim / probe / mux için yerel dosya; isteğe bağlı sinemadan indirir. */
async function ensureLocalVideoSourceForEdit(opts = {}) {
  const announce = opts.announce !== false;
  let rel = String(el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || "").trim();
  if (rel) {
    if (el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
    return rel;
  }
  if (opts.allowDownload !== true) {
    return null;
  }
  const url = String(cinemaNowPlaying.url || el.videoDownloadUrl?.value || "").trim();
  const token = String(cinemaNowPlaying.token || "").trim();
  if (!url && !token) return null;
  if (announce) {
    flashRuzgarDurum("Yerel dosya gerekli — sinema kaynağı indiriliyor…");
  }
  const result = await runCinemaDownloadCurrent();
  rel = String(
    result?.file_path || el.videoRelWorkspace?.value || cinemaNowPlaying.localRel || "",
  ).trim();
  if (rel && el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
  return rel || null;
}

function initSohbetAnlama() {
  if (!window.RuzgarSohbetAnlama?.init) return;
  window.RuzgarSohbetAnlama.init({
    parseVideoTimeSec,
    getCinemaNowPlaying,
    hasActiveCinemaSession,
    extractVideoPageUrl,
    isKnownVideoPageUrl,
  });
}

function initGorselNiyet() {
  if (!window.RuzgarGorselNiyet?.init) return;
  window.RuzgarGorselNiyet.init({
    getApi: () => API,
    getCurrentMode: () => currentMode,
    appendBubble,
    setStatus,
    flash: flashRuzgarDurum,
    formatError: formatClientChatError,
    openMotorWorkbenchQuiet,
    getSharedChatHistory,
    getInputEl: () => el.input,
  });
}

function initVideoChatBrain() {
  if (!window.RuzgarVideoChatBrain?.init) return;
  window.RuzgarVideoChatBrain.init({
    getApi: () => API,
    getCurrentMode: () => currentMode,
    activeMotorChatMode,
    switchMode,
    openMotorWorkbenchQuiet,
    appendBubble,
    setStatus,
    flash: flashRuzgarDurum,
    formatClientChatError,
    formatVideoApiError,
    extractVideoDownloadUrl,
    isVideoDownloadCommand,
    isVideoStreamOpenCommand,
    isMostlyVideoDownloadCommand,
    loadYoutubePreviewInPanel,
    loadPreviewInPanel,
    loadStreamInPanel,
    loadWebCinemaInPanel,
    prefersWebCinemaForUrl,
    isKnownVideoPageUrl,
    renderVideoSearchResults,
    runCinemaDownloadCurrent,
    extractVideoPageUrl,
    loadYoutubeStreamInPanel,
    openYoutubeWatchExternal,
    isRuzgarElectronShell,
    clearYoutubeEmbedPreview,
    isVideoSearchOrPickCommand,
    parseVideoTimeSec,
    loadVideoPreviewFromRel,
    runVideoProbeFromFile,
    runVideoTrimJob,
    runVideoTrimFromCinema,
    runVideoProbeFromStream,
    canStreamEditCinema,
    runVideoTranscodeJob,
    runVideoConcatJob,
    runVideoBurnSubJob,
    runVideoMuxAudioJob,
    runVideoEditMixJob,
    runVideoCreatePlanJob,
    runVideoCreateStoryboardJob,
    runVideoCreateRenderJob,
    runVideoDownloadFromUrl,
    setVideoJobProgress,
    refreshUiManifest,
    openVideoExportFolder,
    applyRecentVideoDownload,
    clearVideoPreview,
    markVideoTimelineIn,
    markVideoTimelineOut,
    syncVideoMarksToTrim: syncVideoMarksToTrimFields,
    addCurrentTimelineSelectionToBin,
    getEl: () => el,
    getLastUiManifest: () => lastUiManifest,
    getCinemaNowPlaying,
    hasActiveCinemaSession,
    getVideoPlayerCurrentTimeSec,
    canSeekVideoPlayer,
    ensureLocalVideoSourceForEdit,
    RUZGAR_VIDEO_DOWNLOAD_TIMEOUT_MS,
    RUZGAR_VIDEO_PICK_RE,
    RUZGAR_VIDEO_PICK_OPEN_RE,
  });
}

function initAnaMotorHub() {
  if (!window.RuzgarAnaMotorHub?.init) return;
  window.RuzgarAnaMotorHub.init({
    getApi: () => API,
    isHubSseFazDEnabled,
    isHubSseFazEEnabled,
    getCurrentMode: () => currentMode,
    switchMode,
    openMotorWorkbenchQuiet,
    clearHubQuietMotor,
    appendBubble,
    setStatus,
    motorLabel: (id) => MODE_LABELS[id] || id,
    getWorkspaceRoot: async () => {
      try {
        if (window.ruzgarApi?.getRoot) return await window.ruzgarApi.getRoot();
      } catch (_) {
        /* ignore */
      }
      return null;
    },
    hasActiveCinemaSession,
    getCinemaNowPlaying,
    hasSesFileSelected: () => !!(el.audioFileInput?.files?.[0]),
    runSesSttFromFile: () => runSesSttFromFile(),
    setSesTranscript: (txt) => {
      if (el.sesTranscript) el.sesTranscript.value = String(txt || "");
    },
    speakStudioTilavetWithProfil: async (text, profil) => {
      try {
        return await speakStudioTilavet(text, { tilavetReferans: profil });
      } catch {
        return false;
      }
    },
    runHizirFromChat: (text) => {
      if (!hizirChatImpliesProductScan(text)) return false;
      if (el.hizirTaraQuery) {
        const hq = hizirQueryFromChat(text);
        if (hq) el.hizirTaraQuery.value = hq;
      }
      void HIZIR_MODU.pazarTara();
      return true;
    },
    openEylemPanel: () => window.RuzgarMotorEylemPanel?.openPanel?.(),
  });
}

function initMotorEylemPanel() {
  if (!window.RuzgarMotorEylemPanel?.init) return;
  window.RuzgarMotorEylemPanel.init({
    getApi: () => API,
    getWorkspaceRoot: async () => {
      try {
        if (window.ruzgarApi?.getRoot) return await window.ruzgarApi.getRoot();
      } catch (_) {
        /* ignore */
      }
      return null;
    },
    flash: flashRuzgarDurum,
  });
}

function wireVideoAtolye() {
  setVideoJobProgress(false);
  wireCinemaHubControls();
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
      clearVideoPreview();
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
  if (el.btnVideoTranscribe) {
    el.btnVideoTranscribe.addEventListener("click", () => {
      void runVideoTranscribeJob();
    });
  }
  if (el.btnVideoTranscriptToSes) {
    el.btnVideoTranscriptToSes.addEventListener("click", () => {
      copyVideoTranscriptToSes();
    });
  }
  if (el.btnVideoMuxAudio) {
    el.btnVideoMuxAudio.addEventListener("click", () => {
      void runVideoMuxAudioJob();
    });
  }
  if (el.btnVideoDownload) {
    el.btnVideoDownload.addEventListener("click", () => {
      void runVideoDownloadJob();
    });
  }
  if (el.videoDownloadUrl) {
    el.videoDownloadUrl.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        void runVideoDownloadJob();
      }
    });
  }
  wireVideoTimeline();
  wireVideoEditPanel();
  wireVideoCreatePanel();
  wireVideoQuickBar();
  if (window.RuzgarVideoAtolye?.init) {
    window.RuzgarVideoAtolye.init({
      flash: flashRuzgarDurum,
      openVideoExportFolder,
    });
  }
  initSohbetAnlama();
  initGorselNiyet();
  initVideoChatBrain();
}

function wireVideoQuickBar() {
  const root = el.pageVideo;
  if (!root || root.dataset.videoQuickBarWired === "1") return;
  root.dataset.videoQuickBarWired = "1";

  const openDock = (name, after) => {
    const v = window.RuzgarVideoAtolye;
    if (v?.openDuzenDock) {
      if (name && v.getActiveDock?.() === name) {
        v.closeDuzenDock();
        return true;
      }
      v.openDuzenDock(name);
      if (typeof after === "function") window.setTimeout(after, 100);
      return true;
    }
    return false;
  };

  const scrollToEl = (target) => {
    if (!target) return;
    target.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  if (el.videoQuickCreate) {
    el.videoQuickCreate.addEventListener("click", () => {
      if (openDock("create", () => el.videoCreateText?.focus?.({ preventScroll: true }))) return;
      scrollToEl(document.getElementById("video-anchor-create"));
      window.setTimeout(() => {
        el.videoCreateText?.focus?.({ preventScroll: true });
      }, 320);
      flashRuzgarDurum("Metin yazın; plan veya doğrudan video oluşturun.");
    });
  }
  if (el.videoQuickYoutube) {
    el.videoQuickYoutube.addEventListener("click", () => {
      if (openDock("download", () => el.videoDownloadUrl?.focus?.({ preventScroll: true }))) return;
      scrollToEl(document.getElementById("video-anchor-download"));
      window.setTimeout(() => {
        el.videoDownloadUrl?.focus?.({ preventScroll: true });
      }, 320);
    });
  }
  if (el.videoQuickTrim) {
    el.videoQuickTrim.addEventListener("click", () => {
      if (openDock("trim", () => el.videoStartSec?.focus?.({ preventScroll: true }))) return;
      scrollToEl(document.getElementById("video-anchor-v2"));
      window.setTimeout(() => {
        el.videoStartSec?.focus?.({ preventScroll: true });
      }, 320);
    });
  }
  if (el.videoQuickAudio) {
    el.videoQuickAudio.addEventListener("click", () => {
      if (openDock("mux", () => el.videoRelMuxVideo?.focus?.({ preventScroll: true }))) return;
      scrollToEl(document.getElementById("video-anchor-v3-mux"));
      window.setTimeout(() => {
        el.videoRelMuxVideo?.focus?.({ preventScroll: true });
      }, 320);
    });
  }
  if (el.videoQuickExport) {
    el.videoQuickExport.addEventListener("click", () => {
      openVideoExportFolder();
      flashRuzgarDurum("Çıktı klasörü açıldı (.ruzgar-video-export).");
    });
  }
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
window.okumaAtolyeRefreshTree = okumaAtolyeRefreshTree;

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
  const btnScApi = document.getElementById("btn-scaffold-api");
  const btnScSite = document.getElementById("btn-scaffold-site");
  const btnScReact = document.getElementById("btn-scaffold-react");
  if (el.progProjectSelect && el.progProjectSelect.dataset.wired !== "1") {
    el.progProjectSelect.dataset.wired = "1";
    el.progProjectSelect.addEventListener("change", () => {
      const slug = String(el.progProjectSelect.value || "").trim();
      if (slug) void switchProgramlamaProject(slug);
    });
  }
  if (btnScApi) {
    btnScApi.addEventListener("click", () => void runQuickScaffold("fastapi_api", "benim-api"));
  }
  if (btnScSite) {
    btnScSite.addEventListener("click", () => void runQuickScaffold("static_site", "vitrinim"));
  }
  if (btnScReact) {
    btnScReact.addEventListener("click", () => void runQuickScaffold("react_vite", "panelim"));
  }
  const btnScMobile = document.getElementById("btn-scaffold-mobile");
  if (btnScMobile) {
    btnScMobile.addEventListener("click", () => void runQuickScaffold("mobile_expo", "mobilim"));
  }
  const btnProjeUret = document.getElementById("btn-proje-uret");
  const btnProjeUretRun = document.getElementById("btn-proje-uret-run");
  const btnProjeUretCancel = document.getElementById("btn-proje-uret-cancel");
  if (btnProjeUret) {
    btnProjeUret.addEventListener("click", () => openProjeUretModal());
  }
  if (btnProjeUretRun) {
    btnProjeUretRun.addEventListener("click", () => void runProjeUretFromUi());
  }
  if (btnProjeUretCancel) {
    btnProjeUretCancel.addEventListener("click", () => closeProjeUretModal());
  }
  const btnPatchApply = document.getElementById("btn-patch-apply-pending");
  if (btnPatchApply) {
    btnPatchApply.addEventListener("click", () => void applyPendingPatchFromAtolye("accepted"));
  }
  const btnPatchApplyAll = document.getElementById("btn-patch-apply-all");
  if (btnPatchApplyAll) {
    btnPatchApplyAll.addEventListener("click", () => void applyPendingPatchFromAtolye("all"));
  }
  const btnPatchUnified = document.getElementById("btn-patch-unified-apply");
  if (btnPatchUnified) {
    btnPatchUnified.addEventListener("click", () => void patchUnifiedApplyFromAtolye());
  }
  const btnPatchAcceptAll = document.getElementById("btn-patch-accept-all");
  if (btnPatchAcceptAll) {
    btnPatchAcceptAll.addEventListener("click", () => void patchAcceptAllFromAtolye());
  }
  const btnPatchRollback = document.getElementById("btn-patch-rollback");
  if (btnPatchRollback) {
    btnPatchRollback.addEventListener("click", () => void rollbackPatchFromAtolye());
  }
  const btnInlineDiffClose = document.getElementById("btn-inline-diff-close");
  if (btnInlineDiffClose) {
    btnInlineDiffClose.addEventListener("click", () => hideProgramlamaInlineDiff());
  }
  const btnGitStatus = document.getElementById("btn-git-status");
  if (btnGitStatus) {
    btnGitStatus.addEventListener("click", () => void gitStatusFromAtolye());
  }
  const btnGitSuggest = document.getElementById("btn-git-commit-suggest");
  if (btnGitSuggest) {
    btnGitSuggest.addEventListener("click", () => void gitSuggestCommitFromAtolye());
  }
  const btnGitCommit = document.getElementById("btn-git-commit-apply");
  if (btnGitCommit) {
    btnGitCommit.addEventListener("click", () => void gitCommitFromAtolye());
  }
  const btnGitPrStatus = document.getElementById("btn-git-pr-status");
  if (btnGitPrStatus) {
    btnGitPrStatus.addEventListener("click", () => void gitPrStatusFromAtolye());
  }
  const btnGitPrCreate = document.getElementById("btn-git-pr-create");
  if (btnGitPrCreate) {
    btnGitPrCreate.addEventListener("click", () => void gitPrCreateFromAtolye());
  }
  const btnMegaRefactor = document.getElementById("btn-mega-refactor");
  if (btnMegaRefactor) {
    btnMegaRefactor.addEventListener("click", () => void megaRefactorFromAtolye());
  }
  const btnMegaResume = document.getElementById("btn-mega-resume");
  if (btnMegaResume) {
    btnMegaResume.addEventListener("click", () => void megaResumeFromAtolye());
  }
  const btnPrPrepare = document.getElementById("btn-pr-prepare");
  if (btnPrPrepare) {
    btnPrPrepare.addEventListener("click", () => void prPrepareFromAtolye());
  }
  const btnGitDiffPreview = document.getElementById("btn-git-diff-preview");
  if (btnGitDiffPreview) {
    btnGitDiffPreview.addEventListener("click", () => void gitDiffPreviewFromAtolye());
  }
  if (el.btnCodeOutputClear) {
    el.btnCodeOutputClear.addEventListener("click", () => setCodeOutput(""));
  }
  if (el.btnUmitOnayApply) {
    el.btnUmitOnayApply.addEventListener("click", () => {
      void sendMessageWithText("tamam yap");
      void refreshProgramlamaUmitOnay();
    });
  }
  if (el.btnUmitOnayCancel) {
    el.btnUmitOnayCancel.addEventListener("click", () => {
      void sendMessageWithText("yapma");
      void refreshProgramlamaUmitOnay();
    });
  }
}

function wireDynamicWorkbench() {
  if (el.btnLayoutFull) el.btnLayoutFull.addEventListener("click", () => setWorkbenchLayout("layout-full"));
  if (el.btnLayoutSplit2) el.btnLayoutSplit2.addEventListener("click", () => setWorkbenchLayout("layout-split2"));
  if (el.btnLayoutSplit4) el.btnLayoutSplit4.addEventListener("click", () => setWorkbenchLayout("layout-split4"));
  wireProgrammingWorkbench();
  wireOkumaAtolye();
  wireMimarAtolye();
  wireTercumeAtolye();
  wireSesAtolye();
  wireVideoAtolye();
  initAnaMotorHub();
  initMotorEylemPanel();
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
  HIZIR_MODU.wire();
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

/** Ortak sohbet paneli — tek konuşma hattı + motor başına uyanış bayrağı */
const motorChatSessions = Object.create(null);
const RUZGAR_SHARED_CHAT_KEY = "__shared__";
const RUZGAR_SHARED_CHAT_LS = "ruzgar_shared_chat_v1";

const MOTOR_CHAT_MODES = [
  "genel",
  "ses",
  "mimar",
  "okuma",
  "video",
  "tercume",
  "programlama",
  "hafiza",
  "hizir",
  "uretim",
  "gelisim",
];

function normalizeMotorChatMode(mode) {
  const m = String(mode || "genel").trim().toLowerCase();
  if (m === "hizli") return "genel";
  if (m === "okuma") return "mimar";
  return MOTOR_CHAT_MODES.includes(m) ? m : "genel";
}

/** Aktif motorun sohbet anahtarı (programlama atölyesi açıkken programlama). */
function activeMotorChatMode() {
  const onProgramlamaPage =
    el.pageProgramlama && !el.pageProgramlama.hidden;
  if (currentMode === "programlama" || onProgramlamaPage) {
    return "programlama";
  }
  return normalizeMotorChatMode(currentMode);
}

function ensureSharedChatStore() {
  if (!motorChatSessions[RUZGAR_SHARED_CHAT_KEY]) {
    motorChatSessions[RUZGAR_SHARED_CHAT_KEY] = {
      history: [],
      lastAssistantReply: "",
    };
    try {
      const raw = sessionStorage.getItem(RUZGAR_SHARED_CHAT_LS);
      if (raw) {
        const j = JSON.parse(raw);
        if (Array.isArray(j.history)) {
          motorChatSessions[RUZGAR_SHARED_CHAT_KEY].history = j.history.slice(
            -MAX_CLIENT_HISTORY_MSGS,
          );
        }
        if (j.lastAssistantReply) {
          motorChatSessions[RUZGAR_SHARED_CHAT_KEY].lastAssistantReply = String(
            j.lastAssistantReply,
          );
          lastAssistantReply = motorChatSessions[RUZGAR_SHARED_CHAT_KEY].lastAssistantReply;
        }
      }
    } catch (_) {
      /* yok say */
    }
  }
  return motorChatSessions[RUZGAR_SHARED_CHAT_KEY];
}

function getSharedChatHistory() {
  return ensureSharedChatStore().history;
}

function persistSharedChatStore() {
  const store = ensureSharedChatStore();
  try {
    sessionStorage.setItem(
      RUZGAR_SHARED_CHAT_LS,
      JSON.stringify({
        history: store.history.slice(-MAX_CLIENT_HISTORY_MSGS),
        lastAssistantReply: store.lastAssistantReply || lastAssistantReply || "",
      }),
    );
  } catch (_) {
    /* yok say */
  }
}

/** API'ye giderken son tur kullanıcı mesajı history'de varsa çift göndermeyi önle. */
function historyForApiTurn(history, currentUserText) {
  const h = Array.isArray(history) ? history.slice() : [];
  const ut = String(currentUserText || "").trim();
  if (!ut || !h.length) return h;
  const last = h[h.length - 1];
  if (last?.role === "user" && String(last.content || "").trim() === ut) {
    return h.slice(0, -1);
  }
  return h;
}

function getMotorChatSession(mode) {
  const key = normalizeMotorChatMode(mode || activeMotorChatMode());
  if (!motorChatSessions[key]) {
    motorChatSessions[key] = {
      sessionWakeUsed: false,
    };
  }
  return motorChatSessions[key];
}

/** Sohbet — son mesaj her zaman görünür (composer altında kalmaz). */
let chatScrollRaf = null;
let chatStickToBottom = true;
let chatResizeObserver = null;

function isChatNearBottom(threshold = 88) {
  if (!el.chat) return true;
  const gap = el.chat.scrollHeight - el.chat.scrollTop - el.chat.clientHeight;
  return gap <= threshold;
}

function scrollChatToBottom(opts = {}) {
  const { force = true, smooth = false } = opts;
  if (!el.chat) return;
  if (!force && !chatStickToBottom && !isChatNearBottom()) return;
  if (force) chatStickToBottom = true;
  const run = () => {
    if (!el.chat) return;
    const box = el.chat;
    box.scrollTop = box.scrollHeight;
    const last = box.querySelector(".bubble:last-of-type");
    if (last) {
      try {
        last.scrollIntoView({ block: "end", behavior: smooth ? "smooth" : "auto" });
      } catch (_) {
        /* yok say */
      }
    }
  };
  if (chatScrollRaf != null) cancelAnimationFrame(chatScrollRaf);
  chatScrollRaf = requestAnimationFrame(() => {
    chatScrollRaf = null;
    run();
    requestAnimationFrame(run);
  });
}

function wireChatAutoScroll() {
  if (!el.chat || chatResizeObserver) return;
  el.chat.addEventListener(
    "scroll",
    () => {
      chatStickToBottom = isChatNearBottom();
    },
    { passive: true },
  );
  chatResizeObserver = new ResizeObserver(() => {
    if (chatStickToBottom) scrollChatToBottom({ smooth: false });
  });
  chatResizeObserver.observe(el.chat);
}

function appendMotorAssistantBubble(text) {
  if (!el.chat) return;
  const div = document.createElement("div");
  div.className = "bubble assistant";
  const t = repairMojibake(String(text || ""));
  if (t.includes("```")) {
    div.innerHTML = renderAssistantRichHtml(t);
    wireAssistantCodeButtons(div);
  } else {
    div.innerHTML = esc(t).replace(/\n/g, "<br>");
  }
  el.chat.appendChild(div);
  scrollChatToBottom();
}

/** Motor değişince sohbet panelini o motorun oturumuna bağla */
function renderMotorChatFromSession(mode) {
  if (!el.chat) return;
  const store = ensureSharedChatStore();
  el.chat.innerHTML = "";
  clearOrchestraBridge();
  for (const msg of store.history) {
    const role = String(msg?.role || "").toLowerCase();
    const content = String(msg?.content || "");
    if (!content) continue;
    if (role === "user") {
      appendBubble("user", content, { skipSessionSync: true });
    } else {
      appendMotorAssistantBubble(content);
    }
  }
  lastAssistantReply = String(store.lastAssistantReply || "").trim();
  updateDashboardLastSpeech();
  showChatWelcomeIfEmpty();
  scrollChatToBottom();
}

let lastAssistantReply = "";

function setStatus(right, left) {
  if (right != null) el.statusR.textContent = right;
  if (left != null) el.statusL.textContent = left;
}
window.setStatus = setStatus;

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

/** Durdur / duraklat görünürlüğü: yanıt beklerken veya ses aktifken */
function syncInterruptButton() {
  const ttsBusy = isTtsActive();
  if (el.stop) el.stop.hidden = !perfBusy && !ttsBusy;
  if (el.ttsPause) {
    el.ttsPause.hidden = !ttsBusy;
    updateTtsPauseButton();
  }
  syncTtsStatusPill();
}

function pauseTtsPlayback() {
  if (!isTtsActive()) return;
  ttsPaused = true;
  try {
    if (ttsPlayingEl && !ttsPlayingEl.paused) ttsPlayingEl.pause();
  } catch (_) {
    /* yok say */
  }
  try {
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause();
    }
  } catch (_) {
    /* yok say */
  }
  syncInterruptButton();
  if (el.ttsStatusPill) {
    el.ttsStatusPill.hidden = false;
    el.ttsStatusPill.textContent = "Duraklatıldı";
  }
  setStatus("Ses duraklatıldı", "Rüzgar");
}

function resumeTtsPlayback() {
  if (!ttsPaused) return;
  ttsPaused = false;
  try {
    if (ttsPlayingEl && ttsPlayingEl.paused) void ttsPlayingEl.play();
  } catch (_) {
    /* yok say */
  }
  try {
    if (window.speechSynthesis.paused) window.speechSynthesis.resume();
  } catch (_) {
    /* yok say */
  }
  syncInterruptButton();
  setStatus("Sesli okuma…", "Rüzgar");
}

function toggleTtsPause() {
  if (ttsPaused) resumeTtsPlayback();
  else pauseTtsPlayback();
}

function interruptRuzgar() {
  if (activeChatAbort || activeChatWs) userRequestedChatStop = true;
  ttsPaused = false;
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
  renderDashboardAgentSteps([]);
  setStatus("Durduruldu", "Rüzgar");
  syncInterruptButton();
}

/** Uygulamayı kapatmadan sohbet oturumunu sıfırla */
function clearChatSession() {
  const store = ensureSharedChatStore();
  store.history = [];
  store.lastAssistantReply = "";
  for (const key of Object.keys(motorChatSessions)) {
    if (key === RUZGAR_SHARED_CHAT_KEY) continue;
    if (motorChatSessions[key]) motorChatSessions[key].sessionWakeUsed = false;
  }
  lastAssistantReply = "";
  try {
    sessionStorage.removeItem(RUZGAR_SHARED_CHAT_LS);
  } catch (_) {
    /* yok say */
  }
  el.chat.innerHTML = "";
  el.input.value = "";
  clearOrchestraBridge();
  renderDashboardAgentSteps([]);
  showChatWelcomeIfEmpty();
  setStatus("Sohbet temizlendi", "Rüzgar");
  window.setTimeout(() => setStatus("Hazır", "Rüzgar"), 1600);
}

async function refreshCurrentMotorPanel() {
  const mode = String(currentMode || "").trim().toLowerCase();
  if (mode === "hizir") {
    await refreshHizirOperasyonPanel();
    setStatus("HIZIR: bellek ve fırsat listesi güncellendi", "Rüzgar");
    return;
  }
  if (mode === "hafiza") {
    await loadHafizaJsonView();
    setStatus("Hafıza görünümü yenilendi", "Rüzgar");
    return;
  }
  if (mode === "mimar" || mode === "okuma") {
    if (window.RuzgarMimarAtolye) window.RuzgarMimarAtolye.load();
    setStatus("Mimar atölyesi yenilendi", "Rüzgar");
    return;
  }
  if (mode === "tercume") {
    if (window.RuzgarTercumeAtolye?.load) window.RuzgarTercumeAtolye.load();
    const tab = document.body.dataset.tercumeTab || "calisma";
    if (tab === "okuma") {
      await loadIlimFileList();
      setStatus("Okuma arşivi yenilendi", "Rüzgar");
    } else {
      await loadTercumeFileList();
      setStatus("Tercüme dosya listesi yenilendi", "Rüzgar");
    }
    return;
  }
  if (mode === "ses") {
    await refreshSesSttHint();
    await refreshSesDubHint();
    setStatus("Ses motoru bilgisi yenilendi", "Rüzgar");
    return;
  }
  if (mode === "video") {
    await refreshVideoEngineHint();
    setStatus("Video motoru özeti yenilendi", "Rüzgar");
    return;
  }
  if (mode === "programlama") {
    await programlamaAtolyeRefreshRoot();
    setStatus("Programlama atölyesi kökü yenilendi", "Rüzgar");
    return;
  }
  if (mode === "genel") {
    updateDynamicWorkbench();
    void refreshUiManifest();
    setStatus("Ana motor paneli güncellendi", "Rüzgar");
    return;
  }
  updateDynamicWorkbench();
  setStatus("Çalışma paneli güncellendi", "Rüzgar");
}

async function hardReloadRuzgarUi() {
  const mode = persistMotorSession();
  setStatus("Arayüz yeniden yükleniyor (önbellek temiz)…", "Rüzgar");
  let target = globalThis.location.href;
  try {
    const u = new URL(globalThis.location.href);
    u.searchParams.set("mode", mode);
    u.searchParams.set("_r", String(Date.now()));
    target = u.toString();
    globalThis.history.replaceState(null, "", target);
  } catch {
    /* ignore */
  }
  try {
    if (window.ruzgarApi?.navReload) {
      const ok = await window.ruzgarApi.navReload({ ignoreCache: true });
      if (ok) return;
    }
  } catch {
    /* tarayıcı yedek */
  }
  try {
    globalThis.location.replace(target);
  } catch {
    globalThis.location.reload();
  }
}

function wireNavToolbar() {
  if (el.navBack) {
    el.navBack.addEventListener("click", () => {
      if (motorNavGo(-1)) {
        setStatus(`Motor: ${MODE_LABELS[currentMode] || currentMode}`, "Rüzgar");
      } else {
        setStatus("Geri: motor geçmişi başında", null);
      }
    });
  }
  if (el.navForward) {
    el.navForward.addEventListener("click", () => {
      if (motorNavGo(1)) {
        setStatus(`Motor: ${MODE_LABELS[currentMode] || currentMode}`, "Rüzgar");
      } else {
        setStatus("İleri: motor geçmişi sonunda", null);
      }
    });
  }
  if (el.navRefresh) {
    el.navRefresh.addEventListener("click", async (ev) => {
      try {
        if (ev.shiftKey) {
          await refreshCurrentMotorPanel();
          return;
        }
        await hardReloadRuzgarUi();
      } catch (e) {
        const msg = e && e.message ? String(e.message) : String(e);
        setStatus(`Yenileme: ${msg.slice(0, 120)}`, null);
      }
    });
  }
  if (el.navClearChat) {
    el.navClearChat.addEventListener("click", () => clearChatSession());
  }

  document.addEventListener(
    "keydown",
    (ev) => {
      if (!(ev.ctrlKey || ev.metaKey) || ev.key.toLowerCase() !== "r") return;
      const tag = String(ev.target?.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea" || ev.target?.isContentEditable) return;
      ev.preventDefault();
      if (ev.shiftKey) void refreshCurrentMotorPanel();
      else void hardReloadRuzgarUi();
    },
    true,
  );

  globalThis.addEventListener("beforeunload", () => {
    persistMotorSession();
  });
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

function trimMotorChatHistory(store) {
  if (store.history.length > MAX_CLIENT_HISTORY_MSGS) {
    store.history = store.history.slice(-MAX_CLIENT_HISTORY_MSGS);
  }
}

function pushMotorChatHistory(role, content, opts = {}) {
  if (opts.skipSessionSync) return;
  const text = String(content || "").trim();
  if (!text) return;
  const store = ensureSharedChatStore();
  const last = store.history[store.history.length - 1];
  if (last && last.role === role && last.content === text) return;
  store.history.push({ role, content: text });
  trimMotorChatHistory(store);
  if (role === "assistant") {
    store.lastAssistantReply = text;
  }
  persistSharedChatStore();
}

function attachSourceTrustBadge(bubbleEl, card) {
  if (!bubbleEl || !card || !card.ok) return;
  const wrap = document.createElement("div");
  wrap.className = "chat-source-trust-wrap";
  const badge = document.createElement("div");
  const cls = String(card.guven_class || "trust-unknown");
  badge.className = `chat-source-trust-badge ${cls}`;
  const pill = document.createElement("span");
  pill.className = "trust-pill";
  pill.textContent = String(card.guven_label || "Güven");
  badge.appendChild(pill);
  const srcCount = Number(card.source_count || 0);
  if (srcCount > 0) {
    const src = document.createElement("span");
    src.className = "trust-sources";
    const previews = Array.isArray(card.sources_preview) ? card.sources_preview : [];
    const names = previews.map((p) => p.id || "K?").join(", ");
    src.textContent = `${srcCount} kaynak${names ? ` (${names})` : ""}`;
    badge.appendChild(src);
  } else if (card.web_used) {
    const src = document.createElement("span");
    src.className = "trust-sources";
    src.textContent = "Web kaynağı";
    badge.appendChild(src);
  }
  if (card.hint) {
    const hint = document.createElement("span");
    hint.className = "trust-hint";
    hint.textContent = String(card.hint);
    badge.appendChild(hint);
  }
  wrap.appendChild(badge);
  if (bubbleEl.parentNode) {
    bubbleEl.parentNode.insertBefore(wrap, bubbleEl.nextSibling);
  }
}

function appendBubble(role, text, opts = {}) {
  const div = document.createElement("div");
  let cls = `bubble ${role}`;
  if (role === "assistant" && opts.error) cls += " chat-error-bubble";
  if (role === "assistant" && opts.clarify) cls += " chat-clarify";
  if (role === "assistant" && opts.actionCard) cls += " chat-action-card";
  div.className = cls;
  if (role === "assistant" && opts.error) {
    div.innerHTML = renderChatErrorHtml(String(text || ""));
  } else if (role === "assistant" && opts.actionCard) {
    const raw = String(text || "").trim();
    const lines = raw.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
    const main = lines[0] || "Tamam.";
    const stepsLine = lines.find((ln) => /^Adımlar\s*:/i.test(ln));
    const confLine = lines.find((ln) => /^Güven\s*:/i.test(ln));
    const steps = stepsLine
      ? stepsLine
          .replace(/^Adımlar\s*:\s*/i, "")
          .split("→")
          .map((s) => s.trim())
          .filter(Boolean)
      : [];
    let confLabel = "";
    let confPct = "";
    if (confLine) {
      const m = confLine.match(/^Güven\s*:\s*([^(]+)\(([^)]+)\)/i);
      if (m) {
        confLabel = String(m[1] || "").trim();
        confPct = String(m[2] || "").trim();
      } else {
        confLabel = confLine.replace(/^Güven\s*:\s*/i, "").trim();
      }
    }
    const stepsHtml = steps.length
      ? `<ol class="chat-action-steps">${steps.map((s) => `<li>${esc(s)}</li>`).join("")}</ol>`
      : "";
    const confHtml = confLabel
      ? `<div class="chat-action-foot"><span class="chat-action-conf">${esc(confLabel)}</span>${
          confPct ? `<span class="chat-action-pct">${esc(confPct)}</span>` : ""
        }</div>`
      : "";
    div.innerHTML =
      `<div class="chat-action-main">${esc(main)}</div>` +
      (stepsHtml ? `<div class="chat-action-mid">${stepsHtml}</div>` : "") +
      confHtml +
      `<div class="chat-action-buttons">` +
      `<button type="button" class="btn-secondary btn-compact chat-action-btn" data-action="undo">Geri al</button>` +
      `<button type="button" class="btn-secondary btn-compact chat-action-btn" data-action="repeat">Aynısını tekrar et</button>` +
      `<button type="button" class="btn-secondary btn-compact chat-action-btn" data-action="details">Detay</button>` +
      `</div>`;
    div.addEventListener("click", (ev) => {
      const btn = ev.target.closest?.(".chat-action-btn");
      if (!btn) return;
      const action = String(btn.dataset.action || "").trim().toLowerCase();
      if (!action) return;
      if (currentMode !== "tercume" || !window.RuzgarTercumeAtolye?.runActionCardCommand) return;
      btn.disabled = true;
      Promise.resolve(window.RuzgarTercumeAtolye.runActionCardCommand(action))
        .then((hit) => {
          if (hit?.message) appendBubble("assistant", String(hit.message || ""), { actionCard: true });
        })
        .catch((e) => {
          appendBubble("assistant", String(e?.message || e || "İşlem başarısız"), { error: true });
        })
        .finally(() => {
          btn.disabled = false;
        });
    });
  } else {
    div.innerHTML = esc(text).replace(/\n/g, "<br>");
  }
  el.chat.appendChild(div);
  scrollChatToBottom({ smooth: role === "user" });
  if (role === "user") {
    pushMotorChatHistory("user", text, opts);
  }
  if (role === "assistant" && !opts.skipSessionSync) {
    const replyText = String(text || "").trim();
    if (!opts.error) {
      lastAssistantReply = replyText;
      pushMotorChatHistory("assistant", replyText, opts);
      updateDashboardLastSpeech();
    } else if (opts.clarify) {
      pushMotorChatHistory("assistant", replyText, opts);
    }
  }
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
  scrollChatToBottom();
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

const RUZGAR_CONNECTION_ACTIVE_MSG = "Rüzgar Başlatıldı - Bağlantı Aktif";

function showRuzgarConnectionActiveBanner() {
  const banner = document.getElementById("ruzgar-connection-banner");
  if (banner) {
    banner.hidden = false;
    banner.textContent = RUZGAR_CONNECTION_ACTIVE_MSG;
    banner.classList.add("is-live");
  }
  flashRuzgarDurum(RUZGAR_CONNECTION_ACTIVE_MSG, 6000);
  ruzgarDebugLog("baglanti", { aktif: true, api: API });
}

function hideRuzgarConnectionActiveBanner() {
  const banner = document.getElementById("ruzgar-connection-banner");
  if (banner) {
    banner.hidden = true;
    banner.classList.remove("is-live");
  }
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

function localApiHealthCandidates() {
  const out = [API];
  try {
    const u = new URL(API);
    const h = String(u.hostname || "").toLowerCase();
    if (h === "127.0.0.1" || h === "localhost") {
      out.push(RUZGAR_LOCAL_API_FALLBACK);
    }
  } catch (_) {
    out.push(RUZGAR_LOCAL_API_FALLBACK);
  }
  return [...new Set(out.map((x) => normalizeRuzgarApiRootTail(x)).filter(Boolean))];
}

async function checkApi() {
  const bases = localApiHealthCandidates();
  for (const base of bases) {
  try {
    const ctrl = new AbortController();
    const tid = window.setTimeout(() => ctrl.abort(), 8000);
    let r;
    try {
      r = await fetch(`${base}/api/health`, { method: "GET", signal: ctrl.signal });
    } finally {
      window.clearTimeout(tid);
    }
    const j = await r.json();
    if (base !== API && j.ok) {
      try {
        localStorage.setItem("ruzgarApi", base);
      } catch (_) {
        /* yok say */
      }
      if (!window.__ruzgarApiPortMigrated) {
        window.__ruzgarApiPortMigrated = true;
        window.location.reload();
        return true;
      }
    }
    ruzgarDebugLog("health", {
      ok: j.ok,
      gemini: j?.super_brain?.gemini_configured,
      port: base,
      build: j?.build?.rev,
      fast_paths: j?.build?.fast_paths,
    });
    if (j.ok) {
      setAnaMotorInfoStripState("ready");
      if (apiWasOffline) {
        apiWasOffline = false;
        showRuzgarConnectionActiveBanner();
      } else if (!window.__ruzgarConnectionBannerShown) {
        window.__ruzgarConnectionBannerShown = true;
        showRuzgarConnectionActiveBanner();
      }
      lastHealthSnapshot = j;
      initFazZUx();
      updateFaz7HealthStrip(j);
      const badge = document.getElementById("ana-motor-phase-badge");
      const promise = document.getElementById("ana-motor-promise");
      if (badge) {
        badge.textContent = `Ana Motor · ${j?.build?.rev || "API bağlı"}`;
      }
      if (promise) {
        promise.textContent =
          "Yerel sunucu aktif (127.0.0.1:8779). Gemini/Groq hazırsa sohbet çalışır.";
      }
      const progRev = document.getElementById("programlama-build-rev");
      const progCacheWin = document.getElementById("programlama-cache-window");
      const rev = String(j?.build?.rev || "");
      if (progRev) {
        progRev.textContent = rev || "rev bilinmiyor";
        if (rev && rev !== RUZGAR_EXPECTED_BUILD_REV) {
          progRev.style.color = "#b91c1c";
          progRev.title = `Eski sunucu! Beklenen: ${RUZGAR_EXPECTED_BUILD_REV}`;
        } else {
          progRev.style.color = "";
          progRev.title = "";
        }
      }
      if (progCacheWin) {
        const c = j?.build?.prompt_cache_v98 || {};
        const winRate = Number(c.window_hit_rate || 0);
        const winHits = Number(c.window_hits || 0);
        const winMisses = Number(c.window_misses || 0);
        const winSec = Number(c.window_sec || 300);
        const pct = Number.isFinite(winRate) ? Math.round(winRate * 100) : 0;
        progCacheWin.textContent = `%${pct} (${winHits}/${winHits + winMisses})`;
        progCacheWin.title = `Son ${winSec} sn: hit ${winHits}, miss ${winMisses}`;
      }
      renderProgramlamaP89Kpi(j?.build || {});
      showStaleBuildBanner(rev, j);
      setAnaMotorInfoStripState("ready");
      void refreshUiManifest();
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
      const am = j.ana_motor || {};
      if (am.main_only_genel_hafiza) {
        apiTitle +=
          " | UYARI: Ana Motor genel modda yalnızca hafıza JSON — LLM/RAG/web kapalı (RUZGAR_MAIN_ONLY_GENEL_HAFIZA=1 kapatın)";
        el.api.textContent = "Sunucu ⚠ hafıza-only";
      } else if (am.ollama_chat_model) {
        apiTitle += ` | Model: ${am.ollama_chat_model}`;
      }
      if (am.question_plan_enabled) {
        apiTitle += " | Soru planı açık";
      }
      el.api.title = apiTitle;
      el.api.className = "tech-chip ok";
      const sb = j.super_brain || {};
      if (sb.gemini_configured && currentMode === "genel" && el.statusR) {
        el.statusR.textContent = sb.gemini_model_default || "Gemini";
        el.statusR.title = "Süper beyin: GLOBAL_API_KEY (.env) — arka plan daemon aktif";
      } else if (am.ollama_chat_model && !am.main_only_genel_hafiza) {
        const shortModel = String(am.ollama_chat_model).split(":")[0];
        if (currentMode === "genel" && el.statusR) {
          el.statusR.textContent = shortModel;
        }
      }
      if (sb.gemini_configured) {
        apiTitle += ` | Gemini: ${sb.gemini_model_default || "gemini-2.0-flash"}`;
        if (sb.gemini_daemon?.ok) apiTitle += " (daemon bağlı)";
      }
      setStatus("Hazır", "Rüzgar");
      if (currentMode === "hizir") syncHizirWorkbenchStripVisibility();
      void tryShowHafizaReminder();
      return true;
    }
    apiWasOffline = true;
    if (faz7HealthStripEl) faz7HealthStripEl.hidden = true;
  } catch (healthErr) {
    ruzgarDebugLog("health:hata", {
      api: base,
      err: String(healthErr?.message || healthErr),
    });
    continue;
  }
  }
  apiWasOffline = true;
  hideRuzgarConnectionActiveBanner();
  lastHealthSnapshot = null;
  setAnaMotorInfoStripState("err");
  const badge = document.getElementById("ana-motor-phase-badge");
  const promise = document.getElementById("ana-motor-promise");
  if (badge) badge.textContent = "Ana Motor · sunucu kapalı";
  if (promise) {
    promise.textContent =
      "Yerel API yok. Ruzgar.ps1 veya Start-Ruzgar.ps1 ile başlatın (port 8779).";
  }
  if (faz7HealthStripEl) faz7HealthStripEl.hidden = true;
  {
    const wrap = document.getElementById("programlama-p89-kpi-card");
    if (wrap) wrap.hidden = true;
  }
  el.api.textContent = "Sunucu kapalı";
  el.api.className = "tech-chip err";
  el.api.title = "";
  if (currentMode === "hizir") setHizirWorkbenchServerPill(false, "");
  setStatus("Önce yerel sunucuyu başlatın (Ruzgar.ps1)", "Rüzgar");
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
wireMotorsCompactToggle();
wireMotorHoverTips();
wireDynamicWorkbench();
wireContextMenu();
updateDynamicWorkbench();
void initialLoadHafiza();

/** Faz F1 — txt/md/pdf tek tur bağlam yükleme */
async function uploadAnaMotorContextFile(file) {
  const name = String(file?.name || "dosya.txt");
  const ext = name.split(".").pop()?.toLowerCase() || "";
  if (!["txt", "md", "pdf"].includes(ext)) {
    setStatus("Desteklenen: .txt .md .pdf", "Rüzgar");
    return null;
  }
  const fd = new FormData();
  fd.append("file", file, name);
  if (anaMotorUploadSessionId) fd.append("session_id", anaMotorUploadSessionId);
  try {
    const res = await fetch(`${API}/api/ana-motor/upload-context`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Dosya yüklenemedi", "Rüzgar");
      return null;
    }
    if (j.session_id) anaMotorUploadSessionId = j.session_id;
    anaMotorUploadQueue.push({ id: j.upload_id, name: j.filename || name, chars: j.chars || 0 });
    const sessTxt = j.session_count ? ` · oturum ${j.session_count} dosya` : "";
    setStatus(
      `Dosya bağlamı hazır: ${j.filename || name} (${j.chars || 0} karakter)${sessTxt} — sorunu yazıp gönder`,
      "Rüzgar",
    );
    if (el.input && !el.input.value.trim()) {
      el.input.value = `Bu dosyaya göre özetle: ${j.filename || name}`;
    }
    updateAnaMotorSessionCard();
    return j;
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    return null;
  }
}

function isAnaMotorDocFile(file) {
  const name = String(file?.name || "").toLowerCase();
  return /\.(txt|md|pdf)$/.test(name);
}

function renderAnaMotorNebulaOneriCard(card) {
  const wrap = document.getElementById("ana-motor-nebula-oneri-card");
  const sumEl = document.getElementById("ana-motor-nebula-oneri-summary");
  const cmdEl = document.getElementById("ana-motor-nebula-oneri-cmd");
  const applyBtn = document.getElementById("btn-ana-nebula-oneri-apply");
  if (!wrap || !sumEl || !cmdEl) return;
  if (!card || !card.ok) {
    wrap.hidden = true;
    anaMotorLastNebulaCard = null;
    syncAnaMotorKaynakPanel();
    return;
  }
  anaMotorLastNebulaCard = card;
  wrap.hidden = false;
  sumEl.textContent =
    `Güven: ${card.guven || "düşük"} — önerilen koleksiyon: ${card.collection_title || card.collection || "—"}. ${card.hint || ""}`;
  cmdEl.textContent = card.suggested_command || "";
  if (applyBtn) applyBtn.disabled = false;
  syncAnaMotorKaynakPanel();
  const kFold = document.getElementById("ana-motor-kaynak-panel-fold");
  if (kFold && !kFold.open) kFold.open = true;
}

function updateAnaMotorSessionCard() {
  const wrap = document.getElementById("ana-motor-session-card");
  const sumEl = document.getElementById("ana-motor-session-summary");
  if (!wrap || !sumEl) return;
  const n = anaMotorUploadQueue.length;
  if (!n && !anaMotorUploadSessionId) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  sumEl.textContent =
    `${n || "?"} dosya · oturum ${anaMotorUploadSessionId ? anaMotorUploadSessionId.slice(0, 8) : "—"} — tek paket: arşiv + TTL + hafıza + Nebula`;
}

async function runAnaMotorPaketSihirbaz() {
  if (!anaMotorUploadSessionId && !anaMotorUploadQueue.length) {
    setStatus("Paket sihirbazı için dosya oturumu yok.", "Rüzgar");
    return;
  }
  const wizBtn = document.getElementById("btn-ana-paket-sihirbaz");
  const progEl = document.getElementById("ana-motor-wizard-progress");
  const card = anaMotorLastNebulaCard;
  const uploadIds = anaMotorUploadQueue.map((x) => x.id).filter(Boolean);
  const body = {
    session_id: anaMotorUploadSessionId || undefined,
    upload_ids: uploadIds.length ? uploadIds : undefined,
    topic: (card && card.topic) || anaMotorLastUserTopic || "",
    collection: (card && card.collection) || "tarih_kaynak",
    do_archive: true,
    do_remember: true,
    do_nebula: true,
    do_ttl_extend: true,
  };
  if (wizBtn) wizBtn.disabled = true;
  if (progEl) {
    progEl.hidden = false;
    progEl.textContent = "Paket sihirbazı çalışıyor…";
  }
  try {
    const res = await fetch(`${API}/api/ana-motor/paket-sihirbaz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Paket sihirbazı başarısız", "Rüzgar");
      if (progEl) progEl.textContent = j.detail || j.error || "Hata";
      return;
    }
    const steps = Array.isArray(j.steps) ? j.steps : [];
    const labels = {
      archive: "Arşiv",
      ttl_extend: "TTL",
      remember: "Hafıza",
      nebula: "Nebula",
    };
    const stepTxt = steps
      .map((s) => {
        const name = labels[s.step] || s.step || "?";
        return `${name}: ${s.ok ? "✓" : "✗"}`;
      })
      .join(" · ");
    if (progEl) progEl.textContent = stepTxt || j.hint || "Tamam";
    setStatus(j.hint || "Paket sihirbazı tamamlandı.", "Rüzgar");
    flashRuzgarDurum(`Paket — ${steps.filter((s) => s.ok).length}/${steps.length} adım`);
    if (j.summary_card) {
      renderAnaMotorPaketOzetCard(j.summary_card);
    }
    if (j.nebula_async) {
      stopAnaMotorNebulaApplyPoll();
      void pollAnaMotorNebulaApplyStatus();
      anaMotorNebulaApplyPoll = window.setInterval(() => {
        void pollAnaMotorNebulaApplyStatus();
      }, 2200);
    }
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    if (progEl) progEl.textContent = formatClientChatError(e);
  } finally {
    if (wizBtn) wizBtn.disabled = false;
  }
}

async function rememberAnaMotorUploadSession() {
  if (!anaMotorUploadSessionId && !anaMotorUploadQueue.length) {
    setStatus("Hatırlanacak dosya oturumu yok.", "Rüzgar");
    return;
  }
  const body = {
    session_id: anaMotorUploadSessionId || undefined,
    upload_ids: anaMotorUploadQueue.map((x) => x.id).filter(Boolean) || undefined,
    topic: anaMotorLastUserTopic || "",
  };
  try {
    const res = await fetch(`${API}/api/ana-motor/session/remember`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Hafızaya yazılamadı", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Dosya oturumu hafızaya kaydedildi.", "Rüzgar");
    flashRuzgarDurum(`Hafıza — ${j.file_count || "?"} dosya`);
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

function stopAnaMotorNebulaApplyPoll() {
  if (anaMotorNebulaApplyPoll != null) {
    window.clearInterval(anaMotorNebulaApplyPoll);
    anaMotorNebulaApplyPoll = null;
  }
}

function renderAnaMotorPaketOzetCard(card) {
  const wrap = document.getElementById("ana-motor-paket-ozet-card");
  const sumEl = document.getElementById("ana-motor-paket-ozet-summary");
  const stepsEl = document.getElementById("ana-motor-paket-ozet-steps");
  const nbBtn = document.getElementById("btn-ana-ozet-nebula-apply");
  if (!wrap || !sumEl || !stepsEl || !card || !card.ok) return;
  anaMotorLastPaketOzetCard = card;
  wrap.hidden = false;
  const src =
    card.source === "auto"
      ? "Otomatik"
      : card.source === "reminder"
        ? "Hatırlatıcı"
        : "Manuel";
  sumEl.textContent =
    `${src} paket — ${card.file_count || "?"} dosya · oturum ${(card.session_id || "—").slice(0, 8)} — ${card.hint || ""}`;
  stepsEl.textContent = card.steps_summary || "—";
  if (nbBtn) {
    const ready = !!(card.nebula_ready || card.collection || (card.upload_ids || []).length);
    nbBtn.hidden = !ready;
  }
  if (card.collection) {
    anaMotorLastNebulaCard = {
      ok: true,
      collection: card.collection,
      topic: card.topic || anaMotorLastUserTopic || "",
      hint: card.hint,
      upload_ids: card.upload_ids,
      session_id: card.session_id,
    };
  }
}

async function applyNebulaFromPaketOzet() {
  const card = anaMotorLastPaketOzetCard;
  if (!card || !card.ok) {
    setStatus("Paket özeti kartı yok.", "Rüzgar");
    return;
  }
  try {
    const res = await fetch(`${API}/api/ana-motor/paket-ozet/nebula-apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ summary_card: card }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Özet Nebula apply başarısız", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Nebula kuyruğa alındı.", "Rüzgar");
    flashRuzgarDurum(`Özet → Nebula ${j.collection || ""}`);
    stopAnaMotorNebulaApplyPoll();
    void pollAnaMotorNebulaApplyStatus();
    anaMotorNebulaApplyPoll = window.setInterval(() => {
      void pollAnaMotorNebulaApplyStatus();
    }, 2200);
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

function stopAnaMotorPaketAutoPoll() {
  if (anaMotorPaketAutoPoll != null) {
    window.clearInterval(anaMotorPaketAutoPoll);
    anaMotorPaketAutoPoll = null;
  }
}

async function pollAnaMotorPaketAutoStatus() {
  try {
    const res = await fetch(`${API}/api/ana-motor/paket-auto/status`);
    const j = await res.json().catch(() => ({}));
    const job = j.job || {};
    if (job.summary_card) {
      renderAnaMotorPaketOzetCard(job.summary_card);
    }
    if (j.nebula_card || job.nebula_card) {
      renderAnaMotorNebulaOneriCard(j.nebula_card || job.nebula_card);
    }
    if (!job.running) {
      stopAnaMotorPaketAutoPoll();
      if (job.summary_card) {
        flashRuzgarDurum(
          `Paket özeti — ${job.summary_card.ok_steps || "?"}/${job.summary_card.total_steps || "?"} adım`,
        );
      } else if (job.error) {
        setStatus(`Otomatik paket hatası: ${job.error}`, "Rüzgar");
      }
    }
  } catch (_) {
    /* ignore poll errors */
  }
}

function startAnaMotorPaketAutoPoll() {
  stopAnaMotorPaketAutoPoll();
  void pollAnaMotorPaketAutoStatus();
  anaMotorPaketAutoPoll = window.setInterval(() => {
    void pollAnaMotorPaketAutoStatus();
  }, 2400);
}

async function pollAnaMotorNebulaApplyStatus() {
  const progEl = document.getElementById("ana-motor-nebula-apply-progress");
  try {
    const res = await fetch(`${API}/api/ana-motor/nebula-apply/status`);
    const j = await res.json().catch(() => ({}));
    const job = j.job || {};
    if (progEl) {
      progEl.hidden = false;
      progEl.textContent = job.running
        ? `İndeks: ${job.progress || "çalışıyor…"}`
        : job.error
          ? `İndeks hatası: ${job.error}`
          : `İndeks tamam — ${job.collection || ""} (${job.chunks || "?"} parça)`;
    }
    if (!job.running) {
      stopAnaMotorNebulaApplyPoll();
      if (!job.error) {
        flashRuzgarDurum(`Nebula indeks — ${job.collection || "tamam"}`);
      }
    }
  } catch (_) {
    /* ignore poll errors */
  }
}

async function applyAnaMotorNebulaOneri() {
  const card = anaMotorLastNebulaCard;
  if (!card || !card.ok) {
    setStatus("Nebula öneri kartı yok.", "Rüzgar");
    return;
  }
  const uploadIds = anaMotorUploadQueue.map((x) => x.id).filter(Boolean);
  const body = {
    collection: card.collection || "",
    topic: card.topic || anaMotorLastUserTopic || "",
    upload_ids: uploadIds.length ? uploadIds : undefined,
    session_id: anaMotorUploadSessionId || undefined,
  };
  try {
    const res = await fetch(`${API}/api/ana-motor/nebula-oneri/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Nebula ekleme başarısız", "Rüzgar");
      return;
    }
    setStatus(j.hint || `Nebula paketi eklendi: ${j.collection}`, "Rüzgar");
    flashRuzgarDurum(`Nebula — ${j.collection} (${j.entries || 1} kayıt)`);
    if (j.async) {
      stopAnaMotorNebulaApplyPoll();
      void pollAnaMotorNebulaApplyStatus();
      anaMotorNebulaApplyPoll = window.setInterval(() => {
        void pollAnaMotorNebulaApplyStatus();
      }, 2200);
    }
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function runReminderPaketSihirbaz(reminder) {
  const action = reminder && reminder.action;
  if (!action || action.type !== "paket_sihirbaz") {
    setStatus("Hatırlatıcı aksiyonu yok.", "Rüzgar");
    return;
  }
  try {
    const res = await fetch(`${API}/api/ana-motor/reminders/paket-sihirbaz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: reminder.kind || "",
        session_id: action.session_id || undefined,
        upload_ids: action.upload_ids || undefined,
        topic: action.topic || reminder.hint || "",
        do_restore_first: !!action.do_restore_first,
      }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Hatırlatıcı paketi başarısız", "Rüzgar");
      return;
    }
    if (j.summary_card) renderAnaMotorPaketOzetCard(j.summary_card);
    if (j.nebula_card) renderAnaMotorNebulaOneriCard(j.nebula_card);
    setStatus(j.hint || "Hatırlatıcıdan paket uygulandı.", "Rüzgar");
    flashRuzgarDurum("Hatırlatıcı → tek paket");
    void refreshAnaMotorArchiveList();
    void refreshAnaMotorSessionTimeline();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

function showAnaMotorDesktopNotifications(notifications) {
  const rows = Array.isArray(notifications) ? notifications : [];
  for (const n of rows) {
    const key = `${n.kind || ""}:${n.body || ""}`;
    if (anaMotorNotifiedHintKeys.has(key)) continue;
    anaMotorNotifiedHintKeys.add(key);
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      try {
        new Notification(n.title || "Rüzgar", { body: n.body || "" });
      } catch (_) {
        flashRuzgarDurum((n.body || "").slice(0, 180));
      }
    } else if (n.severity === "warn") {
      flashRuzgarDurum((n.body || "").slice(0, 180));
    }
  }
}

function stopAnaMotorReminderNotifyPoll() {
  if (anaMotorRemindNotifyPoll != null) {
    window.clearInterval(anaMotorRemindNotifyPoll);
    anaMotorRemindNotifyPoll = null;
  }
}

function startAnaMotorReminderNotifyPoll(pollSec) {
  stopAnaMotorReminderNotifyPoll();
  if (typeof Notification !== "undefined" && Notification.permission === "default") {
    void Notification.requestPermission().catch(() => {});
  }
  const ms = Math.max(60000, Math.min(600000, Number(pollSec || 120) * 1000));
  anaMotorRemindNotifyPoll = window.setInterval(() => {
    void refreshAnaMotorArchiveReminders();
  }, ms);
}

async function loadAnaMotorUnifiedPrefs() {
  try {
    const res = await fetch(`${API}/api/ana-motor/unified-prefs`);
    const j = await res.json().catch(() => ({}));
    const p = j.prefs || {};
    const set = (id, val) => {
      const el = document.getElementById(id);
      if (!el) return;
      if (el.type === "checkbox") el.checked = !!val;
      else el.value = String(val);
    };
    set("ana-uni-desktop", p.desktop_enabled !== false);
    set("ana-uni-email", !!p.email_enabled);
    set("ana-uni-warn-only", p.warn_only !== false);
    set("ana-uni-remind-poll", p.remind_poll_sec || 120);
    set("ana-uni-sched-enabled", p.schedule_enabled !== false);
    set("ana-uni-sched-poll", p.schedule_poll_sec || 3600);
    set("ana-uni-period-days", p.period_days || 7);
    set("ana-uni-compare-email", !!p.compare_email_enabled);
    set("ana-uni-super-email", !!p.super_ozet_email_enabled);
    set("ana-uni-birlesik-email", !!p.birlesik_email_enabled);
    startAnaMotorReminderNotifyPoll(p.remind_poll_sec || 120);
  } catch (_) {
    startAnaMotorReminderNotifyPoll(120);
  }
}

async function saveAnaMotorUnifiedPrefs() {
  const body = {
    desktop_enabled: !!document.getElementById("ana-uni-desktop")?.checked,
    email_enabled: !!document.getElementById("ana-uni-email")?.checked,
    warn_only: !!document.getElementById("ana-uni-warn-only")?.checked,
    remind_poll_sec: parseInt(document.getElementById("ana-uni-remind-poll")?.value || "120", 10),
    schedule_enabled: !!document.getElementById("ana-uni-sched-enabled")?.checked,
    schedule_poll_sec: parseInt(document.getElementById("ana-uni-sched-poll")?.value || "3600", 10),
    period_days: parseInt(document.getElementById("ana-uni-period-days")?.value || "7", 10),
    compare_email_enabled: !!document.getElementById("ana-uni-compare-email")?.checked,
    super_ozet_email_enabled: !!document.getElementById("ana-uni-super-email")?.checked,
    birlesik_email_enabled: !!document.getElementById("ana-uni-birlesik-email")?.checked,
  };
  try {
    const res = await fetch(`${API}/api/ana-motor/unified-prefs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Birleşik tercihler kaydedilemedi", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Birleşik tercihler kaydedildi.", "Rüzgar");
    startAnaMotorReminderNotifyPoll(j.prefs?.remind_poll_sec || body.remind_poll_sec);
    void refreshAnaMotorArchiveReminders();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function downloadAnaMotorSuperOzetPdf() {
  try {
    const res = await fetch(`${API}/api/ana-motor/super-ozet/export-pdf?days=7`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Süper özet PDF indirilemedi", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ruzgar_ana_motor_super_ozet_7g.pdf";
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum("Süper özet PDF indirildi");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function sendAnaMotorCompareEmail() {
  try {
    const res = await fetch(`${API}/api/ana-motor/paket-history/compare/email?days=7&force=1`, {
      method: "POST",
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      setStatus(j.detail || j.error || "Karşılaştırma e-postası gönderilemedi", "Rüzgar");
      return;
    }
    if (j.sent) {
      setStatus(`Karşılaştırma raporu gönderildi: ${j.to || "e-posta"}`, "Rüzgar");
      void refreshAnaMotorNotifyHistory();
    } else {
      setStatus(j.reason || "E-posta gönderilmedi (SMTP/tercih kontrol edin).", "Rüzgar");
    }
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function sendAnaMotorSuperOzetEmail() {
  try {
    const res = await fetch(`${API}/api/ana-motor/super-ozet/email?days=7&force=1`, {
      method: "POST",
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      setStatus(j.detail || j.error || "Süper özet e-postası gönderilemedi", "Rüzgar");
      return;
    }
    if (j.sent) {
      setStatus(`Süper özet gönderildi: ${j.to || "e-posta"}`, "Rüzgar");
      void refreshAnaMotorNotifyHistory();
    } else {
      setStatus(j.reason || "E-posta gönderilmedi (SMTP/tercih kontrol edin).", "Rüzgar");
    }
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function openAnaMotorDashboardHtml() {
  try {
    const url = `${API}/api/ana-motor/dashboard/summary-html?days=7`;
    window.open(url, "_blank", "noopener,noreferrer");
    flashRuzgarDurum("Dashboard HTML açıldı");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function exportAnaMotorUnifiedPrefs() {
  try {
    const res = await fetch(`${API}/api/ana-motor/unified-prefs/export`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Tercih dışa aktarılamadı", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ruzgar_ana_motor_unified_prefs.json";
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum("Birleşik tercihler dışa aktarıldı");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function importAnaMotorUnifiedPrefs(file) {
  if (!file) return;
  try {
    const text = await file.text();
    const res = await fetch(`${API}/api/ana-motor/unified-prefs/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ json_text: text }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Tercih içe aktarılamadı", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Birleşik tercihler içe aktarıldı.", "Rüzgar");
    void loadAnaMotorUnifiedPrefs();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function sendAnaMotorBirlesikEmail() {
  try {
    const res = await fetch(`${API}/api/ana-motor/birlesik-email?days=7&force=1`, {
      method: "POST",
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      setStatus(j.detail || j.error || "Birleşik e-posta gönderilemedi", "Rüzgar");
      return;
    }
    if (j.sent) {
      setStatus(`Birleşik rapor gönderildi: ${j.to || "e-posta"}`, "Rüzgar");
      void refreshAnaMotorNotifyHistory();
    } else {
      setStatus(j.reason || "E-posta gönderilmedi (SMTP/tercih kontrol edin).", "Rüzgar");
    }
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function downloadAnaMotorDashboardPdf() {
  try {
    const res = await fetch(`${API}/api/ana-motor/dashboard/export-pdf?days=7`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Dashboard PDF indirilemedi", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ruzgar_ana_motor_dashboard_7g.pdf";
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum("Dashboard PDF indirildi");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function exportAnaMotorTamPrefs() {
  try {
    const res = await fetch(`${API}/api/ana-motor/tam-prefs/export`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Tam yedek dışa aktarılamadı", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ruzgar_ana_motor_tam_tercih_yedek.json";
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum("Tam tercih yedeği indirildi");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function importAnaMotorTamPrefs(file) {
  if (!file) return;
  try {
    const text = await file.text();
    const res = await fetch(`${API}/api/ana-motor/tam-prefs/import`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ json_text: text }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Tam geri yükleme başarısız", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Tam tercih yedeği geri yüklendi.", "Rüzgar");
    void loadAnaMotorUnifiedPrefs();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

function renderAnaMotorPaketGrafik(data) {
  const wrap = document.getElementById("ana-motor-paket-grafik");
  if (!wrap || !data || !data.summary) return;
  const s = data.summary;
  const bars = Array.isArray(data.bars) ? data.bars : [];
  if (!s.total) {
    wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const barHtml = bars
    .map(
      (b) =>
        `<div class="ana-grafik-bar" title="${b.label}: ${b.count}"><span style="height:${Math.max(4, b.pct || 0)}%"></span><em>${b.count}</em></div>`,
    )
    .join("");
  wrap.innerHTML =
    `<p class="ana-motor-card-sub">Özet: ${s.total} olay · ${s.unique_sessions || "?"} oturum · ${s.file_total || 0} dosya</p>` +
    `<div class="ana-grafik-bars">${barHtml}</div>` +
    `<p class="ana-motor-card-sub">7 gün — ${Object.entries(s.by_olay || {}).map(([k, v]) => `${k}:${v}`).join(" · ")}</p>`;
}

async function refreshAnaMotorPaketGrafik() {
  try {
    const res = await fetch(`${API}/api/ana-motor/paket-history/summary?limit=120`);
    const j = await res.json().catch(() => ({}));
    if (j.ok) renderAnaMotorPaketGrafik(j);
  } catch (_) {
    /* ignore */
  }
}

async function importAnaMotorBulkPaketCsv(file) {
  if (!file) return;
  const progEl = document.getElementById("ana-motor-archive-progress");
  if (progEl) {
    progEl.hidden = false;
    progEl.textContent = "CSV toplu paket sihirbazı…";
  }
  try {
    const text = await file.text();
    const res = await fetch(`${API}/api/ana-motor/paket-history/import-paket`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_text: text, do_restore_first: true }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "CSV toplu paket başarısız", "Rüzgar");
      if (progEl) progEl.textContent = j.detail || j.error || "Hata";
      return;
    }
    setStatus(j.hint || "CSV toplu paket tamam.", "Rüzgar");
    flashRuzgarDurum(`CSV paket — ${j.paket_count || "?"}/${j.attempted || "?"}`);
    if (progEl) progEl.textContent = j.hint || "Tamam";
    void refreshAnaMotorArchiveList();
    void refreshAnaMotorPaketGrafik();
    void refreshAnaMotorPaketAutoStatus();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    if (progEl) progEl.textContent = formatClientChatError(e);
  }
}

async function importAnaMotorPaketCsv(file) {
  if (!file) return;
  const progEl = document.getElementById("ana-motor-archive-progress");
  if (progEl) {
    progEl.hidden = false;
    progEl.textContent = "CSV toplu geri yükleme…";
  }
  try {
    const text = await file.text();
    const res = await fetch(`${API}/api/ana-motor/paket-history/import-restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_text: text }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "CSV toplu yükleme başarısız", "Rüzgar");
      if (progEl) progEl.textContent = j.detail || j.error || "Hata";
      return;
    }
    if (j.upload_ids && j.upload_ids.length) {
      anaMotorUploadQueue.length = 0;
      for (const uid of j.upload_ids) {
        anaMotorUploadQueue.push({ id: uid, name: String(uid).slice(0, 8) });
      }
      if (j.sessions && j.sessions[0]) {
        anaMotorUploadSessionId = j.sessions[0].session_id || anaMotorUploadSessionId;
      }
      updateAnaMotorSessionCard();
    }
    setStatus(j.hint || "CSV toplu geri yükleme tamam.", "Rüzgar");
    flashRuzgarDurum(`CSV restore — ${j.restored_count || "?"}/${j.attempted || "?"}`);
    if (progEl) progEl.textContent = j.hint || "Tamam";
    void refreshAnaMotorArchiveList();
    void refreshAnaMotorPaketGrafik();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    if (progEl) progEl.textContent = formatClientChatError(e);
  }
}

async function applyTimelineAction(ev, action) {
  const sid = (ev && ev.session_id) || "";
  if (!sid || !action || !action.id) return;
  try {
    const res = await fetch(`${API}/api/ana-motor/timeline/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: action.id,
        session_id: sid,
        merge_with_session_id: action.merge_with_session_id || undefined,
        topic: ev.label || "",
      }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Timeline aksiyonu başarısız", "Rüzgar");
      return;
    }
    if (j.session_id) anaMotorUploadSessionId = j.session_id;
    if (Array.isArray(j.upload_ids)) {
      anaMotorUploadQueue.length = 0;
      for (const uid of j.upload_ids) {
        anaMotorUploadQueue.push({ id: uid, name: String(uid).slice(0, 8) });
      }
    }
    updateAnaMotorSessionCard();
    if (j.summary_card) renderAnaMotorPaketOzetCard(j.summary_card);
    if (j.nebula_card) renderAnaMotorNebulaOneriCard(j.nebula_card);
    setStatus(j.hint || "Timeline aksiyonu tamam.", "Rüzgar");
    flashRuzgarDurum(`Timeline — ${action.label || action.id}`);
    void refreshAnaMotorArchiveList();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function downloadAnaMotorPaketExport(kind) {
  const paths = {
    csv: "/api/ana-motor/paket-history/export?limit=200",
    json: "/api/ana-motor/paket-history/export-json?limit=200",
    pdf: "/api/ana-motor/paket-history/export-pdf?limit=200",
  };
  const names = {
    csv: "ruzgar_ana_motor_paket_gecmisi.csv",
    json: "ruzgar_ana_motor_paket_gecmisi.json",
    pdf: "ruzgar_ana_motor_paket_gecmisi.pdf",
  };
  const path = paths[kind] || paths.csv;
  try {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || `${kind.toUpperCase()} indirilemedi`, "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = names[kind] || names.csv;
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum(`Paket geçmişi ${kind.toUpperCase()} indirildi`);
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function downloadAnaMotorPaketCsv() {
  return downloadAnaMotorPaketExport("csv");
}

async function exportAnaMotorNotifyHistory() {
  try {
    const res = await fetch(`${API}/api/ana-motor/notify-history/export?format=json&limit=200`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Bildirim geçmişi indirilemedi", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ruzgar_ana_motor_bildirim_gecmisi.json";
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum("Bildirim geçmişi dışa aktarıldı");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function clearAnaMotorNotifyHistory() {
  try {
    const res = await fetch(`${API}/api/ana-motor/notify-history/clear`, { method: "POST" });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Geçmiş temizlenemedi", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Bildirim geçmişi temizlendi.", "Rüzgar");
    void refreshAnaMotorNotifyHistory();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

function renderAnaMotorCompareChart(data) {
  const wrap = document.getElementById("ana-motor-compare-chart");
  if (!wrap || !data || !data.groups || !data.groups.length) {
    if (wrap) wrap.hidden = true;
    return;
  }
  wrap.hidden = false;
  const groups = data.groups
    .map(
      (g) =>
        `<div class="ana-compare-group" title="${g.label}: bu ${g.current} / önceki ${g.previous}">` +
        `<em>${g.label}</em>` +
        `<div class="ana-compare-pair">` +
        `<span class="ana-compare-bar ana-compare-bar--prev" style="height:${Math.max(4, g.previous_pct || 0)}%"></span>` +
        `<span class="ana-compare-bar ana-compare-bar--cur" style="height:${Math.max(4, g.current_pct || 0)}%"></span>` +
        `</div>` +
        `<small>${g.current}/${g.previous}</small>` +
        `</div>`,
    )
    .join("");
  wrap.innerHTML =
    `<p class="ana-motor-card-sub">Mavi=bu dönem · Gri=önceki (${data.period_days || 7}g)</p>` +
    `<div class="ana-compare-chart-row">${groups}</div>`;
}

async function refreshAnaMotorCompareChart() {
  try {
    const res = await fetch(`${API}/api/ana-motor/paket-history/compare/chart?days=7`);
    const j = await res.json().catch(() => ({}));
    if (j.ok) renderAnaMotorCompareChart(j);
  } catch (_) {
    /* ignore */
  }
}

async function refreshAnaMotorRememberHistory() {
  const wrap = document.getElementById("ana-motor-remember-history");
  const listEl = document.getElementById("ana-motor-remember-history-list");
  if (!wrap || !listEl) return;
  try {
    const res = await fetch(`${API}/api/ana-motor/timeline/remember/history?limit=20`);
    const j = await res.json().catch(() => ({}));
    const rows = Array.isArray(j.items) ? j.items : [];
    listEl.innerHTML = "";
    if (!rows.length) {
      wrap.hidden = true;
      return;
    }
    wrap.hidden = false;
    for (const row of rows) {
      const li = document.createElement("li");
      const when = row.ts ? new Date(row.ts * 1000).toLocaleString("tr-TR") : "";
      const mark = row.ok ? "✓" : "✗";
      li.textContent = `${when} ${mark} ${(row.session_id || "").slice(0, 8)} — ${row.topic || row.event_type || ""}`;
      listEl.appendChild(li);
    }
  } catch (_) {
    wrap.hidden = true;
  }
}

async function downloadAnaMotorCompareExport(kind) {
  const paths = {
    csv: "/api/ana-motor/paket-history/compare/export?format=csv&days=7",
    pdf: "/api/ana-motor/paket-history/compare/export-pdf?days=7",
  };
  const names = {
    csv: "ruzgar_ana_motor_karsilastirma_7g.csv",
    pdf: "ruzgar_ana_motor_karsilastirma_7g.pdf",
  };
  try {
    const res = await fetch(`${API}${paths[kind] || paths.csv}`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Karşılaştırma indirilemedi", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = names[kind] || names.csv;
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum(`Karşılaştırma ${kind.toUpperCase()} indirildi`);
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function exportAnaMotorRememberHistory() {
  try {
    const res = await fetch(`${API}/api/ana-motor/timeline/remember/history/export?format=json&limit=200`);
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      setStatus(j.detail || "Hatırla geçmişi indirilemedi", "Rüzgar");
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ruzgar_ana_motor_hatirla_gecmisi.json";
    a.click();
    URL.revokeObjectURL(url);
    flashRuzgarDurum("Hatırla geçmişi dışa aktarıldı");
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function clearAnaMotorRememberHistory() {
  try {
    const res = await fetch(`${API}/api/ana-motor/timeline/remember/history/clear`, { method: "POST" });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Hatırla geçmişi temizlenemedi", "Rüzgar");
      return;
    }
    setStatus(j.hint || "Hatırla geçmişi temizlendi.", "Rüzgar");
    void refreshAnaMotorRememberHistory();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function tickAnaMotorWeeklySchedule() {
  const hintEl = document.getElementById("ana-motor-schedule-hint");
  try {
    const res = await fetch(`${API}/api/ana-motor/sessions/weekly-summary/schedule/tick?days=7`, {
      method: "POST",
    });
    const j = await res.json().catch(() => ({}));
    if (j.desktop_notifications && j.desktop_notifications.length) {
      showAnaMotorDesktopNotifications(j.desktop_notifications);
      void refreshAnaMotorNotifyHistory();
    }
    if (hintEl && !j.skipped && j.schedule_tick) {
      hintEl.hidden = false;
      hintEl.textContent = "Zamanlayıcı: haftalık özet bildirimi gönderildi.";
    } else if (hintEl && j.skipped && j.reason === "poll_wait") {
      hintEl.hidden = false;
      hintEl.textContent = `Zamanlayıcı: sonraki kontrol ~${j.next_poll_in_sec || "?"} sn`;
    } else if (hintEl) {
      hintEl.hidden = true;
    }
  } catch (_) {
    if (hintEl) hintEl.hidden = true;
  }
}

async function refreshAnaMotorWeeklySummary() {
  const wrap = document.getElementById("ana-motor-weekly-summary");
  const titleEl = document.getElementById("ana-motor-weekly-title");
  const bodyEl = document.getElementById("ana-motor-weekly-body");
  const cmpWrap = document.getElementById("ana-motor-compare-card");
  const cmpTitle = document.getElementById("ana-motor-compare-title");
  const cmpBody = document.getElementById("ana-motor-compare-body");
  if (!wrap || !bodyEl) return;
  void tickAnaMotorWeeklySchedule();
  try {
    const res = await fetch(`${API}/api/ana-motor/sessions/weekly-summary?days=7&notify=0`);
    const j = await res.json().catch(() => ({}));
    const card = j.summary_card;
    if (!j.ok || !card) {
      wrap.hidden = true;
      return;
    }
    wrap.hidden = false;
    if (titleEl) titleEl.textContent = card.title || "Haftalık özet";
    bodyEl.textContent = card.body || "";
    const cmp = j.compare_card;
    if (cmpWrap && cmp && cmp.body) {
      cmpWrap.hidden = false;
      if (cmpTitle) cmpTitle.textContent = cmp.title || "Karşılaştırma";
      if (cmpBody) cmpBody.textContent = cmp.body || "";
      void refreshAnaMotorCompareChart();
    } else if (cmpWrap) {
      cmpWrap.hidden = true;
    }
    void refreshAnaMotorRememberHistory();
  } catch (_) {
    wrap.hidden = true;
  }
}

async function notifyAnaMotorWeeklySummary() {
  try {
    const res = await fetch(`${API}/api/ana-motor/sessions/weekly-summary/notify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ desktop: true, email: false, force: true, days: 7 }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      setStatus(j.detail || "Haftalık özet bildirimi başarısız", "Rüzgar");
      return;
    }
    if (j.desktop_notifications && j.desktop_notifications.length) {
      showAnaMotorDesktopNotifications(j.desktop_notifications);
    }
    setStatus(
      j.email_status?.sent
        ? "Haftalık özet e-posta ile gönderildi."
        : "Haftalık özet masaüstü bildirimi gönderildi.",
      "Rüzgar",
    );
    void refreshAnaMotorNotifyHistory();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
  }
}

async function batchRememberFromTimeline() {
  const progEl = document.getElementById("ana-motor-archive-progress");
  if (progEl) {
    progEl.hidden = false;
    progEl.textContent = "Timeline'dan hatırlanıyor…";
  }
  try {
    const res = await fetch(`${API}/api/ana-motor/timeline/remember/batch?limit=5`, {
      method: "POST",
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Timeline hatırla başarısız", "Rüzgar");
      if (progEl) progEl.textContent = j.detail || j.error || "Hata";
      return;
    }
    setStatus(j.hint || "Timeline oturumları hafızaya yazıldı.", "Rüzgar");
    flashRuzgarDurum(`Hatırla — ${j.remembered_count || "?"}/${j.attempted || "?"}`);
    if (progEl) progEl.textContent = j.hint || "Tamam";
    void refreshAnaMotorRememberHistory();
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    if (progEl) progEl.textContent = formatClientChatError(e);
  }
}

async function refreshAnaMotorArchiveReminders() {
  const remEl = document.getElementById("ana-motor-archive-reminders");
  if (!remEl) return;
  try {
    const res = await fetch(`${API}/api/ana-motor/archive/reminders?limit=6`);
    const j = await res.json().catch(() => ({}));
    const rows = Array.isArray(j.reminders) ? j.reminders : [];
    anaMotorLastReminders = rows;
    if (j.desktop_notifications && j.desktop_notifications.length) {
      showAnaMotorDesktopNotifications(j.desktop_notifications);
    }
    void refreshAnaMotorNotifyHistory();
    remEl.innerHTML = "";
    if (!rows.length) {
      remEl.hidden = true;
      return;
    }
    remEl.hidden = false;
    for (const row of rows) {
      const item = document.createElement("div");
      item.className = "ana-motor-remind-item";
      const txt = document.createElement("span");
      txt.textContent = row.hint || "";
      item.appendChild(txt);
      if (row.action && row.action.type === "paket_sihirbaz") {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "btn-secondary btn-compact";
        btn.textContent = "Tek paket";
        btn.addEventListener("click", () => void runReminderPaketSihirbaz(row));
        item.appendChild(btn);
      }
      remEl.appendChild(item);
    }
  } catch (_) {
    remEl.hidden = true;
  }
}

function anaMotorTimelineFilterQuery() {
  const typeEl = document.getElementById("ana-tl-filter-type");
  const sidEl = document.getElementById("ana-tl-filter-session");
  const daysEl = document.getElementById("ana-tl-filter-days");
  const qs = new URLSearchParams({ limit: "12" });
  const et = (typeEl && typeEl.value) || "";
  const sid = (sidEl && sidEl.value) || "";
  const days = daysEl && daysEl.value ? parseInt(daysEl.value, 10) : NaN;
  if (et) qs.set("event_type", et);
  if (sid.trim()) qs.set("session_id", sid.trim());
  if (!Number.isNaN(days) && days > 0) qs.set("since_days", String(days));
  return qs.toString();
}

async function refreshAnaMotorNotifyHistory() {
  const wrap = document.getElementById("ana-motor-notify-history");
  const listEl = document.getElementById("ana-motor-notify-history-list");
  if (!wrap || !listEl) return;
  try {
    const res = await fetch(`${API}/api/ana-motor/notify-history?limit=20`);
    const j = await res.json().catch(() => ({}));
    const rows = Array.isArray(j.items) ? j.items : [];
    listEl.innerHTML = "";
    if (!rows.length) {
      wrap.hidden = true;
      return;
    }
    wrap.hidden = false;
    for (const row of rows) {
      const li = document.createElement("li");
      const when = row.ts ? new Date(row.ts * 1000).toLocaleString("tr-TR") : "";
      li.textContent = `${when} · ${row.channel || "?"} — ${row.body || row.title || ""}`;
      li.className = `ana-notify-hist-${row.severity || "info"}`;
      listEl.appendChild(li);
    }
  } catch (_) {
    wrap.hidden = true;
  }
}

async function refreshAnaMotorSessionTimeline() {
  const listEl = document.getElementById("ana-motor-session-timeline");
  if (!listEl) return;
  try {
    const res = await fetch(`${API}/api/ana-motor/sessions/timeline?${anaMotorTimelineFilterQuery()}`);
    const j = await res.json().catch(() => ({}));
    const rows = Array.isArray(j.events) ? j.events : [];
    listEl.innerHTML = "";
    if (!rows.length) {
      listEl.hidden = true;
      return;
    }
    listEl.hidden = false;
    for (const ev of rows) {
      const li = document.createElement("li");
      li.className = "ana-motor-timeline-item";
      const txt = document.createElement("span");
      txt.textContent = `${ev.ts_label || ""} — ${ev.label || ev.type || "olay"}`;
      li.appendChild(txt);
      const actions = Array.isArray(ev.actions) ? ev.actions : [];
      if (actions.length) {
        const actWrap = document.createElement("span");
        actWrap.className = "ana-motor-timeline-actions";
        for (const act of actions) {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "btn-secondary btn-compact";
          btn.textContent = act.label || act.id || "?";
          btn.addEventListener("click", () => void applyTimelineAction(ev, act));
          actWrap.appendChild(btn);
        }
        li.appendChild(actWrap);
      }
      listEl.appendChild(li);
    }
  } catch (_) {
    listEl.hidden = true;
  }
}

async function refreshAnaMotorArchiveList() {
  const sel = document.getElementById("ana-motor-archive-select");
  const sumEl = document.getElementById("ana-motor-archive-summary");
  if (!sel) return;
  void refreshAnaMotorArchiveReminders();
  void refreshAnaMotorSessionTimeline();
  void refreshAnaMotorPaketGrafik();
  void refreshAnaMotorWeeklySummary();
  try {
    const res = await fetch(`${API}/api/ana-motor/archive/sessions?limit=12`);
    const j = await res.json().catch(() => ({}));
    const rows = Array.isArray(j.sessions) ? j.sessions : [];
    sel.innerHTML = "";
    if (!rows.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Arşiv oturumu yok";
      sel.appendChild(opt);
      if (sumEl) sumEl.textContent = "Henüz kalıcı arşiv yok.";
      return;
    }
    for (const row of rows) {
      const opt = document.createElement("option");
      opt.value = row.session_id || "";
      const topic = (row.topic || "—").slice(0, 40);
      opt.textContent = `${(row.session_id || "").slice(0, 8)} · ${row.file_count || 0} dosya · ${topic}`;
      sel.appendChild(opt);
    }
    if (sumEl) sumEl.textContent = `${rows.length} arşiv oturumu`;
  } catch (_) {
    if (sumEl) sumEl.textContent = "Arşiv listesi alınamadı.";
  }
}

async function restoreAnaMotorArchiveSession() {
  const sel = document.getElementById("ana-motor-archive-select");
  const progEl = document.getElementById("ana-motor-archive-progress");
  const sid = (sel && sel.value) || "";
  if (!sid) {
    setStatus("Arşiv oturumu seçin.", "Rüzgar");
    return;
  }
  if (progEl) {
    progEl.hidden = false;
    progEl.textContent = "Arşiv geri yükleniyor…";
  }
  try {
    const res = await fetch(`${API}/api/ana-motor/archive/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sid }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Arşiv yüklenemedi", "Rüzgar");
      if (progEl) progEl.textContent = j.detail || j.error || "Hata";
      return;
    }
    anaMotorUploadSessionId = j.session_id || sid;
    anaMotorUploadQueue.length = 0;
    for (const uid of j.upload_ids || []) {
      anaMotorUploadQueue.push({ id: uid, name: uid.slice(0, 8) });
    }
    updateAnaMotorSessionCard();
    if (progEl) progEl.textContent = j.hint || "Arşiv yüklendi.";
    setStatus(j.hint || "Arşiv RAG bağlamına geri yüklendi.", "Rüzgar");
    flashRuzgarDurum(`Arşiv — ${j.file_count || "?"} dosya`);
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    if (progEl) progEl.textContent = formatClientChatError(e);
  }
}

async function mergeAnaMotorArchiveSessions() {
  const sel = document.getElementById("ana-motor-archive-select");
  const progEl = document.getElementById("ana-motor-archive-progress");
  const sidB = (sel && sel.value) || "";
  const sidA = (anaMotorUploadSessionId || "").trim();
  if (!sidA || !sidB) {
    setStatus("Birleştirme için aktif oturum + arşiv seçimi gerekli.", "Rüzgar");
    return;
  }
  if (sidA === sidB) {
    setStatus("Aynı oturum iki kez seçilemez.", "Rüzgar");
    return;
  }
  if (progEl) {
    progEl.hidden = false;
    progEl.textContent = "Oturumlar birleştiriliyor…";
  }
  try {
    const res = await fetch(`${API}/api/ana-motor/sessions/merge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_ids: [sidA, sidB] }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || !j.ok) {
      setStatus(j.detail || j.error || "Birleştirme başarısız", "Rüzgar");
      if (progEl) progEl.textContent = j.detail || j.error || "Hata";
      return;
    }
    anaMotorUploadSessionId = j.session_id || sidA;
    anaMotorUploadQueue.length = 0;
    for (const uid of j.upload_ids || []) {
      anaMotorUploadQueue.push({ id: uid, name: uid.slice(0, 8) });
    }
    updateAnaMotorSessionCard();
    if (progEl) progEl.textContent = j.hint || "Birleştirildi.";
    setStatus(j.hint || "Oturumlar birleştirildi.", "Rüzgar");
    flashRuzgarDurum(`Birleşik oturum — ${j.file_count || "?"} dosya`);
    if (j.nebula_card) {
      renderAnaMotorNebulaOneriCard(j.nebula_card);
    }
  } catch (e) {
    setStatus(formatClientChatError(e), "Rüzgar");
    if (progEl) progEl.textContent = formatClientChatError(e);
  }
}

(function wireAnaMotorNebulaOneriButton() {
  const btn = document.getElementById("btn-ana-nebula-oneri-apply");
  if (btn && !btn.dataset.wired) {
    btn.dataset.wired = "1";
    btn.addEventListener("click", () => void applyAnaMotorNebulaOneri());
  }
  const wizBtn = document.getElementById("btn-ana-paket-sihirbaz");
  if (wizBtn && !wizBtn.dataset.wired) {
    wizBtn.dataset.wired = "1";
    wizBtn.addEventListener("click", () => void runAnaMotorPaketSihirbaz());
  }
  const remBtn = document.getElementById("btn-ana-session-remember");
  if (remBtn && !remBtn.dataset.wired) {
    remBtn.dataset.wired = "1";
    remBtn.addEventListener("click", () => void rememberAnaMotorUploadSession());
  }
  const arBtn = document.getElementById("btn-ana-archive-restore");
  if (arBtn && !arBtn.dataset.wired) {
    arBtn.dataset.wired = "1";
    arBtn.addEventListener("click", () => void restoreAnaMotorArchiveSession());
  }
  const mgBtn = document.getElementById("btn-ana-archive-merge");
  if (mgBtn && !mgBtn.dataset.wired) {
    mgBtn.dataset.wired = "1";
    mgBtn.addEventListener("click", () => void mergeAnaMotorArchiveSessions());
  }
  const ozNbBtn = document.getElementById("btn-ana-ozet-nebula-apply");
  if (ozNbBtn && !ozNbBtn.dataset.wired) {
    ozNbBtn.dataset.wired = "1";
    ozNbBtn.addEventListener("click", () => void applyNebulaFromPaketOzet());
  }
  const csvBtn = document.getElementById("btn-ana-paket-csv");
  if (csvBtn && !csvBtn.dataset.wired) {
    csvBtn.dataset.wired = "1";
    csvBtn.addEventListener("click", () => void downloadAnaMotorPaketCsv());
  }
  const jsonBtn = document.getElementById("btn-ana-paket-json");
  if (jsonBtn && !jsonBtn.dataset.wired) {
    jsonBtn.dataset.wired = "1";
    jsonBtn.addEventListener("click", () => void downloadAnaMotorPaketExport("json"));
  }
  const pdfBtn = document.getElementById("btn-ana-paket-pdf");
  if (pdfBtn && !pdfBtn.dataset.wired) {
    pdfBtn.dataset.wired = "1";
    pdfBtn.addEventListener("click", () => void downloadAnaMotorPaketExport("pdf"));
  }
  const notifyExpBtn = document.getElementById("btn-ana-notify-export");
  if (notifyExpBtn && !notifyExpBtn.dataset.wired) {
    notifyExpBtn.dataset.wired = "1";
    notifyExpBtn.addEventListener("click", () => void exportAnaMotorNotifyHistory());
  }
  const notifyClrBtn = document.getElementById("btn-ana-notify-clear");
  if (notifyClrBtn && !notifyClrBtn.dataset.wired) {
    notifyClrBtn.dataset.wired = "1";
    notifyClrBtn.addEventListener("click", () => void clearAnaMotorNotifyHistory());
  }
  const weeklyNotifyBtn = document.getElementById("btn-ana-weekly-notify");
  if (weeklyNotifyBtn && !weeklyNotifyBtn.dataset.wired) {
    weeklyNotifyBtn.dataset.wired = "1";
    weeklyNotifyBtn.addEventListener("click", () => void notifyAnaMotorWeeklySummary());
  }
  const tlRememberBtn = document.getElementById("btn-ana-timeline-remember");
  if (tlRememberBtn && !tlRememberBtn.dataset.wired) {
    tlRememberBtn.dataset.wired = "1";
    tlRememberBtn.addEventListener("click", () => void batchRememberFromTimeline());
  }
  const rememberClrBtn = document.getElementById("btn-ana-remember-clear");
  if (rememberClrBtn && !rememberClrBtn.dataset.wired) {
    rememberClrBtn.dataset.wired = "1";
    rememberClrBtn.addEventListener("click", () => void clearAnaMotorRememberHistory());
  }
  const rememberExpBtn = document.getElementById("btn-ana-remember-export");
  if (rememberExpBtn && !rememberExpBtn.dataset.wired) {
    rememberExpBtn.dataset.wired = "1";
    rememberExpBtn.addEventListener("click", () => void exportAnaMotorRememberHistory());
  }
  const cmpCsvBtn = document.getElementById("btn-ana-compare-csv");
  if (cmpCsvBtn && !cmpCsvBtn.dataset.wired) {
    cmpCsvBtn.dataset.wired = "1";
    cmpCsvBtn.addEventListener("click", () => void downloadAnaMotorCompareExport("csv"));
  }
  const cmpPdfBtn = document.getElementById("btn-ana-compare-pdf");
  if (cmpPdfBtn && !cmpPdfBtn.dataset.wired) {
    cmpPdfBtn.dataset.wired = "1";
    cmpPdfBtn.addEventListener("click", () => void downloadAnaMotorCompareExport("pdf"));
  }
  const unifiedPrefBtn = document.getElementById("btn-ana-unified-prefs-save");
  if (unifiedPrefBtn && !unifiedPrefBtn.dataset.wired) {
    unifiedPrefBtn.dataset.wired = "1";
    unifiedPrefBtn.addEventListener("click", () => void saveAnaMotorUnifiedPrefs());
  }
  const superPdfBtn = document.getElementById("btn-ana-super-ozet-pdf");
  if (superPdfBtn && !superPdfBtn.dataset.wired) {
    superPdfBtn.dataset.wired = "1";
    superPdfBtn.addEventListener("click", () => void downloadAnaMotorSuperOzetPdf());
  }
  const cmpEmailBtn = document.getElementById("btn-ana-compare-email");
  if (cmpEmailBtn && !cmpEmailBtn.dataset.wired) {
    cmpEmailBtn.dataset.wired = "1";
    cmpEmailBtn.addEventListener("click", () => void sendAnaMotorCompareEmail());
  }
  const superEmailBtn = document.getElementById("btn-ana-super-ozet-email");
  if (superEmailBtn && !superEmailBtn.dataset.wired) {
    superEmailBtn.dataset.wired = "1";
    superEmailBtn.addEventListener("click", () => void sendAnaMotorSuperOzetEmail());
  }
  const dashHtmlBtn = document.getElementById("btn-ana-dashboard-html");
  if (dashHtmlBtn && !dashHtmlBtn.dataset.wired) {
    dashHtmlBtn.dataset.wired = "1";
    dashHtmlBtn.addEventListener("click", () => void openAnaMotorDashboardHtml());
  }
  const unifiedExportBtn = document.getElementById("btn-ana-unified-prefs-export");
  if (unifiedExportBtn && !unifiedExportBtn.dataset.wired) {
    unifiedExportBtn.dataset.wired = "1";
    unifiedExportBtn.addEventListener("click", () => void exportAnaMotorUnifiedPrefs());
  }
  const unifiedImportIn = document.getElementById("ana-unified-prefs-import");
  if (unifiedImportIn && !unifiedImportIn.dataset.wired) {
    unifiedImportIn.dataset.wired = "1";
    unifiedImportIn.addEventListener("change", () => {
      const f = unifiedImportIn.files && unifiedImportIn.files[0];
      void importAnaMotorUnifiedPrefs(f);
      unifiedImportIn.value = "";
    });
  }
  const birlesikEmailBtn = document.getElementById("btn-ana-birlesik-email");
  if (birlesikEmailBtn && !birlesikEmailBtn.dataset.wired) {
    birlesikEmailBtn.dataset.wired = "1";
    birlesikEmailBtn.addEventListener("click", () => void sendAnaMotorBirlesikEmail());
  }
  const dashPdfBtn = document.getElementById("btn-ana-dashboard-pdf");
  if (dashPdfBtn && !dashPdfBtn.dataset.wired) {
    dashPdfBtn.dataset.wired = "1";
    dashPdfBtn.addEventListener("click", () => void downloadAnaMotorDashboardPdf());
  }
  const tamExportBtn = document.getElementById("btn-ana-tam-prefs-export");
  if (tamExportBtn && !tamExportBtn.dataset.wired) {
    tamExportBtn.dataset.wired = "1";
    tamExportBtn.addEventListener("click", () => void exportAnaMotorTamPrefs());
  }
  const tamImportIn = document.getElementById("ana-tam-prefs-import");
  if (tamImportIn && !tamImportIn.dataset.wired) {
    tamImportIn.dataset.wired = "1";
    tamImportIn.addEventListener("change", () => {
      const f = tamImportIn.files && tamImportIn.files[0];
      void importAnaMotorTamPrefs(f);
      tamImportIn.value = "";
    });
  }
  const csvIn = document.getElementById("ana-csv-import-input");
  if (csvIn && !csvIn.dataset.wired) {
    csvIn.dataset.wired = "1";
    csvIn.addEventListener("change", () => {
      const f = csvIn.files && csvIn.files[0];
      void importAnaMotorPaketCsv(f);
      csvIn.value = "";
    });
  }
  const csvPaketIn = document.getElementById("ana-csv-paket-input");
  if (csvPaketIn && !csvPaketIn.dataset.wired) {
    csvPaketIn.dataset.wired = "1";
    csvPaketIn.addEventListener("change", () => {
      const f = csvPaketIn.files && csvPaketIn.files[0];
      void importAnaMotorBulkPaketCsv(f);
      csvPaketIn.value = "";
    });
  }
  const tlFilterBtn = document.getElementById("btn-ana-tl-filter-apply");
  if (tlFilterBtn && !tlFilterBtn.dataset.wired) {
    tlFilterBtn.dataset.wired = "1";
    tlFilterBtn.addEventListener("click", () => void refreshAnaMotorSessionTimeline());
  }
  void refreshAnaMotorArchiveList();
  void loadAnaMotorUnifiedPrefs();
  void refreshAnaMotorNotifyHistory();
  void refreshAnaMotorWeeklySummary();
})();

/** Dinamit — görsel sürükle-bırak + yapıştır + hatırlatıcı poll (Ümit & Gökçenur) */
function wireDinamitFeatures() {
  async function onChatImageFile(file, hint) {
    if (window.RuzgarGorselNiyet?.handleChatImageFile) {
      await window.RuzgarGorselNiyet.handleChatImageFile(file, hint);
      return;
    }
    setStatus("Görsel niyet modülü yüklenemedi.", "Rüzgar");
  }

  const chatDropTargets = [
    document.querySelector(".panel-chat"),
    el.input?.closest(".chat-input-row"),
    el.input,
  ].filter(Boolean);

  for (const target of chatDropTargets) {
    target.addEventListener("dragover", (e) => {
      e.preventDefault();
      try {
        e.dataTransfer.dropEffect = "copy";
      } catch (_) {
        /* ignore */
      }
    });
    target.addEventListener("drop", async (e) => {
      e.preventDefault();
      const f = e.dataTransfer?.files?.[0];
      if (!f) return;
      const mode = activeMotorChatMode();
      if (isAnaMotorDocFile(f) && ["genel", "uretim", "gelisim"].includes(mode)) {
        await uploadAnaMotorContextFile(f);
        return;
      }
      if (!String(f.type || "").startsWith("image/")) {
        setStatus("Sohbete görüntü veya txt/md/pdf bırak", "Rüzgar");
        return;
      }
      const hint = el.input?.value?.trim() || "";
      if (el.input) el.input.value = "";
      await onChatImageFile(f, hint);
    });
  }

  if (el.input) {
    el.input.addEventListener("paste", (e) => {
      silenceVoiceOutputNow();
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type && item.type.startsWith("image/")) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) {
            const hint = el.input.value.trim();
            el.input.value = "";
            void onChatImageFile(file, hint);
          }
          return;
        }
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
    .replace(/_\([^)]*(?:backend|sohbet\s+içi|karakter)[^)]*\)_/gi, "")
    .replace(/\[HTTP\s+\d+\][\s\S]*/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

/** Sesli okuma: ekranda tam metin kalır; TTS kısa ve net (Ümit abi). */
function truncateForTtsSpeech(text) {
  let t = ttsPlainForSpeech(text || "");
  if (!t) return "";
  t = t.replace(
    /Ümit abi,\s*şu an model yanıt üretemedi[^.]*\.\s*/i,
    ""
  );
  t = t.replace(/\(TARIH_VE_KULTUR[^)]+\)/gi, "");
  t = t.replace(/https?:\/\/\S+/g, "");
  t = t.replace(/\s+/g, " ").trim();
  const sentences = [];
  let rest = t;
  const re = /([\s\S]+?)([.!?…])(\s+|$)/g;
  let m;
  while ((m = re.exec(rest)) && sentences.length < RUZGAR_TTS_MAX_SENTENCES) {
    const s = (m[1] + m[2]).trim();
    if (s.length >= 4) sentences.push(s);
  }
  if (sentences.length) {
    t = sentences.join(" ");
  }
  if (t.length > RUZGAR_TTS_MAX_SPEECH_CHARS) {
    const cut = t.lastIndexOf(" ", RUZGAR_TTS_MAX_SPEECH_CHARS - 1);
    t = (cut > 40 ? t.slice(0, cut) : t.slice(0, RUZGAR_TTS_MAX_SPEECH_CHARS)).trim() + "…";
  }
  return t;
}

function isWebSpeechActive() {
  try {
    return !!(window.speechSynthesis.speaking || window.speechSynthesis.paused);
  } catch (_) {
    return false;
  }
}

function isTtsActive() {
  return !!(
    ttsArmed ||
    ttsPlayingEl ||
    ttsPumping ||
    (ttsTextQueue && ttsTextQueue.length > 0) ||
    (ttsPendingChunks && String(ttsPendingChunks).trim().length > 0) ||
    isWebSpeechActive()
  );
}

function updateTtsPauseButton() {
  if (!el.ttsPause) return;
  const iconPause = el.ttsPause.querySelector(".icon-pause");
  const iconPlay = el.ttsPause.querySelector(".icon-play");
  if (iconPause) iconPause.hidden = ttsPaused;
  if (iconPlay) iconPlay.hidden = !ttsPaused;
  el.ttsPause.setAttribute(
    "aria-label",
    ttsPaused ? "Sesli okumayı sürdür" : "Sesli okumayı duraklat"
  );
  el.ttsPause.title = ttsPaused
    ? "Sesli okumayı sürdür"
    : "Sesli okumayı duraklat";
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
  ttsPaused = false;
  ttsArmed = false;
  ttsWebUtterance = null;
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
  ttsArmed = true;
  syncInterruptButton();
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
      while (ttsPaused && ttsSess === ttsSessionCounter) {
        await new Promise((r) => setTimeout(r, 120));
      }
      if (ttsSess !== ttsSessionCounter) break;
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
    if (!ttsPlayingEl && ttsTextQueue.length === 0 && !isWebSpeechActive()) {
      ttsArmed = false;
    }
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
async function streamChat(userText, streamOpts = {}) {
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

  const chatMode = activeMotorChatMode();
  const chatSess = getMotorChatSession(chatMode);
  const codingMode =
    chatMode === "programlama" || !!(el.code && el.code.checked);
  const sharedHist = getSharedChatHistory();
  const body = {
    message: userText,
    history: historyForApiTurn(sharedHist, userText),
    use_web: el.web
      ? !!el.web.checked
      : !["ses", "mimar", "okuma", "tercume", "hafiza", "hizli", "programlama"].includes(
          chatMode,
        ),
    read_message_links:
      el.linkRead == null ? true : !!el.linkRead.checked,
    fetch_pages: Number.parseInt(String(el.fetchN?.value ?? "0"), 10) || 0,
    coding_mode: codingMode,
    session_wake_used: chatSess.sessionWakeUsed,
    mode: chatMode,
    workspace_root: workspaceRoot || undefined,
    autonom_research: !!(el.optAutonom && el.optAutonom.checked),
    ...(chatMode === "hizir"
      ? { hizir_channels: hizirCollectPazarCheckboxIds() }
      : {}),
    ...(chatMode === "programlama"
      ? {
          programlama_active_file: atolyeOpenRel || undefined,
          programlama_editor_snippet: getCodeEditorText().slice(0, 4000) || undefined,
          programlama_language: String(el.codeLanguage?.value || "python").trim() || undefined,
        }
      : {}),
    ...(streamOpts.contextBrief
      ? { conversation_context: String(streamOpts.contextBrief).slice(0, 8000) }
      : {}),
    ...(streamOpts.userRaw ? { user_message_raw: String(streamOpts.userRaw).slice(0, 4000) } : {}),
    ...(streamOpts.cinema ? { cinema_context: streamOpts.cinema } : {}),
    ...(Array.isArray(streamOpts.uploadIds) && streamOpts.uploadIds.length
      ? { ana_motor_upload_ids: streamOpts.uploadIds }
      : {}),
    ...(streamOpts.sessionId ? { ana_motor_session_id: String(streamOpts.sessionId) } : {}),
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
    scrollChatToBottom({ smooth: false });
  }

  function ensureReplyBubble() {
    if (responseBubble) return;
    hideThinkingCenter();
    responseBubble = document.createElement("div");
    responseBubble.className = "bubble assistant";
    el.chat.appendChild(responseBubble);
    scrollChatToBottom({ smooth: false });
  }

  /** Genel hafıza anında cevaplarda gereksiz "düşünüyor"; SSE gelene kadar ertelenir. */
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
    }, getFaz7DeferThinkingMs());
  }

  /** Token/done/error/status — zorunlu akış + hazırlık durumu (Ümit & Gökçenur Işık Hızı). */
  function renderAnaMotorResearchCard(card) {
    const wrap = document.getElementById("ana-motor-research-card");
    const sumEl = document.getElementById("ana-motor-research-summary");
    const listEl = document.getElementById("ana-motor-research-list");
    if (!wrap || !sumEl || !listEl) return;
    if (!card || !card.ok) {
      wrap.hidden = true;
      anaMotorLastResearchCard = null;
      syncAnaMotorKaynakPanel();
      return;
    }
    anaMotorLastResearchCard = card;
    const totals = card.totals || {};
    const parts = [];
    if (totals.nebula) parts.push(`Nebula ${totals.nebula}`);
    if (totals.tarih) parts.push(`Tarih ${totals.tarih}`);
    if (totals.arsiv) parts.push(`Arşiv ${totals.arsiv}`);
    if (totals.tdk) parts.push(`TDK ${totals.tdk}`);
    if (totals.indeks) parts.push(`İndeks ${totals.indeks}`);
    const webTxt = card.web_used ? " · Web" : "";
    sumEl.textContent = `${card.primary || "bilgi"} — ${parts.join(" · ") || "yerel"}${webTxt} · ${card.stamp || ""}`;
    listEl.innerHTML = "";
    const titles = {
      nebula: "Nebula",
      tarih: "Tarih",
      arsiv: "Arşiv",
      tdk: "TDK",
      indeks: "İndeks",
    };
    const buckets = card.buckets || {};
    for (const key of ["nebula", "tarih", "arsiv", "tdk", "indeks"]) {
      const rows = Array.isArray(buckets[key]) ? buckets[key] : [];
      for (const row of rows.slice(0, 3)) {
        const li = document.createElement("li");
        li.textContent = `[${row.id || "?"}] ${titles[key]} · ${row.label || ""} (${row.score || 0})`;
        li.title = row.excerpt || "";
        listEl.appendChild(li);
      }
    }
    wrap.hidden = listEl.children.length === 0 && !parts.length;
    syncAnaMotorKaynakPanel();
    const kFold = document.getElementById("ana-motor-kaynak-panel-fold");
    if (kFold && !kFold.open && !wrap.hidden) {
      kFold.open = true;
    }
  }

  function renderAnaMotorPatchCard(card) {
    const wrap = document.getElementById("ana-motor-patch-card");
    const sumEl = document.getElementById("ana-motor-patch-summary");
    const listEl = document.getElementById("ana-motor-patch-paths");
    if (!wrap || !sumEl || !listEl) return;
    if (!card || !card.ok || !card.has_pending) {
      wrap.hidden = true;
      return;
    }
    wrap.hidden = false;
    const c = card.count || 0;
    const counts = card.counts || {};
    sumEl.textContent =
      `${c} dosya bekliyor — kabul: ${counts.accepted || 0} · red: ${counts.rejected || 0} · ${card.hint || ""}`;
    listEl.innerHTML = "";
    for (const p of card.paths_preview || []) {
      const li = document.createElement("li");
      const code = document.createElement("code");
      code.textContent = p;
      li.appendChild(code);
      listEl.appendChild(li);
    }
  }

  function renderPlanPreview(plan) {
    if (!plan || !plan.primary) return;
    ensureDashboardAgentUi();
    if (!dashboardAgentWrapEl || !dashboardAgentListEl) return;
    dashboardAgentWrapEl.hidden = false;
    const lab = plan.label_tr || plan.primary || "";
    const src = plan.sources || "";
    const wq = (plan.web_query || "").trim();
    const rq = (plan.rag_query || "").trim();
    const skipRetrieval =
      plan.primary === "gundelik" &&
      !plan.use_ilim_rag &&
      !plan.prefer_web;
    const items = [
      { label: "Plan", detail: lab, status: "done" },
      { label: "Kaynaklar", detail: src, status: "done" },
    ];
    if (rq && !skipRetrieval) {
      items.push({
        label: "İndeks sorgusu",
        detail: rq.length > 80 ? `${rq.slice(0, 77)}…` : rq,
        status: "done",
      });
    }
    if (wq && plan.prefer_web) {
      items.push({
        label: "Web sorgusu",
        detail: wq.length > 80 ? `${wq.slice(0, 77)}…` : wq,
        status: "active",
      });
    }
    renderDashboardAgentSteps(items);
    setThinkingPlanHint(plan);
    if (el.dashboardStatus && currentMode === "genel") {
      el.dashboardStatus.textContent = `Plan: ${lab} · ${src}`;
    }
  }

  function processChatEvent(ev) {
    ruzgarDebugLog(`chat:${ev.type || "?"}`, ev);
    if (ev.type === "meta" && ev.research_card) {
      renderAnaMotorResearchCard(ev.research_card);
      return;
    }
    if (ev.type === "meta" && ev.nebula_oneri_card) {
      renderAnaMotorNebulaOneriCard(ev.nebula_oneri_card);
      return;
    }
    if (ev.type === "meta" && ev.plan) {
      clearDeferThinking();
      renderPlanPreview(ev.plan);
      if (ev.plan.status_text) {
        showThinkingCenter(ev.plan.status_text);
        setStatus(ev.plan.status_text, "Rüzgar");
      }
      return;
    }
    if (ev.type === "meta" && ev.instant_memory) {
      clearDeferThinking();
      hideThinkingCenter();
      return;
    }
    if (ev.type === "terminal_output") {
      const prev = String(ev.output_preview || "").trim();
      if (prev) {
        setCodeOutput(
          `[Terminal v3] ${ev.label || ""} exit=${ev.exit_code}\n${prev}`
        );
      }
      return;
    }
    if (
      ev.type === "agent_step" &&
      Array.isArray(ev.steps) &&
      ev.steps.length
    ) {
      renderProgramlamaAgentSteps(ev.steps);
      const ca = ev.code_agent || {};
      const comp = ev.compliance || ca.compliance;
      if (comp) renderProgramlamaCompliance(comp);
      const turn = Number(ca.turn || 0);
      const maxT = Number(ca.max_turns || 0);
      const phase = String(ca.phase || "");
      if (turn > 0 && maxT > 0) {
        const phaseTr =
          phase === "llm_start" || phase === "llm_done"
            ? " · LLM"
            : phase === "write"
              ? " · yazım"
              : phase === "verify"
                ? " · test"
                : phase === "tools"
                  ? " · araç"
                  : "";
        const rem = Number(ca.budget_remaining_sec || 0);
        const remTxt = rem > 0 ? ` · kalan ${rem} sn` : "";
        setStatus(`Görev tur ${turn}/${maxT}${phaseTr}${remTxt}`, "Rüzgar");
        showThinkingCenter(`Görev tur ${turn}/${maxT}${phaseTr}${remTxt}`);
      } else if (phase === "started") {
        setStatus("Otonom görev başladı", "Rüzgar");
      } else if (phase === "finish") {
        hideThinkingCenter();
      }
      return;
    }
    if (ev.type === "meta" && Array.isArray(ev.agent_steps) && ev.agent_steps.length) {
      renderProgramlamaAgentSteps(ev.agent_steps);
      return;
    }
    clearDeferThinking();
    if (ev.type === "status") {
      const t = (ev.text || "").trim();
      const phase = String(ev.phase || "").toLowerCase();
      if (t) {
        let label = t;
        if (phase === "bilim_derin" || phase === "bilim_derin_llm") {
          label = `🔬 ${t}`;
        } else if (
          phase === "archive" ||
          phase === "archive_detail" ||
          phase === "archive_hit"
        ) {
          label = `📚 ${t}`;
        } else if (phase === "full_index" || phase === "encyclopedic") {
          label = `📇 ${t}`;
        } else if (phase === "web" || phase === "web_engine") {
          label = `🌐 ${t}`;
        }
        showThinkingCenter(label);
        setStatus(label, "Rüzgar");
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
      chatSess.sessionWakeUsed = !!ev.new_wake_used;
      hideThinkingCenter();
      if (!responseBubble) {
        responseBubble = document.createElement("div");
        responseBubble.className = "bubble assistant";
        el.chat.appendChild(responseBubble);
      }
      responseBubble.classList.toggle("chat-clarify", !!ev.instant_clarify || !!ev.instant_gundelik);
      responseBubble.classList.toggle("chat-instant-memory", !!ev.instant_memory);
      // Streaming bittikten sonra zenginleştirilmiş render: ```fenced``` kod blokları
      // Programlama Atölyesi'ne tek tıkla atılabilir kart hâline gelir.
      if (full.includes("```")) {
        responseBubble.innerHTML = renderAssistantRichHtml(full);
        wireAssistantCodeButtons(responseBubble);
      } else {
        responseBubble.innerHTML = esc(full).replace(/\n/g, "<br>");
      }
      lastAssistantReply = full;
      if (window.RuzgarTercumeAtolye) window.RuzgarTercumeAtolye.onAssistantReply(full);
      updateDashboardLastSpeech();
      updateDynamicWorkbench();
      renderOrchestraBridge(ev.orchestra);
      if (
        currentMode === "genel" &&
        ev.orchestra?.active_motor &&
        isHubSseFazDEnabled()
      ) {
        openMotorWorkbenchQuiet(ev.orchestra.active_motor);
      }
      if (ev.motor_action?.motor === "video" && window.RuzgarVideoChatBrain?.tryAtolyeFromMessage) {
        void window.RuzgarVideoChatBrain.tryAtolyeFromMessage(
          ev.motor_action.message || ev.user_message || "",
        );
      }
      if (ev.programlama_focus_rel || ev.programlama_project_rel) {
        void applyProgramlamaFocusFromChat(ev);
      }
      if (ev.programlama_delegated) {
        const sumTxt = String(ev.delegate_summary_text || "").trim();
        flashRuzgarDurum(
          sumTxt
            ? sumTxt.replace(/\*\*/g, "").slice(0, 220)
            : "Kod sorusu → Programlama motoru (Faz 59 delege).",
        );
        if (el.code && !el.code.checked) {
          el.code.checked = true;
          switchMode("programlama");
        }
      }
      if (ev.patch_approval_card) {
        renderAnaMotorPatchCard(ev.patch_approval_card);
      }
      if (ev.nebula_oneri_card) {
        renderAnaMotorNebulaOneriCard(ev.nebula_oneri_card);
      }
      if (ev.source_trust_card && responseBubble) {
        attachSourceTrustBadge(responseBubble, ev.source_trust_card);
      }
      if (ev.paket_auto && ev.paket_auto.queued) {
        flashRuzgarDurum(
          ev.paket_auto.hint || `Otomatik paket — ${ev.paket_auto.file_count || "?"} dosya`,
        );
        startAnaMotorPaketAutoPoll();
        stopAnaMotorNebulaApplyPoll();
        void pollAnaMotorNebulaApplyStatus();
        anaMotorNebulaApplyPoll = window.setInterval(() => {
          void pollAnaMotorNebulaApplyStatus();
        }, 2200);
      }
      if (ev.code_patch) {
        showProgramlamaPatchStrip(ev.code_patch);
        if (ev.code_patch.action === "staged") {
          renderAnaMotorPatchCard({
            ok: true,
            has_pending: true,
            count: ev.code_patch.count,
            paths_preview: (ev.code_patch.items || []).map((x) => x.path).filter(Boolean),
            counts: ev.code_patch.counts || {},
            hint: "Programlama atölyesi veya Uygula",
          });
        }
        if (Array.isArray(ev.code_patch.applied) && ev.code_patch.applied.length) {
          flashRuzgarDurum(
            `Faz 10 patch: ${ev.code_patch.applied.length} dosya yazıldı — ${ev.code_patch.applied[0]}`,
          );
          const first = ev.code_patch.applied[0];
          if (first && String(first).startsWith("projects/")) {
            void applyProgramlamaFocusFromChat({
              programlama_focus_rel: first,
              programlama_expand_tree: true,
            });
          }
        }
      }
      const ut = String(ev.user_message || userText || "");
      if (HIZIR_MODU.shouldRefreshAfterChat(ut)) {
        void HIZIR_MODU.refreshPanel();
      }
      const store = ensureSharedChatStore();
      const lastH = store.history[store.history.length - 1];
      if (!lastH || lastH.role !== "user" || lastH.content !== ut) {
        pushMotorChatHistory("user", ut, {});
      }
      pushMotorChatHistory("assistant", full, {});
      lastAssistantReply = full;
      setStatus("Hazır");
      scrollChatToBottom();
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
        } else if (!wantEdge && !ttsEdgeSpokeTurn) {
          window.setTimeout(() => void speakLast(), 80);
        }
      }
      trimMotorChatHistory(ensureSharedChatStore());
      window.setTimeout(() => {
        lastVoiceEmotion = null;
      }, 90000);
    } else if (ev.type === "error") {
      hideThinkingCenter();
      ensureReplyBubble();
      const errText = String(ev.text || "Bilinmeyen hata").trim();
      responseBubble.innerHTML = renderChatErrorHtml(errText);
      setStatus("Hata — ayrıntı sohbette", "Rüzgar");
      flashRuzgarDurum(errText.slice(0, 120));
      appendBubble("assistant", `[DEBUG hata] ${errText}`, { error: true });
    }
  }

  function handleSseJson(jsonStr) {
    try {
      processChatEvent(JSON.parse(jsonStr));
    } catch (parseErr) {
      ruzgarDebugLog("sse:json-parse-hata", {
        raw: String(jsonStr || "").slice(0, 200),
        err: String(parseErr),
      });
      ruzgarDebugLog("sse:parse", String(parseErr));
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

  // Ham JSON anında cevap kapatıldı — sunucu hafızayı Ollama ile doğal sentezler (hafiza_dogal_sentez).
  const skipGenelBak = true;
  const nebulaKitapCmd =
    /\.(?:json|txt|md)\b/i.test(String(userText || "")) &&
    /haf[ıi]zana\s+kaydet|dosyas[ıi]n[ıi]\s+oku/i.test(String(userText || ""));
  const tarihSoruCmd =
    /osmanl|fatih|murat|selçuk|selcuk|istanbul|fethett|tarih|padişah|padisah|ttk|bizans|osman\s+bey/i.test(
      String(userText || ""),
    );
  const casualShortCmd =
    /^(selam|merhaba|naber|nas[ıi]ls[ıi]n|iyi\s+(akşam|aksam|geceler)|günayd[ıi]n|gunaydin|ben\s+geldim|geldim|teşekkür|tesekkur)\b/i.test(
      String(userText || "").trim(),
    ) && String(userText || "").trim().length < 48;
  const egitimCmd =
    /yanl[ıi]ş\s*cevap|yanlis\s*cevap|cevab[ıi]n\s+şu\s+olmalı|cevabin\s+su\s+olmalı|doğru\s+cevap|dogru\s+cevap/i.test(
      String(userText || ""),
    );
  const isProgramlamaAgentTask =
    chatMode === "programlama" &&
    (codingMode ||
      /^\s*(?:görev|gorev)\s*:/im.test(String(userText || "")) ||
      /^\s*(?:görev|gorev)\s+[\w.\-]+\s+/im.test(String(userText || "")));
  const chatFullTimeoutMs = casualShortCmd
    ? RUZGAR_CHAT_CASUAL_TIMEOUT_MS
    : egitimCmd
      ? 15000
    : isProgramlamaAgentTask
      ? RUZGAR_CHAT_PROGRAMMING_AGENT_TIMEOUT_MS
    : nebulaKitapCmd
      ? Math.max(RUZGAR_CHAT_FULL_TIMEOUT_MS, 45000)
      : tarihSoruCmd
        ? Math.max(RUZGAR_CHAT_FULL_TIMEOUT_MS, 90000)
        : RUZGAR_CHAT_FULL_TIMEOUT_MS;
  if (!skipGenelBak) {
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
          chatSess.sessionWakeUsed ||
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
  }

  // Kısa sohbet (nasılsın/selam): tam yanıt beklemeden WS ile token göster — boş balon takılması olmasın
  const useChatFullBatch = RUZGAR_DISABLE_STREAMING && !casualShortCmd;
  if (useChatFullBatch) {
    const fullCtrl = new AbortController();
    activeChatAbort = fullCtrl;
    activeChatWs = null;
    syncInterruptButton();
    let fullTimedOut = false;
    const fullDeadline = window.setTimeout(() => {
      fullTimedOut = true;
      fullCtrl.abort();
    }, chatFullTimeoutMs);
    if (currentMode !== "hafiza") {
      scheduleDeferThinkingOverlay();
    }
    ruzgarDebugLog("chat/full:istek", {
      url: `${API}/api/chat/full`,
      mode: chatMode,
      msgLen: String(userText || "").length,
    });
    try {
      const res = await fetch(`${API}/api/chat/full`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          Accept: "application/json",
          "Accept-Charset": "utf-8",
          "Cache-Control": "no-cache",
        },
        body: JSON.stringify(body),
        cache: "no-store",
        signal: fullCtrl.signal,
      });
      const j = await res.json().catch((jsonErr) => {
        ruzgarDebugLog("chat/full:json-hata", String(jsonErr));
        return {};
      });
      ruzgarDebugLog("chat/full:yanit", {
        http: res.status,
        ok: j.ok,
        events: Array.isArray(j.events) ? j.events.length : 0,
        replyLen: String(j.full_reply || "").length,
        error: j.error || null,
      });
      if (!res.ok || j.ok === false) {
        const errMsg = j.error || j.detail || `HTTP ${res.status}`;
        ruzgarDebugLog("chat/full:sunucu-hata", errMsg);
        throw new Error(errMsg);
      }
      const events = Array.isArray(j.events) ? j.events : [];
      const replyPreview = String(j.full_reply || "").trim();
      let gotDoneFromEvents = false;
      events.forEach((ev) => {
        if (ev && ev.type !== "token" && ev.type !== "done") processChatEvent(ev);
      });
      if (!gotDoneFromEvents) {
        processChatEvent({
          type: "done",
          full_reply: j.full_reply || "",
          user_message: j.user_message || userText,
          new_wake_used: !!j.new_wake_used,
          orchestra: j.orchestra,
          instant_gundelik: !!j.instant_gundelik,
          instant_clarify: !!j.instant_clarify,
          instant_memory: !!j.instant_memory,
        });
      }
      if (!replyPreview && !full.trim()) {
        ruzgarDebugLog("chat/full:bos-yanit", j);
        if (RUZGAR_UI_DEBUG) {
          appendBubble(
            "assistant",
            "Sunucu yanıt üretemedi (boş full_reply).",
            { error: true },
          );
        }
      }
      return;
    } catch (e) {
      hideThinkingCenter();
      ruzgarDebugLog("chat/full:catch", {
        name: e?.name,
        message: e?.message || String(e),
      });
      if (userRequestedChatStop) {
        userRequestedChatStop = false;
        return;
      }
      if (e && e.name === "AbortError") {
        throw new Error(
          fullTimedOut
            ? `Yanıt zaman aşımı (${Math.round(chatFullTimeoutMs / 1000)} sn) — otonom görevde sunucu hâlâ çalışıyor olabilir; Ruzgar_YenidenBaslat.bat veya biraz bekleyip tekrar deneyin.`
            : "Yanıt kesildi — istek iptal edildi."
        );
      }
      throw e;
    } finally {
      window.clearTimeout(fullDeadline);
      clearDeferThinking();
      hideThinkingCenter();
      activeChatAbort = null;
      activeChatWs = null;
      syncInterruptButton();
      scrollChatToBottom();
    }
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
    scrollChatToBottom();
  }
}

/**
 * @param {{ skipUserBubble?: boolean }} opts Ses metni zaten gösterildiyse Yıldırım: çift balon yok.
 */
function hizirChatImpliesProductScan(text) {
  const raw = String(text || "").trim();
  if (!raw) return false;
  const low = raw.toLowerCase();
  if (/ürün\w*\s+.{0,50}\s*tara/.test(low)) return true;
  if (/\btara\b/.test(low) && /ürün|urun|pazar|fiyat|stok|trendyol|amazon/.test(low)) {
    return true;
  }
  if (/^pazar\s+(yerini|tara)/i.test(raw)) return true;
  if (currentMode !== "hizir") return false;
  if (
    /^(merhaba|selam|nasılsın|nasilsin|teşekkür|tesekkur|yardım|yardim|evet|hayır|hayir)\b/i.test(
      low,
    )
  ) {
    return false;
  }
  if (/\?/.test(raw) && !/fiyat|ucuz|ne kadar|kaç tl|kac tl|trendyol|amazon/i.test(low)) {
    return false;
  }
  return raw.length >= 2 && raw.length <= 120;
}

function hizirQueryFromChat(text) {
  const raw = String(text || "").trim();
  const m = raw.match(/(?:gereken\s+)?(?:bazı\s+|bazi\s+)?(.+?)\s+ürün\w*\s+tara/i);
  if (m && m[1] && m[1].trim().length >= 2) return m[1].trim();
  const m2 = raw.match(/pazar\s+tara\s*:?\s*(.+)/i);
  if (m2 && m2[1]) return m2[1].trim();
  return raw
    .replace(/\s*tara\w*/gi, " ")
    .replace(/ürün\w*/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

async function sendMessageWithText(t, opts = {}) {
  const skipUser = !!opts.skipUserBubble;
  const text = (t || "").trim();
  if (!text) return;
  if (perfBusy) {
    flashRuzgarDurum("Önceki yanıt bitene kadar bekleyin veya DURDUR'a basın.");
    return;
  }
  chatStickToBottom = true;
  dismissChatWelcome();
  silenceVoiceOutputNow();
  clearOrchestraBridge();
  const ok = await checkApi();
  if (!ok) {
    ruzgarDebugLog("send:block", { api: API, reason: "health-fail" });
    appendBubble(
      "assistant",
      `Yerel sunucu kapalı (${API}/api/health). Ruzgar.ps1 veya Start-Ruzgar.ps1 ile API’yi başlatın (port ${RUZGAR_LOCAL_API_PORT}).`,
      { error: true }
    );
    return;
  }

  el.input.value = "";
  const chatSess = getMotorChatSession(activeMotorChatMode());
  const priorHistory = getSharedChatHistory().slice();
  let dispatchText = text;
  let understanding = null;
  if (window.RuzgarSohbetAnlama?.understand) {
    understanding = window.RuzgarSohbetAnlama.understand(text, {
      mode: currentMode,
      chatMode: activeMotorChatMode(),
      history: priorHistory,
      cinema: getCinemaNowPlaying?.(),
      hasCinema: hasActiveCinemaSession?.(),
    });
    if (understanding?.text) dispatchText = understanding.text;
    if (understanding?.fromHistory && dispatchText !== text) {
      ruzgarDebugLog("sohbet-anlama", {
        raw: text.slice(0, 120),
        resolved: dispatchText.slice(0, 120),
        intent: understanding.intent,
        motor: understanding.motorHint,
      });
    }
  }
  const motorCtx = {
    understanding,
    history: priorHistory,
    contextBrief: understanding?.contextBrief || "",
  };

  if (!skipUser) {
    appendBubble("user", text);
  }

  const finishMotorInstant = (statusLabel) => {
    setStatus(statusLabel || "Rüzgar", "Rüzgar");
    if (el.send) el.send.disabled = false;
    perfBusy = false;
    updatePerformanceIndicators(perfBusy);
    syncInterruptButton();
  };

  const tryInstantMotors =
    !window.RuzgarSohbetAnlama?.shouldTryInstantMotor
      ? true
      : understanding?.instantMotor === true;

  if (tryInstantMotors && window.RuzgarAnaMotorHub?.tryEylemCommand) {
    const eylemHit = await window.RuzgarAnaMotorHub.tryEylemCommand(dispatchText, motorCtx);
    if (eylemHit?.handled) {
      finishMotorInstant(currentMode === "genel" ? "Ana Motor" : MODE_LABELS[currentMode] || currentMode);
      return;
    }
  }

  if (tryInstantMotors && currentMode === "genel" && window.RuzgarAnaMotorHub?.tryDispatchFromGenel) {
    const hubHit = await window.RuzgarAnaMotorHub.tryDispatchFromGenel(dispatchText, motorCtx);
    if (hubHit?.handled) {
      finishMotorInstant("Ana Motor");
      return;
    }
  }

  if (tryInstantMotors && currentMode !== "genel" && window.RuzgarAnaMotorHub?.tryDispatchActiveMotor) {
    const motorHit = await window.RuzgarAnaMotorHub.tryDispatchActiveMotor(dispatchText, motorCtx);
    if (motorHit?.handled) {
      finishMotorInstant(MODE_LABELS[currentMode] || currentMode);
      return;
    }
  }

  if (!tryInstantMotors) {
    ruzgarDebugLog("sohbet-anlama:llm", {
      reason: understanding?.instantReason || "prefer_chat",
      intent: understanding?.intent,
    });
  }

  if (currentMode === "hizir" && hizirChatImpliesProductScan(text)) {
    if (el.hizirTaraQuery) {
      const hq = hizirQueryFromChat(text);
      if (hq) el.hizirTaraQuery.value = hq;
    }
    void HIZIR_MODU.pazarTara();
  }
  if (el.send) el.send.disabled = true;
  setStatus("İstek…", "Rüzgar");
  perfBusy = true;
  updatePerformanceIndicators(perfBusy);
  syncInterruptButton();

  try {
    const chatPayload =
      understanding?.fromHistory && dispatchText && dispatchText !== text
        ? dispatchText
        : text;
    const cinemaCtx = getCinemaNowPlaying?.();
    const cinemaPayload =
      cinemaCtx && (cinemaCtx.url || cinemaCtx.localRel)
        ? {
            url: String(cinemaCtx.url || "").slice(0, 500),
            localRel: String(cinemaCtx.localRel || "").slice(0, 200),
            title: String(cinemaCtx.title || cinemaCtx.label || "").slice(0, 200),
          }
        : undefined;
    anaMotorLastUserTopic = text;
    const uploadIds = anaMotorUploadQueue.map((x) => x.id).filter(Boolean);
    await streamChat(chatPayload, {
      userRaw: text,
      contextBrief: understanding?.contextBrief || "",
      cinema: cinemaPayload,
      uploadIds,
      sessionId: anaMotorUploadSessionId || undefined,
    });
    if (uploadIds.length || anaMotorUploadSessionId) {
      anaMotorUploadQueue.length = 0;
      anaMotorUploadSessionId = null;
      updateAnaMotorSessionCard();
    }
  } catch (e) {
    appendBubble("assistant", formatClientChatError(e), { error: true });
    setStatus("Hata — ayrıntı sohbette", "Rüzgar");
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
  if (text && window.RuzgarVirusGuard?.consumeVoiceApproval?.(text)) {
    pushSessionSend = false;
    setStatus("İndirme onayı alındı.", "Rüzgar");
    return;
  }
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
  const text = truncateForTtsSpeech(lastAssistantReply || "");
  if (!text) return;
  if (el.voiceOut != null && !el.voiceOut.checked) return;
  ttsArmed = true;
  syncInterruptButton();
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
  ttsWebUtterance = u;
  window.speechSynthesis.speak(u);
  setStatus("Sesli okuma…");
  syncInterruptButton();
  u.onend = () => {
    ttsWebUtterance = null;
    ttsArmed = false;
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
        backend: sesTtsBackendPreference(),
        lang: "tr",
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

/** Tilavet modu — Kuran / gazel / ilahi referans klonu (Faz S5). @returns {Promise<boolean>} */
async function speakStudioTilavet(raw, opts) {
  const options = opts && typeof opts === "object" ? opts : {};
  const tilavetReferans = String(options.tilavetReferans || options.profil || "").trim().toLowerCase();
  const plain = ttsPlainForSpeech(raw || "");
  if (!plain) {
    flashRuzgarDurum("Tilavet icin metin yok.");
    return false;
  }
  let kar = "alim";
  try {
    const rs = await fetch(`${API}/api/ses/settings`);
    if (rs.ok) {
      const j = await rs.json();
      kar = normalizeKarakterForTts(j.karakter || "alim");
    }
  } catch (_) {
    /* ignore */
  }
  const profLabel = tilavetReferans || "tilavet";
  flashRuzgarDurum(`${profLabel} sesiyle sentezleniyor — XTTS ilk seferde uzun sürebilir…`);
  setStatus("Tilavet…", "Rüzgar");
  const ctrl = typeof AbortController !== "undefined" ? new AbortController() : null;
  const abortTimer = ctrl
    ? window.setTimeout(() => ctrl.abort(), 600000)
    : null;
  try {
    const payload = {
      text: plain,
      karakter: kar,
      backend: "auto",
    };
    if (tilavetReferans) payload.tilavet_referans = tilavetReferans;
    const res = await fetch(`${API}/api/tts/tilavet`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl ? ctrl.signal : undefined,
    });
    if (res.ok) {
      const blob = await res.blob();
      if (!blob || blob.size < 128) {
        throw new Error("Ses dosyası boş döndü.");
      }
      await playTtsBlob(blob);
      setStatus("Hazır");
      flashRuzgarDurum("Tilavet okuma tamam — ses çalındı.");
      return true;
    }
    let j = {};
    try {
      j = await res.json();
    } catch {
      j = {};
    }
    const detail = String(j.detail || res.statusText || "Tilavet basarisiz");
    flashRuzgarDurum(detail);
    throw new Error(detail);
  } catch (e) {
    if (e && e.name === "AbortError") {
      flashRuzgarDurum("Tilavet zaman aşımı (10 dk) — CPU'da model hâlâ yükleniyor olabilir.");
    } else {
      flashRuzgarDurum(e && e.message ? e.message : String(e));
    }
    throw e;
  } finally {
    if (abortTimer) clearTimeout(abortTimer);
    setStatus("Hazır", "Rüzgar");
  }
  return false;
}

function speakTextImmediate(text) {
  const plain = truncateForTtsSpeech(text || "");
  if (!plain) return;
  ttsArmed = true;
  syncInterruptButton();
  try {
    window.speechSynthesis.cancel();
  } catch (_) {
    /* yok say */
  }
  try {
    const u = new SpeechSynthesisUtterance(plain);
    u.lang = "tr-TR";
    ttsWebUtterance = u;
    window.speechSynthesis.speak(u);
    setStatus("Sesli okuma…");
    syncInterruptButton();
    u.onend = () => {
      ttsWebUtterance = null;
      ttsArmed = false;
      setStatus("Hazır");
      syncInterruptButton();
    };
  } catch (_) {
    ttsArmed = false;
    syncInterruptButton();
  }
}
window.ruzgarSpeak = speakTextImmediate;

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
if (el.ttsPause) {
  el.ttsPause.addEventListener("click", () => toggleTtsPause());
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
/** IME commit, dokunmatik klavye, sürükleyip bırakma metin — ses varsayılanı kes (görsel yapıştırma wireDinamitFeatures) */
el.input.addEventListener("input", () => silenceVoiceOnUserEdit());
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
    if (action === "sidebar:duzen" || action === "sidebar:gelisim") {
      const kind = action === "sidebar:gelisim" ? "gelisim" : "duzen";
      void window.RuzgarSidebarManager?.renderFromMenu?.(kind);
      return;
    }
    if (action.startsWith("tercume-dock:")) {
      const dock = action.slice("tercume-dock:".length);
      window.RuzgarPanelActions?.run?.(`tercume:${dock}`);
      return;
    }
    if (action === "tercume-ui:reader") {
      window.RuzgarPanelActions?.run?.("tercume-ui:reader");
      flashRuzgarDurum("Kitap görünümü — sohbetle okuma.");
      return;
    }
    if (action === "tercume-ui:classic") {
      window.RuzgarPanelActions?.run?.("tercume-ui:classic");
      flashRuzgarDurum("Klasik ofis görünümü.");
      return;
    }
    if (action === "mic") void menuOpenMic();
    if (action === "speak") speakLast();
    if (action === "menu:disa-aktar") {
      console.log("[RÜZGAR] Hazırlanıyor... (Dışa Aktar — içerik)");
      let body = (lastAssistantReply || "").trim();
      const exportHist = getSharedChatHistory();
      if (!body && exportHist.length) {
        body = exportHist
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
      const defD = "1.0";
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
      const dRaw = window.prompt(
        "Durak çarpanı (0.55–1.6, yüksek = cümle arası daha uzun nefes/durak)",
        defD
      );
      if (dRaw == null) return;
      let hiz = Number.parseFloat(hRaw.replace(",", "."));
      let huzur = Number.parseFloat(zRaw.replace(",", "."));
      let durak = Number.parseFloat(dRaw.replace(",", "."));
      if (!Number.isFinite(hiz)) hiz = 0.92;
      if (!Number.isFinite(huzur)) huzur = 0.88;
      if (!Number.isFinite(durak)) durak = 1.0;
      hiz = Math.min(1, Math.max(0.45, hiz));
      huzur = Math.min(1, Math.max(0.45, huzur));
      durak = Math.min(1.6, Math.max(0.55, durak));
      void fetch(`${API}/api/ses/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hiz,
          huzur,
          durak,
          prosody: true,
          mimarlar: "Ümit & Gökçenur",
        }),
      })
        .then((r) => {
          if (r.ok)
            setStatus(
              `Ses ayarı: hız ${hiz} · huzur ${huzur} · durak ${durak} (S1 prosody)`,
              "Rüzgar"
            );
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
wireFaz7Cila();
wireChatAutoScroll();
document.body.classList.add("faz7-complete", "faz8-complete", "faz-z-complete", "faz-aa-complete");
void refreshUiManifest().finally(() =>
  renderMotorChatFromSession(activeMotorChatMode()),
);
ensureSharedChatStore();
void checkApi();
setInterval(() => void checkApi(), 15000);

/** ruzgar_remote_api.txt güncellendiğinde (ör. 8777→8778) sayfayı yenile — köprü otomatik */
setInterval(() => {
  try {
    const remote = normalizeRuzgarApiRootTail(
      window.ruzgarApi?.getRemoteBrainEndpoint?.() || "",
    );
    if (remote && remote !== API) {
      try {
        localStorage.setItem("ruzgarApi", remote);
      } catch (_) {
        /* yok say */
      }
      ruzgarDebugLog("kopru-yenile", { eski: API, yeni: remote });
      globalThis.location.reload();
    }
  } catch (_) {
    /* yok say */
  }
}, 4000);
setInterval(() => {
  if (document.hidden) return;
  void refreshUiManifest();
}, UI_MANIFEST_POLL_MS);
const PROGRAMLAMA_GIT_POLL_MS = 15000;
setInterval(() => {
  if (document.hidden) return;
  const progPage = document.getElementById("page-programlama");
  if (progPage && !progPage.hidden) {
    void refreshProgramlamaKpiDashboard();
  }
}, PROGRAMLAMA_GIT_POLL_MS);
refreshPerformanceMetrics();
scheduleMetricsPolling();
loadFileTree();
globalThis.__ruzgarSpeak = speakLast;
