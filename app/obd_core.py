#!/usr/bin/env python3
"""
Car Code Reader - vehicle communication (no window code)
========================================================
Reads and clears diagnostic trouble codes - the check-engine codes on any 1996+ car,
and on most CAN cars (roughly 2008+) also ABS, airbag, body and other module codes.
Also shows live sensor data, emissions readiness, freeze frame and the VIN.

Works with ELM327-compatible OBD-II adapters over USB, Bluetooth or Wi-Fi
(OBDLink EX / MX+ recommended). Has a Demo mode so you can try it without a car.

Requires Python 3.8+ and pyserial:   pip install pyserial
Run:                                  python car_code_reader.py
"""

import math
import os
import queue
import re
import socket
import sys
import threading
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:  # Wi-Fi and Demo mode still work without pyserial
    serial = None

from dtc_database import describe_dtc, uds_status_text, decode_dtc_bytes

APP_NAME = "Car Code Reader"
CONN_SERIAL = "USB / Bluetooth (serial port)"
CONN_WIFI = "Wi-Fi adapter"
CONN_DEMO = "Demo mode (no car needed)"
CONN_DEMO_OLD = "Demo mode - 2004 GM truck"

# ----------------------------------------------------------------------------
# Live-data definitions:  PID -> (name, decoder, unit)
# ----------------------------------------------------------------------------
PIDS = {
    0x0C: ("Engine RPM", lambda d: (d[0] * 256 + d[1]) / 4, "rpm"),
    0x0D: ("Vehicle speed", lambda d: d[0], "km/h"),
    0x05: ("Coolant temperature", lambda d: d[0] - 40, "°C"),
    0x0F: ("Intake air temperature", lambda d: d[0] - 40, "°C"),
    0x5C: ("Engine oil temperature", lambda d: d[0] - 40, "°C"),
    0x04: ("Engine load", lambda d: d[0] * 100 / 255, "%"),
    0x11: ("Throttle position", lambda d: d[0] * 100 / 255, "%"),
    0x0B: ("Intake manifold pressure", lambda d: d[0], "kPa"),
    0x10: ("Mass air flow", lambda d: (d[0] * 256 + d[1]) / 100, "g/s"),
    0x06: ("Short-term fuel trim (bank 1)", lambda d: (d[0] - 128) * 100 / 128, "%"),
    0x07: ("Long-term fuel trim (bank 1)", lambda d: (d[0] - 128) * 100 / 128, "%"),
    0x08: ("Short-term fuel trim (bank 2)", lambda d: (d[0] - 128) * 100 / 128, "%"),
    0x09: ("Long-term fuel trim (bank 2)", lambda d: (d[0] - 128) * 100 / 128, "%"),
    0x0E: ("Ignition timing advance", lambda d: d[0] / 2 - 64, "°"),
    0x2F: ("Fuel level", lambda d: d[0] * 100 / 255, "%"),
    0x42: ("Control module voltage", lambda d: (d[0] * 256 + d[1]) / 1000, "V"),
    0x1F: ("Time since engine start", lambda d: d[0] * 256 + d[1], "s"),
    0x21: ("Distance driven with light on", lambda d: d[0] * 256 + d[1], "km"),
    0x31: ("Distance since codes cleared", lambda d: d[0] * 256 + d[1], "km"),
}


def format_value(v, unit):
    if unit == "°C":
        return f"{v * 9 / 5 + 32:.0f} °F   ({v:.0f} °C)"
    if unit == "km/h":
        return f"{v * 0.621371:.0f} mph   ({v:.0f} km/h)"
    if unit == "km":
        return f"{v * 0.621371:.0f} miles   ({v:.0f} km)"
    if unit == "kPa":
        return f"{v:.0f} kPa   ({v * 0.145038:.1f} psi)"
    if unit == "rpm":
        return f"{v:.0f} rpm"
    if unit == "s":
        return f"{int(v) // 60} min {int(v) % 60} s"
    if unit == "V":
        return f"{v:.2f} V"
    if unit == "g/s":
        return f"{v:.1f} g/s"
    return f"{v:.1f} {unit}"


def format_pid(pid, data):
    name, fn, unit = PIDS[pid]
    try:
        return format_value(fn(data), unit)
    except (IndexError, TypeError):
        return "-"


# ----------------------------------------------------------------------------
# Readiness monitors (mode 01 PID 01)
# ----------------------------------------------------------------------------
SPARK_MONITORS = ["Catalyst", "Heated catalyst", "Evaporative system (EVAP)", "Secondary air system",
                  "A/C refrigerant", "Oxygen sensor", "Oxygen sensor heater", "EGR system"]
DIESEL_MONITORS = ["NMHC catalyst", "NOx / SCR aftertreatment", None, "Boost pressure", None,
                   "Exhaust gas sensor", "Particulate filter (DPF)", "EGR / VVT system"]


def decode_readiness(d):
    a, b, c, dd = d[:4]
    mil_on = bool(a & 0x80)
    count = a & 0x7F
    diesel = bool(b & 0x08)
    rows = []
    for i, name in enumerate(["Misfire", "Fuel system", "Comprehensive components"]):
        rows.append((name, bool(b & (1 << i)), bool(b & (1 << (i + 4)))))
    for i, name in enumerate(DIESEL_MONITORS if diesel else SPARK_MONITORS):
        if name:
            rows.append((name, bool(c & (1 << i)), bool(dd & (1 << i))))
    return mil_on, count, diesel, rows  # rows: (name, supported, incomplete)


