# Created by Ümit & Gökçenur
"""
Programlama motoru — Faz 30: Mobil şablon (Expo / React Native).

Şablon kimliği: mobile_expo
Komut: şablon oluştur: mobile_expo uygulamam
"""

from __future__ import annotations

import os
from typing import Any

FAZ30_VERSION = "programlama-faz30-v1-2026-05-25"
MOBILE_TEMPLATE_ID = "mobile_expo"

MOBILE_TEMPLATE_ALIASES: dict[str, str] = {
    "mobile": MOBILE_TEMPLATE_ID,
    "mobil": MOBILE_TEMPLATE_ID,
    "expo": MOBILE_TEMPLATE_ID,
    "react-native": MOBILE_TEMPLATE_ID,
    "react_native": MOBILE_TEMPLATE_ID,
    "mobile_expo": MOBILE_TEMPLATE_ID,
    "mobile_app": MOBILE_TEMPLATE_ID,
}


def _enabled() -> bool:
    return os.environ.get("RUZGAR_FAZ30", "1").strip().lower() not in (
        "0",
        "false",
        "no",
    )


def extra_template_catalog() -> list[dict[str, Any]]:
    if not _enabled():
        return []
    return [
        {
            "id": MOBILE_TEMPLATE_ID,
            "label": "Mobil uygulama (Expo)",
            "stack": ["javascript", "react-native", "expo"],
            "desc": "Tek ekran Expo iskeleti; npm install + npx expo start",
            "faz": 30,
        },
    ]


def mobile_expo_files(
    template_id: str,
    slug: str,
    title: str,
    *,
    projects_base: str = "projects",
) -> dict[str, str] | None:
    if not _enabled():
        return None
    tid = MOBILE_TEMPLATE_ALIASES.get(template_id.strip().lower(), template_id)
    if tid != MOBILE_TEMPLATE_ID:
        return None
    base = f"{projects_base}/{slug}"
    return {
        f"{base}/package.json": f'''{{
  "name": "{slug}",
  "version": "0.1.0",
  "private": true,
  "main": "node_modules/expo/AppEntry.js",
  "scripts": {{
    "start": "expo start",
    "android": "expo start --android",
    "ios": "expo start --ios",
    "web": "expo start --web"
  }},
  "dependencies": {{
    "expo": "~51.0.0",
    "expo-status-bar": "~1.12.1",
    "react": "18.2.0",
    "react-native": "0.74.5"
  }},
  "devDependencies": {{
    "@babel/core": "^7.24.0",
    "babel-preset-expo": "~11.0.0"
  }}
}}
''',
        f"{base}/app.json": f'''{{
  "expo": {{
    "name": "{title}",
    "slug": "{slug}",
    "version": "1.0.0",
    "orientation": "portrait",
    "userInterfaceStyle": "automatic",
    "splash": {{
      "resizeMode": "contain",
      "backgroundColor": "#0f1419"
    }},
    "ios": {{ "supportsTablet": true }},
    "android": {{ "adaptiveIcon": {{ "backgroundColor": "#0f1419" }} }}
  }}
}}
''',
        f"{base}/babel.config.js": """module.exports = function (api) {
  api.cache(true);
  return { presets: ["babel-preset-expo"] };
};
""",
        f"{base}/App.js": f'''import {{ StatusBar }} from "expo-status-bar";
import {{ useState }} from "react";
import {{ Pressable, StyleSheet, Text, View }} from "react-native";

/** {title} — Rüzgar Faz 30 mobil şablon */
export default function App() {{
  const [count, setCount] = useState(0);
  return (
    <View style={{styles.container}}>
      <Text style={{styles.title}}>{title}</Text>
      <Text style={{styles.sub}}>Expo mobil iskelet — Ümit abi</Text>
      <Pressable style={{styles.btn}} onPress={{() => setCount((c) => c + 1)}}>
        <Text style={{styles.btnText}}>Dokun ({{count}})</Text>
      </Pressable>
      <StatusBar style="light" />
    </View>
  );
}}

const styles = StyleSheet.create({{
  container: {{
    flex: 1,
    backgroundColor: "#0f1419",
    alignItems: "center",
    justifyContent: "center",
    padding: 24,
  }},
  title: {{ fontSize: 22, fontWeight: "700", color: "#e7ecf3", marginBottom: 8 }},
  sub: {{ fontSize: 14, color: "#9aa8bc", marginBottom: 20, textAlign: "center" }},
  btn: {{
    backgroundColor: "#3d8bfd",
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 10,
  }},
  btnText: {{ color: "#fff", fontWeight: "600" }},
}});
''',
        f"{base}/README.md": f"""# {title}

Mobil uygulama (Expo / React Native) — Rüzgar Faz 30.

## Gereksinimler

- Node.js 18+
- Expo Go uygulaması (telefonda) veya Android/iOS emülatör

## Çalıştırma

```bash
cd projects/{slug}
npm install
npx expo start
```

QR kodu Expo Go ile okutun veya `a` (Android) / `i` (iOS) tuşları.

## Genişletme

- `App.js` — ana ekran
- `app.json` — uygulama meta verisi
""",
    }


def resolve_mobile_alias(template_id: str) -> str:
    return MOBILE_TEMPLATE_ALIASES.get(
        (template_id or "").strip().lower(),
        (template_id or "").strip().lower(),
    )


def faz30_directive() -> str:
    return (
        "[MOBİL ŞABLON — Faz 30]\n"
        "Şablon: `mobile_expo` — `şablon oluştur: mobile_expo uygulamam`\n"
        "Atölye: + Mobil düğmesi veya `expo` / `mobil` takma adları.\n"
    )
