/**
 * Klon ses stüdyosu — Tilavet yanı panel: liste, motor tikleri, önizleme, ince ayar.
 * Ümit & Gökçenur · 2026-06-08
 */
(function () {
  "use strict";

  const MOTORS = ["sohbet", "tilavet", "okuma"];
  const MOTOR_SHORT = { sohbet: "S", tilavet: "T", okuma: "O" };

  const el = {
    panel: document.getElementById("ses-klon-studio"),
    tbody: document.getElementById("ses-klon-studio-tbody"),
    hint: document.getElementById("ses-klon-studio-hint"),
    tabs: document.querySelectorAll(".ses-klon-tab"),
    hiz: document.getElementById("ses-klon-hiz"),
    huzur: document.getElementById("ses-klon-huzur"),
    durak: document.getElementById("ses-klon-durak"),
    hizVal: document.getElementById("ses-klon-hiz-val"),
    huzurVal: document.getElementById("ses-klon-huzur-val"),
    durakVal: document.getElementById("ses-klon-durak-val"),
    lang: document.getElementById("ses-klon-lang"),
    tilavetMod: document.getElementById("ses-klon-tilavet-mod"),
    prosody: document.getElementById("ses-klon-prosody"),
    btnDinle: document.getElementById("btn-ses-klon-dinle"),
    btnTuneKaydet: document.getElementById("btn-ses-klon-tune-kaydet"),
    btnMotorUygula: document.getElementById("btn-ses-klon-motor-uygula"),
    file: document.getElementById("ses-klon-studio-file"),
    ad: document.getElementById("ses-klon-studio-ad"),
    audio: document.getElementById("ses-klon-preview-audio"),
    transcript: document.getElementById("ses-transcript"),
  };

  if (!el.panel || !el.tbody) return;

  let snapshot = { kolonlar: [], aktif: {} };
  let tabScope = "halka";
  let previewPick = { id: null, scope: "halka" };
  let draftAktif = { sohbet: null, tilavet: null, okuma: null };

  function apiRoot() {
    return window.ruzgarApi?.getApi?.() || window.RUZGAR_API || "http://127.0.0.1:8779";
  }

  function flash(msg) {
    if (typeof window.flashRuzgarDurum === "function") window.flashRuzgarDurum(msg);
    if (el.hint) el.hint.textContent = msg || "";
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function sliderToFloat(inp, def) {
    if (!inp) return def;
    return Math.round(Number(inp.value)) / 100;
  }

  function durakToFloat(inp) {
    if (!inp) return 1.0;
    return Math.round(Number(inp.value)) / 100;
  }

  function syncSliderLabels() {
    if (el.hizVal) el.hizVal.textContent = sliderToFloat(el.hiz, 0.92).toFixed(2);
    if (el.huzurVal) el.huzurVal.textContent = sliderToFloat(el.huzur, 0.88).toFixed(2);
    if (el.durakVal) el.durakVal.textContent = durakToFloat(el.durak).toFixed(2);
  }

  function loadTuningToSliders(tuning) {
    const t = tuning || {};
    if (el.hiz) el.hiz.value = String(Math.round((t.hiz ?? 0.92) * 100));
    if (el.huzur) el.huzur.value = String(Math.round((t.huzur ?? 0.88) * 100));
    if (el.durak) el.durak.value = String(Math.round((t.durak ?? 1.0) * 100));
    if (el.lang && t.lang) el.lang.value = t.lang;
    if (el.tilavetMod) el.tilavetMod.checked = !!t.tilavet_mod;
    if (el.prosody) el.prosody.checked = t.prosody !== false;
    syncSliderLabels();
  }

  function currentTuningPayload() {
    return {
      hiz: sliderToFloat(el.hiz, 0.92),
      huzur: sliderToFloat(el.huzur, 0.88),
      durak: durakToFloat(el.durak),
      lang: el.lang?.value || "tr",
      tilavet_mod: !!el.tilavetMod?.checked,
      prosody: !!el.prosody?.checked,
    };
  }

  function filteredRows() {
    return (snapshot.kolonlar || []).filter((k) => (k.scope || "halka") === tabScope);
  }

  function syncDraftFromSnapshot() {
    const a = snapshot.aktif || {};
    draftAktif = {
      sohbet: a.sohbet || null,
      tilavet: a.tilavet || null,
      okuma: a.okuma || null,
    };
  }

  function renderList() {
    const rows = filteredRows();
    if (!rows.length) {
      const msg =
        tabScope === "ozel"
          ? "Henüz özel ses yok — «+ Ses ekle» ile yükleyin (commit edilmez)."
          : "Bu depoda ses yok.";
      el.tbody.innerHTML = `<tr><td colspan="5" class="ses-kolon-empty">${msg}</td></tr>`;
      return;
    }

    el.tbody.innerHTML = rows
      .map((k) => {
        const kid = String(k.id);
        const sc = k.scope || "halka";
        const checkedPreview =
          previewPick.id === kid && previewPick.scope === sc ? "checked" : "";
        const badge = sc === "ozel" ? '<span class="ses-scope-badge ozel">özel</span>' : "";
        const motorCells = MOTORS.map(
          (m) =>
            `<td class="ses-kolon-radio"><input type="radio" name="studio-motor-${m}" value="${escapeHtml(kid)}" data-scope="${escapeHtml(sc)}" data-motor="${m}" ${draftAktif[m] === kid ? "checked" : ""} title="${m}" /></td>`,
        ).join("");
        return `<tr data-id="${escapeHtml(kid)}" data-scope="${escapeHtml(sc)}">
          <td class="ses-kolon-radio"><input type="radio" name="studio-preview" value="${escapeHtml(kid)}" data-scope="${escapeHtml(sc)}" ${checkedPreview} aria-label="Önizle: ${escapeHtml(k.ad)}" /></td>
          <td><span class="ses-kolon-name">${escapeHtml(k.ad)}</span>${badge}<span class="ses-kolon-meta">${k.wav_ok ? `${k.size_kb} KB` : "dosya yok"}</span></td>
          ${motorCells}
        </tr>`;
      })
      .join("");

    el.tbody.querySelectorAll('input[name="studio-preview"]').forEach((inp) => {
      inp.addEventListener("change", () => {
        if (!inp.checked) return;
        previewPick = { id: inp.value, scope: inp.getAttribute("data-scope") || "halka" };
        const row = (snapshot.kolonlar || []).find(
          (k) => k.id === previewPick.id && (k.scope || "halka") === previewPick.scope,
        );
        loadTuningToSliders(row?.tuning);
        flash(`Önizleme: ${row?.ad || previewPick.id}`);
      });
    });

    el.tbody.querySelectorAll('input[name^="studio-motor-"]').forEach((inp) => {
      inp.addEventListener("change", () => {
        const motor = inp.getAttribute("data-motor");
        if (motor && inp.checked) draftAktif[motor] = inp.value;
      });
    });

    el.tbody.querySelectorAll("tr[data-id]").forEach((tr) => {
      tr.addEventListener("click", (ev) => {
        if (ev.target.tagName === "INPUT") return;
        const id = tr.getAttribute("data-id");
        const sc = tr.getAttribute("data-scope") || "halka";
        const radio = tr.querySelector('input[name="studio-preview"]');
        if (radio) {
          radio.checked = true;
          previewPick = { id, scope: sc };
          const row = (snapshot.kolonlar || []).find((k) => k.id === id && (k.scope || "halka") === sc);
          loadTuningToSliders(row?.tuning);
        }
      });
    });
  }

  async function loadSnapshot() {
    flash("Klon sesler yükleniyor…");
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar`, { method: "GET" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      snapshot = await res.json();
      syncDraftFromSnapshot();
      if (!previewPick.id) {
        const first = filteredRows()[0];
        if (first) {
          previewPick = { id: first.id, scope: first.scope || "halka" };
          loadTuningToSliders(first.tuning);
        }
      }
      renderList();
      const dep = snapshot.depolar?.ozel?.label || "Ümit özel";
      flash(
        `${(snapshot.kolonlar || []).length} model · aktif T:${draftAktif.tilavet || "—"} · ${dep} commit dışı`,
      );
      if (window.ruzgarSesKolonlar?.refresh) void window.ruzgarSesKolonlar.refresh();
    } catch (e) {
      el.tbody.innerHTML =
        '<tr><td colspan="5" class="ses-kolon-empty">Klon listesi okunamadı — sunucuyu yeniden başlatın.</td></tr>';
      flash(String(e?.message || e));
    }
  }

  function plainText() {
    const raw = el.transcript?.value || "";
    if (typeof window.ttsPlainForSpeech === "function") return window.ttsPlainForSpeech(raw);
    return raw.replace(/\s+/g, " ").trim();
  }

  async function previewVoice() {
    const text = plainText();
    if (!text || text.length < 2) {
      flash("Önizleme için metin dökümüne en az bir cümle yazın.");
      return;
    }
    if (!previewPick.id) {
      flash("Listeden bir ses seçin (Dinle sütunu).");
      return;
    }
    flash("XTTS sentezleniyor — ilk seferde uzun sürebilir…");
    if (typeof window.setStatus === "function") window.setStatus("Klon önizleme…", "Rüzgar");
    const tune = currentTuningPayload();
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar/onizle`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          kolon_id: previewPick.id,
          scope: previewPick.scope,
          ...tune,
          tilavet_mod: tune.tilavet_mod,
        }),
      });
      if (!res.ok) {
        let detail = `HTTP ${res.status}`;
        try {
          const j = await res.json();
          detail = j.detail || detail;
        } catch {
          /* ignore */
        }
        throw new Error(detail);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      if (el.audio) {
        el.audio.src = url;
        try {
          await el.audio.play();
        } catch {
          /* kullanıcı play'e basar */
        }
      } else if (typeof window.playTtsBlob === "function") {
        await window.playTtsBlob(blob);
      }
      flash(`Dinleniyor: ${previewPick.id} (${previewPick.scope})`);
    } catch (e) {
      flash(String(e?.message || e));
    } finally {
      if (typeof window.setStatus === "function") window.setStatus("Ses", "Rüzgar");
    }
  }

  async function saveTuning() {
    if (!previewPick.id) {
      flash("Önce bir ses seçin.");
      return;
    }
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar/tuning`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kolon_id: previewPick.id,
          scope: previewPick.scope,
          tuning: currentTuningPayload(),
        }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      snapshot = j;
      renderList();
      flash("İnce ayar bu ses için kaydedildi.");
    } catch (e) {
      flash(String(e?.message || e));
    }
  }

  async function applyMotors() {
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar/uygula`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draftAktif),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      snapshot = j;
      syncDraftFromSnapshot();
      renderList();
      flash("Motor sesleri güncellendi.");
      if (typeof window.refreshSesCloneHint === "function") void window.refreshSesCloneHint();
      if (window.ruzgarSesKolonlar?.refresh) void window.ruzgarSesKolonlar.refresh();
    } catch (e) {
      flash(String(e?.message || e));
    }
  }

  async function uploadVoice() {
    const f = el.file?.files?.[0];
    if (!f) {
      flash("Eklenecek referans dosyası seçin (30–120 sn konuşma).");
      return;
    }
    const ad = String(el.ad?.value || f.name || "Yeni ses").trim();
    const fd = new FormData();
    fd.append("file", f, f.name);
    fd.append("ad", ad);
    fd.append("scope", tabScope);
    flash(tabScope === "ozel" ? "Özel ses kaydediliyor (commit dışı)…" : "Halka açık ses ekleniyor…");
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar`, { method: "POST", body: fd });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      snapshot = j;
      if (el.file) el.file.value = "";
      if (el.ad) el.ad.value = "";
      const entry = j.kolon || {};
      previewPick = { id: entry.id, scope: entry.scope || tabScope };
      await loadSnapshot();
      flash(`«${ad}» eklendi (${tabScope}).`);
    } catch (e) {
      flash(String(e?.message || e));
    }
  }

  el.tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      el.tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      tabScope = tab.getAttribute("data-scope") || "halka";
      const first = filteredRows()[0];
      if (first) {
        previewPick = { id: first.id, scope: first.scope || tabScope };
        loadTuningToSliders(first.tuning);
      }
      renderList();
    });
  });

  [el.hiz, el.huzur, el.durak].forEach((inp) => {
    if (inp) inp.addEventListener("input", syncSliderLabels);
  });

  if (el.btnDinle) el.btnDinle.addEventListener("click", () => void previewVoice());
  if (el.btnTuneKaydet) el.btnTuneKaydet.addEventListener("click", () => void saveTuning());
  if (el.btnMotorUygula) el.btnMotorUygula.addEventListener("click", () => void applyMotors());
  if (el.file) el.file.addEventListener("change", () => void uploadVoice());

  window.ruzgarKlonSesStudio = { refresh: loadSnapshot };

  syncSliderLabels();
  void loadSnapshot();
})();
