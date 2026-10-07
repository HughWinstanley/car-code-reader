"""
OBD-I (1995 and older): blink-code guides and code meanings for GM, Ford, Chrysler, Toyota and Honda.

These vehicles don't send codes over a cable in a standard way. Instead the check-engine light
(or a light on the computer) blinks them out after a simple jumper or key sequence. The app shows
the steps for the vehicle, the person counts the blinks and types the numbers in, and the app
explains them. Code meanings come from published OBD-I code lists; exact meanings can vary a
little by engine, so they say so.
"""

import re

SAFETY = ("Park on level ground with the parking brake set and the transmission in Park (or Neutral "
          "for a manual). Only connect the terminals named below. A wrong jumper can damage the computer.")

GUIDES = {
    "GM": {
        "title": "GM (Chevy, GMC, Buick, Cadillac, Olds, Pontiac), about 1981 to 1995",
        "steps": [
            "Find the ALDL connector under the dash, near the steering column. It has 12 pins in two rows.",
            "With the key OFF, connect a short jumper wire between terminal A and terminal B (the two "
            "pins at one end of the top row; they're usually labeled on the connector).",
            "Turn the key to ON. Don't start the engine.",
            "Watch the check-engine light. Code 12 comes first: 1 flash, a short pause, 2 flashes. It just "
            "means the self-test is working.",
            "Each code then flashes 3 times. A long pause separates codes; a short pause separates the two "
            "digits of one code. When code 12 comes around again, you've seen them all.",
            "Turn the key OFF and remove the jumper.",
        ],
        "note": "Code meanings can differ slightly between engines, so confirm with a repair manual before "
                "replacing parts.",
        "ok": {"12": "Self-test is working (this isn't a fault)."},
    },
    "Ford": {
        "title": "Ford, Lincoln, Mercury (EEC-IV), about 1984 to 1995",
        "steps": [
            "Find the self-test connector under the hood, usually near the fender or firewall: a 6-pin "
            "connector with a single-wire connector right next to it.",
            "With the key OFF, connect a jumper from the single-wire connector (self-test input) to the "
            "signal-return terminal of the 6-pin connector.",
            "Turn the key to ON. Don't start the engine.",
            "Watch the check-engine light. Each digit is a group of flashes, with a short pause between "
            "digits and a longer pause between codes. Older vehicles use 2-digit codes; most 1991 and newer "
            "use 3-digit codes.",
            "First come the 'right now' codes. Then a single flash (code 10) separates them from the memory "
            "codes, which are problems seen in recent driving.",
            "Code 11 (or 111) means the system passed. Turn the key OFF and remove the jumper.",
        ],
        "note": "Some 2-digit codes mean different things on different engines; both meanings are shown.",
        "ok": {"10": "Separator: the codes after this are from memory (recent driving).",
               "11": "System passed (no problem found).", "111": "System passed (no problem found)."},
    },
    "Chrysler": {
        "title": "Chrysler, Dodge, Jeep, Plymouth, about 1983 to 1995",
        "steps": [
            "No jumper needed. Sit in the driver's seat with the engine off.",
            "Within 5 seconds, turn the key ON, OFF, ON, OFF, ON (end on ON; don't start the engine).",
            "The check-engine light comes on briefly, then starts flashing codes (it can take up to 30 seconds).",
            "Each code is two groups of flashes with a short pause between the digits and a longer pause "
            "between codes.",
            "Code 55 means the list is finished.",
        ],
        "note": "Code 12 only means the battery was disconnected recently.",
        "ok": {"55": "End of the list.", "12": "Battery was disconnected recently (not a fault)."},
    },
    "Toyota": {
        "title": "Toyota and Lexus, about 1987 to 1995",
        "steps": [
            "Warm the engine up, then turn it off. Turn off the radio, A/C and lights.",
            "Find the diagnostic check connector under the hood (a small box marked DIAGNOSIS) or, on some "
            "models, under the dash.",
            "Connect a jumper between terminals TE1 and E1 (labeled inside the lid).",
            "Turn the key to ON. Don't start the engine.",
            "Normal (no codes): the check-engine light blinks evenly and quickly, about 4 times a second.",
            "With codes: the first digit flashes, a 1.5-second pause, then the second digit. Codes are 2.5 "
            "seconds apart and the whole list repeats after a 4.5-second pause.",
            "Turn the key OFF and remove the jumper.",
        ],
        "note": "",
        "ok": {"0": "Steady, even blinking: no codes stored."},
    },
    "Honda": {
        "title": "Honda and Acura, about 1988 to 1995",
        "steps": [
            "1991 and older: the computer (ECU) is under the passenger seat or behind the passenger kick "
            "panel. A small red light on it blinks the codes when the key is ON.",
            "1992 to 1995: find the 2-pin service check connector under the passenger side of the dash, near "
            "the computer. Connect its two pins with a paperclip or jumper.",
            "Turn the key to ON. Don't start the engine.",
            "Count the flashes: a long flash counts 10, a short flash counts 1. For example, 1 long and "
            "4 short is code 14.",
            "Turn the key OFF and remove the jumper.",
        ],
        "note": "",
        "ok": {},
    },
}

