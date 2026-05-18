from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA = "ruzgar_merkezi_v1"
_SCHEMA_V2 = "ruzgar_merkezi_v2"
_VALID_NESTED_SCHEMAS = frozenset({_SCHEMA, _SCHEMA_V2})


def merkezi_bellek_path() -> Path:
    """ilim-assistant kökündeki merkezi_bellek.json (paket klasörü değil)."""
    return Path(__file__).resolve().parents[2] / "merkezi_bellek.json"


def _default_document() -> dict[str, Any]:
    return {
        "version": 4,
        "schema": _SCHEMA_V2,
        "engine": "ruzgar",
        "kategoriler": {
            "hizir_ticaret": {
                "meta": {"global_market_engine": "1", "ticaret_avci": "2"},
                "firsatlar": [],
                "stop_loss_log": [],
                "mizan_hareketleri": [],
                "kullanici_mizan": {},
            },
            "genel_onbellek": {"girdiler": []},
        },
    }


def _hizir_ticaret(doc: dict[str, Any]) -> dict[str, Any]:
    k = doc.setdefault("kategoriler", {})
    assert isinstance(k, dict)
    h = k.setdefault("hizir_ticaret", {})
    assert isinstance(h, dict)
    h.setdefault("meta", {})
    if not isinstance(h.get("meta"), dict):
        h["meta"] = {}
    h.setdefault("stop_loss_log", [])
    h.setdefault("mizan_hareketleri", [])
    h.setdefault("kullanici_mizan", {})
    for key in ("firsatlar", "stop_loss_log", "mizan_hareketleri"):
        if not isinstance(h.get(key), list):
            h[key] = []
    if not isinstance(h.get("kullanici_mizan"), dict):
        h["kullanici_mizan"] = {}
    return h


def _genel_onbellek(doc: dict[str, Any]) -> dict[str, Any]:
    k = doc.setdefault("kategoriler", {})
    g = k.setdefault("genel_onbellek", {})
    assert isinstance(g, dict)
    g.setdefault("girdiler", [])
    if not isinstance(g["girdiler"], list):
        g["girdiler"] = []
    return g


