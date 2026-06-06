/**
 * Video motoru — sohbet süper beyin (Ümit & Gökçenur)
 * Talimat → niyet → sinema paneli. Manuel düğmeler yedek kalır.
 */
(function videoChatBrain(global) {
  "use strict";

  const VERSION = "video-super-brain-v5-2026-06-06";

  /** Çok adımlı plan ayırıcı: ve · sonra · virgül */
  const STEP_SPLIT_RE =
    /\s*(?:,\s*|\s+ve\s+|\s+sonra\s+|\s+ardından\s+|\s+ardindan\s+|\s*;\s*|\s*·\s*|\s+ayrıca\s+|\s+ayrica\s+)\s*/i;

  /** @type {Record<string, any>|null} */
  let deps = null;

  function d() {
    return deps || {};
  }

  function fold(text) {
    return String(text || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("tr-TR");
  }

  function el() {
    return d().getEl?.() || {};
  }

  function isVideoIntent(text) {
    const raw = String(text || "").trim();
    if (!raw) return false;
    if (d().extractVideoDownloadUrl?.(raw)) return true;
    if (d().extractVideoPageUrl?.(raw)) return true;
    if (d().isVideoSearchOrPickCommand?.(raw)) return true;
    const low = fold(raw);
    return (
      /\bvideo\b|youtube|youtu\.be|vimeo|tiktok|dailymotion|twitter|x\.com|ffmpeg|sinema|atolye|atölye|kesim|\bkes\b|kurgu|montaj|altyaz|subtitle|mux|transcode|donustur|dönüştür|ffprobe|medya\s+bilgi|indirme|indir\b|klip\b|film\b|oynat|onizleme|önizleme|panel|m3u8/.test(
        low,
      ) || /\.(mp4|mkv|webm|mov|avi|m4v|mp3|wav|srt|vtt|m3u8)\b/i.test(raw)
    );
  }

  function ensureVideo() {
    const mode = d().getCurrentMode?.() || "genel";
    if (mode === "genel" && d().openMotorWorkbenchQuiet) {
      d().openMotorWorkbenchQuiet("video");
      return;
    }
    if (mode !== "video") d().switchMode?.("video");
  }

  function openDock(name) {
    ensureVideo();
    global.RuzgarVideoAtolye?.openDuzenDock?.(name);
  }

  function say(msg, opts) {
    d().appendBubble?.("assistant", msg, opts);
  }

  function getCinema() {
    return d().getCinemaNowPlaying?.() || {};
  }

  function hasActiveCinema() {
    if (d().hasActiveCinemaSession?.()) return true;
    const c = getCinema();
    return !!(String(c.url || "").trim() || String(c.localRel || "").trim());
  }

  function getPlayerTimeSec() {
    const t = d().getVideoPlayerCurrentTimeSec?.();
    return Number.isFinite(t) ? t : null;
  }

  function referencesCurrentVideo(raw) {
    const low = fold(raw);
    return (
      /(?:^|\s)(?:bunu|buna|sunu|şunu|bunun|şunun|videoyu|filmi|klibi|kaydı|kaydi)(?:\s|$)/.test(
        low,
      ) ||
      /(?:sinema(?:da|daki|yi)?|panelde(?:ki)?|oynat(?:ı|i)c(?:ı|i)(?:da|daki)?|açık\s+olan|acik\s+olan|şu\s+an(?:ki)?|su\s+an(?:ki)?)/.test(
        low,
      ) ||
      /(?:oynayan|izlediğim|izledigim)\s+(?:video|film|klip)/.test(low)
    );
  }

  function isVideoActionIntent(text) {
    const low = fold(text);
    return (
      isVideoIntent(text) ||
      /(?:indir|download|kes|trim|kurgu|montaj|mux|dönüştür|donustur|transcode|altyaz|subtitle|medya\s+bilgi|ffprobe|listeye\s+ekle|concat|birleştir|birlestir|kesime?\s+al|oynat|duraklat|durdur|panel)/.test(
        low,
      ) ||
      referencesCurrentVideo(text)
    );
  }

  function wantsCinemaDownload(raw) {
    const low = fold(raw);
    if (!/(?:indir|download|kesime?\s+al|yerel\s+dosya|duzenleme\s+icin|düzenleme\s+için)/.test(low)) {
      return false;
    }
    if (d().extractVideoDownloadUrl?.(raw)) return false;
    if (!hasActiveCinema()) return false;
    return (
      referencesCurrentVideo(raw) ||
      /^(?:indir|download)\b/.test(low) ||
      /sinema/.test(low) ||
      /kesime?\s+al/.test(low) ||
      /yerel/.test(low)
    );
  }

  async function ensureLocalSource(announceChat) {
    const relField = String(el().videoRelWorkspace?.value || "").trim();
    if (relField) return relField;
    const cinema = getCinema();
    if (cinema.localRel) {
      if (el().videoRelWorkspace) el().videoRelWorkspace.value = cinema.localRel;
      return cinema.localRel;
    }
    if (announceChat) {
      say("Ümit abi, sinemadaki videoyu düzenlemek için **yerel dosyaya** indiriyorum…");
    }
    const rel = await d().ensureLocalVideoSourceForEdit?.({
      announce: !announceChat,
      allowDownload: !!announceChat,
    });
    return rel || null;
  }

  function parseExplicitTrimRange(raw) {
    const m = raw.match(
      /(?:kes|trim)\s+(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*[-–]\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)/i,
    );
    if (!m) return null;
    const start = d().parseVideoTimeSec?.(m[1]);
    const end = d().parseVideoTimeSec?.(m[2]);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
    return { start, end };
  }

  function parsePlainSecToken(token) {
    const s = String(token || "").trim().replace(",", ".");
    if (/^\d+:\d+/.test(s)) {
      const v = d().parseVideoTimeSec?.(s);
      return Number.isFinite(v) ? v : null;
    }
    const n = parseFloat(s.replace(/^0+(\d)/, "$1"));
    return Number.isFinite(n) ? n : null;
  }

  function parseNaturalTrimRange(raw) {
    const explicit = parseExplicitTrimRange(raw);
    if (explicit) return explicit;

    const ilaRange =
      raw.match(
        /(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:sn|saniye|sec|dk|dakika|min(?:ute)?)?\s*(?:ila|ile|la|le|-)\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:sn|saniye|sec|dk|dakika|min(?:ute)?)?(?:ler|leri)?(?:\s*(?:arasi|arası|arasinda|arasında|arasi))?/i,
      ) ||
      raw.match(
        /(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:ila|ile|-)\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:saniye|sn|sec|dk|dakika)/i,
      );
    if (ilaRange) {
      const start = parsePlainSecToken(ilaRange[1]);
      const end = parsePlainSecToken(ilaRange[2]);
      if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
        return { start, end };
      }
    }

    const fromTo = raw.match(
      /(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:['']?(?:dan|den|ten))\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:['']?(?:a|e|ya|ye))?\s*kes/i,
    );
    if (fromTo) {
      const start = d().parseVideoTimeSec?.(fromTo[1]);
      const end = d().parseVideoTimeSec?.(fromTo[2]);
      if (Number.isFinite(start) && Number.isFinite(end) && end > start) {
        return { start, end };
      }
    }

    const cur = getPlayerTimeSec();
    const fromHere = raw.match(
      /(?:buradan|su\s*andan|şu\s*andan|simdi(?:ki)?|şimdi(?:ki)?|oynat(?:ı|i)c(?:ı|i)(?:daki)?|konumdan)\s*(?:\d+(?:[.,]\d+)?\s*(?:saniye|sn|sec|dk|dakika|minute|min)\s*)?(?:kes|kırp|kirp|al)?/i,
    );
    const durMatch =
      raw.match(
        /(?:buradan|su\s*andan|şu\s*andan|simdi(?:ki)?|şimdi(?:ki)?|oynat(?:ı|i)c(?:ı|i)(?:daki)?|konumdan)\s*(\d+(?:[.,]\d+)?)\s*(saniye|sn|sec|dk|dakika|minute|min)/i,
      ) ||
      raw.match(/(\d+(?:[.,]\d+)?)\s*(saniye|sn|dk|dakika)\s*(?:lik\s*)?kes/i);
    if (durMatch && cur != null && d().canSeekVideoPlayer?.()) {
      let dur = parseFloat(String(durMatch[1]).replace(",", "."));
      const unit = fold(durMatch[2] || "sn");
      if (/dk|dakika|min/.test(unit)) dur *= 60;
      if (dur > 0) return { start: cur, end: cur + dur };
    }
    if (fromHere && cur != null && d().canSeekVideoPlayer?.()) {
      say(
        "Kaç saniye/dakika keseyim? Örnek: «buradan 30 saniye kes» veya «kes 0:30-1:00»",
        { clarify: true },
      );
      return { needClarify: true };
    }
    if (fromHere && cur == null) {
      say(
        "Web sinemada oynatıcı konumunu okuyamıyorum — saniye yaz: «kes 0:30-1:00» (tam indirme olmadan akıştan keserim).",
        { clarify: true },
      );
      return { needClarify: true };
    }
    return null;
  }

  async function runTrimRange(range, raw) {
    if (!range || range.needClarify) return true;
    ensureVideo();
    openDock("trim");
    if (el().videoStartSec) el().videoStartSec.value = String(range.start.toFixed(2));
    if (el().videoDurationSec) {
      el().videoDurationSec.value = String((range.end - range.start).toFixed(2));
    }
    if (el().videoEndSec) el().videoEndSec.value = "";

    const canStream = d().canStreamEditCinema?.();
    if (canStream) {
      say(
        `Kesim **${range.start.toFixed(1)}–${range.end.toFixed(1)} sn** — oynatılan akıştan alınıyor (**tam indirme yok**)…`,
      );
    } else {
      say(`Kesim **${range.start.toFixed(1)}–${range.end.toFixed(1)} sn** — FFmpeg çalışıyor…`);
    }
    d().setStatus?.("Kesim…", "Rüzgar");

    if (d().runVideoTrimFromCinema) {
      await d().runVideoTrimFromCinema(range);
    } else {
      let rel = await ensureLocalSource(true);
      if (!rel) {
        say("Önce sinemada video aç.", { error: true });
        return true;
      }
      await d().runVideoTrimJob?.();
    }
    d().setStatus?.("Hazır", "Rüzgar");
    return true;
  }

  async function handleCinemaDownload(raw) {
    if (!wantsCinemaDownload(raw)) return false;
    ensureVideo();
    if (!hasActiveCinema()) {
      say("Önce sinemada bir video aç — link ver veya arama yap.", { error: true });
      return true;
    }
    say("Ümit abi, sinemadaki videoyu **yerel dosya** olarak indiriyorum…");
    d().setStatus?.("Video indiriliyor…", "Rüzgar");
    try {
      const result = await d().runCinemaDownloadCurrent?.();
      const rel = String(
        result?.file_path || el().videoRelWorkspace?.value || getCinema().localRel || "",
      ).trim();
      if (rel) {
        if (el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
        await d().loadVideoPreviewFromRel?.(rel);
        say(`Ümit abi, hazır — yerel dosya sinemada.\n\`${rel}\`\n\nArtık «kes …», «medya bilgisi», «kurgu yap» diyebilirsin.`);
      } else {
        say("İndirme tamamlandı ama dosya yolu gelmedi — tekrar dene.", { error: true });
      }
      d().setStatus?.("Hazır", "Rüzgar");
      return true;
    } catch (e) {
      say(`İndirme başarısız: ${d().formatClientChatError?.(e) || e}`, { error: true });
      d().setStatus?.("Hazır", "Rüzgar");
      return true;
    }
  }

  async function tryCompoundVideoPlan(raw) {
    return tryMultiStepVideoPlan(raw);
  }

  function normalizePlanMessage(raw) {
    return String(raw || "")
      .replace(
        /^(?:şu|su|bu|aşağıdaki|asagidaki)\s+(?:işlem|islem|adım|adim|talimat)[^:]*[:：]\s*/i,
        "",
      )
      .replace(/^(?:lütfen|lutfen|rica\s+etsem|rica)\s+/i, "")
      .trim();
  }

  function splitVideoSteps(raw) {
    const text = normalizePlanMessage(raw);
    if (!text) return [];
    const low = fold(text);
    if (!STEP_SPLIT_RE.test(low)) return [text];
    return text
      .split(STEP_SPLIT_RE)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function looksLikeMultiStepPlan(raw) {
    return splitVideoSteps(raw).length >= 2;
  }

  function classifyVideoStep(stepRaw) {
    const raw = String(stepRaw || "").trim();
    if (!raw) return null;
    const low = fold(raw);

    if (wantsCinemaDownload(raw) || (/^(?:indir|download|kesime?\s+al)\b/.test(low) && hasActiveCinema())) {
      return "download";
    }
    if (/(?:medya\s+bilgi|teknik\s+özet|teknik\s+ozet|ffprobe\b)/i.test(raw)) return "probe";
    if (/(?:dönüştür|donustur|transcode|mp4\s+yap|format\s+değiştir)/i.test(low)) return "transcode";
    if (/(?:altyaz[ıi]\s+g[öo]m|subtitle\s+burn|g[öo]m\s+altyaz)/i.test(low)) return "burn_sub";
    if (/(?:\bmux\b|ses\s+ekle|harici\s+ses|ses\s+videoya)/i.test(low)) return "mux";
    if (/(?:listeye\s+ekle|kurgu\s+listesine|kurguya\s+ekle|bin\s+e)/i.test(low)) return "add_bin";
    if (/(?:kurgu\s+yap|montaj\s+yap|birleştir\s+kurgu|birlestir\s+kurgu)/i.test(low)) return "kurgu";
    if (/(?:\bconcat\b|klip\s+birleştir|klip\s+birlestir|videoları\s+birleştir)/i.test(low)) {
      return "concat";
    }
    if (/başlangıç\s+işaretle|baslangic\s+isaretle|mark\s+in|buraya\s+başlangıç/i.test(low)) {
      return "mark_in";
    }
    if (/bitiş\s+işaretle|bitis\s+isaretle|mark\s+out|buraya\s+bitiş/i.test(low)) return "mark_out";
    if (/kesime\s+yaz|trim\s+alan|alanları\s+doldur/i.test(low)) return "sync_trim";
    if (/^(?:oynat|devam et|play)\b/i.test(low)) return "play";
    if (/^(?:duraklat|dur|pause|durdur)\b/i.test(low)) return "pause";

    const trimRange = parseNaturalTrimRange(raw);
    if (trimRange?.needClarify) return "trim_clarify";
    if (
      trimRange &&
      (/\bkes\b|\btrim\b|kırp|kirp|kesim/i.test(raw) ||
        !!parseExplicitTrimRange(raw) ||
        (/['']?(?:dan|den|ten)/i.test(raw) && /kes/i.test(raw)))
    ) {
      return { type: "trim", range: trimRange };
    }
    return null;
  }

  const STEP_LABELS = {
    download: "İndir",
    probe: "Medya bilgisi",
    transcode: "Dönüştür",
    burn_sub: "Altyazı göm",
    mux: "Ses mux",
    add_bin: "Kurgu listesine ekle",
    kurgu: "Kurgu birleştir",
    concat: "Klip birleştir",
    mark_in: "Başlangıç işareti",
    mark_out: "Bitiş işareti",
    sync_trim: "Kes paneline yaz",
    play: "Oynat",
    pause: "Duraklat",
    trim_clarify: "Kesim (netleştirme)",
  };

  function stepLabel(kind) {
    if (kind && typeof kind === "object" && kind.type === "trim") return "Kesim";
    return STEP_LABELS[kind] || String(kind || "?");
  }

  async function executeVideoStep(stepRaw) {
    const raw = String(stepRaw || "").trim();
    const kind = classifyVideoStep(raw);
    if (!kind) return { ok: false, label: raw.slice(0, 40), error: "tanınmadı" };
    if (kind === "trim_clarify") {
      parseNaturalTrimRange(raw);
      return { ok: false, label: stepLabel(kind), error: "netleştirme gerekli" };
    }

    ensureVideo();

    try {
      if (kind === "download") {
        if (!hasActiveCinema()) {
          return { ok: false, label: stepLabel(kind), error: "sinema boş" };
        }
        const result = await d().runCinemaDownloadCurrent?.();
        const rel = String(
          result?.file_path || el().videoRelWorkspace?.value || getCinema().localRel || "",
        ).trim();
        if (rel) {
          if (el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
          await d().loadVideoPreviewFromRel?.(rel);
          return { ok: true, label: stepLabel(kind), detail: rel };
        }
        return { ok: false, label: stepLabel(kind), error: "dosya yolu yok" };
      }

      if (kind === "probe") {
        if (d().canStreamEditCinema?.()) {
          await d().runVideoProbeFromStream?.();
          return { ok: true, label: stepLabel(kind) };
        }
        if (!(await ensureLocalSource(false))) {
          return { ok: false, label: stepLabel(kind), error: "yerel dosya yok" };
        }
        await d().runVideoProbeFromFile?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "transcode") {
        if (!(await ensureLocalSource(false))) {
          return { ok: false, label: stepLabel(kind), error: "yerel dosya yok" };
        }
        openDock("trim");
        await d().runVideoTranscodeJob?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "burn_sub") {
        if (!(await ensureLocalSource(false))) {
          return { ok: false, label: stepLabel(kind), error: "yerel dosya yok" };
        }
        openDock("subtitle");
        await d().runVideoBurnSubJob?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "mux") {
        if (!(await ensureLocalSource(false))) {
          return { ok: false, label: stepLabel(kind), error: "yerel dosya yok" };
        }
        openDock("mux");
        await d().runVideoMuxAudioJob?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "add_bin") {
        if (!(await ensureLocalSource(false))) {
          return { ok: false, label: stepLabel(kind), error: "yerel dosya yok" };
        }
        d().addCurrentTimelineSelectionToBin?.();
        openDock("edit");
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "kurgu") {
        if (!(await ensureLocalSource(false))) {
          return { ok: false, label: stepLabel(kind), error: "yerel dosya yok" };
        }
        openDock("edit");
        await d().runVideoEditMixJob?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "concat") {
        openDock("edit");
        await d().runVideoConcatJob?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind === "mark_in") {
        d().markVideoTimelineIn?.();
        return { ok: true, label: stepLabel(kind) };
      }
      if (kind === "mark_out") {
        d().markVideoTimelineOut?.();
        return { ok: true, label: stepLabel(kind) };
      }
      if (kind === "sync_trim") {
        d().syncVideoMarksToTrim?.();
        openDock("trim");
        return { ok: true, label: stepLabel(kind) };
      }
      if (kind === "play") {
        const v = el().videoPreview;
        if (v?.src) {
          await v.play();
          return { ok: true, label: stepLabel(kind) };
        }
        return { ok: false, label: stepLabel(kind), error: "oynatıcı boş" };
      }
      if (kind === "pause") {
        el().videoPreview?.pause?.();
        return { ok: true, label: stepLabel(kind) };
      }

      if (kind && kind.type === "trim") {
        if (d().runVideoTrimFromCinema) {
          await d().runVideoTrimFromCinema(kind.range);
        } else {
          await runTrimRange(kind.range, raw);
        }
        return { ok: true, label: stepLabel(kind) };
      }
    } catch (e) {
      return {
        ok: false,
        label: stepLabel(kind),
        error: d().formatClientChatError?.(e) || String(e),
      };
    }

    return { ok: false, label: stepLabel(kind), error: "uygulanamadı" };
  }

  async function tryMultiStepVideoPlan(raw) {
    const steps = splitVideoSteps(raw);
    if (steps.length < 2) return false;

    const kinds = steps.map((s) => classifyVideoStep(s));
    const actionable = kinds.filter((k) => k && k !== "trim_clarify");
    if (actionable.length < 2) return false;

    ensureVideo();
    say(
      `Ümit abi, **${steps.length} adımlı** video planı:\n${steps
        .map((s, i) => `${i + 1}. ${stepLabel(kinds[i]) || s}`)
        .join("\n")}\n\nSırayla uyguluyorum…`,
    );

    const results = [];
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i];
      d().setStatus?.(`Video plan ${i + 1}/${steps.length}…`, "Rüzgar");
      const out = await executeVideoStep(step);
      results.push(out);
      if (!out.ok) {
        say(`Adım ${i + 1} durdu: **${out.label}** — ${out.error || "başarısız"}`, {
          error: true,
        });
        break;
      }
    }

    const lines = results.map(
      (r, i) => `${i + 1}. ${r.label} — ${r.ok ? "✓" : "✗"}${r.error ? ` (${r.error})` : ""}`,
    );
    const allOk = results.every((r) => r.ok);
    say(
      (allOk ? "Ümit abi, plan **tamam**:\n" : "Ümit abi, plan **kısmen** tamam:\n") +
        lines.join("\n") +
        `\n\n(${VERSION})`,
    );
    d().setStatus?.("Hazır", "Rüzgar");
    return true;
  }

  function activeRelFromMessage(raw) {
    const bt = raw.match(/`([^`]+)`/);
    if (bt && bt[1]) return bt[1].trim();
    const path = raw.match(
      /(?:^|\s)([\w.\-]+(?:\/[\w.\-]+)+\.(?:mp4|mkv|webm|mov|avi|m4v|mp3|wav|opus|srt|vtt|ass))/i,
    );
    if (path && path[1]) return path[1].trim();
    const openM = raw.match(
      /(?:aç|ac|yükle|yukle|oynat|kullan)\s+(?:şu\s+|su\s+)?(?:dosyayı|dosyayi|videoyu|kaynağı|kaynagi)?\s*[:：]?\s*([\w.\-/]+)/i,
    );
    if (openM && openM[1]) return openM[1].trim();
    return String(el().videoRelWorkspace?.value || getCinema().localRel || "").trim();
  }

  function recentRows() {
    return d().getLastUiManifest?.()?.video?.recent_downloads || [];
  }

  async function handleRecentList() {
    await d().refreshUiManifest?.();
    const rows = recentRows().filter((r) => r && r.file_path);
    if (!rows.length) {
      say(
        "Ümit abi, henüz kayıtlı indirme yok.\n\nYouTube linki ver — indirip **sol sinema oynatıcısında** açarım.",
      );
      return true;
    }
    const lines = ["Ümit abi, **son video indirmeleri:**", ""];
    rows.slice(0, 8).forEach((row, idx) => {
      lines.push(`${idx + 1}. **${row.title || "video"}** — \`${row.file_path}\``);
    });
    lines.push("", "Açmak için: «**1 numarayı oynat**» veya «**son indirilen**»");
    lines.push(`\n(${VERSION})`);
    say(lines.join("\n"));
    return true;
  }

  async function handleOpenRecent(raw) {
    await d().refreshUiManifest?.();
    const rows = recentRows().filter((r) => r && r.file_path);
    if (!rows.length) {
      say("Kayıtlı indirme yok. Önce bir link ver.", { error: true });
      return true;
    }
    let idx = 0;
    const numM = raw.match(
      /(?:#|no|numara)?\s*(\d{1,2})\s*(?:numarayı|numarayi|nolu|\.?\s*(?:videoyu|kaydı|kaydi|indirmeyi))?(?:\s*(?:aç|ac|oynat|yükle|yukle|kullan))?/i,
    );
    if (/son\s+indirilen|en\s+son\s+(?:video|indirme|kayıt|kayit)/i.test(raw)) idx = 0;
    else if (numM && numM[1]) idx = Math.max(0, parseInt(numM[1], 10) - 1);
    else {
      say("Hangi kayıt? Örnek: «1 numarayı oynat» veya «son indirilen».", { error: true });
      return true;
    }
    const row = rows[idx];
    if (!row) {
      say(`Liste ${rows.length} kayıt — ${idx + 1} geçersiz.`, { error: true });
      return true;
    }
    ensureVideo();
    d().applyRecentVideoDownload?.(row);
    await d().loadVideoPreviewFromRel?.(row.file_path);
    say(`Ümit abi, **${row.title || "video"}** sinema oynatıcıda.\n\`${row.file_path}\``);
    return true;
  }

  async function handleSearch(raw) {
    if (!d().isVideoSearchOrPickCommand?.(raw)) return false;
    const isPickDl = d().RUZGAR_VIDEO_PICK_RE?.test?.(String(raw || "").trim());
    const isPickOpen = d().RUZGAR_VIDEO_PICK_OPEN_RE?.test?.(String(raw || "").trim());
    say(
      isPickDl
        ? "Ümit abi, seçtiğin sıradaki videoyu indirip sinemada açıyorum…"
        : isPickOpen
          ? "Ümit abi, seçtiğin videoyu sinema panelinde açıyorum…"
          : "Ümit abi, YouTube'da arıyorum… Panelde tıkla veya «N oynat» de.",
    );
    d().setStatus?.(
      isPickDl ? "Video indiriliyor…" : isPickOpen ? "Sinema açılıyor…" : "YouTube aranıyor…",
      "Rüzgar",
    );
    const ctrl = new AbortController();
    const to = global.setTimeout(
      () => ctrl.abort(),
      isPickDl ? d().RUZGAR_VIDEO_DOWNLOAD_TIMEOUT_MS : 120000,
    );
    try {
      const res = await fetch(`${d().getApi?.()}/api/video/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: raw }),
        signal: ctrl.signal,
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok || j.ok === false) throw new Error(j.detail || `HTTP ${res.status}`);
      ensureVideo();
      if (j.mode === "open" && j.open?.url) {
        const url = String(j.open.url).trim();
        if (el().videoDownloadUrl) el().videoDownloadUrl.value = url;
        await d().loadPreviewInPanel?.(url, { flash: false });
        say(String(j.text || "Sinema panelinde açıldı."));
        d().setStatus?.("YouTube oynatılıyor", "Rüzgar");
        return true;
      }
      say(String(j.text || j.detail || "Arama tamamlandı."));
      if (j.mode === "search" && j.data?.ok) {
        d().renderVideoSearchResults?.(j.data);
      }
      if (j.mode === "download" && j.result?.file_path) {
        const rel = String(j.result.file_path).trim();
        if (el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
        await d().loadVideoPreviewFromRel?.(rel);
        say(`Sinema oynatıcıda: \`${rel}\``);
      }
      await d().refreshUiManifest?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return true;
    } catch (e) {
      say(
        `Video arama/indirme başarısız: ${d().formatClientChatError?.(e) || e}\n\nyt-dlp kurulu olmalı.`,
        { error: true },
      );
      d().setStatus?.("Hazır", "Rüzgar");
      return true;
    } finally {
      global.clearTimeout(to);
    }
  }

  async function handleYoutubeOpen(raw) {
    if (!d().isVideoStreamOpenCommand?.(raw)) return false;
    const url = d().extractVideoDownloadUrl?.(raw) || d().extractVideoPageUrl?.(raw);
    if (!url) return false;
    ensureVideo();
    const ok = await d().loadPreviewInPanel?.(url, { flash: false });
    if (!ok) {
      say("Ümit abi, linki sinemada açamadım — URL'yi kontrol edin veya «Web» yedek düğmesini deneyin.", {
        error: true,
      });
      return { ok: false };
    }
    if (el().videoDownloadUrl) el().videoDownloadUrl.value = url;
    say(
      [
        "Ümit abi, video **sinema oynatıcıda** açıldı (canlı akış — indirme yok).",
        "",
        `\`${url}\``,
        "",
        "Sol panelde oynatılıyor. Yerel dosya / kesim: sinema **İndir** veya «indir» de.",
        "",
        `(${VERSION})`,
      ].join("\n"),
    );
    d().flash?.("Sinema oynatıcıda.");
    d().setStatus?.("Video oynatılıyor", "Rüzgar");
    return { ok: true };
  }

  async function handleDownload(raw) {
    const url = d().extractVideoDownloadUrl?.(raw);
    if (!url) return false;
    if (!d().isVideoDownloadCommand?.(raw)) {
      return false;
    }
    ensureVideo();
    d().clearYoutubeEmbedPreview?.();
    say(
      "Ümit abi, linki **yerel dosya olarak indirip** sinema oynatıcısına yüklüyorum. Biraz sürebilir…",
    );
    d().setStatus?.("Video indiriliyor…", "Rüzgar");
    try {
      const result = await d().runVideoDownloadFromUrl?.(url, { announceChat: false });
      const rel = String(result?.file_path || "").trim();
      const title = String(result?.title || "video").trim();
      say(
        [
          "Ümit abi, video hazır.",
          "",
          `**${title}**`,
          rel ? `Yol: \`${rel}\`` : "",
          rel ? "Sol oynatıcıda açılıyor…" : "",
          "",
          `(${VERSION})`,
        ]
          .filter(Boolean)
          .join("\n"),
      );
      if (rel) {
        if (el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
        if (el().videoDownloadUrl) el().videoDownloadUrl.value = url;
        if (el().videoEditInsertRel) el().videoEditInsertRel.value = rel;
        await d().loadVideoPreviewFromRel?.(rel);
      }
      d().flash?.("Video indirildi.");
      await d().refreshUiManifest?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { ok: true };
    } catch (e) {
      say(
        `Video indirilemedi: ${d().formatClientChatError?.(e) || e}\n\nyt-dlp ve sunucu bağlantısını kontrol edin.`,
        { error: true },
      );
      d().setStatus?.("Hazır", "Rüzgar");
      return { ok: false };
    } finally {
      d().setVideoJobProgress?.(false);
    }
  }

  async function handleOpenRel(raw) {
    const rel = activeRelFromMessage(raw);
    const wantsOpen =
      /(?:aç|ac|yükle|yukle|kullan|göster|goster)\b/i.test(raw) ||
      /\.(mp4|mkv|webm|mov|avi|m4v|mp3|wav)\b/i.test(raw) ||
      /`[^`]+`/.test(raw);
    if (!wantsOpen || !rel || !rel.includes("/")) return false;
    if (d().extractVideoDownloadUrl?.(raw)) return false;
    ensureVideo();
    if (el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
    await d().loadVideoPreviewFromRel?.(rel);
    say(`Ümit abi, sinema oynatıcıda: \`${rel}\``);
    return true;
  }

  function helpText() {
    return (
      "Ümit abi, **sohbetten** sinemadaki videoyu yönet — komut ezberleme yok:\n\n" +
      "• Link + «**panelde aç / oynat**» — canlı akış (YouTube, web…)\n" +
      "• Oynarken: «**indir**» · «**bunu indir**» · «**kesime al**»\n" +
      "• «**kes 0:30-1:00**» — **oynatırken** yalnızca o bölüm alınır (tam indirme yok)\n" +
      "• «**buradan 30 saniye kes**» — HLS/yerel oynatıcıda konumdan\n" +
      "• «**medya bilgisi**» — akıştan ffprobe (indirme yok)\n" +
      "• «**dönüştür**» · «**altyazı göm**» · «**kurgu yap**» (kesim çıktısı veya «indir» sonrası)\n" +
      "• **Çok adım:** «**kes 0:30-1:00, medya bilgisi, listeye ekle**»\n" +
      "• Ana Motor'dan da aynı cümleler — sinema açıksa otomatik video'ya gider\n" +
      "• «**son indirmeler**» · «**1 numarayı oynat**»\n\n" +
      "Web sinemada «buradan kes» için saniye yaz; konum okunmaz.\n" +
      "Altyazı/mux/kurgu için önce kesim çıktısı oluşur veya «indir» de.\n" +
      `(${VERSION})`
    );
  }

  function isCasualGreeting(raw) {
    const w = fold(raw).replace(/[!?.…]+/g, "").trim();
    if (!w || w.length > 100) return false;
    if (
      /^(selam|merhaba|hey|slm|günaydın|gunaydin|iyi akşamlar|iyi aksamlar|sa)(\s+(ruzgar|ümit|umi|abi))?$/.test(
        w,
      )
    ) {
      return true;
    }
    if (/^nas(?:ilsin|ılsın|lsin|ıl|il)/.test(w) && w.length < 50) return true;
    if (/^naber|nbr|ne haber/.test(w) && w.length < 40) return true;
    return false;
  }

  /**
   * @returns {Promise<{handled: boolean, instant?: boolean, reply?: string}>}
   */
  async function tryAtolyeFromMessage(text, opts) {
    if (!deps) return { handled: false };
    const raw = String(text || "").trim();
    if (!raw) return { handled: false };
    const preTrim = opts?.understanding?.trimRange;

    const chatMode = d().activeMotorChatMode?.() || d().getCurrentMode?.() || "genel";
    if (chatMode !== "genel" && chatMode !== "video") return { handled: false };
    if (
      chatMode === "genel" &&
      !isVideoIntent(raw) &&
      !(hasActiveCinema() && isVideoActionIntent(raw))
    ) {
      return { handled: false };
    }

    if (chatMode === "video" && isCasualGreeting(raw)) {
      ensureVideo();
      const cinemaHint = hasActiveCinema()
        ? " Sinemada video **açık** — «indir», «kes …», «medya bilgisi» diyebilirsin."
        : "";
      say(
        "Aleyküm selam Ümit abi. **Video atölyesindeyiz** — konuşarak veya yazarak yönetirsin." +
          cinemaHint +
          "\n\nTam liste: **yardım**",
      );
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:ne\s+yapabil|yardım|yardim|komutlar|nasıl\s+kullan|nasil\s+kullan)/i.test(fold(raw))) {
      ensureVideo();
      say(helpText());
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:video\s+motor|sinema\s+panel|video\s+atölye|video\s+atolye)/i.test(fold(raw))) {
      ensureVideo();
      say("Ümit abi, **Video atölyesi** (sinema paneli) açık. Ne yapmamı istersin?");
      d().setStatus?.("Video atölye", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (await handleSearch(raw)) return { handled: true, instant: true };

    if (/(?:son\s+indir|indirilen\s+videolar|video\s+listesi)/i.test(fold(raw))) {
      ensureVideo();
      await handleRecentList();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (
      /(?:numarayı|numarayi|nolu|son\s+indirilen|en\s+son)/i.test(raw) &&
      /(?:aç|ac|oynat|yükle|yukle|kullan|indir)/i.test(raw)
    ) {
      ensureVideo();
      await handleOpenRecent(raw);
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (await tryMultiStepVideoPlan(raw)) return { handled: true, instant: true };

    const ytOpen = await handleYoutubeOpen(raw);
    if (ytOpen) return { handled: true, instant: true, ok: ytOpen.ok !== false };

    if (await handleCinemaDownload(raw)) return { handled: true, instant: true };

    const dl = await handleDownload(raw);
    if (dl) return { handled: true, instant: true, ok: dl.ok !== false };

    if (await handleOpenRel(raw)) return { handled: true, instant: true };

    const low = fold(raw);

    if (/(?:çıktı|export|dışa\s+aktar|disa\s+aktar)\s+klasör/i.test(low)) {
      ensureVideo();
      d().openVideoExportFolder?.();
      say("Ümit abi, `.ruzgar-video-export/` çıktı klasörünü açıyorum.");
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:medya\s+bilgi|teknik\s+özet|teknik\s+ozet|ffprobe\b)/i.test(raw)) {
      ensureVideo();
      say("Ümit abi, **Medya bilgisi** alınıyor…");
      d().setStatus?.("Medya özeti…", "Rüzgar");
      if (d().canStreamEditCinema?.()) {
        await d().runVideoProbeFromStream?.();
      } else {
        const rel = await ensureLocalSource(true);
        if (!rel) {
          say("Önce sinemada video aç.", { error: true });
          d().setStatus?.("Hazır", "Rüzgar");
          return { handled: true, instant: true };
        }
        await d().runVideoProbeFromFile?.();
      }
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:sıfırla|temizle|önizlemeyi\s+sil|onizlemeyi\s+sil)/i.test(low) && !/aralık/i.test(low)) {
      ensureVideo();
      d().clearVideoPreview?.();
      say("Ümit abi, sinema önizlemesi sıfırlandı.");
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/^(?:oynat|devam et|play)\b/i.test(low) && !d().extractVideoDownloadUrl?.(raw)) {
      ensureVideo();
      const v = el().videoPreview;
      if (v?.src) {
        try {
          await v.play();
          say("Oynatılıyor.");
        } catch (_) {
          say("Oynatılamadı — önce video yükleyin.", { error: true });
        }
      } else {
        say("Önce video yükle: link ver, «son indirilen» de veya dosya yolu yaz.", { error: true });
      }
      return { handled: true, instant: true };
    }

    if (/^(?:duraklat|dur|pause|durdur)\b/i.test(low)) {
      ensureVideo();
      el().videoPreview?.pause?.();
      say("Duraklatıldı.");
      return { handled: true, instant: true };
    }

    if (/başlangıç\s+işaretle|baslangic\s+isaretle|mark\s+in|buraya\s+başlangıç/i.test(low)) {
      ensureVideo();
      d().markVideoTimelineIn?.();
      say("Kesim **başlangıcı** oynatıcı konumuna işaretlendi.");
      return { handled: true, instant: true };
    }

    if (/bitiş\s+işaretle|bitis\s+isaretle|mark\s+out|buraya\s+bitiş/i.test(low)) {
      ensureVideo();
      d().markVideoTimelineOut?.();
      say("Kesim **bitişi** oynatıcı konumuna işaretlendi.");
      return { handled: true, instant: true };
    }

    if (/kesime\s+yaz|trim\s+alan|alanları\s+doldur/i.test(low)) {
      ensureVideo();
      d().syncVideoMarksToTrim?.();
      openDock("trim");
      say("Başlangıç/bitiş **Kes** paneline yazıldı.");
      return { handled: true, instant: true };
    }

    if (/(?:listeye\s+ekle|kurgu\s+listesine|bin\s+e)/i.test(low)) {
      ensureVideo();
      d().addCurrentTimelineSelectionToBin?.();
      openDock("edit");
      say("Seçili aralık kurgu listesine eklendi (varsa).");
      return { handled: true, instant: true };
    }

    if (/(?:kurgu\s+yap|montaj\s+yap|birleştir\s+kurgu|birlestir\s+kurgu)/i.test(low)) {
      ensureVideo();
      openDock("edit");
      if (!(await ensureLocalSource(true))) {
        say("Kurgu için yerel klip gerekir — önce «indir» veya listeye ekle.", { error: true });
        d().setStatus?.("Hazır", "Rüzgar");
        return { handled: true, instant: true };
      }
      say("Ümit abi, kurgu birleştiriliyor…");
      await d().runVideoEditMixJob?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:dönüştür|donustur|transcode|mp4\s+yap|format\s+değiştir)/i.test(low)) {
      ensureVideo();
      const rel = activeRelFromMessage(raw);
      if (rel && el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
      let local = await ensureLocalSource(true);
      if (!local) {
        say("Önce kaynak video olmalı — sinemada aç veya «indir» de.", { error: true });
        openDock("trim");
        return { handled: true, instant: true };
      }
      openDock("trim");
      say("Dönüştürme başlıyor…");
      await d().runVideoTranscodeJob?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:altyaz[ıi]\s+g[öo]m|subtitle\s+burn|g[öo]m\s+altyaz|altyaz[ıi]y[ıi]\s+yak)/i.test(low)) {
      ensureVideo();
      const rel = activeRelFromMessage(raw);
      if (rel && el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
      if (!(await ensureLocalSource(true))) {
        say("Altyazı gömme için yerel video gerekir — «indir» de.", { error: true });
        return { handled: true, instant: true };
      }
      openDock("subtitle");
      say("Ümit abi, altyazı gömme başlıyor…");
      d().setStatus?.("Altyazı…", "Rüzgar");
      await d().runVideoBurnSubJob?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:\bmux\b|ses\s+ekle|harici\s+ses|ses\s+videoya|ses\s+kanal)/i.test(low)) {
      ensureVideo();
      const rel = activeRelFromMessage(raw);
      if (rel && el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
      if (!(await ensureLocalSource(true))) {
        say("Ses mux için yerel video gerekir — «indir» de.", { error: true });
        return { handled: true, instant: true };
      }
      openDock("mux");
      say("Ümit abi, ses mux başlıyor…");
      d().setStatus?.("Mux…", "Rüzgar");
      await d().runVideoMuxAudioJob?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:\bconcat\b|klip\s+birleştir|klip\s+birlestir|videoları\s+birleştir|videolari\s+birlestir|videoları\s+birle)/i.test(low)) {
      ensureVideo();
      openDock("edit");
      say("Ümit abi, klip birleştirme (concat) başlıyor…");
      d().setStatus?.("Concat…", "Rüzgar");
      await d().runVideoConcatJob?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    const dockPhrases = [
      { re: /(?:kesim|trim)\s+panel|panel.*(?:kesim|trim)/i, dock: "trim" },
      { re: /(?:indir|download|youtube)\s+panel|panel.*(?:indir|download|youtube)/i, dock: "download" },
      { re: /(?:kurgu|edit|montaj)\s+panel|panel.*(?:kurgu|edit|montaj)/i, dock: "edit" },
      { re: /(?:altyaz|subtitle)\s+panel|panel.*(?:altyaz|subtitle)/i, dock: "subtitle" },
      { re: /(?:mux|ses\s+ekle|harici\s+ses)\s+panel|panel.*(?:mux|ses)/i, dock: "mux" },
      { re: /(?:meta|bilgi|özet)\s+panel|panel.*(?:meta|bilgi)/i, dock: "meta" },
      { re: /(?:sinema|önizleme|onizleme)\s+panel|panel.*(?:sinema|önizleme)/i, dock: "preview" },
    ];
    if (/panel(?:i|ini)?\s+aç|panel(?:i|ini)?\s+ac|aç\s+.*panel|ac\s+.*panel/i.test(low)) {
      for (const { re, dock } of dockPhrases) {
        if (re.test(raw)) {
          openDock(dock);
          say(`Ümit abi, **${dock}** paneli sinemada açıldı.`);
          d().setStatus?.("Hazır", "Rüzgar");
          return { handled: true, instant: true };
        }
      }
    }

    if (/^(?:indir|download)\b/i.test(low) && !d().extractVideoDownloadUrl?.(raw)) {
      openDock("download");
      say("Ümit abi, **indirme paneli** açık — linki sohbete de yapıştırabilirsin.");
      return { handled: true, instant: true };
    }

    let trimRange = parseNaturalTrimRange(raw);
    if (
      preTrim &&
      Number.isFinite(preTrim.start) &&
      Number.isFinite(preTrim.end) &&
      preTrim.end > preTrim.start
    ) {
      trimRange = { start: preTrim.start, end: preTrim.end };
    }
    if (trimRange?.needClarify) return { handled: true, instant: true };
    if (trimRange && !trimRange.needClarify) {
      const isTrimMsg =
        /\bkes\b|\btrim\b|kırp|kirp|kesim|arasi|arası|arasinda|arasında/i.test(raw) ||
        !!parseExplicitTrimRange(raw) ||
        (/['']?(?:dan|den|ten)/i.test(raw) && /kes/i.test(raw)) ||
        /(\d+)\s*(?:ila|ile|-)\s*(\d+)/i.test(raw);
      if (isTrimMsg) {
        await runTrimRange(trimRange, raw);
        return { handled: true, instant: true };
      }
    }

    if (
      (chatMode === "video" || chatMode === "genel") &&
      hasActiveCinema() &&
      isVideoActionIntent(raw)
    ) {
      say(
        "Ümit abi, tam anlayamadım. Sinemada video açık — örnek:\n" +
          "«**indir**» · «**kes 0:30-1:00**» · «**5 ila 30 saniye kes**» · «**medya bilgisi**»\n" +
          "Tam liste: **yardım**",
        { clarify: true },
      );
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    return { handled: false };
  }

  function showChatWelcome(container) {
    if (!container) return;
    const w = document.createElement("div");
    w.className = "bubble assistant chat-welcome";
    w.setAttribute("role", "note");
    w.innerHTML =
      `<p class="chat-welcome-lead"><strong>Video atölyesi — konuşarak yönet.</strong></p>` +
      `<p>Sinemada video açıkken «indir», «kes …», «medya bilgisi» de — komut ezberleme yok.</p>` +
      `<ul class="chat-welcome-list">` +
      `<li>«indir» / «bunu indir» — oynayan videoyu yerel dosyaya al</li>` +
      `<li>«indir, kes 0:30-1:00, kurgu yap» — çok adımlı plan</li>` +
      `<li>«kes 0:30-1:00» · «buradan 30 saniye kes»</li>` +
      `<li>«medya bilgisi» · «kurgu yap» · «dönüştür»</li>` +
      `<li>«yardım» — tüm talimatlar</li>` +
      `</ul>` +
      `<p class="chat-welcome-foot">${VERSION} · Ümit &amp; Gökçenur</p>`;
    container.appendChild(w);
  }

  function init(options) {
    deps = options || {};
  }

  global.RuzgarVideoChatBrain = {
    VERSION,
    init,
    tryAtolyeFromMessage,
    tryMultiStepFromMessage: tryMultiStepVideoPlan,
    isVideoIntent,
    isVideoActionIntent,
    looksLikeMultiStepPlan,
    showChatWelcome,
  };
})(typeof window !== "undefined" ? window : globalThis);
