"""
Heavy-duty trucks (semis, many buses and medium-duty trucks): SAE J1939 over CAN.

Trucks broadcast their active trouble codes about once a second in DM1 messages; codes that
were active before are asked for with a DM2 request; DM11 clears active codes. A code is an
SPN (what part) plus an FMI (how it failed). Messages longer than 8 bytes come in pieces
(a BAM announcement plus numbered data packets) which are put back together here.

Needs a 9-pin Deutsch (truck) to OBD-II cable. Works best with an OBDLink adapter, whose
receive filters keep a busy truck network from overflowing the adapter.
"""

import re
import time

# --- What the numbers mean ----------------------------------------------------------------
FMI = {
    0: "reading too high (most severe)", 1: "reading too low (most severe)",
    2: "reading erratic, intermittent or incorrect", 3: "voltage too high, or shorted to power",
    4: "voltage too low, or shorted to ground", 5: "current too low, or open circuit",
    6: "current too high, or circuit grounded", 7: "mechanical system not responding or out of adjustment",
    8: "abnormal frequency, pulse width or period", 9: "abnormal update rate",
    10: "abnormal rate of change", 11: "root cause not known", 12: "bad device or component",
    13: "out of calibration", 14: "special instructions (see maker's manual)",
    15: "reading high (least severe)", 16: "reading high (moderately severe)",
    17: "reading low (least severe)", 18: "reading low (moderately severe)",
    19: "received network data in error", 20: "reading drifted high", 21: "reading drifted low",
    31: "condition exists",
}

SPN = {
    27: "EGR valve position", 38: "Fuel level (second tank)", 51: "Throttle position",
    52: "Intercooler temperature", 84: "Vehicle speed (wheel-based)", 91: "Accelerator pedal position",
    94: "Fuel delivery pressure", 95: "Fuel filter differential pressure", 96: "Fuel level",
    97: "Water in fuel", 98: "Engine oil level", 100: "Engine oil pressure", 101: "Crankcase pressure",
    102: "Intake manifold (boost) pressure", 105: "Intake manifold temperature",
    106: "Air intake pressure", 107: "Air filter differential pressure", 108: "Barometric pressure",
    109: "Coolant pressure", 110: "Engine coolant temperature", 111: "Coolant level",
    127: "Transmission oil pressure", 157: "Fuel rail pressure", 158: "Battery voltage (key switch)",
    168: "Battery voltage", 171: "Outside air temperature", 172: "Air intake temperature",
    173: "Exhaust gas temperature", 174: "Fuel temperature", 175: "Engine oil temperature",
    177: "Transmission oil temperature", 183: "Fuel rate", 190: "Engine speed",
    412: "EGR temperature", 597: "Brake switch", 629: "Engine control module",
    639: "J1939 data network", 641: "Variable geometry turbo actuator",
    651: "Fuel injector, cylinder 1", 652: "Fuel injector, cylinder 2", 653: "Fuel injector, cylinder 3",
    654: "Fuel injector, cylinder 4", 655: "Fuel injector, cylinder 5", 656: "Fuel injector, cylinder 6",
    789: "ABS wheel sensor, axle 1 left", 790: "ABS wheel sensor, axle 1 right",
    791: "ABS wheel sensor, axle 2 left", 792: "ABS wheel sensor, axle 2 right",
    793: "ABS wheel sensor, axle 3 left", 794: "ABS wheel sensor, axle 3 right",
    1136: "Engine control module temperature", 1569: "Engine protection torque derate",
    1761: "DEF (diesel exhaust fluid) tank level", 3031: "DEF tank temperature",
    3216: "Aftertreatment NOx sensor (before SCR)", 3226: "Aftertreatment NOx sensor (after SCR)",
    3242: "DPF inlet temperature", 3246: "DPF outlet temperature", 3251: "DPF differential pressure",
    3364: "DEF quality", 3644: "Engine derate request", 3719: "DPF soot load", 3720: "DPF ash load",
    4364: "SCR conversion efficiency", 5246: "SCR operator inducement (derate warning)",
}

