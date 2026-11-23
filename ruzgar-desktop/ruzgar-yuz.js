/* Rüzgar — yeni sohbet yüzü (masaüstü) · 2026-11-23 · Ümit & Gökçenur
 *
 * Mobil yüzün masaüstü karşılığı: sade sohbet + tek canlı «rüzgar çizgisi»
 * (hazır / dinliyor / düşünüyor / konuşuyor), 6 vurgu rengi, «+» menüsü, sessiz cevap şeridi.
 *
 * Sınır (ruzgar-arayuz-kilit-FROZEN): YALNIZ sohbet paneli içi (yazı çubuğu + mesaj görünümü).
 * Motor listesi, geri/ileri/yenile, sohbet tutamacı, dört masa ve Rüzgar sahnesi'ne dokunmaz.
 * Mevcut düğmeler (mikrofon, gönder, durdur, duraklat/devam) SİLİNMEZ; yerleri değişir,
 * böylece app.js içindeki tüm ses/akış mantığı aynen çalışır.
 *
 * Varsayılan AÇIK. Kapatma: «+» menüsü → «Eski sohbete dön»  ya da  ?yuz=0
 * (geri açma: ?yuz=1). Saf yardımcılar Node'da test edilir (ruzgar-yuz.test.js).
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(false);
  else root.RuzgarYuzMasaustu = factory(true);
})(typeof self !== "undefined" ? self : this, function (tarayici) {
  "use strict";

  var VERSION = "yuz-masaustu-v1-2026-11-23";
  var KEY_YUZ = "ruzgar_desk_yuz";
  var KEY_RENK = "ruzgar_desk_yuz_renk";
  var VARSAYILAN_RENK = "altin";

  var RENKLER = [
    { id: "gok", ad: "Gök", hex: "#38bdf8" },
    { id: "turkuaz", ad: "Turkuaz", hex: "#2dd4bf" },
    { id: "altin", ad: "Altın", hex: "#d4af37" },
    { id: "gul", ad: "Gül", hex: "#fb7185" },
    { id: "orman", ad: "Orman", hex: "#4ade80" },
    { id: "mor", ad: "Mor", hex: "#a78bfa" },
  ];

  /* ---------- saf yardımcılar ---------- */

  function renkBul(id) {
    for (var i = 0; i < RENKLER.length; i++) if (RENKLER[i].id === id) return RENKLER[i];
    return renkBul(VARSAYILAN_RENK);
  }

  function renkGecerli(hex) {
    return /^#[0-9a-fA-F]{6}$/.test(String(hex || ""));
  }

  /** Yatay kayabilen sinüs yolu: her 100 birimde bir yarım dalga (Q + T zinciri). */
  function dalgaYolu(genislik, yukseklik) {
    var w = Math.max(200, Math.round(genislik || 800));
    var y = Math.max(8, Math.round(yukseklik || 24));
    var orta = y / 2;
    var d = "M0 " + orta + " Q50 0 100 " + orta;
    for (var x = 200; x <= w; x += 100) d += " T" + x + " " + orta;
    return d;
  }

  /** URL ?yuz=1|0 > kayıtlı tercih > varsayılan AÇIK. Dönüş: "1" | "0". */
  function yuzTercihi(search, saklanan) {
    var m = /[?&]yuz=([01])(?:&|$)/.exec(String(search || ""));
    if (m) return m[1];
    return saklanan === "0" ? "0" : "1";
  }

  function durumNormal(d) {
    return d === "dinle" || d === "konus" || d === "dusun" ? d : "hazir";
  }

  /**
   * Ekrandaki ipuçlarından çizgi durumu. Öncelik: dinle > konuş > düşün > hazır.
   * girdi: { dinliyor, duraklatik, konusuyor, mesgul }
   */
  function durumHesapla(g) {
    g = g || {};
    if (g.dinliyor) return "dinle";
    if (g.duraklatik) return "konus"; // çizgi yine «konuşma» katmanında, ama sakin (ryd-durak)
    if (g.konusuyor) return "konus";
    if (g.mesgul) return "dusun";
    return "hazir";
  }

  function durumMetni(d, duraklatik) {
    if (duraklatik) return "Duraklatıldı · devam için ▶";
    var n = durumNormal(d);
    if (n === "dinle") return "Dinliyor";
    if (n === "dusun") return "Düşünüyor";
    if (n === "konus") return "Konuşuyor · dokun, sussun";
    return "";
  }

  var yardimci = {
    VERSION: VERSION,
    KEY_YUZ: KEY_YUZ,
    KEY_RENK: KEY_RENK,
    RENKLER: RENKLER,
    renkBul: renkBul,
    renkGecerli: renkGecerli,
    dalgaYolu: dalgaYolu,
    yuzTercihi: yuzTercihi,
    durumNormal: durumNormal,
    durumHesapla: durumHesapla,
    durumMetni: durumMetni,
  };

  if (!tarayici) return yardimci;

  /* ---------- DOM (yalnız tarayıcı) ---------- */

  var IKON = {
    plus: "M12 5v14M5 12h14",
    belge: "M7 3h7l4 4v14H7zM14 3v4h4M9 12h6M9 16h6",
    tablo: "M4 5h16v14H4zM4 10h16M10 5v14",
    cizim: "M4 20l4-1 11-11-3-3L5 16zM14 6l3 3",
    sunum: "M4 4h16v11H4zM12 15v5M8 20h8",
    ara: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM20 20l-4-4",
    temizle: "M5 7h14M10 7V4h4v3M7 7l1 13h8l1-13",
    disa: "M12 4v11M7 10l5 5 5-5M5 20h14",
    ses: "M4 10v4h4l5 4V6L8 10zM16 9a4 4 0 0 1 0 6",
    eski: "M10 6l-6 6 6 6M4 12h16",
    kopyala: "M9 9h10v11H9zM5 15V4h10",
    oku: "M4 10v4h4l5 4V6L8 10zM16 9a4 4 0 0 1 0 6",
    tekrar: "M4 13a8 8 0 0 0 14 4M20 11A8 8 0 0 0 6 7M4 5v4h4M20 19v-4h-4",
    kapat: "M6 6l12 12M18 6L6 18",
  };

  function ikonSvg(ad, boy) {
    var b = boy || 20;
    return (
      '<svg viewBox="0 0 24 24" width="' +
      b +
      '" height="' +
      b +
      '" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true"><path d="' +
      (IKON[ad] || "") +
      '"/></svg>'
    );
  }

  function depo() {
    return {
      al: function (k) {
        try {
          return localStorage.getItem(k);
        } catch (_) {
          return null;
        }
      },
      ver: function (k, v) {
        try {
          localStorage.setItem(k, v);
        } catch (_) {}
      },
    };
  }

  function yuzuDegistir(deger) {
    depo().ver(KEY_YUZ, deger);
    try {
      var u = new URL(location.href);
      u.searchParams.delete("yuz");
      location.replace(u.toString());
    } catch (_) {
      location.reload();
    }
  }

  function renkUygula(id) {
    var r = renkBul(id);
    if (renkGecerli(r.hex)) document.documentElement.style.setProperty("--ryd-a", r.hex);
    return r;
  }

  function e(etiket, sinif, html) {
    var n = document.createElement(etiket);
    if (sinif) n.className = sinif;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function gorunur(n) {
    return !!n && !n.hidden && n.getAttribute("hidden") === null;
  }

  function baslat() {
    var d = document;
    var ls = depo();

    var tercih = yuzTercihi(location.search, ls.al(KEY_YUZ));
    if (/[?&]yuz=[01](?:&|$)/.test(location.search)) ls.ver(KEY_YUZ, tercih);
    if (tercih !== "1") return;

    var panel = d.querySelector(".panel-chat");
    var composer = panel && panel.querySelector(".composer");
    var chat = d.getElementById("chat-messages");
    var input = d.getElementById("msg-input");
    var btnSend = d.getElementById("btn-send");
    var btnMic = d.getElementById("btn-mic");
    var btnStop = d.getElementById("btn-stop");
    var btnPause = d.getElementById("btn-tts-pause");
    if (!panel || !composer || !chat || !input || !btnSend || !btnMic) return;

    var html = d.documentElement;
    html.classList.add("ryd");
    renkUygula(ls.al(KEY_RENK) || VARSAYILAN_RENK);

    var yuz = d.getElementById("ruzgar-face");
    var micSeviye = d.getElementById("mic-level-wrap");
    input.setAttribute("rows", "1");
    input.setAttribute("placeholder", "Rüzgar'a yaz…");
    btnSend.setAttribute("aria-label", "Gönder");

    /* --- üstte sessiz marka --- */
    var ust = e("div", "ryd-ust");
    ust.innerHTML = '<span class="ryd-marka">RÜZGAR</span>';
    panel.insertBefore(ust, panel.firstChild);

    /* --- alt çubuk: + · yazı · durdur · duraklat · mikrofon/gönder --- */
    var bar = e("div", "ryd-bar");
    var plus = e("button", "ryd-plus", ikonSvg("plus", 22));
    plus.type = "button";
    plus.id = "rydPlus";
    plus.title = "Menü";
    plus.setAttribute("aria-label", "Menü");
    plus.setAttribute("aria-haspopup", "dialog");
    var alan = e("div", "ryd-alan");
    alan.appendChild(input);
    var act = e("div", "ryd-act");
    act.appendChild(btnMic);
    act.appendChild(btnSend);
    bar.appendChild(plus);
    bar.appendChild(alan);
    if (btnStop) bar.appendChild(btnStop);
    if (btnPause) bar.appendChild(btnPause);
    bar.appendChild(act);

    /* --- rüzgar çizgisi --- */
    var cizgi = e("div", "ryd-cizgi");
    cizgi.id = "rydCizgi";
    cizgi.setAttribute("data-durum", "hazir");
    cizgi.setAttribute("role", "button");
    cizgi.setAttribute("tabindex", "0");
    cizgi.setAttribute("aria-label", "Rüzgar durumu");
    var yol = dalgaYolu(800, 24);
    function katman(sinif) {
      var w = e("div", "ryd-w " + sinif);
      w.innerHTML =
        '<svg viewBox="0 0 800 24" preserveAspectRatio="none" aria-hidden="true">' +
        '<path d="' +
        yol +
        '" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>';
      return w;
    }
    cizgi.appendChild(katman("ryd-w-a"));
    cizgi.appendChild(katman("ryd-w-b"));
    cizgi.appendChild(e("div", "ryd-supurge"));
    var altyazi = e("div", "ryd-altyazi");
    altyazi.setAttribute("aria-live", "polite");

    var alt = e("div", "ryd-alt");
    alt.appendChild(cizgi);
    alt.appendChild(altyazi);
    if (micSeviye) alt.appendChild(micSeviye);
    alt.appendChild(bar);
    composer.appendChild(alt);

    /* --- durum: ekrandaki mevcut ipuçlarından (app.js'e dokunmadan) --- */
    var sonDuraklatik = false;
    function durumOku() {
      var dinliyor = btnMic.classList.contains("listening");
      var pausePlay = btnPause && btnPause.querySelector(".icon-play");
      /* app.js simge durumunu SVG'nin `hidden` özelliğine yazar (öznitelik değil); oradan okunur */
      var duraklatik = !!(btnPause && gorunur(btnPause) && pausePlay && pausePlay.hidden === false);
      if (btnPause) {
        btnPause.classList.toggle("ryd-devam", duraklatik);
        var ip = btnPause.querySelector(".icon-pause");
        if (ip) ip.toggleAttribute("hidden", duraklatik);
        if (pausePlay) pausePlay.toggleAttribute("hidden", !duraklatik);
      }
      var pill = d.getElementById("tts-status-pill");
      var konusuyor = !!(yuz && yuz.classList.contains("is-talking")) || !!(pill && gorunur(pill));
      var dusunuyor = !!(btnSend && btnSend.disabled);
      var dusunOverlay = d.getElementById("thinking-center-overlay");
      if (dusunOverlay && gorunur(dusunOverlay)) dusunuyor = true;
      /* Rüzgar sahnesi durumu zaten hesaplıyor (metin yazarak konuşmayı da kapsar):
         varsa tek doğruluk kaynağı odur, sahne ile çizgi hiç ayrışmaz. */
      var sahne = d.getElementById("ruzgar-sahne");
      var sm = sahne && sahne.getAttribute("data-sahne-mode");
      if (sm === "konus") konusuyor = true;
      if (sm === "dusun") dusunuyor = true;
      if (sm === "dinle") dinliyor = true;
      return {
        durum: durumHesapla({
          dinliyor: dinliyor,
          duraklatik: duraklatik,
          konusuyor: konusuyor,
          mesgul: dusunuyor || (btnStop && gorunur(btnStop)),
        }),
        duraklatik: duraklatik,
      };
    }
    var sonDurum = "";
    function durumYansit() {
      var s = durumOku();
      if (s.durum === sonDurum && s.duraklatik === sonDuraklatik) return;
      sonDurum = s.durum;
      sonDuraklatik = s.duraklatik;
      cizgi.setAttribute("data-durum", s.durum);
      cizgi.classList.toggle("ryd-durak", s.duraklatik);
      var metin = durumMetni(s.durum, s.duraklatik);
      altyazi.textContent = metin;
      altyazi.classList.toggle("on", !!metin);
      cizgi.setAttribute("aria-label", "Rüzgar: " + (metin || "hazır"));
    }
    setInterval(durumYansit, 250);
    durumYansit();

    function cizgiDokun() {
      var n = cizgi.getAttribute("data-durum");
      if (n === "konus" || n === "dusun") {
        try {
          if (btnStop && gorunur(btnStop)) btnStop.click();
        } catch (_) {}
      }
    }
    cizgi.addEventListener("click", cizgiDokun);
    cizgi.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " ") {
        ev.preventDefault();
        cizgiDokun();
      }
    });

    /* --- mikrofon ⇄ gönder + yazı alanı büyümesi --- */
    function barYenile() {
      var yazili = !!(input.value || "").trim();
      bar.classList.toggle("ryd-yazili", yazili);
      input.style.height = "auto";
      var h = Math.min(input.scrollHeight || 0, 150);
      if (h > 0) input.style.height = h + "px";
      bar.classList.toggle("ryd-cok", h > 46);
    }
    input.addEventListener("input", barYenile);
    btnSend.addEventListener("click", function () {
      setTimeout(barYenile, 0);
    });
    setInterval(barYenile, 400);
    barYenile();

    /* --- cevap altı sessiz şerit (cevaba dokununca) --- */
    var acikSerit = null;
    function seritKapat() {
      if (acikSerit && acikSerit.parentNode) acikSerit.parentNode.removeChild(acikSerit);
      acikSerit = null;
    }
    function seritDugme(ad, etiket, fn) {
      var b = e("button", "ryd-serit-d", ikonSvg(ad, 15) + "<span></span>");
      b.type = "button";
      b.querySelector("span").textContent = etiket;
      b.addEventListener("click", function (ev) {
        ev.stopPropagation();
        fn(b);
      });
      return b;
    }
    function metinKopyala(t, b) {
      function tamam() {
        var s = b.querySelector("span");
        var onceki = s.textContent;
        s.textContent = "Kopyalandı";
        setTimeout(function () {
          s.textContent = onceki;
        }, 1300);
      }
      function yedek() {
        try {
          var ta = d.createElement("textarea");
          ta.value = t;
          ta.setAttribute("readonly", "");
          ta.style.position = "fixed";
          ta.style.opacity = "0";
          d.body.appendChild(ta);
          ta.select();
          d.execCommand("copy");
          d.body.removeChild(ta);
          tamam();
        } catch (_) {}
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(t).then(tamam, yedek);
      } else yedek();
    }
    chat.addEventListener("click", function (ev) {
      var t = ev.target;
      if (!t || !t.closest) return;
      if (t.closest(".ryd-serit")) return;
      if (t.closest("a, button, input, select, textarea, summary, .code-card")) return;
      var hedef = t.closest(".bubble.assistant");
      if (!hedef || hedef.classList.contains("chat-welcome") || hedef.classList.contains("thinking-bubble")) {
        seritKapat();
        return;
      }
      try {
        var sec = window.getSelection && String(window.getSelection());
        if (sec && sec.length > 0) return;
      } catch (_) {}
      var ayniydi = acikSerit && acikSerit.previousElementSibling === hedef;
      seritKapat();
      if (ayniydi) return;
      var serit = e("div", "ryd-serit");
      serit.appendChild(
        seritDugme("kopyala", "Kopyala", function (b) {
          metinKopyala((hedef.innerText || hedef.textContent || "").trim(), b);
        }),
      );
      serit.appendChild(
        seritDugme("oku", "Oku", function () {
          try {
            if (typeof window.ruzgarSpeak === "function") window.ruzgarSpeak((hedef.innerText || hedef.textContent || "").trim());
          } catch (_) {}
        }),
      );
      var hepsi = chat.querySelectorAll(".bubble.assistant:not(.chat-welcome)");
      if (hepsi.length && hepsi[hepsi.length - 1] === hedef) {
        serit.appendChild(
          seritDugme("tekrar", "Yeniden dene", function () {
            var p = hedef.previousElementSibling;
            while (p && !(p.classList && p.classList.contains("user"))) p = p.previousElementSibling;
            if (!p) return;
            input.value = (p.innerText || p.textContent || "").trim();
            input.dispatchEvent(new Event("input", { bubbles: true }));
            seritKapat();
            btnSend.click();
          }),
        );
      }
      hedef.insertAdjacentElement("afterend", serit);
      acikSerit = serit;
    });
    if (window.MutationObserver) {
      new MutationObserver(function (kayitlar) {
        for (var i = 0; i < kayitlar.length; i++) {
          var eklenen = kayitlar[i].addedNodes || [];
          for (var j = 0; j < eklenen.length; j++) {
            var n = eklenen[j];
            if (n && n.classList && !n.classList.contains("ryd-serit")) {
              seritKapat();
              return;
            }
          }
        }
      }).observe(chat, { childList: true });
    }

    /* --- «+» menüsü (sohbet panelinin içinde, alttan açılır) --- */
    var menuKok = e("div", "ryd-menu-kok");
    menuKok.hidden = true;
    var perde = e("div", "ryd-perde");
    var sayfa = e("div", "ryd-menu");
    sayfa.setAttribute("role", "dialog");
    sayfa.setAttribute("aria-label", "Rüzgar menüsü");
    menuKok.appendChild(perde);
    menuKok.appendChild(sayfa);
    panel.appendChild(menuKok);

    function menuKapat() {
      menuKok.hidden = true;
      plus.classList.remove("on");
    }
    function hazirla(onek) {
      return function () {
        menuKapat();
        input.value = onek;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        try {
          input.focus();
        } catch (_) {}
      };
    }
    function kutu(ad, etiket, fn) {
      var b = e("button", "ryd-oge", ikonSvg(ad, 20) + "<span></span>");
      b.type = "button";
      b.querySelector("span").textContent = etiket;
      b.addEventListener("click", fn);
      return b;
    }
    function tikla(id) {
      var n = d.getElementById(id);
      if (n) n.click();
    }

    /* bir kez kurulan bölümler: seçenekler (mevcut kutular TAŞINIR, durumları korunur) */
    var izgara = e("div", "ryd-izgara");
    izgara.appendChild(kutu("belge", "Belge", hazirla("Bir belge hazırla: ")));
    izgara.appendChild(kutu("tablo", "Tablo", hazirla("Bir tablo hazırla: ")));
    izgara.appendChild(kutu("cizim", "Çizim", hazirla("Bir çizim yap: ")));
    izgara.appendChild(kutu("sunum", "Sunum", hazirla("Bir sunum hazırla: ")));

    var secenekBasl = e("div", "ryd-baslik", "Seçenekler");
    var secenekler = e("div", "ryd-secenekler");
    [
      "opt-web",
      "opt-voice-out",
      "opt-voice-send",
      "opt-link-read",
      "opt-code",
      "opt-autonom",
      "opt-fetch",
    ].forEach(function (id) {
      var n = d.getElementById(id);
      var satir = n && n.closest ? n.closest("label") : null;
      if (satir) secenekler.appendChild(satir);
    });

    var renkBasl = e("div", "ryd-baslik", "Renk");
    var renkSira = e("div", "ryd-renkler");
    function renkleriKur() {
      renkSira.textContent = "";
      var simdi = ls.al(KEY_RENK) || VARSAYILAN_RENK;
      RENKLER.forEach(function (r) {
        var b = e("button", "ryd-renk" + (r.id === simdi ? " on" : ""));
        b.type = "button";
        b.style.setProperty("--c", r.hex);
        b.setAttribute("aria-label", r.ad);
        b.title = r.ad;
        b.addEventListener("click", function () {
          ls.ver(KEY_RENK, r.id);
          renkUygula(r.id);
          renkleriKur();
        });
        renkSira.appendChild(b);
      });
    }

    var liste = e("div", "ryd-liste");
    liste.appendChild(
      kutu("ara", "Sohbette ara", function () {
        menuKapat();
        d.body.classList.toggle("ruzgar-search-open");
        var a = d.getElementById("chat-history-search");
        if (a && d.body.classList.contains("ruzgar-search-open")) {
          try {
            a.focus();
          } catch (_) {}
        }
      }),
    );
    liste.appendChild(
      kutu("temizle", "Sohbeti temizle", function () {
        menuKapat();
        tikla("btn-chat-panel-clear");
      }),
    );
    liste.appendChild(
      kutu("disa", "Dışa aktar", function () {
        menuKapat();
        tikla("btn-chat-history-export");
      }),
    );
    liste.appendChild(
      kutu("ses", "Ses seç", function () {
        menuKapat();
        try {
          if (typeof window.ruzgarOpenVoiceSheet === "function") window.ruzgarOpenVoiceSheet();
        } catch (_) {}
      }),
    );
    liste.appendChild(
      kutu("eski", "Eski sohbete dön", function () {
        yuzuDegistir("0");
      }),
    );

    sayfa.appendChild(e("div", "ryd-tutac"));
    sayfa.appendChild(izgara);
    sayfa.appendChild(secenekBasl);
    sayfa.appendChild(secenekler);
    sayfa.appendChild(renkBasl);
    sayfa.appendChild(renkSira);
    sayfa.appendChild(liste);

    function menuAc() {
      renkleriKur();
      menuKok.hidden = false;
      plus.classList.add("on");
    }
    plus.addEventListener("click", function () {
      if (menuKok.hidden) menuAc();
      else menuKapat();
    });
    perde.addEventListener("click", menuKapat);
    d.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && !menuKok.hidden) menuKapat();
    });
  }

  function hazirDegilse() {
    try {
      baslat();
    } catch (err) {
      try {
        document.documentElement.classList.remove("ryd");
        if (window.console) console.warn("ruzgar-yuz: açılamadı, eski sohbet kaldı", err);
      } catch (_) {}
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", hazirDegilse);
  else hazirDegilse();

  return yardimci;
});
