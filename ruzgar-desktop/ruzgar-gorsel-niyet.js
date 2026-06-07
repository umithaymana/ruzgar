/**
 * Ekran görüntüsü → OCR + motor aktivasyonu (Ümit & Gökçenur)
 */
(function ruzgarGorselNiyet(global) {
  "use strict";

  const VERSION = "ruzgar-gorsel-niyet-v1-2026-06-06";
  let motorPulseTimer = null;

  /** @type {Record<string, any>|null} */
  let deps = null;

  function d() {
    return deps || {};
  }

  function normalizeMotor(mode) {
    const m = String(mode || "").trim().toLowerCase();
    return m === "okuma" ? "mimar" : m;
  }

  function clearMotorActivations() {
    document.querySelectorAll(".motor-item.is-niyet").forEach((el) => {
      el.classList.remove("is-niyet");
    });
    if (motorPulseTimer) {
      global.clearTimeout(motorPulseTimer);
      motorPulseTimer = null;
    }
  }

  function showMotorActivations(activations, opts) {
    clearMotorActivations();
    const list = Array.isArray(activations) ? activations : [];
    const modes = list.map((a) => normalizeMotor(a?.motor)).filter(Boolean);
    if (!modes.length && opts?.fallbackMotor) {
      modes.push(normalizeMotor(opts.fallbackMotor));
    }
    for (const mode of modes) {
      const btn =
        document.querySelector(`.panel-motors .motor-item[data-mode="${mode}"]`) ||
        document.getElementById(`motor-side-${mode}`);
      if (btn) btn.classList.add("is-niyet");
    }
    if (modes.length) {
      motorPulseTimer = global.setTimeout(clearMotorActivations, opts?.durationMs || 12000);
    }
    return modes;
  }

  async function analyzeImageFile(file, hint) {
    const api = d().getApi?.() || "";
    if (!api) throw new Error("API kökü yok.");
    const fd = new FormData();
    fd.append("file", file, file.name || "ruzgar-screenshot.png");
    if (hint) fd.append("hint", hint);
    const res = await fetch(`${api}/api/vision/analyze`, { method: "POST", body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok || j.ok === false) {
      throw new Error(j.detail || j.summary || `HTTP ${res.status}`);
    }
    return j;
  }

  function buildUnderstandingFromVision(j, hint) {
    const motor = normalizeMotor(j.motor || j.motors?.[0] || "");
    const action = String(j.action_text || hint || "").trim();
    return {
      raw: hint || "📷 Ekran görüntüsü",
      text: action || hint || j.urls?.[0] || "",
      motorHint: motor || "",
      intent: motor ? `${motor}_screenshot` : "screenshot",
      instantMotor: true,
      instantReason: "vision_screenshot",
      fromHistory: false,
      vision: {
        urls: j.urls || [],
        mediaKind: j.media_kind,
        ocrSource: j.ocr_source,
        confidence: j.confidence,
        motor: motor,
      },
    };
  }

  async function dispatchVisionAction(j, hint, motorCtx) {
    const action = String(j.action_text || "").trim();
    if (!action) return { handled: false };
    const understanding = buildUnderstandingFromVision(j, hint);
    const ctx = {
      ...(motorCtx || {}),
      understanding,
      contextBrief: [
        motorCtx?.contextBrief || "",
        j.ocr_text ? `[Ekran OCR] ${String(j.ocr_text).slice(0, 400)}` : "",
      ]
        .filter(Boolean)
        .join("\n"),
    };
    if (d().getCurrentMode?.() === "genel" && global.RuzgarAnaMotorHub?.tryDispatchFromGenel) {
      return global.RuzgarAnaMotorHub.tryDispatchFromGenel(action, ctx);
    }
    if (global.RuzgarAnaMotorHub?.tryDispatchActiveMotor) {
      return global.RuzgarAnaMotorHub.tryDispatchActiveMotor(action, ctx);
    }
    return { handled: false };
  }

  async function handleChatImageFile(file, hint) {
    if (!file || !String(file.type || "").startsWith("image/")) {
      d().flash?.("Yalnızca görüntü dosyası.");
      return { ok: false };
    }
    const userHint = String(hint || "").trim();
    d().appendBubble?.("user", userHint ? `${userHint}\n\n📷 Ekran görüntüsü` : "📷 Ekran görüntüsü");
    d().setStatus?.("Ekran görüntüsü okunuyor…", "Rüzgar");
    try {
      const j = await analyzeImageFile(file, userHint);
      const modes = showMotorActivations(j.activations, { fallbackMotor: j.motor });
      if (j.summary) {
        d().appendBubble?.("assistant", j.summary, { actionCard: true });
      }
      if (modes.length && d().openMotorWorkbenchQuiet) {
        d().openMotorWorkbenchQuiet(modes[0]);
      }
      const priorHistory = d().getSharedChatHistory?.()?.slice?.() || [];
      const hub = await dispatchVisionAction(j, userHint, { history: priorHistory });
      if (hub?.handled) {
        d().setStatus?.(d().getCurrentMode?.() === "genel" ? "Ana Motor" : "Rüzgar", "Rüzgar");
        return { ok: true, handled: true, vision: j };
      }
      if (j.action_text && d().getInputEl?.()) {
        const inp = d().getInputEl();
        if (inp && !inp.value.trim()) inp.value = j.action_text;
      }
      d().setStatus?.("Hazır", "Rüzgar");
      return { ok: true, handled: false, vision: j };
    } catch (e) {
      d().appendBubble?.(
        "assistant",
        `Görsel okunamadı: ${d().formatError?.(e) || e}\n\n` +
          "Tesseract kurulu değilse: `pip install pillow pytesseract` ve sistemde Tesseract. " +
          "Alternatif: linki metin olarak yapıştır.",
        { error: true },
      );
      d().setStatus?.("Hazır", "Rüzgar");
      return { ok: false, error: e };
    }
  }

  function init(options) {
    deps = options || {};
  }

  global.RuzgarGorselNiyet = {
    VERSION,
    init,
    handleChatImageFile,
    analyzeImageFile,
    showMotorActivations,
    clearMotorActivations,
    buildUnderstandingFromVision,
  };
})(typeof window !== "undefined" ? window : globalThis);
