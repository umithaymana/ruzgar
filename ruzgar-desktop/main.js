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
  BrowserView,
  Menu,
  ipcMain,
  shell,
  dialog,
  session,
} = electronApi;
const { pathToFileURL } = require("url");
const http = require("http");
const { spawn } = require("child_process");

const WORKSPACE_ROOT = path.resolve(__dirname, "..");
const DEFAULT_API_PORT = 8779;

/** Tek Electron örneği — ikinci kısayol/tıklama mevcut pencereyi öne getirir. */
const gotSingleInstanceLock = app.requestSingleInstanceLock();
if (!gotSingleInstanceLock) {
  app.quit();
}

/** @type {import("electron").BrowserView | null} */
let youtubeCinemaView = null;
/** @type {import("electron").BrowserWindow | null} */
let youtubeCinemaHostWin = null;

function hideYoutubeCinemaView() {
  if (!youtubeCinemaView || !youtubeCinemaHostWin) return;
  try {
    youtubeCinemaHostWin.removeBrowserView(youtubeCinemaView);
  } catch (_) {
    /* ignore */
  }
  try {
    youtubeCinemaView.webContents.close();
  } catch (_) {
    /* ignore */
  }
  youtubeCinemaView = null;
  youtubeCinemaHostWin = null;
}

function normalizeYoutubeWatchUrlMain(url) {
  let u = String(url || "").trim();
  u = u.replace(/([?&])v-([a-zA-Z0-9_-]{6,})/i, "$1v=$2");
  return u;
}

function readLocalApiPortFromDisk() {
  try {
    const p = path.join(__dirname, "ruzgar_remote_api.txt");
    if (!fs.existsSync(p)) return DEFAULT_API_PORT;
    const line = fs
      .readFileSync(p, "utf8")
      .split(/\r?\n/)
      .find((l) => {
        const t = String(l || "").trim();
        return t.length > 0 && !t.startsWith("#");
      });
    if (!line) return DEFAULT_API_PORT;
    const u = new URL(String(line).trim().replace(/127\.0\.0\.1:8777/i, "127.0.0.1:8779"));
    const port = parseInt(u.port || String(DEFAULT_API_PORT), 10);
    return Number.isFinite(port) && port > 0 ? port : DEFAULT_API_PORT;
  } catch (_) {
    return DEFAULT_API_PORT;
  }
}

