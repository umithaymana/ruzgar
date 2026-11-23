/* node ruzgar-tur-ses.test.js — Madde 2 ortak tur/ses mantığı testleri (ağ yok) */
const assert = require("assert");
const T = require("./ruzgar-tur-ses.js");

const enc = new TextEncoder();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** Sahte fetch yanıtı: parçaları sırayla (isteğe bağlı gecikmeyle) verir */
function fakeRes(parts, { status = 200, ct = "text/event-stream; charset=utf-8", delay = 0, hang = false, signal = null } = {}) {
  let i = 0;
  let cancelled = false;
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: { get: (k) => (k.toLowerCase() === "content-type" ? ct : null) },
    _cancelled: () => cancelled,
    body: {
      getReader() {
        return {
          async read() {
            if (cancelled) return { done: true };
            if (i >= parts.length) {
              if (hang)
                return new Promise((_, rej) => {
                  if (signal) {
                    const fire = () => {
                      const e = new Error("abort");
                      e.name = "AbortError";
                      rej(e);
                    };
                    if (signal.aborted) fire();
                    else signal.addEventListener("abort", fire);
                  }
                });
              return { done: true };
            }
            if (delay) await sleep(delay);
            const p = parts[i++];
            return { done: false, value: typeof p === "string" ? enc.encode(p) : p };
          },
          async cancel() {
            cancelled = true;
          },
          releaseLock() {},
        };
      },
    },
  };
}
const ev = (o) => "data: " + JSON.stringify(o) + "\n\n";
const tok = (t) => ev({ type: "token", text: t });
const done = (full, x) => ev(Object.assign({ type: "done", full_reply: full }, x || {}));

