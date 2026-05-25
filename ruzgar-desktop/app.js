/**
 * Bağlantı hattı: UI → Tünel → Colab API (aynı köke WebSocket/SSE/Fetch).
 * Beyin adresi önceliği: preload + ruzgar_remote_api.txt > ?api > localStorage > yalın yerel.
 * Kök sonda `/api` ise kırpılır — aksi halde fetch `.../api/api/merkezi-bellek` ile 404 verir.
 */
const RUZGAR_LOCAL_API_PORT = 8779;
const RUZGAR_EXPECTED_BUILD_REV = "2026-05-25-programlama-faz32-v44";
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
console.info("[RÜZGAR Connection Bridge] API kök:", API);
const RUZGAR_CHAT_FULL_TIMEOUT_MS = 180000;
const RUZGAR_DISABLE_STREAMING = true;

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
  modeBtnOkuma: document.getElementById("mode-btn-okuma"),
  modeBtnSes: document.getElementById("mode-btn-ses"),
  modeBtnHizir: document.getElementById("mode-btn-hizir"),
  motorDeclarationHeader: document.getElementById("motor-declaration-header"),
  dynamicWorkbench: document.getElementById("dynamic-workbench"),
  pageGenel: document.getElementById("page-genel"),
  pageHafiza: document.getElementById("page-hafiza"),
  pageOkuma: document.getElementById("page-okuma"),
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
  btnVideoSubToTercume: document.getElementById("btn-video-sub-to-tercume"),
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
/** Tercüme Atölyesi — kaynak dosya */
let tercumeOpenRel = null;
/** Ses önizleme blob URL — yeniden seçimde iptal */
let sesPreviewObjectUrl = null;
/** Video önizleme blob URL */
let videoPreviewObjectUrl = null;
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
  "modeBtnOkuma",
  "modeBtnSes",
  "modeBtnHizir",
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
    if (["ses", "okuma", "tercume", "uretim", "hizli", "hafiza", "hizir"].includes(currentMode)) {
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
  } else if (currentMode === "hizir") {
    el.input.placeholder =
      "Örn: «Pazar yerini tara», «Hava durumuna bak», Trendyol fiyat. Yanıt sohbette; veri HIZIR sekmesinde güncellenir.";
  } else {
    el.input.placeholder =
      "Soru yazın veya yapıştırın — Web açıkken arama + okuma; doğrudan https:// bağlantısı da okunur.";
  }
  syncTopModeButtons();
  syncHizirWorkbenchStripVisibility();
  syncWorkbenchHizirToolbar();
  if (el.navRefresh) {
    const tips = {
      genel: "Ana motor panelini yenile",
      hafiza: "Hafıza JSON görünümünü yenile",
      hizir: "HIZIR: merkezi bellek + fırsat listesini yenile (Ana Motor değişmez)",
      okuma: "İlim dosya listesini yenile",
      tercume: "Tercüme dosya listesini yenile",
      ses: "Ses motoru ipuçlarını yenile",
      video: "Video motoru özetini yenile",
      programlama: "Programlama atölyesi kökünü yenile",
    };
    el.navRefresh.title = tips[currentMode] || "Aktif modülü yenile";
  }
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
      (currentMode === "okuma"
        ? "İlim Hazinesi taranıyor…"
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

function openFaz7Help() {
  if (!el.faz7HelpOverlay) return;
  el.faz7HelpOverlay.hidden = false;
  el.faz7HelpOverlay.removeAttribute("aria-hidden");
  el.faz7HelpClose?.focus();
}

function closeFaz7Help() {
  if (!el.faz7HelpOverlay) return;
  el.faz7HelpOverlay.hidden = true;
  el.faz7HelpOverlay.setAttribute("aria-hidden", "true");
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
  dismissChatWelcome();
  const foot = lastUiManifest?.dashboard?.welcome_foot || "Faz 16 aktif · Ümit & Gökçenur";
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
    li.className = "video-edit-bin-item";
    const title = String(row.title || row.url || "video").slice(0, 90);
    const filePath = String(row.file_path || "").slice(0, 140);
    li.textContent = filePath ? `${title} · ${filePath}` : title;
    el.videoDownloadRecent.appendChild(li);
  });
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
      if (pb) pb.textContent = String(meta.tag).split("·")[0].trim() || "Faz 3";
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

