/**
 * Ses kütüphanesi — kolonlanmış referans sesler (sohbet / tilavet / okuma).
 * Ümit & Gökçenur · 2026-06-08
 */
(function () {
  "use strict";

  const MOTORS = ["sohbet", "tilavet", "okuma"];
  const MOTOR_LABEL = { sohbet: "Sohbet", tilavet: "Tilavet", okuma: "Okuma" };

  const el = {
    tbody: document.getElementById("ses-kolon-tbody"),
    hint: document.getElementById("ses-kolon-hint"),
    ad: document.getElementById("ses-kolon-ad"),
    file: document.getElementById("ses-kolon-file-input"),
    btnEkle: document.getElementById("btn-ses-kolon-ekle"),
    btnUygula: document.getElementById("btn-ses-kolon-uygula"),
    btnYenile: document.getElementById("btn-ses-kolon-yenile"),
  };

  if (!el.tbody) return;

  let snapshot = { kolonlar: [], aktif: {} };
  let draftAktif = { sohbet: null, tilavet: null, okuma: null };

  function apiRoot() {
    return window.ruzgarApi?.getApi?.() || window.RUZGAR_API || "http://127.0.0.1:8779";
  }

  function flash(msg) {
    if (typeof window.flashRuzgarDurum === "function") window.flashRuzgarDurum(msg);
    else if (el.hint) el.hint.textContent = msg;
  }

  function setHint(text) {
    if (el.hint) el.hint.textContent = text || "";
  }

  function escapeHtml(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function syncDraftFromSnapshot() {
    const a = snapshot.aktif || {};
    draftAktif = {
      sohbet: a.sohbet || null,
      tilavet: a.tilavet || null,
      okuma: a.okuma || null,
    };
  }

  function aktifSummary() {
    const parts = MOTORS.map((m) => {
      const id = draftAktif[m];
      if (!id) return `${MOTOR_LABEL[m]}: —`;
      const row = (snapshot.kolonlar || []).find((k) => k.id === id);
      return `${MOTOR_LABEL[m]}: ${row?.ad || id}`;
    });
    return parts.join(" · ");
  }

  function renderTable() {
    const rows = snapshot.kolonlar || [];
    if (!rows.length) {
      el.tbody.innerHTML =
        '<tr class="ses-kolon-empty"><td colspan="5">Henüz ses yok — referans yükleyin veya kuran/gazel/ilahi otomatik gelir.</td></tr>';
      setHint(aktifSummary());
      return;
    }

    el.tbody.innerHTML = rows
      .map((k) => {
        const metaCls = k.wav_ok ? "ses-kolon-meta" : "ses-kolon-meta warn";
        const meta = k.wav_ok
          ? `${k.size_kb || 0} KB · ${k.id}`
          : "Dosya eksik — yeniden yükleyin";
        const radios = MOTORS.map(
          (m) =>
            `<td class="ses-kolon-radio"><input type="radio" name="ses-kolon-${m}" value="${escapeHtml(k.id)}" data-motor="${m}" ${draftAktif[m] === k.id ? "checked" : ""} aria-label="${MOTOR_LABEL[m]}: ${escapeHtml(k.ad)}" /></td>`,
        ).join("");
        return `<tr data-kolon-id="${escapeHtml(k.id)}">
          <td><span class="ses-kolon-name">${escapeHtml(k.ad)}</span><span class="${metaCls}">${escapeHtml(meta)}</span></td>
          ${radios}
          <td><button type="button" class="btn-secondary btn-compact ses-kolon-sil" data-id="${escapeHtml(k.id)}" title="Sil">Sil</button></td>
        </tr>`;
      })
      .join("");

    el.tbody.querySelectorAll('input[type="radio"]').forEach((inp) => {
      inp.addEventListener("change", () => {
        const motor = inp.getAttribute("data-motor");
        if (motor && inp.checked) draftAktif[motor] = inp.value;
        setHint(`Taslak — ${aktifSummary()} (Uygula ile kaydet)`);
      });
    });

    el.tbody.querySelectorAll(".ses-kolon-sil").forEach((btn) => {
      btn.addEventListener("click", () => {
        void deleteKolon(btn.getAttribute("data-id"));
      });
    });

    setHint(aktifSummary());
  }

  async function loadKolonlar() {
    setHint("Kütüphane yükleniyor…");
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar`, { method: "GET" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      snapshot = await res.json();
      syncDraftFromSnapshot();
      renderTable();
    } catch (e) {
      el.tbody.innerHTML =
        '<tr class="ses-kolon-empty"><td colspan="5">Kütüphane okunamadı — sunucu çalışıyor mu?</td></tr>';
      setHint(String(e?.message || e));
    }
  }

  async function uploadKolon() {
    const f = el.file?.files?.[0];
    if (!f) {
      flash("Kütüphaneye eklemek için referans ses dosyası seçin.");
      return;
    }
    const ad = String(el.ad?.value || f.name || "Yeni ses").trim();
    const fd = new FormData();
    fd.append("file", f, f.name || "referans.wav");
    fd.append("ad", ad);
    flash("Ses kütüphanesine ekleniyor…");
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar`, { method: "POST", body: fd });
      let j = {};
      try {
        j = await res.json();
      } catch {
        /* ignore */
      }
      if (!res.ok) throw new Error(j.detail || j.error || `HTTP ${res.status}`);
      snapshot = j;
      syncDraftFromSnapshot();
      renderTable();
      if (el.file) el.file.value = "";
      if (el.ad) el.ad.value = "";
      flash(`«${ad}» kütüphaneye eklendi — motor seçip Uygula deyin.`);
    } catch (e) {
      flash(String(e?.message || e));
    }
  }

  async function applyMotors() {
    flash("Motor eşlemesi kaydediliyor…");
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar/uygula`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          sohbet: draftAktif.sohbet,
          tilavet: draftAktif.tilavet,
          okuma: draftAktif.okuma,
        }),
      });
      let j = {};
      try {
        j = await res.json();
      } catch {
        /* ignore */
      }
      if (!res.ok) throw new Error(j.detail || j.error || `HTTP ${res.status}`);
      snapshot = j;
      syncDraftFromSnapshot();
      renderTable();
      flash(`Ses motorları güncellendi — ${aktifSummary()}`);
      if (typeof window.refreshSesCloneHint === "function") void window.refreshSesCloneHint();
    } catch (e) {
      flash(String(e?.message || e));
    }
  }

  async function deleteKolon(id) {
    const kid = String(id || "").trim();
    if (!kid) return;
    if (!window.confirm(`«${kid}» sesini kütüphaneden silmek istiyor musunuz?`)) return;
    try {
      const res = await fetch(`${apiRoot()}/api/ses/kolonlar/${encodeURIComponent(kid)}`, {
        method: "DELETE",
      });
      let j = {};
      try {
        j = await res.json();
      } catch {
        /* ignore */
      }
      if (!res.ok) throw new Error(j.detail || `HTTP ${res.status}`);
      snapshot = j;
      syncDraftFromSnapshot();
      renderTable();
      flash(`«${kid}» silindi.`);
    } catch (e) {
      flash(String(e?.message || e));
    }
  }

  if (el.btnEkle) el.btnEkle.addEventListener("click", () => void uploadKolon());
  if (el.btnUygula) el.btnUygula.addEventListener("click", () => void applyMotors());
  if (el.btnYenile) el.btnYenile.addEventListener("click", () => void loadKolonlar());

  window.ruzgarSesKolonlar = {
    refresh: loadKolonlar,
    getAktif: () => ({ ...draftAktif }),
    getSnapshot: () => snapshot,
  };

  void loadKolonlar();
})();
