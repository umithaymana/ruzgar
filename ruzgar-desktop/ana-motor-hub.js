/**
 * Ana Motor hub — genel sohbetten yardımcı motorlara yönlendirme (Faz 76 + masaüstü)
 * Ümit & Gökçenur
 */
(function anaMotorHub(global) {
  "use strict";

  const VERSION = "ana-motor-hub-v1-2026-06-07";

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

  function say(msg, opts) {
    d().appendBubble?.("assistant", msg, opts);
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

  function isHubHelpRequest(raw) {
    const low = fold(raw);
    if (/^(?:hub|ana motor|motorlar)\s*(?:yardım|yardim|help)?$/.test(low)) return true;
    if (/(?:ne\s+yapabil|hangi\s+motor|motor\s+listesi)/.test(low) && /yardım|yardim|help|hub|ana/.test(low)) {
      return true;
    }
    return false;
  }

  function hubHelpText() {
    return (
      "Ümit abi, **Ana Motor** doğal cümleyle seni doğru motora götürür:\n\n" +
      "· Kod / pytest / proje → **Programlama**\n" +
      "· Video indir · kes · kurgu → **Video**\n" +
      "· Çevir · eser ara → **Tercüme**\n" +
      "· Fotoğraf · sanat · tasarım → **Mimar**\n" +
      "· Ses · transkript → **Ses**\n" +
      "· Hatırla · görev → **Hafıza**\n" +
      "· Pazar · ürün tara → **Hızır**\n\n" +
      "Sekmeye geçmeden burada yazabilirsin; gerekirse motoru açıp işi yaparım.\n" +
      `(${VERSION})`
    );
  }

  function normalizeMotorId(target) {
    const t = String(target || "").trim().toLowerCase();
    if (t === "okuma") return "mimar";
    return t;
  }

  async function fetchHubRoute(text) {
    try {
      const res = await fetch(
        `${d().getApi?.()}/api/ana-motor/hub-route?message=${encodeURIComponent(String(text || ""))}`,
        { method: "GET" },
      );
      if (!res.ok) return null;
      const j = await res.json();
      return j && j.ok ? j : null;
    } catch {
      return null;
    }
  }

  async function dispatchTercume(text) {
    const T = global.RuzgarTercumeAtolye;
    if (!T) return { handled: false };
    if (T.tryAtolyeFromMessage) {
      const hit = await T.tryAtolyeFromMessage(text);
      if (hit?.handled && hit.instant) {
        say(hit.reply || "Tamam.", { actionCard: true });
        return { handled: true };
      }
    }
    if (T.isSearchIntent?.(text) && T.runSearch) {
      if (T.setTercumeTab) T.setTercumeTab("ara");
      const ok = await T.runSearch(text);
      if (ok) {
        say(
          "«Eser ara» sekmesinde sonuçlar listelendi. İndirmek veya çevirmek için sohbetten devam edebilirsin.",
        );
        return { handled: true };
      }
    }
    return { handled: false };
  }

  async function dispatchMimar(text) {
    const M = global.RuzgarMimarAtolye;
    if (!M?.tryAtolyeFromMessage) return { handled: false };
    const hit = await M.tryAtolyeFromMessage(text);
    if (hit?.handled && hit.instant) {
      say(hit.reply || "Tamam.");
      return { handled: true };
    }
    if (hit?.handled) return { handled: true };
    return { handled: false };
  }

  async function dispatchVideo(text) {
    const V = global.RuzgarVideoChatBrain;
    if (!V?.tryAtolyeFromMessage) return { handled: false };
    const hit = await V.tryAtolyeFromMessage(text);
    return { handled: !!hit?.handled };
  }

  async function dispatchToMotor(target, text) {
    const mode = normalizeMotorId(target);
    const label = d().motorLabel?.(mode) || mode;
    d().switchMode?.(mode);

    let result = { handled: false };
    if (mode === "video") result = await dispatchVideo(text);
    else if (mode === "tercume") result = await dispatchTercume(text);
    else if (mode === "mimar") result = await dispatchMimar(text);
    else if (mode === "hizir") {
      if (d().runHizirFromChat?.(text)) {
        say("Hızır panelinde tarama başlatıldı.");
        result = { handled: true };
      }
    } else if (mode === "programlama") {
      say(
        `**${label}** motoruna geçtim. Kod sorunu, pytest veya dosya yolunu yaz — editör sağda.`,
      );
      result = { handled: true };
    } else if (mode === "ses") {
      say(`**${label}** motoruna geçtim. «Metne dök» veya dosya seç; sohbetten devam edebilirsin.`);
      result = { handled: true };
    } else if (mode === "hafiza") {
      say(`**${label}** motoruna geçtim. Hatırlatmak veya analiz ettirmek istediğini yaz.`);
      result = { handled: true };
    } else {
      say(`**${label}** motoruna yönlendirdim.`);
      result = { handled: true };
    }

    if (result.handled) {
      d().setStatus?.(label, "Rüzgar");
    }
    return { ...result, switched: true, mode, label };
  }

  /**
   * Genel modda: niyet → motor delege
   * @returns {Promise<{handled: boolean}>}
   */
  async function tryDispatchFromGenel(text) {
    if (!deps) return { handled: false };
    if (d().getCurrentMode?.() !== "genel") return { handled: false };

    const raw = String(text || "").trim();
    if (!raw) return { handled: false };

    if (isHubHelpRequest(raw)) {
      say(hubHelpText());
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    if (isCasualGreeting(raw)) {
      say(
        "Aleyküm selam Ümit abi. **Ana Motor** hazır — video, tercüme, kod, mimar, ses… " +
          "Ne istersen söyle, seni doğru motora götürürüm. Liste: **hub yardım**",
      );
      d().setStatus?.("Ana Motor", "Rüzgar");
      return { handled: true };
    }

    const route = await fetchHubRoute(raw);
    if (!route || !route.target || route.target === "genel") {
      return { handled: false };
    }

    const label = route.target_label || route.target;
    say(`Ümit abi, bunu **${label}** motorunda hallediyorum…`);

    const out = await dispatchToMotor(route.target, raw);
    return { handled: !!out.handled };
  }

  /**
   * Aktif motorda atölye delege (hub geçişi sonrası veya doğrudan motor modu)
   */
  async function tryDispatchActiveMotor(text) {
    const mode = d().getCurrentMode?.() || "genel";
    if (mode === "genel") return { handled: false };

    if (mode === "video") return dispatchVideo(text);
    if (mode === "tercume") return dispatchTercume(text);
    if (mode === "mimar" || mode === "okuma") return dispatchMimar(text);
    if (mode === "hizir" && d().runHizirFromChat?.(text)) {
      return { handled: true };
    }
    return { handled: false };
  }

  function showChatWelcome(container) {
    if (!container) return;
    const w = document.createElement("div");
    w.className = "bubble assistant chat-welcome";
    w.setAttribute("role", "note");
    w.innerHTML =
      `<p class="chat-welcome-lead"><strong>Ana Motor — merkez.</strong></p>` +
      `<p>Video, tercüme, kod, mimar, ses… Tek sohbetten yönlendirir; gerekirse motoru açar.</p>` +
      `<ul class="chat-welcome-list">` +
      `<li>«YouTube linki indir» · «imam-ı rabbani eserlerini ara»</li>` +
      `<li>«pytest geçir» · «fotoğraf paneli aç»</li>` +
      `<li><strong>hub yardım</strong> — motor listesi</li>` +
      `</ul>` +
      `<p class="chat-welcome-foot">${VERSION} · Ümit &amp; Gökçenur</p>`;
    container.appendChild(w);
  }

  function init(options) {
    deps = options || {};
  }

  global.RuzgarAnaMotorHub = {
    VERSION,
    init,
    tryDispatchFromGenel,
    tryDispatchActiveMotor,
    showChatWelcome,
    isHubHelpRequest,
  };
})(typeof window !== "undefined" ? window : globalThis);
