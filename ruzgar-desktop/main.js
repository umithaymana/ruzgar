const path = require("path");
const fs = require("fs");
/**
 * Chromium (Chrome değil) konuşma tanıması için Google API anahtarı gerekir.
 * İlk satırı kullanır; # ile başlayan satırlar yorum sayılır.
 * https://www.electronjs.org/docs/latest/api/environment-variables#google_api_key
 */
(function loadGoogleApiKeyForSpeech() {
  try {
    if (process.env.GOOGLE_API_KEY) return;
    const keyFile = path.join(__dirname, "google_api_key.txt");
    if (!fs.existsSync(keyFile)) return;
    const raw = fs.readFileSync(keyFile, "utf8");
    const line = raw.split(/\r?\n/).find((l) => {
      const t = l.trim();
      return t.length > 0 && !t.startsWith("#");
    });
    if (line) process.env.GOOGLE_API_KEY = line.trim();
  } catch (_) {
    /* yok say */
  }
})();

/** Node ile `node main.js` çalıştırılırsa `require("electron")` string döner; `app` tanımsız olur. */
const electronApi = require("electron");
if (typeof electronApi === "string" || !electronApi.app) {
  console.error(
    "[RÜZGAR] main.js yalnızca Electron ile çalışır. ruzgar-desktop klasöründe: npm start"
  );
  process.exit(1);
}
const {
  app,
  BrowserWindow,
  Menu,
  ipcMain,
  shell,
  dialog,
  session,
} = electronApi;
const { pathToFileURL } = require("url");

const WORKSPACE_ROOT = path.resolve(__dirname, "..");

function activeWindow(fallback) {
  return BrowserWindow.getFocusedWindow() || fallback;
}

function sharedWebPreferences() {
  return {
    preload: path.join(__dirname, "preload.js"),
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: false,
  };
}

function openIndexMode(mode) {
  const m = String(mode || "genel");
  const base = pathToFileURL(path.join(__dirname, "index.html")).href;
  const win = new BrowserWindow({
    width: 1280,
    height: 840,
    minWidth: 960,
    minHeight: 600,
    title: `RÜZGAR — ${m}`,
    backgroundColor: "#1e1e1e",
    show: false,
    webPreferences: sharedWebPreferences(),
  });
  const htmlPath = path.join(__dirname, "index.html");
  win.webContents.on("did-fail-load", (_e, code, desc, url) => {
    dialog.showErrorBox(
      "RUZGAR",
      `Sayfa yuklenemedi: ${desc} (${code})\n${url}\n\nDosya: ${htmlPath}`
    );
  });
  win
    .loadURL(`${base}?mode=${encodeURIComponent(m)}`)
    .catch((err) => {
      dialog.showErrorBox("RUZGAR", `loadURL: ${err.message}\n${htmlPath}`);
    });
  win.once("ready-to-show", () => {
    win.show();
    win.focus();
  });
}

function safeWorkspaceAbs(relPath) {
  const trimmed = String(relPath ?? "")
    .trim()
    .replace(/^[/\\]+/, "");
  const abs = trimmed
    ? path.resolve(WORKSPACE_ROOT, trimmed)
    : path.resolve(WORKSPACE_ROOT);
  const root = path.resolve(WORKSPACE_ROOT);
  const relCheck = path.relative(root, abs);
  if (relCheck.startsWith("..") || path.isAbsolute(relCheck)) return null;
  return abs;
}

const SKIP_DIR_NAMES = new Set([
  "node_modules",
  "__pycache__",
  ".venv",
  "venv",
  ".git",
]);

function safeListDir(rel = "") {
  const normRel = String(rel ?? "")
    .trim()
    .replace(/^[/\\]+/, "")
    .replace(/\\/g, "/");
  const base = safeWorkspaceAbs(normRel);
  if (!base || !fs.existsSync(base) || !fs.statSync(base).isDirectory()) {
    return [];
  }
  return fs
    .readdirSync(base, { withFileTypes: true })
    .filter((e) => {
      const n = e.name;
      if (SKIP_DIR_NAMES.has(n)) return false;
      return !n.startsWith(".") || n === ".vscode";
    })
    .map((e) => ({
      name: e.name,
      isDir: e.isDirectory(),
      rel: normRel ? `${normRel}/${e.name}` : e.name,
    }))
    .sort((a, b) => {
      if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
      return a.name.localeCompare(b.name, "tr");
    });
}

