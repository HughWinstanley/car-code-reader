"""
Scan history: every scan is saved per vehicle, so you can see what was found before and what changed.
Kept in a small file next to the app's updates (in the user's own folder), never sent anywhere.
"""

import datetime
import json
import os

import updater

MAX_PER_VEHICLE = 50


def _path():
    return os.path.join(os.path.dirname(updater.updates_dir()), "history.json")


def load():
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []


def _write(records):
    path = _path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=1)
    os.replace(tmp, path)


def vehicle_key(vin, name):
    return vin if vin and len(vin) == 17 else (name or "Unknown vehicle")


def add(vin, name, kind, items, mil_on=None):
    """Save one scan. items: the app's problem list."""
    records = load()
    rec = {
        "when": datetime.datetime.now().isoformat(timespec="seconds"),
        "vehicle": vehicle_key(vin, name), "name": name or "Unknown vehicle", "vin": vin or "",
        "kind": kind or "all", "mil_on": mil_on,
        "codes": [{"code": i["code"], "text": i["info"]["description"], "module": i["module"],
                   "status": i["status"], "level": i["level"]} for i in items],
    }
    records.append(rec)
    mine = [r for r in records if r["vehicle"] == rec["vehicle"]]
    if len(mine) > MAX_PER_VEHICLE:
        drop = mine[0]
        records.remove(drop)
    try:
        _write(records)
    except OSError:
        pass
    return rec


def by_vehicle():
    """-> [(vehicle name, [scans newest first])], most recently scanned vehicle first."""
    groups = {}
    for r in load():
        groups.setdefault(r["vehicle"], []).append(r)
    out = []
    for key, scans in groups.items():
        scans.sort(key=lambda r: r["when"], reverse=True)
        out.append((scans[0]["name"], scans))
    out.sort(key=lambda g: g[1][0]["when"], reverse=True)
    return out


def changes(newer, older):
    """-> (new codes, gone codes) between two scans of the same vehicle."""
    a = {c["code"] for c in newer["codes"]}
    b = {c["code"] for c in older["codes"]}
    return sorted(a - b), sorted(b - a)


def clear():
    try:
        os.remove(_path())
    except OSError:
        pass
