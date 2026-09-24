"""Confronto tra dati estratti e ground truth, campo per campo."""
import re
from datetime import date

PAROLE_VUOTE = {"del", "della", "dei", "tra", "per", "con", "delle", "degli"}


def _parole(s: str) -> set[str]:
    return {w for w in re.split(r"[^a-z0-9àèéìòù]+", s.lower()) if len(w) > 2 and w not in PAROLE_VUOTE}


def _data(v) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", s)
    if m:
        return date(int(m[3]), int(m[2]), int(m[1])).isoformat()
    return s[:10]


def corrisponde(campo: str, atteso, estratto) -> bool:
    if estratto is None:
        return False
    if isinstance(atteso, bool):
        return bool(estratto) == atteso
    if isinstance(atteso, (int, float)):
        try:
            return abs(float(estratto) - float(atteso)) <= 0.05
        except (TypeError, ValueError):
            return False
    if isinstance(atteso, list):
        return {str(x).strip().lower() for x in atteso} == {str(x).strip().lower() for x in estratto}
    if campo == "data" or campo.startswith("data_"):
        return _data(atteso) == _data(estratto)
    a, e = str(atteso).strip().lower(), str(estratto).strip().lower()
    if a == e:
        return True
    # Testi liberi (oggetto, destinazione): basta che ci siano quasi tutte le parole attese
    attese = _parole(a)
    return bool(attese) and len(attese & _parole(e)) / len(attese) >= 0.75


def confronta(atteso: dict, estratto: dict) -> list[dict]:
    return [{"campo": k, "atteso": v, "estratto": estratto.get(k), "ok": corrisponde(k, v, estratto.get(k))}
            for k, v in atteso.items()]
