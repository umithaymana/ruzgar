/**
 * Rüzgar — merkezi sohbet anlama (tüm motorlar)
 * Devrik cümle, yazım hatası, eksik özne; sohbet geçmişi + sinema bağlamı.
 */
(function ruzgarSohbetAnlama(global) {
  "use strict";

  const VERSION = "ruzgar-sohbet-anlama-v6-sohbet-once-2026-11-12";

  /** @type {Record<string, any>|null} */
  let deps = null;

  function d() {
    return deps || {};
  }

  function fold(text) {
    // tr-TR: ASCII "I" → "ı"; eşleşme için yumuşak harfleri ASCII'ye çek
    return String(text || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("tr-TR")
      .replace(/ı/g, "i")
      .replace(/ğ/g, "g")
      .replace(/ü/g, "u")
      .replace(/ş/g, "s")
      .replace(/ö/g, "o")
      .replace(/ç/g, "c");
  }

  function trimHistory(history, max) {
    const list = Array.isArray(history) ? history : [];
    const n = Number.isFinite(max) ? max : 32;
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
      /https?:\/\/[^\s<>"']+|(?:www\.)?(?:youtube\.com|youtu\.be|vimeo\.com|dailymotion\.com|dai\.ly|tiktok\.com|twitch\.tv)[^\s]*/gi;
    let m;
    const s = String(text || "");
    while ((m = re.exec(s))) {
      urls.push(m[0].replace(/[),.]+$/, ""));
    }
    return urls;
  }

  function isVideoPlatformUrl(url) {
    if (d().isKnownVideoPageUrl) return !!d().isKnownVideoPageUrl(url);
    const u = String(url || "").trim();
    if (!u) return false;
    return /(?:youtube\.com|youtu\.be|vimeo\.com|dailymotion\.com|dai\.ly|tiktok\.com|twitch\.tv|\.mp4|\.mkv|\.webm|\.m3u8)/i.test(
      u,
    );
  }

  function firstVideoUrlInText(text) {
    const fromDeps = d().extractVideoPageUrl?.(text);
    if (fromDeps && isVideoPlatformUrl(fromDeps)) return fromDeps;
    for (const u of extractUrls(text)) {
      if (isVideoPlatformUrl(u)) return u;
    }
    return "";
  }

  function lastVideoUrlFromHistory(history) {
    for (let i = history.length - 1; i >= 0; i--) {
      const urls = extractUrls(history[i]?.content || "");
      if (urls.length) return urls[0];
    }
    return "";
  }

  function isShortAck(text) {
    const w = fold(text).replace(/[!?.…]+/g, "").trim();
    return /^(?:evet|hayir|hayır|tamam|ok|peki|olur|oldu|guzel|güzel|super|süper|selam|merhaba|tesekkur|teşekkür)$/.test(
      w,
    );
  }

  function lastSubstantiveUserTurn(history) {
    for (let i = history.length - 1; i >= 0; i--) {
      const m = history[i];
      if (String(m?.role || "").toLowerCase() !== "user") continue;
      const c = String(m?.content || "").trim();
      if (!c || c.length < 2 || isShortAck(c)) continue;
      return c;
    }
    return "";
  }

  function lastAssistantTurn(history) {
    for (let i = history.length - 1; i >= 0; i--) {
      const m = history[i];
      if (String(m?.role || "").toLowerCase() !== "assistant") continue;
      const c = String(m?.content || "").trim();
      if (c) return c;
    }
    return "";
  }

  function isEllipticalFollowUp(text) {
    const raw = String(text || "").trim();
    if (!raw || raw.length > 220) return false;
    const low = fold(raw);
    if (
      /(?:yukaridaki|yukarıdaki|yukardaki|az\s+once|az\s+önce|demin|dedigim|dediğim|soyledigim|söylediğim|bahsettigim|bahsettiğim|anlattigim|anlattığım|yazdigim|yazdığım|sohbetteki|sohbet\s+teki)/.test(
        low,
      )
    ) {
      return true;
    }
    if (/^(?:onu|bunu|sunu|şunu|o\s+is|bu\s+is|o\s+video|bu\s+video)\b/.test(low)) return true;
    if (
      /^(?:ayni|aynı|öyle|oyle|böyle|boyle|devam|peki\s+o|simdi\s+o|şimdi\s+o|hadi\s+o|yap\s+o|yap\s+bunu)\b/.test(
        low,
      )
    ) {
      return true;
    }
    if (/^sen\s+(?:yap|hallet|anla|algila|algıla|devam)/.test(low)) return true;
    if (
      raw.length < 64 &&
      !extractUrls(raw).length &&
      /^(?:kes|indir|oynat|cevir|çevir|ac|aç|medya|kurgu|panel)\b/.test(low)
    ) {
      return true;
    }
    return false;
  }

  function resolveEllipticalFollowUp(text, history) {
    if (!isEllipticalFollowUp(text)) return text;
    const prevUser = lastSubstantiveUserTurn(history);
    const prevAssist = lastAssistantTurn(history);
    const anchor = prevUser || prevAssist;
    if (!anchor) return text;

    const low = fold(text);
    const stripLead = text
      .replace(
        /^(?:onu|bunu|sunu|şunu|yukarıdaki|yukardaki|yukaridaki|az\s+once|az\s+önce|demin|dediğim|dedigim|söylediğim|soyledigim|bahsettiğim|bahsettigim|anlattığım|anlattigim|yazdığım|yazdigim|sohbetteki)[,\s:]*/i,
        "",
      )
      .trim();

    if (/^(?:ayni|aynı|öyle|oyle|böyle|boyle|devam|sen\s+yap|hallet|anla)/i.test(low)) {
      return prevUser || anchor;
    }

    if (stripLead && stripLead !== text && stripLead.length >= 2) {
      return `${prevUser || anchor} — ${stripLead}`;
    }

    if (
      /(?:yukaridaki|yukarıdaki|dedigim|dediğim|soyledigim|bahsettigim|anlattigim|yazdigim|sohbetteki)/.test(
        low,
      )
    ) {
      const rest = text
        .replace(
          /.*?(?:yukarıdaki|yukardaki|yukaridaki|dediğim|dedigim|söylediğim|soyledigim|bahsettiğim|bahsettigim|anlattığım|anlattigim|yazdığım|yazdigim|sohbetteki)[,\s:]*/i,
          "",
        )
        .trim();
      if (rest.length >= 2) return `${prevUser || anchor} — ${rest}`;
      return prevUser || anchor;
    }

    if (prevUser && text.length < 80) {
      return `${prevUser} — ${text}`;
    }
    return text;
  }

  function buildContextBrief(history, maxLines) {
    const tail = trimHistory(history, maxLines || 16);
    const lines = [];
    for (const m of tail) {
      const role = String(m?.role || "").toLowerCase() === "user" ? "Ümit abi" : "Rüzgar";
      const c = String(m?.content || "").trim();
      if (!c) continue;
      lines.push(`${role}: ${c.slice(0, 420)}`);
    }
    return lines.join("\n");
  }

  /** Kütüphane / ilim bilgisi — tercüme/video atölyesine kaçmasın */
  function looksLikeKutuphaneOrIlim(text) {
    const raw = String(text || "").trim();
    if (!raw) return false;
    const low = fold(raw);
    // Açık atölye çevirisi → ilim değil
    if (
      /\b(?:cevir|çevir|tercume|tercüme|translate)\b/.test(low) &&
      /\b(?:bu\s+metni|sayfayi|sayfayı|ingilizce|arapca|arapça|almanca|english|arabic)\b/.test(low)
    ) {
      return false;
    }
    if (
      /\b(?:nedir|kimdir|ne\s+demek|hakkinda|hakkında|anlat|acikla|açıkla|ozetle|özetle|bilgi\s+ver|ogret|öğret|kimdi|neydi)\b/.test(
        low,
      )
    ) {
      return true;
    }
    if (
      /\b(?:tefsir|fik[iı]h|hadis|akaid|siyer|teracim|kutuphane|kütüphane|raf|kaynak|hangi\s+eser|eserden|eserini)\b/.test(
        low,
      )
    ) {
      return true;
    }
    if (
      /\b(?:hz\.?|hazreti|peygamber|ebubekir|ebu\s*bekir|omer|osman|ali|sahabe|halid|muhammed)\b/.test(low) &&
      /\b(?:kim|nedir|anlat|hakkinda|hakkında|kimdir|neydi|kimdi|bilgi)\b/.test(low)
    ) {
      return true;
    }
    if (/\b(?:kaynak|eser)\b/.test(low) && /\b(?:yaz|soyle|söyle|goster|göster|ver)\b/.test(low)) {
      return true;
    }
    return false;
  }

  function recentTopicFromHistory(history) {
    const joined = history
      .slice(-10)
      .map((m) => String(m?.content || ""))
      .join(" ");
    const low = fold(joined);
    if (/youtube|youtu\.be|sinema|video|oynat|indir|kes|kurgu|ffmpeg/.test(low)) {
      return "video";
    }
    // meal/ayet/kuran/eser tek başına tercüme konusu sayılmaz
    if (/terc[üu]me|cevir|çevir/.test(low)) return "tercume";
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

    // İlim / kütüphane sorusu → motor atölyesine kayma
    if (looksLikeKutuphaneOrIlim(text)) return "";

    if (ctx?.vision?.motor) {
      const vm = String(ctx.vision.motor || "").trim().toLowerCase();
      return vm === "okuma" ? "mimar" : vm;
    }

    if (firstVideoUrlInText(text)) return "video";

    const low = fold(text);
    const cinema = ctx?.cinema || {};
    const hasCinema =
      !!ctx?.hasCinema ||
      !!(String(cinema.url || "").trim() || String(cinema.localRel || "").trim());

    if (hasCinema && /(?:kes|indir|oynat|kurgu|medya|sinema|video|youtube|ffprobe|trim|mux|altyaz)/.test(low)) {
      return "video";
    }
    // meal/ayet/kuran tek başına tercüme değil; açık çevir / eser ara kalsın
    if (/terc[üu]me|cevir|çevir/i.test(text)) return "tercume";
    if (/\beser\s+ara\b/i.test(text)) return "tercume";
    if (/pytest|git\s+durum|kod\s+mod|programlama|proje\s+tara|briefing/i.test(text)) return "programlama";
    if (/haf[ıi]za|hat[ıi]rla:|g[öo]rev\s+listesi/i.test(text)) return "hafiza";
    if (/whisper|metne\s+d[öo]k|transkript|ses\s+profil/i.test(text)) return "ses";
    if (/(?:kuran|gazel|ilahi|tilavet)\s+ses(?:i(?:yle|ni)?)?\s*(?:ile\s+|le\s+)?(?:oku|seslendir|okut)/i.test(text)) {
      return "ses";
    }
    if (/h[ıi]z[ıi]r|pazar\s+tara|trendyol|amazon/i.test(text)) return "hizir";
    if (/mimar|pdf|okuma|sayfa\s+\d/i.test(text)) return "mimar";

    const topic = recentTopicFromHistory(ctx?.history || []);
    if (topic && (isActionFragment(text) || isEllipticalFollowUp(text))) return topic;
    return "";
  }

  function resolveFromHistory(text, ctx) {
    let out = String(text || "").trim();
    const history = trimHistory(ctx?.history || [], ctx?.maxHistory || 40);
    if (!out) return out;

    // İlim sorusunu video/önceki emre yapıştırma
    if (looksLikeKutuphaneOrIlim(out)) return out;

    out = resolveEllipticalFollowUp(out, history);
    if (!history.length) return out;

    const cinema = ctx?.cinema || {};
    const hasCinema =
      !!ctx?.hasCinema ||
      !!(String(cinema.url || "").trim() || String(cinema.localRel || "").trim());
    const lastUsers = lastMessages(history, "user", 4);
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
      !/(?:youtube|youtu\.be|dailymotion|dai\.ly|vimeo|\.mp4|\.mkv)/i.test(out);

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
      const prevUser = lastSubstantiveUserTurn(history);
      if (prevUser && fold(prevUser) !== fold(out)) {
        const prevLow = fold(prevUser);
        if (/oynat|indir|kes|panel|sinema|video|cevir|çevir|kurgu/.test(prevLow)) {
          const rest = out.replace(/^(?:simdi|şimdi|peki|tamam|devam)[,.\s!]*/i, "").trim();
          out = rest ? `${prevUser} — ${rest}` : prevUser;
        }
      }
    }

    const urlFromHist = lastVideoUrlFromHistory(history);
    if (urlFromHist && lacksSubject && /^(?:oynat|indir|panelde\s+ac|panelde\s+aç)\b/i.test(out)) {
      out = `${urlFromHist} ${out}`;
    }

    return out.trim();
  }

  function hasExplicitMotorSignal(text, understanding, ctx) {
    const raw = String(text || "").trim();
    if (!raw) return false;
    if (firstVideoUrlInText(raw)) return true;
    if (ctx?.vision?.urls?.length) return true;
    if (extractUrls(raw).some(isVideoPlatformUrl)) return true;
    if (understanding?.trimRange) return true;
    const intent = String(understanding?.intent || "");
    if (
      intent &&
      intent !== "sohbet" &&
      (intent.startsWith("video_") || intent.endsWith("_action"))
    ) {
      return true;
    }
    const low = fold(raw);
    if (/^(?:yardim|yardım|help|hub\s+yardim|eylem\s)/.test(low)) return true;
    if (/^https?:\/\//.test(raw)) return true;
    if (global.RuzgarVideoChatBrain?.looksLikeMultiStepPlan?.(raw)) return true;
    if (expandTrimRangePhrase(raw)) return true;
    if (
      /(?:kuran|gazel|ilahi|tilavet)\s+ses(?:i(?:yle|ni)?)?\s*(?:ile\s+|le\s+)?(?:oku|seslendir|okut)/.test(
        low,
      )
    ) {
      return true;
    }
    if (
      /\b(?:indir|download|kes\b|trim\b|oynat\b|ffprobe|medya\s+bilgi|kurgu\s+yap|dönüştür|donustur)\b/.test(
        low,
      )
    ) {
      if (
        ctx?.hasCinema ||
        understanding?.motorHint === "video" ||
        /\b(?:video|youtube|sinema|film|klip|shorts)\b/.test(low)
      ) {
        return true;
      }
    }
    return false;
  }

  function looksLikeNaturalConversation(text) {
    const raw = String(text || "").trim();
    if (!raw) return true;
    const low = fold(raw);

    if (looksLikeKutuphaneOrIlim(raw)) return true;

    if (
      /(?:anlamad|anlamiyor|anlamıyor|anlamadin|anlamadın|anlamiyormusun|anlıyor\s+musun|duymuyor|duymadin|duymadın|yazdiklarim|yazdıklarım|yukaridaki|yukarıdaki|az\s+once|az\s+önce|acikla|açıkla|neden\s+|nas[ıi]l\s+|ne\s+demek|ne\s+ister|sence|dusun|düşün|merak|sohbet|konusalim|konuşalım|hakkinda|hakkında|lutfen|lütfen\s+anla|kimdir|nedir)/.test(
        low,
      )
    ) {
      if (!hasExplicitMotorSignal(raw, null, null)) return true;
    }

    if (/\?/.test(raw) && !/^(?:kes|indir|oynat|yardim|yardım)\s/i.test(raw)) {
      if (!hasExplicitMotorSignal(raw, null, null)) return true;
    }

    if (raw.length > 90 && !extractUrls(raw).length && !expandTrimRangePhrase(raw)) {
      if (!/^(?:kes|indir|oynat|download|trim)\b/.test(low)) return true;
    }

    if (/^(?:selam|merhaba|naber|nas[ıi]ls[ıi]n|iyi\s+(?:akşam|aksam|gün|gun))/.test(low)) {
      if (raw.length > 18 && !hasExplicitMotorSignal(raw, null, null)) return true;
    }

    return false;
  }

  /** Sohbet önce: yalnız net iş emri motor/masa çalsın */
  function isNetIsEmri(text, understanding, ctx) {
    const raw = String(text || "").trim();
    if (!raw) return false;
    if (looksLikeKutuphaneOrIlim(raw)) return false;
    const low = fold(raw);
    if (/^eylem\s/.test(low)) return true;
    if (/^(?:gorev|görev|is|iş|yap)\s*:/i.test(raw)) return true;
    if (
      /^(?:tamam[,.]?\s+)?(?:yap|uygula|kaydet|baslat|başlat|basla)\s*[.!]*$/.test(low)
    ) {
      return true;
    }
    if (/^(?:bunu|onu|sunu|şunu)\s+(?:yap|uygula|kaydet)\b/.test(low)) return true;
    if (/^(?:yapma|yap\s+ma|iptal|vazgec|vazgeç)\s*[.!]*$/.test(low)) return true;
    if (/\b(?:dosyaya\s+yaz|belgeye\s+yaz|hucreye\s+yaz|dosyaya\s+ekle)\b/.test(low)) {
      return true;
    }
    if (/\b(?:programlamada|kodda|atolyede|atölyede)\s*:/.test(low)) return true;
    if (hasExplicitMotorSignal(raw, understanding, ctx)) return true;
    return false;
  }

  /**
   * Net motor komutu mu, yoksa doğal sohbet mi?
   * @returns {{ try: boolean, reason: string, preferChat?: boolean }}
   */
  function shouldTryInstantMotor(understanding, text, ctx) {
    const raw = String(text || "").trim();
    if (!raw) return { try: false, reason: "empty", preferChat: true };

    if (/^eylem\s/i.test(fold(raw))) return { try: true, reason: "eylem" };

    const resolved = String(understanding?.text || raw).trim();
    if (looksLikeKutuphaneOrIlim(raw) || looksLikeKutuphaneOrIlim(resolved)) {
      return { try: false, reason: "kutuphane_ilim", preferChat: true };
    }

    // Varsayılan sohbet — net iş emri yoksa LLM / sohbet
    if (!isNetIsEmri(raw, understanding, ctx) && !isNetIsEmri(resolved, understanding, ctx)) {
      return { try: false, reason: "sohbet_once", preferChat: true };
    }

    const explicit =
      hasExplicitMotorSignal(raw, understanding, ctx) ||
      hasExplicitMotorSignal(resolved, understanding, ctx);

    if (looksLikeNaturalConversation(raw) && !explicit) {
      return { try: false, reason: "natural_chat", preferChat: true };
    }

    if (explicit) {
      return { try: true, reason: "explicit_action" };
    }

    if (firstVideoUrlInText(raw) || ctx?.vision?.urls?.length) {
      return { try: true, reason: "video_url" };
    }

    if (understanding?.intent === "continuation" && understanding?.fromHistory) {
      return { try: true, reason: "continuation_action" };
    }

    if (ctx?.hasCinema && understanding?.trimRange) {
      return { try: true, reason: "cinema_trim" };
    }

    return { try: false, reason: "default_llm", preferChat: true };
  }

  function buildCinemaContextBrief(cinema) {
    const c = cinema || {};
    const url = String(c.url || "").trim();
    const rel = String(c.localRel || "").trim();
    const title = String(c.title || c.label || "").trim();
    if (!url && !rel) return "";
    const parts = [];
    if (title) parts.push(`Başlık: ${title.slice(0, 120)}`);
    if (url) parts.push(`URL: ${url.slice(0, 240)}`);
    if (rel) parts.push(`Yerel: ${rel.slice(0, 120)}`);
    return parts.join(" · ");
  }

  /**
   * @param {string} raw
   * @param {object} [ctx]
   */
  function understand(raw, ctx) {
    const original = String(raw || "").trim();
    const history = trimHistory(ctx?.history || [], ctx?.maxHistory || 40);
    let text = normalizeSurface(original);
    text = resolveFromHistory(text, { ...ctx, history });

    const trimRange = expandTrimRangePhrase(text) || expandTrimRangePhrase(original);
    if (trimRange?.normalized && !/^kes\s+\d/i.test(fold(text))) {
      text = trimRange.normalized;
    }

    const motorHint = inferMotorHint(text, { ...ctx, history });
    const fromHistory = text !== original;
    const low = fold(text);
    const contextBrief = buildContextBrief(history, 16);

    let intent = "sohbet";
    const videoUrl = firstVideoUrlInText(text) || ctx?.vision?.urls?.[0] || "";
    if (trimRange) intent = "video_trim";
    else if (videoUrl && !/\b(?:indir|download)\b/.test(low)) intent = "video_play";
    else if (/\b(?:indir|download)\b/.test(low)) intent = "video_download";
    else if (/\b(?:oynat|play)\b/.test(low)) intent = "video_play";
    else if (/\b(?:kes|trim|kirp|kırp)\b/.test(low)) intent = "video_trim";
    else if (/medya\s+bilgi|ffprobe/.test(low)) intent = "video_probe";
    else if (motorHint && motorHint !== "genel") intent = `${motorHint}_action`;
    else if (isEllipticalFollowUp(original)) intent = "continuation";

    const cinemaBrief = buildCinemaContextBrief(ctx?.cinema);
    let fullContextBrief = contextBrief;
    if (cinemaBrief) {
      fullContextBrief = fullContextBrief
        ? `${fullContextBrief}\n[Sinemada açık] ${cinemaBrief}`
        : `[Sinemada açık] ${cinemaBrief}`;
    }

    const partial = {
      raw: original,
      text,
      motorHint,
      trimRange: trimRange ? { start: trimRange.start, end: trimRange.end } : null,
      fromHistory,
      intent,
      contextBrief: fullContextBrief,
    };
    const gate = shouldTryInstantMotor(partial, original, ctx);

    return {
      ...partial,
      preferChat: !!gate.preferChat,
      instantMotor: gate.try,
      instantReason: gate.reason,
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
    resolveEllipticalFollowUp,
    buildContextBrief,
    buildCinemaContextBrief,
    inferMotorHint,
    looksLikeKutuphaneOrIlim,
    looksLikeNaturalConversation,
    isNetIsEmri,
    hasExplicitMotorSignal,
    shouldTryInstantMotor,
  };
})(typeof window !== "undefined" ? window : globalThis);
