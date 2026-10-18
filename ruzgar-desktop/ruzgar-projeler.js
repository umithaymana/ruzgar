/* Programlama çalışma sayfası — ajan masası: emir, günlük, önizleme, elle düzeltme. */
(function () {
  const listeEl = document.getElementById("ruzgar-projeler-liste");
  const dosyaEl = document.getElementById("ruzgar-projeler-dosyalar");
  const durumEl = document.getElementById("ruzgar-projeler-durum");
  const onizleme = document.getElementById("ruzgar-proje-onizleme");
  const denemeKutu = document.getElementById("ruzgar-projeler-deneme");
  const araKutu = document.getElementById("ruzgar-projeler-ara");
  const gunlukEl = document.getElementById("ruzgar-ajan-gunluk");
  const emirKutu = document.getElementById("ruzgar-ajan-emir");
  if (!listeEl || !dosyaEl || !onizleme) return;

  let secili = "";
  let acikDosya = "";
  let sonListe = [];

  function apiKok() {
    const kok = typeof API === "string" ? API : "";
    return String(kok || "http://127.0.0.1:8779").replace(/\/$/, "");
  }

  function harf(text) {
    return String(text || "")
      .replace(/İ/g, "i")
      .replace(/I/g, "i")
      .toLowerCase()
      .replace(/ı/g, "i")
      .replace(/ğ/g, "g")
      .replace(/ü/g, "u")
      .replace(/ş/g, "s")
      .replace(/ö/g, "o")
      .replace(/ç/g, "c")
      .replace(/\s+/g, " ")
      .trim();
  }

  function durum(text) {
    if (durumEl) durumEl.textContent = text || "";
  }

  function gunlukYaz(satirlar) {
    if (!gunlukEl) return;
    gunlukEl.innerHTML = "";
    (satirlar || []).forEach(function (satir) {
      const li = document.createElement("li");
      li.textContent = String(satir || "");
      gunlukEl.appendChild(li);
    });
  }

  function programlamaAcik() {
    const sayfa = document.getElementById("page-programlama");
    return !!(sayfa && !sayfa.hidden);
  }

  let istenenGorunum = "";
  let sozlukSoz = null;
  const masaSozluk = {};
  const masaCevap = {};

  function sozluguYukle() {
    if (sozlukSoz) return sozlukSoz;
    sozlukSoz = fetch("modules/programlama/manifest.json", { cache: "no-cache" })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        const yan = (data && data.sidebar) || {};
        ["default", "duzen", "gelisim"].forEach(function (anahtar) {
          (yan[anahtar] || []).forEach(function (grup) {
            (grup.items || []).forEach(function (item) {
              const komut = String(item.action || "").replace(/^prog:/, "");
              if (!komut) return;
              if (item.reply) masaCevap[komut] = item.reply;
              (item.phrases || []).forEach(function (phrase) {
                masaSozluk[harf(phrase)] = komut;
              });
            });
          });
        });
      })
      .catch(function () { sozlukSoz = null; });
    return sozlukSoz;
  }

  function calismaKutu() {
    return document.getElementById("ruzgar-calisma");
  }

  function seciliSatir() {
    return sonListe.find(function (row) { return row.rel === secili; }) || null;
  }

  function oranSec() {
    const row = seciliSatir();
    if (row && row.site) return 0.56;
    if (row && row.python) return 0.34;
    return 0.5;
  }

  function oranYaz(oran) {
    const kutu = calismaKutu();
    if (!kutu || kutu.dataset.gorunum !== "iki") return;
    const genislik = kutu.getBoundingClientRect().width || kutu.clientWidth || 1;
    const tutamak = 8;
    const alt = 160;
    const ust = Math.max(alt, genislik - tutamak - alt);
    const ham = Number(oran);
    const hedef = Math.min(ust, Math.max(alt, (Number.isFinite(ham) ? ham : 0.5) * genislik));
    kutu.style.gridTemplateColumns = "minmax(0, " + Math.round(hedef) + "px) " + tutamak + "px minmax(0, 1fr)";
    try { localStorage.setItem("ruzgar-prog-oran", String(hedef / genislik)); } catch (err) { /* saklanamazsa sayfa yine bölünür */ }
  }

  function gorunumKur(mod) {
    const kutu = calismaKutu();
    if (!kutu) return "proje";
    const hedef = mod === "kod" || mod === "proje" || mod === "iki" ? mod : "proje";
    kutu.dataset.gorunum = hedef;
    if (hedef === "iki") {
      let sakli = oranSec();
      try {
        const kayit = Number(localStorage.getItem("ruzgar-prog-oran"));
        if (kayit >= 0.22 && kayit <= 0.78) sakli = kayit;
      } catch (err) { /* kayıt yoksa proje durumuna göre */ }
      oranYaz(sakli);
    } else {
      kutu.style.gridTemplateColumns = "";
    }
    return hedef;
  }

  function tutamagiBagla() {
    const tutamak = document.getElementById("ruzgar-calisma-tutamak");
    const kutu = calismaKutu();
    if (!tutamak || !kutu || tutamak.dataset.bagli === "1") return;
    tutamak.dataset.bagli = "1";
    tutamak.addEventListener("pointerdown", function (event) {
      if (kutu.dataset.gorunum !== "iki" || event.button !== 0) return;
      event.preventDefault();
      try { tutamak.setPointerCapture(event.pointerId); } catch (err) { /* tutamak yine de sürüklenir */ }
      kutu.classList.add("is-dragging");
      function move(ev) {
        const rect = kutu.getBoundingClientRect();
        const x = ev.clientX - rect.left;
        oranYaz(x / Math.max(rect.width, 1));
      }
      function up(ev) {
        if (tutamak.hasPointerCapture(ev.pointerId)) tutamak.releasePointerCapture(ev.pointerId);
        kutu.classList.remove("is-dragging");
        tutamak.removeEventListener("pointermove", move);
        tutamak.removeEventListener("pointerup", up);
        tutamak.removeEventListener("pointercancel", up);
      }
      tutamak.addEventListener("pointermove", move);
      tutamak.addEventListener("pointerup", up);
      tutamak.addEventListener("pointercancel", up);
    });
  }

  function komutGovdesi(text) {
    let low = harf(text);
    if (!low || low.length > 600) return "";
    const kolon = low.indexOf(":");
    let bas = kolon >= 0 ? low.slice(0, kolon) : low;
    const son = kolon >= 0 ? low.slice(kolon) : "";
    bas = bas.replace(/[?!]+/g, " ").replace(/\s+/g, " ").trim();
    bas = bas.replace(/^(lutfen|bana|rica etsem)\s+/, "");
    bas = bas.replace(/\s+(lutfen|olur mu|yapar misin|yapar misiniz|misin|misiniz|musun|musunuz)$/, "");
    bas = bas.replace(/\b(gosterir|gosteririm)\b/g, "goster");
    bas = bas.replace(/\b(acar|acarim)\b/g, "ac");
    bas = bas.replace(/\b(yazar|yazarim)\b/g, "yaz");
    bas = bas.replace(/\byapar\b/g, "yap");
    bas = bas.replace(/\b(ekler|eklerim)\b/g, "ekle");
    bas = bas.replace(/\b(siler|silerim)\b/g, "sil");
    return (bas.replace(/\s+/g, " ").trim() + son).trim();
  }

  function soruMu(low) {
    return /\b(nedir|nasil|anlat|neden)\b/.test(low);
  }

  function sozlukBul(low) {
    if (masaSozluk[low]) return masaSozluk[low];
    const anahtarlar = Object.keys(masaSozluk).sort(function (a, b) { return b.length - a.length; });
    for (let i = 0; i < anahtarlar.length; i++) {
      const phrase = anahtarlar[i];
      const kacis = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      if (new RegExp("(^|\\s)" + kacis + "(\\s|$)").test(low)) return masaSozluk[phrase];
    }
    return "";
  }

  function ajanEmriMi(low) {
    return /^(basligi|baslik)\b/.test(low)
      || /^(paragraf|buton)\b/.test(low)
      || /\byerine\b.+\byaz$/.test(low)
      || /^(basit site yap|statik site yap|web sitesi yap|bir site yap|site yap|kucuk python araci yap|python araci yap|python cli yap|komut satiri araci yap|kucuk uygulama yap)\b/.test(low);
  }

  function emirGibi(low) {
    return /\b(goster|ac|yaz|ekle|sil|kaydet|yap|degistir|ciz|cizgi|kutu|daire|slayt|baslik|paragraf|buton|temizle)\b/.test(low);
  }

  function yakinSoz(low) {
    const raf = [
      ["teke", "aynı bağlantıları teke indir"],
      ["rengini", "başlık rengini mavi yap"],
      ["resim", "resim koy: foto.png"],
      ["baglanti", "bağlantı ekle: Rüzgar | https://ornek.com"],
      ["klasordekileri", "klasördekileri say"],
      ["bak", "deneme sayfasına bak ve söyle"],
      ["belgeye", "belgeye bak ve söyle"],
      ["yerine", "deneme sayfasında selam yerine merhaba yaz"],
      ["sayfasina", "deneme sayfasına başlığı selam yap, hoş geldin yaz, tıkla butonu koy, sayfayı göster"],
      ["dosyasina", "merhaba dosyasına selam yaz"],
      ["dosyasini", "merhaba dosyasını oku"],
      ["sayfasi", "deneme sayfası yap"],
      ["sayfayi", "sayfayı göster"],
      ["kod", "kodları göster"],
      ["proje", "projeyi göster"],
      ["baslik", "başlığı … yap"],
      ["paragraf", "paragraf ekle: …"],
      ["buton", "buton ekle: …"],
      ["belge", "belgeye yaz: …"],
      ["tablo", "tablo A1 = 10"],
      ["ciz", "çizgi 40 40 400 200"],
      ["slayt", "slayt ekle: Başlık | metin"],
      ["site", "site yap"],
      ["kaydet", "kaydet"],
      ["dosya", "dosyaları göster"],
    ];
    for (let i = 0; i < raf.length; i++) {
      if (low.indexOf(raf[i][0]) >= 0) return raf[i][1];
    }
    return "masa komutları";
  }

  function yol(rel) {
    return String(rel || "").replace(/\\/g, "/").replace(/^\/+/, "");
  }

  function projeAdi(rel) {
    const parts = yol(rel).split("/");
    return parts[0] === "projects" ? parts[1] || "" : "";
  }

  async function apiJson(url, options) {
    const res = await fetch(url, options);
    const data = await res.json().catch(function () { return {}; });
    if (!res.ok || data.ok === false) {
      const detail = data.detail;
      throw new Error(typeof detail === "string" ? detail : data.error || "İstek olmadı.");
    }
    return data;
  }

  async function klasorKaydet(yolMetin) {
    return apiJson(apiKok() + "/api/programlama/calisma-klasoru", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ yol: yolMetin || "" }),
    });
  }

  async function klasorListe() {
    return apiJson(apiKok() + "/api/programlama/calisma-klasoru");
  }

  async function klasorSayfadaGoster() {
    const data = await klasorListe();
    if (!data.klasor) {
      durum("Çalışma klasörü seçilmedi.");
      return { handled: true, reply: "Çalışma klasörü seçilmedi. Şöyle söyle: çalışma klasörü: tam yol" };
    }
    if (window.switchMode) window.switchMode("programlama");
    secili = "klasor";
    dosyaEl.innerHTML = "";
    (data.dosyalar || []).forEach(function (item) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = yol(item.rel).replace(/^klasor\//, "");
      btn.dataset.rel = item.rel;
      btn.addEventListener("click", function () { void dosyaAc(item.rel); });
      li.appendChild(btn);
      dosyaEl.appendChild(li);
    });
    if (!(data.dosyalar || []).length) dosyaEl.innerHTML = "<li>Dosya yok.</li>";
    const html = (data.dosyalar || []).find(function (item) { return /index\.html?$/i.test(item.rel); });
    if (html) {
      onizleme.src = apiKok() + "/api/programlama/calisma-onizleme/" + encodeURI(yol(html.rel).replace(/^klasor\//, "")) + "?t=" + Date.now();
    }
    durum(data.klasor);
    gorunumKur("proje");
    const adlar = (data.dosyalar || []).slice(0, 12).map(function (item) { return yol(item.rel).replace(/^klasor\//, ""); });
    return {
      handled: true,
      reply: "Klasör açık: " + data.klasor + (adlar.length ? "\n" + adlar.join(", ") : "\nDosya yok."),
    };
  }

  async function klasorDosyaOku(ad) {
    const data = await apiJson(apiKok() + "/api/programlama/calisma-oku?rel=" + encodeURIComponent(ad));
    if (window.switchMode) window.switchMode("programlama");
    acikDosya = data.rel;
    if (typeof atolyeOpenRel !== "undefined") atolyeOpenRel = data.rel;
    const editor = document.getElementById("code-editor");
    if (editor) editor.value = data.text || "";
    if (/\.html?$/i.test(data.rel)) {
      onizleme.src = apiKok() + "/api/programlama/calisma-onizleme/" + encodeURI(yol(data.rel).replace(/^klasor\//, "")) + "?t=" + Date.now();
    }
    durum(data.rel);
    const metin = String(data.text || "");
    const kesik = metin.length > 500 ? metin.slice(0, 500) + "…" : metin;
    return { handled: true, reply: data.rel + " okundu.\n" + (kesik || "(boş)") };
  }

  async function klasorDosyaYaz(ad, metin) {
    const data = await apiJson(apiKok() + "/api/programlama/calisma-yaz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rel: ad, text: metin }),
    });
    durum("Yazıldı: " + data.rel);
    return { handled: true, reply: "Yazıldı: " + data.rel };
  }

  function klasorGorunum(data) {
    if (window.switchMode) window.switchMode("programlama");
    if ((data.rel && String(data.rel).indexOf("klasor/") === 0) || data.klasor) secili = "klasor";
    if (data.gorunum) gorunumKur(data.gorunum);
    const editor = document.getElementById("code-editor");
    const etiket = document.getElementById("code-active-file");
    if (data.rel) {
      acikDosya = data.rel;
      if (typeof atolyeOpenRel !== "undefined") atolyeOpenRel = data.rel;
      if (etiket) etiket.textContent = "Dosya: " + data.rel;
      durum(data.rel);
    } else if (data.klasor) {
      durum(data.klasor);
    }
    if (editor && typeof data.text === "string") editor.value = data.text;
    if (data.onizleme && data.rel && /\.html?$/i.test(data.rel)) {
      onizleme.src = apiKok() + "/api/programlama/calisma-onizleme/" + encodeURI(yol(data.rel).replace(/^klasor\//, "")) + "?t=" + Date.now();
    } else if (data.gorunum === "kod") {
      onizleme.removeAttribute("src");
    }
  }

  async function klasorSozu(raw) {
    try {
      const data = await apiJson(apiKok() + "/api/programlama/calisma-soz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ yazi: raw }),
      });
      if (!data.handled) return null;
      if (data.gorunum || data.rel) klasorGorunum(data);
      if (window.ruzgarMasaBekleyenSil && /\bbak\s+ve\s+s[öo]yle\b/i.test(String(raw))) window.ruzgarMasaBekleyenSil();
      return { handled: true, reply: data.reply || "Tamam." };
    } catch (err) {
      return { handled: true, reply: "Yazılmadı. " + (err.message || "Kapı kapalı.") };
    }
  }

  async function listele(rel) {
    if (window.ruzgarApi && window.ruzgarApi.listDir) {
      return window.ruzgarApi.listDir(rel);
    }
    const data = await apiJson(apiKok() + "/api/workspace/list?rel=" + encodeURIComponent(rel));
    return data.items || [];
  }

  function onizlemeAdresi(rel) {
    const clean = yol(rel);
    const encoded = clean.split("/").map(encodeURIComponent).join("/");
    return apiKok() + "/api/programlama/onizleme/" + encoded + "?t=" + Date.now();
  }

  function goster(rel) {
    const clean = yol(rel);
    if (!/\.(html|htm)$/i.test(clean)) {
      onizleme.removeAttribute("src");
      return;
    }
    onizleme.src = onizlemeAdresi(clean);
  }

  async function dosyalariYaz(projeRel) {
    dosyaEl.innerHTML = "";
    const bekleyen = [projeRel];
    const bulunan = [];
    const atla = { __pycache__: 1, node_modules: 1, ".pytest_cache": 1, ".git": 1 };
    while (bekleyen.length && bulunan.length < 80) {
      const klasor = bekleyen.shift();
      let items = [];
      try {
        items = await listele(klasor);
      } catch (err) {
        durum(err.message || "Liste okunamadı.");
        return;
      }
      items.forEach(function (item) {
        if (atla[item.name]) return;
        if (item.isDir) bekleyen.push(item.rel);
        else bulunan.push(item);
      });
    }
    if (!bulunan.length) {
      dosyaEl.innerHTML = "<li>Dosya yok.</li>";
      return;
    }
    bulunan.forEach(function (item) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = yol(item.rel).slice(projeRel.length + 1);
      btn.dataset.rel = item.rel;
      if (yol(item.rel) === acikDosya) btn.classList.add("is-on");
      btn.addEventListener("click", function () {
        void dosyaAc(item.rel);
      });
      li.appendChild(btn);
      dosyaEl.appendChild(li);
    });
  }

  async function dosyaAc(rel) {
    const clean = yol(rel);
    acikDosya = clean;
    if (typeof openProgramlamaWorkspaceFile === "function") {
      await openProgramlamaWorkspaceFile(clean);
    }
    goster(clean);
    dosyaEl.querySelectorAll("button").forEach(function (btn) {
      btn.classList.toggle("is-on", yol(btn.dataset.rel) === clean);
    });
    durum(clean);
  }

  function listeCiz() {
    listeEl.innerHTML = "";
    const deneme = !!(denemeKutu && denemeKutu.checked);
    const aranan = harf(araKutu ? araKutu.value : "");
    const satirlar = sonListe.filter(function (row) {
      if (!deneme && row.deneme) return false;
      if (aranan && harf(row.name).indexOf(aranan) < 0) return false;
      return true;
    });
    if (!satirlar.length) {
      listeEl.innerHTML = "<li>Gösterilecek proje yok.</li>";
      return;
    }
    satirlar.forEach(function (row) {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      const tur = row.site ? "site" : row.python ? "python" : "dosya";
      btn.textContent = row.name + " · " + tur;
      btn.dataset.rel = row.rel;
      if (row.rel === secili) btn.classList.add("is-on");
      btn.addEventListener("click", function () {
        void projeAc(row.rel);
      });
      li.appendChild(btn);
      listeEl.appendChild(li);
    });
  }

  async function projeleriYukle() {
    try {
      const data = await apiJson(apiKok() + "/api/programlama/projeler");
      sonListe = data.projeler || [];
      listeCiz();
      if (!durumEl.textContent) durum(sonListe.length + " proje");
    } catch (err) {
      durum(err.message || "Projeler okunamadı.");
    }
  }

  async function projeAc(rel) {
    const clean = yol(rel);
    const ad = projeAdi(clean) || clean.replace(/^projects\//, "").split("/")[0];
    secili = ad ? "projects/" + ad : clean;
    if (window.switchMode) window.switchMode("programlama");
    if (!sonListe.length) await projeleriYukle();
    listeCiz();
    await dosyalariYaz(secili);
    const site = sonListe.some(function (row) { return row.rel === secili && row.site; });
    const dosya = /^projects\/.+\.[a-z0-9]+$/i.test(clean);
    const hedef = dosya ? clean : (site ? secili + "/index.html" : "");
    if (hedef) await dosyaAc(hedef);
    else durum(secili);
    const gor = istenenGorunum || (seciliSatir() && seciliSatir().site ? "iki" : (seciliSatir() && seciliSatir().python ? "kod" : "proje"));
    istenenGorunum = "";
    gorunumKur(gor);
    return secili;
  }

  async function dosyaEkle() {
    if (!secili) {
      durum("Önce bir proje seç.");
      return;
    }
    if (secili === "klasor") {
      const adDis = window.prompt("Dosya adı (örnek not.txt)", "not.txt");
      if (adDis == null) return;
      klasorDosyaYaz(adDis, "").then(function () { return klasorSayfadaGoster(); }).catch(function (err) {
        durum(err.message || "Eklenemedi.");
      });
      return;
    }
    const ad = window.prompt("Dosya adı (örnek css/ek.css veya not.txt)", "not.txt");
    if (ad == null) return;
    const ek = yol(ad).replace(/^projects\//, "");
    if (!ek || ek.indexOf("..") >= 0) {
      durum("Dosya adı geçersiz.");
      return;
    }
    const rel = secili + "/" + ek;
    try {
      await apiJson(apiKok() + "/api/programlama/proje-yaz", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: rel, text: "" }),
      });
      await dosyalariYaz(secili);
      await dosyaAc(rel);
      durum("Eklendi: " + rel);
    } catch (err) {
      durum(err.message || "Eklenemedi.");
    }
  }

  async function dosyaSil() {
    const rel = yol(typeof atolyeOpenRel === "string" ? atolyeOpenRel : acikDosya);
    if (!rel || (rel.indexOf("projects/") !== 0 && rel.indexOf("klasor/") !== 0)) {
      durum("Silinecek dosya seçili değil.");
      return;
    }
    if (rel.indexOf("klasor/") === 0) {
      durum("Gösterilen klasördeki dosya buradan silinmez.");
      return;
    }
    if (!window.confirm(rel + " silinsin mi?")) return;
    try {
      await apiJson(apiKok() + "/api/programlama/proje-sil", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: rel }),
      });
      acikDosya = "";
      if (typeof atolyeOpenRel !== "undefined") atolyeOpenRel = null;
      const editor = document.getElementById("code-editor");
      if (editor) editor.value = "";
      const siteKaldi = !/\.(html|htm)$/i.test(rel);
      if (siteKaldi && secili) goster(secili + "/index.html");
      else onizleme.removeAttribute("src");
      await dosyalariYaz(secili);
      durum("Silindi: " + rel);
    } catch (err) {
      durum(err.message || "Silinemedi.");
    }
  }

  async function projeSil() {
    if (!secili) {
      durum("Önce bir proje seç.");
      return;
    }
    if (secili === "klasor") {
      durum("Bu klasör silinmez. Bırakmak için: klasörü bırak");
      return;
    }
    if (!window.confirm(secili + " klasörü silinsin mi?")) return;
    try {
      await apiJson(apiKok() + "/api/programlama/proje-sil", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: secili }),
      });
      secili = "";
      acikDosya = "";
      dosyaEl.innerHTML = "";
      onizleme.removeAttribute("src");
      await projeleriYukle();
      durum("Proje silindi.");
    } catch (err) {
      durum(err.message || "Proje silinemedi.");
    }
  }

  async function ajanYap(emir) {
    const raw = String(emir || "").trim();
    if (!raw) {
      durum("Emir boş.");
      return { reply: "Emir boş." };
    }
    const hedef = secili || "projects/vitrin";
    gunlukYaz(["Emir alındı.", "Proje: " + hedef]);
    try {
      const data = await apiJson(apiKok() + "/api/programlama/proje-ajan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rel: hedef, emir: raw, dosya: acikDosya }),
      });
      gunlukYaz(["Emir alındı."].concat(data.adimlar || []));
      const ac = data.rel || data.proje || hedef;
      await projeAc(ac);
      durum(data.ozet || "Emir uygulandı.");
      const satirlar = data.adimlar || [];
      return { reply: (data.ozet || "Emir uygulandı.") + (satirlar.length ? "\n" + satirlar.join("\n") : "") };
    } catch (err) {
      const mesaj = err.message || "Emir uygulanamadı.";
      gunlukYaz(["Emir alındı.", mesaj]);
      durum(mesaj);
      return { reply: mesaj };
    }
  }

  function kacis(text) {
    return String(text || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/"/g, "&quot;");
  }

  function cekmeceAc(baslik, html) {
    const host = document.getElementById("ruzgar-slide-host");
    const title = document.getElementById("ruzgar-slide-title");
    const body = document.getElementById("ruzgar-slide-body");
    if (!host || !body) return null;
    if (title) title.textContent = baslik;
    body.innerHTML = '<div class="ruzgar-drawer-panel-list">' + html + "</div>";
    host.hidden = false;
    requestAnimationFrame(function () { host.classList.add("is-open"); });
    return body;
  }

  function cekmeceKapat() {
    if (window.RuzgarSidebarManager && window.RuzgarSidebarManager.closeSlidePanel) {
      window.RuzgarSidebarManager.closeSlidePanel();
    }
  }

  function gorunenProjeler() {
    const deneme = !!(denemeKutu && denemeKutu.checked);
    const aranan = harf(araKutu ? araKutu.value : "");
    return sonListe.filter(function (row) {
      if (!deneme && row.deneme) return false;
      if (aranan && harf(row.name).indexOf(aranan) < 0) return false;
      return true;
    });
  }

  async function menudenProjeler() {
    if (!sonListe.length) await projeleriYukle();
    const deneme = !!(denemeKutu && denemeKutu.checked);
    const body = cekmeceAc(
      "Düzen · Projeler",
      '<label class="ruzgar-drawer-control-label">Proje ara</label>'
      + '<input id="ruzgar-menu-ara" class="ruzgar-ajan-emir" type="search" value="' + kacis(araKutu ? araKutu.value : "") + '" />'
      + '<label class="ruzgar-drawer-control-label"><input id="ruzgar-menu-deneme" type="checkbox"' + (deneme ? " checked" : "") + " /> Denemeleri göster</label>"
      + '<div id="ruzgar-menu-projeler"></div>'
    );
    if (!body) return;
    const liste = body.querySelector("#ruzgar-menu-projeler");
    const ara = body.querySelector("#ruzgar-menu-ara");
    const kutu = body.querySelector("#ruzgar-menu-deneme");
    function ciz() {
      if (ara && araKutu) araKutu.value = ara.value;
      if (kutu && denemeKutu) denemeKutu.checked = kutu.checked;
      listeCiz();
      const satirlar = gorunenProjeler().map(function (row) {
        const tur = row.site ? "site" : row.python ? "python" : "dosya";
        return '<button type="button" class="ruzgar-drawer-btn" data-rel="' + kacis(row.rel) + '"><span class="ruzgar-drawer-btn-text">' + kacis(row.name + " · " + tur) + "</span></button>";
      }).join("");
      liste.innerHTML = satirlar || "<p>Gösterilecek proje yok.</p>";
      liste.querySelectorAll("[data-rel]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          istenenGorunum = (calismaKutu() && calismaKutu().dataset.gorunum) || "proje";
          void projeAc(btn.getAttribute("data-rel"));
          cekmeceKapat();
        });
      });
    }
    if (ara) ara.addEventListener("input", ciz);
    if (kutu) kutu.addEventListener("change", ciz);
    ciz();
  }

  async function menudenDosyalar() {
    if (!secili) {
      cekmeceAc("Dosya · Dosyalar", "<p>Önce Düzen menüsünden bir proje seç.</p>");
      return;
    }
    await dosyalariYaz(secili);
    const dugmeler = Array.from(dosyaEl.querySelectorAll("button")).map(function (btn) {
      return '<button type="button" class="ruzgar-drawer-btn" data-rel="' + kacis(btn.dataset.rel) + '"><span class="ruzgar-drawer-btn-text">' + kacis(btn.textContent) + "</span></button>";
    }).join("");
    const body = cekmeceAc("Dosya · Dosyalar", dugmeler || "<p>Dosya yok.</p>");
    if (!body) return;
    body.querySelectorAll("[data-rel]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        void dosyaAc(btn.getAttribute("data-rel"));
        cekmeceKapat();
      });
    });
  }

  function menudenGunluk() {
    const satirlar = gunlukEl
      ? Array.from(gunlukEl.querySelectorAll("li")).map(function (li) { return "<li>" + kacis(li.textContent) + "</li>"; }).join("")
      : "";
    cekmeceAc("Gelişim · Günlük", satirlar ? "<ol class=\"ruzgar-ajan-gunluk\">" + satirlar + "</ol>" : "<p>Günlük boş.</p>");
  }

  function menudenEmir() {
    const body = cekmeceAc(
      "Gelişim · Emir",
      '<form id="ruzgar-menu-emir" class="ruzgar-ajan-form">'
      + '<input class="ruzgar-ajan-emir" name="emir" type="text" placeholder="Başlığı değiştir, paragraf ekle, basit site yap: ad" />'
      + '<button type="submit" class="btn-primary btn-compact">Yap</button></form>'
    );
    const form = body && body.querySelector("#ruzgar-menu-emir");
    if (!form) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      const yazi = form.emir ? form.emir.value : "";
      cekmeceKapat();
      void ajanYap(yazi);
    });
  }

  window.ruzgarCalismaGorunum = gorunumKur;
  window.ruzgarProgramlamaMenu = function (ad) {
    const komut = String(ad || "");
    if (window.switchMode) window.switchMode("programlama");
    if (komut === "kod" || komut === "proje") {
      istenenGorunum = komut;
      if (secili) void projeAc(secili);
      else if (komut === "proje") void projeAc("projects/vitrin");
      else gorunumKur("kod");
      durum(komut === "kod" ? "Kod" : "Proje");
      return;
    }
    if (komut === "iki") {
      istenenGorunum = "iki";
      void projeAc(secili || "projects/vitrin");
      return;
    }
    if (komut === "ekle") void dosyaEkle();
    else if (komut === "kaydet") {
      if (typeof saveProgramlamaAtolyeBuffer === "function") void saveProgramlamaAtolyeBuffer();
    }
    else if (komut === "sil") void dosyaSil();
    else if (komut === "proje-sil") void projeSil();
    else if (komut === "yenile") void projeleriYukle();
    else if (komut === "projeler") void menudenProjeler();
    else if (komut === "dosyalar") void menudenDosyalar();
    else if (komut === "gunluk") menudenGunluk();
    else if (komut === "emir") menudenEmir();
    else if (komut === "calistir") document.getElementById("btn-code-run")?.click();
    else if (komut === "acikla") document.getElementById("btn-code-explain")?.click();
    else if (komut === "hata") document.getElementById("btn-code-fix")?.click();
    else if (komut === "test") document.getElementById("btn-code-test")?.click();
    else if (komut === "site") document.getElementById("btn-scaffold-site")?.click();
    else if (komut === "onayla") document.getElementById("btn-umit-onay-apply")?.click();
    else if (komut === "yapma") document.getElementById("btn-umit-onay-cancel")?.click();
  };
  window.ruzgarProjeAc = projeAc;
  window.ruzgarProjeOdak = function (rel) {
    return projeAc(rel || "projects/vitrin");
  };
  window.ruzgarProjeKayitSonrasi = function (rel) {
    const clean = yol(rel);
    if (/\.(html|htm|css|js)$/i.test(clean)) goster(projeAdi(clean) ? "projects/" + projeAdi(clean) + "/index.html" : clean);
    if (secili) void dosyalariYaz(secili);
  };
  window.ruzgarKomutGovdesi = komutGovdesi;

  window.ruzgarProjeKomut = function (text) {
    const raw = String(text || "").trim();
    if (!raw || raw.length > 600) return null;
    return sozluguYukle().then(function () {
      return projeKomutCoz(raw);
    });
  };

  window.ruzgarEmirYalan = function (text) {
    const raw = String(text || "").trim();
    if (!raw || raw.length > 600) return null;
    return sozluguYukle().then(function () {
      const low = komutGovdesi(raw);
      if (!low || soruMu(low) || !emirGibi(low)) return null;
      if (sozlukBul(low)) return null;
      if (/^(?:projeyi|proje|siteyi|vitrini)\s+(?:goster|ac)\b/.test(low)) return null;
      if (programlamaAcik() && ajanEmriMi(low)) return null;
      if (ajanEmriMi(low)) {
        return { handled: true, reply: "Bunu yapmadım. Dosya değişmedi. Programlama sayfasında söyle: " + yakinSoz(low) + "." };
      }
      return { handled: true, reply: "Bunu yapmadım. Dosya değişmedi. Şöyle söyle: " + yakinSoz(low) + "." };
    });
  };

  function klasorSozuMu(raw) {
    const yazi = String(raw || "").trim();
    if (!yazi || yazi.length > 600) return false;
    if (/^(?:çalışma klasörü|calisma klasoru)\s*:/i.test(yazi)) return true;
    if (/^(?:klasörü bırak|klasoru birak|klasörü göster|klasoru goster|çalışma klasörü|calisma klasoru)$/i.test(yazi)) return true;
    if (/^(?:dosyayı oku|dosyayi oku)\s*:/i.test(yazi)) return true;
    if (/^(?:dosyaya yaz|dosyaya ekle)\s*:/i.test(yazi)) return true;
    const low = harf(yazi);
    if (/^belgede\b/.test(low)) return false;
    if (/^(?:klasordekileri)\s+say$/.test(low)) return true;
    if (/^(?:not defteri|not defter)\s+yap$/.test(low)) return true;
    if (/\sdosyasi\s+yap$/.test(low)) return true;
    if (/^ara\s+baslik\b/.test(low)) return true;
    if (/^baglanti\b/.test(low)) return true;
    if (/^baslik\s+rengini\b/.test(low)) return true;
    if (/\ssayfasinin\s+baslik\s+rengini\b/.test(low)) return true;
    if (/\bayni\s+(?:baglantilari|ara\s+basliklari|resimleri)\s+teke\s+indir$/.test(low)) return true;
    if (/^resim\s+koy\b/.test(low)) return true;
    if (/\ssayfasinin\s+adini\b/.test(low)) return true;
    if (/\sdosyasina\s+\S/.test(low) && /\syaz$/.test(low)) return true;
    if (/\sdosyasini\s+oku$/.test(low)) return true;
    if (/(^|\s)(sayfa yap|sayfa ac|sayfayi goster)\b/.test(low)) return true;
    if (/\ssayfasi\s+yap\b/.test(low) || /\ssayfasini\s+goster\b/.test(low)) return true;
    if (/\ssayfasina\b/.test(low) || /\ssayfasinda\b/.test(low)) return true;
    if (/\b(sayfasina|dosyasina)\s+bak\s+ve\s+soyle\b/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+ne\s+yapiyor$/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+ne\s+donduruyor$/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+kimi\s+cagiriyor$/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+nerede$/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+neye\s+yaziyor$/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+neye\s+bakiyor$/.test(low)) return true;
    if (/\.py\s+icinde\s+[a-z_][a-z0-9_]*\s+sinifi\s+ne\s+yapiyor$/.test(low)) return true;
    if (/\.py\s+neyi\s+ice\s+aliyor$/.test(low)) return true;
    if (/^orta\s+is\s+yap$/.test(low)) return true;
    if (/\.py\s+ne\s+yapiyor$/.test(low)) return true;
    if (/\.py\s+dosyasinin\s+ne\s+yaptigini\s+soyle$/.test(low)) return true;
    if (/\.py(?:\s+dosyasini)?\s+calistir$/.test(low)) return true;
    if (/^uygula$/.test(low)) return true;
    if (/\byerine\b/.test(low) && /\byaz$/.test(low)) return true;
    if (/\bicinde\b/.test(low) && /\byerine\b/.test(low)) return true;
    if (/\sbutonu\s+(koy|ekle)\b/.test(low) || /^buton koy\b/.test(low)) return true;
    if (/^basligina\b/.test(low) || /\bbasligi\b.+\bolsun$/.test(low)) return true;
    if (/\bsayfayi\b/.test(low) && /\b(bastan|tasarla|yeniden)\b/.test(low)) return true;
    if (/^(basligi|baslik|paragraf|buton)\b/.test(low)) return true;
    if ((low.indexOf(",") >= 0 || /\ssonra\s/.test(low))
      && /dosyasina|dosyasini|sayfa|baslig|paragraf|buton|calisma klasoru|klasoru/.test(low)) return true;
    return false;
  }

  function masaBakAd(low) {
    if (/^belgeye\s+bak\s+ve\s+soyle$/.test(low)) return "belge";
    if (/^tabloya\s+bak\s+ve\s+soyle$/.test(low)) return "tablo";
    if (/^cizime\s+bak\s+ve\s+soyle$/.test(low)) return "cizim";
    if (/^sunuma\s+bak\s+ve\s+soyle$/.test(low)) return "sunum";
    return "";
  }

  function projeKomutCoz(raw) {
    const bakLow = harf(raw);
    const masaAd = masaBakAd(bakLow);
    if (masaAd) {
      if (window.ruzgarMasaBak) return window.ruzgarMasaBak(masaAd);
      return { handled: true, reply: "Masa kapalı." };
    }
    if (/^uygula$/.test(bakLow) && window.ruzgarMasaBekleyenUygula) {
      const bekleyen = window.ruzgarMasaBekleyenUygula();
      if (bekleyen) return bekleyen;
    }
    if (klasorSozuMu(raw)) {
      return klasorSozu(raw).then(function (sonuc) {
        if (sonuc) return sonuc;
        return projeKomutDevam(raw);
      });
    }
    return projeKomutDevam(raw);
  }

  function projeKomutDevam(raw) {
    const low = komutGovdesi(raw);
    if (!low || soruMu(low)) return null;
    const komut = sozlukBul(low);
    if (komut) {
      window.ruzgarProgramlamaMenu(komut);
      return { handled: true, reply: masaCevap[komut] || "Tamam." };
    }
    let ad = null;
    const named = low.match(/^(?:projeyi|proje|siteyi|vitrini)\s+(?:goster|ac)\s*[:\-]\s*(.+)$/);
    if (named) ad = named[1].trim();
    else if (/^(vitrini goster|vitrini ac|siteyi goster|siteyi ac)$/.test(low)) {
      ad = "vitrin";
      istenenGorunum = "proje";
    }
    else if (/^(projeyi goster|projeyi ac|proje goster|proje ac)$/.test(low)) ad = "";
    else if (programlamaAcik() && ajanEmriMi(low)) {
      return ajanYap(raw.replace(/^[Ll]ütfen\s+/, "").replace(/\?+$/g, "").trim()).then(function (sonuc) {
        return { handled: true, reply: sonuc.reply };
      });
    }
    else return null;
    const hedef = ad ? "projects/" + ad.replace(/^projects\//, "") : "projects/vitrin";
    void projeAc(hedef);
    const cevap = ad
      ? "Çalışma sayfasında " + ad + " açıldı. Dosyayı seç, alttan düzelt, Kaydet."
      : "Projeler çalışma sayfasında. Site varsa önizleme açılır.";
    return { handled: true, reply: cevap };
  };

  const yenile = document.getElementById("ruzgar-projeler-yenile");
  if (yenile) yenile.addEventListener("click", function () { void projeleriYukle(); });
  if (denemeKutu) denemeKutu.addEventListener("change", listeCiz);
  if (araKutu) araKutu.addEventListener("input", listeCiz);
  const ekle = document.getElementById("ruzgar-proje-ekle");
  if (ekle) ekle.addEventListener("click", function () { void dosyaEkle(); });
  const kaydet = document.getElementById("ruzgar-proje-kaydet");
  if (kaydet) {
    kaydet.addEventListener("click", function () {
      if (typeof saveProgramlamaAtolyeBuffer === "function") void saveProgramlamaAtolyeBuffer();
    });
  }
  const sil = document.getElementById("ruzgar-proje-sil");
  if (sil) sil.addEventListener("click", function () { void dosyaSil(); });
  const klasorSil = document.getElementById("ruzgar-proje-klasor-sil");
  if (klasorSil) klasorSil.addEventListener("click", function () { void projeSil(); });
  const ajanForm = document.getElementById("ruzgar-ajan-form");
  if (ajanForm) {
    ajanForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const yazi = emirKutu ? emirKutu.value : "";
      void ajanYap(yazi);
    });
  }

  tutamagiBagla();

  const sayfa = document.getElementById("page-programlama");
  if (sayfa) {
    const goz = new MutationObserver(function () {
      if (!sayfa.hidden) void projeleriYukle();
    });
    goz.observe(sayfa, { attributes: true, attributeFilter: ["hidden"] });
    if (!sayfa.hidden) void projeleriYukle();
  }
})();
