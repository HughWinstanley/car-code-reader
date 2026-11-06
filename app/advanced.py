"""
Deeper OBD-II data that professional scan tools show, all read-only:

- Self-test results (mode $06): the numbers behind each emissions self-test, with the pass/fail limits,
  including misfire counts for each cylinder. Standard format on CAN vehicles (about 2008 and newer).
- Module info (mode $09): calibration IDs, calibration verification numbers, module names and
  in-use performance counters (how often each self-test has run).
"""

# --- Self-test results (mode $06) ------------------------------------------------------------------
def _mid_names():
    n = {}
    for i in range(16):  # $01-$10: oxygen sensors, $41-$50: their heaters
        bank, sensor = i // 4 + 1, i % 4 + 1
        n[0x01 + i] = f"Oxygen sensor, bank {bank} sensor {sensor}"
        n[0x41 + i] = f"Oxygen sensor heater, bank {bank} sensor {sensor}"
    for b in range(4):
        n[0x21 + b] = f"Catalytic converter, bank {b + 1}"
        n[0x31 + b] = f"EGR / valve timing, bank {b + 1}"
        n[0x35 + b] = f"Variable valve timing, bank {b + 1}"
        n[0x61 + b] = f"Heated catalyst, bank {b + 1}"
        n[0x71 + b] = f"Secondary air system {b + 1}"
        n[0x81 + b] = f"Fuel system, bank {b + 1}"
    n.update({
        0x39: "EVAP leak test (gas cap off)", 0x3A: "EVAP leak test (0.090 inch)",
        0x3B: "EVAP leak test (0.040 inch)", 0x3C: "EVAP leak test (0.020 inch)", 0x3D: "EVAP purge flow",
        0x85: "Boost pressure control, bank 1", 0x86: "Boost pressure control, bank 2",
        0x90: "NOx trap, bank 1", 0x91: "NOx trap, bank 2", 0x98: "NOx catalyst, bank 1",
        0x99: "NOx catalyst, bank 2", 0xA1: "Misfire, all cylinders",
        0xB0: "Diesel particulate filter, bank 1", 0xB1: "Diesel particulate filter, bank 2",
    })
    for c in range(12):
        n[0xA2 + c] = f"Misfire, cylinder {c + 1}"
    return n


MID_NAMES = _mid_names()
MISFIRE_TIDS = {0x0B: "average of the last 10 drives", 0x0C: "this drive or the last one"}

# Unit and scaling IDs (SAE J1979): id -> (scale, offset, unit). Signed versions are 0x80 + id.
UNITS = {
    0x01: (1, 0, ""), 0x02: (0.1, 0, ""), 0x03: (0.01, 0, ""), 0x04: (0.001, 0, ""),
    0x05: (0.0000305, 0, ""), 0x06: (0.000305, 0, ""), 0x07: (0.25, 0, "rpm"), 0x08: (0.01, 0, "km/h"),
    0x09: (1, 0, "km/h"), 0x0A: (0.122, 0, "mV"), 0x0B: (0.001, 0, "V"), 0x0C: (0.01, 0, "V"),
    0x0D: (0.00390625, 0, "mA"), 0x0E: (0.001, 0, "A"), 0x0F: (0.01, 0, "A"), 0x10: (1, 0, "ms"),
    0x11: (100, 0, "ms"), 0x12: (1, 0, "s"), 0x13: (1, 0, "mΩ"), 0x14: (1, 0, "Ω"), 0x15: (1, 0, "kΩ"),
    0x16: (0.1, -40, "°C"), 0x17: (0.01, 0, "kPa"), 0x18: (0.0117, 0, "kPa"), 0x19: (0.079, 0, "kPa"),
    0x1A: (10, 0, "kPa"), 0x1C: (0.01, 0, "°"), 0x1D: (0.5, 0, "°"), 0x1E: (0.0000305, 0, "ratio"),
    0x1F: (0.05, 0, "air/fuel"), 0x20: (0.0039062, 0, "ratio"), 0x21: (1, 0, "mHz"), 0x22: (1, 0, "Hz"),
    0x23: (1, 0, "kHz"), 0x24: (1, 0, "counts"), 0x25: (1, 0, "km"), 0x27: (0.01, 0, "g/s"),
    0x28: (1, 0, "g/s"), 0x2B: (1, 0, "switches"), 0x2F: (0.01, 0, "%"), 0x31: (0.001, 0, "L"),
    0x34: (1, 0, "min"), 0x35: (10, 0, "ms"),
}


