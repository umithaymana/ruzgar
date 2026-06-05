/**
 * Video motoru — sohbet süper beyin (Ümit & Gökçenur)
 * Talimat → niyet → sinema paneli. Manuel düğmeler yedek kalır.
 */
(function videoChatBrain(global) {
  "use strict";

  const VERSION = "video-super-brain-v1-2026-06-07";

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
    if (d().isVideoSearchOrPickCommand?.(raw)) return true;
    const low = fold(raw);
    return (
      /\bvideo\b|youtube|youtu\.be|ffmpeg|sinema|atolye|atölye|kesim|\bkes\b|kurgu|montaj|altyaz|subtitle|mux|transcode|donustur|dönüştür|ffprobe|medya\s+bilgi|indirme|indir\b|klip\b|film\b|oynat|onizleme|önizleme|panel/.test(
        low,
      ) || /\.(mp4|mkv|webm|mov|avi|m4v|mp3|wav|srt|vtt)\b/i.test(raw)
    );
  }

  function ensureVideo() {
    if (d().getCurrentMode?.() !== "video") d().switchMode?.("video");
  }

  function openDock(name) {
    ensureVideo();
    global.RuzgarVideoAtolye?.openDuzenDock?.(name);
  }

  function say(msg, opts) {
    d().appendBubble?.("assistant", msg, opts);
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
    return String(el().videoRelWorkspace?.value || "").trim();
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
    const isPick = d().RUZGAR_VIDEO_PICK_RE?.test?.(String(raw || "").trim());
    say(
      isPick
        ? "Ümit abi, seçtiğin sıradaki videoyu indirip sinemada açıyorum…"
        : "Ümit abi, YouTube'da arıyorum… İndirmek için numara veya link yaz.",
    );
    d().setStatus?.(isPick ? "Video indiriliyor…" : "YouTube aranıyor…", "Rüzgar");
    const ctrl = new AbortController();
    const to = global.setTimeout(
      () => ctrl.abort(),
      isPick ? d().RUZGAR_VIDEO_DOWNLOAD_TIMEOUT_MS : 120000,
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
      say(String(j.text || j.detail || "Arama tamamlandı."));
      if (j.mode === "download" && j.result?.file_path) {
        ensureVideo();
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

  async function handleDownload(raw) {
    const url = d().extractVideoDownloadUrl?.(raw);
    if (!url) return false;
    if (!d().isMostlyVideoDownloadCommand?.(raw) && !/(?:oynat|aç|ac|burada)/i.test(raw)) {
      return false;
    }
    ensureVideo();
    say(
      "Ümit abi, linki **indirip sol sinema oynatıcısına** yüklüyorum (canlı YouTube akışı yok). Biraz sürebilir…",
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
      return true;
    } catch (e) {
      say(
        `Video indirilemedi: ${d().formatClientChatError?.(e) || e}\n\nyt-dlp ve sunucu bağlantısını kontrol edin.`,
        { error: true },
      );
      d().setStatus?.("Hazır", "Rüzgar");
      return true;
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
      "Ümit abi, **sohbetten** video atölyesini yönetebilirsin — düğmelere dokunmana gerek yok:\n\n" +
      "• Link + «indir / oynat / burada aç»\n" +
      "• «şu filmi ara …» · «3 numarayı indir»\n" +
      "• «son indirmeler» · «son indirilen» · «1 numarayı oynat»\n" +
      "• «medya bilgisi» · «kes 0:30-1:00» · «dönüştür»\n" +
      "• «başlangıç işaretle» · «bitiş işaretle» · «listeye ekle» · «kurgu yap»\n" +
      "• «kesim paneli aç» · «çıktı klasörü» · «sıfırla»\n" +
      "• «video motoru» — sinema paneline geç\n\n" +
      "Ne istersen söyle; sinema paneline yansıtırım.\n" +
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
  async function tryAtolyeFromMessage(text) {
    if (!deps) return { handled: false };
    const raw = String(text || "").trim();
    if (!raw) return { handled: false };

    const chatMode = d().activeMotorChatMode?.() || d().getCurrentMode?.() || "genel";
    if (chatMode !== "genel" && chatMode !== "video") return { handled: false };
    if (chatMode === "genel" && !isVideoIntent(raw)) return { handled: false };

    if (chatMode === "video" && isCasualGreeting(raw)) {
      ensureVideo();
      say(
        "Aleyküm selam Ümit abi. **Video atölyesindeyiz** — sohbetle yönetirsin; düğmeler yedek.\n\n" +
          "Örnek: link + «oynat», «kes 0:30-1:00», «medya bilgisi». Tam liste: **yardım**",
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

    if (await handleDownload(raw)) return { handled: true, instant: true };

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
      await d().runVideoProbeFromFile?.();
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
      say("Ümit abi, kurgu birleştiriliyor…");
      await d().runVideoEditMixJob?.();
      d().setStatus?.("Hazır", "Rüzgar");
      return { handled: true, instant: true };
    }

    if (/(?:dönüştür|donustur|transcode|mp4\s+yap|format\s+değiştir)/i.test(low)) {
      ensureVideo();
      const rel = activeRelFromMessage(raw);
      if (rel && el().videoRelWorkspace) el().videoRelWorkspace.value = rel;
      if (!String(el().videoRelWorkspace?.value || "").trim()) {
        say("Önce kaynak yolu veya indirilmiş video olmalı.", { error: true });
        openDock("trim");
        return { handled: true, instant: true };
      }
      openDock("trim");
      say("Dönüştürme başlıyor…");
      await d().runVideoTranscodeJob?.();
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

    const trimMatch = raw.match(
      /(?:kes|trim)\s+(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)\s*[-–]\s*(\d+(?::\d+(?::\d+)?)?(?:[.,]\d+)?)/i,
    );
    if (trimMatch) {
      ensureVideo();
      const start = d().parseVideoTimeSec?.(trimMatch[1]);
      const end = d().parseVideoTimeSec?.(trimMatch[2]);
      if (!Number.isFinite(start) || !Number.isFinite(end) || end <= start) {
        say("Kesim aralığını anlayamadım. Örnek: `kes 0:30-1:00`", { error: true });
        return { handled: true, instant: true };
      }
      const rel = String(el().videoRelWorkspace?.value || "").trim();
      if (!rel) {
        say("Önce kaynak video olmalı — link ver veya «son indirilen» de.", { error: true });
        openDock("trim");
        return { handled: true, instant: true };
      }
      if (el().videoStartSec) el().videoStartSec.value = String(start.toFixed(2));
      if (el().videoDurationSec) el().videoDurationSec.value = String((end - start).toFixed(2));
      if (el().videoEndSec) el().videoEndSec.value = "";
      openDock("trim");
      say(`Kesim **${start.toFixed(1)}–${end.toFixed(1)} sn** — FFmpeg çalışıyor…`);
      d().setStatus?.("Kesim…", "Rüzgar");
      await d().runVideoTrimJob?.();
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
      `<p class="chat-welcome-lead"><strong>Video atölyesi — sohbetle yönet.</strong></p>` +
      `<p>Düğmeler yedek; talimatları buraya yaz, sinema paneline yansıtırım.</p>` +
      `<ul class="chat-welcome-list">` +
      `<li>Link + «indir / oynat» → indirip sol oynatıcıda açarım</li>` +
      `<li>«kes 0:30-1:00» · «medya bilgisi» · «kurgu yap»</li>` +
      `<li>«son indirmeler» · «1 numarayı oynat»</li>` +
      `<li>«yardım» — tüm komutlar</li>` +
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
    isVideoIntent,
    showChatWelcome,
  };
})(typeof window !== "undefined" ? window : globalThis);
