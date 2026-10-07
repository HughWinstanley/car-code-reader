"""
Trouble-code knowledge for Car Code Reader.

- GENERIC: meanings of standard (SAE J2012) codes that mean the same thing on every car.
- describe_dtc(): meaning + plain-English category for any code, known or not.
- describe_ftb(): meaning of the "-XX" failure-type suffix that module (UDS) codes carry.
- common_causes(): what usually fixes the most common codes.

You can add your own codes (e.g. manufacturer-specific ones for your make) in a file
named custom_codes.csv next to this file, one per line:   P1234,My description here
"""

import csv
import os
import sys

GENERIC = {}


def _family(base, name, kinds=("circuit malfunction", "circuit range/performance",
                                "circuit low input", "circuit high input", "circuit intermittent")):
    for i, kind in enumerate(kinds):
        GENERIC["P%04d" % (base + i)] = f"{name} {kind}"


def _o2(base, bank, sensor):
    kinds = ["O2 sensor circuit malfunction", "O2 sensor circuit low voltage",
             "O2 sensor circuit high voltage", "O2 sensor circuit slow response",
             "O2 sensor circuit no activity detected", "O2 sensor heater circuit malfunction"]
    for i, kind in enumerate(kinds):
        GENERIC["P%04d" % (base + i)] = f"{kind} (bank {bank}, sensor {sensor})"


# --- Patterned families -------------------------------------------------------
GENERIC["P0300"] = "Random/multiple cylinder misfire detected"
for n in range(1, 13):
    GENERIC["P03%02d" % n] = f"Cylinder {n} misfire detected"
    GENERIC["P02%02d" % n] = f"Fuel injector circuit/open - cylinder {n}"
    GENERIC["P0%d" % (350 + n)] = f"Ignition coil {chr(64 + n)} (cylinder {n}) primary/secondary circuit"
GENERIC["P0200"] = "Fuel injector circuit malfunction"
GENERIC["P0350"] = "Ignition coil primary/secondary circuit malfunction"

for base, bank, sensor in ((130, 1, 1), (136, 1, 2), (142, 1, 3), (150, 2, 1), (156, 2, 2), (162, 2, 3)):
    _o2(base, bank, sensor)

_family(100, "Mass air flow (MAF) sensor")
_family(105, "Manifold absolute pressure (MAP) / barometric pressure sensor")
_family(110, "Intake air temperature (IAT) sensor")
_family(115, "Engine coolant temperature (ECT) sensor")
_family(120, "Throttle/pedal position sensor A")
_family(180, "Fuel temperature sensor A")
_family(190, "Fuel rail pressure sensor")
_family(195, "Engine oil temperature sensor")
_family(220, "Throttle/pedal position sensor B")
_family(325, "Knock sensor 1 (bank 1)")
_family(330, "Knock sensor 2 (bank 2)")
_family(335, "Crankshaft position sensor A")
_family(340, "Camshaft position sensor A (bank 1)")
_family(345, "Camshaft position sensor A (bank 2)")
_family(460, "Fuel level sensor")
_family(705, "Transmission range sensor (PRNDL input)")
_family(710, "Transmission fluid temperature sensor")
_family(520, "Engine oil pressure sensor/switch", ("circuit malfunction", "circuit range/performance",
                                                   "circuit low voltage", "circuit high voltage"))
_family(530, "A/C refrigerant pressure sensor", ("circuit malfunction", "circuit range/performance",
                                                 "circuit low input", "circuit high input"))

for i, gear in enumerate(["1", "2", "3", "4", "5", "reverse"]):
    GENERIC["P%04d" % (731 + i)] = f"Gear {gear} incorrect ratio" if gear != "reverse" else "Reverse incorrect ratio"

for base, letter in ((750, "A"), (755, "B"), (760, "C"), (765, "D"), (770, "E")):
    for i, kind in enumerate(["malfunction", "performance or stuck off", "stuck on",
                              "electrical", "intermittent"]):
        GENERIC["P%04d" % (base + i)] = f"Shift solenoid {letter} {kind}"