SOURCE = {
    0: "Engine", 1: "Engine #2", 3: "Transmission", 11: "ABS / brakes", 15: "Engine retarder",
    16: "Driveline retarder", 17: "Cruise control", 23: "Instrument cluster", 25: "Climate control",
    33: "Body controller", 41: "Exhaust retarder", 49: "Cab controller", 61: "Aftertreatment (emissions)",
}

LAMPS = ("Check engine (malfunction) lamp", "Red stop lamp", "Amber warning lamp", "Protect lamp")


def source_name(sa):
    return SOURCE.get(sa, f"Module {sa}")


def spn_name(spn):
    return SPN.get(spn, f"Part number {spn} (maker-specific; look it up)")


def describe(spn, fmi):
    return f"{spn_name(spn)}: {FMI.get(fmi, 'manufacturer-specific failure type')}"


# --- Decoding --------------------------------------------------------------------------------
def frame_parts(header_hex):
    """'18FECA00' -> (pgn, source address). PDU1 messages (PF < 240) carry a destination, not a PGN byte."""
    ident = int(header_hex, 16)
    dp = (ident >> 24) & 0x01
    pf, ps, sa = (ident >> 16) & 0xFF, (ident >> 8) & 0xFF, ident & 0xFF
    pgn = (dp << 16) | (pf << 8) | (ps if pf >= 240 else 0)
    return pgn, sa


def parse_lines(lines):
    """Monitor/response lines (headers on, spaces off) -> [(pgn, sa, data bytes)]."""
    out = []
    for line in lines:
        h = line.replace(" ", "").upper()
        if len(h) >= 10 and re.fullmatch(r"[0-9A-F]+", h) and len(h) % 2 == 0:
            pgn, sa = frame_parts(h[:8])
            out.append((pgn, sa, bytes.fromhex(h[8:])))
    return out


def assemble(frames, wanted):
    """Put single frames and BAM multi-packet messages back together.
    -> {(pgn, sa): data} for PGNs in `wanted` (latest copy wins)."""
    msgs, pending = {}, {}
    for pgn, sa, data in frames:
        if pgn in wanted and len(data) >= 2:
            msgs[(pgn, sa)] = data
        elif pgn == 0xEC00 and len(data) >= 8 and data[0] in (0x20, 0x10):  # TP.CM (BAM or RTS)
            target = data[5] | (data[6] << 8) | (data[7] << 16)
            if target in wanted:
                pending[sa] = {"pgn": target, "size": data[1] | (data[2] << 8), "count": data[3], "parts": {}}
        elif pgn == 0xEB00 and sa in pending and data:  # TP.DT
            p = pending[sa]
            p["parts"][data[0]] = data[1:8]
            if len(p["parts"]) >= p["count"]:
                body = b"".join(p["parts"][i] for i in sorted(p["parts"]))[:p["size"]]
                msgs[(p["pgn"], sa)] = body
                del pending[sa]
    return msgs


def decode_dm(data):
    """DM1/DM2 payload -> (lamps dict, [(spn, fmi, occurrences)])."""
    lamps = {}
    if len(data) >= 2:
        for i, name in enumerate(LAMPS):
            lamps[name] = ((data[0] >> (6 - 2 * i)) & 0x03) == 1
    dtcs = []
    for i in range(2, len(data) - 3, 4):
        b0, b1, b2, b3 = data[i:i + 4]
        spn = b0 | (b1 << 8) | ((b2 & 0xE0) << 11)
        fmi = b2 & 0x1F
        if spn == 0 or (b0, b1, b2) == (0xFF, 0xFF, 0xFF):
            continue
        dtcs.append((spn, fmi, b3 & 0x7F))
    return lamps, dtcs


DM1, DM2, DM3, DM11, VIN = 0xFECA, 0xFECB, 0xFECC, 0xFED3, 0xFEEC

