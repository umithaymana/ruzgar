const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("ruzgarApi", {
  listDir: (rel) => ipcRenderer.invoke("workspace:list", rel),
  getRoot: () => ipcRenderer.invoke("workspace:root"),
  openModeWindow: (mode) => ipcRenderer.invoke("ruzgar:open-mode", mode),
  openWorkspaceRel: (rel) => ipcRenderer.invoke("ruzgar:open-workspace", rel),
  openLocalhostUrl: (url) => ipcRenderer.invoke("ruzgar:open-external", url),
  /** Pencere geçmişi (dosya yok — tam yeniden yüklemeden çıkmak için) */
  navGoBack: () => ipcRenderer.invoke("ruzgar:nav-go-back"),
  navGoForward: () => ipcRenderer.invoke("ruzgar:nav-go-forward"),
  navReload: () => ipcRenderer.invoke("ruzgar:nav-reload"),
  onMenu: (fn) => {
    ipcRenderer.on("ruzgar-menu", (_e, action) => fn(action));
  },
});