# --- Individually listed codes ------------------------------------------------
GENERIC.update({
    # Cam timing / O2 heaters
    "P0010": "Intake camshaft position actuator circuit (bank 1)",
    "P0011": "Intake camshaft timing over-advanced or system performance (bank 1)",
    "P0012": "Intake camshaft timing over-retarded (bank 1)",
    "P0013": "Exhaust camshaft position actuator circuit (bank 1)",
    "P0014": "Exhaust camshaft timing over-advanced or system performance (bank 1)",
    "P0015": "Exhaust camshaft timing over-retarded (bank 1)",
    "P0016": "Crankshaft/camshaft position correlation (bank 1, sensor A)",
    "P0017": "Crankshaft/camshaft position correlation (bank 1, sensor B)",
    "P0018": "Crankshaft/camshaft position correlation (bank 2, sensor A)",
    "P0019": "Crankshaft/camshaft position correlation (bank 2, sensor B)",
    "P0020": "Intake camshaft position actuator circuit (bank 2)",
    "P0021": "Intake camshaft timing over-advanced or system performance (bank 2)",
    "P0022": "Intake camshaft timing over-retarded (bank 2)",
    "P0030": "O2 sensor heater control circuit (bank 1, sensor 1)",
    "P0031": "O2 sensor heater control circuit low (bank 1, sensor 1)",
    "P0032": "O2 sensor heater control circuit high (bank 1, sensor 1)",
    "P0036": "O2 sensor heater control circuit (bank 1, sensor 2)",
    "P0037": "O2 sensor heater control circuit low (bank 1, sensor 2)",
    "P0038": "O2 sensor heater control circuit high (bank 1, sensor 2)",
    "P0050": "O2 sensor heater control circuit (bank 2, sensor 1)",
    "P0051": "O2 sensor heater control circuit low (bank 2, sensor 1)",
    "P0052": "O2 sensor heater control circuit high (bank 2, sensor 1)",
    "P0056": "O2 sensor heater control circuit (bank 2, sensor 2)",
    "P0057": "O2 sensor heater control circuit low (bank 2, sensor 2)",
    "P0058": "O2 sensor heater control circuit high (bank 2, sensor 2)",
    # Fuel system
    "P0087": "Fuel rail/system pressure too low",
    "P0088": "Fuel rail/system pressure too high",
    "P0089": "Fuel pressure regulator performance",
    "P0093": "Fuel system large leak detected",
    "P0125": "Insufficient coolant temperature for closed-loop fuel control",
    "P0128": "Coolant temperature below thermostat regulating temperature",
    "P0170": "Fuel trim malfunction (bank 1)",
    "P0171": "System too lean (bank 1)",
    "P0172": "System too rich (bank 1)",
    "P0173": "Fuel trim malfunction (bank 2)",
    "P0174": "System too lean (bank 2)",
    "P0175": "System too rich (bank 2)",
    "P0217": "Engine overtemperature condition",
    "P0219": "Engine overspeed condition",
    "P0230": "Fuel pump primary circuit malfunction",
    "P0231": "Fuel pump secondary circuit low",
    "P0232": "Fuel pump secondary circuit high",
    "P0234": "Turbocharger/supercharger overboost condition",
    "P0299": "Turbocharger/supercharger underboost condition",
    # Ignition / sensors
    "P0365": "Camshaft position sensor B circuit (bank 1)",
    "P0366": "Camshaft position sensor B circuit range/performance (bank 1)",
    "P0380": "Glow plug/heater circuit A malfunction",
    # Emission controls
    "P0400": "Exhaust gas recirculation (EGR) flow malfunction",
    "P0401": "EGR flow insufficient detected",
    "P0402": "EGR flow excessive detected",
    "P0403": "EGR control circuit malfunction",
    "P0404": "EGR control circuit range/performance",
    "P0405": "EGR sensor A circuit low",
    "P0406": "EGR sensor A circuit high",
    "P0410": "Secondary air injection system malfunction",
    "P0411": "Secondary air injection system incorrect flow detected",
    "P0412": "Secondary air injection switching valve A circuit",
    "P0418": "Secondary air injection pump relay A circuit",
    "P0420": "Catalyst system efficiency below threshold (bank 1)",
    "P0421": "Warm-up catalyst efficiency below threshold (bank 1)",
    "P0430": "Catalyst system efficiency below threshold (bank 2)",
    "P0431": "Warm-up catalyst efficiency below threshold (bank 2)",
    "P0440": "Evaporative emission (EVAP) system malfunction",
    "P0441": "EVAP system incorrect purge flow",
    "P0442": "EVAP system small leak detected",
    "P0443": "EVAP purge control valve circuit malfunction",
    "P0444": "EVAP purge control valve circuit open",
    "P0445": "EVAP purge control valve circuit shorted",
    "P0446": "EVAP vent control circuit malfunction",
    "P0447": "EVAP vent control circuit open",
    "P0448": "EVAP vent control circuit shorted",
    "P0449": "EVAP vent valve/solenoid circuit malfunction",
    "P0450": "EVAP pressure sensor malfunction",
    "P0451": "EVAP pressure sensor range/performance",
    "P0452": "EVAP pressure sensor low input",
    "P0453": "EVAP pressure sensor high input",
    "P0454": "EVAP pressure sensor intermittent",
    "P0455": "EVAP system large leak detected",
    "P0456": "EVAP system very small leak detected",
    "P0457": "EVAP system leak detected (fuel cap loose/off)",
    "P0480": "Cooling fan 1 control circuit malfunction",
    "P0481": "Cooling fan 2 control circuit malfunction",
    # Speed / idle / inputs
    "P0500": "Vehicle speed sensor malfunction",
    "P0501": "Vehicle speed sensor range/performance",
    "P0502": "Vehicle speed sensor low input",
    "P0503": "Vehicle speed sensor intermittent/erratic/high",
    "P0505": "Idle air control system malfunction",
    "P0506": "Idle control system RPM lower than expected",
    "P0507": "Idle control system RPM higher than expected",
    "P0560": "System voltage malfunction",
    "P0562": "System voltage low",
    "P0563": "System voltage high",
    "P0571": "Brake switch A circuit malfunction",
    # Computer / outputs
    "P0600": "Serial communication link malfunction",
    "P0601": "Internal control module memory checksum error",
    "P0602": "Control module programming error",
    "P0603": "Internal control module keep-alive memory (KAM) error",
    "P0604": "Internal control module RAM error",
    "P0605": "Internal control module ROM error",
    "P0606": "Control module processor fault",
    "P0607": "Control module performance",
    "P0620": "Generator (alternator) control circuit malfunction",
    "P0621": "Generator lamp 'L' terminal circuit malfunction",
    "P0622": "Generator field 'F' terminal circuit malfunction",
    "P0627": "Fuel pump control circuit open",
    "P0641": "Sensor reference voltage A circuit open",
    "P0651": "Sensor reference voltage B circuit open",
    "P0685": "ECM/PCM power relay control circuit open",
    # Transmission
    "P0700": "Transmission control system malfunction (TCM has requested the check engine light)",
    "P0715": "Input/turbine speed sensor circuit malfunction",
    "P0716": "Input/turbine speed sensor circuit range/performance",
    "P0717": "Input/turbine speed sensor circuit no signal",
    "P0718": "Input/turbine speed sensor circuit intermittent",
    "P0720": "Output speed sensor circuit malfunction",
    "P0721": "Output speed sensor circuit range/performance",
    "P0722": "Output speed sensor circuit no signal",
    "P0723": "Output speed sensor circuit intermittent",
    "P0730": "Incorrect gear ratio",
    "P0740": "Torque converter clutch circuit malfunction",
    "P0741": "Torque converter clutch circuit performance or stuck off",
    "P0742": "Torque converter clutch circuit stuck on",
    "P0743": "Torque converter clutch circuit electrical",
    "P0744": "Torque converter clutch circuit intermittent",
    "P0841": "Transmission fluid pressure sensor/switch A circuit range/performance",
    "P0850": "Park/neutral switch input circuit",
    "P0868": "Transmission fluid pressure low",
    # Hybrid
    "P0A80": "Replace hybrid battery pack",
    "P0AA6": "Hybrid battery voltage system isolation fault",
    # P2xxx
    "P2002": "Diesel particulate filter efficiency below threshold (bank 1)",
    "P2004": "Intake manifold runner control stuck open (bank 1)",
    "P2096": "Post-catalyst fuel trim system too lean (bank 1)",
    "P2097": "Post-catalyst fuel trim system too rich (bank 1)",
    "P2098": "Post-catalyst fuel trim system too lean (bank 2)",
    "P2099": "Post-catalyst fuel trim system too rich (bank 2)",
    "P2101": "Throttle actuator control motor circuit range/performance",
    "P2111": "Throttle actuator control system stuck open",
    "P2112": "Throttle actuator control system stuck closed",
    "P2119": "Throttle actuator control throttle body range/performance",
    "P2135": "Throttle/pedal position sensor A/B voltage correlation",
    "P2138": "Throttle/pedal position sensor D/E voltage correlation",
    "P2187": "System too lean at idle (bank 1)",
    "P2188": "System too rich at idle (bank 1)",
    "P2189": "System too lean at idle (bank 2)",
    "P2190": "System too rich at idle (bank 2)",
    "P2195": "O2 sensor signal biased/stuck lean (bank 1, sensor 1)",
    "P2196": "O2 sensor signal biased/stuck rich (bank 1, sensor 1)",
    "P2197": "O2 sensor signal biased/stuck lean (bank 2, sensor 1)",
    "P2198": "O2 sensor signal biased/stuck rich (bank 2, sensor 1)",
    "P2270": "O2 sensor signal biased/stuck lean (bank 1, sensor 2)",
    "P2271": "O2 sensor signal biased/stuck rich (bank 1, sensor 2)",
    "P2272": "O2 sensor signal biased/stuck lean (bank 2, sensor 2)",
    "P2273": "O2 sensor signal biased/stuck rich (bank 2, sensor 2)",
    "P2463": "Diesel particulate filter soot accumulation",
    "P2610": "ECM/PCM internal engine-off timer performance",
    "P2A00": "O2 sensor circuit range/performance (bank 1, sensor 1)",
    "P2A03": "O2 sensor circuit range/performance (bank 2, sensor 1)",
    "P20EE": "SCR NOx catalyst efficiency below threshold (bank 1)",
    # Network
    "U0001": "High-speed CAN communication bus",
    "U0073": "Control module communication bus A off",
    "U0100": "Lost communication with ECM/PCM 'A'",
    "U0101": "Lost communication with TCM (transmission)",
    "U0121": "Lost communication with ABS control module",
    "U0140": "Lost communication with body control module (BCM)",
    "U0151": "Lost communication with restraints (airbag) control module",
    "U0155": "Lost communication with instrument panel cluster",
    "U0164": "Lost communication with HVAC control module",
    "U0401": "Invalid data received from ECM/PCM 'A'",
    "U0415": "Invalid data received from ABS control module",
    # Chassis / body
    "C0035": "Left front wheel speed sensor circuit",
    "C0040": "Right front wheel speed sensor circuit",
    "C0045": "Left rear wheel speed sensor circuit",
    "C0050": "Right rear wheel speed sensor circuit",
    "B0001": "Driver frontal airbag stage 1 deployment control",
    "B0002": "Driver frontal airbag stage 2 deployment control",
})

