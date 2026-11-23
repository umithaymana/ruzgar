/* Rüzgar — yeni sohbet yüzü (mobil) · 2026-11-23 · Ümit & Gökçenur
 *
 * Tavır: sade sohbet + tek canlı «rüzgar çizgisi» (hazır / dinliyor / düşünüyor / konuşuyor).
 * Mevcut düğmeler (mikrofon, gönder, sürekli sohbet) SİLİNMEZ; yerleri değişir, böylece
 * ses akışı, barge-in ve tur kilidi aynen çalışır. Yüz KAPALI gelir:
 *   - Eski yüzdeki «Yeni yüz» düğmesi ya da  ?yuz=1  ile açılır
 *   - «+» menüsünden «Eski yüze dön» ya da  ?yuz=0  ile kapanır
 * Saf yardımcılar Node'da test edilir (ruzgar-yuz.test.js); DOM kısmı yalnız tarayıcıda çalışır.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory(false);
  else root.RuzgarYuz = factory(true);
})(typeof self !== "undefined" ? self : this, function (tarayici) {
  "use strict";

  var VERSION = "yuz-v1-2026-11-23";
  var KEY_YUZ = "ruzgar_pwa_yuz";
  var KEY_RENK = "ruzgar_pwa_yuz_renk";

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
    return RENKLER[0];
  }

  function selamMetni(saat) {
    var h = Number(saat);
    if (!isFinite(h)) h = 12;
    if (h >= 5 && h < 11) return "Günaydın";
    if (h >= 11 && h < 17) return "İyi günler";
    if (h >= 17 && h < 22) return "İyi akşamlar";
    return "İyi geceler";
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

  /** URL ?yuz=1|0 > kayıtlı tercih. Dönüş: "1" | "0". */
  function yuzTercihi(search, saklanan) {
    var m = /[?&]yuz=([01])(?:&|$)/.exec(String(search || ""));
    if (m) return m[1];
    return saklanan === "1" ? "1" : "0";
  }

  function durumNormal(d) {
    return d === "dinle" || d === "konus" || d === "dusun" ? d : "hazir";
  }

  function durumMetni(d) {
    var n = durumNormal(d);
    if (n === "dinle") return "Dinliyor";
    if (n === "dusun") return "Düşünüyor";
    if (n === "konus") return "Konuşuyor · dokun, sussun";
    return "";
  }

  function kullaniciAdiGuzel(ham) {
    var s = String(ham == null ? "" : ham).trim();
    if (!/^[A-Za-zÇĞİÖŞÜçğıöşü0-9._-]{2,24}$/.test(s)) return "";
    return s.charAt(0).toLocaleUpperCase("tr-TR") + s.slice(1);
  }

  function renkGecerli(hex) {
    return /^#[0-9a-fA-F]{6}$/.test(String(hex || ""));
  }

  var yardimci = {
    VERSION: VERSION,
    RENKLER: RENKLER,
    renkBul: renkBul,
    selamMetni: selamMetni,
    dalgaYolu: dalgaYolu,
    yuzTercihi: yuzTercihi,
    durumNormal: durumNormal,
    durumMetni: durumMetni,
    kullaniciAdiGuzel: kullaniciAdiGuzel,
    renkGecerli: renkGecerli,
  };

  if (!tarayici) return yardimci;

  /* ---------- DOM (yalnız tarayıcı) ---------- */

  var IKON = {
    plus: "M12 5v14M5 12h14",
    canli: "M3 12h2M7 8v8M11 5v14M15 8v8M19 10v4",
    belge: "M7 3h7l4 4v14H7zM14 3v4h4M9 12h6M9 16h6",
    tablo: "M4 5h16v14H4zM4 10h16M10 5v14",
    cizim: "M4 20l4-1 11-11-3-3L5 16zM14 6l3 3",
    sunum: "M4 4h16v11H4zM12 15v5M8 20h8",
    panel: "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z",
    yenile: "M20 11a8 8 0 1 0-2.3 5.7M20 5v6h-6",
    cikis: "M10 4H5v16h5M15 8l4 4-4 4M19 12H9",
    sohbet: "M4 5h16v11H9l-5 4z",
    eski: "M10 6l-6 6 6 6M4 12h16",
    kopyala: "M9 9h10v11H9zM5 15V4h10",
    oku: "M4 10v4h4l5 4V6L8 10zM16 9a4 4 0 0 1 0 6",
    tekrar: "M4 13a8 8 0 0 0 14 4M20 11A8 8 0 0 0 6 7M4 5v4h4M20 19v-4h-4",
  };

  function ikonSvg(ad) {
    return (
      '<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" ' +
      'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
      '<path d="' +
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
      u.searchParams.set("v", String(Date.now()));
      location.replace(u.toString());
    } catch (_) {
      location.reload();
    }
  }

  function renkUygula(id) {
    var r = renkBul(id);
    if (renkGecerli(r.hex)) document.documentElement.style.setProperty("--accent", r.hex);
    return r;
  }

  function e(etiket, sinif, html) {
    var n = document.createElement(etiket);
    if (sinif) n.className = sinif;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function baslat() {
    var d = document;
    var ls = depo();
    var bYeni = d.getElementById("btnYuzYeni");
    if (bYeni) {
      bYeni.onclick = function () {
        yuzuDegistir("1");
      };
    }

    var tercih = yuzTercihi(location.search, ls.al(KEY_YUZ));
    if (/[?&]yuz=[01](?:&|$)/.test(location.search)) ls.ver(KEY_YUZ, tercih);
    if (tercih !== "1") return;

    var html = d.documentElement;
    html.classList.add("ry");

    var chat = d.getElementById("chat");
    var input = d.getElementById("input");
    var btnSend = d.getElementById("btnSend");
    var btnMic = d.getElementById("btnMic");
    var btnLive = d.getElementById("btnLive");
    var dock = d.getElementById("sahneDock");
    var chatView = d.getElementById("chatView");
    var meta = d.getElementById("meta");
    if (!chat || !input || !btnSend || !btnMic || !dock || !chatView) return;

    renkUygula(ls.al(KEY_RENK) || "gok");
    if (meta) meta.textContent = "";
    input.setAttribute("rows", "1");
    input.setAttribute("placeholder", "Rüzgar'a yaz…");
    input.setAttribute("enterkeyhint", "send");
    btnSend.setAttribute("aria-label", "Gönder");
    btnMic.setAttribute("aria-label", "Basılı tut, konuş");

    /* --- alt çubuk: + · yazı alanı · mikrofon/gönder --- */
    var bar = e("div", "ry-bar");
    bar.id = "ryBar";
    var plus = e("button", "ry-plus", ikonSvg("plus"));
    plus.type = "button";
    plus.id = "ryPlus";
    plus.setAttribute("aria-label", "Menü");
    plus.setAttribute("aria-haspopup", "dialog");
    var alan = e("div", "ry-alan");
    alan.appendChild(input);
    var act = e("div", "ry-act");
    act.appendChild(btnMic);
    act.appendChild(btnSend);
    bar.appendChild(plus);
    bar.appendChild(alan);
    bar.appendChild(act);

    /* --- rüzgar çizgisi --- */
    var cizgi = e("div", "ry-cizgi");
    cizgi.id = "ryCizgi";
    cizgi.setAttribute("data-durum", "hazir");
    cizgi.setAttribute("role", "button");
    cizgi.setAttribute("tabindex", "0");
    cizgi.setAttribute("aria-label", "Rüzgar durumu");
    var yol = dalgaYolu(800, 24);
    function katman(sinif) {
      var w = e("div", "ry-w " + sinif);
      w.innerHTML =
        '<svg viewBox="0 0 800 24" preserveAspectRatio="none" aria-hidden="true">' +
        '<path d="' +
        yol +
        '" fill="none" stroke="currentColor" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>';
      return w;
    }
    cizgi.appendChild(katman("ry-w-a"));
    cizgi.appendChild(katman("ry-w-b"));
    var supurge = e("div", "ry-supurge");
    cizgi.appendChild(supurge);
    var altyazi = e("div", "ry-altyazi");
    altyazi.id = "ryDurumMetin";
    altyazi.setAttribute("aria-live", "polite");

    var alt = e("div", "ry-alt");
    alt.appendChild(cizgi);
    alt.appendChild(altyazi);
    alt.appendChild(bar);
    dock.appendChild(alt);

    function durumBas(d) {
      var n = durumNormal(d);
      cizgi.setAttribute("data-durum", n);
      altyazi.textContent = durumMetni(n);
      altyazi.classList.toggle("on", n !== "hazir");
      cizgi.setAttribute("aria-label", "Rüzgar: " + (durumMetni(n) || "hazır"));
    }
    var sade = d.getElementById("sadeDurum");
    if (sade) {
      durumBas(sade.getAttribute("data-durum"));
      new MutationObserver(function () {
        durumBas(sade.getAttribute("data-durum"));
      }).observe(sade, { attributes: true, attributeFilter: ["data-durum"] });
    }
    function cizgiDokun() {
      var n = cizgi.getAttribute("data-durum");
      if (n === "konus" || n === "dusun") {
        try {
          window.ruzgarMobil && window.ruzgarMobil.sustur("yuz-cizgi");
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
      bar.classList.toggle("ry-yazili", yazili);
      input.style.height = "auto";
      var h = Math.min(input.scrollHeight || 0, 132);
      if (h > 0) input.style.height = h + "px";
    }
    input.addEventListener("input", barYenile);
    btnSend.addEventListener("click", function () {
      setTimeout(barYenile, 0);
    });
    setInterval(barYenile, 400);
    barYenile();

    /* --- boş ekran: selam + öneri çipleri --- */
    var bos = e("div", "ry-bos");
    bos.id = "ryBos";
    var kim = "";
    try {
      var ham = ls.al("ruzgar_pwa_who");
      var ad = "";
      if (ham) {
        try {
          var j = JSON.parse(ham);
          ad = (j && (j.kullanici || j.ad)) || "";
        } catch (_) {
          ad = ham;
        }
      }
      kim = kullaniciAdiGuzel(ad);
    } catch (_) {}
    var selam = selamMetni(new Date().getHours()) + (kim ? " " + kim : "");
    bos.innerHTML =
      '<div class="ry-bos-ad">RÜZGAR</div><div class="ry-bos-selam"></div><div class="ry-ciplar"></div>';
    bos.querySelector(".ry-bos-selam").textContent = selam;
    var ciplar = bos.querySelector(".ry-ciplar");
    [
      "Bugün neler yapabiliriz?",
      "Bir konuyu bana anlat: ",
      "Bir belge hazırla: ",
    ].forEach(function (m) {
      var c = e("button", "ry-cip");
      c.type = "button";
      c.textContent = m.trim().replace(/:$/, "");
      c.addEventListener("click", function () {
        input.value = m;
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
      });
      ciplar.appendChild(c);
    });
    dock.insertBefore(bos, chat);
    function bosYenile() {
      chatView.classList.toggle("ry-bos-on", chat.childElementCount === 0);
    }
    new MutationObserver(bosYenile).observe(chat, { childList: true });
    bosYenile();

    /* --- cevap altı sessiz şerit (dokununca) --- */
    var acikSerit = null;
    function seritKapat() {
      if (acikSerit && acikSerit.parentNode) acikSerit.parentNode.removeChild(acikSerit);
      acikSerit = null;
    }
    function seritDugme(ad, etiket, fn) {
      var b = e("button", "ry-serit-d", ikonSvg(ad) + "<span></span>");
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
      var hedef = ev.target && ev.target.closest ? ev.target.closest(".bubble.bot") : null;
      if (!hedef) {
        if (!(ev.target && ev.target.closest && ev.target.closest(".ry-serit"))) seritKapat();
        return;
      }
      try {
        var sec = window.getSelection && String(window.getSelection());
        if (sec && sec.length > 0) return;
      } catch (_) {}
      var ayniydi = acikSerit && acikSerit.previousElementSibling === hedef;
      seritKapat();
      if (ayniydi) return;
      var serit = e("div", "ry-serit");
      serit.appendChild(
        seritDugme("kopyala", "Kopyala", function (b) {
          metinKopyala(hedef.textContent || "", b);
        }),
      );
      serit.appendChild(
        seritDugme("oku", "Oku", function () {
          try {
            window.ruzgarMobil && window.ruzgarMobil.oku(hedef.textContent || "");
          } catch (_) {}
        }),
      );
      var sonBot = chat.querySelectorAll(".bubble.bot");
      if (sonBot.length && sonBot[sonBot.length - 1] === hedef) {
        serit.appendChild(
          seritDugme("tekrar", "Yeniden dene", function () {
            var p = hedef.previousElementSibling;
            while (p && !(p.classList && p.classList.contains("user"))) p = p.previousElementSibling;
            if (!p) return;
            input.value = p.textContent || "";
            input.dispatchEvent(new Event("input", { bubbles: true }));
            seritKapat();
            btnSend.click();
          }),
        );
      }
      hedef.insertAdjacentElement("afterend", serit);
      acikSerit = serit;
    });

    /* --- «+» menüsü --- */
    var menuKok = e("div", "ry-menu-kok");
    menuKok.hidden = true;
    var perde = e("div", "ry-perde");
    var sayfa = e("div", "ry-menu");
    sayfa.setAttribute("role", "dialog");
    sayfa.setAttribute("aria-label", "Rüzgar menüsü");
    menuKok.appendChild(perde);
    menuKok.appendChild(sayfa);
    d.body.appendChild(menuKok);

    function menuKapat() {
      menuKok.hidden = true;
      d.body.classList.remove("ry-menu-acik");
    }
    function tikla(id) {
      var n = d.getElementById(id);
      if (n) n.click();
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
      var b = e("button", "ry-oge", ikonSvg(ad) + "<span></span>");
      b.type = "button";
      b.querySelector("span").textContent = etiket;
      b.addEventListener("click", fn);
      return b;
    }
    function menuKur() {
      sayfa.textContent = "";
      sayfa.appendChild(e("div", "ry-tutac"));
      var canliEtiket =
        btnLive && /durdur|kapat|bitir/i.test(btnLive.textContent || "")
          ? "Sürekli sohbeti durdur"
          : "Sürekli sohbet";
      var izgara = e("div", "ry-izgara");
      izgara.appendChild(
        kutu("canli", canliEtiket, function () {
          menuKapat();
          if (btnLive) btnLive.click();
        }),
      );
      izgara.appendChild(kutu("belge", "Belge", hazirla("Bir belge hazırla: ")));
      izgara.appendChild(kutu("tablo", "Tablo", hazirla("Bir tablo hazırla: ")));
      izgara.appendChild(kutu("cizim", "Çizim", hazirla("Bir çizim yap: ")));
      izgara.appendChild(kutu("sunum", "Sunum", hazirla("Bir sunum hazırla: ")));
      sayfa.appendChild(izgara);

      var renkBasl = e("div", "ry-baslik", "Renk");
      sayfa.appendChild(renkBasl);
      var renkSira = e("div", "ry-renkler");
      var simdi = ls.al(KEY_RENK) || "gok";
      RENKLER.forEach(function (r) {
        var b = e("button", "ry-renk" + (r.id === simdi ? " on" : ""));
        b.type = "button";
        b.style.setProperty("--c", r.hex);
        b.setAttribute("aria-label", r.ad);
        b.title = r.ad;
        b.addEventListener("click", function () {
          ls.ver(KEY_RENK, r.id);
          renkUygula(r.id);
          menuKur();
        });
        renkSira.appendChild(b);
      });
      sayfa.appendChild(renkSira);

      var alt2 = e("div", "ry-liste");
      var panelAcik = d.getElementById("panelView") && !d.getElementById("panelView").classList.contains("hidden");
      if (panelAcik) {
        alt2.appendChild(
          kutu("sohbet", "Sohbete dön", function () {
            menuKapat();
            tikla("btnNavChat");
          }),
        );
      } else {
        alt2.appendChild(
          kutu("panel", "Panel", function () {
            menuKapat();
            tikla("btnNavPanel");
          }),
        );
      }
      alt2.appendChild(
        kutu("yenile", "Yenile", function () {
          menuKapat();
          tikla("btnNavReload");
        }),
      );
      alt2.appendChild(
        kutu("cikis", "Çıkış", function () {
          menuKapat();
          tikla("btnNavLogout");
        }),
      );
      alt2.appendChild(
        kutu("eski", "Eski yüze dön", function () {
          yuzuDegistir("0");
        }),
      );
      sayfa.appendChild(alt2);
    }
    function menuAc() {
      menuKur();
      menuKok.hidden = false;
      d.body.classList.add("ry-menu-acik");
    }
    plus.addEventListener("click", menuAc);
    perde.addEventListener("click", menuKapat);
    d.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && !menuKok.hidden) menuKapat();
    });

    /* üst köşe: sohbet dışında da (panel) menüye ulaşılsın */
    var ust = d.querySelector(".top-head");
    if (ust) {
      var ustBtn = e("button", "ry-ust-btn", ikonSvg("plus"));
      ustBtn.type = "button";
      ustBtn.id = "ryUstBtn";
      ustBtn.setAttribute("aria-label", "Menü");
      ustBtn.addEventListener("click", menuAc);
      ust.appendChild(ustBtn);
    }
  }

  function hazirDegilse() {
    try {
      baslat();
    } catch (err) {
      try {
        document.documentElement.classList.remove("ry");
        if (window.console) console.warn("ruzgar-yuz: açılamadı, eski yüz kaldı", err);
      } catch (_) {}
    }
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", hazirDegilse);
  else hazirDegilse();

  return yardimci;
});
