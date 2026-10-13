# RÜZGAR — mobil (Expo)

Telefon, Rüzgar sunucusuna sorar. Kütüphane, arama cetveli ve anahtarlar telefonda durmaz.

Bugün kapı yalnız bu bilgisayardadır: `http://127.0.0.1:8779`. Uygulama `POST /api/chat/full` kullanır. Ollama adresi telefona verilmez.

Halka açılış ayrı bir gündür. O gün sunucu adresi değişir; kapının önüne kimlik ve TLS konur.

## Kurulum

```bash
cd ilim-mobile
npm install
npx expo start
```

Expo Go ile QR kodu tarayın veya emülatör kullanın. Aynı bilgisayardaki emülatör varsayılan adrese bağlanır.

## Mağaza

`eas build` ile Android veya iOS paketi ayrı bir adımdır. Bu klasör başlangıç istemcisidir.
