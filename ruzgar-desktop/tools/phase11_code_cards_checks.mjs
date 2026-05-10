/**
 * Faz 1.1 — kod kartı fenced-block doğruluğu (app.js ile senkron tutulmalı).
 * Çalıştır: node tools/phase11_code_cards_checks.mjs
 */

import assert from "node:assert";

const LANG_CLASS = `[a-zA-Z0-9_+#.-]*`;
/** app.js içindeki renderAssistantRichHtml fence ile aynı kalıp */
const FENCE_RE = new RegExp(
  "```[ \\t]*(" + LANG_CLASS + ")[ \\t]*\\r?\\n([\\s\\S]*?)\\n?[ \\t]*```",
  "g"
);

const CODE_LANG_NORMALIZE = {
  py: "python",
  python: "python",
  python3: "python",
  js: "javascript",
  javascript: "javascript",
  node: "javascript",
  nodejs: "javascript",
  ts: "typescript",
  typescript: "typescript",
  rs: "rust",
  rust: "rust",
  go: "go",
  golang: "go",
  cs: "csharp",
  csharp: "csharp",
  "c#": "csharp",
  kotlin: "kotlin",
  kt: "kotlin",
  swift: "swift",
  dart: "dart",
  vue: "vue",
  jsx: "jsx",
  tsx: "tsx",
  java: "java",
  cpp: "cpp",
  cxx: "cpp",
  cc: "cpp",
  c: "c",
  sqlite: "sql",
  sql: "sql",
  yaml: "yaml",
  yml: "yaml",
  md: "markdown",
  markdown: "markdown",
  html: "html",
  htm: "html",
  css: "css",
  json: "json",
  bash: "bash",
  sh: "bash",
  shell: "bash",
  pwsh: "powershell",
  ps1: "powershell",
  powershell: "powershell",
  text: "text",
  txt: "text",
  "": "text",
};

function normalizeCodeLang(raw) {
  const t = String(raw || "").trim().toLowerCase();
  return CODE_LANG_NORMALIZE[t] || t || "text";
}

function codeLangIsRunnable(lang) {
  const v = normalizeCodeLang(lang);
  return v === "python" || v === "javascript";
}

function extractFences(txt) {
  const out = [];
  let m;
  const re = new RegExp(FENCE_RE.source, "g");
  while ((m = re.exec(txt)) !== null) {
    out.push({ langRaw: m[1], body: m[2] });
  }
  return out;
}

function run() {
  const a = extractFences("Önce metin.\n```python\nprint(42)\n```\nSon.");
  assert.strictEqual(a.length, 1);
  assert.strictEqual(a[0].langRaw, "python");
  assert.strictEqual(a[0].body.trim(), "print(42)");

  const b = extractFences("``` js \nconsole.log(1)\n ```");
  assert.strictEqual(b.length, 1);
  assert.strictEqual(b[0].langRaw, "js");

  const c = extractFences("```csharp\nvar x = 1;\r\n```");
  assert.strictEqual(c.length, 1);
  assert.strictEqual(normalizeCodeLang(c[0].langRaw), "csharp");

  const d = extractFences("```c#\n;\n```");
  assert.strictEqual(d.length, 1);
  assert.strictEqual(normalizeCodeLang(d[0].langRaw), "csharp");

  assert.strictEqual(
    extractFences("```typescript\nlet n: number = 1\n```").length,
    1
  );
  assert.strictEqual(codeLangIsRunnable("typescript"), false);
  assert.strictEqual(codeLangIsRunnable("py"), true);
  assert.strictEqual(codeLangIsRunnable("node"), true);

  const multi = extractFences("```python\n1\n```\nvb\n```bash\necho x\n```");
  assert.strictEqual(multi.length, 2);

  /** Kapanmadan fenced yoksa eşleşme üretmez (çıktı sırasında zararsız) */
  assert.strictEqual(extractFences("```python\nprint(9)").length, 0);

  console.log(
    "Faz 1.1 kod kartı doğruluk kontrolleri: OK (" +
      new URL(import.meta.url).pathname +
      ")"
  );
}

run();