# Live data: PGN -> [(key, name, decoder, unit)]
LIVE = {
    0xF004: [("rpm", "Engine RPM", lambda d: (d[3] | d[4] << 8) * 0.125 if d[4] != 0xFF else None, "rpm")],
    0xFEEE: [("ect", "Coolant temperature", lambda d: d[0] - 40 if d[0] != 0xFF else None, "°C")],
    0xFEEF: [("oilp", "Oil pressure", lambda d: d[3] * 4 if d[3] != 0xFF else None, "kPa")],
    0xFEF1: [("speed", "Vehicle speed", lambda d: (d[1] | d[2] << 8) / 256 if d[2] != 0xFF else None, "km/h")],
    0xFEF7: [("volts", "Battery voltage", lambda d: (d[4] | d[5] << 8) * 0.05 if d[5] != 0xFF else None, "V")],
    0xFEFC: [("fuel", "Fuel level", lambda d: d[1] * 0.4 if d[1] != 0xFF else None, "%")],
    0xFE56: [("def", "DEF level", lambda d: d[0] * 0.4 if d[0] != 0xFF else None, "%")],
}
LIVE_NAMES = [(k, n) for rows in LIVE.values() for k, n, _f, _u in rows]


# --- Talking to the adapter -----------------------------------------------------------------
def _filters(elm, pgns):
    """OBDLink receive filters: only the messages we care about (plus transport packets)."""
    if not elm.is_stn:
        return
    elm.send("STFAC")
    for pgn in pgns:
        pf, ps = (pgn >> 8) & 0xFF, pgn & 0xFF
        if pf >= 240:
            elm.send("STFPA 00%02X%02X00,00FFFF00" % (pf, ps))
        else:
            elm.send("STFPA 00%02X0000,00FF0000" % pf)


def monitor(elm, seconds, pgns):
    with elm.lock:
        _filters(elm, list(pgns) + [0xEC00, 0xEB00])
        lines = elm.monitor("STMA" if elm.is_stn else "ATMA", seconds)
    return parse_lines(lines)


def initialize(elm):
    """Connect to a truck's J1939 network: 250 kbps first, then 500 kbps (2016+ trucks with a green 9-pin)."""
    elm.send("ATZ", timeout=4)
    for c in ("ATE0", "ATL0", "ATS0", "ATH1"):
        elm.send(c)
    elm.version = " ".join(elm.send("ATI")) or "unknown"
    sti = " ".join(elm.send("STI", timeout=1.5))
    elm.is_stn = "STN" in sti.upper()
    if elm.is_stn:
        elm.version = (" ".join(elm.send("STDI", timeout=1.5)) or "OBDLink") + f" ({sti})"
    for rate in (250, 500):
        if elm.is_stn:
            elm.send("STP42")
            if rate == 500:
                elm.send("STPBR 500000")
        else:
            if rate == 500:
                break
            elm.send("ATSPA")
        elm.send("ATCAF0")
        elm.send("ATJHF0")
        frames = monitor(elm, 1.2, [DM1, 0xF004, 0xFEEE, 0xFEF1, 0xFEF7])
        if frames:
            elm.protocol, elm.protocol_name = "J", f"SAE J1939 heavy-duty, {rate} kbps"
            elm.ecus = sorted({sa for _p, sa, _d in frames})
            return
    raise ConnectionError(
        "The adapter is working, but no heavy-duty truck network answered.\n\n"
        "- Use a 9-pin truck to OBD-II cable (a green 9-pin port on 2016+ trucks)\n"
        "- Turn the key to ON\n"
        "- Most US trucks are 12 V; the OBDLink EX isn't made for 24 V systems")


def _request(elm, pgn, dest=0xFF):
    """Send a J1939 Request (PGN 59904) for `pgn`; return the raw lines that came back."""
    with elm.lock:
        _filters(elm, [pgn, 0xEC00, 0xEB00, 0xE800])
        elm.send("ATCP18")
        elm.send("ATSHEA%02XF9" % dest)
        lines = elm.send("%02X%02X%02X" % (pgn & 0xFF, (pgn >> 8) & 0xFF, (pgn >> 16) & 0xFF), timeout=2)
        lines += elm.monitor("STMA" if elm.is_stn else "ATMA", 0.8)
    return parse_lines(lines)


