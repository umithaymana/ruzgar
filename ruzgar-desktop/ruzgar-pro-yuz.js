/**
 * Çalışma masası: robot yüz, ses seçimi, kendi ses kaydı, proje klasörü.
 * Ümit & Gökçenur
 */
(function () {
  "use strict";

  const KEY = "ruzgar.pro.voice";
  const FOLDER_KEY = "ruzgar.pro.folder";
  const BUILTIN = {
    emel: { karakter: "asistan", backend: "edge", label: "Emel" },
    ahmet: { karakter: "alim", backend: "edge", label: "Ahmet" },
    edip: { karakter: "edip", backend: "edge", label: "Edip" },
  };

  const face = document.getElementById("ruzgar-face");
  const stateEl = document.getElementById("ruzgar-face-state");
  const hintEl = document.getElementById("ruzgar-presence-hint");
  const pathEl = document.getElementById("ruzgar-presence-path");
  const select = document.getElementById("ruzgar-voice-select");
  const nameInput = document.getElementById("ruzgar-voice-name");
  const fileInput = document.getElementById("ruzgar-voice-file");
  const previewBtn = document.getElementById("ruzgar-voice-preview");
  const readBtn = document.getElementById("ruzgar-pro-read");
  const folderBtn = document.getElementById("ruzgar-pro-folder");
  const folderOpenBtn = document.getElementById("ruzgar-pro-folder-open");
  const codeBtn = document.getElementById("ruzgar-pro-code");
  const toolsBtn = document.getElementById("ruzgar-pro-tools");
  const talkBtn = document.getElementById("ruzgar-pro-talk");

  if (!face || !select) return;

  let customId = "";

  function apiRoot() {
    const raw = window.ruzgarApi?.getRemoteBrainEndpoint?.() || window.RUZGAR_API || "http://127.0.0.1:8779";
    return String(raw || "http://127.0.0.1:8779").replace(/\/+$/, "");
  }

  function hint(text) {
    if (hintEl) hintEl.textContent = text || "";
  }

  function setState(text) {
    if (stateEl) stateEl.textContent = text;
  }

  function savedChoice() {
    try {
      return localStorage.getItem(KEY) || "emel";
    } catch (_) {
      return "emel";
    }
  }

  function remember(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (_) {
      /* yok say */
    }
  }

  window.ruzgarProVoicePayload = function () {
    const choice = savedChoice();
    if (choice.indexOf("ozel:") === 0) {
      return { karakter: "asistan", backend: "auto", prosody: true };
    }
    const row = BUILTIN[choice] || BUILTIN.emel;
    return { karakter: row.karakter, backend: row.backend, prosody: true };
  };

  function ensureOption(value, label) {
    let opt = select.querySelector('option[value="' + value + '"]');
    if (!opt) {
      opt = document.createElement("option");
      opt.value = value;
      select.appendChild(opt);
    }
    opt.textContent = label;
    return opt;
  }

  function applyChoice(value) {
    select.value = value;
    remember(value);
    const row = BUILTIN[value];
    setState(row ? row.label : "Kendi sesin");
    if (row) {
      void fetch(apiRoot() + "/api/ses/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ karakter: row.karakter, prosody: true }),
      }).catch(function () {});
      void fetch(apiRoot() + "/api/ses/kolonlar/uygula", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sohbet: "" }),
      }).catch(function () {});
    }
  }

  function syncTalking() {
    const pill = document.getElementById("tts-status-pill");
    const mic = document.getElementById("btn-mic");
    const audioLive = Array.prototype.some.call(
      document.querySelectorAll("audio"),
      function (a) {
        return !a.paused && !a.ended;
      }
    );
    const synth = !!(window.speechSynthesis && window.speechSynthesis.speaking);
    const talking = audioLive || synth || (pill && !pill.hidden);
    const listening = !!(mic && mic.classList.contains("listening"));
    face.classList.toggle("is-talking", talking && !listening);
    face.classList.toggle("is-listening", listening);
    if (talkBtn) {
      talkBtn.classList.toggle("is-on", listening);
      talkBtn.textContent = listening ? "Dinliyorum…" : "Konuş";
    }
    if (listening) setState("Dinliyor");
    else if (talking) setState("Konuşuyor");
    else {
      const choice = savedChoice();
      const row = BUILTIN[choice];
      setState(row ? row.label : "Kendi sesin");
    }
  }

  document.addEventListener(
    "play",
    function (ev) {
      if (ev.target && ev.target.tagName === "AUDIO") syncTalking();
    },
    true
  );
  document.addEventListener(
    "pause",
    function (ev) {
      if (ev.target && ev.target.tagName === "AUDIO") syncTalking();
    },
    true
  );
  document.addEventListener(
    "ended",
    function (ev) {
      if (ev.target && ev.target.tagName === "AUDIO") syncTalking();
    },
    true
  );

  const pill = document.getElementById("tts-status-pill");
  if (pill && window.MutationObserver) {
    new MutationObserver(syncTalking).observe(pill, {
      attributes: true,
      attributeFilter: ["hidden"],
    });
  }
  window.setInterval(syncTalking, 400);

  select.addEventListener("change", function () {
    const value = select.value;
    if (value.indexOf("ozel:") === 0) {
      customId = value.slice(5);
      remember(value);
      setState("Kendi sesin");
      void fetch(apiRoot() + "/api/ses/kolonlar/uygula", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sohbet: customId }),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("ses bağlanamadı");
          hint("Bu kayıt konuşma sesi oldu. Klon motoru yoksa Rüzgar Emel ile okur.");
        })
        .catch(function () {
          hint("Rüzgar kapalı. Açılınca bu ses konuşmaya bağlanır.");
        });
      return;
    }
    applyChoice(value);
    hint("");
  });

  if (previewBtn) {
    previewBtn.addEventListener("click", function () {
      const voice = window.ruzgarProVoicePayload();
      hint("Ses hazırlanıyor…");
      fetch(apiRoot() + "/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "Merhaba, ben Rüzgar. Seni dinliyorum.",
          karakter: voice.karakter,
          backend: voice.backend,
          prosody: true,
        }),
      })
        .then(function (res) {
          if (!res.ok) throw new Error("okunamadı");
          return res.blob();
        })
        .then(function (blob) {
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audio.addEventListener("ended", function () {
            URL.revokeObjectURL(url);
            syncTalking();
          });
          hint("");
          return audio.play();
        })
        .catch(function () {
          hint("Rüzgar kapalı. Açınca bu düğme seçili sesi okur.");
        });
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", function () {
      const file = fileInput.files && fileInput.files[0];
      fileInput.value = "";
      if (!file) return;
      const ad = (nameInput && nameInput.value.trim()) || file.name.replace(/\.[^.]+$/, "") || "Esin";
      const fd = new FormData();
      fd.append("file", file);
      fd.append("ad", ad);
      fd.append("sohbet", "1");
      fd.append("scope", "ozel");
      hint(ad + " kaydediliyor…");
      fetch(apiRoot() + "/api/ses/kolonlar", { method: "POST", body: fd })
        .then(function (res) {
          return res.json().then(function (data) {
            if (!res.ok) throw new Error((data && data.detail) || "yüklenemedi");
            return data;
          });
        })
        .then(function (data) {
          const rows = (data && data.kolonlar) || [];
          const mine = rows.filter(function (k) {
            return String(k.ad || "") === ad || String(k.scope || "") === "ozel";
          });
          const last = mine.length ? mine[mine.length - 1] : rows[rows.length - 1];
          const id = last && (last.id || last.kolon_id);
          if (!id) throw new Error("kayıt kimliği yok");
          customId = String(id);
          ensureOption("ozel:" + customId, ad + " — kendi sesin");
          select.value = "ozel:" + customId;
          remember(select.value);
          return fetch(apiRoot() + "/api/ses/kolonlar/uygula", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sohbet: customId }),
          });
        })
        .then(function () {
          setState("Kendi sesin");
          hint(ad + " eklendi. Klon motoru hazırsa Rüzgar bu sesle konuşur; değilse Emel okur.");
        })
        .catch(function () {
          hint("Ses eklenemedi. Rüzgar açıkken 30 saniyelik net bir kayıt dene.");
        });
    });
  }

  if (readBtn) {
    readBtn.addEventListener("click", function () {
      const box = document.getElementById("opt-voice-out");
      if (!box) return;
      box.checked = !box.checked;
      box.dispatchEvent(new Event("change", { bubbles: true }));
      readBtn.classList.toggle("is-on", box.checked);
      hint(box.checked ? "Yanıtlar sesli okunacak." : "Sesli okuma kapalı.");
    });
    const box = document.getElementById("opt-voice-out");
    if (box) readBtn.classList.toggle("is-on", box.checked);
  }

  function showFolder(rel) {
    if (pathEl) pathEl.textContent = rel ? "Bağlı klasör: " + rel : "Bağlı klasör yok";
  }

  try {
    showFolder(localStorage.getItem(FOLDER_KEY) || "");
  } catch (_) {
    showFolder("");
  }

  if (folderBtn) {
    folderBtn.addEventListener("click", function () {
      const api = window.ruzgarApi;
      if (!api || !api.pickWorkspaceDirectory) {
        hint("Klasör bağlamak için masaüstü Rüzgar penceresini aç.");
        return;
      }
      api.pickWorkspaceDirectory().then(function (r) {
        if (!r || !r.ok) {
          hint(r && r.error ? r.error : "Klasör seçilmedi. Proje kökünün içinden bir klasör seç.");
          return;
        }
        const rel = String(r.rel || "");
        try {
          localStorage.setItem(FOLDER_KEY, rel);
        } catch (_) {
          /* yok say */
        }
        const work = document.getElementById("tercume-work-root");
        if (work && rel) work.value = rel;
        showFolder(rel || "(proje kökü)");
        hint("Klasör bağlandı. Programlama ve çeviri bu yolu kullanır.");
      });
    });
  }

  if (folderOpenBtn) {
    folderOpenBtn.addEventListener("click", function () {
      let rel = "";
      try {
        rel = localStorage.getItem(FOLDER_KEY) || "";
      } catch (_) {
        rel = "";
      }
      const api = window.ruzgarApi;
      if (!api || !api.openWorkspaceRel) {
        hint("Klasörü açmak için masaüstü Rüzgar penceresini aç.");
        return;
      }
      api.openWorkspaceRel(rel);
    });
  }

  if (codeBtn) {
    codeBtn.addEventListener("click", function () {
      const btn = document.getElementById("motor-side-programlama");
      if (btn) btn.click();
    });
  }

  if (toolsBtn) {
    toolsBtn.addEventListener("click", function () {
      const on = document.body.classList.toggle("ruzgar-pro-tools");
      toolsBtn.classList.toggle("is-on", on);
      hint(on ? "Atölye ayrıntıları açık." : "Atölye ayrıntıları gizlendi.");
    });
  }

  if (talkBtn) {
    talkBtn.addEventListener("click", function () {
      if (typeof window.__ruzgarMicToggle === "function") window.__ruzgarMicToggle();
    });
  }

  const initial = savedChoice();
  if (initial.indexOf("ozel:") === 0) {
    ensureOption(initial, "Kendi sesin");
    select.value = initial;
    setState("Kendi sesin");
  } else if (BUILTIN[initial]) {
    select.value = initial;
    setState(BUILTIN[initial].label);
  }
  syncTalking();
})();
