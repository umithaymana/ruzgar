/**
 * RÜZGAR — yerel ağdaki Ollama’ya bağlanır (OpenAI uyumlu API).
 * Örnek taban: http://192.168.1.10:11434  (sonunda /v1 olmadan)
 *
 * PC’de Ollama’nın telefondan erişilebilmesi için (Windows):
 *   setx OLLAMA_HOST 0.0.0.0
 * Ollama’yı yeniden başlat; güvenlik duvarında 11434 izni ver.
 */

import { useCallback, useState } from "react";
import {
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { StatusBar } from "expo-status-bar";

const SYSTEM_RÜZGAR = `Sen RÜZGAR adlı asistansın. Kullanıcıya her zaman "Ümit abi" diye hitap et. Nazik ve net ol.`;

type Msg = { role: "user" | "assistant"; text: string };

async function chatOllama(
  baseUrl: string,
  model: string,
  messages: { role: string; content: string }[],
): Promise<string> {
  const url = `${baseUrl.replace(/\/$/, "")}/v1/chat/completions`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer ollama",
    },
    body: JSON.stringify({
      model,
      messages,
      temperature: 0.35,
      stream: false,
    }),
  });
  const raw = await res.text();
  if (!res.ok) {
    throw new Error(raw.slice(0, 400));
  }
  const j = JSON.parse(raw);
  return j.choices?.[0]?.message?.content?.trim() ?? "(Yanıt yok)";
}

export default function App() {
  const [baseUrl, setBaseUrl] = useState("http://192.168.1.1:11434");
  const [model, setModel] = useState("llama3.2");
  const [input, setInput] = useState("");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);

  const send = useCallback(async () => {
    const t = input.trim();
    if (!t || loading) return;
    setInput("");
    const nextUser: Msg = { role: "user", text: t };
    setMsgs((m) => [...m, nextUser]);
    setLoading(true);
    try {
      const history = [
        { role: "system", content: SYSTEM_RÜZGAR },
        ...msgs.flatMap((x) => [
          { role: x.role, content: x.text },
        ]),
        { role: "user", content: t },
      ];
      const reply = await chatOllama(baseUrl, model, history);
      setMsgs((m) => [...m, { role: "assistant", text: reply }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert("Bağlantı hatası", msg);
      setMsgs((m) => [...m, { role: "assistant", text: `[Hata] ${msg}` }]);
    } finally {
      setLoading(false);
    }
  }, [baseUrl, input, loading, model, msgs]);

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <StatusBar style="light" />
      <Text style={styles.title}>RÜZGAR</Text>
      <Text style={styles.hint}>
        Ollama adresi (PC IP): aynı Wi‑Fi’de olmalısınız.
      </Text>
      <TextInput
        style={styles.cfg}
        value={baseUrl}
        onChangeText={setBaseUrl}
        autoCapitalize="none"
        autoCorrect={false}
        placeholder="http://192.168.x.x:11434"
      />
      <TextInput
        style={styles.cfg}
        value={model}
        onChangeText={setModel}
        autoCapitalize="none"
        placeholder="Model adı (örn. llama3.2)"
      />
      <ScrollView style={styles.chat}>
        {msgs.map((m, i) => (
          <View
            key={i}
            style={[
              styles.bubble,
              m.role === "user" ? styles.userBubble : styles.botBubble,
            ]}
          >
            <Text style={styles.bubbleText}>{m.text}</Text>
          </View>
        ))}
      </ScrollView>
      <View style={styles.row}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ümit abi için mesaj…"
          multiline
          editable={!loading}
        />
        <Pressable
          style={[styles.btn, loading && styles.btnDisabled]}
          onPress={send}
          disabled={loading}
        >
          <Text style={styles.btnTxt}>{loading ? "…" : "Gönder"}</Text>
        </Pressable>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, paddingTop: 48, paddingHorizontal: 12, backgroundColor: "#1a1a2e" },
  title: { fontSize: 22, fontWeight: "700", color: "#eaeaea", marginBottom: 4 },
  hint: { fontSize: 12, color: "#aaa", marginBottom: 8 },
  cfg: {
    borderWidth: 1,
    borderColor: "#444",
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    color: "#fff",
    fontSize: 13,
  },
  chat: { flex: 1, marginVertical: 10 },
  bubble: {
    maxWidth: "92%",
    padding: 10,
    borderRadius: 12,
    marginBottom: 8,
  },
  userBubble: { alignSelf: "flex-end", backgroundColor: "#4361ee" },
  botBubble: { alignSelf: "flex-start", backgroundColor: "#16213e" },
  bubbleText: { color: "#f8f8f2", fontSize: 15 },
  row: { flexDirection: "row", alignItems: "flex-end", paddingBottom: 24, gap: 8 },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: "#444",
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    color: "#fff",
    fontSize: 15,
  },
  btn: {
    backgroundColor: "#e94560",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
  },
  btnDisabled: { opacity: 0.5 },
  btnTxt: { color: "#fff", fontWeight: "600" },
});