def _migrate_flat_to_nested(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schema") in _VALID_NESTED_SCHEMAS and isinstance(raw.get("kategoriler"), dict):
        return raw
    return {
        "version": 3,
        "schema": _SCHEMA,
        "engine": raw.get("engine", "ruzgar"),
        "kategoriler": {
            "hizir_ticaret": {
                "firsatlar": list(raw.get("hizir_firsatlar") or []),
                "stop_loss_log": list(raw.get("hizir_stop_loss_log") or []),
                "mizan_hareketleri": list(raw.get("hizir_mizan_hareketleri") or []),
                "kullanici_mizan": dict(raw.get("hizir_kullanici_mizan") or {}),
            },
            "genel_onbellek": {"girdiler": list(raw.get("ruzgar_genel_onbellek") or [])},
        },
        "updated_at": raw.get("updated_at"),
    }


def load_merkezi_bellek(path: Path | None = None) -> dict[str, Any]:
    p = path or merkezi_bellek_path()
    if not p.is_file():
        return _default_document()
    raw_txt = p.read_text(encoding="utf-8")
    data = json.loads(raw_txt) if raw_txt.strip() else _default_document()
    if not isinstance(data, dict):
        return _default_document()
    return _migrate_flat_to_nested(data)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    tmp = path.parent / f".{path.name}.{os.getpid()}.tmp"
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def append_opportunity(record: dict[str, Any], path: Path | None = None) -> None:
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    rows = _hizir_ticaret(doc)["firsatlar"]
    rows.append(record)
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(p, doc)


def append_stop_loss_event(event: dict[str, Any], path: Path | None = None) -> None:
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    log = _hizir_ticaret(doc)["stop_loss_log"]
    log.append(event)
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(p, doc)


def append_genel_onbellek_girdi(
    girdi: dict[str, Any],
    path: Path | None = None,
) -> None:
    """Rüzgar genel önbellek (pazar özeti, uçuş stub vb.)."""
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    girdi.setdefault("tarih", datetime.now(timezone.utc).isoformat())
    _genel_onbellek(doc)["girdiler"].append(girdi)
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(p, doc)


def save_merkezi_bellek(doc: dict[str, Any], path: Path | None = None) -> None:
    """Tam belge yazımı (Ticaret Avcısı senkronu vb.)."""
    p = path or merkezi_bellek_path()
    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(p, doc)


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def find_fresh_genel_girdi(
    *,
    tip: str,
    anahtar: str,
    max_age_sec: float,
    path: Path | None = None,
) -> dict[str, Any] | None:
    doc = load_merkezi_bellek(path)
    now = datetime.now(timezone.utc)
    girdiler = list(reversed(_genel_onbellek(doc)["girdiler"]))
    for row in girdiler:
        if row.get("tip") != tip or row.get("anahtar") != anahtar:
            continue
        dt = _parse_iso(str(row.get("tarih") or ""))
        if dt is None:
            continue
        if (now - dt).total_seconds() <= max_age_sec:
            return row
    return None


def find_hizir_firsat_summary_lines(
    msg: str,
    *,
    max_rows: int = 6,
    path: Path | None = None,
) -> list[str]:
    """Ürün adında sorgu kelimeleri geçen son fırsat satırları (metin özet)."""
    words = [w for w in re.split(r"\W+", (msg or "").lower()) if len(w) >= 3]
    if not words:
        return []
    doc = load_merkezi_bellek(path)
    rows = list(reversed(_hizir_ticaret(doc)["firsatlar"]))
    out: list[str] = []
    for r in rows:
        if len(out) >= max_rows:
            break
        name = str(r.get("urun_adi") or "").lower()
        if not any(w in name for w in words[:12]):
            continue
        try:
            nm_v = float(r.get("net_marj_yuzde"))
            nm_s = f"{nm_v:.1f}%"
        except (TypeError, ValueError):
            nm_s = "—"
        out.append(
            f"- {r.get('urun_adi')} | Bölge: {r.get('bolge', '—')} | "
            f"kaynak {r.get('kaynak_fiyat')} → hedef {r.get('hedef_fiyat')} | "
            f"net kâr {r.get('potansiyel_kar')} | net marj {nm_s} | "
            f"{r.get('tarih')}"
        )
    return out


def _empty_mizan_row() -> dict[str, Any]:
    return {
        "net_kar_toplam": 0.0,
        "komisyon_toplam": 0.0,
        "kdv_toplam": 0.0,
        "islem_sayisi": 0,
    }


def record_mizan_hareketi(
    kullanici_id: str,
    *,
    net_kar: float,
    komisyon: float,
    kdv: float,
    path: Path | None = None,
    ek_not: str | None = None,
) -> None:
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    htc = _hizir_ticaret(doc)
    uid = (kullanici_id or "anon").strip() or "anon"
    mizan: dict[str, Any] = htc["kullanici_mizan"]
    row = mizan.get(uid)
    if not isinstance(row, dict):
        row = _empty_mizan_row()
    row["net_kar_toplam"] = float(row.get("net_kar_toplam", 0.0)) + float(net_kar)
    row["komisyon_toplam"] = float(row.get("komisyon_toplam", 0.0)) + float(komisyon)
    row["kdv_toplam"] = float(row.get("kdv_toplam", 0.0)) + float(kdv)
    row["islem_sayisi"] = int(row.get("islem_sayisi", 0)) + 1
    row["guncelleme"] = datetime.now(timezone.utc).isoformat()
    mizan[uid] = row

    hareketler = htc["mizan_hareketleri"]
    ev = {
        "tarih": datetime.now(timezone.utc).isoformat(),
        "kullanici_id": uid,
        "net_kar": round(float(net_kar), 4),
        "komisyon": round(float(komisyon), 4),
        "kdv": round(float(kdv), 4),
    }
    if ek_not:
        ev["not"] = ek_not
    hareketler.append(ev)

    doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_write_json(p, doc)


def persist_if_avla(
    analysis: dict[str, Any],
    *,
    product_name: str,
    source_price: float,
    target_price: float,
    path: Path | None = None,
    kullanici_id: str | None = None,
    record_mizan: bool | None = None,
) -> bool:
    if record_mizan is None:
        record_mizan = bool((kullanici_id or "").strip())
    if analysis.get("status") != "AVLA":
        return False
    when = datetime.now(timezone.utc).isoformat()
    bd = analysis.get("breakdown") or {}
    if not isinstance(bd, dict):
        bd = {}
    record: dict[str, Any] = {
        "tarih": when,
        "urun_adi": product_name,
        "kaynak_fiyat": float(source_price),
        "hedef_fiyat": float(target_price),
        "potansiyel_kar": float(analysis.get("net_profit", 0.0)),
        "kdv_tutari": float(bd.get("vat_amount", 0.0)),
        "satis_komisyon_tutari": float(bd.get("sale_commission_amount", 0.0)),
        "alis_tarafi_komisyon_tutari": float(bd.get("buy_commission_amount", 0.0)),
        "kargo": float(bd.get("shipping", 0.0)),
        "hata_payi_tutari": float(bd.get("error_margin_amount", 0.0)),
        "maliyet_toplam": float(bd.get("cost_basis", 0.0)),
        "net_satis": float(bd.get("net_sale", 0.0)),
    }
    if kullanici_id:
        record["kullanici_id"] = (kullanici_id or "").strip()
    append_opportunity(record, path=path)

    if record_mizan:
        uid = (kullanici_id or "anon").strip() or "anon"
        record_mizan_hareketi(
            uid,
            net_kar=float(analysis.get("net_profit", 0.0)),
            komisyon=float(bd.get("sale_commission_amount", 0.0))
            + float(bd.get("buy_commission_amount", 0.0)),
            kdv=float(bd.get("vat_amount", 0.0)),
            path=path,
            ek_not=product_name[:200],
        )
    return True


def append_hizir_pas_gecildi(kart_id: str, path: Path | None = None) -> None:
    """PAS GEÇ: kart kimliğini meta.pas_gecildi listesine ekler (yeniden üretimi engeller)."""
    kid = (kart_id or "").strip()
    if not kid:
        return
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    htc = _hizir_ticaret(doc)
    meta = htc.setdefault("meta", {})
    if not isinstance(meta, dict):
        meta = {}
        htc["meta"] = meta
    pg = meta.setdefault("pas_gecildi", [])
    if not isinstance(pg, list):
        pg = []
        meta["pas_gecildi"] = pg
    if kid not in pg:
        pg.append(kid)
    if len(pg) > 400:
        meta["pas_gecildi"] = pg[-400:]
    save_merkezi_bellek(doc, path=p)


def clear_hizir_vitrin_state(path: Path | None = None) -> dict[str, Any]:
    """Sayfayı temizle: pazar_keşif girdileri, pas geç listesi ve otomatik fırsatlar silinir; elle satırlar kalır."""
    p = path or merkezi_bellek_path()
    doc = load_merkezi_bellek(p)
    g = _genel_onbellek(doc)
    g["girdiler"] = [
        x
        for x in (g.get("girdiler") or [])
        if not (isinstance(x, dict) and x.get("tip") == "pazar_keşif")
    ]
    htc = _hizir_ticaret(doc)
    meta = htc.setdefault("meta", {})
    if not isinstance(meta, dict):
        meta = {}
        htc["meta"] = meta
    meta["pas_gecildi"] = []
    manual = [r for r in htc["firsatlar"] if isinstance(r, dict) and not r.get("otomatik")]
    htc["firsatlar"] = manual
    save_merkezi_bellek(doc, path=p)
    from ilim_assistant.hizir.ticaret_avci import reconcile_ticaret_avci_firsatlar

    return reconcile_ticaret_avci_firsatlar(path=p)


def pas_gec_hizir_kart(kart_id: str, path: Path | None = None) -> dict[str, Any]:
    append_hizir_pas_gecildi(kart_id, path=path)
    from ilim_assistant.hizir.ticaret_avci import reconcile_ticaret_avci_firsatlar

    return reconcile_ticaret_avci_firsatlar(path=path)
