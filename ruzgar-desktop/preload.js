const { contextBridge, ipcRenderer } = require("electron");
const fs = require("fs");
const path = require("path");

/** ruzgar_remote_api.txt — ilk yorum dışı satır = API kökü (tünel); yoksa boş. */
function readRemoteBrainEndpointFromDisk() {
  try {
    const p = path.join(__dirname, "ruzgar_remote_api.txt");
    if (!fs.existsSync(p)) return "";
    const raw = fs.readFileSync(p, "utf8");
    const line = raw.split(/\r?\n/).find((l) => {
      const t = String(l || "").trim();
      return t.length > 0 && !t.startsWith("#");
    });
    if (line) {
      return String(line)
        .trim()
        .replace(/\/+$/, "")
        .replace(/127\.0\.0\.1:8777/gi, "127.0.0.1:8779")
        .replace(/localhost:8777/gi, "localhost:8779");
    }
    return "http://127.0.0.1:8779";
  } catch (_) {
    return "http://127.0.0.1:8779";
  }
}

contextBridge.exposeInMainWorld("ruzgarApi", {
  /** Köprü kökü — app.js normalize eder; sonda /api olmamalı (çift /api/api önlenir). */
  getRemoteBrainEndpoint: () => readRemoteBrainEndpointFromDisk(),
  listDir: (rel) => ipcRenderer.invoke("workspace:list", rel),
  getRoot: () => ipcRenderer.invoke("workspace:root"),
  readText: (rel) => ipcRenderer.invoke("workspace:read-text", rel),
  writeText: (rel, text) =>
    ipcRenderer.invoke("workspace:write-text", { rel, text }),
  openModeWindow: (mode) => ipcRenderer.invoke("ruzgar:open-mode", mode),
  openWorkspaceRel: (rel) => ipcRenderer.invoke("ruzgar:open-workspace", rel),
  pickWorkspaceDirectory: () => ipcRenderer.invoke("ruzgar:pick-directory"),
  pickSaveDirectory: () => ipcRenderer.invoke("ruzgar:pick-save-directory"),
  openLocalhostUrl: (url) => ipcRenderer.invoke("ruzgar:open-external", url),
  openExternalUrl: (url) => ipcRenderer.invoke("ruzgar:open-external", url),
  /** Pencere geçmişi (dosya yok — tam yeniden yüklemeden çıkmak için) */
  navGoBack: () => ipcRenderer.invoke("ruzgar:nav-go-back"),
  navGoForward: () => ipcRenderer.invoke("ruzgar:nav-go-forward"),
  navReload: () => ipcRenderer.invoke("ruzgar:nav-reload"),
  restartApi: () => ipcRenderer.invoke("ruzgar:restart-api"),
  onMenu: (fn) => {
    ipcRenderer.on("ruzgar-menu", (_e, action) => fn(action));
  },
});
