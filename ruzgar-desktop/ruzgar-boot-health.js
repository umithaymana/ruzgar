/**
 * app.js yüklenmeden önce yerel API health — "Ana Motor · bağlanıyor" takılmasını önler.
 */
(function ruzgarBootHealth(global) {
  "use strict";

  const PORT = 8779;
  const LOCAL = `http://127.0.0.1:${PORT}`;
  const LOCALHOST = `http://localhost:${PORT}`;

  function normalizeRoot(raw) {
    let s = String(raw || "")
      .trim()
      .replace(/\/+$/, "")
      .replace(/127\.0\.0\.1:8777/gi, `127.0.0.1:${PORT}`)
      .replace(/localhost:8777/gi, `localhost:${PORT}`);
    if (/\/api$/i.test(s)) s = s.replace(/\/api$/i, "").replace(/\/+$/, "");
    return s;
  }

  function apiCandidates() {
    const out = [];
    try {
      const injected = global.__RUZGAR_API_ROOT__;
      if (injected) out.push(normalizeRoot(injected));
    } catch (_) {
      /* yok say */
    }
    try {
      if (global.location?.pathname?.startsWith("/ui")) {
        out.push(normalizeRoot(global.location.origin));
      }
    } catch (_) {
      /* yok say */
    }
    try {
      const remote = global.ruzgarApi?.getRemoteBrainEndpoint?.();
      if (remote) out.push(normalizeRoot(remote));
    } catch (_) {
      /* yok say */
    }
    out.push(LOCAL, LOCALHOST);
    return [...new Set(out.filter(Boolean))];
  }

  function $(id) {
    return global.document?.getElementById(id) || null;
  }

  function applyReady(j, base) {
    global.__RUZGAR_BOOT_HEALTH__ = j;
    global.__RUZGAR_BOOT_API__ = base;
    const strip = $("ana-motor-info-strip");
    const badge = $("ana-motor-phase-badge");
    const promise = $("ana-motor-promise");
    const apiChip = $("api-status");
    const banner = $("ruzgar-connection-banner");
    if (strip) {
      strip.classList.remove(
        "atelier-info-strip-ana--loading",
        "atelier-info-strip-ana--err",
      );
      strip.classList.add("atelier-info-strip-ana--ready");
    }
    const rev = String(j?.build?.rev || "").trim();
    if (badge) badge.textContent = rev ? `Ana Motor · ${rev}` : "Ana Motor · bağlı";
    if (promise) {
      promise.textContent =
        "Yerel sunucu aktif (127.0.0.1:8779). Sol menüden yardımcı motorlara geçebilirsiniz.";
    }
    if (apiChip) {
      apiChip.textContent = "Sunucu ✓";
      apiChip.className = "tech-chip ok";
    }
    if (banner) {
      banner.hidden = false;
      banner.classList.add("is-live");
    }
  }

  function applyErr() {
    const strip = $("ana-motor-info-strip");
    const apiChip = $("api-status");
    if (strip) {
      strip.classList.remove("atelier-info-strip-ana--loading");
      strip.classList.add("atelier-info-strip-ana--err");
    }
    if (apiChip) {
      apiChip.textContent = "Sunucu kapalı";
      apiChip.className = "tech-chip err";
    }
    const banner = $("ruzgar-connection-banner");
    if (banner) {
      banner.hidden = true;
      banner.classList.remove("is-live");
    }
  }

  async function probeOnce() {
    for (const base of apiCandidates()) {
      try {
        const ctrl = new AbortController();
        const tid = global.setTimeout(() => ctrl.abort(), 12000);
        let r;
        try {
          r = await global.fetch(`${base}/api/health?lite=1`, {
            method: "GET",
            cache: "no-store",
            signal: ctrl.signal,
          });
        } finally {
          global.clearTimeout(tid);
        }
        const j = await r.json();
        if (j && j.ok) {
          applyReady(j, base);
          global.__ruzgarBootHealthAt = Date.now();
          return true;
        }
      } catch (_) {
        /* sonraki aday */
      }
    }
    return false;
  }

  async function boot() {
    if (global.__RUZGAR_BOOT_HEALTH__?.ok) return;
    const ok = await probeOnce();
    if (!ok) applyErr();
  }

  void boot();
  let n = 0;
  const poll = global.setInterval(() => {
    n += 1;
    if (global.__RUZGAR_BOOT_HEALTH__?.ok || n > 40) {
      global.clearInterval(poll);
      return;
    }
    void probeOnce();
  }, 3000);
})(typeof window !== "undefined" ? window : globalThis);
