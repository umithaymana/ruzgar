/** Bulut/Railway: ?api=https://... veya localStorage.ruzgarApi */
const API =
  new URLSearchParams(window.location.search).get("api") ||
  (typeof localStorage !== "undefined"
    ? localStorage.getItem("ruzgarApi")
    : null) ||
  "http://127.0.0.1:8777";
/** Sunucudaki prior_messages limitiyle uyumlu; gereksiz büyük JSON göndermez */
const MAX_CLIENT_HISTORY_MSGS = 32;

const MODE_QS = new URLSearchParams(window.location.search);
const MODE = (MODE_QS.get("mode") || "genel").trim().toLowerCase();

const MODE_LABELS = {
  genel: "Genel",
  uretim: "Üretim",
  gelisim: "Gelişim",
  ses: "Ses",
  okuma: "Okuma",
  video: "Video",
  programlama: "Programlama",
  duzen: "Düzen",
  dosya: "Dosya",
  hizli: "Hızlı",
};

const el = {
  chat: document.getElementById("chat-messages"),
  input: document.getElementById("msg-input"),
  send: document.getElementById("btn-send"),
  mic: document.getElementById("btn-mic"),
  web: document.getElementById("opt-web"),
  linkRead: document.getElementById("opt-link-read"),
  fetchN: document.getElementById("opt-fetch"),
  code: document.getElementById("opt-code"),
  voiceOut: document.getElementById("opt-voice-out"),
  voiceSend: document.getElementById("opt-voice-send"),
  api: document.getElementById("api-status"),
  modeBadge: document.getElementById("mode-badge"),
  statusR: document.getElementById("status-right"),
  statusL: document.getElementById("status-left"),
  tree: document.getElementById("file-tree"),
  navBack: document.getElementById("nav-back"),
  navForward: document.getElementById("nav-forward"),
  navRefresh: document.getElementById("nav-refresh"),
  navClearChat: document.getElementById("nav-clear-chat"),
};

function syncWebFetchUi() {
  if (el.fetchN) el.fetchN.disabled = !el.web.checked;
}

function applyModeToUI() {
  const label = MODE_LABELS[MODE] || MODE;
  if (el.modeBadge) el.modeBadge.textContent = label;
  document.title = `RÜZGAR — ${label}`;
  if (MODE === "programlama") el.code.checked = true;
  if (["ses", "okuma", "uretim", "hizli"].includes(MODE)) {
    el.web.checked = false;
  } else {
    el.web.checked = true;
  }
  syncWebFetchUi();
}
applyModeToUI();
if (el.web) el.web.addEventListener("change", syncWebFetchUi);

/** @type {{role:string, content:string}[]} */
let chatHistory = [];
let sessionWakeUsed = false;
let lastAssistantReply = "";