def read_codes(elm):
    """-> list of {sa, name, lamps, active: [...], previous: [...]} for every module heard from."""
    dm1 = assemble(monitor(elm, 2.6, [DM1]), {DM1})
    dm2 = assemble(_request(elm, DM2), {DM2})
    modules = {}
    for (pgn, sa), data in list(dm1.items()) + list(dm2.items()):
        m = modules.setdefault(sa, {"sa": sa, "name": source_name(sa), "lamps": {}, "active": [], "previous": []})
        lamps, dtcs = decode_dm(data)
        if pgn == DM1:
            m["lamps"], m["active"] = lamps, dtcs
        else:
            m["previous"] = dtcs
    return sorted(modules.values(), key=lambda m: m["sa"])


def clear_codes(elm):
    """DM11 clears active codes, DM3 clears previously active ones (all modules, global request)."""
    _request(elm, DM11)
    time.sleep(0.3)
    _request(elm, DM3)
    return True


def read_vin(elm):
    msgs = assemble(_request(elm, VIN), {VIN})
    for (_p, _sa), data in sorted(msgs.items(), key=lambda kv: kv[0][1]):
        vin = data.decode("ascii", "ignore").split("*")[0].strip()
        if len(vin) >= 11:
            return vin
    return ""


def read_live(elm, seconds=1.0):
    """-> {key: formatted text} from whatever the truck broadcast during `seconds`."""
    from obd_core import format_value
    values = {}
    for pgn, sa, data in monitor(elm, seconds, list(LIVE)):
        for key, _name, fn, unit in LIVE.get(pgn, []):
            try:
                v = fn(data)
            except IndexError:
                v = None
            if v is not None and (key not in values or sa == 0):
                values[key] = format_value(v, unit) if unit != "%" else f"{v:.0f} %"
    return values