# ----------------------------------------------------------------------------
# Module addresses for the ABS / airbag / body scan
# ----------------------------------------------------------------------------
MODULES_11BIT = {
    0x7E0: "Engine (ECM/PCM)", 0x7E1: "Transmission (TCM)", 0x7E2: "OBD module #3",
    0x7E3: "OBD module #4", 0x7E4: "OBD module #5", 0x7E5: "OBD module #6",
    0x7E6: "OBD module #7", 0x7E7: "OBD module #8",
    0x760: "ABS / brakes (typical Ford)", 0x737: "Airbag (typical Ford)",
    0x726: "Body control (typical Ford)", 0x720: "Instrument cluster (typical Ford)",
    0x730: "Power steering (typical Ford)",
    0x7B0: "ABS / brakes (typical Toyota/Lexus)", 0x780: "Airbag (typical Toyota/Lexus)",
    0x7C0: "Instrument cluster (typical Toyota/Lexus)",
    0x241: "Body control (typical GM)", 0x243: "ABS / brakes (typical GM)", 0x247: "Airbag (typical GM)",
    0x7D1: "ABS / brakes (typical Hyundai/Kia)", 0x7D2: "Airbag (typical Hyundai/Kia)",
    0x7A0: "Body control (typical Hyundai/Kia)", 0x7C6: "Instrument cluster (typical Hyundai/Kia)",
    0x713: "ABS / brakes (typical VW/Audi)", 0x715: "Airbag (typical VW/Audi)",
    0x710: "Gateway (typical VW/Audi)",
}
MODULES_29BIT = {0x10: "Engine (ECM/PCM)", 0x11: "Engine #2", 0x18: "Transmission (TCM)"}

ECU_NAMES = {
    "7E8": "Engine (ECM/PCM)", "7E9": "Transmission (TCM)", "7EA": "OBD module #3",
    "7EB": "OBD module #4", "7EC": "OBD module #5", "7ED": "OBD module #6",
    "7EE": "OBD module #7", "7EF": "OBD module #8",
    "18DAF110": "Engine (ECM/PCM)", "18DAF111": "Engine #2", "18DAF118": "Transmission (TCM)",
    "10": "Engine (ECM/PCM)", "18": "Transmission (TCM)",
}


# Ford CAN modules (2005+). The same addresses can sit on HS-CAN (pins 6/14) or, depending on
# model/year, on Ford's medium-speed MS-CAN (pins 3/11), which only OBDLink-type adapters reach.
FORD_MODULES = {
    0x7E0: "Engine (PCM)", 0x7E1: "Transmission (TCM)", 0x760: "ABS / brakes",
    0x737: "Airbag (RCM)", 0x726: "Body control (BCM)", 0x720: "Instrument cluster (IPC)",
    0x730: "Power steering (PSCM)", 0x7D0: "SYNC / infotainment (APIM)", 0x727: "Audio (ACM)",
    0x733: "Climate control (HVAC)", 0x736: "Parking aid (PAM)",
}
FORD_EXTRA = [0x724, 0x740, 0x741, 0x761, 0x765, 0x706, 0x7A7, 0x775, 0x70C, 0x732, 0x734, 0x7C5]

# GM GMLAN modules (about 2007-2016): physical requests on 0x241-0x25F.
GM_MODULES = {0x241: "Body control (BCM)", 0x243: "ABS / brakes (EBCM)", 0x247: "Airbag (SDM)"}

HS, MS = "hs", "ms"


def _name(table, tid, prefix="Module"):
    return table.get(tid) or MODULES_11BIT.get(tid) or f"{prefix} 0x{tid:03X}"


def scan_targets(is_29bit, deep, make="", ms_can=False):
    """-> [(request id, module name, bus)]. bus 'ms' needs an OBDLink (STN) adapter."""
    if is_29bit:  # 29-bit cars: try every address (skip the tester's own 0xF1 and broadcast 0x33)
        return [(t, MODULES_29BIT.get(t, f"Module 0x{t:02X}"), HS) for t in range(0x100) if t not in (0x33, 0xF1)]
    gm = make.startswith("GM") or make in ("Chevrolet", "GMC", "Buick", "Cadillac", "Pontiac", "Oldsmobile",
                                            "Saturn", "Hummer", "Isuzu", "Saab")
    ford = make in ("Ford", "Lincoln", "Mercury")
    if deep:
        ids = list(range(0x700, 0x7F0)) + list(range(0x240, 0x260))
        out = [(t, _name(FORD_MODULES if ford else GM_MODULES, t), HS) for t in ids if t != 0x7DF]
        if ms_can and not gm:
            out += [(t, _name(FORD_MODULES, t), MS) for t in range(0x700, 0x7F0) if t != 0x7DF]
        return out
    obd = [(t, MODULES_11BIT[t], HS) for t in range(0x7E0, 0x7E8)]
    gm_list = [(t, _name(GM_MODULES, t, "GM module"), HS) for t in range(0x241, 0x260)]
    ford_ids = [t for t in FORD_MODULES if t not in (0x7E0, 0x7E1)] + FORD_EXTRA
    ford_hs = [(t, _name(FORD_MODULES, t, "Ford module"), HS) for t in ford_ids]
    ford_ms = [(t, _name(FORD_MODULES, t, "Ford module"), MS) for t in ford_ids] if ms_can else []
    if gm:
        return obd + gm_list
    if ford:
        return obd + ford_hs + ford_ms
    others = [(t, n, HS) for t, n in MODULES_11BIT.items() if t not in range(0x7E0, 0x7E8)]
    seen, out = set(), []
    for item in obd + others + gm_list + ford_hs + ford_ms:
        if (item[0], item[2]) not in seen:
            seen.add((item[0], item[2]))
            out.append(item)
    return out


