/**
 * Ana Motor hub — Faz B: kabiliyet kaydı + sessiz panel + tam delegasyon
 * Ümit & Gökçenur
 */
(function anaMotorHub(global) {
  "use strict";

  const VERSION = "ana-motor-hub-v10-hub-sse-faz-e-2026-06-11";

  const SERVER_STREAM_MOTORS_D = new Set(["tercume", "video", "programlama"]);
  const SERVER_STREAM_MOTORS_E = new Set([
    "tercume",
    "video",
    "programlama",
    "ses",
    "hafiza",
    "mimar",
    "hizir",
    "okuma",
  ]);

  /** Alt-intent → sentetik sohbet (motor runner) */
  const SUB_INTENT_MSG = {
    video: {
      indir: null,
      kes: null,
      probe: "medya bilgisi",
      oynat: "oynat",
      kurgu: "kurgu yap",
      transcode: "dönüştür",
      mux: "ses ekle mux",
      burn_sub: "altyazı göm",
      concat: "klip birleştir",
      list: "son indirmeler",
    },
    programlama: {
      pytest: "pytest geçir",
      git: "git durumu",
      briefing: "briefing",
      scan: "proje tara",
      self_scan: "self scan",
    },
    hafiza: {
      durum: "hafıza durumu",
      gorev: "görev listesi",
      hatirla: null,
    },
    ses: {
      stt: "metne dök",
      profil: "ses profili",
      oku: null,
      ayar: "ses ayarları",
    },
    tercume: { ara: null, cevir: "bu sayfayı çevir", indir: null },
    mimar: { foto: "fotoğraf paneli aç", sanat: "sanat galerisi", tasarim: "tasarım paneli" },
    hizir: { tara: null, pazar: "pazar yerini tara" },
  };

  function resolveDispatchText(motor, subIntent, originalText) {
    const mid = normalizeMotorId(motor);
    const sub = String(subIntent || "").trim().toLowerCase();
    if (!sub) return originalText;
    const synth = SUB_INTENT_MSG[mid]?.[sub];
    if (synth === null || synth === undefined) return originalText;
    return synth;
  }

  /** Panelli motorlar — genel modda sekme değil, arka plan paneli */
  const PANEL_MOTORS = new Set(["video", "tercume", "mimar", "ses", "hizir"]);

  /** @type {Record<string, any>|null} */
  let deps = null;
  /** @type {Record<string, any>|null} */
  let capabilitiesCache = null;

  function d() {
    return deps || {};
  }

  function fold(text) {
    return String(text || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("tr-TR");
  }

  /** «kuran sesiyle oku: …» → { profil, text } */
  function parseTilavetReadCommand(text) {
    const raw = String(text || "").trim();
    if (!raw) return null;
    const colonRe =
      /(?:^|\b)(kuran|gazel|ilahi|tilavet)\s+ses(?:i(?:yle|ni)?)?(?:\s+(?:ile|le))?\s*(?:oku|seslendir|okut|dinlet)\s*[:：]\s*(.+)$/isu;
    let m = raw.match(colonRe);
    if (m) {
      let prof = String(m[1] || "kuran").toLowerCase();
      if (prof === "tilavet") prof = "kuran";
      const body = String(m[2] || "").trim();
      return body.length >= 2 ? { profil: prof, text: body } : null;
    }
    const inlineRe =
      /^(?:kuran|gazel|ilahi|tilavet)\s+ses(?:i(?:yle|ni)?)?(?:\s+(?:ile|le))?\s*(?:oku|seslendir|okut|dinlet)\s+(.+)$/isu;
    m = raw.match(inlineRe);
    if (!m) return null;
    let prof = String(m[1] || "kuran").toLowerCase();
    if (prof === "tilavet") prof = "kuran";
    const body = String(m[2] || "").trim();
    return body.length >= 2 ? { profil: prof, text: body } : null;
  }

  async function runTilavetReadFromChat(tr) {
    if (!tr?.text) return false;
    prepareMotorContext("ses", true);
    d().setSesTranscript?.(tr.text);
    say(
      `Ümit abi, **${tr.profil}** referans sesiyle okuyorum — XTTS klon (ilk seferde model yüklenebilir, CPU'da birkaç dk sürebilir).`,
    );
    d().setStatus?.("Tilavet…", "Rüzgar");
    try {
      const ok = await d().speakStudioTilavetWithProfil?.(tr.text, tr.profil);
      if (ok === false) {
        say("Ümit abi, ses üretilemedi — durum çubuğundaki hataya bak.", { error: true });
        return false;
      }
      return true;
    } catch (e) {
      say(String(e?.message || e || "Tilavet okuma başarısız."), { error: true });
      return false;
    } finally {
      d().setStatus?.("Ses", "Rüzgar");
    }
  }

  function say(msg, opts) {
    d().appendBubble?.("assistant", msg, opts);
  }

  function isCasualGreeting(raw) {
    const w = fold(raw).replace(/[!?.…]+/g, "").trim();
    if (!w || w.length > 100) return false;
    if (
      /^(selam(?:ünaleyküm|unaleykum)?|aleykumselam|merhaba|hey|slm|günaydın|gunaydin|iyi akşamlar|iyi aksamlar|sa)(\s+(ruzgar|ümit|umi|abi))?$/.test(
        w,
      )
    ) {
      return true;
    }
    if (/^nas(?:ilsin|ılsın|lsin|ıl|il)/.test(w) && w.length < 50) return true;
    if (/^naber|nbr|ne haber/.test(w) && w.length < 40) return true;
    if (/^(?:selam|merhaba|hey|slm)\s+(?:naber|nbr|ne\s*haber|nas[ıi]ls[ıi]n)/.test(w)) return true;
    return false;
  }

  function isHubHelpRequest(raw) {
    const low = fold(raw);
    if (/^(?:hub|ana motor|motorlar)\s*(?:yardım|yardim|help|kabiliyet)?$/.test(low)) return true;
    if (/(?:ne\s+yapabil|hangi\s+motor|motor\s+listesi|kabiliyet)/.test(low) && /yardım|yardim|help|hub|ana/.test(low)) {
      return true;
    }
    return false;
  }

  async function fetchCapabilities() {
    if (capabilitiesCache) return capabilitiesCache;
    try {
      const res = await fetch(`${d().getApi?.()}/api/ana-motor/capabilities`, { method: "GET" });
      if (!res.ok) return null;
      const j = await res.json();
      if (j && j.ok) capabilitiesCache = j;
      return capabilitiesCache;
    } catch {
      return null;
    }
  }

  function hubHelpTextFallback() {
    return (
      "Ümit abi, **Ana Motor** doğal cümleyle işi yapar:\n\n" +
      "· Kod · pytest · git → **Programlama**\n" +
      "· Video indir · kes · altyazı · mux → **Video** (sinema açıksa «indir» yeter)\n" +
      "· Link yapıştır veya **ekran görüntüsü** bırak → OCR ile video/ses/görsel algılanır\n" +
      "· Çok adım: «indir, kes 0:30-1:00, kurgu yap» → **Video planı**\n" +
      "· Çevir · eser ara → **Tercüme**\n" +
      "· Fotoğraf · sanat → **Mimar**\n" +
      "· Ses · metne dök → **Ses**\n" +
      "· Hatırla · görev → **Hafıza**\n" +
      "· Pazar tara → **Hızır**\n\n" +
      "Genel sohbet kalır; panel gerekirse arka planda açılır.\n" +
      `(${VERSION})`
    );
  }

  async function hubHelpText() {
    const cap = await fetchCapabilities();
    if (!cap?.motors) return hubHelpTextFallback();
    const lines = [
      "Ümit abi, **Ana Motor kabiliyet kaydı** — tek sohbetten:",
      "",
    ];
    const entries = Object.entries(cap.motors).sort(
      (a, b) => (b[1]?.priority || 0) - (a[1]?.priority || 0),
    );
    for (const [, spec] of entries) {
      const label = spec?.label_tr || "?";
      const ex = (spec?.examples || [])[0] || "…";
      lines.push(`· **${label}** — «${ex}»`);
    }
    lines.push("", "Genel modda yaz; sohbet kopmaz, panel arka planda açılır.");
    lines.push("", "**Eylem öğret:** `eylem öğret: «tetik» → video/kes` · `eylem paneli`");
    if (cap.learned_actions?.count) {
      lines.push(`Öğrenilen eylem: **${cap.learned_actions.approved_count || 0}** onaylı`);
    }
    lines.push(`(${VERSION})`);
    return lines.join("\n");
  }

  function normalizeMotorId(target) {
    const t = String(target || "").trim().toLowerCase();
    if (t === "okuma") return "mimar";
    return t;
  }

  function prepareMotorContext(mode, fromGenel) {
    if (!fromGenel) {
      d().switchMode?.(mode);
      return;
    }
    if (PANEL_MOTORS.has(mode) && d().openMotorWorkbenchQuiet) {
      d().openMotorWorkbenchQuiet(mode);
    }
  }

  async function workspaceRootQs() {
    if (!d().getWorkspaceRoot) return "";
    try {
      const root = await d().getWorkspaceRoot();
      if (root) return `&workspace_root=${encodeURIComponent(String(root))}`;
    } catch {
      /* ignore */
    }
    return "";
  }

  async function fetchJsonTimeout(url, ms = 3500) {
    const ctrl = new AbortController();
    const tid = global.setTimeout(() => ctrl.abort(), ms);
    try {
      const res = await fetch(url, { method: "GET", signal: ctrl.signal });
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    } finally {
      global.clearTimeout(tid);
    }
  }

  async function fetchLearnedInstant(text) {
    try {
      const rootQs = await workspaceRootQs();
      const j = await fetchJsonTimeout(
        `${d().getApi?.()}/api/ana-motor/learned-instant?message=${encodeURIComponent(String(text || ""))}${rootQs}`,
      );
      return j && j.ok && j.handled ? j : null;
    } catch {
      return null;
    }
  }

  async function fetchHubRoute(text) {
    try {
      const rootQs = await workspaceRootQs();
      const j = await fetchJsonTimeout(
        `${d().getApi?.()}/api/ana-motor/hub-route?message=${encodeURIComponent(String(text || ""))}${rootQs}`,
      );
      return j && j.ok ? j : null;
    } catch {
      return null;
    }
  }

  function serverHubStreamEnabled() {
    return d().isHubSseFazDEnabled?.() !== false;
  }

  function serverStreamMotorSet() {
    if (d().isHubSseFazEEnabled?.() !== false) return SERVER_STREAM_MOTORS_E;
    return SERVER_STREAM_MOTORS_D;
  }

  function shouldRouteViaServerStream(motorId) {
    if (!serverHubStreamEnabled()) return false;
    const mid = normalizeMotorId(motorId);
    return serverStreamMotorSet().has(mid);
  }

  async function fetchMotorDispatch(text, target) {
    const mode = normalizeMotorId(target);
    if (!mode || mode === "genel") return null;
    try {
      const rootQs = await workspaceRootQs();
      const j = await fetchJsonTimeout(
        `${d().getApi?.()}/api/ana-motor/motor-dispatch?message=${encodeURIComponent(String(text || ""))}&target=${encodeURIComponent(mode)}${rootQs}`,
      );
      return j && j.ok ? j : null;
    } catch {
      return null;
    }
  }

  function shouldUseActionCard(target, reply) {
    const mode = normalizeMotorId(target);
    if (mode !== "tercume") return false;
    const body = String(reply || "");
    return /^Adımlar\s*:/im.test(body) || /^Güven\s*:/im.test(body);
  }

  async function dispatchBackendInstant(text, target) {
    const j = await fetchMotorDispatch(text, target);
    if (j?.handled && j.reply) {
      const reply = String(j.reply);
      const opts = shouldUseActionCard(target, reply) ? { actionCard: true } : undefined;
      say(reply, opts);
      return { handled: true, replyShown: true, mode: normalizeMotorId(target) };
    }
    return { handled: false };
  }

  async function dispatchTercume(text) {
    const T = global.RuzgarTercumeAtolye;
    if (!T) return { handled: false };
    if (T.tryAtolyeFromMessage) {
      const hit = await T.tryAtolyeFromMessage(text);
      if (hit?.handled) {
        if (hit.instant && hit.reply) {
          say(hit.reply, { actionCard: true });
          return { handled: true, replyShown: true, mode: "tercume" };
        }
        return { handled: true };
      }
    }
    if (T.isSearchIntent?.(text) && T.runSearch) {
      if (T.setTercumeTab) T.setTercumeTab("ara");
      const ok = await T.runSearch(text);
      if (ok) {
        say("Eser arama sonuçları listelendi — sohbetten devam edebilirsin.");
        return { handled: true };
      }
    }
    const backend = await dispatchBackendInstant(text, "tercume");
    if (backend.handled) return backend;
    return { handled: false };
  }

  async function dispatchMimar(text) {
    const M = global.RuzgarMimarAtolye;
    if (M?.tryAtolyeFromMessage) {
      const hit = await M.tryAtolyeFromMessage(text);
      if (hit?.handled) {
        if (hit.instant && hit.reply) say(hit.reply);
        return { handled: true };
      }
    }
    return dispatchBackendInstant(text, "mimar");
  }

  function shouldFastRouteVideo(text) {
    const V = global.RuzgarVideoChatBrain;
    if (!V) return false;
    if (V.looksLikeMultiStepPlan?.(text)) return true;
    if (V.isVideoIntent?.(text)) return true;
    if (d().hasActiveCinemaSession?.() && V.isVideoActionIntent?.(text)) return true;
    return false;
  }

  async function tryVideoFromGenel(text, motorCtx) {
    if (serverHubStreamEnabled()) return { handled: false };
    if (!shouldFastRouteVideo(text)) return { handled: false };
    const out = await dispatchToMotor("video", text, { fromGenel: true, motorCtx });
    if (!out.handled) return { handled: false };
    if (
      out.ok !== false &&
      !out.replyShown &&
      !global.RuzgarVideoChatBrain?.looksLikeMultiStepPlan?.(text)
    ) {
      say("Ümit abi, **Video** talimatın sinemada uygulandı.");
    }
    d().setStatus?.("Ana Motor", "Rüzgar");
    return { handled: true };
  }

  async function dispatchVideo(text, ctx) {
    const V = global.RuzgarVideoChatBrain;
    if (!V?.tryAtolyeFromMessage) return { handled: false };
    const hit = await V.tryAtolyeFromMessage(text, ctx);
    if (!hit?.handled) return { handled: false };
    return { handled: true, ok: hit.ok !== false };
  }

  async function dispatchProgramlama(text) {
    return dispatchBackendInstant(text, "programlama");
  }

  async function dispatchSes(text) {
    const tilavetRead = parseTilavetReadCommand(text);
    if (tilavetRead) {
      const ok = await runTilavetReadFromChat(tilavetRead);
      return { handled: true, ok };
    }
    const low = fold(text);
    if (
      /(?:videodaki|sinemadaki|videonun)\s+ses|ses(?:i|ini)?\s+(?:klonla|referans)|(?:kuran|gazel|ilahi)\s+ses(?:i|ini)?\s+(?:yap|al|klonla)/.test(
        low,
      )
    ) {
      const V = global.RuzgarVideoChatBrain;
      if (V?.tryAtolyeFromMessage) {
        prepareMotorContext("video", true);
        const hit = await V.tryAtolyeFromMessage(text);
        if (hit?.handled) return { handled: true };
      }
    }
    if (/(?:metne\s+d[öo]k|transkript|whisper|stt\b)/.test(low)) {
      if (d().hasSesFileSelected?.()) {
        await d().runSesSttFromFile?.();
        return { handled: true };
      }
      say("Ümit abi, sağ panelden ses dosyası seç — «metne dök» deyince Whisper ile dökerim.");
      return { handled: true };
    }
    return dispatchBackendInstant(text, "ses");
  }

  async function dispatchHafiza(text) {
    return dispatchBackendInstant(text, "hafiza");
  }

  async function dispatchHizir(text) {
    if (d().runHizirFromChat?.(text)) {
      say("Hızır panelinde tarama başlatıldı.");
      return { handled: true };
    }
    return dispatchBackendInstant(text, "hizir");
  }

  const DISPATCHERS = {
    video: dispatchVideo,
    tercume: dispatchTercume,
    mimar: dispatchMimar,
    programlama: dispatchProgramlama,
    ses: dispatchSes,
    hafiza: dispatchHafiza,
    hizir: dispatchHizir,
  };

  async function dispatchToMotor(target, text, opts) {
    const fromGenel = opts?.fromGenel ?? d().getCurrentMode?.() === "genel";
    const mode = normalizeMotorId(target);
    const label = d().motorLabel?.(mode) || mode;
    if (fromGenel && shouldRouteViaServerStream(mode)) {
      d().clearHubQuietMotor?.();
      return { handled: false, mode, label, fromGenel };
    }
    prepareMotorContext(mode, fromGenel);

    const fn = DISPATCHERS[mode];
    let result = { handled: false };
    const subIntent = opts?.subIntent || opts?.learnedAction?.sub_intent;
    const dispatchText = subIntent ? resolveDispatchText(mode, subIntent, text) : text;
    const motorCtx = opts?.motorCtx || null;
    if (fn) {
      result = await fn(dispatchText, motorCtx);
    } else {
      say(`**${label}** motoruna yönlendirdim.`);
      result = { handled: true };
    }

    if (result.handled) {
      d().setStatus?.(fromGenel ? "Ana Motor" : label, "Rüzgar");
    } else if (fromGenel) {
      d().clearHubQuietMotor?.();
    }
    return { ...result, switched: !fromGenel, mode, label, fromGenel };
  }

  function showOrchestraFromRoute(route) {
    if (!route || !d().renderOrchestraBridge) return;
    const orch = route.orchestra;
    if (
      orch &&
      (orch.active_motor || (Array.isArray(orch.motors) && orch.motors.length))
    ) {
      d().renderOrchestraBridge(orch);
      return;
    }
    const tgt = normalizeMotorId(route.target);
    if (!tgt || tgt === "genel") return;
    d().renderOrchestraBridge({
      active_motor: tgt,
      hub_preview: { reason: route.meta?.reason },
      hub: { channel: String(route.meta?.reason || "") },
      motors: [
        {
          id: tgt,
          label: route.target_label || tgt,
          handoff: "",
        },
      ],
    });
  }

  async function tryDispatchFromGenel(text, motorCtx) {
    if (!deps) return { handled: false };
    if (d().getCurrentMode?.() !== "genel") return { handled: false };

    const raw = String(text || "").trim();
    if (!raw) return { handled: false };

    if (isHubHelpRequest(raw)) {
      say(await hubHelpText());
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    if (isCasualGreeting(raw)) {
      say(
        "Aleyküm selam Ümit abi. **Ana Motor** hazır — buradan video, tercüme, kod, hafıza… " +
          "Ne istersen söyle. Liste: **hub yardım** · Eylem: **eylem öğret: «…» → video**",
      );
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    const learnedInstant = await fetchLearnedInstant(raw);
    if (learnedInstant?.reply) {
      if (learnedInstant.reply === "__OPEN_EYLEM_PANEL__") {
        d().openEylemPanel?.();
        say("Ümit abi, **Eylem yönetim paneli** açıldı.");
      } else {
        say(learnedInstant.reply, { actionCard: true });
      }
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    if (/^eylem\s+paneli\s*$/i.test(fold(raw))) {
      d().openEylemPanel?.();
      say("Ümit abi, **Eylem yönetim paneli** açıldı.");
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    const videoFast = await tryVideoFromGenel(raw, motorCtx);
    if (videoFast.handled) return videoFast;

    const tilavetRead = parseTilavetReadCommand(raw);
    if (tilavetRead) {
      const out = await dispatchToMotor("ses", raw, { fromGenel: true, motorCtx });
      if (out.handled && out.ok !== false) {
        say(`Ümit abi, **${tilavetRead.profil}** sesiyle okuma tamamlandı (sohbet Ana Motor'da).`);
        return { handled: true };
      }
      if (out.handled) return { handled: true, ok: false };
    }

    const route = await fetchHubRoute(raw);
    if (route) showOrchestraFromRoute(route);
    if (route?.target && shouldRouteViaServerStream(route.target)) {
      return { handled: false };
    }
    if (!route || !route.target || route.target === "genel") {
      if (
        motorCtx?.understanding?.motorHint &&
        motorCtx.understanding.motorHint !== "genel" &&
        !shouldRouteViaServerStream(motorCtx.understanding.motorHint)
      ) {
        const hintOut = await dispatchToMotor(motorCtx.understanding.motorHint, raw, {
          fromGenel: true,
          motorCtx,
        });
        if (hintOut.handled) {
          if (!hintOut.replyShown) {
            const lbl = d().motorLabel?.(motorCtx.understanding.motorHint) || motorCtx.understanding.motorHint;
            say(`Ümit abi, **${lbl}** — sohbet akışından anladım ve uyguladım.`);
          }
          return { handled: true };
        }
      }
      return { handled: false };
    }

    const label = route.target_label || route.target;
    const learned = route.meta?.learned_action;
    const out = await dispatchToMotor(route.target, raw, {
      fromGenel: true,
      learnedAction: learned,
      subIntent: learned?.sub_intent,
      motorCtx,
    });
    if (out.handled && out.ok !== false) {
      if (!out.replyShown) {
        const sub = learned?.sub_intent ? `/${learned.sub_intent}` : "";
        const extra = learned?.trigger
          ? ` (öğrenilen: «${learned.trigger}»→${learned.motor}${sub})`
          : "";
        say(`Ümit abi, **${label}** — hallettim.${extra}`);
      }
      return { handled: true };
    }
    if (out.handled && out.ok === false) {
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }
    return { handled: false };
  }

  async function tryDispatchActiveMotor(text, motorCtx) {
    const mode = normalizeMotorId(d().getCurrentMode?.() || "genel");
    if (mode === "genel") return { handled: false };

    const fn = DISPATCHERS[mode];
    if (fn) return fn(text, motorCtx);
    return { handled: false };
  }

  function showChatWelcome(container) {
    if (!container) return;
    const w = document.createElement("div");
    w.className = "bubble assistant chat-welcome";
    w.setAttribute("role", "note");
    w.innerHTML =
      `<p class="chat-welcome-lead"><strong>Ana Motor — tek sohbet, tüm motorlar.</strong></p>` +
      `<p>Buradan yaz; gerekirse panel arka planda açılır, sohbet <strong>genel</strong> kalır.</p>` +
      `<ul class="chat-welcome-list">` +
      `<li><strong>Video:</strong> «indir» · «kes 0:30-1:00» · link yapıştır (YouTube/Dailymotion)</li>` +
      `<li><strong>Kod:</strong> pytest geçir · git durumu · proje tara · briefing</li>` +
      `<li><strong>Tercüme:</strong> eser ara · bu sayfayı çevir</li>` +
      `<li><strong>Hafıza:</strong> hatırla: … · görev listesi · hafıza durumu</li>` +
      `<li><strong>Ses:</strong> «kuran sesiyle oku: …» · gazel · ilahi · metne dök</li>` +
      `<li><strong>Öğren:</strong> <code>eylem öğret: «tetik» → video/kes</code></li>` +
      `<li><strong>Yönet:</strong> hub yardım · eylem listesi · eylem paneli</li>` +
      `</ul>` +
      `<p class="chat-welcome-foot">${VERSION} · Ümit &amp; Gökçenur</p>`;
    container.appendChild(w);
  }

  function isEylemCommand(raw) {
    const low = fold(raw);
    if (/^eylem\s+paneli\s*$/.test(low)) return true;
    if (/^(?:eylem|komut)\s+(?:öğret|ogret)\s*[:：]/i.test(raw)) return true;
    if (/^eylem\s+(?:listesi|sil|unut|onayla)\s*[:：]?/i.test(raw)) return true;
    return false;
  }

  /**
   * Eylem öğret/liste/panel — tüm modlarda (Video dahil)
   * @returns {Promise<{handled: boolean}>}
   */
  async function tryEylemCommand(text, _motorCtx) {
    const raw = String(text || "").trim();
    if (!raw || !isEylemCommand(raw)) return { handled: false };

    if (/^eylem\s+paneli\s*$/i.test(fold(raw))) {
      d().openEylemPanel?.();
      say("Ümit abi, **Eylem yönetim paneli** açıldı.");
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    const learnedInstant = await fetchLearnedInstant(raw);
    if (learnedInstant?.reply) {
      if (learnedInstant.reply === "__OPEN_EYLEM_PANEL__") {
        d().openEylemPanel?.();
        say("Ümit abi, **Eylem yönetim paneli** açıldı.");
      } else {
        say(learnedInstant.reply, { actionCard: true });
      }
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }
    return { handled: false };
  }

  function init(options) {
    deps = options || {};
    capabilitiesCache = null;
  }

  global.RuzgarAnaMotorHub = {
    VERSION,
    init,
    tryDispatchFromGenel,
    tryDispatchActiveMotor,
    tryEylemCommand,
    isEylemCommand,
    showChatWelcome,
    isHubHelpRequest,
    dispatchToMotor,
    fetchCapabilities,
    parseTilavetReadCommand,
    shouldRouteViaServerStream,
    serverHubStreamEnabled,
  };
})(typeof window !== "undefined" ? window : globalThis);