# --- Pretend semi truck for Demo mode ---------------------------------------------------------
class DemoSemiTransport:
    """Behaves like an OBDLink on a truck's J1939 network: an engine with two active codes sent in
    pieces (BAM), an ABS module with one, a transmission with none, and live engine data."""

    VIN = "1XKYD49X0DJ000000"

    def __init__(self):
        self._out, self._mon, self._t0 = b"", None, time.time()
        self._hdr, self._filters = "", []
        self._dm1 = {0x00: [(3719, 16, 3), (1761, 18, 1)], 0x0B: [(789, 5, 2)], 0x03: []}
        self._dm2 = {0x00: [(100, 1, 1)]}

    # adapter plumbing -------------------------------------------------------------------
    def write(self, data):
        if self._mon is not None:  # any character stops monitoring
            self._mon = None
            self._out += b"\rSTOPPED\r\r>"
            return
        cmd = data.decode("ascii", "ignore").strip().upper().replace(" ", "")
        if cmd in ("STMA", "ATMA"):
            self._mon = time.time()
            self._last = self._mon - 0.001
            return
        self._out += ("\r".join(self._respond(cmd)) + "\r\r>").encode()

    def read(self):
        time.sleep(0.01)
        if self._mon is not None:
            now = time.time()
            self._out += "".join(f + "\r" for f in self._frames_between(self._last, now)).encode()
            self._last = now
        out, self._out = self._out, b""
        return out

    def flush_input(self):
        self._out = b""

    def close(self):
        pass

    # behaviour --------------------------------------------------------------------------
    def _respond(self, c):
        if c in ("ATZ", "ATWS"):
            self._filters = []
            return ["ELM327 v1.5 (demo)"]
        if c == "ATI":
            return ["ELM327 v1.5"]
        if c == "STI":
            return ["STN2232 v5.10.3"]
        if c == "STDI":
            return ["OBDLink EX r1.0.0 (demo semi)"]
        if c == "ATRV":
            return ["13.8V"]
        if c == "STFAC":
            self._filters = []
            return ["OK"]
        if c.startswith("STFPA"):
            pat, _, mask = c[5:].partition(",")
            self._filters.append((int(pat, 16), int(mask, 16)))
            return ["OK"]
        if c.startswith("ATSH"):
            self._hdr = c[4:]
            return ["OK"]
        if c.startswith("AT") or c.startswith("ST"):
            return ["OK"]
        if self._hdr.startswith("EA") and len(c) == 6:
            pgn = int(c[4:6] + c[2:4] + c[0:2], 16)
            return self._answer_request(pgn) or ["NO DATA"]
        return ["NO DATA"]

    def _passes(self, ident):
        return not self._filters or any((ident & m) == (p & m) for p, m in self._filters)

    def _frame(self, ident, data):
        data = bytes(data) + b"\xFF" * (8 - len(data))
        return "%08X" % ident + data.hex().upper() if self._passes(ident) else None

    def _message(self, pgn, sa, payload, prio=6):
        """Single frame, or BAM + data packets for longer payloads."""
        if len(payload) <= 8:
            f = self._frame((prio << 26) | ((pgn & 0x3FFFF) << 8) | sa, payload)
            return [f] if f else []
        packets = (len(payload) + 6) // 7
        cm = [0x20, len(payload) & 0xFF, len(payload) >> 8, packets, 0xFF, pgn & 0xFF, (pgn >> 8) & 0xFF, pgn >> 16]
        out = [self._frame((7 << 26) | (0xECFF << 8) | sa, cm)]
        for i in range(packets):
            out.append(self._frame((7 << 26) | (0xEBFF << 8) | sa, [i + 1] + list(payload[i * 7:(i + 1) * 7])))
        return [f for f in out if f]

    @staticmethod
    def _dm_payload(dtcs, amber):
        lamp = 0x04 if amber else 0x00  # amber warning lamp on
        if not dtcs:
            return bytes([lamp, 0xFF, 0, 0, 0, 0, 0xFF, 0xFF])
        out = bytearray([lamp, 0xFF])
        for spn, fmi, oc in dtcs:
            out += bytes([spn & 0xFF, (spn >> 8) & 0xFF, ((spn >> 11) & 0xE0) | fmi, oc & 0x7F])
        return bytes(out)

    def _frames_between(self, t_from, t_to):
        out = []
        for tick in range(int(t_from * 10) + 1, int(t_to * 10) + 1):  # 10 ticks per second
            t = tick / 10 - self._t0
            rpm = 650 + 900 * max(0.0, ((t % 12) - 4) / 8)
            out += self._message(0xF004, 0x00, [0xF0, 0x7D, 0x7D, int(rpm * 8) & 0xFF, int(rpm * 8) >> 8, 0, 0, 0], 3)
            if tick % 10 == 0:  # once a second: DM1 from each module plus slow data
                for sa, dtcs in self._dm1.items():
                    out += self._message(DM1, sa, self._dm_payload(dtcs, bool(dtcs)))
                out += self._message(0xFEEE, 0x00, [88 + 40, 0, 0, 0, 0, 0, 0, 0])
                out += self._message(0xFEEF, 0x00, [0, 0, 0, 72, 0, 0, 0, 0])
                speed = int(max(0.0, (t % 30) - 10) * 3.2 * 256)
                out += self._message(0xFEF1, 0x00, [0, speed & 0xFF, speed >> 8, 0, 0, 0, 0, 0])
                out += self._message(0xFEF7, 0x00, [0, 0, 0, 0, 276 & 0xFF, 276 >> 8, 0, 0])
                out += self._message(0xFEFC, 0x00, [0, 158, 0, 0, 0, 0, 0, 0])
                out += self._message(0xFE56, 0x3D, [70, 0, 0, 0, 0, 0, 0, 0])
        return out

    def _answer_request(self, pgn):
        if pgn == DM2:
            out = []
            for sa, dtcs in self._dm2.items():
                out += self._message(DM2, sa, self._dm_payload(dtcs, False))
            return out
        if pgn == DM11:
            self._dm1 = {sa: [] for sa in self._dm1}
            return self._message(0xE800, 0x00, [0, 0xFF, 0xFF, 0xFF, 0xF9, 0xD3, 0xFE, 0x00])
        if pgn == DM3:
            self._dm2 = {}
            return self._message(0xE800, 0x00, [0, 0xFF, 0xFF, 0xFF, 0xF9, 0xCC, 0xFE, 0x00])
        if pgn == VIN:
            return self._message(VIN, 0x00, (self.VIN + "*").encode())
        return []