CODES = {
    "GM": {
        "13": "Oxygen sensor circuit open or not active", "14": "Coolant temperature sensor: reads too hot (shorted)",
        "15": "Coolant temperature sensor: reads too cold (open)", "16": "Distributorless ignition circuit fault",
        "17": "Camshaft position sensor circuit or timing", "18": "Camshaft or crankshaft sensor fault",
        "19": "Crankshaft sensor fault", "21": "Throttle position sensor: voltage high",
        "22": "Throttle position sensor: voltage low", "23": "Intake air temperature sensor: reads too cold",
        "24": "Vehicle speed sensor circuit", "25": "Intake air temperature sensor: reads too hot",
        "26": "Quad driver module circuit", "28": "Quad driver module circuit", "31": "Wastegate solenoid circuit",
        "32": "EGR system fault", "33": "MAP sensor: voltage high (low vacuum)", "34": "MAP sensor: voltage low (high vacuum)",
        "35": "Idle air control circuit", "36": "Ignition system fault", "38": "Brake switch circuit",
        "39": "Clutch switch circuit", "41": "Cylinder select or ignition reference fault",
        "42": "Electronic spark timing (EST) circuit", "43": "Knock sensor / spark control circuit",
        "44": "Oxygen sensor: running lean", "45": "Oxygen sensor: running rich", "46": "Pass-key anti-theft or power steering pressure switch",
        "47": "Computer data circuit", "48": "Misfire", "51": "Computer memory (PROM / MEM-CAL) fault",
        "52": "Engine oil temperature low, or CALPAK fault", "53": "System voltage high/low, or EGR solenoid 1",
        "54": "Fuel pump voltage low, or EGR solenoid 2", "55": "Computer fault, or EGR solenoid 3",
        "56": "Quad driver module B circuit", "58": "Anti-theft (VATS) circuit", "61": "A/C performance or weak oxygen sensor",
        "62": "Engine oil temperature high", "63": "Right oxygen sensor circuit, or MAP out of range",
        "64": "Right oxygen sensor: running lean", "65": "Right oxygen sensor: running rich",
        "66": "A/C pressure sensor: low", "67": "A/C pressure sensor or clutch circuit", "68": "A/C compressor relay circuit",
        "69": "A/C clutch circuit / pressure high", "72": "Gear selector switch circuit",
        "75": "Digital EGR solenoid 2", "76": "Digital EGR solenoid 3", "77": "Digital EGR solenoid 1",
    },
    "Ford2": {
        "12": "Idle speed control not controlling idle (usually too low)", "13": "Idle speed control didn't respond",
        "14": "Ignition pickup signal erratic", "15": "Keep-alive memory power lost or computer fault",
        "16": "Idle RPM too low / throttle stop too high", "17": "Throttle stop set too low",
        "18": "Check base timing; ignition tach signal erratic", "19": "No power to computer, or erratic idle",
        "21": "Coolant temperature sensor out of range", "22": "MAP / barometric sensor out of range",
        "23": "Throttle position sensor out of range", "24": "Air temperature sensor out of range",
        "25": "Knock sensor not tested", "26": "Mass air flow / vane air flow out of range",
        "27": "Vehicle speed sensor", "28": "Vane air temperature sensor out of range", "29": "Vehicle speed sensor",
        "31": "EGR position / feedback signal low", "32": "EGR not responding", "33": "EGR didn't open",
        "34": "EGR not responding or EGR sensor high", "35": "EGR sensor signal high or RPM too low to test",
        "38": "Idle tracking switch intermittent", "39": "Torque converter clutch not engaging",
        "41": "Running lean (right or only side)", "42": "Running rich (right or only side)",
        "43": "Oxygen sensor not reading, or lean at wide-open throttle", "44": "Air injection (AIR) inoperative",
        "45": "Air injection not diverting", "46": "Air injection bypass not working",
        "47": "Low flow of unmetered air", "48": "High flow of unmetered air", "49": "Spark output circuit",
        "51": "Coolant temperature sensor signal high (open)", "52": "Power steering pressure switch open",
        "53": "Throttle position sensor high", "54": "Air temperature sensor high (open)", "55": "Low key power to computer",
        "56": "Air flow sensor high", "57": "Park/neutral switch intermittent", "58": "Idle tracking switch",
        "59": "Transmission shift problem", "61": "Coolant temperature sensor low (shorted)", "62": "Transmission circuit fault",
        "63": "Throttle position sensor low", "64": "Air temperature sensor low (shorted)",
        "65": "Oxygen sensor intermittent / overdrive cancel switch", "66": "Air flow sensor low",
        "67": "Park/neutral switch circuit or A/C on during test", "68": "Idle tracking switch grounded",
        "69": "Transmission switch", "72": "No MAP/MAF change in the throttle test", "73": "No throttle position change in test",
        "74": "Brake switch", "75": "Brake switch shorted", "76": "Air flow didn't respond in test",
        "77": "Throttle wasn't pressed during test (rerun)", "78": "Power circuit intermittent",
        "79": "A/C was on during test", "81": "Boost or air diverter solenoid", "82": "Fan control or air bypass solenoid",
        "83": "High-speed fan circuit or EGR solenoid", "84": "EGR vacuum regulator", "85": "Shift or canister purge solenoid",
        "86": "3-4 shift solenoid", "87": "Fuel pump circuit", "88": "Throttle kicker or fan control circuit",
        "89": "Converter clutch override solenoid", "91": "Running lean (left side) / shift solenoid 1",
        "92": "Running rich (left side) / shift solenoid 2", "93": "Throttle binding or oxygen sensor not reading",
        "94": "Air injection inoperative / torque converter clutch circuit", "95": "Fuel pump circuit / air not diverting",
        "96": "Fuel pump monitor / air bypass", "97": "Overdrive cancel light circuit", "98": "Transmission pressure control (EPC) circuit",
        "99": "Idle needs to relearn / transmission pressure control",
    },
    "Ford3": {
        "112": "Intake air temperature sensor low (shorted)", "113": "Intake air temperature sensor high (open)",
        "114": "Intake air temperature out of range", "116": "Coolant temperature sensor out of range",
        "117": "Coolant temperature sensor low (shorted)", "118": "Coolant temperature sensor high (open)",
        "121": "Throttle position sensor out of range", "122": "Throttle position sensor low",
        "123": "Throttle position sensor high", "124": "Throttle position voltage higher than expected",
        "125": "Throttle position voltage lower than expected", "126": "MAP / barometric sensor out of range",
        "128": "MAP vacuum not changing", "129": "No MAP/MAF change during test", "136": "Oxygen sensor: lean (left/front)",
        "137": "Oxygen sensor: rich (left/front)", "139": "Oxygen sensor not switching (left/front)",
        "144": "Oxygen sensor not switching (right/rear or only)", "157": "Mass air flow sensor low",
        "158": "Mass air flow sensor high", "159": "Mass air flow sensor out of range", "167": "No throttle change during test",
        "171": "Oxygen sensor at adaptive limit (right/rear)", "172": "Oxygen sensor: lean (right/rear)",
        "173": "Oxygen sensor: rich (right/rear)", "174": "Oxygen sensor slow (right/rear)",
        "175": "Oxygen sensor at adaptive limit (left/front)", "176": "Oxygen sensor: lean (left/front)",
        "177": "Oxygen sensor: rich (left/front)", "178": "Oxygen sensor slow (left/front)",
        "179": "Rich at part throttle (right/rear)", "181": "Lean at part throttle (right/rear)",
        "182": "Rich at idle (right/rear)", "183": "Lean at idle (right/rear)", "184": "Mass air flow higher than expected",
        "185": "Mass air flow lower than expected", "186": "Injector pulse too long", "187": "Injector pulse too short",
        "188": "Rich at part throttle (left/front)", "189": "Lean at part throttle (left/front)",
        "191": "Rich at idle (left/front)", "192": "Lean at idle (left/front)", "194": "Run the injector balance test",
        "195": "Run the injector balance test", "211": "Ignition pickup (PIP) signal erratic",
        "212": "Ignition tach / spark output circuit", "213": "Spark output circuit open or shorted",
        "214": "Cylinder ID circuit", "215": "Ignition coil 1 primary circuit", "216": "Ignition coil 2 primary circuit",
        "217": "Ignition coil 3 primary circuit", "218": "Ignition diagnostic signal / left coil pack",
        "219": "Spark output circuit; timing defaulted", "222": "Ignition diagnostic signal / right coil pack",
        "223": "Dual plug / spark output circuit", "224": "Ignition coil primary circuit", "225": "Knock sensor not tested",
        "226": "Ignition diagnostic monitor signal", "232": "Ignition coil primary circuit", "238": "Ignition coil 4 primary circuit",
        "311": "Air injection not working (right/rear)", "312": "Air injection not diverting", "313": "Air injection not bypassing",
        "314": "Air injection not working (left/front)", "326": "EGR pressure feedback low", "327": "EGR feedback signal low",
        "328": "EGR valve position low", "332": "EGR didn't open during test", "334": "EGR position sensor high",
        "335": "EGR feedback out of range", "336": "EGR pressure feedback high", "337": "EGR feedback signal high",
        "338": "Engine didn't warm up (check thermostat)", "339": "Engine overheated", "341": "Octane jumper installed (information)",
        "411": "Idle too high during test", "412": "Idle too low during test", "452": "Vehicle speed sensor",
        "511": "No power to computer or bad computer", "512": "Memory power was interrupted", "513": "Computer internal fault",
        "519": "Power steering pressure switch open", "521": "Steering wasn't turned during test",
        "522": "Park/neutral or clutch switch circuit", "525": "Park/neutral or clutch switch circuit",
        "536": "Brake switch circuit", "538": "Test wasn't completed (rerun)", "539": "A/C was on during test",
        "542": "Fuel pump circuit", "543": "Fuel pump circuit / relay", "552": "Air injection bypass solenoid",
        "553": "Air injection diverter solenoid", "556": "Fuel pump relay circuit", "558": "EGR vacuum regulator circuit",
        "559": "A/C relay circuit", "563": "High-speed fan circuit", "564": "Fan control circuit",
        "565": "Canister purge solenoid", "566": "3-4 shift solenoid", "617": "Transmission 1-2 shift failure",
        "618": "Transmission 2-3 shift failure", "619": "Transmission 3-4 shift failure", "621": "Shift solenoid 1 circuit",
        "622": "Shift solenoid 2 circuit", "624": "Transmission pressure control (EPC) circuit", "625": "Transmission pressure control (EPC) circuit",
        "626": "Coast clutch solenoid", "627": "Torque converter clutch circuit", "628": "Torque converter clutch slipping",
        "629": "Torque converter clutch circuit", "631": "Overdrive cancel light circuit", "632": "Overdrive cancel switch didn't cycle in test",
        "633": "4x4 low switch position during test", "634": "Gear selector position sensor", "636": "Transmission fluid temperature out of range",
        "637": "Transmission fluid temperature sensor high (open)", "638": "Transmission fluid temperature sensor low (shorted)",
        "639": "Transmission speed sensor", "641": "Shift solenoid 3 circuit", "643": "Torque converter clutch circuit",
        "645": "Transmission 1st gear failure", "646": "Transmission 2nd gear failure", "647": "Transmission 3rd gear failure",
        "648": "Transmission 4th gear failure", "649": "Transmission pressure control system", "651": "Transmission pressure control solenoid",
        "652": "Torque converter clutch circuit", "654": "Transmission not in Park during test", "656": "Torque converter clutch slipping",
        "657": "Transmission overheating", "998": "Key-on test not passed yet / transmission pressure control",
    },
    "Chrysler": {
        "11": "No crankshaft reference signal while cranking", "13": "MAP sensor not responding (no vacuum change)",
        "14": "MAP sensor voltage out of range", "15": "No vehicle speed signal", "17": "Engine staying too cold (check thermostat)",
        "21": "Oxygen sensor not switching", "22": "Coolant temperature sensor out of range",
        "23": "Intake air temperature sensor out of range", "24": "Throttle position sensor out of range",
        "25": "Idle air control motor circuit", "27": "Fuel injector driver circuit", "33": "A/C clutch relay circuit",
        "34": "Cruise control solenoid circuit", "35": "Radiator fan relay circuit", "41": "Alternator field control circuit",
        "42": "Auto shutdown relay circuit", "44": "Coolant temperature sensor circuit", "46": "Charging voltage too high",
        "47": "Charging voltage too low", "51": "Oxygen sensor: running lean", "52": "Oxygen sensor: running rich",
        "53": "Computer internal fault", "54": "No camshaft (fuel sync) signal while cranking",
        "62": "Couldn't update service-reminder mileage", "63": "Computer memory write failed",
    },
    "Toyota": {
        "11": "Computer power supply interrupted", "12": "No RPM signal while cranking", "13": "RPM signal lost above 1000 rpm",
        "14": "Ignition confirmation (IGF) signal missing", "21": "Oxygen sensor or its heater", "22": "Coolant temperature sensor",
        "24": "Intake air temperature sensor", "25": "Running lean", "26": "Running rich", "27": "Rear oxygen sensor circuit",
        "28": "Second oxygen sensor", "31": "Vacuum (MAP) sensor or air flow meter signal", "32": "Air flow meter signal",
        "33": "Idle speed control valve circuit", "34": "Turbo boost pressure abnormal", "35": "Turbo pressure sensor",
        "41": "Throttle position sensor", "42": "Vehicle speed sensor", "43": "No starter signal",
        "51": "Switch signal (A/C, throttle idle contact or neutral) during test", "52": "Knock sensor 1",
        "53": "Knock sensor 2 / knock control in computer", "71": "EGR system", "72": "Fuel cut solenoid",
    },
    "Honda": {
        "0": "Engine computer (ECU) fault", "1": "Front oxygen sensor", "3": "MAP sensor (electrical)",
        "4": "Crankshaft position sensor", "5": "MAP sensor (vacuum hose or sensor)", "6": "Coolant temperature sensor",
        "7": "Throttle position sensor", "8": "Top dead center (TDC) sensor", "9": "Cylinder position sensor",
        "10": "Intake air temperature sensor", "12": "EGR system", "13": "Barometric pressure sensor",
        "14": "Idle air control valve", "15": "Ignition output signal", "16": "Fuel injectors",
        "17": "Vehicle speed sensor", "21": "VTEC solenoid", "22": "VTEC oil pressure switch", "23": "Knock sensor",
        "41": "Oxygen sensor heater", "43": "Fuel supply system", "45": "Fuel system too rich or too lean",
    },
}

GROUP_OF_FAMILY = {"GM": "GM", "Ford": "Ford", "Chrysler": "Chrysler", "Dodge": "Chrysler", "Jeep": "Chrysler",
                   "Plymouth": "Chrysler", "Toyota": "Toyota", "Honda": "Honda"}


def group_for(family):
    return GROUP_OF_FAMILY.get(family)


def parse_entry(text):
    """'12, 33  44 111' -> ['12', '33', '44', '111'] (keeps order, drops repeats)."""
    out = []
    for c in re.findall(r"\d+", text or ""):
        c = c.lstrip("0") or "0"
        if c not in out:
            out.append(c)
    return out


def explain(group, code):
    """-> (meaning, kind) where kind is 'ok' (not a fault), 'fault' or 'unknown'."""
    guide = GUIDES[group]
    if code in guide["ok"]:
        return guide["ok"][code], "ok"
    if group == "Ford":
        table = CODES["Ford3"] if len(code) == 3 else CODES["Ford2"]
    else:
        table = CODES[group]
    if code in table:
        return table[code], "fault"
    return "Not in the built-in list for this make. Check that the flashes were counted correctly.", "unknown"
