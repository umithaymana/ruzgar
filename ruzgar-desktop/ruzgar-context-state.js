/**
 * Rüzgar — global bağlam durumu (Component mimarisi)
 * UI seçimleri (seviye, motor) tek kaynaktan API/prompt'a akar.
 */
(function initRuzgarContextState(global) {
  const LS_SYSTEM_LEVEL = "ruzgar_system_level";

  const DEFAULT_STATE = {
    motor: "genel",
    system_level: "akademik",
  };

  class RuzgarContextState {
    constructor() {
      this._state = { ...DEFAULT_STATE };
      this._listeners = new Set();
      try {
        const saved = localStorage.getItem(LS_SYSTEM_LEVEL);
        if (saved === "ilkokul" || saved === "lise" || saved === "akademik") {
          this._state.system_level = saved;
        }
      } catch {
        /* ignore */
      }
    }

    get(key) {
      return this._state[key];
    }

    getSnapshot() {
      return { ...this._state };
    }

    set(partial) {
      if (!partial || typeof partial !== "object") return;
      let changed = false;
      for (const [k, v] of Object.entries(partial)) {
        if (this._state[k] !== v) {
          this._state[k] = v;
          changed = true;
        }
      }
      if (changed) this._notify();
    }

    setMotor(motor) {
      const m = String(motor || "").trim().toLowerCase();
      if (m === "okuma") this.set({ motor: "mimar" });
      else if (m) this.set({ motor: m });
    }

    setSystemLevel(level) {
      const L = String(level || "").trim().toLowerCase();
      const norm =
        L === "ilkokul" || L === "lise" || L === "akademik" ? L : "akademik";
      this.set({ system_level: norm });
      try {
        localStorage.setItem(LS_SYSTEM_LEVEL, norm);
      } catch {
        /* ignore */
      }
    }

    /** Tercüme API / prompt için — system_level: {değer} */
    toPromptContext() {
      const level = this._state.system_level || "akademik";
      return {
        system_level: level,
        read_level: level,
      };
    }

    /** FormData veya JSON gövdesine ek alanlar */
    appendToFormData(fd) {
      if (!fd || typeof fd.append !== "function") return fd;
      const ctx = this.toPromptContext();
      fd.append("system_level", ctx.system_level);
      fd.append("read_level", ctx.read_level);
      return fd;
    }

    appendToJsonBody(body) {
      const ctx = this.toPromptContext();
      return { ...body, system_level: ctx.system_level, read_level: ctx.read_level };
    }

    subscribe(fn) {
      if (typeof fn !== "function") return () => {};
      this._listeners.add(fn);
      return () => this._listeners.delete(fn);
    }

    _notify() {
      const snap = this.getSnapshot();
      this._listeners.forEach((fn) => {
        try {
          fn(snap);
        } catch (e) {
          console.warn("[RuzgarContext]", e);
        }
      });
      try {
        global.dispatchEvent(
          new CustomEvent("ruzgar-context-change", { detail: snap }),
        );
      } catch {
        /* ignore */
      }
    }
  }

  const instance = new RuzgarContextState();
  global.RuzgarContext = instance;
})(typeof window !== "undefined" ? window : globalThis);