# --- Custom codes from CSV -----------------------------------------------------
CUSTOM = {}


def _load_custom():
    folders = {os.path.dirname(os.path.abspath(__file__)),
               os.path.dirname(os.path.abspath(sys.argv[0] or "."))}
    for folder in folders:
        path = os.path.join(folder, "custom_codes.csv")
        if not os.path.exists(path):
            continue
        try:
            with open(path, newline="", encoding="utf-8") as f:
                for row in csv.reader(f):
                    if len(row) >= 2 and row[0].strip() and not row[0].startswith("#"):
                        CUSTOM[row[0].strip().upper()] = row[1].strip()
        except OSError:
            pass


_load_custom()

# --- Categories ---------------------------------------------------------------
SYSTEMS = {
    "P": "Powertrain (engine, transmission, emissions)",
    "C": "Chassis (ABS/brakes, steering, suspension)",
    "B": "Body (airbags, seats, lights, locks, climate)",
    "U": "Network (communication between modules)",
}

P_SUBSYSTEMS = {
    "0": "fuel/air metering and auxiliary emission controls",
    "1": "fuel and air metering",
    "2": "fuel and air metering (injector circuits)",
    "3": "ignition system or misfire",
    "4": "auxiliary emission controls (EGR, EVAP, catalyst)",
    "5": "vehicle speed, idle control and auxiliary inputs",
    "6": "computer and output circuits",
    "7": "transmission", "8": "transmission", "9": "transmission",
    "A": "hybrid propulsion system", "B": "hybrid propulsion system", "C": "hybrid propulsion system",
}