def _value(raw, uas):
    """Raw 16-bit number -> (value, unit). Unknown units stay as plain numbers."""
    signed = uas >= 0x80
    if signed and raw >= 0x8000:
        raw -= 0x10000
    scale, offset, unit = UNITS.get(uas & 0x7F if signed else uas, (1, 0, ""))
    return raw * scale + offset, unit


def _supported(elm, mode):
    """Which IDs ($01-$FF) a mode supports, from its $00, $20, $40 ... support bitmaps."""
    sup = set()
    base = 0
    while base <= 0xE0:
        got = False
        res = elm.request("%02X%02X" % (mode, base))
        for msgs in res.values():
            for m in msgs:
                if len(m) >= 6 and m[0] == mode + 0x40 and m[1] == base:
                    bits = int.from_bytes(m[2:6], "big")
                    sup.update(base + i + 1 for i in range(32) if bits & (1 << (31 - i)))
                    got = True
        if not got or (base + 0x20) not in sup:
            break
        base += 0x20
    return sorted(i for i in sup if i % 0x20)


def self_tests(elm, progress=None):
    """-> list of results: {mid, name, tid, value, low, high, unit, passed, misfire}. CAN vehicles only."""
    if not getattr(elm, "is_can", False):
        raise ValueError("Self-test results in the standard format are only on vehicles that use CAN "
                         "(most 2008 and newer). Older vehicles keep them in maker-specific formats.")
    mids = _supported(elm, 0x06)
    out = []
    for n, mid in enumerate(mids):
        if progress:
            progress(n, len(mids))
        res = elm.request("06%02X" % mid)
        for msgs in res.values():
            for m in msgs:
                if len(m) < 2 or m[0] != 0x46 or m[1] != mid:
                    continue
                body = m[1:]  # records of 9 bytes: MID, TID, unit, value, minimum, maximum
                for i in range(0, len(body) - 8, 9):
                    if body[i] != mid:
                        continue
                    tid, uas = body[i + 1], body[i + 2]
                    raw = [int.from_bytes(body[i + 3 + 2 * k:i + 5 + 2 * k], "big") for k in range(3)]
                    val, unit = _value(raw[0], uas)
                    low, _ = _value(raw[1], uas)
                    high, _ = _value(raw[2], uas)
                    out.append({"mid": mid, "name": MID_NAMES.get(mid, f"Test group ${mid:02X}"), "tid": tid,
                                "value": val, "low": low, "high": high, "unit": unit,
                                "passed": low <= val <= high,
                                "misfire": MISFIRE_TIDS.get(tid) if 0xA2 <= mid <= 0xAD else None})
    return out


def misfire_summary(results):
    """-> {cylinder number: (count this/last drive, 10-drive average)} from the self-test results."""
    cyl = {}
    for r in results:
        if 0xA2 <= r["mid"] <= 0xAD and r["tid"] in (0x0B, 0x0C):
            c = r["mid"] - 0xA1
            cur, avg = cyl.get(c, (None, None))
            if r["tid"] == 0x0C:
                cur = r["value"]
            else:
                avg = r["value"]
            cyl[c] = (cur, avg)
    return dict(sorted(cyl.items()))


# --- Module info (mode $09) ------------------------------------------------------------------------
IPT_SPARK = [("conditions", "Times the driving conditions for self-tests were met"),
             ("ignitions", "Ignition cycles counted"),
             ("Catalyst, bank 1", None), ("Catalyst, bank 2", None), ("Oxygen sensor, bank 1", None),
             ("Oxygen sensor, bank 2", None), ("EGR / valve timing", None), ("Secondary air", None),
             ("EVAP system", None), ("Rear oxygen sensor, bank 1", None), ("Rear oxygen sensor, bank 2", None)]


def _mode9(elm, info_type):
    """-> {module: data bytes} for one mode $09 item, joined across messages."""
    res = elm.request("09%02X" % info_type, timeout=8)
    out = {}
    for ecu, msgs in res.items():
        parts = [m for m in msgs if len(m) > 3 and m[0] == 0x49 and m[1] == info_type]
        if not parts:
            continue
        if elm.is_can:  # one message: 49 tt count data...
            out[ecu] = bytes(parts[0][3:])
        else:           # older protocols: 49 tt seq data(4), one message per piece
            out[ecu] = b"".join(bytes(m[3:]) for m in sorted(parts, key=lambda m: m[2]))
    return out


def _text(b):
    return "".join(chr(c) for c in b if 32 <= c < 127).strip()