# Older (pre-CAN) Ford SCP / GM Class 2 trucks: module addresses follow SAE J2178 ranges.
LEGACY_RANGES = [
    (0x10, 0x17, "Engine (PCM)"), (0x18, 0x1F, "Transmission / transfer case"),
    (0x28, 0x2F, "ABS / brakes"), (0x30, 0x37, "Steering"), (0x38, 0x3F, "Suspension"),
    (0x40, 0x57, "Body control (BCM/GEM)"), (0x58, 0x5F, "Airbag (SDM/RCM)"),
    (0x60, 0x6F, "Instrument cluster"), (0x70, 0x7F, "Lighting"), (0x80, 0x8F, "Radio / audio"),
    (0x90, 0x97, "Phone / communication"), (0x98, 0x9F, "Climate control (HVAC)"),
    (0xA0, 0xBF, "Doors / seats / convenience"), (0xC0, 0xC7, "Security / anti-theft"),
]
LEGACY_QUICK = [0x10, 0x11, 0x18, 0x1A, 0x28, 0x29, 0x30, 0x38, 0x40, 0x41, 0x45,
                0x58, 0x60, 0x61, 0x80, 0x98, 0x99, 0xA0, 0xA1, 0xC0]


def legacy_module_name(addr):
    for lo, hi, name in LEGACY_RANGES:
        if lo <= addr <= hi:
            return name
    return f"Module 0x{addr:02X}"


def legacy_scan_targets(deep):
    addrs = range(0x10, 0xF0) if deep else LEGACY_QUICK
    return [(a, legacy_module_name(a), "j1850") for a in addrs if a != 0xF1]


# Make from VIN (first characters) - used to improve online lookups.
WMI = {
    "1F": "Ford", "2F": "Ford", "3F": "Ford", "1L": "Lincoln", "1G": "GM", "2G": "GM", "3G": "GM",
    "1C": "Chrysler/Dodge/Jeep/Ram", "2C": "Chrysler/Dodge/Jeep/Ram", "3C": "Chrysler/Dodge/Jeep/Ram",
    "1J": "Jeep", "1N": "Nissan", "3N": "Nissan", "JN": "Nissan", "1H": "Honda", "2H": "Honda",
    "JH": "Honda/Acura", "5J": "Honda/Acura", "5F": "Honda", "4T": "Toyota", "5T": "Toyota",
    "JT": "Toyota/Lexus", "2T": "Toyota", "1M": "Mercury", "2M": "Mercury", "5L": "Lincoln", "KL": "GM", "JF": "Subaru", "4S": "Subaru", "KM": "Hyundai",
    "5N": "Hyundai", "KN": "Kia", "5X": "Kia", "WV": "Volkswagen", "3V": "Volkswagen",
    "1V": "Volkswagen", "WA": "Audi", "WB": "BMW", "5U": "BMW", "WD": "Mercedes-Benz",
    "W1": "Mercedes-Benz", "4J": "Mercedes-Benz", "JM": "Mazda", "JA": "Mitsubishi", "YV": "Volvo",
}


def make_from_vin(vin):
    return WMI.get((vin or "")[:2].upper(), "") if vin and len(vin) == 17 else ""


# ----------------------------------------------------------------------------
# Transports (how bytes get to the adapter)
# ----------------------------------------------------------------------------
class SerialTransport:
    def __init__(self, port, baud):
        self.ser = serial.Serial(port, baud, timeout=0.1)

    def write(self, data):
        self.ser.write(data)

    def read(self):
        return self.ser.read(512)

    def flush_input(self):
        self.ser.reset_input_buffer()

    def close(self):
        self.ser.close()


class TcpTransport:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.settimeout(0.1)

    def write(self, data):
        self.sock.sendall(data)

    def read(self):
        try:
            data = self.sock.recv(512)
        except socket.timeout:
            return b""
        if data == b"":
            raise ConnectionError("The Wi-Fi adapter closed the connection.")
        return data

    def flush_input(self):
        self.sock.settimeout(0.01)
        try:
            while self.sock.recv(1024):
                pass
        except (socket.timeout, OSError):
            pass
        self.sock.settimeout(0.1)

    def close(self):
        self.sock.close()


