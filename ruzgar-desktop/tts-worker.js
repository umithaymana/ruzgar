/**
 * Edge TTS ağ çağrıları — ana UI iş parçacığından ayrı (Ümit & Gökçenur Işık Hızı).
 * postMessage: { id, api, text, karakter }
 * response: { id, ok, buf } veya { id, ok:false, err }
 */
self.onmessage = async (ev) => {
  const d = ev.data || {};
  const { id, api, text, karakter, emotion } = d;
  if (id == null || !api || text == null) {
    self.postMessage({ id: id ?? -1, ok: false, err: "bad-args" });
    return;
  }
  const root = String(api).replace(/\/$/, "");
  try {
    const res = await fetch(`${root}/api/tts`, {
      method: "POST",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        Pragma: "no-cache",
      },
      body: JSON.stringify({
        text: String(text),
        karakter: String(karakter || "asistan"),
        backend: "edge",
        ...(emotion && emotion !== "notr" ? { emotion: String(emotion) } : {}),
      }),
    });
    if (!res.ok) {
      self.postMessage({
        id,
        ok: false,
        err: `HTTP ${res.status}`,
      });
      return;
    }
    const buf = await res.arrayBuffer();
    self.postMessage({ id, ok: true, buf }, [buf]);
  } catch (e) {
    self.postMessage({ id, ok: false, err: String(e) });
  }
};