def is_manufacturer_specific(code):
    letter, digit = code[0], code[1]
    if letter == "P":
        return digit == "1" or (digit == "3" and code[2] in "0123")
    return digit in "12"


def category_text(code):
    if len(code) != 5 or code[0] not in SYSTEMS:
        return "Unrecognized code format"
    parts = [SYSTEMS[code[0]]]
    parts.append("manufacturer-specific code (meaning depends on the make)"
                 if is_manufacturer_specific(code)
                 else "generic code (same meaning on every make)")
    if code[0] == "P" and code[2] in P_SUBSYSTEMS:
        parts.append("area: " + P_SUBSYSTEMS[code[2]])
    return " · ".join(parts)


def describe_dtc(code):
    """Return a dict with description, category, failure type and common causes."""
    base, _, ftb = code.upper().partition("-")
    desc = CUSTOM.get(code.upper()) or CUSTOM.get(base) or GENERIC.get(base)
    known = desc is not None
    if not known:
        area = SYSTEMS.get(base[:1], "Unknown system").split(" (")[0].lower()
        if base[:1] == "P" and len(base) == 5 and base[2] in P_SUBSYSTEMS:
            area = P_SUBSYSTEMS[base[2]]
        if len(base) == 5 and base[0] in SYSTEMS and is_manufacturer_specific(base):
            desc = f"Manufacturer-specific {area} code - double-click to look it up for your make"
        else:
            desc = f"{area[:1].upper() + area[1:]} code - not in the built-in list, double-click to look it up"
    return {
        "description": desc,
        "known": known,
        "category": category_text(base),
        "failure_type": describe_ftb(ftb) if ftb else "",
        "causes": common_causes(base),
    }