class DemoTransport:
    """Pretends to be an ELM327 plugged into a car that has a few problems."""

    VIN = "1FTDEMO12C4567890"

    def __init__(self):
        self._out = b""
        self._hdr = "7DF"
        self._t0 = time.time()
        self._cleared = False
        # request ID -> (response ID, [(byte A, byte B, failure type, status)])
        self._modules = {
            0x7E0: (0x7E8, [(0x03, 0x01, 0x00, 0x09)]),                            # P0301-00
            0x760: (0x768, [(0x40, 0x35, 0x1C, 0x09)]),                            # C0035-1C
            0x737: (0x73F, [(0x80, 0x01, 0x13, 0x08), (0xC1, 0x21, 0x00, 0x09)]),  # B0001-13, U0121-00
            0x726: (0x72E, []),
        }

    def write(self, data):
        cmd = data.decode("ascii", "ignore").strip().upper().replace(" ", "")
        self._out += ("\r".join(self._respond(cmd)) + "\r\r>").encode()

    def read(self):
        time.sleep(0.01)
        out, self._out = self._out, b""
        return out

    def flush_input(self):
        self._out = b""

    def close(self):
        pass

    @staticmethod
    def _frames(hdr, payload):
        payload = bytes(payload)
        if len(payload) <= 7:
            return [hdr + "%02X" % len(payload) + payload.hex().upper() + "AA" * (7 - len(payload))]
        out = [hdr + "1%03X" % len(payload) + payload[:6].hex().upper()]
        rest, seq = payload[6:], 1
        while rest:
            chunk, rest = rest[:7], rest[7:]
            out.append(hdr + "2%X" % (seq & 0xF) + chunk.hex().upper() + "AA" * (7 - len(chunk)))
            seq += 1
        return out

    def _respond(self, c):
        if c.startswith("AT"):
            if c in ("ATZ", "ATWS", "ATI"):
                if c != "ATI":
                    self._hdr = "7DF"
                return ["ELM327 v1.5 (demo)"]
            if c == "ATDPN":
                return ["A6"]
            if c == "ATDP":
                return ["AUTO, ISO 15765-4 (CAN 11/500)"]
            if c == "ATRV":
                return ["14.1V"]
            if c.startswith("ATSH"):
                self._hdr = c[4:]
            return ["OK"]
        if not re.fullmatch(r"[0-9A-F]+", c) or len(c) % 2:
            return ["?"]
        req = bytes.fromhex(c)
        hdr = int(self._hdr, 16) if len(self._hdr) == 3 else 0
        if req[0] in (0x19, 0x14):
            return self._uds(hdr, req)
        if hdr in (0x7DF, 0x7E0):
            return self._obd(req)
        return ["NO DATA"]

    def _uds(self, hdr, req):
        if hdr not in self._modules:
            return ["NO DATA"]
        resp, dtcs = self._modules[hdr]
        rh = "%03X" % resp
        if req[0] == 0x19 and len(req) >= 3 and req[1] == 0x02:
            body = b"".join(bytes(d) for d in dtcs if d[3] & req[2])
            return self._frames(rh, bytes([0x59, 0x02, 0xFF]) + body)
        if req[0] == 0x14:
            self._modules[hdr] = (resp, [])
            return self._frames(rh, b"\x54")
        return self._frames(rh, bytes([0x7F, req[0], 0x11]))

    def _obd(self, req):
        E, T = "7E8", "7E9"
        mode = req[0]
        if mode == 0x01 and len(req) == 2:
            data = self._pid(req[1])
            if data is None:
                return ["NO DATA"]
            out = self._frames(E, bytes([0x41, req[1]]) + data)
            if req[1] == 0x00:
                out += self._frames(T, bytes.fromhex("410098180001"))
            return out
        if mode == 0x02 and len(req) == 3:
            if self._cleared:
                return ["NO DATA"]
            data = b"\x03\x01" if req[1] == 0x02 else self._pid(req[1], frozen=True)
            if data is None:
                return ["NO DATA"]
            return self._frames(E, bytes([0x42, req[1], req[2]]) + data)
        if mode == 0x03:
            if self._cleared:
                return self._frames(E, b"\x43\x00") + self._frames(T, b"\x43\x00")
            return self._frames(E, bytes.fromhex("4303030104200171")) + self._frames(T, bytes.fromhex("43010700"))
        if mode == 0x07:
            return self._frames(E, b"\x47\x00" if self._cleared else bytes.fromhex("47010302"))
        if mode == 0x0A:
            return self._frames(E, bytes.fromhex("4A010420"))  # permanent codes survive clearing
        if mode == 0x04:
            self._cleared = True
            self._modules[0x7E0] = (0x7E8, [])
            return self._frames(E, b"\x44") + self._frames(T, b"\x44")
        if mode == 0x09 and len(req) == 2 and req[1] == 0x02:
            return self._frames(E, b"\x49\x02\x01" + self.VIN.encode())
        return ["NO DATA"]

    def _pid(self, pid, frozen=False):
        t = 0 if frozen else time.time() - self._t0
        rpm = 2150 if frozen else 780 + 1400 * max(0.0, math.sin(t / 4))
        speed = 38 if frozen else max(0.0, 60 * math.sin(t / 12))
        coolant = 92 if frozen else min(90, 40 + t * 2)

        def b(*vals):
            return bytes(max(0, min(255, int(v))) for v in vals)

        table = {
            0x00: bytes.fromhex("BE3FA013"), 0x20: bytes.fromhex("00020001"), 0x40: bytes.fromhex("40000000"),
            0x01: b(0x82 if not self._cleared else 0x00, 0x07, 0xE5, 0xE5 if self._cleared else 0x04),
            0x03: b(2, 0), 0x04: b(25 + rpm / 100), 0x05: b(coolant + 40),
            0x06: b(128 + 6 * math.sin(t)), 0x07: b(138), 0x0B: b(30 + rpm / 60),
            0x0C: int(rpm * 4).to_bytes(2, "big"), 0x0D: b(speed), 0x0E: b((12 + 64) * 2),
            0x0F: b(28 + 40), 0x10: int((2.5 + rpm / 250) * 100).to_bytes(2, "big"),
            0x11: b((15 + rpm / 100) * 255 / 100), 0x13: b(0x33), 0x1C: b(1),
            0x1F: int(t).to_bytes(2, "big"), 0x2F: b(0.62 * 255), 0x42: (14100).to_bytes(2, "big"),
        }
        return table.get(pid)


