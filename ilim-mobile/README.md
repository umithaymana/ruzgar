# RÜZGAR — mobil (Expo)

Telefonundan **aynı Wi‑Fi üzerindeki PC’de çalışan Ollama** ile sohbet eder.

## Kurulum

```bash
cd ilim-mobile
npm install
npx expo start
```

Expo Go uygulaması ile QR kodu tarayın veya emülatör kullanın.

## PC tarafı

1. Ollama çalışıyor olmalı (`ollama serve`).
2. Yerel ağdan erişim için (Windows PowerShell, bir kez):

```powershell
setx OLLAMA_HOST "0.0.0.0"
```

Ollama’yı yeniden başlatın. Güvenlik duvarında **11434** TCP izni verin.

3. PC’nin IP adresini öğrenin (`ipconfig`) ve uygulamadaki adresi `http://IP:11434` yapın.

## Mağazaya yükleme

`eas build` ile Android APK/AAB veya iOS için Apple Developer hesabı gerekir; bu repo bir başlangıç iskeletidir.
