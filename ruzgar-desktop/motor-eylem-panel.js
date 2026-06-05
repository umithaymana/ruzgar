/**
 * Öğrenilen motor eylemleri — yönetim paneli (Faz C+)
 * Ümit & Gökçenur
 */
(function motorEylemPanel(global) {
  "use strict";

  const VERSION = "motor-eylem-panel-v1-2026-06-07";

  /** @type {Record<string, any>|null} */
  let deps = null;

  function d() {
    return deps || {};
  }

  function el() {
    return {
      overlay: document.getElementById("eylem-yonet-overlay"),
      list: document.getElementById("eylem-list"),
      empty: document.getElementById("eylem-list-empty"),
      path: document.getElementById("eylem-store-path"),
      catalog: document.getElementById("eylem-sub-intent-hint"),
    };
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

  function openPanel() {
    const { overlay } = el();
    if (!overlay) return;
    overlay.hidden = false;
    overlay.removeAttribute("aria-hidden");
    void refreshList();
    void refreshCatalogHint();
  }

  function closePanel() {
    const { overlay } = el();
    if (!overlay) return;
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
  }

  async function refreshCatalogHint() {
    const { catalog } = el();
    if (!catalog) return;
    try {
      const res = await fetch(`${d().getApi?.()}/api/ana-motor/sub-intents`);
      const j = await res.json().catch(() => ({}));
      if (!res.ok || !j.motors) {
        catalog.textContent = "Örnek: eylem öğret: «tetik» → video/kes";
        return;
      }
      const bits = Object.entries(j.motors)
        .slice(0, 4)
        .map(([m, subs]) => `${m}/${(subs || [])[0] || "?"}`)
        .join(" · ");
      catalog.textContent = `Alt-intent: ${bits} … — ${j.teach_format || ""}`;
    } catch {
      catalog.textContent = "eylem öğret: «tetik» → video/kes";
    }
  }

  async function refreshList() {
    const { list, empty, path } = el();
    if (!list) return;
    list.innerHTML = "";
    try {
      const rootQs = await workspaceRootQs();
      const q = rootQs ? `?${rootQs.replace(/^&/, "")}` : "";
      const res = await fetch(`${d().getApi?.()}/api/ana-motor/learned-actions${q}`);
      const j = await res.json().catch(() => ({}));
      if (path && j.path) path.textContent = j.path;
      const rows = Array.isArray(j.actions) ? j.actions : [];
      if (empty) empty.hidden = rows.length > 0;
      if (!rows.length) return;

      for (const row of rows) {
        const wrap = document.createElement("div");
        wrap.className = "eylem-list-row";
        const sub = row.sub_intent ? `/${row.sub_intent}` : "";
        const st = row.approved ? "✓" : "⏳";
        wrap.innerHTML =
          `<div class="eylem-list-main">` +
          `<span class="eylem-list-id">${st} <code>${String(row.id || "")}</code></span>` +
          `<span class="eylem-list-trig">«${String(row.trigger || "").replace(/</g, "&lt;")}»</span>` +
          `<span class="eylem-list-motor">→ ${String(row.motor || "")}${sub}</span>` +
          `</div>` +
          `<button type="button" class="btn-secondary btn-compact eylem-del-btn" data-id="${String(row.id || "").replace(/"/g, "&quot;")}">Sil</button>`;
        list.appendChild(wrap);
      }

      list.querySelectorAll(".eylem-del-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const id = btn.getAttribute("data-id");
          if (id) void deleteAction(id);
        });
      });
    } catch (e) {
      if (empty) {
        empty.hidden = false;
        empty.textContent = String(e.message || e);
      }
    }
  }

  async function deleteAction(actionId) {
    const id = String(actionId || "").trim();
    if (!id) return;
    if (!global.confirm(`Eylem silinsin mi? (${id})`)) return;
    try {
      const rootQs = await workspaceRootQs();
      const q = rootQs ? `?${rootQs.replace(/^&/, "")}` : "";
      const res = await fetch(
        `${d().getApi?.()}/api/ana-motor/learned-action/${encodeURIComponent(id)}${q}`,
        { method: "DELETE" },
      );
      if (!res.ok) {
        const j = await res.json().catch(() => ({}));
        throw new Error(j.detail || res.statusText);
      }
      d().flash?.(`Eylem silindi: ${id}`);
      await refreshList();
    } catch (e) {
      d().flash?.(String(e.message || e));
    }
  }

  function wire() {
    const { overlay } = el();
    document.getElementById("btn-eylem-yonet")?.addEventListener("click", () => openPanel());
    document.getElementById("btn-eylem-yonet-kapat")?.addEventListener("click", () => closePanel());
    document.getElementById("btn-eylem-yonet-refresh")?.addEventListener("click", () => void refreshList());
    overlay?.addEventListener("click", (e) => {
      if (e.target === overlay) closePanel();
    });
    document.addEventListener("keydown", (ev) => {
      if (ev.key === "Escape" && overlay && !overlay.hidden) closePanel();
    });
  }

  function init(options) {
    deps = options || {};
    wire();
  }

  global.RuzgarMotorEylemPanel = {
    VERSION,
    init,
    openPanel,
    closePanel,
    refreshList,
  };
})(typeof window !== "undefined" ? window : globalThis);
