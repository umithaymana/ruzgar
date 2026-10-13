/**
 * RÜZGAR — ince istemci. Yalnız Rüzgar kapısına konuşur (POST /api/chat/full).
 * Bugün kapı bu bilgisayarda: http://127.0.0.1:8779
 * Ollama telefona açılmaz. Halka açılış ayrı gündür.
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

type Msg = { role: "user" | "assistant"; text: string };

async function chatRuzgar(
  baseUrl: string,
  message: string,
  history: { role: string; content: string }[],
): Promise<string> {
  const url = `${baseUrl.replace(/\/$/, "")}/api/chat/full`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      history,
      mode: "genel",
      use_web: false,
    }),
  });
  const raw = await res.text();
  if (!res.ok) {
    throw new Error(raw.slice(0, 400));
  }
  const j = JSON.parse(raw);
  const reply = String(j.full_reply ?? "").trim();
  return reply || "(Yanıt yok)";
}

export default function App() {
  const [baseUrl, setBaseUrl] = useState("http://127.0.0.1:8779");
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
      const history = msgs.map((x) => ({ role: x.role, content: x.text }));
      const reply = await chatRuzgar(baseUrl, t, history);
      setMsgs((m) => [...m, { role: "assistant", text: reply }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      Alert.alert("Bağlantı hatası", msg);
      setMsgs((m) => [...m, { role: "assistant", text: `[Hata] ${msg}` }]);
    } finally {
      setLoading(false);
    }
  }, [baseUrl, input, loading, msgs]);

  return (
    <KeyboardAvoidingView
      style={styles.root}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <StatusBar style="light" />
      <Text style={styles.title}>RÜZGAR</Text>
      <Text style={styles.hint}>
        Rüzgar kapısı. Bugün bu bilgisayar: 127.0.0.1:8779
      </Text>
      <TextInput
        style={styles.cfg}
        value={baseUrl}
        onChangeText={setBaseUrl}
        autoCapitalize="none"
        autoCorrect={false}
        placeholder="http://127.0.0.1:8779"
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
          placeholder="Mesaj…"
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