class DemoOldGMTransport(DemoTransport):
    """Pretends to be a 2004 GM truck on the older J1850 VPW (Class 2) system."""

    def __init__(self):
        super().__init__()
        self._hdr = "686AF1"
        # module address -> [(byte A, byte B, active now?)]
        self._old = {
            0x10: [(0x03, 0x00, True), (0x01, 0x71, True)],    # P0300, P0171
            0x28: [(0x40, 0x35, True), (0x40, 0x50, False)],   # C0035 now, C0050 history
            0x58: [(0x80, 0x01, False)],                       # B0001 history
            0x40: [], 0x60: [],
        }

    @staticmethod
    def _f(header, data):
        return (bytes(header) + bytes(data) + b"\x5A").hex().upper()  # last byte = checksum

    def _respond(self, c):
        if c.startswith("AT"):
            if c in ("ATZ", "ATWS", "ATI"):
                if c != "ATI":
                    self._hdr = "686AF1"
                return ["ELM327 v1.5 (demo)"]
            if c == "ATDPN":
                return ["A2"]
            if c == "ATDP":
                return ["AUTO, SAE J1850 VPW"]
            if c == "ATRV":
                return ["13.9V"]
            if c.startswith("ATSH"):
                self._hdr = c[4:]
            return ["OK"]
        if not re.fullmatch(r"[0-9A-F]+", c) or len(c) % 2:
            return ["?"]
        req = bytes.fromhex(c)
        if self._hdr.startswith("6C") and len(self._hdr) == 6:
            addr = int(self._hdr[2:4], 16)
            if addr not in self._old:
                return ["NO DATA"]
            rh = [0x6C, 0xF1, addr]
            if req[0] == 0x19:
                current_only = len(req) > 1 and req[1] != 0xFF
                out = [self._f(rh, [0x59, a, b, 0xD0 if now else 0x40])
                       for a, b, now in self._old[addr] if now or not current_only]
                return out + [self._f(rh, [0x59, 0x00, 0x00, 0xFF])]
            if req[0] == 0x14:
                self._old[addr] = []
                if addr == 0x10:
                    self._cleared = True
                return [self._f(rh, [0x54])]
            return [self._f(rh, [0x7F, req[0], 0x11])]
        return self._old_obd(req)

    def _old_obd(self, req):
        H = [0x48, 0x6B, 0x10]
        mode = req[0]
        if mode == 0x01 and len(req) == 2:
            data = self._pid(req[1])
            return [self._f(H, [0x41, req[1]] + list(data))] if data is not None else ["NO DATA"]
        if mode == 0x02 and len(req) == 3:
            if self._cleared:
                return ["NO DATA"]
            data = b"\x03\x00" if req[1] == 0x02 else self._pid(req[1], frozen=True)
            return [self._f(H, [0x42, req[1], req[2]] + list(data))] if data is not None else ["NO DATA"]
        if mode == 0x03:
            codes = [(a, b) for a, b, now in self._old[0x10] if now]
            flat = [x for ab in codes for x in ab]
            flat = flat or [0] * 6
            flat += [0] * (-len(flat) % 6)
            return [self._f(H, [0x43] + flat[i:i + 6]) for i in range(0, len(flat), 6)]
        if mode == 0x07:
            return [self._f(H, [0x47, 0, 0, 0, 0, 0, 0])]
        if mode == 0x04:
            self._cleared = True
            self._old[0x10] = []
            return [self._f(H, [0x44])]
        return ["NO DATA"]  # no permanent codes or VIN on a truck this old


# ----------------------------------------------------------------------------
# ELM327 protocol handling
# ----------------------------------------------------------------------------
def isotp_reassemble(frames):
    """Join ISO-TP CAN frames (each starting with its PCI byte) into whole messages."""
    msgs, cur, need = [], None, 0
    for f in frames:
        if not f:
            continue
        kind = f[0] >> 4
        if kind == 0:
            msgs.append(bytes(f[1:1 + (f[0] & 0x0F)]))
            cur = None
        elif kind == 1 and len(f) >= 2:
            need = ((f[0] & 0x0F) << 8) | f[1]
            cur = bytearray(f[2:])
        elif kind == 2 and cur is not None:
            cur += f[1:]
            if len(cur) >= need:
                msgs.append(bytes(cur[:need]))
                cur = None
    if cur is not None:
        msgs.append(bytes(cur))
    return msgs


