/* Rüzgar — ortak TUR + SES mantığı (Madde 2 · Sprint E+F) · 2026-11-23
 *
 * Tek dosya, DOM'suz saf mantık (tarayıcıda window.RuzgarTurSes, Node'da require):
 *   - SSE okuyucu (/api/chat/stream) + kimlik-hatası (auth_error) ayrımı
 *   - Cümle çekici (akış sırasında ilk ses parçasını erken çıkarır)
 *   - TTS kuyruğu (parça oluşunca sentez başlar; 1 parça önden hazırlık)
 *   - Tur kilidi (turn_id + barge-in: eski kuyruk/ses yeni cevaba binmez)
 *   - Oturum (akış + çekici + kuyruk + telemetri; düzeltme/iptal kuralları)
 *
 * Masaüstü `ruzgar-desktop/app.js` (arayüz kilidi) aynı kuralları kendi içinde taşır
 * (ttsSessionCounter + takeFirstTtsSentence); sabitler bilerek onunla hizalıdır.
 * Mobil PWA bu dosyayı kullanır. Kapatma: localStorage ruzgar_pwa_tur_ses=0
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.RuzgarTurSes = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  var VERSION = "tur-ses-v1-2026-11-23";

  /** Masaüstü RUZGAR_TTS_STREAM_* sabitleriyle hizalı */
  var CFG = {
    MIN_FIRST_CHARS: 28,
    FIRST_CHARS: 110,
    EARLY_CHARS: 72,
    MERGE_CHARS: 380,
    MIN_QUEUE_CHARS: 20,
    LONG_NO_PUNCT_CHARS: 260,
    MAX_SPEECH_CHARS: 3200,
    SSE_IDLE_MS: 90000,
    SSE_IDLE_AFTER_TOKEN_MS: 45000,
  };

  /** fetchChunk bu değeri dönerse sunucu «tur iptal» dedi → kuyruk durur */
  var IPTAL = { iptal: true };

  function nowMs() {
    try {
      if (typeof performance !== "undefined" && performance.now) return performance.now();
    } catch (_) {}
    return Date.now();
  }

  function newTurnId() {
    var r = "";
    try {
      if (typeof crypto !== "undefined" && crypto.getRandomValues) {
        var a = new Uint8Array(6);
        crypto.getRandomValues(a);
        for (var i = 0; i < a.length; i++) r += ("0" + a[i].toString(16)).slice(-2);
      }
    } catch (_) {}
    if (!r) r = Math.random().toString(16).slice(2, 14);
    return "t" + Date.now().toString(36) + "-" + r;
  }

  /* ------------------------------------------------------------------ metin */

  /** Masaüstü ttsPlainForSpeech + prepareTtsSpeechText ile aynı temizlik (köşeli etiket korunur) */
  function speechPlain(text) {
    var t = String(text == null ? "" : text)
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/\*\*([^*]+)\*\*/g, "$1")
      .replace(/\*([^*]+)\*/g, "$1")
      .replace(/^#+\s*/gm, "")
      .replace(/_\([^)]*(?:backend|sohbet\s+içi|karakter)[^)]*\)_/gi, "")
      .replace(/\[HTTP\s+\d+\][\s\S]*/gi, "")
      .replace(/\(TARIH_VE_KULTUR[^)]+\)/gi, "")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/\s+/g, " ")
      .trim();
    return t;
  }

  function collapseWs(s) {
    return String(s == null ? "" : s).replace(/\s+/g, " ").trim();
  }

  /**
   * Akışta söylenen metin (streamed), sunucunun nihai cevabının (full) ÖNEKİ mi?
   * Boşluk farkları yok sayılır. false → model cevabı sonradan değiştirdi (düzeltme).
   */
  function prefixConsistent(streamed, full) {
    var a = collapseWs(streamed);
    var b = collapseWs(full);
    if (!a) return true;
    return b.indexOf(a) === 0;
  }

  /* --------------------------------------------------------- cümle çekici */

  var TERM_RE = /[.!?…]+["'»”)\]]*(?:\s+|$)|\n+/g;

  function sentenceEnds(s, final) {
    var ends = [];
    var m;
    TERM_RE.lastIndex = 0;
    while ((m = TERM_RE.exec(s)) !== null) {
      var end = m.index + m[0].length;
      var atEnd = end >= s.length;
      var hasWs = /\s$/.test(m[0]);
      // Akışta sonu-metin terminatörü (boşluksuz) belirsiz: «3.» + «14» olabilir → final'e bırak
      if (atEnd && !hasWs && !final) continue;
      if (m[0] === "") {
        TERM_RE.lastIndex++;
        continue;
      }
      ends.push(end);
    }
    if (final && s.length && (!ends.length || ends[ends.length - 1] < s.length)) ends.push(s.length);
    return ends;
  }

  function lastSepCut(s, limit, minLen) {
    var seps = [". ", "! ", "? ", "… ", ", ", "; ", ": ", " — ", " - "];
    var best = -1;
    var bestLen = 0;
    for (var i = 0; i < seps.length; i++) {
      var k = s.lastIndexOf(seps[i], limit);
      if (k >= minLen && k > best) {
        best = k;
        bestLen = seps[i].length;
      }
    }
    if (best >= 0) return best + bestLen;
    var sp = s.lastIndexOf(" ", limit);
    return sp >= minLen ? sp + 1 : -1;
  }

  /**
   * Akış token'larından konuşulacak parçaları çıkarır.
   *   push(text) → [parça…]   (akış sırasında; ilk parça erken)
   *   flush()    → [parça…]   (akış bitti; kalan her şey)
   *   spokenRaw() → ham metinden şimdiye kadar parçaya dönüşen önek
   */
  function createPuller(opts) {
    var c = Object.assign({}, CFG, opts || {});
    var rawAll = "";
    var pending = "";
    var released = 0;
    var spokenChars = 0;
    var capped = false;

    function emit(rawChunk, out) {
      var plain = speechPlain(rawChunk);
      if (plain.length >= 2) {
        if (spokenChars + plain.length > c.MAX_SPEECH_CHARS) {
          capped = true;
          return;
        }
        spokenChars += plain.length;
        released += 1;
        out.push(plain);
      }
    }

    function pull(final) {
      var out = [];
      var guard = 0;
      while (!capped && pending.trim() && guard++ < 200) {
        var isFirst = released === 0;
        var minLen = isFirst ? c.MIN_FIRST_CHARS : c.MIN_QUEUE_CHARS;
        var target = isFirst ? c.FIRST_CHARS : c.MERGE_CHARS;
        var ends = sentenceEnds(pending, final);
        var cut = -1;
        for (var i = 0; i < ends.length; i++) {
          var len = ends[i];
          if (len < minLen) continue;
          if (cut < 0) {
            cut = len;
            if (isFirst) break;
            continue;
          }
          // sonraki cümleyi aynı parçaya kat (hedefi aşmadan, parça yeterince dolmadıysa)
          if (len <= target && cut < Math.floor(target * 0.72)) cut = len;
          else break;
        }
        if (cut < 0 && isFirst && pending.length >= c.EARLY_CHARS) {
          cut = lastSepCut(pending, c.EARLY_CHARS, minLen);
        }
        if (cut < 0 && !isFirst && pending.length >= c.LONG_NO_PUNCT_CHARS) {
          cut = lastSepCut(pending, c.MERGE_CHARS, minLen);
          if (cut < 0) cut = Math.min(pending.length, c.MERGE_CHARS);
        }
        if (cut < 0 && final) {
          cut = pending.length <= c.MERGE_CHARS ? pending.length : lastSepCut(pending, c.MERGE_CHARS, 40);
          if (cut < 0) cut = Math.min(pending.length, c.MERGE_CHARS);
        }
        if (cut < 0) break;
        // Kesim noktası MERGE_CHARS'ı aşıyorsa (tek uzun cümle) böl
        if (cut > c.MERGE_CHARS + 120) {
          var alt = lastSepCut(pending, c.MERGE_CHARS, minLen);
          if (alt > 0) cut = alt;
        }
        var head = pending.slice(0, cut);
        pending = pending.slice(cut);
        emit(head, out);
      }
      return out;
    }

    return {
      push: function (text) {
        var t = String(text == null ? "" : text);
        if (!t) return [];
        rawAll += t;
        pending += t;
        return pull(false);
      },
      flush: function () {
        var out = pull(true);
        pending = "";
        return out;
      },
      reset: function () {
        rawAll = "";
        pending = "";
        released = 0;
        spokenChars = 0;
        capped = false;
      },
      /** Henüz konuşma kuyruğuna girmemiş kısmı değiştir (nihai cevapla hizalama) */
      replaceTail: function (text) {
        var t = String(text == null ? "" : text);
        rawAll = rawAll.slice(0, rawAll.length - pending.length) + t;
        pending = t;
        return pull(false);
      },
      released: function () {
        return released;
      },
      spokenRaw: function () {
        return rawAll.slice(0, rawAll.length - pending.length);
      },
      raw: function () {
        return rawAll;
      },
      pendingLen: function () {
        return pending.length;
      },
    };
  }

  /* -------------------------------------------------------------- tur kilidi */

  function makeAbort() {
    try {
      if (typeof AbortController !== "undefined") return new AbortController();
    } catch (_) {}
    return { signal: { aborted: false }, abort: function () { this.signal.aborted = true; } };
  }

  /**
   * Tur kilidi: aynı anda tek aktif tur. Yeni tur başlayınca eskisi iptal (barge).
   *   cancelSpeech(reason) → yalnız ses (sohbet akışı sürer; V4 «sus» kuralı)
   *   cancelAll(reason)    → ses + akış
   */
  function createTurnLock(opts) {
    var o = opts || {};
    var seq = 0;
    var cur = null;

    function safe(fn, a, b, c) {
      try {
        if (typeof fn === "function") fn(a, b, c);
      } catch (_) {}
    }

    function make() {
      var t = {
        id: newTurnId(),
        n: ++seq,
        t0: nowMs(),
        ttsCancelled: false,
        streamAborted: false,
        reason: "",
        streamCtrl: makeAbort(),
        _l: [],
        onCancel: function (fn) {
          if (t.ttsCancelled) {
            safe(fn, t.reason);
            return function () {};
          }
          t._l.push(fn);
          return function () {
            var i = t._l.indexOf(fn);
            if (i >= 0) t._l.splice(i, 1);
          };
        },
        cancelTts: function (reason) {
          if (t.ttsCancelled) return false;
          t.ttsCancelled = true;
          t.reason = String(reason || "iptal");
          var ls = t._l.splice(0);
          for (var i = 0; i < ls.length; i++) safe(ls[i], t.reason);
          safe(o.onCancel, t, t.reason);
          return true;
        },
        abortStream: function () {
          if (t.streamAborted) return;
          t.streamAborted = true;
          try {
            t.streamCtrl.abort();
          } catch (_) {}
        },
        cancel: function (reason) {
          var a = t.cancelTts(reason);
          t.abortStream();
          return a;
        },
        isActive: function () {
          return cur === t && !t.ttsCancelled;
        },
      };
      return t;
    }

    return {
      begin: function (reason) {
        if (cur) cur.cancel(reason || "yeni_tur");
        cur = make();
        return cur;
      },
      current: function () {
        return cur;
      },
      cancelSpeech: function (reason) {
        return cur ? cur.cancelTts(reason || "barge") : false;
      },
      cancelAll: function (reason) {
        return cur ? cur.cancel(reason || "iptal") : false;
      },
    };
  }

  /* ------------------------------------------------------------- TTS kuyruğu */

  /**
   * Parça kuyruğu: push(text) gelir gelmez sentez başlar; sıra korunur;
   * `ahead` kadar parça önceden hazırlanır (çalarken sonraki sentezlenir).
   *   opts.fetchChunk(text, {signal, index}) → Promise<Blob|null|IPTAL>
   *   opts.play(blob, text, index)           → Promise (bitince/iptalde çözülür)
   *   opts.turn                               → iptal bağı (turn.onCancel)
   */
  function createTtsQueue(opts) {
    var o = opts || {};
    var turn = o.turn || null;
    var ahead = Math.max(1, o.ahead || 1);
    var ctrl = makeAbort();
    var pending = [];
    var inflight = [];
    var finished = false;
    var cancelled = false;
    var running = false;
    var waiter = null;
    var played = 0;
    var skipped = 0;
    var index = 0;
    var doneResolve;
    var done = new Promise(function (r) {
      doneResolve = r;
    });
    var unbind = null;
    var cancelR;
    var cancelP = new Promise(function (r) {
      cancelR = r;
    });

    function wake() {
      if (waiter) {
        var w = waiter;
        waiter = null;
        w();
      }
    }

    function safeFetch(text, idx) {
      var p;
      try {
        p = Promise.resolve(o.fetchChunk(text, { signal: ctrl.signal, index: idx }));
      } catch (e) {
        p = Promise.resolve(null);
      }
      return p.catch(function () {
        return null;
      });
    }

    function fill() {
      while (!cancelled && inflight.length < ahead && pending.length) {
        var t = pending.shift();
        var idx = index++;
        inflight.push({ text: t, idx: idx, p: safeFetch(t, idx) });
      }
    }

    async function loop() {
      if (running) return;
      running = true;
      try {
        while (!cancelled) {
          fill();
          if (!inflight.length) {
            if (finished) break;
            await new Promise(function (r) {
              waiter = r;
            });
            continue;
          }
          var head = inflight.shift();
          var blob = await Promise.race([head.p, cancelP]);
          if (cancelled) break;
          fill(); // çalarken sonraki parçayı sentezle
          if (blob === IPTAL) {
            q.cancel("sunucu_iptal");
            break;
          }
          if (!blob) {
            skipped += 1;
            continue;
          }
          played += 1;
          try {
            // play takılırsa bile iptal kuyruğu serbest bırakır (kaynak sızıntısı yok)
            await Promise.race([Promise.resolve(o.play(blob, head.text, head.idx)), cancelP]);
          } catch (_) {}
        }
      } finally {
        running = false;
        pending.length = 0;
        inflight.length = 0;
        if (unbind) {
          unbind();
          unbind = null;
        }
        doneResolve({ played: played, skipped: skipped, cancelled: cancelled });
      }
    }

    var q = {
      push: function (text) {
        if (cancelled || finished) return false;
        var t = String(text == null ? "" : text);
        if (t.length < 2) return false;
        pending.push(t);
        if (!running) void loop();
        wake();
        return true;
      },
      finish: function () {
        if (finished) return;
        finished = true;
        if (!running) void loop();
        wake();
      },
      cancel: function (reason) {
        if (cancelled) return false;
        cancelled = true;
        try {
          ctrl.abort();
        } catch (_) {}
        cancelR();
        pending.length = 0;
        inflight.length = 0;
        if (typeof o.onCancel === "function") {
          try {
            o.onCancel(reason || "iptal");
          } catch (_) {}
        }
        wake();
        if (!running) {
          if (unbind) {
            unbind();
            unbind = null;
          }
          doneResolve({ played: played, skipped: skipped, cancelled: true });
        }
        return true;
      },
      done: done,
      isCancelled: function () {
        return cancelled;
      },
      isFinished: function () {
        return finished;
      },
      stats: function () {
        return { played: played, skipped: skipped, queued: pending.length, inflight: inflight.length };
      },
    };

    if (turn && typeof turn.onCancel === "function") {
      unbind = turn.onCancel(function (reason) {
        q.cancel(reason);
      });
    }
    return q;
  }

  /* -------------------------------------------------------------------- SSE */

  /** "data: {...}\n\n" bloklarından JSON olayları çıkarır. Kalan yarım blok `rest` olarak döner. */
  function parseSseBuffer(buf, final) {
    var events = [];
    var parts = buf.split(/\r?\n\r?\n/);
    var rest = parts.pop();
    if (final && rest && rest.trim()) {
      parts.push(rest);
      rest = "";
    }
    for (var i = 0; i < parts.length; i++) {
      var lines = parts[i].split(/\r?\n/);
      var data = [];
      for (var j = 0; j < lines.length; j++) {
        var ln = lines[j];
        if (ln.charAt(0) === ":") continue;
        if (ln.slice(0, 5) === "data:") data.push(ln.slice(5).replace(/^ /, ""));
      }
      if (!data.length) continue;
      try {
        events.push(JSON.parse(data.join("\n")));
      } catch (_) {}
    }
    return { events: events, rest: rest || "" };
  }

  function withTimeout(promise, ms, onTimeout) {
    if (!ms || ms <= 0) return promise;
    return new Promise(function (resolve, reject) {
      var tid = setTimeout(function () {
        try {
          onTimeout();
        } catch (_) {}
        reject(new Error("sse_idle"));
      }, ms);
      promise.then(
        function (v) {
          clearTimeout(tid);
          resolve(v);
        },
        function (e) {
          clearTimeout(tid);
          reject(e);
        },
      );
    });
  }

  /**
   * /api/chat/stream akışını olay olay okur.
   *   onEvent(obj) → true dönerse okuma erken biter (done sonrası)
   */
  async function readSse(res, onEvent, opts) {
    var o = opts || {};
    var dec = typeof TextDecoder !== "undefined" ? new TextDecoder("utf-8") : null;
    if (!res.body || !res.body.getReader) {
      var txt = await res.text();
      var pr = parseSseBuffer(txt, true);
      for (var i = 0; i < pr.events.length; i++) if (onEvent(pr.events[i])) break;
      return { events: pr.events.length, noStream: true };
    }
    var reader = res.body.getReader();
    var buf = "";
    var n = 0;
    var stop = false;
    try {
      while (!stop) {
        var idle = typeof o.idleMs === "function" ? o.idleMs() : o.idleMs;
        var chunk = await withTimeout(reader.read(), idle, function () {
          try {
            reader.cancel();
          } catch (_) {}
        });
        if (chunk.done) {
          if (dec) buf += dec.decode();
          var tail = parseSseBuffer(buf, true);
          for (var a = 0; a < tail.events.length; a++) {
            n++;
            if (onEvent(tail.events[a])) break;
          }
          break;
        }
        var v = chunk.value;
        buf += typeof v === "string" ? v : dec ? dec.decode(v, { stream: true }) : String(v);
        var pe = parseSseBuffer(buf, false);
        buf = pe.rest;
        for (var k = 0; k < pe.events.length; k++) {
          n++;
          if (onEvent(pe.events[k])) {
            stop = true;
            break;
          }
        }
      }
    } finally {
      try {
        if (stop) await reader.cancel();
      } catch (_) {}
      try {
        reader.releaseLock && reader.releaseLock();
      } catch (_) {}
    }
    return { events: n };
  }

  /**
   * Sohbet turunu SSE ile yürüt.
   * Dönüş: { ok, full, done, error, authError, code, httpStatus, tokens, firstTokenMs,
   *          aborted, networkError, broke, fallback }
   *   fallback=true → hiç token gelmedi ve kimlik hatası yok: /api/chat/full yedeğine geç
   */
  async function streamTurn(o) {
    var f = o.fetchImpl || (typeof fetch !== "undefined" ? fetch : null);
    var t0 = o.t0 != null ? o.t0 : nowMs();
    var r = {
      ok: false,
      full: "",
      done: null,
      error: null,
      authError: false,
      code: "",
      httpStatus: 0,
      tokens: 0,
      firstTokenMs: null,
      aborted: false,
      networkError: null,
      broke: false,
      fallback: false,
    };
    if (!f) {
      r.networkError = "fetch_yok";
      r.fallback = true;
      return r;
    }
    var headers = Object.assign({ "Content-Type": "application/json" }, o.headers || {});
    var res;
    try {
      res = await f(o.url, {
        method: "POST",
        headers: headers,
        body: JSON.stringify(o.body || {}),
        signal: o.signal,
      });
    } catch (e) {
      r.aborted = !!(e && e.name === "AbortError") || !!(o.signal && o.signal.aborted);
      r.networkError = String((e && e.message) || e || "ag");
      r.fallback = !r.aborted;
      return r;
    }
    r.httpStatus = res.status || 0;
    if (!res.ok) {
      if (res.status === 401 || res.status === 403) {
        r.authError = true;
        r.code = "http_" + res.status;
        r.error = "Oturum geçersiz veya süresi dolmuş. PWA'dan tekrar giriş.";
      } else {
        r.networkError = "http_" + res.status;
        r.fallback = true;
      }
      return r;
    }
    var ct = "";
    try {
      ct = (res.headers && res.headers.get && res.headers.get("content-type")) || "";
    } catch (_) {}
    if (ct && ct.indexOf("text/event-stream") < 0 && ct.indexOf("json") >= 0) {
      // Akış yerine düz JSON döndü (ara katman): yedeğe düş
      r.networkError = "akis_degil";
      r.fallback = true;
      return r;
    }
    var gotDone = false;
    try {
      await readSse(
        res,
        function (ev) {
          if (!ev || typeof ev !== "object") return false;
          if (ev.type === "token" && ev.text) {
            if (r.tokens === 0) r.firstTokenMs = Math.round(nowMs() - t0);
            r.tokens += 1;
            r.full += ev.text;
            if (o.onToken) o.onToken(ev.text, r.full, ev);
          } else if (ev.type === "status") {
            if (o.onStatus) o.onStatus(ev);
          } else if (ev.type === "meta") {
            if (o.onMeta) o.onMeta(ev);
          } else if (ev.type === "error") {
            r.error = String(ev.text || "Bilinmeyen hata");
            if (ev.auth_error) {
              r.authError = true;
              r.code = String(ev.code || "oturum_gecersiz");
            }
            if (o.onError) o.onError(ev);
          } else if (ev.type === "done") {
            gotDone = true;
            r.done = ev;
            if (ev.auth_error) {
              r.authError = true;
              r.code = String(ev.code || r.code || "oturum_gecersiz");
            }
            if (r.firstTokenMs == null && String(ev.full_reply || "").trim() && !ev.auth_error && !ev.stream_error) {
              r.firstTokenMs = Math.round(nowMs() - t0);
            }
            if (o.onDone) o.onDone(ev);
            return true; // akışı kapat
          }
          return false;
        },
        {
          idleMs: function () {
            var base = r.tokens > 0 ? CFG.SSE_IDLE_AFTER_TOKEN_MS : CFG.SSE_IDLE_MS;
            return o.idleMs != null ? o.idleMs : base;
          },
        },
      );
    } catch (e) {
      r.aborted = !!(e && e.name === "AbortError") || !!(o.signal && o.signal.aborted);
      r.networkError = String((e && e.message) || e || "akis");
    }
    r.broke = !gotDone && !r.error && !r.aborted;
    r.fallback = !r.authError && !r.aborted && r.tokens === 0 && !gotDone && !r.error;
    r.ok = gotDone && !r.authError && !(r.done && r.done.stream_error);
    return r;
  }

  /* ----------------------------------------------------------------- oturum */

  /**
   * Tek sohbet turu: akış + cümle çekici + TTS kuyruğu + telemetri.
   *  o.turn, o.url, o.body, o.headers, o.fetchImpl
   *  o.speak (varsayılan true), o.ttsFetch(text,{signal,index}), o.ttsPlay(blob,text,idx,ctx)
   *  o.onToken(text, full) · o.onStatus · o.onMeta · o.onFirstAudio(ms, path)
   *  o.postTelemetry(rec)
   *  Dönüş: { stream, finalText, spoken, ttsDone, corrected, telemetry }
   */
  function createSession(o) {
    var turn = o.turn;
    var t0 = o.t0 != null ? o.t0 : nowMs();
    var speak = o.speak !== false && typeof o.ttsFetch === "function" && typeof o.ttsPlay === "function";
    var puller = createPuller(o.pullerOpts);
    var st = { firstTokenMs: null, firstAudioMs: null, firstAudioPath: null, chunks: 0, corrected: false, cancelled: false };
    var queue = null;
    var telemetrySent = false;
    var ctx = {
      turn: turn,
      markFirstAudio: function (path) {
        if (st.firstAudioMs != null) return;
        st.firstAudioMs = Math.round(nowMs() - t0);
        st.firstAudioPath = path || "blob";
        if (o.onFirstAudio) {
          try {
            o.onFirstAudio(st.firstAudioMs, st.firstAudioPath);
          } catch (_) {}
        }
      },
    };

    function newQueue() {
      return createTtsQueue({
        turn: turn,
        ahead: o.ahead || 1,
        fetchChunk: o.ttsFetch,
        play: function (blob, text, idx) {
          return o.ttsPlay(blob, text, idx, ctx);
        },
        onCancel: function (reason) {
          st.cancelled = true;
          if (o.onQueueCancel) o.onQueueCancel(reason);
        },
      });
    }

    function enqueue(chunks) {
      if (!speak || !chunks || !chunks.length) return;
      if (turn && turn.ttsCancelled) return;
      if (!queue) queue = newQueue();
      for (var i = 0; i < chunks.length; i++) {
        if (typeof o.skipChunk === "function" && o.skipChunk(chunks[i])) continue;
        if (queue.push(chunks[i])) {
          st.chunks += 1;
          if (st.chunks === 1 && o.onFirstChunk) {
            try {
              o.onFirstChunk(chunks[i]);
            } catch (_) {}
          }
        }
      }
    }

    function sendTelemetry(extra) {
      if (telemetrySent || !o.postTelemetry) return null;
      telemetrySent = true;
      var rec = Object.assign(
        {
          turn_id: turn && turn.id,
          ilk_token_ms: st.firstTokenMs,
          ilk_ses_ms: st.firstAudioMs,
          ilk_ses_yolu: st.firstAudioPath,
          parca: st.chunks,
          iptal: !!st.cancelled,
        },
        extra || {},
      );
      try {
        o.postTelemetry(rec);
      } catch (_) {}
      return rec;
    }

    async function run() {
      var stream;
      try {
        stream = await streamTurn({
          url: o.url,
          body: o.body,
          headers: o.headers,
          fetchImpl: o.fetchImpl,
          signal: turn && turn.streamCtrl ? turn.streamCtrl.signal : o.signal,
          t0: t0,
          idleMs: o.idleMs,
          onToken: function (text, full, ev) {
            if (st.firstTokenMs == null) st.firstTokenMs = Math.round(nowMs() - t0);
            if (speak) enqueue(puller.push(text));
            if (o.onToken) o.onToken(text, full, ev);
          },
          onStatus: o.onStatus,
          onMeta: o.onMeta,
          onError: o.onError,
          onDone: o.onDone,
        });
      } catch (e) {
        stream = { ok: false, full: "", done: null, error: String((e && e.message) || e), fallback: true };
      }
      if (stream.firstTokenMs != null && st.firstTokenMs == null) st.firstTokenMs = stream.firstTokenMs;

      var done = stream.done;
      var bad = !!(stream.authError || (done && (done.auth_error || done.stream_error)));
      var finalText = "";
      if (!bad) finalText = String((done && done.full_reply) || "").trim() || String(stream.full || "").trim();
      var corrected = false;

      if (speak && !bad && finalText && !(turn && turn.ttsCancelled)) {
        var spokenRaw = puller.spokenRaw();
        if (prefixConsistent(spokenRaw, finalText)) {
          // Normal: kuyruğa girmiş önek nihai cevapla uyumlu → kalan kısım nihai cevaptan alınır
          // (akışta görülmeyen alt bilgi / hızlı şerit tek parça cevap / sonradan kırpılan kuyruk)
          var tail;
          if (finalText.indexOf(spokenRaw) === 0) tail = finalText.slice(spokenRaw.length);
          else tail = collapseWs(finalText).slice(collapseWs(spokenRaw).length);
          enqueue(puller.replaceTail(tail));
          enqueue(puller.flush());
        } else if (puller.released() === 0) {
          // Henüz hiçbir şey konuşma kuyruğuna girmedi: temiz başla
          puller.reset();
          puller.push(finalText);
          enqueue(puller.flush());
          corrected = true;
        } else {
          // Model cevabı sonradan değiştirdi: eski parçalar durur, düzeltilmiş cevap baştan
          corrected = true;
          st.corrected = true;
          if (queue) queue.cancel("duzeltme");
          queue = null;
          st.cancelled = false;
          puller.reset();
          puller.push(finalText);
          enqueue(puller.flush());
        }
      } else if (speak && bad && queue) {
        // Hata/kimlik reddi: söylenmekte olan parçalar varsa sustur
        queue.cancel("hata");
      }
      if (queue) queue.finish();

      var ttsDone = queue
        ? queue.done.then(function (r) {
            sendTelemetry();
            return r;
          })
        : Promise.resolve({ played: 0, skipped: 0, cancelled: false }).then(function (r) {
            sendTelemetry();
            return r;
          });

      return {
        stream: stream,
        finalText: finalText,
        spoken: st.chunks,
        ttsDone: ttsDone,
        corrected: corrected,
        state: st,
      };
    }

    return {
      run: run,
      ctx: ctx,
      state: st,
      cancelTts: function (reason) {
        if (turn) turn.cancelTts(reason || "barge");
        else if (queue) queue.cancel(reason || "barge");
      },
      getQueue: function () {
        return queue;
      },
    };
  }

  return {
    VERSION: VERSION,
    CFG: CFG,
    IPTAL: IPTAL,
    newTurnId: newTurnId,
    speechPlain: speechPlain,
    prefixConsistent: prefixConsistent,
    createPuller: createPuller,
    createTurnLock: createTurnLock,
    createTtsQueue: createTtsQueue,
    parseSseBuffer: parseSseBuffer,
    readSse: readSse,
    streamTurn: streamTurn,
    createSession: createSession,
  };
});