function setStatus(right, left) {
  if (right != null) el.statusR.textContent = right;
  if (left != null) el.statusL.textContent = left;
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

async function checkApi() {
  try {
    const r = await fetch(`${API}/api/health`, { method: "GET" });
    const j = await r.json();
    if (j.ok) {
      el.api.textContent = j.stt ? "API ✓ STT" : "API ✓";
      el.api.title = j.stt
        ? "desktop_server + yerel Whisper STT"
        : "API açık — pip install faster-whisper ile STT ekleyin";
      el.api.className = "panel-badge ok";
      setStatus("Hazır", "Rüzgar");
      return true;
    }
  } catch {
    el.api.textContent = "API kapalı";
    el.api.className = "panel-badge err";
    el.api.title = "";
    setStatus("Önce desktop_server.py çalıştır", "Rüzgar");
  }
  return false;
}

async function streamChat(userText) {
  let workspaceRoot = null;
  try {
    if (window.ruzgarApi?.getRoot) {
      workspaceRoot = await window.ruzgarApi.getRoot();
    }
  } catch {
    workspaceRoot = null;
  }
  const body = {
    message: userText,
    history: chatHistory,
    use_web: el.web.checked,
    read_message_links:
      el.linkRead == null ? true : !!el.linkRead.checked,
    fetch_pages: Number.parseInt(String(el.fetchN?.value ?? "1"), 10) || 0,
    coding_mode: el.code.checked,
    session_wake_used: sessionWakeUsed,
    mode: MODE,
    workspace_root: workspaceRoot || undefined,
  };

  const res = await fetch(`${API}/api/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      Accept: "text/event-stream",
      "Accept-Charset": "utf-8",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const dec = new TextDecoder("utf-8");
  let buf = "";
  let full = "";
  const bubble = document.createElement("div");
  bubble.className = "bubble assistant";
  el.chat.appendChild(bubble);

  function consumeBlock(block) {
    const line = block.trim();
    if (!line.startsWith("data:")) return;
    const jsonStr = line.slice(5).trim();
    try {
      const ev = JSON.parse(jsonStr);
      if (ev.type === "token" && ev.text) {
        full += ev.text;
        bubble.innerHTML = esc(repairMojibake(full));
        el.chat.scrollTop = el.chat.scrollHeight;
        setStatus("Yazıyor…");
      } else if (ev.type === "done") {
        const streamed = repairMojibake(full);
        const srv = repairMojibake(ev.full_reply || "");
        let merged = srv || streamed;
        if (looksLikeMojibake(srv) && streamed.length > 0 && !looksLikeMojibake(streamed)) {
          merged = streamed + extractYerelFooter(srv);
        }
        full = stripYerelFooter(merged);
        sessionWakeUsed = !!ev.new_wake_used;
        bubble.innerHTML = esc(full);
        lastAssistantReply = full;
        chatHistory.push({ role: "user", content: ev.user_message || userText });
        chatHistory.push({ role: "assistant", content: full });
        if (el.voiceOut == null || el.voiceOut.checked) {
          window.setTimeout(() => speakLast(), 80);
        }
        if (chatHistory.length > MAX_CLIENT_HISTORY_MSGS) {
          chatHistory = chatHistory.slice(-MAX_CLIENT_HISTORY_MSGS);
        }
        setStatus("Hazır");
      } else if (ev.type === "error") {
        bubble.innerHTML = esc(ev.text || "Hata");
        setStatus("Hata");
      }
    } catch {
      /* kesik JSON */
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() || "";
    for (const block of parts) consumeBlock(block);
  }
  if (buf.trim()) consumeBlock(buf);
}

async function sendMessageWithText(t) {
  const text = (t || "").trim();
  if (!text) return;
  const ok = await checkApi();
  if (!ok) return;

  el.input.value = "";
  appendBubble("user", text);
  el.send.disabled = true;
  setStatus("İstek…");

  try {
    await streamChat(text);
  } catch (e) {
    appendBubble("assistant", String(e));
    setStatus("Hata");
  } finally {
    el.send.disabled = false;
  }
}

async function sendMessage() {
  const t = el.input.value.trim();
  if (!t) return;
  await sendMessageWithText(t);
}

/** Yerel Whisper STT (MediaRecorder → /api/stt). Google Web Speech kullanılmaz. */
let recState = null;
/** Basılı tutunca kayıt */
let micPressed = false;
/** Bırakınca Konuşunca gönder */
let pushSessionSend = false;
/** ses → Mikrofon menü oturumu (zamanlayıcı iptali) */
let menuMicToken = 0;

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
  return typeof j.text === "string" ? j.text : "";
}

async function finalizeRecording(state) {
  if (state.timer) {
    clearTimeout(state.timer);
    state.timer = null;
  }
  el.mic.classList.remove("recording");
  setStatus("Metne çevriliyor…", "Rüzgar");
  let blob;
  try {
    blob = await blobFromStoppedRecorder(state);
  } catch (e) {
    setStatus(String(e && e.message ? e.message : e), "Rüzgar");
    pushSessionSend = false;
    return;
  }
  if (!blob || blob.size < 64) {
    setStatus("Ses kaydı çok kısa", "Rüzgar");
    pushSessionSend = false;
    return;
  }
  let text = "";
  try {
    text = await postSttBlob(blob);
  } catch (e) {
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
    void sendMessageWithText(full);
  }
  pushSessionSend = false;
  setStatus("Hazır", "Rüzgar");
}

async function startBtnRecording() {
  await discardActiveRecording();
  if (!navigator.mediaDevices?.getUserMedia) {
    throw new Error("Bu ortamda mikrofon API yok.");
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  window.__ruzgarMicOk = true;
  const mime = pickRecorderMime();
  const recorder = new MediaRecorder(
    stream,
    mime ? { mimeType: mime } : undefined
  );
  const chunks = [];
  recorder.ondataavailable = (ev) => {
    if (ev.data && ev.data.size) chunks.push(ev.data);
  };
  recorder.start(120);
  recState = { kind: "btn", stream, recorder, chunks, mime };
  el.mic.classList.add("recording");
  setStatus("Dinleniyor… (bırakınca Whisper)", "Rüzgar");
}

async function micPointerDown(e) {
  if (e.pointerType === "mouse" && e.button !== 0) return;
  e.preventDefault();
  try {
    el.mic.setPointerCapture(e.pointerId);
  } catch (_) {}
  if (micPressed) return;
  micPressed = true;
  pushSessionSend = true;
  try {
    await startBtnRecording();
  } catch (err) {
    micPressed = false;
    pushSessionSend = false;
    setStatus(err && err.message ? err.message : String(err), "Rüzgar");
  }
}

async function micPointerUp(e) {
  if (micPressed) {
    micPressed = false;
    try {
      el.mic.releasePointerCapture(e.pointerId);
    } catch (_) {}
    const s = recState;
    if (s && s.kind === "btn") {
      recState = null;
      await finalizeRecording(s);
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
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    window.__ruzgarMicOk = true;
    const mime = pickRecorderMime();
    const recorder = new MediaRecorder(
      stream,
      mime ? { mimeType: mime } : undefined
    );
    const chunks = [];
    recorder.ondataavailable = (ev) => {
      if (ev.data && ev.data.size) chunks.push(ev.data);
    };
    recorder.start(120);
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
    };
    el.mic.classList.add("recording");
    setStatus("Dinleniyor… (en fazla 12 sn)", "Rüzgar");
  } catch (err) {
    pushSessionSend = false;
    setStatus(err && err.message ? err.message : String(err), "Rüzgar");
  }
}

function speakLast() {
  if (!lastAssistantReply) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(lastAssistantReply);
  u.lang = "tr-TR";
  window.speechSynthesis.speak(u);
  setStatus("Sesli okuma…");
  u.onend = () => setStatus("Hazır");
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

el.send.addEventListener("click", sendMessage);
el.input.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key === "Enter") {
    e.preventDefault();
    sendMessage();
  }
});
el.mic.addEventListener("pointerdown", (e) => {
  void micPointerDown(e);
});
el.mic.addEventListener("pointerup", micPointerUp);
el.mic.addEventListener("pointercancel", micPointerUp);
el.mic.addEventListener("lostpointercapture", micPointerUp);
/* pointerleave kaldırıldı: kenarda milimetrelik hareket “bırakıldı” sanıp tanımayı kesiyor + Windows’ta çok sayıda erişim kaydı */

if (window.ruzgarApi?.onMenu) {
  window.ruzgarApi.onMenu((action) => {
    if (action === "focus-chat") el.input.focus();
    if (action === "mic") void menuOpenMic();
    if (action === "speak") speakLast();
  });
}

wireNavToolbar();
checkApi();
setInterval(checkApi, 15000);
loadFileTree();
globalThis.__ruzgarSpeak = speakLast;