class ELM327:
    def __init__(self, transport, log=None):
        self.t = transport
        self.log = log or (lambda s: None)
        self.lock = threading.RLock()
        self.protocol = ""
        self.protocol_name = ""
        self.version = ""
        self.ecus = []
        self._supported = None
        self.is_stn = False   # OBDLink-type adapter (can reach Ford MS-CAN)
        self.make = ""        # filled in from the VIN by the app
        self._bus = None

    @property
    def is_can(self):
        return self.protocol in ("6", "7", "8", "9")

    @property
    def is_29bit(self):
        return self.protocol in ("7", "9")

    def close(self):
        try:
            self.t.close()
        except Exception:
            pass

    def send(self, cmd, timeout=5.0):
        """Send one command, return the reply lines (prompt and echo removed)."""
        with self.lock:
            self.t.flush_input()
            self.log(f"> {cmd}")
            self.t.write((cmd + "\r").encode("ascii"))
            buf = b""
            deadline = time.time() + timeout
            while time.time() < deadline:
                chunk = self.t.read()
                if chunk:
                    buf += chunk
                    if b">" in buf:
                        break
            else:
                self.log("  (no reply - timed out)")
            text = buf.decode("ascii", errors="ignore").replace(">", "").replace("\x00", "")
            lines = [ln.strip() for ln in re.split(r"[\r\n]+", text) if ln.strip()]
            if lines and lines[0].replace(" ", "").upper() == cmd.replace(" ", "").upper():
                lines = lines[1:]  # echo
            for ln in lines:
                self.log(f"< {ln}")
            return lines

    def parse(self, lines):
        """Reply lines -> {module header: [message bytes, ...]}."""
        frames = []
        for line in lines:
            h = line.replace(" ", "").upper()
            if len(h) >= 4 and re.fullmatch(r"[0-9A-F]+", h):
                frames.append(h)
        out = {}
        if self.is_can:
            hl = 8 if self.is_29bit else 3
            groups = {}
            for f in frames:
                if len(f) > hl and (len(f) - hl) % 2 == 0:
                    groups.setdefault(f[:hl], []).append(bytes.fromhex(f[hl:]))
            for hdr, fl in groups.items():
                msgs = isotp_reassemble(fl)
                if msgs:
                    out[hdr] = msgs
        else:  # older protocols: 3 header bytes + data + checksum
            for f in frames:
                if len(f) >= 10 and len(f) % 2 == 0:
                    b = bytes.fromhex(f)
                    out.setdefault("%02X" % b[2], []).append(b[3:-1])
        return out

    def request(self, cmd, timeout=5.0):
        return self.parse(self.send(cmd, timeout))

    def initialize(self):
        self.send("ATZ", timeout=4)
        for c in ("ATE0", "ATL0", "ATS0", "ATH1", "ATAT1", "ATSP0"):
            self.send(c)
        self.version = " ".join(self.send("ATI")) or "unknown"
        sti = " ".join(self.send("STI", timeout=1.5))  # OBDLink (STN chip) adapters answer this
        self.is_stn = "STN" in sti.upper()
        if self.is_stn:
            self.version = (" ".join(self.send("STDI", timeout=1.5)) or "OBDLink") + f" ({sti})"
        lines = self.send("0100", timeout=25)  # starts the automatic protocol search
        dpn = "".join(self.send("ATDPN")).strip().upper()
        self.protocol = dpn[-1:] if dpn else ""
        self.protocol_name = " ".join(self.send("ATDP")).replace("AUTO, ", "")
        res = self.parse(lines)
        self.ecus = sorted(h for h, msgs in res.items() if any(m[:2] == b"\x41\x00" for m in msgs))
        if not self.ecus:
            raise ConnectionError(
                "The adapter is working, but the car didn't answer.\n\n"
                "- Turn the ignition ON (engine can be off or running)\n"
                "- Make sure the adapter is pushed fully into the OBD port\n"
                "- Cars older than 1996 (US) don't have OBD-II")

    def voltage(self):
        return " ".join(self.send("ATRV")) or "-"

    def query_pid_all(self, mode, pid, extra=b""):
        res = self.request("%02X%02X" % (mode, pid) + extra.hex().upper())
        out = {}
        for ecu, msgs in res.items():
            for m in msgs:
                if len(m) >= 2 and m[0] == mode + 0x40 and m[1] == pid:
                    out[ecu] = m[2 + len(extra):]
                    break
        return out

    def query_pid(self, mode, pid, extra=b""):
        r = self.query_pid_all(mode, pid, extra)
        return r[sorted(r)[0]] if r else None

    def supported_pids(self):
        if self._supported is not None:
            return self._supported
        sup = set()
        for base in (0x00, 0x20, 0x40):
            if base and base not in sup:
                break
            for d in self.query_pid_all(1, base).values():
                if len(d) >= 4:
                    bits = int.from_bytes(d[:4], "big")
                    sup.update(base + i + 1 for i in range(32) if bits & (1 << (31 - i)))
        self._supported = sup
        return sup

    def read_dtcs(self, mode):
        """mode '03' stored, '07' pending, '0A' permanent -> [(module header, code)]."""
        res = self.request(mode, timeout=10)
        sid = int(mode, 16) + 0x40
        out = []
        for ecu, msgs in res.items():
            for m in msgs:
                if not m or m[0] != sid:
                    continue
                body = m[2:] if self.is_can else m[1:]  # CAN replies carry a count byte
                for i in range(0, len(body) - 1, 2):
                    if body[i] or body[i + 1]:
                        item = (ecu, decode_dtc_bytes(body[i], body[i + 1]))
                        if item not in out:
                            out.append(item)
        return out

    def clear_obd(self):
        res = self.request("04", timeout=10)
        return any(m[:1] == b"\x44" for msgs in res.values() for m in msgs)

    def read_vin(self):
        res = self.request("0902", timeout=8)
        data = bytearray()
        for ecu in sorted(res):
            for m in res[ecu]:
                if m[:2] == b"\x49\x02":
                    data += m[3:]
            if data:
                break
        vin = "".join(chr(c) for c in data if chr(c).isalnum())
        return vin[-17:] if len(vin) >= 17 else ""

    # --- Module (UDS) access -------------------------------------------------------
    def _uds_setup(self):
        self.send("ATAT0")
        self.send("ATST32")  # wait up to 200 ms for each module
        if self.is_29bit:
            self.send("ATCP18")
            self.send("ATCF18DAF100")
            self.send("ATCM1FFFFF00")
        else:
            self.send("ATCF400")  # accept replies from IDs 0x400-0x7FF (incl. GM 0x5xx/0x6xx)
            self.send("ATCM400")
        self.send("ATFCSD300000")
        self.send("ATFCSM1")

    def _select_bus(self, bus):
        """Switch between the normal high-speed CAN and Ford's MS-CAN (OBDLink only)."""
        if bus == self._bus:
            return
        if bus == MS:
            self.send("STP53")      # ISO 15765, 11-bit, 125 kbps on pins 3/11
        elif self._bus == MS:
            self.send("STP33")      # back to ISO 15765, 11-bit, 500 kbps on pins 6/14
        self._bus = bus
        self._uds_setup()           # filters must be set again after STP

    @staticmethod
    def _raw_frames(lines):
        """Lines with CAN auto-formatting off -> [(id, data bytes)]."""
        out = []
        for line in lines:
            h = line.replace(" ", "").upper()
            if len(h) >= 5 and re.fullmatch(r"[0-9A-F]+", h) and (len(h) - 3) % 2 == 0:
                out.append((h[:3], bytes.fromhex(h[3:])))
        return out

    def _gmlan_read(self, tid):
        """GM 2007-2016 (GMLAN) service $A9/$81. Codes come back as single frames on ID+0x300.
        -> None if the module stayed silent, else [(code, status text)]."""
        self.send("ATCAF0")
        try:
            self.send("ATSH%03X" % tid)
            lines = self.send("03A9811200000000", timeout=2)  # status mask $12 = current + history
        finally:
            self.send("ATCAF1")
        uudt, usdt = "%03X" % (tid + 0x300), "%03X" % (tid + 0x400)
        answered, out = False, []
        for cid, data in self._raw_frames(lines):
            if cid == usdt:
                answered = True
            if cid == uudt and data[:1] == b"\x81":
                answered = True
                if len(data) >= 5 and (data[1] or data[2]):
                    st = data[4]
                    label = "Current" if st & 0x02 else "History (not active now)" if st & 0x10 else "Stored"
                    if st & 0x80:
                        label += ", warning light on"
                    if data[3]:
                        label += f", symptom {data[3]:02X}"
                    item = (decode_dtc_bytes(data[1], data[2]), label)
                    if item not in out:
                        out.append(item)
        return out if answered else None

    def _gmlan_clear(self, tid):
        self.send("ATCAF0")
        try:
            self.send("ATSH%03X" % tid)
            lines = self.send("0104000000000000", timeout=3)
        finally:
            self.send("ATCAF1")
        usdt = "%03X" % (tid + 0x400)
        return any(cid == usdt and data[:2] == b"\x01\x44" for cid, data in self._raw_frames(lines))

    def _kwp_read(self):
        """Older CAN modules (e.g. some 2005-2010 Fords) use KWP2000 service $18 instead of $19."""
        for req in ("1800FF00", "1802FF00"):
            for msgs in self.request(req, timeout=2).values():
                for m in msgs:
                    if m[:1] == b"\x58":
                        body, out = m[2:], []
                        for i in range(0, len(body) - 2, 3):
                            if body[i] or body[i + 1]:
                                out.append((decode_dtc_bytes(body[i], body[i + 1]), "Stored"))
                        return out
        return None

    def _uds_target(self, tid):
        if self.is_29bit:
            self.send("ATSHDA%02XF1" % tid)
            self.send("ATFCSH18DA%02XF1" % tid)
        else:
            self.send("ATSH%03X" % tid)
            self.send("ATFCSH%03X" % tid)

    def _uds_restore(self):
        if self._bus == MS:
            self.send("STP33")
        self._bus = None
        self.send("ATWS", timeout=4)
        for c in ("ATE0", "ATL0", "ATS0", "ATH1", "ATAT1", "ATSPA" + (self.protocol or "0")):
            self.send(c)

    def uds_scan(self, targets, progress=None, stop=None):
        found = []
        with self.lock:
            self._bus = None
            try:
                for i, target in enumerate(targets):
                    tid, name, bus = (tuple(target) + (HS,))[:3]
                    if stop is not None and stop.is_set():
                        break
                    if progress:
                        progress(i, len(targets), name + (" (MS-CAN)" if bus == MS else ""))
                    self._select_bus(bus)
                    entry = {"target": tid, "name": name, "bus": bus}
                    if not self.is_29bit and 0x240 <= tid <= 0x25F:   # GM GMLAN address range
                        dtcs = self._gmlan_read(tid)
                        if dtcs is not None:
                            found.append(dict(entry, resp="%03X" % (tid + 0x400), dtcs=dtcs, kind="gmlan"))
                        continue
                    self._uds_target(tid)
                    res = self.request("19028D", timeout=2)
                    done = False
                    for hdr, msgs in res.items():
                        for m in msgs:
                            if done:
                                break
                            if len(m) >= 3 and m[0] == 0x59 and m[1] == 0x02:
                                recs, dtcs = m[3:], []
                                for j in range(0, len(recs) - 3, 4):
                                    a, b, ftb, st = recs[j:j + 4]
                                    if st & 0x8D:
                                        dtcs.append((decode_dtc_bytes(a, b) + "-%02X" % ftb, st))
                                found.append(dict(entry, resp=hdr, dtcs=dtcs, kind="uds"))
                                done = True
                            elif len(m) >= 2 and m[0] == 0x7F and m[1] == 0x19:
                                kwp = self._kwp_read()        # module is there but speaks KWP2000
                                found.append(dict(entry, resp=hdr, dtcs=kwp or [], kind="kwp"))
                                done = True
            finally:
                self._uds_restore()
        return found

    # --- Older trucks: GM Class 2 (J1850 VPW) and Ford SCP (J1850 PWM) ---------------
    @property
    def is_j1850(self):
        return self.protocol in ("1", "2")  # 1 = PWM (Ford), 2 = VPW (GM)

    @property
    def can_scan_modules(self):
        return self.is_can or self.is_j1850

    def module_targets(self, deep):
        if self.is_j1850:
            return legacy_scan_targets(deep)
        return scan_targets(self.is_29bit, deep, self.make, ms_can=self.is_stn)

    def module_scan(self, targets, progress=None, stop=None):
        if self.is_j1850:
            return self.legacy_scan(targets, progress, stop)
        return self.uds_scan(targets, progress, stop)

    def module_clear(self, targets):
        return self.legacy_clear(targets) if self.is_j1850 else self.uds_clear(targets)

    def _legacy_header(self, addr):
        # GM Class 2 uses priority byte 6C, Ford SCP uses C4; the scan tool is F1.
        return ("6C%02XF1" if self.protocol == "2" else "C4%02XF1") % addr

    def _legacy_replies(self, cmd, addr, sid):
        msgs = self.request(cmd, timeout=2).get("%02X" % addr, [])
        return bool(msgs), [m for m in msgs if m and m[0] == sid]

    def _legacy_read_module(self, addr):
        """-> (module answered?, [(code, status text)])"""
        if self.protocol == "2":  # GM Class 2: service $19, one DTC per reply, list ends with 00 00
            answered, current_msgs = self._legacy_replies("19D2FF00", addr, 0x59)
            if not answered:
                return False, []
            _, all_msgs = self._legacy_replies("19FFFF00", addr, 0x59)

            def codes(msgs):
                return [decode_dtc_bytes(m[1], m[2]) for m in msgs if len(m) >= 3 and (m[1] or m[2])]
            current = codes(current_msgs)
            out = [(c, "Current") for c in dict.fromkeys(current)]
            for c in dict.fromkeys(codes(all_msgs)):
                if c not in current:
                    out.append((c, "History (not active now)"))
            return True, out
        # Ford SCP: try service $13 (all DTCs), then $18 (DTCs by status)
        answered, msgs = self._legacy_replies("13", addr, 0x53)
        out = []
        for m in msgs:
            body = m[1:]
            for i in range(0, len(body) - 1, 2):
                if body[i] or body[i + 1]:
                    item = (decode_dtc_bytes(body[i], body[i + 1]), "Stored")
                    if item not in out:
                        out.append(item)
        if msgs:
            return True, out
        answered2, msgs = self._legacy_replies("1800FF00", addr, 0x58)
        for m in msgs:
            body = m[1:]
            if len(body) % 3 == 1:  # leading count byte
                body = body[1:]
            for i in range(0, len(body) - 2, 3):
                if body[i] or body[i + 1]:
                    item = (decode_dtc_bytes(body[i], body[i + 1]), "Stored")
                    if item not in out:
                        out.append(item)
        return (answered or answered2), out

    def legacy_scan(self, targets, progress=None, stop=None):
        found = []
        with self.lock:
            self.send("ATAT0")
            self.send("ATST32")
            self.send("ATAL")
            try:
                for i, target in enumerate(targets):
                    addr, name = target[0], target[1]
                    if stop is not None and stop.is_set():
                        break
                    if progress:
                        progress(i, len(targets), name)
                    self.send("ATSH" + self._legacy_header(addr))
                    answered, dtcs = self._legacy_read_module(addr)
                    if answered:
                        found.append({"target": addr, "name": name, "resp": "%02X" % addr, "dtcs": dtcs,
                                      "bus": "j1850"})
            finally:
                self._uds_restore()
        return found

    def legacy_clear(self, targets):
        results = []
        with self.lock:
            self.send("ATAT0")
            self.send("ATST32")
            try:
                for target in targets:
                    addr, name = target[0], target[1]
                    self.send("ATSH" + self._legacy_header(addr))
                    _, msgs = self._legacy_replies("14", addr, 0x54)
                    results.append((name, bool(msgs)))
            finally:
                self._uds_restore()
        return results

    def uds_clear(self, targets):
        results = []
        with self.lock:
            self._bus = None
            try:
                for target in targets:
                    tid, name, bus = (tuple(target) + (HS,))[:3]
                    self._select_bus(bus)
                    if not self.is_29bit and 0x240 <= tid <= 0x25F:
                        results.append((name, self._gmlan_clear(tid)))
                        continue
                    self._uds_target(tid)
                    ok = False
                    for req in ("14FFFFFF", "14FF00"):     # UDS, then KWP2000 style
                        res = self.request(req, timeout=4)
                        if any(m[:1] == b"\x54" for msgs in res.values() for m in msgs):
                            ok = True
                            break
                    results.append((name, ok))
            finally:
                self._uds_restore()
        return results