function probeApiHealth(port) {
  return new Promise((resolve) => {
    const req = http.get(
      `http://127.0.0.1:${port}/api/health`,
      { timeout: 6000 },
      (res) => {
        let body = "";
        res.on("data", (c) => {
          body += c;
        });
        res.on("end", () => {
          try {
            const j = JSON.parse(body);
            resolve(res.statusCode === 200 && j && j.ok === true);
          } catch (_) {
            resolve(false);
          }
        });
      }
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

function readExpectedBuildRev() {
  try {
    const p = path.join(WORKSPACE_ROOT, "ilim-assistant", "ruzgar_build_rev.txt");
    if (fs.existsSync(p)) {
      const line = fs
        .readFileSync(p, "utf8")
        .split(/\r?\n/)
        .find((l) => {
          const t = String(l || "").trim();
          return t.length > 0 && !t.startsWith("#");
        });
      if (line) return String(line).trim();
    }
  } catch (_) {
    /* ignore */
  }
  return "2026-06-15-ruzgar-programlama-pro-v1";
}

function fetchHealthJson(port) {
  return new Promise((resolve) => {
    const req = http.get(
      `http://127.0.0.1:${port}/api/health`,
      { timeout: 8000 },
      (res) => {
        let body = "";
        res.on("data", (c) => {
          body += c;
        });
        res.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (_) {
            resolve(null);
          }
        });
      }
    );
    req.on("error", () => resolve(null));
    req.on("timeout", () => {
      req.destroy();
      resolve(null);
    });
  });
}

function spawnForceRestartApi() {
  const ps1 = path.join(WORKSPACE_ROOT, "Ruzgar.ps1");
  if (!fs.existsSync(ps1)) return Promise.resolve(false);
  return new Promise((resolve) => {
    try {
      const child = spawn(
        "powershell.exe",
        [
          "-NoProfile",
          "-ExecutionPolicy",
          "Bypass",
          "-File",
          ps1,
          "-ForceRestart",
          "-ApiOnly",
        ],
        {
          cwd: WORKSPACE_ROOT,
          detached: true,
          stdio: "ignore",
          windowsHide: true,
        }
      );
      child.unref();
      resolve(true);
    } catch (_) {
      resolve(false);
    }
  });
}

async function waitForExpectedHealth(port, expectedRev, maxMs = 120000) {
  const deadline = Date.now() + maxMs;
  while (Date.now() < deadline) {
    const j = await fetchHealthJson(port);
    const rev = String(j?.build?.rev || "").trim();
    if (j && j.ok === true && rev === expectedRev) {
      return true;
    }
    await new Promise((r) => setTimeout(r, 600));
  }
  return false;
}

async function ensureFreshApiOnLaunch() {
  const port = readLocalApiPortFromDisk();
  const expected = readExpectedBuildRev();
  const skipBecauseLauncher = process.env.RUZGAR_ELECTRON_API_FRESH === "1";
  const j = await fetchHealthJson(port);
  const rev = String(j?.build?.rev || "").trim();
  const pro = j?.build?.programlama_pro_v1 === true;
  const fresh = Boolean(j && j.ok === true && rev === expected && pro);

  if (skipBecauseLauncher && fresh) {
    console.info(`[RÜZGAR] API launcher taze (rev=${rev})`);
    return;
  }
  if (process.env.RUZGAR_DESKTOP_FRESH_API === "0" && fresh) {
    return;
  }
  if (fresh && !skipBecauseLauncher) {
    console.info(`[RÜZGAR] API guncel rev=${rev}; yeniden baslatma atlandi`);
    return;
  }

  console.info(
    `[RÜZGAR] API yenileniyor (sunucu=${rev || "?"} beklenen=${expected})…`
  );
  await spawnForceRestartApi();
  const ok = await waitForExpectedHealth(port, expected, 120000);
  if (!ok) {
    console.warn("[RÜZGAR] API beklenen build rev ile hazir olmadi");
  } else {
    console.info(`[RÜZGAR] API hazir rev=${expected}`);
  }
}

async function ensureLocalApiServer() {
  const port = readLocalApiPortFromDisk();
  if (await probeApiHealth(port)) return;
  const ia = path.join(WORKSPACE_ROOT, "ilim-assistant");
  if (!fs.existsSync(path.join(ia, "run_desktop_api.py"))) return;
  const py = process.platform === "win32" ? "py" : "python";
  const args =
    process.platform === "win32"
      ? ["-3", "run_desktop_api.py", "--host", "127.0.0.1", "--port", String(port)]
      : ["run_desktop_api.py", "--host", "127.0.0.1", "--port", String(port)];
  const env = {
    ...process.env,
    RUZGAR_API_PORT: String(port),
    RUZGAR_SKIP_RAG_WARMUP: process.env.RUZGAR_SKIP_RAG_WARMUP || "1",
  };
  try {
    const child = spawn(py, args, {
      cwd: ia,
      detached: true,
      stdio: "ignore",
      windowsHide: true,
      env,
    });
    child.unref();
  } catch (e) {
    console.warn("[RÜZGAR] API otomatik başlatılamadı:", e && e.message ? e.message : e);
    return;
  }
  for (let i = 0; i < 180; i++) {
    await new Promise((r) => setTimeout(r, 500));
    if (await probeApiHealth(port)) {
      console.info(`[RÜZGAR] Yerel API hazır (127.0.0.1:${port})`);
      return;
    }
  }
  console.warn(`[RÜZGAR] API ${port} portunda 90 sn içinde yanıt vermedi`);
}

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

async function loadUiIntoWindow(win, queryString) {
  const port = readLocalApiPortFromDisk();
  const htmlPath = path.join(__dirname, "index.html");
  const qs = queryString ? `?${queryString}` : "";
  const uiUrl = `http://127.0.0.1:${port}/ui/index.html${qs}`;
  for (let i = 0; i < 180; i++) {
    if (await probeApiHealth(port)) {
      console.info(`[RÜZGAR] UI: ${uiUrl}`);
      return win.loadURL(uiUrl);
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  console.warn("[RÜZGAR] Yerel API yok — file:// yedek devre dışı (API şart)");
  dialog.showErrorBox(
    "RUZGAR",
    `Yerel API (127.0.0.1:${port}) hazır değil.\n\n` +
      "1) Ruzgar_Port_Temizle.bat (yönetici)\n" +
      "2) Ruzgar_TemizBaslat.bat\n\n" +
      "API gelene kadar arayüz açılmaz (bağlantı hatası önlenir)."
  );
  app.quit();
  return Promise.resolve();
}

function openIndexMode(mode) {
  const m = String(mode || "genel");
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
  win.webContents.on("did-fail-load", (_e, code, desc, url, isMainFrame) => {
    if (isMainFrame === false) return;
    dialog.showErrorBox(
      "RUZGAR",
      `Sayfa yuklenemedi: ${desc} (${code})\n${url}\n\nDosya: ${htmlPath}`
    );
  });
  loadUiIntoWindow(win, `mode=${encodeURIComponent(m)}`).catch((err) => {
    dialog.showErrorBox("RUZGAR", `loadUI: ${err.message}\n${htmlPath}`);
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
        { type: "separator" },
        {
          label: "Paneller…",
          accelerator: "Ctrl+Shift+P",
          click: () => {
            const w = activeWindow(mainWin);
            w?.webContents.send("ruzgar-menu", "sidebar:duzen");
          },
        },
      ],
    },
    {
      label: "gelişim",
      submenu: [
        {
          label: "Gelişim panelleri…",
          click: () => {
            const w = activeWindow(mainWin);
            w?.webContents.send("ruzgar-menu", "sidebar:gelisim");
          },
        },
        { type: "separator" },
        {
          label: "Geliştirici araçları",
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
  win.webContents.on("did-fail-load", (_e, code, desc, url, isMainFrame) => {
    if (isMainFrame === false) return;
    dialog.showErrorBox(
      "RUZGAR",
      `Sayfa yuklenemedi: ${desc} (${code})\n${url}\n\nDosya: ${htmlPath}`
    );
  });

  loadUiIntoWindow(win).catch((err) => {
    dialog.showErrorBox("RUZGAR", `loadUI: ${err.message}\n${htmlPath}`);
  });

  win.once("ready-to-show", () => {
    win.show();
    win.focus();
  });
}

app.on("second-instance", async () => {
  const wins = BrowserWindow.getAllWindows();
  if (!wins.length) return;
  const port = readLocalApiPortFromDisk();
  const apiReady = await probeApiHealth(port);
  for (const win of wins) {
    if (win.isMinimized()) win.restore();
    win.focus();
    if (!apiReady) continue;
    const wc = win.webContents;
    let current = "";
    try {
      current = wc.getURL();
    } catch (_) {
      /* ignore */
    }
    const onLocalUi =
      current.includes(`127.0.0.1:${port}/ui`) ||
      current.includes(`localhost:${port}/ui`);
    if (current.startsWith("file:") || !onLocalUi) {
      let qs = "";
      try {
        qs = new URL(current).search || "";
      } catch (_) {
        /* ignore */
      }
      const uiUrl = `http://127.0.0.1:${port}/ui/index.html${qs}`;
      console.info(`[RÜZGAR] second-instance → UI yenile: ${uiUrl}`);
      wc.loadURL(uiUrl);
    } else {
      wc.reloadIgnoringCache();
    }
  }
});

app.whenReady().then(async () => {
  if (!gotSingleInstanceLock) return;
  await ensureFreshApiOnLaunch();
  await ensureLocalApiServer();
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
  ipcMain.handle("ruzgar:pick-directory", async () => {
    const win = BrowserWindow.getFocusedWindow();
    const opts = { properties: ["openDirectory", "createDirectory"], title: "Çalışma klasörü seçin" };
    const r = win
      ? await dialog.showOpenDialog(win, opts)
      : await dialog.showOpenDialog(opts);
    if (r.canceled || !r.filePaths?.length) {
      return { ok: false };
    }
    const picked = path.resolve(r.filePaths[0]);
    const root = path.resolve(WORKSPACE_ROOT);
    if (!picked.startsWith(root)) {
      return { ok: false, error: "Klasör proje kökü içinde olmalı." };
    }
    const rel = path.relative(root, picked).split(path.sep).join("/");
    return { ok: true, rel };
  });
  ipcMain.handle("ruzgar:pick-save-directory", async () => {
    const win = BrowserWindow.getFocusedWindow();
    const opts = {
      properties: ["openDirectory", "createDirectory"],
      title: "İndirme klasörünü seçin (Farklı kaydet)",
    };
    const r = win
      ? await dialog.showOpenDialog(win, opts)
      : await dialog.showOpenDialog(opts);
    if (r.canceled || !r.filePaths?.length) {
      return { ok: false };
    }
    const picked = path.resolve(r.filePaths[0]);
    const root = path.resolve(WORKSPACE_ROOT);
    let rel = "";
    if (picked.startsWith(root)) {
      rel = path.relative(root, picked).split(path.sep).join("/");
    }
    return { ok: true, abs: picked, rel };
  });
  ipcMain.handle("ruzgar:youtube-cinema-show", async (_e, payload) => {
    const win = BrowserWindow.getFocusedWindow() || BrowserWindow.getAllWindows()[0];
    if (!win) return { ok: false, error: "Pencere yok" };
    const rawUrl = normalizeYoutubeWatchUrlMain(payload?.url);
    if (!rawUrl) return { ok: false, error: "URL yok" };
    let watchUrl = rawUrl;
    try {
      const u = new URL(rawUrl);
      const vid = u.searchParams.get("v");
      if (vid && u.hostname.includes("youtube")) {
        watchUrl = `https://www.youtube.com/watch?v=${encodeURIComponent(vid)}`;
      }
    } catch {
      return { ok: false, error: "Geçersiz URL" };
    }

    hideYoutubeCinemaView();

    const b = payload?.bounds || {};
    const x = Math.max(0, Math.round(Number(b.x) || 0));
    const y = Math.max(0, Math.round(Number(b.y) || 0));
    const w = Math.max(320, Math.round(Number(b.width) || 640));
    const h = Math.max(180, Math.round(Number(b.height) || 360));

    const view = new BrowserView({
      webPreferences: {
        partition: "persist:ruzgar-youtube-cinema",
        contextIsolation: true,
        nodeIntegration: false,
      },
    });
    win.addBrowserView(view);
    view.setBounds({ x, y, width: w, height: h });
    view.setAutoResize({ width: true, height: true });
    youtubeCinemaView = view;
    youtubeCinemaHostWin = win;

    await view.webContents.loadURL(watchUrl);
    return { ok: true };
  });
  ipcMain.handle("ruzgar:youtube-cinema-hide", () => {
    hideYoutubeCinemaView();
    return { ok: true };
  });
  ipcMain.handle("ruzgar:youtube-cinema-bounds", (_e, bounds) => {
    if (!youtubeCinemaView) return { ok: false };
    const b = bounds || {};
    youtubeCinemaView.setBounds({
      x: Math.max(0, Math.round(Number(b.x) || 0)),
      y: Math.max(0, Math.round(Number(b.y) || 0)),
      width: Math.max(320, Math.round(Number(b.width) || 640)),
      height: Math.max(180, Math.round(Number(b.height) || 360)),
    });
    return { ok: true };
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
  ipcMain.handle("ruzgar:nav-reload", (_evt, opts = {}) => {
    const wc = focusedWebContents();
    if (!wc) return false;
    const ignoreCache = !opts || opts.ignoreCache !== false;
    if (ignoreCache) wc.reloadIgnoringCache();
    else wc.reload();
    return true;
  });

  ipcMain.handle("ruzgar:restart-api", async () => {
    const ps1 = path.join(WORKSPACE_ROOT, "Ruzgar.ps1");
    if (!fs.existsSync(ps1)) {
      return { ok: false, error: "Ruzgar.ps1 bulunamadı" };
    }
    return new Promise((resolve) => {
      try {
        const child = spawn(
          "powershell.exe",
          [
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ps1,
            "-ForceRestart",
            "-ApiOnly",
          ],
          {
            cwd: WORKSPACE_ROOT,
            detached: true,
            stdio: "ignore",
            windowsHide: true,
          }
        );
        child.unref();
        resolve({ ok: true, message: "API yeniden başlatılıyor" });
      } catch (e) {
        resolve({ ok: false, error: e && e.message ? e.message : String(e) });
      }
    });
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