async function main() {
  let n = 0;
  const ok = (name) => {
    n++;
    console.log("ok -", name);
  };

  // ---------------------------------------------------------------- metin
  assert.strictEqual(T.speechPlain("**Merhaba** *abi* https://x.y/z\n\n# Başlık"), "Merhaba abi Başlık");
  assert.strictEqual(T.speechPlain("[korku] Dikkat!"), "[korku] Dikkat!"); // etiket korunur
  assert.strictEqual(T.speechPlain("```js\nx=1\n```"), "");
  assert.ok(T.prefixConsistent("Merhaba  dünya", "Merhaba dünya, nasılsın?"));
  assert.ok(T.prefixConsistent("", "x"));
  assert.ok(!T.prefixConsistent("Merhaba dünya", "Selam dünya"));
  ok("metin/prefix");

  // ---------------------------------------------------------------- SSE ayrıştırma
  let pr = T.parseSseBuffer(':ruzgar-events\n\n' + tok("a") + 'data: {"type":"tok', false);
  assert.strictEqual(pr.events.length, 1);
  assert.ok(pr.rest.startsWith('data: {"type":"tok'));
  pr = T.parseSseBuffer(tok("é") + done("bitti"), false);
  assert.deepStrictEqual(pr.events.map((e) => e.type), ["token", "done"]);
  pr = T.parseSseBuffer("data: bozuk\n\n" + tok("x"), false);
  assert.strictEqual(pr.events.length, 1);
  ok("sse ayrıştırma");

  // ---------------------------------------------------------------- çekici
  {
    const p = T.createPuller();
    const out = [];
    const text =
      "Merhaba Ümit abi, bugün hava gayet güzel görünüyor. Dışarı çıkıp biraz yürüyüş yapmak iyi gelir. " +
      "Akşama doğru yağmur bekleniyor, yanına bir şemsiye almayı unutma. Sağlıkla kal.";
    // token token (5'er karakter)
    for (let i = 0; i < text.length; i += 5) out.push(...p.push(text.slice(i, i + 5)));
    // İlk parça erken çıkmalı (tüm metin gelmeden)
    assert.ok(out.length >= 1, "ilk parça akış sırasında çıktı");
    assert.ok(out[0].length >= 28 && out[0].length <= 140, "ilk parça kısa: " + out[0].length);
    assert.ok(/[.!?]$/.test(out[0]), "ilk parça cümle sonunda biter: " + out[0]);
    const rest = p.flush();
    const all = [...out, ...rest].join(" ");
    assert.strictEqual(all.replace(/\s+/g, " "), text.replace(/\s+/g, " "));
    ok("çekici: erken ilk parça + kayıpsız");
  }
  {
    // Ondalık sayı / kısaltma bölünmez; sonu-metin terminatörü akışta beklenir
    const p = T.createPuller();
    assert.deepStrictEqual(p.push("Pi sayısı yaklaşık 3.14 olarak bilinir ve çok kullanılır bu alanda"), []);
    const p2 = T.createPuller();
    assert.deepStrictEqual(p2.push("Bu cümle yeterince uzun ve bitiyor."), []); // sonu boşluksuz → bekle
    const out = p2.push(" Sonraki");
    assert.strictEqual(out.length, 1);
    assert.strictEqual(out[0], "Bu cümle yeterince uzun ve bitiyor.");
    ok("çekici: 3.14 ve sonu-boşluksuz terminatör");
  }
  {
    // Noktasız uzun akış: erken kesim ilk parçada, uzun-noktasız sonrakilerde
    const p = T.createPuller();
    const words = "kelime ".repeat(40);
    const got = p.push(words);
    assert.ok(got.length >= 1 && got[0].length <= 90, "noktasız ilk parça erken kesildi");
    const all = (got.join(" ") + " " + p.flush().join(" ")).split(/\s+/).filter(Boolean).length;
    assert.strictEqual(all, 40);
    ok("çekici: noktasız metin takılmaz");
  }
  {
    // kısa ilk cümle sonraki cümlelerle birleşir, takılmaz
    const p = T.createPuller();
    const out = p.push("Evet. Bunu sana şöyle açıklayayım sevgili dostum, dinle. Başka");
    assert.ok(out.length === 1 && out[0].startsWith("Evet. Bunu"), JSON.stringify(out));
    ok("çekici: kısa ilk cümle takılmaz");
  }
  {
    const p = T.createPuller();
    const long = ("Bu uzun bir cümledir. ".repeat(300)).trim();
    const out = [...p.push(long), ...p.flush()];
    const total = out.join(" ").length;
    assert.ok(total <= T.CFG.MAX_SPEECH_CHARS + 50, "tavan uygulandı: " + total);
    ok("çekici: konuşma tavanı");
  }
  {
    const p = T.createPuller();
    p.push("Merhaba dünya, bu bir deneme cümlesidir. Devam");
    const spoken = p.spokenRaw();
    assert.ok(spoken.startsWith("Merhaba dünya"));
    p.replaceTail("Devam ediyoruz şimdi.");
    assert.strictEqual(p.raw(), spoken + "Devam ediyoruz şimdi.");
    ok("çekici: replaceTail/spokenRaw");
  }

  // ---------------------------------------------------------------- tur kilidi
  {
    const lock = T.createTurnLock();
    const a = lock.begin();
    let aCancelled = "";
    a.onCancel((r) => (aCancelled = r));
    const b = lock.begin();
    assert.strictEqual(aCancelled, "yeni_tur");
    assert.ok(a.ttsCancelled && a.streamAborted && !b.ttsCancelled);
    assert.ok(a.streamCtrl.signal.aborted && !b.streamCtrl.signal.aborted);
    assert.notStrictEqual(a.id, b.id);
    assert.ok(lock.cancelSpeech("barge"));
    assert.ok(b.ttsCancelled && !b.streamAborted, "barge yalnız sesi keser, akışı değil");
    assert.ok(!lock.cancelSpeech("barge"), "ikinci iptal no-op");
    // iptalden sonra kaydolan dinleyici hemen çağrılır
    let late = "";
    b.onCancel((r) => (late = r));
    assert.strictEqual(late, "barge");
    ok("tur kilidi");
  }

  // ---------------------------------------------------------------- TTS kuyruğu
  {
    // sıra korunur, ilk parça çalarken sonraki sentezlenir (prefetch), play sırayla
    const log = [];
    const lock = T.createTurnLock();
    const turn = lock.begin();
    const q = T.createTtsQueue({
      turn,
      ahead: 1,
      fetchChunk: async (t, { index }) => {
        log.push("fetch" + index);
        await sleep(index === 0 ? 30 : 5);
        return { t };
      },
      play: async (blob, t, idx) => {
        log.push("play" + idx + ":start");
        await sleep(40);
        log.push("play" + idx + ":end");
      },
    });
    q.push("Birinci parça burada.");
    q.push("İkinci parça burada.");
    q.push("Üçüncü parça burada.");
    q.finish();
    const r = await q.done;
    assert.strictEqual(r.played, 3);
    const order = log.filter((l) => l.startsWith("play") && l.endsWith("start"));
    assert.deepStrictEqual(order, ["play0:start", "play1:start", "play2:start"]);
    // prefetch: fetch1, play0 bitmeden başlamış olmalı
    assert.ok(log.indexOf("fetch1") < log.indexOf("play0:end"), log.join(","));
    ok("kuyruk: sıra + prefetch");
  }
  {
    // metin akarken ilk parça push edilir edilmez fetch başlar (bitiş beklenmez)
    const lock = T.createTurnLock();
    const turn = lock.begin();
    let fetched = 0;
    const q = T.createTtsQueue({
      turn,
      fetchChunk: async () => {
        fetched++;
        return {};
      },
      play: async () => {},
    });
    q.push("Hemen sentezlenmeli parça.");
    await sleep(5);
    assert.strictEqual(fetched, 1, "finish() beklemeden fetch başladı");
    q.finish();
    await q.done;
    ok("kuyruk: finish beklemeden sentez");
  }
  {
    // iptal: bekleyen/hazırlanan parçalar çalınmaz, çalan play serbest kalır (sızıntı yok), fetch abort
    const lock = T.createTurnLock();
    const turn = lock.begin();
    const played = [];
    let aborted = false;
    const q = T.createTtsQueue({
      turn,
      ahead: 2,
      fetchChunk: async (t, { signal }) => {
        signal.addEventListener && signal.addEventListener("abort", () => (aborted = true));
        await sleep(10);
        return {};
      },
      play: (b, t, idx) =>
        new Promise((res) => {
          played.push(idx);
          /* asla bitmeyen play (takılı ses) */
        }),
    });
    q.push("Parça bir burada yazıyor.");
    q.push("Parça iki burada yazıyor.");
    q.push("Parça üç burada yazıyor.");
    await sleep(40);
    assert.deepStrictEqual(played, [0]);
    lock.cancelSpeech("barge");
    const r = await Promise.race([q.done, sleep(300).then(() => "ASILI")]);
    assert.notStrictEqual(r, "ASILI", "takılı play iptalde serbest bırakıldı");
    assert.ok(r.cancelled);
    assert.ok(aborted, "devam eden sentez abort edildi");
    assert.deepStrictEqual(played, [0], "eski parçalar çalınmadı");
    assert.strictEqual(q.push("geç gelen parça"), false);
    ok("kuyruk: barge iptali sızıntısız");
  }
  {
    // yeni tur eski turun kuyruğunu keser; eski ses yeni cevaba binmez
    const lock = T.createTurnLock();
    const t1 = lock.begin();
    const played = [];
    const q1 = T.createTtsQueue({
      turn: t1,
      fetchChunk: async (t) => {
        await sleep(20);
        return { t };
      },
      play: async (b) => {
        played.push("eski:" + b.t);
        await sleep(30);
      },
    });
    q1.push("Eski turun birinci parçası.");
    q1.push("Eski turun ikinci parçası.");
    const t2 = lock.begin(); // yeni tur
    const q2 = T.createTtsQueue({
      turn: t2,
      fetchChunk: async (t) => ({ t }),
      play: async (b) => {
        played.push("yeni:" + b.t);
      },
    });
    q2.push("Yeni cevap burada.");
    q2.finish();
    await Promise.all([q1.done, q2.done]);
    assert.deepStrictEqual(played, ["yeni:Yeni cevap burada."]);
    ok("kuyruk: yeni tur eski sesi keser");
  }
  {
    // sunucu iptali (IPTAL) kuyruğu durdurur
    const lock = T.createTurnLock();
    const turn = lock.begin();
    const played = [];
    const q = T.createTtsQueue({
      turn,
      fetchChunk: async (t, { index }) => (index === 1 ? T.IPTAL : {}),
      play: async (b, t, idx) => played.push(idx),
    });
    ["Bir burada yazıyor.", "İki burada yazıyor.", "Üç burada yazıyor."].forEach((s) => q.push(s));
    q.finish();
    const r = await q.done;
    assert.ok(r.cancelled);
    assert.deepStrictEqual(played, [0]);
    ok("kuyruk: sunucu iptali");
  }
  {
    // fetch hatası (null/throw) parçayı atlar, kuyruk devam eder
    const lock = T.createTurnLock();
    const turn = lock.begin();
    const played = [];
    const q = T.createTtsQueue({
      turn,
      fetchChunk: async (t, { index }) => {
        if (index === 0) throw new Error("ağ");
        if (index === 1) return null;
        return {};
      },
      play: async (b, t, idx) => played.push(idx),
    });
    ["Bir burada yazıyor.", "İki burada yazıyor.", "Üç burada yazıyor."].forEach((s) => q.push(s));
    q.finish();
    const r = await q.done;
    assert.deepStrictEqual(played, [2]);
    assert.strictEqual(r.skipped, 2);
    ok("kuyruk: hata atlar");
  }
  {
    // hiç push yok + finish → done çözülür (asılı kalmaz)
    const q = T.createTtsQueue({ fetchChunk: async () => ({}), play: async () => {} });
    q.finish();
    const r = await Promise.race([q.done, sleep(200).then(() => "ASILI")]);
    assert.notStrictEqual(r, "ASILI");
    ok("kuyruk: boş finish");
  }

  // ---------------------------------------------------------------- streamTurn
  {
    const res = fakeRes([":ruzgar-events\n\n", tok("Merhaba "), tok("dünya."), done("Merhaba dünya.")]);
    const fetchImpl = async (url, init) => {
      assert.strictEqual(url, "/api/chat/stream");
      assert.strictEqual(init.method, "POST");
      assert.strictEqual(init.headers.Authorization, "Bearer abc");
      const b = JSON.parse(init.body);
      assert.strictEqual(b.device_id, "dev1");
      return res;
    };
    const toks = [];
    const r = await T.streamTurn({
      url: "/api/chat/stream",
      fetchImpl,
      headers: { Authorization: "Bearer abc" },
      body: { message: "x", device_id: "dev1" },
      onToken: (t, full) => toks.push(full),
    });
    assert.ok(r.ok && r.tokens === 2 && r.full === "Merhaba dünya." && r.done.full_reply === "Merhaba dünya.");
    assert.deepStrictEqual(toks, ["Merhaba ", "Merhaba dünya."]);
    assert.ok(r.firstTokenMs != null);
    assert.ok(!r.fallback);
    ok("streamTurn: normal akış");
  }
  {
    // parça sınırları ortasında bölünmüş (UTF-8 çok baytlı karakter dâhil) akış
    const bytes = enc.encode(tok("Şöyle güzel ğüşiöç.") + done("Şöyle güzel ğüşiöç."));
    const parts = [];
    for (let i = 0; i < bytes.length; i += 7) parts.push(bytes.slice(i, i + 7));
    const r = await T.streamTurn({ url: "/s", fetchImpl: async () => fakeRes(parts), body: {} });
    assert.strictEqual(r.full, "Şöyle güzel ğüşiöç.");
    assert.ok(r.ok);
    ok("streamTurn: bölünmüş UTF-8");
  }
  {
    // auth_error (error + done)
    const res = fakeRes([
      ev({ type: "error", text: "Oturum geçersiz.", code: "oturum_gecersiz", auth_error: true }),
      done("Oturum geçersiz.", { stream_error: true, auth_error: true, code: "oturum_gecersiz" }),
    ]);
    const r = await T.streamTurn({ url: "/s", fetchImpl: async () => res, body: {} });
    assert.ok(r.authError && !r.ok && !r.fallback);
    assert.strictEqual(r.code, "oturum_gecersiz");
    assert.strictEqual(r.tokens, 0);
    ok("streamTurn: auth_error");
  }
  {
    // HTTP 401 → authError (yedek yol denenmez)
    const r = await T.streamTurn({ url: "/s", fetchImpl: async () => fakeRes([], { status: 401 }), body: {} });
    assert.ok(r.authError && !r.fallback);
    // HTTP 500 → yedek
    const r2 = await T.streamTurn({ url: "/s", fetchImpl: async () => fakeRes([], { status: 500 }), body: {} });
    assert.ok(!r2.authError && r2.fallback);
    // ağ hatası → yedek
    const r3 = await T.streamTurn({
      url: "/s",
      fetchImpl: async () => {
        throw new TypeError("Failed to fetch");
      },
      body: {},
    });
    assert.ok(r3.fallback && !r3.aborted);
    // düz JSON (akış değil) → yedek
    const r4 = await T.streamTurn({ url: "/s", fetchImpl: async () => fakeRes(['{"ok":1}'], { ct: "application/json" }), body: {} });
    assert.ok(r4.fallback);
    ok("streamTurn: HTTP/ağ hataları");
  }
  {
    // akış ortasında kopma: token var → yedek YOK (çift işlem olmasın), broke=true
    const r = await T.streamTurn({
      url: "/s",
      fetchImpl: async () => fakeRes([tok("Yarım "), tok("cevap")]),
      body: {},
    });
    assert.ok(r.broke && !r.fallback && !r.ok && r.full === "Yarım cevap");
    // hiç token yok, done yok → yedek
    const r2 = await T.streamTurn({ url: "/s", fetchImpl: async () => fakeRes([":x\n\n"]), body: {} });
    assert.ok(r2.fallback && r2.broke);
    ok("streamTurn: kopma");
  }
  {
    // takılan akış (idle) → kesilir, bağlantı iptal edilir
    const res = fakeRes([tok("Başladı ")], { hang: true });
    const t0 = Date.now();
    const r = await T.streamTurn({ url: "/s", fetchImpl: async () => res, body: {}, idleMs: 80 });
    assert.ok(Date.now() - t0 < 1000);
    assert.ok(res._cancelled(), "okuyucu iptal edildi");
    assert.ok(!r.ok && r.networkError === "sse_idle" && r.tokens === 1 && !r.fallback);
    ok("streamTurn: idle zaman aşımı");
  }
  {
    // abort sinyali
    const ctrl = new AbortController();
    const r = await T.streamTurn({
      url: "/s",
      signal: ctrl.signal,
      fetchImpl: async (u, init) => {
        ctrl.abort();
        const e = new Error("abort");
        e.name = "AbortError";
        throw e;
      },
      body: {},
    });
    assert.ok(r.aborted && !r.fallback);
    ok("streamTurn: abort");
  }
  {
    // done sonrası akış kapatılır (okuyucu iptal)
    const res = fakeRes([tok("a b c. "), done("a b c."), tok("SIZINTI")]);
    const r = await T.streamTurn({ url: "/s", fetchImpl: async () => res, body: {} });
    assert.ok(r.ok && r.full === "a b c. ");
    assert.ok(res._cancelled());
    ok("streamTurn: done sonrası kapanış");
  }

  // ---------------------------------------------------------------- oturum
  function mkSession(streamParts, extra) {
    const lock = extra && extra.lock ? extra.lock : T.createTurnLock();
    const turn = lock.begin();
    const log = { fetched: [], played: [], telemetry: [], firstAudio: null, tokens: [] };
    let clock = 0;
    const sess = T.createSession(
      Object.assign(
        {
          turn,
          url: "/api/chat/stream",
          body: { message: "m", turn_id: turn.id },
          fetchImpl: async (u, init) => fakeRes(streamParts, Object.assign({ signal: init && init.signal }, (extra && extra.res) || {})),
          ttsFetch: async (t) => {
            log.fetched.push(t);
            await sleep(3);
            return { t };
          },
          ttsPlay: async (blob, t, idx, ctx) => {
            ctx.markFirstAudio("blob");
            log.played.push(t);
            await sleep(5);
          },
          onToken: (t, full) => log.tokens.push(full),
          onFirstAudio: (ms, path) => (log.firstAudio = { ms, path }),
          postTelemetry: (rec) => log.telemetry.push(rec),
        },
        (extra && extra.opts) || {},
      ),
    );
    return { sess, turn, log, lock };
  }
  {
    // metin akarken ses başlar; tam cevap gelmeden ilk parça çalınır
    const full = "Merhaba Ümit abi, bugün hava gayet güzel görünüyor. Dışarı çıkıp yürümek iyi gelir. Sağlıkla kal.";
    const parts = [":ruzgar-events\n\n"];
    for (let i = 0; i < full.length; i += 8) parts.push(tok(full.slice(i, i + 8)));
    parts.push(done(full));
    const { sess, log } = mkSession(parts, { res: { delay: 4 } });
    const res = await sess.run();
    // stream bitince ttsDone henüz çözülmemiş olabilir; ilk parça stream bitmeden sentezlenmeye başlamış olmalı
    await res.ttsDone;
    assert.ok(res.stream.ok);
    assert.strictEqual(log.played.join(" "), full);
    assert.ok(log.telemetry.length === 1);
    const tel = log.telemetry[0];
    assert.ok(tel.ilk_token_ms != null && tel.ilk_ses_ms != null);
    assert.ok(tel.ilk_ses_ms >= tel.ilk_token_ms, "duyulan ilk ses ilk token'dan önce olamaz");
    assert.strictEqual(tel.ilk_ses_yolu, "blob");
    assert.strictEqual(tel.iptal, false);
    assert.ok(tel.parca >= 2);
    assert.ok(log.firstAudio && log.firstAudio.ms === tel.ilk_ses_ms);
    ok("oturum: akarken konuşur + telemetri ayrı");
  }
  {
    // ses, tam metin bitmeden BAŞLAR (akış 'hang' benzeri: done gecikmeli)
    const first = "Bu ilk cümle akış sırasında seslendirilmeli. ";
    const parts = [tok(first), tok("İkinci cümle de gelecek ")];
    let releaseDone;
    const gate = new Promise((r) => (releaseDone = r));
    const res = {
      ok: true,
      status: 200,
      headers: { get: () => "text/event-stream" },
      body: {
        getReader() {
          let i = 0;
          return {
            async read() {
              if (i < parts.length) return { done: false, value: enc.encode(parts[i++]) };
              if (i === parts.length) {
                i++;
                await gate;
                return { done: false, value: enc.encode(done(first + "İkinci cümle de gelecek sonunda.")) };
              }
              return { done: true };
            },
            async cancel() {},
            releaseLock() {},
          };
        },
      },
    };
    const lock = T.createTurnLock();
    const turn = lock.begin();
    const played = [];
    const sess = T.createSession({
      turn,
      url: "/s",
      body: {},
      fetchImpl: async () => res,
      ttsFetch: async (t) => ({ t }),
      ttsPlay: async (b, t, idx, ctx) => {
        ctx.markFirstAudio("blob");
        played.push(t);
      },
    });
    const runP = sess.run();
    await sleep(40);
    assert.ok(played.length >= 1 && played[0].startsWith("Bu ilk cümle"), "metin bitmeden ses başladı: " + JSON.stringify(played));
    releaseDone();
    const r = await runP;
    await r.ttsDone;
    assert.strictEqual(played.join(" "), "Bu ilk cümle akış sırasında seslendirilmeli. İkinci cümle de gelecek sonunda.");
    ok("oturum: tam metin beklenmeden ses");
  }
  {
    // hızlı şerit: token yok, yalnız done.full_reply → konuşulur
    const { sess, log } = mkSession([done("Hızlı şerit cevabı tek parça geldi.")]);
    const r = await sess.run();
    await r.ttsDone;
    assert.deepStrictEqual(log.played, ["Hızlı şerit cevabı tek parça geldi."]);
    ok("oturum: yalnız done");
  }
  {
    // auth_error: ses YOK, kuyruk yok
    const { sess, log } = mkSession([
      ev({ type: "error", text: "Oturum geçersiz.", code: "oturum_gecersiz", auth_error: true }),
      done("Oturum geçersiz.", { stream_error: true, auth_error: true }),
    ]);
    const r = await sess.run();
    await r.ttsDone;
    assert.ok(r.stream.authError);
    assert.strictEqual(log.played.length, 0);
    assert.strictEqual(log.fetched.length, 0);
    assert.strictEqual(r.finalText, "");
    ok("oturum: auth_error sessiz");
  }
  {
    // model cevabı sonradan düzeltir: eski parça çalınmaz/kesilir, düzeltilmiş cevap baştan
    const first = "Eski cevabın ilk cümlesi burada duruyor. ";
    const parts = [tok(first), tok("Eski ikinci ")];
    const corrected = "Düzeltilmiş cevap tamamen farklı bir şey söylüyor.";
    parts.push(done(corrected));
    const played = [];
    const lock = T.createTurnLock();
    const turn = lock.begin();
    const sess = T.createSession({
      turn,
      url: "/s",
      body: {},
      fetchImpl: async () => fakeRes(parts),
      ttsFetch: async (t) => {
        await sleep(2);
        return { t };
      },
      ttsPlay: async (b, t) => {
        played.push(t);
        await sleep(30);
      },
    });
    const r = await sess.run();
    await r.ttsDone;
    assert.ok(r.corrected);
    assert.ok(played.includes(corrected), JSON.stringify(played));
    // eski parça (varsa) en fazla BİR tane çalmaya başlamış olabilir ama düzeltilmiş cevabın ardından eski parça çalınmaz
    const idx = played.indexOf(corrected);
    assert.strictEqual(played.slice(idx + 1).length, 0);
    ok("oturum: düzeltme eski parçaları çalmaz");
  }
  {
    // barge-in: akış sürerken ses kesilir → sonraki tokenlar konuşulmaz, metin akmaya devam eder
    const lock = T.createTurnLock();
    const first = "Birinci cümle seslendirilecek ve çalacak. ";
    const later = "Bu ikinci cümle barge sonrası gelir ve çalmamalı. ";
    let releaseMore;
    const gate = new Promise((r) => (releaseMore = r));
    const res = {
      ok: true,
      status: 200,
      headers: { get: () => "text/event-stream" },
      body: {
        getReader() {
          let i = 0;
          const seq = [tok(first), "GATE", tok(later), done(first + later)];
          return {
            async read() {
              if (i >= seq.length) return { done: true };
              const s = seq[i++];
              if (s === "GATE") {
                await gate;
                return this.read();
              }
              return { done: false, value: enc.encode(s) };
            },
            async cancel() {},
            releaseLock() {},
          };
        },
      },
    };
    const turn = lock.begin();
    const played = [];
    const texts = [];
    const sess = T.createSession({
      turn,
      url: "/s",
      body: {},
      fetchImpl: async () => res,
      ttsFetch: async (t) => ({ t }),
      ttsPlay: async (b, t) => {
        played.push(t);
        await sleep(20);
      },
      onToken: (t, full) => texts.push(full),
    });
    const runP = sess.run();
    await sleep(30);
    assert.strictEqual(played.length, 1);
    lock.cancelSpeech("barge");
    releaseMore();
    const r = await runP;
    await r.ttsDone;
    assert.strictEqual(played.length, 1, "barge sonrası parça çalınmadı");
    assert.ok(r.stream.ok && r.stream.full.includes("barge sonrası"), "metin akmaya devam etti");
    ok("oturum: barge sonrası konuşmaz, metin sürer");
  }
  {
    // yeni tur: eski turun akışı abort + eski ses susar
    const lock = T.createTurnLock();
    const aCtx = mkSession([tok("Eski tur bir cümle yazıyor burada. "), tok("devam")], { lock, res: { hang: true } });
    const aRun = aCtx.sess.run();
    await sleep(40);
    const bCtx = mkSession([tok("Yeni cevap buradadır, merhaba. "), done("Yeni cevap buradadır, merhaba.")], { lock });
    const bRes = await bCtx.sess.run();
    await bRes.ttsDone;
    const aRes = await Promise.race([aRun, sleep(1500).then(() => "ASILI")]);
    assert.notStrictEqual(aRes, "ASILI", "eski tur akışı asılı kalmadı");
    await aRes.ttsDone;
    assert.deepStrictEqual(bCtx.log.played, ["Yeni cevap buradadır, merhaba."]);
    assert.ok(aCtx.log.telemetry[0] && aCtx.log.telemetry[0].iptal === true);
    ok("oturum: yeni tur eskisini keser, eski akış serbest");
  }
  {
    // sessiz tur (speak=false): kuyruk yok, telemetri token ile gider
    const { sess, log } = mkSession([tok("Sadece metin. "), done("Sadece metin.")], { opts: { speak: false } });
    const r = await sess.run();
    await r.ttsDone;
    assert.strictEqual(log.played.length, 0);
    assert.strictEqual(log.telemetry.length, 1);
    assert.ok(log.telemetry[0].ilk_token_ms != null && log.telemetry[0].ilk_ses_ms == null);
    ok("oturum: sessiz tur");
  }

  console.log("\n" + n + " test grubu geçti");
}

main().catch((e) => {
  console.error("BAŞARISIZ:", e && e.stack ? e.stack : e);
  process.exit(1);
});
