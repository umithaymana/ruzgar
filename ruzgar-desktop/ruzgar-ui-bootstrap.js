/**
 * app.js yuklenmeden once: surum goster, motor tikla, JS hata yakala, kritik tus yedegi.
 */
(function ruzgarUiBootstrap(global) {
  "use strict";
  const REV = "20260620-btn-fallback";
  global.__RUZGAR_UI_REV_BOOT = REV;

  const sr = global.document.getElementById("status-right");
  const apiChip = global.document.getElementById("api-status");
  if (sr) sr.textContent = "UI " + REV;

  function markJsFault(label) {
    if (sr) sr.textContent = String(label || "JS HATA").slice(0, 48) + " · " + REV;
    if (apiChip) {
      apiChip.textContent = "JS hata";
      apiChip.className = "tech-chip err";
    }
  }

  global.addEventListener("error", (ev) => {
    const msg = String(ev.message || "JS hatasi").slice(0, 80);
    markJsFault("JS HATA");
    try {
      global.console.error("[RUZGAR bootstrap]", msg, ev.filename, ev.lineno);
    } catch (_) {
      /* ignore */
    }
  });

  global.addEventListener("unhandledrejection", (ev) => {
    const msg = String(ev.reason?.message || ev.reason || "promise").slice(0, 80);
    markJsFault("JS HATA");
    try {
      global.console.error("[RUZGAR bootstrap] unhandledrejection", msg);
    } catch (_) {
      /* ignore */
    }
  });

  /** Gorunmez modal / dusunme katmani tiklamalari yutuyorsa kapat */
  function dismissStuckOverlays() {
    const ids = [
      "sistem-ayarlari-overlay",
      "hafiza-yonet-overlay",
      "eylem-yonet-overlay",
      "kisisel-panel-overlay",
      "faz7-help-overlay",
      "thinking-center-overlay",
      "ruzgar-slide-host",
    ];
    for (const id of ids) {
      const node = global.document.getElementById(id);
      if (!node || node.hidden) continue;
      node.hidden = true;
      node.setAttribute("aria-hidden", "true");
      node.classList.remove("is-open");
    }
    global.document.body.classList.remove("ruzgar-split-dragging", "core-busy");
  }

  global.document.addEventListener(
    "click",
    (ev) => {
      const t = ev.target;
      if (!(t instanceof Element)) return;

      const modeBtn = t.closest(
        "button[data-mode], .motor-item[data-mode], .mode-tab[data-mode]",
      );
      if (modeBtn && !modeBtn.disabled) {
        const mode = String(modeBtn.getAttribute("data-mode") || "")
          .trim()
          .toLowerCase();
        if (mode) {
          if (typeof global.switchMode === "function") {
            global.switchMode(mode);
          } else {
            global.__RUZGAR_PENDING_MODE = mode;
          }
        }
        return;
      }

      const sendBtn = t.closest("#btn-send");
      if (sendBtn && !sendBtn.disabled && typeof global.sendMessage === "function") {
        ev.preventDefault();
        void global.sendMessage();
        return;
      }

      if (t.closest("#nav-refresh")) {
        ev.preventDefault();
        try {
          global.location.reload();
        } catch (_) {
          /* ignore */
        }
        return;
      }

      if (t.closest("#nav-clear-chat") && typeof global.clearChatSession === "function") {
        ev.preventDefault();
        void global.clearChatSession({ confirm: true });
      }
    },
    true,
  );

  function flushPendingMode() {
    const pending = global.__RUZGAR_PENDING_MODE;
    if (!pending || typeof global.switchMode !== "function") return;
    global.switchMode(pending);
    global.__RUZGAR_PENDING_MODE = null;
  }

  function watchAppReady() {
    flushPendingMode();
    if (global.__RUZGAR_APP_SEND_READY) {
      if (sr && String(sr.textContent || "").startsWith("JS HATA")) return;
      return;
    }
    if (sr && !String(sr.textContent || "").includes("JS HATA")) {
      sr.textContent = "app.js bekleniyor… Ctrl+Shift+R";
    }
  }

  global.addEventListener("DOMContentLoaded", () => {
    dismissStuckOverlays();
    const voiceSend = global.document.getElementById("opt-voice-send");
    if (voiceSend) voiceSend.checked = false;
    const codeMode = global.document.getElementById("opt-code");
    if (codeMode) codeMode.checked = false;
    const micWrap = global.document.getElementById("mic-level-wrap");
    if (micWrap) {
      micWrap.hidden = true;
      micWrap.setAttribute("aria-hidden", "true");
    }
    const send = global.document.getElementById("btn-send");
    if (send) send.disabled = false;

    global.setTimeout(flushPendingMode, 0);
    global.setTimeout(watchAppReady, 2500);
    global.setTimeout(watchAppReady, 6000);
  });
})(typeof window !== "undefined" ? window : globalThis);