# --- UDS failure-type byte (the "-XX" after module codes) ----------------------
FTB = {
    0x00: "No sub-type information", 0x01: "General electrical failure", 0x02: "General signal failure",
    0x03: "Frequency/PWM signal failure", 0x04: "System internal failure", 0x05: "System programming failure",
    0x06: "Algorithm-based failure", 0x07: "Mechanical failure", 0x08: "Bus signal/message failure",
    0x09: "Component failure", 0x11: "Circuit short to ground", 0x12: "Circuit short to battery",
    0x13: "Circuit open", 0x14: "Circuit short to ground or open", 0x15: "Circuit short to battery or open",
    0x16: "Circuit voltage below threshold", 0x17: "Circuit voltage above threshold",
    0x19: "Circuit current above threshold", 0x1C: "Circuit voltage out of range",
    0x1D: "Circuit current out of range", 0x1F: "Circuit intermittent",
    0x21: "Signal amplitude below minimum", 0x22: "Signal amplitude above maximum",
    0x23: "Signal stuck low", 0x24: "Signal stuck high", 0x26: "Signal rate of change too low",
    0x27: "Signal rate of change too high", 0x28: "Signal bias level out of range",
    0x29: "Signal invalid", 0x2F: "Signal erratic", 0x31: "No signal",
    0x36: "Signal frequency too low", 0x37: "Signal frequency too high", 0x38: "Signal frequency incorrect",
    0x41: "General checksum failure", 0x42: "General memory failure", 0x44: "Data memory failure",
    0x45: "Program memory failure", 0x46: "Calibration/parameter memory failure",
    0x47: "Watchdog/safety processor failure", 0x48: "Supervision software failure",
    0x49: "Internal electronic failure", 0x4B: "Over temperature", 0x51: "Not programmed",
    0x52: "Not activated", 0x54: "Missing calibration", 0x55: "Not configured",
    0x61: "Signal calculation failure", 0x62: "Signal compare failure",
    0x64: "Signal plausibility failure", 0x67: "Signal incorrect after event",
    0x71: "Actuator stuck", 0x72: "Actuator stuck open", 0x73: "Actuator stuck closed",
    0x74: "Actuator slipping", 0x77: "Commanded position not reachable",
    0x78: "Alignment or adjustment incorrect", 0x7B: "Low fluid level",
    0x81: "Invalid serial data received", 0x82: "Alive/sequence counter incorrect",
    0x83: "Message signature/checksum incorrect", 0x84: "Signal below allowable range",
    0x85: "Signal above allowable range", 0x86: "Signal invalid", 0x87: "Missing message",
    0x88: "Bus off", 0x8F: "Erratic", 0x92: "Performance or incorrect operation",
    0x93: "No operation", 0x94: "Unexpected operation", 0x95: "Incorrect assembly",
    0x96: "Component internal failure", 0x97: "Operation obstructed or blocked",
    0x98: "Component or system over temperature",
}


