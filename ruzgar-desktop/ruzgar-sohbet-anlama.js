/**
 * Rüzgar — merkezi sohbet anlama (tüm motorlar)
 * Devrik cümle, yazım hatası, eksik özne; sohbet geçmişi + sinema bağlamı.
 */
(function ruzgarSohbetAnlama(global) {
  "use strict";

  const VERSION = "ruzgar-sohbet-anlama-v1-2026-06-06";

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

  function trimHistory(history, max) {
    const list = Array.isArray(history) ? history : [];
    const n = Number.isFinite(max) ? max : 24;
    return list.slice(-n);
  }

  function lastMessages(history, role, count) {
    const want = String(role || "").toLowerCase();
    const out = [];
    for (let i = history.length - 1; i >= 0 && out.length < count; i--) {
      const m = history[i];
      if (String(m?.role || "").toLowerCase() !== want) continue;
      const c = String(m?.content || "").trim();
      if (c) out.unshift(c);
    }
    return out;
  }

  function normalizeSurface(raw) {
    let t = String(raw || "").trim();
    if (!t) return "";
    t = t.replace(/\s+/g, " ");
    t = t.replace(/\bvideo\s+nun\b/gi, "videonun");
    t = t.replace(/\bvideo\s+n[ıi]\b/gi, "videonun");
    t = t.replace(/\boynayan\s+video\s+nun\b/gi, "oynayan videonun");
    t = t.replace(/\bsaniyeler\b/gi, "saniye");
    t = t.replace(/\bdakikalari\b/gi, "dakika");
    t = t.replace(/\b(d[aâ]kika)\s+arasi\b/gi, "$1 arası");
    t = t.replace(/\b05\b/g, "5");
    t = t.replace(/\b0(\d)\b/g, "$1");
    return t.trim();
  }

  function parsePlainSeconds(token) {
    const s = String(token || "").trim().replace(",", ".");
    if (!s) return null;
    if (/^\d+:\d+/.test(s)) {
      return d().parseVideoTimeSec?.(s) ?? null;
    }
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : null;
  }

  /** «5 ila 30 saniye arasını kes» → kes 5-30 */
  function expandTrimRangePhrase(text) {
    const raw = String(text || "");
    const m =
      raw.match(
        /(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:sn|saniye|sec|dk|dakika|min(?:ute)?)?\s*(?:ila|ile|la|le|-)\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:sn|saniye|sec|dk|dakika|min(?:ute)?)?(?:ler|leri)?(?:\s*(?:arasi|arası|arasinda|arasında|arasi))?/i,
      ) ||
      raw.match(
        /(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:ila|ile|-)\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*(?:saniye|sn|sec|dk|dakika)/i,
      );
    if (!m) return null;
    const start = parsePlainSeconds(m[1]);
    const end = parsePlainSeconds(m[2]);
    if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) return null;
    const hasTrim =
      /\bkes\b|\btrim\b|kirp|kırp|kesim|arasi|arası|arasinda|arasında|\bal\b/i.test(raw);
    if (!hasTrim) return null;
    return {
      start,
      end,
      normalized: `kes ${start}-${end}`,
    };
  }

  function extractUrls(text) {
    const urls = [];
    const re =
      /https?:\/\/[^\s<>"']+|(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com|tiktok\.com)[^\s]*/gi;
    let m;
    const s = String(text || "");
    while ((m = re.exec(s))) {
      urls.push(m[0].replace(/[),.]+$/, ""));
    }
    return urls;
  }

  function lastVideoUrlFromHistory(history) {
    for (let i = history.length - 1; i >= 0; i--) {
      const urls = extractUrls(history[i]?.content || "");
      if (urls.length) return urls[0];
    }
    return "";
  }

  function recentTopicFromHistory(history) {
    const joined = history
      .slice(-8)
      .map((m) => String(m?.content || ""))
      .join(" ");
    const low = fold(joined);
    if (/youtube|youtu\.be|sinema|video|oynat|indir|kes|kurgu|ffmpeg/.test(low)) {
      return "video";
    }
    if (/terc[üu]me|cevir|eser|ayet|meal|kuran|kur'an/.test(low)) return "tercume";
    if (/pytest|git|kod|program|dosya|proje|python|javascript/.test(low)) return "programlama";
    if (/mimar|okuma|pdf|kitap|sayfa/.test(low)) return "mimar";
    if (/haf[ıi]za|hat[ıi]rla|g[öo]rev\s+list/.test(low)) return "hafiza";
    if (/ses|whisper|stt|transkript|tts/.test(low)) return "ses";
    if (/h[ıi]z[ıi]r|trendyol|amazon|pazar|fiyat/.test(low)) return "hizir";
    return "";
  }

  function referencesPlayingVideo(text) {
    const low = fold(text);
    return (
      /(?:^|\s)(?:bunu|buna|sunu|şunu|bunun|şunun|videoyu|filmi|klibi)(?:\s|$)/.test(low) ||
      /(?:sinema|panelde|oynat|acik\s+olan|açık\s+olan|su\s+an|şu\s+an|oynayan|izledigim|izlediğim)/.test(
        low,
      )
    );
  }

  function isActionFragment(text) {
    const low = fold(text);
    if (low.length > 140) return false;
    return (
      /^(?:kes|indir|oynat|dur|durdur|medya|kurgu|donustur|dönüştür|ffprobe|panel|yardim|yardım)\b/.test(
        low,
      ) ||
      /(?:ila|ile|-)\s*\d/.test(low) ||
      /\d+\s*(?:ila|ile|-)\s*\d/.test(low) ||
      referencesPlayingVideo(text)
    );
  }

  function inferMotorHint(text, ctx) {
    const mode = String(ctx?.mode || ctx?.chatMode || "genel").toLowerCase();
    if (mode !== "genel") return mode;

    const low = fold(text);
    const cinema = ctx?.cinema || {};
    const hasCinema =
      !!ctx?.hasCinema ||
      !!(String(cinema.url || "").trim() || String(cinema.localRel || "").trim());

    if (hasCinema && /(?:kes|indir|oynat|kurgu|medya|sinema|video|youtube|ffprobe|trim|mux|altyaz)/.test(low)) {
      return "video";
    }
    if (/terc[üu]me|cevir|eser\s+ara|meal|ayet|kuran|kur'an|sure\s+\d/i.test(text)) return "tercume";
    if (/pytest|git\s+durum|kod\s+mod|programlama|proje\s+tara|briefing/i.test(text)) return "programlama";
    if (/haf[ıi]za|hat[ıi]rla:|g[öo]rev\s+listesi/i.test(text)) return "hafiza";
    if (/whisper|metne\s+d[öo]k|transkript|ses\s+profil/i.test(text)) return "ses";
    if (/h[ıi]z[ıi]r|pazar\s+tara|trendyol|amazon/i.test(text)) return "hizir";
    if (/mimar|pdf|okuma|sayfa\s+\d/i.test(text)) return "mimar";

    const topic = recentTopicFromHistory(ctx?.history || []);
    if (topic && isActionFragment(text)) return topic;
    return "";
  }

  function resolveFromHistory(text, ctx) {
    let out = String(text || "").trim();
    const history = trimHistory(ctx?.history || [], ctx?.maxHistory || 24);
    if (!out || !history.length) return out;

    const cinema = ctx?.cinema || {};
    const hasCinema =
      !!ctx?.hasCinema ||
      !!(String(cinema.url || "").trim() || String(cinema.localRel || "").trim());
    const lastUsers = lastMessages(history, "user", 3);
    const lastAssist = lastMessages(history, "assistant", 2).join(" ");
    const videoContext =
      hasCinema ||
      /sinema|video|oynat|youtube|indir|kes|akış|akis|panelde/i.test(
        fold(lastUsers.join(" ") + " " + lastAssist),
      );

    const trimExp = expandTrimRangePhrase(out);
    if (trimExp?.normalized) {
      out = trimExp.normalized;
    }

    const low = fold(out);
    const lacksSubject =
      !referencesPlayingVideo(out) &&
      !extractUrls(out).length &&
      !/(?:youtube|youtu\.be|\.mp4|\.mkv)/i.test(out);

    if (videoContext && lacksSubject && isActionFragment(out)) {
      if (/^\d+\s*(?:ila|ile|-)/.test(low) || /(?:arasi|arası|arasinda|arasında)/.test(low)) {
        out = `oynayan videonun ${out}`;
      } else if (/^(?:kes|indir|medya|kurgu|donustur|dönüştür|ffprobe)\b/i.test(out)) {
        out = `sinemadaki videoyu ${out}`;
      } else if (/^(?:bunu|sunu|şunu)\b/i.test(out)) {
        out = out.replace(/^(?:bunu|sunu|şunu)\b/i, "sinemadaki videoyu");
      }
    }

    if (/^(?:simdi|şimdi|peki|tamam|devam)\b/i.test(out) && out.length < 80) {
      const prevUser = lastMessages(history, "user", 1)[0] || "";
      if (prevUser && fold(prevUser) !== fold(out)) {
        const prevLow = fold(prevUser);
        if (/oynat|indir|kes|panel|sinema/.test(prevLow)) {
          const rest = out.replace(/^(?:simdi|şimdi|peki|tamam|devam)[,.\s!]*/i, "").trim();
          out = rest ? `${prevUser} — ${rest}` : prevUser;
        }
      }
    }

    if (/^sen\s+(?:yap|hallet|devam)/i.test(out) || /^şunu\s+yap$/i.test(fold(out))) {
      const prev = lastUsers[lastUsers.length - 1] || "";
      if (prev) out = prev;
    }

    const urlFromHist = lastVideoUrlFromHistory(history);
    if (urlFromHist && lacksSubject && /^(?:oynat|indir|panelde\s+ac|panelde\s+aç)\b/i.test(out)) {
      out = `${urlFromHist} ${out}`;
    }

    return out.trim();
  }

  /**
   * @param {string} raw
   * @param {object} [ctx]
   * @returns {{ raw: string, text: string, motorHint: string, trimRange: {start:number,end:number}|null, fromHistory: boolean, intent: string }}
   */
  function understand(raw, ctx) {
    const original = String(raw || "").trim();
    const history = trimHistory(ctx?.history || [], ctx?.maxHistory || 24);
    let text = normalizeSurface(original);
    text = resolveFromHistory(text, { ...ctx, history });

    const trimRange = expandTrimRangePhrase(text) || expandTrimRangePhrase(original);
    if (trimRange?.normalized && !/^kes\s+\d/i.test(fold(text))) {
      text = trimRange.normalized;
    }

    const motorHint = inferMotorHint(text, { ...ctx, history });
    const fromHistory = text !== original;
    const low = fold(text);

    let intent = "sohbet";
    if (trimRange) intent = "video_trim";
    else if (/\b(?:indir|download)\b/.test(low)) intent = "video_download";
    else if (/\b(?:oynat|play)\b/.test(low)) intent = "video_play";
    else if (/\b(?:kes|trim|kirp|kırp)\b/.test(low)) intent = "video_trim";
    else if (/medya\s+bilgi|ffprobe/.test(low)) intent = "video_probe";
    else if (motorHint && motorHint !== "genel") intent = `${motorHint}_action`;

    return {
      raw: original,
      text,
      motorHint,
      trimRange: trimRange ? { start: trimRange.start, end: trimRange.end } : null,
      fromHistory,
      intent,
    };
  }

  function init(options) {
    deps = options || {};
  }

  global.RuzgarSohbetAnlama = {
    VERSION,
    init,
    understand,
    fold,
    normalizeSurface,
    expandTrimRangePhrase,
    resolveFromHistory,
    inferMotorHint,
  };
})(typeof window !== "undefined" ? window : globalThis);