function buildMenu(mainWin) {
  // Faz 0: Sol motor menüsü artık ses/okuma/video/programlama/üretim/gelişim/tercüme
  // motorlarını yönetiyor. Üst native bar yalnızca dosya/düzen ve geliştirici aracıyla
  // sade tutulur; mod pencerelerini açan eski menüler kaldırıldı.
  const template = [
    {
      label: "dosya",
      submenu: [
        {
          label: "Çalışma klasörünü göster",
          click: () => shell.openPath(WORKSPACE_ROOT),
        },
        {
          label: "ilim-assistant klasörü",
          click: () =>
            shell.openPath(path.join(WORKSPACE_ROOT, "ilim-assistant")),
        },
        {
          label: "ilim-video klasörü",
          click: () =>
            shell.openPath(path.join(WORKSPACE_ROOT, "ilim-video")),
        },
        { type: "separator" },
        {
          label: "Yeni sohbet penceresi (genel)",
          click: () => openIndexMode("genel"),
        },
        { type: "separator" },
        { label: "Çıkış", role: "quit" },
      ],
    },
    {
      label: "düzen",
      submenu: [
        {
          label: "Sohbet kutusuna odaklan (aktif pencere)",
          click: () => {
            const w = activeWindow(mainWin);
            w?.webContents.send("ruzgar-menu", "focus-chat");
          },
        },
        { type: "separator" },
        { label: "Geri al", role: "undo" },
        { label: "Yinele", role: "redo" },
        { type: "separator" },
        { label: "Kes", role: "cut" },
        { label: "Kopyala", role: "copy" },
        { label: "Yapıştır", role: "paste" },
      ],
    },
    {
      label: "gelişim",
      submenu: [
        {
          label: "Geliştirici araçları (DevTools)",
          accelerator: "F12",
          click: () => {
            const w = activeWindow(mainWin);
            w?.webContents.toggleDevTools();
          },
        },
      ],
    },
  ];
  return Menu.buildFromTemplate(template);
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 960,
    minHeight: 600,
    title: "Rüzgar",
    backgroundColor: "#1e1e1e",
    show: false,
    webPreferences: sharedWebPreferences(),
  });

  Menu.setApplicationMenu(buildMenu(win));

  const htmlPath = path.join(__dirname, "index.html");
  win.webContents.on("did-fail-load", (_e, code, desc, url) => {
    dialog.showErrorBox(
      "RUZGAR",
      `Sayfa yuklenemedi: ${desc} (${code})\n${url}\n\nDosya: ${htmlPath}`
    );
  });

  win.loadFile(htmlPath).catch((err) => {
    dialog.showErrorBox(
      "RUZGAR",
      `loadFile: ${err.message}\n${htmlPath}`
    );
  });

  win.once("ready-to-show", () => {
    win.show();
    win.focus();
  });
}