def describe_ftb(ftb_hex):
    try:
        value = int(ftb_hex, 16)
    except ValueError:
        return ""
    return f"-{value:02X}: " + FTB.get(value, "Manufacturer-specific failure type")


def uds_status_text(status):
    parts = []
    if status & 0x01:
        parts.append("Active now")
    if status & 0x08:
        parts.append("Stored")
    elif status & 0x04:
        parts.append("Pending")
    if status & 0x80:
        parts.append("Warning light on")
    return ", ".join(parts) or "History"


def decode_dtc_bytes(a, b):
    """Two raw bytes -> code text, e.g. 0x03 0x01 -> 'P0301'."""
    return "PCBU"[a >> 6] + str((a >> 4) & 0x3) + "%X" % (a & 0xF) + "%02X" % b


# --- What usually fixes it -------------------------------------------------------
_CAUSES = {
    "misfire": "Worn spark plugs, a bad ignition coil, a clogged or leaking fuel injector, a vacuum leak, "
               "or low compression. Tip: swap that cylinder's coil with a neighbor - if the misfire "
               "follows the coil, the coil is bad. A flashing check-engine light means a severe misfire: "
               "avoid driving hard, it can overheat the catalytic converter.",
    "lean": "Vacuum leak (cracked intake hose, PCV hose, intake gasket), dirty or failing MAF sensor, "
            "weak fuel pump or clogged fuel filter, or an exhaust leak ahead of the O2 sensor.",
    "rich": "Leaking injector, fuel pressure too high, dirty MAF sensor, faulty coolant temperature "
            "sensor, or a clogged air filter.",
    "cat": "Worn-out catalytic converter, a failing downstream O2 sensor, or an exhaust leak. Fix any "
           "misfire or oil-burning problem first - those are what kill converters.",
    "evap": "Loose, worn or wrong gas cap (check this first - it's free), cracked EVAP hoses, a faulty "
            "purge or vent valve, or a leaking charcoal canister. Shops find small leaks with a smoke test.",
    "thermostat": "Thermostat stuck open (most common), low coolant, or a faulty coolant temperature sensor.",
    "vvt": "Low or dirty engine oil (check first), a faulty VVT/oil-control solenoid, or timing chain wear.",
    "timing": "Stretched timing chain or a belt that jumped a tooth, a faulty crank or cam sensor, or a "
              "VVT problem. Don't ignore this one - timing problems can damage the engine.",
    "egr": "Carbon-clogged EGR passages or valve, or a faulty EGR valve/sensor.",
    "idle": "Dirty throttle body (cleaning often fixes it), a vacuum leak, or a faulty idle control valve.",
    "o2heater": "The O2 sensor's internal heater failed (replace the sensor), a blown fuse, or damaged wiring.",
    "voltage": "Weak battery, failing alternator, or corroded battery terminals / ground straps.",
    "tcm": "The transmission computer has its own codes - they usually show up in this list too "
           "(look for 'Transmission'). Check those for the real fault.",
    "crankcam": "Faulty sensor, damaged wiring or connector, or a damaged reluctor/tone ring.",
    "maf": "Dirty MAF sensor (try MAF sensor cleaner), an air leak after the sensor, or a clogged air filter.",
    "network": "Wiring or connector problem on the module network, a weak battery or low voltage, a blown "
               "fuse to the module that went silent, or a failed module.",
    "fuelpressure": "Weak fuel pump, clogged fuel filter, faulty pressure regulator, or a bad fuel pressure sensor.",
    "boost": "Boost leak (cracked intercooler hose or loose clamp), faulty wastegate or turbo, or a bad boost sensor.",
    "postcat": "Exhaust leak, an upstream fuel-trim problem, or a failing O2 sensor.",
    "wheelspeed": "Dirty or damaged wheel speed sensor, damaged wiring (common near the wheel), a rusty "
                  "or cracked tone ring, or a worn wheel bearing on hubs with built-in sensors.",
}