def module_info(elm):
    """-> {module: {"name", "calids", "cvns", "usage"}}. Missing pieces are simply left out."""
    info = {}

    def mod(ecu):
        return info.setdefault(ecu, {"name": "", "calids": [], "cvns": [], "usage": []})

    for ecu, d in _mode9(elm, 0x0A).items():
        mod(ecu)["name"] = _text(d[:20].replace(b"\x00", b" ")).replace(" -", " - ")
    for ecu, d in _mode9(elm, 0x04).items():
        mod(ecu)["calids"] = [t for t in (_text(d[i:i + 16]) for i in range(0, len(d), 16)) if t]
    for ecu, d in _mode9(elm, 0x06).items():
        mod(ecu)["cvns"] = [d[i:i + 4].hex().upper() for i in range(0, len(d) - 3, 4)]
    for ecu, d in _mode9(elm, 0x08).items():
        counts = [int.from_bytes(d[i:i + 2], "big") for i in range(0, len(d) - 1, 2)]
        usage = []
        if len(counts) >= 2:
            usage.append((IPT_SPARK[0][1], str(counts[0])))
            usage.append((IPT_SPARK[1][1], str(counts[1])))
        for k, (name, _) in enumerate(IPT_SPARK[2:]):
            i = 2 + 2 * k
            if i + 1 < len(counts) and counts[i + 1]:
                done, chances = counts[i], counts[i + 1]
                usage.append((name, f"ran {done} times in {chances} chances"))
        mod(ecu)["usage"] = usage
    return info


# --- Used car check: everything here only reads from the vehicle -----------------------------------
RECENT_CLEAR_MILES = 100   # codes cleared closer than this can hide a problem from a buyer
RECENT_CLEAR_WARMUPS = 10
KM_TO_MILES = 0.621371


def used_car_verdict(rows):
    """rows: (label, value, words, level) with level good, warn, bad or info -> (headline, explanation)."""
    bad = [r for r in rows if r[3] == "bad"]
    warn = [r for r in rows if r[3] == "warn"]
    if bad:
        return f"{len(bad)} thing{'s' if len(bad) != 1 else ''} to sort out first", \
            "Get these explained or priced before you agree to buy."
    if warn:
        return f"{len(warn)} thing{'s' if len(warn) != 1 else ''} to ask about", \
            "Nothing failed outright, but ask the seller about these."
    return "Nothing stood out", "The computers didn't report a problem. A mechanic should still inspect it."


def used_car_check(elm):
    """Read what a buyer wants to know. -> (rows, headline, explanation)"""
    from obd_core import decode_readiness

    def number(pid):
        d = elm.query_pid(1, pid)
        return int.from_bytes(d[:2], "big") if d and len(d) >= 2 else None

    rows = []
    vin = elm.read_vin() or ""
    rows.append(("VIN", vin, "Compare it to the title and the dash plate", "info") if len(vin) == 17 else
                ("VIN", "Not reported", "Older vehicles may not report it. Check the dash plate", "warn"))
    d = elm.query_pid(1, 0xA6)
    if d and len(d) >= 4:
        miles = int.from_bytes(d[:4], "big") / 10 * KM_TO_MILES
        rows.append(("Odometer in the computer", f"{miles:,.0f} miles", "Compare it to the dash", "info"))
    ready = elm.query_pid(1, 1)
    mil_on, not_ready = None, []
    if ready and len(ready) >= 4:
        mil_on, _count, _diesel, monitors = decode_readiness(ready)
        not_ready = [m[0] for m in monitors[3:] if m[1] and m[2]]
        rows.append(("Check-engine light", "On" if mil_on else "Off",
                     "Find out why before buying" if mil_on else "Off", "bad" if mil_on else "good"))
    for mode, label, level, words in (("03", "Stored codes", "bad", "Look these up before buying"),
                                      ("07", "Pending codes", "warn", "Seen once, may come back"),
                                      ("0A", "Permanent codes", "bad", "Only clear once the repair is proven")):
        codes = sorted({c for _e, c in elm.read_dtcs(mode)})
        rows.append((label, ", ".join(codes), words, level) if codes else (label, "None", "None", "good"))
    far, warm = number(0x31), elm.query_pid(1, 0x30)
    warmups = warm[0] if warm else None
    if far is not None:
        miles = far * KM_TO_MILES
        recent = miles < RECENT_CLEAR_MILES or (warmups is not None and warmups < RECENT_CLEAR_WARMUPS)
        rows.append(("Driven since codes were cleared", f"{miles:,.0f} miles",
                     "Cleared recently. This can hide a problem" if recent else "Not recently cleared",
                     "warn" if recent else "good"))
    if warmups is not None:
        rows.append(("Warm-ups since codes were cleared", str(warmups), "Part of the same check", "info"))
    with_light = number(0x21)
    if with_light:
        rows.append(("Driven with the light on", f"{with_light * KM_TO_MILES:,.0f} miles", "Ask why it wasn't fixed", "warn"))
    if ready and len(ready) >= 4:
        rows.append(("Smog self-tests unfinished", ", ".join(not_ready) if not_ready else "None",
                     "Often means codes were cleared or the battery was off" if not_ready else "All finished",
                     "warn" if not_ready else "good"))
    return (rows,) + used_car_verdict(rows)


