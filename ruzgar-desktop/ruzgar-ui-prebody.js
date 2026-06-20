/**
 * index.html govdesi yuklenmeden once: motor paneli kompakt / split CSS degiskenleri.
 * CSP script-src 'self' — inline script yasak; harici dosya.
 */
(function ruzgarUiPrebody(global) {
  "use strict";
  try {
    const motorsCompact = global.localStorage.getItem("ruzgarMotorsCompact");
    const compactOn = motorsCompact === "1" || motorsCompact === null;
    if (compactOn) {
      global.document.body.classList.add("ui-motors-compact");
      global.document.documentElement.style.setProperty("--ruzgar-motors-w", "52px");
    }
    if (!compactOn) {
      const splitRaw = global.localStorage.getItem("ruzgarSplit.v1");
      if (splitRaw) {
        const split = JSON.parse(splitRaw);
        if (typeof split.motors === "number" && split.motors > 80) {
          global.document.documentElement.style.setProperty(
            "--ruzgar-motors-w",
            `${split.motors}px`,
          );
        }
        if (typeof split.chat === "number") {
          global.document.documentElement.style.setProperty(
            "--ruzgar-chat-w",
            `${split.chat}px`,
          );
        }
      }
    }
  } catch (_) {
    /* ignore */
  }
})(typeof window !== "undefined" ? window : globalThis);
