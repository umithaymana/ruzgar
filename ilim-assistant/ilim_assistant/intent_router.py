"""Basit niyet sınıflandırması (hava vs gramer vs genel) — küçük Naive Bayes."""

from __future__ import annotations

import os

_vectorizer = None
_model = None

_INTENT_OFF = os.environ.get("INTENT_CLASSIFIER", "1").strip() in ("0", "false", "no")

# Kısa eğitim kümesi — weather ile grammar karışmasını azaltır
_TRAIN_TEXTS = [
    # weather
    "hava nasıl bugün",
    "bugün hava durumu",
    "yarın yağmur var mı",
    "istanbul hava kaç derece",
    "sıcak mı dışarı",
    "kar yağıyor mu",
    "şemsiye lazım mı",
    "meteoroloji uyarısı var mı",
    "rüzgar esiyor mu bugün",
    "nem oranı nedir",
    "bulutlu mu gökyüzü",
    "hafta sonu hava nasıl",
    "deniz suyu sıcaklığı",
    "sis var mı",
    "şimdi kaç derece",
    # grammar / dilbilgisi
    "bu cümle doğru mu",
    "gramer hatası var mı",
    "doğru yazımı nedir",
    "fiil çekimi yanlış mı",
    "nesne yüklem uyumu",
    "bağlaç kullanımı",
    "noktalama doğru mu",
    "özne ve yüklem ilişkisi",
    "ses olayı nedir",
    "ünlü düşmesi örneği",
    "arap nahiv örneği",
    "nahiv kuralı",
    "tecvid kuralı örneği",
    "edebi sanatlar",
    "anlatım bozukluğu var mı",
    # genel (weather veya grammar değil) — günlük konuşma, gündem, argo değil ama gündelik dil
    "selam nasılsın",
    "günaydın keyifler nasıl",
    "akşam ne yapalım",
    "çok yorgunum bugün",
    "işten çıktım trafik berbat",
    "film önerisi ver",
    "gen z ne demek",
    "python ile dosya okuma",
    "kuranı kerim meal",
    "matematik problemi çöz",
    "tarihte osmanlı",
    "hangi model daha iyi",
    "şarjım bitiyor",
    "yemek tarifi ver",
    "python nedir",
    "cursor kullanımı",
    "marketten ekmek al dedim",
    "rezervasyon için arama yapacağım",
    "dedikodu yapmayı sevmem",
    "bu kelimenin gündelik anlamı ne",
]


_TRAIN_LABELS = (
    ["weather"] * 15
    + ["grammar"] * 15
    + ["general"] * 20
)


def _fit():
    global _vectorizer, _model
    if _model is not None:
        return
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.naive_bayes import MultinomialNB

    _vectorizer = CountVectorizer(ngram_range=(1, 2), min_df=1)
    X = _vectorizer.fit_transform(_TRAIN_TEXTS)
    _model = MultinomialNB()
    _model.fit(X, _TRAIN_LABELS)


def predict_intent(text: str) -> str:
    """weather | grammar | general"""
    if _INTENT_OFF:
        return "general"
    t = (text or "").strip()
    if not t:
        return "general"
    try:
        _fit()
        assert _vectorizer is not None and _model is not None
        Xt = _vectorizer.transform([t])
        return str(_model.predict(Xt)[0])
    except Exception:
        return "general"


def should_use_ilim_rag(text: str) -> bool:
    """
    Yerel knowledge/*.md bağlamı: yalnızca dilbilgisi/nahiv/tecvid niyeti için.
    INTENT_CLASSIFIER kapalıyken eski davranış — her mesajda RAG denenir.
    """
    if _INTENT_OFF:
        return True
    return predict_intent(text) == "grammar"