# --- Trip meter: fuel economy from the air the engine uses, and a 0-60 timer -------------------------
GRAMS_PER_GALLON = 2801.18   # gasoline, 6.17 lb per gallon
AIR_FUEL = 14.7
MPH_60_IN_KMH = 96.56


class TripMeter:
    """Feed it speed and mass air flow over time. Fuel figures are gasoline estimates."""

    def __init__(self):
        self.miles = self.gallons = 0.0
        self.instant_mpg = None
        self.best_0_60 = self.last_0_60 = None
        self._last, self._armed, self._launch = None, False, None

    def update(self, now, kmh, maf=None):
        if self._last is not None:
            dt = now - self._last
            self.miles += kmh * KM_TO_MILES * dt / 3600
            if maf:
                self.gallons += maf / AIR_FUEL / GRAMS_PER_GALLON * dt
        self._last = now
        self.instant_mpg = (kmh * KM_TO_MILES) / (maf * 3600 / AIR_FUEL / GRAMS_PER_GALLON) if maf else None
        if kmh < 1:
            self._armed, self._launch = True, None
        elif self._armed:
            if self._launch is None:
                self._launch = now
            if kmh >= MPH_60_IN_KMH:
                self.last_0_60 = now - self._launch
                self.best_0_60 = min(self.best_0_60 or self.last_0_60, self.last_0_60)
                self._armed, self._launch = False, None

    @property
    def average_mpg(self):
        return self.miles / self.gallons if self.gallons else None


# --- Freeze frame in plain English --------------------------------------------------------------
def freeze_notes(rows):
    """Clues from a freeze frame's readings, as sentences. rows: [(name, formatted value), ...]"""
    import re
    table = dict(rows)

    def num(name):
        text = table.get(name) or ""
        m = re.search(r"(-?[0-9]+(?:\.[0-9]+)?)\s*°C", text) or re.search(r"(-?[0-9]+(?:\.[0-9]+)?)", text)
        return float(m.group(1)) if m else None

    def first(name):
        m = re.search(r"-?[0-9]+", table.get(name) or "")
        return int(m.group(0)) if m else None

    notes = []
    rpm, speed, coolant, load = num("Engine RPM"), first("Vehicle speed"), num("Coolant temperature"), num("Engine load")
    if rpm is not None and rpm < 50:
        notes.append("The engine wasn't running when this was saved.")
    elif rpm is not None and speed:
        notes.append(f"The vehicle was moving at {speed} mph with the engine at {rpm:.0f} rpm.")
    elif rpm is not None and speed == 0:
        notes.append("The engine was idling with the vehicle stopped." if rpm < 1500
                     else f"The vehicle was stopped with the engine revving at {rpm:.0f} rpm.")
    if load is not None and load >= 80:
        notes.append(f"The engine was working hard ({load:.0f}% load), so think about problems that show up under "
                     "power, like weak spark or low fuel pressure.")
    cold = coolant is not None and coolant < 60
    if cold:
        notes.append("The engine was still cold, so think about problems that only show up before it warms up.")
    elif coolant is not None and coolant >= 112:
        notes.append("The engine was running hot, so check the coolant level and cooling system first.")
    elif coolant is not None and coolant >= 75:
        notes.append("The engine was fully warmed up.")
    trims = []
    for bank in (1, 2):
        short, long_ = num(f"Short-term fuel trim (bank {bank})"), num(f"Long-term fuel trim (bank {bank})")
        if short is not None or long_ is not None:
            trims.append((bank, (short or 0) + (long_ or 0)))
    for bank, total in trims:
        if total >= 10:
            notes.append(f"Fuel trim on bank {bank} was {total:+.0f}%. The computer was adding fuel, which usually "
                         "means too much air or too little fuel, like a vacuum leak, dirty air flow sensor or weak "
                         "fuel pump.")
        elif total <= -10:
            notes.append(f"Fuel trim on bank {bank} was {total:+.0f}%. The computer was taking fuel away, which "
                         "usually means too much fuel, like a leaking injector or high fuel pressure.")
    if rpm is not None and rpm < 50:  # trims mean nothing with the engine off
        return [n for n in notes if not n.startswith("Fuel trim")]
    if trims and not cold and all(abs(t) < 10 for _b, t in trims):
        notes.append("Fuel trims looked normal, so a fuel mixture problem is less likely.")
    return notes