app.whenReady().then(() => {
  /** Mikrofon / ses yakalama — Windows izin diyaloğu ve Electron oturumu için */
  try {
    const defaultSession = session && session.defaultSession;
    if (defaultSession) {
      defaultSession.setPermissionRequestHandler(
        (_wc, permission, callback) => {
          if (typeof callback !== "function") return;
          const allow = new Set([
            "media",
            "audioCapture",
            "microphone",
            "display-capture",
          ]);
          callback(allow.has(permission));
        }
      );
      defaultSession.setPermissionCheckHandler((_wc, permission) => {
        return (
          permission === "media" ||
          permission === "audioCapture" ||
          permission === "microphone"
        );
      });
    }
  } catch (e) {
    console.error("[RÜZGAR] Oturum izin ayarları:", e);
  }

  ipcMain.handle("workspace:list", (_e, rel) => safeListDir(rel || ""));
  ipcMain.handle("workspace:root", () => WORKSPACE_ROOT);
  ipcMain.handle("workspace:read-text", (_e, rel) => {
    try {
      const trimmed = String(rel ?? "").trim().replace(/^[/\\]+/, "");
      if (!trimmed) {
        return { ok: false, error: "Dosya yolu gerekli." };
      }
      const p = safeWorkspaceAbs(trimmed);
      if (!p || !fs.existsSync(p) || !fs.statSync(p).isFile()) {
        return { ok: false, error: "Dosya yok veya bir klasör seçildi." };
      }
      const st = fs.statSync(p);
      if (st.size > 2_000_000) {
        return { ok: false, error: "Dosya çok büyük (2 MB okuma sınırı)." };
      }
      const text = fs.readFileSync(p, "utf8");
      return { ok: true, text };
    } catch (e) {
      return { ok: false, error: e && e.message ? String(e.message) : String(e) };
    }
  });
  ipcMain.handle("workspace:write-text", (_e, payload) => {
    try {
      const rawRel = payload && payload.rel != null ? String(payload.rel) : "";
      const trimmed = rawRel.trim().replace(/^[/\\]+/, "");
      if (!trimmed) {
        return { ok: false, error: "Kayıt için göreli dosya yolu gerekli." };
      }
      const text = payload && payload.text != null ? String(payload.text) : "";
      const p = safeWorkspaceAbs(trimmed);
      if (!p) {
        return { ok: false, error: "Geçersiz dosya yolu." };
      }
      const bytes = Buffer.byteLength(text, "utf8");
      if (bytes > 2_500_000) {
        return { ok: false, error: "İçerik çok büyük (yaklaşık 2.5 MB yazma sınırı)." };
      }
      fs.mkdirSync(path.dirname(p), { recursive: true });
      fs.writeFileSync(p, text, "utf8");
      return { ok: true };
    } catch (e) {
      return { ok: false, error: e && e.message ? String(e.message) : String(e) };
    }
  });
  ipcMain.handle("ruzgar:open-mode", (_e, mode) => {
    openIndexMode(String(mode || "genel"));
  });
  ipcMain.handle("ruzgar:open-workspace", (_e, rel) => {
    const r = String(rel || "").replace(/^[/\\]+/, "");
    const target = path.resolve(WORKSPACE_ROOT, r);
    if (!target.startsWith(WORKSPACE_ROOT)) {
      return false;
    }
    shell.openPath(target);
    return true;
  });
  ipcMain.handle("ruzgar:open-external", (_e, url) => {
    try {
      const raw = String(url || "").trim();
      const u = new URL(raw);
      if (u.protocol !== "http:" && u.protocol !== "https:") {
        return false;
      }
      const h = (u.hostname || "").toLowerCase();
      if (h === "localhost" || h === "127.0.0.1") {
        return false;
      }
      shell.openExternal(u.href);
      return true;
    } catch {
      return false;
    }
  });

  function focusedWebContents() {
    const w = BrowserWindow.getFocusedWindow();
    return w?.webContents ?? null;
  }

  ipcMain.handle("ruzgar:nav-go-back", () => {
    const wc = focusedWebContents();
    if (wc && wc.canGoBack()) {
      wc.goBack();
      return true;
    }
    return false;
  });
  ipcMain.handle("ruzgar:nav-go-forward", () => {
    const wc = focusedWebContents();
    if (wc && wc.canGoForward()) {
      wc.goForward();
      return true;
    }
    return false;
  });
  ipcMain.handle("ruzgar:nav-reload", () => {
    const wc = focusedWebContents();
    if (wc) {
      wc.reload();
      return true;
    }
    return false;
  });

  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
}).catch((err) => {
  console.error("[RÜZGAR] whenReady:", err);
  try {
    dialog.showErrorBox(
      "RUZGAR",
      `Uygulama başlatılamadı: ${err && err.message ? err.message : String(err)}`
    );
  } catch (_) {
    /* dialog yoksa */
  }
  app.quit();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