def open_adapter(kind, target, log):
    if kind == CONN_DEMO:
        return ELM327(DemoTransport(), log)
    if kind == CONN_DEMO_OLD:
        return ELM327(DemoOldGMTransport(), log)
    if kind == CONN_WIFI:
        host, _, port = (target or "192.168.0.10:35000").partition(":")
        port = int(port or 35000)
        try:
            t = TcpTransport(host.strip(), port)
        except OSError as e:
            raise ConnectionError(f"Couldn't reach the Wi-Fi adapter at {host}:{port}.\n\n"
                                  "Join your computer to the adapter's Wi-Fi network first "
                                  f"(usually named 'WiFi_OBDII' or similar).\n\n({e})")
        return ELM327(t, log)
    if serial is None:
        raise ConnectionError("The pyserial package isn't installed.\n\nOpen a terminal and run:\n"
                              "    pip install pyserial\n\nthen restart this program.")
    port = (target or "").split(" — ")[0].strip()
    if not port:
        raise ConnectionError("Pick your adapter's port from the list (click ↻ to refresh it).\n\n"
                              "USB adapters show up as something like /dev/cu.usbserial-… on a Mac "
                              "or COM3 on Windows. Bluetooth adapters must be paired in your computer's "
                              "Bluetooth settings first (PIN is usually 1234 or 0000).")
    for baud in (38400, 115200, 9600, 230400, 500000):
        try:
            t = SerialTransport(port, baud)
        except Exception as e:
            raise ConnectionError(f"Couldn't open {port}: {e}")
        elm = ELM327(t, log)
        try:
            t.write(b"\r")
            time.sleep(0.2)
            t.flush_input()
            reply = " ".join(elm.send("ATI", timeout=1.5)).upper()
        except Exception:
            reply = ""
        if any(k in reply for k in ("ELM", "STN", "OBD")):
            return elm
        t.close()
    raise ConnectionError(f"No OBD adapter answered on {port}.\n\n"
                          "Check that it's the right port and that the adapter is plugged into the car "
                          "(its light should be on).")


VIN_YEAR_CODES = "ABCDEFGHJKLMNPRSTVWXY123456789"


def year_from_vin(vin, now=None):
    """Model year from the 10th VIN character (codes repeat every 30 years)."""
    if not vin or len(vin) != 17 or vin[9].upper() not in VIN_YEAR_CODES:
        return None
    import datetime
    base = 1980 + VIN_YEAR_CODES.index(vin[9].upper())
    now = now or datetime.date.today().year
    candidates = [y for y in (base, base + 30) if 1996 <= y <= now + 1]
    return max(candidates) if candidates else None


SKIP_PORTS = ("bluetooth-incoming-port", "debug-console", "wlan-debug")


def list_ports():
    """Serial ports that could be an OBD adapter, likeliest first."""
    if serial is None:
        return []
    ports = [p for p in serial.tools.list_ports.comports() if not any(s in p.device.lower() for s in SKIP_PORTS)]
    keys = ("obd", "elm", "ftdi", "usbserial", "usb", "ch340", "serial", "rfcomm", "bluetooth")
    ports.sort(key=lambda p: 0 if any(k in (p.device + " " + (p.description or "")).lower() for k in keys) else 1)
    return [(p.device, p.description or "") for p in ports]