async function refreshUiManifest() {
  try {
    const r = await fetch(`${API}/api/ui/manifest`, { method: "GET", cache: "no-store" });
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
  renderMotorChatFromSession(next);
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
      "Programlama motoru açıldı; Faz 6 — şablon projeler, oturum bağlamı, onaylı düzeltme.",
    hafiza:
      "Hafıza motoru açıldı; bu motorla gelişim ve hafıza teknikleri üzerinde çalışabilirsiniz.",
    ses:
      "Ses motoru — Stüdyo: dosya + konuşmayı metne dökme, transkript; tarayıcıdan seslendirme.",
    tercume:
      "Tercüme motoru — Ofis paneli: arşiv + iki kolon; Çevir ile Rüzgar’a yapılandırılmış istek.",
    hizir:
      "HIZIR — Merkezi Bellek v3: ticari fırsatlar ve genel keşif önbelleği; sunucu API ile canlı yenilenir.",
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

function hideProgramlamaInlineDiff() {
  const panel = document.getElementById("programlama-inline-diff");
  if (panel) panel.hidden = true;
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
    preOld.textContent = data.old_text || "(yeni dosya)";
    preNew.textContent = data.new_text || "";
    panel.hidden = false;
    void openProgramlamaWorkspaceFile(rel);
    if (data.new_text && el.codeEditor) {
      el.codeEditor.value = data.new_text;
    }
    flashRuzgarDurum("Faz 27: eski/yeni yan yana");
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

function showStaleBuildBanner(rev) {
  const stale = Boolean(rev && rev !== RUZGAR_EXPECTED_BUILD_REV);
  let box = document.getElementById("ruzgar-stale-build-banner");
  if (!stale) {
    if (box) box.remove();
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
    `<strong>Eski Rüzgar API çalışıyor</strong> (build: <code>${escAttr(rev)}</code>). ` +
    `Güncel kod için proje kökünde: <code>Ruzgar_YenidenBaslat.bat</code> veya ` +
    `<code>.\\Ruzgar.ps1 -ForceRestart</code> — beklenen: <code>${escAttr(RUZGAR_EXPECTED_BUILD_REV)}</code>.`;
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

function updateDynamicWorkbench() {
  const pages = [
    el.pageGenel,
    el.pageHafiza,
    el.pageHizir,
    el.pageOkuma,
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
    okuma: el.pageOkuma,
    tercume: el.pageTercume,
    video: el.pageVideo,
    programlama: el.pageProgramlama,
    ses: el.pageSes,
  };
  const active = map[currentMode] || el.pageGenel;
  if (active) {
    active.hidden = false;
    active.style.display = "";
  }
  if (currentMode === "hafiza") {
    setWorkbenchLayout("layout-split2");
  } else if (el.dynamicWorkbench?.classList.contains("layout-split2")) {
    setWorkbenchLayout("layout-full");
  }
  if (el.dashboardStatus)
    el.dashboardStatus.textContent = `Aktif motor: ${MODE_LABELS[currentMode] || currentMode}`;
  updateDashboardLastSpeech();
  if (currentMode === "hafiza") void loadHafizaJsonView();
  if (currentMode === "okuma") void loadIlimFileList();
  if (currentMode === "tercume") void loadTercumeFileList();
  if (currentMode === "ses") void refreshSesSttHint();
  if (currentMode === "video") void refreshVideoEngineHint();
  if (currentMode === "programlama") {
    updateProgramlamaActiveFileLabel();
    void programlamaAtolyeRefreshRoot();
  }
  if (currentMode === "hizir") void refreshHizirOperasyonPanel();
  syncWorkbenchHizirToolbar();
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
      let detail = j.detail || j.error;
      if (Array.isArray(detail)) {
        detail = detail.map((x) => (x && x.msg ? x.msg : JSON.stringify(x))).join("; ");
      }
      flashRuzgarDurum(String(detail || "Kurgu başarısız."));
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
        "Ortam inceleme hazır — v2 kesim; v3 altyazı/ses; v4 altyazı→Tercüme; v5 görsel kurgu (timeline + FFmpeg mix, merkezi havuz). Çıktı: .ruzgar-video-export/.";
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

async function runVideoDownloadJob() {
  const url = String(el.videoDownloadUrl?.value || "").trim();
  if (!url) {
    flashRuzgarDurum("İndirmek için önce video URL girin.");
    el.videoDownloadUrl?.focus();
    return;
  }
  const btn = el.btnVideoDownload;
  if (btn) btn.disabled = true;
  if (el.videoDownloadStatus) el.videoDownloadStatus.textContent = "İndiriliyor… Bu işlem video boyutuna göre sürebilir.";
  flashRuzgarDurum("Video indiriliyor…");
  try {
    const res = await fetch(`${API}/api/video/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || j.ok === false) {
      const detail = j.detail || j.result?.error || `HTTP ${res.status}`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    const result = j.result || {};
    const rel = String(result.file_path || "").trim();
    const title = String(result.title || "video").trim();
    if (el.videoDownloadStatus) {
      el.videoDownloadStatus.textContent = rel ? `İndirildi: ${title} · ${rel}` : `İndirildi: ${title}`;
    }
    if (rel) {
      if (el.videoRelWorkspace) el.videoRelWorkspace.value = rel;
      if (el.videoEditInsertRel) el.videoEditInsertRel.value = rel;
    }
    flashRuzgarDurum("Video indirildi ve merkezi havuza kaydedildi.");
    await refreshUiManifest();
  } catch (e) {
    const msg = String(e && e.message ? e.message : e);
    if (el.videoDownloadStatus) el.videoDownloadStatus.textContent = `İndirme başarısız: ${msg}`;
    flashRuzgarDurum("Video indirme başarısız.");
  } finally {
    if (btn) btn.disabled = false;
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
  wireVideoQuickBar();
}

function wireVideoQuickBar() {
  const root = el.pageVideo;
  if (!root || root.dataset.videoQuickBarWired === "1") return;
  root.dataset.videoQuickBarWired = "1";

  const scrollToEl = (target) => {
    if (!target) return;
    target.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  if (el.videoQuickCreate) {
    el.videoQuickCreate.addEventListener("click", () => {
      const sticky = root.querySelector(".video-player-sticky");
      scrollToEl(sticky);
      try {
        el.videoFileInput?.click();
      } catch (_) {
        el.videoFileInput?.focus();
      }
      flashRuzgarDurum("Kaynak dosya seçin; önizleme solda güncellenir.");
    });
  }
  if (el.videoQuickYoutube) {
    el.videoQuickYoutube.addEventListener("click", () => {
      const a = document.getElementById("video-anchor-download");
      scrollToEl(a);
      window.setTimeout(() => {
        el.videoDownloadUrl?.focus?.({ preventScroll: true });
      }, 320);
    });
  }
  if (el.videoQuickTrim) {
    el.videoQuickTrim.addEventListener("click", () => {
      const a = document.getElementById("video-anchor-v2");
      scrollToEl(a);
      window.setTimeout(() => {
        el.videoStartSec?.focus?.({ preventScroll: true });
      }, 320);
    });
  }
  if (el.videoQuickAudio) {
    el.videoQuickAudio.addEventListener("click", () => {
      const a = document.getElementById("video-anchor-v3-mux");
      scrollToEl(a);
      window.setTimeout(() => {
        el.videoRelMuxVideo?.focus?.({ preventScroll: true });
      }, 320);
    });
  }
  if (el.videoQuickExport) {
    el.videoQuickExport.addEventListener("click", () => {
      const a = document.getElementById("video-anchor-v2");
      scrollToEl(a);
      openVideoExportFolder();
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
  const btnPatchApply = document.getElementById("btn-patch-apply-pending");
  if (btnPatchApply) {
    btnPatchApply.addEventListener("click", () => void applyPendingPatchFromAtolye("accepted"));
  }
  const btnPatchApplyAll = document.getElementById("btn-patch-apply-all");
  if (btnPatchApplyAll) {
    btnPatchApplyAll.addEventListener("click", () => void applyPendingPatchFromAtolye("all"));
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

/** Ortak sohbet paneli — her motorun kendi geçmişi / uyanış bayrağı / son yanıtı */
const motorChatSessions = Object.create(null);

const MOTOR_CHAT_MODES = [
  "genel",
  "ses",
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

function getMotorChatSession(mode) {
  const key = normalizeMotorChatMode(mode || activeMotorChatMode());
  if (!motorChatSessions[key]) {
    motorChatSessions[key] = {
      history: [],
      sessionWakeUsed: false,
      lastAssistantReply: "",
    };
  }
  return motorChatSessions[key];
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
}

/** Motor değişince sohbet panelini o motorun oturumuna bağla */
function renderMotorChatFromSession(mode) {
  if (!el.chat) return;
  const key = normalizeMotorChatMode(mode || activeMotorChatMode());
  const sess = getMotorChatSession(key);
  el.chat.innerHTML = "";
  clearOrchestraBridge();
  for (const msg of sess.history) {
    const role = String(msg?.role || "").toLowerCase();
    const content = String(msg?.content || "");
    if (!content) continue;
    if (role === "user") {
      appendBubble("user", content, { skipSessionSync: true });
    } else {
      appendMotorAssistantBubble(content);
    }
  }
  lastAssistantReply = String(sess.lastAssistantReply || "").trim();
  updateDashboardLastSpeech();
  showChatWelcomeIfEmpty();
  el.chat.scrollTop = el.chat.scrollHeight;
}

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
  const sess = getMotorChatSession(activeMotorChatMode());
  sess.history = [];
  sess.sessionWakeUsed = false;
  sess.lastAssistantReply = "";
  lastAssistantReply = "";
  el.chat.innerHTML = "";
  el.input.value = "";
  clearOrchestraBridge();
  renderDashboardAgentSteps([]);
  showChatWelcomeIfEmpty();
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
      const mode = String(currentMode || "").trim().toLowerCase();
      try {
        /* UI Fix — Üst «Yenile»: yalnızca aktif modül; tam uygulama/Electron reload yok */
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
        if (mode === "okuma") {
          await loadIlimFileList();
          setStatus("İlim dosya listesi yenilendi", "Rüzgar");
          return;
        }
        if (mode === "tercume") {
          await loadTercumeFileList();
          setStatus("Tercüme dosya listesi yenilendi", "Rüzgar");
          return;
        }
        if (mode === "ses") {
          await refreshSesSttHint();
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
          setStatus("Ana motor paneli güncellendi", "Rüzgar");
          return;
        }
      } catch (e) {
        const msg = e && e.message ? String(e.message) : String(e);
        setStatus(`Yenileme: ${msg.slice(0, 120)}`, null);
        return;
      }
      updateDynamicWorkbench();
      setStatus("Çalışma paneli güncellendi", "Rüzgar");
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

function appendBubble(role, text, opts = {}) {
  const div = document.createElement("div");
  let cls = `bubble ${role}`;
  if (role === "assistant" && opts.error) cls += " chat-error-bubble";
  if (role === "assistant" && opts.clarify) cls += " chat-clarify";
  div.className = cls;
  if (role === "assistant" && opts.error) {
    div.innerHTML = renderChatErrorHtml(String(text || ""));
  } else {
    div.innerHTML = esc(text).replace(/\n/g, "<br>");
  }
  el.chat.appendChild(div);
  el.chat.scrollTop = el.chat.scrollHeight;
  if (role === "assistant" && !opts.error && !opts.skipSessionSync) {
    lastAssistantReply = String(text || "").trim();
    const sess = getMotorChatSession(activeMotorChatMode());
    sess.lastAssistantReply = lastAssistantReply;
    updateDashboardLastSpeech();
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
    const r = await fetch(`${base}/api/health`, { method: "GET" });
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
      setAnaMotorInfoStripState("loading");
      if (apiWasOffline) {
        apiWasOffline = false;
        showRuzgarConnectionActiveBanner();
      } else if (!window.__ruzgarConnectionBannerShown) {
        window.__ruzgarConnectionBannerShown = true;
        showRuzgarConnectionActiveBanner();
      }
      lastHealthSnapshot = j;
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
      showStaleBuildBanner(rev);
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

  const chatMode = activeMotorChatMode();
  const chatSess = getMotorChatSession(chatMode);
  const codingMode =
    chatMode === "programlama" || !!(el.code && el.code.checked);
  const body = {
    message: userText,
    history: chatSess.history,
    use_web: el.web
      ? !!el.web.checked
      : !["ses", "okuma", "tercume", "hafiza", "hizli", "programlama"].includes(
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
    if (
      ev.type === "agent_step" &&
      Array.isArray(ev.steps) &&
      ev.steps.length
    ) {
      renderProgramlamaAgentSteps(ev.steps);
      const ca = ev.code_agent || {};
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
        setStatus(`Görev tur ${turn}/${maxT}${phaseTr}`, "Rüzgar");
        showThinkingCenter(`Görev tur ${turn}/${maxT}${phaseTr}`);
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
      updateDashboardLastSpeech();
      updateDynamicWorkbench();
      renderOrchestraBridge(ev.orchestra);
      if (ev.programlama_focus_rel || ev.programlama_project_rel) {
        void applyProgramlamaFocusFromChat(ev);
      }
      if (ev.programlama_delegated) {
        flashRuzgarDurum("Kod sorusu → Programlama motoru (Faz 10 delege).");
        if (el.code && !el.code.checked) {
          el.code.checked = true;
          switchMode("programlama");
        }
      }
      if (ev.code_patch) {
        showProgramlamaPatchStrip(ev.code_patch);
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
      chatSess.history.push({
        role: "user",
        content: ev.user_message || userText,
      });
      chatSess.history.push({ role: "assistant", content: full });
      chatSess.lastAssistantReply = full;
      lastAssistantReply = full;
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
      if (chatSess.history.length > MAX_CLIENT_HISTORY_MSGS) {
        chatSess.history = chatSess.history.slice(-MAX_CLIENT_HISTORY_MSGS);
      }
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
  const chatFullTimeoutMs = casualShortCmd
    ? 12000
    : egitimCmd
      ? 15000
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

  if (RUZGAR_DISABLE_STREAMING) {
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
            ? "Yanıt zaman aşımı (180 sn) — sunucu yavaş veya Ollama/Gemini bekliyor; Ruzgar.ps1 -ForceRestart deneyin."
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
  if (!skipUser) {
    appendBubble("user", text);
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
    await streamChat(text);
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
      const exportSess = getMotorChatSession(activeMotorChatMode());
      if (!body && exportSess.history.length) {
        body = exportSess.history
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
wireFaz7Cila();
document.body.classList.add("faz7-complete", "faz8-complete");
void refreshUiManifest().finally(() =>
  renderMotorChatFromSession(activeMotorChatMode()),
);
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
refreshPerformanceMetrics();
scheduleMetricsPolling();
loadFileTree();
globalThis.__ruzgarSpeak = speakLast;