def common_causes(code):
    c = code.upper().split("-")[0]
    if "P0300" <= c <= "P0312":
        return _CAUSES["misfire"]
    if c in ("P0171", "P0174", "P0170", "P0173", "P2187", "P2189"):
        return _CAUSES["lean"]
    if c in ("P0172", "P0175", "P2188", "P2190"):
        return _CAUSES["rich"]
    if c in ("P0420", "P0421", "P0430", "P0431"):
        return _CAUSES["cat"]
    if "P0440" <= c <= "P0457":
        return _CAUSES["evap"]
    if c in ("P0128", "P0125"):
        return _CAUSES["thermostat"]
    if c in ("P0010", "P0011", "P0012", "P0013", "P0014", "P0015", "P0020", "P0021", "P0022"):
        return _CAUSES["vvt"]
    if c in ("P0016", "P0017", "P0018", "P0019"):
        return _CAUSES["timing"]
    if "P0400" <= c <= "P0406":
        return _CAUSES["egr"]
    if c in ("P0505", "P0506", "P0507"):
        return _CAUSES["idle"]
    if ("P0030" <= c <= "P0058") or c in ("P0135", "P0141", "P0147", "P0155", "P0161", "P0167"):
        return _CAUSES["o2heater"]
    if c in ("P0560", "P0562", "P0563", "P0620", "P0621", "P0622"):
        return _CAUSES["voltage"]
    if c == "P0700":
        return _CAUSES["tcm"]
    if "P0335" <= c <= "P0349" or c in ("P0365", "P0366"):
        return _CAUSES["crankcam"]
    if "P0100" <= c <= "P0104":
        return _CAUSES["maf"]
    if c.startswith("U0"):
        return _CAUSES["network"]
    if c in ("P0087", "P0088", "P0089", "P0190", "P0191", "P0192", "P0193"):
        return _CAUSES["fuelpressure"]
    if c in ("P0234", "P0299"):
        return _CAUSES["boost"]
    if c in ("P2096", "P2097", "P2098", "P2099"):
        return _CAUSES["postcat"]
    if c in ("C0035", "C0040", "C0045", "C0050"):
        return _CAUSES["wheelspeed"]
    return ""


# --- How urgent is it? -------------------------------------------------------------
GENERIC.setdefault("P0524", "Engine oil pressure too low")


def _is_evap(c):
    return "P0440" <= c <= "P0457"


def severity(code, status="", module=""):
    """-> 'high' (fix soon), 'medium' (get it checked), 'low' (low priority) or 'past' (history)."""
    c = code.upper().split("-")[0]
    s, m = status.lower(), module.lower()
    if "history" in s:
        return "past"
    if "pending" in s or "permanent" in s:
        return "low"
    if "airbag" in m or "restraint" in m or "abs" in m or "brake" in m:
        return "high"
    if "P0300" <= c <= "P0312" or c in ("P0217", "P0524"):
        return "high"
    if _is_evap(c):
        return "low"
    return "medium"


def why_it_matters(code, status="", module=""):
    c = code.upper().split("-")[0]
    s, m = status.lower(), module.lower()
    if "history" in s:
        return "This happened before but isn't happening right now. Often it's a loose connector or a wire that rubs."
    if "permanent" in s:
        return ("The vehicle is waiting to re-test this after a repair. It clears itself after a few normal drives "
                "once the problem is fixed.")
    if "pending" in s:
        return "The vehicle noticed this once. If it happens again on another drive, it becomes a stored code."
    if "airbag" in m or "restraint" in m:
        return "The airbag light is probably on. Airbags may not deploy in a crash until this is fixed."
    if "abs" in m or "brake" in m:
        return ("ABS and traction control may be switched off. Your normal brakes still work, but the wheels can "
                "lock up in a hard stop.")
    if "P0300" <= c <= "P0312":
        return ("A misfire wastes fuel and can overheat and ruin the catalytic converter. If the check-engine light "
                "is flashing, avoid hard driving.")
    if c == "P0217":
        return "The engine is overheating. Stop driving and let it cool to avoid serious engine damage."
    if c == "P0524":
        return "Low oil pressure can destroy the engine. Check the oil level before driving again."
    if _is_evap(c):
        return "This affects emissions, not how the vehicle drives. It will fail an emissions test until fixed."
    if c.startswith("U"):
        return ("Modules aren't talking to each other properly. That can cause odd warning lights or features "
                "that stop working.")
    return "This can affect how the vehicle runs or its emissions. Have it looked at when you can."
