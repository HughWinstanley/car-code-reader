"""
Safety recalls for a vehicle, from the U.S. government's free NHTSA database (api.nhtsa.gov).

NHTSA names models its own way ("F-250 SD", "SILVERADO"), so the app's model name is matched loosely
against NHTSA's list for that make and year. With a VIN, NHTSA's own decoder gives the exact model.
"""

import json
import re
import urllib.parse

import updater  # its _fetch uses the Mac's built-in curl, which trusts the system's certificates

API = "https://api.nhtsa.gov"
VPIC = "https://vpic.nhtsa.dot.gov/api/vehicles"


def _get(url):
    return json.loads(updater._fetch(url, timeout=20).decode("utf-8"))


def _norm(text):
    t = (text or "").upper().replace("SUPER DUTY", "SD").replace("HEAVY DUTY", "HD")
    return re.sub(r"[^A-Z0-9]", "", t)


def _variants(model):
    """'Silverado 2500 / 2500HD' -> ['SILVERADO2500', 'SILVERADO2500HD']; drops '(...)' notes."""
    model = re.sub(r"\(.*?\)", "", model or "")
    parts = [p.strip() for p in model.split("/") if p.strip()]
    if not parts:
        return []
    first_word = parts[0].split()[0]
    out = []
    for p in parts:
        if p[:1].isdigit():  # '2500HD' -> 'Silverado 2500HD'
            p = f"{first_word} {p}"
        out.append(_norm(p))
    return [v for v in out if v]


def _same_line(extra):
    """What's left over between two names only counts as the same vehicle if it's a size or duty rating
    ('2500', 'HD', 'SD', 'PICKUP'), not another model ('SPORT TRAC', 'MAXX')."""
    return re.fullmatch(r"(\d+|HD|SD|PICKUP|TRUCK)*", extra) is not None


def matching_models(model, nhtsa_models):
    """NHTSA model names that are the same vehicle as `model` (or a broader name for it)."""
    found = []
    for name in nhtsa_models:
        n = _norm(name)
        if len(n) < 3:
            continue
        for v in _variants(model):
            if n == v or (v.startswith(n) and _same_line(v[len(n):])) or (n.startswith(v) and _same_line(n[len(v):])):
                found.append(name)
                break
    return found


def decode_vin(vin):
    """-> (make, model, year) from NHTSA's VIN decoder, or None."""
    d = _get(f"{VPIC}/DecodeVinValues/{urllib.parse.quote(vin)}?format=json")
    r = (d.get("Results") or [{}])[0]
    make, model, year = r.get("Make", ""), r.get("Model", ""), r.get("ModelYear", "")
    return (make, model, year) if make and year else None


def models_for(make, year):
    d = _get(f"{API}/products/vehicle/models?modelYear={year}&make={urllib.parse.quote(make.upper())}"
             f"&issueType=r")
    return [r.get("model", "") for r in d.get("results", []) if r.get("model")]


def recalls_for(make, model, year):
    d = _get(f"{API}/recalls/recallsByVehicle?make={urllib.parse.quote(make.upper())}"
             f"&model={urllib.parse.quote(model)}&modelYear={year}")
    return d.get("results", [])


def find(make, model, year, vin=""):
    """-> (recalls, how_matched). Each recall: dict with campaign, date, component, summary, consequence,
    remedy, park_it. Only vehicle recalls; aftermarket equipment recalls are left out. Raises if offline."""
    if vin and len(vin) == 17:
        try:
            dec = decode_vin(vin)
            if dec:
                make, vin_model, year = dec
                model = vin_model or model
        except Exception:  # noqa: BLE001 - fall back to the picked vehicle
            pass
    if not (make and model and year):
        return [], []
    names = matching_models(model, models_for(make, year))
    seen, out = set(), []
    for name in names:
        for r in recalls_for(make, name, year):
            camp = r.get("NHTSACampaignNumber", "")
            if not camp or camp in seen or camp[2:3] != "V":  # 'V' = vehicle recall ('E' = aftermarket part)
                continue
            seen.add(camp)
            out.append({
                "campaign": camp, "date": r.get("ReportReceivedDate", ""),
                "component": (r.get("Component") or "").replace(":", " - ").title(),
                "summary": _sentence_case(r.get("Summary", "")),
                "consequence": _sentence_case(r.get("Consequence", "")),
                "remedy": _sentence_case(r.get("Remedy", "")),
                "park_it": bool(r.get("parkIt")),
            })
    out.sort(key=lambda r: r["campaign"], reverse=True)
    return out, names


def _sentence_case(text):
    """NHTSA text is ALL CAPS; make it easier to read."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if text and text.upper() == text:
        text = text.lower()
        text = re.sub(r"(^|[.!?]\s+)([a-z])", lambda m: m.group(1) + m.group(2).upper(), text)
        for word in ("nhtsa", "abs", "gm", "vin", "srs", "pcm", "ecm"):
            text = re.sub(rf"\b{word}\b", word.upper(), text)
        for word in ("ford", "chevrolet", "gmc", "general motors", "dodge", "chrysler", "toyota", "honda"):
            text = re.sub(rf"\b{word}\b", word.title(), text)
    return text


def lookup_page(vin=""):
    """NHTSA's own page that says whether recalls are still open on one exact vehicle (by VIN)."""
    return f"https://www.nhtsa.gov/recalls?vin={vin}" if vin else "https://www.nhtsa.gov/recalls"
