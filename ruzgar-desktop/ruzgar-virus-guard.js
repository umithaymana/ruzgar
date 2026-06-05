/**
 * Rüzgar Virüs Koruması — karantina tarama + sesli/metin onay + commit.
 * Ümit & Gökçenur
 */
(function (global) {
  "use strict";

  const VOICE_OK = [
    /tamam\s+indirebilirsin/i,
    /indirebilirsin/i,
    /evet\s+indir/i,
    /^onayla$/i,
    /^tamam$/i,
    /indir\s*onay/i,
  ];

  let _pendingResolve = null;
  let _pendingReject = null;
  let _pendingTimer = null;
  let _bannerEl = null;

  function normalizeVoice(text) {
    return String(text || "")
      .toLowerCase()
      .replace(/[.,!?;:]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function isApprovalPhrase(text) {
    const t = normalizeVoice(text);
    if (!t) return false;
    return VOICE_OK.some((re) => re.test(t));
  }

  function speak(text, speakFn) {
    const fn = speakFn || global.ruzgarSpeak;
    if (typeof fn === "function") {
      fn(text);
    }
  }

  function removeBanner() {
    if (_bannerEl && _bannerEl.parentNode) {
      _bannerEl.parentNode.removeChild(_bannerEl);
    }
    _bannerEl = null;
  }

  function showApprovalBanner(hint) {
    removeBanner();
    const el = document.createElement("div");
    el.className = "ruzgar-virus-guard-banner";
    el.setAttribute("role", "alertdialog");
    el.setAttribute("aria-label", "Virüs koruması onayı");
    el.innerHTML =
      `<strong>Rüzgar Virüs Kalkanı</strong>` +
      `<p>Rüzgar kendi motoruyla taradı; temiz. Onay için mikrofona basılı tutup «<em>${hint || "tamam indirebilirsin"}</em>» deyin ` +
      `veya aşağıdaki düğmeye basın.</p>` +
      `<div class="ruzgar-virus-guard-banner-actions">` +
      `<button type="button" class="btn-primary btn-compact" data-vg-approve>Onayla — indir</button>` +
      `<button type="button" class="btn-secondary btn-compact" data-vg-cancel>İptal</button>` +
      `</div>`;
    document.body.appendChild(el);
    _bannerEl = el;
    el.querySelector("[data-vg-approve]")?.addEventListener("click", () => {
      finishApproval(true);
    });
    el.querySelector("[data-vg-cancel]")?.addEventListener("click", () => {
      finishApproval(false);
    });
  }

  function clearWait() {
    if (_pendingTimer) {
      global.clearTimeout(_pendingTimer);
      _pendingTimer = null;
    }
    _pendingResolve = null;
    _pendingReject = null;
    removeBanner();
  }

  function finishApproval(ok) {
    const res = _pendingResolve;
    const rej = _pendingReject;
    clearWait();
    if (ok && res) res(true);
    else if (!ok && rej) rej(new Error("İndirme onayı iptal edildi."));
  }

  function waitForUserApproval(hint, timeoutMs) {
    return new Promise((resolve, reject) => {
      clearWait();
      _pendingResolve = resolve;
      _pendingReject = reject;
      showApprovalBanner(hint);
      _pendingTimer = global.setTimeout(() => {
        clearWait();
        reject(new Error("Onay süresi doldu (2 dk). Tekrar deneyin."));
      }, timeoutMs || 120000);
    });
  }

  function consumeVoiceApproval(text) {
    if (!_pendingResolve) return false;
    if (!isApprovalPhrase(text)) return false;
    finishApproval(true);
    return true;
  }

  function apiErrorDetail(j, status) {
    const d = j && j.detail;
    if (typeof d === "string" && d.trim()) return d.trim();
    if (Array.isArray(d) && d.length) {
      return d
        .map((x) => (x && (x.msg || x.message)) || "")
        .filter(Boolean)
        .join(" · ");
    }
    if (j && typeof j.error === "string" && j.error.trim()) return j.error.trim();
    if (j && typeof j.tts_message === "string" && j.tts_message.trim()) return j.tts_message.trim();
    return `Tarama hatası (${status})`;
  }

  async function preflight(apiBase, url, kind, filenameHint) {
    const fd = new FormData();
    fd.append("url", url);
    fd.append("kind", kind || "url");
    if (filenameHint) fd.append("filename_hint", filenameHint);
    const res = await fetch(`${apiBase}/api/ruzgar/virus-guard/preflight`, {
      method: "POST",
      body: fd,
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(apiErrorDetail(j, res.status));
    }
    return j;
  }

  async function commit(apiBase, pendingId, target) {
    const fd = new FormData();
    fd.append("pending_id", pendingId);
    if (target?.abs) fd.append("target_abs", target.abs);
    if (target?.rel) fd.append("target_dir_rel", target.rel);
    const res = await fetch(`${apiBase}/api/ruzgar/virus-guard/commit`, {
      method: "POST",
      body: fd,
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(typeof j.detail === "string" ? j.detail : "Onay sonrası taşıma başarısız");
    }
    return j;
  }

  async function reject(apiBase, pendingId) {
    const fd = new FormData();
    fd.append("pending_id", pendingId);
    try {
      await fetch(`${apiBase}/api/ruzgar/virus-guard/reject`, { method: "POST", body: fd });
    } catch (_) {
      /* ignore */
    }
  }

  async function runUrlDownload(opts) {
    const apiBase = opts.apiBase;
    const url = String(opts.url || "").trim();
    if (!url) throw new Error("URL yok.");
    if (opts.flash) opts.flash("Rüzgar Virüs Kalkanı: karantinaya indiriliyor ve taranıyor…");

    const pre = await preflight(apiBase, url, "url", opts.filenameHint || "");
    const scan = pre.scan || {};
    const layerN = (scan.layers || []).length;
    const risk = scan.risk_score ?? 0;
    if (opts.flash) {
      opts.flash(
        `Rüzgar Virüs Kalkanı: ${layerN} katman · risk ${risk}/100 — sesli onay bekleniyor…`
      );
    }
    speak(pre.tts_message || "Dosyayı taradım. Onay verir misin?", opts.speak);

    try {
      await waitForUserApproval(pre.voice_prompt_hint || "tamam indirebilirsin", opts.approvalTimeoutMs);
    } catch (err) {
      await reject(apiBase, pre.pending_id);
      throw err;
    }

    if (opts.flash) opts.flash("Onay alındı, dosya hedef klasöre taşınıyor…");
    const out = await commit(apiBase, pre.pending_id, {
      abs: opts.targetAbs,
      rel: opts.targetDirRel,
    });
    if (pre.tts_after_commit) speak(pre.tts_after_commit, opts.speak);
    if (typeof opts.onSuccess === "function") opts.onSuccess(out, pre);
    return out;
  }

  async function runVideoDownload(opts) {
    const apiBase = opts.apiBase;
    const url = String(opts.url || "").trim();
    if (!url) throw new Error("Video URL yok.");
    if (opts.flash) opts.flash("Rüzgar Virüs Kalkanı: video karantinaya indiriliyor ve taranıyor…");

    const pre = await preflight(apiBase, url, "video");
    const autoApprove = !!pre.auto_approve || pre.phase === "auto_approved";

    if (autoApprove) {
      if (opts.flash) opts.flash("Video temiz — otomatik onay (YouTube). Teslim ediliyor…");
    } else {
      if (opts.flash) opts.flash("Video tarandı. Sesli onay bekleniyor…");
      speak(pre.tts_message || "Videoyu taradım. Onay verir misin?", opts.speak);

      try {
        await waitForUserApproval(pre.voice_prompt_hint || "tamam indirebilirsin", opts.approvalTimeoutMs);
      } catch (err) {
        await reject(apiBase, pre.pending_id);
        throw err;
      }
    }

    if (opts.flash && !autoApprove) opts.flash("Onay alındı, video teslim ediliyor…");
    const out = await commit(apiBase, pre.pending_id, {});
    if (pre.tts_after_commit && !autoApprove) speak(pre.tts_after_commit, opts.speak);
    if (typeof opts.onSuccess === "function") opts.onSuccess(out, pre);
    const meta = pre.video_metadata || {};
    const rel = String(out.rel || meta.file_path || "").trim();
    return {
      ...out,
      result: {
        ...meta,
        file_path: rel || meta.file_path || "",
        title: meta.title || out.filename || "",
        ok: out.ok !== false,
      },
    };
  }

  global.RuzgarVirusGuard = {
    version: "ruzgar-virus-guard-ui-v1",
    isApprovalPhrase,
    consumeVoiceApproval,
    runUrlDownload,
    runVideoDownload,
    preflight,
    commit,
    reject,
  };
})(window);
